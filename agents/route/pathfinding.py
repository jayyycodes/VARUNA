import math
import heapq
from typing import Tuple, List, Set, Optional, Callable

def heuristic(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-Circle Haversine distance heuristic (in km)."""
    R_EARTH_KM = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R_EARTH_KM * c

def get_neighbors(node: Tuple[float, float], resolution: float, bbox: Tuple[float, float, float, float]) -> List[Tuple[float, float]]:
    """Get valid orthogonal and diagonal neighbors for a node within the bounding box."""
    lat, lon = node
    min_lat, max_lat, min_lon, max_lon = bbox
    directions = [
        (resolution, 0), (-resolution, 0), (0, resolution), (0, -resolution),
        (resolution, resolution), (resolution, -resolution),
        (-resolution, resolution), (-resolution, -resolution)
    ]
    neighbors = []
    for d_lat, d_lon in directions:
        n_lat, n_lon = round(lat + d_lat, 4), round(lon + d_lon, 4)
        if min_lat <= n_lat <= max_lat and min_lon <= n_lon <= max_lon:
            neighbors.append((n_lat, n_lon))
    return neighbors

def a_star_search(
    start: Tuple[float, float],
    dest: Tuple[float, float],
    resolution: float,
    bbox: Tuple[float, float, float, float],
    is_safe_callback: Callable[[float, float], bool]
) -> Optional[List[Tuple[float, float]]]:
    """
    Standard A* algorithm.
    is_safe_callback(lat, lon) -> bool (True = safe/passable, False = restricted/blocked)
    """
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0.0}
    f_score = {start: heuristic(start[0], start[1], dest[0], dest[1])}
    closed_set: Set[Tuple[float, float]] = set()
    
    node_safety_cache = {}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current in closed_set:
            continue
        closed_set.add(current)
        
        # If we reached destination or are exceptionally close (within resolution)
        if current == dest or heuristic(current[0], current[1], dest[0], dest[1]) < (resolution * 111 * 0.5):
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            # Snap final point exactly to destination
            if path[-1] != dest:
                path.append(dest)
            # Ensure start point is exact
            if path[0] != start:
                path.insert(0, start)
            return path
            
        for neighbor in get_neighbors(current, resolution, bbox):
            if neighbor not in node_safety_cache:
                node_safety_cache[neighbor] = is_safe_callback(neighbor[0], neighbor[1])
                
            if not node_safety_cache[neighbor]:
                continue # Impassable node
                
            tentative_g = g_score[current] + heuristic(current[0], current[1], neighbor[0], neighbor[1])
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor[0], neighbor[1], dest[0], dest[1])
                f_score[neighbor] = f
                heapq.heappush(open_set, (f, neighbor))
                
    return None # No path found
