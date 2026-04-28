# Block: Top-level section

A FigJam Section node with a colored background, an H2 header as first child, 32px padding, and children laid out below the header.

## Definition

- **Node type:** `SECTION` (created with `figma.createSection()`).
- **Width:** left column = 800, right column = ≥1200 (driven by diagram width).
- **Fill:** `section.fills = [{ type: 'SOLID', color: SECTION_COLOR_BY_SLUG[slug] }]`. See [foundation/palette.md](../foundation/palette.md).
- **STRICT — no section label:** `section.name = ""`. Project-plan boards do **not** use FigJam's section title-bar label. The user-facing title is rendered as the H2 text node inside the section (see Header below). Setting `section.name` to anything non-empty produces a duplicate label that visually clutters the board.
- **Header:** an H2 text node as the section's **first child**, at `(32, 32)`. Header text is the user-facing title (e.g. `"Goals, Non-Goals & Success Metrics"`). This is the **only** label the section gets.
- **Padding:** 32px on all four sides. First child at `(32, 32)`; last child's bottom + 32 = section height.
- **Hug behavior:** sections do NOT auto-grow. Call `section.resizeWithoutConstraints(w, h)` after appending children.
- **Placeholder during build:** set `section.placeholder = true` in the skeleton pass. Set `section.placeholder = false` at the end of the fill pass for that section.

## Create script (skeleton pass)

```js
const section = figma.createSection();
section.name = ""; // STRICT — no FigJam section label; H2 text inside is the only title
section.fills = [{ type: 'SOLID', color: SECTION_COLOR_BY_SLUG.goals }];
section.resizeWithoutConstraints(800, 400); // DEFAULT_H — fill pass will overwrite
section.x = 0;
section.y = 152 + cumulative_y;
section.placeholder = true;
```

## Add the H2 header (first action in fill pass)

```js
const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);

const h2 = figma.createText();
h2.fontName = font;
h2.fontSize = 40;
h2.characters = "Goals, Non-Goals & Success Metrics"; // user-facing header
h2.fills = [{ type: 'SOLID', color: CHARCOAL }];
section.appendChild(h2);   // append FIRST
h2.x = 32;
h2.y = 32;
```

## Hug section after filling

After all children are appended and positioned:

```js
const maxBottom = Math.max(...section.children.map(c => c.y + c.height));
section.resizeWithoutConstraints(800, maxBottom + 32);
section.placeholder = false;
```

## Pre-flight checklist

- [ ] `section.name = ""` (no section title-bar label — STRICT).
- [ ] Fill is set via `hex/255` palette color (not rounded decimals).
- [ ] H2 is the first child.
- [ ] `appendChild` is called before setting `x`/`y` on any child.
- [ ] `resizeWithoutConstraints(w, h)` runs after all children are appended.
- [ ] `section.placeholder` is `false` at end of this section's fill.
- [ ] Return includes `section.id` in `mutatedNodeIds` (or `createdNodeIds` on skeleton pass).

## Right-column (diagram) section

Same as above but:
- `fill` = `ARCH_PALE.white`.
- Width = `max(RIGHT_COL_W_MIN, diag.width + 64)` after the diagram is reparented.
- `section.name = ""` (same rule — no title-bar label).
- See [blocks/diagram-section.md](diagram-section.md) for the reparent flow.
