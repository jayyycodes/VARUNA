"""
Tests for Planner Agent, AI Gateway, and FastAPI Backend (Jay's components).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.envelope import AgentEnvelope, RiskVerdict
from agents.planner.mock_agents import (
    mock_weather,
    mock_marine,
    mock_geofencing,
    mock_rag,
    mock_risk_verdict,
)
from agents.planner.planner_agent import PlannerAgent


client = TestClient(app)


def test_mock_agents_envelopes():
    """Verify all mock agents return valid AgentEnvelope instances conforming to schema."""
    qid = "test-run-123"
    lat, lon, d = 16.99, 73.30, "2026-09-09"

    w = mock_weather(qid, lat, lon, d)
    assert isinstance(w, AgentEnvelope)
    assert w.agent == "weather_intelligence"
    assert "wind_speed_kmh" in w.data

    m = mock_marine(qid, lat, lon, d)
    assert isinstance(m, AgentEnvelope)
    assert m.agent == "marine_fishing"
    assert "pfz_zones" in m.data

    g = mock_geofencing(qid, lat, lon)
    assert isinstance(g, AgentEnvelope)
    assert g.agent == "geofencing"
    assert "in_indian_eez" in g.data

    r = mock_rag(qid, "What are the rules for purse seine fishing?")
    assert isinstance(r, dict)
    assert r["agent"] == "rag_advisory"

    rv = mock_risk_verdict(qid, w, m, g)
    assert isinstance(rv, RiskVerdict)
    assert rv.verdict in ("SAFE", "CAUTION", "UNSAFE")
    assert len(rv.reasons) > 0


@pytest.mark.asyncio
async def test_planner_graph_execution():
    """Test full LangGraph planner pipeline runs without exceptions."""
    planner = PlannerAgent()
    result = await planner.handle_query("Is it safe to go fishing tomorrow near Ratnagiri?")

    assert "text" in result
    assert "intent" in result
    assert result["intent"] in ("safety_check", "find_fishing_zone", "regulation_question", "route_request")
    assert "evidence" in result
    assert result["status"] == "success"
    assert len(result["text"]) > 0


def test_api_health_endpoint():
    """Verify GET /health returns 200 and expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") in ("ok", "degraded")
    assert data.get("service") == "varuna-orca"


def test_api_chat_endpoint():
    """Verify POST /chat successfully handles user queries."""
    payload = {
        "query": "Is it safe to sail tomorrow off Mumbai coast?",
        "conversation_id": "test-session-001",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query_run_id" in data
    assert "intent" in data
    assert "text" in data
    assert len(data["text"]) > 0
    assert data.get("status") == "success"
