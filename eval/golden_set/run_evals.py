"""
Golden-Set Evaluation Runner for Varuna (SIH26176).

Evaluates the deterministic Risk Assessment Agent against 35+ curated,
authoritative historical and operational marine scenarios across Indian
coastal zones.

Usage::

    python eval/golden_set/run_evals.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.schemas.envelope import AgentEnvelope
from agents.risk.risk_agent import RiskAgent


def run_golden_set_evals() -> bool:
    data_path = Path(__file__).parent / "test_cases.json"
    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        return False

    with open(data_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    agent = RiskAgent()
    total = len(cases)
    passed = 0
    failures = []
    verdict_distribution = {"SAFE": 0, "CAUTION": 0, "UNSAFE": 0}

    now = datetime.now(timezone.utc)
    t0 = time.perf_counter()

    print(f"\n================================================================================")
    print(f"  VARUNA (ORCA) — GOLDEN-SET REGRESSION EVALUATION ({total} TEST CASES)")
    print(f"  Owner: Jaish | Sourced: INCOIS OSF, IMD Beaufort 6, IMBL, MPAs")
    print(f"================================================================================\n")

    for case in cases:
        cid = case["id"]
        region = case["region"]
        inp = case["inputs"]
        expected = case["expected_verdict"]

        weather_env = AgentEnvelope(
            agent="weather_intelligence",
            query_run_id=f"eval-{cid}",
            status="success",
            confidence=0.95,
            source="IMD / INCOIS OSF / Open-Meteo",
            timestamp=now,
            data={
                "wave_height_m": inp.get("wave_height_m"),
                "wind_speed_kmh": inp.get("wind_speed_kmh"),
                "lightning_risk": inp.get("lightning_risk"),
                "cyclone_alert": inp.get("cyclone_alert"),
            },
        )

        marine_env = AgentEnvelope(
            agent="marine_fishing",
            query_run_id=f"eval-{cid}",
            status="success",
            confidence=0.92,
            source="INCOIS PFZ WebGIS",
            timestamp=now,
            data={"pfz_zones": [{"zone_id": f"PFZ-{cid}", "productivity_score": 0.82}]},
        )

        geo_env = AgentEnvelope(
            agent="geofencing",
            query_run_id=f"eval-{cid}",
            status="success",
            confidence=0.98,
            source="PostGIS Maritime Boundary Engine",
            timestamp=now,
            data={
                "status": inp.get("geofencing_status", "clear"),
                "distance_km": inp.get("distance_km", 9999.0),
                "nearest_boundary_name": inp.get("nearest_boundary_name", "EEZ Boundary"),
            },
        )

        verdict_obj = agent.correlate(f"eval-{cid}", weather_env, marine_env, geo_env)
        computed = verdict_obj.verdict
        verdict_distribution[computed] = verdict_distribution.get(computed, 0) + 1

        is_match = (computed == expected)
        if is_match:
            passed += 1
            print(f"  [PASS] {cid:<7} | {region[:32]:<32} | Expected: {expected:<7} | Computed: {computed:<7}")
        else:
            failures.append({
                "id": cid,
                "region": region,
                "expected": expected,
                "computed": computed,
                "reasons": verdict_obj.reasons,
                "inputs": inp,
            })
            print(f"  [FAIL] {cid:<7} | {region[:32]:<32} | Expected: {expected:<7} | Computed: {computed:<7} ***")

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    accuracy = (passed / total) * 100.0

    print(f"\n--------------------------------------------------------------------------------")
    print(f"  EVALUATION SUMMARY")
    print(f"--------------------------------------------------------------------------------")
    print(f"  Total Test Cases:    {total}")
    print(f"  Passed:              {passed}")
    print(f"  Failed:              {len(failures)}")
    print(f"  Accuracy:            {accuracy:.2f}%")
    print(f"  Total Duration:      {elapsed_ms:.1f} ms (avg {elapsed_ms/total:.2f} ms/case)")
    print(f"  Verdict Breakdown:   SAFE: {verdict_distribution.get('SAFE', 0)} | "
          f"CAUTION: {verdict_distribution.get('CAUTION', 0)} | "
          f"UNSAFE: {verdict_distribution.get('UNSAFE', 0)}")
    print(f"================================================================================\n")

    if failures:
        print("FAILURES DETAIL:")
        for f in failures:
            print(f"  - Case {f['id']} ({f['region']}): Expected {f['expected']}, got {f['computed']}")
            print(f"    Reasons: {f['reasons']}")
            print(f"    Inputs: {f['inputs']}")
        return False

    return True


if __name__ == "__main__":
    success = run_golden_set_evals()
    sys.exit(0 if success else 1)
