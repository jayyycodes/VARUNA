# VARUNA Design System — Mobile & Web

Owner: Adeey — Lead Experience & Integration Architect
Status: proposed visual direction, replaces the current Stitch exports as the reference doc for all frontend prompts
Read alongside: `docs/ADEEY_ARCHITECTURE_ENGINEER.md`, `docs/prompts/_shared/role-and-safety-rules.md`

---

## 0. Why this replaces the Stitch references

The Stitch exports and the seven shared inspiration screenshots are generic SaaS-dashboard patterns: rounded cards of one radius, a soft grey shadow under everything, gradient washes as decoration. That reads as templated, and worse — on a safety product it competes visually with the one thing that actually matters, the verdict. This document defines a direction grounded in VARUNA's real subject: open water, hazard, visibility, and the difference between "productive" and "safe." Two of the references (the player-profile tool and the crypto portfolio) have structural ideas worth reusing — dense multi-pane layout, translucent floating chrome, tabular numerals — and those are kept below. The rest are not used as visual sources.

---

## 1. Design plan

### Color — 6 named values, two families that must never blend

Verdict colors and PFZ colors are **structurally separate palettes** — this is not a style preference, it's the architecture doc's non-negotiable rule (§4.1, §6) made visual.

| Token | Hex | Use |
|---|---|---|
| `--water-900` | `#0B1E2D` | Base dark surface — the app's "night ocean" background |
| `--foam-50` | `#F3F6F5` | Base light surface / primary text on dark |
| `--verdict-safe` | `#3FA76B` | SAFE only |
| `--verdict-caution` | `#E0A030` | CAUTION only |
| `--verdict-unsafe` | `#D14343` | UNSAFE only |
| `--verdict-unknown` | `#7C8A93` | UNKNOWN / indeterminate — deliberately unsaturated, never reassuring |
| `--pfz-productive` | `#6B7FE0` | PFZ productivity scale (indigo family) — never green/amber/red, so it can't be misread as a verdict |

Everything else — chrome, nav, borders, secondary text — is a **neutral grey-blue ramp** derived from `--water-900` (5 steps, e.g. `#12293B`, `#1B3A50`, `#4A6478`, `#8FA3AF`, `#F3F6F5`). No separate "brand color." The verdict and PFZ tokens above are the only saturated colors in the system — that scarcity is what makes them mean something the instant they appear.

### Type — one family, tabular numerals for data

Use the platform system-font stack (`-apple-system, "Segoe UI", Roboto, sans-serif`) as the single family, per Apple's own guidance: it already ships correct optical sizing per platform and needs no justification to override. Distinguish hierarchy with weight + size + leading as a set, not a second typeface:

- Verdict headline: 28–34px, weight 650, tight leading (1.05), slight negative tracking (`-0.01em`)
- Body / evidence text: 15–16px, weight 400–450, leading 1.5
- Numeric readouts (wave height, coordinates, thresholds): `font-variant-numeric: tabular-nums`, weight 500 — this is a functional choice (columns of numbers must align), not a decorative monospace label

No tracked-out uppercase eyebrows, no middle-dot metadata strings, no `→` on buttons. Labels say exactly what they are: "Wave height," not "WAVE HEIGHT ⌁ LIVE."

### Layout — asymmetric three-pane on desktop, stacked-with-sheet on mobile

```
DESKTOP (≥1024px)
┌──────────┬─────────────────────────────┬──────────────┐
│  Query   │                             │   Evidence   │
│  history │      Map (full height)      │   & sources  │
│  + nav   │  verdict card floats top-   │   (collapsi- │
│  (240px) │  left over the map          │   ble, 340px)│
└──────────┴─────────────────────────────┴──────────────┘
```
The map *is* the canvas — verdict and evidence float over it as translucent panels (see §3), not beside it in equal-weight cards. This is the one structural idea worth keeping from the crypto-portfolio reference: a full-bleed primary surface with data floating on top of it, not boxed away from it.

```
MOBILE (<768px)
┌─────────────────────────┐
│ Verdict card (fixed,    │  ← always visible, never scrolls away
│ full-width, top)        │
├─────────────────────────┤
│                         │
│   Map (fills remaining  │
│   viewport)             │
│                         │
├─────────────────────────┤
│ ▔▔▔ evidence sheet ▔▔▔  │  ← draggable bottom sheet, collapsed by default
└─────────────────────────┘
```
Satisfies the architecture doc's rule directly: verdict/action visible without scrolling past a full-height map (§4.5, §8, definition of done).

### Principles

1. **Scarcity of color is the safety mechanism.** Verdict and PFZ hues appear nowhere else in the UI — not in nav, not in charts, not in buttons — so their appearance is never ambiguous.
2. **The map is the canvas, not a card.** Everything else is a translucent layer floating over it, reinforcing that this is one coherent scene, not a dashboard of unrelated widgets.
3. **Numbers are furniture, not decoration.** Tabular alignment, no sparkline-for-its-own-sake, no gradient area fills under charts unless the shape itself is the answer to the user's question (e.g., an actual wave-height forecast curve).
4. **Motion explains state changes, it doesn't perform for their own sake.** Apple's rules below govern exactly which four interactions get springs — everything else stays a plain, quick cross-fade.

---

## 2. Component patterns kept from the references (with reasoning)

| Pattern | Source | Adapted for VARUNA as |
|---|---|---|
| Multi-pane layout, right rail collapses to a summary strip | Sportselects profile | Desktop query/map/evidence three-pane; evidence rail collapses to just headline reasons |
| Translucent dark chip over a busy background | Crypto portfolio | Verdict card floating over the map — `backdrop-filter: blur(20px)` + `--water-900` at 70% alpha |
| Tabular data rows with right-aligned numeric column | Sportselects contract table | Rule-trace rows: measured value / threshold / result, right-aligned tabular numerals |
| Everything else (rounded stat cards, gradient chart fill, sidebar icon rail as decoration) | — | Not used — generic SaaS default, doesn't serve a safety-critical hierarchy |

---

## 3. Apple motion — applied only where a user directly manipulates something

Per the Apple design doc's own rule (§4): "reach for springs for anything a user can touch." VARUNA has exactly four such interactions. Everything else (page loads, list appearing, panel fade) is a plain 150–200ms cross-fade — no spring, no exception, because those aren't gestures.

| Interaction | Spring | Values | Why |
|---|---|---|---|
| Evidence bottom sheet drag (mobile) | Yes | damping `0.8`, response `0.3` | User's finger drags it; must track 1:1 and carry release velocity (§2, §5 of Apple doc) |
| Verdict card entrance on new query result | No — cross-fade only | 200ms opacity | Not gesture-driven; a bouncy verdict card undermines the seriousness of a safety statement |
| Map layer toggle (PFZ / hazard / geofence checkboxes) | Yes, subtle | damping `1.0`, response `0.2` | Direct tap feedback, no overshoot — toggling a layer is not a "momentum" action |
| Pinch/pan on the Leaflet map | Native (Leaflet's own) | — | Don't fight the map library's own gesture handling |
| Rule-trace card expand/collapse | Yes | damping `1.0`, response `0.25` | User-triggered disclosure; critically damped, no bounce — this is informational, not playful |

**Explicitly do not spring:** the verdict color/text change itself, the degraded/indeterminate banner appearing, any citation or evidence text. These are safety statements — they should feel immediate and certain, not bouncy or "alive." Save all bounce (`damping < 1.0`) for the one momentum-driven gesture (the bottom sheet).

### Materials — one deliberate use

Only the verdict card and the evidence sheet get `backdrop-filter` translucency, because they float over the map (§12 of Apple doc: material weight encodes hierarchy). Nav chrome, buttons, and citation cards are solid — stacking two translucent surfaces is explicitly the thing to avoid.

```css
.verdict-card {
  background: rgba(11, 30, 45, 0.72); /* --water-900 at 72% */
  backdrop-filter: blur(20px) saturate(160%);
  border-top: 1px solid rgba(255,255,255,0.15); /* light catching the material, per Apple doc */
}
```

### Reduced motion / accessibility (non-negotiable, from both docs)

- `prefers-reduced-motion`: bottom sheet becomes a plain slide with no spring; layer toggle loses its scale animation, keeps the color/checkmark change.
- Verdict is never color-only: every verdict state pairs the hue with an icon and a text label (architecture doc §6 enum policy, restated here as a UI rule).
- All floating panels remain keyboard-reachable and screen-reader labeled even when visually "floating" over the map.

---

## 4. Screen specs

### 4.1 Verdict card (the one element allowed to be bold)

- Headline uses the verdict color as a left border + icon only — background stays neutral translucent, **not** a full verdict-colored fill. (A full red card reads as an error state, not a considered safety verdict — keep the color as a signal, not a wash.)
- Order inside the card, fixed: verdict word → recommended action → confidence band + one-line reason → 1–3 tappable reasons.
- Reasons open the evidence sheet scrolled to the matching rule-trace card (architecture doc §4.2, §8).

### 4.2 Map

- Full-bleed, no card border, no shadow — it's the canvas.
- Legend is a small translucent chip, bottom-left, collapsible, never covering the verdict card.
- PFZ layer uses the indigo scale exclusively; hazard/geofence layers use the verdict reds/ambers; user location is a simple neutral dot — never borrow a verdict or PFZ hue for it.

### 4.3 Evidence sheet

- Collapsed state on mobile: a single grabber handle + "Evidence & sources" label + chevron, ~64px tall.
- Expanded: rule-trace cards (tabular value/threshold/result), then a "Sources" section with citation cards (title, publisher, timestamp, short excerpt, link).
- An unsupported claim renders as plain grey text with a small "not verified" label — never styled like a resolved fact.

### 4.4 Query / chat panel (desktop left rail, mobile modal)

- Plain text input + location/time chips. No decorative icons per field. History list uses tabular timestamp alignment, matching the rest of the system's numeric discipline.

---

## 5. Handoff note for Antigravity prompts

Replace `[STITCH_REFERENCE_PATHS]` in every step/master prompt with this file's path: `docs/design/VARUNA_DESIGN_SYSTEM.md`. Keep the Apple motion doc alongside it as `docs/design/apple-design.md` and reference both in Step 01/02's "Reads" section — the analysis step should map §4 of this doc directly onto the component-by-component build order in Steps 06–08.
