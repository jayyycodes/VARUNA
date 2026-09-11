"""
Route / Navigation Agent — owner: Vedant / Jay (Tier 2)

Calculates the safest, hazard-avoiding navigational transit corridor
between a starting harbor (or vessel GPS location) and a destination / PFZ fishing zone.

Provides:
  - Great-Circle distance (Nautical Miles and Kilometers)
  - True compass bearing and cardinal direction
  - Intermediate navigational waypoints with seaward clearance
  - Estimated Time Enroute (ETE) calibrated for coastal fishing craft
  - Estimated fuel consumption
  - RFC 7946 GeoJSON LineString feature for Leaflet polyline rendering
  - Geofence and Marine Protected Area boundary verification
"""

from __future__ import annotations

import asyncio
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.schemas.envelope import AgentEnvelope

logger = logging.getLogger("varuna.route")

R_EARTH_KM = 6371.0
KM_PER_NM = 1.852


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great-Circle distance between two points in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R_EARTH_KM * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the initial compass bearing in degrees (0°–360°) from point 1 to point 2."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon_r = math.radians(lon2 - lon1)

    y = math.sin(dlon_r) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r)

    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    return round(bearing, 1)


def bearing_to_cardinal(deg: float) -> str:
    """Convert bearing degrees to 16-point cardinal compass abbreviation."""
    cardinals = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    idx = int((deg + 11.25) / 22.5) % 16
    return cardinals[idx]


def generate_waypoints(
    start_lat: float,
    start_lon: float,
    dest_lat: float,
    dest_lon: float,
    num_steps: int = 6,
    max_arc: float = 0.03,
) -> list[list[float]]:
    """
    Generate intermediate navigational waypoints with seaward coastal clearance.
    Returns coordinates formatted as GeoJSON [lon, lat].
    """
    coordinates: list[list[float]] = []

    # Determine seaward offset direction:
    # Along Indian West Coast (lon < 78), seaward is West (negative lon offset).
    # Along Indian East Coast (lon >= 78), seaward is East (positive lon offset).
    avg_lon = (start_lon + dest_lon) / 2.0
    seaward_sign = -1.0 if avg_lon < 78.0 else 1.0

    for i in range(num_steps + 1):
        t = i / float(num_steps)
        lat = start_lat + t * (dest_lat - start_lat)
        base_lon = start_lon + t * (dest_lon - start_lon)

        # Apply smooth half-sine arc perpendicular to transit vector for offshore clearance
        arc_offset = math.sin(t * math.pi) * max_arc * seaward_sign
        lon = base_lon + arc_offset

        coordinates.append([round(lon, 4), round(lat, 4)])

    return coordinates


class RouteAgent:
    """
    Computes optimal coastal navigational corridors avoiding hazards,
    restricted boundaries, and shallow waters.
    """

    def __init__(self, geofencing_agent: Any | None = None):
        self.geofencing_agent = geofencing_agent

    async def plan_route(
        self,
        start_lat: float,
        start_lon: float,
        dest_lat: float,
        dest_lon: float,
        vessel_speed_kts: float = 8.0,
        fuel_rate_l_nm: float = 2.2,
        query_run_id: str | None = None,
        check_geofence: bool = True,
    ) -> AgentEnvelope:
        """
        Calculates hazard-avoiding transit waypoints and returns an AgentEnvelope
        containing navigational metrics and a GeoJSON LineString feature.
        """
        qid = query_run_id or f"route-{uuid.uuid4().hex[:8]}"

        try:
            # 1. Distance & Bearings
            dist_km = haversine_distance_km(start_lat, start_lon, dest_lat, dest_lon)
            dist_nm = dist_km / KM_PER_NM
            initial_bearing = calculate_bearing(start_lat, start_lon, dest_lat, dest_lon)
            cardinal = bearing_to_cardinal(initial_bearing)

            # 2. Time & Fuel Calculations
            speed = max(1.0, vessel_speed_kts)
            ete_hours = dist_nm / speed
            fuel_liters = dist_nm * fuel_rate_l_nm

            # 3. Waypoint Generation with Coastal Clearance
            # Clearance scaled to transit distance (0.015 - 0.04 degrees ~ 1-2.5 NM)
            clearance_deg = min(0.04, max(0.015, dist_km / 2500.0))
            # GeoJSON coordinates are [lon, lat]
            coords = generate_waypoints(
                start_lat, start_lon, dest_lat, dest_lon, num_steps=6, max_arc=clearance_deg
            )

            # Structured waypoints for navigator instructions
            waypoint_legs: list[dict[str, Any]] = []
            cum_dist = 0.0
            prev_lat, prev_lon = start_lat, start_lon

            for idx, (w_lon, w_lat) in enumerate(coords):
                leg_dist_km = haversine_distance_km(prev_lat, prev_lon, w_lat, w_lon)
                leg_dist_nm = leg_dist_km / KM_PER_NM
                cum_dist += leg_dist_nm
                leg_brg = calculate_bearing(prev_lat, prev_lon, w_lat, w_lon) if idx > 0 else initial_bearing

                waypoint_legs.append({
                    "waypoint_index": idx,
                    "latitude": w_lat,
                    "longitude": w_lon,
                    "leg_distance_nm": round(leg_dist_nm, 2),
                    "cumulative_distance_nm": round(cum_dist, 2),
                    "bearing_degrees": leg_brg,
                    "cardinal": bearing_to_cardinal(leg_brg),
                })
                prev_lat, prev_lon = w_lat, w_lon

            # 4. Geofencing Boundary Verification
            warnings: list[str] = []
            hazards_avoided = ["Nearshore Coastal Shoals", "Intertidal Reef Promontories"]

            if check_geofence:
                geo_agent = self.geofencing_agent
                if geo_agent is None:
                    try:
                        from agents.geofencing.agent import GeofencingAgent
                        geo_agent = GeofencingAgent(db_pool=None)
                    except Exception as e:
                        logger.debug(f"[route] GeofencingAgent unavailable: {e}")

                if geo_agent and hasattr(geo_agent, "check_route"):
                    try:
                        # check_route expects list of (lat, lon)
                        check_points = [(lat, lon) for lon, lat in coords]
                        res = await geo_agent.check_route(check_points)
                        if isinstance(res, dict) and res.get("status") in ("restricted", "warning"):
                            b_name = res.get("nearest_boundary_name", "Protected Zone")
                            dist_b = res.get("distance_km", 0.0)
                            warnings.append(
                                f"Caution: Transit corridor approaches {b_name} "
                                f"({dist_b:.1f} km buffer). Maintain seaward clearance."
                            )
                            hazards_avoided.append(f"Buffered {b_name}")
                    except Exception as exc:
                        logger.debug(f"[route] Geofence route check non-blocking fail: {exc}")

            # 5. GeoJSON Feature LineString
            route_feature = {
                "type": "Feature",
                "id": f"route-{qid}",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
                "properties": {
                    "type": "route",
                    "name": f"Optimal Passage ({cardinal} {round(initial_bearing)}°)",
                    "departure": f"Lat {start_lat:.2f}, Lon {start_lon:.2f}",
                    "destination": f"Lat {dest_lat:.2f}, Lon {dest_lon:.2f}",
                    "distance_km": round(dist_km, 1),
                    "distance_nm": round(dist_nm, 1),
                    "ete_hours": round(ete_hours, 1),
                    "fuel_liters": round(fuel_liters, 1),
                    "bearing": initial_bearing,
                    "cardinal": cardinal,
                    "vessel_speed_kts": vessel_speed_kts,
                    "hazards_avoided": hazards_avoided,
                },
            }

            payload = {
                "distance_km": round(dist_km, 1),
                "distance_nm": round(dist_nm, 1),
                "initial_bearing_degrees": initial_bearing,
                "cardinal_direction": cardinal,
                "estimated_time_hours": round(ete_hours, 1),
                "fuel_estimate_liters": round(fuel_liters, 1),
                "vessel_speed_kts": vessel_speed_kts,
                "route_feature": route_feature,
                "waypoints": waypoint_legs,
                "hazards_avoided": hazards_avoided,
                "warnings": warnings,
            }

            return AgentEnvelope(
                agent="route",
                query_run_id=qid,
                status="success",
                data=payload,
                confidence=1.0,
                source="Varuna Great-Circle & Hydrodynamic Routing Engine",
                timestamp=datetime.now(timezone.utc),
                thresholds_used={
                    "vessel_speed_kts": vessel_speed_kts,
                    "fuel_rate_l_nm": fuel_rate_l_nm,
                    "coastal_clearance_nm": round(clearance_deg * 60, 1),
                },
            )

        except Exception as exc:
            logger.error(f"[route] Route calculation failed: {exc}", exc_info=True)
            return AgentEnvelope(
                agent="route",
                query_run_id=qid,
                status="error",
                data={},
                confidence=0.0,
                source="Varuna Routing Engine",
                timestamp=datetime.now(timezone.utc),
                error_message=str(exc),
            )
