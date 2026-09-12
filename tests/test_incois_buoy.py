"""
Tests for INCOIS Wave-Rider Buoy Integration and Confidence Calibration — owner: Cbum
"""

import pytest
from datetime import datetime, timezone
from agents.weather.incois_buoy import (
    BuoyObservation,
    INCOISBuoyClient,
    compute_model_confidence_score,
    find_nearest_station,
    haversine_distance_km,
)


def test_station_picker():
    # Near Ratnagiri (16.98, 73.32)
    res = find_nearest_station(16.98, 73.32, max_radius_km=100.0)
    assert res is not None
    station, dist = res
    assert station["station_id"] == "INCOIS-CB01"
    assert dist < 10.0

    # Far inland or deep ocean beyond radius (e.g. Himalayas 30.0, 78.0)
    res_far = find_nearest_station(30.0, 78.0, max_radius_km=350.0)
    assert res_far is None


def test_confidence_calibration():
    obs = BuoyObservation(
        station_id="INCOIS-CB01",
        station_name="Ratnagiri Coastal Buoy",
        station_lat=17.0,
        station_lon=73.3,
        distance_to_query_km=25.0,
        observed_wave_height_m=1.4,
        observed_swell_period_s=8.0,
        observed_sea_surface_temp_c=28.5,
        observed_current_speed_knots=1.0,
        observation_time=datetime.now(timezone.utc).isoformat(),
    )

    # 1. Close match (model 1.5 vs buoy 1.4 -> delta 0.1m)
    conf_high, notes = compute_model_confidence_score(1.5, obs)
    assert conf_high >= 0.95

    # 2. Moderate match (model 2.0 vs buoy 1.4 -> delta 0.6m)
    conf_med, _ = compute_model_confidence_score(2.0, obs)
    assert 0.89 <= conf_med <= 0.93

    # 3. High divergence (model 3.5 vs buoy 1.4 -> delta 2.1m)
    conf_low, _ = compute_model_confidence_score(3.5, obs)
    assert conf_low <= 0.80

    # 4. No buoy
    conf_none, notes_none = compute_model_confidence_score(1.5, None)
    assert conf_none == 0.88
    assert "No active INCOIS wave-rider buoy" in notes_none[0]


@pytest.mark.asyncio
async def test_incois_client_fetch(monkeypatch):
    client = INCOISBuoyClient(redis_client=None)

    # Ratnagiri coordinates
    obs = await client.fetch_nearest_buoy_observation(17.0, 73.3)
    assert obs is not None
    assert obs.station_id == "INCOIS-CB01"
    assert obs.observed_wave_height_m is not None
