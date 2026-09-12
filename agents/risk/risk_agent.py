"""
Risk Assessment Agent — owner: Jaish

Correlates Weather + Marine + Geofencing outputs into a Safe/Caution/Unsafe
verdict using a DETERMINISTIC RULE ENGINE. The LLM only explains this verdict
in natural language downstream — it never decides the verdict itself.
This is the single most important guardrail in the whole system.

Tier-2 Capabilities:
  1. Vessel-Specific Safety Criteria (Country Craft vs. Mechanized vs. Longliner).
  2. Compound Maritime Risk Modeling (Cross Swell, Opposing Currents, Shoaling).
  3. Threshold Rule Versioning & DB Audit Log (PostgreSQL risk_verdicts table).
  4. Time-to-Shelter Evacuation Estimator (Ports of Refuge & Squall Intercepts).

Follows agents/risk/README.md specification and official INCOIS / IMD thresholds.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.schemas.envelope import AgentEnvelope, RiskVerdict
from .audit_logger import RULE_VERSIONS, RiskAuditLogger
from .compound_risk import CompoundHazard, CompoundRiskEngine, CompoundRiskInput
from .evacuation import EvacuationAssessment, EvacuationEngine

logger = logging.getLogger("varuna.risk")

# Compass bearing mapping for ocean currents / winds
COMPASS_POINTS = {
    "N": 0.0, "NNE": 22.5, "NE": 45.0, "ENE": 67.5,
    "E": 90.0, "ESE": 112.5, "SE": 135.0, "SSE": 157.5,
    "S": 180.0, "SSW": 202.5, "SW": 225.0, "WSW": 247.5,
    "W": 270.0, "WNW": 292.5, "NW": 315.0, "NNW": 337.5,
}

VESSEL_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "traditional_craft": {
        "display_name": "Non-Mechanized / Traditional Country Craft (<10m)",
        "wave_caution_m": 0.8,
        "wave_unsafe_m": 1.2,
        "wind_caution_kmh": 15.0,
        "wind_unsafe_kmh": 20.0,
    },
    "country_craft": {
        "display_name": "Non-Mechanized / Traditional Country Craft (<10m)",
        "wave_caution_m": 0.8,
        "wave_unsafe_m": 1.2,
        "wind_caution_kmh": 15.0,
        "wind_unsafe_kmh": 20.0,
    },
    "artisanal": {
        "display_name": "Artisanal Craft (<10m)",
        "wave_caution_m": 0.8,
        "wave_unsafe_m": 1.2,
        "wind_caution_kmh": 15.0,
        "wind_unsafe_kmh": 20.0,
    },
    "mechanized_trawler": {
        "display_name": "Mechanized Trawler / Gillnetter (10-15m)",
        "wave_caution_m": 1.5,
        "wave_unsafe_m": 2.5,
        "wind_caution_kmh": 25.0,
        "wind_unsafe_kmh": 40.0,
    },
    "standard": {
        "display_name": "Standard Mechanized Craft (10-15m)",
        "wave_caution_m": 1.5,
        "wave_unsafe_m": 2.5,
        "wind_caution_kmh": 25.0,
        "wind_unsafe_kmh": 40.0,
    },
    "deep_sea_longliner": {
        "display_name": "Deep-Sea Commercial Longliner (>20m)",
        "wave_caution_m": 2.5,
        "wave_unsafe_m": 3.5,
        "wind_caution_kmh": 40.0,
        "wind_unsafe_kmh": 55.0,
    },
    "commercial": {
        "display_name": "Deep-Sea Commercial Longliner (>20m)",
        "wave_caution_m": 2.5,
        "wave_unsafe_m": 3.5,
        "wind_caution_kmh": 40.0,
        "wind_unsafe_kmh": 55.0,
    },
}


def _parse_direction_deg(raw: Any) -> Optional[float]:
    """Parses compass string or numeric degrees into float degrees."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw) % 360.0
    if isinstance(raw, str):
        cleaned = raw.strip().upper()
        if cleaned in COMPASS_POINTS:
            return COMPASS_POINTS[cleaned]
        try:
            return float(cleaned) % 360.0
        except ValueError:
            return None
    return None


class RiskAgent:
    """
    Deterministic Risk Assessment Agent.

    Evaluates maritime safety based on official INCOIS Ocean State Forecast (OSF)
    Small-Craft Advisories, IMD Beaufort Scale 6 winds, IMD convective lightning,
    PostGIS territorial sovereignty / geofencing boundaries, vessel classifications,
    compound sea states, and port evacuation margins.
    """

    # Baseline standard thresholds (Mechanized craft fallback)
    WAVE_HEIGHT_UNSAFE_M = 2.5
    WAVE_HEIGHT_CAUTION_M = 1.5

    WIND_SPEED_UNSAFE_KMH = 40.0
    WIND_SPEED_CAUTION_KMH = 25.0

    WARNING_DISTANCE_KM = 2.0

    def __init__(self, audit_logger: Optional[RiskAuditLogger] = None) -> None:
        self._audit_logger = audit_logger or RiskAuditLogger()

    def correlate(
        self,
        query_run_id_or_weather: str | AgentEnvelope,
        weather_or_marine: AgentEnvelope,
        marine_or_geo: AgentEnvelope,
        geo: AgentEnvelope | None = None,
        *,
        vessel_type: str = "mechanized_trawler",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        squall_distance_km: Optional[float] = None,
        squall_speed_kmh: float = 35.0,
        audit_log: bool = False,
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

        # ── Resolve Vessel-Specific Thresholds ──────────────────────────
        vessel_key = vessel_type.lower()
        v_thresh = VESSEL_THRESHOLDS.get(vessel_key, VESSEL_THRESHOLDS["mechanized_trawler"])
        wave_caution_limit = v_thresh["wave_caution_m"]
        wave_unsafe_limit = v_thresh["wave_unsafe_m"]
        wind_caution_limit = v_thresh["wind_caution_kmh"]
        wind_unsafe_limit = v_thresh["wind_unsafe_kmh"]
        vessel_display = v_thresh["display_name"]

        # ── Extract Weather Inputs ──────────────────────────────────────
        w_data = weather.data or {}
        wave = float(w_data.get("wave_height_m") or w_data.get("wave_height") or 0.0)
        wind = float(w_data.get("wind_speed_kmh") or w_data.get("wind_speed") or 0.0)
        lightning = str(w_data.get("lightning_risk") or "none").lower()
        cyclone = w_data.get("cyclone_alert")
        wind_dir = _parse_direction_deg(w_data.get("wind_direction_deg") or w_data.get("wind_direction"))
        wave_dir = _parse_direction_deg(w_data.get("wave_direction_deg") or w_data.get("wave_direction"))
        swell_dir = _parse_direction_deg(w_data.get("swell_direction_deg") or w_data.get("swell_direction"))

        # ── Extract Geofencing Inputs ───────────────────────────────────
        g_data = geofencing.data or {}
        geo_status = str(g_data.get("status") or "clear").lower()
        boundary = str(g_data.get("nearest_boundary_name") or "restricted boundary")
        dist = float(g_data.get("distance_km") if g_data.get("distance_km") is not None else 9999.0)

        # ── Extract Marine Inputs ───────────────────────────────────────
        m_data = marine.data or {}
        pfz_zones = m_data.get("pfz_zones") or []
        current_spd = float(m_data.get("ocean_current_speed_knots") or 0.0)
        current_dir = _parse_direction_deg(m_data.get("ocean_current_direction"))
        depth = float(m_data.get("bathymetric_depth_m") or m_data.get("depth_m") or 0.0) or None

        # Resolve Lat/Lon
        lat = latitude or w_data.get("latitude") or m_data.get("latitude") or g_data.get("latitude")
        lon = longitude or w_data.get("longitude") or m_data.get("longitude") or g_data.get("longitude")

        reasons: list[str] = []
        triggered_rules: list[dict[str, Any]] = []
        verdict = "SAFE"

        # 1. Geofencing check (Primary Sovereignty & Legal Guardrail)
        if geo_status == "restricted":
            verdict = "UNSAFE"
            msg = f"Vessel is inside restricted maritime zone: {boundary}"
            reasons.append(msg)
            triggered_rules.append({
                "rule": "GEOFENCING_RESTRICTED",
                "severity": "UNSAFE",
                "details": msg,
                "version": RULE_VERSIONS["RULE-GEO-01"],
            })
        elif geo_status == "warning" or dist <= self.WARNING_DISTANCE_KM:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = f"Vessel is close ({dist:.1f}km) to international boundary: {boundary}"
            reasons.append(msg)
            triggered_rules.append({
                "rule": "GEOFENCING_IMBL_WARNING",
                "severity": "CAUTION",
                "details": msg,
                "version": RULE_VERSIONS["RULE-GEO-01"],
            })

        # 2. Cyclone Bulletin check (Absolute Zero-Departure order)
        if cyclone and str(cyclone).lower() not in ("none", "null", "false", ""):
            cyclone_str = str(cyclone)
            # Watch -> CAUTION, Alert/Warning/Cyclone -> UNSAFE
            if "watch" in cyclone_str.lower() and not any(k in cyclone_str.lower() for k in ("warning", "alert", "landfall")):
                if verdict != "UNSAFE":
                    verdict = "CAUTION"
                msg = f"Pre-genesis cyclone watch in effect: {cyclone_str}"
                reasons.append(msg)
                triggered_rules.append({
                    "rule": "CYCLONE_WATCH",
                    "severity": "CAUTION",
                    "details": msg,
                    "version": RULE_VERSIONS["RULE-CYC-01"],
                })
            else:
                verdict = "UNSAFE"
                msg = f"Mandatory zero-departure order: Active cyclone bulletin ({cyclone_str})"
                reasons.append(msg)
                triggered_rules.append({
                    "rule": "CYCLONE_ALERT_HALT",
                    "severity": "UNSAFE",
                    "details": msg,
                    "version": RULE_VERSIONS["RULE-CYC-01"],
                })

        # 3. Wave Height Check (Vessel-Scaled INCOIS OSF limit)
        if wave > wave_unsafe_limit:
            verdict = "UNSAFE"
            msg = (
                f"Significant wave height {wave:.1f}m exceeds {vessel_display} safety threshold "
                f"({wave_unsafe_limit}m)"
            )
            reasons.append(msg)
            triggered_rules.append({
                "rule": "WAVE_HEIGHT_UNSAFE",
                "severity": "UNSAFE",
                "details": msg,
                "version": RULE_VERSIONS["RULE-WAVE-01"],
            })
        elif wave > wave_caution_limit:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = (
                f"Significant wave height {wave:.1f}m requires caution for {vessel_display} "
                f"(threshold {wave_caution_limit}m)"
            )
            reasons.append(msg)
            triggered_rules.append({
                "rule": "WAVE_HEIGHT_CAUTION",
                "severity": "CAUTION",
                "details": msg,
                "version": RULE_VERSIONS["RULE-WAVE-01"],
            })

        # 4. Wind Speed Check (Vessel-Scaled IMD Beaufort Scale)
        if wind > wind_unsafe_limit:
            verdict = "UNSAFE"
            msg = (
                f"Wind speed {wind:.1f} km/h exceeds {vessel_display} safe threshold "
                f"({wind_unsafe_limit} km/h)"
            )
            reasons.append(msg)
            triggered_rules.append({
                "rule": "WIND_SPEED_UNSAFE",
                "severity": "UNSAFE",
                "details": msg,
                "version": RULE_VERSIONS["RULE-WIND-01"],
            })
        elif wind > wind_caution_limit:
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = (
                f"Moderately strong wind: {wind:.1f} km/h (caution threshold for {vessel_display}: "
                f"{wind_caution_limit} km/h)"
            )
            reasons.append(msg)
            triggered_rules.append({
                "rule": "WIND_SPEED_CAUTION",
                "severity": "CAUTION",
                "details": msg,
                "version": RULE_VERSIONS["RULE-WIND-01"],
            })

        # 5. Convective Storm & Lightning Risk (IMD Convective Storm Warning)
        if lightning in ("high", "severe", "extreme"):
            verdict = "UNSAFE"
            msg = f"Severe lightning and convective storm activity reported ({lightning})"
            reasons.append(msg)
            triggered_rules.append({
                "rule": "LIGHTNING_SEVERE",
                "severity": "UNSAFE",
                "details": msg,
                "version": RULE_VERSIONS["RULE-LIGHTNING-01"],
            })
        elif lightning == "moderate":
            if verdict != "UNSAFE":
                verdict = "CAUTION"
            msg = "Moderate lightning probability in the operating sector"
            reasons.append(msg)
            triggered_rules.append({
                "rule": "LIGHTNING_MODERATE",
                "severity": "CAUTION",
                "details": msg,
                "version": RULE_VERSIONS["RULE-LIGHTNING-01"],
            })

        # 6. Compound Maritime Risk Modeling
        compound_input = CompoundRiskInput(
            wave_height_m=wave,
            wave_direction_deg=wave_dir,
            wind_direction_deg=wind_dir,
            swell_direction_deg=swell_dir,
            current_speed_knots=current_spd,
            current_direction_deg=current_dir,
            bathymetric_depth_m=depth,
        )
        compound_hazards = CompoundRiskEngine.evaluate(compound_input)
        for ch in compound_hazards:
            if ch.severity == "UNSAFE":
                verdict = "UNSAFE"
            elif ch.severity == "CAUTION" and verdict != "UNSAFE":
                verdict = "CAUTION"
            reasons.append(ch.description)
            triggered_rules.append({
                "rule": ch.hazard_code,
                "severity": ch.severity,
                "details": ch.description,
                "parameters": ch.parameters_involved,
                "version": ch.rule_version,
            })

        # 7. Time-to-Shelter Evacuation Check
        evac_assessment: Optional[EvacuationAssessment] = None
        if lat is not None and lon is not None:
            evac_assessment = EvacuationEngine.evaluate_evacuation(
                lat=float(lat),
                lon=float(lon),
                vessel_type=vessel_type,
                squall_distance_km=squall_distance_km,
                squall_speed_kmh=squall_speed_kmh,
            )
            if evac_assessment.evacuation_hazard_code == "EVACUATION_INTERCEPT_IMMINENT":
                verdict = "UNSAFE"
                reasons.append(evac_assessment.advisory_notes)
                triggered_rules.append({
                    "rule": "EVACUATION_INTERCEPT_IMMINENT",
                    "severity": "UNSAFE",
                    "details": evac_assessment.advisory_notes,
                    "version": RULE_VERSIONS["RULE-EVAC-01"],
                })
            elif evac_assessment.evacuation_hazard_code == "EVACUATION_MARGIN_TIGHT":
                if verdict != "UNSAFE":
                    verdict = "CAUTION"
                reasons.append(evac_assessment.advisory_notes)
                triggered_rules.append({
                    "rule": "EVACUATION_MARGIN_TIGHT",
                    "severity": "CAUTION",
                    "details": evac_assessment.advisory_notes,
                    "version": RULE_VERSIONS["RULE-EVAC-01"],
                })

        # 8. Default Safe state if no thresholds breached
        if not reasons:
            reasons.append(
                f"All marine, weather, and territorial parameters are within safe operational limits for {vessel_display}"
            )

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
                "vessel_type": vessel_type,
                "latitude": lat,
                "longitude": lon,
            },
            "thresholds": {
                "vessel_class": vessel_display,
                "wave_unsafe_m": wave_unsafe_limit,
                "wave_caution_m": wave_caution_limit,
                "wind_unsafe_kmh": wind_unsafe_limit,
                "wind_caution_kmh": wind_caution_limit,
                "warning_distance_km": self.WARNING_DISTANCE_KM,
                "authoritative_sources": [
                    "INCOIS Ocean State Forecast (OSF) Small-Craft Advisory",
                    "IMD Beaufort Scale 6 (Strong Breeze)",
                    "IMD RSMC New Delhi Cyclone Warning Protocols",
                    "Maritime Zones of India Act (1976 / 1981)",
                    "DG Shipping Vessel Safety Norms (2020)",
                ],
            },
            "triggered_rules": triggered_rules,
            "rule_versions": RULE_VERSIONS,
            "evacuation": evac_assessment.model_dump(mode="json") if evac_assessment else None,
            "computed_verdict": verdict,
        }

        # Audit persistence (non-blocking)
        if audit_log and self._audit_logger:
            try:
                self._audit_logger.log_verdict(
                    query_run_id=query_run_id,
                    verdict=verdict,
                    vessel_type=vessel_type,
                    reasons=reasons,
                    rule_trace=rule_trace,
                    latitude=float(lat) if lat else None,
                    longitude=float(lon) if lon else None,
                )
            except Exception as exc:
                logger.warning("Audit log error: %s", exc)

        return RiskVerdict(
            query_run_id=query_run_id,
            verdict=verdict,  # type: ignore[arg-type]
            reasons=reasons,
            rule_trace=rule_trace,
            created_at=datetime.now(timezone.utc),
        )
