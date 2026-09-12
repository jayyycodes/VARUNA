"""
Varuna ORCA — FastAPI Backend Entrypoint

The API gateway that connects the frontend to the Planner/Orchestrator agent.

Start:
    uvicorn backend.main:app --reload

Endpoints:
    POST /chat   — process a natural-language marine query
    GET  /health — service health check

Interactive docs: http://localhost:8000/docs
"""

import logging
import os
import sys
import uuid
from pathlib import Path

# ── Ensure project root is in sys.path ─────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.planner.planner_agent import PlannerAgent
from backend.routes.alerts import router as alerts_router
from backend.routes.analytics import router as analytics_router

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-5s  %(message)s",
)
logger = logging.getLogger("varuna.api")


# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Varuna ORCA",
    description=(
        "Agentic Marine Intelligence for India's Coastline — "
        "Smart India Hackathon 2026, SIH26176"
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register subrouters
app.include_router(alerts_router)
app.include_router(analytics_router)


# ── Planner (singleton) ──────────────────────────────────────────────
planner = PlannerAgent()


# ── Request / Response Schemas ────────────────────────────────────────

class ChatRequest(BaseModel):
    """User query payload (accepts either 'query' or 'text')."""
    query: str | None = Field(None, description="Natural-language question about marine conditions")
    text: str | None = Field(None, description="Alias for query")
    conversation_id: str | None = Field(None, description="Session ID for multi-turn context")
    user_id: str | None = Field(None, description="User identifier")
    location: dict | None = Field(None, description="Optional lat/lon coordinates")
    time_window: dict | None = Field(None, description="Optional time window")
    locale: str | None = Field("en-IN", description="Response language locale")
    session_id: str | None = Field(None, description="Alias for conversation_id")

    def get_query_text(self) -> str:
        q = (self.query or self.text or "").strip()
        if not q:
            return "Check current marine safety conditions"
        return q

    def get_session_id(self) -> str:
        return self.conversation_id or self.session_id or str(uuid.uuid4())


class ChatResponse(BaseModel):
    """
    Full structured response from the ORCA pipeline.

    Contains the conversational text, map data (GeoJSON), evidence trail,
    and risk verdict — everything the frontend needs to render the UI.
    """
    query_run_id: str
    intent: str
    text: str
    map_data: dict | None = None
    evidence: list | None = None
    risk_verdict: dict | None = None
    status: str


# ── Core Query Handler ───────────────────────────────────────────────

async def process_query_pipeline(req: ChatRequest) -> ChatResponse:
    """Helper to dispatch queries to LangGraph planner."""
    cid = req.get_session_id()
    uid = req.user_id or "anonymous"
    q = req.get_query_text()

    logger.info(f"[api] Processing query={q!r}  cid={cid[:8]}…  uid={uid}")

    result = await planner.handle_query(
        query=q,
        conversation_id=cid,
        user_id=uid,
    )

    return ChatResponse(**result)


# ── Endpoints ────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Primary chat endpoint connecting directly to LangGraph planner."""
    return await process_query_pipeline(req)


@app.post("/v1/query", response_model=ChatResponse)
async def v1_query(req: ChatRequest):
    """V1 REST query endpoint alias."""
    return await process_query_pipeline(req)


@app.post("/v1/chat", response_model=ChatResponse)
async def v1_chat(req: ChatRequest):
    """V1 Chat endpoint alias."""
    return await process_query_pipeline(req)


@app.get("/health")
@app.get("/v1/health")
async def health():
    """Service health check — used by Frontend, Docker, load balancers, and CI."""
    from backend.gateway.circuit_breaker import circuit_registry
    from backend.gateway.observability import is_tracing_active

    upstream = circuit_registry.get_all_status()
    all_healthy = all(s["is_healthy"] for s in upstream)

    return {
        "status": "ok" if all_healthy else "degraded",
        "service": "varuna-orca",
        "version": "0.1.0",
        "planner_ready": True,
        "tracing_active": is_tracing_active(),
        "upstream_circuits": upstream,
    }


@app.get("/api/health/upstream")
async def upstream_health():
    """Detailed upstream circuit breaker and latency monitoring."""
    from backend.gateway.circuit_breaker import circuit_registry
    circuits = circuit_registry.get_all_status()
    return {
        "all_healthy": all(s["is_healthy"] for s in circuits),
        "circuits": circuits,
    }
