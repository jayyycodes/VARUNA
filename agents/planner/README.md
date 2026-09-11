# Planner / Orchestrator Agent
**Owner:** Jay  
**Status:** Tier 2 Production Hardened ✅ | Golden Set Benchmarking (Tier 3)

## Responsibility
Parses user natural-language intent, decomposes it into sub-tasks, dispatches specialized domain agents in parallel, enforces deterministic safety guardrails, and aggregates results into an explainable response envelope.

---

## 1. MVP Tasks (Completed ✅)
- [x] **Intent Classification**: Implemented multi-intent detection (`safety_check`, `find_fishing_zone`, `route_request`, `regulation_question`).
- [x] **LangGraph State Machine**: Orchestrates parallel agent dispatch, conditional branches, and aggregation nodes.
- [x] **Parallel Execution**: Dispatches Weather, Marine, and Geofencing agents concurrently via `asyncio.gather()`.
- [x] **Strict Safety Guardrail Enforcement**: Risk Agent's deterministic rule-engine verdict is strictly non-negotiable; LLM synthesis is forbidden from downgrading `UNSAFE` or `CAUTION`.
- [x] **Route Agent Integration**: Integrated Tier-2 Route Optimization Agent for port-to-port and port-to-PFZ navigational queries.
- [x] **Fault Tolerance & Fallbacks**: Partial failure handling ensures the system degrades gracefully if an individual agent times out.

---

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 3, 9, & 10), the next operational priorities are:

- [x] **Multi-Turn Session Memory**:
  - Persists conversation state, last-queried port/coordinates, vessel profile, and route waypoints across follow-up queries (e.g. *"Is it safe there tomorrow?"*). Tested via `test_planner_multiturn_session`.
- [x] **AI Gateway & Provider Abstraction**:
  - Implemented high-performance router with automatic failover (Groq primary $\to$ Cerebras fallback) using `openai/gpt-oss-120b`.
  - Added latency metrics, token tracking, and non-blocking circuit protection.
- [x] **Circuit Breaker Ladder**:
  - 3-state machine (`CLOSED`, `OPEN`, `HALF_OPEN`) in `backend/gateway/circuit_breaker.py` guarding upstream APIs (`open_meteo_weather`, `incois_wfs`, `geofencing_postgis`, `groq_llm`, `cerebras_llm`) with fast-fail fallback execution.
- [x] **Observability & Agent Trajectory Tracing**:
  - Integrated LangSmith SDK (`RunTree`) across state transitions in `backend/gateway/observability.py` recording agent invocation order, tool call payloads, latency breakdowns, and LLM spans.
- [x] **Multilingual Pipeline Integration**:
  - Integrated `translate_in()` and `translate_out()` wrappers in `backend/gateway/multilingual.py` for Hindi and Marathi Devanagari detection and bidirectional translation.
- [x] **Upstream Health Monitoring**:
  - Exposes circuit status via `GET /health` and dedicated `GET /api/health/upstream` endpoint.
- [ ] **Golden Set Trajectory Evaluation Suite**:
  - Benchmark intent classification accuracy and tool selection correctness across 50 regional golden queries.

---

## 3. Interface Contract
- **Consumes**: Normalized query payload + Redis session ID.
- **Produces**: Final aggregated dictionary passed to Visualization Agent / API response.
- **Contract Schema**: [`backend/schemas/envelope.py::AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py)
