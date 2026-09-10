"""
Weather Intelligence Agent — owner: Cbum

Fetches wind, wave height, lightning, and cyclone data for a given
lat/long + date/time window from Open-Meteo / IMD.
Normalizes all data into a standardized AgentEnvelope.
"""

import asyncio
import logging
import os
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


def find_target_hour_index(times: list[str] | None, target_date_str: str, preferred_hour: str = "12:00") -> int:
    """Find index in hourly time array matching target date at preferred hour (default 12:00 midday).
    Falls back to any hour on target_date, or index 0 if not found.
    """
    if not times:
        return 0

    # 1. Exact match for target_date + "T" + preferred_hour (e.g. "2026-09-11T12:00")
    needle = f"{target_date_str}T{preferred_hour}"
    for idx, t in enumerate(times):
        if str(t).startswith(needle):
            return idx

    # 2. Match any hour for target_date_str (e.g. "2026-09-11")
    for idx, t in enumerate(times):
        if str(t).startswith(target_date_str):
            return idx

    # 3. Default fallback
    return 0


def _safe_get_index(lst: list | None, idx: int, default: float) -> float:
    """Extract float from list at index with fallback to first valid element or default."""
    if not lst or not isinstance(lst, list):
        return default
    if 0 <= idx < len(lst) and lst[idx] is not None:
        try:
            return float(lst[idx])
        except (ValueError, TypeError):
            pass
    for item in lst:
        if item is not None:
            try:
                return float(item)
            except (ValueError, TypeError):
                pass
    return default


class WeatherAgent:
    """Live Weather Intelligence Agent integrating Open-Meteo Marine & Forecast APIs."""

    def __init__(self, redis_client=None, timeout: float = 10.0):
        if redis_client is not None:
            self.redis = redis_client
        else:
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                r = redis.from_url(redis_url, socket_connect_timeout=1.0)
                r.ping()
                self.redis = r
                logger.info(f"[weather_agent] Auto-connected Redis cache at {redis_url}")
            except Exception as e:
                logger.debug(f"[weather_agent] Redis not connected ({e}); running without persistent cache.")
                self.redis = None

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

            # Determine the exact midday (T12:00) index for target date
            m_idx = find_target_hour_index(marine_data.get("time"), date, "12:00")
            w_idx = find_target_hour_index(weather_data.get("time"), date, "12:00")

            # Extract target values matching the selected midday index
            wave_height = _safe_get_index(marine_data.get("wave_height"), m_idx, 1.2)
            wave_period = _safe_get_index(marine_data.get("wave_period"), m_idx, 8.0)
            wind_speed = _safe_get_index(weather_data.get("wind_speed_10m"), w_idx, 18.0)
            wind_deg = _safe_get_index(weather_data.get("wind_direction_10m"), w_idx, 225.0)
            wind_dir = degrees_to_cardinal(wind_deg)
            temp = _safe_get_index(weather_data.get("temperature_2m"), w_idx, 28.0)
            humidity = _safe_get_index(weather_data.get("relative_humidity_2m"), w_idx, 75.0)
            rain_prob = _safe_get_index(weather_data.get("precipitation_probability"), w_idx, 10.0)
            wind_gusts = _safe_get_index(weather_data.get("wind_gusts_10m"), w_idx, wind_speed * 1.2)

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
