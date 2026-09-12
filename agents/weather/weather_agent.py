"""
Weather Intelligence Agent — owner: Cbum (Atharva Sarnaik)

Fetches wind, wave height, lightning, and cyclone data for a given
lat/long + date/time window from Open-Meteo, IMD RSMC, INCOIS Buoys, and MOSDAC.
Implements a 4-tier fallback chain (Live -> Stale Cache -> Climatology -> Static)
guarded by circuit breakers. Normalizes all data into a standardized AgentEnvelope.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from backend.gateway.circuit_breaker import circuit_registry
from backend.schemas.envelope import AgentEnvelope
from agents.weather.alert_broadcaster import evaluate_and_broadcast_alerts
from agents.weather.imd_bulletin import IMDCycloneClient
from agents.weather.incois_buoy import (
    INCOISBuoyClient,
    compute_model_confidence_score,
)
from agents.weather.mosdac_client import MOSDACLightningClient

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


def get_regional_climatology(lat: float, lon: float, date_str: str) -> dict[str, Any]:
    """
    Tier 3 Fallback: Regional Climatology calibrated against INCOIS OSF baseline.
    Estimates seasonal wave/wind conditions for Indian maritime zones.
    """
    try:
        month = int(date_str.split("-")[1])
    except Exception:
        month = datetime.now(timezone.utc).month

    is_west_coast = lon < 77.5

    # Southwest Monsoon (June - September)
    if 6 <= month <= 9:
        if is_west_coast:
            wave_h = 2.4
            swell_p = 9.0
            wind_spd = 26.0
            wind_dir = "SW"
            wind_deg = 225.0
            rain_prob = 65.0
        else:
            wave_h = 1.9
            swell_p = 8.5
            wind_spd = 22.0
            wind_dir = "S"
            wind_deg = 180.0
            rain_prob = 45.0
    # Post-Monsoon / Northeast Monsoon (October - December)
    elif 10 <= month <= 12:
        if is_west_coast:
            wave_h = 1.2
            swell_p = 7.5
            wind_spd = 14.0
            wind_dir = "NW"
            wind_deg = 315.0
            rain_prob = 15.0
        else:
            wave_h = 1.8
            swell_p = 8.5
            wind_spd = 24.0
            wind_dir = "NE"
            wind_deg = 45.0
            rain_prob = 55.0
    # Fair Weather / Pre-Monsoon (January - May)
    else:
        wave_h = 1.1
        swell_p = 7.0
        wind_spd = 15.0
        wind_dir = "NW" if is_west_coast else "SE"
        wind_deg = 315.0 if is_west_coast else 135.0
        rain_prob = 10.0

    return {
        "wave_height_m": wave_h,
        "swell_period_s": swell_p,
        "wind_speed_kmh": wind_spd,
        "wind_direction": wind_dir,
        "wind_direction_deg": wind_deg,
        "wind_gusts_kmh": round(wind_spd * 1.25, 1),
        "temperature_c": 28.5,
        "humidity_pct": 75.0,
        "rain_probability_pct": rain_prob,
        "lightning_risk": "moderate" if rain_prob >= 50.0 else "low",
        "cyclone_alert": None,
        "visibility_km": 10.0 if rain_prob < 50.0 else 7.0,
        "forecast_summary": f"Regional climatology estimate for Indian waters (Month {month}). Wave {wave_h}m, Wind {wind_spd} km/h.",
    }


class WeatherAgent:
    """
    Tier 2 Live Weather Intelligence Agent.
    Integrates Open-Meteo Marine & Forecast APIs, IMD RSMC Bulletins,
    INCOIS Ocean Buoys, and MOSDAC Convective Intelligence.
    """

    def __init__(self, redis_client=None, timeout: float = 8.0):
        if redis_client is not None:
            self.redis = redis_client
        else:
            try:
                import redis
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                r = redis.from_url(redis_url, socket_connect_timeout=1.0)
                r.ping()
                self.redis = r
                logger.info(f"[weather_agent] Connected to Redis cache at {redis_url}")
            except Exception as e:
                logger.debug(f"[weather_agent] Redis unavailable ({e}); proceeding in-memory.")
                self.redis = None

        self.timeout = timeout
        self.marine_url = "https://marine-api.open-meteo.com/v1/marine"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

        # Specialized sub-clients
        self.imd_client = IMDCycloneClient(redis_client=self.redis, timeout=self.timeout)
        self.incois_buoy_client = INCOISBuoyClient(redis_client=self.redis, timeout=self.timeout)
        self.mosdac_client = MOSDACLightningClient(redis_client=self.redis, timeout=self.timeout)

    async def _fetch_open_meteo_marine(self, lat: float, lon: float) -> dict[str, Any]:
        """Fetch marine telemetry from Open-Meteo Marine API guarded by circuit breaker."""
        async def _req():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(
                    self.marine_url,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "hourly": "wave_height,wave_direction,wave_period,swell_wave_height,wind_wave_height",
                        "timezone": "auto",
                    },
                )
                res.raise_for_status()
                return res.json()

        return await circuit_registry.call("open_meteo_marine", _req)

    async def _fetch_open_meteo_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Fetch atmospheric forecast from Open-Meteo Weather API guarded by circuit breaker."""
        async def _req():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(
                    self.weather_url,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                        "timezone": "auto",
                    },
                )
                res.raise_for_status()
                return res.json()

        return await circuit_registry.call("open_meteo_weather", _req)

    async def get_forecast(
        self, lat: float, lon: float, date: str, query_run_id: str | None = None
    ) -> AgentEnvelope:
        """
        Fetch marine and atmospheric weather forecast for lat/lon and date.
        Uses 4-tier fallback chain (Live Telemetry -> Stale Cache -> Climatology -> Static).
        """
        run_id = query_run_id or f"weather-{lat:.2f}-{lon:.2f}-{date}"
        cache_key = f"varuna:weather:{lat:.2f}:{lon:.2f}:{date}"

        # -------------------------------------------------------------
        # 1. Tier 1: Check Active Redis Cache (TTL 1 hr)
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # 2. Tier 1: Fetch Live Telemetry (Parallel Multi-Source Gather)
        # -------------------------------------------------------------
        try:
            marine_json, weather_json, buoy_obs, cyclone_threat = await asyncio.gather(
                self._fetch_open_meteo_marine(lat, lon),
                self._fetch_open_meteo_weather(lat, lon),
                self.incois_buoy_client.fetch_nearest_buoy_observation(lat, lon),
                self.imd_client.check_cyclone_threat(lat, lon, radius_km=400.0),
                return_exceptions=False,
            )

            marine_data = marine_json.get("hourly", {})
            weather_data = weather_json.get("hourly", {})

            # Target midday index
            m_idx = find_target_hour_index(marine_data.get("time"), date, "12:00")
            w_idx = find_target_hour_index(weather_data.get("time"), date, "12:00")

            wave_height = _safe_get_index(marine_data.get("wave_height"), m_idx, 1.2)
            wave_period = _safe_get_index(marine_data.get("wave_period"), m_idx, 8.0)
            wind_speed = _safe_get_index(weather_data.get("wind_speed_10m"), w_idx, 18.0)
            wind_deg = _safe_get_index(weather_data.get("wind_direction_10m"), w_idx, 225.0)
            wind_dir = degrees_to_cardinal(wind_deg)
            temp = _safe_get_index(weather_data.get("temperature_2m"), w_idx, 28.0)
            humidity = _safe_get_index(weather_data.get("relative_humidity_2m"), w_idx, 75.0)
            rain_prob = _safe_get_index(weather_data.get("precipitation_probability"), w_idx, 10.0)
            wind_gusts = _safe_get_index(weather_data.get("wind_gusts_10m"), w_idx, wind_speed * 1.2)

            # Evaluate lightning risk via MOSDAC convective heuristic
            lightning_eval = self.mosdac_client.estimate_lightning_risk(
                rain_probability_pct=rain_prob,
                temperature_c=temp,
                humidity_pct=humidity,
                wind_gusts_kmh=wind_gusts,
            )
            lightning_risk = lightning_eval["lightning_risk"]
            visibility_km = 10.0 if rain_prob < 60.0 else 6.0

            # Determine Cyclone Alert (IMD authoritative threat > wind speed heuristic)
            cyclone_alert = None
            if cyclone_threat:
                cyclone_alert = cyclone_threat["summary"]
            elif wind_speed >= 62.0 or wind_gusts >= 80.0:
                cyclone_alert = "WARNING: Deep Depression / Cyclonic storm force winds detected in telemetry."

            # Calibrate confidence score using real INCOIS buoy telemetry
            confidence_score, confidence_notes = compute_model_confidence_score(wave_height, buoy_obs)

            forecast_summary = (
                f"Wind speed {wind_speed:.1f} km/h from {wind_dir} (gusts {wind_gusts:.1f} km/h). "
                f"Wave height {wave_height:.2f}m with swell period {wave_period:.1f}s. "
                f"Rain probability {rain_prob:.0f}%, temperature {temp:.1f}°C. "
                f"Lightning risk: {lightning_risk}."
            )
            if cyclone_alert:
                forecast_summary = f"{cyclone_alert} | {forecast_summary}"

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
                "buoy_observation": buoy_obs.to_dict() if buoy_obs else None,
                "confidence_notes": confidence_notes,
                "lightning_source": lightning_eval.get("source"),
            }

            envelope = AgentEnvelope(
                agent="weather_intelligence",
                query_run_id=run_id,
                status="success",
                data=payload,
                confidence=round(confidence_score, 2),
                source="Open-Meteo Marine, IMD RSMC & INCOIS Telemetry",
                timestamp=datetime.now(timezone.utc),
                thresholds_used={
                    "wave_caution_m": 1.5,
                    "wave_unsafe_m": 2.5,
                    "wind_caution_kmh": 25.0,
                    "wind_unsafe_kmh": 40.0,
                },
            )

            # Cache successful response in Redis
            if self.redis:
                try:
                    self.redis.setex(cache_key, 3600, envelope.model_dump_json())
                    # Also write stale fallback cache with 24h TTL
                    self.redis.setex(f"stale:{cache_key}", 86400, envelope.model_dump_json())
                except Exception as e:
                    logger.warning(f"[weather_agent] Failed to save to Redis cache: {e}")

            # Proactive Alert Broadcast check
            try:
                evaluate_and_broadcast_alerts(envelope)
            except Exception as e:
                logger.warning(f"[weather_agent] Alert broadcast check error: {e}")

            return envelope

        except Exception as live_err:
            logger.warning(f"[weather_agent] Live forecast failed: {live_err}. Initiating fallback chain.")

            # -------------------------------------------------------------
            # 3. Tier 2: Check Stale Cache Fallback
            # -------------------------------------------------------------
            if self.redis:
                try:
                    stale_val = self.redis.get(f"stale:{cache_key}")
                    if stale_val:
                        if isinstance(stale_val, bytes):
                            stale_val = stale_val.decode("utf-8")
                        stale_env = AgentEnvelope.model_validate_json(stale_val)
                        stale_env.status = "degraded"
                        stale_env.confidence = 0.70
                        stale_env.source = "Weather Agent Stale Cache (Live API Unreachable)"
                        stale_env.error_message = f"Live telemetry failed ({live_err}); serving cached forecast."
                        return stale_env
                except Exception as cache_err:
                    logger.debug(f"[weather_agent] Stale cache lookup failed: {cache_err}")

            # -------------------------------------------------------------
            # 4. Tier 3: Regional Climatology Fallback (INCOIS OSF calibrated)
            # -------------------------------------------------------------
            try:
                climatology_data = get_regional_climatology(lat, lon, date)
                climatology_data["location"] = {"lat": lat, "lon": lon}
                climatology_data["date"] = date

                return AgentEnvelope(
                    agent="weather_intelligence",
                    query_run_id=run_id,
                    status="degraded",
                    data=climatology_data,
                    confidence=0.60,
                    source="INCOIS OSF Regional Climatology Baseline",
                    timestamp=datetime.now(timezone.utc),
                    thresholds_used={
                        "wave_caution_m": 1.5,
                        "wind_caution_kmh": 25.0,
                    },
                    error_message=f"Live API unavailable ({live_err}); serving regional climatology baseline.",
                )
            except Exception as clim_err:
                logger.error(f"[weather_agent] Climatology fallback error: {clim_err}")

            # -------------------------------------------------------------
            # 5. Tier 4: Static Baseline Safety Net
            # -------------------------------------------------------------
            static_payload: dict[str, Any] = {
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
                "forecast_summary": "Live telemetry unavailable; static safety baseline provided.",
            }
            return AgentEnvelope(
                agent="weather_intelligence",
                query_run_id=run_id,
                status="degraded",
                data=static_payload,
                confidence=0.50,
                source="Weather Agent Static Safety Baseline",
                timestamp=datetime.now(timezone.utc),
                thresholds_used={
                    "wave_caution_m": 1.5,
                    "wind_caution_kmh": 25.0,
                },
                error_message=str(live_err),
            )
