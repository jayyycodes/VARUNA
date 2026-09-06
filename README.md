# Varuna (ORCA) — Agentic Marine Intelligence for India's Coastline

**Smart India Hackathon 2026 — Problem Statement SIH26176**
*ORCA: Marine EcOsystem Reasoning with Collaborative Agents*
Organization: ISRO / Department of Space

---

## 1. What This Is

A conversational, multi-agent AI platform that lets fishermen, coastal
authorities, and maritime operators ask natural-language questions about
marine conditions — and get evidence-backed, explainable answers with
maps and citations, not guesses.

> *"ChatGPT for the ocean — but connected to real satellite, marine, and
> weather data, and capable of making decisions on a map."*

The three workflows we're building end-to-end:
1. **"Where should I fish?"** → PFZ + SST + chlorophyll + weather + distance → ranked zones on a map
2. **"Can I go out tomorrow?"** → waves + wind + tide + cyclone + lightning → safety verdict + explanation
3. **"How do I get there safely?"** → hazards + boundaries + conditions → a route on the map

Full technical proposal: see `docs/ORCA_Proposal.pdf` (add this file when available).

---

## 2. Architecture at a Glance

```
USER QUERY (any language)
      |
      v
[ translate_in() wrapper ]  <- NOT an agent, just I/O transformation
      |
      v
PLANNER / ORCHESTRATOR AGENT  (owner: Jay)
      |
      |------------+-------------+--------------+
      v            v             v              v
  WEATHER       MARINE &      GEOFENCING      RAG/ADVISORY
  AGENT         FISHING       AGENT           AGENT
  (Cbum)        AGENT         (Vedant)        (Prapti + Jay/Adeey)
                (Jaish)
      |            |             |              |
      +------------+-------------+--------------+
                   v
           RISK ASSESSMENT AGENT  (owner: Jaish)
      (rule-based threshold engine — NOT the LLM —
       computes the Safe/Caution/Unsafe verdict)
                   |
                   v
           ROUTE/NAVIGATION AGENT  (owner: Vedant, Tier 2)
                   |
                   v
        VISUALIZATION/REPORTING AGENT  (owner: Adeey)
    (map layers + chart + explanation + citations)
                   |
                   v
        [ translate_out() wrapper ]
                   |
                   v
        USER: text + map + "why" panel
```

**Core design principle:** the Planner never talks to raw external APIs
directly — only through agents, which own their data domain and caching.
If INCOIS goes down mid-demo, the Marine Agent falls back to its last
cached bulletin instead of the whole system failing.

---

## 3. Team & Responsibilities (Full Detail)

This is the authoritative task list. Each agent folder also has its own
`README.md` with the same content scoped to that agent — this table is
the bird's-eye view.

| Person | Owns | MVP Focus | Further-Stage Focus |
|---|---|---|---|
| **Jay** | Planner/Orchestrator Agent, API Gateway, FastAPI backend, AI Gateway (LiteLLM) integration | Intent parsing, parallel agent dispatch, LangGraph state machine, aggregation logic | Model routing, prompt caching, circuit breakers, full tracing, agent trajectory evals |
| **Adeey** | Visualization/Reporting Agent + full frontend (React, Leaflet, chat UI) | Response schema, GeoJSON generation, evidence/"why" panel, wiring frontend to backend | Groundedness evals, multi-language rendering, offline map tile caching, progressive rendering |
| **Jaish** | Marine & Fishing Intelligence Agent + Risk Assessment Agent | PFZ/SST/chlorophyll ingestion, zone ranking, **deterministic rule engine for safety verdicts**, golden-set construction | Historical trend analysis, golden-set CI automation, threshold versioning, groundedness checks on Risk explanations |
| **Vedant** | Geospatial/Geofencing Agent (+ Route/Navigation Agent, Tier 2) | PostGIS boundary loading, point-in-polygon checks, EEZ/IMBL/MPA status | Route-based checking, hazard-weighted pathfinding, offline-mode verification |
| **Cbum** | Weather Intelligence Agent | Open-Meteo/IMD/INCOIS integration, response normalization, Redis caching | Circuit breakers, fallback chains, per-source uptime tracking |
| **Prapti** | RAG/Advisory Agent — data layer | PDF collection (MFRAs, PFZ bulletins, advisories), chunking, embedding, vector DB load | Retrieval evals, re-embedding pipeline, additional regional sources |

**Shared/rotating responsibility (infra):** Docker Compose, the message
envelope schema, CI pipeline, and observability tracing are set up by Jay
on Day 0 since every agent depends on that shared contract existing
first. Prapti picks up CI/observability wiring once her RAG data-prep
work is done, since it becomes mechanical once the schema exists.

**Why this split:** Jay, Adeey, and Jaish absorb the highest-judgment,
most architecturally complex pieces (orchestration, the viz/frontend
contract, and the two ML-heavy agents). Vedant, Cbum, and Prapti each own
exactly one clearly-specced, self-contained agent with minimal
cross-team coordination needed to make progress — this keeps everyone
productive without bottlenecking on the harder pieces.

---

## 4. Repo Structure

```
varuna/
├── README.md                  <- you are here
├── backend/
│   ├── main.py                 (FastAPI entrypoint — TODO)
│   ├── gateway/                (AI Gateway / LiteLLM config — Jay)
│   ├── schemas/
│   │   └── envelope.py         (shared AgentEnvelope + RiskVerdict — READ THIS FIRST)
│   ├── db/                     (DB models/migrations — schema in docs/)
│   └── utils/
├── agents/
│   ├── planner/                (Jay)
│   ├── weather/                (Cbum)
│   ├── marine_fishing/         (Jaish)
│   ├── geofencing/             (Vedant)
│   ├── risk/                   (Jaish)
│   ├── route/                  (Vedant, Tier 2)
│   ├── rag_advisory/           (Prapti + Jay/Adeey)
│   └── visualization/          (Adeey)
│       Each folder has its own README.md with detailed MVP +
│       further-stage tasks, and an interface contract.
├── frontend/                   (Adeey — React + Leaflet + chat UI)
├── data/
│   ├── etl/                    (ingestion scripts per data source)
│   └── cache/                  (local dev cache, gitignored)
├── eval/
│   └── golden_set/             (30-50 historical query test cases — Jaish)
└── infra/                      (Docker Compose, CI config, observability setup)
```

---

## 5. Inter-Agent Message Contract

Every agent returns a response wrapped in the same envelope
(`backend/schemas/envelope.py::AgentEnvelope`) so the Planner can
aggregate without special-casing each agent, and so every claim shown to
the user traces back to a source + timestamp. **Read this file before
writing any agent code.**

```python
class AgentEnvelope(BaseModel):
    agent: str
    query_run_id: str
    status: Literal["success", "error", "degraded"]
    data: dict
    confidence: float
    source: str
    timestamp: datetime
    thresholds_used: dict | None = None
```

The Risk Agent additionally produces a `RiskVerdict` with a full
`rule_trace` — this is what powers the explainability/evidence panel and
must never be replaced by an LLM-generated guess.

---

## 6. Data Sources (All Free, Public)

| Need | Source | Used By |
|---|---|---|
| Potential Fishing Zones | INCOIS PFZ WebGIS | Marine & Fishing Agent |
| Sea Surface Temperature | ISRO MOSDAC / INCOIS | Marine & Fishing Agent |
| Chlorophyll Concentration | ISRO OCM-3 / MOSDAC | Marine & Fishing Agent |
| Waves, Currents, Ocean State | INCOIS Ocean State Forecast | Weather + Risk Agents |
| Cyclone / Lightning Alerts | IMD + MOSDAC | Weather Agent |
| General Weather | IMD / Open-Meteo | Weather Agent |
| Tide Predictions | INCOIS Tide Service | Route Agent |
| Maritime Boundaries (EEZ/IMBL) | Govt. shapefiles | Geofencing Agent |
| Marine Protected Areas | Protected Planet / India GIS | Geofencing Agent |
| Fishing Regulations / MFRAs | Govt. marine fishing regulation acts | RAG/Advisory Agent |

---

## 7. Tech Stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (Python) |
| Backend API | FastAPI |
| LLM | GTP-OSS 120B / LLAMA 70B versitile, tool-calling — **confirm final provider before build** |
| Spatial DB | PostgreSQL + PostGIS (Supabase) |
| Vector Store | pgvector / Chroma |
| Cache / Session | Redis |
| Map Frontend | Leaflet.js + India coastline/EEZ GeoJSON |
| Multilingual | Bhashini API / IndicTrans2 (MVP: English + 1 regional language) |
| Deployment | Docker Compose (demo) → documented Kubernetes path |

**Note:** if you see any tool referenced elsewhere (slides, docs) that
isn't on this list, it hasn't been confirmed — check with Jay before
building against it.

---

## 8. MVP Scope

**Tier 1 — build for real, non-negotiable:**
Planner + Weather + Marine/Fishing + Geofencing agents live with real
APIs; Risk Agent with a real rule-based threshold engine; evidence
panel in UI; map with PFZ markers + geofence overlay; 2-turn contextual
conversation.

**Tier 2 — thin but visible:**
Multilingual (English + 1 regional language); Route Agent (straight-line
vs. hazard-avoiding comparison); cyclone/lightning alerts (can be
synthetic, clearly labeled).

**Tier 3 — roadmap only, not built for the hackathon:**
Full 8-language support; real-time satellite ingestion pipelines;
production-scale multi-tenant deployment.

---

## 9. Production-Readiness Checklist

These aren't optional polish — they're what separates this from a
typical hackathon chatbot. See each agent's README for how these apply
to that specific agent.

- [ ] **Guardrail:** Risk Agent verdicts come from the rule engine, never the LLM
- [ ] **Guardrail:** RAG Agent answers are citation-grounded, no invented regulations
- [ ] **Optimization:** response caching (Redis), parallel agent dispatch, prompt caching
- [ ] **AI Gateway:** LiteLLM or Portkey — provider abstraction, rate limiting, cost tracking
- [ ] **Evals:** golden-set (30-50 queries), agent trajectory evals, retrieval evals, groundedness evals
- [ ] **Observability:** LangSmith/Langfuse tracing, Prometheus + Grafana metrics, alerting
- [ ] **Resilience:** circuit breakers, idempotent retries with backoff, graceful degradation ladder
- [ ] **Offline-first:** geofencing works fully offline (GPS + local polygons, no LLM needed)
- [ ] **Secrets management:** no hardcoded API keys, `.env` + `.gitignore` minimum
- [ ] **CI/CD:** unit tests (especially Risk Agent thresholds), golden-set evals run on every commit

---

## 10. Build Order

1. **Day 0:** Jay sets up repo, Docker Compose, message envelope schema
2. **Day 1:** Weather Agent (Cbum) + Geofencing Agent (Vedant) start on real data; Planner skeleton (Jay) starts against mocked agent responses
3. **Day 2:** Marine & Fishing Agent (Jaish) + Risk Agent rule engine (Jaish) built; Planner wired to real Weather + Geofencing agents
4. **Day 3:** Frontend shell + map (Adeey) against mocked JSON; Visualization Agent response schema finalized
5. **Day 4:** RAG data layer (Prapti) + retrieval-generation loop; Route Agent (Vedant) started
6. **Day 5:** End-to-end integration testing, golden-set eval run, observability dashboards wired, demo rehearsal

---

## 11. Setup

```bash
# TODO once backend/main.py and docker-compose.yml exist:
docker compose up -d          # Postgres + PostGIS + Redis
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

*(Environment variables, API keys, and DB migration steps to be added
once each is finalized — do not commit real keys, use `.env.example` as
a template.)*
