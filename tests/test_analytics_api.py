"""
Test suite for Fishery Analytics & Historical Trends API.
"""

from fastapi.testclient import TestClient

from backend.main import app


def test_get_historical_trends_endpoint():
    client = TestClient(app)
    res = client.get("/api/analytics/historical-trends?sector=Ratnagiri")
    assert res.status_code == 200
    data = res.json()
    assert "Ratnagiri" in data["sector"] or "Konkan" in data["sector"]
    assert data["overall_status"] == "DECLINED"
    assert len(data["months"]) == 12
    assert "statutory_reference" in data
    assert "Maharashtra" in data["statutory_reference"]["act"]


def test_list_sectors_endpoint():
    client = TestClient(app)
    res = client.get("/api/analytics/sectors")
    assert res.status_code == 200
    sectors = res.json()
    assert isinstance(sectors, list)
    assert len(sectors) >= 5


def test_bathymetry_check_endpoint():
    client = TestClient(app)
    res = client.get("/api/analytics/bathymetry?lat=16.99&lon=73.28&distance_from_shore_km=15.0&vessel_type=artisanal")
    assert res.status_code == 200
    data = res.json()
    assert "estimated_depth_meters" in data
    assert data["depth_category"] in ("Shallow Coastal (<30m)", "Inner Continental Shelf (30-50m)")
    assert data["gear_compatible"] is True
