"""
Tests for newly integrated backend routers:
- /api/fleet
- /api/analytics/historical-trends
- /api/route/plan & /api/route/ports
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_fleet_status_endpoint():
    res = client.get("/api/fleet")
    assert res.status_code == 200
    data = res.json()
    assert "active_craft" in data
    assert "vessels" in data
    assert len(data["vessels"]) > 0
    assert data["vessels"][0]["id"].startswith("IND-")
    assert "lat" in data["vessels"][0]
    assert "lon" in data["vessels"][0]


def test_historical_trends_endpoint():
    res = client.get("/api/analytics/historical-trends")
    assert res.status_code == 200
    data = res.json()
    assert "sector" in data
    assert "sst_baseline_celsius" in data
    assert "chlorophyll_baseline_mg_m3" in data
    assert "primary_causes" in data
    assert len(data["primary_causes"]) >= 3


def test_route_ports_catalog():
    res = client.get("/api/route/ports")
    assert res.status_code == 200
    ports = res.json()
    assert len(ports) >= 5
    port_ids = [p["id"] for p in ports]
    assert "ratnagiri" in port_ids
    assert "malvan" in port_ids


def test_route_plan_endpoint():
    payload = {
        "departure_port": "ratnagiri",
        "destination_port": "malvan",
        "vessel_speed_kts": 8.0,
    }
    res = client.post("/api/route/plan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["distance_nm"] > 0
    assert "safe_route_feature" in data
    assert "direct_route_feature" in data
