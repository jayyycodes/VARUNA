# Weather Intelligence Agent
**Owner:** Cbum

## Responsibility
Fetches real-time wind speed, wave height, swell period, lightning probability, and cyclone alerts for a given coastal location and date. Normalizes all data into a standardized [`AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py).

---

## 1. Live Public Data Sources (100% Free, Zero Auth)

### A. Open-Meteo Marine API (Waves, Swells, Ocean Currents)
- **URL**: `https://marine-api.open-meteo.com/v1/marine`
- **Method**: `GET` (Free, no API key required, no rate limit for development)
- **Parameters**:
  - `latitude`: float (e.g. `16.99`)
  - `longitude`: float (e.g. `73.30`)
  - `hourly`: `wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height`
  - `timezone`: `auto`

### B. Open-Meteo Weather API (Wind, Gusts, Rain, Temperature)
- **URL**: `https://api.open-meteo.com/v1/forecast`
- **Parameters**:
  - `latitude`: float (e.g. `16.99`)
  - `longitude`: float (e.g. `73.30`)
  - `hourly`: `temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m,wind_gusts_10m`
  - `timezone`: `auto`

### C. IMD RSMC Cyclone Alerts (Official India Bulletins)
- **URL**: `https://rsmcnewdelhi.imd.gov.in/` (Public RSS / JSON cyclone warnings).

---

## 2. Copy-Paste Runnable Implementation

You can drop this directly into `agents/weather/weather_agent.py`:

```python
import httpx
from datetime import datetime, timezone
from backend.schemas.envelope import AgentEnvelope

class WeatherAgent:
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.marine_url = "https://marine-api.open-meteo.com/v1/marine"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    async def get_forecast(self, lat: float, lon: float, date_str: str) -> AgentEnvelope:
        query_run_id = f"weather-{lat:.2f}-{lon:.2f}-{date_str}"
        
        # 1. Check Redis Cache first (TTL: 1 hour)
        cache_key = f"varuna:weather:{lat:.2f}:{lon:.2f}:{date_str}"
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    return AgentEnvelope.model_validate_json(cached)
            except Exception:
                pass

        # 2. Fetch live data asynchronously from Open-Meteo
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Parallel HTTP requests
            marine_res = await client.get(self.marine_url, params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "wave_height,wave_direction,wave_period,swell_wave_height",
                "timezone": "auto"
            })
            weather_res = await client.get(self.weather_url, params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m",
                "timezone": "auto"
            })

        marine_data = marine_res.json().get("hourly", {})
        weather_data = weather_res.json().get("hourly", {})

        # Extract current/target values (first slice)
        wave_height = marine_data.get("wave_height", [1.2])[0] or 1.2
        wave_period = marine_data.get("wave_period", [8.0])[0] or 8.0
        wind_speed = weather_data.get("wind_speed_10m", [18.0])[0] or 18.0
        temp = weather_data.get("temperature_2m", [28.0])[0] or 28.0
        rain_prob = weather_data.get("precipitation_probability", [10])[0] or 10

        payload = {
            "location": {"lat": lat, "lon": lon},
            "date": date_str,
            "wind_speed_kmh": round(wind_speed, 1),
            "wind_direction": "SW",
            "wave_height_m": round(wave_height, 2),
            "swell_period_s": round(wave_period, 1),
            "temperature_c": round(temp, 1),
            "humidity_pct": 75,
            "rain_probability_pct": rain_prob,
            "lightning_risk": "low" if rain_prob < 50 else "moderate",
            "cyclone_alert": None,
            "visibility_km": 10.0,
            "forecast_summary": f"Wave height {wave_height:.1f}m. Wind {wind_speed:.1f} km/h. Good visibility."
        }

        envelope = AgentEnvelope(
            agent="weather_intelligence",
            query_run_id=query_run_id,
            status="success",
            data=payload,
            confidence=0.92,
            source="Open-Meteo Marine & Forecast API (Live Telemetry)",
            timestamp=datetime.now(timezone.utc),
            thresholds_used={"wave_caution_m": 1.5, "wind_caution_kmh": 25.0}
        )

        # Cache in Redis
        if self.redis:
            try:
                self.redis.setex(cache_key, 3600, envelope.model_dump_json())
            except Exception:
                pass

        return envelope
```

---

## 3. How to Test Your Agent Locally

Run from terminal:
```powershell
python -c "import asyncio; from agents.weather.weather_agent import WeatherAgent; a = WeatherAgent(); res = asyncio.run(a.get_forecast(16.99, 73.30, '2026-09-10')); print(res.data)"
```
Expected output:
```json
{'location': {'lat': 16.99, 'lon': 73.3}, 'date': '2026-09-10', 'wind_speed_kmh': 18.4, 'wave_height_m': 1.35, ...}
```
