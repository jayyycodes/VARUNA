# MOSDAC WMS / WCS Endpoint Setup & Integration Guide

**Author:** Cbum (Atharva Sarnaik) — VARUNA Weather Intelligence  
**Component:** `agents/weather/mosdac_client.py`  
**Target:** ISRO Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC)

---

## 1. Overview

ISRO’s MOSDAC (https://mosdac.gov.in) provides real-time and archived meteorological/oceanographic products derived from Indian earth observation satellites:
- **INSAT-3D / INSAT-3DR / INSAT-3DS**: Convective precipitation, Cloud Motion Vectors (CMV), Cloud Top Temperature (CTT), Convective Cloud Index (CCI), and Hydro-Estimator Precipitation.
- **ScatSat-1 / Oceansat-3**: Sea surface wind vectors and ocean color.
- **Lightning Flash Density**: Geostationary Lightning Imager (GLI) proxy / Ground Network gridded data.

Currently, VARUNA uses an atmospheric convective instability proxy (`rain_probability_pct`, `temperature_c`, `humidity_pct`, `wind_gusts_kmh`) inside `agents/weather/mosdac_client.py`. This guide details how to transition to direct **WMS (Web Map Service)** and **WCS (Web Coverage Service)** live raster querying once MOSDAC credentials are authenticated.

---

## 2. Obtaining MOSDAC API Credentials

1. **Register User Account:**
   - Visit [https://mosdac.gov.in/user/register](https://mosdac.gov.in/user/register).
   - Register under Academic / Research / Institutional category.
2. **Apply for Open OGC Web Services Token:**
   - Navigate to *User Profile -> API / Token Access*.
   - Generate an OAuth2 Bearer Token / HTTP Basic Auth key for OGC WMS/WCS endpoints.
3. **Set Environment Variables in VARUNA `.env`:**
   ```bash
   MOSDAC_USERNAME=your_username
   MOSDAC_PASSWORD=your_password
   MOSDAC_API_TOKEN=your_oauth_or_api_token
   MOSDAC_WMS_URL=https://mosdac.gov.in/geoserver/wms
   MOSDAC_WCS_URL=https://mosdac.gov.in/geoserver/wcs
   ```

---

## 3. OGC WMS (Web Map Service) Query Pattern

WMS allows querying point values via `GetFeatureInfo` on raster layers without downloading entire NetCDF / GeoTIFF files.

### 3.1 Key Layers for Maritime Squall & Lightning

| Layer Name | Satellite / Instrument | Description | Unit |
| :--- | :--- | :--- | :--- |
| `mosdac:insat3d_ctt` | INSAT-3D Imager | Cloud Top Temperature (CTT < -40°C indicates deep convection) | Kelvin |
| `mosdac:lightning_density` | Ground + Geo Proxy | Lightning Flash Count per 100 km² / hr | Flashes/hr |
| `mosdac:insat3d_he` | INSAT-3D Hydro-Estimator | Instantaneous Convective Rainfall Rate | mm/hr |
| `mosdac:convective_index` | INSAT-3DR Imager | Convective Cloud Depth Index | Dimensionless (0-100) |

### 3.2 WMS `GetFeatureInfo` HTTP Request Example

```python
import httpx

params = {
    "SERVICE": "WMS",
    "VERSION": "1.1.1",
    "REQUEST": "GetFeatureInfo",
    "LAYERS": "mosdac:lightning_density",
    "QUERY_LAYERS": "mosdac:lightning_density",
    "SRS": "EPSG:4326",
    "BBOX": f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}",
    "WIDTH": "101",
    "HEIGHT": "101",
    "X": "50",
    "Y": "50",
    "INFO_FORMAT": "application/json",
}

headers = {
    "Authorization": f"Bearer {os.getenv('MOSDAC_API_TOKEN')}",
    "User-Agent": "VARUNA-Maritime-AI/1.0",
}

async with httpx.AsyncClient() as client:
    res = await client.get("https://mosdac.gov.in/geoserver/wms", params=params, headers=headers)
    feature_data = res.json()
    # Extracts pixel value representing lightning flash rate at target (lat, lon)
```

---

## 4. OGC WCS (Web Coverage Service) for Bounding Box Rasters

If the Route Planning Agent needs a 2D convective hazard grid for entire voyage path:

```http
GET /geoserver/wcs?
  SERVICE=WCS&
  VERSION=2.0.1&
  REQUEST=GetCoverage&
  COVERAGEID=mosdac__insat3d_ctt_latest&
  SUBSET=Lat(14.0,20.0)&
  SUBSET=Long(70.0,76.0)&
  FORMAT=image/tiff
```

You can read the returned GeoTIFF in Python using `rasterio` or `tifffile`:

```python
import io
import rasterio

with rasterio.open(io.BytesIO(res.content)) as src:
    ctt_array = src.read(1)  # 2D temperature array
    min_temp = ctt_array.min()
    # Deep convective squall threshold: CTT <= 210K (-63°C)
```

---

## 5. Circuit Breaker & Caching Strategy

When enabling live MOSDAC WMS/WCS in `agents/weather/mosdac_client.py`:
1. **Circuit Breaker:** Already pre-registered in `backend/gateway/circuit_breaker.py`:
   ```python
   self.register("mosdac_lightning", failure_threshold=3, recovery_timeout=90.0)
   ```
2. **Redis Caching:** Cache bounding-box and point queries for **15 minutes (900s)**:
   - Cache key format: `varuna:mosdac:lightning:{lat:.2f}:{lon:.2f}`
3. **Graceful Degradation:** If MOSDAC WMS times out (> 4.0s), automatically fall back to the existing `estimate_lightning_risk()` precipitation heuristic.
