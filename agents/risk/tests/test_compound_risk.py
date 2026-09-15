"""
Unit tests for Compound Maritime Risk Modeling in RiskAgent.
Tests beam seas / cross swell, opposing current wave steepening, and shallow shoaling.
"""

from agents.risk.compound_risk import CompoundRiskEngine, CompoundRiskInput, _angular_difference_deg
from agents.risk.risk_agent import RiskAgent
from backend.schemas.envelope import AgentEnvelope
from datetime import datetime, timezone


def test_angular_difference():
    assert _angular_difference_deg(10.0, 350.0) == 20.0
    assert _angular_difference_deg(90.0, 180.0) == 90.0
    assert _angular_difference_deg(0.0, 180.0) == 180.0
    assert _angular_difference_deg(45.0, 45.0) == 0.0


def test_cross_swell_detection():
    # Crossing angle 90 degrees in 1.8m waves -> Beam seas hazard
    inp = CompoundRiskInput(
        wave_height_m=1.8,
        wind_direction_deg=90.0,
        swell_direction_deg=180.0,
    )
    hazards = CompoundRiskEngine.evaluate(inp)
    assert len(hazards) == 1
    assert hazards[0].hazard_code == "COMPOUND_CROSS_SWELL"
    assert hazards[0].severity == "CAUTION"
    assert "Beam Seas" in hazards[0].title


def test_opposing_current_detection():
    # Opposing current (180 deg opposite) at 2.0 knots in 1.5m waves -> Wave steepening
    inp = CompoundRiskInput(
        wave_height_m=1.5,
        wave_direction_deg=90.0,
        current_direction_deg=270.0,
        current_speed_knots=2.0,
    )
    hazards = CompoundRiskEngine.evaluate(inp)
    assert any(h.hazard_code == "COMPOUND_OPPOSING_CURRENT" for h in hazards)
    opp_h = [h for h in hazards if h.hazard_code == "COMPOUND_OPPOSING_CURRENT"][0]
    assert "steepening" in opp_h.description.lower()


def test_shoaling_breaker_hazard():
    # Shallow water 2.5m with 1.8m waves -> Shoaling breaker hazard
    inp = CompoundRiskInput(
        wave_height_m=1.8,
        bathymetric_depth_m=2.5,
    )
    hazards = CompoundRiskEngine.evaluate(inp)
    assert any(h.hazard_code == "COMPOUND_SHOALING_BREAKER" for h in hazards)
    sh_h = [h for h in hazards if h.hazard_code == "COMPOUND_SHOALING_BREAKER"][0]
    assert sh_h.severity == "UNSAFE"


def test_risk_agent_integration_with_compound_risk():
    now = datetime.now(timezone.utc)
    weather = AgentEnvelope(
        agent="weather_intelligence",
        query_run_id="test-compound",
        status="success",
        confidence=0.9,
        source="IMD",
        timestamp=now,
        data={
            "wave_height_m": 1.6,  # Normally safe/borderline for trawler
            "wind_speed_kmh": 20.0,
            "wind_direction_deg": 90.0,
            "swell_direction_deg": 180.0,  # 90 deg crossing angle
        },
    )
    marine = AgentEnvelope(
        agent="marine_fishing",
        query_run_id="test-compound",
        status="success",
        confidence=0.9,
        source="INCOIS",
        timestamp=now,
        data={},
    )
    geo = AgentEnvelope(
        agent="geofencing",
        query_run_id="test-compound",
        status="success",
        confidence=0.9,
        source="PostGIS",
        timestamp=now,
        data={"status": "clear", "distance_km": 60.0},
    )

    ra = RiskAgent()
    res = ra.correlate("c-1", weather, marine, geo, vessel_type="mechanized_trawler")
    assert res.verdict == "CAUTION"
    assert any("beam seas" in r.lower() or "cross swell" in r.lower() for r in res.reasons)
