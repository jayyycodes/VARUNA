"""
Unit tests for agents/marine_fishing/satellite_raster.py
Tests NOAA ERDDAP URL builders, 2D raster parsing, front detection, and fallbacks.
"""

from datetime import date
import httpx
import pytest

from agents.marine_fishing.satellite_raster import (
    SatelliteRasterClient,
    RasterGrid,
    OceanographicFront,
    SatelliteAnalysisResult,
    SST_FILL_VALUE,
    CHL_FILL_VALUE,
)


@pytest.fixture
def sample_bbox():
    return (16.0, 72.5, 17.5, 73.5)


@pytest.fixture
def sample_date():
    return date(2026, 9, 12)


def test_build_sst_griddap_url(sample_bbox, sample_date):
    client = SatelliteRasterClient(base_url="https://coastwatch.pfeg.noaa.gov/erddap")
    url = client._build_sst_griddap_url(sample_bbox, sample_date, stride=2)

    assert "https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaacwLEOACSPOSSTL3SnrtCDaily.json?" in url
    assert "sea_surface_temperature[(2026-09-12T12:00:00Z)]" in url
    assert "[(16.000):2:(17.500)]" in url
    assert "[(72.500):2:(73.500)]" in url


def test_build_chl_griddap_url(sample_bbox, sample_date):
    client = SatelliteRasterClient(base_url="https://coastwatch.pfeg.noaa.gov/erddap")
    url = client._build_chl_griddap_url(sample_bbox, sample_date, stride=1)

    assert "https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaacwNPPN20VIIRSDINEOFDaily.json?" in url
    assert "chlor_a[(2026-09-12T12:00:00Z)][(0.0)]" in url
    assert "[(16.000):1:(17.500)]" in url
    assert "[(72.500):1:(73.500)]" in url


def test_parse_erddap_grid_response():
    client = SatelliteRasterClient()
    mock_data = {
        "table": {
            "columnNames": ["time", "latitude", "longitude", "sea_surface_temperature"],
            "rows": [
                ["2026-09-12T12:00:00Z", 16.0, 72.5, 28.5],
                ["2026-09-12T12:00:00Z", 16.0, 73.0, SST_FILL_VALUE],  # Fill value
                ["2026-09-12T12:00:00Z", 17.0, 72.5, 29.0],
                ["2026-09-12T12:00:00Z", 17.0, 73.0, 29.2],
            ],
        }
    }

    grid = client._parse_erddap_grid_response(
        mock_data,
        parameter="sea_surface_temperature",
        units="deg_C",
        dataset_id="test_sst",
        source="Test Source",
        fill_value=SST_FILL_VALUE,
    )

    assert grid is not None
    assert grid.latitudes == [16.0, 17.0]
    assert grid.longitudes == [72.5, 73.0]
    assert grid.matrix[0][0] == 28.5
    assert grid.matrix[0][1] is None  # fill value masked out
    assert grid.matrix[1][0] == 29.0
    assert grid.matrix[1][1] == 29.2
    assert grid.is_fallback is False
    assert grid.min_value == 28.5
    assert grid.max_value == 29.2


def test_generate_fallback_raster(sample_bbox, sample_date):
    client = SatelliteRasterClient()
    grid = client._generate_fallback_raster(
        sample_bbox,
        sample_date,
        parameter="sea_surface_temperature",
        units="deg_C",
        source="Fallback Test",
    )

    assert grid.is_fallback is True
    assert len(grid.latitudes) == 10
    assert len(grid.longitudes) == 10
    assert len(grid.matrix) == 10
    assert len(grid.matrix[0]) == 10
    assert 27.0 <= grid.mean_value <= 31.0


def test_detect_ocean_fronts():
    client = SatelliteRasterClient()
    # Create a 4x4 grid with a sharp thermal gradient across longitude
    lats = [16.0, 16.1, 16.2, 16.3]
    lons = [72.0, 72.1, 72.2, 72.3]

    sst_matrix = [
        [28.0, 28.1, 29.5, 29.6],  # Sharp jump between 72.1 and 72.2
        [28.0, 28.2, 29.6, 29.7],
        [28.1, 28.3, 29.7, 29.8],
        [28.1, 28.3, 29.8, 29.9],
    ]

    chl_matrix = [
        [2.0, 1.8, 0.4, 0.3],  # High chlorophyll in cooler waters
        [2.2, 1.9, 0.4, 0.2],
        [2.1, 1.8, 0.3, 0.2],
        [2.0, 1.7, 0.3, 0.2],
    ]

    sst_grid = RasterGrid(
        parameter="sea_surface_temperature",
        units="deg_C",
        dataset_id="test_sst",
        source="Test",
        timestamp="2026-09-12T12:00:00Z",
        latitudes=lats,
        longitudes=lons,
        matrix=sst_matrix,
        mean_value=28.8,
    )

    chl_grid = RasterGrid(
        parameter="chlorophyll_a",
        units="mg/m^3",
        dataset_id="test_chl",
        source="Test",
        timestamp="2026-09-12T12:00:00Z",
        latitudes=lats,
        longitudes=lons,
        matrix=chl_matrix,
        mean_value=1.1,
    )

    fronts = client.detect_ocean_fronts(sst_grid, chl_grid)
    assert len(fronts) > 0

    front_types = {f.front_type for f in fronts}
    assert "upwelling_convergence" in front_types or "thermal_front" in front_types
    for f in fronts:
        assert f.gradient_strength > 0
        assert len(f.target_species) > 0


@pytest.mark.asyncio
async def test_get_satellite_analysis_with_mock_transport(sample_bbox, sample_date):
    # Setup mock transport returning 200 for SST and 500 for CHL (triggers fallback for CHL)
    sst_response_json = {
        "table": {
            "columnNames": ["time", "latitude", "longitude", "sea_surface_temperature"],
            "rows": [
                ["2026-09-12T12:00:00Z", 16.0, 72.5, 28.8],
                ["2026-09-12T12:00:00Z", 16.0, 73.0, 29.5],
                ["2026-09-12T12:00:00Z", 17.0, 72.5, 28.9],
                ["2026-09-12T12:00:00Z", 17.0, 73.0, 29.7],
            ],
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "noaacwLEOACSPOSSTL3SnrtCDaily" in url_str:
            return httpx.Response(200, json=sst_response_json)
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = SatelliteRasterClient(http_client=http_client)
        result = await client.get_satellite_analysis(sample_bbox, sample_date)

        assert isinstance(result, SatelliteAnalysisResult)
        assert result.sst_grid.is_fallback is False
        assert result.chl_grid.is_fallback is True  # fallback triggered on 500
        assert result.target_date == "2026-09-12"
        assert "Satellite analysis" in result.summary
