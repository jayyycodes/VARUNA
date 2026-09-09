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

Full technical proposal: see `Docs/ORCA_Proposal_Detailed.md`.

---

## 1.1 National Hackathon Target Queries (SIH26176 Alignment)

Varuna directly addresses the primary operational queries expected by the hackathon evaluation jury:

| # | Typical User Query | Responsible Agent(s) | Live Data & Evidence Sourced |
|---|---|---|---|
| 1 | **"Where is the nearest Potential Fishing Zone (PFZ) today?"** | Marine & Fishing Agent | INCOIS PFZ GeoJSON advisories, SST gradients, and Chlorophyll-a concentration ranked by proximity. |
| 2 | **"Is it safe to venture into the sea tomorrow morning?"** | Weather Agent + Risk Assessment Agent | Real-time wave height, swell period, wind speed, lightning alerts, evaluated against small-craft safety thresholds. |
| 3 | **"What are the tide, weather, and sea conditions near my fishing location?"** | Weather Agent + Marine Agent | Open-Meteo Marine API, INCOIS Ocean State Forecast (OSF), and tidal predictions for target coordinates. |
| 4 | **"Are there any lightning or cyclone alerts in my area?"** | Weather Agent | IMD RSMC cyclone bulletins, MOSDAC lightning feeds, and convective storm warnings. |
| 5 | **"Which regions show high chlorophyll concentration and favourable sea surface temperature?"** | Marine & Fishing Agent | ISRO OCM-3 / Sentinel-3 ocean color data + NOAA GHRSST / INSAT-3D thermal infrared SST. |
| 6 | **"What is the safest route for a fishing vessel considering weather and sea-state conditions?"** | Route / Navigation Agent | A* pathfinding over bathymetry grid avoiding restricted zones, land contours, and wave swell sectors. |
| 7 | **"Why has fish productivity declined in a particular coastal region?"** | Marine Agent + RAG Agent | Historical SST anomaly analysis, seasonal upwelling patterns, thermal stress, and overfishing regulation history. |
| 8 | **"Which fishing zones should be avoided due to hazardous marine conditions or geofencing restrictions?"** | Geofencing Agent + Risk Agent | PostGIS boundary checks against International Maritime Boundary Lines (IMBL), Marine Protected Areas (MPAs), and severe sea states. |

---

## 1.2 What Better We Have Done (Varuna's Competitive Edge)

Beyond answering baseline queries, Varuna introduces five critical architectural innovations:

1. **The "High-Fish / High-Death" Safety Gatekeeper**:
   - *The Problem*: Competitor systems blindly point fishermen to high-chlorophyll zones even when a 3-meter swell or cyclone is rolling in.
   - *Varuna's Edge*: Our Planner cross-correlates PFZ productivity with Weather & Geofencing before presenting it. If a prime fishing zone sits inside dangerous waters, the system strictly marks the expedition as **UNSAFE / CAUTION** and redirects to a sheltered alternative.

2. **International Maritime Boundary (IMBL) Pre-emption**:
   - *The Problem*: Indian fishermen frequently cross into Sri Lankan or Pakistani waters by accident, resulting in boat seizures and arrests.
   - *Varuna's Edge*: PostGIS spatial engine computes dynamic safety corridors with a **2 km Warning Buffer** and immediate **Restricted Flag** before crossing the IMBL, preventing international incidents.

3. **Deterministic Life-or-Death Safety Guardrail (Zero LLM Hallucination)**:
   - *The Problem*: General LLMs hallucinate numbers and can falsely assure a fisherman that "conditions seem pleasant."
   - *Varuna's Edge*: The safety verdict (`SAFE`, `CAUTION`, `UNSAFE`) is **100% computed by an auditable, deterministic Python rule engine** based on official INCOIS and IMD small-craft criteria. The LLM is strictly confined to explaining the verdict in plain conversational language.

4. **Verifiable Multi-Agent Evidence DAG & Audit Trail**:
   - *The Problem*: Black-box chatbots provide advice with no provenance.
   - *Varuna's Edge*: Every response includes an Evidence Trail linking to the exact satellite pass timestamp, buoy station ID, legal act section (e.g. *Maharashtra MFRA 1981*), and confidence score.

5. **Edge-First Offline Resilience**:
   - *The Problem*: Marine connectivity at sea is intermittent and fragile.
   - *Varuna's Edge*: PostGIS boundary checks run entirely locally without external network dependencies. If cloud satellite APIs timeout, the system gracefully falls back to local cached telemetry and pre-baked fixtures without crashing.

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

## 6. Real-Time Public Data Endpoints (All 100% Free)

Every agent consumes free, publicly accessible real-time feeds without paywalls:

| Domain | Sponsoring Body | Endpoint / Feed | Frequency | Used By Agent |
|---|---|---|---|---|
| **Waves, Swell & Wind** | Open-Meteo Marine | `https://marine-api.open-meteo.com/v1/marine` (hourly `wave_height,wave_period,swell_wave_height,wind_wave_height`) | Hourly Real-Time | Weather Agent |
| **Atmospheric Weather** | Open-Meteo Weather | `https://api.open-meteo.com/v1/forecast` (`wind_speed_10m,wind_gusts_10m,precipitation,lightning`) | Hourly Real-Time | Weather Agent |
| **Cyclone & Storm Bulletins** | IMD RSMC New Delhi | `https://rsmcnewdelhi.imd.gov.in/` (RSS bulletins & cyclone tracks) | Live Bulletins | Weather Agent |
| **Potential Fishing Zones (PFZ)** | INCOIS WebGIS / SAMUDRA | `https://incois.gov.in/portal/datainfo/pfz.jsp` (GeoJSON / Shapefiles) | Daily Advisories | Marine & Fishing Agent |
| **Sea Surface Temp (SST)** | NOAA ERDDAP / ISRO MOSDAC | `https://coastwatch.pfeg.noaa.gov/erddap/griddap/` (GHRSST 5km Indian EEZ) | Daily Satellite | Marine & Fishing Agent |
| **Chlorophyll-a Concentration** | Copernicus Marine / OCM-3 | Sentinel-3 OLCI / ISRO OCM-3 ocean color products | Daily Satellite | Marine & Fishing Agent |
| **Maritime Boundaries (EEZ/IMBL)**| MarineRegions.org v12 | Shapefiles / GeoJSON for India, Sri Lanka, Pakistan, Maldives EEZ | Static / High Precision | Geofencing Agent |
| **Marine Protected Areas (MPA)** | Protected Planet (WDPA) | WDPA Indian Marine Sanctuaries & National Parks GeoJSON | Static / Annual Update | Geofencing Agent |
| **Tide Predictions** | INCOIS Tide Service | INCOIS major coastal port tidal tables (hourly high/low tide) | Daily / Hourly | Route Agent |
| **Marine Regulations (MFRAs)** | Govt. State Gazetteers | Maharashtra MFRA 1981, Tamil Nadu MFRA 1983, Annual Monsoon Bans | Statutory Text | RAG / Advisory Agent |

> **Single-Command Local Seeding**: Run `python data/etl/setup_data.py` to automatically seed your local PostGIS and Redis environments with baseline spatial and telemetry data.

---

## 7. Tech Stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (Python) |
| Backend API | FastAPI |
| LLM | **Groq** (primary, e.g. `llama-3.3-70b-versatile`) + **Cerebras** (fallback/RAG, e.g. `llama3.1-70b`) — both free tier, routed via `backend/gateway/ai_gateway.py` |
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

### Day 0 — done by Jay before anyone else writes agent logic

1. Repo created, tasks assigned ✅
2. `docker compose up -d` — brings up Postgres+PostGIS and Redis (no custom
   image build needed, both use pre-built images from Docker Hub)
3. Verify Postgres is reachable and `infra/init.sql` ran automatically
   (check: `docker exec -it <postgres_container> psql -U varuna -d varuna -c '\dt'`
   — should list `users`, `conversations`, `messages`, `query_runs`,
   `agent_runs`, `risk_verdicts`)
4. Copy `.env.example` → `.env`, fill in `GROQ_API_KEY` and `CEREBRAS_API_KEY`
   (free signup at console.groq.com and cloud.cerebras.ai)
5. `pip install -r requirements.txt`
6. Sanity-check the AI Gateway: run one `call_llm("planner", [...])` call
   from a Python shell against Groq, confirm the Cerebras fallback path
   works by temporarily using a bad Groq key
7. **Message envelope schema — what "Day 0" actually means for this:**
   the schema itself (`backend/schemas/envelope.py`) is already written.
   Day 0's job is not to design it further — it's to make sure everyone
   has *read* it and agrees to return exactly this shape from their
   agent, since `agent_runs.output_data` in the DB and every downstream
   consumer (Risk Agent, Visualization Agent) depends on it staying
   consistent. Treat it as locked unless there's a real reason to change
   it — and if it changes, that's a message to the whole team, not a
   silent edit.
8. Push `.env.example` (never `.env`), confirm `.gitignore` is catching
   `.env` and `__pycache__/` before anyone commits
9. Share with the team: repo URL, "run `docker compose up -d` then read
   your agent's README" — that's the only onboarding needed

### Day 1 onward

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
