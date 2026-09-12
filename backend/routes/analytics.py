"""
Fishery Analytics & Historical Trends API.

Provides coastal fishery productivity anomalies, marine heatwave metrics,
upwelling indices, and bathymetric depth validation.
Directly powers the frontend HistoricalTrendsView and SIH National Query #7.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Query

from agents.marine_fishing.bathymetry import BathymetryEngine
from agents.marine_fishing.historical_trends import (
    HistoricalTrendReport,
    HistoricalTrendsEngine,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/historical-trends", response_model=HistoricalTrendReport)
def get_historical_trends(
    lat: float = Query(16.99, description="Target latitude (e.g. 16.99 for Ratnagiri)"),
    lon: float = Query(73.28, description="Target longitude (e.g. 73.28 for Ratnagiri)"),
    sector: Optional[str] = Query(None, description="Optional coastal sector name or keyword (e.g. 'Konkan', 'Veraval')"),
) -> HistoricalTrendReport:
    """
    Get 12-month historical SST and chlorophyll anomalies, upwelling suppression factor,
    and statutory MFRA reference for target coastal sector.
    """
    return HistoricalTrendsEngine.get_trend_report(lat=lat, lon=lon, sector_hint=sector)


@router.get("/sectors")
def list_coastal_sectors() -> list[dict[str, Any]]:
    """List all supported coastal monitoring sectors across Indian EEZ."""
    return HistoricalTrendsEngine.list_available_sectors()


@router.get("/bathymetry")
def check_bathymetry(
    lat: float = Query(..., description="Vessel latitude"),
    lon: float = Query(..., description="Vessel longitude"),
    distance_from_shore_km: float = Query(..., ge=0.0, description="Distance from shore in km"),
    vessel_type: str = Query("artisanal", description="Vessel classification (artisanal, motorized_obm, mechanized_trawler, deep_sea_longliner)"),
) -> dict[str, Any]:
    """Check estimated depth and gear compatibility for vessel type."""
    depth_m = BathymetryEngine.estimate_depth_meters(lat, lon, distance_from_shore_km)
    category = BathymetryEngine.categorize_depth(depth_m)
    annotated = BathymetryEngine.filter_and_annotate_zones(
        [{"lat": lat, "lon": lon, "distance_km": distance_from_shore_km}],
        vessel_type=vessel_type,
    )[0]

    return {
        "lat": lat,
        "lon": lon,
        "distance_from_shore_km": distance_from_shore_km,
        "estimated_depth_meters": depth_m,
        "depth_category": category,
        "vessel_type": vessel_type,
        "gear_compatible": annotated["gear_compatible"],
        "gear_warning": annotated.get("gear_warning"),
    }
