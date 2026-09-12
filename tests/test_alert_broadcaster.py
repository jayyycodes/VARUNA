"""
Tests for Proactive Marine Alert Broadcaster and Alerts API — owner: Cbum
"""

import pytest
from datetime import datetime, timezone
from agents.weather.alert_broadcaster import (
    determine_coastal_region_and_ports,
    evaluate_and_broadcast_alerts,
    upsert_marine_alert,
)
from backend.routes.alerts import CURRENT_ALERTS, clear_expired_alerts
from backend.schemas.envelope import AgentEnvelope


def test_coastal_region_determination():
    # Ratnagiri / Konkan
    region, ports = determine_coastal_region_and_ports(17.0, 73.3)
    assert "Maharashtra" in region or "Konkan" in region
    assert "Ratnagiri" in ports

    # Kochi / Kerala
    region, ports = determine_coastal_region_and_ports(9.96, 76.24)
    assert "Kerala" in region
    assert "Kochi" in ports

    # Visakhapatnam / AP
    region, ports = determine_coastal_region_and_ports(17.7, 83.3)
    assert "Andhra" in region
    assert "Visakhapatnam" in ports


def test_broadcast_high_swell_alert():
    envelope = AgentEnvelope(
        agent="weather_intelligence",
        query_run_id="test-run-1",
        status="success",
        data={
            "location": {"lat": 9.96, "lon": 76.24},
            "wave_height_m": 3.8,  # Unsafe wave threshold
            "wind_speed_kmh": 20.0,
            "rain_probability_pct": 20.0,
            "lightning_risk": "low",
        },
        confidence=0.92,
        source="Test Live Source",
        timestamp=datetime.now(timezone.utc),
    )

    alerts = evaluate_and_broadcast_alerts(envelope)
    assert len(alerts) >= 1
    swell_alert = alerts[0]
    assert swell_alert["type"] == "HIGH SWELL / KALLAKKADAL"
    assert swell_alert["severity"] == "UNSAFE"
    assert "Kerala" in swell_alert["region"]


def test_broadcast_convective_lightning_alert():
    envelope = AgentEnvelope(
        agent="weather_intelligence",
        query_run_id="test-run-2",
        status="success",
        data={
            "location": {"lat": 17.0, "lon": 73.3},
            "wave_height_m": 1.2,
            "wind_speed_kmh": 22.0,
            "wind_gusts_kmh": 45.0,
            "rain_probability_pct": 85.0,
            "lightning_risk": "high",
        },
        confidence=0.90,
        source="Test Live Source",
        timestamp=datetime.now(timezone.utc),
    )

    alerts = evaluate_and_broadcast_alerts(envelope)
    assert len(alerts) >= 1
    lightning_alert = alerts[0]
    assert lightning_alert["type"] == "SEVERE LIGHTNING / CONVECTIVE SQUALL"
    assert lightning_alert["severity"] == "UNSAFE"


@pytest.mark.asyncio
async def test_clear_expired_alerts():
    # Insert an expired alert
    expired_alert = {
        "id": "test-expired-alert",
        "type": "HIGH SWELL",
        "severity": "CAUTION",
        "region": "Goa Coast",
        "headline": "Expired Alert Test",
        "details": "Details",
        "authority": "INCOIS",
        "issued_at": "2020-01-01T00:00:00Z",
        "valid_until": "2020-01-01T06:00:00Z",
        "affected_ports": ["Panaji"],
    }
    upsert_marine_alert(expired_alert)
    assert any(a["id"] == "test-expired-alert" for a in CURRENT_ALERTS)

    res = await clear_expired_alerts()
    assert res["status"] == "success"
    assert not any(a["id"] == "test-expired-alert" for a in CURRENT_ALERTS)
