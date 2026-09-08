# VARUNA — Claude Project Context

## Project

**VARUNA / ORCA** is an Agentic Marine Intelligence platform for India's coastline, created for Smart India Hackathon 2026 (SIH26176, ISRO / Department of Space).

The product helps fishermen, coastal authorities, and maritime operators ask natural-language questions and receive evidence-backed answers with maps and citations. Its core user journeys are:

1. **Where should I fish?** — PFZ, SST, chlorophyll, weather, and distance produce ranked fishing zones.
2. **Can I go out tomorrow?** — waves, wind, tide, cyclone, lightning, and boundaries produce a safety verdict.
3. **How do I get there safely?** — hazards and boundaries produce a route/map response.

The project is currently an architecture scaffold. Most Python agents contain interface skeletons with `NotImplementedError`; the shared Pydantic envelope is the implemented cross-agent contract. Do not assume APIs, frontend code, database schema, ETL pipelines, or observability are already implemented just because the README describes them.

## Read first

Before planning or editing, read these files in this order:

1. `README.md` — source of truth for team ownership, scope, data sources, build order, and system design.
2. `ADEEY_ARCHITECTURE_ENGINEER.md` — Adeey's detailed architectural charter, contracts, quality gates, and delivery plan.
3. `agents/visualization/README.md` — Visualization Agent scope.
4. `backend/schemas/envelope.py` — current shared `AgentEnvelope` and `RiskVerdict` types.
5. The relevant domain README in `agents/` before touching an integration boundary.

## Team ownership

| Owner | Responsibility | Do not take over without explicit instruction |
|---|---|---|
| Jay | Planner/Orchestrator, FastAPI/API gateway, LangGraph, final agent dispatch/aggregation | Planner intent policy, orchestration, backend gateway |
| Adeey | Visualization/Reporting Agent, React + Leaflet frontend, final response projection, evidence/citations UI, RAG presentation integration | This is the active ownership context for Claude |
| Jaish | Marine/Fishing intelligence and deterministic Risk Assessment Agent | PFZ ranking, SST/chlorophyll science, safety rule logic/thresholds |
| Vedant | Geofencing and Tier-2 Route/Navigation Agent | Boundary correctness, PostGIS spatial calculations, pathfinding |
| Cbum | Weather Intelligence Agent | Weather source acquisition/normalization/caching |
| Prapti | RAG data layer | Source collection, chunking, embeddings, vector-store loading |

## Adeey's role

Adeey is the **Lead Experience & Integration Architect**. This is not merely a visual/UI role. Adeey owns the system's human-trust boundary:

- final versioned response DTO sent to the client;
- structured conversion of agents' approved output into map layers, evidence, and citations;
- React + TypeScript frontend and Leaflet map experience;
- safety-first presentation of deterministic risk outputs;
- accessibility, responsiveness, source freshness, degradation, and uncertainty UX;
- frontend-backend contract validation and fixture-driven integration;
- presentation of RAG answers only when grounded in citations.

## Architectural boundary

```text
User query → translation wrapper → Planner (Jay) → domain agents
                                        ↓
                           Risk Agent (Jaish; deterministic)
                                        ↓
              Visualization/Reporting boundary (Adeey)
          response contract + map + evidence + citations + UI
                                        ↓
                         React + Leaflet client (Adeey)
```

Adeey does **not** own weather retrieval, PFZ scoring, rule thresholds, boundary calculations, route algorithms, or RAG document ingestion. When a requirement crosses these boundaries, identify the owning teammate and propose a contract rather than duplicating the domain logic.

## Non-negotiable safety rules

1. The Risk Agent's deterministic `RiskVerdict` is the only authority for `SAFE`, `CAUTION`, and `UNSAFE`.
2. Never calculate, alter, upgrade, downgrade, or infer a safety verdict in the frontend or visualization layer.
3. An LLM may organize/translate a pre-approved evidence packet, but may not invent facts, thresholds, regulations, or a verdict.
4. Every user-visible safety claim must map to structured evidence/rule-trace IDs.
5. Every regulation/advisory/RAG claim must map to one or more authoritative citation IDs.
6. If risk-critical information is absent, stale, or conflicting, make it prominent. Never turn that into a reassuring “safe” presentation.
7. Use an explicit `UNKNOWN` verdict and/or `indeterminate` decision state for insufficient information, based on the approved backend policy.
8. PFZ productivity is not navigation safety. A productive zone must never visually or textually override an unsafe travel/departure verdict.
9. Do not expose raw agent envelopes, prompt/tool traces, credentials, raw source chunks, exception stack traces, or backend internals to the browser.

## Current shared contract

`backend/schemas/envelope.py` currently contains:

```python
class AgentEnvelope(BaseModel):
    agent: str
    query_run_id: str
    status: Literal["success", "error", "degraded"]
    data: dict[str, Any]
    confidence: float
    source: str
    timestamp: datetime
    thresholds_used: dict[str, Any] | None
    error_message: str | None

class RiskVerdict(BaseModel):
    query_run_id: str
    verdict: Literal["SAFE", "CAUTION", "UNSAFE"]
    reasons: list[str]
    rule_trace: dict[str, Any]
    created_at: datetime
```

This is an internal inter-agent envelope. It is not an adequate final browser contract by itself. Do not pass its free-form `data` dictionary directly to React components.

## Proposed final response contract

The recommended browser-facing DTO is versioned and contains:

```text
schema_version
query_run_id
session_id
generated_at
decision_status: complete | degraded | indeterminate | error
summary:
  headline
  verdict: SAFE | CAUTION | UNSAFE | UNKNOWN
  confidence_band: high | medium | low | unknown
  confidence_reason
  action
claims[]:
  id, text, kind, evidence_ids[], citation_ids[]
map:
  viewport, layers[]
evidence_panel:
  rule_trace[], data_freshness[], missing_inputs[]
citations[]:
  id, title, publisher, url, excerpt, published_at, accessed_at
notices[]
degradation
```

Do not implement unapproved interface changes silently. If Jay has not yet approved a final DTO, clearly label any model/schema change as proposed and build fixtures/adapters around it.

## GeoJSON and map rules

- Use RFC 7946 GeoJSON in WGS84 / EPSG:4326.
- Coordinate order is always **`[longitude, latitude]`**, not `[latitude, longitude]`.
- Every feature needs a stable string ID.
- Every visible feature should carry semantic properties including `layer_id`, `title`, `severity`, `source_ids`, `observed_at`, and `valid_to` if applicable.
- Allow-listed layer types: `user_location`, `pfz`, `hazard_zone`, `geofence`, `route`, `advisory_area`.
- Unknown layer types must be rejected or safely ignored; malformed geometry must not crash the verdict/evidence UI.
- Keep PFZ/productivity colors and language distinct from risk/severity colors and language.
- Provide map legend and layer controls; do not communicate severity by color alone.
- The browser must not calculate geofence status, safety severity, or route risk.

## Frontend principles

- Preferred stack: React + TypeScript + Leaflet.
- Organize by feature: `query`, `decision`, `map`, `evidence`, `citations`, `advisory`, with a typed `api` boundary and reusable UI components.
- Validate backend response at runtime before rendering.
- Treat the final response as immutable server state. Layer visibility, selected feature, and open/closed panels are local UI state.
- Display hierarchy: **verdict → required action → top reasons → map → evidence/sources → details**.
- Support loading, complete, degraded, indeterminate, empty, validation error, and generic backend-error states.
- On mobile, verdict/action must be visible without a user having to scroll below a full-height map.
- Use keyboard-accessible controls and readable text alternatives for map information.
- Show source timestamps, validity range, and stale/missing data clearly.

## Stitch design references and snippets

The user may provide Stitch screenshots/exports and code snippets. Treat them as visual/style reference, not an excuse to copy unsafe interaction logic or infer missing domain data.

When references are available:

1. Inspect them before coding.
2. Identify reusable layout patterns, typography, spacing, tokens, components, and responsive behavior.
3. Map reference areas to VARUNA concepts: query, verdict, map, layers, evidence, citations, notices.
4. Retain their visual language while applying VARUNA's safety hierarchy and accessibility constraints.
5. Ask for the exact asset/path if a reference is named but unavailable.

## Fixture-first workflow

Build and validate the frontend against versioned mock JSON fixtures before depending on live agents/APIs. Required scenarios:

1. Complete safe response.
2. Caution due to a wave-height threshold.
3. Unsafe cyclone/lightning response.
4. Productive PFZ but unsafe departure response.
5. Restricted geofence response.
6. Stale/unavailable weather source response.
7. Missing risk-critical data / indeterminate response.
8. Cited RAG/regulation answer.
9. RAG insufficient-evidence response.
10. Invalid schema/GeoJSON response for validator failure tests.

For each fixture, preserve clear mock/demo labeling, timestamps, evidence IDs, citations, and source freshness.

## Testing requirements

For every meaningful feature, add or update tests appropriate to the repository's stack.

Minimum checks:

- final response schema accepts valid fixtures and rejects invalid ones;
- coordinate-order regression test uses a known Indian coastal location;
- unknown/invalid map layers fail safely;
- each risk claim resolves to rule-trace evidence;
- each regulation claim resolves to citations;
- a degraded/indeterminate response cannot be presented as unqualified safe travel;
- PFZ visual treatment cannot override an unsafe verdict;
- accessible labels exist for verdict, freshness, layer controls, and evidence;
- loading, error, stale, and mobile layouts are covered.

## Working protocol

For each coding request:

1. Read the relevant architecture/agent documents and inspect the existing implementation.
2. State the scope, assumptions, integration impact, and exact files to change.
3. Make the smallest correct change. Do not refactor unrelated code.
4. Preserve existing work; the working tree may contain changes created by other teammates.
5. Do not modify files owned by other team members unless the request explicitly authorizes it.
6. Add/update tests and run appropriate commands.
7. Report changed files, validation results, remaining assumptions, and required decisions from Jay/team owners.
8. Prefer a small, independently reviewable Git commit after a coherent feature is complete.

## Never do these things

- Do not implement risk rule logic in UI code.
- Do not replace the rule engine with an LLM.
- Do not generate/cite imaginary official sources.
- Do not silently invent API fields when a contract is incomplete.
- Do not use latitude/longitude in the wrong order for GeoJSON.
- Do not let a map marker or productive PFZ card visually contradict an `UNSAFE` verdict.
- Do not hide data staleness or agent failure.
- Do not make a broad unrelated refactor during a focused task.
- Do not commit secrets, API keys, or local environment files.

## Standard implementation-task response format

Before edits, respond with:

```text
Scope:
Assumptions:
Files to change:
Verification plan:
```

After edits, respond with:

```text
Implemented:
Files changed:
Verification:
Safety/contract notes:
Open questions or handoffs:
```

## Current task placeholder

The active task will be supplied by Adeey. Treat all instructions above as persistent project constraints unless the active task explicitly and safely changes them.
