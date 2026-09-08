"""
Mock agent implementations for Planner development.

These return realistic AgentEnvelope responses with hardcoded data
so the Planner/Orchestrator can be fully built and tested before
real agents (Weather, Marine, Geofencing) are delivered by teammates.

Swap each mock with the real agent import as they become available:
  - mock_weather     → WeatherAgent.get_forecast()         (Cbum)
  - mock_marine      → MarineFishingAgent.get_ocean_state() (Jaish)
  - mock_geofencing  → GeofencingAgent.check_geofence()     (Vedant)
  - mock_risk_verdict → RiskAgent.correlate()               (Jaish)
  - mock_rag         → RAGAdvisoryAgent.answer_with_citations() (Prapti)
"""

from datetime import datetime, timezone
from backend.schemas.envelope import AgentEnvelope, RiskVerdict


# ── Weather Agent Mock ─────────────────────────────────────────────────

def mock_weather(
    query_run_id: str, lat: float, lon: float, date: str
) -> AgentEnvelope:
    """Simulates Open-Meteo / IMD / INCOIS Ocean State Forecast response."""
    return AgentEnvelope(
        agent="weather_intelligence",
        query_run_id=query_run_id,
        status="success",
        data={
            "location": {"lat": lat, "lon": lon},
            "date": date,
            "wind_speed_kmh": 22.5,
            "wind_direction": "SW",
            "wave_height_m": 1.8,
            "swell_period_s": 8.2,
            "temperature_c": 28.3,
            "humidity_pct": 78,
            "rain_probability_pct": 15,
            "lightning_risk": "low",
            "cyclone_alert": None,
            "visibility_km": 12.0,
            "forecast_summary": (
                "Moderate winds from southwest at 22.5 km/h. "
                "Wave height 1.8m — within safe limits for small craft. "
                "No cyclone activity detected. Good visibility."
            ),
        },
        confidence=0.85,
        source="Open-Meteo API + IMD Regional Forecast (mock)",
        timestamp=datetime.now(timezone.utc),
    )


# ── Marine & Fishing Agent Mock ────────────────────────────────────────

def mock_marine(
    query_run_id: str, lat: float, lon: float, date: str
) -> AgentEnvelope:
    """Simulates INCOIS PFZ WebGIS + MOSDAC SST/OCM-3 response."""
    return AgentEnvelope(
        agent="marine_fishing",
        query_run_id=query_run_id,
        status="success",
        data={
            "location": {"lat": lat, "lon": lon},
            "date": date,
            "sst_celsius": 27.6,
            "chlorophyll_mg_m3": 3.2,
            "pfz_zones": [
                {
                    "zone_id": "PFZ-MH-042",
                    "name": "Ratnagiri Offshore Zone A",
                    "center_lat": round(lat + 0.15, 4),
                    "center_lon": round(lon - 0.20, 4),
                    "productivity_score": 0.82,
                    "distance_km": 18.5,
                    "species_likely": ["mackerel", "sardine"],
                },
                {
                    "zone_id": "PFZ-MH-043",
                    "name": "Ratnagiri Offshore Zone B",
                    "center_lat": round(lat + 0.30, 4),
                    "center_lon": round(lon - 0.35, 4),
                    "productivity_score": 0.71,
                    "distance_km": 32.0,
                    "species_likely": ["tuna", "pomfret"],
                },
                {
                    "zone_id": "PFZ-MH-044",
                    "name": "Devgad Coastal Zone",
                    "center_lat": round(lat - 0.10, 4),
                    "center_lon": round(lon - 0.12, 4),
                    "productivity_score": 0.65,
                    "distance_km": 12.8,
                    "species_likely": ["sardine", "prawn"],
                },
            ],
            "ocean_current_direction": "NW",
            "ocean_current_speed_knots": 1.2,
        },
        confidence=0.78,
        source="INCOIS PFZ WebGIS + MOSDAC SST (mock)",
        timestamp=datetime.now(timezone.utc),
    )


# ── Geofencing Agent Mock ──────────────────────────────────────────────

def mock_geofencing(
    query_run_id: str, lat: float, lon: float
) -> AgentEnvelope:
    """Simulates PostGIS EEZ/IMBL/MPA boundary checks."""
    return AgentEnvelope(
        agent="geofencing",
        query_run_id=query_run_id,
        status="success",
        data={
            "location": {"lat": lat, "lon": lon},
            "in_indian_eez": True,
            "distance_to_imbl_km": 145.3,
            "distance_to_eez_boundary_km": 180.7,
            "nearest_mpa": {
                "name": "Malvan Marine Sanctuary",
                "distance_km": 42.1,
                "status": "outside",
            },
            "restricted_zone": False,
            "warnings": [],
        },
        confidence=0.95,
        source="PostGIS EEZ/IMBL/MPA boundaries (mock)",
        timestamp=datetime.now(timezone.utc),
    )


# ── Risk Assessment Mock ──────────────────────────────────────────────
# In production this is Jaish's DETERMINISTIC rule engine.
# The LLM never decides the verdict — only explains it.

def mock_risk_verdict(
    query_run_id: str,
    weather: AgentEnvelope,
    marine: AgentEnvelope,
    geo: AgentEnvelope,
) -> RiskVerdict:
    """
    Simplified deterministic risk assessment.

    Thresholds (source: INCOIS/IMD small-craft advisories):
      - Wave height > 2.5 m  → UNSAFE
      - Wave height > 1.5 m  → CAUTION
      - Wind speed > 40 km/h → UNSAFE
      - Wind speed > 25 km/h → CAUTION
      - Lightning high/severe → UNSAFE
      - Restricted zone       → UNSAFE
    """
    wave = weather.data.get("wave_height_m", 0)
    wind = weather.data.get("wind_speed_kmh", 0)
    lightning = weather.data.get("lightning_risk", "none")
    cyclone = weather.data.get("cyclone_alert")
    restricted = geo.data.get("restricted_zone", False)

    reasons: list[str] = []
    verdict = "SAFE"

    # ── Wave height ────────────────────────────────────────────────
    if wave > 2.5:
        verdict = "UNSAFE"
        reasons.append(f"Wave height {wave}m exceeds 2.5m small-craft threshold")
    elif wave > 1.5:
        if verdict != "UNSAFE":
            verdict = "CAUTION"
        reasons.append(f"Wave height {wave}m — moderate, exercise caution")

    # ── Wind speed ─────────────────────────────────────────────────
    if wind > 40:
        verdict = "UNSAFE"
        reasons.append(f"Wind speed {wind} km/h exceeds 40 km/h safe limit")
    elif wind > 25:
        if verdict != "UNSAFE":
            verdict = "CAUTION"
        reasons.append(f"Wind speed {wind} km/h — moderately strong")

    # ── Lightning ──────────────────────────────────────────────────
    if lightning in ("high", "severe"):
        verdict = "UNSAFE"
        reasons.append(f"Lightning risk is {lightning}")

    # ── Cyclone ────────────────────────────────────────────────────
    if cyclone:
        verdict = "UNSAFE"
        reasons.append(f"Active cyclone alert: {cyclone}")

    # ── Geofencing ─────────────────────────────────────────────────
    if restricted:
        verdict = "UNSAFE"
        reasons.append("Location is in a restricted maritime zone")

    if not reasons:
        reasons.append("All conditions within safe thresholds")

    return RiskVerdict(
        query_run_id=query_run_id,
        verdict=verdict,
        reasons=reasons,
        rule_trace={
            "inputs": {
                "wave_height_m": wave,
                "wind_speed_kmh": wind,
                "lightning_risk": lightning,
                "cyclone_alert": cyclone,
                "restricted_zone": restricted,
            },
            "thresholds": {
                "wave_unsafe_m": 2.5,
                "wave_caution_m": 1.5,
                "wind_unsafe_kmh": 40,
                "wind_caution_kmh": 25,
                "lightning_unsafe": ["high", "severe"],
            },
            "computed_verdict": verdict,
        },
        created_at=datetime.now(timezone.utc),
    )


# ── RAG / Advisory Mock ───────────────────────────────────────────────

def mock_rag(query_run_id: str, question: str) -> dict:
    """Simulates vector DB retrieval + grounded answer generation."""
    return {
        "agent": "rag_advisory",
        "query_run_id": query_run_id,
        "answer": (
            "According to the Maharashtra Marine Fishing Regulation Act (MFRA) 1981, "
            "mechanized fishing vessels are prohibited from operating within 5 nautical "
            "miles of the coast. The annual monsoon fishing ban typically runs from "
            "June 1 to July 31 along the west coast of India. During this period, "
            "all mechanized boats are required to stay in harbour."
        ),
        "citations": [
            {
                "source": "Maharashtra MFRA 1981, Section 4",
                "chunk": (
                    "No mechanized fishing vessel shall engage in fishing within "
                    "the territorial waters measured from the appropriate baseline "
                    "up to the distance of five nautical miles..."
                ),
                "relevance_score": 0.92,
            },
            {
                "source": "DAHDF Notification — Annual Monsoon Ban",
                "chunk": (
                    "Fishing by mechanized vessels banned from 1st June to 31st July "
                    "on the west coast and 15th April to 14th June on the east coast."
                ),
                "relevance_score": 0.87,
            },
        ],
        "confidence": 0.88,
        "source": "Vector DB — MFRA + DAHDF advisories (mock)",
    }
