# Step 04 — Define typed response contract

**Status:** blocked on Jay's approval  
**Model:** Gemini 3.1 Pro or Claude  
**Depends on:** Step 03

## Reads

- `README.md`
- `backend/schemas/envelope.py`
- `docs/ADEEY_ARCHITECTURE_ENGINEER.md` (canonical final response contract)
- `docs/prompts/_shared/role-and-safety-rules.md`
- `[JAY_APPROVED_RESPONSE_CONTRACT_IF_AVAILABLE]`

## Task

Design and implement TypeScript types plus runtime validation for `UserResponseV1`. The frontend must consume this versioned final DTO, never raw `AgentEnvelope` objects.

Required data: schema version, query/run IDs, generated timestamp, decision state, verdict/action, confidence band/reason, claims/evidence/citation IDs, citations, freshness, degradation notices, GeoJSON FeatureCollections, allowed map layers, and rule-trace items.

## Step-specific constraints

- Verdict enum: `SAFE`, `CAUTION`, `UNSAFE`, `UNKNOWN`.
- Decision state enum: `complete`, `degraded`, `indeterminate`, `error`.
- Risk-rule claims require evidence IDs; regulation/advisory claims require citation IDs.
- Flag backend contract changes as proposals for Jay. Do not silently change the Planner's interface.

## Exit criterion

Runtime validation accepts a valid response and rejects invalid fixtures for missing evidence, missing citations, bad geometry/coordinates, unknown map layer, and incompatible schema version.

## Current task

`[INSERT_ONE_BOUNDED_CONTRACT_REQUEST]`

