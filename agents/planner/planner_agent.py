"""
Planner / Orchestrator Agent — owner: Jay

Parses user intent, decomposes into sub-tasks, dispatches to specialized
agents in parallel where possible, aggregates their AgentEnvelope results,
and builds the final task graph for the Visualization Agent to render.

See agents/planner/README.md for full task breakdown (MVP + further stage).
"""

from backend.schemas.envelope import AgentEnvelope


class PlannerAgent:
    async def handle_query(self, normalized_query: str, session_context: dict) -> dict:
        """
        1. Parse intent (safety_check / find_fishing_zone / route_request / regulation_question)
        2. Decide which agents to call based on intent
        3. Dispatch via asyncio.gather() for independent agents
        4. Pass results to Risk Agent if safety-relevant
        5. Pass final structured result to Visualization Agent
        """
        raise NotImplementedError("TODO: implement LangGraph state machine")
