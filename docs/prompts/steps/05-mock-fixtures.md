# Step 05 — Create validated mock fixtures

**Status:** not started  
**Model:** Gemini 3.6 Flash or Gemini 3.8 Flash  
**Depends on:** Step 04

## Reads

- `docs/prompts/_shared/role-and-safety-rules.md`
- `[FRONTEND_RESPONSE_TYPES_AND_VALIDATOR]`
- `docs/ADEEY_ARCHITECTURE_ENGINEER.md`

## Task

Create versioned mock final-response fixtures and validation tests for: safe complete, caution wave threshold, unsafe cyclone/lightning, productive PFZ but unsafe travel, restricted geofence, stale/unavailable weather, indeterminate missing critical input, cited RAG answer, insufficient-evidence RAG answer, and invalid GeoJSON/schema cases.

## Step-specific constraints

- Mark all simulated data clearly as mock/demo data.
- Each risk claim must link to a trace entry; each regulation claim must link to a citation.
- Use plausible Indian coastal coordinates, timestamps, units, and source metadata; never represent them as live data.

## Exit criterion

Every valid fixture validates and every deliberately invalid fixture fails with the expected contract error.

## Current task

`[INSERT_ONE_BOUNDED_FIXTURE_REQUEST]`

