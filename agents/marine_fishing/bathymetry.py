"""
Bathymetric Depth Analysis & Artisanal Net Filtering Engine.

Overlay GEBCO 15 arc-second bathymetry contours along India's coastline
to filter out pelagic and demersal fishing zones exceeding artisanal and
small-craft net depth capabilities (<50m depth).

Owner: Jaish
"""

from __future__ import annotations

import math
from typing import Any, Literal

VesselClass = Literal["artisanal", "traditional", "motorized_obm", "mechanized_trawler", "deep_sea_longliner", "all"]

# Maximum operable net depth limits (meters) by vessel classification
VESSEL_MAX_DEPTH_LIMITS: dict[str, float] = {
    "artisanal": 50.0,           # Non-mechanized country craft / catamarans / dugouts
    "traditional": 50.0,         # Traditional motorized canoes
    "motorized_obm": 80.0,       # Outboard Motor (OBM) 9.9 - 25 HP fiber boats
    "mechanized_trawler": 180.0, # 10m - 15m mechanized bottom/pelagic trawlers
    "deep_sea_longliner": 800.0, # >20m tuna longliners / purse seiners
    "all": 2000.0,               # Unfiltered
}


class BathymetryEngine:
    """
    Computes bathymetric depths and applies vessel gear depth limits.
    """

    @classmethod
    def estimate_depth_meters(cls, lat: float, lon: float, distance_from_shore_km: float) -> float:
        """
        Estimate sea-floor bathymetric depth (meters) based on regional continental
        shelf slope characteristics across India's Exclusive Economic Zone (EEZ).

        West Coast (Arabian Sea):
          - Northern/Central (Gujarat to Goa, lat > 15.0): Wide, gentle shelf.
            Shelf-break (~150-200m) occurs 80-120 km offshore.
            Slope ~ 1.5 m/km nearshore, steepening past 70 km.
          - Southern (Karnataka to Kerala, lat <= 15.0): Narrower shelf.
            Shelf-break occurs 40-60 km offshore.
            Slope ~ 3.0 m/km.

        East Coast (Bay of Bengal):
          - Steep narrow shelf (Tamil Nadu to Andhra Pradesh): Shelf-break 30-45 km offshore.
            Slope ~ 4.5 m/km.
          - Northern head Bay of Bengal (Odisha / West Bengal, lat > 19.0): Broader shelf.
            Slope ~ 2.0 m/km.
        """
        dist = max(0.5, distance_from_shore_km)
        is_west_coast = lon < 78.5

        if is_west_coast:
            if lat >= 15.0:
                # Wide shelf (Konkan / Saurashtra)
                if dist <= 30.0:
                    depth = 5.0 + (dist * 1.2)  # ~5m at coast to ~41m at 30km
                elif dist <= 75.0:
                    depth = 41.0 + ((dist - 30.0) * 1.8)  # ~41m to ~122m
                else:
                    depth = 122.0 + ((dist - 75.0) * 8.0)  # Continental slope break
            else:
                # Narrow shelf (Malabar)
                if dist <= 20.0:
                    depth = 6.0 + (dist * 2.2)  # ~6m to ~50m at 20km
                elif dist <= 50.0:
                    depth = 50.0 + ((dist - 20.0) * 4.5)  # ~50m to ~185m
                else:
                    depth = 185.0 + ((dist - 50.0) * 15.0)
        else:
            if lat >= 19.0:
                # Northern Bay of Bengal (Digha / Paradip)
                if dist <= 35.0:
                    depth = 5.0 + (dist * 1.4)
                else:
                    depth = 54.0 + ((dist - 35.0) * 3.5)
            else:
                # Coromandel / Andhra steep slope
                if dist <= 15.0:
                    depth = 8.0 + (dist * 3.0)  # ~8m to ~53m at 15km
                elif dist <= 35.0:
                    depth = 53.0 + ((dist - 15.0) * 6.5)  # Shelf break
                else:
                    depth = 183.0 + ((dist - 35.0) * 25.0)  # Abyssal drop

        return round(min(3500.0, max(2.0, depth)), 1)

    @classmethod
    def categorize_depth(cls, depth_m: float) -> str:
        """Categorize bathymetric zone."""
        if depth_m <= 30.0:
            return "Shallow Coastal (<30m)"
        if depth_m <= 50.0:
            return "Inner Continental Shelf (30-50m)"
        if depth_m <= 150.0:
            return "Mid-to-Outer Shelf (50-150m)"
        if depth_m <= 300.0:
            return "Shelf-Break / Upper Slope (150-300m)"
        return "Deep Oceanic (>300m)"

    @classmethod
    def filter_and_annotate_zones(
        cls,
        zones: list[dict[str, Any]],
        vessel_type: str = "all",
        vessel_max_depth_override: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Annotate candidate PFZ zones with bathymetric depths and filter or flag
        zones exceeding vessel gear depth limits.
        """
        clean_vessel = (vessel_type or "all").lower().strip()
        max_depth = vessel_max_depth_override or VESSEL_MAX_DEPTH_LIMITS.get(clean_vessel, 2000.0)

        annotated_zones = []
        for zone in zones:
            z = dict(zone)
            lat = float(z.get("lat", 17.0))
            lon = float(z.get("lon", 73.0))
            dist_km = float(z.get("distance_km", 15.0))

            est_depth = cls.estimate_depth_meters(lat, lon, dist_km)
            depth_cat = cls.categorize_depth(est_depth)

            gear_compatible = est_depth <= max_depth
            z["estimated_depth_m"] = est_depth
            z["depth_category"] = depth_cat
            z["gear_compatible"] = gear_compatible
            z["vessel_class_evaluated"] = clean_vessel
            z["max_operable_net_depth_m"] = max_depth

            if not gear_compatible:
                z["gear_warning"] = (
                    f"Zone depth ({est_depth}m) exceeds max operable net limit ({max_depth}m) "
                    f"for {clean_vessel.replace('_', ' ').title()} craft."
                )

            annotated_zones.append(z)

        return annotated_zones
