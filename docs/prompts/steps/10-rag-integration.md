# Step 10 — Integrate cited RAG answers

**Status:** blocked on Prapti's retrieval metadata  
**Model:** Gemini 3.1 Pro or Claude  
**Depends on:** Step 07 and Step 09

## Reads

- `agents/rag_advisory/README.md`
- `docs/prompts/_shared/role-and-safety-rules.md`
- `[JAY_AND_PRAPTI_RAG_RESPONSE_SPEC]`
- `[FRONTEND_RESPONSE_TYPES]`
- `[EVIDENCE_PANEL_COMPONENTS]`

## Task

Integrate citation-grounded RAG/advisory answers into the final response and frontend. Render answer claims only when their citation IDs resolve to title, publisher, source link, timestamp, and approved excerpt metadata.

## Step-specific constraints

- For insufficient evidence, state that the available official sources cannot verify the answer and provide a safe next action.
- Preserve canonical numeric values, verdict enums, source language, and evidence IDs during translation/rendering.
- Do not treat retrieval confidence alone as proof of a legal or regulatory claim.

## Exit criterion

A cited answer renders linked authoritative sources; an uncited or insufficient-evidence answer never appears as a verified fact.

## Current task

`[INSERT_ONE_BOUNDED_RAG_REQUEST]`

