# Block: Diagram section

A right-column SECTION that wraps a `generate_diagram` result. Architecture diagrams always go here; never on the left.

## When to use

- Current State Architecture
- Target State Architecture
- Key Flow diagrams (0–N)

## Properties

- Section fill: `ARCH_PALE.white` (right-column diagram sections are white).
- Section width: `max(RIGHT_COL_W_MIN, diag.width + 64)` after diagram is reparented.
- Section height: `h2.y + h2.height + 16 + diag.height + 32`.
- Section padding: 32 on all sides, same as left column.
- Placeholder: `true` until the diagram is successfully reparented.
- **STRICT — `section.name = ""`** (no FigJam title-bar label). The H2 text node inside is the only label.
- H2 header: section title (e.g. `"Current State Architecture"`).

## Three-call sequence

### Call 1 — Create skeleton section

`use_figma`:

```js
const section = figma.createSection();
section.name = ""; // STRICT — no section label
section.fills = [{ type: 'SOLID', color: SECTION.white }];
section.resizeWithoutConstraints(RIGHT_COL_W_MIN, 400);
section.x = 832; // RIGHT_COL_X
section.y = SECTION_TOP_Y + cumulative_y_right;
section.placeholder = true;

const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);

const h2 = figma.createText();
h2.fontName = font;
h2.fontSize = 40;
h2.characters = "Current State Architecture";
h2.fills = [{ type: 'SOLID', color: CHARCOAL }];
section.appendChild(h2);
h2.x = 32;
h2.y = 32;

return { createdNodeIds: { section: section.id, h2: h2.id } };
```

### Call 2 — `generate_diagram`

Use the `generate_diagram` MCP tool. Compose Mermaid from tech-context (see `generate-diagram` skill — re-load its SKILL.md first). Architecture diagrams:

```
{
  mermaid: "<mermaid source>",
  useArchitectureLayoutCode: "FIGMA_DIAGRAM_2026",
  editorType: "figjam"
}
```

Capture whatever the tool returns — diagram node ID, or nothing (then fall back to scanning page children).

### Call 3 — Reparent + resize

**CRITICAL: architecture diagrams are NOT a single node.** `generate_diagram` with `FIGMA_DIAGRAM_2026` produces:
- 1–2 subgraph `SECTION` nodes (only the categories Figma's layout promotes to sections — observed: `Clients` and `Core Services` become sections; others get inlined)
- Multiple `SHAPE_WITH_TEXT` nodes at the page level (one per remaining subgraph node)
- Multiple `CONNECTOR` nodes at the page level

Reparenting only one of these (e.g. the `Core Services` subgraph) breaks the diagram. You MUST wrap **all** new page-level nodes.

**Flow:**

1. **Collect all new page-level nodes.** Exclude your known plan nodes (metadata strip + previously-created sections). Everything else is part of the diagram.
2. **Compute the bounding box** across all diagram nodes.
3. **Create a new section** (or resize the existing placeholder) sized to `bboxW + 64 × bboxH + 56 + 64` (64 = padding, 56 = H2 + gap).
4. **Reparent each diagram node**: `section.appendChild(n); n.x = (originalPageX - minX) + 32; n.y = (originalPageY - minY) + 32 + 56`.
5. **Force connectors to re-route** after moving their endpoints (see trap below).

```js
const h = (r, g, b) => ({ r: r/255, g: g/255, b: b/255 });
const CHARCOAL = h(0x1E, 0x1E, 0x1E);
const WHITE = h(0xFF, 0xFF, 0xFF);

// Exclude your plan's known node IDs (sections + metadata strip)
const planIds = new Set([/* ...your plan IDs... */]);
const diagramNodes = figma.currentPage.children.filter(n => !planIds.has(n.id));

let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
for (const n of diagramNodes) {
  minX = Math.min(minX, n.x);
  minY = Math.min(minY, n.y);
  maxX = Math.max(maxX, n.x + n.width);
  maxY = Math.max(maxY, n.y + n.height);
}
const bboxW = maxX - minX;
const bboxH = maxY - minY;

const SECTION_PAD = 32;
const HEADER_BLOCK = 56; // 40 H2 + 16 gap

const section = figma.createSection();
section.name = ""; // STRICT — no section label
section.fills = [{ type: 'SOLID', color: WHITE }];
section.resizeWithoutConstraints(bboxW + 2*SECTION_PAD, bboxH + HEADER_BLOCK + 2*SECTION_PAD);
section.x = 832;
section.y = 152;

const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);

const h2 = figma.createText();
h2.fontName = font;
h2.fontSize = 40;
h2.characters = "Target State Architecture";
h2.fills = [{ type: 'SOLID', color: CHARCOAL }];
h2.textAutoResize = 'WIDTH_AND_HEIGHT';
section.appendChild(h2);
h2.x = SECTION_PAD;
h2.y = SECTION_PAD;

const dxBase = -minX + SECTION_PAD;
const dyBase = -minY + SECTION_PAD + HEADER_BLOCK;

for (const n of diagramNodes) {
  const newLocalX = n.x + dxBase;
  const newLocalY = n.y + dyBase;
  section.appendChild(n);
  n.x = newLocalX;
  n.y = newLocalY;
}
section.placeholder = false;
```

### CRITICAL TRAP — Connector re-routing after reparent (delete + recreate is the reliable fix)

Setting `n.x`/`n.y` on a `CONNECTOR` node during reparent "pins" its bounding box to bogus coordinates and breaks its auto-routing.

**The cheap fix (`c.connectorStart = c.connectorStart`) is NOT reliable for long-bend connectors.** Empirical finding: short connectors (single-bend, both endpoints close) re-route fine via the assign-to-self trick. **Long-bend connectors that span large distances (e.g. service → datastore across multiple lanes) retain stale elbow waypoints and end up with negative y-coordinates, extending hundreds of pixels above the section.**

**Reliable fix: delete every connector and recreate from spec.** This is the STRICT default for diagram reparenting in this skill.

```js
const fontMedium = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(fontMedium);

const connectors = section.children.filter(c => c.type === 'CONNECTOR');

// 1. Capture each connector's full spec BEFORE deletion
const specs = connectors.map(c => ({
  start: { endpointNodeId: c.connectorStart.endpointNodeId, magnet: c.connectorStart.magnet || 'AUTO' },
  end:   { endpointNodeId: c.connectorEnd.endpointNodeId,   magnet: c.connectorEnd.magnet   || 'AUTO' },
  lineType: c.connectorLineType,
  strokes: JSON.parse(JSON.stringify(c.strokes)),
  strokeWeight: c.strokeWeight,
  dashPattern: c.dashPattern ? Array.from(c.dashPattern) : null,
  startStrokeCap: c.connectorStartStrokeCap,
  endStrokeCap: c.connectorEndStrokeCap,
  // Label: prefer text.characters, fall back to name (the Mermaid label is in name)
  label: (c.text && c.text.characters) ? c.text.characters : c.name,
  name: c.name,
}));

// 2. Delete the broken connectors
for (const c of connectors) c.remove();

// 3. Recreate fresh inside the section
for (const s of specs) {
  const c = figma.createConnector();
  section.appendChild(c);
  c.connectorStart = s.start;
  c.connectorEnd = s.end;
  if (s.lineType) c.connectorLineType = s.lineType;
  if (s.strokes) c.strokes = s.strokes;
  if (s.strokeWeight) c.strokeWeight = s.strokeWeight;
  if (s.dashPattern && s.dashPattern.length) c.dashPattern = s.dashPattern;
  if (s.startStrokeCap) c.connectorStartStrokeCap = s.startStrokeCap;
  if (s.endStrokeCap) c.connectorEndStrokeCap = s.endStrokeCap;
  c.name = s.name;
  if (s.label) {
    // STRICT — fresh connector text has NO usable defaults. Set ALL THREE explicitly:
    c.text.fontName = fontMedium;                                  // (1) loaded font
    c.text.fontSize = 14;                                          // (2) labels render at 14px
    c.text.characters = s.label;                                   // (3) the label
    c.text.fills = [{ type: 'SOLID', color: CHARCOAL }];           // (4) text color — DEFAULT IS EMPTY ARRAY
  }
}
```

### Why the assign-to-self trick alone fails

`c.connectorStart = c.connectorStart` triggers a re-route, but the elbow control points (the bend waypoints) are cached separately and don't reset. For an L-shaped or U-shaped connector, the cached waypoint may sit hundreds of pixels away from the new endpoint positions, leaving the connector visually broken with the bbox extending outside the section.

`figma.createConnector()` produces a connector with no cached waypoints — the routing recomputes from scratch based on the current endpoint positions. That's why delete + recreate is reliable.

### Alternative — never set x/y on connectors during the move loop

If you skip CONNECTORs entirely in the reparent x/y-setting loop and only call appendChild + the assign-to-self trick, **short connectors will work**. Long-bend connectors will still break. Delete + recreate covers both cases.

### Connector text — fontName + fontSize + fills are ALL mandatory

A freshly-created connector's `text` sublayer is a stub:
- `fontName` is set to a default that **may not be loaded** — you must reassign explicitly to a loaded font.
- `fontSize` is missing/zero — set to 14 explicitly.
- `fills` is an **empty array `[]`** — the label renders with NO COLOR (transparent) and is invisible. Set `text.fills = [{ type: 'SOLID', color: CHARCOAL }]` explicitly.

If you set only `characters` and `fontName`, the label will appear correctly when you read `c.text.characters` back, BUT will not render visually. This is the easiest-to-miss bug in this whole skill — verify with a screenshot, not a use_figma read.

The four-line pattern (with comments) belongs at every connector creation site:

```js
c.text.fontName   = { family: 'Inter', style: 'Medium' }; // already loaded
c.text.fontSize   = 14;
c.text.characters = label;
c.text.fills      = [{ type: 'SOLID', color: { r: 0x1E/255, g: 0x1E/255, b: 0x1E/255 } }];
```

## Failure handling

If `generate_diagram` fails: do NOT leave the section with `placeholder = true`. Instead, in the reparent call, create a TEXT node explaining the failure and treat it as the diagram:

```js
const errorText = figma.createText();
errorText.fontName = font;
errorText.fontSize = 16;
errorText.characters = "Diagram generation failed: " + errMessage + ". Regenerate manually.";
errorText.fills = [{ type: 'SOLID', color: CHARCOAL }];
section.appendChild(errorText);
errorText.x = 32;
errorText.y = headerBottom + 16;
errorText.resize(RIGHT_COL_W_MIN - 64, errorText.height);

section.resizeWithoutConstraints(RIGHT_COL_W_MIN, errorText.y + errorText.height + 32);
section.placeholder = false;
```

Continue to the next diagram.

## Pre-flight checklist

- [ ] Skeleton section created with white fill + H2 header.
- [ ] `generate_diagram` called with the correct `editorType: "figjam"` and architecture layout code.
- [ ] Diagram reparented with `appendChild` BEFORE setting `x`/`y`.
- [ ] Section resized to `max(1200, diag.width + 64) × (diag.y + diag.height + 32)`.
- [ ] `placeholder = false` at end of reparent call.
- [ ] Failure leaves a text placeholder, not an empty section.
- [ ] Return `section.id` + `diag.id` (or `errorText.id`) in `mutatedNodeIds`.
