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

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 1.1, 3, 6, & 9), the next operational priorities are:

- [ ] **Automated INCOIS PFZ WebGIS Advisory Ingestion**:
  - Build automated scraper/ETL for daily INCOIS PFZ shapefiles and GeoJSON advisories (`https://incois.gov.in/portal/datainfo/pfz.jsp`).
  - Store multi-day advisories in PostGIS with spatial indexing (`GIST`).
- [ ] **Live Satellite Raster Ingestion (NOAA ERDDAP / ISRO OCM-3)**:
  - Connect NOAA CoastWatch ERDDAP for GHRSST 1km/5km daily SST grids.
  - Ingest Copernicus Marine / Sentinel-3 OLCI and ISRO OCM-3 Chlorophyll-a raster products.
- [ ] **Historical Productivity & Trend Analysis (SIH Target Query #7)**:
  - Implement historical trend engine answering *"Why has fish productivity declined in this region?"*.
  - Correlate SST anomalies (marine heatwaves), seasonal upwelling shifts, and chlorophyll depletion over 5-year spans.
- [ ] **Golden-Set CI Automation**:
  - Build automated regression pipeline running 30–50 historical ground-truth test cases verified against ICAR-CMFRI landing data.
- [ ] **Bathymetric Depth Filtering**:
  - Overlay GEBCO 15 arc-second bathymetry contours to filter out pelagic zones that exceed small-craft artisanal net depth limits (<50m depth).

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
