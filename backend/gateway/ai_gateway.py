"""
AI Gateway — centralized LLM access layer for Varuna / ORCA.

Every LLM call in the system goes through `call_llm()`.
No agent holds provider API keys directly.

Provides:
  - Provider abstraction via LiteLLM (Groq, Cerebras, or any OpenAI-compatible)
  - Automatic fallback: primary model fails → fallback model
  - Per-agent model routing (cheaper model for intent, larger for planning)
  - Structured logging of latency + token usage

Usage:
    from backend.gateway.ai_gateway import call_llm

    text = await call_llm("planner", [{"role": "user", "content": "..."}])
"""

import os
import logging
import time

from dotenv import load_dotenv
from litellm import acompletion

load_dotenv()
logger = logging.getLogger("varuna.gateway")


# ── Model routing table ───────────────────────────────────────────────
# Each agent role maps to a model. Override any of these via .env.
# Format: "provider/model_name" — LiteLLM resolves the provider.

MODELS: dict[str, str] = {
    "planner":      os.getenv("PLANNER_MODEL",      "groq/openai/gpt-oss-120b"),
    "intent":       os.getenv("INTENT_MODEL",        "groq/openai/gpt-oss-120b"),
    "risk_explain": os.getenv("RISK_EXPLAIN_MODEL",  "groq/openai/gpt-oss-120b"),
    "rag":          os.getenv("RAG_MODEL",           "groq/qwen/qwen3.8-27b"),
    "synthesizer":  os.getenv("SYNTHESIZER_MODEL",   "groq/openai/gpt-oss-120b"),
    "default":      os.getenv("FALLBACK_MODEL",      "groq/qwen/qwen3.8-27b"),
}

FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "groq/qwen/qwen3.8-27b")


# ── Startup checks ────────────────────────────────────────────────────

def _check_api_keys() -> None:
    """Warn early if provider keys are missing."""
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("[gateway] GROQ_API_KEY not set — Groq models will fail")
    if not os.getenv("CEREBRAS_API_KEY"):
        logger.warning("[gateway] CEREBRAS_API_KEY not set — Cerebras fallback will fail")

_check_api_keys()


# ── Public API ─────────────────────────────────────────────────────────

async def call_llm(
    role: str,
    messages: list[dict],
    *,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    response_format: dict | None = None,
) -> str:
    """
    Route an LLM call through the AI Gateway with automatic fallback.

    Args:
        role: Routing key — determines which model to use (see MODELS dict).
              One of: "planner", "intent", "risk_explain", "rag", "synthesizer".
        messages: Chat messages in OpenAI format
                  [{"role": "system", "content": "..."}, ...].
        temperature: Sampling temperature (lower = more deterministic).
        max_tokens: Maximum completion tokens.
        response_format: Optional, e.g. {"type": "json_object"} for JSON mode.

    Returns:
        The assistant's response content as a string.

    Raises:
        Exception: If both primary and fallback providers fail.
    """
    model = MODELS.get(role, MODELS["default"])

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format

    # ── Try primary model ──────────────────────────────────────────
    t0 = time.monotonic()
    try:
        resp = await acompletion(**kwargs)
        ms = (time.monotonic() - t0) * 1000
        tok = resp.usage.total_tokens if resp.usage else "?"
        logger.info(f"[gateway] {role} → {model}  OK  ({ms:.0f}ms, {tok} tok)")
        return resp.choices[0].message.content

    except Exception as primary_err:
        logger.warning(f"[gateway] {role} → {model}  FAILED: {primary_err}")
        # If we're already on the fallback model, don't retry the same thing
        if model == FALLBACK_MODEL:
            raise

    # ── Try fallback model ─────────────────────────────────────────
    kwargs["model"] = FALLBACK_MODEL
    t0 = time.monotonic()
    try:
        resp = await acompletion(**kwargs)
        ms = (time.monotonic() - t0) * 1000
        tok = resp.usage.total_tokens if resp.usage else "?"
        logger.info(
            f"[gateway] {role} → {FALLBACK_MODEL} (fallback) OK  "
            f"({ms:.0f}ms, {tok} tok)"
        )
        return resp.choices[0].message.content

    except Exception as fallback_err:
        logger.error(f"[gateway] Fallback {FALLBACK_MODEL} also failed: {fallback_err}")
        raise
