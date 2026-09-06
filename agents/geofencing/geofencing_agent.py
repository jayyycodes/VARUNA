"""
Geospatial / Geofencing Agent — owner: Vedant

Point-in-polygon checks against EEZ / IMBL / Marine Protected Area
boundaries using PostGIS. Works fully offline once shapefiles are loaded.

See agents/geofencing/README.md for full task breakdown (MVP + further stage).
"""

from backend.schemas.envelope import AgentEnvelope


class GeofencingAgent:
    async def check_geofence(self, lat: float, lon: float) -> AgentEnvelope:
        raise NotImplementedError("TODO: ST_Contains / ST_DWithin query against PostGIS")
