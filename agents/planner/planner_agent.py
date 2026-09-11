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
    prior_location: dict[str, Any] | None
    prior_destination: dict[str, Any] | None
    detected_language: str

    # ── After intent classification ────────────────────────────────
    intent: str                         # safety_check | find_fishing_zone | route_request | regulation_question
    location: dict[str, Any]            # {"lat": float, "lon": float, "name": str}
    destination: dict[str, Any] | None  # optional {"lat": float, "lon": float, "name": str} for routing
    date: str                           # ISO date YYYY-MM-DD

    # ── Agent results (serialized envelopes) ───────────────────────
    weather_result: dict[str, Any]
    marine_result: dict[str, Any]
    geofencing_result: dict[str, Any]
    route_result: dict[str, Any]
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
6. If route navigation data is available, provide the recommended compass heading, nautical distance (NM), estimated travel time (hours), and fuel required (liters).
7. Be concise and practical — your audience is working fishermen, not academics.
8. End with one clear, actionable recommendation.

Write the response as plain text paragraphs. No markdown headers or bullet points."""


# ── Verified Indian Coastal Ports Gazetteer ─────────────────────────────
INDIAN_COASTAL_PORTS: dict[str, dict[str, Any]] = {
    # Maharashtra / Konkan
    "ratnagiri": {"lat": 16.99, "lon": 73.30, "name": "Ratnagiri, Maharashtra"},
    "malvan": {"lat": 16.05, "lon": 73.47, "name": "Malvan, Sindhudurg, Maharashtra"},
    "mumbai": {"lat": 18.94, "lon": 72.83, "name": "Mumbai, Maharashtra"},
    "sassoon": {"lat": 18.91, "lon": 72.82, "name": "Sassoon Dock, Mumbai, Maharashtra"},
    "bhaucha dhakka": {"lat": 18.96, "lon": 72.85, "name": "Ferry Wharf, Mumbai, Maharashtra"},
    "alibaug": {"lat": 18.64, "lon": 72.87, "name": "Alibaug, Maharashtra"},
    "dahanu": {"lat": 19.97, "lon": 72.73, "name": "Dahanu, Maharashtra"},
    # Gujarat
    "veraval": {"lat": 20.90, "lon": 70.37, "name": "Veraval, Gujarat"},
    "porbandar": {"lat": 21.64, "lon": 69.60, "name": "Porbandar, Gujarat"},
    "okha": {"lat": 22.47, "lon": 69.07, "name": "Okha, Gujarat"},
    "mangrol": {"lat": 21.12, "lon": 70.12, "name": "Mangrol, Gujarat"},
    "jakhau": {"lat": 23.23, "lon": 68.70, "name": "Jakhau, Kutch, Gujarat"},
    # Goa & Karnataka
    "mormugao": {"lat": 15.42, "lon": 73.80, "name": "Mormugao, Goa"},
    "goa": {"lat": 15.42, "lon": 73.80, "name": "Goa Coastal Waters"},
    "panaji": {"lat": 15.50, "lon": 73.83, "name": "Panaji, Goa"},
    "karwar": {"lat": 14.81, "lon": 74.13, "name": "Karwar, Karnataka"},
    "mangalore": {"lat": 12.87, "lon": 74.84, "name": "Mangalore, Karnataka"},
    "malpe": {"lat": 13.35, "lon": 74.70, "name": "Malpe, Udupi, Karnataka"},
    # Kerala
    "kochi": {"lat": 9.93, "lon": 76.26, "name": "Kochi, Kerala"},
    "cochin": {"lat": 9.93, "lon": 76.26, "name": "Cochin, Kerala"},
    "munambam": {"lat": 10.18, "lon": 76.17, "name": "Munambam, Kerala"},
    "kollam": {"lat": 8.88, "lon": 76.59, "name": "Kollam, Kerala"},
    "vizhinjam": {"lat": 8.38, "lon": 76.99, "name": "Vizhinjam, Kerala"},
    "beypore": {"lat": 11.16, "lon": 75.80, "name": "Beypore, Kozhikode, Kerala"},
    # Tamil Nadu & Puducherry
    "tuticorin": {"lat": 8.76, "lon": 78.13, "name": "Thoothukudi / Tuticorin, Tamil Nadu"},
    "thoothukudi": {"lat": 8.76, "lon": 78.13, "name": "Thoothukudi, Tamil Nadu"},
    "rameshwaram": {"lat": 9.28, "lon": 79.31, "name": "Rameshwaram, Tamil Nadu"},
    "nagapattinam": {"lat": 10.77, "lon": 79.84, "name": "Nagapattinam, Tamil Nadu"},
    "cuddalore": {"lat": 11.75, "lon": 79.77, "name": "Cuddalore, Tamil Nadu"},
    "chennai": {"lat": 13.08, "lon": 80.27, "name": "Chennai (Kasimedu), Tamil Nadu"},
    "kasimedu": {"lat": 13.12, "lon": 80.29, "name": "Kasimedu Fishing Harbour, Chennai"},
    # Andhra Pradesh & Odisha & West Bengal
    "visakhapatnam": {"lat": 17.69, "lon": 83.22, "name": "Visakhapatnam, Andhra Pradesh"},
    "vizag": {"lat": 17.69, "lon": 83.22, "name": "Visakhapatnam, Andhra Pradesh"},
    "kakinada": {"lat": 16.99, "lon": 82.25, "name": "Kakinada, Andhra Pradesh"},
    "machilipatnam": {"lat": 16.18, "lon": 81.14, "name": "Machilipatnam, Andhra Pradesh"},
    "paradeep": {"lat": 20.32, "lon": 86.61, "name": "Paradeep, Odisha"},
    "dhamra": {"lat": 20.80, "lon": 86.97, "name": "Dhamra, Odisha"},
    "digha": {"lat": 21.63, "lon": 87.52, "name": "Digha, West Bengal"},
    "kakdwip": {"lat": 21.87, "lon": 88.18, "name": "Kakdwip, West Bengal"},
}


def resolve_port_location(query: str, extracted_loc: dict[str, Any] | None) -> dict[str, Any]:
    """
    Deterministically resolve coordinates from query text or extracted name
    against the verified Indian Coastal Port Gazetteer, eliminating LLM coordinate hallucination.
    """
    normalized_q = query.lower()
    extracted_name = (extracted_loc.get("name") or "").lower() if extracted_loc else ""

    # Check extracted name first, then words in raw query
    for port_key, port_info in INDIAN_COASTAL_PORTS.items():
        if port_key in extracted_name or port_key in normalized_q:
            return {
                "lat": port_info["lat"],
                "lon": port_info["lon"],
                "name": port_info["name"],
            }

    # Fallback to LLM extraction if coordinates are within the Indian maritime bounding envelope
    if extracted_loc and isinstance(extracted_loc.get("lat"), (int, float)) and isinstance(extracted_loc.get("lon"), (int, float)):
        lat = float(extracted_loc["lat"])
        lon = float(extracted_loc["lon"])
        if 4.0 <= lat <= 26.0 and 65.0 <= lon <= 95.0:
            return {
                "lat": lat,
                "lon": lon,
                "name": extracted_loc.get("name") or f"Location ({lat:.2f}N, {lon:.2f}E)",
            }

    return {"lat": 16.99, "lon": 73.30, "name": "Ratnagiri, Maharashtra (default)"}


def extract_route_endpoints(
    query: str,
    parsed: dict | None = None,
    prior_location: dict[str, Any] | None = None,
    prior_destination: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """
    Extracts departure and destination locations for routing.
    Detects patterns like 'from PortA to PortB' or multiple ports in query.
    Falls back to prior session location for multi-turn queries.
    """
    q_lower = query.lower()
    ports_found = [p for p in INDIAN_COASTAL_PORTS if p in q_lower]

    if len(ports_found) >= 2:
        # Check order of appearance in string
        p1, p2 = ports_found[0], ports_found[1]
        pos1 = q_lower.find(p1)
        pos2 = q_lower.find(p2)
        start_key = p1 if pos1 < pos2 else p2
        dest_key = p2 if pos1 < pos2 else p1
        start = INDIAN_COASTAL_PORTS[start_key]
        dest = INDIAN_COASTAL_PORTS[dest_key]
        return start, dest

    # Single port in routing query with prior location context
    if len(ports_found) == 1:
        port = INDIAN_COASTAL_PORTS[ports_found[0]]
        # If query asks "to <port>" or "route to <port>" and we have prior location
        if prior_location and any(kw in q_lower for kw in ["to ", "reach ", "route "]):
            return prior_location, port
        return port, None

    # No explicit port in query — check prior location for follow-up questions
    if prior_location and any(kw in q_lower for kw in ["there", "here", "tomorrow", "this", "safe", "weather", "route"]):
        return prior_location, prior_destination

    # Check if destination explicitly parsed by LLM
    if parsed and parsed.get("destination"):
        raw_dest = parsed["destination"]
        dest = resolve_port_location(raw_dest.get("name", ""), raw_dest)
        start = resolve_port_location(query, parsed.get("location"))
        return start, dest

    start = resolve_port_location(query, parsed.get("location") if parsed else None)
    return start, None


# ═══════════════════════════════════════════════════════════════════════
# Graph nodes
# ═══════════════════════════════════════════════════════════════════════

async def classify_intent(state: PlannerState) -> dict:
    """Use LLM structured output to parse intent, location, destination, and date."""
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
        location, destination = extract_route_endpoints(
            state["query"],
            parsed,
            prior_location=state.get("prior_location"),
            prior_destination=state.get("prior_destination"),
        )
        query_date = parsed.get("date", tomorrow_str)

        logger.info(
            f"[planner] Intent: {intent} | "
            f"Location: {location.get('name')} ({location.get('lat')}, {location.get('lon')}) | "
            f"Destination: {destination.get('name') if destination else 'None'} | "
            f"Date: {query_date}"
        )
        return {"intent": intent, "location": location, "destination": destination, "date": query_date}

    except Exception as e:
        logger.error(f"[planner] Intent classification failed: {e} — using defaults")
        location, destination = extract_route_endpoints(
            state["query"],
            None,
            prior_location=state.get("prior_location"),
            prior_destination=state.get("prior_destination"),
        )
        return {
            "intent": "safety_check",
            "location": location,
            "destination": destination,
            "date": tomorrow_str,
        }


async def dispatch_data_agents(state: PlannerState) -> dict:
    """
    Call Weather + Marine + Geofencing agents in parallel.

    Weather is LIVE (Cbum's WeatherAgent — Open-Meteo).
    Marine is LIVE (Jaish's MarineFishingAgent — NOAA ERDDAP + INCOIS WFS).
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

    async def _get_marine() -> AgentEnvelope:
        """Call Jaish's LIVE MarineFishingAgent; fall back to mock on any failure."""
        try:
            from agents.marine_fishing.marine_agent import MarineFishingAgent
            result = await MarineFishingAgent().get_ocean_state(
                lat=lat, lon=lon, date_str=d, query_run_id=qid
            )
            if result.status == "error":
                logger.warning(
                    f"[planner] Live Marine returned error ({result.error_message}) — using mock fallback"
                )
                return mock_marine(qid, lat, lon, d)
            logger.info(
                f"[planner] Live Marine OK ({result.status}) — "
                f"{len(result.data.get('pfz_zones', []))} zones"
            )
            return result
        except Exception as exc:
            logger.warning(f"[planner] MarineFishingAgent import/call failed: {exc} — using mock fallback")
            return mock_marine(qid, lat, lon, d)

    # Dispatch Weather + Marine + Geofencing in parallel
    weather, marine, geo = await asyncio.gather(_get_weather(), _get_marine(), _get_geofencing())

    # 4. Route Navigation Planning
    route_result = None
    start_lat = lat
    start_lon = lon
    dest_info = state.get("destination")
    intent = state.get("intent", "")

    dest_lat: float | None = None
    dest_lon: float | None = None

    if dest_info:
        dest_lat = float(dest_info["lat"])
        dest_lon = float(dest_info["lon"])
    elif marine and hasattr(marine, "data") and marine.data.get("pfz_zones"):
        top_zone = marine.data["pfz_zones"][0]
        if "coordinates" in top_zone and isinstance(top_zone["coordinates"], (list, tuple)):
            dest_lon, dest_lat = float(top_zone["coordinates"][0]), float(top_zone["coordinates"][1])
        elif "latitude" in top_zone and "longitude" in top_zone:
            dest_lat, dest_lon = float(top_zone["latitude"]), float(top_zone["longitude"])
    elif intent == "route_request":
        # Default transit 15 NM offshore from departure port
        dest_lat = start_lat - 0.15
        dest_lon = start_lon - 0.15

    if dest_lat is not None and dest_lon is not None and (intent in ("route_request", "find_fishing_zone") or dest_info is not None):
        try:
            from agents.route.route_agent import RouteAgent
            r_agent = RouteAgent()
            r_env = await r_agent.plan_route(
                start_lat=start_lat,
                start_lon=start_lon,
                dest_lat=dest_lat,
                dest_lon=dest_lon,
                query_run_id=qid,
            )
            route_result = r_env.model_dump(mode="json")
            logger.info(
                f"[planner] RouteAgent OK ({r_env.status}) — "
                f"{route_result['data'].get('distance_nm')} NM | "
                f"Heading: {route_result['data'].get('cardinal_direction')} ({route_result['data'].get('initial_bearing_degrees')}°)"
            )
        except Exception as exc:
            logger.warning(f"[planner] RouteAgent call failed: {exc}")

    logger.info(
        f"[planner] Dispatched data agents — "
        f"Weather: {weather.status} (LIVE), Marine: {marine.status} (LIVE), "
        f"Geofencing: {geo.status} (LIVE), Route: {'computed' if route_result else 'none'}"
    )

    return {
        "weather_result": weather.model_dump(mode="json"),
        "marine_result": marine.model_dump(mode="json"),
        "geofencing_result": geo.model_dump(mode="json"),
        "route_result": route_result,
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

    try:
        from agents.risk.risk_agent import RiskAgent
        verdict = RiskAgent().correlate(qid, weather, marine, geo)
    except Exception as exc:
        logger.warning(f"[planner] RiskAgent correlate failed: {exc} — using mock fallback")
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
        "departure_location": state.get("location"),
        "destination_location": state.get("destination"),
        "weather": state.get("weather_result", {}),
        "marine_fishing": state.get("marine_result", {}),
        "geofencing": state.get("geofencing_result", {}),
        "route_navigation": state.get("route_result", {}),
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

    # Destination location
    dest = state.get("destination")
    if dest and dest.get("lat") and dest.get("lon"):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [dest.get("lon", 0), dest.get("lat", 0)],
            },
            "properties": {
                "type": "destination_location",
                "name": dest.get("name", "Destination"),
                "icon": "flag",
            },
        })

    # Route navigation LineString features (Safe Corridor + Direct Baseline)
    route = state.get("route_result", {})
    if route:
        r_data = route.get("data", {})
        if r_data.get("route_feature"):
            features.append(r_data["route_feature"])
        if r_data.get("route_direct_feature"):
            features.append(r_data["route_direct_feature"])

    return {"type": "FeatureCollection", "features": features}


def _build_evidence(state: PlannerState) -> list[dict]:
    """Compile an evidence trail from all agent envelopes."""
    evidence: list[dict] = []

    for key in ("weather_result", "marine_result", "geofencing_result", "route_result"):
        result = state.get(key, {})
        # Include both 'success' and 'degraded' — degraded is real live data with
        # a reduced confidence score and should be surfaced to the frontend as such.
        if result and result.get("status") in ("success", "degraded"):
            ev_entry = {
                "agent": result.get("agent"),
                "source": result.get("source"),
                "confidence": result.get("confidence"),
                "timestamp": result.get("timestamp"),
                "status": result.get("status"),  # expose degraded status to frontend
            }
            if result.get("agent") == "route":
                r_data = result.get("data", {})
                ev_entry["distance_nm"] = r_data.get("distance_nm")
                ev_entry["estimated_time_hours"] = r_data.get("estimated_time_hours")
                ev_entry["fuel_liters"] = r_data.get("fuel_estimate_liters")
                if "comparison" in r_data:
                    ev_entry["comparison"] = r_data["comparison"]
            evidence.append(ev_entry)

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
        self.sessions: dict[str, dict[str, Any]] = {}
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
            conversation_id: Session ID for multi-turn context.
            user_id: User identifier.

        Returns:
            dict matching the ChatResponse schema:
            {query_run_id, intent, text, map_data, evidence, risk_verdict, status}
        """
        query_run_id = str(uuid.uuid4())
        cid = conversation_id or "default_session"

        # 1. Retrieve prior session context for multi-turn continuity
        prior_context = self.sessions.get(cid, {})
        prior_loc = prior_context.get("location")
        prior_dest = prior_context.get("destination")

        # 2. Multilingual translation & language detection
        from backend.gateway.multilingual import translate_in, translate_out
        clean_query, detected_lang = await translate_in(query)

        logger.info(
            f"[planner] Query: {query!r} (lang={detected_lang}, en={clean_query!r}, run={query_run_id[:8]}…)"
        )

        try:
            result = await self.graph.ainvoke({
                "query": clean_query,
                "conversation_id": cid,
                "user_id": user_id,
                "query_run_id": query_run_id,
                "prior_location": prior_loc,
                "prior_destination": prior_dest,
                "detected_language": detected_lang,
            })

            resp = result.get("response", {
                "query_run_id": query_run_id,
                "intent": "error",
                "text": "An unexpected error occurred while processing your query.",
                "map_data": None,
                "evidence": None,
                "risk_verdict": None,
                "status": "error",
            })

            # 3. Save updated session state
            final_loc = result.get("location") or prior_loc
            final_dest = result.get("destination") or prior_dest
            self.sessions[cid] = {
                "location": final_loc,
                "destination": final_dest,
                "last_query": clean_query,
                "last_intent": result.get("intent"),
                "last_verdict": result.get("risk_verdict", {}).get("verdict"),
                "route": result.get("route_result"),
            }

            # 4. Outbound localized translation if needed
            if detected_lang != "en" and resp.get("text"):
                resp["text"] = await translate_out(resp["text"], detected_lang)
                resp["detected_language"] = detected_lang

            return resp

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
