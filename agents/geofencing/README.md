# Geospatial / Geofencing Agent
**Owner:** Vedant

## Responsibility
Performs high-performance point-in-polygon and proximity checks against International Maritime Boundary Lines (IMBL), Exclusive Economic Zones (EEZ), and Marine Protected Areas (MPAs) using PostgreSQL + PostGIS.

Works 100% offline without external internet or LLM calls.

---

## 1. Local PostGIS Setup & Automated Seeding

Your PostGIS instance runs via Docker on port **5433** (to prevent collision with native Windows PostgreSQL services).

### Instant Seed Command
Any teammate can seed the required spatial boundaries into PostGIS by running:
```powershell
python data/etl/setup_data.py
```
This automatically applies [`infra/002_geofencing_schema.sql`](file:///c:/Development/Varuna/infra/002_geofencing_schema.sql) and seeds reference boundaries (Sri Lanka EEZ, Kaziranga MPA, Malvan Sanctuary).

---

## 2. PostGIS Spatial Queries Used

In [`agents/geofencing/queries.py`](file:///c:/Development/Varuna/agents/geofencing/queries.py):

```sql
-- Nearest boundary distance calculation and containment check:
SELECT 
    name,
    ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000.0 AS distance_km,
    ST_Contains(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS contains
FROM restricted_zones
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
LIMIT 1;
```

---

## 3. Status Rules

| Calculated Spatial Condition | Output Status | Action / Warning |
|---|---|---|
| Point lies inside polygon (`contains == True`) | **`restricted`** | **UNSAFE**: Immediate warning to halt vessel and return to Indian EEZ. |
| Distance to polygon edge `<= 2.0 km` | **`warning`** | **CAUTION**: Alert that vessel is within 2 km border proximity buffer. |
| Distance to polygon edge `> 2.0 km` | **`clear`** | Safe to navigate. |

---

## 4. How to Run the Geofencing Test Suite

Run the 8 automated boundary tests from terminal:
```powershell
pytest -v agents/geofencing/tests/test_geofencing.py
```

All 8 test scenarios pass cleanly:
1. `test_deep_ocean_clear` (Deep ocean coordinate)
2. `test_inside_indian_eez_clear` (Mumbai coast)
3. `test_sri_lanka_eez_restricted` (7.5°N, 79.0°E inside Sri Lanka EEZ)
4. `test_sri_lanka_imbl_warning` (7.5°N, 78.705°E within 1.4km of IMBL)
5. `test_mpa_restricted` (Inside sanctuary)
6. `test_mpa_warning` (Edge proximity)
7. `test_exact_boundary` (Exact perimeter ring)
8. `test_route_crossing` (Multi-waypoint transition)
