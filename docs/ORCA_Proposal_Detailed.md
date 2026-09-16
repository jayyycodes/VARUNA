# ORCA — Marine EcOsystem Reasoning with Collaborative Agents

**Smart India Hackathon 2026 — PS ID: SIH26176**  
**Organization:** ISRO / Department of Space  
**Document:** Proposed Solution & Technical Architecture — v1  
**Team:** 6 members  
**Purpose:** Internal team alignment  
**Prepared:** August 2026

---

## 1. Problem Statement

Fishermen, coastal authorities, and maritime operators need practical daily answers to questions such as:

- Where should I fish today?
- Is it safe to go out tomorrow?
- Which zones should I avoid?
- How can I reach a destination safely?

The underlying information required to answer these questions is distributed across systems such as **ISRO, INCOIS, and IMD**. Important data includes satellite Sea Surface Temperature (SST), chlorophyll concentration, weather forecasts, tides, cyclone alerts, maritime boundaries, and fishing advisories.

The core problem is not simply the absence of data. Much of the required information is already publicly available, but it is scattered across different systems and formats that are difficult for non-technical users to interpret.

**SIH26176 asks for an Agentic AI platform that brings these sources together, reasons over them, and produces evidence-backed answers in plain conversational language.**

---

## 2. ORCA — The Core Pitch

> **"ChatGPT for the ocean — but connected to real marine, satellite, and weather data, and capable of making decisions on a map."**

ORCA is **not intended to be a generic chatbot with marine information added to it**.

Instead, it is designed as a collaborative-agent system where:

1. A user asks a question in natural language.
2. A Planner / Orchestrator Agent understands the intent.
3. The Planner decomposes the question into specialized subtasks.
4. Specialized agents independently investigate their respective domains.
5. Their findings are correlated.
6. A deterministic Risk Assessment Agent computes safety status where applicable.
7. A Route / Navigation Agent determines safe routes where required.
8. A Visualization / Reporting Agent converts the results into maps, charts, explanations, and evidence.
9. The user receives a conversational response together with a map and an evidence trail.

The result is intended to be:

**Text + Map + Evidence Trail**

rather than an unsupported LLM guess.

---

## 3. Example User Interaction

### User Query

> "Is it safe to venture into the sea tomorrow near Ratnagiri?"

### Example ORCA Response

> Fishing is not recommended tomorrow between 5–10 AM. Expected wave height is 2.1–2.8 m, wind is 32 km/h, and lightning probability is high. Recommendation: delay departure until afternoon.

The response is accompanied by:

- A highlighted hazard zone on the map.
- Evidence from the relevant sources.
- References to:
  - IMD forecast
  - INCOIS ocean-state information
  - Marine advisory

The important design goal is that the user should be able to understand **both the recommendation and why ORCA produced it**.

---

# 4. Three Killer Workflows

The proposal identifies three workflows as the most important end-to-end demonstrations.

## 4.1 "Where should I fish?"

ORCA combines:

- Potential Fishing Zones (PFZ)
- Sea Surface Temperature (SST)
- Chlorophyll concentration
- Weather
- Distance
- Safety conditions

The system then produces **ranked fishing zones on a map**.

### Expected Output

- Ranked candidate fishing areas
- Map markers / zones
- Relevant environmental conditions
- Safety information
- Supporting evidence

---

## 4.2 "Can I go out tomorrow?"

ORCA combines:

- Weather
- Waves
- Wind
- Tide
- Cyclone information
- Lightning information

The system produces a **safety verdict with an explanation**.

The safety result is not supposed to be invented by the LLM. It is computed by a deterministic rule-based Risk Assessment Agent.

---

## 4.3 "How do I get there safely?"

ORCA combines:

- GIS information
- Maritime hazards
- Maritime boundaries
- Current conditions

The Route / Navigation Agent computes a route on the map that attempts to avoid:

- Hazards
- Restricted zones
- Unsafe areas

The proposal specifically calls for showing a comparison between a straight-line route and a geofence/hazard-avoiding route as part of the MVP.

---

# 5. System Architecture

## 5.1 High-Level Flow

```text
USER QUERY
(any language)
       |
       v
[ translate_in() wrapper ]
(not an agent; I/O transformation)
       |
       v
PLANNER / ORCHESTRATOR AGENT
       |
       +----------------+------------------+----------------+
       |                |                  |                |
       v                v                  v                v
 WEATHER          MARINE &            GEOFENCING       RAG /
 AGENT            FISHING AGENT       AGENT            ADVISORY
       |                |                  |                |
       +----------------+------------------+----------------+
                                |
                                v
                    RISK ASSESSMENT AGENT
                    -----------------------
                    Rule-based threshold engine
                    NOT the LLM
                                |
                                v
                    ROUTE / NAVIGATION AGENT
                    ------------------------
                    Safest path avoiding hazards
                                |
                                v
                    VISUALIZATION / REPORTING
                    -------------------------
                    Map layers + charts
                    + explanation + citations
                                |
                                v
                    [ translate_out() wrapper ]
                                |
                                v
                  USER: text + map + "why" panel
```

---

## 5.2 Important Architecture Principle

The **Planner / Orchestrator never communicates directly with raw external APIs**.

Instead:

- Each specialized agent owns its data domain.
- Each agent communicates with its relevant data sources/tools.
- Agents manage caching for their own domains.
- The Planner coordinates agents rather than becoming a direct API integration layer.

### Why this matters

If an external service such as INCOIS becomes temporarily unavailable during a demonstration, the Marine Agent can fall back to its most recent cached bulletin instead of allowing the entire system to fail.

This creates a more resilient architecture and keeps domain responsibilities separated.

---

# 6. Agents — Finalized Design

The document defines **7 core agents + 1 language wrapper**.

| Component | Responsibility | Key Data / Tools |
|---|---|---|
| Planner / Orchestrator | Parses intent, decomposes tasks, decides which agents to call, aggregates results | LLM with tool-calling, LangGraph state machine |
| Weather Intelligence | Wind, rain, wave height, lightning, cyclone forecasts | IMD, Open-Meteo, INCOIS Ocean State Forecast |
| Marine & Fishing Intelligence | SST, chlorophyll, PFZ advisories; ranks fishing zones | INCOIS PFZ WebGIS, MOSDAC SST/OCM-3 |
| Geospatial / Geofencing | Point-in-polygon checks against EEZ/IMBL/MPA; distance-to-boundary | PostGIS, Shapely, boundary shapefiles |
| Risk Assessment | Correlates all inputs into one safety verdict against real thresholds | Deterministic rule engine |
| Route / Navigation | Computes safest path avoiding hazards and restricted zones | PostGIS routing, hazard-weighted pathfinding |
| RAG / Advisory | Answers regulatory/advisory questions with citations | Vector DB over MFRAs, PFZ bulletins, cyclone advisories |
| Visualization / Reporting | Converts verdict, route, and advisory into map layers, charts, and plain-language explanations | Leaflet / Mapbox specification generation |
| Language Wrapper | Detects language and translates input/output | Bhashini API / IndicTrans2 |

---

# 7. Agent Responsibilities in Detail

## 7.1 Planner / Orchestrator Agent

### Responsibilities

- Understand user intent.
- Decompose a query into subtasks.
- Decide which specialized agents are required.
- Coordinate agent execution.
- Aggregate their results.
- Produce a structured state for downstream processing.

### Technology

- LLM with tool-calling
- LangGraph state machine

The Planner is the central coordination layer, but it does **not** directly access raw external APIs.

---

## 7.2 Weather Intelligence Agent

### Responsibilities

Handles environmental and weather-related conditions such as:

- Wind
- Rain
- Wave height
- Lightning
- Cyclones

### Data Sources

- IMD
- Open-Meteo
- INCOIS Ocean State Forecast

### Typical Use

For a query such as:

> "Can I go fishing tomorrow?"

the Weather Agent can provide the weather and ocean-state inputs required by the Risk Assessment Agent.

---

## 7.3 Marine & Fishing Intelligence Agent

### Responsibilities

Handles:

- Sea Surface Temperature
- Chlorophyll
- Potential Fishing Zone advisories
- Fishing-zone ranking

### Data Sources / Tools

- INCOIS PFZ WebGIS
- ISRO MOSDAC
- OCM-3
- Relevant satellite-derived marine information

### Typical Use

For:

> "Where should I fish today?"

the agent contributes PFZ, SST, chlorophyll, and other relevant marine indicators to identify and rank candidate fishing zones.

---

## 7.4 Geospatial / Geofencing Agent

### Responsibilities

Performs spatial checks including:

- Point-in-polygon operations
- EEZ checks
- IMBL checks
- MPA checks
- Distance-to-boundary calculations

### Technology

- PostgreSQL
- PostGIS
- Shapely
- Boundary shapefiles

This agent determines whether a location is inside or near restricted or important maritime boundaries.

---

## 7.5 Risk Assessment Agent

This is one of the most important safety components.

### Core Responsibility

Correlates the available environmental inputs and computes a single:

- **Safe**
- **Caution**
- **Unsafe**

verdict based on predefined real thresholds.

### Critical Design Rule

> **The LLM does not decide the safety verdict.**

The deterministic rule engine computes the verdict.

The LLM is used only to explain the result in plain language.

### Reason

The proposal considers this non-negotiable because ORCA may provide information related to fishermen safety.

This separation reduces the risk of an LLM hallucinating or changing a safety classification.

---

## 7.6 Route / Navigation Agent

### Responsibilities

Computes a safer path by considering:

- Hazards
- Restricted zones
- Maritime boundaries
- Spatial conditions

### Technology

- PostGIS routing
- Hazard-weighted pathfinding

The goal is to produce a route that is safer than simply drawing a straight line between two points.

---

## 7.7 RAG / Advisory Agent

### Responsibilities

Answers questions such as:

- Why is this zone restricted?
- What regulation applies here?
- What does a particular advisory mean?

### Knowledge Sources

The vector database contains documents such as:

- Marine Fishing Regulation Acts (MFRAs)
- PFZ bulletins
- Cyclone advisories
- Other relevant regulatory/advisory documents

### Important Rule

Responses must be **citation-grounded**.

The RAG Agent must not invent regulations outside the documents retrieved from its knowledge base.

---

## 7.8 Visualization / Reporting Agent

### Responsibilities

Transforms system outputs into user-facing information:

- Map layers
- Charts
- Plain-language explanations
- Evidence / citations
- Route visualization
- Hazard visualization

### Technology

- Leaflet
- Mapbox specification generation

---

## 7.9 Language Wrapper

The language component is explicitly **not counted as a graph agent**.

### Responsibilities

- Detect input language.
- Translate the input into the internal processing language.
- Translate the final output back into the user's language.

### Technology

- Bhashini API
- IndicTrans2

### MVP

- English
- 1 regional Indian language

### Why It Is Not an Agent

The language layer performs a fixed transformation rather than:

- reasoning,
- planning,
- tool selection,
- or domain-specific decision-making.

Keeping it as a wrapper preserves the clarity of the "collaborating agents" architecture and avoids an unnecessary reasoning/latency hop.

---

# 8. Data Sources

The proposal states that approximately **95% of the required information is already published freely by ISRO, INCOIS, and IMD**.

The project does not plan to collect its own sensor data. Instead, ORCA focuses on building the **AI + reasoning layer over existing public data**.

| Required Data | Source | Used By |
|---|---|---|
| Potential Fishing Zones (PFZ) | INCOIS PFZ WebGIS | Marine & Fishing Agent |
| Sea Surface Temperature | ISRO MOSDAC / INCOIS | Marine & Fishing Agent |
| Chlorophyll Concentration | ISRO OCM-3 / MOSDAC | Marine & Fishing Agent |
| Waves, Currents, Ocean State | INCOIS Ocean State Forecast | Weather + Risk Agents |
| Cyclone / Lightning Alerts | IMD + MOSDAC | Weather Agent / Alerting |
| General Weather Forecast | IMD / Open-Meteo | Weather Agent |
| Tide Predictions | INCOIS Tide Service | Route / Departure Timing |
| Maritime Boundaries (EEZ/IMBL) | Government shapefiles | Geofencing Agent |
| Marine Protected Areas | Protected Planet / India GIS | Geofencing Agent |
| Fishing Regulations / MFRAs | Government marine fishing regulation acts | RAG / Advisory Agent |

---

# 9. Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| Orchestration | LangGraph (Python) | Explicit state machine and easy live demonstration of the agent graph |
| Backend API | FastAPI | Async architecture and parallel agent calls |
| LLM | Claude / GPT-class model with tool-calling | Structured tool-calling for reliable agent outputs |
| Spatial Database | PostgreSQL + PostGIS | Industry-standard geospatial queries |
| Vector Store | Chroma / pgvector | RAG over advisories and regulations |
| Cache / Session | Redis | Multi-turn context and response caching |
| Map Frontend | Leaflet.js + India coastline/EEZ GeoJSON | Lightweight and no API-key friction for demo |
| Multilingual | Bhashini API / IndicTrans2 | Government / India-focused language support |
| Deployment | Docker Compose; Kubernetes path documented | Simple hackathon deployment with a path toward production |

---

# 10. MVP Scope

The proposal deliberately separates what will actually be built from what will only be discussed as future scope.

## Tier 1 — Build for Real / Non-Negotiable

The following must be implemented:

- Planner Agent
- Weather Agent
- Marine / Fishing Agent
- Geofencing Agent
- At least **2 real APIs live**
- Risk Agent
- Real rule-based threshold engine
- Evidence / citation panel in UI
- Map with PFZ markers
- Geofence overlay
- 2-turn contextual conversation

This is the primary working MVP.

---

## Tier 2 — Thin but Visible

These features should be demonstrated, but do not require the same depth as Tier 1:

- English + 1 regional language
- Route optimization
- Straight-line vs. geofence-avoiding route comparison
- Cyclone alerts
- Lightning alerts

Cyclone/lightning alerts may be **synthetic for the demo**, but they must be clearly labeled as synthetic.

---

## Tier 3 — Roadmap / Not Built

The following remain roadmap items:

- Full 8-language support
- Real-time satellite ingestion pipelines
- Production-scale multi-tenant deployment

### Scope Philosophy

The document emphasizes that the team should be honest about this split rather than pretending that roadmap functionality is already production-ready.

---

# 11. Production-Grade Architecture

Although the hackathon MVP is intentionally constrained, production-oriented design principles are included from the beginning.

---

## 11.1 Optimization

### Prompt Caching

Cache Planner and Risk system prompts where the schema is static and repeated across queries.

### Response Caching

Use Redis to cache Weather and Marine data.

Suggested cache key:

```text
rounded_latitude + rounded_longitude + date
```

The reason is that INCOIS/IMD data does not change every second.

### Parallel Tool Calls

Weather, Marine, and Geospatial agents should run concurrently where dependencies allow.

Conceptually:

```python
asyncio.gather(
    weather_agent(...),
    marine_agent(...),
    geospatial_agent(...)
)
```

This reduces end-to-end latency.

### Model Routing

Use:

- Smaller / cheaper model for intent parsing and RAG synthesis.
- Larger model for Planner decomposition where more reasoning capability is required.

### Token Budgets

Assign agent-specific token budgets.

Structured outputs such as:

- Risk results
- Geofencing results

should remain small.

---

# 12. Guardrails

Guardrails are especially important because the system deals with safety-related recommendations.

## 12.1 Input Guardrails

Before the Planner sees a request:

- Detect prompt injection.
- Detect out-of-scope queries.

---

## 12.2 Tool-Call Validation

Every agent tool call should be validated using Pydantic schemas.

Example:

- Reject latitude/longitude values outside the intended Indian coastline / supported geographic area.

This prevents invalid or malicious tool inputs from propagating through the system.

---

## 12.3 Safety Verdict Guardrail

The most important output guardrail:

> **The LLM must never directly state the safety verdict.**

Instead:

```text
Environmental Inputs
        |
        v
Deterministic Rule Engine
        |
        +----> SAFE
        +----> CAUTION
        +----> UNSAFE
        |
        v
LLM Explanation
```

The LLM explains the deterministic result in natural language.

---

## 12.4 RAG Grounding

The RAG Agent must ground regulatory answers in retrieved documents.

It should not generate unsupported regulations.

---

## 12.5 Human-in-the-Loop Actions

Any future action that **writes or sends something externally** requires human confirmation.

Example:

- Sending an SMS alert.

The system should not autonomously perform such actions without confirmation.

---

# 13. AI Gateway

A dedicated AI Gateway should sit between the backend and LLM providers.

Possible technologies:

- LiteLLM — self-hosted
- Portkey

### Responsibilities

- Single interface across multiple LLM providers
- Centralized rate limiting
- Provider fallback
- Per-agent cost tracking
- Centralized API key management

### Security Principle

Agents should **never hold LLM provider keys directly**.

Instead:

```text
Agents
   |
   v
Backend
   |
   v
AI Gateway
   |
   +---- Provider A
   +---- Provider B
   +---- Provider C
```

This simplifies provider switching and centralized governance.

---

# 14. Evaluation Strategy

The proposal includes multiple evaluation layers.

## 14.1 Golden-Set Evaluations

Build a set of approximately:

**30–50 real queries**

with known-correct verdicts based on historical INCOIS/IMD data.

This becomes the regression suite.

---

## 14.2 Agent Trajectory Evaluations

Evaluate whether:

- The Planner selected the correct agents.
- The agents were called in the correct order.
- The resulting trajectory matches the intended workflow.

---

## 14.3 Retrieval Evaluations

For the RAG Agent, measure:

- Precision@k
- Recall@k

This evaluates whether the correct regulatory/advisory documents are being retrieved.

---

## 14.4 Groundedness Evaluation

Check whether every claim in the final answer can be traced to the **structured evidence envelope**.

This is particularly important for an evidence-backed system.

---

## 14.5 Online Evaluation

The UI can capture:

- Thumbs up
- Thumbs down
- Implicit user feedback

This can later be used to identify weak answers and workflows.

---

## 14.6 Load Evaluation

Use tools such as:

- Locust
- k6

to test concurrent requests.

This matters because judges may send multiple queries simultaneously during a live demonstration.

---

# 15. Observability

The proposal treats observability as a core production feature.

## 15.1 Distributed Tracing

Possible technologies:

- LangSmith
- Langfuse
- OpenTelemetry
- Jaeger

The objective is to maintain a full per-query trace showing:

- Agent execution
- Latency
- Token usage
- Tool calls
- Errors

---

## 15.2 Structured Logging

Every agent call should produce a consistent log envelope containing fields such as:

```json
{
  "agent": "...",
  "query_id": "...",
  "data": "...",
  "confidence": "...",
  "source": "...",
  "timestamp": "..."
}
```

This logging structure also doubles as the **explainability trail** displayed to users.

---

## 15.3 Metrics

Suggested stack:

- Prometheus
- Grafana

Monitor:

- Query volume
- Per-agent p50 latency
- Per-agent p95 latency
- Per-agent p99 latency
- External API error rates
- Cache hit rate

---

## 15.4 Alerting

Trigger alerts when:

- An external data source becomes stale beyond the fallback threshold.
- Risk Agent error rates increase unexpectedly.

---

## 15.5 Cost Tracking

The AI Gateway tracks:

- Cost per query
- Cost per agent type

This provides visibility into the economics of the system.

---

# 16. Additional Production Essentials

## 16.1 Prompt / Model Versioning

Every log should contain prompt/model version information.

This is needed to reproduce or debug a problematic verdict later.

---

## 16.2 Circuit Breakers

If an external API repeatedly times out:

1. Stop repeatedly hitting the failing service.
2. Open the circuit.
3. Serve cached data when appropriate.
4. Resume calls after recovery conditions are met.

This prevents one unstable external service from degrading the whole system.

---

## 16.3 Idempotent Retries

External calls and ingestion jobs should use:

- Idempotent operations
- Exponential backoff

to handle transient failures safely.

---

## 16.4 API Rate Limiting

Rate limiting should exist at ORCA's own API layer to protect against:

- Abuse
- Runaway frontend loops
- Accidental request storms

---

## 16.5 Secrets Management

No API keys or secrets should be hardcoded, including in the hackathon repository.

---

## 16.6 CI/CD

Use a testing pyramid including:

### Unit Tests

Especially important for:

- Risk Agent threshold logic
- Geospatial calculations
- Utility functions

### Integration Tests

Particularly for:

- Planner orchestration
- Agent interactions
- Tool endpoints

### Golden-Set Evaluations

Run the golden-set regression suite on every commit.

---

## 16.7 Dataset / Version Tracking

Every verdict should be traceable to the **exact data snapshot** that produced it.

This is important for reproducibility and debugging.

---

# 17. Graceful Degradation

ORCA should explicitly define how the system behaves as external services fail.

Proposed degradation ladder:

```text
ALL APIs AVAILABLE
        |
        v
ONE API DOWN
        |
        v
ALL APIs DOWN
        |
        v
FULLY OFFLINE
```

### Fully Offline Mode

The system should still be able to provide basic functions using:

- Cached data
- Locally stored geospatial boundaries
- On-device geofencing

The proposal explicitly notes that **basic safety functions should not require an LLM**.

---

# 18. Human Escalation for Borderline Cases

For borderline or ambiguous risk situations, the system should not force a confident automated decision.

Instead, it should escalate the user toward authoritative guidance, such as:

> Consult the nearest INCOIS / Coast Guard advisory.

The principle is:

**When uncertainty is high, defer rather than fabricate confidence.**

---

# 19. Offline-First / Low-Connectivity Design

Poor network connectivity in coastal areas is treated as a first-class architectural requirement.

## 19.1 Backend Does the Heavy Processing

Heavy operations such as:

- Satellite ingestion
- AI reasoning
- Data processing

happen on the backend.

The phone receives only a small JSON payload — potentially only a few KB — instead of raw datasets.

---

## 19.2 Local Caching

The application caches:

- Latest weather
- Ocean conditions
- PFZ information
- Advisories
- Map tiles

When offline:

- Cached information remains available.
- The system synchronizes automatically when connectivity returns.

---

## 19.3 Timestamp Every Cached Result

Every cached result must display its:

**Last Updated** timestamp.

The application must never present stale cached data as if it were live.

---

## 19.4 Offline Geofencing

Geofencing can operate completely offline using:

- GPS
- Locally stored boundary polygons

No internet connection is required for this function.

---

## 19.5 Low-Bandwidth Critical Alerts

Critical alerts should have a secondary low-bandwidth channel:

- SMS

in addition to:

- App push notifications

This provides another communication path when internet connectivity is poor.

---

# 20. Team Allocation

The proposal divides the six-person team into the following roles.

| Role | Focus |
|---|---|
| AI / Agent Lead | Agent architecture, orchestration, LLM tool-calling, Planner logic |
| ML / Data | Satellite data pipelines, SST/chlorophyll processing, fishing intelligence, Risk Agent thresholds |
| GIS Engineer | PostGIS, GeoPandas, spatial queries, geofencing, route optimization |
| Backend Engineer | FastAPI, databases, agent tool endpoints, AI gateway integration |
| Frontend Engineer | React/Next.js, Leaflet map, chat UI, evidence/explanation panels |
| Data / DevOps | Ingestion cron jobs, Docker, observability stack, CI/CD, testing |

---

# 21. Five-Day Build Order

The document proposes a focused five-day implementation sequence.

## Day 1

### Objectives

- Inter-agent message schema
- PostgreSQL/PostGIS setup
- One real API — weather
- End-to-end flow through a stub Planner

### Target

Establish the basic system pipeline before adding complex agents.

```text
User
 -> Stub Planner
 -> Weather
 -> Backend
 -> Response
```

---

## Day 2

### Objectives

Add:

- Marine & Fishing Agent
- Geofencing Agent
- Parallel dispatch in Planner
- Risk Agent rule engine

At this point, the project should have its core multi-agent + deterministic safety architecture.

---

## Day 3

### Objectives

Build:

- Frontend map
- Chat UI
- Evidence panel
- Multi-turn session context

The core user interaction should now become demonstrable.

---

## Day 4

### Objectives

Add:

- Route Agent
- RAG / Advisory Agent
- Multilingual wrapper
- 2 languages
- Explainability UI polish

---

## Day 5

### Objectives

Perform:

- End-to-end testing using realistic demo queries
- Live API failure / fallback rehearsal
- Observability dashboard integration
- Pitch deck preparation
- Final integration

The pitch deck should be built around the architecture and diagrams from the proposal.

---

# 22. How ORCA Should Be Pitched

The proposal's central pitch is that ORCA is not merely an agent demonstration.

It is designed with operational discipline normally expected from a production system.

The major points to emphasize are:

### 1. Explainability

Every agent call is traced and logged.

This makes the reasoning process auditable and supports the evidence trail shown to users.

### 2. Resilience

External data sources have:

- Caching
- Circuit breakers
- Fallback behavior

Therefore, a single API outage should not break the complete system.

### 3. Deterministic Safety

The Risk Agent's verdict comes from a deterministic rule engine rather than directly from an LLM.

The rule engine can be validated against a golden set of historical INCOIS data.

### 4. AI Governance

An AI Gateway provides:

- Per-query cost visibility
- Per-agent cost tracking
- Latency visibility
- Provider abstraction
- Centralized key management

### 5. Real Deployment Potential

The intended distinction is:

> **ORCA is not just a chatbot prototype; it is an architecture that could realistically be handed to INCOIS or a state fisheries department.**

---

# 23. End-to-End Conceptual Workflow

A complete ORCA request can be understood as the following pipeline:

```text
1. USER
   |
   | Natural-language question
   v
2. LANGUAGE INPUT WRAPPER
   |
   | Translate / normalize
   v
3. PLANNER / ORCHESTRATOR
   |
   | Decompose intent
   |
   +----------------------+
   |          |           |
   v          v           v
Weather    Marine      Geospatial
Agent      Agent       Agent
   |          |           |
   +----------+-----------+
              |
              v
4. EVIDENCE / STRUCTURED RESULTS
              |
              v
5. RISK ASSESSMENT
   |
   | Deterministic thresholds
   |
   +----> SAFE
   +----> CAUTION
   +----> UNSAFE
              |
              v
6. ROUTE / NAVIGATION
   |
   | If routing is needed
   v
7. RAG / ADVISORY
   |
   | Explain regulations / advisories
   v
8. VISUALIZATION / REPORTING
   |
   +---- Map
   +---- Charts
   +---- Explanation
   +---- Evidence / citations
              |
              v
9. LANGUAGE OUTPUT WRAPPER
              |
              v
10. USER
    |
    +---- Conversational answer
    +---- Map
    +---- "Why" panel
```

---

# 24. Key Architectural Principles

The proposal can be reduced to the following principles.

## Principle 1 — Agents Own Domains

Each agent should own a clearly defined domain and its relevant tools/data.

---

## Principle 2 — Planner Coordinates, Not Raw APIs

The Planner should not directly access external data sources.

It coordinates specialized agents.

---

## Principle 3 — LLM Explains Safety; Rules Decide Safety

For safety-critical output:

```text
LLM ≠ Safety Decision Maker
Rule Engine = Safety Decision Maker
LLM = Explanation Layer
```

---

## Principle 4 — Evidence Over Guessing

Every important claim should be backed by structured evidence.

RAG responses should be citation-grounded.

---

## Principle 5 — Design for Failure

External APIs can fail.

Therefore:

- Cache data.
- Use circuit breakers.
- Use retries.
- Define graceful degradation.
- Make offline operation possible for basic functions.

---

## Principle 6 — Low Connectivity Is a Design Constraint

The client should receive small payloads rather than raw marine datasets.

Offline cache and offline geofencing are key components.

---

## Principle 7 — Production Discipline Starts in the MVP

The architecture includes:

- Observability
- Evaluation
- Cost tracking
- Secrets management
- CI/CD
- Versioning
- Dataset tracking
- Load testing

rather than leaving them entirely for a future rewrite.

---

# 25. MVP Success Criteria

The strongest practical demonstration should prove that ORCA can execute the following three workflows:

### Workflow A — Fishing Recommendation

```text
"Where should I fish today?"
       |
       v
PFZ + SST + Chlorophyll
       +
Weather + Safety + Distance
       |
       v
Ranked fishing zones
       |
       v
Map visualization + evidence
```

### Workflow B — Safety Recommendation

```text
"Can I go out tomorrow?"
       |
       v
Weather + Waves + Wind
+ Tide + Cyclone + Lightning
       |
       v
Deterministic Risk Engine
       |
       v
SAFE / CAUTION / UNSAFE
       |
       v
Plain-language explanation
+ evidence
```

### Workflow C — Safe Navigation

```text
"How do I get there safely?"
       |
       v
GIS + Hazards + Boundaries
       |
       v
Hazard-weighted pathfinding
       |
       v
Safe route
       |
       v
Map visualization
```

If these three workflows are polished end-to-end with real data, the proposal considers them sufficient for a compelling demonstration. Additional capabilities such as multilingual support, proactive alerts, and historical analysis are additive.

---

# 26. Important Scope Boundaries

The proposal explicitly distinguishes between:

### Built / Demonstrated

- Core agent architecture
- Real data integration
- Deterministic risk engine
- Evidence trail
- Mapping
- Basic contextual conversation
- Limited multilingual support
- Basic route optimization
- Production-minded resilience

### Roadmap

- Full 8-language support
- Real-time satellite ingestion pipelines
- Production-scale multi-tenant deployment

This distinction is important for technical credibility during judging and Q&A.

---

# 27. Final Architecture Summary

ORCA is proposed as a **marine decision-support platform powered by collaborative AI agents and authoritative marine data**.

At a high level:

```text
             ┌──────────────────────┐
             │        USER          │
             │ Natural Language     │
             └──────────┬───────────┘
                        │
                        v
             ┌──────────────────────┐
             │ Language Wrapper     │
             └──────────┬───────────┘
                        │
                        v
             ┌──────────────────────┐
             │ Planner /            │
             │ Orchestrator         │
             └──────────┬───────────┘
                        │
          ┌─────────────┼──────────────┐
          │             │              │
          v             v              v
     ┌─────────┐   ┌─────────┐   ┌────────────┐
     │ Weather │   │ Marine  │   │ Geospatial │
     │ Agent   │   │ Agent   │   │ Agent      │
     └────┬────┘   └────┬────┘   └─────┬──────┘
          │             │              │
          └─────────────┼──────────────┘
                        v
             ┌──────────────────────┐
             │ Risk Assessment      │
             │ Deterministic Rules  │
             └──────────┬───────────┘
                        │
                        v
             ┌──────────────────────┐
             │ Route / Navigation   │
             └──────────┬───────────┘
                        │
                        v
             ┌──────────────────────┐
             │ RAG / Advisory       │
             └──────────┬───────────┘
                        │
                        v
             ┌──────────────────────┐
             │ Visualization /      │
             │ Reporting            │
             └──────────┬───────────┘
                        │
                        v
             ┌──────────────────────┐
             │ Evidence + Map +     │
             │ Explanation          │
             └──────────────────────┘
```

The surrounding production infrastructure provides:

- Redis caching
- AI Gateway
- Observability
- Evaluation
- Circuit breakers
- Retries
- CI/CD
- Versioning
- Offline-first behavior
- Human escalation

---

# 28. One-Line Project Definition

> **ORCA is an agentic marine decision-support system that combines satellite, ocean, weather, geospatial, and regulatory data to provide evidence-backed fishing, safety, and navigation recommendations through conversational AI and interactive maps.**

---

## Source Document

This Markdown document is derived from:

**ORCA — Marine EcOsystem Reasoning with Collaborative Agents**  
**Smart India Hackathon 2026 — PS ID: SIH26176**  
**Proposed Solution & Technical Architecture — v1**  
**August 2026**

It preserves the proposal's architecture, terminology, agent responsibilities, data sources, MVP scope, production requirements, offline-first strategy, team allocation, build order, and pitch framing.
