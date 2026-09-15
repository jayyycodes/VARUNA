"""
Unit tests for Vessel-Specific Safety Criteria in RiskAgent.
Tests dynamic scaling across Traditional Craft, Mechanized Trawlers, and Deep-Sea Longliners.
"""

from datetime import datetime, timezone
import pytest

from backend.schemas.envelope import AgentEnvelope
from agents.risk.risk_agent import RiskAgent


def _make_envelopes(wave: float, wind: float):
    now = datetime.now(timezone.utc)
    weather = AgentEnvelope(
        agent="weather_intelligence",
        query_run_id="test-run",
        status="success",
        confidence=0.9,
        source="IMD / Open-Meteo",
        timestamp=now,
        data={"wave_height_m": wave, "wind_speed_kmh": wind},
    )
    marine = AgentEnvelope(
        agent="marine_fishing",
        query_run_id="test-run",
        status="success",
        confidence=0.9,
        source="INCOIS PFZ",
        timestamp=now,
        data={"pfz_zones": []},
    )
    geo = AgentEnvelope(
        agent="geofencing",
        query_run_id="test-run",
        status="success",
        confidence=0.9,
        source="PostGIS",
        timestamp=now,
        data={"status": "clear", "distance_km": 50.0},
    )
    return weather, marine, geo


def test_traditional_craft_wave_scaling():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=1.3, wind=15.0)

    # Traditional craft unsafe limit is 1.2m -> 1.3m is UNSAFE
    trad_res = ra.correlate("t-1", w, m, g, vessel_type="traditional_craft")
    assert trad_res.verdict == "UNSAFE"
    assert "traditional" in trad_res.reasons[0].lower() or "1.3" in trad_res.reasons[0]

    # Mechanized trawler caution limit is 1.5m -> 1.3m is SAFE
    trawl_res = ra.correlate("t-2", w, m, g, vessel_type="mechanized_trawler")
    assert trawl_res.verdict == "SAFE"


def test_mechanized_trawler_vs_longliner_wave_scaling():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=2.8, wind=20.0)

    # Mechanized trawler unsafe limit is 2.5m -> 2.8m is UNSAFE
    trawl_res = ra.correlate("t-3", w, m, g, vessel_type="mechanized_trawler")
    assert trawl_res.verdict == "UNSAFE"

    # Deep-sea longliner unsafe limit is 3.5m, caution is 2.5m -> 2.8m is CAUTION
    long_res = ra.correlate("t-4", w, m, g, vessel_type="deep_sea_longliner")
    assert long_res.verdict == "CAUTION"


def test_deep_sea_longliner_unsafe_threshold():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=3.8, wind=30.0)

    long_res = ra.correlate("t-5", w, m, g, vessel_type="deep_sea_longliner")
    assert long_res.verdict == "UNSAFE"
    assert "deep-sea" in long_res.reasons[0].lower() or "3.8" in long_res.reasons[0]


def test_wind_speed_scaling_traditional_craft():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=0.6, wind=22.0)

    # Traditional craft wind unsafe limit is 20.0 km/h -> 22.0 km/h is UNSAFE
    trad_res = ra.correlate("t-6", w, m, g, vessel_type="country_craft")
    assert trad_res.verdict == "UNSAFE"

    # Mechanized trawler wind caution limit is 25.0 km/h -> 22.0 km/h is SAFE
    trawl_res = ra.correlate("t-7", w, m, g, vessel_type="mechanized_trawler")
    assert trawl_res.verdict == "SAFE"
