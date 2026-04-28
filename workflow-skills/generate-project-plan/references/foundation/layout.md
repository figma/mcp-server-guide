# Layout

Canvas geometry, sizing, positioning.

## Constants

```js
const LEFT_COL_X = 0;
const LEFT_COL_W = 800;
const GUTTER_X   = 32;
const RIGHT_COL_X = LEFT_COL_X + LEFT_COL_W + GUTTER_X; // 832
const RIGHT_COL_W_MIN = 1200;
const GUTTER_Y   = 32;
const SECTION_PAD = 32; // inner padding, all four sides
const METADATA_STRIP_H = 120;
const SECTION_TOP_Y = METADATA_STRIP_H + GUTTER_Y; // 152
```

## Canvas map

```
+--------------------------------------------------------+
|  (0, 0)                                                |
|  [ Board metadata strip — full width, ~120px tall ]    |
|                                                        |
|  x=0             x=832                                 |
|  +-----------+   +---------------------------+         |
|  | LEFT COL  |   | RIGHT COL                 |         |
|  | 800 wide  |   | width driven by diagrams  |         |
|  |  [sec 1]  |   |  [Current State]          |         |
|  |    ↓32    |   |        ↓32                |         |
|  |  [sec 2]  |   |  [Target State]           |         |
|  |    ↓32    |   |        ↓32                |         |
|  |   ...     |   |  [Key Flow 1]             |         |
|  +-----------+   +---------------------------+         |
+--------------------------------------------------------+
```

## Left column stacking

```js
curY_left = SECTION_TOP_Y;
for (const section of leftSectionsInOrder) {
  section.x = LEFT_COL_X;
  section.y = curY_left;
  // After fill, section.resizeWithoutConstraints(LEFT_COL_W, section_h).
  curY_left += section.height + GUTTER_Y;
}
```

## Right column stacking

```js
curY_right = SECTION_TOP_Y;
for (const section of rightSectionsInOrder) {
  section.x = RIGHT_COL_X;
  section.y = curY_right;
  // After fill, section.resizeWithoutConstraints(max(RIGHT_COL_W_MIN, diag.width + 64), h).
  curY_right += section.height + GUTTER_Y;
}
```

Right column `x` is fixed at 832 regardless of section width. Wider sections extend further right.

## Inner padding rule

Every top-level section: first child's `x = 32, y = 32`. Last child's bottom edge + 32 = section height.

## Sub-column positioning (for 3- or 4-column layouts inside a section)

For a 3-column layout inside an 800-wide section:
- Inner width = `800 - 2 * 32 = 736`
- With 2 gutters of 32: each column = `(736 - 64) / 3 = 224` wide
- Column x positions: `32`, `288`, `544`

For a 4-column layout:
- With 3 gutters of 32: each column = `(736 - 96) / 4 = 160` wide
- Column x positions: `32`, `224`, `416`, `608`

See `blocks/multi-column-text.md` for formulas at runtime.

## Section hug sizing

After appending children, compute:
```js
const maxChildBottom = Math.max(...section.children.map(c => c.y + c.height));
section.resizeWithoutConstraints(LEFT_COL_W, maxChildBottom + SECTION_PAD);
```

Sections do NOT auto-grow — always explicit `resizeWithoutConstraints`.

## Placeholder lifecycle

- Skeleton pass: `section.placeholder = true`.
- End of fill pass for that section: `section.placeholder = false`.
- NEVER leave a section with `placeholder = true` at end-of-run.

## Re-stack pass

After all left-column fills, a re-stack pass fixes cumulative Y based on actual post-resize heights:

```js
let y = SECTION_TOP_Y;
for (const id of leftColumnSectionIdsInOrder) {
  const sec = await figma.getNodeByIdAsync(id);
  sec.y = y;
  sec.x = 0;
  y += sec.height + GUTTER_Y;
}
```

Run this once between the left-column fill pass and the diagram pass.
