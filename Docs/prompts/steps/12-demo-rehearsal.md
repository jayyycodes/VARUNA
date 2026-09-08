# Step 12 — Rehearse the demo

**Status:** not started  
**Model:** Gemini 3.6 Flash for checklist/fixes; Gemini 3.1 Pro for final review  
**Depends on:** Step 11

## Reads

- `README.md`
- `docs/prompts/_shared/role-and-safety-rules.md`
- `[DEMO_FIXTURES_OR_DEMO_MODE]`
- `[FRONTEND_RUNBOOK]`
- `[OPEN_REVIEW_FINDINGS]`

## Task

Create and execute the demo rehearsal checklist. Test: a normal safety question, unsafe cyclone/lightning, productive PFZ but unsafe travel, restricted geofence, cited regulation answer, and stale/missing-data response. Verify the product remains understandable under a simulated source failure.

## Step-specific constraints

- Do not call simulated data “live.” Show its data time and demo status accurately.
- The 90-second story should be: ask → verdict/action → reasons → map → evidence/source → graceful degraded case.
- Record any manual recovery step required for a failed external source.

## Deliverable

Save `docs/demo-runbook.md` with commands, scenario inputs, expected behavior, fallback behavior, screenshots/recording locations if applicable, and owner of every unresolved issue.

## Exit criterion

The team can reproduce the demo sequence and a data-source failure without improvising or making an unsupported safety claim.

## Current task

`[INSERT_ONE_BOUNDED_DEMO_REQUEST]`

