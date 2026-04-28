# Block: Metadata strip

The H1 project title + 4 body texts (Owner / Status / Last updated / Source) at the top of the **column wrapper**. NOT a standalone section, NOT positioned at the page origin — they are the first children of the unlabeled white column wrapper SECTION.

## Structure

Not a section — just five TEXT nodes positioned at the page top starting at `(0, 0)`.

| Element | Font size | Position (local to column wrapper) |
|---|---|---|
| Project title (H1) | **40** Inter Medium | `(64, 64)` — column wrapper padding |
| Owner | 16 | At `(64, h1.y + h1.height + 16)` — start of body row |
| Status | 16 | Right of Owner with 32px gap |
| Last updated | 16 | Right of Status with 32px gap |
| Source PRD link | 16, underlined | Right of Last updated with 32px gap |

H1 is **40px** (NOT 64). 64 doesn't fit inside the 800-wide column wrapper for typical project titles. 40 matches H2 size visually but the placement at the top of the wrapper makes it read as the title.

Total metadata-block height (top of wrapper to bottom of body row): `64 + 48 + 16 + 19 = 147` (with 64 padding above, then 64 padding below the body row → first section starts at y = 211).

## Positioning logic (children of the column wrapper)

```js
const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);

const PAD = 64; // column wrapper padding

// H1 project title — first child of the column wrapper at (PAD, PAD)
const title = figma.createText();
title.fontName = font;
title.fontSize = 40;                                      // STRICT — 40, not 64
title.characters = projectTitle;
title.fills = [{ type: 'SOLID', color: CHARCOAL }];
title.textAutoResize = 'WIDTH_AND_HEIGHT';
columnWrapper.appendChild(title);
title.x = PAD;
title.y = PAD;

// Body row — Owner / Status / Last updated / PRD link, 32px gap
const rowY = title.y + title.height + 16;
const labels = [
  { text: "Owner: " + ownerName },
  { text: "Status: Draft" },
  { text: "Last updated: " + new Date().toISOString().slice(0, 10) },
  { text: "Source: " + prdPath, underline: true },
];

let rowX = 0;
const createdIds = { title: title.id };
const rowIds = {};
for (const [i, item] of labels.entries()) {
  const t = figma.createText();
  t.fontName = font;
  t.fontSize = 16;
  t.characters = item.text;
  t.fills = [{ type: 'SOLID', color: CHARCOAL }];
  if (item.underline) {
    t.setRangeTextDecoration(0, t.characters.length, 'UNDERLINE');
  }
  t.textAutoResize = 'WIDTH_AND_HEIGHT';
  columnWrapper.appendChild(t);
  t.x = rowX;
  t.y = rowY;
  rowX += t.width + 32;
  rowIds["row" + i] = t.id;
}

// First content section starts at: rowY + body.height + 64 (gutter)

return { createdNodeIds: { title: title.id, ...rowIds } };
```

Notes:
- The nodes are children of the **column wrapper** SECTION, not the page.
- They sit at the top of the wrapper (above the 6 content sections), with the same 64px padding as the rest of the wrapper.
- No separate background fill — they inherit the wrapper's white fill.

## Status values

- `"Draft"` — initial
- `"In review"`
- `"Approved"`
- `"In progress"`
- `"Shipped"`

Always start with `"Draft"`.

## Missing fields

- No owner → `"Owner: TBD"`
- No PRD path → omit the PRD link entirely; shrink the row.
- `Last updated` — always set at generation time.

## Pre-flight checklist

- [ ] Font loaded before any text creation.
- [ ] All five (or four if PRD missing) text nodes created.
- [ ] H1 at `(0, 0)`; body row at `y = title.height + 16`.
- [ ] PRD link has underline via `setRangeTextDecoration`.
- [ ] Return all node IDs in `createdNodeIds`.
