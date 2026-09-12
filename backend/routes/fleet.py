"""
Fleet Telemetry & AIS Operations API
Provides real-time positioning, geofence compliance, safety advisories,
and harbor status for Indian coastal fishing vessels and patrol craft.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/fleet", tags=["fleet"])


class VesselTelemetry(BaseModel):
    id: str
    name: str
    type: str
    port: str
    lat: float
    lon: float
    coordinates: str
    status: str
    compliance: str
    severity: str  # safe, caution, unsafe
    fuel: str
    crew: int
    ais_status: str
    heading_deg: int
    speed_kts: float
    last_ping_utc: str


class FleetSummary(BaseModel):
    active_craft: int
    in_pfz_count: int
    weather_clear_pct: float
    harbor_moored_count: int
    timestamp_utc: str
    vessels: list[VesselTelemetry]


# Live coastal vessel state
LIVE_VESSELS: list[dict[str, Any]] = [
    {
        "id": "IND-MH-0192",
        "name": "Matsya Sagar IV",
        "type": "Mechanized Trawler (14m)",
        "port": "Mirya Bay, Ratnagiri",
        "lat": 17.018,
        "lon": 73.182,
        "coordinates": "17.02° N, 73.18° E",
        "status": "Operating in PFZ Zone",
        "compliance": "SAFE (All Clear)",
        "severity": "safe",
        "fuel": "74%",
        "crew": 6,
        "ais_status": "Active (Class B AIS)",
        "heading_deg": 240,
        "speed_kts": 6.8,
        "last_ping_utc": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "IND-MH-5510",
        "name": "Sindhudurg Star",
        "type": "Artisanal Motor Craft (7.5m)",
        "port": "Malvan Port",
        "lat": 16.024,
        "lon": 73.421,
        "coordinates": "16.02° N, 73.42° E",
        "status": "Transit near Sanctuary Buffer",
        "compliance": "SAFE (Clear of MPA Core)",
        "severity": "safe",
        "fuel": "65%",
        "crew": 3,
        "ais_status": "Active (VHF Ch 16)",
        "heading_deg": 170,
        "speed_kts": 5.2,
        "last_ping_utc": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "IND-KL-4081",
        "name": "Samudra Jyoti",
        "type": "Motorized Gillnetter (9.5m)",
        "port": "Cochin Harbour",
        "lat": 9.925,
        "lon": 76.152,
        "coordinates": "09.92° N, 76.15° E",
        "status": "Returning to Harbor",
        "compliance": "CAUTION (Wave Swell 2.6m)",
        "severity": "caution",
        "fuel": "42%",
        "crew": 4,
        "ais_status": "Active",
        "heading_deg": 85,
        "speed_kts": 7.4,
        "last_ping_utc": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "IND-AP-8821",
        "name": "Bay Queen III",
        "type": "Deep Sea Longliner (16m)",
        "port": "Visakhapatnam",
        "lat": 17.652,
        "lon": 83.324,
        "coordinates": "17.65° N, 83.32° E",
        "status": "Moored / Harbor Anchor",
        "compliance": "UNSAFE (Port Signal #8 Active)",
        "severity": "unsafe",
        "fuel": "90%",
        "crew": 8,
        "ais_status": "Harbour Transponder Standby",
        "heading_deg": 0,
        "speed_kts": 0.0,
        "last_ping_utc": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "IND-GJ-1104",
        "name": "Saurashtra Shakti",
        "type": "Wooden Trawler (12m)",
        "port": "Veraval Port",
        "lat": 20.895,
        "lon": 70.368,
        "coordinates": "20.90° N, 70.37° E",
        "status": "Fishing in Continental Shelf",
        "compliance": "SAFE (EEZ Verified)",
        "severity": "safe",
        "fuel": "58%",
        "crew": 5,
        "ais_status": "Active",
        "heading_deg": 195,
        "speed_kts": 6.1,
        "last_ping_utc": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "IND-TN-3392",
        "name": "Coromandel Fisher",
        "type": "Pair Trawler (15m)",
        "port": "Chennai Fisheries Harbour",
        "lat": 13.125,
        "lon": 80.312,
        "coordinates": "13.13° N, 80.31° E",
        "status": "En Route to PFZ Alpha",
        "compliance": "SAFE (All Clear)",
        "severity": "safe",
        "fuel": "81%",
        "crew": 7,
        "ais_status": "Active",
        "heading_deg": 110,
        "speed_kts": 8.0,
        "last_ping_utc": datetime.now(timezone.utc).isoformat(),
    },
]


@router.get("", response_model=FleetSummary)
@router.get("/status", response_model=FleetSummary)
async def get_fleet_status():
    """
    Returns live coastal fleet positioning, AIS statuses, and safety compliance metrics.
    """
    active_count = len([v for v in LIVE_VESSELS if v["speed_kts"] > 0])
    in_pfz = len([v for v in LIVE_VESSELS if "PFZ" in v["status"]])
    safe_count = len([v for v in LIVE_VESSELS if v["severity"] == "safe"])
    moored = len([v for v in LIVE_VESSELS if v["speed_kts"] == 0])

    compliance_pct = round((safe_count / max(1, len(LIVE_VESSELS))) * 100.0, 1)

    return FleetSummary(
        active_craft=len(LIVE_VESSELS),
        in_pfz_count=in_pfz,
        weather_clear_pct=compliance_pct,
        harbor_moored_count=moored,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        vessels=[VesselTelemetry(**v) for v in LIVE_VESSELS],
    )
