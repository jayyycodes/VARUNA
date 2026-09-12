"""
Unit tests for Time-to-Shelter Evacuation Estimator.
Tests port of refuge matching, transit durations, and squall interception windows.
"""

from agents.risk.evacuation import EvacuationEngine, EvacuationAssessment
from agents.risk.risk_agent import RiskAgent
from backend.schemas.envelope import AgentEnvelope
from datetime import datetime, timezone


def test_find_nearest_port_ratnagiri():
    # Near Ratnagiri coordinates (17.10N, 73.15E)
    port, dist_km = EvacuationEngine.find_nearest_port(17.10, 73.15)
    assert "Ratnagiri" in port["name"]
    assert dist_km < 30.0


def test_find_nearest_port_veraval():
    # Near Veraval coordinates (20.85N, 70.30E)
    port, dist_km = EvacuationEngine.find_nearest_port(20.85, 70.30)
    assert "Veraval" in port["name"]
    assert dist_km < 25.0


def test_evacuation_feasible_margin():
    # 20km from port at 15.74 km/h -> ~1.27h transit. Squall 70km away at 35 km/h -> 2.0h arrival. Margin > 0.5h
    res = EvacuationEngine.evaluate_evacuation(
        lat=17.10,
        lon=73.20,
        vessel_type="mechanized_trawler",
        squall_distance_km=70.0,
        squall_speed_kmh=35.0,
    )
    assert res.evacuation_feasible is True
    assert res.transit_duration_hours < 2.0
    assert res.safety_margin_hours is not None
    assert res.safety_margin_hours > 0.5


def test_evacuation_intercept_imminent():
    # 40km from port at 9.26 km/h (country craft) -> ~4.3h transit. Squall 35km away at 35 km/h -> 1.0h arrival.
    res = EvacuationEngine.evaluate_evacuation(
        lat=17.30,
        lon=73.10,
        vessel_type="traditional_craft",
        squall_distance_km=35.0,
        squall_speed_kmh=35.0,
    )
    assert res.evacuation_feasible is False
    assert res.evacuation_hazard_code == "EVACUATION_INTERCEPT_IMMINENT"
    assert "CRITICAL" in res.advisory_notes


def test_risk_agent_integration_with_evacuation():
    now = datetime.now(timezone.utc)
    weather = AgentEnvelope(
        agent="weather_intelligence",
        query_run_id="test-evac",
        status="success",
        confidence=0.9,
        source="IMD",
        timestamp=now,
        data={"wave_height_m": 1.0, "wind_speed_kmh": 15.0},
    )
    marine = AgentEnvelope(
        agent="marine_fishing",
        query_run_id="test-evac",
        status="success",
        confidence=0.9,
        source="INCOIS",
        timestamp=now,
        data={},
    )
    geo = AgentEnvelope(
        agent="geofencing",
        query_run_id="test-evac",
        status="success",
        confidence=0.9,
        source="PostGIS",
        timestamp=now,
        data={"status": "clear", "distance_km": 60.0},
    )

    ra = RiskAgent()
    # Imminent squall intercept 25km away approaching at 50 km/h (0.5h arrival) with 40km to port
    res = ra.correlate(
        "e-1", weather, marine, geo,
        latitude=17.30, longitude=73.00,
        vessel_type="traditional_craft",
        squall_distance_km=25.0,
        squall_speed_kmh=50.0,
    )
    assert res.verdict == "UNSAFE"
    assert any("intercept" in r.lower() or "shelter" in r.lower() or "anchorage" in r.lower() for r in res.reasons)
    assert res.rule_trace["evacuation"] is not None
