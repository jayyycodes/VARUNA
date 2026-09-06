"""
Route / Navigation Agent — owner: Vedant (Tier 2, after Geofencing is stable)

Computes the safest path between two points avoiding hazards, restricted
zones, and high-wave regions using a hazard-weighted grid + A*/Dijkstra.

See agents/route/README.md for full task breakdown (MVP + further stage).
"""


class RouteAgent:
    def compute_safe_route(self, start: tuple, end: tuple, hazards: list) -> dict:
        raise NotImplementedError("TODO: hazard-weighted A* over PostGIS grid")
