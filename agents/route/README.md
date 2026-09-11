# Route / Navigation Agent
**Owner:** Vedant (Tier 2)  
**Status:** MVP Complete ✅ | Next Phase: A* Bathymetry & Dynamic Weather Routing

## Responsibility
Computes the safest navigational corridor between departure ports and destination fishing grounds or coastal harbors. Avoids shallow waters, severe wave swell sectors, and restricted marine boundaries (MPAs and foreign EEZs).

Directly powers Adeey's **Route Optimization & Safe Passage View** ([`frontend/src/features/routing/`](file:///c:/Development/Varuna/frontend/src/features/routing)) and the main Leaflet interactive navigation map.

---

## 1. MVP Tasks (Completed ✅)
- [x] **Geodetic Distance & Heading**: Computes Great-Circle distance (km & NM) and initial navigational bearing / cardinal heading ($170.1^\circ\text{ S}$).
- [x] **Coastal Clearance Arc**: Implemented offshore buffer offset to bypass near-shore rocky shoals and reef promontories along the Konkan coast.
- [x] **Boundary Clearance Validation**: Cross-checks trajectory against Malvan Marine Sanctuary and foreign EEZ boundaries to issue buffer cautions.
- [x] **Vessel Telemetry Modeling**: Estimates fuel burn ($2.2\text{ L/NM}$) and transit duration at standard artisanal cruising speeds ($8\text{ knots}$).
- [x] **GeoJSON LineString Export**: Produces valid GeoJSON features for seamless Leaflet map rendering.
- [x] **Full Planner Integration**: Dispatched automatically when user intent contains navigational routing.

---

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 1.1, 3, & 6), the next operational priorities are:

- [ ] **A* Grid Search on GEBCO Bathymetry**:
  - Replace clearance heuristics with full A* pathfinding over a 15-arc-second bathymetric water depth grid.
  - Hard constraint: Guarantee vessel never crosses zero-depth land contours or rocky shoals.
- [ ] **Dynamic Weather-Weighted Cost Surface**:
  - Formulate real-time cost grid:
    $$\text{Cost}(u \to v) = d(u,v) \times \left(1.0 + w_{\text{swell}} \cdot H_s^2 + w_{\text{wind}} \cdot \cos(\theta_{\text{headwind}}) + w_{\text{zone}} \cdot \mathbb{I}_{\text{restricted}}\right)$$
  - Steer craft around heavy swell zones ($>2.5$m) into sheltered coastal lee waters.
- [ ] **INCOIS Tidal Draft Clearance Engine**:
  - Ingest INCOIS coastal tidal tables (hourly high/low tide predictions) to calculate draft safety at shallow bay mouths and estuaries.
- [ ] **Multi-Waypoint Route Chains**:
  - Support multi-leg itineraries (e.g. *Ratnagiri Harbor $\to$ PFZ Zone Alpha-7 $\to$ Malvan Landing Center*).
- [ ] **Engine-Specific Fuel Optimization**:
  - Customize fuel economy curves based on inboard diesel HP, outboard 2-stroke engines, and speed-over-ground (SOG).

---

## 3. Verification & Testing
Run route agent automated test suite:
```powershell
pytest tests/test_route.py -v
```
Or run quick command-line test:
```powershell
python -c "from agents.route.route_agent import RouteAgent; ra = RouteAgent(); res = ra.plan_route(16.99, 73.30, 16.05, 73.47); print(res['distance_nm'], 'NM | Fuel:', res['fuel_estimate_liters'], 'L | Heading:', res['compass_heading'])"
```
