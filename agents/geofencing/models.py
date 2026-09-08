from pydantic import BaseModel
from typing import Literal

class GeofencingRequest(BaseModel):
    query_run_id: str
    lat: float
    lon: float

class GeofencingDataPayload(BaseModel):
    status: Literal["clear", "warning", "restricted"]
    nearest_boundary_name: str
    distance_km: float
