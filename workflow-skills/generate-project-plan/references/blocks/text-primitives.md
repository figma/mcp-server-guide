# Block: Text primitives (body, H3, bulleted list)

The text elements that appear inside almost every section.

## Typography constants — STRICT (matches reference board)

| Element | When to use | Font | Size | Color |
|---|---|---|---|---|
| H1 | Board metadata strip | Inter Medium | 64 | Charcoal `#1E1E1E` |
| H2 | Section title (top of every section) | Inter Medium | 40 | Charcoal `#1E1E1E` |
| H3 — full-width subhead | Sub-section header in single-column context (e.g. "Resources" inside Motivation) | Inter Medium | **40** | Charcoal `#1E1E1E` |
| H3 — nested-section header | First text inside a child section (e.g. "Design Decision 1: Delivery Surface") | Inter Medium | **32** | Charcoal `#1E1E1E` |
| H3 — column title | Title of a column in a 2/3/4-col multi-column-text layout (e.g. "Goals", "Risks", "Open Questions") | Inter Medium | **24** | Charcoal `#1E1E1E` |
| Body | Paragraphs, list items | Inter Medium | 16 | Charcoal `#1E1E1E` |
| Table cell | Header AND body cells | **Inter Bold** | 16 | Header text + body text both Charcoal `#1E1E1E` |

> **Why three different H3 sizes?** The reference board uses 40px for sub-section heads inside an otherwise full-width section (matches H2 visually for emphasis). Column titles in narrow contexts must be 24px so they don't wrap or overflow. Nested-section headers sit between — 32px reads as a section header without overflowing the child section.

All text uses the same font family and style. Size is the only variable for headers.

**Load the font ONCE per `use_figma` script**, before creating any text:

```js
const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);
```

## Body paragraph

```js
const body = figma.createText();
body.fontName = font;
body.fontSize = 16;
body.characters = BODY_TEXT;
body.fills = [{ type: 'SOLID', color: CHARCOAL }];
body.textAutoResize = 'HEIGHT';
section.appendChild(body);
body.x = 32;
body.y = h2.y + h2.height + 16;
body.resize(800 - 64, body.height); // wrap at inner width = 736
```

## H3 subheader — pick the size for the context

```js
// Full-width subhead inside a single-column section (e.g. "Resources" in Motivation)
const h3Full = figma.createText();
h3Full.fontName = font;
h3Full.fontSize = 40;                          // STRICT: 40, NOT 24
h3Full.characters = "Resources";
h3Full.fills = [{ type: 'SOLID', color: CHARCOAL }];
section.appendChild(h3Full);
h3Full.x = 32;
h3Full.y = body.y + body.height + 24;

// Nested-section header (e.g. "Design Decision 1: Delivery Surface")
h3Nested.fontSize = 32;                        // STRICT: 32 (fits in 736-wide child section)

// Column title in a multi-column layout (e.g. "Goals", "Risks", "Open Questions")
h3Col.fontSize = 24;                           // STRICT: 24 (fits in 224-px columns without wrapping)
```

## Bulleted list

FigJam text supports list formatting via `setRangeListOptions`. Each line is a list item. Load font first.

```js
const items = ["Item one", "Item two", "Item three"];
const text = items.join('\n');

const list = figma.createText();
list.fontName = font;
list.fontSize = 16;
list.characters = text;
list.fills = [{ type: 'SOLID', color: CHARCOAL }];
list.textAutoResize = 'HEIGHT';
list.setRangeListOptions(0, text.length, { type: 'UNORDERED' });
list.setRangeIndentation(0, text.length, 1);
section.appendChild(list);
list.x = 32;
list.y = h3.y + h3.height + 16;
list.resize(800 - 64, list.height);
```

## Ordered list

Same as bulleted, but `type: 'ORDERED'`.

```js
list.setRangeListOptions(0, text.length, { type: 'ORDERED' });
```

## Stacking rule — STRICT 24px between blocks

Every gap between sibling blocks inside a section is **24px**. No exceptions. Use `prevChild.y + prevChild.height + 24`.

| From | To | Gap |
|---|---|---|
| Section top | H2 (first child) | 32 (= section padding) |
| H2 | body / intro / H3 / table / first column | **24** |
| Body | H3 | **24** |
| H3 (40/32/24px) | body / table / list / column | **24** |
| Body | body | **24** |
| List | next block | **24** |
| Last child | Section bottom | 32 (= section padding) |

**NEVER use a fixed offset.** Read `prevChild.height` after the font size is set, then add 24. If you later change a header's `fontSize`, you must re-position every downstream child or they'll overlap.

## Pre-flight checklist

- [ ] Font loaded before any `characters` / `fontSize` / `fills` on text nodes.
- [ ] Every text node appended to its parent BEFORE setting `x`/`y` / `resize`.
- [ ] `textAutoResize = 'HEIGHT'` + `resize(w, text.height)` for wrapped body / list nodes. H2/H3 use `textAutoResize = 'WIDTH_AND_HEIGHT'` or skip resize if they fit on one line.
- [ ] Return text node IDs in `mutatedNodeIds`.
