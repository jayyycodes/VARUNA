# Adeey — Lead Experience & Integration Architect

**Project:** VARUNA / ORCA — Agentic Marine Intelligence for India's Coastline  
**SIH problem:** SIH26176 (ISRO / Department of Space)  
**Document purpose:** Define Adeey's ownership, architectural decisions, interfaces, acceptance criteria, and execution plan.  
**Repository assessed:** 6 September 2026

---

## 1. Your role in one sentence

You are the **Lead Experience & Integration Architect**: the engineer responsible for turning specialist-agent outputs into a trustworthy, fast, understandable coastal decision product — a response a fisherman or authority can act on because its map, evidence, uncertainty, and citations agree.

The existing README formally assigns you the **Visualization/Reporting Agent**, the full **React + Leaflet frontend**, and joint ownership of the **RAG retrieval-to-generation loop**. The architecture role below makes the boundaries explicit: you do not own weather science, PFZ ranking, legal source collection, geospatial boundary correctness, or the safety verdict rule itself. You own the system contract that ensures those outputs become coherent and safely presented to a human.

### Title options for a pitch or team slide

- **Best technical title:** Lead Experience & Integration Architect
- **Short team title:** Frontend & Explainability Architect
- **SIH-friendly title:** Decision Intelligence & Visualization Lead

Use the first title when discussing architecture with judges; it accurately communicates that the frontend is a safety-critical integration surface, not merely styling.

---

## 2. What the repository actually contains today

This repository is an **architecture scaffold**, not yet a running end-to-end application.

| Area | Current state | Architectural implication for Adeey |
|---|---|---|
| `backend/schemas/envelope.py` | `AgentEnvelope` and `RiskVerdict` Pydantic models are implemented. | This is the only enforceable shared API contract. Build outward from it, but close its gaps before frontend work is coupled to it. |
| `agents/*/*_agent.py` | Eight agents exist as class skeletons; every operation raises `NotImplementedError`. | Use typed mock fixtures first. Do not wait for each agent to be live to build the experience. |
| `backend/main.py` | Absent, although the README references it. | There is no HTTP API, route, auth boundary, or orchestration entry point to integrate with yet. |
| `frontend/` | Absent, although the README assigns it to you. | You need to establish the frontend foundation and its API client contract. |
| `backend/db/`, `backend/gateway/`, `backend/utils/` | Package placeholders only. | PostGIS, Redis, AI gateway, session/context, and operational concerns are design intentions, not code. |
| `data/etl/`, `eval/`, `infra/`, `docs/` | Referenced by README but absent. | Treat them as planned deliverables; do not claim they are implemented. |
| `docker-compose.yml` | Starts only PostGIS and Redis with development credentials. | It is useful local infrastructure, but does not start the FastAPI service or frontend. |

### Consequence

The best immediate contribution is not a visually polished screen against unstable JSON. It is a **versioned, testable final-response contract plus realistic fixtures**, then a frontend that renders success, degraded, and unsafe cases predictably.

---

## 3. System map and your architectural boundary

```text
User (any language)
        │
        ▼
translate_in ──► API / Planner ──► domain agents in parallel
                                      │
       ┌─────────── weather ──────────┼────────── marine/PFZ ──────────┐
       │                              │                                  │
       └──────── geofence ────────────┴──────────── RAG ────────────────┘
                                      │
                                      ▼
                         Risk rule engine (deterministic)
                                      │
                                      ▼
                ADEEY'S RESPONSE BOUNDARY / Visualization Agent
       ┌──────────────────────┬─────────────────────┬──────────────────┐
       │ Response contract    │ Evidence projection  │ Map/chart spec   │
       │ safe explanation     │ citation provenance  │ presentation     │
       └──────────────────────┴─────────────────────┴──────────────────┘
                                      │
                                      ▼
                      ADEEY'S REACT + LEAFLET CLIENT
              chat • map • verdict • evidence • source freshness
                                      │
                                      ▼
                              translate_out / user
```

### You own

1. The canonical **final response DTO** sent from backend to client.
2. Conversion of domain data into explicit, valid **GeoJSON FeatureCollections** and render-safe layer metadata.
3. A claim/evidence/citation model that lets a user inspect *why* a result was produced.
4. Safe natural-language rendering that never extends beyond deterministic evidence and retrieved source material.
5. The frontend information architecture: chat, map, verdict, layer controls, evidence panel, errors, stale-data cues, and mobile usability.
6. Frontend-backend contract tests, mock scenarios, visual regression/manual acceptance checks, and groundedness checks at the presentation boundary.
7. The RAG answer projection with Jay after Prapti provides indexed source chunks: citation display, unsupported-claim rejection, and UI behavior for insufficient evidence.

### You influence, but do not own

| Boundary partner | Their authority | Your responsibility at the boundary |
|---|---|---|
| Jay — Planner/API | Intent routing, state machine, final endpoint, session behavior | Specify response versioning, streaming/partial-result behavior, and frontend error semantics. |
| Jaish — Risk and Marine | PFZ score and deterministic safety rules | Render rule traces faithfully; reject an explanation that contradicts or exceeds a trace. |
| Vedant — Geofence/Route | Geometry validity, distance, restricted-zone logic, routes | Define feature/layer conventions; never reinterpret a geo status in the client. |
| Cbum — Weather | Source retrieval, normalization, freshness and cache state | Display source freshness, units, degraded status, and confidence without fabricating precision. |
| Prapti — RAG data | Source PDF collection, chunking, embeddings, retrieval corpus | Make citation IDs, excerpts, document metadata, and absent-evidence states usable in the product. |

---

## 4. The non-negotiable architecture principles you should champion

### 4.1 Presentation cannot make decisions

`SAFE`, `CAUTION`, and `UNSAFE` must originate only from `RiskVerdict`. The UI may choose color, wording, ordering, and accessibility treatment; it must not calculate or upgrade/downgrade a verdict from weather values.

### 4.2 Every displayed claim is traceable

A statement such as “Avoid departure: waves exceed the small-craft threshold” must link to a structured rule check, source, timestamp, and threshold version. A regulation explanation must link to a retrieved document chunk. If no evidence exists, say **“Not enough verified data to make this claim.”**

### 4.3 Degraded is a first-class outcome

`status="degraded"` is not a quiet warning. A partial answer must name missing/stale domains, reduce confidence visibly, avoid an unqualified safety statement, and show the data timestamp. For safety questions, a missing risk-critical input should result in an indeterminate/escalation presentation unless the Risk Agent supplies an explicit verdict policy.

### 4.4 GeoJSON is data, not UI state

Backend produces valid WGS84 (`EPSG:4326`) features with stable IDs and semantic properties. The frontend maps semantic layer types to visual styles. Do not have Leaflet-specific objects cross the API boundary.

### 4.5 The user needs hierarchy, not an information dump

Answer in this order: **verdict → required action → top reasons → map context → evidence and sources → details**. On a small boat or a mobile device, that hierarchy is a safety requirement.

### 4.6 Explicit uncertainty earns trust

Confidence is not a decoration. Explain whether it reflects stale data, partial sources, coarse location, forecast horizon, or unavailable geometry. Avoid false precision such as `0.87` in the UI; display calibrated bands (High / Medium / Low) with a reason.

---

## 5. Contract assessment: current strengths and gaps

`AgentEnvelope` is a good start because it standardizes agent name, run correlation, state, data, confidence, source, timestamp, thresholds, and an error message. Its flexible `data: dict[str, Any]`, however, is suitable for early scaffolding only.

### Gaps that should be resolved before production integration

| Gap | Why it matters | Recommended decision |
|---|---|---|
| No API response schema | Frontend will become coupled to undocumented nested dicts. | Add a dedicated, versioned `UserResponseV1` Pydantic model. |
| No response schema version | A later agent change can silently break the client. | Include `schema_version: "1.0"`; make incompatible changes a new major version. |
| Free-form agent data | Fields/units can drift between producers. | Create typed domain payload models or validate adapters before the visualization layer. |
| One `source: str` | A composite response has multiple sources; one string loses provenance. | Use per-claim or per-feature citations with IDs, URL/document metadata, retrieval time, and source time. |
| No freshness/staleness model | `timestamp` is ambiguous: fetched, generated, or forecast-valid? | Include `observed_at`, `retrieved_at`, `valid_from`, `valid_to`, and `age_minutes` where relevant. |
| Three-state agent status only | No clear user-level state for insufficient information. | Keep agent status as-is initially; introduce `decision_status: complete | degraded | indeterminate` in final output. |
| `RiskVerdict` lacks threshold version | Historic decisions cannot be reproduced after rule updates. | Add `threshold_version` and references in `rule_trace`. |
| No units/coordinate reference | Leaflet could render wrong scales or styles. | Require SI units and WGS84 longitude/latitude positions; document that GeoJSON order is `[longitude, latitude]`. |
| No feature identity/layer semantics | Frontend cannot reliably toggle, select, or update map entities. | Require `feature.id`, `layer_id`, `layer_type`, `severity`, and `z_index`. |
| No security or audience policy | Raw operational data/error messages may be exposed. | Final DTO must be an allow-list projection; do not serialize internal agent envelopes directly. |

---

## 6. Canonical final response contract (proposed v1)

The Planner should pass internal outputs to `VisualizationAgent`; the visualization layer projects them to this final DTO. The browser receives only this DTO, never raw internal envelopes or prompt/tool traces.

```json
{
  "schema_version": "1.0",
  "query_run_id": "uuid",
  "session_id": "opaque-id",
  "generated_at": "2026-09-06T10:30:00Z",
  "decision_status": "complete",
  "summary": {
    "headline": "CAUTION — delay departure until conditions improve.",
    "verdict": "CAUTION",
    "confidence_band": "medium",
    "confidence_reason": "Wave forecast is current; lightning feed is unavailable.",
    "action": "Check the next INCOIS bulletin before leaving."
  },
  "claims": [
    {
      "id": "claim-wave-001",
      "text": "Forecast wave height is 2.8 m, above the 2.5 m small-craft threshold.",
      "kind": "risk_rule",
      "evidence_ids": ["evidence-wave-001"],
      "citation_ids": ["source-incois-001"]
    }
  ],
  "map": {
    "viewport": {"center": [73.3, 17.0], "zoom": 8},
    "layers": [
      {
        "id": "hazards",
        "type": "hazard_zone",
        "label": "High-wave area",
        "visible_by_default": true,
        "feature_collection": {"type": "FeatureCollection", "features": []}
      }
    ]
  },
  "evidence_panel": {
    "rule_trace": [],
    "data_freshness": [],
    "missing_inputs": []
  },
  "citations": [
    {
      "id": "source-incois-001",
      "title": "INCOIS Ocean State Forecast",
      "publisher": "INCOIS",
      "url": "https://...",
      "published_at": "2026-09-06T00:00:00Z",
      "accessed_at": "2026-09-06T10:29:00Z",
      "excerpt": "Short, relevant source excerpt only."
    }
  ],
  "notices": [],
  "degradation": null
}
```

### Required enum policy

| Field | Allowed values | UI rule |
|---|---|---|
| `summary.verdict` | `SAFE`, `CAUTION`, `UNSAFE`, `UNKNOWN` | `UNKNOWN` never receives safe/unsafe color semantics. |
| `decision_status` | `complete`, `degraded`, `indeterminate`, `error` | `indeterminate` must lead with missing safety data and escalation guidance. |
| `claims.kind` | `risk_rule`, `observation`, `forecast`, `geofence`, `recommendation`, `regulation` | Regulation and recommendation claims require citations; risk-rule claims require rule trace evidence. |
| `map.layers[].type` | `pfz`, `hazard_zone`, `geofence`, `route`, `user_location`, `advisory_area` | Styling comes from a client-side allow-list; unknown types are not rendered silently. |
| `confidence_band` | `high`, `medium`, `low`, `unknown` | Never render a raw float as a decision guarantee. |

### GeoJSON conventions

- Geometry is RFC 7946 GeoJSON in WGS84. Coordinate arrays are `[longitude, latitude]`, never `[lat, lon]`.
- Every feature has a stable string `id`; do not use array position as identity.
- Every visible feature has `properties.layer_id`, `title`, `severity`, `source_ids`, `observed_at`, and `valid_to` when applicable.
- Geometry must be validated server-side: valid polygon rings, no coordinate outside longitude `[-180, 180]`/latitude `[-90, 90]`, and reasonable coordinate count limits.
- PFZ suitability and safety are different concepts. A productive zone cannot be styled or worded as a safe zone unless supported by Risk output.
- Do not expose raw restricted-boundary geometry if access policy says it is sensitive; serve generalized geometry if required.

---

## 7. Explanation safety design

The README permits an LLM only to explain an already-computed result. Your implementation should make unsafe generation structurally difficult.

### Safe generation pipeline

1. **Build an evidence packet** from `RiskVerdict.rule_trace`, allowed weather/marine/geofence fields, and retrieved RAG passages.
2. **Render deterministic statements first** for verdict, measured value, comparator, threshold, action, freshness, and unavailable inputs.
3. If an LLM is used, ask it to reorganize or translate only the evidence packet; demand structured output containing `claim_id` references for every sentence.
4. **Validate every sentence**: each claim must reference an allowed evidence or citation ID. Reject/replace ungrounded sentences with deterministic text.
5. Render citations and source timestamps adjacent to expandable evidence, not hidden behind a generic “AI says” label.

### Do not allow the explanation layer to

- derive a verdict, change a severity, or reinterpret a rule;
- describe future safety beyond the source validity window;
- claim a regulation unless a retrieved authoritative source supports it;
- turn absent weather, boundary, or PFZ information into reassurance;
- hide conflict between sources; show the conflict and conservative action instead;
- reveal internal prompts, credentials, raw exceptions, or model provider traces.

### Recommended deterministic template

```text
{VERDICT} for {location} during {time window}.
Recommended action: {action}.
Key reason(s): {one to three trace-backed reasons}.
Data status: {freshness and missing-input disclosure}.
```

This template is the reliable baseline for the demo and offline/degraded mode. An LLM is optional enhancement, never a dependency for safety communication.

---

## 8. Frontend architecture

### Suggested structure

```text
frontend/
├── src/
│   ├── app/                 # routing, providers, app shell
│   ├── api/                 # typed HTTP client and response validation
│   ├── features/
│   │   ├── query/           # chat input, location/time capture, history
│   │   ├── decision/        # verdict card, actions, notices
│   │   ├── map/             # Leaflet map, layer adapters, legends
│   │   ├── evidence/        # rule checks, freshness, citations
│   │   └── advisory/        # RAG answer and source reader
│   ├── components/          # reusable accessible primitives
│   ├── contracts/           # generated/shared DTO types and validators
│   ├── fixtures/            # versioned mock response scenarios
│   ├── styles/              # design tokens; map-safe color system
│   └── test/
├── public/
└── README.md
```

### State ownership

| State | Owner | Notes |
|---|---|---|
| Current request, user-selected location/time | Query feature | Keep query intent separate from response. |
| Final response DTO | Query/cache layer | Immutable server result keyed by `query_run_id`; do not mutate it based on UI toggles. |
| Visible layers, selected feature, panel open state | Map/UI feature | Ephemeral presentation state only. |
| Session conversation context | Backend/Redis | Client may display history, but the backend remains authoritative. |
| User location permission | Browser + query feature | Ask explicitly; provide manual location fallback. |
| Source/citation selection | Evidence feature | Read-only projection of final response. |

### Rendering flow

1. Submit normalized query with explicit location and time window.
2. Show a bounded loading state: “Checking weather, marine conditions, and boundaries.”
3. Validate the returned DTO at the API boundary. If invalid, show a safe generic error and log the contract failure.
4. Render the verdict and action before map detail.
5. Add only allow-listed map layers; draw user location and relevant layers.
6. Make each headline reason selectable to open the linked rule/evidence item and map feature where applicable.
7. Show source time, response time, missing inputs, and degraded state without burying them in a tooltip.

### Visual language

- Do not use red/green alone. Pair color with text, icon, and pattern; ensure adequate contrast.
- Reserve severe red for `UNSAFE`; use amber for `CAUTION`, and a distinct neutral state for `UNKNOWN` / `indeterminate`.
- Productive PFZ styling should be blue/teal; it must remain visually distinct from risk severity.
- A map legend is mandatory whenever dynamic overlay categories are visible.
- Use concise field-friendly language. “Do not depart” is clearer than “adverse maritime conditions observed.”
- Support mobile first: a map uses height efficiently, panels are collapsible, and critical action is visible without scrolling.

---

## 9. API and integration handshake with Jay

Agree on these before either side treats integration as complete.

| Topic | Decision required | Acceptance rule |
|---|---|---|
| Endpoint | `POST /v1/query` (recommended) and optional `GET /v1/query-runs/{id}` | Endpoint returns `UserResponseV1` or documented async/polling state. |
| Input | text, lat/lon or named location, time window, locale, session ID | Invalid/missing location produces a clear prompt, not an invented coordinate. |
| Correlation | `query_run_id` across planner, envelopes, logs, and client | Every visible response can be traced to a run ID. |
| Timeouts | individual agent timeout and whole-request budget | UI receives partial/degraded result or a declared timeout state, not an infinite spinner. |
| Partial results | polling/SSE vs single final response | Pick one for MVP; do not simulate streaming with inconsistent payload shapes. |
| Error taxonomy | validation, unavailable, timeout, internal | API never serializes a stack trace; frontend maps codes to plain-language actions. |
| Versioning | contract version in every response | Client rejects incompatible major versions gracefully. |
| Locale | response language and source language fields | Translation never changes underlying evidence IDs or numeric values. |

### Request shape recommendation

```json
{
  "text": "Can I go fishing tomorrow morning?",
  "location": {"lat": 9.9312, "lon": 76.2673},
  "time_window": {"start": "2026-09-07T06:00:00+05:30", "end": "2026-09-07T12:00:00+05:30"},
  "locale": "en-IN",
  "session_id": "optional-opaque-id"
}
```

Use ISO-8601 timestamps with offsets. Never pass ambiguous local date strings alone for safety forecasts.

---

## 10. Scenario fixtures you should own

Create versioned JSON fixtures before real agents are wired. They are the fastest way to de-risk frontend and contract integration.

| Fixture | Expected UI behavior |
|---|---|
| `safe_complete.json` | Green/positive verdict plus sources, current conditions, normal layers. |
| `caution_wave_threshold.json` | Amber action card; a selected reason links exactly to wave measurement and threshold in the trace. |
| `unsafe_cyclone_or_lightning.json` | Prominent do-not-depart action; no PFZ recommendation can visually override it. |
| `geofence_restricted.json` | Restricted geometry and reason; report regulation source when available. |
| `pfz_productive_but_unsafe.json` | Displays zone productivity but clearly prevents it from being interpreted as a departure recommendation. |
| `weather_stale_or_missing.json` | Degraded/indeterminate banner, timestamps, missing data list, conservative action. |
| `rag_cited_answer.json` | Every regulation claim expands to source document/chunk evidence. |
| `rag_insufficient_evidence.json` | States inability to verify and offers a source/authority path; no generated legal answer. |
| `invalid_geometry.json` | Client safely skips bad layer, retains decision panel, records contract violation. |
| `multilingual_output.json` | Text changes locale while quantities, verdict, claim IDs, and citations stay identical. |

Each fixture must be usable in unit tests, Storybook/component previews if adopted, and demo rehearsal. This makes your work demonstrable before external APIs become reliable.

---

## 11. Quality gates and test strategy

### Contract tests

- Pydantic/OpenAPI contract test between backend output and frontend validator.
- Snapshot each fixture against the v1 schema.
- Reject an unknown verdict, map layer type, claim kind, malformed GeoJSON, missing claim evidence, or citation-less regulation claim.
- Test coordinate order deliberately using a known Kochi/Visakhapatnam point so `[lat, lon]` mistakes are caught.

### Safety and groundedness tests

- For every `UNSAFE` and `CAUTION` fixture, check that headline text is supported by a rule trace.
- Check that no response containing missing critical safety input says “safe to go” without a Risk Agent-issued verdict policy.
- Check every generated/rendered claim has one or more `evidence_ids`; all cited IDs resolve.
- Check threshold values, units, comparator, and rule trace agree exactly.
- Check a productive PFZ never changes `UNSAFE` into a favorable overall recommendation.

### UI and accessibility tests

- Keyboard access to map alternatives, layer controls, citations, and evidence panel.
- Screen-reader labels for severity, source freshness, and map meaning; never encode safety by color alone.
- Mobile layout at common small-device width; no critical verdict/action hidden below the map.
- Empty, loading, timeout, error, and degraded states.
- Legend, unit display, time zone, and data-age display for every active layer.

### Performance targets for MVP

| Metric | Target | Reason |
|---|---|---|
| Initial app shell | usable on moderate mobile connection | The visual shell should not wait for map tiles or all agents. |
| Query feedback | loading acknowledgement immediately | Users should know their safety query is being processed. |
| Map feature count | cap/generalize large features | Prevent boundary/PFZ data from freezing mobile browsers. |
| Final render | render verdict before optional charts/layers | Primary decision must not wait for embellishments. |
| Payload | avoid raw source documents/agent internals | Better privacy, performance, and stable boundaries. |

---

## 12. Delivery plan

### Phase A — establish the contract (first priority)

1. Align with Jay on the v1 final response schema and endpoint behavior.
2. Add typed models for final response, citations, evidence, map layers, and errors.
3. Define a clear `UNKNOWN`/`indeterminate` safety policy with Jaish and Jay.
4. Build the ten mock fixtures above and validate them in CI/local tests.
5. Document the GeoJSON and timestamp conventions in one canonical location.

**Exit criterion:** the planner can return a mock response that the frontend validates without relying on agent-specific internal dictionaries.

### Phase B — make the decision experience real

1. Scaffold React + TypeScript application and typed API client.
2. Implement verdict/action card, freshness notices, evidence panel, citations, and responsive map shell.
3. Build Leaflet layer adapters for PFZ, hazard, geofence, route, and user location.
4. Implement visual distinction between productivity, restriction, and risk.
5. Connect fixtures, then the mock planner endpoint.

**Exit criterion:** all core scenarios can be demoed end-to-end with no real external API dependency.

### Phase C — connect live domains safely

1. Integrate real AgentEnvelope adapters one domain at a time.
2. Add stale/partial agent behavior and data-age displays.
3. Wire RAG retrieval-generation output only after citation IDs and source metadata are stable.
4. Add contract tests for real planner responses and coordinate with owners when violations occur.
5. Instrument client-visible failures with `query_run_id` and safe operational telemetry.

**Exit criterion:** a live safety query produces an evidence-backed, traceable response; one unavailable source creates a clear degraded state rather than a broken page.

### Phase D — demo hardening

1. Run the scripted scenarios against demo data/cache and capture fallback behavior.
2. Test slow network, empty response, malformed geometry, stale forecast, and partial service failure.
3. Rehearse a 90-second explanation: query → verdict → map → why panel → citations.
4. Prepare one deliberate “we refuse to overclaim” scenario; it demonstrates engineering maturity to judges.

**Exit criterion:** no screen shown in the demo can contradict the deterministic verdict or lack an explanation for user-visible risk information.

---

## 13. Key risks and decisions to force early

| Risk | Likely failure | Your architectural response |
|---|---|---|
| External data inconsistency | Weather/PFZ feeds disagree or arrive stale. | Surface age/source/conflict; request conservative risk policy; never hide the discrepancy. |
| LLM hallucination | Fluent explanation invents a regulation or safety rationale. | Evidence-ID validation and deterministic fallback templates. |
| Geometry mistakes | Lat/lon swap or invalid polygon places hazard in the wrong sea. | Contract validation, known-location tests, server-side geometry validation, explicit GeoJSON conventions. |
| Productive vs safe confusion | User sees PFZ highlight as permission to travel. | Separate layers/colors/labels and let risk verdict dominate the layout. |
| API/contract drift | Agent payload changes break client during integration. | One versioned DTO, fixtures, CI contract tests, no raw `dict` leakage. |
| Demo API outage | External service fails at presentation time. | Cached fixture/demo mode labeled with data timestamp; degraded UX tested beforehand. |
| Mobile field conditions | Slow network, sunlight, low digital literacy. | Mobile-first hierarchy, concise action language, progressive loading, no color-only meaning. |
| Multilingual ambiguity | Translation changes a technical threshold or severity. | Keep verdict/enums/numerics and evidence IDs canonical; translate approved presentation strings only. |

---

## 14. Definition of done for your ownership

Your component is done for MVP when all of the following are true:

- [ ] A documented `UserResponseV1` is approved with Jay and used by the API/client boundary.
- [ ] The UI can render `SAFE`, `CAUTION`, `UNSAFE`, `UNKNOWN`, complete, degraded, indeterminate, loading, and error states.
- [ ] Each safety verdict visibly includes an action, 1–3 trace-backed reasons, data freshness, and accessible evidence.
- [ ] Leaflet renders valid PFZ, hazard, geofence, and route GeoJSON with legend and accessible alternatives.
- [ ] PFZ productivity is never visually or linguistically confused with safe navigation.
- [ ] Every regulation/RAG claim has a resolvable citation; unsupported claims are not displayed as facts.
- [ ] Explanations cannot exceed deterministic risk traces or retrieved evidence.
- [ ] Mock fixture tests cover success, unsafe, partial/stale, geofence, RAG, malformed-data, and mobile states.
- [ ] API validation, coordinate order, units, timestamps, and schema version are tested.
- [ ] A demo can survive at least one source failure and explain that limitation honestly.

---

## 15. Your judge-facing architectural narrative

> “My role is Lead Experience & Integration Architect. VARUNA has several specialist agents, but a multi-agent system is only trustworthy if its final answer is coherent and auditable. I designed the response boundary between those agents and the user: the Risk engine remains deterministic, the map uses validated GeoJSON, every displayed claim links to an evidence trace and source, and degraded data is disclosed rather than hidden. The React and Leaflet interface prioritizes the operational decision — whether to go, where, and why — while keeping productivity, safety, regulations, and uncertainty distinct. That makes the system explainable enough for real coastal decision-making, not just a chatbot with a map.”

---

## 16. First conversations to schedule with the team

1. **Jay (30 minutes):** approve final response DTO, endpoint/state model, session ID, timeouts, and schema versioning.
2. **Jaish (20 minutes):** agree the exact `RiskVerdict.rule_trace` structure, threshold source/version, and indeterminate policy.
3. **Vedant (20 minutes):** set GeoJSON geometry, status/severity, feature-ID, coordinate order, and geometry validation conventions.
4. **Cbum (15 minutes):** standardize weather units, forecast-valid time, retrieval time, cache age, and unavailable-source representation.
5. **Prapti (20 minutes):** specify citation/document/chunk metadata and the UI-safe excerpt policy; align on RAG insufficient-evidence behavior.

These conversations are high leverage because they convert the README's component-level intent into contracts that can be implemented independently without costly late integration rework.

---

## 17. Final role statement

Adeey is not simply “the person building the frontend.” You are the engineer who owns the **human-trust boundary** of VARUNA: the contract, evidence, geospatial rendering, explanation safeguards, and interaction design that turn distributed AI and environmental data into a decision a person can verify and safely use.

