# Planner / Orchestrator Agent
**Owner:** Jay  
**Status:** MVP Complete ✅ | Next Phase: Production Hardening & Observability

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

- [ ] **Multi-Turn Session Memory (Redis)**:
  - Persist conversation state, last-queried port/coordinates, vessel profile, and route waypoints across follow-up queries (e.g. *"Is it safe there tomorrow?"*).
- [ ] **AI Gateway & Provider Abstraction**:
  - Implement LiteLLM router with automatic failover: Groq `llama-3.3-70b-versatile` (primary) $\to$ Cerebras `llama3.1-70b` (fallback).
  - Add request rate-limiting, usage metrics, and token cost tracking per query.
- [ ] **Prompt Caching**:
  - Enable prompt caching on static system prompts and agent schemas to achieve sub-second response times.
- [ ] **Circuit Breaker Ladder**:
  - If an upstream agent or external feed times out 3 times consecutively, trip circuit breaker for $N$ minutes and return cached/degraded envelopes without blocking the graph.
- [ ] **Observability & Agent Trajectory Tracing**:
  - Integrate LangSmith / Langfuse tracing across every state transition to record agent invocation order, tool call payloads, and latency breakdowns.
- [ ] **Trajectory Evaluation Suite**:
  - Run automated evals over the 30–50 query golden dataset to benchmark intent classification accuracy and tool selection correctness.
- [ ] **Multilingual Pipeline Integration**:
  - Connect `translate_in()` and `translate_out()` wrappers to Bhashini / IndicTrans2 for Hindi, Marathi, Tamil, and Malayalam translation.

---

## 3. Interface Contract
- **Consumes**: Normalized query payload + Redis session ID.
- **Produces**: Final aggregated dictionary passed to Visualization Agent / API response.
- **Contract Schema**: [`backend/schemas/envelope.py::AgentEnvelope`](file:///c:/Development/Varuna/backend/schemas/envelope.py)
