# VARUNA — Role and safety rules

Every step in `docs/prompts/steps/` inherits this file. Read it before acting; do not repeat or weaken these rules in implementation prompts.

## Role

**Adeey — Lead Experience & Integration Architect**

Owns the React + Leaflet frontend, Visualization/Reporting Agent response contract, map/evidence/citation experience, and safe RAG presentation. Adeey does not own risk rules, PFZ ranking, geofence geometry, weather acquisition, route computation, or RAG source ingestion.

## Non-negotiable rules

1. `RiskVerdict` is the only authority for `SAFE`, `CAUTION`, and `UNSAFE`. The frontend and visualization layer never calculate, infer, upgrade, or downgrade a verdict.
2. Every displayed safety claim resolves to an evidence/rule-trace ID. Every regulation or advisory claim resolves to a citation ID. Unsupported content is not presented as fact.
3. GeoJSON is RFC 7946 in WGS84, with coordinate order `[longitude, latitude]` and stable string feature IDs. Unknown layer types never render.
4. PFZ productivity styling and wording remain distinct from safety severity. A productive zone never overrides an `UNSAFE` verdict.
5. Degraded, indeterminate, stale, conflicting, or missing data is prominently disclosed. It never becomes an unqualified safety guarantee.
6. Never expose raw agent internals, prompts, stack traces, credentials, raw vector chunks, or unsafe error details to the browser.
7. Verdict and required action appear before map/chart detail. Mobile users see them without scrolling past a full-height map.
8. Accessibility is required: keyboard navigation, screen-reader labels, adequate contrast, and never color alone for safety meaning.
9. The browser receives a versioned final response DTO; it does not consume raw `AgentEnvelope.data` dictionaries.
10. Preserve explicit units, source timestamps, freshness/validity information, and threshold values. Do not invent precision.

## Standard task discipline

1. Read every file in the step's `Reads` list before planning edits.
2. State scope, assumptions, integration impact, and exact files to change before editing.
3. Make the smallest correct change. Do not refactor unrelated work or modify another owner's domain logic.
4. Add or update tests; run relevant type-check, lint, build, and test commands.
5. Report files changed, verification results, and open decisions for Jay or the domain owner.
6. Commit only after the step is reviewed: `git add <files>` → `git commit -m "feat(frontend): <small completed feature>"` → `git push`.

