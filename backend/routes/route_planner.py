"""
Route Navigation & Safe Corridor Planning API
Direct endpoint exposing Vedant's RouteAgent for on-demand
dual-route comparison (Safe Passage vs Direct Baseline).
"""

from __future__ import annotations

import uuid
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.route.route_agent import RouteAgent

router = APIRouter(prefix="/api/route", tags=["route"])

# Well-known coastal port coordinates for easy lookup
COASTAL_PORTS: dict[str, dict[str, float]] = {
    "ratnagiri": {"lat": 16.989, "lon": 73.284, "name": "Ratnagiri Harbour"},
    "malvan": {"lat": 16.052, "lon": 73.468, "name": "Malvan Port"},
    "mumbai": {"lat": 18.922, "lon": 72.834, "name": "Mumbai Sassoon Docks"},
    "alibaug": {"lat": 18.641, "lon": 72.872, "name": "Alibaug Port"},
    "goa": {"lat": 15.498, "lon": 73.827, "name": "Mormugao Port, Goa"},
    "karwar": {"lat": 14.805, "lon": 74.133, "name": "Karwar Fisheries Harbour"},
    "mangalore": {"lat": 12.868, "lon": 74.842, "name": "New Mangalore Port"},
    "cochin": {"lat": 9.967, "lon": 76.242, "name": "Cochin Fisheries Harbour"},
    "vizhinjam": {"lat": 8.375, "lon": 76.991, "name": "Vizhinjam Port"},
    "chennai": {"lat": 13.125, "lon": 80.312, "name": "Chennai Kasimedu Harbour"},
    "visakhapatnam": {"lat": 17.686, "lon": 83.218, "name": "Visakhapatnam Port"},
}


class RoutePlanRequest(BaseModel):
    departure_port: Optional[str] = None
    destination_port: Optional[str] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    vessel_speed_kts: float = Field(default=8.0, ge=2.0, le=35.0)


class RoutePlanResponse(BaseModel):
    query_run_id: str
    status: str
    departure: dict[str, Any]
    destination: dict[str, Any]
    distance_nm: float
    distance_km: float
    estimated_time_hours: float
    fuel_estimate_liters: float
    cardinal_direction: str
    initial_bearing_degrees: float
    hazards_avoided: list[str]
    warnings: list[str]
    safe_route_feature: dict[str, Any]
    direct_route_feature: dict[str, Any]
    feature_collection: dict[str, Any]


@router.post("/plan", response_model=RoutePlanResponse)
async def plan_route(req: RoutePlanRequest):
    """
    Computes an optimal safe coastal route avoiding nearshore hazards and MPAs,
    contrasted against an unbuffered direct rhumb line baseline.
    """
    # Resolve departure coordinates
    start_lat = req.start_lat
    start_lon = req.start_lon
    dep_name = "Custom Departure"

    if req.departure_port and req.departure_port.lower() in COASTAL_PORTS:
        port = COASTAL_PORTS[req.departure_port.lower()]
        start_lat = port["lat"]
        start_lon = port["lon"]
        dep_name = port["name"]

    # Resolve destination coordinates
    dest_lat = req.dest_lat
    dest_lon = req.dest_lon
    dest_name = "Custom Destination"

    if req.destination_port and req.destination_port.lower() in COASTAL_PORTS:
        port = COASTAL_PORTS[req.destination_port.lower()]
        dest_lat = port["lat"]
        dest_lon = port["lon"]
        dest_name = port["name"]

    if start_lat is None or start_lon is None or dest_lat is None or dest_lon is None:
        raise HTTPException(
            status_code=400,
            detail="Valid departure and destination coordinates or recognized port names required.",
        )

    qid = f"route-{uuid.uuid4().hex[:8]}"
    agent = RouteAgent()
    envelope = await agent.plan_route(
        start_lat=start_lat,
        start_lon=start_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        vessel_speed_kts=req.vessel_speed_kts,
        query_run_id=qid,
    )

    data = envelope.data
    return RoutePlanResponse(
        query_run_id=qid,
        status="success",
        departure={"name": dep_name, "lat": start_lat, "lon": start_lon},
        destination={"name": dest_name, "lat": dest_lat, "lon": dest_lon},
        distance_nm=data.get("distance_nm", 0.0),
        distance_km=data.get("distance_km", 0.0),
        estimated_time_hours=data.get("estimated_time_hours", 0.0),
        fuel_estimate_liters=data.get("fuel_estimate_liters", 0.0),
        cardinal_direction=data.get("cardinal_direction", "S"),
        initial_bearing_degrees=data.get("initial_bearing_degrees", 180.0),
        hazards_avoided=data.get("hazards_avoided", []),
        warnings=data.get("warnings", []),
        safe_route_feature=data.get("route_feature", {}),
        direct_route_feature=data.get("direct_route_feature", {}),
        feature_collection=data.get("dual_route_geojson", {}),
    )


@router.get("/ports")
async def list_ports():
    """Returns catalog of supported Indian coastal ports for route auto-completion."""
    return [{"id": k, **v} for k, v in COASTAL_PORTS.items()]
