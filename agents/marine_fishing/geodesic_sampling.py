"""
Geodesic resampling of PFZ MultiLineString features.

Converts each PFZ line feature (already fetched and parsed by
:class:`~agents.marine_fishing.pfz_client.PFZClient`) into a series of
:class:`~agents.marine_fishing.models.PFZSamplePoint` at a configurable
geodesic interval, using pyproj.Geod (WGS84) for real-world distance
calculations.

Why pyproj, not shapely's default distance?
    shapely computes distance in planar/Cartesian coordinate space by default —
    calling ``.length`` or ``.interpolate()`` on a LineString built from raw
    (lon, lat) coordinates returns a value in *degrees*, not kilometres, and
    ignores that a degree of longitude represents a different real-world
    distance depending on latitude.  This module uses ``pyproj.Geod`` for
    rigorous geodesic distance and point interpolation on the WGS84 ellipsoid.

Owner: Jaish
"""

from __future__ import annotations

import logging

from pyproj import Geod
from shapely.geometry import MultiLineString

from .models import PFZFeature, PFZSamplePoint

logger = logging.getLogger("varuna.pfz.geodesic")

# WGS84 geodesic calculator — shared across all calls in this module.
_GEOD = Geod(ellps="WGS84")


def sample_pfz_feature(
    feature: PFZFeature,
    interval_km: float = 3.0,
) -> list[PFZSamplePoint]:
    """
    Geodesically resample a PFZ feature's MultiLineString geometry into
    a series of points at approximately ``interval_km`` intervals, using
    pyproj.Geod (WGS84) for real-world distance — not shapely's planar
    default.  Always preserves each part's original first/last vertex.
    Handles multi-part geometries independently (never bridges the gap
    between parts).  For any part shorter than ``interval_km``, emits
    exactly one midpoint.

    Parameters
    ----------
    feature : PFZFeature
        A parsed PFZ line feature with a shapely geometry (typically
        MultiLineString).
    interval_km : float
        Target spacing between sample points, in kilometres.  Must be > 0.

    Returns
    -------
    list[PFZSamplePoint]
        Sampled points across all parts, ordered by part_index then by
        distance_along_part_km.

    Raises
    ------
    ValueError
        If ``interval_km`` is <= 0.
    """
    if interval_km <= 0:
        raise ValueError(
            f"interval_km must be > 0, got {interval_km}"
        )

    geometry = feature.geometry

    # ── Geometry type validation ──────────────────────────────────────
    if geometry.geom_type == "LineString":
        # Normalise single LineString into MultiLineString for uniform handling.
        geometry = MultiLineString([geometry])
    elif geometry.geom_type == "MultiLineString":
        # Empty MultiLineString (0 parts) → return [] cleanly.
        if geometry.is_empty:
            return []
    else:
        raise ValueError(
            f"sample_pfz_feature requires a LineString or MultiLineString "
            f"geometry, got {geometry.geom_type}"
        )

    source_uid = str(feature.uid) if feature.uid is not None else None

    all_points: list[PFZSamplePoint] = []

    for part_index, part in enumerate(geometry.geoms):
        coords = list(part.coords)  # list of (lon, lat) tuples
        if len(coords) < 2:
            logger.warning(
                "[geodesic] Skipping degenerate part %d with %d vertex(es)",
                part_index,
                len(coords),
            )
            continue

        # ── Build cumulative geodesic distance array ──────────────────
        cum_dist = [0.0]  # in km
        for i in range(1, len(coords)):
            lon1, lat1 = coords[i - 1]
            lon2, lat2 = coords[i]
            _, _, dist_m = _GEOD.inv(lon1, lat1, lon2, lat2)
            cum_dist.append(cum_dist[-1] + abs(dist_m) / 1000.0)

        total_length_km = cum_dist[-1]

        if total_length_km == 0.0:
            # All vertices are identical — degenerate, emit nothing meaningful.
            logger.warning(
                "[geodesic] Part %d has zero geodesic length, skipping",
                part_index,
            )
            continue

        # ── SHORT-SEGMENT RULE ────────────────────────────────────────
        # Boundary case:
        #   total_length_km <  interval_km → exactly one midpoint
        #   total_length_km == interval_km → falls through to normal
        #     sampling, which produces exactly two points (the original
        #     start and end vertices), not a midpoint.
        # The strict-less-than comparison is intentional.
        if total_length_km < interval_km:
            midpoint = _interpolate_at(
                coords, cum_dist, total_length_km / 2.0
            )
            all_points.append(
                PFZSamplePoint(
                    lon=midpoint[0],
                    lat=midpoint[1],
                    part_index=part_index,
                    distance_along_part_km=total_length_km / 2.0,
                    is_endpoint=False,
                    source_uid=source_uid,
                )
            )
            continue

        # ── NORMAL SAMPLING ───────────────────────────────────────────
        # Generate target distances: 0, interval_km, 2*interval_km, ...
        # Always include 0 and total_length_km.
        targets: list[float] = []
        d = 0.0
        while d < total_length_km:
            targets.append(d)
            d += interval_km
        # Always add the final endpoint if not already there (due to
        # floating-point, the last step may have overshot or landed exactly).
        if not targets or abs(targets[-1] - total_length_km) > 1e-9:
            targets.append(total_length_km)

        for target_d in targets:
            # Use original vertices for exact endpoints to avoid
            # floating-point near-duplicates.
            if abs(target_d) < 1e-9:
                lon, lat = coords[0]
                is_ep = True
            elif abs(target_d - total_length_km) < 1e-9:
                lon, lat = coords[-1]
                is_ep = True
            else:
                lon, lat = _interpolate_at(coords, cum_dist, target_d)
                is_ep = False

            all_points.append(
                PFZSamplePoint(
                    lon=lon,
                    lat=lat,
                    part_index=part_index,
                    distance_along_part_km=target_d,
                    is_endpoint=is_ep,
                    source_uid=source_uid,
                )
            )

    return all_points


# ── Internal helpers ──────────────────────────────────────────────────────


def _interpolate_at(
    coords: list[tuple[float, ...]],
    cum_dist: list[float],
    target_km: float,
) -> tuple[float, float]:
    """
    Interpolate a (lon, lat) point at ``target_km`` along the piecewise
    geodesic path defined by ``coords`` and its cumulative distance array.

    Walks the cumulative distance array to find the segment containing
    ``target_km``, then uses ``geod.fwd()`` from that segment's start
    vertex along the segment's azimuth for the remaining distance.

    Zero-length segments (duplicate consecutive vertices) are skipped
    without crashing.
    """
    for i in range(1, len(cum_dist)):
        if cum_dist[i] >= target_km - 1e-12:
            seg_start_km = cum_dist[i - 1]
            seg_len_km = cum_dist[i] - seg_start_km

            if seg_len_km < 1e-12:
                # Zero-length segment — return the start vertex.
                return (coords[i - 1][0], coords[i - 1][1])

            remaining_km = target_km - seg_start_km
            lon1, lat1 = coords[i - 1]
            lon2, lat2 = coords[i]

            fwd_az, _, _ = _GEOD.inv(lon1, lat1, lon2, lat2)
            lon_out, lat_out, _ = _GEOD.fwd(
                lon1, lat1, fwd_az, remaining_km * 1000.0
            )
            return (lon_out, lat_out)

    # Fallback (should not happen if target_km <= total_length): return last vertex.
    return (coords[-1][0], coords[-1][1])
