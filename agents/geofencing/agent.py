import os
import sys
from datetime import datetime, timezone
import asyncio
import psycopg2
from psycopg2 import pool

# Add the backend path so we can import AgentEnvelope
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.schemas.envelope import AgentEnvelope

from .models import GeofencingRequest, GeofencingDataPayload
from .queries import check_geofence

class GeofencingAgent:
    def __init__(self, db_pool=None):
        if db_pool:
            self.db_pool = db_pool
        else:
            host = os.getenv("POSTGRES_HOST", "127.0.0.1")
            port = int(os.getenv("POSTGRES_PORT", "5433"))
            db = os.getenv("POSTGRES_DB", "varuna")
            user = os.getenv("POSTGRES_USER", "varuna")
            password = os.getenv("POSTGRES_PASSWORD", "varuna_dev")
            self.db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dbname=db, user=user, password=password, host=host, port=port)

    async def run(self, request: GeofencingRequest) -> AgentEnvelope:
        try:
            # Run the synchronous psycopg2 logic in a thread pool to avoid blocking the event loop
            status_val, boundary_name, distance = await asyncio.to_thread(
                self._run_check_sync, request.lat, request.lon
            )
            
            data_payload = GeofencingDataPayload(
                status=status_val,
                nearest_boundary_name=boundary_name,
                distance_km=distance
            )
            
            return AgentEnvelope(
                agent="geofencing",
                query_run_id=request.query_run_id,
                status="success",
                data=data_payload.model_dump(),
                confidence=1.0,
                source="Local PostGIS Shapefiles (WDPA, MarineRegions)",
                timestamp=datetime.now(timezone.utc),
                thresholds_used={"warning_threshold_km": 2.0}
            )
            
        except Exception as e:
            return AgentEnvelope(
                agent="geofencing",
                query_run_id=request.query_run_id,
                status="error",
                data={},
                confidence=0.0,
                source="Local PostGIS",
                timestamp=datetime.now(timezone.utc),
                error_message=str(e)
            )

    async def check_route(self, waypoints: list[tuple[float, float]]) -> dict:
        """
        Validates a list of waypoints. Returns the first breach (warning/restricted) encountered.
        """
        try:
            for lat, lon in waypoints:
                status_val, boundary_name, distance = await asyncio.to_thread(
                    self._run_check_sync, lat, lon
                )
                if status_val in ("restricted", "warning"):
                    return {
                        "status": status_val,
                        "breach_lat": lat,
                        "breach_lon": lon,
                        "nearest_boundary_name": boundary_name,
                        "distance_km": distance
                    }
            
            return {"status": "clear"}
            
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    def _run_check_sync(self, lat: float, lon: float):
        conn = self.db_pool.getconn()
        try:
            res = check_geofence(conn, lat, lon)
            return res
        finally:
            self.db_pool.putconn(conn)
