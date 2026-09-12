"""
Tests for Tier-2 Route / Navigation Agent (agents/route/route_agent.py).
Focuses on Hierarchical A* pathfinding, fallbacks, and performance constraints.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from agents.route.route_agent import (
    RouteAgent,
    bearing_to_cardinal,
    calculate_bearing,
    haversine_distance_km,
)
from backend.schemas.envelope import AgentEnvelope

class MockPool:
    def getconn(self): return "mock_conn"
    def putconn(self, conn): pass

class MockGeoAgent:
    def __init__(self):
        self.db_pool = MockPool()

def mock_check_geofence_clear(conn, lat, lon):
    return "clear", "Ocean", 100.0

def mock_check_geofence_wall(conn, lat, lon):
    if 74.0 <= lon <= 74.2 and 15.8 <= lat <= 16.2:
        return "restricted", "Wall Zone", 0.0
    return "clear", "Ocean", 100.0

def mock_check_geofence_small_tunnel(conn, lat, lon):
    # Place the MPA exactly on the A* path's horizontal segment at lat 16.108, lon ~74.05
    # The coarse nodes are 74.040 and 74.067. This tiny block falls exactly between them.
    if 74.048 <= lon <= 74.052 and 16.106 <= lat <= 16.110:
        return "restricted", "Small MPA", 0.0
    return "clear", "Ocean", 100.0

def mock_check_geofence_boxed_in(conn, lat, lon):
    if 73.8 <= lon <= 74.2 and 15.8 <= lat <= 16.2:
        if (lat, lon) != (16.5, 73.5):
            return "restricted", "Boxed In", 0.0
    return "clear", "Ocean", 100.0


@pytest.mark.asyncio
@patch('agents.route.route_agent.check_geofence', side_effect=mock_check_geofence_clear)
async def test_route_clear_ocean(mock_check):
    agent = RouteAgent(geofencing_agent=MockGeoAgent())
    envelope = await agent.plan_route(16.0, 73.0, 16.0, 75.0)
    assert envelope.status == "success"
    assert envelope.data["route_status"] == "clear"


@pytest.mark.asyncio
@patch('agents.route.route_agent.check_geofence', side_effect=mock_check_geofence_wall)
async def test_route_hazard_detour(mock_check):
    agent = RouteAgent(geofencing_agent=MockGeoAgent())
    envelope = await agent.plan_route(16.0, 73.0, 16.0, 75.5)
    assert envelope.status == "success"
    assert envelope.data["route_status"] == "clear"


@pytest.mark.asyncio
@patch('agents.route.route_agent.check_geofence', side_effect=mock_check_geofence_small_tunnel)
async def test_route_small_mpa_tunneling(mock_check):
    agent = RouteAgent(geofencing_agent=MockGeoAgent())
    envelope = await agent.plan_route(16.0, 73.5, 16.1, 74.5)
    assert envelope.status == "success"
    assert envelope.data["route_status"] == "clear"
    assert len(envelope.data.get("warnings", [])) > 0
    assert "Applied hierarchical fine-search detour" in envelope.data["warnings"][0]


@pytest.mark.asyncio
@patch('agents.route.route_agent.check_geofence', side_effect=mock_check_geofence_boxed_in)
async def test_route_no_safe_route_fallback(mock_check):
    agent = RouteAgent(geofencing_agent=MockGeoAgent())
    envelope = await agent.plan_route(16.5, 73.5, 16.0, 74.0)
    assert envelope.status == "success"
    assert envelope.data["route_status"] == "restricted"
    assert envelope.data.get("route_geometry") is None


@pytest.mark.asyncio
@patch('agents.route.route_agent.check_geofence', side_effect=mock_check_geofence_clear)
async def test_benchmark_long_route(mock_check):
    agent = RouteAgent(geofencing_agent=MockGeoAgent())
    t0 = time.perf_counter()
    envelope = await agent.plan_route(19.0, 72.8, 7.0, 79.8)
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000
    assert envelope.status == "success"
    assert envelope.data["route_status"] == "clear"
    assert latency_ms < 500.0, f"Benchmark failed: {latency_ms:.2f}ms"
