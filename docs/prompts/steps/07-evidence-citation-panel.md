# Step 07 — Build evidence and citation panel

**Status:** not started  
**Model:** Gemini 3.6 Flash for UI; Gemini 3.1 Pro for policy review  
**Depends on:** Step 06

## Reads

- `docs/prompts/_shared/role-and-safety-rules.md`
- `agents/risk/README.md`
- `agents/rag_advisory/README.md`
- `[FRONTEND_RESPONSE_TYPES]`
- `[MOCK_FIXTURE_DIRECTORY]`
- `docs/design/VARUNA_DESIGN_SYSTEM.md`
- `docs/design/VARUNA_UI_UX_MASTER_CONTEXT.md`

## Task

Implement an expandable evidence experience: rule-trace cards, measured input, threshold/comparator, result, data freshness, missing inputs, citations, short source excerpts, and links from headline reasons to their exact supporting evidence.

## Step-specific constraints

- The UI does not write new explanations or combine evidence into new claims.
- If a claim has no valid supporting ID, present a safe unsupported/verification-needed state rather than a fact.
- Do not show raw retrieved chunks beyond the approved excerpt policy.

## Exit criterion

Selecting every visible headline reason opens its exact evidence; every regulation answer exposes authoritative citations or an explicit insufficient-evidence state.

## Current task

`[INSERT_ONE_BOUNDED_EVIDENCE_REQUEST]`

