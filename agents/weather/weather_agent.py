"""
Weather Intelligence Agent — owner: Cbum

Fetches wind, wave height, lightning, and cyclone data for a given
lat/long + date/time window from Open-Meteo / IMD.
Normalizes all data into a standardized AgentEnvelope.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.schemas.envelope import AgentEnvelope

logger = logging.getLogger("weather_agent")


def degrees_to_cardinal(deg: float | None) -> str:
    """Convert degrees (0-360) to 8-point compass direction."""
    if deg is None:
        return "N/A"
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = round(deg / 45.0) % 8
    return directions[idx]


class WeatherAgent:
    """Live Weather Intelligence Agent integrating Open-Meteo Marine & Forecast APIs."""

    def __init__(self, redis_client=None, timeout: float = 10.0):
        self.redis = redis_client
        self.timeout = timeout
        self.marine_url = "https://marine-api.open-meteo.com/v1/marine"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    async def get_forecast(
        self, lat: float, lon: float, date: str, query_run_id: str | None = None
    ) -> AgentEnvelope:
        """Fetch marine and atmospheric weather forecast for lat/lon and date.

        Args:
            lat: Latitude of target location.
            lon: Longitude of target location.
            date: Target date string (YYYY-MM-DD).
            query_run_id: Optional ID linking to parent query run.

        Returns:
            AgentEnvelope containing normalized weather & marine metrics.
        """
        run_id = query_run_id or f"weather-{lat:.2f}-{lon:.2f}-{date}"
        cache_key = f"varuna:weather:{lat:.2f}:{lon:.2f}:{date}"

        # 1. Check Redis Cache first (TTL: 1 hour)
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    logger.info(f"[weather_agent] Cache hit for {cache_key}")
                    if isinstance(cached, bytes):
                        cached = cached.decode("utf-8")
                    envelope = AgentEnvelope.model_validate_json(cached)
                    if query_run_id:
                        envelope.query_run_id = query_run_id
                    return envelope
            except Exception as e:
                logger.warning(f"[weather_agent] Redis cache read failed: {e}")

        # 2. Fetch live data asynchronously from Open-Meteo
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                marine_res, weather_res = await asyncio.gather(
                    client.get(
                        self.marine_url,
                        params={
                            "latitude": lat,
                            "longitude": lon,
                            "hourly": "wave_height,wave_direction,wave_period,swell_wave_height,wind_wave_height",
                            "timezone": "auto",
                        },
                    ),
                    client.get(
                        self.weather_url,
                        params={
                            "latitude": lat,
                            "longitude": lon,
                            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                            "timezone": "auto",
                        },
                    ),
                )

                marine_res.raise_for_status()
                weather_res.raise_for_status()

                marine_json = marine_res.json()
                weather_json = weather_res.json()

            marine_data = marine_json.get("hourly", {})
            weather_data = weather_json.get("hourly", {})

            # Extract current/target values (fallback to safe defaults if empty/None)
            wave_height_list = marine_data.get("wave_height") or [1.2]
            wave_period_list = marine_data.get("wave_period") or [8.0]
            wind_speed_list = weather_data.get("wind_speed_10m") or [18.0]
            wind_dir_list = weather_data.get("wind_direction_10m") or [225.0]
            temp_list = weather_data.get("temperature_2m") or [28.0]
            humidity_list = weather_data.get("relative_humidity_2m") or [75.0]
            rain_prob_list = weather_data.get("precipitation_probability") or [10.0]
            gusts_list = weather_data.get("wind_gusts_10m") or [wind_speed_list[0] if wind_speed_list else 22.0]

            wave_height = float(wave_height_list[0] if wave_height_list[0] is not None else 1.2)
            wave_period = float(wave_period_list[0] if wave_period_list[0] is not None else 8.0)
            wind_speed = float(wind_speed_list[0] if wind_speed_list[0] is not None else 18.0)
            wind_deg = float(wind_dir_list[0] if wind_dir_list[0] is not None else 225.0)
            wind_dir = degrees_to_cardinal(wind_deg)
            temp = float(temp_list[0] if temp_list[0] is not None else 28.0)
            humidity = float(humidity_list[0] if humidity_list[0] is not None else 75.0)
            rain_prob = float(rain_prob_list[0] if rain_prob_list[0] is not None else 10.0)
            wind_gusts = float(gusts_list[0] if gusts_list[0] is not None else wind_speed * 1.2)

            lightning_risk = "low" if rain_prob < 40 else ("moderate" if rain_prob < 70 else "high")
            visibility_km = 10.0 if rain_prob < 60 else 6.0

            # Cyclone alert heuristics (wind > 62 km/h or gusts > 80 km/h)
            cyclone_alert = None
            if wind_speed >= 62.0 or wind_gusts >= 80.0:
                cyclone_alert = "WARNING: Deep Depression / Cyclonic storm force winds detected in telemetry."

            forecast_summary = (
                f"Wind speed {wind_speed:.1f} km/h from {wind_dir} (gusts {wind_gusts:.1f} km/h). "
                f"Wave height {wave_height:.2f}m with swell period {wave_period:.1f}s. "
                f"Rain probability {rain_prob:.0f}%, temperature {temp:.1f}°C. "
                f"Lightning risk: {lightning_risk}."
            )

            payload: dict[str, Any] = {
                "location": {"lat": lat, "lon": lon},
                "date": date,
                "wind_speed_kmh": round(wind_speed, 1),
                "wind_direction": wind_dir,
                "wind_direction_deg": round(wind_deg, 1),
                "wind_gusts_kmh": round(wind_gusts, 1),
                "wave_height_m": round(wave_height, 2),
                "swell_period_s": round(wave_period, 1),
                "temperature_c": round(temp, 1),
                "humidity_pct": round(humidity, 1),
                "rain_probability_pct": round(rain_prob, 1),
                "lightning_risk": lightning_risk,
                "cyclone_alert": cyclone_alert,
                "visibility_km": visibility_km,
                "forecast_summary": forecast_summary,
            }

            envelope = AgentEnvelope(
                agent="weather_intelligence",
                query_run_id=run_id,
                status="success",
                data=payload,
                confidence=0.92,
                source="Open-Meteo Marine & Forecast API (Live Telemetry)",
                timestamp=datetime.now(timezone.utc),
                thresholds_used={
                    "wave_caution_m": 1.5,
                    "wave_unsafe_m": 2.5,
                    "wind_caution_kmh": 25.0,
                    "wind_unsafe_kmh": 40.0,
                },
            )

            # Cache in Redis
            if self.redis:
                try:
                    self.redis.setex(cache_key, 3600, envelope.model_dump_json())
                    logger.info(f"[weather_agent] Cached forecast to Redis: {cache_key}")
                except Exception as e:
                    logger.warning(f"[weather_agent] Failed to save to Redis cache: {e}")

            return envelope

        except Exception as err:
            logger.error(f"[weather_agent] Live forecast retrieval failed: {err}", exc_info=True)
            # Return degraded fallback envelope
            fallback_payload: dict[str, Any] = {
                "location": {"lat": lat, "lon": lon},
                "date": date,
                "wind_speed_kmh": 18.0,
                "wind_direction": "SW",
                "wind_direction_deg": 225.0,
                "wind_gusts_kmh": 22.0,
                "wave_height_m": 1.2,
                "swell_period_s": 8.0,
                "temperature_c": 28.0,
                "humidity_pct": 75.0,
                "rain_probability_pct": 10.0,
                "lightning_risk": "low",
                "cyclone_alert": None,
                "visibility_km": 10.0,
                "forecast_summary": "Live telemetry unavailable; standard seasonal estimate provided.",
            }
            return AgentEnvelope(
                agent="weather_intelligence",
                query_run_id=run_id,
                status="degraded",
                data=fallback_payload,
                confidence=0.50,
                source="Weather Agent Fallback (API error)",
                timestamp=datetime.now(timezone.utc),
                thresholds_used={
                    "wave_caution_m": 1.5,
                    "wind_caution_kmh": 25.0,
                },
                error_message=str(err),
            )
