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
    # Inside Sri Lanka EEZ (ocean, not landmass)
    # 7.5 N, 79.0 E
    req = GeofencingRequest(query_run_id="test-3", lat=7.5, lon=79.0)
    res = await agent.run(req)
    
    assert res.status == "success"
    assert res.data["status"] == "restricted"
    assert "Sri Lanka" in res.data["nearest_boundary_name"]
    assert res.data["distance_km"] == 0.0
