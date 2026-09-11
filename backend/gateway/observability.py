"""
LangSmith & Observability Tracing for Varuna / ORCA
Provides full telemetry, agent trajectory logging, and LLM call spans.

Integrates with:
  - LANGSMITH_TRACING=true
  - LANGSMITH_API_KEY
  - LANGSMITH_PROJECT=varuna-orca
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Optional

logger = logging.getLogger("varuna.observability")

# Environment flags
TRACING_ENABLED = os.getenv("LANGSMITH_TRACING", "").lower() in ("true", "1", "yes")
LANGSMITH_KEY = os.getenv("LANGSMITH_API_KEY", "")
PROJECT_NAME = os.getenv("LANGSMITH_PROJECT", "varuna-orca")

try:
    from langsmith import Client, RunTree
    langsmith_client = Client() if (TRACING_ENABLED and LANGSMITH_KEY) else None
except Exception as _e:
    langsmith_client = None


def is_tracing_active() -> bool:
    """Check if LangSmith tracing is configured and active."""
    return bool(langsmith_client is not None and TRACING_ENABLED)


def log_agent_trajectory(
    run_id: str,
    agent_name: str,
    intent: str,
    status: str,
    latency_ms: float,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    error: Optional[str] = None,
):
    """
    Records an agent trajectory step into LangSmith and structured logs.
    """
    logger.info(
        f"[trace] agent={agent_name} intent={intent} status={status} "
        f"latency={latency_ms:.1f}ms run={run_id[:8]}"
    )

    if not is_tracing_active():
        return

    try:
        run = RunTree(
            name=f"agent:{agent_name}",
            run_type="chain",
            project_name=PROJECT_NAME,
            inputs={"intent": intent, "inputs": inputs},
            outputs={"status": status, "outputs": outputs, "error": error},
            extra={"metadata": {"agent": agent_name, "query_run_id": run_id}},
        )
        run.end(outputs={"status": status, "outputs": outputs, "error": error})
        run.post()
    except Exception as exc:
        logger.debug(f"[observability] LangSmith agent span non-blocking error: {exc}")


def log_llm_span(
    role: str,
    provider: str,
    model_name: str,
    prompt_messages: list[dict],
    response_content: str,
    latency_ms: float,
    error: Optional[str] = None,
):
    """
    Records an LLM completion span into LangSmith and telemetry.
    """
    logger.info(
        f"[trace:llm] role={role} provider={provider}/{model_name} "
        f"latency={latency_ms:.0f}ms tokens_approx={len(response_content)//4}"
    )

    if not is_tracing_active():
        return

    try:
        run = RunTree(
            name=f"llm:{role}",
            run_type="llm",
            project_name=PROJECT_NAME,
            inputs={"messages": prompt_messages},
            outputs={"content": response_content, "error": error},
            extra={
                "metadata": {
                    "role": role,
                    "provider": provider,
                    "model": model_name,
                    "latency_ms": round(latency_ms, 1),
                }
            },
        )
        run.end(outputs={"content": response_content, "error": error})
        run.post()
    except Exception as exc:
        logger.debug(f"[observability] LangSmith LLM span non-blocking error: {exc}")
