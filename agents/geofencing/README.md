# Geospatial / Geofencing Agent
**Owner:** Vedant  
**Status:** MVP Complete ✅ | Next Phase: Trajectory Intersections & Complete MPA Ingestion

## Responsibility
Performs sub-millisecond point-in-polygon containment and proximity buffer calculations against International Maritime Boundary Lines (IMBL), Exclusive Economic Zones (EEZ), and Marine Protected Areas (MPAs) using PostgreSQL + PostGIS.

> Operates **100% offline** without external internet dependencies or LLM overhead.

---

## 1. MVP Tasks (Completed ✅)
- [x] **PostGIS Spatial Engine**: Configured local containerized PostGIS instance on port `5433` with spatial indexes (`GIST`).
- [x] **Boundary Seeding & Schema**: Automated loading of Sri Lanka EEZ, Indian EEZ, Pakistan EEZ, and Malvan Marine Sanctuary via [`data/etl/setup_data.py`](file:///c:/Development/Varuna/data/etl/setup_data.py).
- [x] **Spatial Classification Logic**:
  - Point inside polygon $\to$ `restricted` (Immediate halt warning).
  - Distance $\le 2.0$ km $\to$ `warning` (Border proximity caution).
  - Distance $> 2.0$ km $\to$ `clear`.
- [x] **Standardized Envelope**: Wraps results into [`AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py).
- [x] **Automated Test Suite**: 8 automated test scenarios in `agents/geofencing/tests/test_geofencing.py` passing cleanly.

---

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 1.1, 3, 6, & 9), the next operational priorities are:

- [ ] **Full MarineRegions.org v12 Ingestion**:
  - Ingest high-precision shapefiles for all Indian subcontinent maritime boundaries (India, Sri Lanka, Pakistan, Maldives, Bangladesh, Myanmar EEZ and treaty lines).
- [ ] **Comprehensive WDPA Marine Protected Areas (MPAs)**:
  - Load all 31+ Indian MPAs, Marine National Parks, and Biosphere Reserves (Gulf of Mannar, Sundarbans, Gahirmatha, Mahatma Gandhi Marine NP) from Protected Planet WDPA.
- [ ] **Route Trajectory Corridor Intersection (`ST_Intersects`)**:
  - Add spatial validation for entire multi-waypoint LineString routes to ensure no planned passage cuts through restricted marine reserves or crosses the IMBL.
- [ ] **Monsoon Fishing Ban Territorial Polygons**:
  - Map state-specific territorial water corridors (0–5 NM artisanal zone vs 5–12 NM mechanized zone vs 12–200 NM EEZ) to automatically flag trawlers operating during state monsoon bans.
- [ ] **Onboard Offline Edge Mode (SpatiaLite / FlatGeobuf)**:
  - Package boundaries into lightweight SpatiaLite or FlatGeobuf binaries for zero-network execution directly on vessels' mobile devices.

---

## 3. Boundary Status Rules
| Spatial Condition | Status | Action / Notice |
|---|---|---|
| Inside Restricted Zone (`contains == True`) | **`restricted`** | **UNSAFE**: Immediate warning to halt vessel and return to Indian EEZ. |
| Distance to Boundary $\le 2.0$ km | **`warning`** | **CAUTION**: Alert vessel is within 2 km border proximity buffer. |
| Distance to Boundary $> 2.0$ km | **`clear`** | Cleared for lawful maritime navigation. |

---

## 4. Verification & Testing
Run the automated PostGIS test suite:
```powershell
pytest agents/geofencing/tests/test_geofencing.py -v
```
