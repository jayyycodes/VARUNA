# Weather Intelligence Agent
**Owner:** Cbum  
**Status:** MVP Complete ✅ | Next Phase: Live IMD / MOSDAC Feeds & Resilience

## Responsibility
Fetches real-time coastal and marine atmospheric conditions including wind speed, significant wave height, swell period, lightning probability, and cyclone alerts. Normalizes all telemetry into a standardized [`AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py).

---

## 1. MVP Tasks (Completed ✅)
- [x] **Open-Meteo Marine API Integration**: Live ingestion of `wave_height`, `wave_period`, `wave_direction`, and `swell_wave_height`.
- [x] **Open-Meteo Atmospheric Forecast API**: Live hourly telemetry for `wind_speed_10m`, `wind_gusts_10m`, `temperature_2m`, and `precipitation_probability`.
- [x] **Envelope Normalization**: Standardized all values into small-craft thresholds (km/h, meters, knots, degrees).
- [x] **Redis Telemetry Caching**: 1-hour TTL caching keyed by `varuna:weather:{lat}:{lon}:{date}`.
- [x] **Target Hour & Date Indexing**: Temporal matching for future departure queries (*"tomorrow morning"*, specific dates).

---

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 3, 6, & 9), the next operational priorities are:

- [ ] **Live IMD RSMC Cyclone Bulletin Ingestion**:
  - Implement an automated parser for IMD RSMC New Delhi RSS/bulletin feeds (`https://rsmcnewdelhi.imd.gov.in/`).
  - Extract active cyclone tracks, coordinates, storm cones, and warning levels (Pre-Genesis, Depression, Deep Depression, CS, VSCS).
- [ ] **ISRO MOSDAC / INSAT-3D Lightning Feed**:
  - Ingest real-time convective storm cloud-top brightness temperature and lightning flash density from MOSDAC to replace precipitation heuristics.
- [ ] **Multi-Tier Fallback Chain & Circuit Breaker**:
  - Build automated fallback sequence: Open-Meteo Live $\to$ Redis Cache $\to$ INCOIS OSF Station Climatology.
  - Track upstream uptime and latency; trip circuit breaker after 3 consecutive timeouts.
- [ ] **INCOIS Wave-Rider Buoy Cross-Referencing**:
  - Ground numerical models against real-time observation from INCOIS coastal wave-rider buoys (e.g. Ratnagiri, Kochi, Chennai, Vizag).
- [ ] **Proactive Weather Alert Broadcaster**:
  - Trigger webhook alerts when wind gusts exceed 22 kts (40 km/h) or wave heights exceed 2.5 m threshold.

---

## 3. Real-Time Public Data Endpoints
| Parameter | Source Body | Endpoint / Feed | Frequency |
|---|---|---|---|
| **Waves & Swell** | Open-Meteo Marine | `https://marine-api.open-meteo.com/v1/marine` | Hourly Live |
| **Wind, Temp, Rain** | Open-Meteo Forecast | `https://api.open-meteo.com/v1/forecast` | Hourly Live |
| **Cyclone Bulletins** | IMD RSMC New Delhi | `https://rsmcnewdelhi.imd.gov.in/` | Live Bulletins |
| **Lightning & Convection** | ISRO MOSDAC / INSAT-3D | Public satellite thermal IR grids | 30-min pass |

---

## 4. Verification & Testing
Run local unit test:
```powershell
python -c "import asyncio; from agents.weather.weather_agent import WeatherAgent; a = WeatherAgent(); res = asyncio.run(a.get_forecast(16.99, 73.30, '2026-09-11')); print(res.data)"
```
Or execute full test suite:
```powershell
pytest tests/test_weather.py -v
```
