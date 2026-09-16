# Step 11 — Run safety and accessibility review

**Status:** not started  
**Model:** Gemini 3.1 Pro or Claude  
**Depends on:** Steps 06–10

## Reads

- `README.md`
- `docs/ADEEY_ARCHITECTURE_ENGINEER.md`
- `docs/prompts/_shared/role-and-safety-rules.md`
- `[FRONTEND_SOURCE_PATH]`
- `[VISUALIZATION_SOURCE_PATH]`
- `[FIXTURE_AND_TEST_PATHS]`

## Task

Review the completed frontend/visualization boundary without editing code. Audit safe, caution, unsafe, PFZ-but-unsafe, geofence, stale data, indeterminate, cited RAG, insufficient-evidence RAG, and invalid GeoJSON/schema scenarios.

## Step-specific constraints

- Report findings by `P0` (could cause unsafe action), `P1` (contract/evidence/geometry failure), `P2` (accessibility/usability/performance), and `P3` (polish).
- Every finding needs exact path, affected scenario, impact, recommended correction, and regression test.
- Treat a false reassurance caused by hidden/missing data as P0.

## Exit criterion

There are no unresolved P0/P1 findings and the review report is attached to the implementation PR.

## Current task

`[INSERT_ONE_BOUNDED_REVIEW_REQUEST]`

