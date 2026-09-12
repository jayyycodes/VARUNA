"""
Proactive Marine Alert Broadcaster — owner: Cbum (Atharva Sarnaik)

Monitors weather telemetry envelopes against coastal safety thresholds.
When dangerous maritime thresholds are exceeded (high swell, convective squall,
gale force winds, or tropical cyclones), generates authoritative Marine Alerts
and publishes them to the active alerts registry (`backend/routes/alerts.py`).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.schemas.envelope import AgentEnvelope

logger = logging.getLogger("alert_broadcaster")


def determine_coastal_region_and_ports(lat: float, lon: float) -> tuple[str, list[str]]:
    """Determine descriptive coastal region name and major ports from coordinates."""
    # Maharashtra / Konkan
    if 15.5 <= lat <= 20.2 and 72.0 <= lon <= 74.0:
        return "Maharashtra Konkan Coast", ["Ratnagiri", "Malvan", "Mumbai", "Jaigad"]
    # Goa
    if 14.8 <= lat < 15.5 and 73.0 <= lon <= 74.5:
        return "Goa Coast", ["Mormugao", "Panaji"]
    # Karnataka
    if 12.8 <= lat < 14.8 and 73.8 <= lon <= 75.2:
        return "Karnataka Coast", ["Mangalore", "Karwar", "Malpe"]
    # Kerala
    if 8.0 <= lat < 12.8 and 74.5 <= lon <= 77.5:
        return "Kerala Coast", ["Kochi", "Vizhinjam", "Kollam", "Alappuzha", "Beypore"]
    # Tamil Nadu / Coromandel
    if 8.0 <= lat <= 13.6 and 77.5 < lon <= 80.6:
        return "Tamil Nadu Coast / Palk Bay", ["Chennai", "Ennore", "Tuticorin", "Nagapattinam"]
    # Andhra Pradesh
    if 13.6 < lat <= 19.0 and 80.0 <= lon <= 85.0:
        return "Andhra Pradesh Coast", ["Visakhapatnam", "Kakinada", "Machilipatnam", "Krishnapatnam"]
    # Odisha / North Bay of Bengal
    if 19.0 < lat <= 22.0 and 84.5 <= lon <= 88.0:
        return "Odisha / North Bay of Bengal", ["Paradip", "Dhamra", "Gopalpur", "Puri"]
    # West Bengal
    if 21.0 <= lat <= 23.0 and 87.5 <= lon <= 89.5:
        return "West Bengal Coast / Sundarbans", ["Haldia", "Kolkata", "Digha"]
    # Gujarat / Gulf of Khambhat & Kutch
    if 20.0 <= lat <= 24.5 and 68.0 <= lon <= 73.2:
        return "Gujarat Coast", ["Kandla", "Mundra", "Pipavav", "Porbandar", "Veraval"]

    return "Indian Coastal Waters", ["Coastal Sector"]


def upsert_marine_alert(alert_dict: dict[str, Any]) -> None:
    """Safely register or update alert in backend CURRENT_ALERTS in-memory store."""
    try:
        from backend.routes.alerts import CURRENT_ALERTS
        
        # Remove any existing alert with exact same id
        existing_idx = next(
            (i for i, a in enumerate(CURRENT_ALERTS) if a.get("id") == alert_dict.get("id")),
            None,
        )
        if existing_idx is not None:
            CURRENT_ALERTS[existing_idx] = alert_dict
            logger.info(f"[alert_broadcaster] Updated existing alert: {alert_dict.get('id')}")
        else:
            CURRENT_ALERTS.insert(0, alert_dict)
            logger.info(f"[alert_broadcaster] Registered new alert: {alert_dict.get('id')}")
    except Exception as exc:
        logger.warning(f"[alert_broadcaster] Failed to upsert alert to registry: {exc}")


def evaluate_and_broadcast_alerts(envelope: AgentEnvelope) -> list[dict[str, Any]]:
    """
    Evaluate an AgentEnvelope against safety criteria and broadcast alerts if thresholds breached.
    Returns list of generated alert dictionaries.
    """
    data = envelope.data
    if not isinstance(data, dict):
        return []

    loc = data.get("location", {})
    lat = loc.get("lat", 0.0)
    lon = loc.get("lon", 0.0)

    region, ports = determine_coastal_region_and_ports(lat, lon)
    now_utc = datetime.now(timezone.utc)
    valid_until = (now_utc + timedelta(hours=6)).isoformat()
    issued_at = now_utc.isoformat()

    wind_speed = float(data.get("wind_speed_kmh", 0.0))
    wind_gusts = float(data.get("wind_gusts_kmh", 0.0))
    wave_height = float(data.get("wave_height_m", 0.0))
    lightning_risk = str(data.get("lightning_risk", "low")).lower()
    cyclone_alert = data.get("cyclone_alert")
    rain_prob = float(data.get("rain_probability_pct", 0.0))

    generated_alerts: list[dict[str, Any]] = []

    # 1. Cyclone Warning
    if cyclone_alert or wind_speed >= 62.0 or wind_gusts >= 80.0:
        alert_id = f"alert-cyclone-{round(lat, 1)}-{round(lon, 1)}"
        alert = {
            "id": alert_id,
            "type": "CYCLONE WARNING",
            "severity": "UNSAFE",
            "region": region,
            "headline": f"Tropical Cyclone / Storm Force Winds ({wind_speed:.0f} km/h) — Immediate Port Suspension",
            "details": f"{cyclone_alert or 'Dangerous gale force winds detected.'} Sustained wind {wind_speed:.1f} km/h, gusts reaching {wind_gusts:.1f} km/h. Sea conditions extremely rough.",
            "authority": "IMD Cyclone Warning Division & VARUNA Weather Intel",
            "action_scenario": "unsafe_cyclone",
            "issued_at": issued_at,
            "valid_until": valid_until,
            "affected_ports": ports,
            "boundary_geojson": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
        }
        upsert_marine_alert(alert)
        generated_alerts.append(alert)

    # 2. Severe Convective Lightning Squall
    elif lightning_risk == "high" and rain_prob >= 65.0:
        alert_id = f"alert-lightning-{round(lat, 1)}-{round(lon, 1)}"
        alert = {
            "id": alert_id,
            "type": "SEVERE LIGHTNING / CONVECTIVE SQUALL",
            "severity": "UNSAFE",
            "region": region,
            "headline": f"Severe Convective Lightning Squall Alert ({region})",
            "details": f"High risk of cloud-to-water lightning discharges with squalls up to {wind_gusts:.1f} km/h. Rain probability {rain_prob:.0f}%. Artisanal craft advised to seek shelter.",
            "authority": "MOSDAC Convective Systems / VARUNA Weather Intel",
            "action_scenario": "unsafe_lightning",
            "issued_at": issued_at,
            "valid_until": valid_until,
            "affected_ports": ports,
            "boundary_geojson": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
        }
        upsert_marine_alert(alert)
        generated_alerts.append(alert)

    # 3. High Swell / Kallakkadal Alert
    elif wave_height >= 2.5:
        severity = "UNSAFE" if wave_height >= 3.5 else "CAUTION"
        action_scenario = "unsafe_wave" if wave_height >= 3.5 else "caution_wave"
        alert_id = f"alert-swell-{round(lat, 1)}-{round(lon, 1)}"
        alert = {
            "id": alert_id,
            "type": "HIGH SWELL / KALLAKKADAL",
            "severity": severity,
            "region": region,
            "headline": f"High Swell Surge Alert {wave_height:.2f}m — Coastal Hazard",
            "details": f"Significant wave height {wave_height:.2f}m detected in coastal sector. Nearshore surge and dangerous breaker zones active near harbor mouths.",
            "authority": "INCOIS Coastal Hazard Warning Centre & VARUNA Weather Intel",
            "action_scenario": action_scenario,
            "issued_at": issued_at,
            "valid_until": valid_until,
            "affected_ports": ports,
            "boundary_geojson": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
        }
        upsert_marine_alert(alert)
        generated_alerts.append(alert)

    # 4. Gale Wind Caution
    elif wind_speed >= 40.0:
        alert_id = f"alert-wind-{round(lat, 1)}-{round(lon, 1)}"
        alert = {
            "id": alert_id,
            "type": "GALE WIND ADVISORY",
            "severity": "CAUTION",
            "region": region,
            "headline": f"Strong Wind Advisory ({wind_speed:.0f} km/h)",
            "details": f"Rough sea conditions with sustained winds {wind_speed:.1f} km/h (gusts {wind_gusts:.1f} km/h). Small motorized craft advised to exercise caution.",
            "authority": "IMD Marine Advisory & VARUNA Weather Intel",
            "action_scenario": "caution_wind",
            "issued_at": issued_at,
            "valid_until": valid_until,
            "affected_ports": ports,
            "boundary_geojson": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
        }
        upsert_marine_alert(alert)
        generated_alerts.append(alert)

    return generated_alerts
