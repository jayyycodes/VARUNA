"""
Varuna (ORCA) — Time-to-Shelter Evacuation Estimator.
Calculates transit duration to nearest designated port of refuge and evaluates
whether incoming squalls or gale fronts will intercept the vessel prior to safe return.

Owner: Jaish
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# Baseline designated ports of refuge along Indian coasts
DESIGNATED_REFUGE_PORTS: List[Dict[str, Any]] = [
    {"name": "Ratnagiri Mirya Bay", "lat": 17.00, "lon": 73.28, "coast": "West - Konkan"},
    {"name": "Malvan Fishery Port", "lat": 16.05, "lon": 73.47, "coast": "West - Konkan"},
    {"name": "Marmagao Harbor", "lat": 15.41, "lon": 73.80, "coast": "West - Goa"},
    {"name": "Karwar Port", "lat": 14.80, "lon": 74.13, "coast": "West - Karnataka"},
    {"name": "New Mangalore Port", "lat": 12.92, "lon": 74.82, "coast": "West - Karnataka"},
    {"name": "Kochi Harbor", "lat": 9.96, "lon": 76.24, "coast": "West - Malabar"},
    {"name": "Veraval Harbor", "lat": 20.90, "lon": 70.37, "coast": "West - Saurashtra"},
    {"name": "Porbandar Port", "lat": 21.64, "lon": 69.60, "coast": "West - Saurashtra"},
    {"name": "Okha Port", "lat": 22.47, "lon": 69.07, "coast": "West - Gujarat"},
    {"name": "Tuticorin Port", "lat": 8.75, "lon": 78.18, "coast": "East - Tamil Nadu"},
    {"name": "Chennai Harbor", "lat": 13.08, "lon": 80.29, "coast": "East - Coromandel"},
    {"name": "Visakhapatnam Outer Harbor", "lat": 17.68, "lon": 83.30, "coast": "East - Andhra Pradesh"},
    {"name": "Paradip Port", "lat": 20.26, "lon": 86.67, "coast": "East - Odisha"},
    {"name": "Digha Fishery Wharf", "lat": 21.62, "lon": 87.52, "coast": "East - West Bengal"},
    {"name": "Kavaratti Port", "lat": 10.56, "lon": 72.63, "coast": "Lakshadweep"},
    {"name": "Port Blair Port", "lat": 11.66, "lon": 92.73, "coast": "Andaman & Nicobar"},
]

# Vessel cruise speed in km/h
VESSEL_SPEEDS_KMH: Dict[str, float] = {
    "traditional_craft": 9.26,       # ~5.0 knots
    "country_craft": 9.26,
    "artisanal": 9.26,
    "mechanized_trawler": 15.74,     # ~8.5 knots
    "standard": 15.74,
    "deep_sea_longliner": 22.22,     # ~12.0 knots
    "commercial": 22.22,
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class EvacuationAssessment(BaseModel):
    """Result of time-to-shelter evacuation calculation."""
    nearest_port_name: str
    port_distance_km: float
    vessel_speed_kmh: float
    transit_duration_hours: float
    squall_distance_km: Optional[float] = None
    squall_speed_kmh: Optional[float] = None
    time_to_squall_intercept_hours: Optional[float] = None
    safety_margin_hours: Optional[float] = None
    evacuation_feasible: bool = True
    evacuation_hazard_code: Optional[str] = None
    advisory_notes: str
    rule_version: str = "RULE-EVAC-01: v1.0"


class EvacuationEngine:
    """Computes vessel evacuation metrics to coastal ports of refuge."""

    @classmethod
    def find_nearest_port(cls, lat: float, lon: float) -> Tuple[Dict[str, Any], float]:
        nearest_port = DESIGNATED_REFUGE_PORTS[0]
        min_dist = float("inf")
        for p in DESIGNATED_REFUGE_PORTS:
            d = _haversine_km(lat, lon, p["lat"], p["lon"])
            if d < min_dist:
                min_dist = d
                nearest_port = p
        return nearest_port, min_dist

    @classmethod
    def evaluate_evacuation(
        cls,
        lat: float,
        lon: float,
        vessel_type: str = "mechanized_trawler",
        squall_distance_km: Optional[float] = None,
        squall_speed_kmh: float = 35.0,
    ) -> EvacuationAssessment:
        nearest_port, dist_km = cls.find_nearest_port(lat, lon)
        speed_kmh = VESSEL_SPEEDS_KMH.get(vessel_type.lower(), 15.74)
        transit_hours = dist_km / max(1.0, speed_kmh)

        time_to_squall: Optional[float] = None
        safety_margin: Optional[float] = None
        feasible = True
        hazard_code: Optional[str] = None

        if squall_distance_km is not None and squall_distance_km > 0:
            time_to_squall = squall_distance_km / max(5.0, squall_speed_kmh)
            safety_margin = time_to_squall - transit_hours

            if safety_margin < 0.5:
                # Squall arrives well before vessel reaches harbor
                feasible = False
                hazard_code = "EVACUATION_INTERCEPT_IMMINENT"
                advisory = (
                    f"CRITICAL: Approaching squall will intercept vessel {abs(safety_margin):.1f}h "
                    f"before reaching {nearest_port['name']} ({dist_km:.1f}km away). Seek immediate local anchorage."
                )
            elif safety_margin < 1.5:
                # Tight margin
                feasible = True
                hazard_code = "EVACUATION_MARGIN_TIGHT"
                advisory = (
                    f"CAUTION: Narrow evacuation window ({safety_margin:.1f}h margin) "
                    f"to {nearest_port['name']} before squall arrival."
                )
            else:
                feasible = True
                advisory = (
                    f"Safe evacuation margin ({safety_margin:.1f}h) to reach "
                    f"{nearest_port['name']} ({dist_km:.1f}km away at {speed_kmh:.1f} km/h)."
                )
        else:
            advisory = (
                f"Nearest port of refuge is {nearest_port['name']} ({dist_km:.1f}km away, "
                f"approx {transit_hours:.1f}h transit at {speed_kmh:.1f} km/h)."
            )

        return EvacuationAssessment(
            nearest_port_name=nearest_port["name"],
            port_distance_km=round(dist_km, 2),
            vessel_speed_kmh=round(speed_kmh, 2),
            transit_duration_hours=round(transit_hours, 2),
            squall_distance_km=round(squall_distance_km, 2) if squall_distance_km else None,
            squall_speed_kmh=round(squall_speed_kmh, 2) if squall_distance_km else None,
            time_to_squall_intercept_hours=round(time_to_squall, 2) if time_to_squall else None,
            safety_margin_hours=round(safety_margin, 2) if safety_margin else None,
            evacuation_feasible=feasible,
            evacuation_hazard_code=hazard_code,
            advisory_notes=advisory,
            rule_version="RULE-EVAC-01: v1.0",
        )
