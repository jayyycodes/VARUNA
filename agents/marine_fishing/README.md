# Marine & Fishing Intelligence Agent
**Owner:** Jaish

## Responsibility
Fetches SST, chlorophyll concentration, and PFZ advisories; ranks
fishing zones by productivity. This is the most data-science-heavy
agent — the productivity ranking logic is where real judgment matters.

## MVP Tasks
- [ ] Parse INCOIS PFZ WebGIS advisories (check whether a structured feed exists or if bulletins are PDF-only — if PDF-only, build a parser)
- [ ] Integrate MOSDAC SST layer (NetCDF/OPeNDAP — coordinate with Vedant/Data ETL on ingestion format)
- [ ] Integrate MOSDAC OCM-3 chlorophyll layer
- [ ] Build a basic zone-ranking function: combine SST + chlorophyll + distance into a productivity score
- [ ] Normalize into `AgentEnvelope` with ranked zone list + confidence per zone
- [ ] Write 5-10 manual test cases against known PFZ bulletin dates (compare your ranking against the actual published PFZ zones for validation)

## Further Stage (Production)
- [ ] Historical trend analysis: "why has productivity declined here" using NOAA/MOSDAC historical SST + chlorophyll archives
- [ ] Seasonal pattern modeling (monsoon vs. non-monsoon productivity shifts)
- [ ] Golden-set eval: validate ranked zones against real INCOIS PFZ bulletins for a held-out date range
- [ ] Scheduled ingestion job (cron) pulling all tracked coastal regions in one batch rather than per-request
- [ ] Dataset versioning — tag which MOSDAC/INCOIS bulletin date produced a given ranking, for traceability

## Interface Contract
Consumes: `(lat, lon, date)` or a region bounding box
Produces: `AgentEnvelope` with `data = {sst_celsius, chlorophyll_mg_m3, ranked_zones: [{lat, lon, distance_km, productivity_score}]}`
