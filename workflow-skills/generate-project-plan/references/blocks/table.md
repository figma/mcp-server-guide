# Block: Table

A FigJam `TABLE` node with a colored header row whose palette inherits from the parent section.

## When to use

- Resources (columns: Type, Link, Description)
- Goals / Non-goals (columns: Goal, Description)
- Metrics (columns: Type, Metric)
- Dependencies (columns: Type, Dependency, Notes)
- Rollout stages (columns: Stage, Activities, Metric to Watch, Gate)
- Milestones (columns: #, Phase, Timeline, Description)
- Tradeoffs (inside a nested Design Decision section)

Use a table when the data is inherently **structured rows × columns** and every row answers the same set of questions. Otherwise prefer body text or multi-column text.

## Key API facts

- FigJam only (`figma.createTable(rows, cols)`). Not available in Figma Design.
- `table.width` and `table.height` are **read-only**. Use `resizeRow(i, h)` and `resizeColumn(j, w)`.
- Rows / columns cannot go below their minimum size.
- `table.cellAt(r, c)` returns a `TABLE_CELL` node with a `text` sublayer. Load the cell's font before setting `text.characters` or `text.fills`.
- Tables do NOT have strokes. Cells have fills only.

## Palette inheritance — STRICT (two-tone, light-on-pale)

The header row uses the FigJam **SECTION palette** color matching the parent section's hue. NOT the dark-saturated palette. See `TABLE_HEADER_BY_SECTION` in [foundation/palette.md](../foundation/palette.md).

- `goals` section bg `#EBFFEE` (ARCH_PALE.green) → header fill `#CDF4D3` (lightGreen) + `#1E1E1E` charcoal text
- `dependencies` section bg `#FFF7F0` (ARCH_PALE.orange) → header fill `#FFE0C2` (lightOrange) + charcoal text
- `motivation` section bg `#F8F5FF` (ARCH_PALE.violet) → header fill `#DCCCFF` (lightViolet) + charcoal text
- Body cells: default fill (white). Text: `#1E1E1E` (charcoal).

**Both header AND body cells use `Inter Bold` 16px.** This matches the reference board's table convention.

## Create script

```js
// rows[0] is the header row.
const rows = [
  ['Type', 'Link', 'Description'],
  ['PRD', 'https://…', 'Markdown → FigJam sync'],
  ['Design doc', 'https://…', 'Architecture proposal'],
];
const numRows = rows.length;
const numCols = rows[0].length;

const table = figma.createTable(numRows, numCols);

// STRICT: load Inter Bold (NOT Medium) — both header and body cells use Bold
const fontBold = { family: 'Inter', style: 'Bold' };
await figma.loadFontAsync(fontBold);

// Palette lookup based on parent section
const headerPreset = TABLE_HEADER_BY_SECTION[sectionSlug]; // e.g. TABLE_HEADER.lightGreen
const CHARCOAL_FILL = { type: 'SOLID', color: CHARCOAL };

for (let r = 0; r < numRows; r++) {
  for (let c = 0; c < numCols; c++) {
    const cell = table.cellAt(r, c);
    cell.text.fontName = fontBold;             // STRICT: Bold for every cell
    cell.text.fills = [CHARCOAL_FILL];         // STRICT: charcoal text in every cell
    if (r === 0) {
      cell.fills = [{ type: 'SOLID', color: headerPreset.fill }]; // light hue
    }
    cell.text.characters = rows[r][c];
  }
}

// Append to section and position (appendChild BEFORE x/y)
section.appendChild(table);
table.x = 32;
table.y = prevChildBottom + 16;

// Width: table is content-sized; columns can be resized explicitly if needed.
// For a standard 3-col table inside an 800-wide section with 32 padding:
// target total width = 736, so each column ≈ 245. Adjust based on data.
table.resizeColumn(0, 160);
table.resizeColumn(1, 240);
table.resizeColumn(2, 336);
```

## Column width heuristics

| N columns | Target total width | Distribution |
|---|---|---|
| 2 | 736 | 240 / 496 (label / description) |
| 3 | 736 | 160 / 240 / 336 (short / medium / long) |
| 4 | 736 | 120 / 180 / 180 / 256 |
| 5 | 736 | 100 / 140 / 160 / 160 / 176 |

Adjust if one column clearly needs more room (e.g. Description always wider than #).

## Ordered / numbered rows

For Milestones (e.g. numbered `#` column), the first column's values are `"1"`, `"2"`, etc. — just strings. No list formatting needed.

## Multi-line cell text

Cells wrap automatically based on the column width. Use `\n` in `text.characters` for explicit line breaks.

## Pre-flight checklist

- [ ] Table created with exact `(numRows, numCols)` matching the data.
- [ ] **`Inter Bold` loaded** BEFORE setting any cell text (NOT Medium — STRICT).
- [ ] Header row has explicit `cell.fills` (light-tone matching section) + dark charcoal `cell.text.fills`.
- [ ] Body cells have `cell.text.fills = CHARCOAL` and no explicit `cell.fills` (default white).
- [ ] Every cell's `text.fontName = { family: 'Inter', style: 'Bold' }`.
- [ ] Palette colors use `hex/255` notation.
- [ ] Appended to section BEFORE setting `x`/`y`.
- [ ] Columns resized if defaults don't match the content.
- [ ] Table ID returned in `mutatedNodeIds`.
