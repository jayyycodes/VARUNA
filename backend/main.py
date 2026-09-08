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
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.planner.planner_agent import PlannerAgent

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


# ── Planner (singleton) ──────────────────────────────────────────────
planner = PlannerAgent()


# ── Request / Response Schemas ────────────────────────────────────────

class ChatRequest(BaseModel):
    """User query payload."""
    query: str = Field(..., description="Natural-language question about marine conditions")
    conversation_id: str | None = Field(None, description="Session ID for multi-turn context")
    user_id: str | None = Field(None, description="User identifier")


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


# ── Endpoints ────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Process a natural-language marine query through the ORCA agent pipeline.

    The query flows through:
    1. Intent classification (LLM)
    2. Parallel agent dispatch (Weather + Marine + Geofencing, or RAG)
    3. Deterministic risk assessment
    4. Response synthesis (LLM)

    Returns text + map data + evidence trail + risk verdict.
    """
    cid = req.conversation_id or str(uuid.uuid4())
    uid = req.user_id or "anonymous"

    logger.info(f"[api] POST /chat — query={req.query!r}  cid={cid[:8]}…  uid={uid}")

    result = await planner.handle_query(
        query=req.query,
        conversation_id=cid,
        user_id=uid,
    )

    return ChatResponse(**result)


@app.get("/health")
async def health():
    """Service health check — used by Docker, load balancers, and CI."""
    return {
        "status": "ok",
        "service": "varuna-orca",
        "version": "0.1.0",
    }
