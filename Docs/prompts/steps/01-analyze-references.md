# Step 01 — Analyze Stitch references

**Status:** not started  
**Model:** Gemini 3.1 Pro or Claude  
**Depends on:** none

## Reads

- `README.md`
- `docs/ADEEY_ARCHITECTURE_ENGINEER.md`
- `docs/prompts/_shared/role-and-safety-rules.md`
- `docs/design/VARUNA_DESIGN_SYSTEM.md`
- `docs/design/VARUNA_UI_UX_MASTER_CONTEXT.md`

## Task

Analyze the Stitch references and existing snippets without editing code. Produce a short implementation brief that identifies the visual system, reusable component patterns, responsive behavior, and a safe mapping to VARUNA's query, verdict, map, evidence, citations, and notices.

## Step-specific constraints

- Treat Stitch as visual direction, not as a source of API fields or marine-business logic.
- Flag any design element that would hide uncertainty, make PFZ look like safe travel, or place the map ahead of the verdict/action.
- If a named reference is unavailable, stop and request its exact path rather than guessing.

## Deliverable

Save the findings as `docs/design-reference-analysis.md` with: screen inventory, inferred tokens, component inventory, responsive notes, required non-happy-path states, and open questions for Jay.

## Exit criterion

The team can build a consistent UI from the document without reopening every reference image.

## Current task

`[INSERT_ONE_BOUNDED_REQUEST_AND_REFERENCE_PATHS]`

