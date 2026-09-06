# Geospatial / Geofencing Agent
**Owner:** Vedant

## Responsibility
Point-in-polygon checks against EEZ, IMBL, and Marine Protected Area
boundaries. This agent is self-contained and works entirely offline
once shapefiles are loaded — good first PostGIS task.

## MVP Tasks
- [ ] Load EEZ / IMBL shapefiles into PostGIS as `geometry(Polygon, 4326)`
- [ ] Load Marine Protected Area shapefiles similarly
- [ ] Implement `ST_Contains` check: is a coordinate inside a restricted polygon?
- [ ] Implement `ST_DWithin` check: how close is a coordinate to a boundary (for "warning" status)?
- [ ] Return status: `clear` / `warning` (within N km) / `restricted` (inside)
- [ ] Write 5-10 manual test cases with known coordinates (e.g. a point clearly inside Indian EEZ, one near the Sri Lanka IMBL)

## Further Stage (Production)
- [ ] Route-based checking: sample points every 500m along a path and flag the first breach (needed once Route Agent is built)
- [ ] Return distance-to-nearest-boundary so Visualization Agent can draw a "safe corridor"
- [ ] Once stable, take on the **Route/Navigation Agent** as a second task (shares the same spatial data and PostGIS skillset)
- [ ] Offline-mode support: confirm this agent's logic can run fully on-device with no LLM and no internet (pure math — should already be true, just needs verification)
- [ ] Add more MPA/coral reef/ecologically sensitive zone shapefiles as they're identified

## Interface Contract
Consumes: `(lat, lon)` or a list of route waypoints
Produces: `AgentEnvelope` with `data = {status: "clear"|"warning"|"restricted", nearest_boundary_name, distance_km}`
