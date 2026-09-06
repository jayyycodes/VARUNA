"""
Visualization / Reporting Agent — owner: Adeey

Converts Risk/Route/RAG outputs into GeoJSON map layers, chart specs,
and the final natural-language explanation with citations.

See agents/visualization/README.md for full task breakdown (MVP + further stage).
"""


class VisualizationAgent:
    def build_response(self, verdict, evidence, coords) -> dict:
        raise NotImplementedError("TODO: build GeoJSON + text + citation payload")
