"""
INCOIS PFZ WFS Client — async client for Potential Fishing Zone advisories.

Fetches PFZ line features from the INCOIS GeoServer WFS endpoint
(PFZ_Automation:pfzlines).  This is a pure data-access client that returns
typed Pydantic models — it does NOT produce AgentEnvelopes, interpret
advisory status (e.g. fishing-ban / adverse-sea), or implement geodesic
sampling (PR2).

Owner: Jaish
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import xml.etree.ElementTree as ET
from datetime import date

import httpx
from dotenv import load_dotenv
from shapely.geometry import shape as shapely_shape

from .models import (
    PFZBoundingBox,
    PFZFeature,
    PFZOutcome,
    PFZQueryResult,
)

load_dotenv()
logger = logging.getLogger("varuna.pfz")

# ── WFS request constants ──────────────────────────────────────────────
_WFS_SERVICE = "WFS"
_WFS_VERSION = "1.1.0"
_WFS_REQUEST = "GetFeature"
_WFS_TYPE_NAME = "PFZ_Automation:pfzlines"
_WFS_OUTPUT_FORMAT = "application/json"

# OGC namespace for XML exception parsing
_OWS_NS = "http://www.opengis.net/ows"

# Default retry configuration
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 1.0  # seconds; doubled on each subsequent retry


class PFZClient:
    """
    Async client for the INCOIS Potential Fishing Zone (PFZ) WFS endpoint.

    Usage::

        client = PFZClient()
        result = await client.get_pfz_features(date(2026, 9, 8))

        if result.outcome == PFZOutcome.SUCCESS:
            for feat in result.features:
                print(feat.sector_name, feat.geometry)
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_base: float = _DEFAULT_BACKOFF_BASE,
    ) -> None:
        self._base_url = base_url or os.getenv(
            "INCOIS_PFZ_WFS_URL",
            "https://incois.gov.in/geoserver/PFZ_Automation/ows",
        )
        self._timeout = timeout or float(
            os.getenv("INCOIS_PFZ_TIMEOUT_SECONDS", "10.0")
        )
        self._external_client = http_client
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    # ── Public API ─────────────────────────────────────────────────────

    async def get_pfz_features(
        self,
        target_date: date,
        sector: str | None = None,
        bbox: PFZBoundingBox | None = None,
    ) -> PFZQueryResult:
        """
        Fetch PFZ line features for a given date, with optional spatial/sector
        filters.

        Returns a :class:`PFZQueryResult` whose ``outcome`` discriminates
        between success, empty, and various error conditions.  The public
        interface never raises exceptions for expected WFS outcomes — callers
        should pattern-match on ``outcome`` instead of try/except.
        """
        year, julian_day = self._date_to_year_julian(target_date)
        cql_filter = self._build_cql_filter(year, julian_day, sector, bbox)
        params = self._build_wfs_params(cql_filter)

        logger.info(
            "[pfz] Fetching PFZ features: date=%s year=%d jday=%s sector=%s bbox=%s",
            target_date.isoformat(),
            year,
            julian_day,
            sector,
            bbox,
        )

        if self._external_client is not None:
            return await self._execute_with_retry(self._external_client, params)

        async with httpx.AsyncClient() as client:
            return await self._execute_with_retry(client, params)

    @staticmethod
    def build_cache_key(
        year: int,
        julian_day: str,
        sector: str | None,
        bbox: PFZBoundingBox | None,
    ) -> str:
        """
        Build a deterministic cache key for a PFZ WFS query.

        .. todo::
           Wire this into the Redis caching layer in a future PR.
           The key shape is decided here so future caching work does not
           have to rediscover the components that make a query unique.

        Returns a colon-separated string, e.g.
        ``pfz:v1:2026:251`` or
        ``pfz:v1:2026:251:sector=Maharashtra:bbox=18.5,72.0,20.0,73.0``.
        """
        parts = [f"pfz:v1:{year}:{julian_day}"]
        if sector is not None:
            parts.append(f"sector={sector}")
        if bbox is not None:
            parts.append(
                f"bbox={bbox.min_lat},{bbox.min_lon},"
                f"{bbox.max_lat},{bbox.max_lon}"
            )
        return ":".join(parts)

    # ── Date conversion ────────────────────────────────────────────────

    @staticmethod
    def _date_to_year_julian(target_date: date) -> tuple[int, str]:
        """
        Convert a Python date to ``(year, zero-padded-3-digit-julian-day)``.

        Example: ``date(2026, 9, 8)`` → ``(2026, "251")``
        """
        year = target_date.year

        # strftime("%j") produces "001"–"366", matching the "251" format
        # observed in INCOIS WFS testing.
        #
        # TODO: verify INCOIS's actual padding convention for single-digit
        # Julian days once a real early-January date is testable.  strftime("%j")
        # zero-pads to 3 digits, which is our best assumption from prior
        # research — but it is an untested assumption for days < 100 and
        # must be visibly flagged as such, not silently assumed.
        julian_day = target_date.strftime("%j")

        return year, julian_day

    # ── CQL filter construction ────────────────────────────────────────

    @staticmethod
    def _build_cql_filter(
        year: int,
        julian_day: str,
        sector: str | None,
        bbox: PFZBoundingBox | None,
    ) -> str:
        """Build the ``CQL_FILTER`` query parameter for the WFS request."""
        parts: list[str] = [
            f"Year={year}",
            f"Julian_day='{julian_day}'",
        ]
        if sector is not None:
            parts.append(f"SECTORNAME='{sector}'")
        if bbox is not None:
            parts.append(PFZClient._build_bbox_filter(bbox))
        return " AND ".join(parts)

    @staticmethod
    def _build_bbox_filter(bbox: PFZBoundingBox) -> str:
        """
        Build the CQL BBOX predicate for the INCOIS PFZ WFS endpoint.

        EXPERIMENTALLY VERIFIED COMPLETE SYNTAX
        ========================================
        The complete CQL BBOX syntax for this GeoServer endpoint is::

            BBOX(the_geom, min_lat, min_lon, max_lat, max_lon)

        Two distinct requirements were experimentally verified against the live
        INCOIS endpoint:

        1. Explicit geometry-property syntax:
           GeoServer's CQL parser requires the geometry attribute name as the
           first argument (here, ``the_geom``). The bare 4-argument form
           ``BBOX(min_lat, min_lon, max_lat, max_lon)`` is rejected by GeoServer
           with an OGC ExceptionReport ("Could not parse CQL filter list. Encountered ')'...").

        2. Endpoint-specific axis order:
           This endpoint requires **latitude (Y) before longitude (X)**::

               min_lat, min_lon, max_lat, max_lon

           This is the REVERSE of the standard OGC CQL convention (minx, miny, maxx, maxy).
           Live testing confirmed that lat-first returns matching features, whereas
           standard lon-first returns 0 features due to inverted coordinates.

        The returned GeoJSON coordinates use standard ``[longitude, latitude]``;
        only the WFS CQL BBOX predicate uses this endpoint-specific convention.
        """
        return (
            f"BBOX(the_geom,"
            f"{bbox.min_lat},{bbox.min_lon},"
            f"{bbox.max_lat},{bbox.max_lon})"
        )

    @staticmethod
    def _build_wfs_params(cql_filter: str) -> dict[str, str]:
        """Build the full query-parameter dict for a WFS GetFeature request."""
        return {
            "service": _WFS_SERVICE,
            "version": _WFS_VERSION,
            "request": _WFS_REQUEST,
            "typeName": _WFS_TYPE_NAME,
            "outputFormat": _WFS_OUTPUT_FORMAT,
            "CQL_FILTER": cql_filter,
        }

    # ── HTTP execution with retry ──────────────────────────────────────

    async def _execute_with_retry(
        self,
        client: httpx.AsyncClient,
        params: dict[str, str],
    ) -> PFZQueryResult:
        """
        Execute the WFS request with bounded retry for transient errors only.

        Allows 1 initial request plus up to ``max_retries`` retries (up to
        ``1 + max_retries`` total attempts).

        Retries on:  ``httpx.TimeoutException``, ``httpx.NetworkError``
        Does NOT retry on:  successful HTTP responses (even with OGC errors),
        or unexpected exceptions.
        """
        total_attempts = self._max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                response = await client.get(
                    self._base_url,
                    params=params,
                    timeout=self._timeout,
                )
                result = self._classify_response(response)
                result.attempts = attempt
                return result

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                logger.warning(
                    "[pfz] Attempt %d/%d failed (transient): %s",
                    attempt,
                    total_attempts,
                    exc,
                )
                if attempt < total_attempts:
                    backoff = self._backoff_base * (2 ** (attempt - 1))
                    logger.info("[pfz] Retrying in %.1fs…", backoff)
                    await asyncio.sleep(backoff)

            except Exception as exc:
                logger.error(
                    "[pfz] Non-transient error on attempt %d: %s", attempt, exc
                )
                return PFZQueryResult(
                    outcome=PFZOutcome.UNEXPECTED_ERROR,
                    error_message=f"Unexpected error during HTTP request: {exc}",
                    attempts=attempt,
                )

        return PFZQueryResult(
            outcome=PFZOutcome.TRANSIENT_ERROR,
            error_message=(
                f"Initial request and all {self._max_retries} retries failed "
                f"({total_attempts} total attempts). Last error: {last_error}"
            ),
            attempts=total_attempts,
        )

    # ── Response classification ────────────────────────────────────────

    @staticmethod
    def _classify_response(response: httpx.Response) -> PFZQueryResult:
        """
        Classify an HTTP response into one of the five PFZ outcomes.

        Classification is based on Content-Type and body content, **not** on
        HTTP status code alone — this endpoint has been verified to return
        HTTP 200 with an OGC XML exception body for invalid requests.
        """
        content_type = response.headers.get("content-type", "").lower()

        # 1. Check for OGC XML exception (can arrive with ANY HTTP status,
        #    including 200 — confirmed via live DevTools inspection)
        if "xml" in content_type:
            parsed = PFZClient._try_parse_ogc_exception(response.text)
            if parsed is not None:
                return parsed
            return PFZQueryResult(
                outcome=PFZOutcome.UNEXPECTED_ERROR,
                error_message=(
                    f"XML response (HTTP {response.status_code}) is not a "
                    f"parseable OGC ExceptionReport"
                ),
            )

        # 2. Non-200 with non-XML content → UNEXPECTED_ERROR
        if response.status_code != 200:
            return PFZQueryResult(
                outcome=PFZOutcome.UNEXPECTED_ERROR,
                error_message=(
                    f"HTTP {response.status_code}, "
                    f"Content-Type: {content_type}"
                ),
            )

        # 3. HTTP 200 with JSON → parse as GeoJSON FeatureCollection
        if "json" in content_type:
            return PFZClient._parse_geojson_response(response.text)

        # 4. HTTP 200 with unexpected Content-Type
        return PFZQueryResult(
            outcome=PFZOutcome.UNEXPECTED_ERROR,
            error_message=f"HTTP 200 but unexpected Content-Type: {content_type}",
        )

    # ── OGC exception parsing ──────────────────────────────────────────

    @staticmethod
    def _try_parse_ogc_exception(body: str) -> PFZQueryResult | None:
        """
        Attempt to parse an OGC ``ExceptionReport`` from an XML body.

        Returns a ``WFS_ERROR`` result if an ``<ows:Exception>`` is found,
        or ``None`` if the XML is not a recognisable OGC exception.
        """
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return None

        # Look for <ows:Exception> with the OGC namespace
        exception_el = root.find(f"{{{_OWS_NS}}}Exception")
        if exception_el is None:
            return None

        exception_code = exception_el.get("exceptionCode", "Unknown")
        text_el = exception_el.find(f"{{{_OWS_NS}}}ExceptionText")
        exception_text = (
            text_el.text.strip()
            if text_el is not None and text_el.text
            else None
        )

        logger.warning(
            "[pfz] OGC WFS exception: code=%s text=%s",
            exception_code,
            exception_text,
        )

        return PFZQueryResult(
            outcome=PFZOutcome.WFS_ERROR,
            error_message=f"OGC WFS exception: {exception_code}",
            exception_code=exception_code,
            exception_text=exception_text,
        )

    # ── GeoJSON parsing ────────────────────────────────────────────────

    @staticmethod
    def _parse_geojson_response(body: str) -> PFZQueryResult:
        """Parse a GeoJSON FeatureCollection body into typed PFZ features."""
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as exc:
            return PFZQueryResult(
                outcome=PFZOutcome.UNEXPECTED_ERROR,
                error_message=f"Malformed JSON body: {exc}",
            )

        if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
            got = (
                data.get("type")
                if isinstance(data, dict)
                else type(data).__name__
            )
            return PFZQueryResult(
                outcome=PFZOutcome.UNEXPECTED_ERROR,
                error_message=f"Expected GeoJSON FeatureCollection, got type={got}",
            )

        raw_features = data.get("features", [])
        if not raw_features:
            return PFZQueryResult(outcome=PFZOutcome.EMPTY)

        features: list[PFZFeature] = []
        parse_errors: list[str] = []

        for i, raw in enumerate(raw_features):
            try:
                features.append(PFZClient._parse_single_feature(raw))
            except Exception as exc:
                msg = f"Feature[{i}]: {exc}"
                parse_errors.append(msg)
                logger.warning("[pfz] Skipping unparseable feature: %s", msg)

        if not features:
            return PFZQueryResult(
                outcome=PFZOutcome.UNEXPECTED_ERROR,
                error_message=(
                    f"All {len(raw_features)} features failed to parse. "
                    f"First error: {parse_errors[0] if parse_errors else 'unknown'}"
                ),
            )

        if parse_errors:
            logger.warning(
                "[pfz] Parsed %d/%d features (%d skipped due to errors)",
                len(features),
                len(raw_features),
                len(parse_errors),
            )

        return PFZQueryResult(outcome=PFZOutcome.SUCCESS, features=features)

    @staticmethod
    def _parse_single_feature(raw: dict) -> PFZFeature:
        """Parse a single GeoJSON Feature dict into a :class:`PFZFeature`."""
        geom_dict = raw.get("geometry")
        if geom_dict is None:
            raise ValueError("Feature has no 'geometry' field")

        geometry = shapely_shape(geom_dict)

        props = raw.get("properties", {})

        sno = props.get("Sno")
        serial_number = str(sno) if sno is not None else None

        return PFZFeature(
            geometry=geometry,
            sector_boundary=props.get("SECTORBOUN"),
            sector_boundary_1=props.get("SECTORBO_1"),
            sector_name=props.get("SECTORNAME"),
            julian_day=str(props.get("Julian_day", "")),
            serial_number=serial_number,
            year=int(props.get("Year", 0)),
            uid=props.get("UID"),
            length=props.get("Length"),
        )
