# Planner / Orchestrator Agent
**Owner:** Jay

## Responsibility
Parses user intent, decomposes it into sub-tasks, decides which agents to call
and in what order, and aggregates their results into a final response.
This is the highest-judgment component in the system — every other agent
is called *through* the Planner, never directly by the Gateway.

## MVP Tasks
- [ ] Define intent categories: `safety_check`, `find_fishing_zone`, `route_request`, `regulation_question`
- [ ] Build intent classifier (LLM w/ function-calling, structured output)
- [ ] Implement LangGraph state machine: intent → agent dispatch → aggregation
- [ ] Dispatch Weather + Marine + Geofencing agents in **parallel** via `asyncio.gather()` for safety_check queries
- [ ] Pass Weather/Marine/Geofencing outputs to Risk Agent, then to Visualization Agent
- [ ] Handle partial failures gracefully (one agent times out → proceed with what's available, flag degraded confidence)

## Further Stage (Production)
- [ ] Model routing: cheaper/smaller model for intent parsing, larger model reserved for complex decomposition
- [ ] Prompt caching on the static system prompt + tool schemas
- [ ] Circuit breaker: if an agent fails 3x consecutively, skip it for N minutes, serve cached/degraded response
- [ ] Full LangSmith/Langfuse tracing on every Planner decision (log which agents were called, in what order, why)
- [ ] Agent trajectory eval: does the Planner call the *right* agents for a given intent category? (golden-set validation)
- [ ] Multi-turn context handling: follow-up queries ("is it safe there tomorrow?") should reuse location/time from previous turn
- [ ] Human-in-the-loop escalation path for ambiguous/borderline intent classification

## Interface Contract
Consumes: normalized query (post `translate_in()`) + session context from Redis
Produces: final aggregated response dict, handed to Visualization Agent
Uses: `backend/schemas/envelope.py` — every downstream agent call returns an `AgentEnvelope`
