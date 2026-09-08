# Step 09 — Integrate Planner API

**Status:** blocked on Jay's endpoint specification  
**Model:** Gemini 3.1 Pro or Claude  
**Depends on:** Step 04, Step 05, Step 06, and Step 08

## Reads

- `README.md`
- `agents/planner/README.md`
- `backend/schemas/envelope.py`
- `docs/prompts/_shared/role-and-safety-rules.md`
- `[JAY_API_ENDPOINT_SPEC]`
- `[FRONTEND_RESPONSE_TYPES]`

## Task

Implement the typed planner API client, request model, runtime response validation, response-state mapper, query-run correlation, mock API mode, and integration tests.

## Step-specific constraints

- Use explicit location and ISO-8601 time windows; do not infer coordinates or time.
- User-facing errors must be plain language and must not expose backend internals.
- Define the request timeout and partial-result behavior from Jay's API specification before implementation.
- Do not simulate streaming or polling unless Jay's endpoint contract supports it.

## Exit criterion

Mocked HTTP integration tests cover complete, degraded, indeterminate, timeout, malformed-error, invalid-schema, and unsafe responses.

## Current task

`[INSERT_ONE_BOUNDED_API_INTEGRATION_REQUEST]`

