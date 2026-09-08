# Step 08 — Build Leaflet map

**Status:** not started  
**Model:** Gemini 3.6 Flash or Gemini 3.8 Flash  
**Depends on:** Step 05 and Step 06

## Reads

- `docs/prompts/_shared/role-and-safety-rules.md`
- `agents/geofencing/README.md`
- `agents/route/README.md`
- `[FRONTEND_RESPONSE_TYPES]`
- `[MOCK_FIXTURE_DIRECTORY]`
- `docs/design-reference-analysis.md`

## Task

Implement Leaflet map rendering and adapters for `user_location`, `pfz`, `hazard_zone`, `geofence`, `route`, and `advisory_area`. Add layer controls, an accessible legend, selected-feature detail, viewport handling, and safe invalid-geometry behavior.

## Step-specific constraints

- Test known coordinates to detect latitude/longitude swaps.
- Do not request device location without user action; support manual location input.
- Render only allow-listed layer types and keep invalid geometry from breaking the rest of the page.
- Never calculate or reinterpret a geofence/risk state in the client.

## Exit criterion

All valid fixture layers render with a clear legend; invalid or unknown layers fail safely, and PFZ cannot be confused with a safety map layer.

## Current task

`[INSERT_ONE_BOUNDED_MAP_REQUEST]`

