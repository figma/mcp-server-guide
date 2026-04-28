# Plugin API Traps

The FigJam Plugin API accessed via `use_figma` has several dangerous mismatches between the top-level `figma-use/SKILL.md` rules and the per-node reference docs. Read this before writing any `use_figma` script for this skill.

## Trap 1 — `return` vs `figma.closePlugin()`

| File | Says |
|---|---|
| `figma-use/SKILL.md` rule #1 | **Use `return`** to send data back. Do NOT call `figma.closePlugin()`. Do NOT wrap in async IIFE. |
| `create-section.md` Key Points | "Always wrap code in an async IIFE" and "Always call `figma.closePlugin()`" |
| `create-sticky.md` Key Points | Same wrong guidance |
| `create-text.md` Key Points | Same wrong guidance |
| `create-connector.md` Key Points | Same wrong guidance |
| `create-table.md` Key Points | Same wrong guidance |
| `create-code-block.md` | Correct (uses `return`) |

**Rule:** `figma-use/SKILL.md` wins. When copying examples from the per-node docs, strip the IIFE wrapper and the `closePlugin()` call. Use `return { createdNodeIds: [...], mutatedNodeIds: [...] }`.

## Trap 2 — Atomic error semantics

A failing `use_figma` script makes **no changes** to the file. Do not retry blindly: read the error, fix the script, then retry. Because the file is untouched, there are no partial nodes to clean up.

## Trap 3 — `resizeWithoutConstraints` for sections

Sections do NOT support `resize()`. Use `section.resizeWithoutConstraints(w, h)`. `width` and `height` are read-only otherwise.

## Trap 4 — Coordinates are reparented by `appendChild`

When you call `parent.appendChild(node)`, the node's `x`/`y` becomes relative to the parent's coordinate space. For sections, `(0, 0)` is the section's top-left. **Call `appendChild` FIRST, then set `x`/`y`.** Setting position before appending leaves the node in a confusing coordinate frame.

## Trap 5 — Two-pass sticky layout

Sticky widths are fixed (240 or 416) but heights auto-grow when text overflows. Assuming a uniform 240×240 will cause overlaps.

```js
// Pass 1: create all stickies and set text/color
const stickies = [];
for (const label of labels) {
  const s = figma.createSticky();
  await figma.loadFontAsync(s.text.fontName);
  s.text.characters = label;
  stickies.push(s);
}

// Pass 2: now read actual .width / .height and position
for (const s of stickies) {
  // use s.width, s.height here — not 240×240
}
```

## Trap 6 — `hex/255` notation for palette colors

FigJam palette matching is exact. Rounded decimals make FigJam treat the color as "Custom" instead of a palette color.

```js
// WRONG — will render as Custom
{ r: 0.76, g: 0.89, b: 1.00 }

// CORRECT — matches the Light blue palette swatch
{ r: 0xC2/255, g: 0xE5/255, b: 0xFF/255 }
```

Use a helper:

```js
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 });
```

## Trap 7 — Font must be loaded before any text operation

```js
const text = figma.createText();
await figma.loadFontAsync(text.fontName);   // REQUIRED before `characters`, `fontSize`, etc.
text.characters = "Hello";
```

Not required for color-only changes (`text.fills = [...]`).

## Trap 8 — Connector `text.fontName` is invalid by default

A newly-created connector's `text.fontName` cannot be loaded directly. You MUST explicitly set `text.fontName` to a known loaded font, then set `text.characters`.

```js
const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);

const c = figma.createConnector();
c.connectorStart = { endpointNodeId: a.id, magnet: 'AUTO' };
c.connectorEnd   = { endpointNodeId: b.id, magnet: 'AUTO' };
c.text.fontName   = font;
c.text.characters = 'depends on';
```

Existing connectors with labels DO have valid `text.fontName` — load directly.

Also: **visible label is `connector.text.characters`, NOT `connector.name`**. `name` only changes the layers panel.

## Trap 9 — Position new top-level nodes away from `(0, 0)`

Nodes appended directly to a page default to `(0, 0)`. If content already exists there, the new node overlaps it. Scan `figma.currentPage.children` and pick a clear spot.

Nodes nested inside frames/sections don't have this problem — the parent positions them.

## Trap 10 — `layoutSizingHorizontal/Vertical = 'FILL'`

Set this AFTER `parent.appendChild(child)`. Setting before append throws. Same for `'HUG'` on non-auto-layout nodes.

## Trap 11 — `figma.currentPage = page` does NOT work

Use `await figma.setCurrentPageAsync(page)`. The sync setter throws `"Setting figma.currentPage is not supported"` in `use_figma`. `figma.currentPage` also resets to the first page at the start of every `use_figma` call.

## Trap 12 — `figma.notify()` throws

It's not implemented under `use_figma`. Never call it.

## Trap 13 — Return ALL created/mutated node IDs

`console.log()` output is NOT returned. The agent only sees the `return` value. Collect every affected node ID:

```js
return {
  createdNodeIds: [...],
  mutatedNodeIds: [...],
  // optional: counts, status, screenshot metadata
};
```

Downstream calls need these IDs to reference what was created.

## Trap 14 — Colors are 0–1, not 0–255

```js
// WRONG
{ r: 194, g: 229, b: 255 }

// CORRECT
{ r: 194/255, g: 229/255, b: 255/255 }
```

Color objects are `{ r, g, b }` only — no `a` field. Opacity goes at the paint level: `{ type: 'SOLID', color: {...}, opacity: 0.5 }`.

## Trap 15 — `fills` and `strokes` are read-only arrays

Clone, modify, reassign. Don't mutate in place.

```js
// WRONG
node.fills[0].opacity = 0.5;

// CORRECT
const fills = JSON.parse(JSON.stringify(node.fills));
fills[0].opacity = 0.5;
node.fills = fills;
```

## Trap 16 — Batch size

Keep each `use_figma` call to ≤10 logical operations (a "logical operation" ≈ create + configure + parent one node). Split large builds across multiple calls. Validate between.

## Trap 17 — Section resize after adding children

Sections DO NOT auto-grow. After `appendChild`, measure children and call `resizeWithoutConstraints` with `(maxChildRight + 32, maxChildBottom + 32)` to fit with 32px padding. Exception: sections that are part of a grid layout must keep uniform dimensions — don't hug individually.

## Trap 18 — Sticky palette ≠ section palette ≠ text palette

Three different palettes, all named from the same color names:

- **Sticky** palette (from `create-sticky.md`): 10 brighter colors — White, Gray `#E6E6E6`, Green `#B3EFBD`, Teal `#B3F4EF`, Blue `#A8DAFF`, Violet `#D3BDFF`, Pink `#FFA8DB`, Red `#FFB8A8`, Orange `#FFD3A8`, Yellow `#FFE299`.
- **Section** palette (from `create-section.md`): 10 lighter colors — White, Light gray `#D9D9D9`, Light green `#CDF4D3`, Light teal `#C6FAF6`, Light blue `#C2E5FF`, Light violet `#DCCCFF`, Light pink `#FFC2EC`, Light red `#FFCDC2`, Light orange `#FFE0C2`, Light yellow `#FFECBD`.
- **Text** palette (from `create-text.md`): 22 colors including Charcoal `#1E1E1E` (default; use this for body text unless specified otherwise).

Don't cross-pick — a "Blue" sticky is `#A8DAFF`, a "Blue" section is `#C2E5FF`, they are NOT the same.

## Trap 19 — Table sizing

Tables are FigJam-only (`figma.createTable(rows, cols)`). `width` and `height` are read-only. Use `resizeRow(i, h)` and `resizeColumn(j, w)`. Rows and columns cannot go below their minimum. `cellAt(r, c)` for cell access; load the cell's font before setting `text.characters` or `text.fills`.

## Trap 20 — The code block node is first-class, not a shape

`figma.createCodeBlock()`. Set `cb.code` (not `cb.text.characters`) and `cb.codeLanguage` from a fixed enum (`TYPESCRIPT`, `JAVASCRIPT`, `PYTHON`, `GO`, `RUST`, `RUBY`, `CSS`, `HTML`, `JSON`, `GRAPHQL`, `SQL`, `SWIFT`, `KOTLIN`, `CPP`, `BASH`, `PLAINTEXT`). No font loading required. FigJam-only.
