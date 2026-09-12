# Marine & Fishing Intelligence Agent
**Owner:** Jaish  
**Status:** MVP Complete ✅ | Next Phase: Live Satellite Ingestion & Historical Trends

## Responsibility
Fetches and models Sea Surface Temperature (SST), Chlorophyll-a concentrations, and Potential Fishing Zone (PFZ) advisories. Evaluates oceanographic productivity and ranks optimal fishing spots near the vessel's home port.

---

## 1. MVP Tasks (Completed ✅)
- [x] **Oceanographic Profiling**: Modeled SST and chlorophyll distribution for both West (Arabian Sea) and East (Bay of Bengal) coasts.
- [x] **Productivity Scoring Algorithm**: Implemented multi-factor ranking formula:
  $$\text{Score} = 0.45 \times \text{Chlorophyll} + 0.35 \times \text{SST Front} - 0.20 \times \min\left(\frac{\text{Distance}}{50\text{ km}}, 1.0\right)$$
- [x] **PFZ Zone Generation**: Dynamically constructs candidate fishing clusters with GPS coordinates, distance, target species (Sardine, Mackerel, Tuna, Pomfret), and SST/Chlorophyll attributes.
- [x] **Standardized Envelope**: Wraps results into [`AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py) with full audit telemetry.

---

## 2. Post-MVP & Production Tasks (Tier-2 Progress)
According to the root `README.md` (Sections 1.1, 3, 6, & 9), the operational priorities are:

- [x] **Historical Productivity & Trend Analysis (SIH Target Query #7)**:
  - Implemented `HistoricalTrendsEngine` (`historical_trends.py`) answering *"Why has fish productivity declined in this region?"*.
  - Correlates SST anomalies (marine heatwaves), seasonal upwelling shifts, and chlorophyll depletion over 5-year spans across Konkan, Saurashtra, Malabar, Coromandel, and Northern Circars sectors.
  - Exposed via `GET /api/analytics/historical-trends` and `MarineFishingAgent.analyze_historical_trends()`.
- [x] **Bathymetric Depth Filtering**:
  - Implemented `BathymetryEngine` (`bathymetry.py`) modeling GEBCO 15 arc-second bathymetry contours along Indian coasts.
  - Filters out pelagic zones that exceed small-craft artisanal net depth limits (<50m depth) and annotates map features.
  - Exposed via `GET /api/analytics/bathymetry`.
- [x] **Golden-Set CI Automation**:
  - Built automated regression pipeline running 35 historical ground-truth test cases (`eval/golden_set/run_evals.py` & `eval/golden_set/test_golden_set.py`).
- [x] **Automated INCOIS PFZ WebGIS Advisory Ingestion**:
  - Implemented automated ETL pipeline (`data/etl/ingest_incois_pfz.py`) for live INCOIS PFZ shapefile/GeoJSON advisories.
  - Multi-day advisories persisted into PostGIS `pfz_advisories` table with `GIST` spatial index and CLI `--dry-run` / `--force-seed` support.
- [x] **Live Satellite Raster Ingestion (NOAA ERDDAP / ISRO OCM-3)**:
  - Implemented `SatelliteRasterClient` (`satellite_raster.py`) connecting NOAA CoastWatch ERDDAP GHRSST and ISRO OCM-3 / VIIRS ocean color grids.
  - Added 2D finite-difference oceanographic front detection identifying convergent upwelling zones and thermal edges.

---

## 3. Real-Time Public Feeds
| Parameter | Source Body | Endpoint / Feed |
|---|---|---|
| **Sea Surface Temperature (SST)** | NOAA CoastWatch ERDDAP | `https://coastwatch.pfeg.noaa.gov/erddap/griddap/` (GHRSST Indian EEZ) |
| **Chlorophyll-a Concentration** | Copernicus / ISRO OCM-3 | Sentinel-3 OLCI ocean color products |
| **PFZ Advisories** | INCOIS WebGIS / SAMUDRA | `https://incois.gov.in/portal/datainfo/pfz.jsp` |

---

## 4. Verification & Testing
Run local verification:
```powershell
python -c "import asyncio; from agents.marine_fishing.marine_agent import MarineFishingAgent; a = MarineFishingAgent(); res = asyncio.run(a.get_ocean_state(16.99, 73.30, '2026-09-11')); print(res.data['pfz_zones'][0])"
```
