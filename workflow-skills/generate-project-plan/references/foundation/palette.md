# Palette

> **STRICT DEFAULT — DO NOT DEVIATE WITHOUT USER OVERRIDE.**
>
> Project plan sections use a **pale palette** that visually pairs with the architecture-diagram subgraph wrappers. The FigJam SECTION palette (`#CDF4D3`, `#C2E5FF`, `#DCCCFF`, `#FFE0C2`, etc.) is **too saturated** for project-plan boards — it clashes with the diagram colors that `generate_diagram` produces. Use the `ARCH_PALE` palette below instead.
>
> Two of these colors (`#EBFFEE` for green, `#F8F5FF` for violet) are pulled directly from `share/mermaid/src/mermaid_v2/diagrams/processors/architecture/constants.ts` — they are the section-wrapper fills the architecture layout uses for `client` and `service` subgraphs. The rest are observed from a canonical reference board.

All palette colors use **`hex/255` notation** — e.g. `{r: 0xEB/255, g: 0xFF/255, b: 0xEE/255}`. Rounded decimals render as "Custom" in FigJam.

Helper:

```js
const h = (r, g, b) => ({ r: r/255, g: g/255, b: b/255 });
const CHARCOAL = h(0x1E, 0x1E, 0x1E);
const WHITE    = h(0xFF, 0xFF, 0xFF);
```

## ARCH_PALE — section background palette (THE canonical palette)

```js
const ARCH_PALE = {
  white:    h(0xFF, 0xFF, 0xFF),  // gateway, external, diagram sections
  green:    h(0xEB, 0xFF, 0xEE),  // = architecture client section wrapper
  violet:   h(0xF8, 0xF5, 0xFF),  // = architecture service section wrapper
  blueLite: h(0xF5, 0xFB, 0xFF),  // very pale blue (pairs with diagram datastore #BDE3FF)
  blue:     h(0xDB, 0xF0, 0xFF),  // pale blue, slightly more saturated
  orange:   h(0xFF, 0xF7, 0xF0),  // pale peach
  teal:     h(0xF1, 0xFE, 0xFD),  // very pale teal
  yellow:   h(0xFF, 0xFB, 0xF0),  // very pale yellow
  pink:     h(0xFF, 0xEE, 0xF8),  // derived pale pink
  red:      h(0xFF, 0xEE, 0xE8),  // derived pale red/coral
};
```

## Architecture diagram node fills (DO NOT MODIFY)

These come from `CATEGORY_DEFAULT_STYLES` in the architecture constants. `generate_diagram` applies them automatically — never override.

```js
const ARCH_NODE_FILLS = {
  client:    h(0xAF, 0xF4, 0xC6),  // mint green (rounded rectangle)
  gateway:   h(0xFF, 0xFF, 0xFF),  // white (square; diamond if labeled "Load Balancer" / "ALB" / "LB")
  service:   h(0xE4, 0xCC, 0xFF),  // light purple (square)
  datastore: h(0xBD, 0xE3, 0xFF),  // light blue (cylinder / ENG_DATABASE)
  external:  h(0xFF, 0xFF, 0xFF),  // white (PREDEFINED_PROCESS / 3D-stacked)
  async:     h(0xBD, 0xE3, 0xFF),  // light blue (ENG_QUEUE / stadium shape)
};
```

Architecture **subgraph section wrappers** (only client and service get wrappers — gateway/datastore/external/async are bare shapes):

```js
const ARCH_SECTION_WRAPPERS = {
  client:  h(0xEB, 0xFF, 0xEE),  // = ARCH_PALE.green
  service: h(0xF8, 0xF5, 0xFF),  // = ARCH_PALE.violet
};
```

## Sticky palette

For sticky-column blocks (success metrics, risks, open questions). Stickies use a brighter palette than sections:

```js
const STICKY = {
  white:  h(0xFF, 0xFF, 0xFF),
  gray:   h(0xE6, 0xE6, 0xE6),
  green:  h(0xB3, 0xEF, 0xBD),
  teal:   h(0xB3, 0xF4, 0xEF),
  blue:   h(0xA8, 0xDA, 0xFF),
  violet: h(0xD3, 0xBD, 0xFF),
  pink:   h(0xFF, 0xA8, 0xDB),
  red:    h(0xFF, 0xB8, 0xA8),
  orange: h(0xFF, 0xD3, 0xA8),
  yellow: h(0xFF, 0xE2, 0x99),
};
```

## Table header palette — STRICT: light fill + dark text + Bold font

> **The reference board uses a TWO-TONE per-section palette: section background = ARCH_PALE (very pale), table header = matching FigJam SECTION palette (mid-tone, same hue), table cell text = `#1E1E1E` charcoal.** Do NOT use dark fills with white text — that pattern is for FigJam's standalone tables, not for project-plan boards. The pale-on-pale two-tone is what makes the board feel cohesive.

```js
const TABLE_HEADER = {
  // Header row uses the FigJam SECTION palette — same hue as parent section, slightly more saturated
  lightGray:   { fill: h(0xD9, 0xD9, 0xD9), text: CHARCOAL },
  lightGreen:  { fill: h(0xCD, 0xF4, 0xD3), text: CHARCOAL },
  lightTeal:   { fill: h(0xC6, 0xFA, 0xF6), text: CHARCOAL },
  lightBlue:   { fill: h(0xC2, 0xE5, 0xFF), text: CHARCOAL },
  lightViolet: { fill: h(0xDC, 0xCC, 0xFF), text: CHARCOAL },
  lightPink:   { fill: h(0xFF, 0xC2, 0xEC), text: CHARCOAL },
  lightRed:    { fill: h(0xFF, 0xCD, 0xC2), text: CHARCOAL },
  lightOrange: { fill: h(0xFF, 0xE0, 0xC2), text: CHARCOAL },
  lightYellow: { fill: h(0xFF, 0xEC, 0xBD), text: CHARCOAL },
};
```

**Both header AND body cells use `Inter Bold` (NOT Medium).** Header text stays dark; body cell fill stays white (default).

## Section → default ARCH_PALE color (slug-based mapping)

```js
const SECTION_COLOR_BY_SLUG = {
  motivation:      ARCH_PALE.violet,    // ideation/intro — pairs with service
  context:         ARCH_PALE.white,
  goals:           ARCH_PALE.green,     // north star — pairs with client
  approach:        ARCH_PALE.green,
  alternatives:    ARCH_PALE.yellow,    // caution / "considered"
  designDecisions: ARCH_PALE.blue,      // structured decisions — pairs with datastore
  dependencies:    ARCH_PALE.orange,    // warnings / external dependencies
  implementation:  ARCH_PALE.violet,    // active work — pairs with service
  milestones:      ARCH_PALE.blue,      // time/sequencing
  rollout:         ARCH_PALE.orange,    // launches / staged
  risks:           ARCH_PALE.pink,      // hazards
  diagram:         ARCH_PALE.white,     // right-column diagram sections
};
```

## Section → matching table header (STRICT mapping)

When a section contains a table, the table header uses the FigJam SECTION palette color **matching the parent section's hue**.

```js
const TABLE_HEADER_BY_SECTION = {
  motivation:      TABLE_HEADER.lightViolet,
  context:         TABLE_HEADER.lightGray,
  goals:           TABLE_HEADER.lightGreen,
  approach:        TABLE_HEADER.lightGreen,
  alternatives:    TABLE_HEADER.lightYellow,
  designDecisions: TABLE_HEADER.lightBlue,
  dependencies:    TABLE_HEADER.lightOrange,
  implementation:  TABLE_HEADER.lightViolet,
  milestones:      TABLE_HEADER.lightBlue,
  rollout:         TABLE_HEADER.lightOrange,
  risks:           TABLE_HEADER.lightPink,
};
```

**Two-tone effect:** section bg = ARCH_PALE.X (very pale X-hue), table header = TABLE_HEADER.lightX (mid-tone X-hue), body cells white. This creates a coherent layered look across each section.

## Text colors

Body text inside any pale section is `CHARCOAL` (`#1E1E1E`). White text on dark table headers and saturated stickies. Never use a colored text fill.

## What NOT to use (and why)

| Wrong palette | Why not |
|---|---|
| `#CDF4D3` (FigJam lightGreen) | Too saturated. Mismatches diagram client wrapper `#EBFFEE`. |
| `#C2E5FF` (FigJam lightBlue) | Too saturated. Visual jump next to diagram subgraphs. |
| `#DCCCFF` (FigJam lightViolet) | Too saturated. Mismatches diagram service wrapper `#F8F5FF`. |
| `#FFE0C2` (FigJam lightOrange) | Too saturated. Use `#FFF7F0` instead. |
| `#FFC2EC` (FigJam lightPink) | Too saturated. Use `#FFEEF8`. |

If a user explicitly asks for the saturated FigJam palette, override per-section. **Otherwise, ARCH_PALE is mandatory.**
