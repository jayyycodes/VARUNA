# Risk Assessment Agent
**Owner:** Jaish

## Responsibility
Correlates Weather + Marine + Geofencing outputs into a single
Safe/Caution/Unsafe verdict using a **deterministic rule engine**.

**This is the most safety-critical component in the entire system.**
The LLM is NEVER allowed to decide the verdict — it only explains a
verdict the rule engine already computed. This is a non-negotiable
guardrail, not a suggestion.

## MVP Tasks
- [ ] Research and document real safety thresholds from INCOIS/IMD guidelines (wave height limits for small craft, wind speed limits, etc.) — cite the source for each threshold
- [ ] Build the rule engine as plain conditional logic (no LLM call inside this function at all)
- [ ] Define verdict logic: what combination of breaches = CAUTION vs. UNSAFE?
- [ ] Return a `RiskVerdict` with full `rule_trace` — every threshold checked and its result, for the evidence panel
- [ ] Build the golden-set: 30-50 real historical query scenarios (real dates/locations with known INCOIS/IMD conditions) with the verdict a human would assign — this is the regression suite

## Further Stage (Production)
- [ ] Run the golden-set as an automated eval in CI on every commit to this agent
- [ ] Groundedness eval: confirm the LLM's natural-language explanation (built downstream in Visualization Agent) never states anything the `rule_trace` doesn't support
- [ ] Human-in-the-loop escalation: for borderline/ambiguous threshold cases, output "consult nearest INCOIS/Coast Guard advisory" rather than forcing a confident call
- [ ] Threshold versioning: if thresholds are updated, tag which version produced a given historical verdict
- [ ] Consider ML-assisted threshold calibration once enough real usage data exists (still human-reviewed, still not an LLM decision)

## Interface Contract
Consumes: `AgentEnvelope` outputs from Weather, Marine, Geofencing agents
Produces: `RiskVerdict` (see `backend/schemas/envelope.py`) — verdict + reasons + full rule_trace
