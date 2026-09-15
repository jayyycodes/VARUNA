"""
Visualization / Reporting Agent — owner: Adeey

Converts Risk/Route/RAG outputs into GeoJSON map layers, chart specs,
evidence DAG traces, and the final structured reporting payload with citations.
"""

from typing import Any, Dict, List, Optional
import uuid
import time


class VisualizationAgent:
    """
    Transforms multi-agent reasoning, deterministic rule traces, GeoJSON spatial layers,
    and statutory citations into an intuitive, explainable payload for the frontend.
    """

    def __init__(self):
        self.agent_name = "visualization_reporting_agent"
        self.version = "1.0.0"

    def build_geojson_layers(
        self,
        coords: Optional[Dict[str, float]] = None,
        verdict: Optional[str] = None,
        hazards: Optional[List[Dict[str, Any]]] = None,
        pfz_points: Optional[List[Dict[str, Any]]] = None,
        route_waypoints: Optional[List[Dict[str, float]]] = None,
    ) -> List[Dict[str, Any]]:
        """Generates standard Leaflet-compatible GeoJSON feature layers."""
        layers = []
        lat = coords.get("lat", 16.99) if coords else 16.99
        lon = coords.get("lon", 73.30) if coords else 73.30

        # Base Location Layer
        layers.append({
            "id": f"loc-{uuid.uuid4().hex[:8]}",
            "name": "Target Operational Sector",
            "type": "point",
            "visible": True,
            "data": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "title": "Target Sector",
                            "verdict": verdict or "SAFE",
                            "radius_km": 15,
                        },
                    }
                ],
            },
        })

        # PFZ Clusters
        if pfz_points:
            features = []
            for idx, pt in enumerate(pfz_points):
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [pt.get("lon", lon + 0.1), pt.get("lat", lat + 0.1)],
                    },
                    "properties": {
                        "zone_name": pt.get("name", f"PFZ Zone {idx + 1}"),
                        "chlorophyll": pt.get("chlorophyll", "1.2 mg/m³"),
                        "sst": pt.get("sst", "28.4°C"),
                        "depth_m": pt.get("depth", 45),
                    },
                })
            layers.append({
                "id": f"pfz-{uuid.uuid4().hex[:8]}",
                "name": "Potential Fishing Zones (PFZ)",
                "type": "point",
                "visible": True,
                "data": {"type": "FeatureCollection", "features": features},
            })

        # Navigational Corridors
        if route_waypoints and len(route_waypoints) > 1:
            coordinates = [[wp.get("lon", 0), wp.get("lat", 0)] for wp in route_waypoints]
            layers.append({
                "id": f"route-{uuid.uuid4().hex[:8]}",
                "name": "Safe Navigation Passage",
                "type": "route",
                "visible": True,
                "data": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": coordinates},
                            "properties": {
                                "status": "CLEARED",
                                "clearance_buffer_nm": 2.0,
                            },
                        }
                    ],
                },
            })

        return layers

    def build_response(
        self,
        verdict: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        coords: Optional[Dict[str, float]] = None,
        query_text: str = "",
        hazards: Optional[List[Dict[str, Any]]] = None,
        pfz_points: Optional[List[Dict[str, Any]]] = None,
        route_waypoints: Optional[List[Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Builds the complete UserResponseV1-compliant visualization & evidence payload.
        """
        verdict_str = verdict.get("verdict", "SAFE") if isinstance(verdict, dict) else str(verdict)
        layers = self.build_geojson_layers(
            coords=coords,
            verdict=verdict_str,
            hazards=hazards,
            pfz_points=pfz_points,
            route_waypoints=route_waypoints,
        )

        return {
            "schema_version": "1.0.0",
            "query_run_id": f"run-{uuid.uuid4().hex[:8]}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "query": query_text,
            "summary": {
                "verdict": verdict_str,
                "headline": verdict.get("headline", f"Conditions assessed as {verdict_str}."),
                "action": verdict.get("action", "Monitor routine VHF channel 16 updates."),
                "confidence": verdict.get("confidence", "HIGH"),
                "confidence_reason": verdict.get("confidence_reason", "All sensor telemetry verified."),
            },
            "map_layers": layers,
            "evidence_trail": evidence or [],
            "rule_trace": verdict.get("rule_trace", []),
            "citations": verdict.get("citations", []),
            "freshness": verdict.get("freshness", []),
        }
