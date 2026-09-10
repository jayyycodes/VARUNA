"""
Planner / Orchestrator Agent — owner: Jay

LangGraph state machine that orchestrates the full ORCA query pipeline:

  1. classify_intent  — LLM extracts intent, location, date from user query
  2. dispatch_agents  — calls Weather + Marine + Geofencing (or RAG) in parallel
  3. assess_risk      — deterministic rule engine computes SAFE/CAUTION/UNSAFE
  4. synthesize       — LLM composes a user-facing response with evidence

Currently uses mock agents (agents/planner/mock_agents.py).
Swap with real agents as teammates deliver — the Planner doesn't care
whether the AgentEnvelope came from a mock or a real API.

Graph:
  START → classify_intent → [route_by_intent]
                              ├─ data query  → dispatch_data_agents → assess_risk → synthesize → END
                              └─ regulation  → dispatch_rag                       → synthesize → END
"""

import asyncio
import json
import logging
import uuid
from datetime import date, timedelta
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.gateway.ai_gateway import call_llm
from backend.schemas.envelope import AgentEnvelope

from agents.planner.mock_agents import (
    mock_geofencing,
    mock_marine,
    mock_rag,
    mock_risk_verdict,
    mock_weather,
)

logger = logging.getLogger("varuna.planner")


# ═══════════════════════════════════════════════════════════════════════
# State
# ═══════════════════════════════════════════════════════════════════════

class PlannerState(TypedDict, total=False):
    # ── Inputs ─────────────────────────────────────────────────────
    query: str
    conversation_id: str
    user_id: str
    query_run_id: str

    # ── After intent classification ────────────────────────────────
    intent: str                         # safety_check | find_fishing_zone | route_request | regulation_question
    location: dict[str, Any]            # {"lat": float, "lon": float, "name": str}
    date: str                           # ISO date YYYY-MM-DD

    # ── Agent results (serialized envelopes) ───────────────────────
    weather_result: dict[str, Any]
    marine_result: dict[str, Any]
    geofencing_result: dict[str, Any]
    rag_result: dict[str, Any]

    # ── Risk assessment ────────────────────────────────────────────
    risk_verdict: dict[str, Any]

    # ── Final output ───────────────────────────────────────────────
    response: dict[str, Any]
    error: str


# ═══════════════════════════════════════════════════════════════════════
# Prompts
# ═══════════════════════════════════════════════════════════════════════

INTENT_SYSTEM_PROMPT = """\
You are the intent classifier for ORCA, a marine intelligence system \
for Indian fishermen and coastal operators.

Given a user query about marine / fishing / coastal conditions, extract:

1. **intent** — exactly one of:
   - "safety_check"      → asks about safety, weather, whether it's safe to go out
   - "find_fishing_zone"  → asks where to fish, best spots, PFZ
   - "route_request"      → asks about navigation, how to reach a location safely
   - "regulation_question" → asks about rules, regulations, why a zone is restricted

2. **location** — lat/lon and place name.
   If the user names a place, approximate its coordinates.
   If unspecified, default to Ratnagiri, Maharashtra (lat 16.99, lon 73.30).

3. **date** — the date in YYYY-MM-DD format.
   "today" = {today}. "tomorrow" = {tomorrow}.
   If unspecified, use tomorrow.

Respond ONLY with valid JSON — no markdown fences, no explanation:
{{"intent":"...","location":{{"lat":0.0,"lon":0.0,"name":"..."}},"date":"YYYY-MM-DD","reasoning":"one line"}}"""


SYNTHESIS_SYSTEM_PROMPT = """\
You are the response writer for ORCA, a marine intelligence system \
for Indian fishermen and coastal operators.

Given structured agent results, write a clear, practical, conversational response.

RULES — you MUST follow all of these:
1. Reference specific numbers (wave height, wind speed, SST, distance, etc.).
2. The risk verdict "{verdict}" was computed by a deterministic rule engine. \
It is FINAL. State it clearly — do NOT soften, override, or reinterpret it.
3. Explain WHY the verdict was reached using the reasons provided.
4. If PFZ fishing zones are available, recommend the top zones with distance and likely species.
5. If geofencing data is available, mention boundary status and any warnings.
6. Be concise and practical — your audience is working fishermen, not academics.
7. End with one clear, actionable recommendation.

Write the response as plain text paragraphs. No markdown headers or bullet points."""


# ═══════════════════════════════════════════════════════════════════════
# Graph nodes
# ═══════════════════════════════════════════════════════════════════════

async def classify_intent(state: PlannerState) -> dict:
    """Use LLM structured output to parse intent, location, and date."""
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    messages = [
        {
            "role": "system",
            "content": INTENT_SYSTEM_PROMPT.format(
                today=today_str, tomorrow=tomorrow_str
            ),
        },
        {"role": "user", "content": state["query"]},
    ]

    try:
        try:
            raw = await call_llm(
                "intent",
                messages,
                temperature=0.0,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
        except Exception:
            raw = await call_llm(
                "intent",
                messages,
                temperature=0.0,
                max_tokens=512,
            )

        clean_raw = raw.strip()
        if "```" in clean_raw:
            parts = clean_raw.split("```")
            if len(parts) >= 2:
                clean_raw = parts[1]
                if clean_raw.startswith("json"):
                    clean_raw = clean_raw[4:]
        parsed = json.loads(clean_raw.strip())

        intent = parsed.get("intent", "safety_check")
        location = parsed.get("location", {"lat": 16.99, "lon": 73.30, "name": "Ratnagiri"})
        query_date = parsed.get("date", tomorrow_str)

        logger.info(
            f"[planner] Intent: {intent} | "
            f"Location: {location.get('name')} ({location.get('lat')}, {location.get('lon')}) | "
            f"Date: {query_date}"
        )
        return {"intent": intent, "location": location, "date": query_date}

    except Exception as e:
        logger.error(f"[planner] Intent classification failed: {e} — using defaults")
        return {
            "intent": "safety_check",
            "location": {"lat": 16.99, "lon": 73.30, "name": "Ratnagiri (default)"},
            "date": tomorrow_str,
        }


async def dispatch_data_agents(state: PlannerState) -> dict:
    """
    Call Weather + Marine + Geofencing agents in parallel.

    Weather is now LIVE (Cbum's WeatherAgent — Open-Meteo).
    Marine is still mocked (until Jaish delivers).
    Geofencing attempts LIVE (Vedant's PostGIS agent), falls back to mock.
    """
    qid = state["query_run_id"]
    lat = state["location"]["lat"]
    lon = state["location"]["lon"]
    d = state["date"]

    async def _get_weather() -> AgentEnvelope:
        """Call Cbum's LIVE WeatherAgent; fall back to mock only on import/crash."""
        try:
            from agents.weather.weather_agent import WeatherAgent
            result = await WeatherAgent().get_forecast(lat=lat, lon=lon, date=d, query_run_id=qid)
            # 'degraded' is still real live data with a fallback payload — do NOT replace with mock.
            # Only fall back to mock on a hard 'error' status (shouldn't happen; WeatherAgent
            # returns degraded instead, but guard anyway).
            if result.status == "error":
                logger.warning(
                    f"[planner] Live Weather returned error ({result.error_message}) — using mock fallback"
                )
                return mock_weather(qid, lat, lon, d)
            logger.info(f"[planner] Live Weather OK ({result.status}) — {result.data.get('forecast_summary')}")
            return result
        except Exception as exc:
            logger.warning(f"[planner] WeatherAgent import/call failed: {exc} — using mock fallback")
            return mock_weather(qid, lat, lon, d)

    async def _get_geofencing() -> AgentEnvelope:
        """Call Vedant's LIVE GeofencingAgent (PostGIS); fall back to mock on any failure."""
        try:
            from agents.geofencing.agent import GeofencingAgent
            from agents.geofencing.models import GeofencingRequest
            result = await GeofencingAgent(db_pool=None).run(
                GeofencingRequest(query_run_id=qid, lat=lat, lon=lon)
            )
            if result.status == "error":
                logger.warning(
                    f"[planner] Live Geofencing returned error ({result.error_message}) — using mock fallback"
                )
                return mock_geofencing(qid, lat, lon)
            logger.info(
                f"[planner] Live Geofencing OK — status: {result.data.get('status')}, "
                f"nearest: {result.data.get('nearest_boundary_name')}"
            )
            return result
        except Exception as exc:
            logger.warning(f"[planner] GeofencingAgent import/call failed: {exc} — using mock fallback")
            return mock_geofencing(qid, lat, lon)

    # Dispatch Weather + Geofencing in parallel; Marine is still mocked (Jaish pending)
    weather, geo = await asyncio.gather(_get_weather(), _get_geofencing())
    marine = mock_marine(qid, lat, lon, d)

    logger.info(
        f"[planner] Dispatched 3 data agents — "
        f"Weather: {weather.status} (LIVE), Marine: mock, Geofencing: {geo.status} (LIVE)"
    )

    return {
        "weather_result": weather.model_dump(mode="json"),
        "marine_result": marine.model_dump(mode="json"),
        "geofencing_result": geo.model_dump(mode="json"),
    }


async def dispatch_rag(state: PlannerState) -> dict:
    """Call RAG/Advisory agent for regulation questions."""
    qid = state["query_run_id"]
    q = state["query"]
    try:
        from agents.rag_advisory.rag_agent import RAGAdvisoryAgent
        agent = RAGAdvisoryAgent()
        rag_result = await agent.answer_with_citations(question=q, query_run_id=qid)
        logger.info(f"[planner] Live RAG agent OK — {len(rag_result.get('citations', []))} citations")
    except Exception as e:
        logger.warning(f"[planner] Live RAG agent failed ({e}) — using mock fallback")
        rag_result = mock_rag(qid, q)

    return {"rag_result": rag_result}


async def assess_risk(state: PlannerState) -> dict:
    """
    Run deterministic risk assessment on collected agent results.

    This is the most important safety guardrail — the verdict comes from
    a rule engine with real thresholds, NEVER from the LLM.
    """
    qid = state["query_run_id"]

    weather = AgentEnvelope(**state["weather_result"])
    marine = AgentEnvelope(**state["marine_result"])
    geo = AgentEnvelope(**state["geofencing_result"])

    # TODO: Replace with Jaish's real RiskAgent.correlate()
    verdict = mock_risk_verdict(qid, weather, marine, geo)

    logger.info(f"[planner] Risk verdict: {verdict.verdict} — {verdict.reasons}")
    return {"risk_verdict": verdict.model_dump(mode="json")}


async def synthesize_response(state: PlannerState) -> dict:
    """
    Use LLM to compose a user-facing response from agent results.

    The LLM explains the data and verdict — it does NOT decide the verdict.
    Also builds GeoJSON map data and evidence trail from envelopes.
    """
    intent = state.get("intent", "unknown")
    verdict_data = state.get("risk_verdict") or {}
    verdict_str = verdict_data.get("verdict", "N/A")

    # ── Build LLM context ─────────────────────────────────────────
    agent_context = {
        "intent": intent,
        "weather": state.get("weather_result", {}),
        "marine_fishing": state.get("marine_result", {}),
        "geofencing": state.get("geofencing_result", {}),
        "rag_advisory": state.get("rag_result", {}),
        "risk_verdict": verdict_data,
    }

    messages = [
        {
            "role": "system",
            "content": SYNTHESIS_SYSTEM_PROMPT.format(verdict=verdict_str),
        },
        {
            "role": "user",
            "content": (
                f"User query: {state['query']}\n\n"
                f"Agent results:\n{json.dumps(agent_context, indent=2, default=str)}"
            ),
        },
    ]

    # ── Generate response text ────────────────────────────────────
    try:
        text = await call_llm("synthesizer", messages, temperature=0.3, max_tokens=1024)
    except Exception as e:
        logger.error(f"[planner] Synthesis LLM failed: {e}")
        text = _fallback_text(state)

    # ── Build structured output ───────────────────────────────────
    return {
        "response": {
            "query_run_id": state["query_run_id"],
            "intent": intent,
            "text": text,
            "map_data": _build_map_data(state),
            "evidence": _build_evidence(state),
            "risk_verdict": verdict_data or None,
            "status": "success",
        }
    }


# ═══════════════════════════════════════════════════════════════════════
# Routing
# ═══════════════════════════════════════════════════════════════════════

def route_by_intent(state: PlannerState) -> str:
    """Decide which dispatch path to take based on classified intent."""
    if state.get("intent") == "regulation_question":
        return "dispatch_rag"
    # safety_check, find_fishing_zone, route_request all need data agents
    return "dispatch_data_agents"


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _build_map_data(state: PlannerState) -> dict:
    """Build a GeoJSON FeatureCollection from agent results."""
    features: list[dict] = []

    # User / query location
    loc = state.get("location", {})
    if loc:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [loc.get("lon", 0), loc.get("lat", 0)],
            },
            "properties": {
                "type": "user_location",
                "name": loc.get("name", "Query location"),
                "icon": "anchor",
            },
        })

    # PFZ zones from marine data
    marine = state.get("marine_result", {})
    for zone in marine.get("data", {}).get("pfz_zones", []):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [zone.get("center_lon", 0), zone.get("center_lat", 0)],
            },
            "properties": {
                "type": "pfz_zone",
                "zone_id": zone.get("zone_id"),
                "name": zone.get("name"),
                "productivity_score": zone.get("productivity_score"),
                "distance_km": zone.get("distance_km"),
                "species": zone.get("species_likely", []),
                "icon": "fish",
            },
        })

    # Nearest MPA from geofencing data
    geo = state.get("geofencing_result", {})
    mpa = geo.get("data", {}).get("nearest_mpa", {})
    if mpa and mpa.get("name"):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    loc.get("lon", 0) - 0.5,  # approximate offset
                    loc.get("lat", 0) - 0.3,
                ],
            },
            "properties": {
                "type": "mpa",
                "name": mpa.get("name"),
                "distance_km": mpa.get("distance_km"),
                "status": mpa.get("status"),
                "icon": "shield",
            },
        })

    return {"type": "FeatureCollection", "features": features}


def _build_evidence(state: PlannerState) -> list[dict]:
    """Compile an evidence trail from all agent envelopes."""
    evidence: list[dict] = []

    for key in ("weather_result", "marine_result", "geofencing_result"):
        result = state.get(key, {})
        # Include both 'success' and 'degraded' — degraded is real live data with
        # a reduced confidence score and should be surfaced to the frontend as such.
        if result and result.get("status") in ("success", "degraded"):
            evidence.append({
                "agent": result.get("agent"),
                "source": result.get("source"),
                "confidence": result.get("confidence"),
                "timestamp": result.get("timestamp"),
                "status": result.get("status"),  # expose degraded status to frontend
            })

    # RAG citations
    rag = state.get("rag_result", {})
    if rag and rag.get("citations"):
        for cite in rag["citations"]:
            evidence.append({
                "agent": "rag_advisory",
                "source": cite.get("source"),
                "confidence": cite.get("relevance_score"),
                "timestamp": None,
            })

    return evidence


def _fallback_text(state: PlannerState) -> str:
    """Generate a basic text response without LLM if synthesis fails."""
    verdict = state.get("risk_verdict", {})
    v = verdict.get("verdict", "UNKNOWN") if verdict else "UNKNOWN"
    reasons = verdict.get("reasons", []) if verdict else []
    return (
        f"Safety assessment: {v}. "
        + " ".join(reasons)
        + " (Note: detailed narrative unavailable due to a temporary issue — "
        "raw data is shown above.)"
    )


# ═══════════════════════════════════════════════════════════════════════
# Build the LangGraph
# ═══════════════════════════════════════════════════════════════════════

def _build_graph():
    builder = StateGraph(PlannerState)

    # ── Nodes ──────────────────────────────────────────────────────
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("dispatch_data_agents", dispatch_data_agents)
    builder.add_node("dispatch_rag", dispatch_rag)
    builder.add_node("assess_risk", assess_risk)
    builder.add_node("synthesize_response", synthesize_response)

    # ── Edges ──────────────────────────────────────────────────────
    builder.add_edge(START, "classify_intent")

    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "dispatch_data_agents": "dispatch_data_agents",
            "dispatch_rag": "dispatch_rag",
        },
    )

    builder.add_edge("dispatch_data_agents", "assess_risk")
    builder.add_edge("assess_risk", "synthesize_response")
    builder.add_edge("dispatch_rag", "synthesize_response")
    builder.add_edge("synthesize_response", END)

    return builder.compile()


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════

class PlannerAgent:
    """
    Entry point for the ORCA orchestration pipeline.

    Usage:
        planner = PlannerAgent()
        result = await planner.handle_query("Is it safe to fish tomorrow near Ratnagiri?")
    """

    def __init__(self):
        self.graph = _build_graph()
        logger.info("[planner] LangGraph compiled — ready to handle queries")

    async def handle_query(
        self,
        query: str,
        conversation_id: str = "",
        user_id: str = "anonymous",
    ) -> dict:
        """
        Process a user query through the full agent pipeline.

        Args:
            query: Natural language question about marine conditions.
            conversation_id: Session ID for multi-turn context (future).
            user_id: User identifier.

        Returns:
            dict matching the ChatResponse schema:
            {query_run_id, intent, text, map_data, evidence, risk_verdict, status}
        """
        query_run_id = str(uuid.uuid4())
        logger.info(f"[planner] New query: {query!r}  (run={query_run_id[:8]}…)")

        try:
            result = await self.graph.ainvoke({
                "query": query,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "query_run_id": query_run_id,
            })

            return result.get("response", {
                "query_run_id": query_run_id,
                "intent": "error",
                "text": "An unexpected error occurred while processing your query.",
                "map_data": None,
                "evidence": None,
                "risk_verdict": None,
                "status": "error",
            })

        except Exception as e:
            logger.error(f"[planner] Pipeline failed: {e}", exc_info=True)
            return {
                "query_run_id": query_run_id,
                "intent": "error",
                "text": f"Sorry, I encountered an error: {e}",
                "map_data": None,
                "evidence": None,
                "risk_verdict": None,
                "status": "error",
            }
