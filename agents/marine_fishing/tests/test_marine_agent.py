"""
Unit tests for MarineFishingAgent (agents/marine_fishing/marine_agent.py).

Tests live/mock pipeline execution, ranking logic, geodesic resampling,
and graceful degradation fallbacks.
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from shapely.geometry import LineString, MultiLineString

from backend.schemas.envelope import AgentEnvelope
from agents.marine_fishing.marine_agent import (
    MarineFishingAgent,
    _compute_productivity_score,
    _determine_species,
    _haversine_distance_km,
)
from agents.marine_fishing.models import (
    CHLObservation,
    ObservationOutcome,
    PFZBoundingBox,
    PFZFeature,
    PFZOutcome,
    PFZQueryResult,
    PFZSamplePoint,
    SampledEnvironmentalPoint,
    SSTObservation,
)


def test_haversine_distance():
    # Distance between Mumbai (18.92, 72.83) and Ratnagiri (16.99, 73.30) is ~220 km
    d = _haversine_distance_km(18.92, 72.83, 16.99, 73.30)
    assert 200 < d < 240


def test_productivity_scoring():
    # Optimal conditions: chl 0.8, sst 28.0 with front, close distance 10km
    score_opt = _compute_productivity_score(
        chl=0.8, sst=28.0, front_position=True, gradient_k_per_km=0.05, dist_km=10.0
    )
    # Sub-optimal: low chl 0.1, cold sst 24.0, far 60km
    score_sub = _compute_productivity_score(
        chl=0.1, sst=24.0, front_position=False, gradient_k_per_km=0.01, dist_km=60.0
    )
    assert score_opt > score_sub
    assert 0.0 <= score_opt <= 1.0
    assert 0.0 <= score_sub <= 1.0


def test_species_determination():
    nearshore = _determine_species(28.5, 0.9, dist_km=8.0)
    assert "Prawn" in nearshore or "Croaker" in nearshore

    offshore = _determine_species(27.8, 0.6, dist_km=25.0)
    assert "Tuna" in offshore or "Pomfret" in offshore

    pelagic = _determine_species(28.2, 0.75, dist_km=16.0)
    assert "Mackerel" in pelagic or "Sardine" in pelagic


@pytest.mark.asyncio
async def test_marine_agent_success_pipeline():
    """Verify MarineFishingAgent processes features and returns ranked zones."""
    mock_geom = MultiLineString([LineString([(73.35, 17.02), (73.40, 17.08)])])
    mock_feat = PFZFeature(
        geometry=mock_geom,
        julian_day="253",
        year=2026,
        sector_name="Maharashtra",
    )
    mock_pfz_res = PFZQueryResult(
        outcome=PFZOutcome.SUCCESS,
        features=[mock_feat],
    )

    mock_pfz_client = AsyncMock()
    mock_pfz_client.get_pfz_features.return_value = mock_pfz_res

    mock_env_client = AsyncMock()
    mock_sample_point = PFZSamplePoint(
        lon=73.35,
        lat=17.02,
        part_index=0,
        distance_along_part_km=0.0,
        is_endpoint=True,
    )
    mock_env_point = SampledEnvironmentalPoint(
        sample_point=mock_sample_point,
        sst=SSTObservation(
            outcome=ObservationOutcome.SUCCESS,
            value_celsius=28.3,
            front_position=True,
            gradient_magnitude_k_per_km=0.06,
            requested_time=datetime.now(timezone.utc),
        ),
        chl=CHLObservation(
            outcome=ObservationOutcome.SUCCESS,
            value_mg_m3=0.82,
            requested_time=datetime.now(timezone.utc),
        ),
    )
    mock_env_client.join_environmental_data.return_value = [mock_env_point]

    agent = MarineFishingAgent(pfz_client=mock_pfz_client, env_client=mock_env_client)
    res = await agent.get_ocean_state(16.99, 73.30, "2026-09-10", query_run_id="run-1")

    assert isinstance(res, AgentEnvelope)
    assert res.status == "success"
    assert res.agent == "marine_fishing"
    assert res.query_run_id == "run-1"
    assert len(res.data["pfz_zones"]) == 1
    assert res.data["pfz_zones"][0]["sst_c"] == 28.3
    assert res.data["pfz_zones"][0]["chlorophyll"] == 0.82


@pytest.mark.asyncio
async def test_marine_agent_fallback_on_empty_or_error():
    """Verify MarineFishingAgent degrades gracefully when INCOIS WFS is empty or errors."""
    mock_pfz_client = AsyncMock()
    mock_pfz_client.get_pfz_features.return_value = PFZQueryResult(
        outcome=PFZOutcome.EMPTY,
        features=[],
    )
    mock_env_client = AsyncMock()

    agent = MarineFishingAgent(pfz_client=mock_pfz_client, env_client=mock_env_client)
    res = await agent.get_ocean_state(16.99, 73.30, "2026-09-10")

    assert isinstance(res, AgentEnvelope)
    assert res.status == "degraded"
    assert len(res.data["pfz_zones"]) == 3
    # Top zone should have highest productivity score
    scores = [z["productivity_score"] for z in res.data["pfz_zones"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_marine_agent_satellite_raster_slice():
    agent = MarineFishingAgent()
    envelope = await agent.get_satellite_raster_slice(
        bbox=(16.0, 72.5, 17.5, 73.5),
        target_date="2026-09-12",
        query_run_id="test-raster-run",
    )
    assert isinstance(envelope, AgentEnvelope)
    assert envelope.status == "success"
    assert envelope.agent == "marine_fishing"
    assert envelope.query_run_id == "test-raster-run"
    assert "sst_grid" in envelope.data
    assert "chl_grid" in envelope.data
    assert "detected_fronts" in envelope.data
    assert envelope.data["front_count"] >= 0

