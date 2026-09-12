"""
Tests for Weather Intelligence Multi-Tier Fallback Chain — owner: Cbum
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.weather.weather_agent import WeatherAgent, get_regional_climatology


def test_regional_climatology_monsoon():
    # West Coast in July (Month 07)
    res_west = get_regional_climatology(17.0, 73.0, "2026-07-15")
    assert res_west["wave_height_m"] >= 2.0
    assert res_west["wind_speed_kmh"] >= 20.0
    assert res_west["wind_direction"] == "SW"

    # East Coast in November (Month 11 - NE monsoon)
    res_east = get_regional_climatology(13.0, 80.5, "2026-11-15")
    assert res_east["wind_direction"] == "NE"
    assert res_east["wave_height_m"] >= 1.5


@pytest.mark.asyncio
async def test_fallback_to_climatology_when_live_fails(monkeypatch):
    # Instantiate agent without redis
    agent = WeatherAgent(redis_client=None)

    # Force live fetch methods to throw exception
    async def mock_fail(*args, **kwargs):
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr(agent, "_fetch_open_meteo_marine", mock_fail)
    monkeypatch.setattr(agent, "_fetch_open_meteo_weather", mock_fail)

    envelope = await agent.get_forecast(17.0, 73.3, "2026-07-20")
    assert envelope.status == "degraded"
    assert envelope.confidence == 0.60
    assert "Climatology" in envelope.source
    assert envelope.data["wave_height_m"] >= 2.0


@pytest.mark.asyncio
async def test_fallback_to_stale_cache(monkeypatch):
    # Mock Redis client with stale cache hit
    mock_redis = MagicMock()
    
    # Active cache misses, but stale cache hits
    def mock_get(key):
        if key.startswith("stale:"):
            from datetime import datetime, timezone
            from backend.schemas.envelope import AgentEnvelope
            cached_env = AgentEnvelope(
                agent="weather_intelligence",
                query_run_id="stale-run-1",
                status="success",
                data={"wave_height_m": 1.5, "wind_speed_kmh": 20.0},
                confidence=0.92,
                source="Open-Meteo",
                timestamp=datetime.now(timezone.utc),
            )
            return cached_env.model_dump_json()
        return None

    mock_redis.get.side_effect = mock_get

    agent = WeatherAgent(redis_client=mock_redis)

    async def mock_fail(*args, **kwargs):
        raise ConnectionError("Network down")

    monkeypatch.setattr(agent, "_fetch_open_meteo_marine", mock_fail)
    monkeypatch.setattr(agent, "_fetch_open_meteo_weather", mock_fail)

    envelope = await agent.get_forecast(17.0, 73.3, "2026-09-12")
    assert envelope.status == "degraded"
    assert envelope.confidence == 0.70
    assert "Stale Cache" in envelope.source
