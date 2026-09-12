# Weather Intelligence Agent
**Owner:** Cbum (Atharva Sarnaik)  
**Status:** Tier 1 & Tier 2 Complete ✅ | Production Ready 🚀

## Responsibility
Fetches real-time coastal and marine atmospheric conditions including wind speed, significant wave height, swell period, lightning probability, buoy telemetry, and cyclone alerts. Normalizes all telemetry into a standardized [`AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py).

---

## 1. MVP Tasks (Tier 1 — Completed ✅)
- [x] **Open-Meteo Marine API Integration**: Live ingestion of `wave_height`, `wave_period`, `wave_direction`, and `swell_wave_height`.
- [x] **Open-Meteo Atmospheric Forecast API**: Live hourly telemetry for `wind_speed_10m`, `wind_gusts_10m`, `temperature_2m`, and `precipitation_probability`.
- [x] **Envelope Normalization**: Standardized all values into small-craft thresholds (km/h, meters, knots, degrees).
- [x] **Redis Telemetry Caching**: 1-hour TTL caching keyed by `varuna:weather:{lat}:{lon}:{date}`.
- [x] **Target Hour & Date Indexing**: Temporal matching for future departure queries (*"tomorrow morning"*, specific dates).

---

## 2. Production & Resilience Tasks (Tier 2 — Completed ✅)
According to the root `README.md` (Sections 3, 6, & 9), all operational priorities are fully implemented:

- [x] **Live IMD RSMC Cyclone Bulletin Ingestion (`agents/weather/imd_bulletin.py`)**:
  - Implemented automated RSS/XML parser for IMD RSMC New Delhi bulletins using standard library `xml.etree.ElementTree` and defensive regex extraction.
  - Extracts active cyclone tracks, coordinates, storm cones, port warning signals (e.g. Signal #8), and intensity classifications (Depression up to Super Cyclonic Storm).
- [x] **ISRO MOSDAC / Convective Lightning Intelligence (`agents/weather/mosdac_client.py` & `MOSDAC_WMS_SETUP_GUIDE.md`)**:
  - Real-time convective squall and lightning strike risk evaluator utilizing CAPE, precipitation probability, and thermal instability proxies.
  - Provided comprehensive OGC WMS/WCS GeoServer raster setup guide for live satellite layer integration.
- [x] **Multi-Tier Fallback Chain & Circuit Breakers (`agents/weather/weather_agent.py`)**:
  - Built 4-tier fallback sequence: Open-Meteo Live $\to$ Stale Redis Cache (24h) $\to$ INCOIS OSF Regional Climatology Baseline $\to$ Static Safety Net.
  - Pre-registered circuit breakers (`imd_rsmc`, `incois_buoy`, `incois_osf`, `mosdac_lightning`) in `backend/gateway/circuit_breaker.py`.
- [x] **INCOIS Wave-Rider Buoy Cross-Referencing (`agents/weather/incois_buoy.py`)**:
  - Spatial station picker matching closest Indian wave-rider buoys (Ratnagiri, Kochi, Chennai, Vizag, Mumbai, Goa, Paradip).
  - Dynamically computes confidence scores ($0.75 - 0.96$) by comparing numerical NWP model outputs against physical buoy telemetry.
- [x] **Proactive Weather Alert Broadcaster (`agents/weather/alert_broadcaster.py` & `backend/routes/alerts.py`)**:
  - Threshold-triggered generation of authoritative alerts (`HIGH SWELL / KALLAKKADAL`, `GALE WIND ADVISORY`, `SEVERE LIGHTNING / CONVECTIVE SQUALL`, `CYCLONE WARNING`).
  - Added `POST /api/alerts/clear-expired` endpoint to purge expired alerts.

---

## 3. Real-Time Public Data Endpoints
| Parameter | Source Body | Endpoint / Feed | Frequency |
|---|---|---|---|
| **Waves & Swell** | Open-Meteo Marine | `https://marine-api.open-meteo.com/v1/marine` | Hourly Live |
| **Wind, Temp, Rain** | Open-Meteo Forecast | `https://api.open-meteo.com/v1/forecast` | Hourly Live |
| **Cyclone Bulletins** | IMD RSMC New Delhi | `https://rsmcnewdelhi.imd.gov.in/` | Live Bulletins |
| **Wave-Rider Buoys** | INCOIS ERDDAP | `https://incois.gov.in/erddap/tabledap/` | Live Telemetry |
| **Lightning & Convection** | ISRO MOSDAC / Convective Model | Convective Instability & WMS | 30-min pass |

---

## 4. Verification & Testing
Execute full test suite (20/20 passing):
```powershell
pytest tests/test_weather.py tests/test_imd_bulletin.py tests/test_incois_buoy.py tests/test_alert_broadcaster.py tests/test_weather_fallback.py -v
```
