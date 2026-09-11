# Visualization / Reporting Agent & Frontend
**Owner:** Adeey  
**Status:** MVP Complete ✅ | Next Phase: Offline Tile Caching & Historical Trend Charts

## Responsibility
Transforms multi-agent reasoning, deterministic rule traces, GeoJSON spatial layers, and legal citations into an intuitive, high-aesthetic command dashboard for maritime operators and fishermen.

---

## 1. MVP Tasks (Completed ✅)
- [x] **User Contract & Schema Definition**: Designed strict TypeScript interfaces in [`frontend/src/contracts/userResponse.ts`](file:///c:/Development/Varuna/frontend/src/contracts/userResponse.ts).
- [x] **Interactive Leaflet Map Canvas**:
  - Rendered PFZ fishing spot clusters with dual-ring halo styling and rich oceanographic telemetry popups.
  - Rendered hazard polygons (cyclone cones, severe wave squalls) with red/amber safety styling.
  - Rendered dynamic navigational routes as glowing dashed teal corridors (`#35B8A6`) with waypoint markers.
  - Implemented dynamic auto-framing bounding box and centroid calculations.
- [x] **Evidence & Provenance Panel**:
  - *Rules & Traces Tab*: Visual audit cards showing deterministic thresholds, measured values, and `BREACH` / `PASSED` status.
  - *Data Freshness Tab*: Real-time feed latency and station observation timestamps.
  - *Statutory Citations Tab*: Grounded legal citations with official publishers and gazette excerpts.
- [x] **Specialized Operational Views**:
  - *Marine Intelligence Command* (Main map & safety assessment).
  - *Route Optimization & Safe Passage* (Live navigational timeline, corridor clearance, and vessel telemetry HUD).
  - *Active Alerts & Fleet Operations* dashboard views.

---

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 1.1, 3, & 9), the next operational priorities are:

- [ ] **Offline Map Tile Caching (Service Worker / PWA)**:
  - Implement IndexedDB / CacheStorage service worker caching for coastal marine basemap tiles (0–12 NM zone) so maps render with zero cellular connectivity at sea.
- [ ] **Historical Trend & Time-Series Charts (SIH Query #7)**:
  - Build interactive time-series visualizations for SST anomalies, chlorophyll concentration cycles, and historical upwelling trends.
- [ ] **Progressive Streaming Rendering**:
  - Implement Server-Sent Events (SSE) / WebSocket streaming to render GeoJSON map layers instantly while the LLM natural-language explanation streams in progressively.
- [ ] **Interactive Claim Grounding (Hover-to-Highlight)**:
  - On hovering over any claim in the AI explanation, visually highlight the corresponding sensor card, rule trace, or citation in the Evidence Panel.
- [ ] **Multilingual UI Localization (Bhashini Integration)**:
  - Support Hindi, Marathi, Tamil, and Malayalam UI localization with Text-to-Speech (TTS) voice playback for artisanal boat operators.
- [ ] **Mobile Touch Optimization**:
  - Refine viewport gestures, high-contrast daylight mode, and enlarged touch targets for wet-finger operation on fishing vessels.

---

## 3. Verification & Frontend Build
Test frontend build and TypeScript compilation:
```powershell
cd frontend
npm run build
```
Or run live development server:
```powershell
npm run dev
```
