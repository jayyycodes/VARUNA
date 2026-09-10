"""
Tests for the INCOIS PFZ WFS Client.

Uses httpx.MockTransport to simulate WFS responses without network access.
Fixture files are in agents/marine_fishing/tests/fixtures/.
"""

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from shapely.geometry import MultiLineString

from agents.marine_fishing.models import (
    PFZBoundingBox,
    PFZFeature,
    PFZOutcome,
)
from agents.marine_fishing.pfz_client import PFZClient

# ── Fixture helpers ────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    """Read a fixture file as a UTF-8 string."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _make_json_transport(fixture_name: str) -> httpx.MockTransport:
    """Create a MockTransport that returns the given JSON fixture."""
    body = _load_fixture(fixture_name)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=body,
            headers={"content-type": "application/json"},
        )

    return httpx.MockTransport(handler)


def _make_xml_transport(fixture_name: str) -> httpx.MockTransport:
    """Create a MockTransport that returns the given XML fixture."""
    body = _load_fixture(fixture_name)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=body,
            headers={"content-type": "application/xml"},
        )

    return httpx.MockTransport(handler)


@pytest.fixture
def sample_date() -> date:
    """A known date that maps to Julian day 251."""
    return date(2026, 9, 8)


# ── SUCCESS ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_success_parses_features(sample_date):
    """SUCCESS: parses pfz_sample_features.json correctly into typed models."""
    transport = _make_json_transport("pfz_sample_features.json")
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.SUCCESS
    assert len(result.features) == 4
    assert result.error_message is None
    assert result.attempts == 1

    # Verify typed fields on first feature
    feat = result.features[0]
    assert feat.year == 2026
    assert feat.julian_day == "251"
    assert feat.sector_name == "Maharashtra"
    assert feat.serial_number == "001"
    assert isinstance(feat.serial_number, str)
    assert feat.uid == 2026251001.0
    assert isinstance(feat.uid, float)
    assert feat.length == 52.3
    assert feat.sector_boundary == 3
    assert isinstance(feat.sector_boundary, int)
    assert feat.sector_boundary_1 == 3
    assert isinstance(feat.sector_boundary_1, int)

    # Geometry is a valid shapely MultiLineString
    assert feat.geometry is not None
    assert feat.geometry.geom_type == "MultiLineString"
    assert not feat.geometry.is_empty


def test_pfz_feature_preserves_verified_schema_types():
    """
    Verify PFZFeature field types accurately preserve INCOIS DescribeFeatureType:
    - SECTORBOUN (xsd:int) -> int
    - SECTORBO_1 (xsd:int) -> int
    - Sno (xsd:string) -> str, preserving leading zeros (e.g. '001')
    - UID (xsd:double) -> float, stored as numeric
    """
    raw_feature = {
        "type": "Feature",
        "geometry": {
            "type": "MultiLineString",
            "coordinates": [[[72.35, 19.10], [72.48, 19.25]]],
        },
        "properties": {
            "SECTORBOUN": 3,
            "SECTORBO_1": 3,
            "SECTORNAME": "Maharashtra",
            "Julian_day": "251",
            "Sno": "001",
            "Year": 2026,
            "UID": 2026251001.0,
            "Length": 52.3,
        },
    }

    feat = PFZClient._parse_single_feature(raw_feature)

    assert feat.sector_boundary == 3
    assert isinstance(feat.sector_boundary, int)
    assert feat.sector_boundary_1 == 3
    assert isinstance(feat.sector_boundary_1, int)
    assert feat.serial_number == "001"
    assert isinstance(feat.serial_number, str)
    assert feat.uid == 2026251001.0
    assert isinstance(feat.uid, float)


# ── EMPTY ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_distinguishable_from_success(sample_date):
    """EMPTY: parses pfz_empty.json; outcome is EMPTY, not SUCCESS."""
    transport = _make_json_transport("pfz_empty.json")
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.EMPTY
    assert result.outcome != PFZOutcome.SUCCESS
    assert len(result.features) == 0
    assert result.error_message is None


# ── WFS_ERROR ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wfs_error_parses_ogc_exception(sample_date):
    """WFS_ERROR: parses pfz_ogc_exception.xml; extracts exceptionCode and text."""
    transport = _make_xml_transport("pfz_ogc_exception.xml")
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.WFS_ERROR
    assert result.exception_code == "OperationNotSupported"
    assert result.exception_text is not None
    assert "geoserver" in result.exception_text.lower()
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_wfs_error_not_retried(sample_date):
    """WFS_ERROR: OGC exception responses are NEVER retried (call count == 1)."""
    call_count = 0
    body = _load_fixture("pfz_ogc_exception.xml")

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200, text=body, headers={"content-type": "application/xml"}
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.WFS_ERROR
    assert call_count == 1
    assert result.attempts == 1


# ── TRANSIENT_ERROR ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_transient_error_retries_exhausted(sample_date):
    """TRANSIENT_ERROR: connection failure triggers retry; all attempts exhausted."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(handler)
    client = PFZClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,  # skip delay in tests
    )

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.TRANSIENT_ERROR
    assert call_count == 4  # 1 initial request + 3 retries
    assert result.attempts == 4
    assert result.error_message is not None
    assert "Connection refused" in result.error_message


@pytest.mark.asyncio
async def test_transient_error_success_on_retry(sample_date):
    """Retry recovery: first attempt fails transiently, second succeeds."""
    call_count = 0
    sample_body = _load_fixture("pfz_sample_features.json")

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectError("Connection refused")
        return httpx.Response(
            200,
            text=sample_body,
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(
        http_client=httpx.AsyncClient(transport=transport),
        backoff_base=0.0,
    )

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.SUCCESS
    assert call_count == 2
    assert result.attempts == 2


# ── UNEXPECTED_ERROR ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unexpected_error_malformed_json(sample_date):
    """UNEXPECTED_ERROR: malformed JSON does not crash; returns structured error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="{this is not valid json!!!",
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.UNEXPECTED_ERROR
    assert "Malformed JSON" in result.error_message


@pytest.mark.asyncio
async def test_unexpected_error_not_retried(sample_date):
    """UNEXPECTED_ERROR: malformed JSON is NOT retried (call count == 1)."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            text="not json at all",
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.UNEXPECTED_ERROR
    assert call_count == 1
    assert result.attempts == 1


@pytest.mark.asyncio
async def test_unexpected_error_http_500(sample_date):
    """UNEXPECTED_ERROR: non-200 with non-XML body surfaces as structured error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            text="Internal Server Error",
            headers={"content-type": "text/html"},
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.UNEXPECTED_ERROR
    assert "500" in result.error_message


# ── BBOX axis-order regression ─────────────────────────────────────────


def test_bbox_filter_produces_incois_axis_order():
    """
    Regression: _build_bbox_filter uses INCOIS-specific
    min_lat,min_lon,max_lat,max_lon order, NOT the standard OGC
    min_lon,min_lat,max_lon,max_lat order.
    """
    bbox = PFZBoundingBox(
        min_lat=18.5, min_lon=72.0, max_lat=20.0, max_lon=73.0
    )
    result = PFZClient._build_bbox_filter(bbox)

    # Correct INCOIS order: lat,lon,lat,lon → 18.5,72.0,20.0,73.0
    assert result == "BBOX(the_geom,18.5,72.0,20.0,73.0)"

    # Standard OGC order (WRONG for this endpoint) would be:
    # lon,lat,lon,lat → 72.0,18.5,73.0,20.0
    wrong_order = (
        f"BBOX(the_geom,"
        f"{bbox.min_lon},{bbox.min_lat},"
        f"{bbox.max_lon},{bbox.max_lat})"
    )
    assert wrong_order == "BBOX(the_geom,72.0,18.5,73.0,20.0)"
    assert result != wrong_order


@pytest.mark.asyncio
async def test_bbox_round_trip_correct_order_returns_features(sample_date):
    """
    Round-trip: correct INCOIS bbox order returns features; mock verifies
    the CQL_FILTER string sent over the wire uses the INCOIS axis order.

    Uses pfz_sample_features.json's actual Maharashtra coordinates —
    features 1 and 2 have coordinates within BBOX(18.5,72.0,20.0,73.0).
    """
    sample_body = _load_fixture("pfz_sample_features.json")
    empty_body = _load_fixture("pfz_empty.json")
    captured_cql: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        cql = request.url.params.get("CQL_FILTER", "")
        captured_cql.append(cql)
        # Return features only for the correct INCOIS axis order
        if "BBOX(the_geom,18.5,72.0,20.0,73.0)" in cql:
            return httpx.Response(
                200,
                text=sample_body,
                headers={"content-type": "application/json"},
            )
        return httpx.Response(
            200,
            text=empty_body,
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    bbox = PFZBoundingBox(
        min_lat=18.5, min_lon=72.0, max_lat=20.0, max_lon=73.0
    )
    result = await client.get_pfz_features(sample_date, bbox=bbox)

    assert result.outcome == PFZOutcome.SUCCESS
    assert len(result.features) > 0
    # Verify the CQL sent uses INCOIS order, not standard OGC order
    assert "BBOX(the_geom,18.5,72.0,20.0,73.0)" in captured_cql[0]
    assert "BBOX(the_geom,72.0,18.5,73.0,20.0)" not in captured_cql[0]


def test_bbox_model_rejects_out_of_range_latitude():
    """
    PFZBoundingBox field constraints reject numerically out-of-range coordinates (>90).

    Note: This does not detect axis-order swaps in general, because Indian coastal
    longitudes (~68-97°E) fall within the valid [-90, 90] latitude range and would
    pass undetected by numerical bounds alone. Protection against axis-order mistakes
    is handled by tests directly verifying the CQL output string.
    """
    with pytest.raises(ValidationError):
        PFZBoundingBox(
            min_lat=95.0, min_lon=18.5, max_lat=20.0, max_lon=73.0
        )


def test_bbox_model_rejects_reversed_latitude_bounds():
    """PFZBoundingBox model_validator enforces min_lat < max_lat."""
    with pytest.raises(ValidationError, match="min_lat .* must be less than max_lat"):
        PFZBoundingBox(
            min_lat=20.0, min_lon=72.0, max_lat=18.5, max_lon=73.0
        )


def test_bbox_model_rejects_reversed_longitude_bounds():
    """PFZBoundingBox model_validator enforces min_lon < max_lon."""
    with pytest.raises(ValidationError, match="min_lon .* must be less than max_lon"):
        PFZBoundingBox(
            min_lat=18.5, min_lon=73.0, max_lat=20.0, max_lon=72.0
        )


# ── Count-parity test (deferred) ──────────────────────────────────────


@pytest.mark.skip(
    reason="Count-parity test against a real 106-feature INCOIS capture is deferred until a real capture is available from a live DevTools session. Do not fabricate this fixture."
)
def test_count_parity_real_capture_deferred():
    """
    Count-parity test against a real 106-feature INCOIS capture is
    deferred until a real capture is available from a live DevTools
    session. Do not fabricate this fixture.
    """
    pass


# ── Multi-part geometry safety ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_multipart_geometry_both_parts_handled(sample_date):
    """
    Synthetic multi-part MultiLineString: confirm both parts are
    independently accessible in the parsed geometry (no assumption
    of exactly one part).
    """
    multi_part_fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "pfzlines.synthetic-multi",
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        # Part 1: off Maharashtra coast
                        [[72.5, 19.0], [72.6, 19.1], [72.7, 19.2]],
                        # Part 2: separate segment further south
                        [[73.0, 15.5], [73.1, 15.6], [73.2, 15.7]],
                    ],
                },
                "geometry_name": "the_geom",
                "properties": {
                    "SECTORNAME": "TestSector",
                    "Julian_day": "251",
                    "Sno": "001",
                    "Year": 2026,
                    "UID": 2026251001.0,
                    "Length": 99.9,
                },
            }
        ],
        "totalFeatures": 1,
        "numberMatched": 1,
        "numberReturned": 1,
    }
    body = json.dumps(multi_part_fc)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text=body, headers={"content-type": "application/json"}
        )

    transport = httpx.MockTransport(handler)
    client = PFZClient(http_client=httpx.AsyncClient(transport=transport))

    result = await client.get_pfz_features(sample_date)

    assert result.outcome == PFZOutcome.SUCCESS
    assert len(result.features) == 1

    geom = result.features[0].geometry
    assert geom.geom_type == "MultiLineString"
    assert isinstance(geom, MultiLineString)

    # Both parts must be independently accessible
    parts = list(geom.geoms)
    assert len(parts) == 2

    # Each part is independently iterable with correct point counts
    part1_coords = list(parts[0].coords)
    part2_coords = list(parts[1].coords)
    assert len(part1_coords) == 3
    assert len(part2_coords) == 3

    # Parts are distinct (different coordinate ranges)
    assert part1_coords[0] != part2_coords[0]


# ── Date conversion ───────────────────────────────────────────────────


def test_date_to_year_julian():
    """Verify date → (year, zero-padded julian_day) conversion."""
    assert PFZClient._date_to_year_julian(date(2026, 9, 8)) == (2026, "251")
    assert PFZClient._date_to_year_julian(date(2026, 1, 1)) == (2026, "001")
    assert PFZClient._date_to_year_julian(date(2026, 12, 31)) == (2026, "365")


# ── CQL filter construction ───────────────────────────────────────────


def test_cql_filter_basic():
    """CQL filter includes Year and Julian_day."""
    cql = PFZClient._build_cql_filter(2026, "251", None, None)
    assert cql == "Year=2026 AND Julian_day='251'"


def test_cql_filter_with_sector():
    """CQL filter includes SECTORNAME when provided."""
    cql = PFZClient._build_cql_filter(2026, "251", "Maharashtra", None)
    assert cql == "Year=2026 AND Julian_day='251' AND SECTORNAME='Maharashtra'"


def test_cql_filter_with_bbox():
    """CQL filter includes BBOX with INCOIS axis order."""
    bbox = PFZBoundingBox(
        min_lat=18.5, min_lon=72.0, max_lat=20.0, max_lon=73.0
    )
    cql = PFZClient._build_cql_filter(2026, "251", None, bbox)
    assert cql == (
        "Year=2026 AND Julian_day='251' AND "
        "BBOX(the_geom,18.5,72.0,20.0,73.0)"
    )


def test_cql_filter_with_sector_and_bbox():
    """CQL filter includes both sector and BBOX."""
    bbox = PFZBoundingBox(
        min_lat=18.5, min_lon=72.0, max_lat=20.0, max_lon=73.0
    )
    cql = PFZClient._build_cql_filter(2026, "251", "Maharashtra", bbox)
    assert cql == (
        "Year=2026 AND Julian_day='251' AND "
        "SECTORNAME='Maharashtra' AND "
        "BBOX(the_geom,18.5,72.0,20.0,73.0)"
    )


# ── Cache key ─────────────────────────────────────────────────────────


def test_build_cache_key_simple():
    """Cache key for date-only query."""
    key = PFZClient.build_cache_key(2026, "251", None, None)
    assert key == "pfz:v1:2026:251"


def test_build_cache_key_with_sector():
    """Cache key includes sector component."""
    key = PFZClient.build_cache_key(2026, "251", "Maharashtra", None)
    assert key == "pfz:v1:2026:251:sector=Maharashtra"


def test_build_cache_key_with_bbox():
    """Cache key includes bbox component."""
    bbox = PFZBoundingBox(
        min_lat=18.5, min_lon=72.0, max_lat=20.0, max_lon=73.0
    )
    key = PFZClient.build_cache_key(2026, "251", None, bbox)
    assert key == "pfz:v1:2026:251:bbox=18.5,72.0,20.0,73.0"


def test_build_cache_key_full():
    """Cache key includes all components."""
    bbox = PFZBoundingBox(
        min_lat=18.5, min_lon=72.0, max_lat=20.0, max_lon=73.0
    )
    key = PFZClient.build_cache_key(2026, "251", "Maharashtra", bbox)
    assert key == "pfz:v1:2026:251:sector=Maharashtra:bbox=18.5,72.0,20.0,73.0"


# ── WFS params ────────────────────────────────────────────────────────


def test_wfs_params_structure():
    """WFS params include all required fields."""
    params = PFZClient._build_wfs_params("Year=2026 AND Julian_day='251'")
    assert params == {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": "PFZ_Automation:pfzlines",
        "outputFormat": "application/json",
        "CQL_FILTER": "Year=2026 AND Julian_day='251'",
    }
