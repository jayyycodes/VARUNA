"""
Unit tests for eval/risk_groundedness.py
Tests LLM groundedness evaluator on verdict concordance, numerical fidelity, and hallucination catching.
"""

from datetime import datetime, timezone
import pytest

from backend.schemas.envelope import RiskVerdict
from eval.risk_groundedness import RiskGroundednessEvaluator


def _make_verdict(verdict: str, wave: float, wind: float, reasons: list[str]) -> RiskVerdict:
    return RiskVerdict(
        query_run_id="q-ground",
        verdict=verdict,  # type: ignore[arg-type]
        reasons=reasons,
        rule_trace={
            "inputs": {"wave_height_m": wave, "wind_speed_kmh": wind, "cyclone_alert": None, "lightning_risk": "none"},
            "thresholds": {"wave_unsafe_m": 2.5, "wind_unsafe_kmh": 40.0},
            "triggered_rules": [],
            "computed_verdict": verdict,
        },
        created_at=datetime.now(timezone.utc),
    )


def test_grounded_explanation_passes():
    v = _make_verdict("SAFE", 1.2, 18.0, ["All parameters within safe limits"])
    exp = "Conditions are calm. Significant wave height is 1.2m and wind speed is 18.0 km/h, well below unsafe limits."
    report = RiskGroundednessEvaluator.evaluate(v, exp)

    assert report.is_grounded is True
    assert report.verdict_concordance is True
    assert len(report.violations) == 0
    assert report.score == 1.0


def test_numerical_hallucination_fails():
    v = _make_verdict("SAFE", 1.2, 18.0, ["All parameters within safe limits"])
    # Hallucinates 8.5m waves and 95 km/h winds
    exp = "Waves are currently 8.5m with gusts of 95 km/h."
    report = RiskGroundednessEvaluator.evaluate(v, exp)

    assert report.is_grounded is False
    assert any(viol.category == "NUMERICAL_HALLUCINATION" for viol in report.violations)
    assert report.score < 1.0


def test_verdict_contradiction_fails():
    v = _make_verdict("UNSAFE", 3.2, 50.0, ["Wave height exceeds threshold"])
    # Claims safe to depart when computed verdict is UNSAFE
    exp = "It is completely safe to depart today with smooth sailing guaranteed."
    report = RiskGroundednessEvaluator.evaluate(v, exp)

    assert report.is_grounded is False
    assert report.verdict_concordance is False
    assert any(viol.category == "VERDICT_CONTRADICTION" for viol in report.violations)


def test_unmentioned_cyclone_fails():
    v = _make_verdict("UNSAFE", 3.0, 42.0, ["Wave height high"])
    # Invents a cyclone warning that wasn't in inputs
    exp = "Mandatory halt due to category 4 cyclone warning off the coast."
    report = RiskGroundednessEvaluator.evaluate(v, exp)

    assert any(viol.category == "UNGROUNDED_HAZARD" for viol in report.violations)
