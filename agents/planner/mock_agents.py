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


# ── Coastal Hubs & MPA Catalog for Dynamic Synthesis ───────────────────

import math

COASTAL_HUBS = [
    {"name": "Ratnagiri", "lat": 16.99, "lon": 73.30, "state": "Maharashtra"},
    {"name": "Malvan", "lat": 16.05, "lon": 73.47, "state": "Maharashtra"},
    {"name": "Mumbai", "lat": 18.94, "lon": 72.83, "state": "Maharashtra"},
    {"name": "Veraval", "lat": 20.90, "lon": 70.37, "state": "Gujarat"},
    {"name": "Porbandar", "lat": 21.64, "lon": 69.60, "state": "Gujarat"},
    {"name": "Goa", "lat": 15.42, "lon": 73.80, "state": "Goa"},
    {"name": "Karwar", "lat": 14.81, "lon": 74.13, "state": "Karnataka"},
    {"name": "Mangalore", "lat": 12.87, "lon": 74.84, "state": "Karnataka"},
    {"name": "Kochi", "lat": 9.93, "lon": 76.26, "state": "Kerala"},
    {"name": "Kollam", "lat": 8.88, "lon": 76.59, "state": "Kerala"},
    {"name": "Vizhinjam", "lat": 8.38, "lon": 76.99, "state": "Kerala"},
    {"name": "Thoothukudi", "lat": 8.76, "lon": 78.13, "state": "Tamil Nadu"},
    {"name": "Rameshwaram", "lat": 9.28, "lon": 79.31, "state": "Tamil Nadu"},
    {"name": "Chennai", "lat": 13.08, "lon": 80.27, "state": "Tamil Nadu"},
    {"name": "Visakhapatnam", "lat": 17.69, "lon": 83.22, "state": "Andhra Pradesh"},
    {"name": "Kakinada", "lat": 16.99, "lon": 82.25, "state": "Andhra Pradesh"},
    {"name": "Paradeep", "lat": 20.32, "lon": 86.61, "state": "Odisha"},
    {"name": "Digha", "lat": 21.63, "lon": 87.52, "state": "West Bengal"},
]

MAJOR_INDIAN_MPAS = [
    {"name": "Malvan Marine Sanctuary", "lat": 16.05, "lon": 73.47, "state": "Maharashtra"},
    {"name": "Gulf of Kutch Marine National Park", "lat": 22.45, "lon": 69.50, "state": "Gujarat"},
    {"name": "Gulf of Mannar Marine National Park", "lat": 9.15, "lon": 79.05, "state": "Tamil Nadu"},
    {"name": "Gahirmatha Marine Sanctuary", "lat": 20.70, "lon": 87.05, "state": "Odisha"},
    {"name": "Pulicat Lake Bird & Marine Sanctuary", "lat": 13.60, "lon": 80.20, "state": "Tamil Nadu / AP"},
    {"name": "Netrani Island Biodiversity Zone", "lat": 14.02, "lon": 74.33, "state": "Karnataka"},
    {"name": "Sundarbans Marine Biosphere Buffer", "lat": 21.75, "lon": 88.85, "state": "West Bengal"},
    {"name": "Sir Creek International Maritime Boundary (IMBL)", "lat": 23.70, "lon": 68.15, "state": "Gujarat / Pakistan"},
    {"name": "Palk Bay International Maritime Boundary (IMBL)", "lat": 9.25, "lon": 79.50, "state": "Tamil Nadu / Sri Lanka"},
]

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Marine & Fishing Agent Mock ────────────────────────────────────────

def mock_marine(
    query_run_id: str, lat: float, lon: float, date: str
) -> AgentEnvelope:
    """Simulates INCOIS PFZ WebGIS + MOSDAC SST/OCM-3 response dynamically for any Indian coastal coordinate."""
    nearest_hub = min(COASTAL_HUBS, key=lambda h: haversine_km(lat, lon, h["lat"], h["lon"]))
    hub_name = nearest_hub["name"]
    code_hash = abs(hash(f"{lat:.2f},{lon:.2f}")) % 900 + 100

    # West Coast (Arabian Sea): seaward is WEST (negative lon)
    # East Coast (Bay of Bengal): seaward is EAST (positive lon)
    lon_dir = -1.0 if lon < 78.5 else 1.0

    return AgentEnvelope(
        agent="marine_fishing",
        query_run_id=query_run_id,
        status="success",
        data={
            "location": {"lat": lat, "lon": lon},
            "date": date,
            "sst_celsius": 28.2,
            "chlorophyll_mg_m3": 0.68,
            "pfz_zones": [
                {
                    "zone_id": f"PFZ-IND-{code_hash}-C",
                    "name": f"{hub_name} Nearshore Bank",
                    "center_lat": round(lat + 0.04, 4),
                    "center_lon": round(lon + (lon_dir * 0.10), 4),
                    "productivity_score": 0.704,
                    "distance_km": 12.0,
                    "species_likely": ["prawn", "croaker", "sole"],
                    "depth": "19.4m",
                    "sst_c": 28.6,
                    "chlorophyll": 0.58,
                },
                {
                    "zone_id": f"PFZ-IND-{code_hash}-A",
                    "name": f"{hub_name} Offshore Sector Alpha",
                    "center_lat": round(lat + 0.08, 4),
                    "center_lon": round(lon + (lon_dir * 0.18), 4),
                    "productivity_score": 0.710,
                    "distance_km": 21.1,
                    "species_likely": ["mackerel", "sardine", "anchovy"],
                    "depth": "48.2m",
                    "sst_c": 28.4,
                    "chlorophyll": 0.72,
                },
                {
                    "zone_id": f"PFZ-IND-{code_hash}-B",
                    "name": f"{hub_name} Continental Shelf-break",
                    "center_lat": round(lat + 0.12, 4),
                    "center_lon": round(lon + (lon_dir * 0.30), 4),
                    "productivity_score": 0.655,
                    "distance_km": 33.5,
                    "species_likely": ["tuna", "pomfret", "ribbonfish"],
                    "depth": "114.0m",
                    "sst_c": 27.8,
                    "chlorophyll": 0.65,
                },
            ],
            "ocean_current_direction": "NW" if lon < 78.5 else "NE",
            "ocean_current_speed_knots": 1.2,
        },
        confidence=0.82,
        source="INCOIS PFZ WebGIS + MOSDAC SST",
        timestamp=datetime.now(timezone.utc),
    )


# ── Geofencing Agent Mock ──────────────────────────────────────────────

def mock_geofencing(
    query_run_id: str, lat: float, lon: float
) -> AgentEnvelope:
    """Simulates PostGIS EEZ/IMBL/MPA boundary checks with true geodesic distances across all Indian waters."""
    nearest_mpa = min(MAJOR_INDIAN_MPAS, key=lambda m: haversine_km(lat, lon, m["lat"], m["lon"]))
    dist_mpa = round(haversine_km(lat, lon, nearest_mpa["lat"], nearest_mpa["lon"]), 1)

    dist_sir_creek = round(haversine_km(lat, lon, 23.70, 68.15), 1)
    dist_palk_bay = round(haversine_km(lat, lon, 9.25, 79.50), 1)
    dist_imbl = min(dist_sir_creek, dist_palk_bay)

    is_restricted = (dist_mpa < 2.0) or (dist_imbl < 5.0)
    status = "restricted" if is_restricted else ("warning" if (dist_mpa < 15.0 or dist_imbl < 20.0) else "outside")

    warnings = []
    if dist_imbl < 20.0:
        warnings.append(f"Caution: Operating within {dist_imbl} km of International Maritime Boundary Line (IMBL).")
    if dist_mpa < 15.0:
        warnings.append(f"Environmental Alert: Operating within {dist_mpa} km buffer of {nearest_mpa['name']}.")

    return AgentEnvelope(
        agent="geofencing",
        query_run_id=query_run_id,
        status="success",
        data={
            "location": {"lat": lat, "lon": lon},
            "in_indian_eez": True,
            "distance_to_imbl_km": dist_imbl,
            "distance_to_eez_boundary_km": round(min(dist_imbl, 200.0), 1),
            "nearest_boundary_name": nearest_mpa["name"],
            "distance_km": dist_mpa,
            "nearest_mpa": {
                "name": nearest_mpa["name"],
                "lat": nearest_mpa["lat"],
                "lon": nearest_mpa["lon"],
                "distance_km": dist_mpa,
                "status": status,
            },
            "restricted_zone": is_restricted,
            "warnings": warnings,
        },
        confidence=0.98,
        source="PostGIS EEZ/IMBL/MPA boundaries",
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
    geo_status = geo.data.get("status")
    restricted = geo.data.get("restricted_zone", False) or (geo_status == "restricted")
    geo_warning = (geo_status == "warning")
    boundary = geo.data.get("nearest_boundary_name") or "restricted maritime zone"

    if restricted:
        verdict = "UNSAFE"
        reasons.append(f"Location is inside restricted maritime zone ({boundary})")
    elif geo_warning:
        if verdict != "UNSAFE":
            verdict = "CAUTION"
        dist = geo.data.get("distance_km", 0)
        reasons.append(f"Vessel is close ({dist:.1f}km) to maritime boundary ({boundary})")

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
    """Simulates vector DB retrieval + grounded answer generation using the 9-state statutory corpus."""
    import re
    try:
        from agents.rag_advisory.rag_agent import CORPUS
    except Exception:
        CORPUS = []

    q_lower = question.lower()

    # Score each chunk in CORPUS based on keyword match and exact term occurrences
    scored = []
    for item in CORPUS:
        score = 0
        keywords = item.get("keywords", [])
        for kw in keywords:
            if kw.lower() in q_lower:
                score += 3
        # Additional lexical overlap
        chunk_words = set(re.findall(r"\w+", item.get("chunk", "").lower()))
        query_words = set(re.findall(r"\w+", q_lower))
        overlap = len(chunk_words & query_words)
        score += overlap

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    if scored:
        top_items = [item for _, item in scored[:2]]
    else:
        # Fallback to central ban or general regulations
        top_items = [
            item for item in CORPUS
            if "monsoon ban" in item.get("source", "").lower() or "section 4" in item.get("source", "").lower()
        ][:2]
        if not top_items and CORPUS:
            top_items = CORPUS[:2]

    citations = []
    for idx, it in enumerate(top_items):
        citations.append({
            "source": it.get("source", "Official Gazette"),
            "chunk": it.get("chunk", ""),
            "relevance_score": round(max(0.82, 0.95 - idx * 0.05), 2),
        })

    primary_chunk = top_items[0].get("chunk", "") if top_items else "Maritime regulatory guidelines apply."
    source_name = top_items[0].get("source", "State Marine Fishing Regulation Act") if top_items else "Gazette"
    answer = f"According to {source_name}: {primary_chunk}"

    return {
        "agent": "rag_advisory",
        "query_run_id": query_run_id,
        "answer": answer,
        "citations": citations,
        "confidence": 0.92,
        "source": "Vector DB — 9-State MFRA & Central Notifications",
    }
