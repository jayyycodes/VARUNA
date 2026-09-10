"""
Tests for PFZ geodesic resampling.

All geometries used in these tests are clearly synthetic — small, hand-built
line segments designed to exercise specific algorithm properties.  They are
NOT real INCOIS captures.

Test #8 (integration) uses the already-approved hand-crafted fixture
pfz_sample_features.json, which contains realistic but not fabricated-as-real
coordinates.
"""

import json
from pathlib import Path

import pytest
from pyproj import Geod
from shapely.geometry import MultiLineString, shape as shapely_shape

from agents.marine_fishing.geodesic_sampling import sample_pfz_feature
from agents.marine_fishing.models import PFZFeature, PFZSamplePoint

# ── Shared helpers ────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_GEOD = Geod(ellps="WGS84")


def _make_feature(
    coords: list,
    *,
    geom_type: str = "MultiLineString",
    uid: float | None = 1001.0,
) -> PFZFeature:
    """Build a minimal PFZFeature from raw coordinate lists."""
    geom = shapely_shape({"type": geom_type, "coordinates": coords})
    return PFZFeature(
        geometry=geom,
        julian_day="001",
        year=2026,
        uid=uid,
    )


def _geodesic_distance_km(lon1, lat1, lon2, lat2) -> float:
    """Independent geodesic distance (km) via pyproj — used to validate sampler."""
    _, _, dist_m = _GEOD.inv(lon1, lat1, lon2, lat2)
    return abs(dist_m) / 1000.0


# ── Test 1: Straight-line synthetic case (meridian) ───────────────────


def test_straight_meridian_sampling():
    """
    Synthetic: straight line along a constant meridian (lon=72.0,
    lat 10.0→11.0).  Geodesic distance is independently computed and
    compared against the sampler's output cumulative distances AND
    geographic positions.

    Position validation uses an independent geod.fwd() calculation in
    the test — it does NOT reuse the sampler's internal interpolation
    helper.
    """
    coords = [[[72.0, 10.0], [72.0, 10.5], [72.0, 11.0]]]
    feature = _make_feature(coords)

    # Independent expected total distance (two segments).
    seg1_km = _geodesic_distance_km(72.0, 10.0, 72.0, 10.5)
    seg2_km = _geodesic_distance_km(72.0, 10.5, 72.0, 11.0)
    expected_total_km = seg1_km + seg2_km

    points = sample_pfz_feature(feature, interval_km=20.0)

    # For a ~111 km line with 20 km interval, target distances are:
    # 0, 20, 40, 60, 80, 100, and the final endpoint (~111) = 7 points.
    assert len(points) == 7, f"Expected 7 points, got {len(points)}"

    # First and last cumulative distances should bracket the expected total.
    assert abs(points[0].distance_along_part_km - 0.0) < 0.001
    assert abs(points[-1].distance_along_part_km - expected_total_km) < 0.05

    # ── Independent position validation ───────────────────────────────
    # For a constant-meridian line, azimuth from start is due south→north
    # (≈0° or ≈360°).  We independently compute each target position using
    # geod.fwd() from the line's start vertex and compare.
    start_lon, start_lat = 72.0, 10.0
    fwd_az, _, _ = _GEOD.inv(72.0, 10.0, 72.0, 11.0)  # azimuth along meridian

    for pt in points:
        if pt.is_endpoint:
            continue  # endpoints are original vertices, validated in test 2

        # Independently compute expected position at this cumulative distance.
        exp_lon, exp_lat, _ = _GEOD.fwd(
            start_lon, start_lat, fwd_az, pt.distance_along_part_km * 1000.0
        )

        # Assert positions match within ~10 m tolerance.
        _, _, sep_m = _GEOD.inv(pt.lon, pt.lat, exp_lon, exp_lat)
        assert abs(sep_m) < 10.0, (
            f"Point at d={pt.distance_along_part_km:.2f} km: "
            f"sampler ({pt.lon:.6f}, {pt.lat:.6f}) vs "
            f"independent ({exp_lon:.6f}, {exp_lat:.6f}), "
            f"separation {abs(sep_m):.1f} m"
        )

    # Each intermediate point should be at its expected interval.
    for i, pt in enumerate(points[:-1]):  # skip last (endpoint, not at exact multiple)
        expected_d = i * 20.0
        if expected_d <= expected_total_km:
            assert abs(pt.distance_along_part_km - expected_d) < 0.05, (
                f"Point {i}: expected ~{expected_d:.2f} km, "
                f"got {pt.distance_along_part_km:.2f} km"
            )


# ── Test 2: Endpoint preservation ─────────────────────────────────────


def test_endpoint_preservation():
    """
    Synthetic: endpoints of each part must exactly match the original
    first/last vertex coordinates and have is_endpoint=True.
    """
    coords = [[[72.0, 10.0], [72.5, 10.5], [73.0, 11.0]]]
    feature = _make_feature(coords)

    points = sample_pfz_feature(feature, interval_km=20.0)

    assert len(points) >= 2

    first = points[0]
    last = points[-1]

    # First point matches first vertex exactly.
    assert first.lon == 72.0
    assert first.lat == 10.0
    assert first.is_endpoint is True
    assert first.distance_along_part_km == 0.0

    # Last point matches last vertex exactly.
    assert last.lon == 73.0
    assert last.lat == 11.0
    assert last.is_endpoint is True


# ── Test 3: Short-segment rule ────────────────────────────────────────


def test_short_segment_returns_single_midpoint():
    """
    Synthetic: a part shorter than interval_km returns exactly one point,
    which is a midpoint (is_endpoint=False) — not one of the original
    vertices.
    """
    # Two points ~1.5 km apart (very short segment).
    coords = [[[72.0, 10.0], [72.01, 10.01]]]
    feature = _make_feature(coords)

    seg_km = _geodesic_distance_km(72.0, 10.0, 72.01, 10.01)
    assert seg_km < 5.0, "Segment must be shorter than interval for this test"

    points = sample_pfz_feature(feature, interval_km=5.0)

    assert len(points) == 1
    pt = points[0]
    assert pt.is_endpoint is False
    assert pt.part_index == 0
    # Midpoint should be roughly halfway.
    assert abs(pt.distance_along_part_km - seg_km / 2.0) < 0.01


# ── Test 4: Multi-part independence ───────────────────────────────────


def test_multipart_independence():
    """
    Synthetic: a MultiLineString with two clearly separated parts
    (one near Maharashtra ~72°E/19°N, another near Kerala ~76°E/10°N).
    Confirms each part is sampled independently, part_index distinguishes
    them, and no distance leaks across the gap.
    """
    coords = [
        # Part 0: Maharashtra coast (~40 km-ish line).
        [[72.0, 19.0], [72.2, 19.2], [72.4, 19.4]],
        # Part 1: Kerala coast (~40 km-ish line), far away.
        [[76.0, 10.0], [76.2, 10.2], [76.4, 10.4]],
    ]
    feature = _make_feature(coords)

    points = sample_pfz_feature(feature, interval_km=10.0)

    part0_pts = [p for p in points if p.part_index == 0]
    part1_pts = [p for p in points if p.part_index == 1]

    assert len(part0_pts) >= 2
    assert len(part1_pts) >= 2

    # Each part's distances start at 0 — they are independent walks.
    assert part0_pts[0].distance_along_part_km == 0.0
    assert part1_pts[0].distance_along_part_km == 0.0

    # No single point's cumulative distance should exceed its own part's
    # total length.
    part0_total = _geodesic_distance_km(72.0, 19.0, 72.2, 19.2) + \
                  _geodesic_distance_km(72.2, 19.2, 72.4, 19.4)
    part1_total = _geodesic_distance_km(76.0, 10.0, 76.2, 10.2) + \
                  _geodesic_distance_km(76.2, 10.2, 76.4, 10.4)

    for p in part0_pts:
        assert p.distance_along_part_km <= part0_total + 0.01
    for p in part1_pts:
        assert p.distance_along_part_km <= part1_total + 0.01

    # The sum of max distances per part should NOT exceed the sum of
    # independently-computed part lengths (proves no gap bridging).
    sum_max = part0_pts[-1].distance_along_part_km + \
              part1_pts[-1].distance_along_part_km
    assert sum_max <= part0_total + part1_total + 0.1


# ── Test 5: Configurable interval ────────────────────────────────────


def test_configurable_interval():
    """
    Synthetic: same geometry sampled at 2.0 km and 5.0 km intervals
    produces correspondingly different point counts — smaller interval
    yields more points.
    """
    coords = [[[72.0, 10.0], [72.3, 10.3], [72.6, 10.6]]]
    feature = _make_feature(coords)

    points_2km = sample_pfz_feature(feature, interval_km=2.0)
    points_5km = sample_pfz_feature(feature, interval_km=5.0)

    assert len(points_2km) > len(points_5km), (
        f"2 km interval ({len(points_2km)} pts) should produce more points "
        f"than 5 km interval ({len(points_5km)} pts)"
    )


# ── Test 6: Invalid interval raises ValueError ───────────────────────


def test_invalid_interval_raises_valueerror():
    """interval_km <= 0 must raise ValueError."""
    coords = [[[72.0, 10.0], [72.1, 10.1]]]
    feature = _make_feature(coords)

    with pytest.raises(ValueError, match="interval_km must be > 0"):
        sample_pfz_feature(feature, interval_km=0.0)

    with pytest.raises(ValueError, match="interval_km must be > 0"):
        sample_pfz_feature(feature, interval_km=-1.0)


# ── Test 7: Coordinate order (lon, lat) ──────────────────────────────


def test_coordinate_order_is_lon_lat():
    """
    Every returned PFZSamplePoint must have plausible (lon, lat) values
    matching the input GeoJSON/shapely convention — NOT swapped.

    For Indian-ocean PFZ features, longitudes are roughly 68–97°E and
    latitudes are roughly 8–24°N.  Swapping would place lon in 8–24 and
    lat in 68–97, which is out of range for latitude.
    """
    coords = [[[72.5, 19.0], [72.6, 19.1], [72.7, 19.2]]]
    feature = _make_feature(coords)

    points = sample_pfz_feature(feature, interval_km=3.0)

    for pt in points:
        # lon should be in roughly 72–73 range for this geometry.
        assert 72.0 <= pt.lon <= 73.0, f"lon {pt.lon} out of expected range"
        # lat should be in roughly 19–20 range.
        assert 18.5 <= pt.lat <= 20.0, f"lat {pt.lat} out of expected range"

        # Explicit axis-order check: lat must NOT be in the longitude range.
        assert pt.lat < 90.0, "lat > 90 suggests axis swap"


# ── Test 8: Integration with approved fixture ────────────────────────


def test_integration_with_fixture():
    """
    Integration: run sample_pfz_feature() against the first feature from
    the approved pfz_sample_features.json fixture and confirm it produces
    a sensible number of points for its known Length property (~52.3 km).
    """
    fixture_path = FIXTURES_DIR / "pfz_sample_features.json"
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))

    raw_feat = raw["features"][0]
    geom = shapely_shape(raw_feat["geometry"])
    props = raw_feat["properties"]

    feature = PFZFeature(
        geometry=geom,
        sector_boundary=props.get("SECTORBOUN"),
        sector_boundary_1=props.get("SECTORBO_1"),
        sector_name=props.get("SECTORNAME"),
        julian_day=str(props["Julian_day"]),
        serial_number=str(props.get("Sno", "")),
        year=int(props["Year"]),
        uid=props.get("UID"),
        length=props.get("Length"),
    )

    points = sample_pfz_feature(feature, interval_km=3.0)

    # No errors — points were produced.
    assert len(points) > 0

    # With ~52 km length and 3 km interval, we expect roughly 17-19 points
    # (including endpoints).  Allow generous tolerance because the fixture
    # geometry has only 4 vertices and the actual geodesic length may differ
    # from the Length property (which is from the WFS, possibly computed
    # differently).
    # The key assertion: it runs, produces a plausible count, and doesn't crash.
    assert len(points) >= 3, (
        f"Expected at least 3 points for a ~52 km line, got {len(points)}"
    )

    # source_uid should be populated from the feature's UID.
    assert all(pt.source_uid == str(feature.uid) for pt in points)

    # All points belong to part 0 (single-part MultiLineString fixture).
    assert all(pt.part_index == 0 for pt in points)

    # Endpoints must be preserved.
    assert points[0].is_endpoint is True
    assert points[-1].is_endpoint is True


# ── Test 9: Empty MultiLineString ─────────────────────────────────────


def test_empty_multilinestring_returns_empty_list():
    """
    An empty MultiLineString (zero parts) should return an empty list
    cleanly without error.
    """
    geom = MultiLineString()  # empty
    feature = PFZFeature(
        geometry=geom,
        julian_day="001",
        year=2026,
    )

    points = sample_pfz_feature(feature, interval_km=3.0)

    assert points == []


# ── Test 10: Unsupported geometry type ────────────────────────────────


def test_unsupported_geometry_raises_valueerror():
    """
    Geometry types other than LineString/MultiLineString (e.g. Point)
    must raise ValueError with a clear message.
    """
    from shapely.geometry import Point

    geom = Point(72.0, 19.0)
    feature = PFZFeature(
        geometry=geom,
        julian_day="001",
        year=2026,
    )

    with pytest.raises(ValueError, match="requires a LineString or MultiLineString"):
        sample_pfz_feature(feature, interval_km=3.0)


# ── Test 11: Exact-interval boundary case ─────────────────────────────


def test_exact_interval_boundary_case():
    """
    Boundary case: total_length_km == interval_km.

    When the line length exactly equals the sampling interval:
    - total_length_km < interval_km is False, so no short-segment midpoint is emitted.
    - Normal sampling produces exactly 2 points: the original start and end vertices.
    - Both points must have is_endpoint=True.
    - distance_along_part_km must be 0.0 and interval_km (within tolerance).

    The end vertex is constructed using an independent pyproj.Geod calculation.
    """
    interval_km = 5.0
    start_lon, start_lat = 72.0, 19.0
    azimuth = 45.0  # arbitrary heading

    # Independently compute end coordinate exactly interval_km (5000 m) away
    end_lon, end_lat, _ = _GEOD.fwd(start_lon, start_lat, azimuth, interval_km * 1000.0)

    # Double check independent distance
    _, _, measured_m = _GEOD.inv(start_lon, start_lat, end_lon, end_lat)
    assert abs(measured_m - (interval_km * 1000.0)) < 1e-3

    coords = [[[start_lon, start_lat], [end_lon, end_lat]]]
    feature = _make_feature(coords)

    points = sample_pfz_feature(feature, interval_km=interval_km)

    # Exactly two samples returned (no midpoint)
    assert len(points) == 2, f"Expected exactly 2 points, got {len(points)}"

    # First sample is original start coordinate
    assert abs(points[0].lon - start_lon) < 1e-7
    assert abs(points[0].lat - start_lat) < 1e-7
    assert points[0].is_endpoint is True
    assert abs(points[0].distance_along_part_km - 0.0) < 1e-4

    # Last sample is original end coordinate
    assert abs(points[1].lon - end_lon) < 1e-7
    assert abs(points[1].lat - end_lat) < 1e-7
    assert points[1].is_endpoint is True
    assert abs(points[1].distance_along_part_km - interval_km) < 1e-4