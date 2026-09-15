# Varuna (ORCA) — Agentic Marine Intelligence for India's Coastline

**Smart India Hackathon 2026 — Problem Statement SIH26176**
*ORCA: Marine EcOsystem Reasoning with Collaborative Agents*
Organization: ISRO / Department of Space

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![TypeScript](https://img.shields.io/badge/typescript-5.x-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 1. What This Is

A conversational, multi-agent AI platform that lets fishermen, coastal
authorities, and maritime operators ask natural-language questions about
marine conditions — and get evidence-backed, explainable answers with
maps and citations, not guesses.

> *"ChatGPT for the ocean — but connected to real satellite, marine, and
> weather data, and capable of making decisions on a map."*

The three workflows built end-to-end:
1. **"Where should I fish?"** → PFZ + SST + chlorophyll + weather + distance → ranked zones on a map
2. **"Can I go out tomorrow?"** → waves + wind + tide + cyclone + lightning → safety verdict + explanation
3. **"How do I get there safely?"** → hazards + boundaries + conditions → a route on the map

Full technical proposal: see `Docs/ORCA_Proposal_Detailed.md`.

---

## 1.1 National Hackathon Target Queries (SIH26176 Alignment)

Varuna directly addresses all 8 primary operational queries expected by the hackathon evaluation jury:

| # | Typical User Query | Responsible Agent(s) | Live Data & Evidence Sourced | Status |
|---|---|---|---|---|
| 1 | **"Where is the nearest Potential Fishing Zone (PFZ) today?"** | Marine & Fishing Agent | INCOIS PFZ GeoJSON advisories, SST gradients, Chlorophyll-a concentration ranked by proximity. | ✅ Live |
| 2 | **"Is it safe to venture into the sea tomorrow morning?"** | Weather Agent + Risk Assessment Agent | Real-time wave height, swell period, wind speed, lightning alerts, evaluated against small-craft safety thresholds. | ✅ Live |
| 3 | **"What are the tide, weather, and sea conditions near my fishing location?"** | Weather Agent + Marine Agent | Open-Meteo Marine API, INCOIS Ocean State Forecast (OSF), and tidal predictions for target coordinates. | ✅ Live |
| 4 | **"Are there any lightning or cyclone alerts in my area?"** | Weather Agent | IMD RSMC cyclone bulletins, MOSDAC lightning feeds, and convective storm warnings. | ✅ Live |
| 5 | **"Which regions show high chlorophyll concentration and favourable sea surface temperature?"** | Marine & Fishing Agent | ISRO OCM-3 / Sentinel-3 ocean color data + NOAA GHRSST / INSAT-3D thermal infrared SST. | ✅ Live |
| 6 | **"What is the safest route for a fishing vessel considering weather and sea-state conditions?"** | Route / Navigation Agent | A* pathfinding over bathymetry grid avoiding restricted zones, land contours, and wave swell sectors. | ✅ Live |
| 7 | **"Why has fish productivity declined in a particular coastal region?"** | Marine Agent + RAG Agent | Historical SST anomaly analysis, seasonal upwelling patterns, thermal stress, and overfishing regulation history. | ✅ Live |
| 8 | **"Which fishing zones should be avoided due to hazardous marine conditions or geofencing restrictions?"** | Geofencing Agent + Risk Agent | PostGIS boundary checks against International Maritime Boundary Lines (IMBL), Marine Protected Areas (MPAs), and severe sea states. | ✅ Live |

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

## 2. Architecture

```
USER QUERY (any language)
      |
      v
[ translate_in() wrapper ]  <- Bhashini / IndicTrans2 multilingual I/O
      |
      v
PLANNER / ORCHESTRATOR AGENT  (LangGraph state machine)
      |
      |--- asyncio.gather() parallel dispatch ---|
      v            v             v              v
  WEATHER       MARINE &      GEOFENCING      RAG/ADVISORY
  AGENT         FISHING       AGENT           AGENT
  (Open-Meteo   AGENT         (PostGIS +      (pgvector +
   + IMD RSMC)  (INCOIS PFZ    WDPA/IMBL)     statutory PDFs)
                + NOAA SST)
      |            |             |              |
      +------------+-------------+--------------+
                   v
           RISK ASSESSMENT ENGINE
      (deterministic rule engine — NOT the LLM —
       computes Safe/Caution/Unsafe verdict with
       9 versioned threshold rules)
                   |
                   v
           ROUTE/NAVIGATION AGENT
      (A* pathfinding with coastline collision
       detection + seaward arc deflection)
                   |
                   v
        VISUALIZATION/REPORTING
    (GeoJSON map layers + evidence panel +
     reasoning DAG + citations)
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

## 3. Team & Responsibilities

| Person | Owns | Status |
|---|---|---|
| **Jay** | Planner/Orchestrator Agent, API Gateway, FastAPI backend, AI Gateway (LiteLLM), Risk Assessment Engine | ✅ Complete |
| **Adeey** | Visualization/Reporting Agent + full frontend (React, Leaflet, chat UI, Executive Dashboard) | ✅ Complete |
| **Jaish** | Marine & Fishing Intelligence Agent + Risk Assessment rule engine | ✅ Complete |
| **Vedant** | Geospatial/Geofencing Agent + Route/Navigation Agent (A* pathfinding) | ✅ Complete |
| **Cbum** | Weather Intelligence Agent (Open-Meteo + IMD + INCOIS integration) | ✅ Complete |
| **Prapti** | RAG/Advisory Agent — PDF collection, chunking, embedding, pgvector search | ✅ Complete |

---

## 4. Repo Structure

```
varuna/
├── README.md                   <- you are here
├── backend/
│   ├── main.py                  FastAPI entrypoint (3 endpoints: /chat, /health, /v1/query)
│   ├── gateway/
│   │   ├── ai_gateway.py        LiteLLM multi-provider routing (Groq + Cerebras)
│   │   ├── circuit_breaker.py   11-service circuit breaker registry
│   │   ├── multilingual.py      Bhashini/LLM translation wrapper (EN, HI, MR, TA)
│   │   └── observability.py     LangSmith tracing integration
│   ├── routes/
│   │   ├── alerts.py            GET /api/alerts - marine alert feed
│   │   ├── analytics.py         GET /api/analytics/historical-trends
│   │   ├── fleet.py             GET /api/fleet - vessel tracking
│   │   └── route_planner.py     POST /api/route/plan - dual-route planning
│   └── schemas/
│       └── envelope.py          AgentEnvelope + RiskVerdict contracts
├── agents/
│   ├── planner/                 LangGraph orchestrator with parallel agent dispatch
│   ├── weather/                 Open-Meteo Marine + IMD RSMC + MOSDAC lightning
│   ├── marine_fishing/          INCOIS PFZ + NOAA GHRSST SST + chlorophyll
│   ├── geofencing/              PostGIS point-in-polygon (EEZ/IMBL/MPA/MWS)
│   ├── risk/                    Deterministic rule engine (9 versioned threshold rules)
│   ├── route/                   A* pathfinding + coastline collision + seaward deflection
│   └── rag_advisory/            pgvector HNSW search over statutory PDFs
├── frontend/                    React + Vite + Leaflet + Framer Motion
│   └── src/
│       ├── api/client.ts        VarunaApiClient with live/mock fallback
│       ├── features/
│       │   ├── chat/            Copilot chat + reasoning view
│       │   ├── map/             Leaflet MapCanvas with GeoJSON layers
│       │   ├── dashboard/       Executive dashboard with live telemetry
│       │   ├── fleet/           Fleet operations tracker
│       │   ├── routing/         Dual-route optimization view
│       │   ├── alerts/          Active marine alerts panel
│       │   ├── analytics/       Historical fishery trends
│       │   ├── decision/        Verdict card display
│       │   ├── evidence/        Evidence rail + bottom sheet
│       │   └── reasoning/       Agentic reasoning DAG visualization
│       ├── contracts/           UserResponseV1 TypeScript schema
│       ├── fixtures/            8 validated scenario fixtures
│       └── hooks/               useLocalization (EN/HI/MR/TA)
├── data/
│   ├── etl/                     INCOIS SAMUDRA PFZ ingestion + GeoJSON validation
│   ├── rag_documents/           Statutory PDFs (MFRA 1981, monsoon bans, etc.)
│   └── cache/                   Local dev cache (gitignored)
├── eval/
│   └── golden_set/              Query test cases for evaluation
├── tests/                       pytest suite (planner, agents, routes, observability)
├── Docs/                        Frontend test report, proposal docs
└── infra/
    ├── init.sql                 PostgreSQL schema (20 tables)
    └── 002_geofencing_schema.sql PostGIS spatial schema
```

---

## 5. Inter-Agent Message Contract

Every agent returns a response wrapped in the same envelope
(`backend/schemas/envelope.py::AgentEnvelope`) so the Planner can
aggregate without special-casing each agent, and so every claim shown to
the user traces back to a source + timestamp.

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

The Risk Assessment Engine additionally produces a `RiskVerdict` with a full
`rule_trace` containing 9 versioned threshold rules — this is what powers
the explainability/evidence panel and is **never** replaced by an LLM-generated guess.

---

## 6. Real-Time Public Data Endpoints (All 100% Free)

Every agent consumes free, publicly accessible real-time feeds without paywalls:

| Domain | Sponsoring Body | Endpoint / Feed | Frequency | Used By Agent |
|---|---|---|---|---|
| **Waves, Swell & Wind** | Open-Meteo Marine | `https://marine-api.open-meteo.com/v1/marine` | Hourly Real-Time | Weather Agent |
| **Atmospheric Weather** | Open-Meteo Weather | `https://api.open-meteo.com/v1/forecast` | Hourly Real-Time | Weather Agent |
| **Cyclone & Storm Bulletins** | IMD RSMC New Delhi | `https://rsmcnewdelhi.imd.gov.in/` | Live Bulletins | Weather Agent |
| **MOSDAC Lightning** | ISRO MOSDAC | Lightning density feeds | Real-Time | Weather Agent |
| **Potential Fishing Zones (PFZ)** | INCOIS SAMUDRA | `https://incois.gov.in/portal/datainfo/pfz.jsp` | Daily Advisories | Marine & Fishing Agent |
| **Sea Surface Temp (SST)** | NOAA ERDDAP / GHRSST | `https://coastwatch.pfeg.noaa.gov/erddap/griddap/` | Daily Satellite | Marine & Fishing Agent |
| **Chlorophyll-a Concentration** | Copernicus / OCM-3 | Sentinel-3 OLCI / ISRO OCM-3 ocean color | Daily Satellite | Marine & Fishing Agent |
| **INCOIS Buoy Telemetry** | INCOIS | Real-time buoy network data | Hourly | Marine & Fishing Agent |
| **Maritime Boundaries (EEZ/IMBL)** | MarineRegions.org v12 | Shapefiles / GeoJSON for India EEZ/IMBL | Static | Geofencing Agent |
| **Marine Protected Areas (MPA)** | Protected Planet (WDPA) | Indian Marine Sanctuaries & Parks GeoJSON | Static | Geofencing Agent |
| **Marine Regulations (MFRAs)** | Govt. State Gazetteers | Maharashtra MFRA 1981, TN MFRA 1983, Monsoon Bans | Statutory Text | RAG / Advisory Agent |

---

## 7. Tech Stack

| Layer | Choice | Status |
|---|---|---|
| Orchestration | LangGraph (Python) with parallel `asyncio.gather` dispatch | ✅ Live |
| Backend API | FastAPI with 3 core + 4 supplementary endpoints | ✅ Live |
| LLM Providers | **Groq** (primary) + **Cerebras** (fallback) — both free tier, routed via `backend/gateway/ai_gateway.py` with automatic failover | ✅ Live |
| Risk Engine | Deterministic Python rule engine with 9 versioned threshold rules (no LLM) | ✅ Live |
| Spatial DB | PostgreSQL + PostGIS (Supabase, 20-table schema) | ✅ Live |
| Vector Store | pgvector with HNSW indexing for RAG document search | ✅ Live |
| Cache / Session | Redis (graceful degradation if unavailable) | ✅ Live |
| Map Frontend | Leaflet.js + custom GeoJSON layers (PFZ, routes, geofences, MPAs) | ✅ Live |
| Frontend Framework | React 19 + Vite + TypeScript + Framer Motion | ✅ Live |
| Multilingual | LLM-based translation wrapper (EN, HI, MR, TA) | ✅ Live |
| Observability | LangSmith tracing + 11-service circuit breaker registry | ✅ Live |
| Deployment | Vercel (frontend) + Railway (backend) | 🚀 Ready |

---

## 8. Features Built

### Tier 1 — Core (All Complete ✅)
- ✅ Planner/Orchestrator with LangGraph state machine and parallel agent dispatch
- ✅ Weather Intelligence Agent (Open-Meteo Marine + IMD RSMC + MOSDAC lightning)
- ✅ Marine & Fishing Intelligence Agent (INCOIS PFZ + NOAA GHRSST SST + Chlorophyll-a)
- ✅ Geospatial/Geofencing Agent (PostGIS with EEZ/IMBL/MPA/MWS boundary checks)
- ✅ Risk Assessment Engine (deterministic rule engine with 9 versioned threshold rules)
- ✅ Evidence panel with rule traces, data freshness indicators, and citations
- ✅ Interactive map with PFZ markers, route overlays, and geofence boundaries
- ✅ Copilot chat with multi-turn conversational context and tab persistence

### Tier 2 — Extended (All Complete ✅)
- ✅ Multilingual support (English, Hindi, Marathi, Tamil) with dynamic UI localization
- ✅ Route/Navigation Agent (A* pathfinding with coastline collision detection + seaward arc deflection)
- ✅ RAG/Advisory Agent (pgvector HNSW search over statutory PDFs — MFRA 1981, monsoon bans)
- ✅ Regulatory intent detection (PROHIBITED/PERMITTED verdicts for legal queries)
- ✅ Active marine alerts panel with live backend feed
- ✅ Fleet operations tracker with vessel positions and compliance status
- ✅ Executive dashboard with real-time telemetry cards and system health
- ✅ Historical fishery trends and productivity anomaly analysis
- ✅ Agentic reasoning DAG visualization (4-step deterministic trace)

### Production Readiness
- ✅ **Guardrail:** Risk verdicts come from rule engine, never the LLM
- ✅ **Guardrail:** RAG answers are citation-grounded with statutory references
- ✅ **Caching:** Response and telemetry caching with Redis
- ✅ **AI Gateway:** LiteLLM multi-provider routing with automatic failover
- ✅ **Observability:** LangSmith tracing with 11-service circuit breaker registry
- ✅ **Resilience:** Circuit breakers, graceful degradation, offline geofencing
- ✅ **Secrets:** All API keys in `.env` (gitignored), `.env.example` provided
- ✅ **Tests:** pytest suite covering planner, agents, routes, and observability
- ✅ **Audit:** Query execution traces logged to Supabase `query_runs` + `risk_verdicts` tables

---

## 9. API Reference

### Core Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Primary chat endpoint — processes natural-language marine queries through the full agent pipeline |
| `POST` | `/v1/query` | V1 REST query endpoint (alias for /chat) |
| `POST` | `/v1/chat` | V1 Chat endpoint (alias for /chat) |
| `GET` | `/health` | Service health check with upstream circuit breaker status |
| `GET` | `/v1/health` | Health check alias |
| `GET` | `/api/health/upstream` | Detailed upstream circuit breaker monitoring |

### Supplementary Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/alerts` | Active marine alerts feed (cyclone, swell, lightning, regulatory) |
| `GET` | `/api/fleet` | Coastal fleet status and vessel positions |
| `GET` | `/api/analytics/historical-trends` | Historical fishery productivity anomaly analysis |
| `GET` | `/api/route/ports` | Coastal ports catalog for route planning |
| `POST` | `/api/route/plan` | Compute dual-route passage (safe corridor vs. direct baseline) |

### Chat Request Schema

```json
{
  "query": "Where is the nearest PFZ from Ratnagiri?",
  "locale": "en-IN",
  "session_id": "optional-session-id",
  "location": { "lat": 16.99, "lon": 73.28 },
  "time_window": {
    "start": "2026-09-14T00:00:00Z",
    "end": "2026-09-14T12:00:00Z"
  }
}
```

---

## 10. Setup & Deployment

### Local Development

```bash
# 1. Clone and install dependencies
git clone https://github.com/jayyycodes/VARUNA.git
cd VARUNA

# 2. Backend setup
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

# 3. Environment setup
cp .env.example .env
# Fill in GROQ_API_KEY, CEREBRAS_API_KEY, and POSTGRES_URL

# 4. Start infrastructure (PostgreSQL + PostGIS + Redis)
docker compose up -d

# 5. Start backend
uvicorn backend.main:app --reload --port 8000

# 6. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
# App runs at http://localhost:5173
```

### Production Deployment

**Backend → Railway/Render:**
```bash
# Start command:
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
Set all `.env` variables as environment variables in the Railway dashboard.

**Frontend → Vercel:**
- Root directory: `frontend`
- Framework: Vite
- Build command: `npm run build`
- Output: `dist`
- Environment variable: `VITE_API_URL=https://your-backend-url.railway.app`

---

## 11. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key for primary LLM provider |
| `CEREBRAS_API_KEY` | ✅ | Cerebras API key for fallback LLM provider |
| `POSTGRES_URL` | ✅ | PostgreSQL connection string (Supabase) |
| `POSTGRES_HOST` | ✅ | PostgreSQL host |
| `POSTGRES_PORT` | ✅ | PostgreSQL port (default: 5432) |
| `POSTGRES_DB` | ✅ | Database name |
| `POSTGRES_USER` | ✅ | Database user |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `REDIS_URL` | ❌ | Redis URL for caching (graceful fallback if missing) |
| `LANGSMITH_API_KEY` | ❌ | LangSmith tracing key |
| `LANGSMITH_PROJECT` | ❌ | LangSmith project name |
| `APP_ENV` | ❌ | `development` or `production` |
| `VITE_API_URL` | ✅ (prod) | Backend API URL for frontend (production only) |

> **Security:** Never commit `.env` files. Use `.env.example` as a template. All keys are gitignored.

---

## 12. Testing

```bash
# Run full Python test suite
python -m pytest tests/ -v

# TypeScript compilation check
cd frontend && npx tsc --noEmit

# Production build verification
cd frontend && npx vite build

# Backend health check
curl http://localhost:8000/health
```

---

## 13. License

MIT License — see `LICENSE` for details.

Built with 🌊 for Smart India Hackathon 2026 by Team Varuna.
