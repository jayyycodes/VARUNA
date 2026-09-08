import pytest
import asyncio
from agents.geofencing.agent import GeofencingAgent
from agents.geofencing.models import GeofencingRequest

@pytest.fixture
def agent():
    return GeofencingAgent(db_pool=None)

@pytest.mark.asyncio
async def test_deep_ocean_clear(agent):
    # Somewhere far into the Indian Ocean, away from EEZs and MPAs
    # e.g., 5.0 N, 90.0 E
    req = GeofencingRequest(query_run_id="test-1", lat=5.0, lon=90.0)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "clear"

@pytest.mark.asyncio
async def test_inside_indian_eez_clear(agent):
    # E.g. off the coast of Mumbai
    # 18.0 N, 71.0 E
    req = GeofencingRequest(query_run_id="test-2", lat=18.0, lon=71.0)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "clear"
    
@pytest.mark.asyncio
async def test_sri_lanka_eez_restricted(agent):
    # Test 4: Inside Sri Lanka EEZ (ocean, not landmass)
    # 7.5 N, 79.0 E
    req = GeofencingRequest(query_run_id="test-4", lat=7.5, lon=79.0)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "restricted"
    assert "Sri Lanka" in res.data["nearest_boundary_name"]
    assert res.data["distance_km"] == 0.0

@pytest.mark.asyncio
async def test_sri_lanka_imbl_warning(agent):
    # Test 3: Near Sri Lanka IMBL (1.39 km away)
    req = GeofencingRequest(query_run_id="test-3", lat=7.5, lon=78.705)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "warning"
    assert "Sri Lanka" in res.data["nearest_boundary_name"]

@pytest.mark.asyncio
async def test_mpa_restricted(agent):
    # Test 5: Inside an MPA (Kaziranga)
    req = GeofencingRequest(query_run_id="test-5", lat=26.60, lon=93.379)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "restricted"
    assert res.data["distance_km"] == 0.0

@pytest.mark.asyncio
async def test_mpa_warning(agent):
    # Test 6: Edge case, 1.57 km outside MPA boundary
    req = GeofencingRequest(query_run_id="test-6", lat=26.58, lon=93.379)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "warning"

@pytest.mark.asyncio
async def test_exact_boundary(agent):
    # Test 7: Exactly on the boundary polygon ring
    # PostGIS ST_Contains is False for boundaries, but distance is 0.0.
    # Therefore, our logic (distance <= 2.0) will flag this as a warning.
    req = GeofencingRequest(query_run_id="test-7", lat=26.74915299899999, lon=93.47639850500002)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "warning"
    assert res.data["distance_km"] == 0.0

@pytest.mark.asyncio
async def test_route_crossing(agent):
    # Test 8: A route (list of waypoints) that starts clear and crosses into restricted
    route = [
        (5.0, 90.0),   # Deep ocean (Clear)
        (7.5, 78.705), # Near IMBL (Warning)
        (7.5, 79.0)    # Inside Sri Lanka (Restricted)
    ]
    
    statuses = []
    for i, (lat, lon) in enumerate(route):
        req = GeofencingRequest(query_run_id=f"test-8-{i}", lat=lat, lon=lon)
        res = await agent.run(req)
        statuses.append(res.data["status"])
        
    assert statuses == ["clear", "warning", "restricted"]
