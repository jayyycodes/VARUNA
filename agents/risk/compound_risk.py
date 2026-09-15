"""
Varuna (ORCA) — Compound Maritime Risk Modeling Engine.
Evaluates nonlinear multi-variable physical sea interactions:
  1. Beam Seas / Cross Swell: Crossing angles between wind waves and primary swell
     causing severe dynamic rolling and vessel capsize risks.
  2. Current-Wave Opposing Interaction: Strong surface currents opposing wave
     direction, creating steep breaking seas and harbor mouth hazards.
  3. Shallow-Water Shoaling: Waves refracting and steepening over shallow bathymetry
     (<10m or depth <= 2 * Hs).

Owner: Jaish
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CompoundRiskInput(BaseModel):
    """Input environmental parameters for compound risk analysis."""
    wave_height_m: float = 0.0
    wave_direction_deg: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    swell_direction_deg: Optional[float] = None
    current_speed_knots: float = 0.0
    current_direction_deg: Optional[float] = None
    bathymetric_depth_m: Optional[float] = None


class CompoundHazard(BaseModel):
    """Specific nonlinear compound physical sea hazard."""
    hazard_code: str
    severity: str  # "CAUTION" | "UNSAFE"
    title: str
    description: str
    parameters_involved: Dict[str, Any] = Field(default_factory=dict)
    rule_version: str = "RULE-COMPOUND-01: v1.2"


def _angular_difference_deg(deg1: float, deg2: float) -> float:
    """Computes absolute minimum angular difference between two compass bearings in [0, 180]."""
    diff = abs(deg1 - deg2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


class CompoundRiskEngine:
    """
    Evaluates nonlinear combinations of waves, wind, currents, and bathymetry.
    """

    CROSS_SWELL_MIN_ANGLE_DEG = 60.0
    CROSS_SWELL_MAX_ANGLE_DEG = 120.0
    CROSS_SWELL_MIN_WAVE_M = 1.4

    OPPOSING_CURRENT_MIN_ANGLE_DEG = 135.0
    OPPOSING_CURRENT_MIN_SPEED_KTS = 1.2
    OPPOSING_CURRENT_MIN_WAVE_M = 1.2

    SHOALING_DEPTH_THRESHOLD_M = 10.0

    @classmethod
    def evaluate(cls, inputs: CompoundRiskInput) -> List[CompoundHazard]:
        hazards: List[CompoundHazard] = []

        # 1. Beam Seas / Cross Swell Hazard
        # Angle between wind direction and dominant swell direction
        wind_dir = inputs.wind_direction_deg
        swell_dir = inputs.swell_direction_deg or inputs.wave_direction_deg
        wave_h = inputs.wave_height_m

        if wind_dir is not None and swell_dir is not None and wave_h >= cls.CROSS_SWELL_MIN_WAVE_M:
            crossing_angle = _angular_difference_deg(wind_dir, swell_dir)
            if cls.CROSS_SWELL_MIN_ANGLE_DEG <= crossing_angle <= cls.CROSS_SWELL_MAX_ANGLE_DEG:
                severity = "UNSAFE" if wave_h >= 2.2 else "CAUTION"
                hazards.append(
                    CompoundHazard(
                        hazard_code="COMPOUND_CROSS_SWELL",
                        severity=severity,
                        title="Beam Seas / Dangerous Cross Swell",
                        description=(
                            f"Beam seas / dangerous cross swell: Wind direction ({wind_dir:.0f}°) and dominant swell ({swell_dir:.0f}°) "
                            f"cross at {crossing_angle:.0f}°, inducing heavy vessel roll resonance "
                            f"in {wave_h:.1f}m seas."
                        ),
                        parameters_involved={
                            "wind_direction_deg": wind_dir,
                            "swell_direction_deg": swell_dir,
                            "crossing_angle_deg": round(crossing_angle, 1),
                            "wave_height_m": wave_h,
                        },
                        rule_version="RULE-COMPOUND-01: v1.2",
                    )
                )

        # 2. Opposing Current & Wave Steepening Hazard
        # Current flowing against incoming waves
        curr_dir = inputs.current_direction_deg
        curr_spd = inputs.current_speed_knots
        wave_dir = inputs.wave_direction_deg or inputs.swell_direction_deg

        if curr_dir is not None and wave_dir is not None:
            rel_angle = _angular_difference_deg(curr_dir, wave_dir)
            if (
                rel_angle >= cls.OPPOSING_CURRENT_MIN_ANGLE_DEG
                and curr_spd >= cls.OPPOSING_CURRENT_MIN_SPEED_KTS
                and wave_h >= cls.OPPOSING_CURRENT_MIN_WAVE_M
            ):
                severity = "UNSAFE" if (curr_spd >= 2.2 or wave_h >= 2.0) else "CAUTION"
                hazards.append(
                    CompoundHazard(
                        hazard_code="COMPOUND_OPPOSING_CURRENT",
                        severity=severity,
                        title="Wave Steepening Opposing Surface Current",
                        description=(
                            f"Surface current of {curr_spd:.1f} kts directly opposes waves "
                            f"(relative angle {rel_angle:.0f}°), triggering dangerous wave steepening "
                            f"and breaking sea conditions."
                        ),
                        parameters_involved={
                            "current_speed_knots": curr_spd,
                            "current_direction_deg": curr_dir,
                            "wave_direction_deg": wave_dir,
                            "opposing_angle_deg": round(rel_angle, 1),
                        },
                        rule_version="RULE-COMPOUND-02: v1.2",
                    )
                )

        # 3. Shallow-Water Shoaling Breaker Hazard
        depth = inputs.bathymetric_depth_m
        if depth is not None and depth > 0:
            if wave_h > 0 and (depth <= 2.0 * wave_h or depth < cls.SHOALING_DEPTH_THRESHOLD_M):
                severity = "UNSAFE" if (depth <= 1.5 * wave_h and wave_h >= 1.5) else "CAUTION"
                hazards.append(
                    CompoundHazard(
                        hazard_code="COMPOUND_SHOALING_BREAKER",
                        severity=severity,
                        title="Shallow-Water Shoaling & Coastal Breakers",
                        description=(
                            f"Water depth ({depth:.1f}m) causes rapid wave shoaling and breaking "
                            f"for {wave_h:.1f}m incoming swell near shallow approaches."
                        ),
                        parameters_involved={
                            "bathymetric_depth_m": depth,
                            "wave_height_m": wave_h,
                            "depth_to_wave_ratio": round(depth / max(0.1, wave_h), 2),
                        },
                        rule_version="RULE-COMPOUND-03: v1.1",
                    )
                )

        return hazards
