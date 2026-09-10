"""
Risk Assessment Agent — owner: Jaish

Correlates Weather + Marine + Geofencing outputs into a Safe/Caution/Unsafe
verdict using a DETERMINISTIC RULE ENGINE. The LLM only explains this verdict
in natural language downstream — it never decides the verdict itself.
This is the single most important guardrail in the whole system.

Follows agents/risk/README.md specification and official INCOIS / IMD thresholds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.schemas.envelope import AgentEnvelope, RiskVerdict


class RiskAgent:
    """
    Deterministic Risk Assessment Agent.

    Evaluates maritime safety based on official INCOIS Ocean State Forecast (OSF)
    Small-Craft Advisories, IMD Beaufort Scale 6 winds, IMD convective lightning,
    and PostGIS territorial sovereignty / geofencing boundaries.
    """

    # Official INCOIS / IMD safety thresholds
    WAVE_HEIGHT_UNSAFE_M = 2.5
    WAVE_HEIGHT_CAUTION_M = 1.5

    WIND_SPEED_UNSAFE_KMH = 40.0
    WIND_SPEED_CAUTION_KMH = 25.0

    WARNING_DISTANCE_KM = 2.0

    def correlate(
        self,
        query_run_id_or_weather: str | AgentEnvelope,
        weather_or_marine: AgentEnvelope,
        marine_or_geo: AgentEnvelope,
        geo: AgentEnvelope | None = None,
    ) -> RiskVerdict:
        """
        Correlate weather, marine, and geofencing envelopes into a deterministic
        Safe / Caution / Unsafe verdict.

        Supports both 4-argument signature:
            correlate(query_run_id, weather, marine, geo)
        and 3-argument signature:
            correlate(weather, marine, geo)
        """
        if isinstance(query_run_id_or_weather, str):
            query_run_id = query_run_id_or_weather
            weather = weather_or_marine
            marine = marine_or_geo
            if geo is None:
                raise ValueError("geo AgentEnvelope must be provided when query_run_id is first arg")
            geofencing = geo
        else:
            weather = query_run_id_or_weather
            marine = weather_or_marine
            geofencing = marine_or_geo
            query_run_id = weather.query_run_id

        # Extract Weather inputs
        w_data = weather.data or {}
        wave = float(w_data.get("wave_height_m") or w_data.get("wave_height") or 0.0)
        wind = float(w_data.get("wind_speed_kmh") or w_data.get("wind_speed") or 0.0)
        lightning = str(w_data.get("lightning_risk") or "none").lower()
        cyclone = w_data.get("cyclone_alert")

        # Extract Geofencing inputs
        g_data = geofencing.data or {}
        geo_status = str(g_data.get("status") or "clear").lower()
        boundary = str(g_data.get("nearest_boundary_name") or "restricted boundary")
        dist = float(g_data.get("distance_km") if g_data.get("distance_km") is not None else 9999.0)

        # Extract Marine inputs
        m_data = marine.data or {}
        pfz_zones = m_data.get("pfz_zones") or []

        reasons: list[str] = []
        triggered_rules: list[dict[str, Any]] = []
        verdict = "SAFE"

        # 1. Geofencing check (Primary Sovereignty & Legal Guardrail)
        if geo_status == "restricted":
            verdict = "UNSAFE"
            msg = f"Vessel is inside restricted maritime zone: {boundary}"
            reasons.append(msg)
            triggered_rules.append({"rule": "GEOFENCING_RESTRICTED", "severity": "UNSAFE", "details": msg})
        elif geo_status == "warning" or dist <= self.WARNING_DISTANCE_KM:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = f"Vessel is close ({dist:.1f}km) to international boundary: {boundary}"
            reasons.append(msg)
            triggered_rules.append({"rule": "GEOFENCING_IMBL_WARNING", "severity": "CAUTION", "details": msg})

        # 2. Cyclone Bulletin check (Absolute Zero-Departure order)
        if cyclone and str(cyclone).lower() not in ("none", "null", "false", ""):
            cyclone_str = str(cyclone)
            # Watch -> CAUTION, Alert/Warning/Cyclone -> UNSAFE
            if "watch" in cyclone_str.lower() and not any(k in cyclone_str.lower() for k in ("warning", "alert", "landfall")):
                if verdict != "UNSAFE":
                    verdict = "CAUTION"
                msg = f"Pre-genesis cyclone watch in effect: {cyclone_str}"
                reasons.append(msg)
                triggered_rules.append({"rule": "CYCLONE_WATCH", "severity": "CAUTION", "details": msg})
            else:
                verdict = "UNSAFE"
                msg = f"Mandatory zero-departure order: Active cyclone bulletin ({cyclone_str})"
                reasons.append(msg)
                triggered_rules.append({"rule": "CYCLONE_ALERT_HALT", "severity": "UNSAFE", "details": msg})

        # 3. Wave Height Check (INCOIS OSF small-craft safety limit)
        if wave > self.WAVE_HEIGHT_UNSAFE_M:
            verdict = "UNSAFE"
            msg = f"Significant wave height {wave:.1f}m exceeds small-craft safety threshold ({self.WAVE_HEIGHT_UNSAFE_M}m)"
            reasons.append(msg)
            triggered_rules.append({"rule": "WAVE_HEIGHT_UNSAFE", "severity": "UNSAFE", "details": msg})
        elif wave > self.WAVE_HEIGHT_CAUTION_M:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = f"Significant wave height {wave:.1f}m requires caution for small craft (threshold {self.WAVE_HEIGHT_CAUTION_M}m)"
            reasons.append(msg)
            triggered_rules.append({"rule": "WAVE_HEIGHT_CAUTION", "severity": "CAUTION", "details": msg})

        # 4. Wind Speed Check (IMD Beaufort Scale 6)
        if wind > self.WIND_SPEED_UNSAFE_KMH:
            verdict = "UNSAFE"
            msg = f"Wind speed {wind:.1f} km/h exceeds safe threshold ({self.WIND_SPEED_UNSAFE_KMH} km/h)"
            reasons.append(msg)
            triggered_rules.append({"rule": "WIND_SPEED_UNSAFE", "severity": "UNSAFE", "details": msg})
        elif wind > self.WIND_SPEED_CAUTION_KMH:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = f"Moderately strong wind: {wind:.1f} km/h (caution threshold {self.WIND_SPEED_CAUTION_KMH} km/h)"
            reasons.append(msg)
            triggered_rules.append({"rule": "WIND_SPEED_CAUTION", "severity": "CAUTION", "details": msg})

        # 5. Convective Storm & Lightning Risk (IMD Convective Storm Warning)
        if lightning in ("high", "severe", "extreme"):
            verdict = "UNSAFE"
            msg = f"Severe lightning and convective storm activity reported ({lightning})"
            reasons.append(msg)
            triggered_rules.append({"rule": "LIGHTNING_SEVERE", "severity": "UNSAFE", "details": msg})
        elif lightning == "moderate":
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = "Moderate lightning probability in the operating sector"
            reasons.append(msg)
            triggered_rules.append({"rule": "LIGHTNING_MODERATE", "severity": "CAUTION", "details": msg})

        # 6. Default Safe state if no thresholds breached
        if not reasons:
            reasons.append("All marine, weather, and territorial parameters are within safe operational limits")

        rule_trace = {
            "inputs": {
                "wave_height_m": wave,
                "wind_speed_kmh": wind,
                "lightning_risk": lightning,
                "cyclone_alert": cyclone,
                "geofencing_status": geo_status,
                "distance_to_boundary_km": dist,
                "nearest_boundary_name": boundary,
                "pfz_candidates_count": len(pfz_zones),
            },
            "thresholds": {
                "wave_unsafe_m": self.WAVE_HEIGHT_UNSAFE_M,
                "wave_caution_m": self.WAVE_HEIGHT_CAUTION_M,
                "wind_unsafe_kmh": self.WIND_SPEED_UNSAFE_KMH,
                "wind_caution_kmh": self.WIND_SPEED_CAUTION_KMH,
                "warning_distance_km": self.WARNING_DISTANCE_KM,
                "authoritative_sources": [
                    "INCOIS Ocean State Forecast (OSF) Small-Craft Advisory",
                    "IMD Beaufort Scale 6 (Strong Breeze)",
                    "IMD RSMC New Delhi Cyclone Warning Protocols",
                    "Maritime Zones of India Act (1976 / 1981)",
                ],
            },
            "triggered_rules": triggered_rules,
            "computed_verdict": verdict,
        }

        return RiskVerdict(
            query_run_id=query_run_id,
            verdict=verdict,  # type: ignore[arg-type]
            reasons=reasons,
            rule_trace=rule_trace,
            created_at=datetime.now(timezone.utc),
        )

