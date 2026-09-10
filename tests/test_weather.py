"""
Tests for Weather Intelligence Agent (Cbum's component).
Supports execution via pytest or python -m unittest.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch
import httpx

from backend.schemas.envelope import AgentEnvelope
from agents.weather.weather_agent import WeatherAgent, degrees_to_cardinal


class TestWeatherAgent(unittest.IsolatedAsyncioTestCase):
    def test_degrees_to_cardinal(self):
        self.assertEqual(degrees_to_cardinal(0), "N")
        self.assertEqual(degrees_to_cardinal(45), "NE")
        self.assertEqual(degrees_to_cardinal(90), "E")
        self.assertEqual(degrees_to_cardinal(135), "SE")
        self.assertEqual(degrees_to_cardinal(180), "S")
        self.assertEqual(degrees_to_cardinal(225), "SW")
        self.assertEqual(degrees_to_cardinal(270), "W")
        self.assertEqual(degrees_to_cardinal(315), "NW")
        self.assertEqual(degrees_to_cardinal(360), "N")
        self.assertEqual(degrees_to_cardinal(None), "N/A")

    async def test_weather_agent_live_fetch(self):
        """Verify live Open-Meteo integration returns valid AgentEnvelope with expected fields."""
        agent = WeatherAgent()
        lat, lon, date_str = 16.99, 73.30, "2026-09-10"
        qid = "test-weather-run-1"

        envelope = await agent.get_forecast(lat=lat, lon=lon, date=date_str, query_run_id=qid)

        self.assertIsInstance(envelope, AgentEnvelope)
        self.assertEqual(envelope.agent, "weather_intelligence")
        self.assertEqual(envelope.query_run_id, qid)
        self.assertIn(envelope.status, ("success", "degraded"))
        self.assertGreater(envelope.confidence, 0.0)

        data = envelope.data
        self.assertIn("wind_speed_kmh", data)
        self.assertIn("wave_height_m", data)
        self.assertIn("temperature_c", data)
        self.assertIn("rain_probability_pct", data)
        self.assertIn("lightning_risk", data)
        self.assertIn("forecast_summary", data)

    async def test_weather_agent_error_fallback(self):
        """Verify WeatherAgent gracefully falls back to degraded status on API network failure."""
        agent = WeatherAgent(timeout=0.001)

        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("Connection timed out")):
            envelope = await agent.get_forecast(16.99, 73.30, "2026-09-10", "fail-run-1")

            self.assertIsInstance(envelope, AgentEnvelope)
            self.assertEqual(envelope.agent, "weather_intelligence")
            self.assertEqual(envelope.status, "degraded")
            self.assertEqual(envelope.confidence, 0.50)
            self.assertIn("wind_speed_kmh", envelope.data)
            self.assertIn("wave_height_m", envelope.data)

    async def test_weather_agent_redis_caching(self):
        """Verify WeatherAgent checks and writes to Redis cache."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # Cache miss first

        agent = WeatherAgent(redis_client=mock_redis)
        envelope = await agent.get_forecast(16.99, 73.30, "2026-09-10", "cache-run-1")

        self.assertEqual(envelope.status, "success")
        # Ensure setex was called to store cache
        self.assertTrue(mock_redis.setex.called)

        # Now simulate cache hit
        mock_redis.get.return_value = envelope.model_dump_json()
        cached_envelope = await agent.get_forecast(16.99, 73.30, "2026-09-10", "cache-run-2")

        self.assertEqual(cached_envelope.query_run_id, "cache-run-2")
        self.assertEqual(cached_envelope.data["wind_speed_kmh"], envelope.data["wind_speed_kmh"])


if __name__ == "__main__":
    unittest.main()
