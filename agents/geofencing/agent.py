import os
import sys
from datetime import datetime, timezone
import asyncio

# Add the backend path so we can import AgentEnvelope
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.schemas.envelope import AgentEnvelope

from .models import GeofencingRequest, GeofencingDataPayload
from .queries import check_geofence

class GeofencingAgent:
    def __init__(self, db_pool):
        self.db_pool = db_pool

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

    def _run_check_sync(self, lat: float, lon: float):
        import psycopg2
        # In a real setup, we'd use a connection pool provided by the framework.
        # For testing, we make a quick connection.
        conn = psycopg2.connect(
            dbname="varuna", user="varuna", password="varuna_dev", host="localhost", port="5432"
        )
        # check_geofence is now a sync function
        import asyncio
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(check_geofence(conn, lat, lon))
        conn.close()
        return res
