"""
Unit tests for RiskAgent (agents/risk/risk_agent.py).

Verifies deterministic threshold evaluations based on official INCOIS OSF
small-craft guidelines and IMD advisories.
"""

from datetime import datetime, timezone

import pytest

from backend.schemas.envelope import AgentEnvelope, RiskVerdict
from agents.risk.risk_agent import RiskAgent


def _make_envelopes(
    wave: float = 1.0,
    wind: float = 18.0,
    lightning: str = "none",
    cyclone: str | None = None,
    geo_status: str = "clear",
    geo_dist: float = 50.0,
    boundary_name: str = "Indian EEZ Outer Boundary",
) -> tuple[AgentEnvelope, AgentEnvelope, AgentEnvelope]:
    now = datetime.now(timezone.utc)
    weather = AgentEnvelope(
        agent="weather_intelligence",
        query_run_id="test-run",
        status="success",
        confidence=0.9,
        source="IMD / Open-Meteo",
        timestamp=now,
        data={
            "wave_height_m": wave,
            "wind_speed_kmh": wind,
            "lightning_risk": lightning,
            "cyclone_alert": cyclone,
        },
    )
    marine = AgentEnvelope(
        agent="marine_fishing",
        query_run_id="test-run",
        status="success",
        confidence=0.9,
        source="INCOIS PFZ",
        timestamp=now,
        data={"pfz_zones": [{"zone_id": "PFZ-1"}]},
    )
    geo = AgentEnvelope(
        agent="geofencing",
        query_run_id="test-run",
        status="success",
        confidence=0.9,
        source="PostGIS",
        timestamp=now,
        data={
            "status": geo_status,
            "distance_km": geo_dist,
            "nearest_boundary_name": boundary_name,
        },
    )
    return weather, marine, geo


def test_risk_all_clear_safe():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=0.8, wind=15.0, lightning="none", cyclone=None, geo_status="clear")
    res = ra.correlate("run-safe", w, m, g)
    assert res.verdict == "SAFE"
    assert "safe operational limits" in res.reasons[0].lower()
    assert res.rule_trace["computed_verdict"] == "SAFE"


def test_risk_wave_caution():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=1.8)
    res = ra.correlate("run-caution", w, m, g)
    assert res.verdict == "CAUTION"
    assert any("wave" in r.lower() and "1.8" in r for r in res.reasons)


def test_risk_wave_unsafe():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=2.8)
    res = ra.correlate("run-unsafe", w, m, g)
    assert res.verdict == "UNSAFE"
    assert any("2.8" in r and "exceeds" in r for r in res.reasons)


def test_risk_wind_caution():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wind=32.0)
    res = ra.correlate("run-caution", w, m, g)
    assert res.verdict == "CAUTION"
    assert any("wind" in r.lower() and "32" in r for r in res.reasons)


def test_risk_wind_unsafe():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wind=45.0)
    res = ra.correlate("run-unsafe", w, m, g)
    assert res.verdict == "UNSAFE"
    assert any("45" in r and "exceeds" in r for r in res.reasons)


def test_risk_lightning_moderate():
    ra = RiskAgent()
    w, m, g = _make_envelopes(lightning="moderate")
    res = ra.correlate("run-caution", w, m, g)
    assert res.verdict == "CAUTION"
    assert any("lightning" in r.lower() for r in res.reasons)


def test_risk_lightning_severe():
    ra = RiskAgent()
    w, m, g = _make_envelopes(lightning="severe")
    res = ra.correlate("run-unsafe", w, m, g)
    assert res.verdict == "UNSAFE"
    assert any("lightning" in r.lower() for r in res.reasons)


def test_risk_cyclone_watch():
    ra = RiskAgent()
    w, m, g = _make_envelopes(cyclone="Watch: Low pressure system developing")
    res = ra.correlate("run-caution", w, m, g)
    assert res.verdict == "CAUTION"
    assert any("cyclone watch" in r.lower() for r in res.reasons)


def test_risk_cyclone_alert_halt():
    ra = RiskAgent()
    w, m, g = _make_envelopes(cyclone="Warning: Severe Cyclonic Storm")
    res = ra.correlate("run-unsafe", w, m, g)
    assert res.verdict == "UNSAFE"
    assert any("zero-departure" in r.lower() for r in res.reasons)


def test_risk_geofencing_warning():
    ra = RiskAgent()
    w, m, g = _make_envelopes(geo_status="warning", geo_dist=1.5, boundary_name="India-Sri Lanka IMBL")
    res = ra.correlate("run-caution", w, m, g)
    assert res.verdict == "CAUTION"
    assert any("international boundary" in r.lower() for r in res.reasons)


def test_risk_geofencing_restricted():
    ra = RiskAgent()
    w, m, g = _make_envelopes(geo_status="restricted", boundary_name="Marine National Park Gulf of Mannar")
    res = ra.correlate("run-unsafe", w, m, g)
    assert res.verdict == "UNSAFE"
    assert any("restricted maritime zone" in r.lower() for r in res.reasons)


def test_risk_unsafe_overrides_caution():
    # Wave is CAUTION (1.8m), but wind is UNSAFE (48 km/h) -> must be UNSAFE
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=1.8, wind=48.0)
    res = ra.correlate("run-conflict", w, m, g)
    assert res.verdict == "UNSAFE"
    assert len(res.reasons) >= 2


def test_risk_deterministic_audit_trace():
    ra = RiskAgent()
    w, m, g = _make_envelopes(wave=2.9, wind=15.0)
    res = ra.correlate("audit-1", w, m, g)
    assert "inputs" in res.rule_trace
    assert "thresholds" in res.rule_trace
    assert "triggered_rules" in res.rule_trace
    assert res.rule_trace["inputs"]["wave_height_m"] == 2.9
    assert res.rule_trace["thresholds"]["wave_unsafe_m"] == 2.5
