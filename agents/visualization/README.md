# Visualization / Reporting Agent
**Owner:** Adeey (also owns the frontend that consumes this agent's output)

## Responsibility
Converts Risk/Route/RAG outputs into GeoJSON map layers, chart specs,
and the final natural-language explanation with citations — the last
step before the response reaches the user.

## MVP Tasks
- [ ] Define the final response schema: `{text, map_geojson, evidence_panel, citations}`
- [ ] Build the natural-language explanation generator (LLM call — but constrained to ONLY restate the RiskVerdict's rule_trace, never invent new claims)
- [ ] Build GeoJSON layer generation for: PFZ zones, hazard zones, geofence boundaries, route lines
- [ ] Build the evidence/"why" panel data structure the frontend will render
- [ ] Wire this into the frontend (React + Leaflet) — chat UI + map + evidence panel

## Further Stage (Production)
- [ ] Groundedness eval: LLM-as-judge check that every sentence in the generated text traces to the evidence envelope
- [ ] Chart generation for historical trend questions (SST/chlorophyll over time)
- [ ] Multi-language output rendering (paired with the `translate_out()` wrapper)
- [ ] Offline map tile caching for the region the user typically operates in
- [ ] Progressive rendering: show map + partial data while the full explanation is still generating

## Interface Contract
Consumes: `RiskVerdict`, Route Agent output, RAG Agent output
Produces: final user-facing response `{text, map_geojson, evidence_panel, citations}`
