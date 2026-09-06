# Route / Navigation Agent
**Owner:** Vedant (Tier 2 — start after Geofencing Agent is stable)

## Responsibility
Computes the safest path between two points, avoiding hazards,
restricted zones, and high-wave regions.

## MVP Tasks (Tier 2 — build after core Tier 1 agents are working)
- [ ] Build a hazard-weighted grid over the coastal region (combine wave height + restricted zones as a cost surface)
- [ ] Implement A* or Dijkstra pathfinding over that grid
- [ ] Return route as a GeoJSON LineString + total distance + any waypoint warnings
- [ ] Write 2-3 manual test cases comparing a straight-line route vs. the hazard-avoiding route

## Further Stage (Production)
- [ ] Real-time re-routing if conditions change mid-route
- [ ] Multi-vessel routing (if extended to fleet management use case)
- [ ] Route optimization considering fuel efficiency, not just hazard avoidance
- [ ] Integration with the offline-first mode: cache the last computed route for offline access

## Interface Contract
Consumes: `(start_coords, end_coords)`, Geofencing Agent output, Weather Agent output
Produces: `{route_geometry: GeoJSON, distance_km, warnings: [...]}`
