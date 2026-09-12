import math
from typing import Tuple, List

def calculate_resolution(dist_km: float) -> float:
    """Scale resolution dynamically between 0.02 and 0.1 degrees based on distance."""
    if dist_km < 50:
        return 0.02
    elif dist_km > 700:
        return 0.1
    # Linear scale between 50km and 700km
    return round(0.02 + (0.08 * (dist_km - 50) / 650.0), 3)

def build_bounding_box(start_lat: float, start_lon: float, dest_lat: float, dest_lon: float, padding_pct: float = 0.15) -> Tuple[float, float, float, float]:
    """Returns min_lat, max_lat, min_lon, max_lon with padding."""
    min_lat = min(start_lat, dest_lat)
    max_lat = max(start_lat, dest_lat)
    min_lon = min(start_lon, dest_lon)
    max_lon = max(start_lon, dest_lon)
    
    lat_diff = max_lat - min_lat
    lon_diff = max_lon - min_lon
    
    # Handle straight line vertical/horizontal routes by ensuring minimum box dimensions
    if lat_diff < 0.1: lat_diff = 0.1
    if lon_diff < 0.1: lon_diff = 0.1
        
    pad_lat = lat_diff * padding_pct
    pad_lon = lon_diff * padding_pct
    
    return (
        min_lat - pad_lat,
        max_lat + pad_lat,
        min_lon - pad_lon,
        max_lon + pad_lon
    )

def generate_grid_nodes(min_lat: float, max_lat: float, min_lon: float, max_lon: float, resolution: float) -> List[Tuple[float, float]]:
    """Generates a flat list of (lat, lon) coordinate tuples representing grid nodes."""
    nodes = []
    lat = min_lat
    while lat <= max_lat + (resolution / 2): # allow slight float precision over
        lon = min_lon
        while lon <= max_lon + (resolution / 2):
            nodes.append((round(lat, 4), round(lon, 4)))
            lon += resolution
        lat += resolution
    return nodes

def snap_to_grid(lat: float, lon: float, resolution: float) -> Tuple[float, float]:
    """Snap an arbitrary coordinate to the nearest grid resolution interval."""
    return (
        round(round(lat / resolution) * resolution, 4),
        round(round(lon / resolution) * resolution, 4)
    )
