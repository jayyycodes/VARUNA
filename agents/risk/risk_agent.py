"""
Risk Assessment Agent — owner: Jaish

Correlates Weather + Marine + Geofencing outputs into a Safe/Caution/Unsafe
verdict using a DETERMINISTIC RULE ENGINE. The LLM only explains this verdict
in natural language downstream — it never decides the verdict itself.
This is the single most important guardrail in the whole system.

See agents/risk/README.md for full task breakdown (MVP + further stage).
"""

from backend.schemas.envelope import AgentEnvelope, RiskVerdict


class RiskAgent:
    # Thresholds MUST be sourced from real INCOIS/IMD safety guidelines — cite the source.
    WAVE_HEIGHT_SMALL_CRAFT_MAX_M = 2.5

    def correlate(self, weather: AgentEnvelope, marine: AgentEnvelope, geo: AgentEnvelope) -> RiskVerdict:
        raise NotImplementedError("TODO: rule engine — no LLM call in this function")
