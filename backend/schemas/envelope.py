"""
Shared inter-agent message envelope.

Every agent returns a response in this exact shape so the Planner
can aggregate results without special-casing each agent, and so every
claim shown to the user can be traced back to a source + timestamp.

See /README.md section "Inter-Agent Message Contract" for the full spec.
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class AgentEnvelope(BaseModel):
    agent: str  # e.g. "weather_intelligence", "marine_fishing", "geofencing"
    query_run_id: str  # links back to the parent query_runs row
    status: Literal["success", "error", "degraded"]
    data: dict[str, Any]  # agent-specific structured payload
    confidence: float = Field(ge=0.0, le=1.0)
    source: str  # e.g. "IMD Regional Forecast API", "INCOIS PFZ WebGIS"
    timestamp: datetime
    thresholds_used: dict[str, Any] | None = None  # for Risk Agent traceability
    error_message: str | None = None


class RiskVerdict(BaseModel):
    query_run_id: str
    verdict: Literal["SAFE", "CAUTION", "UNSAFE"]
    reasons: list[str]  # human-readable, e.g. "wave height 2.8m exceeds 2.5m threshold"
    rule_trace: dict[str, Any]  # exact rule engine inputs/outputs — NEVER LLM-generated
    created_at: datetime
