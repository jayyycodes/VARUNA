# Risk Assessment Agent
**Owner:** Jaish

## Responsibility
Correlates Weather, Marine, and Geofencing outputs into a deterministic **Safe / Caution / Unsafe** verdict.

> [!CAUTION]
> **Safety Guardrail**: The LLM is **strictly forbidden** from deciding or overriding the safety verdict. The verdict is 100% computed by an auditable, deterministic Python rule engine based on official INCOIS and IMD maritime advisories. The LLM only receives the computed verdict and explains it in plain language.

---

## 1. Official INCOIS / IMD Threshold Reference

These thresholds are sourced directly from INCOIS Ocean State Forecast (OSF) Small-Craft Safety Advisories:

| Parameter | Unit | SAFE Threshold | CAUTION Threshold | UNSAFE Threshold (Halt) | Official Source |
|---|---|---|---|---|---|
| **Significant Wave Height ($H_s$)** | meters | $\le 1.5$ m | $1.5$ m to $2.5$ m | $> 2.5$ m | INCOIS OSF Small-Craft Warning |
| **Wind Speed** | km/h | $\le 25$ km/h (14 kts) | $25$ to $40$ km/h (14–22 kts) | $> 40$ km/h (22 kts) | IMD Beaufort Scale 6 (Strong Breeze) |
| **Lightning Risk** | categorical | `none` / `low` | `moderate` | `high` / `severe` | IMD Convective Storm Warning |
| **Cyclone Alert** | alert state | `None` | `Watch` (Pre-genesis) | `Alert` / `Warning` / `Post-Landfall` | IMD RSMC New Delhi Bulletins |
| **Geofencing / Boundaries** | spatial | `clear` ($> 2.0$ km) | `warning` ($\le 2.0$ km to IMBL) | `restricted` (Inside MPA / Foreign EEZ) | Maritime Zones of India Act / PostGIS |

---

## 2. Copy-Paste Runnable Implementation

You can drop this directly into `agents/risk/risk_agent.py`:

```python
from datetime import datetime, timezone
from backend.schemas.envelope import AgentEnvelope, RiskVerdict

class RiskAgent:
    def correlate(
        self,
        query_run_id: str,
        weather: AgentEnvelope,
        marine: AgentEnvelope,
        geo: AgentEnvelope
    ) -> RiskVerdict:
        wave = weather.data.get("wave_height_m", 0.0)
        wind = weather.data.get("wind_speed_kmh", 0.0)
        lightning = weather.data.get("lightning_risk", "none")
        cyclone = weather.data.get("cyclone_alert")
        
        geo_status = geo.data.get("status", "clear")
        boundary = geo.data.get("nearest_boundary_name", "restricted zone")
        dist = geo.data.get("distance_km", 9999.0)

        reasons = []
        verdict = "SAFE"

        # 1. Geofencing check (Primary Sovereignty & Legal Guardrail)
        if geo_status == "restricted":
            verdict = "UNSAFE"
            reasons.append(f"Vessel is inside restricted maritime zone: {boundary}")
        elif geo_status == "warning":
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            reasons.append(f"Vessel is close ({dist:.1f}km) to international boundary: {boundary}")

        # 2. Cyclone Bulletin check (Absolute Zero-Departure)
        if cyclone:
            verdict = "UNSAFE"
            reasons.append(f"Mandatory zero-departure order: Active cyclone alert ({cyclone})")

        # 3. Wave Height Check
        if wave > 2.5:
            verdict = "UNSAFE"
            reasons.append(f"Wave height {wave}m exceeds small-craft limit (2.5m)")
        elif wave > 1.5:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            reasons.append(f"Wave height {wave}m requires caution for small vessels")

        # 4. Wind Speed Check
        if wind > 40.0:
            verdict = "UNSAFE"
            reasons.append(f"Wind speed {wind} km/h exceeds safe threshold (40 km/h)")
        elif wind > 25.0:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            reasons.append(f"Moderately strong wind: {wind} km/h")

        # 5. Lightning Risk Check
        if lightning in ("high", "severe"):
            verdict = "UNSAFE"
            reasons.append(f"Severe lightning activity reported ({lightning})")

        if not reasons:
            reasons.append("All marine, weather, and territorial parameters within safe operational limits")

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
                    "geofencing_status": geo_status,
                    "distance_to_boundary_km": dist
                },
                "thresholds": {
                    "wave_unsafe_m": 2.5,
                    "wave_caution_m": 1.5,
                    "wind_unsafe_kmh": 40.0,
                    "wind_caution_kmh": 25.0,
                    "warning_distance_km": 2.0
                },
                "computed_verdict": verdict
            },
            created_at=datetime.now(timezone.utc)
        )
```

---

## 3. How to Test Your Agent Locally

```powershell
python -c "from agents.risk.risk_agent import RiskAgent; from agents.planner.mock_agents import mock_weather, mock_marine, mock_geofencing; ra = RiskAgent(); w = mock_weather('t', 16.99, 73.30, '2026-09-10'); m = mock_marine('t', 16.99, 73.30, '2026-09-10'); g = mock_geofencing('t', 16.99, 73.30); print(ra.correlate('t', w, m, g).verdict)"
```
