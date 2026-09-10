"""
Tests for NOAA CoastWatch ERDDAP Environmental Client (SST + CHL).

Uses httpx.MockTransport to simulate ERDDAP metadata and griddap responses
without network access.

FIXTURE PROVENANCE DOCUMENTATION:
- CHL SUCCESS fixture: REAL CAPTURE from live NOAA ERDDAP query performed on
  2026-09-10 against noaacwNPPN20VIIRSDINEOFDaily for 2026-09-07T12:00:00Z at
  lat=18.541662, lon=72.541664 returning chlor_a=0.881046 mg/m^3.
- SST SUCCESS fixture: SYNTHETIC REALISTIC FIXTURE constructed to match realistic
  Maharashtra coastal oceanographic conditions (28.95°C, quality_level=5,
  gradient=0.045 K/km, front_position=1). It is NOT a verbatim raw capture from
  NOAA and must not be cited as such.

Owner: Jaish
"""

from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timezone

import httpx
import pytest

from agents.marine_fishing.environmental_client import (
    CHL_CONFIDENCE_CEILING,
    CHL_DATASET_ID,
    CHL_FILL_VALUE,
    SST_DATASET_ID,
    SST_FILL_VALUE,
    EnvironmentalClient,
)
from agents.marine_fishing.models import (
    ObservationOutcome,
    PFZSamplePoint,
    SampledEnvironmentalPoint,
)

# ── Fixture Data ───────────────────────────────────────────────────────

# Metadata fixture for SST dataset (time_coverage_end: 2026-09-08T12:00:00Z)
SST_METADATA_FIXTURE = {
    "table": {
        "columnNames": [
            "Row Type",
            "Variable Name",
            "Attribute Name",
            "Data Type",
            "Value",
        ],
        "columnTypes": ["String", "String", "String", "String", "String"],
        "rows": [
            [
                "attribute",
                "NC_GLOBAL",
                "time_coverage_start",
                "String",
                "2020-01-01T12:00:00Z",
            ],
            [
                "attribute",
                "NC_GLOBAL",
                "time_coverage_end",
                "String",
                "2026-09-08T12:00:00Z",
            ],
        ],
    }
}

# Metadata fixture for CHL dataset (time_coverage_end: 2026-09-07T12:00:00Z)
CHL_METADATA_FIXTURE = {
    "table": {
        "columnNames": [
            "Row Type",
            "Variable Name",
            "Attribute Name",
            "Data Type",
            "Value",
        ],
        "columnTypes": ["String", "String", "String", "String", "String"],
        "rows": [
            [
                "attribute",
                "NC_GLOBAL",
                "time_coverage_start",
                "String",
                "2020-05-01T12:00:00Z",
            ],
            [
                "attribute",
                "NC_GLOBAL",
                "time_coverage_end",
                "String",
                "2026-09-07T12:00:00Z",
            ],
        ],
    }
}

# SYNTHETIC REALISTIC FIXTURE: Realistic Maharashtra SST observation
SST_SUCCESS_SYNTHETIC_FIXTURE = {
    "table": {
        "columnNames": [
            "time",
            "latitude",
            "longitude",
            "sea_surface_temperature",
            "quality_level",
            "sst_gradient_magnitude",
            "sst_front_position",
        ],
        "columnTypes": [
            "String",
            "double",
            "double",
            "float",
            "byte",
            "float",
            "byte",
        ],
        "columnUnits": [
            "UTC",
            "degrees_north",
            "degrees_east",
            "degree_C",
            "1",
            "kelvin/km",
            "1",
        ],
        "rows": [
            ["2026-09-08T12:00:00Z", 18.51, 72.51, 28.95, 5, 0.045, 1]
        ],
    }
}

# REAL CAPTURE FIXTURE: Live query to noaacwNPPN20VIIRSDINEOFDaily on 2026-09-10
CHL_SUCCESS_REAL_CAPTURE_FIXTURE = {
    "table": {
        "columnNames": ["time", "altitude", "latitude", "longitude", "chlor_a"],
        "columnTypes": ["String", "double", "float", "float", "float"],
        "columnUnits": ["UTC", "m", "degrees_north", "degrees_east", "mg m^-3"],
        "rows": [
            ["2026-09-07T12:00:00Z", 0, 18.541662, 72.541664, 0.881046]
        ],
    }
}

# SST Fill Value fixture (-327.68)
SST_FILL_VALUE_FIXTURE = {
    "table": {
        "columnNames": [
            "time",
            "latitude",
            "longitude",
            "sea_surface_temperature",
            "quality_level",
            "sst_gradient_magnitude",
            "sst_front_position",
        ],
        "columnTypes": [
            "String",
            "double",
            "double",
            "float",
            "byte",
            "float",
            "byte",
        ],
        "columnUnits": [
            "UTC",
            "degrees_north",
            "degrees_east",
            "degree_C",
            "1",
            "kelvin/km",
            "1",
        ],
        "rows": [
            ["2026-09-08T12:00:00Z", 18.51, 72.51, SST_FILL_VALUE, 0, None, None]
        ],
    }
}

# CHL Fill Value fixture (-999.0)
CHL_FILL_VALUE_FIXTURE = {
    "table": {
        "columnNames": ["time", "altitude", "latitude", "longitude", "chlor_a"],
        "columnTypes": ["String", "double", "float", "float", "float"],
        "columnUnits": ["UTC", "m", "degrees_north", "degrees_east", "mg m^-3"],
        "rows": [
            ["2026-09-07T12:00:00Z", 0, 18.541662, 72.541664, CHL_FILL_VALUE]
        ],
    }
}


def _make_transport(
    sst_griddap_data: dict | None = None,
    chl_griddap_data: dict | None = None,
    sst_metadata: dict | None = None,
    chl_metadata: dict | None = None,
    sst_status: int = 200,
    chl_status: int = 200,
    recorded_requests: list[httpx.Request] | None = None,
    custom_time_response: dict | None = None,
) -> httpx.MockTransport:
    """Helper creating a MockTransport routing metadata and griddap requests."""

    def handler(request: httpx.Request) -> httpx.Response:
        if recorded_requests is not None:
            recorded_requests.append(request)

        url_str = str(request.url)

        # Metadata info queries
        if f"/info/{SST_DATASET_ID}/index.json" in url_str:
            return httpx.Response(200, json=sst_metadata or SST_METADATA_FIXTURE)
        if f"/info/{CHL_DATASET_ID}/index.json" in url_str:
            return httpx.Response(200, json=chl_metadata or CHL_METADATA_FIXTURE)

        # Coordinate variable time queries
        if "?time[" in url_str or "?time" in url_str:
            if custom_time_response is not None:
                return httpx.Response(200, json=custom_time_response)
            default_time = (
                "2026-09-08T12:00:00Z"
                if SST_DATASET_ID in url_str
                else "2026-09-07T12:00:00Z"
            )
            return httpx.Response(
                200,
                json={
                    "table": {
                        "columnNames": ["time"],
                        "columnTypes": ["String"],
                        "columnUnits": ["UTC"],
                        "rows": [[default_time]],
                    }
                },
            )

        # Griddap observation queries
        if f"/griddap/{SST_DATASET_ID}.json" in url_str:
            if sst_status != 200:
                return httpx.Response(sst_status, text="Error from SST server")
            return httpx.Response(
                200, json=sst_griddap_data or SST_SUCCESS_SYNTHETIC_FIXTURE
            )

        if f"/griddap/{CHL_DATASET_ID}.json" in url_str:
            if chl_status != 200:
                return httpx.Response(chl_status, text="Error from CHL server")
            return httpx.Response(
                200, json=chl_griddap_data or CHL_SUCCESS_REAL_CAPTURE_FIXTURE
            )

        return httpx.Response(404, text=f"Not Found: {url_str}")

    return httpx.MockTransport(handler)


# ── Test 1: SST SUCCESS ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sst_success_parses_synthetic_fixture():
    """
    Test 1: SST SUCCESS parses synthetic realistic fixture.
    Verifies value_celsius, quality_level, gradient, front_position, and provenance.
    """
    transport = _make_transport(sst_griddap_data=SST_SUCCESS_SYNTHETIC_FIXTURE)
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    target_date = date(2026, 9, 8)
    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=target_date)

    assert obs.outcome == ObservationOutcome.SUCCESS
    assert obs.value_celsius == 28.95
    assert obs.quality_level == 5
    assert obs.gradient_magnitude_k_per_km == 0.045
    assert obs.front_position is True
    assert obs.grid_lat == 18.51
    assert obs.grid_lon == 72.51
    assert obs.source_dataset == SST_DATASET_ID
    assert obs.error_message is None
    assert obs.observation_time == datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    assert obs.requested_time.date() == target_date


# ── Test 2: SST FILL_VALUE ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sst_fill_value_produces_none_value():
    """
    Test 2: SST FILL_VALUE (-327.68) yields outcome=FILL_VALUE and value=None.
    Confirms fill values are never converted to 0.0.
    """
    transport = _make_transport(sst_griddap_data=SST_FILL_VALUE_FIXTURE)
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=date(2026, 9, 8))

    assert obs.outcome == ObservationOutcome.FILL_VALUE
    assert obs.value_celsius is None
    assert obs.value_celsius != 0.0
    assert obs.observation_time is not None
    assert obs.grid_lat == 18.51


# ── Test 3: CHL SUCCESS (Real Capture) ─────────────────────────────────


@pytest.mark.asyncio
async def test_chl_success_real_capture_fixture():
    """
    Test 3: CHL SUCCESS using the real captured 0.881046 mg/m^3 fixture.
    Verifies exact value, documented confidence ceiling (0.7), and grid coordinate provenance.
    """
    transport = _make_transport(chl_griddap_data=CHL_SUCCESS_REAL_CAPTURE_FIXTURE)
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    target_date = date(2026, 9, 7)
    obs = await client.get_chl(lat=18.5, lon=72.5, target_date=target_date)

    assert obs.outcome == ObservationOutcome.SUCCESS
    assert obs.value_mg_m3 == 0.881046
    assert obs.confidence_ceiling == CHL_CONFIDENCE_CEILING
    assert obs.confidence_ceiling == 0.7
    assert obs.grid_lat == pytest.approx(18.541662, abs=1e-5)
    assert obs.grid_lon == pytest.approx(72.541664, abs=1e-5)
    assert obs.source_dataset == CHL_DATASET_ID
    assert obs.observation_time == datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)


# ── Test 4: CHL FILL_VALUE ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chl_fill_value_produces_none_value():
    """
    Test 4: CHL FILL_VALUE (-999.0) yields outcome=FILL_VALUE and value=None.
    Confirms missing values are never zeroed.
    """
    transport = _make_transport(chl_griddap_data=CHL_FILL_VALUE_FIXTURE)
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    obs = await client.get_chl(lat=18.5, lon=72.5, target_date=date(2026, 9, 7))

    assert obs.outcome == ObservationOutcome.FILL_VALUE
    assert obs.value_mg_m3 is None
    assert obs.value_mg_m3 != 0.0
    assert obs.confidence_ceiling is None


# ── Test 5: CHL Altitude Dimension Structure ───────────────────────────


def test_chl_altitude_dimension_structure_vs_sst():
    """
    Test 5: CHL dimension structure vs SST.
    CHL query URL MUST include the mandatory [(0.0)] altitude bracket.
    SST query URL MUST NOT include an altitude bracket.
    Uses dynamic resolved timestamp without hardcoded noon assumption.
    """
    base_url = "https://coastwatch.noaa.gov/erddap"
    test_time_str = "2026-09-08T06:30:15Z"
    lat, lon = 18.5, 72.5

    sst_url = EnvironmentalClient._build_sst_query_url(
        base_url, test_time_str, lat, lon
    )
    chl_url = EnvironmentalClient._build_chl_query_url(
        base_url, test_time_str, lat, lon
    )

    # CHL must include [(0.0)] altitude slice
    assert "[(0.0)]" in chl_url
    assert chl_url == (
        f"{base_url}/griddap/{CHL_DATASET_ID}.json?"
        f"chlor_a[({test_time_str})][(0.0)][({lat})][({lon})]"
    )

    # SST must not have [(0.0)]
    assert "[(0.0)]" not in sst_url
    assert sst_url.startswith(f"{base_url}/griddap/{SST_DATASET_ID}.json?")
    assert f"[({test_time_str})][({lat})][({lon})]" in sst_url


# ── Test 6: Coordinate Order Regression ────────────────────────────────


@pytest.mark.asyncio
async def test_coordinate_order_latitude_before_longitude():
    """
    Test 6: Coordinate order regression.
    ERDDAP griddap dimension order is [time][altitude?][latitude][longitude].
    Latitude MUST precede longitude in query strings. Distinct lat (18.5) and
    lon (72.8) ensure an axis inversion is reliably caught.
    """
    recorded: list[httpx.Request] = []
    transport = _make_transport(recorded_requests=recorded)
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    lat, lon = 18.5, 72.8
    await client.get_sst(lat=lat, lon=lon, target_date=date(2026, 9, 8))
    await client.get_chl(lat=lat, lon=lon, target_date=date(2026, 9, 7))

    urls = [str(r.url) for r in recorded]

    sst_griddap_urls = [
        u for u in urls if f"/griddap/{SST_DATASET_ID}" in u and "sea_surface" in u
    ]
    assert len(sst_griddap_urls) == 1
    # Check [latitude][longitude] -> [(18.5)][(72.8)]
    assert "[(18.5)][(72.8)]" in sst_griddap_urls[0]
    assert "[(72.8)][(18.5)]" not in sst_griddap_urls[0]

    chl_griddap_urls = [
        u for u in urls if f"/griddap/{CHL_DATASET_ID}" in u and "chlor_a" in u
    ]
    assert len(chl_griddap_urls) == 1
    assert "[(0.0)][(18.5)][(72.8)]" in chl_griddap_urls[0]
    assert "[(0.0)][(72.8)][(18.5)]" not in chl_griddap_urls[0]


# ── Test 7: Dynamic Date Fallback & Actual Timestamp Preservation ──────


@pytest.mark.asyncio
async def test_dynamic_date_fallback_and_no_future_drift():
    """
    Test 7: Dynamic latest-date fallback.
    When requested date is beyond time_coverage_end:
    - Outcome is STALE_FALLBACK.
    - requested_time reflects the originally requested date.
    - observation_time reflects the actual observation timestamp returned by ERDDAP.
    - Uses actual latest available timestamp from ERDDAP metadata without hardcoded noon.
    """
    # Create metadata with an explicit non-noon time_coverage_end (18:45:00Z)
    non_noon_sst_meta = {
        "table": {
            "columnNames": [
                "Row Type",
                "Variable Name",
                "Attribute Name",
                "Data Type",
                "Value",
            ],
            "columnTypes": ["String", "String", "String", "String", "String"],
            "rows": [
                [
                    "attribute",
                    "NC_GLOBAL",
                    "time_coverage_start",
                    "String",
                    "2020-01-01T12:00:00Z",
                ],
                [
                    "attribute",
                    "NC_GLOBAL",
                    "time_coverage_end",
                    "String",
                    "2026-09-08T18:45:00Z",
                ],
            ],
        }
    }
    non_noon_sst_data = {
        "table": {
            "columnNames": [
                "time",
                "latitude",
                "longitude",
                "sea_surface_temperature",
            ],
            "columnTypes": ["String", "double", "double", "float"],
            "columnUnits": ["UTC", "degrees_north", "degrees_east", "degree_C"],
            "rows": [["2026-09-08T18:45:00Z", 18.51, 72.51, 28.95]],
        }
    }

    recorded: list[httpx.Request] = []
    transport = _make_transport(
        sst_metadata=non_noon_sst_meta,
        sst_griddap_data=non_noon_sst_data,
        recorded_requests=recorded,
    )
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    requested_future_date = date(2026, 9, 15)
    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=requested_future_date)

    assert obs.outcome == ObservationOutcome.STALE_FALLBACK
    assert obs.requested_time.date() == requested_future_date
    assert obs.observation_time == datetime(
        2026, 9, 8, 18, 45, tzinfo=timezone.utc
    )
    assert obs.value_celsius == 28.95

    # Verify that the griddap query used the actual metadata timestamp, NOT noon
    query_urls = [
        str(r.url) for r in recorded if "sea_surface_temperature" in str(r.url)
    ]
    assert len(query_urls) == 1
    assert "[(2026-09-08T18:45:00Z)]" in query_urls[0]
    assert "12:00:00Z" not in query_urls[0]


# ── Test 8: Transient Error Retries Exhausted ──────────────────────────


@pytest.mark.asyncio
async def test_transient_error_retries_exhausted():
    """
    Test 8: Transient network failures trigger retry up to max_retries
    and conclude with TRANSIENT_ERROR.
    """
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        url_str = str(request.url)
        if "index.json" in url_str:
            return httpx.Response(200, json=SST_METADATA_FIXTURE)
        call_count += 1
        raise httpx.ConnectError("Connection refused by NOAA ERDDAP")

    transport = httpx.MockTransport(handler)
    client = EnvironmentalClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,
        max_retries=3,
    )

    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=date(2026, 9, 8))

    assert obs.outcome == ObservationOutcome.TRANSIENT_ERROR
    assert call_count == 4  # 1 initial + 3 retries
    assert obs.value_celsius is None
    assert "Connection refused" in (obs.error_message or "")


# ── Test 9: Non-Transient Errors Not Retried ────────────────────────────


@pytest.mark.asyncio
async def test_non_transient_error_not_retried():
    """
    Test 9: Non-transient responses (e.g. malformed JSON or HTTP 404) are executed
    exactly once without retry (call_count == 1).
    """
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        url_str = str(request.url)
        if "index.json" in url_str:
            return httpx.Response(200, json=SST_METADATA_FIXTURE)
        call_count += 1
        return httpx.Response(200, text="not json { bad: data")

    transport = httpx.MockTransport(handler)
    client = EnvironmentalClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,
    )

    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=date(2026, 9, 8))

    assert obs.outcome == ObservationOutcome.UNEXPECTED_ERROR
    assert call_count == 1
    assert "Malformed JSON" in (obs.error_message or "")


# ── Test 10: Join Environmental Data with Mixed Outcomes ───────────────


@pytest.mark.asyncio
async def test_join_environmental_data_mixed_outcomes():
    """
    Test 10: join_environmental_data with 3 synthetic PFZSamplePoints:
    Point 0: SST SUCCESS / CHL SUCCESS
    Point 1: SST FILL_VALUE / CHL SUCCESS
    Point 2: SST TRANSIENT_ERROR / CHL SUCCESS
    Confirms all 3 points are preserved in order and zero points are dropped.
    """
    points = [
        PFZSamplePoint(
            lon=72.51,
            lat=18.51,
            part_index=0,
            distance_along_part_km=0.0,
            is_endpoint=True,
            source_uid="2026251001.0",
        ),
        PFZSamplePoint(
            lon=72.52,
            lat=18.52,
            part_index=0,
            distance_along_part_km=3.0,
            is_endpoint=False,
            source_uid="2026251001.0",
        ),
        PFZSamplePoint(
            lon=72.53,
            lat=18.53,
            part_index=0,
            distance_along_part_km=6.0,
            is_endpoint=True,
            source_uid="2026251001.0",
        ),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if f"/info/{SST_DATASET_ID}/index.json" in url_str:
            return httpx.Response(200, json=SST_METADATA_FIXTURE)
        if f"/info/{CHL_DATASET_ID}/index.json" in url_str:
            return httpx.Response(200, json=CHL_METADATA_FIXTURE)

        # Time coordinate queries
        if "?time[" in url_str:
            time_val = (
                "2026-09-07T12:00:00Z"
                if CHL_DATASET_ID in url_str
                else "2026-09-07T12:00:00Z"
            )
            return httpx.Response(
                200,
                json={
                    "table": {
                        "columnNames": ["time"],
                        "columnTypes": ["String"],
                        "columnUnits": ["UTC"],
                        "rows": [[time_val]],
                    }
                },
            )

        # CHL always succeeds
        if f"/griddap/{CHL_DATASET_ID}.json" in url_str:
            return httpx.Response(200, json=CHL_SUCCESS_REAL_CAPTURE_FIXTURE)

        # SST outcome varies by point latitude:
        if f"/griddap/{SST_DATASET_ID}.json" in url_str:
            if "[(18.51)]" in url_str:
                return httpx.Response(200, json=SST_SUCCESS_SYNTHETIC_FIXTURE)
            elif "[(18.52)]" in url_str:
                return httpx.Response(200, json=SST_FILL_VALUE_FIXTURE)
            elif "[(18.53)]" in url_str:
                raise httpx.ConnectError("SST server unavailable for point 2")

        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = EnvironmentalClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,
    )

    joined = await client.join_environmental_data(
        points, target_date=date(2026, 9, 7)
    )

    assert len(joined) == 3
    assert all(isinstance(p, SampledEnvironmentalPoint) for p in joined)

    # Point 0: SUCCESS / SUCCESS
    assert joined[0].sample_point.lat == 18.51
    assert joined[0].sst.outcome == ObservationOutcome.SUCCESS
    assert joined[0].sst.value_celsius == 28.95
    assert joined[0].chl.outcome == ObservationOutcome.SUCCESS

    # Point 1: FILL_VALUE / SUCCESS
    assert joined[1].sample_point.lat == 18.52
    assert joined[1].sst.outcome == ObservationOutcome.FILL_VALUE
    assert joined[1].sst.value_celsius is None
    assert joined[1].chl.outcome == ObservationOutcome.SUCCESS

    # Point 2: TRANSIENT_ERROR / SUCCESS
    assert joined[2].sample_point.lat == 18.53
    assert joined[2].sst.outcome == ObservationOutcome.TRANSIENT_ERROR
    assert joined[2].sst.value_celsius is None
    assert joined[2].chl.outcome == ObservationOutcome.SUCCESS


# ── Test 11: Concurrency Bound Strictly Limiting Network Calls ────────


@pytest.mark.asyncio
async def test_concurrency_bound_semaphore():
    """
    Test 11: Concurrency bound.
    Instruments mock transport with active in-flight request tracking and verifies
    simultaneous network requests never exceed max_concurrency.
    """
    max_concurrency = 3
    active_in_flight = 0
    max_observed_in_flight = 0
    lock = asyncio.Lock()

    async def async_handler(request: httpx.Request) -> httpx.Response:
        nonlocal active_in_flight, max_observed_in_flight
        url_str = str(request.url)

        async with lock:
            active_in_flight += 1
            if active_in_flight > max_observed_in_flight:
                max_observed_in_flight = active_in_flight

        # Simulate network latency
        await asyncio.sleep(0.01)

        async with lock:
            active_in_flight -= 1

        if "index.json" in url_str:
            if SST_DATASET_ID in url_str:
                return httpx.Response(200, json=SST_METADATA_FIXTURE)
            return httpx.Response(200, json=CHL_METADATA_FIXTURE)

        if SST_DATASET_ID in url_str:
            return httpx.Response(200, json=SST_SUCCESS_SYNTHETIC_FIXTURE)
        return httpx.Response(200, json=CHL_SUCCESS_REAL_CAPTURE_FIXTURE)

    transport = httpx.MockTransport(async_handler)
    client = EnvironmentalClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,
    )

    # Create 8 sample points
    points = [
        PFZSamplePoint(
            lon=72.0 + i * 0.1,
            lat=18.0 + i * 0.1,
            part_index=0,
            distance_along_part_km=float(i * 3),
            is_endpoint=(i in (0, 7)),
        )
        for i in range(8)
    ]

    joined = await client.join_environmental_data(
        points, target_date=date(2026, 9, 7), max_concurrency=max_concurrency
    )

    assert len(joined) == 8
    # Individual network requests are strictly bounded by max_concurrency
    assert max_observed_in_flight <= max_concurrency


# ── Test 12: Cache Key Stub ────────────────────────────────────────────


def test_build_cache_key_stub():
    """
    Test 12: Cache key stub produces deterministic string shape.
    """
    target_date = date(2026, 9, 8)
    key = EnvironmentalClient.build_cache_key(
        dataset_id=SST_DATASET_ID,
        target_date=target_date,
        lat=18.51234,
        lon=72.51876,
    )
    assert key == f"env:v1:{SST_DATASET_ID}:2026-09-08:18.5123,72.5188"


# ── Test 13: Non-Noon Time Coordinate Resolution from ERDDAP ──────────


@pytest.mark.asyncio
async def test_timestamp_resolution_preserves_non_noon_time_coordinate():
    """
    Test 13: Confirms actual time coordinate returned by ERDDAP (e.g. 05:42:10Z)
    is used in the griddap query slice without being replaced by noon.
    """
    custom_time_str = "2026-09-05T05:42:10Z"
    custom_time_data = {
        "table": {
            "columnNames": ["time"],
            "columnTypes": ["String"],
            "columnUnits": ["UTC"],
            "rows": [[custom_time_str]],
        }
    }
    custom_sst_obs_data = {
        "table": {
            "columnNames": [
                "time",
                "latitude",
                "longitude",
                "sea_surface_temperature",
            ],
            "columnTypes": ["String", "double", "double", "float"],
            "columnUnits": ["UTC", "degrees_north", "degrees_east", "degree_C"],
            "rows": [[custom_time_str, 18.51, 72.51, 29.10]],
        }
    }

    recorded: list[httpx.Request] = []
    transport = _make_transport(
        sst_griddap_data=custom_sst_obs_data,
        custom_time_response=custom_time_data,
        recorded_requests=recorded,
    )
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    target_date = date(2026, 9, 5)
    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=target_date)

    assert obs.outcome == ObservationOutcome.SUCCESS
    assert obs.observation_time == datetime(
        2026, 9, 5, 5, 42, 10, tzinfo=timezone.utc
    )
    assert obs.value_celsius == 29.10

    # Confirm the griddap query URL slice uses the actual resolved timestamp
    griddap_requests = [
        str(r.url) for r in recorded if "sea_surface_temperature" in str(r.url)
    ]
    assert len(griddap_requests) == 1
    assert f"[({custom_time_str})]" in griddap_requests[0]
    assert "12:00:00Z" not in griddap_requests[0]


# ── Test 14: SST Gradient Fill Value (-32.768) Parsed as None ──────────


@pytest.mark.asyncio
async def test_sst_gradient_fill_value_is_none():
    """
    Test 14: Confirms that sst_gradient_magnitude = -32.768 (the verified Float32
    _FillValue in NOAA .das metadata) is correctly parsed as None, not treated as a valid gradient.
    """
    grad_fill_sst_data = {
        "table": {
            "columnNames": [
                "time",
                "latitude",
                "longitude",
                "sea_surface_temperature",
                "quality_level",
                "sst_gradient_magnitude",
                "sst_front_position",
            ],
            "columnTypes": [
                "String",
                "double",
                "double",
                "float",
                "byte",
                "float",
                "byte",
            ],
            "columnUnits": [
                "UTC",
                "degrees_north",
                "degrees_east",
                "degree_C",
                "1",
                "kelvin/km",
                "1",
            ],
            "rows": [
                [
                    "2026-09-08T12:00:00Z",
                    18.51,
                    72.51,
                    28.95,
                    5,
                    -32.768,
                    1,
                ]
            ],
        }
    }

    transport = _make_transport(sst_griddap_data=grad_fill_sst_data)
    client = EnvironmentalClient(http_client=httpx.AsyncClient(transport=transport))

    obs = await client.get_sst(lat=18.51, lon=72.51, target_date=date(2026, 9, 8))

    assert obs.outcome == ObservationOutcome.SUCCESS
    assert obs.value_celsius == 28.95
    assert obs.quality_level == 5
    assert obs.gradient_magnitude_k_per_km is None
    assert obs.front_position is True


# ── Test 15: Constructor max_concurrency Respected Without Override ────


@pytest.mark.asyncio
async def test_constructor_max_concurrency_respected_without_method_override():
    """
    Test 15: Confirms that EnvironmentalClient(max_concurrency=2) limits concurrent
    network requests in join_environmental_data() to 2 when no method-level override is supplied.
    """
    constructor_max_concurrency = 2
    active_in_flight = 0
    max_observed_in_flight = 0
    lock = asyncio.Lock()

    async def async_handler(request: httpx.Request) -> httpx.Response:
        nonlocal active_in_flight, max_observed_in_flight
        url_str = str(request.url)

        async with lock:
            active_in_flight += 1
            if active_in_flight > max_observed_in_flight:
                max_observed_in_flight = active_in_flight

        # Simulate network delay
        await asyncio.sleep(0.01)

        async with lock:
            active_in_flight -= 1

        if "index.json" in url_str:
            if SST_DATASET_ID in url_str:
                return httpx.Response(200, json=SST_METADATA_FIXTURE)
            return httpx.Response(200, json=CHL_METADATA_FIXTURE)

        if SST_DATASET_ID in url_str:
            return httpx.Response(200, json=SST_SUCCESS_SYNTHETIC_FIXTURE)
        return httpx.Response(200, json=CHL_SUCCESS_REAL_CAPTURE_FIXTURE)

    transport = httpx.MockTransport(async_handler)
    client = EnvironmentalClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,
        max_concurrency=constructor_max_concurrency,
    )

    points = [
        PFZSamplePoint(
            lon=72.0 + i * 0.1,
            lat=18.0 + i * 0.1,
            part_index=0,
            distance_along_part_km=float(i * 3),
            is_endpoint=(i in (0, 7)),
        )
        for i in range(8)
    ]

    # Call join_environmental_data WITHOUT passing max_concurrency
    joined = await client.join_environmental_data(
        points, target_date=date(2026, 9, 7)
    )

    assert len(joined) == 8
    assert max_observed_in_flight <= constructor_max_concurrency
