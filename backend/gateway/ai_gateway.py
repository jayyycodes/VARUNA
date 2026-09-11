"""
AI Gateway — centralized LLM access layer for Varuna / ORCA.

Every LLM call in the system goes through `call_llm()`.
No agent holds provider API keys directly.

Provides:
  - Direct ultra-fast async provider clients (Groq + Cerebras) with httpx transport
  - Automatic fallback: primary model fails → fallback model
  - Per-agent model routing (cheaper model for intent, larger for planning)
  - Structured logging of latency + token usage

Usage:
    from backend.gateway.ai_gateway import call_llm

    text = await call_llm("planner", [{"role": "user", "content": "..."}])
"""

from __future__ import annotations

import os
import logging
import time
from typing import Any
from dotenv import load_dotenv
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

load_dotenv()
logger = logging.getLogger("varuna.gateway")

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

CEREBRAS_KEY = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_BASE = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")

# Initialize SDK clients
groq_client = AsyncOpenAI(api_key=GROQ_KEY, base_url=GROQ_BASE) if (GROQ_KEY and AsyncOpenAI) else None
cerebras_client = AsyncOpenAI(api_key=CEREBRAS_KEY, base_url=CEREBRAS_BASE) if (CEREBRAS_KEY and AsyncOpenAI) else None

# ── Model routing table ───────────────────────────────────────────────
MODELS: dict[str, str] = {
    "planner":      os.getenv("PLANNER_MODEL",      "openai/gpt-oss-120b"),
    "intent":       os.getenv("INTENT_MODEL",        "openai/gpt-oss-120b"),
    "risk_explain": os.getenv("RISK_EXPLAIN_MODEL",  "openai/gpt-oss-120b"),
    "rag":          os.getenv("RAG_MODEL",           "qwen/qwen3.8-27b"),
    "synthesizer":  os.getenv("SYNTHESIZER_MODEL",   "openai/gpt-oss-120b"),
    "default":      os.getenv("FALLBACK_MODEL",      "openai/gpt-oss-120b"),
}

FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "openai/gpt-oss-120b")


def _clean_model_name(raw_model: str) -> tuple[str, str]:
    """Determine provider and clean model name."""
    if raw_model.startswith("groq/"):
        return "groq", raw_model[5:]
    if raw_model.startswith("cerebras/"):
        return "cerebras", raw_model[9:]
    return "groq", raw_model


async def _execute_chat(
    client: AsyncOpenAI | None,
    model_name: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    response_format: dict | None,
) -> str:
    """Execute completion request with AsyncOpenAI client."""
    if not client:
        raise ValueError("Client for provider is not configured or missing API key.")

    kwargs: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format

    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


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
    """
    target_model = MODELS.get(role, MODELS["default"])
    provider, model_name = _clean_model_name(target_model)
    from backend.gateway.circuit_breaker import circuit_registry
    from backend.gateway.observability import log_llm_span

    # 1. Try Primary Provider (Guarded by Circuit Breaker)
    primary_svc = f"{provider}_llm"
    t0 = time.monotonic()

    if circuit_registry.get(primary_svc).is_available():
        try:
            active_client = groq_client if provider == "groq" else cerebras_client
            content = await _execute_chat(
                active_client,
                model_name,
                messages,
                temperature,
                max_tokens,
                response_format,
            )
            ms = (time.monotonic() - t0) * 1000
            circuit_registry.get(primary_svc).record_success()
            logger.info(f"[gateway] {role} → {provider}/{model_name} OK ({ms:.0f}ms)")
            log_llm_span(role, provider, model_name, messages, content, ms)
            return content

        except Exception as primary_err:
            circuit_registry.get(primary_svc).record_failure(primary_err)
            logger.warning(f"[gateway] {role} → {provider}/{model_name} FAILED: {primary_err}")
    else:
        logger.info(f"[gateway] Primary {primary_svc} circuit is OPEN — skipping directly to fallback")

    # 2. Try Fallback Provider (Guarded by Circuit Breaker)
    fb_provider, fb_model = _clean_model_name(FALLBACK_MODEL)
    fb_svc = f"{fb_provider}_llm"
    t0 = time.monotonic()

    try:
        fallback_client = cerebras_client if fb_provider == "cerebras" or groq_client is None else groq_client
        content = await _execute_chat(
            fallback_client,
            fb_model,
            messages,
            temperature,
            max_tokens,
            response_format,
        )
        ms = (time.monotonic() - t0) * 1000
        circuit_registry.get(fb_svc).record_success()
        logger.info(f"[gateway] {role} → {fb_provider}/{fb_model} (fallback) OK ({ms:.0f}ms)")
        log_llm_span(role, fb_provider, fb_model, messages, content, ms)
        return content

    except Exception as fallback_err:
        circuit_registry.get(fb_svc).record_failure(fallback_err)
        logger.error(f"[gateway] Fallback {FALLBACK_MODEL} also failed: {fallback_err}")
        log_llm_span(role, fb_provider, fb_model, messages, "", (time.monotonic() - t0) * 1000, error=str(fallback_err))
        raise fallback_err
