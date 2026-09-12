"""
Route / Navigation Agent — owner: Vedant / Jay (Tier 2)

Calculates the safest, hazard-avoiding navigational transit corridor
using a Hierarchical A* pathfinding algorithm over dynamic grids.
"""

from __future__ import annotations

import asyncio
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any, List, Tuple

from backend.schemas.envelope import AgentEnvelope
from agents.geofencing.queries import check_geofence
from agents.route.grid import build_bounding_box, calculate_resolution
from agents.route.pathfinding import a_star_search, heuristic

logger = logging.getLogger("varuna.route")

R_EARTH_KM = 6371.0
KM_PER_NM = 1.852

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return heuristic(lat1, lon1, lat2, lon2)

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon_r = math.radians(lon2 - lon1)
    y = math.sin(dlon_r) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    return round(bearing, 1)

def bearing_to_cardinal(deg: float) -> str:
    cardinals = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((deg + 11.25) / 22.5) % 16
    return cardinals[idx]

def interpolate_segment(p1: Tuple[float, float], p2: Tuple[float, float], step_km: float = 1.0) -> List[Tuple[float, float]]:
    """Interpolate points between two coordinates at roughly `step_km` intervals."""
    dist = haversine_distance_km(p1[0], p1[1], p2[0], p2[1])
    if dist <= step_km:
        return [p1, p2]
    
    num_steps = int(math.ceil(dist / step_km))
    points = []
    for i in range(num_steps + 1):
        t = i / float(num_steps)
        lat = p1[0] + t * (p2[0] - p1[0])
        lon = p1[1] + t * (p2[1] - p1[1])
        points.append((round(lat, 4), round(lon, 4)))
    return points

class RouteAgent:
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
        check_geofence_flag: bool = True,
    ) -> AgentEnvelope:
        qid = query_run_id or f"route-{uuid.uuid4().hex[:8]}"
        
        try:
            dist_km = haversine_distance_km(start_lat, start_lon, dest_lat, dest_lon)
            dist_nm = dist_km / KM_PER_NM
            initial_bearing = calculate_bearing(start_lat, start_lon, dest_lat, dest_lon)
            cardinal = bearing_to_cardinal(initial_bearing)

            # Lazy init GeofencingAgent
            geo_agent = self.geofencing_agent
            if geo_agent is None:
                try:
                    from agents.geofencing.agent import GeofencingAgent
                    geo_agent = GeofencingAgent(db_pool=None)
                except Exception as e:
                    logger.error(f"[route] GeofencingAgent unavailable: {e}")
                    raise RuntimeError("GeofencingAgent is required for RouteAgent.")

            # Run the heavy hierarchical A* in a background thread to prevent blocking the async event loop
            result_payload = await asyncio.to_thread(
                self._run_hierarchical_pathfinding_sync,
                start_lat, start_lon, dest_lat, dest_lon, geo_agent, dist_km
            )

            if result_payload["route_status"] == "restricted":
                # Boxed-in fallback (No safe route)
                return AgentEnvelope(
                    agent="route",
                    query_run_id=qid,
                    status="success",
                    data=result_payload,
                    confidence=1.0,
                    source="Varuna Hierarchical A* Routing Engine",
                    timestamp=datetime.now(timezone.utc),
                )
                
            # Path found successfully
            coords = result_payload["route_geometry"]["coordinates"]
            
            # Format waypoints and calculate final distances
            waypoint_legs: list[dict[str, Any]] = []
            safe_cum_dist_nm = 0.0
            prev_lat, prev_lon = start_lat, start_lon

            for idx, (w_lon, w_lat) in enumerate(coords):
                leg_dist_km = haversine_distance_km(prev_lat, prev_lon, w_lat, w_lon)
                leg_dist_nm = leg_dist_km / KM_PER_NM
                safe_cum_dist_nm += leg_dist_nm
                leg_brg = calculate_bearing(prev_lat, prev_lon, w_lat, w_lon) if idx > 0 else initial_bearing

                waypoint_legs.append({
                    "waypoint_index": idx,
                    "latitude": w_lat,
                    "longitude": w_lon,
                    "leg_distance_nm": round(leg_dist_nm, 2),
                    "cumulative_distance_nm": round(safe_cum_dist_nm, 2),
                    "bearing_degrees": leg_brg,
                    "cardinal": bearing_to_cardinal(leg_brg),
                })
                prev_lat, prev_lon = w_lat, w_lon

            actual_safe_dist_nm = safe_cum_dist_nm
            actual_safe_dist_km = actual_safe_dist_nm * KM_PER_NM
            speed = max(1.0, vessel_speed_kts)
            safe_ete_hours = actual_safe_dist_nm / speed
            safe_fuel_liters = actual_safe_dist_nm * fuel_rate_l_nm

            direct_ete_hours = dist_nm / speed
            direct_fuel_liters = dist_nm * fuel_rate_l_nm

            safe_route_feature = {
                "type": "Feature",
                "id": f"route-safe-{qid}",
                "geometry": result_payload["route_geometry"],
                "properties": {
                    "type": "route",
                    "route_variant": "safe",
                    "name": f"Optimal Safe Passage ({cardinal} {round(initial_bearing)}°)",
                    "departure": f"Lat {start_lat:.2f}, Lon {start_lon:.2f}",
                    "destination": f"Lat {dest_lat:.2f}, Lon {dest_lon:.2f}",
                    "distance_km": round(actual_safe_dist_km, 1),
                    "distance_nm": round(actual_safe_dist_nm, 1),
                    "ete_hours": round(safe_ete_hours, 1),
                    "fuel_liters": round(safe_fuel_liters, 1),
                    "vessel_speed_kts": vessel_speed_kts,
                    "is_recommended": True,
                },
            }

            payload = {
                "route_status": "clear",
                "distance_km": round(actual_safe_dist_km, 1),
                "distance_nm": round(actual_safe_dist_nm, 1),
                "initial_bearing_degrees": initial_bearing,
                "cardinal_direction": cardinal,
                "estimated_time_hours": round(safe_ete_hours, 1),
                "fuel_estimate_liters": round(safe_fuel_liters, 1),
                "vessel_speed_kts": vessel_speed_kts,
                "route_feature": safe_route_feature,
                "waypoints": waypoint_legs,
                "comparison": {
                    "safe_distance_nm": round(actual_safe_dist_nm, 1),
                    "direct_distance_nm": round(dist_nm, 1),
                    "delta_distance_nm": round(actual_safe_dist_nm - dist_nm, 1),
                    "safe_fuel_liters": round(safe_fuel_liters, 1),
                    "direct_fuel_liters": round(direct_fuel_liters, 1),
                    "delta_fuel_liters": round(safe_fuel_liters - direct_fuel_liters, 1),
                },
                "warnings": result_payload.get("warnings", []),
            }

            return AgentEnvelope(
                agent="route",
                query_run_id=qid,
                status="success",
                data=payload,
                confidence=1.0,
                source="Varuna Hierarchical A* Routing Engine",
                timestamp=datetime.now(timezone.utc),
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

    def _run_hierarchical_pathfinding_sync(self, start_lat, start_lon, dest_lat, dest_lon, geo_agent, dist_km) -> dict:
        """Synchronous wrapper for database connection checking and hierarchical A*."""
        conn = geo_agent.db_pool.getconn()
        try:
            def is_safe(lat: float, lon: float) -> bool:
                status_val, _, _ = check_geofence(conn, lat, lon)
                return status_val != "restricted" # Treat warnings as passable, restricted as wall

            start = (start_lat, start_lon)
            dest = (dest_lat, dest_lon)
            
            # Step 1: Coarse Pass
            coarse_res = calculate_resolution(dist_km)
            bbox = build_bounding_box(start_lat, start_lon, dest_lat, dest_lon, padding_pct=0.15)
            
            coarse_path = a_star_search(start, dest, coarse_res, bbox, is_safe)
            
            if not coarse_path:
                return {
                    "route_status": "restricted",
                    "route_geometry": None,
                    "reason": "no safe corridor found within search bounds"
                }
                
            # Step 2: Fine-Resolution Safety Sweep
            spliced_path = []
            warnings = []
            
            for i in range(len(coarse_path) - 1):
                p1 = coarse_path[i]
                p2 = coarse_path[i+1]
                spliced_path.append(p1)
                
                # Interpolate segment at 1km intervals
                fine_points = interpolate_segment(p1, p2, step_km=1.0)
                segment_safe = True
                
                for fp in fine_points:
                    if not is_safe(fp[0], fp[1]):
                        segment_safe = False
                        break
                        
                if not segment_safe:
                    # Step 3: Local Nudging (Hierarchical A*)
                    # Padding local bounding box by 2 coarse cells
                    pad = coarse_res * 2.0
                    local_bbox = (
                        min(p1[0], p2[0]) - pad,
                        max(p1[0], p2[0]) + pad,
                        min(p1[1], p2[1]) - pad,
                        max(p1[1], p2[1]) + pad
                    )
                    
                    fine_res = coarse_res / 5.0 # High resolution local search
                    local_path = a_star_search(p1, p2, fine_res, local_bbox, is_safe)
                    
                    if local_path:
                        # Splice local detour (skipping first point to avoid duplicate)
                        spliced_path.extend(local_path[1:-1])
                        warnings.append(f"Applied hierarchical fine-search detour near {p1}.")
                    else:
                        # Fallback: if even local nudge fails, the route is unsafe.
                        return {
                            "route_status": "restricted",
                            "route_geometry": None,
                            "reason": f"fine-resolution local detour failed between {p1} and {p2}"
                        }

            # Add final destination node
            spliced_path.append(coarse_path[-1])
            
            # Format to GeoJSON coordinates: [lon, lat]
            geojson_coords = [[lon, lat] for lat, lon in spliced_path]
            
            return {
                "route_status": "clear",
                "route_geometry": {
                    "type": "LineString",
                    "coordinates": geojson_coords
                },
                "warnings": warnings
            }

        finally:
            geo_agent.db_pool.putconn(conn)
