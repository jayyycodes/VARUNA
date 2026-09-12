import math
from typing import Tuple, List

def calculate_resolution(dist_km: float) -> float:
    if dist_km < 50:
        return 0.02
    elif dist_km > 700:
        return 0.1
    return round(0.02 + (0.08 * (dist_km - 50) / 650.0), 3)

def build_bounding_box(start_lat: float, start_lon: float, dest_lat: float, dest_lon: float, padding_pct: float = 0.15) -> Tuple[float, float, float, float]:
    min_lat = min(start_lat, dest_lat)
    max_lat = max(start_lat, dest_lat)
    min_lon = min(start_lon, dest_lon)
    max_lon = max(start_lon, dest_lon)
    
    lat_diff = max_lat - min_lat
    lon_diff = max_lon - min_lon
    
    # Use the max difference to ensure the bounding box has plenty of lateral room for detours
    max_diff = max(lat_diff, lon_diff, 1.0)
    pad = max_diff * padding_pct
    
    return (
        min_lat - pad,
        max_lat + pad,
        min_lon - pad,
        max_lon + pad
    )

def generate_grid_nodes(min_lat: float, max_lat: float, min_lon: float, max_lon: float, resolution: float) -> List[Tuple[float, float]]:
    nodes = []
    lat = min_lat
    while lat <= max_lat + (resolution / 2):
        lon = min_lon
        while lon <= max_lon + (resolution / 2):
            nodes.append((round(lat, 4), round(lon, 4)))
            lon += resolution
        lat += resolution
    return nodes

def snap_to_grid(lat: float, lon: float, resolution: float) -> Tuple[float, float]:
    return (
        round(round(lat / resolution) * resolution, 4),
        round(round(lon / resolution) * resolution, 4)
    )
