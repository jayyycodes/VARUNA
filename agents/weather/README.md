# Weather Intelligence Agent
**Owner:** Cbum

## Responsibility
Fetches wind speed, wave height, lightning probability, and cyclone alerts
for a given location and time window. This is the simplest agent in the
system — a good first task to get comfortable with the codebase.

## MVP Tasks
- [ ] Integrate Open-Meteo API (no API key needed) for wind/rain/temperature
- [ ] Integrate IMD API for cyclone bulletins and lightning nowcasts (check current public access method)
- [ ] Integrate INCOIS Ocean State Forecast for wave height/direction/period
- [ ] Normalize all three sources into a single `AgentEnvelope` with consistent units (km/h, meters, etc.)
- [ ] Add Redis caching: key on `(lat rounded to 0.1°, lon rounded to 0.1°, date)`, TTL 1-3 hours
- [ ] Write 5-10 manual test cases against known coastal coordinates (Ratnagiri, Kochi, Visakhapatnam)

## Further Stage (Production)
- [ ] Circuit breaker + exponential backoff retry on all three external APIs
- [ ] Fallback chain: if live API fails, serve last cached value + explicit "data is N hours old" flag
- [ ] Track per-source uptime/error rate in Prometheus for the observability dashboard
- [ ] Add cyclone track history lookup (for "why" questions about past storms)
- [ ] Batch/scheduled ingestion (cron) instead of live-calling per request, once query volume grows

## Interface Contract
Consumes: `(lat, lon, date, time_window)`
Produces: `AgentEnvelope` with `data = {wind_speed_kmph, wave_height_m, wave_direction, lightning_alert, cyclone_alert, rain_probability}`
