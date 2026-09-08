# Step 06 — Build verdict and action UI

**Status:** not started  
**Model:** Gemini 3.6 Flash or Gemini 3.8 Flash  
**Depends on:** Step 05

## Reads

- `docs/prompts/_shared/role-and-safety-rules.md`
- `docs/design-reference-analysis.md`
- `[FRONTEND_RESPONSE_TYPES]`
- `[MOCK_FIXTURE_DIRECTORY]`
- `docs/design/VARUNA_DESIGN_SYSTEM.md`
- `docs/design/VARUNA_UI_UX_MASTER_CONTEXT.md`

## Task

Implement the decision experience: verdict card, recommended action, confidence band/reason, top trace-backed reasons, data-freshness indicator, degradation/indeterminate notice, and loading/error states.

## Step-specific constraints

- Use only the backend-provided verdict and action.
- Make the “productive PFZ but unsafe” fixture unambiguous at a glance.
- Support all verdict and decision-state combinations from the contract, not only happy-path content.

## Exit criterion

At mobile and desktop widths, a user sees the verdict, action, reasons, and data limitation before optional map details.

## Current task

`[INSERT_ONE_BOUNDED_DECISION_UI_REQUEST]`

