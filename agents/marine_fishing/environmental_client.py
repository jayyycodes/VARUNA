"""
NOAA CoastWatch ERDDAP Client — Environmental data fetch and join for PFZ points.

Fetches Sea Surface Temperature (SST) from NOAA ACSPO L3S and Chlorophyll-a
(CHL) from NOAA VIIRS DINEOF gap-filled products, joining observations onto
geodesically-sampled PFZ points (PFZSamplePoint).

Owner: Jaish
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import date, datetime, time as dt_time, timezone

import httpx
from dotenv import load_dotenv

from .models import (
    CHLObservation,
    ObservationOutcome,
    PFZSamplePoint,
    SampledEnvironmentalPoint,
    SSTObservation,
)

load_dotenv()
logger = logging.getLogger("varuna.environmental")

# ── Dataset Identifiers ────────────────────────────────────────────────
SST_DATASET_ID = "noaacwLEOACSPOSSTL3SnrtCDaily"
CHL_DATASET_ID = "noaacwNPPN20VIIRSDINEOFDaily"

# ── Fill Values (verified from NOAA ERDDAP .das NetCDF metadata) ────────
SST_FILL_VALUE = -327.68
SST_GRADIENT_FILL_VALUE = -32.768
CHL_FILL_VALUE = -999.0

# ── Confidence Ceiling ─────────────────────────────────────────────────
# Documented constant placeholder: noaacwNPPN20VIIRSDINEOFDaily is an L4
# DINEOF gap-filled product with no per-pixel observed-vs-interpolated flag.
# A fixed ceiling is assigned to all successful/stale CHL observations pending
# domain-expert justification.
CHL_CONFIDENCE_CEILING = 0.7

# Default retry configuration
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 1.0


class EnvironmentalClient:
    """
    Async client for NOAA CoastWatch ERDDAP SST and Chlorophyll-a datasets.

    Usage::

        client = EnvironmentalClient()
        joined = await client.join_environmental_data(sample_points, target_date)
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_base: float = _DEFAULT_BACKOFF_BASE,
        cache_ttl_seconds: float = 3600.0,
        max_concurrency: int = 5,
    ) -> None:
        self._base_url = (
            base_url
            or os.getenv(
                "NOAA_ERDDAP_BASE_URL",
                "https://coastwatch.noaa.gov/erddap",
            )
        ).rstrip("/")
        self._timeout = timeout or float(
            os.getenv("NOAA_ERDDAP_TIMEOUT_SECONDS", "10.0")
        )
        self._external_client = http_client
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._cache_ttl_seconds = cache_ttl_seconds
        self._max_concurrency = max_concurrency
        self._default_semaphore = asyncio.Semaphore(max_concurrency)

        # In-memory time coverage cache: dataset_id -> (start_dt, end_dt, start_str, end_str, timestamp)
        # Strictly keyed by dataset_id so SST and CHL rolling lags remain distinct.
        self._time_coverage_cache: dict[
            str, tuple[datetime, datetime, str, str, float]
        ] = {}

        # In-memory time coordinate cache for historical date lookups:
        # (dataset_id, date) -> actual_timestamp_str
        self._time_coordinate_cache: dict[tuple[str, date], str] = {}

    # ── Public API ─────────────────────────────────────────────────────

    async def get_sst(
        self,
        lat: float,
        lon: float,
        target_date: date | datetime,
        *,
        semaphore: asyncio.Semaphore | None = None,
    ) -> SSTObservation:
        """
        Fetch SST observation for a single coordinate point and target date.
        """
        req_dt, req_date = self._normalize_requested_time(target_date)
        sem = semaphore or self._default_semaphore

        if self._external_client is not None:
            return await self._get_sst_impl(
                self._external_client, lat, lon, req_dt, req_date, sem
            )

        async with httpx.AsyncClient() as client:
            return await self._get_sst_impl(
                client, lat, lon, req_dt, req_date, sem
            )

    async def get_chl(
        self,
        lat: float,
        lon: float,
        target_date: date | datetime,
        *,
        semaphore: asyncio.Semaphore | None = None,
    ) -> CHLObservation:
        """
        Fetch Chlorophyll-a observation for a single coordinate point and target date.
        """
        req_dt, req_date = self._normalize_requested_time(target_date)
        sem = semaphore or self._default_semaphore

        if self._external_client is not None:
            return await self._get_chl_impl(
                self._external_client, lat, lon, req_dt, req_date, sem
            )

        async with httpx.AsyncClient() as client:
            return await self._get_chl_impl(
                client, lat, lon, req_dt, req_date, sem
            )

    async def join_environmental_data(
        self,
        sample_points: list[PFZSamplePoint],
        target_date: date | datetime,
        *,
        max_concurrency: int | None = None,
    ) -> list[SampledEnvironmentalPoint]:
        """
        Fetch SST and CHL for each PFZSamplePoint concurrently.

        Concurrency is bounded at the individual network operation level by
        a shared asyncio.Semaphore. Respects constructor-level max_concurrency
        when no explicit per-call override is supplied. Preserves all points in
        original sequence; errors are captured on individual observations.
        """
        effective_concurrency = (
            max_concurrency
            if max_concurrency is not None
            else self._max_concurrency
        )
        semaphore = asyncio.Semaphore(effective_concurrency)

        async def _fetch_point(
            sp: PFZSamplePoint,
            client: httpx.AsyncClient,
        ) -> SampledEnvironmentalPoint:
            sst_obs, chl_obs = await asyncio.gather(
                self._get_sst_impl(
                    client,
                    sp.lat,
                    sp.lon,
                    *self._normalize_requested_time(target_date),
                    semaphore=semaphore,
                ),
                self._get_chl_impl(
                    client,
                    sp.lat,
                    sp.lon,
                    *self._normalize_requested_time(target_date),
                    semaphore=semaphore,
                ),
            )
            return SampledEnvironmentalPoint(
                sample_point=sp,
                sst=sst_obs,
                chl=chl_obs,
            )

        if self._external_client is not None:
            tasks = [
                _fetch_point(sp, self._external_client) for sp in sample_points
            ]
            return list(await asyncio.gather(*tasks))

        async with httpx.AsyncClient() as client:
            tasks = [_fetch_point(sp, client) for sp in sample_points]
            return list(await asyncio.gather(*tasks))

    @staticmethod
    def build_cache_key(
        dataset_id: str,
        target_date: date | datetime,
        lat: float,
        lon: float,
    ) -> str:
        """
        Build a deterministic cache key for an ERDDAP environmental query.

        .. todo::
           Wire this into Redis caching in a future PR.
        """
        date_str = (
            target_date.date().isoformat()
            if isinstance(target_date, datetime)
            else target_date.isoformat()
        )
        return f"env:v1:{dataset_id}:{date_str}:{lat:.4f},{lon:.4f}"

    # ── Internal Implementation ────────────────────────────────────────

    async def _get_sst_impl(
        self,
        client: httpx.AsyncClient,
        lat: float,
        lon: float,
        req_dt: datetime,
        req_date: date,
        semaphore: asyncio.Semaphore,
    ) -> SSTObservation:
        # 1. Resolve actual available timestamp from ERDDAP
        query_time_str, is_stale, err = await self._resolve_query_timestamp(
            client, SST_DATASET_ID, req_date, semaphore
        )
        if err is not None or query_time_str is None:
            return SSTObservation(
                outcome=ObservationOutcome.UNEXPECTED_ERROR,
                requested_time=req_dt,
                error_message=err or "Failed to resolve SST time coordinate",
            )

        # 2. Build ERDDAP query URL with resolved actual timestamp
        url = self._build_sst_query_url(
            self._base_url, query_time_str, lat, lon
        )

        # 3. Execute with transient retry bounded by semaphore
        resp_data, outcome, err_msg = await self._execute_erddap_query(
            client, url, semaphore
        )
        if outcome != ObservationOutcome.SUCCESS or not resp_data:
            return SSTObservation(
                outcome=outcome,
                requested_time=req_dt,
                error_message=err_msg,
            )

        # 4. Parse table response
        return self._parse_sst_response(resp_data, req_dt, is_stale)

    async def _get_chl_impl(
        self,
        client: httpx.AsyncClient,
        lat: float,
        lon: float,
        req_dt: datetime,
        req_date: date,
        semaphore: asyncio.Semaphore,
    ) -> CHLObservation:
        # 1. Resolve actual available timestamp from ERDDAP
        query_time_str, is_stale, err = await self._resolve_query_timestamp(
            client, CHL_DATASET_ID, req_date, semaphore
        )
        if err is not None or query_time_str is None:
            return CHLObservation(
                outcome=ObservationOutcome.UNEXPECTED_ERROR,
                requested_time=req_dt,
                error_message=err or "Failed to resolve CHL time coordinate",
            )

        # 2. Build ERDDAP query URL with resolved actual timestamp
        url = self._build_chl_query_url(
            self._base_url, query_time_str, lat, lon
        )

        # 3. Execute with transient retry bounded by semaphore
        resp_data, outcome, err_msg = await self._execute_erddap_query(
            client, url, semaphore
        )
        if outcome != ObservationOutcome.SUCCESS or not resp_data:
            return CHLObservation(
                outcome=outcome,
                requested_time=req_dt,
                error_message=err_msg,
            )

        # 4. Parse table response
        return self._parse_chl_response(resp_data, req_dt, is_stale)

    # ── Query URL Builders ─────────────────────────────────────────────

    @staticmethod
    def _build_sst_query_url(
        base_url: str,
        time_str: str,
        lat: float,
        lon: float,
    ) -> str:
        """
        Build griddap query URL for SST (3D: time, latitude, longitude).

        COORDINATE ORDER CONVENTION:
        ERDDAP griddap dimension constraints are strictly [time][latitude][longitude].
        Latitude MUST precede longitude. This is opposite to PFZSamplePoint's
        storage convention (lon, lat) and distinct from OGC WFS CQL BBOX.
        No hardcoded noon timestamp is used; time_str is resolved from ERDDAP.
        """
        vars_to_request = [
            "sea_surface_temperature",
            "quality_level",
            "sst_gradient_magnitude",
            "sst_front_position",
        ]
        # Query slice bracket: [(time)][(lat)][(lon)]
        slice_bracket = f"[({time_str})][({lat})][({lon})]"
        query_expr = ",".join(f"{v}{slice_bracket}" for v in vars_to_request)
        return f"{base_url}/griddap/{SST_DATASET_ID}.json?{query_expr}"

    @staticmethod
    def _build_chl_query_url(
        base_url: str,
        time_str: str,
        lat: float,
        lon: float,
    ) -> str:
        """
        Build griddap query URL for Chlorophyll-a (4D: time, altitude, latitude, longitude).

        COORDINATE ORDER & ALTITUDE CONVENTION:
        Altitude dimension is mandatory for noaacwNPPN20VIIRSDINEOFDaily and must
        be [(0.0)]. Omitting it shifts subsequent dimensions and produces HTTP 404.
        Latitude MUST precede longitude: [time][altitude][latitude][longitude].
        No hardcoded noon timestamp is used; time_str is resolved from ERDDAP.
        """
        slice_bracket = f"[({time_str})][(0.0)][({lat})][({lon})]"
        return f"{base_url}/griddap/{CHL_DATASET_ID}.json?chlor_a{slice_bracket}"

    @staticmethod
    def _build_time_query_url(
        base_url: str,
        dataset_id: str,
        target_date: date,
    ) -> str:
        """
        Build griddap query URL to discover the actual available time coordinate
        for target_date from ERDDAP.
        """
        date_iso = target_date.isoformat()
        return (
            f"{base_url}/griddap/{dataset_id}.json?time"
            f"[({date_iso}T00:00:00Z):1:({date_iso}T23:59:59Z)]"
        )

    # ── Timestamp Resolution & Metadata Discovery ──────────────────────

    @staticmethod
    def _normalize_requested_time(
        target: date | datetime,
    ) -> tuple[datetime, date]:
        if isinstance(target, datetime):
            dt = target if target.tzinfo else target.replace(tzinfo=timezone.utc)
            return dt, dt.date()
        return datetime.combine(target, dt_time(12, 0), tzinfo=timezone.utc), target

    async def _resolve_query_timestamp(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        req_date: date,
        semaphore: asyncio.Semaphore,
    ) -> tuple[str | None, bool, str | None]:
        """
        Resolve the actual available timestamp from ERDDAP for req_date:
        - If req_date < coverage start: returns (None, False, error_message).
        - If req_date > coverage end: returns (cov_end_str, True, None) [STALE_FALLBACK].
          Uses actual latest available timestamp from ERDDAP metadata (never hardcoded noon).
        - If req_date == coverage end date: returns (cov_end_str, False, None).
        - If within range: queries ERDDAP for the actual available time coordinate for that day.
        """
        try:
            cov_start_dt, cov_end_dt, cov_start_str, cov_end_str = (
                await self._get_time_coverage(client, dataset_id, semaphore)
            )
        except Exception as exc:
            return None, False, f"Failed to fetch metadata for {dataset_id}: {exc}"

        start_date = cov_start_dt.date()
        end_date = cov_end_dt.date()

        if req_date < start_date:
            return (
                None,
                False,
                f"Requested date {req_date} precedes dataset coverage start {start_date}",
            )

        if req_date > end_date:
            # Stale fallback: use actual latest available timestamp from metadata
            return cov_end_str, True, None

        if req_date == end_date:
            return cov_end_str, False, None

        # Within coverage range: check cache or query ERDDAP for actual time coordinate
        cache_key = (dataset_id, req_date)
        if cache_key in self._time_coordinate_cache:
            return self._time_coordinate_cache[cache_key], False, None

        time_url = self._build_time_query_url(
            self._base_url, dataset_id, req_date
        )
        resp_data, outcome, err_msg = await self._execute_erddap_query(
            client, time_url, semaphore
        )

        if outcome != ObservationOutcome.SUCCESS or not resp_data:
            return (
                None,
                False,
                f"No available time coordinate found for {req_date} in {dataset_id}: {err_msg}",
            )

        try:
            rows = resp_data.get("table", {}).get("rows", [])
            if not rows or not rows[0]:
                return (
                    None,
                    False,
                    f"Empty time rows returned for {req_date} in {dataset_id}",
                )
            actual_time_str = str(rows[0][0])
            self._time_coordinate_cache[cache_key] = actual_time_str
            return actual_time_str, False, None
        except Exception as exc:
            return (
                None,
                False,
                f"Failed to parse time coordinate response for {req_date}: {exc}",
            )

    async def _get_time_coverage(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        semaphore: asyncio.Semaphore,
    ) -> tuple[datetime, datetime, str, str]:
        now = time.monotonic()
        cached = self._time_coverage_cache.get(dataset_id)
        if cached and (now - cached[4] < self._cache_ttl_seconds):
            return cached[0], cached[1], cached[2], cached[3]

        url = f"{self._base_url}/info/{dataset_id}/index.json"
        total_attempts = self._max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                async with semaphore:
                    response = await client.get(url, timeout=self._timeout)
                if response.status_code != 200:
                    raise ValueError(
                        f"HTTP {response.status_code} fetching metadata for {dataset_id}"
                    )
                data = response.json()
                start_dt, end_dt, start_str, end_str = (
                    self._parse_coverage_metadata(data)
                )
                self._time_coverage_cache[dataset_id] = (
                    start_dt,
                    end_dt,
                    start_str,
                    end_str,
                    now,
                )
                return start_dt, end_dt, start_str, end_str

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < total_attempts:
                    backoff = self._backoff_base * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)

            except Exception as exc:
                logger.error(
                    "[environmental] Non-transient error fetching metadata for %s: %s",
                    dataset_id,
                    exc,
                )
                raise

        raise RuntimeError(
            f"Failed to fetch metadata for {dataset_id} after {total_attempts} attempts: {last_error}"
        )

    @staticmethod
    def _parse_coverage_metadata(
        data: dict,
    ) -> tuple[datetime, datetime, str, str]:
        table = data.get("table", {})
        col_names = table.get("columnNames", [])
        rows = table.get("rows", [])

        attr_name_idx = (
            col_names.index("Attribute Name")
            if "Attribute Name" in col_names
            else -1
        )
        val_idx = col_names.index("Value") if "Value" in col_names else -1

        start_str: str | None = None
        end_str: str | None = None

        for row in rows:
            if attr_name_idx != -1 and val_idx != -1:
                attr = row[attr_name_idx]
                val = row[val_idx]
                if attr == "time_coverage_start":
                    start_str = str(val)
                elif attr == "time_coverage_end":
                    end_str = str(val)

        if not start_str or not end_str:
            raise ValueError(
                "Could not find time_coverage_start/end in ERDDAP metadata"
            )

        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        return start_dt, end_dt, start_str, end_str

    # ── Execution with Retry ───────────────────────────────────────────

    async def _execute_erddap_query(
        self,
        client: httpx.AsyncClient,
        url: str,
        semaphore: asyncio.Semaphore,
    ) -> tuple[dict | None, ObservationOutcome, str | None]:
        total_attempts = self._max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                async with semaphore:
                    response = await client.get(url, timeout=self._timeout)

                # Non-transient responses are never retried
                if response.status_code != 200:
                    err_text = response.text[:200]
                    return (
                        None,
                        ObservationOutcome.UNEXPECTED_ERROR,
                        f"HTTP {response.status_code}: {err_text}",
                    )

                try:
                    data = response.json()
                    return data, ObservationOutcome.SUCCESS, None
                except Exception as exc:
                    return (
                        None,
                        ObservationOutcome.UNEXPECTED_ERROR,
                        f"Malformed JSON: {exc}",
                    )

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < total_attempts:
                    backoff = self._backoff_base * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)

            except Exception as exc:
                return (
                    None,
                    ObservationOutcome.UNEXPECTED_ERROR,
                    f"Unexpected error: {exc}",
                )

        return (
            None,
            ObservationOutcome.TRANSIENT_ERROR,
            f"Request failed after {total_attempts} attempts: {last_error}",
        )

    # ── Response Parsing ───────────────────────────────────────────────

    @staticmethod
    def _parse_sst_response(
        data: dict,
        req_dt: datetime,
        is_stale: bool,
    ) -> SSTObservation:
        try:
            table = data.get("table", {})
            col_names = table.get("columnNames", [])
            rows = table.get("rows", [])
            if not rows:
                return SSTObservation(
                    outcome=ObservationOutcome.UNEXPECTED_ERROR,
                    requested_time=req_dt,
                    error_message="Empty rowset returned by ERDDAP",
                )

            col_map = {name: idx for idx, name in enumerate(col_names)}
            row = rows[0]

            # Parse observation timestamp strictly from ERDDAP row
            time_raw = row[col_map["time"]]
            obs_dt = (
                datetime.fromisoformat(str(time_raw).replace("Z", "+00:00"))
                if time_raw
                else None
            )

            grid_lat = (
                float(row[col_map["latitude"]])
                if "latitude" in col_map and row[col_map["latitude"]] is not None
                else None
            )
            grid_lon = (
                float(row[col_map["longitude"]])
                if "longitude" in col_map and row[col_map["longitude"]] is not None
                else None
            )

            raw_sst = (
                row[col_map["sea_surface_temperature"]]
                if "sea_surface_temperature" in col_map
                else None
            )

            # Check fill value: null or -327.68
            is_fill = (
                raw_sst is None
                or abs(float(raw_sst) - SST_FILL_VALUE) < 1e-3
            )

            if is_fill:
                return SSTObservation(
                    outcome=ObservationOutcome.FILL_VALUE,
                    value_celsius=None,
                    requested_time=req_dt,
                    observation_time=obs_dt,
                    grid_lat=grid_lat,
                    grid_lon=grid_lon,
                )

            sst_val = float(raw_sst)

            # Parse quality and auxiliary fields
            qual_idx = col_map.get("quality_level", -1)
            qual_raw = (
                row[qual_idx]
                if qual_idx != -1 and qual_idx < len(row)
                else None
            )
            qual = (
                int(qual_raw)
                if qual_raw is not None and qual_raw != -128
                else None
            )

            grad_idx = col_map.get("sst_gradient_magnitude", -1)
            grad_raw = (
                row[grad_idx]
                if grad_idx != -1 and grad_idx < len(row)
                else None
            )
            grad = (
                float(grad_raw)
                if grad_raw is not None
                and abs(float(grad_raw) - SST_GRADIENT_FILL_VALUE) > 1e-3
                else None
            )

            front_idx = col_map.get("sst_front_position", -1)
            front_raw = (
                row[front_idx]
                if front_idx != -1 and front_idx < len(row)
                else None
            )
            front = (
                bool(front_raw)
                if front_raw is not None and front_raw != -128
                else None
            )

            outcome = (
                ObservationOutcome.STALE_FALLBACK
                if is_stale
                else ObservationOutcome.SUCCESS
            )

            return SSTObservation(
                outcome=outcome,
                value_celsius=sst_val,
                quality_level=qual,
                gradient_magnitude_k_per_km=grad,
                front_position=front,
                requested_time=req_dt,
                observation_time=obs_dt,
                grid_lat=grid_lat,
                grid_lon=grid_lon,
            )

        except Exception as exc:
            return SSTObservation(
                outcome=ObservationOutcome.UNEXPECTED_ERROR,
                requested_time=req_dt,
                error_message=f"Failed to parse SST table: {exc}",
            )

    @staticmethod
    def _parse_chl_response(
        data: dict,
        req_dt: datetime,
        is_stale: bool,
    ) -> CHLObservation:
        try:
            table = data.get("table", {})
            col_names = table.get("columnNames", [])
            rows = table.get("rows", [])
            if not rows:
                return CHLObservation(
                    outcome=ObservationOutcome.UNEXPECTED_ERROR,
                    requested_time=req_dt,
                    error_message="Empty rowset returned by ERDDAP",
                )

            col_map = {name: idx for idx, name in enumerate(col_names)}
            row = rows[0]

            # Parse observation timestamp strictly from ERDDAP row
            time_raw = row[col_map["time"]]
            obs_dt = (
                datetime.fromisoformat(str(time_raw).replace("Z", "+00:00"))
                if time_raw
                else None
            )

            grid_lat = (
                float(row[col_map["latitude"]])
                if "latitude" in col_map and row[col_map["latitude"]] is not None
                else None
            )
            grid_lon = (
                float(row[col_map["longitude"]])
                if "longitude" in col_map and row[col_map["longitude"]] is not None
                else None
            )

            raw_chl = (
                row[col_map["chlor_a"]] if "chlor_a" in col_map else None
            )

            # Check fill value: null or -999.0
            is_fill = (
                raw_chl is None
                or abs(float(raw_chl) - CHL_FILL_VALUE) < 1e-3
            )

            if is_fill:
                return CHLObservation(
                    outcome=ObservationOutcome.FILL_VALUE,
                    value_mg_m3=None,
                    confidence_ceiling=None,
                    requested_time=req_dt,
                    observation_time=obs_dt,
                    grid_lat=grid_lat,
                    grid_lon=grid_lon,
                )

            chl_val = float(raw_chl)
            outcome = (
                ObservationOutcome.STALE_FALLBACK
                if is_stale
                else ObservationOutcome.SUCCESS
            )

            return CHLObservation(
                outcome=outcome,
                value_mg_m3=chl_val,
                confidence_ceiling=CHL_CONFIDENCE_CEILING,
                requested_time=req_dt,
                observation_time=obs_dt,
                grid_lat=grid_lat,
                grid_lon=grid_lon,
            )

        except Exception as exc:
            return CHLObservation(
                outcome=ObservationOutcome.UNEXPECTED_ERROR,
                requested_time=req_dt,
                error_message=f"Failed to parse CHL table: {exc}",
            )
