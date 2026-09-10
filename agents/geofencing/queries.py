import json
from typing import Tuple, Optional

# In a real setup, we would use asyncpg or psycopg2.
# Using a dummy class for demonstration. We will assume a psycopg2/asyncpg connection is passed.

def get_nearest_zone(conn, lat: float, lon: float) -> Optional[dict]:
    """
    Returns the nearest zone, distance, and whether it contains the point.
    Returns: { "name": str, "distance_km": float, "contains": bool }
    """
    query = """
    SELECT 
        name,
        ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000.0 AS distance_km,
        ST_Contains(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS contains
    FROM restricted_zones
    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
    LIMIT 1;
    """
    with conn.cursor() as cur:
        cur.execute(query, (lon, lat, lon, lat, lon, lat))
        row = cur.fetchone()
        
    if not row: return None
    return {"name": row[0], "distance_km": float(row[1]), "contains": bool(row[2])}

def check_geofence(conn, lat: float, lon: float, warning_threshold_km: float = 2.0) -> Tuple[str, str, float]:
    """
    Returns (status, nearest_boundary_name, distance_km)
    status: 'clear' | 'warning' | 'restricted'
    """
    nearest = get_nearest_zone(conn, lat, lon)
    
    if not nearest:
        return "clear", "None", 9999.9
        
    distance_km = nearest["distance_km"]
    name = nearest["name"]
    
    if nearest["contains"]:
        return "restricted", name, distance_km
    elif distance_km <= warning_threshold_km:
        return "warning", name, distance_km
    else:
        return "clear", name, distance_km
