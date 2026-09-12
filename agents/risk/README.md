# Risk Assessment Agent
**Owner:** Jaish  
**Status:** MVP Complete ✅ | Next Phase: Vessel-Specific Criteria & Compound Sea States

## Responsibility
Correlates real-time Weather, Marine, and Geofencing telemetry into an auditable, deterministic **Safe / Caution / Unsafe** operational verdict.

> [!CAUTION]
> **Deterministic Life-or-Death Safety Guardrail**:  
> The LLM is **strictly forbidden** from deciding or overriding the safety verdict. The verdict is 100% computed by an auditable, deterministic Python rule engine based on official INCOIS and IMD maritime advisories. The LLM only receives the computed verdict and explains it in plain language.

---

## 1. MVP Tasks (Completed ✅)
- [x] **Deterministic Rule Engine**: Multi-domain evaluation engine correlating waves, wind, lightning, cyclones, and boundary proximity.
- [x] **Official Maritime Thresholds**:
  - *Significant Wave Height*: $\le 1.5$ m (Safe), $1.5$–$2.5$ m (Caution), $> 2.5$ m (Unsafe / Halt).
  - *Wind Speed*: $\le 25$ km/h (Safe), $25$–$40$ km/h (Caution), $> 40$ km/h (Unsafe / Halt).
  - *Lightning*: `low`/`none` (Safe), `moderate` (Caution), `high`/`severe` (Unsafe).
  - *Cyclones*: Any active bulletin $\to$ Mandatory zero-departure `UNSAFE`.
  - *Geofencing*: `restricted` $\to$ `UNSAFE`, `warning` $\to$ `CAUTION`.
- [x] **Verifiable Rule Trace**: Emits detailed `rule_trace` containing inputs, thresholds, and comparison operators for the frontend evidence panel.
- [x] **Planner Enforcement**: Guaranteed non-downgradable guardrail holding across all queries.

---

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 1.2, 3, & 9), the next operational priorities are:

- [x] **Vessel-Specific Safety Criteria**:
  - Dynamically scaled thresholds based on vessel classification (`VESSEL_THRESHOLDS`):
    - *Non-mechanized / Traditional Country Craft*: Cap at $H_s \le 1.2$ m, Wind $\le 20$ km/h.
    - *Mechanized Trawlers (10–15m)*: Standard thresholds ($H_s \le 2.5$ m, Wind $\le 40$ km/h).
    - *Deep-Sea Commercial Longliners (>20m)*: Tolerant up to $H_s \le 3.5$ m, Wind $\le 55$ km/h.
  - Implemented and unit tested across all craft classes (`agents/risk/tests/test_vessel_criteria.py`).
- [x] **Compound Maritime Risk Modeling**:
  - Implemented `CompoundRiskEngine` (`compound_risk.py`) evaluating nonlinear multi-variable sea interactions:
    - Beam Seas / Dangerous Cross Swell ($60^\circ \le \Delta\theta \le 120^\circ$ inducing vessel roll resonance).
    - Current-Wave Opposing Interaction ($\Delta\theta \ge 135^\circ$, current $\ge 1.2$ kts causing steep breaking seas).
    - Shallow-Water Shoaling Breakers ($\text{depth} \le 2 \times H_s$ or $\text{depth} < 10$ m).
- [x] **Threshold Rule Versioning & DB Audit Log**:
  - Assigned explicit version tags (`RULE-GEO-01: v2.0`, `RULE-CYC-01: v2.0`, `RULE-WAVE-01: v2.1`, `RULE-WIND-01: v2.1`, `RULE-COMPOUND-01: v1.2`, `RULE-EVAC-01: v1.0`).
  - Implemented `RiskAuditLogger` (`audit_logger.py`) persisting audit telemetry into PostgreSQL `risk_verdicts` table.
- [x] **Automated LLM Groundedness Evaluator**:
  - Implemented `RiskGroundednessEvaluator` (`eval/risk_groundedness.py`) asserting natural language explanations never hallucinate numbers, contradict computed verdicts, or invent ungrounded hazards.
- [x] **Time-to-Shelter Evacuation Estimator**:
  - Implemented `EvacuationEngine` (`evacuation.py`) matching vessel position to nearest port of refuge across 16 Indian harbors.
  - Computes transit duration against advancing squall / gale speed to evaluate evacuation margins ($\Delta T < 0.5$h triggers emergency intercept warning).

---

## 3. Official Threshold Reference Table
| Parameter | Unit | SAFE | CAUTION | UNSAFE | Authority |
|---|---|---|---|---|---|
| **Significant Wave Height** | meters | $\le 1.5$ m | $1.5$ – $2.5$ m | $> 2.5$ m | INCOIS OSF Warning |
| **Wind Speed** | km/h | $\le 25$ km/h | $25$ – $40$ km/h | $> 40$ km/h | IMD Beaufort Scale |
| **Lightning Risk** | category | `none` / `low` | `moderate` | `high` / `severe` | IMD Convective Storm |
| **Cyclone Warning** | state | `None` | `Watch` | `Alert` / `Warning` | IMD RSMC New Delhi |
| **Border Proximity** | km | $> 2.0$ km | $\le 2.0$ km | Inside Zone | Maritime Zones Act |

---

## 4. Verification & Testing
Run local verification:
```powershell
python -c "from agents.risk.risk_agent import RiskAgent; from agents.planner.mock_agents import mock_weather, mock_marine, mock_geofencing; ra = RiskAgent(); w = mock_weather('t', 16.99, 73.30, '2026-09-11'); m = mock_marine('t', 16.99, 73.30, '2026-09-11'); g = mock_geofencing('t', 16.99, 73.30); print(ra.correlate('t', w, m, g).verdict)"
```
