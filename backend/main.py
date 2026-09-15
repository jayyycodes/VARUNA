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

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import sys
import uuid

# ── Ensure project root is in sys.path ─────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.planner.planner_agent import PlannerAgent
from backend.routes.alerts import router as alerts_router
from backend.routes.analytics import router as analytics_router
from backend.routes.fleet import router as fleet_router
from backend.routes.route_planner import router as route_router

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

# ── CORS ─────────────────────────────────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
if cors_origins_env == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if cors_origins_env != "*" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register subrouters
app.include_router(alerts_router)
app.include_router(fleet_router)
app.include_router(analytics_router)
app.include_router(route_router)


# ── Planner (singleton) ──────────────────────────────────────────────
planner = PlannerAgent()


def log_query_execution_to_supabase(
    query_run_id: str,
    intent: str,
    status: str,
    started_at: datetime,
    completed_at: datetime,
    risk_verdict: dict | None = None,
):
    """Asynchronously persist query execution trace and risk verdict to Supabase audit tables."""
    try:
        import psycopg2
        from psycopg2.extras import Json
        host = os.getenv("POSTGRES_HOST")
        if not host:
            return

        conn = psycopg2.connect(
            host=host,
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            connect_timeout=3,
        )
        with conn.cursor() as cur:
            # 1. Upsert into query_runs
            cur.execute(
                """
                INSERT INTO query_runs (id, intent, status, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE 
                SET intent = EXCLUDED.intent, status = EXCLUDED.status, completed_at = EXCLUDED.completed_at;
                """,
                (query_run_id, intent, status, started_at, completed_at)
            )

            # 2. Insert into risk_verdicts if verdict is present
            if risk_verdict and isinstance(risk_verdict, dict) and "verdict" in risk_verdict:
                verdict_str = str(risk_verdict.get("verdict", "CAUTION"))
                rule_trace = risk_verdict.get("rules_fired") or risk_verdict.get("rule_trace") or risk_verdict
                verdict_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO risk_verdicts (id, query_run_id, verdict, rule_trace, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (verdict_id, query_run_id, verdict_str, Json(rule_trace), completed_at)
                )

        conn.commit()
        conn.close()
        logger.debug(f"[supabase_audit] Logged query_run {query_run_id[:8]} to Supabase.")
    except Exception as e:
        logger.warning(f"[supabase_audit] Supabase query_runs log skipped: {e}")


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

async def process_query_pipeline(req: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    """Helper to dispatch queries to LangGraph planner and enqueue audit logging."""
    started_at = datetime.now(timezone.utc)
    cid = req.get_session_id()
    uid = req.user_id or "anonymous"
    q = req.get_query_text()

    logger.info(f"[api] Processing query={q!r}  cid={cid[:8]}…  uid={uid}")

    result = await planner.handle_query(
        query=q,
        conversation_id=cid,
        user_id=uid,
        locale=req.locale,
    )

    completed_at = datetime.now(timezone.utc)
    qid = result.get("query_run_id") or str(uuid.uuid4())

    background_tasks.add_task(
        log_query_execution_to_supabase,
        query_run_id=qid,
        intent=result.get("intent", "general_query"),
        status=result.get("status", "SUCCESS"),
        started_at=started_at,
        completed_at=completed_at,
        risk_verdict=result.get("risk_verdict"),
    )

    return ChatResponse(**result)


# ── Endpoints ────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    """Primary chat endpoint connecting directly to LangGraph planner."""
    return await process_query_pipeline(req, background_tasks)


@app.post("/v1/query", response_model=ChatResponse)
async def v1_query(req: ChatRequest, background_tasks: BackgroundTasks):
    """V1 REST query endpoint alias."""
    return await process_query_pipeline(req, background_tasks)


@app.post("/v1/chat", response_model=ChatResponse)
async def v1_chat(req: ChatRequest, background_tasks: BackgroundTasks):
    """V1 Chat endpoint alias."""
    return await process_query_pipeline(req, background_tasks)


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
