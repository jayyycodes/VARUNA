# VARUNA — UI/UX Master Context (merged, corrected)

Owner: Adeey — Lead Experience & Integration Architect
Supersedes: the earlier "ORCA — UI/UX Master Context" doc and the previous `VARUNA_DESIGN_SYSTEM.md` draft. This is now the single reference.
Read alongside: `docs/ADEEY_ARCHITECTURE_ENGINEER.md`, `docs/prompts/_shared/role-and-safety-rules.md`

**Naming note:** the product is **VARUNA**. "ORCA" appeared in the earlier design doc as a naming mixup, not an alternate product — every screen/copy reference below uses VARUNA.

**What changed from the ORCA doc, and why:** typography (Sora/Manrope), component shapes (pills, corner radii, glass-on-overlays-only), the map-rendering rule, the data-density rule, and the failure-pattern log are kept as-is — they were sound. The **color system is replaced**, because the old one had three semantic slots (teal/navy/orange) covering a product that needs five: four verdict states (`SAFE`/`CAUTION`/`UNSAFE`/`UNKNOWN`) plus a PFZ productivity scale that the architecture doc requires to be structurally distinct from all four (§4.1, §6, definition-of-done). Under the old palette, `UNKNOWN`/indeterminate had no distinct treatment — a P0 against your own architecture doc, since that's the state most likely to be mistaken for "probably fine."

---

## 1. Product & persona overview

*(unchanged from the ORCA doc — this structure was correct)*

| | Mobile | Web |
|---|---|---|
| **Persona** | Small-boat fisherman | Coastal authority / fleet operator |
| **Navigation model** | Linear, conversational | Tab-based, non-linear |
| **Primary task** | Ask a question, get a safety answer | Monitor fleet, review agent reasoning, manage alerts |
| **Tone** | Calm, reassuring, minimal reading | Denser, operational, more data per screen |

---

## 2. Design system

### 2.1 Brand identity
Premium marine intelligence platform. Calm, restrained, trustworthy. Every decision is checked against: *would this look frivolous next to a cyclone warning?* This framing from the original doc stays — it's the right test.

### 2.2 Color tokens — corrected for the 5-state requirement

**Neutral / chrome (unchanged in spirit from the old doc):**

| Token | Hex | Usage |
|---|---|---|
| Navy | `#0A1F33` | Headlines, primary text, primary UI actions, active nav states — the one general-purpose brand accent |
| Near-black canvas | `#071018` | Dark-theme canvas |
| Light canvas | `#F7F6F2` | Warm off-white — never pure white |
| Dark cards | `#101C2C` | Never pure black |

**Verdict family — appears ONLY on verdict cards, safety status dots/badges, and risk-breakdown rows. Never used decoratively, never used for chrome, buttons, or nav:**

| Verdict | Hex | Rule |
|---|---|---|
| `SAFE` | `#2E9E6B` (green) | Dot + text label always; filled pill only if the product surfaces a positive confirmation state prominently |
| `CAUTION` | `#E0A030` (amber) | Dot + text label in calm contexts; filled pill when action is required before departure |
| `UNSAFE` | `#D14343` (red) | Always a filled pill — this is the one state that must never be understated |
| `UNKNOWN` / indeterminate | `#7C8A93` (desaturated slate) | **Never a calm dot.** Use an outlined/dashed pill with an explicit "not enough data" icon — it must look unresolved, not fine |

**PFZ productivity — a single-hue teal scale, structurally separate from verdict colors, used only on PFZ layers/markers/confidence indicators:**

| Token | Hex range | Usage |
|---|---|---|
| PFZ scale | `#0F5C6E` → `#35B8A6` | Single-hue gradient by productivity/confidence — never rainbow, never reused as a verdict color anywhere else in the app |

**Hard rule carried over from the old doc's orange-discipline, now generalized:** if a verdict color or the PFZ teal appears anywhere outside its reserved role (nav, chrome, a "fun" chart accent) in a generated screen, that's a design-system violation to flag and fix, not a stylistic choice to accept.

### 2.3 Typography — kept from the ORCA doc, unchanged
- **Headlines / hero numbers:** Sora, bold, slightly condensed.
- **Body / labels:** Manrope, regular/medium weight, normal tracking.
- Display styling (Sora) never bleeds into chrome, buttons, or data values — only headlines and hero numbers.
- **New addition (from the marine design pass):** numeric readouts inside data rows (wave height, coordinates, thresholds) use `font-variant-numeric: tabular-nums` in Manrope, so columns of numbers align — this is a legibility rule, not a third typeface.

### 2.4 Component language — kept from the ORCA doc, unchanged
- **Corners:** 20–24px primary cards, 16px secondary cards, full-pill (999px) on buttons/tabs/status badges.
- **Depth:** soft, heavily diffused ambient shadows only — never hard drop shadows. Depth from layering, not shadow intensity.
- **Glassmorphism:** floating overlays only (bottom sheets, map overlay cards, telemetry callouts) — never static backgrounds or every card.
- **Navigation pill pattern:** top nav = pill-shaped segmented tabs, active tab as a solid pill inside a lighter track. Sidebar active state = a pill whose fill matches the flat canvas color behind it, so it visually merges rather than using an arbitrary highlight.
- **Sidebar:** two explicit states, expanded (icon+label) and collapsed (icon-only rail) — both must be designed, not implied.

### 2.5 Status pattern — updated for 4 verdict states, not 1 alert color
- **Calm/informational states** (data freshness OK, a normal reading, a resolved SAFE result the user has already seen): small colored dot + text label.
- **Filled pill badges** reserved for `UNSAFE` always, and `CAUTION` when it demands pre-departure action. Overusing filled badges elsewhere makes everything look equally urgent and defeats the alert system — this rule from the old doc still holds.
- **`UNKNOWN`/indeterminate gets neither treatment above** — see §2.2. It needs to visually register as "we don't know," which a calm dot cannot communicate and a solid alert-red pill would mis-communicate (it isn't necessarily dangerous, it's unresolved).

### 2.6 The map-rendering rule — kept, unchanged
Any map area is a simple, flat, single-hue fill — light blue for sea, a thin coastline line, no satellite texture, no photorealistic imagery. Choropleth overlays (chlorophyll, SST, PFZ productivity) use a single-hue gradient, never rainbow. This was the single largest cause of broken renders in the earlier prototype pass — treat as a hard constraint. **Addition:** hazard/geofence overlays use the verdict red/amber directly (not a separate map palette), so a hazard zone on the map and a hazard reason in the verdict card read as the same signal.

### 2.7 Data density rule — kept, unchanged
Max 2–3 data points per card. Cards asked to hold 5+ named stats reliably break layout. Split dense screens into multiple smaller generations and assemble them.

---

## 3. Mobile screens (fisherman-facing)

*(Screens and flow kept from the ORCA doc; color/status treatment corrected per §2)*

- **M1 — Home:** greeting, date + sector, chat input as primary entry, 2 quick-action chips (not 3), bottom pill tab bar (Home/Map/Alerts/Settings).
- **M2 — Chat:** user messages right-aligned/navy-filled (not teal — teal is reserved for PFZ now); assistant responses left-aligned plain card, embedded mini evidence card, "View reasoning" link.
- **M3 — PFZ/Map results:** flat map, 2–3 zone markers using the **PFZ teal scale**, frosted bottom sheet with swipeable zone cards. Confidence shown as dot + percentage in **PFZ teal**, never in a verdict color — productivity confidence and safety verdict must stay visually unrelated even at the confidence-dot level.
- **M4 — Zone detail:** stat grid, risk breakdown (weather/boundary/historical yield) where **each status dot now uses the actual verdict palette** (§2.2) instead of the old generic orange-for-everything, plus "Get Safe Route" / "Ask Follow-up" actions.
- **M5 — Alerts/hazard:** centered hazard icon using `UNSAFE` red or `CAUTION` amber (matched to the actual verdict, not a fixed "alert orange"), status pill, headline advisory, single CTA. Dark variant remains primary (pre-dawn/overnight use case).

---

## 4. Web screens (authority/ops-facing)

*(Kept from the ORCA doc; renamed to VARUNA; color corrected per §2)*

- **W1 — Fleet Ops overview:** 2 KPI cards, flat map panel, 2 port status cards (3 stat rows each).
- **W2 — Ocean Eye:** layer toggle (Chlorophyll/SST/PFZ — PFZ layer uses the teal scale, never a verdict color), flat map, Active Alerts / Agent Activity / PFZ summary column. Keep the civilian-not-tactical correction.
- **W3 — Route Planner:** waypoint list with status pills (using verdict colors where a waypoint has a safety implication, neutral navy otherwise), flat map, floating live-telemetry card. Indian coastal waypoints, not Southeast Asian.
- **W4 — Intelligence / Agentic Reasoning trace:** the closing demo beat, unchanged in structure. Node states (Planning → Marine Data → Risk Assessment → Synthesis) use **neutral navy/slate**, not verdict colors — this trace is about system process, not a safety statement, so it should not visually compete with the verdict palette. The final "Consensus Reached" / "Deploy Recommendation" state may adopt the actual resulting verdict color, since at that point it *is* reporting the verdict.
- **W5 — Weather Advisory report:** situation summary, composite risk gauge, sector-by-sector table — gauge and table status cells use the verdict palette directly. Coastal Maharashtra/Konkan sector names, not North Sea.
- **W6 — Alerts (fleet-wide):** vector-style map, alert markers in verdict red/amber matched to severity, two priority alert cards, compliance stat row. Clean vector map, not a stock command-center background.

---

## 5. Navigation & flow logic — unchanged from the ORCA doc

Mobile is a linear chain (Home → Chat → PFZ results → Zone detail → Route, with Alerts as a direct-entry exception). Web is a tab hub with no fixed order; the rehearsed demo path is Fleet Ops → Ocean Eye → Route Planner → **Intelligence (closing screen)** → Weather/Alerts as needed.

---

## 6. Apple motion — where springs apply on these specific screens

Per the Apple design reference, springs are for direct manipulation only:

| Screen / element | Interaction | Spring | Why |
|---|---|---|---|
| M3 bottom sheet zone cards | Swipe between cards | damping `0.8`, response `0.3` | Momentum-driven gesture, needs velocity handoff |
| Sidebar expand/collapse (web) | Tap toggle | damping `1.0`, response `0.25` | Direct tap, no overshoot — this is furniture, not a flourish |
| Top nav pill tab switch | Tap | damping `1.0`, response `0.2` | Same — a settled, non-bouncy slide of the active pill |
| M4 risk-breakdown row expand | Tap to expand evidence | damping `1.0`, response `0.25` | Informational disclosure, critically damped |
| Verdict card appearing (any screen) | **No spring — cross-fade only, 200ms** | — | A safety statement should feel immediate and certain, not "alive" |

---

## 7. Recurring failure patterns — kept, plus one addition

*(All entries below are from the original prototype pass and remain valid lessons.)*

- Content drift toward generic global shipping SaaS (European ports, Southeast Asian lanes, North Sea weather) without an explicit geography/persona lock in every prompt.
- Complex/photorealistic maps break renders — §2.6 is a hard constraint, not a suggestion.
- Dense cards (5+ stats) break layout — §2.7.
- Structural gaps get filled with blank placeholders rather than omitted — every card needs explicit content specified.
- Horizontal rows need counting against screen width (2 mobile chips safe, 3 overflows).
- Tone drift toward military/tactical styling on monitoring screens — needs an explicit "civilian, not tactical" instruction each time.
- **New:** verdict/PFZ color conflation — without an explicit instruction pinning which palette a given card/marker/dot belongs to (§2.2), a generator will reach for "teal" or "orange" as a generic accent regardless of whether the element is reporting safety or productivity. Every prompt touching a status dot, badge, or map marker must state which of the two palettes it draws from.

---

## 8. What's still open

- Figma-prototype vs. coded-prototype decision for the SIH demo (unresolved in the source doc — still unresolved here).
- Full light + dark generation for every screen in §3–4.
- Reconciling any developer-facing "Schema Explorer" screens (flat, monospace register) with this system, if shown in-app rather than as a slide.
- Sidebar collapsed-state variants beyond Fleet Ops and Intelligence.
- **New:** re-audit every existing Stitch frame against §2.2's corrected palette before treating any of them as final — anything generated under the old teal/navy/orange system needs its status dots, badges, and map markers re-checked against which of the two new palettes they should belong to.

---

## 9. Handoff note for Antigravity prompts

Use this file (`docs/design/VARUNA_UI_UX_MASTER_CONTEXT.md`) as the `[STITCH_REFERENCE_PATHS]` input for Step 01 (Analyze references) in the prompt sequence, alongside any Stitch frames that still hold once re-audited per §8. Step 01's output should flag any existing frame whose status dots/badges/markers don't yet match §2.2 before Step 03 builds the shell from it.
