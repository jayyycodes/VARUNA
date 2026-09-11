"""
Tests for Tier-2 Route / Navigation Agent (agents/route/route_agent.py).
"""

import pytest
from agents.route.route_agent import (
    RouteAgent,
    bearing_to_cardinal,
    calculate_bearing,
    haversine_distance_km,
)


def test_haversine_distance_calculation():
    """Verify Great-Circle distance matches expected nautical distance."""
    # Ratnagiri harbor to Malvan harbor (~106 km / ~57.5 NM)
    dist_km = haversine_distance_km(16.99, 73.30, 16.05, 73.47)
    assert 100.0 < dist_km < 115.0

    # Zero distance
    zero_dist = haversine_distance_km(16.99, 73.30, 16.99, 73.30)
    assert zero_dist == pytest.approx(0.0, abs=1e-3)


def test_bearing_and_cardinal_calculation():
    """Verify compass bearing angles and 16-point cardinal directions."""
    # North
    b_north = calculate_bearing(10.0, 75.0, 12.0, 75.0)
    assert b_north == pytest.approx(0.0, abs=1.0)
    assert bearing_to_cardinal(b_north) == "N"

    # South
    b_south = calculate_bearing(12.0, 75.0, 10.0, 75.0)
    assert b_south == pytest.approx(180.0, abs=1.0)
    assert bearing_to_cardinal(b_south) == "S"

    # East
    b_east = calculate_bearing(10.0, 75.0, 10.0, 77.0)
    assert 85.0 < b_east < 95.0
    assert "E" in bearing_to_cardinal(b_east)

    # Ratnagiri (16.99N, 73.30E) to Malvan (16.05N, 73.47E) -> South-Southeast
    b_ratnagiri_malvan = calculate_bearing(16.99, 73.30, 16.05, 73.47)
    assert 160.0 < b_ratnagiri_malvan < 180.0
    assert bearing_to_cardinal(b_ratnagiri_malvan) in ("S", "SSE")


@pytest.mark.asyncio
async def test_route_agent_plan_route_happy_path():
    """Verify RouteAgent returns a valid AgentEnvelope with correct metrics and GeoJSON."""
    agent = RouteAgent(geofencing_agent=None)
    envelope = await agent.plan_route(
        start_lat=16.99,
        start_lon=73.30,
        dest_lat=16.05,
        dest_lon=73.47,
        vessel_speed_kts=8.0,
        fuel_rate_l_nm=2.2,
    )

    assert envelope.agent == "route"
    assert envelope.status == "success"
    assert envelope.confidence == 1.0

    data = envelope.data
    assert "distance_km" in data
    assert "distance_nm" in data
    assert "estimated_time_hours" in data
    assert "fuel_estimate_liters" in data
    assert "route_feature" in data
    assert "waypoints" in data

    # Distance assertions
    assert 100.0 < data["distance_km"] < 115.0
    assert 54.0 < data["distance_nm"] < 63.0

    # Speed & Fuel assertions (8 kts, 2.2 L/NM)
    expected_ete = data["distance_nm"] / 8.0
    assert data["estimated_time_hours"] == pytest.approx(expected_ete, abs=0.2)

    expected_fuel = data["distance_nm"] * 2.2
    assert data["fuel_estimate_liters"] == pytest.approx(expected_fuel, abs=0.5)

    # GeoJSON Feature validation (RFC 7946 coordinates [lon, lat])
    feat = data["route_feature"]
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "LineString"
    coords = feat["geometry"]["coordinates"]
    assert len(coords) == 7  # 6 steps = 7 points

    # First coord is departure [start_lon, start_lat]
    assert coords[0] == [73.30, 16.99]
    # Last coord is destination [dest_lon, dest_lat]
    assert coords[-1] == [73.47, 16.05]

    props = feat["properties"]
    assert props["type"] == "route"
    assert "Optimal Safe Passage" in props["name"] or "Optimal Passage" in props["name"]


@pytest.mark.asyncio
async def test_route_agent_coastal_clearance_west_coast():
    """Verify intermediate waypoints apply seaward offshore clearance on West Coast."""
    agent = RouteAgent(geofencing_agent=None)
    envelope = await agent.plan_route(
        start_lat=16.99,
        start_lon=73.30,
        dest_lat=16.05,
        dest_lon=73.47,
    )
    coords = envelope.data["route_feature"]["geometry"]["coordinates"]

    # Midpoint waypoint (index 3) should have lon shifted slightly westward (seaward)
    # Base straight-line lon at midpoint t=0.5 would be (73.30 + 73.47)/2 = 73.385
    # Seaward arc offsets lon to the West (< 73.385)
    mid_lon, mid_lat = coords[3]
    base_mid_lon = (73.30 + 73.47) / 2.0
    assert mid_lon < base_mid_lon


@pytest.mark.asyncio
async def test_route_agent_with_geofence_boundary_warning():
    """Verify RouteAgent captures geofencing proximity warnings if detected along corridor."""
    class MockGeofencingAgent:
        async def check_route(self, waypoints):
            return {
                "status": "warning",
                "nearest_boundary_name": "Malvan Marine Sanctuary Buffer",
                "distance_km": 1.4,
            }

    agent = RouteAgent(geofencing_agent=MockGeofencingAgent())
    envelope = await agent.plan_route(
        start_lat=16.99,
        start_lon=73.30,
        dest_lat=16.05,
        dest_lon=73.47,
    )

    assert envelope.status == "success"
    warnings = envelope.data["warnings"]
    assert len(warnings) > 0
    assert "Malvan Marine Sanctuary Buffer" in warnings[0]
    assert "Buffered Malvan Marine Sanctuary Buffer" in envelope.data["hazards_avoided"]


@pytest.mark.asyncio
async def test_planner_route_integration():
    """Verify Planner orchestrates RouteAgent when user queries navigation between two ports."""
    from agents.planner.planner_agent import PlannerAgent
    planner = PlannerAgent()
    result = await planner.handle_query("What is the safest route from Ratnagiri to Malvan?")

    assert result["status"] == "success"
    assert "text" in result
    assert "map_data" in result
    assert "features" in result["map_data"]

    # Verify a LineString route feature was added to map_data
    features = result["map_data"]["features"]
    route_features = [f for f in features if f.get("properties", {}).get("type") == "route"]
    assert len(route_features) >= 1

    route_f = route_features[0]
    assert route_f["geometry"]["type"] == "LineString"
    assert len(route_f["geometry"]["coordinates"]) >= 5

    # Verify route evidence was included in evidence trail
    evidence = result.get("evidence", [])
    route_evidence = [ev for ev in evidence if ev.get("agent") == "route"]
    assert len(route_evidence) >= 1
    assert "distance_nm" in route_evidence[0]

