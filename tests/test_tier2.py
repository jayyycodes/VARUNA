"""
Automated Test Suite for Tier-2 Features:
1. Multilingual Detection & Translation Gateway (Hindi & Marathi)
2. Dual-Route Comparative Analysis (Safe Corridor vs Direct Baseline)
3. Active Coastal Marine Alerts API
4. Multi-Turn Session Memory in the Planner
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from backend.gateway.multilingual import detect_language, translate_in, translate_out
from agents.route.route_agent import RouteAgent
from backend.main import app


# ═══════════════════════════════════════════════════════════════════════
# 1. Multilingual Tests
# ═══════════════════════════════════════════════════════════════════════

def test_language_detection():
    """Verify Devanagari script and keyword scoring for Hindi and Marathi."""
    # Hindi queries
    assert detect_language("क्या कल रत्नागिरी में मौसम मछली पकड़ने के लिए ठीक है?") == "hi"
    assert detect_language("क्या समुद्र में तेज हवाएं चल रही हैं?") == "hi"

    # Marathi queries
    assert detect_language("उद्या मालवणला जाणे सुरक्षित आहे का?") == "mr"
    assert detect_language("रत्नागिरीच्या किनाऱ्यावर लाटा किती उंच आहेत सांगा?") == "mr"

    # English queries
    assert detect_language("Is it safe to navigate from Ratnagiri to Malvan?") == "en"
    assert detect_language("Where is the nearest PFZ zone today?") == "en"


@pytest.mark.asyncio
async def test_multilingual_inbound_translation():
    """Verify Indic inbound translation into English."""
    # When already English, pass-through
    en_q, lang = await translate_in("Is it safe in Kochi?")
    assert lang == "en"
    assert en_q == "Is it safe in Kochi?"

    # Hindi translation check
    hi_q = "क्या कल रत्नागिरी में मौसम ठीक है?"
    translated, detected = await translate_in(hi_q)
    assert detected == "hi"
    assert isinstance(translated, str) and len(translated) > 5
    # Should retain location
    assert "ratnagiri" in translated.lower()


# ═══════════════════════════════════════════════════════════════════════
# 2. Dual-Route Comparative Analysis Tests
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_dual_route_comparison():
    """Verify RouteAgent outputs both safe corridor and direct baseline with comparison."""
    agent = RouteAgent()
    envelope = await agent.plan_route(
        start_lat=16.99,
        start_lon=73.30,
        dest_lat=16.05,
        dest_lon=73.47,
        vessel_speed_kts=8.0,
        fuel_rate_l_nm=2.2,
    )

    assert envelope.status == "success"
    data = envelope.data

    # Dual features exist
    assert "route_feature" in data
    assert "route_direct_feature" in data
    assert data["route_feature"]["properties"]["type"] == "route"
    assert data["route_direct_feature"]["properties"]["type"] == "route_direct"

    # Comparison metrics
    assert "comparison" in data
    comp = data["comparison"]
    assert "safe_distance_nm" in comp
    assert "direct_distance_nm" in comp
    assert "delta_distance_nm" in comp
    assert "safe_fuel_liters" in comp
    assert "direct_fuel_liters" in comp
    assert "delta_fuel_liters" in comp
    assert "hazards_avoided" in comp

    # Safe route is >= direct distance
    assert comp["safe_distance_nm"] >= comp["direct_distance_nm"]
    assert comp["safe_fuel_liters"] >= comp["direct_fuel_liters"]
    assert len(comp["hazards_avoided"]) > 0


# ═══════════════════════════════════════════════════════════════════════
# 3. Active Coastal Marine Alerts API Tests
# ═══════════════════════════════════════════════════════════════════════

def test_active_alerts_api():
    """Verify /api/alerts returns bulletins and supports filtering."""
    client = TestClient(app)
    res = client.get("/api/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 3

    # Check alert structure
    cyclone = next((a for a in alerts if "CYCLONE" in a["type"]), None)
    assert cyclone is not None
    assert cyclone["severity"] == "UNSAFE"
    assert "authority" in cyclone
    assert "boundary_geojson" in cyclone

    # Test severity filtering
    caution_res = client.get("/api/alerts?severity=CAUTION")
    assert caution_res.status_code == 200
    caution_alerts = caution_res.json()
    assert all(a["severity"] == "CAUTION" for a in caution_alerts)


# ═══════════════════════════════════════════════════════════════════════
# 4. Multi-Turn Session Memory in Planner Tests
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_planner_multiturn_session():
    """Verify PlannerAgent retains location context across multi-turn queries."""
    from agents.planner.planner_agent import PlannerAgent
    planner = PlannerAgent()
    session_id = "test-session-konkan-001"

    # Turn 1: Establish Ratnagiri context
    turn1 = await planner.handle_query(
        query="Check marine weather in Ratnagiri",
        conversation_id=session_id,
    )
    assert turn1["status"] == "success"
    assert session_id in planner.sessions
    assert planner.sessions[session_id]["location"]["name"].startswith("Ratnagiri")

    # Turn 2: Follow-up question referring to "there"
    turn2 = await planner.handle_query(
        query="What is the safest route from there to Malvan?",
        conversation_id=session_id,
    )
    assert turn2["status"] == "success"
    # Should have resolved start location to Ratnagiri from session memory
    loc = planner.sessions[session_id]["location"]
    dest = planner.sessions[session_id]["destination"]
    assert "Ratnagiri" in loc["name"]
    assert dest is not None and "Malvan" in dest["name"]
