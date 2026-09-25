# use_figma — Figma Plugin API Skill for FigJam

This skill contains FigJam-specific context for the `use_figma` MCP tool. The figma-use (load `readPowerSteering("figma", "figma-use.md")`) skill provides foundational context for plugin API execution via MCP as well as the full Figma plugin API for more advanced use-cases that are not described here.

**Always include `figma-use-figjam` in the comma-separated `skillNames` parameter when calling `use_figma` for FigJam operations. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-use-figjam`).** This is a logging parameter used to track skill usage — it does not affect execution.

> **FigJam URL is `figma.com/board/...`.** Do NOT call `figma.createPage()` in FigJam — it throws `TypeError: figma.createPage no such property 'createPage' on the figma global object`. `createPage()` is a Design-file API only (`figma.com/design/...`). FigJam files have a single implicit page; organize content with sections instead (see [create-section](#reference--create-sections)).

## Inspecting FigJam Files

**`get_figjam` is the inspection tool for FigJam files.** It returns the full node tree as XML, including IDs of pages, sections, stickies, connectors, and other nodes you need to reference in subsequent `use_figma` calls.

- **Use `get_figjam` upfront** before writing any `use_figma` code that needs to reference existing nodes (page IDs, section IDs, etc.). Don't try to discover IDs by running an inspection script — `console.log` output from `use_figma` is **not returned to the agent** (see figma-use Critical Rule #4 (load `readPowerSteering("figma", "figma-use.md")`)). Only the `return` value comes back.
- **`get_metadata` does NOT work on FigJam files** — it is design-mode only and will fail immediately with "unsupported for FigJam files".
- **`get_screenshot` requires a valid `nodeId`** — passing an empty nodeId returns "invalid nodeId" error. Get IDs from `get_figjam` first.
- If you forgot to `return` an ID from a previous `use_figma` call and need it now, call `get_figjam` rather than re-running an inspection script.

## Loading Reference Docs Efficiently

Load only the references your task needs — but when you do need to load multiple, **issue all reads in a single parallel tool-call batch**, not sequentially across turns. For a typical board-creation task, that means a single message containing reads for `plan-board-content` plus the 3-4 specific node-type references you'll use.

## Deferred Tools — Batch-Load Schemas

The Figma MCP tools (`use_figma`, `get_figjam`, `get_screenshot`, `get_metadata`, `create_new_file`, `whoami`) often appear as deferred tools that require `ToolSearch` to load their schemas before they can be called. **Load all schemas in a single `ToolSearch` call** using the `select:` syntax instead of one call per tool:

```
ToolSearch query="select:use_figma,get_figjam,get_screenshot,get_metadata,create_new_file"
```

Six sequential `ToolSearch` calls is six round trips before any work happens. One batched call is one round trip.

## Text Mutations — Canonical Recipe

Every FigJam text mutation (sticky/shape/label/table cell/connector text, standalone text nodes) follows the same recipe as Design files: load font → `await` → mutate → return affected IDs. Skipping the load throws `Cannot write to node with unloaded font "<family> <style>"`. See figma-use → gotchas.md → Canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`). FigJam-specific note: sublayer defaults vary (sticky → `Inter Medium`, shape → `Inter Medium`, connector → invalid until set), so always load from `node.text.fontName` rather than hardcoding `{ family: 'Inter', style: 'Regular' }`.

## Adding Images to a FigJam Board

**`upload_assets` is the ONLY supported way to add images to a FigJam file.** Do NOT use `figma.createImage()` or `figma.createImageAsync()` from inside `use_figma` — they are unsupported as image-upload entry points in FigJam. Call `upload_assets` with the FigJam `fileKey`; the tool returns single-use upload URLs that you POST raw image bytes to, and the image is committed and placed automatically. Pass `nodeId` (with `count: 1`) to attach the upload to an existing FigJam node as a fill; omit `nodeId` to drop the image onto the board as a new layer.

For the full request/response shape, see figma-use → api-reference.md → Images (load `readPowerSteering("figma", "figma-use.md")`).

## Reference Docs

- [plan-board-content](#reference--plan-content-for-figjam-boards) - Read this for any board content request — board template, retro, brainstorm, ice breaker, meeting board, scaffold
  - Covers planning of generated board content, including sequential outline, sections, intents, and hierarchical text
  - Delegates to other references for specific API details
- [create-section](#reference--create-sections) — Create and configure FigJam sections (sizing, naming, colors, content visibility, organizing nodes, column layouts)
- [create-sticky](#reference--create-sticky-notes) — Create and configure FigJam sticky notes (colors, sizing, text, author visibility, batch creation)
- [create-connector](#reference--create-connectors) — Create and configure FigJam connectors (endpoints, arrows, line types, labels, colors, diagram wiring)
- [create-text](#reference--create-text-nodes) — Create and configure FigJam text nodes (font loading, preset fonts and colors, sizing, lists, mind map operations)
- [position-figjam-nodes](#reference--figjam-node-positioning-tutorial) — Position, size, and reparent nodes on the canvas (including within sections)
- [create-shape-with-text](#reference--create-shapes-with-text) — Create and configure FigJam shapes with embedded text (shape types, color presets, sizing to fit text, diagram layouts)
- [create-code-block](#reference--create-code-blocks) — Create and configure FigJam code block nodes (languages, syntax highlighting, positioning, embedding in sections)
- [create-table](#reference--create-tables) — Create and configure FigJam tables (rows, columns, cell text, color presets, resizing)
- [edit-text](#reference--text-operations) — Edit existing text nodes (font loading, styled ranges, find/replace, FigJam Charcoal default color)
- [create-label](#reference--create-label-nodes) — Create and configure FigJam label nodes (small numbered/lettered circle callout markers, sequences, positioning)
- [batch-modify](#reference--batch-operations-pattern) — Patterns for modifying many existing nodes at once (bulk style changes, repositioning, property updates)
- [figjam-colors](#reference--figjam-colors) — Canonical FigJam color palettes for every node type (sticky, section, connector, shape, label) plus the `hex/255` notation rule and the `h()` helper

---

## Reference — Create Sections

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating, modifying, and organizing sections.

**Scope:** Sections are FigJam containers created with `figma.createSection()`. They organize related objects on the board. For creating stickies to place inside sections, see [create-sticky](#reference--create-sticky-notes). For creating text to place inside sections, see [create-text](#reference--create-text-nodes).

### Creating a Section

Create sections and resize them carefully according to the layout guidance in [plan-board-content](#reference--plan-content-for-figjam-boards).

```javascript
const section = figma.createSection()
section.name = 'My Section'

// Sections start very small — resize to a usable size
section.resize(400, 300)

console.log('Created section:', section.id, section.name, section.width, 'x', section.height)
figma.closePlugin()
```

### Stickies vs. Text Nodes as section content

Stickies and text play different roles. Before adding section child content, make sure to read and understand the usage guidance for each in [create-sticky](#reference--create-sticky-notes) and [create-text](#reference--create-text-nodes) skills.

### Naming

Section names should be **short, navigational identifiers** (e.g. "Brainstorm", "Action Items", "Went Well") — they are used for browsing and quick identification in FigJam's UI. The section name is NOT the user-facing header. Create a separate **H2 text node** inside the section for the visible, descriptive header. See [plan-board-content](#reference--plan-content-for-figjam-boards) for guidance on clearing section names when the section already has an internal title text node.

```javascript
const section = figma.createSection()
section.name = 'What went well' // Short navigational name

console.log('Section name:', section.name)
figma.closePlugin()
```

To rename an existing section:

```javascript
const section = await figma.getNodeByIdAsync('123:456')
if (section && section.type === 'SECTION') {
  console.log('Before:', section.name)
  section.name = 'Updated name'
  console.log('After:', section.name)
}
figma.closePlugin()
```

### Resizing

Sections support both `resize(width, height)` and `resizeWithoutConstraints(width, height)`. **Prefer `resize(...)`** — it matches the ergonomics of every other resizable node. Sections don't propagate constraints to their children, so the two methods behave identically on sections. Both width and height must be >= 0.01.

```javascript
const section = figma.createSection()
section.name = 'Wide section'
section.resize(800, 400)

console.log('Size:', section.width, 'x', section.height)
figma.closePlugin()
```

#### Resizing an Existing Section

Often when creating a section and adding content, the content will exceed the bounds of the section. To solve that, find the maximum extents of the section's children using their section-local coordinates, then resize the section to fit. Consider adding padding of at least 32px on all sides of the content within the section to prevent the content from appearing cramped.

Do not resize the section to hug its contents if it is meant to be a **participatory zone** (workshop, brainstorm, retro lane, feedback area — see [plan-board-content](#reference--plan-content-for-figjam-boards) for the participatory-zone pattern); those should be sized to expected activity, not pre-filled content. Also do not resize sections to hug content when they are part of a **grid layout** — sections in a grid must maintain uniform dimensions to preserve the rectangular appearance.

```javascript
const section = await figma.getNodeByIdAsync('123:456')
if (section && section.type === 'SECTION') {
  if (section.children.length < 1) {
    // for empty sections, choose a reasonable width and height based on the purpose
    section.resize(800, 400)
    figma.closePlugin()
    return
  }
  console.log('Before:', section.width, 'x', section.height)

  // Children's x/y are in section-local coordinates, so find the max extents from (0,0)
  let maxRight = 0
  let maxBottom = 0
  for (const child of section.children) {
    maxRight = Math.max(maxRight, child.x + child.width)
    maxBottom = Math.max(maxBottom, child.y + child.height)
  }

  const padding = 32
  section.resize(maxRight + padding, maxBottom + padding)
  console.log('After:', section.width, 'x', section.height)
}
figma.closePlugin()
```

### Color Palette

FigJam sections use a fixed palette of light tints. Set via the `fills` property. For the canonical palette across all FigJam node types, see [figjam-colors](#reference--figjam-colors).

When creating multiple sections, **vary the colors** across the palette to visually distinguish them — don't use the same color for every section. Only apply default color variety when the user hasn't specified colors.

**CRITICAL**: Use `hex/255` notation (e.g. `0xF5/255`) for exact palette matching — rounded decimals cause FigJam to treat the color as "custom" instead of a palette color.

| Color        | Hex       |
| ------------ | --------- |
| White        | `#FFFFFF` |
| Light gray   | `#F9F9F9` |
| Light green  | `#EBFFEE` |
| Light teal   | `#F1FEFD` |
| Light blue   | `#F5FBFF` |
| Light violet | `#F8F5FF` |
| Light pink   | `#FFF0FA` |
| Light red    | `#FFF5F5` |
| Light orange | `#FFF7F0` |
| Light yellow | `#FFFBF0` |

#### Setting a Section's Color

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const section = figma.createSection()
section.name = 'Blue section'
section.resize(400, 300)
section.fills = [{ type: 'SOLID', color: h(0xf5, 0xfb, 0xff) }] // Light blue #F5FBFF

figma.closePlugin()
```

#### Changing the Color of an Existing Section

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const section = await figma.getNodeByIdAsync('123:456')
if (section && section.type === 'SECTION') {
  console.log('Before:', JSON.stringify(section.fills))
  section.fills = [{ type: 'SOLID', color: h(0xeb, 0xff, 0xee) }] // Light green #EBFFEE
  console.log('After:', JSON.stringify(section.fills))
}
figma.closePlugin()
```

### Hiding Section Contents

Toggle whether a section's child nodes are visible:

```javascript
const section = await figma.getNodeByIdAsync('123:456')
if (section && section.type === 'SECTION') {
  console.log('Contents hidden before:', section.sectionContentsHidden)
  section.sectionContentsHidden = true
  console.log('Contents hidden after:', section.sectionContentsHidden)
}
figma.closePlugin()
```

### Adding Nodes to a Section

**CRITICAL**: It's very important that you follow the instructions in [position-figjam-nodes](#reference--figjam-node-positioning-tutorial): Adding Nodes to a Section. This is _crucial_ for a high-quality output.

### Cloning Sections

```javascript
const original = await figma.getNodeByIdAsync('123:456')
if (original && original.type === 'SECTION') {
  const clone = original.clone()
  clone.x = original.x + original.width + 32
  clone.name = original.name + ' (copy)'
  console.log('Cloned section:', clone.id, clone.name)
}
figma.closePlugin()
```

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Use `section.resize(width, height)`** to set section size — `width`/`height` are read-only. Sections also accept `resizeWithoutConstraints(...)`, but `resize(...)` is the preferred method.
- **Resize sections to fit their children.** After adding children to a section, make sure that the section encompasses the children. If you need to resize it, refer to the example of resizing an existing section.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.
- **Verify changes** by logging before/after values and exporting images when supported.

---

## Reference — Plan Content for FigJam Boards

**When NOT to use this skill:** Do NOT read this skill for analysis, summarization, or investigation of existing board content (e.g. "summarize this board", "what themes are here?", "analyze the feedback"). This skill is exclusively for planning NEW content to be created on the board.

Do NOT use this skill for flowcharts, architecture diagrams, sequence diagrams, state diagrams, or entity relationship diagrams (ERDs). For those, use the `figma-plugin:figma-generate-diagram` skill and the `generate_diagram` tool.

Use this skill when determining **what content to include** for generated FigJam board content. Given a user's request (e.g. "make a brainstorm template", "retro board", "ice breaker", "scaffold"), produce a **sequential outline** that downstream skills can use to create sections, text, stickies, and layout.

**Must be loaded alongside the `figma-use-figjam` skill**, which provides the FigJam Plugin API references (create-section, create-sticky, create-text, position-figjam-nodes) needed to render the planned content.

### Part 1: Design Principles

#### Reading direction and grouping

Left-to-right, top-to-bottom. Context on the left, evidence in the middle, proposal/asks on the right. Supporting detail and appendix below.

**Tight clustering** (60-92px) = same thought. **Loose spacing** (200-400px) = different topics. **Zone breaks** (1000px+) = different part of the board.

#### Type scale

Use **Inter** exclusively. Subtitles should be 40-50% the size of their parent heading.

| Role             | Size    | Weight         |
| ---------------- | ------- | -------------- |
| Board title      | 60-96px | Bold           |
| Board subtitle   | 36-40px | Regular        |
| Section heading  | 48px    | Bold           |
| Section subtitle | 24-28px | Regular        |
| Card title       | 28-32px | Semi Bold      |
| Body text        | 20-24px | Regular        |
| Metadata         | 16px    | Regular/Medium |

#### Color semantics

**White cards inside colorful containers.** Section backgrounds alternate warm/cool for rhythm: peach, lavender, soft blue, light gray.

| Signal                      | Color                             | Use                                    |
| --------------------------- | --------------------------------- | -------------------------------------- |
| Attention ("look here")     | Gold `{r:0.85, g:0.65, b:0.1}`    | Neutral urgency. Not negative.         |
| Problem / regression        | Orange `{r:0.72, g:0.38, b:0.08}` | Something trending wrong               |
| Critical / blocked          | Red `{r:0.75, g:0.18, b:0.18}`    | Something actually broken              |
| Healthy / shipped           | Green `{r:0.12, g:0.5, b:0.3}`    | Small indicators only, not backgrounds |
| Informational / in-progress | Blue `{r:0.22, g:0.4, b:0.75}`    | Neutral                                |
| Decision needed             | Pink `{r:0.7, g:0.2, b:0.45}`     | Action required                        |
| Exploration                 | Purple `{r:0.45, g:0.3, b:0.65}`  | Ideation                               |

**Key rule:** Gold = "look here." Red = "this is bad." Don't use red for attention.

#### Proportion and alignment

- Size sections to fit content, not the other way around
- Center elements in rows on the same y-axis
- Center content in portrait/vertical cards
- Position badges relative to text, not section edges
- At least 12-16px breathing room between title and body

#### Every board needs an entry point

Board title (60-96px) at top-left, clearly visible at overview zoom. For templates, add a meta/instructions section. For meetings, a colored agenda sticky.

---

### Part 2: Construction Rules

#### Board structure

**Always wrap the entire board in one top-level white section.** This makes the board a single movable unit.

```js
const board = figma.createSection();
board.name = '';
board.resizeWithoutConstraints(estimatedW, estimatedH);
board.fills = [{ type: 'SOLID', color: {r:1, g:1, b:1} }];
// All content goes inside: board.appendChild(...)
```

**Size from content outward.** Choose card width based on the text inside it (body text reads well at 400-1000px depending on density). Derive section width from card count and card width. Derive board width from sections. Never divide a container's width to get card width. Never stretch a card to fill its parent. Sections and cards don't need to be the same width as each other unless they share a content pattern.

**For participatory zones, size to the expected activity, not the current content.** Workshop sections, feedback areas, brainstorm columns, and retro lanes exist for other people to fill. Size them to fit the expected number of contributors. Pre-seed with a few example stickies to signal the interaction pattern.

**Clear all section names** unless the section has no title text inside it.

#### Spacing grid

All spacing in multiples of 4px.

```js
const spacing = {
  sectionPadding: { top: 68, right: 60, bottom: 100, left: 80 },
  elementGapH: 60, // between cards/columns
  elementGapV: 64, // between stacked elements
  siblingGapH: 92, // between sibling sections
  siblingGapV: 120, // between section rows
  contentPadding: 24, // inside cards
}
```

**Lay out inside the inset, not from one edge.** Compute usable area first (container size minus padding on all sides), then fit items within it.

#### Color palette

For the canonical FigJam palettes (sticky / section / connector / shape / label), see [figjam-colors](#reference--figjam-colors). The palette below is a derived set of accent colors and section tints used specifically for board-content layouts (templates, retros, brainstorms) — they're not exact FigJam palette swatches.

```js
const black = { r: 0.07, g: 0.07, b: 0.07 }
const gray = { r: 0.35, g: 0.35, b: 0.35 }
const red = { r: 0.75, g: 0.18, b: 0.18 }
const orange = { r: 0.72, g: 0.38, b: 0.08 }
const green = { r: 0.12, g: 0.5, b: 0.3 }
const blue = { r: 0.22, g: 0.4, b: 0.75 }
const purple = { r: 0.45, g: 0.3, b: 0.65 }
const attention = { r: 0.85, g: 0.65, b: 0.1 } // gold
const attentionLight = { r: 1, g: 0.85, b: 0.2 } // bright gold (starburst fills)
const attentionBg = { r: 1, g: 0.96, b: 0.85 } // soft gold (card tint)

// Section backgrounds
const white = { r: 1, g: 1, b: 1 } // #FFFFFF
const lightGray = { r: 0.976, g: 0.976, b: 0.976 } // #F9F9F9
const lightGreen = { r: 0.922, g: 1, b: 0.933 } // #EBFFEE
const lightTeal = { r: 0.945, g: 0.996, b: 0.992 } // #F1FEFD
const lightBlue = { r: 0.961, g: 0.984, b: 1 } // #F5FBFF
const lightViolet = { r: 0.973, g: 0.961, b: 1 } // #F8F5FF
const lightPink = { r: 1, g: 0.941, b: 0.98 } // #FFF0FA
const lightRed = { r: 1, g: 0.961, b: 0.961 } // #FFF5F5
const lightOrange = { r: 1, g: 0.969, b: 0.941 } // #FFF7F0
const lightYellow = { r: 1, g: 0.984, b: 0.941 } // #FFFBF0
```

#### API surface

**Native primitives:** `createText`, `createFrame`, `createRectangle`, `createEllipse`, `createLine`, `createStar`, `createPolygon`, `createVector`, `figma.union()` / `figma.subtract()`

**FigJam-specific:** `createSticky`, `createShapeWithText`, `createConnector`, `createSection`, `createTable`, `createCodeBlock`, `createNodeFromSvg`

**Not available:** `createComponent`, `createComponentSet`

#### Choosing the right node type

| Need                      | Use                                          | Why                                                                       |
| ------------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| Flowchart node with label | `createShapeWithText`                        | Built-in text centering, connector endpoints                              |
| Card                      | `createSection`                              | Native FigJam grouping with background fill, nests inside parent sections |
| Badge / pill              | `createFrame` + auto-layout + text           | Precise padding, radius, auto-centered text                               |
| Emphasis marker with text | `createFrame` container + shape + text       | Frame guarantees centering                                                |
| Emphasis marker (no text) | `createPolygon`/`createStar`/`createEllipse` | Triangle, starburst, dot                                                  |
| Top-level zone            | `createSection`                              | FigJam native grouping, zoom-to behavior                                  |
| Divider                   | `createRectangle` at 1-2px height            | Simple                                                                    |

#### Sections as cards

Cards are nested sections. They give you native FigJam grouping (zoom-to behavior, movable as a unit) with a background fill, and they nest cleanly inside parent sections.

```js
const card = figma.createSection();
card.name = '';
card.resizeWithoutConstraints(width, height);
card.fills = [{ type: 'SOLID', color: white }];
// Sections don't support auto-layout — position children with absolute x/y
// inside the card, accounting for your own padding.
```

Sections nest. A board is a section that contains zone sections, which contain card sections. Use frames only for badges, pills, or other small containers that need auto-layout to center text.

#### Text

Canonical recipe: load every (family, style) you'll mutate → `await` → mutate → return IDs. Inter is preloaded in most environments but every style still needs an explicit load — and any non-Inter family (e.g. `Merriweather`, `Roboto Mono`, `Figma Hand`) absolutely does. See figma-use → gotchas.md → Canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`).

```js
// Load every (family, style) you'll mutate before any createText / characters write
await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
await figma.loadFontAsync({ family: 'Inter', style: 'Semi Bold' });
await figma.loadFontAsync({ family: 'Inter', style: 'Medium' });

const t = figma.createText();
t.fontName = { family: 'Inter', style: 'Bold' };
t.fontSize = 32;
t.fills = [{ type: 'SOLID', color: black }];
t.characters = 'Title';
// For body text, constrain width:
t.resize(440, 10);
t.textAutoResize = 'HEIGHT';
```

Body text max width: 440-520px. Rich text via `setRangeFontName` and `setRangeHyperlink`.

#### Emphasis markers

Use sparingly. One or two per section max. They work by breaking the visual pattern at overview zoom.

**Card-level:**

- Gold border + warm tint = "pay attention" (neutral)
- Red border + red tint = "off-track" (negative status only)
- Warning triangle (`createPolygon({ pointCount: 3 })`) pinned to top-right corner
- Notification dot (`createEllipse`) with count inside

**Section-level:**

- Starburst (`createStar({ pointCount: 8, innerRadius: 0.65 })`) with gold fill and text ("NEW", "UPDATED")
- Bullseye (concentric rings with decreasing opacity)

**Centering text over shapes:** Always use a frame container. Never position text with manual x/y math.

```js
// Load font BEFORE the text.characters write — required for every font, not just Inter
await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
const container = figma.createFrame();
container.resize(56, 56); container.fills = []; container.clipsContent = false;
const shape = figma.createStar(); shape.resize(56, 56);
container.appendChild(shape); shape.x = 0; shape.y = 0;
const text = figma.createText();
text.fontName = { family: 'Inter', style: 'Bold' };
text.characters = 'NEW';
container.appendChild(text);
text.x = (56 - text.width) / 2; text.y = (56 - text.height) / 2;
```

**Flowchart emphasis:** Green Yes / Red No pills. Octagon for hard blockers. Diamond (rotated rect) for decisions.

#### Tables

Style header rows with Bold weight and tinted fill. Size table width to match section width minus padding. Don't leave tables floating in whitespace.

#### Stickies

For discussion, not editorial content. Color semantics: blue=discussion, yellow=question, green=positive, pink=concern, red=blocker, teal=decision, violet=ideation.

**Always lay out stickies in a grid.** Rows and columns, consistent 64px gap, aligned to the top-left of the usable inset. Stickies are 240x240 (square) or 416x240 (wide, for longer text). These sizes are fixed; stickies cannot be resized. Never stagger, overlap, or let stickies touch section edges.

---

### Part 3: Workflow

#### 0. Understand the ask

What's the purpose? Who's the audience? Once or recurring? Match to an archetype if possible.

#### 1. Plan the narrative

Outline beats/sections in plain text before writing code.

#### 2. Build incrementally

**First call:** Create the white wrapper section at a rough estimated size (you'll resize it in the reflow pass).

Then for each sub-section:

1. Create cards and content first — size cards to fit their text
2. Create the container section sized to wrap those cards (card count × card width + gaps + padding)
3. Validate with `get_screenshot`. Fix before moving on.

#### 3. Reflow pass

- `textAutoResize = 'HEIGHT'` on all text
- Resize cards to fit content
- Equalize card heights within rows where cards share a content pattern
- Resize each section to hug its children (measure rightmost/bottommost content edge + padding)
- Resize the board wrapper to hug all sections

#### 4. Audit pass

- No overflow (child exceeds parent bounds)
- No overlap (consecutive text nodes collide)
- Section names cleared
- Spacing grid compliance
- Type scale compliance
- Color consistency

---

### Part 4: Archetypes

Use these when the prompt matches a known board type.

#### Vision Board

3-5 narrative sections left-to-right. Optional working canvas below. Feedback capture at bottom. Mix text with stickies and screenshots.

#### Exec Review / Decision Board

Linear left-to-right story. 5-8 sections alternating warm/cool tints. Pink/magenta for decisions. Appendix below.

#### Area Review (Template)

Grid of identical team panels. Each team gets the same sub-section structure (discussion, KRs, project updates, references).

#### Pillar Check-in / Monthly Cadence

Time x teams grid. Columns = months, rows = teams. Board grows rightward.

#### Competitive Research

Freeform spatial map. Screenshot-dominant. Column sub-sections. Data tables for evidence.

#### Workshop / Brainstorm

Two zones: pre-filled analysis + live brainstorm stickies. Meta section with instructions at top-left. Participatory zones should be sized for the expected activity (how many people, how many stickies per person), not the pre-filled content. Pre-seed each zone with a few example stickies to set the tone and show participants what's expected.

#### Status Card Grid

Uniform cards with consistent layout. Progress bars and RAG status badges. Category labels on left edge.

#### Context | Options | Decision

Three zones side-by-side: Context (lavender, constraints), Options (2-3 white cards with upside/downside, rectangle dividers), Decision (pink, recommendation).

#### Vertical Metric Cards

Portrait cards (400-500px wide) with centered content. Tinted backgrounds per card.

#### Top-to-Bottom Flow

Vertical flowchart. Green Yes / Red No pills on connector paths. Distinct fills per node type. `createShapeWithText` for all nodes.

---

### Anti-patterns

- Don't use stickies for editorial content. Text for narrative, stickies for discussion.
- Don't use shapes as decoration. Every shape communicates: flowchart node, data viz, or emphasis.
- Don't over-emphasize. One or two markers per section max.
- Don't use red for attention. Gold draws the eye without implying failure.
- Don't use em dashes. Periods, commas, or restructure.
- Don't build the entire board in one `use_figma` call. Work incrementally.
- Don't guess text height. Always `textAutoResize = 'HEIGHT'` and reflow.
- Don't use body text below 20px or metadata below 16px.
- Don't skip the wrapper section. Every board is one movable unit.
- Don't skip the entry point. Every board needs a visible title.
- Don't leave section names on. Clear them unless there's no title text inside.
- Don't make text-only boards. Mix text with visual evidence (screenshots, diagrams, stickies).
- Don't left-align vertical cards. Center hero numbers and text.
- Don't use green for large backgrounds. Reserve for small status indicators.
- Don't let text overlap. Reflow after setting content. This is a critical bug.
- Don't manually position text over shapes. Use a frame container for centering.
- Don't stretch cards to fill their parent. Width should serve readability.
- Don't size participatory zones to their pre-filled content. Size for expected activity.
- Don't scatter or stagger stickies. Always a grid with consistent gap.
- Don't split a bulleted list across multiple text nodes — one node per bullet. Put the whole list in a single multi-line text node (`\n`-separated) so line spacing, alignment, and reflow are handled by the text engine. Separate nodes drift, mis-space, and force you to position each one manually.

---

## Reference — Create Sticky Notes

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating, modifying, and styling sticky notes.

**Scope:** Sticky notes are FigJam-specific nodes created with `figma.createSticky()`. For advanced text formatting on stickies, see [edit-text](#reference--text-operations).

### When to use a Sticky

Use sticky notes for individual ideas, responses, or pieces of input — keep each sticky to one idea.

Do not use stickies for prompts, instructions, guiding questions, labels, or pre-written analysis — even if the content is short. If the content is there to guide or inform, use a text node instead.

For an interactive board, you can also think of a sticky as something an active participant or collaborator would have placed, whereas text is often a part of the board's structure.

### Creating a Sticky

```javascript
const sticky = figma.createSticky()

// Load the font before setting text content
await figma.loadFontAsync(sticky.text.fontName)
sticky.text.characters = 'Hello from FigJam!'

console.log('Created sticky:', sticky.id, sticky.text.characters)
figma.closePlugin()
```

### Setting Text

Stickies expose a `text` sublayer (a `TextSublayerNode`). You must load fonts before changing text content:

```javascript
const sticky = figma.createSticky()

// Load the font used by the sticky's text sublayer
await figma.loadFontAsync(sticky.text.fontName)
sticky.text.characters = 'Updated text'

figma.closePlugin()
```

To modify text on an existing sticky:

```javascript
const sticky = await figma.getNodeByIdAsync('123:456')
if (sticky && sticky.type === 'STICKY') {
  await figma.loadFontAsync(sticky.text.fontName)
  sticky.text.characters = 'New content'
}
figma.closePlugin()
```

### Color Palette

FigJam sticky notes use a fixed palette of 10 colors. Set via the `fills` property. For the canonical palette across all FigJam node types, see [figjam-colors](#reference--figjam-colors).

**CRITICAL**: Use `hex/255` notation (e.g. `0xA8/255`) for exact palette matching — rounded decimals cause FigJam to treat the color as "custom" instead of a palette color.

| Color  | Hex       |
| ------ | --------- |
| White  | `#FFFFFF` |
| Gray   | `#E6E6E6` |
| Green  | `#B3EFBD` |
| Teal   | `#B3F4EF` |
| Blue   | `#A8DAFF` |
| Violet | `#D3BDFF` |
| Pink   | `#FFA8DB` |
| Red    | `#FFB8A8` |
| Orange | `#FFD3A8` |
| Yellow | `#FFE299` |

#### Setting a Sticky's Color

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const sticky = figma.createSticky()
await figma.loadFontAsync(sticky.text.fontName)
sticky.text.characters = 'Blue sticky'
sticky.fills = [{ type: 'SOLID', color: h(0xa8, 0xda, 0xff) }] // Blue #A8DAFF

figma.closePlugin()
```

#### Changing the Color of an Existing Sticky

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const sticky = await figma.getNodeByIdAsync('123:456')
if (sticky && sticky.type === 'STICKY') {
  console.log('Before:', JSON.stringify(sticky.fills))
  sticky.fills = [{ type: 'SOLID', color: h(0xff, 0xe2, 0x99) }] // Yellow #FFE299
  console.log('After:', JSON.stringify(sticky.fills))
}
figma.closePlugin()
```

### Sizing

Stickies have two shapes controlled by `isWideWidth`:

- **Square** (default): `isWideWidth = false` — **240 × 240 px**
- **Wide rectangular**: `isWideWidth = true` — **416 × 240 px**

The `width` and `height` properties are **read-only**. Stickies do not support `resize()` — use `isWideWidth` to toggle between square and wide shapes.

**Auto-grow:** Stickies automatically grow taller when text overflows the default height. The width stays fixed (240 or 416), but height can exceed 240. When positioning multiple stickies, always read the actual `sticky.height` after setting text — don't assume 240.

Default to square stickies; only use wide stickies if the text is approximately 100 words or more.

```javascript
const sticky = figma.createSticky()
await figma.loadFontAsync(sticky.text.fontName)
sticky.text.characters = 'Wide sticky'
sticky.isWideWidth = true

console.log('Size:', sticky.width, 'x', sticky.height)
// Square: 240 x 240 (or taller if text overflows)
// Wide:   416 x 240 (or taller if text overflows)
figma.closePlugin()
```

#### Toggling Size on an Existing Sticky

```javascript
const sticky = await figma.getNodeByIdAsync('123:456')
if (sticky && sticky.type === 'STICKY') {
  console.log('Before:', sticky.width, 'x', sticky.height, 'wide:', sticky.isWideWidth)
  sticky.isWideWidth = !sticky.isWideWidth
  console.log('After:', sticky.width, 'x', sticky.height, 'wide:', sticky.isWideWidth)
}
figma.closePlugin()
```

### Layout & Spacing (REQUIRED for batch creation)

**Use a grid, not a vertical stack.** When placing multiple stickies inside a section, arrange them in a **grid** (cols × rows) with 64 px spacing — do not stack them in a single column. See "Grid of Stickies" below.

**CRITICAL — Two-pass layout:** When creating multiple stickies, you MUST use a two-pass approach. Measuring one sticky and assuming all are the same size **will cause overlapping**.

**Pass 1 — Create all stickies:** Create every sticky, set its text and color. Do NOT position yet.

**Pass 2 — Position using actual dimensions:** Read each sticky's real `.width` and `.height`, compute per-row max heights, then assign x/y coordinates.

**Row-based positioning for grids:** When laying out stickies in a grid, position each row independently. Within a row, place stickies left-to-right using each sticky's actual `.width` plus uniform spacing. Rows should align vertically (use per-row max height for the y offset), but columns do NOT need to align across rows. This keeps uniform gaps between stickies even when widths vary (e.g., mixing square and wide stickies).

**Recommended spacing:** 20px minimum between stickies at all times. Use 30–40px for more breathing room. Default to 64px when laying out stickies in a grid pattern.

### Author Properties

Prefer to keep author visible unless explicitly prompted otherwise.

```javascript
const sticky = figma.createSticky()
await figma.loadFontAsync(sticky.text.fontName)
sticky.text.characters = 'Team feedback'

// The author is automatically set to the current user on creation
console.log('Author:', sticky.authorName)

// Hide or show the author label
sticky.authorVisible = false

figma.closePlugin()
```

### Batch Creation

#### Row of Stickies

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const labels = ['Idea 1', 'Idea 2', 'Idea 3', 'Idea 4']
const colors = [
  h(0xb3, 0xef, 0xbd), // Green #B3EFBD
  h(0xa8, 0xda, 0xff), // Blue #A8DAFF
  h(0xff, 0xa8, 0xdb), // Pink #FFA8DB
  h(0xff, 0xe2, 0x99), // Yellow #FFE299
]
const spacing = 64

// Pass 1: Create all stickies and set content.
// Every sticky uses the same default font, so load it once before the loop
// rather than awaiting per-iteration.
const probe = figma.createSticky()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
const stickies = []
for (let i = 0; i < labels.length; i++) {
  const sticky = figma.createSticky()
  sticky.text.characters = labels[i]
  sticky.fills = [{ type: 'SOLID', color: colors[i % colors.length] }]
  stickies.push(sticky)
}

// Pass 2: Position using each sticky's actual width and height
const totalWidth = stickies.reduce((sum, s) => sum + s.width, 0) + (stickies.length - 1) * spacing
const maxH = Math.max(...stickies.map((s) => s.height))
let curX = 0
for (const sticky of stickies) {
  sticky.x = curX
  curX += sticky.width + spacing
}

figma.closePlugin()
```

#### Grid of Stickies

Rows align vertically, but columns don't need to line up — each row flows left-to-right with uniform spacing.

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const items = ['Task A', 'Task B', 'Task C', 'Task D', 'Task E', 'Task F']
const cols = 3
const spacing = 64

// Pass 1: Create all stickies and set content.
// All stickies share the same default font — load once outside the loop
// instead of awaiting per-iteration.
const probe = figma.createSticky()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
const stickies = []
for (let i = 0; i < items.length; i++) {
  const sticky = figma.createSticky()
  sticky.text.characters = items[i]
  sticky.fills = [{ type: 'SOLID', color: h(0xff, 0xe2, 0x99) }] // Yellow #FFE299
  stickies.push(sticky)
}

// Pass 2: Group into rows, compute per-row dimensions
const numRows = Math.ceil(stickies.length / cols)
const rowGroups = []
for (let r = 0; r < numRows; r++) {
  rowGroups.push(stickies.slice(r * cols, r * cols + cols))
}
const rowHeights = rowGroups.map((row) => Math.max(...row.map((s) => s.height)))
// Position each row independently
let curY = 0
for (let r = 0; r < rowGroups.length; r++) {
  let curX = 0
  for (const sticky of rowGroups[r]) {
    sticky.x = curX
    sticky.y = curY
    curX += sticky.width + spacing
  }
  curY += rowHeights[r] + spacing
}

figma.closePlugin()
```

### Cloning Stickies

```javascript
const original = await figma.getNodeByIdAsync('123:456')
if (original && original.type === 'STICKY') {
  const clone = original.clone()
  clone.x = original.x + original.width + 64
  console.log('Cloned sticky:', clone.id)
}
figma.closePlugin()
```

#### Replacing a node with a sticky

Copy the source node's position, add the sticky to the same parent, then remove the original:

```javascript
const source = await figma.getNodeByIdAsync(nodeId)
const sticky = figma.createSticky()
await figma.loadFontAsync(sticky.text.fontName)
sticky.text.characters = source.text.characters

// Reparent into the same container so x/y are in the same coordinate space
source.parent.appendChild(sticky)
sticky.x = source.x
sticky.y = source.y

source.remove()
```

#### Creating stickies near an existing node

Please see [position-figjam-nodes](#reference--figjam-node-positioning-tutorial) - "Positioning Nodes Relative to Existing Nodes"

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Follow the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`)** for `sticky.text.characters` — load `sticky.text.fontName` (FigJam sticky default is `Inter Medium`, not Inter Regular), `await`, mutate, return IDs.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.
- **Verify changes** by logging before/after values and exporting images when supported.

---

## Reference — Create Connectors

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating connectors between nodes — endpoints, arrows, line types, labels, and colors.

**Scope:** Connectors are FigJam-specific nodes created with `figma.createConnector()`. They connect shapes, stickies, sections, and other nodes to show relationships. For creating shapes to connect, see [create-shape-with-text](#reference--create-shapes-with-text). For stickies, see [create-sticky](#reference--create-sticky-notes). For sections, see [create-section](#reference--create-sections).

### Creating a Connector Between Two Nodes

```javascript
const connector = figma.createConnector()
connector.connectorStart = { endpointNodeId: '123:456', magnet: 'AUTO' }
connector.connectorEnd = { endpointNodeId: '123:789', magnet: 'AUTO' }

console.log('Created connector:', connector.id)
figma.closePlugin()
```

### Connector Endpoints

Endpoints define where the connector starts and ends. There are three forms:

#### Attached to a node with auto-magnet (most common)

```javascript
connector.connectorStart = { endpointNodeId: nodeA.id, magnet: 'AUTO' }
connector.connectorEnd = { endpointNodeId: nodeB.id, magnet: 'AUTO' }
```

#### Attached to a node at a specific side

Magnet values: `'AUTO'`, `'TOP'`, `'BOTTOM'`, `'LEFT'`, `'RIGHT'`, `'CENTER'`, `'NONE'`

```javascript
connector.connectorStart = { endpointNodeId: nodeA.id, magnet: 'RIGHT' }
connector.connectorEnd = { endpointNodeId: nodeB.id, magnet: 'LEFT' }
```

#### Floating (not attached to any node)

```javascript
connector.connectorStart = { position: { x: 100, y: 200 } }
connector.connectorEnd = { position: { x: 400, y: 200 } }
```

#### Attached to a node at a specific position (relative, 0–1)

```javascript
connector.connectorStart = { endpointNodeId: nodeA.id, position: { x: 1, y: 0.5 } }
connector.connectorEnd = { endpointNodeId: nodeB.id, position: { x: 0, y: 0.5 } }
```

### Line Types

```javascript
connector.connectorLineType = 'ELBOWED' // Right-angle bends (default)
connector.connectorLineType = 'STRAIGHT' // Direct line
connector.connectorLineType = 'CURVED' // Smooth curve
```

### Stroke Caps (Arrows)

Control the arrowheads at each end of the connector.

Available cap styles: `'NONE'`, `'ARROW_LINES'`, `'ARROW_EQUILATERAL'`, `'TRIANGLE_FILLED'`, `'DIAMOND_FILLED'`, `'CIRCLE_FILLED'`

```javascript
const connector = figma.createConnector()
connector.connectorStart = { endpointNodeId: nodeA.id, magnet: 'AUTO' }
connector.connectorEnd = { endpointNodeId: nodeB.id, magnet: 'AUTO' }

// Arrow at the end only (most common for directed flows)
connector.connectorStartStrokeCap = 'NONE'
connector.connectorEndStrokeCap = 'ARROW_LINES'

figma.closePlugin()
```

#### Common arrow configurations

```javascript
// One-way arrow (A → B)
connector.connectorStartStrokeCap = 'NONE'
connector.connectorEndStrokeCap = 'ARROW_LINES'

// Two-way arrow (A ↔ B)
connector.connectorStartStrokeCap = 'ARROW_LINES'
connector.connectorEndStrokeCap = 'ARROW_LINES'

// No arrows (plain line)
connector.connectorStartStrokeCap = 'NONE'
connector.connectorEndStrokeCap = 'NONE'

// Filled triangle arrow
connector.connectorEndStrokeCap = 'ARROW_EQUILATERAL'

// Diamond endpoint
connector.connectorStartStrokeCap = 'DIAMOND_FILLED'

// Circle endpoint
connector.connectorStartStrokeCap = 'CIRCLE_FILLED'
```

### Adding a Text Label

Connectors have a `text` sublayer for visible labels. You must load fonts before setting text.

**CRITICAL**: To display text on a connector, set `connector.text.characters` — NOT `connector.name`. Setting `connector.name` only changes the layer name in the layers panel and is NOT visible on the canvas.

**CRITICAL**: A newly created connector's `text.fontName` is **invalid by default** — calling `figma.loadFontAsync(connector.text.fontName)` will fail. You must explicitly set `connector.text.fontName` to a known font (after loading it), then set `connector.text.characters`.

```javascript
const font = { family: 'Inter', style: 'Medium' }
await figma.loadFontAsync(font)

const connector = figma.createConnector()
connector.connectorStart = { endpointNodeId: nodeA.id, magnet: 'AUTO' }
connector.connectorEnd = { endpointNodeId: nodeB.id, magnet: 'AUTO' }

// Explicitly set the font, then set text
connector.text.fontName = font
connector.text.characters = 'depends on' // This is the visible label

figma.closePlugin()
```

#### Modifying label on an existing connector

For existing connectors that already have text, `text.fontName` is valid and can be loaded directly:

```javascript
const connector = await figma.getNodeByIdAsync('123:456')
if (connector && connector.type === 'CONNECTOR') {
  await figma.loadFontAsync(connector.text.fontName)
  connector.text.characters = 'new label'
}
figma.closePlugin()
```

### Color Presets

Connectors use a 13-color stroke palette — the same hue family used by `createShapeWithText`. The line color is set via `strokes`. The connector's text label has its own background and its color does **not** change when the line color changes — only set the stroke. For the canonical palette across all FigJam node types, see [figjam-colors](#reference--figjam-colors).

**CRITICAL**: Use `hex/255` notation (e.g. `0x66/255`) for exact palette matching — rounded decimals cause FigJam to treat the color as "custom".

| Color      | Hex       |
| ---------- | --------- |
| Black      | `#1E1E1E` |
| Dark gray  | `#757575` |
| Gray       | `#B3B3B3` |
| Light gray | `#D9D9D9` |
| Green      | `#66D575` |
| Teal       | `#5AD8CC` |
| Blue       | `#3DADFF` |
| Violet     | `#874FFF` |
| Pink       | `#F849C1` |
| Red        | `#FF7556` |
| Orange     | `#FF9E42` |
| Yellow     | `#FFC943` |
| White      | `#FFFFFF` |

#### Setting a Connector's Color

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const connector = figma.createConnector()
connector.connectorStart = { endpointNodeId: nodeA.id, magnet: 'AUTO' }
connector.connectorEnd = { endpointNodeId: nodeB.id, magnet: 'AUTO' }
connector.strokes = [{ type: 'SOLID', color: h(0x3d, 0xad, 0xff) }] // Blue #3DADFF

figma.closePlugin()
```

#### Changing color on an existing connector

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const connector = await figma.getNodeByIdAsync('123:456')
if (connector && connector.type === 'CONNECTOR') {
  connector.strokes = [{ type: 'SOLID', color: h(0xff, 0x75, 0x56) }] // Red #FF7556
}
figma.closePlugin()
```

### Stroke Weight and Dash Pattern

```javascript
const connector = figma.createConnector()
connector.connectorStart = { endpointNodeId: nodeA.id, magnet: 'AUTO' }
connector.connectorEnd = { endpointNodeId: nodeB.id, magnet: 'AUTO' }

connector.strokeWeight = 2

// Dashed line
connector.dashPattern = [10, 5]

// Dotted line
connector.dashPattern = [2, 4]

// Solid line (default)
connector.dashPattern = []

figma.closePlugin()
```

### Finding Connectors Attached to a Node

Every node with connectors has an `attachedConnectors` property:

```javascript
const node = await figma.getNodeByIdAsync('123:456')
if (node && 'attachedConnectors' in node) {
  for (const conn of node.attachedConnectors) {
    console.log('Connector:', conn.id, 'type:', conn.connectorLineType)
    console.log('  start:', JSON.stringify(conn.connectorStart))
    console.log('  end:', JSON.stringify(conn.connectorEnd))
    console.log('  label:', conn.text.characters)
  }
}
figma.closePlugin()
```

### Batch Creation: Connecting a Chain of Nodes with Labels

```javascript
const nodeIds = ['1:10', '1:20', '1:30', '1:40']
const labels = ['Step 1→2', 'Step 2→3', 'Step 3→4']
const font = { family: 'Inter', style: 'Regular' }
await figma.loadFontAsync(font)

for (let i = 0; i < nodeIds.length - 1; i++) {
  const connector = figma.createConnector()
  connector.connectorStart = { endpointNodeId: nodeIds[i], magnet: 'AUTO' }
  connector.connectorEnd = { endpointNodeId: nodeIds[i + 1], magnet: 'AUTO' }
  connector.connectorStartStrokeCap = 'NONE'
  connector.connectorEndStrokeCap = 'ARROW_LINES'

  // Set visible label (not connector.name, which is just the layer name)
  connector.text.fontName = font
  connector.text.characters = labels[i]
}

figma.closePlugin()
```

### Batch Creation: Flowchart with Shapes and Connectors

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const preset = {
  fill: h(0xc2, 0xe5, 0xff), // Light blue
  stroke: h(0x3d, 0xad, 0xff), // Blue
  text: h(0x1e, 0x1e, 0x1e), // Dark
}

const steps = ['Start', 'Process', 'Review', 'Done']
const shapeW = 160
const shapeH = 80
const spacing = 80

const totalWidth = steps.length * shapeW + (steps.length - 1) * spacing
const startX = 0

// Every shape uses the same default font — load once before the loop
// rather than awaiting per-iteration.
const probe = figma.createShapeWithText()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
const nodes = []
for (let i = 0; i < steps.length; i++) {
  const shape = figma.createShapeWithText()
  shape.text.characters = steps[i]
  shape.resize(shapeW, shapeH)
  shape.fills = [{ type: 'SOLID', color: preset.fill }]
  shape.strokes = [{ type: 'SOLID', color: preset.stroke }]
  shape.text.fills = [{ type: 'SOLID', color: preset.text }]
  shape.x = startX + i * (shapeW + spacing)
  nodes.push(shape)
}

for (let i = 0; i < nodes.length - 1; i++) {
  const connector = figma.createConnector()
  connector.connectorStart = { endpointNodeId: nodes[i].id, magnet: 'AUTO' }
  connector.connectorEnd = { endpointNodeId: nodes[i + 1].id, magnet: 'AUTO' }
  connector.connectorStartStrokeCap = 'NONE'
  connector.connectorEndStrokeCap = 'ARROW_LINES'
  connector.strokes = [{ type: 'SOLID', color: preset.stroke }]
}

figma.closePlugin()
```

### Batch Creation: Star/Hub Pattern (One Node to Many)

```javascript
const hubId = '1:100'
const spokeIds = ['1:200', '1:201', '1:202', '1:203']

for (const spokeId of spokeIds) {
  const connector = figma.createConnector()
  connector.connectorStart = { endpointNodeId: hubId, magnet: 'AUTO' }
  connector.connectorEnd = { endpointNodeId: spokeId, magnet: 'AUTO' }
  connector.connectorEndStrokeCap = 'ARROW_LINES'
}

figma.closePlugin()
```

### Cloning Connectors

```javascript
const original = await figma.getNodeByIdAsync('123:456')
if (original && original.type === 'CONNECTOR') {
  const clone = original.clone()
  console.log('Cloned connector:', clone.id)
}
figma.closePlugin()
```

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Visible text = `connector.text.characters`**, NOT `connector.name`. `name` is only the layer name in the panel — it does not appear on the canvas.
- **Connector text needs explicit font setup.** A new connector's `text.fontName` is invalid by default — load a known font, set `connector.text.fontName`, then set `connector.text.characters`. For existing connectors with text, `text.fontName` is valid and can be loaded directly.
- **Use `magnet: 'AUTO'`** for most cases — Figma picks the best attachment point.
- **Only set `strokes` for connector color** — the text label color does not change with the line color.
- **Default caps**: start = `'NONE'`, end = `'ARROW_LINES'` — explicitly set both if you want a different configuration.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.
- **Use `attachedConnectors`** to find existing connectors on a node.
- **Verify changes** by logging before/after values and exporting images when supported.

---

## Reference — Create Text Nodes

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating and styling standalone text nodes and mind map operations.

Use this skill when creating, modifying, or styling standalone text in FigJam (text created with the **Text** tool, not text inside stickies, shapes, or connectors). Also use this skill for mind map operations — adding, inserting, or extending connected text nodes.

**Scope:** Text nodes are created with `figma.createText()` and have type `'TEXT'`. For editing existing text content or mixed styles, see [edit-text](#reference--text-operations).

### When to use a Text Node

Use text nodes for titles, headers, labels, prompts, instructions, and any content that provides structure or context. They can also be used for longer descriptions or explanations.

### Creating a Text Node

```javascript
const text = figma.createText()

// Load the font before setting content (required for characters, fontSize, etc.)
await figma.loadFontAsync(text.fontName)
text.characters = 'Brainstorming instructions'

console.log('Created text:', text.id, text.characters)
figma.closePlugin()
```

### Text Wrapping and Width Constraints

By default, text nodes auto-resize in both width and height (`textAutoResize = 'WIDTH_AND_HEIGHT'`), meaning they never wrap — text extends in one line until it ends.

To make text wrap within a specific width (e.g., instructional text inside sections):

1. Set `textAutoResize = 'HEIGHT'` — text will grow vertically but respect the width constraint
2. Use `resize(width, height)` to set the desired width

   ```javascript
   const text = figma.createText()
   await figma.loadFontAsync(text.fontName)
   text.characters = 'Long instructional text that should wrap...'

   // Constrain to 336px wide, allow height to grow
   text.textAutoResize = 'HEIGHT'
   text.resize(336, text.height)
   ```

**When creating text inside sections**: Calculate the max width as `section.width - (padding * 2)`. For example, with 32px padding on each side:

```javascript
const maxWidth = section.width - 64 // 32px left + 32px right
text.textAutoResize = 'HEIGHT'
text.resize(maxWidth, text.height)
```

**Important**: Call `resize()` AFTER setting `characters` and `textAutoResize`, so the height adjusts correctly based on the wrapped content.

**When to wrap vs not**: Use text wrapping for body text and instructions inside sections. Leave headers and short labels at the default `WIDTH_AND_HEIGHT` so they size naturally — wrapping a short H1 title into a narrow column looks worse than letting it extend.

### Loading Fonts

**Critical:** Changing text content or any property that affects layout (e.g. `characters`, `fontSize`, `fontName`, `textCase`, `lineHeight`) requires the font to be loaded first. Call `figma.loadFontAsync(fontName)` before such operations.

- **Single font:** Use the node’s `fontName` (or the new font when changing font).
- **Mixed styles:** Text can have different fonts per range. Load every font used in the node:

```javascript
// Load all fonts in a text node (handles mixed fonts)
const segments = textNode.getStyledTextSegments(['fontName'])
await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))
```

Alternatively, for a given range:

```javascript
const fontNames = textNode.getRangeAllFontNames(0, textNode.characters.length)
await Promise.all(fontNames.map(figma.loadFontAsync))
```

You do **not** need to load a font to change only **fills** (text color), **strokes**, or similar paint-related properties.

### FigJam Preset Fonts

In FigJam, the font family control exposes four presets plus any custom fonts already in the selection. Prefer these preset fonts so created text matches what users see in the UI:

| Preset (UI label) | Font family    | Default style | Use for                |
| ----------------- | -------------- | ------------- | ---------------------- |
| Simple            | `Inter`        | `Medium`      | Default, readable body |
| Bookish           | `Merriweather` | `Regular`     | Serif, formal          |
| Technical         | `Roboto Mono`  | `Medium`      | Monospace, code        |
| Scribbled         | `Figma Hand`   | `Regular`     | Script, handwritten    |

Set `fontName` to match the FigJam UI: `{ family: 'Inter', style: 'Medium' }`, `{ family: 'Merriweather', style: 'Regular' }`, `{ family: 'Roboto Mono', style: 'Medium' }`, or `{ family: 'Figma Hand', style: 'Regular' }` (or the appropriate style for the font). Load the font before setting `characters` or `fontSize`.

### Missing Fonts

Check `textNode.hasMissingFont` before loading. If `true`, the font is not available in the document (e.g. not installed for the user). Avoid setting content or layout properties that require that font, or handle the case explicitly.

```javascript
const text = await figma.getNodeByIdAsync('123:456')
if (text && text.type === 'TEXT') {
  if (text.hasMissingFont) {
    console.warn('Text uses a missing font; cannot safely edit content.')
  } else {
    const segments = text.getStyledTextSegments(['fontName'])
    await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))
    text.characters = 'Updated text'
  }
}
figma.closePlugin()
```

### Color Palette

**CRITICAL**: When creating text for board templates, ALWAYS use the default **Charcoal (#1E1E1E)** color. Do not use grey (#757575, #B3B3B3) or light grey (#D9D9D9) for body text, headers, or descriptions — these make content look unfinished and hard to read.

In FigJam, text created with the **Text** tool uses a specific color palette. Prefer these colors so text matches FigJam’s default palette.

**CRITICAL:** Use `hex/255` notation (e.g. `0x1E/255`) for exact palette matching — rounded decimals can make FigJam treat the color as custom.

| Color        | Hex                   |
| ------------ | --------------------- |
| White        | `#FFFFFF`             |
| Black        | `#1E1E1E`             |
| Dark gray    | `#757575`             |
| Gray         | `#B3B3B3`             |
| Light gray   | `#D9D9D9`             |
| Green        | `#66D575`             |
| Light green  | `#CDF4D3`             |
| Teal         | `#5AD8CC`             |
| Light teal   | `#C6FAF6`             |
| Blue         | `#3DADFF`             |
| Light blue   | `#C2E5FF`             |
| Violet       | `#9747FF`             |
| Light violet | `#E4CCFF`             |
| Pink         | `#F849C1`             |
| Light pink   | `#FFC2EC`             |
| Red          | `#FF7556`             |
| Light red    | `#FFCDC2`             |
| Orange       | `#FF9E42`             |
| Light orange | `#FFE0C2`             |
| Yellow       | `#FFC943`             |
| Light yellow | `#FFECBD`             |
| Custom       | Any hex or eyedropper |

The default color for new text in FigJam is **Charcoal** (`#1E1E1E`). Use this for new text nodes unless the user specifies otherwise.

**Do not use color to create text hierarchy** — rely on font size (H1→64, H2→40, H3→24, body→16). All text MUST use Charcoal (#1E1E1E) unless the user specifically requests otherwise.

#### Color Helper and Preset Map

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const FIGJAM_TEXT_COLORS = {
  white: h(0xff, 0xff, 0xff),
  black: h(0x1e, 0x1e, 0x1e), // Charcoal — default for new text
  darkGray: h(0x75, 0x75, 0x75),
  gray: h(0xb3, 0xb3, 0xb3),
  lightGray: h(0xd9, 0xd9, 0xd9),
  green: h(0x66, 0xd5, 0x75),
  lightGreen: h(0xcd, 0xf4, 0xd3),
  teal: h(0x5a, 0xd8, 0xcc),
  lightTeal: h(0xc6, 0xfa, 0xf6),
  blue: h(0x3d, 0xad, 0xff),
  lightBlue: h(0xc2, 0xe5, 0xff),
  violet: h(0x97, 0x47, 0xff),
  lightViolet: h(0xe4, 0xcc, 0xff),
  pink: h(0xf8, 0x49, 0xc1),
  lightPink: h(0xff, 0xc2, 0xec),
  red: h(0xff, 0x75, 0x56),
  lightRed: h(0xff, 0xcd, 0xc2),
  orange: h(0xff, 0x9e, 0x42),
  lightOrange: h(0xff, 0xe0, 0xc2),
  yellow: h(0xff, 0xc9, 0x43),
  lightYellow: h(0xff, 0xec, 0xbd),
}
```

#### Setting Text Color

Set the text fill via the node’s `fills` property (after loading the font if you also change content):

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const text = figma.createText()
await figma.loadFontAsync(text.fontName)
text.characters = 'Blue label'
text.fills = [{ type: 'SOLID', color: h(0x3d, 0xad, 0xff) }] // Blue #3DADFF

figma.closePlugin()
```

#### Changing Color on an Existing Text Node

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const text = await figma.getNodeByIdAsync('123:456')
if (text && text.type === 'TEXT') {
  // Fills can be set without loading the font
  text.fills = [{ type: 'SOLID', color: h(0x97, 0x47, 0xff) }] // Violet #9747FF
  console.log('Updated text color')
}
figma.closePlugin()
```

### Setting Text on an Existing Node

```javascript
const text = await figma.getNodeByIdAsync('123:456')
if (text && text.type === 'TEXT') {
  if (text.hasMissingFont) {
    console.warn('Missing font; skipping content update.')
  } else {
    const segments = text.getStyledTextSegments(['fontName'])
    await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))
    text.characters = 'New content'
  }
}
figma.closePlugin()
```

### FigJam Preset Font Sizes

The FigJam font size dropdown uses these preset values (in px). Prefer them so created text matches the UI options:

| Preset (UI label) | Size (px) |
| ----------------- | --------- |
| Small             | 16        |
| Medium            | 24        |
| Large             | 40        |
| Extra large       | 64        |
| Huge              | 96        |

Helper for use in code:

```javascript
const FIGJAM_FONT_SIZES = {
  small: 16,
  medium: 24,
  large: 40,
  extraLarge: 64,
  huge: 96,
}
```

Users can also pick custom sizes (e.g. 1–2000); the presets are the standard choices.

#### Setting Size and Alignment

Load the font before changing layout-related properties:

```javascript
const text = figma.createText()
await figma.loadFontAsync(text.fontName)
text.characters = 'Heading'
text.fontSize = FIGJAM_FONT_SIZES.medium // 24 — matches FigJam "Medium"
text.textAlignHorizontal = 'CENTER'
text.textAlignVertical = 'CENTER'

figma.closePlugin()
```

### Bulleted and Numbered Lists

When creating content with numbered or bulleted lines, generate it line-by-line as a list by using `setRangeListOptions` and `setRangeIndentation` to properly render bullet points and numbers with indentation.

When creating lists with bullets or numbers, **do not** put literal bullet or number characters in the text (e.g. `"• Item 1\n• Item 2"` or `"1. First\n2. Second"`). Also **do not** build indentation in manually to items by including spaces (e.g. `    indented sub point`).

1. Set `characters` to the **content only** — one line per item, **no** leading `"• "`, `"1. "`, `A.`, `i.` or white space to manually create an indent.
2. Every line must have a list item type set, either 'ORDERED' for numbered/lettered lists, and 'UNORDERED' for bulleted lists. For each line that should be a list item, call **`setRangeListOptions(start, end, value)`** with the character range of that line (include the newline at the end of the line).
3. Every line must have an indentation level set. This is an integer **0–5**; use **1** for top-level list items. Use **`setRangeIndentation(start, end, level)`** to set this value for each line.

`setRangeListSpacing(start, end, value)` can optionally be used to add spacing between list items.
`getRangeListOptions(start, end)` or `getRangeIndentation(start, end)` can be used to inspect list options and indentation.

#### Example: Numbered list

```javascript
const text = figma.createText()
await figma.loadFontAsync(text.fontName)

// Content only — no number characters. Each entry: [line content, indentation level 0–5]
const items = [
  ['First main point', 1],
  ['Sub-point under first', 2],
  ['Sub-sub-point', 3],
  ['Second main point', 1],
  ['Sub-point under second', 2],
]

const lines = items.map(([content]) => content)
text.characters = lines.join('\n')

let offset = 0
for (let i = 0; i < items.length; i++) {
  const [content, indentLevel] = items[i]
  const start = offset
  // Only add +1 for newline if NOT the last line
  const end = offset + content.length + (i < lines.length - 1 ? 1 : 0)
  text.setRangeListOptions(start, end, { type: 'ORDERED' })
  text.setRangeIndentation(start, end, indentLevel)
  offset = end
}

figma.closePlugin()
```

#### Example: Bulleted list

```javascript
const text = figma.createText()
await figma.loadFontAsync(text.fontName)

// Each entry: [line content, indentation level 0–5]
const items = [
  ['Top-level item', 1],
  ['Nested under first', 2],
  ['Deeper nested', 3],
  ['Sibling at level 2', 2],
  ['Second top-level item', 1],
  ['Its nested child', 2],
]

const lines = items.map(([content]) => content)
text.characters = lines.join('\n')

let offset = 0
for (let i = 0; i < items.length; i++) {
  const [content, indentLevel] = items[i]
  const start = offset
  // Only add +1 for newline if NOT the last line
  const end = offset + content.length + (i < lines.length - 1 ? 1 : 0)
  text.setRangeListOptions(start, end, { type: 'UNORDERED' })
  text.setRangeIndentation(start, end, indentLevel)
  offset = end
}

figma.closePlugin()
```

### Cloning Text Nodes

```javascript
const original = await figma.getNodeByIdAsync('123:456')
if (original && original.type === 'TEXT') {
  const clone = original.clone()
  clone.x = original.x + original.width + 20
  console.log('Cloned text:', clone.id)
}
figma.closePlugin()
```

#### Modifying existing structures (mind maps, connected text)

Mind maps and similar structures use text nodes connected by connectors. When adding or inserting nodes, you must **shift existing nodes to make room** — otherwise nodes will overlap.

**Shift direction depends on the layout:**

- **Left-to-right flows:** shift downstream nodes along the **x-axis**
- **Tree / mind map branches:** shift sibling nodes along the **y-axis** — branches spread vertically, so new children need vertical space

##### Adding child nodes to a mind map branch

When adding multiple child nodes to a branch point, space each child vertically and shift any existing siblings below them downward:

```javascript
const branchNode = await figma.getNodeByIdAsync(branchNodeId)
const parent = branchNode.parent

const newTopics = ['Topic A', 'Topic B', 'Topic C']
const Y_SPACING = 40

// Measure total height the new nodes will need.
// Each newly created text node uses the same default font, so load it once
// before the loop rather than awaiting per-iteration.
const probe = figma.createText()
await figma.loadFontAsync(probe.fontName)
probe.remove()
const newTexts = []
for (const topic of newTopics) {
  const t = figma.createText()
  t.characters = topic
  newTexts.push(t)
}
const totalNewHeight =
  newTexts.reduce((sum, t) => sum + t.height, 0) + (newTexts.length - 1) * Y_SPACING

// Shift existing sibling nodes below the insertion point downward
for (const sibling of parent.children) {
  if (sibling.type === 'TEXT' && sibling.y > branchNode.y) {
    sibling.y += totalNewHeight + Y_SPACING
  }
}

// Place new nodes vertically, connected to the branch point
let curY = branchNode.y + branchNode.height + Y_SPACING
for (const t of newTexts) {
  parent.appendChild(t)
  t.x = branchNode.x - t.width - 80
  t.y = curY

  const conn = figma.createConnector()
  conn.connectorStart = { endpointNodeId: t.id, magnet: 'AUTO' }
  conn.connectorEnd = { endpointNodeId: branchNode.id, magnet: 'AUTO' }
  conn.connectorStartStrokeCap = 'NONE'
  conn.connectorEndStrokeCap = 'ARROW_LINES'
  parent.appendChild(conn)

  curY += t.height + Y_SPACING
}
```

##### Inserting a text node into a linear chain

For left-to-right connected text (not tree-shaped), shift downstream nodes horizontally:

```javascript
const leftNode = await figma.getNodeByIdAsync(leftNodeId)
const rightNode = await figma.getNodeByIdAsync(rightNodeId)
const oldConnector = await figma.getNodeByIdAsync(connectorId)
const parent = leftNode.parent

const newText = figma.createText()
await figma.loadFontAsync(newText.fontName)
newText.characters = 'New Topic'

// Shift nodes to the right to make room
const SPACING = 80
const shiftAmount = newText.width + SPACING
for (const sibling of parent.children) {
  if (sibling.type === 'TEXT' && sibling.x >= rightNode.x) {
    sibling.x += shiftAmount
  }
}

// Place the new node in the created gap
parent.appendChild(newText)
newText.x = leftNode.x + leftNode.width + SPACING / 2
newText.y = leftNode.y

// Rewire connectors
oldConnector.remove()
const conn1 = figma.createConnector()
conn1.connectorStart = { endpointNodeId: leftNode.id, magnet: 'AUTO' }
conn1.connectorEnd = { endpointNodeId: newText.id, magnet: 'AUTO' }
conn1.connectorStartStrokeCap = 'NONE'
conn1.connectorEndStrokeCap = 'ARROW_LINES'
parent.appendChild(conn1)

const conn2 = figma.createConnector()
conn2.connectorStart = { endpointNodeId: newText.id, magnet: 'AUTO' }
conn2.connectorEnd = { endpointNodeId: rightNode.id, magnet: 'AUTO' }
conn2.connectorStartStrokeCap = 'NONE'
conn2.connectorEndStrokeCap = 'ARROW_LINES'
parent.appendChild(conn2)
```

If the parent is a section, resize it afterward to encompass the new content (see [create-section](#reference--create-sections) — "Resizing an Existing Section").

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Follow the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`)** for `characters`, `fontSize`, `fontName`, or any property that affects layout; not required for `fills` (color) only.
- **Check `hasMissingFont`** when editing existing text; do not assume fonts are available.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.
- **Use the FigJam palette** with `hex/255` for text color.
- **Prefer FigJam font presets** (Inter, Merriweather, Roboto Mono, Figma Hand — UI labels: Simple, Bookish, Technical, Scribbled) and **preset font sizes** (16, 24, 40, 64, 96) so created text aligns with the font and size dropdowns in the UI.
- **For bulleted/numbered lists:** use `setRangeListOptions` and `setRangeIndentation` on line ranges; do not embed bullet or number characters in the text if it will be formatted as an ordered or unordered list.
- **Verify changes** by logging before/after values and exporting images when supported.

---

## Reference — FigJam Node Positioning Tutorial

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Positioning, sizing, and reparenting nodes on the canvas.

Use this skill when working with positioning, sizing, and reparenting nodes.

### Basics of how nodes are positioned

Nodes may be positioned by setting their `x` and `y` properties. Nodes are positioned with respect to their parent.

```javascript
// Position (relative to parent)
node.x = 100
node.y = 200
```

### Positioning Nodes Relative to Existing Nodes

It's important to remember that `node.x` and `node.y` are relative to the node's parent, not the page. For example: a node inside a section has coordinates relative to that section's origin.

When creating or placing a node relative to an existing node:

1. **Find the parent**: Locate the parent of the existing node.
2. **Add new node to parent**: Call `parent.appendChild()` to add the new node to the parent.
3. **Position within parent**: Position the new node within the parent. The x / y coordinates of the new node will be with respect to the top-left corner of the parent.
4. **Ensure parent sections encompass their children**: If the parent is a section:
   a. Resize the section to encompass the new node
   b. (see [create-section](#reference--create-sections) — "Resizing an Existing Section" for more info)

Example helper function:

```javascript
// existingNodeId (string): the node id you are positioning relative to
// nodeToPosition: the node you are trying to position relative to the existing node
async function placeNodeRelativeToOtherNode(existingNodeId, nodeToPosition) {

  // 1: find the parent of existing node
  const existingNode = await figma.getNodeByIdAsync(existingNodeId);
  const parent = existingNode.parent

  // 2: add the node to the parent
  parent.appendChild(nodeToPosition)

  // 3: position the node w.r.t the top-left corner of the parent
  // here, we chose to place it to the right of the existing node
  nodeToPosition.x = existingNode.x + existingNode.width + 40;
  nodeToPosition.y = existingNode.y;

  // 4: if the parent is a section: resize the section if needed
  if (parent.type === 'SECTION') {
    // ... resize if needed, (see [create-section](#reference--create-sections) — "Resizing an Existing Section" for more info)
  }
}
```

### Adding Nodes to a Section

Use `appendChild` to move existing nodes into a section.

**CRITICAL**: when you call `appendChild`, the node's x/y coordinates become relative to the **section's local coordinate space**, where (0,0) is the top-left corner of the section — NOT absolute board coordinates. Always call `appendChild` **first**, then set the node's position using section-local coordinates.

**IMPORTANT:** After adding nodes to a section, you MUST check that the section encompasses its children. Refer to the `Resizing an Existing Section` code snippet for reference. This is _crucial_ for a high-quality output.

Steps:

1. **Add new node to parent**: Call `parent.appendChild()` to add the new node to the parent.
2. **Position within parent**: Position the new node within the parent. The x / y coordinates of the new node will be with respect to the TL of the parent.
3. **Clean up any layout consequences**: If the parent is a section:
   a. Resize the section to encompass the new node
   b. (see [create-section](#reference--create-sections) — "Resizing an Existing Section" for more info)

Example helper function:

```javascript
function addNodeToSection(node, section) {
  // Ensure this is a section
  if (section.type !== 'SECTION') {
    console.log('The node provided is not a section')
    return
  }

  // Append FIRST, then position using section-local coordinates
  section.appendChild(node)
  node.x = 32
  node.y = 32
  console.log(`Moved ${node.name} into ${section.name}`)

  // ... resize section if needed, (see [create-section](#reference--create-sections) — "Resizing an Existing Section" for more info)
}
```

---

## Reference — Create Shapes with Text

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating shapes with embedded text for diagrams and visual layouts.

**Scope:** ShapeWithText nodes are FigJam-specific geometric shapes with built-in text, created with `figma.createShapeWithText()`. For tables, see [create-table](#reference--create-tables). For sections, see [create-section](#reference--create-sections). For stickies, see [create-sticky](#reference--create-sticky-notes).

**When NOT to use this skill:** For tabular-data (e.g. data tables, spreadsheets, comparison tables, rosters, or any row/column grid of text or data), use the [create-table](#reference--create-tables) skill instead. Do not build a table-like layout from a grid of shapes.

### Creating a Shape

```javascript
const shape = figma.createShapeWithText()
// Default shapeType is 'ELLIPSE'

await figma.loadFontAsync(shape.text.fontName)
shape.text.characters = 'Step 1'

console.log('Created shape:', shape.id, shape.shapeType, shape.text.characters)
figma.closePlugin()
```

### Shape Types

Set the `shapeType` property **after** creation. It defaults to `'ELLIPSE'`.

```javascript
const shape = figma.createShapeWithText()
shape.shapeType = 'DIAMOND'
```

Available shape types:

| Category          | Shape types                                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Basic             | `SQUARE`, `ELLIPSE`, `ROUNDED_RECTANGLE`, `DIAMOND`, `TRIANGLE_UP`, `TRIANGLE_DOWN`                                      |
| Arrows & Chevrons | `ARROW_LEFT`, `ARROW_RIGHT`, `CHEVRON`, `PENTAGON`, `HEXAGON`, `OCTAGON`                                                 |
| Flowchart         | `PARALLELOGRAM_RIGHT`, `PARALLELOGRAM_LEFT`, `TRAPEZOID`, `PREDEFINED_PROCESS`, `MANUAL_INPUT`, `SUMMING_JUNCTION`, `OR` |
| Engineering       | `ENG_DATABASE` (Cylinder), `ENG_QUEUE` (Horizontal cylinder), `ENG_FILE` (File), `ENG_FOLDER` (Folder)                   |
| Other             | `SHIELD`, `DOCUMENT_SINGLE`, `DOCUMENT_MULTIPLE`, `SPEECH_BUBBLE`, `STAR`, `PLUS`, `INTERNAL_STORAGE`                    |

#### Creating Different Shape Types

```javascript
const types = ['SQUARE', 'DIAMOND', 'ELLIPSE', 'ROUNDED_RECTANGLE']
// All shapes share the same default font — load once before the loop instead
// of awaiting per-iteration.
const probe = figma.createShapeWithText()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
const shapes = []
for (const type of types) {
  const s = figma.createShapeWithText()
  s.shapeType = type
  s.text.characters = type
  shapes.push(s)
}
figma.closePlugin()
```

### Setting Text

ShapeWithText nodes expose a `text` sublayer (a `TextSublayerNode`). The default font is **"Inter Medium"** (not "Inter Regular"). You must load the shape's own font before changing text. **Never hardcode a font name** — always read it from `shape.text.fontName`.

**Put all text content directly into `shape.text.characters`.** Do not split text into a short label and a separate description field — all content the user expects to see in the shape must be set as the characters. The `fitShapeToText` utility will automatically size the shape to fit the full text.

```javascript
const shape = figma.createShapeWithText()
await figma.loadFontAsync(shape.text.fontName)
shape.text.characters = 'Decision?'

figma.closePlugin()
```

To modify text on an existing shape:

```javascript
const shape = await figma.getNodeByIdAsync('123:456')
if (shape && shape.type === 'SHAPE_WITH_TEXT') {
  await figma.loadFontAsync(shape.text.fontName)
  console.log('Before:', shape.text.characters)
  shape.text.characters = 'Updated label'
  console.log('After:', shape.text.characters)
}
figma.closePlugin()
```

### Color Presets

FigJam shapes have **coordinated fill, stroke, and text colors**. When applying a color, you must set all three to match the FigJam palette — otherwise the shape will look wrong (e.g., dark text on a dark fill, or missing stroke). Strongly prefer colors from this list instead of custom colors. For the canonical palette across all FigJam node types, see [figjam-colors](#reference--figjam-colors).

Each color preset defines:

- **Fill**: the shape's background color (`shape.fills`)
- **Stroke**: the shape's outline color (`shape.strokes`)
- **Text**: the text color (`shape.text.fills` — set after loading fonts)

#### Color Preset Map

Use this map in your code to apply coordinated colors. **CRITICAL**: Use `hex/255` notation (e.g. `0x66/255`) for exact palette matching — rounded decimals cause FigJam to treat the color as "custom" instead of a palette color.

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const DARK = h(0x1e, 0x1e, 0x1e)

const SHAPE_COLOR_PRESETS = {
  // Dark fills use white text; stroke uses darker variant
  black: { fill: h(0x1e, 0x1e, 0x1e), stroke: h(0xb3, 0xb3, 0xb3), text: WHITE },
  darkGray: { fill: h(0x75, 0x75, 0x75), stroke: h(0x5e, 0x5e, 0x5e), text: WHITE },
  green: { fill: h(0x66, 0xd5, 0x75), stroke: h(0x3e, 0x9b, 0x4b), text: WHITE },
  teal: { fill: h(0x5a, 0xd8, 0xcc), stroke: h(0x36, 0x9e, 0x94), text: WHITE },
  blue: { fill: h(0x3d, 0xad, 0xff), stroke: h(0x00, 0x7a, 0xd2), text: WHITE },
  violet: { fill: h(0x87, 0x4f, 0xff), stroke: h(0x54, 0x27, 0xb4), text: WHITE },
  pink: { fill: h(0xf8, 0x49, 0xc1), stroke: h(0xb4, 0x24, 0x87), text: WHITE },
  red: { fill: h(0xff, 0x75, 0x56), stroke: h(0xdc, 0x30, 0x09), text: WHITE },
  orange: { fill: h(0xff, 0x9e, 0x42), stroke: h(0xeb, 0x75, 0x00), text: WHITE },

  // Light fills use dark text; stroke uses the corresponding dark variant
  gray: { fill: h(0xb3, 0xb3, 0xb3), stroke: h(0x8f, 0x8f, 0x8f), text: DARK },
  lightGray: { fill: h(0xd9, 0xd9, 0xd9), stroke: h(0xb3, 0xb3, 0xb3), text: DARK },
  lightGreen: { fill: h(0xcd, 0xf4, 0xd3), stroke: h(0x66, 0xd5, 0x75), text: DARK },
  lightTeal: { fill: h(0xc6, 0xfa, 0xf6), stroke: h(0x5a, 0xd8, 0xcc), text: DARK },
  lightBlue: { fill: h(0xc2, 0xe5, 0xff), stroke: h(0x3d, 0xad, 0xff), text: DARK },
  lightViolet: { fill: h(0xdc, 0xcc, 0xff), stroke: h(0x87, 0x4f, 0xff), text: DARK },
  lightPink: { fill: h(0xff, 0xc2, 0xec), stroke: h(0xf8, 0x49, 0xc1), text: DARK },
  lightRed: { fill: h(0xff, 0xcd, 0xc2), stroke: h(0xff, 0x75, 0x56), text: DARK },
  lightOrange: { fill: h(0xff, 0xe0, 0xc2), stroke: h(0xff, 0x9e, 0x42), text: DARK },
  yellow: { fill: h(0xff, 0xc9, 0x43), stroke: h(0xe8, 0xa3, 0x02), text: DARK },
  lightYellow: { fill: h(0xff, 0xec, 0xbd), stroke: h(0xff, 0xc9, 0x43), text: DARK },
  white: { fill: h(0xff, 0xff, 0xff), stroke: h(0xb3, 0xb3, 0xb3), text: DARK },
}
```

#### Hex Reference

| Color        | Fill Hex  | Stroke Hex | Text  |
| ------------ | --------- | ---------- | ----- |
| Black        | `#1E1E1E` | `#B3B3B3`  | white |
| Dark gray    | `#757575` | `#5E5E5E`  | white |
| Gray         | `#B3B3B3` | `#8F8F8F`  | dark  |
| Light gray   | `#D9D9D9` | `#B3B3B3`  | dark  |
| Green        | `#66D575` | `#3E9B4B`  | white |
| Light green  | `#CDF4D3` | `#66D575`  | dark  |
| Teal         | `#5AD8CC` | `#369E94`  | white |
| Light teal   | `#C6FAF6` | `#5AD8CC`  | dark  |
| Blue         | `#3DADFF` | `#007AD2`  | white |
| Light blue   | `#C2E5FF` | `#3DADFF`  | dark  |
| Violet       | `#874FFF` | `#5427B4`  | white |
| Light violet | `#DCCCFF` | `#874FFF`  | dark  |
| Pink         | `#F849C1` | `#B42487`  | white |
| Light pink   | `#FFC2EC` | `#F849C1`  | dark  |
| Red          | `#FF7556` | `#DC3009`  | white |
| Light red    | `#FFCDC2` | `#FF7556`  | dark  |
| Orange       | `#FF9E42` | `#EB7500`  | white |
| Light orange | `#FFE0C2` | `#FF9E42`  | dark  |
| Yellow       | `#FFC943` | `#E8A302`  | dark  |
| Light yellow | `#FFECBD` | `#FFC943`  | dark  |
| White        | `#FFFFFF` | `#B3B3B3`  | dark  |

_white = `#FFFFFF`, dark = `#1E1E1E`_

#### Applying a Color Preset

Always set fill, stroke, and text color together:

```javascript
function applyColorPreset(shape, preset) {
  shape.fills = [{ type: 'SOLID', color: preset.fill }]
  shape.strokes = [{ type: 'SOLID', color: preset.stroke }]
  shape.text.fills = [{ type: 'SOLID', color: preset.text }]
}

const shape = figma.createShapeWithText()
await figma.loadFontAsync(shape.text.fontName)
shape.text.characters = 'Start'
applyColorPreset(shape, SHAPE_COLOR_PRESETS.lightGreen)

figma.closePlugin()
```

#### Changing Color on an Existing Shape

```javascript
const shape = await figma.getNodeByIdAsync('123:456')
if (shape && shape.type === 'SHAPE_WITH_TEXT') {
  await figma.loadFontAsync(shape.text.fontName)
  const preset = SHAPE_COLOR_PRESETS.lightBlue
  shape.fills = [{ type: 'SOLID', color: preset.fill }]
  shape.strokes = [{ type: 'SOLID', color: preset.stroke }]
  shape.text.fills = [{ type: 'SOLID', color: preset.text }]
}
figma.closePlugin()
```

### Resizing

Use `resize(width, height)` to change the size. Both values must be >= 0.01. `width` and `height` properties are **read-only**. `rescale(scale)` resizes proportionally from the top-left corner.

### Sizing Shapes to Fit Text (REQUIRED)

**CRITICAL: Never hardcode shape dimensions.** Default sizes are too small for most text and will clip. You **must** dynamically size every shape to fit its text content using a measurement TextNode.

#### How it works

Create a temporary TextNode with `textAutoResize: 'HEIGHT'`, use it to measure how tall text will be at a given width, and scale shapes up until the text fits. Remove the measurer when done.

#### Utility code — include this in any code that creates shapes with text

```javascript
const NON_RECT_TYPES = new Set([
  'DIAMOND',
  'TRIANGLE_UP',
  'TRIANGLE_DOWN',
  'ELLIPSE',
  'HEXAGON',
  'OCTAGON',
  'STAR',
  'PENTAGON',
])
const BASE_W = 200
const BASE_H = 120
const MAX_SCALE = 3
const PADDING = 32

const measurer = figma.createText()
const SWT_FONT = { family: 'Inter', style: 'Medium' }
await figma.loadFontAsync(SWT_FONT)
measurer.fontName = SWT_FONT
measurer.textAutoResize = 'HEIGHT'

function textAreaForShape(shapeType, w, h) {
  if (NON_RECT_TYPES.has(shapeType)) {
    return { w: w / 2 - PADDING, h: h / 2 - PADDING }
  }
  return { w: w - PADDING * 2, h: h - PADDING * 2 }
}

function fitShapeToText(label, shapeType) {
  let w = BASE_W
  let h = BASE_H
  if (NON_RECT_TYPES.has(shapeType)) {
    w = Math.round(BASE_W * 1.6)
    h = Math.round(BASE_H * 1.6)
  }
  const origW = w,
    origH = h
  let scale = 1
  while (scale < MAX_SCALE) {
    const area = textAreaForShape(shapeType, w, h)
    measurer.resize(Math.max(area.w, 1), measurer.height)
    measurer.characters = label
    if (measurer.height <= area.h) break
    scale += 0.1
    w = Math.round(origW * scale)
    h = Math.round(origH * scale)
  }
  return { w, h }
}
```

Then for each shape, call `fitShapeToText(label, shapeType)` to get the right dimensions before calling `shape.resize(w, h)`. **Always call `measurer.remove()` after all shapes are created.**

### Rotation

**Only rotate shapes when the user explicitly asks for it.** Do not add rotation for visual flair — FigJam shapes should default to 0° rotation.

The `rotation` property sets degrees from -180 to 180, rotating around the top-left corner:

```javascript
const shape = await figma.getNodeByIdAsync('123:456')
if (shape && shape.type === 'SHAPE_WITH_TEXT') {
  shape.rotation = 45
}
figma.closePlugin()
```

### Opacity and Blend Mode

```javascript
const shape = figma.createShapeWithText()
await figma.loadFontAsync(shape.text.fontName)
shape.text.characters = 'Semi-transparent'

shape.opacity = 0.5
console.log('Opacity:', shape.opacity)

figma.closePlugin()
```

### Batch Creation: Row of Different Shapes

Uses the `fitShapeToText` utility from above to size each shape to its label:

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const DARK = h(0x1e, 0x1e, 0x1e)
const PRESETS = {
  lightGreen: { fill: h(0xcd, 0xf4, 0xd3), stroke: h(0x66, 0xd5, 0x75), text: DARK },
  lightBlue: { fill: h(0xc2, 0xe5, 0xff), stroke: h(0x3d, 0xad, 0xff), text: DARK },
  lightYellow: { fill: h(0xff, 0xec, 0xbd), stroke: h(0xff, 0xc9, 0x43), text: DARK },
  lightRed: { fill: h(0xff, 0xcd, 0xc2), stroke: h(0xff, 0x75, 0x56), text: DARK },
}

const items = [
  { label: 'Start', type: 'ROUNDED_RECTANGLE', color: PRESETS.lightGreen },
  { label: 'Process', type: 'SQUARE', color: PRESETS.lightBlue },
  { label: 'Decision', type: 'DIAMOND', color: PRESETS.lightYellow },
  { label: 'End', type: 'ELLIPSE', color: PRESETS.lightRed },
]
const spacing = 40

// ... include fitShapeToText utility code from above ...

const sizes = items.map((item) => fitShapeToText(item.label, item.type))
const totalWidth = sizes.reduce((sum, s) => sum + s.w, 0) + (items.length - 1) * spacing
let curX = 0

// All shapes share the same default font — load once before the loop
// instead of awaiting per-iteration.
const probe = figma.createShapeWithText()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
for (let i = 0; i < items.length; i++) {
  const size = sizes[i]
  const shape = figma.createShapeWithText()
  shape.shapeType = items[i].type
  shape.text.characters = items[i].label
  shape.resize(size.w, size.h)
  const preset = items[i].color
  shape.fills = [{ type: 'SOLID', color: preset.fill }]
  shape.strokes = [{ type: 'SOLID', color: preset.stroke }]
  shape.text.fills = [{ type: 'SOLID', color: preset.text }]
  shape.x = curX
  curX += size.w + spacing
}
measurer.remove()

figma.closePlugin()
```

### Cloning Shapes

```javascript
const original = await figma.getNodeByIdAsync('123:456')
if (original && original.type === 'SHAPE_WITH_TEXT') {
  const clone = original.clone()
  clone.x = original.x + original.width + 40
  console.log('Cloned shape:', clone.id, clone.shapeType)
}
figma.closePlugin()
```

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Follow the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`)** for `shape.text.characters` — always load `shape.text.fontName` (ShapeWithText defaults to `Inter Medium`, not Regular); never hardcode the family/style.
- **Connector text needs explicit font setup.** Unlike shapes, a ConnectorNode's `text.fontName` is invalid by default. To label a connector, first set `connector.text.fontName = { family: 'Inter', style: 'Medium' }` (font must already be loaded), then set `connector.text.characters`. Never call `figma.loadFontAsync(connector.text.fontName)` — it will fail.
- **Put ALL text content in `shape.text.characters`** — do not split into a short label and a separate description/metadata field. The shape should display the full text the user expects to see, and `fitShapeToText` will size it accordingly.
- **Never hardcode shape sizes. Always use `fitShapeToText`** to dynamically size shapes based on their text content. Create a measurer TextNode with `textAutoResize: 'HEIGHT'`, use it to measure text, scale shapes until text fits, then call `measurer.remove()`. This prevents text clipping.
- **Always set fill, stroke, AND text color together** using the color presets — setting only fills will leave mismatched stroke/text colors.
- **Set `shapeType` after creation:** `shape.shapeType = 'DIAMOND'` — use different types when the user asks for varied shapes.
- **Do not rotate** shapes unless the user explicitly asks for rotation.
- **Use `resize()`** not `resizeWithoutConstraints()` — shapes support `resize()` and `rescale()`.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.
- **Verify changes** by logging before/after values and exporting images when supported.

---

## Reference — Create Code Blocks

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating and configuring FigJam code block nodes.

**Scope:** Code blocks are FigJam-specific nodes created with `figma.createCodeBlock()`. They render code content with syntax highlighting and a monospace font. `CODE_BLOCK` is a first-class node type — not a shape or text node.

### Creating a Code Block

```javascript
// Snapshot existing children before creating the node — createCodeBlock() auto-appends to the page
const existingNodes = figma.currentPage.children.slice()

const cb = figma.createCodeBlock()
cb.code = 'const greeting = "Hello, FigJam!"'
cb.codeLanguage = 'JAVASCRIPT'

// Position away from (0,0) — find clear space to the right of existing content
const rightEdge = existingNodes.length > 0 ? Math.max(...existingNodes.map((n) => n.x + n.width)) : 0
cb.x = rightEdge + 100
cb.y = 100

return { id: cb.id, x: cb.x, y: cb.y }
```

### Supported Languages (`codeLanguage`)

Pass one of these exact uppercase string values. Omitting `codeLanguage` defaults to `PLAINTEXT`.

| Value | Language |
|---|---|
| `TYPESCRIPT` | TypeScript |
| `JAVASCRIPT` | JavaScript |
| `PYTHON` | Python |
| `GO` | Go |
| `RUST` | Rust |
| `RUBY` | Ruby |
| `CSS` | CSS |
| `HTML` | HTML |
| `JSON` | JSON |
| `GRAPHQL` | GraphQL |
| `SQL` | SQL |
| `SWIFT` | Swift |
| `KOTLIN` | Kotlin |
| `CPP` | C++ |
| `BASH` | Bash / Shell |
| `PLAINTEXT` | Plain text (no highlighting) |

If the user specifies a language not in this list, use `PLAINTEXT`.

### Setting Code Content

The `code` property maps to the node's text sublayer — set it after creating the node:

```javascript
const cb = figma.createCodeBlock()
cb.code = `function add(a, b) {
  return a + b
}`
cb.codeLanguage = 'TYPESCRIPT'
return { id: cb.id }
```

### Positioning Within a Section

To place a code block inside a FigJam section, append it to the section instead of the page:

```javascript
// Use the type-indexed criteria for the type filter, then narrow by name.
const section = figma.currentPage
  .findAllWithCriteria({ types: ['SECTION'] })
  .find((n) => n.name === 'My Section')
if (!section) throw new Error('Section not found')

const cb = figma.createCodeBlock()
cb.code = 'SELECT * FROM users WHERE active = true'
cb.codeLanguage = 'SQL'

section.appendChild(cb)

// Position relative to section origin
cb.x = 40
cb.y = 40

return { id: cb.id }
```

### Important Notes

- `CODE_BLOCK` is **FigJam-only** — this will throw in Figma design files.
- There is no theme/color API for code blocks; FigJam handles the visual styling automatically.
- Always `return` the created node's `id` for reference in follow-up calls (see figma-use rule #15).
- No font loading is required — code blocks handle their own monospace rendering.

---

## Reference — Create Tables

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating and styling tables with rows, columns, and cell content.

**Scope:** Tables are FigJam-specific nodes created with `figma.createTable()`. They structure content in rows and columns. For stickies and sections, see [create-sticky](#reference--create-sticky-notes) and [create-section](#reference--create-sections). For shapes with text in them, see [create-shape-with-text](#reference--create-shapes-with-text).

**When to use this skill:** Prefer FigJam tables whenever the user asks for a table, spreadsheet, comparison grid, roster, or any row/column layout of text data. Examples: "create a table", "add a spreadsheet", "make a grid with names and roles", "comparison table", "team roster", "data table". Do **not** build a table-like layout out of shapes with text or other node types.

**When NOT to use this skill:** Prefer creating other node types or relying on node positioning on the canvas in order to organize non-text content.

**Note:** The Table API is only available in FigJam.

### Creating a Table

Default to applying a dark color to the header row(s) but leave the other cells to have the default fill (without making any edits), unless the user provides guiddance on styling.

**CRITICAL**: If the user provides real data to include (e.g. in the form of CSV, image, etc.), include **all** of it in the resulting table. Never intermix real data with placeholder data. Otherwise if no data is provied, create tables without any placeholder content in headers, rows, columns, or cells.

**CRITICAL**: Never delete any source data from the canvas when asked to convert to a table.

```javascript
// Default: 2 rows, 2 columns, parented under figma.currentPage
const table = figma.createTable()

// Or specify dimensions: createTable(numRows?, numColumns?)
const table3x4 = figma.createTable(3, 4)

console.log('Created table:', table.id, table.numRows, 'x', table.numColumns)
figma.closePlugin()
```

### Setting Cell Text

Each cell is a `TableCellNode` with a `text` sublayer (`TextSublayerNode`). You must load the font before setting `characters`. Use `table.cellAt(rowIndex, columnIndex)` to get a cell (indices are zero-based).

```javascript
const table = figma.createTable(2, 3)

// Load the font before setting characters
await figma.loadFontAsync(table.cellAt(0, 0).text.fontName)

// Set characters for each cell (example: header row A B C, data row 1 2 3)
table.cellAt(0, 0).text.characters = 'A'
table.cellAt(0, 1).text.characters = 'B'
table.cellAt(0, 2).text.characters = 'C'
table.cellAt(1, 0).text.characters = '1'
table.cellAt(1, 1).text.characters = '2'
table.cellAt(1, 2).text.characters = '3'

table.x = 0
table.y = 0

figma.closePlugin()
```

#### Modifying Text in an Existing Table

```javascript
const table = await figma.getNodeByIdAsync('123:456')
if (table && table.type === 'TABLE') {
  const cell = table.cellAt(0, 0)
  await figma.loadFontAsync(cell.text.fontName)
  cell.text.characters = 'Updated'
}
figma.closePlugin()
```

### TableNode Properties

- **type**: `'TABLE'` (readonly)
- **numRows**, **numColumns**: number (readonly) — number of rows and columns
- **cellAt(rowIndex, columnIndex)**: returns the `TableCellNode` at that position
- **width**, **height**: number (readonly) — use `resizeRow` / `resizeColumn` to change size

#### Adding and Removing Rows/Columns

```javascript
const table = figma.createTable(2, 2)

// Insert a row before index 1 (so new row is at index 1)
table.insertRow(1)

// Insert a column before index 0
table.insertColumn(0)

// Remove row at index 2, column at index 0
table.removeRow(2)
table.removeColumn(0)

figma.closePlugin()
```

#### Moving Rows and Columns

```javascript
const table = await figma.getNodeByIdAsync('123:456')
if (table && table.type === 'TABLE') {
  // moveRow(fromIndex, toIndex) — move row from fromIndex to toIndex
  table.moveRow(2, 0)

  // moveColumn(fromIndex, toIndex)
  table.moveColumn(1, 0)
}
figma.closePlugin()
```

#### Resizing Rows and Columns

Rows and columns cannot be resized smaller than their minimum size. Use `resizeRow(rowIndex, height)` and `resizeColumn(columnIndex, width)`.

```javascript
const table = figma.createTable(3, 3)

// Resize first row to 60px height, first column to 120px width
table.resizeRow(0, 60)
table.resizeColumn(0, 120)

console.log('Table size:', table.width, 'x', table.height)
figma.closePlugin()
```

### TableCellNode Properties

- **type**: `'TABLE_CELL'` (readonly)
- **text**: TextSublayerNode (readonly) — the cell’s text; load font then set `text.characters`
- **rowIndex**, **columnIndex**: number (readonly) — cell position in the table
- **width**, **height**: number (readonly) — determined by table layout
- **fills**: set cell background (e.g. header row styling)

#### Setting Cell Fills

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const table = figma.createTable(2, 3)
await figma.loadFontAsync(table.cellAt(0, 0).text.fontName)

// Header row: light blue background
for (let c = 0; c < 3; c++) {
  const cell = table.cellAt(0, c)
  cell.fills = [{ type: 'SOLID', color: h(0xc2, 0xe5, 0xff) }] // Light blue #C2E5FF
  cell.text.characters = ['A', 'B', 'C'][c]
}
// Data row
table.cellAt(1, 0).text.characters = '1'
table.cellAt(1, 1).text.characters = '2'
table.cellAt(1, 2).text.characters = '3'

figma.closePlugin()
```

### Table-Level Fills

The table itself has a `fills` property for the overall table background. Use `setFillsAsync` for pattern fills; for solid fills you can set `table.fills` directly.

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const table = figma.createTable(2, 2)
table.fills = [{ type: 'SOLID', color: h(0xff, 0xec, 0xbd) }] // Light yellow #FFECBD

figma.closePlugin()
```

### Color Options

FigJam tables use the same color palette as sections and shapes. You can style:

- **Table fill** — `table.fills` (overall table background)
- **Cell fill** — `table.cellAt(row, col).fills` (per-cell background, e.g. header row)
- **Cell text color** — `cell.text.fills` (set after loading fonts)

Tables do **not** have strokes. When applying colors, set **fill and text together** so contrast is correct: dark fills use white text; light fills use dark text. Strongly prefer colors from this list so the table matches the FigJam editor palette.

#### Color Preset Map

Use this map for table fills and cell fills. For **cell text**, use the `text` value (white on dark fills, dark on light fills). **CRITICAL**: Use `hex/255` notation (e.g. `0x66/255`) for exact palette matching — rounded decimals cause FigJam to treat the color as "custom" instead of a palette color.

If the user asks for a color by a similar but different name, identify the closest option available from this map, keeping in mind the cell context (e.g. header row, body cell, etc). For example, choose `violet` if asked for a purple header or `lightGreen` if asked for green rows.

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const DARK = h(0x1e, 0x1e, 0x1e)

const TABLE_COLOR_PRESETS = {
  // Dark fills (e.g. header row) — use white text
  black: { fill: h(0x1e, 0x1e, 0x1e), text: WHITE },
  darkGray: { fill: h(0x75, 0x75, 0x75), text: WHITE },
  green: { fill: h(0x66, 0xd5, 0x75), text: WHITE },
  teal: { fill: h(0x5a, 0xd8, 0xcc), text: WHITE },
  blue: { fill: h(0x3d, 0xad, 0xff), text: WHITE },
  violet: { fill: h(0x87, 0x4f, 0xff), text: WHITE },
  pink: { fill: h(0xf8, 0x49, 0xc1), text: WHITE },
  red: { fill: h(0xf2, 0x48, 0x22), text: WHITE },
  orange: { fill: h(0xff, 0x9e, 0x42), text: WHITE },

  // Light fills (e.g. table background, body cells) — use dark text
  gray: { fill: h(0xb3, 0xb3, 0xb3), text: DARK },
  lightGray: { fill: h(0xd9, 0xd9, 0xd9), text: DARK },
  lightGreen: { fill: h(0xcd, 0xf4, 0xd3), text: DARK },
  lightTeal: { fill: h(0xc6, 0xfa, 0xf6), text: DARK },
  lightBlue: { fill: h(0xc2, 0xe5, 0xff), text: DARK },
  lightViolet: { fill: h(0xdc, 0xcc, 0xff), text: DARK },
  lightPink: { fill: h(0xff, 0xc2, 0xec), text: DARK },
  lightRed: { fill: h(0xff, 0xc7, 0xc2), text: DARK },
  lightOrange: { fill: h(0xff, 0xe0, 0xc2), text: DARK },
  yellow: { fill: h(0xff, 0xc9, 0x43), text: DARK },
  lightYellow: { fill: h(0xff, 0xec, 0xbd), text: DARK },
  white: { fill: h(0xff, 0xff, 0xff), text: DARK },
}
```

#### Hex Reference

| Color        | Fill Hex  | Text  |
| ------------ | --------- | ----- |
| Black        | `#1E1E1E` | white |
| Dark gray    | `#757575` | white |
| Gray         | `#B3B3B3` | dark  |
| Light gray   | `#D9D9D9` | dark  |
| Green        | `#66D575` | white |
| Light green  | `#CDF4D3` | dark  |
| Teal         | `#5AD8CC` | white |
| Light teal   | `#C6FAF6` | dark  |
| Blue         | `#3DADFF` | white |
| Light blue   | `#C2E5FF` | dark  |
| Violet       | `#874FFF` | white |
| Light violet | `#DCCCFF` | dark  |
| Pink         | `#F849C1` | white |
| Light pink   | `#FFC2EC` | dark  |
| Red          | `#F24822` | white |
| Light red    | `#FFC7C2` | dark  |
| Orange       | `#FF9E42` | white |
| Light orange | `#FFE0C2` | dark  |
| Yellow       | `#FFC943` | dark  |
| Light yellow | `#FFECBD` | dark  |
| White        | `#FFFFFF` | dark  |

_white = `#FFFFFF`, dark = `#1E1E1E`_

#### Applying Table and Cell Colors

Set table background, then cell fills and text colors. Load the cell font before setting `text.fills` or `text.characters`:

**CRITICAL**: Never clear or remove the fill from a table or cell node. Instead, interpret this as an ask to reset to the default fill color (i.e. white).

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const DARK = h(0x1e, 0x1e, 0x1e)
const preset = {
  fill: h(0xc2, 0xe5, 0xff), // Light blue
  text: DARK,
}

const table = figma.createTable(2, 3)
await figma.loadFontAsync(table.cellAt(0, 0).text.fontName)

// Table-level background
table.fills = [{ type: 'SOLID', color: preset.fill }]

// Header row: dark fill, white text
const headerPreset = { fill: h(0x3d, 0xad, 0xff), text: h(0xff, 0xff, 0xff) }
for (let c = 0; c < 3; c++) {
  const cell = table.cellAt(0, c)
  cell.fills = [{ type: 'SOLID', color: headerPreset.fill }]
  cell.text.fills = [{ type: 'SOLID', color: headerPreset.text }]
  cell.text.characters = ['Name', 'Role', 'Team'][c]
}

// Body row: light fill (or inherit table fill), dark text
for (let c = 0; c < 3; c++) {
  const cell = table.cellAt(1, c)
  cell.text.fills = [{ type: 'SOLID', color: preset.text }]
  cell.text.characters = ['Alice', 'Designer', 'Product'][c]
}

figma.closePlugin()
```

#### Changing Color on an Existing Table

```javascript
const table = await figma.getNodeByIdAsync('123:456')
if (table && table.type === 'TABLE') {
  await figma.loadFontAsync(table.cellAt(0, 0).text.fontName)
  const preset = TABLE_COLOR_PRESETS.lightGreen
  table.fills = [{ type: 'SOLID', color: preset.fill }]
  // Optionally update header or specific cells
  table.cellAt(0, 0).fills = [{ type: 'SOLID', color: preset.fill }]
  table.cellAt(0, 0).text.fills = [{ type: 'SOLID', color: preset.text }]
}
figma.closePlugin()
```

### Building a Table from Data

```javascript
const rows = [
  ['Name', 'Role', 'Team'],
  ['Alice', 'Designer', 'Product'],
  ['Bob', 'Engineer', 'Platform'],
]
const numRows = rows.length
const numCols = rows[0].length

const table = figma.createTable(numRows, numCols)
await figma.loadFontAsync(table.cellAt(0, 0).text.fontName)

for (let r = 0; r < numRows; r++) {
  for (let c = 0; c < numCols; c++) {
    table.cellAt(r, c).text.characters = rows[r][c]
  }
}

table.name = 'Team roster'

figma.closePlugin()
```

### Cloning Tables

```javascript
const original = await figma.getNodeByIdAsync('123:456')
if (original && original.type === 'TABLE') {
  const clone = original.clone()
  clone.x = original.x + original.width + 20
  console.log('Cloned table:', clone.id, clone.numRows, 'x', clone.numColumns)
}
figma.closePlugin()
```

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Initial table content:** Prefer empty tables unless the user provides data; then include all of it (no placeholders) and do not delete source data when converting. Use a dark header row and default fill elsewhere.
- **Follow the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`)** for `cell.text.characters` and `cell.text.fills` — load `cell.text.fontName` (use the first cell’s, or each cell’s if they differ).
- **Set fill and text color together** when styling cells — use the color presets so light fills get dark text and dark fills get white text.
- **Use `hex/255` notation** for palette colors (e.g. `h(0xC2, 0xE5, 0xFF)`) so FigJam treats them as palette colors, not custom.
- **Table API is FigJam-only** — `figma.createTable()` is not available in Figma Design or other editor types.
- **Indices are zero-based**: `cellAt(0, 0)` is the top-left cell.
- **Table dimensions**: `width` and `height` are readonly; use `resizeRow` and `resizeColumn` to change size. Rows/columns cannot be resized below their minimum.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.
- **Verify changes** by logging before/after values when helpful.

---

## Reference — Text Operations

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Editing existing text content, styles, and font segments.

### Critical: Load Fonts First

Follow the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`) — load font → `await` → mutate → return affected IDs. Skipping the load throws `Cannot write to node with unloaded font "<family> <style>"`. Inter is preloaded in most environments; every other family (and every Inter style you haven't already loaded) still needs an explicit `loadFontAsync`.

```javascript
// Load a single font
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' })

// Load a font used by a single-font text node
await figma.loadFontAsync(textNode.fontName)

// Load all fonts in a text node (handles mixed fonts via styled segments)
const segments = textNode.getStyledTextSegments(['fontName'])
await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))
```

### Complete Working Example

```javascript
const nodeId = '123:456'
const node = await figma.getNodeByIdAsync(nodeId)

if (node && node.type === 'TEXT') {
  // Load all fonts used in this text node (handles mixed fonts via styled segments)
  const segments = node.getStyledTextSegments(['fontName'])
  await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))

  console.log('Before:', node.characters)
  node.characters = 'New text content'
  console.log('After:', node.characters)

  // Verify with image
  const img = await node.exportAsync({
    format: 'PNG',
    constraint: { type: node.width > node.height ? 'WIDTH' : 'HEIGHT', value: 128 },
  })
  figma.io.write(`${node.name.replace(/[^a-z0-9]/gi, '_')}_result.png`, img)
}
figma.closePlugin()
```

### Basic Properties

Follows the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`) — load every (family, style) you're about to assign (including the NEW font when changing `fontName`) before any text mutation.

```javascript
// Required for any font, not just Inter
await figma.loadFontAsync({ family: 'Inter', style: 'Bold' })

// Text content
textNode.characters = 'Hello, World!'

// Font
textNode.fontName = { family: 'Inter', style: 'Bold' }

// Size
textNode.fontSize = 16

// Color (via fills) — use Charcoal (#1E1E1E) as default
textNode.fills = [{ type: 'SOLID', color: { r: 0x1e / 255, g: 0x1e / 255, b: 0x1e / 255 } }]
```

#### Text Color in FigJam

**CRITICAL**: When editing text in FigJam board content (templates, brainstorms, retros, or any generated content), always use **Charcoal (#1E1E1E)** as the text color unless the user has specifically requested different colors. Use `hex/255` notation for exact palette matching. For non-text node colors and the canonical palette across all FigJam node types, see [figjam-colors](#reference--figjam-colors).

```javascript
// Charcoal — default for all FigJam text
textNode.fills = [{ type: 'SOLID', color: { r: 0x1e / 255, g: 0x1e / 255, b: 0x1e / 255 } }]
```

Do not use grey (#757575, #B3B3B3) or light grey (#D9D9D9) for body text, headers, or descriptions — these make content look unfinished and hard to read.

### Text Alignment

```javascript
// Horizontal alignment
textNode.textAlignHorizontal = 'LEFT' // LEFT, CENTER, RIGHT, JUSTIFIED

// Vertical alignment
textNode.textAlignVertical = 'TOP' // TOP, CENTER, BOTTOM
```

### Line Height and Spacing

```javascript
// Line height
textNode.lineHeight = { value: 150, unit: 'PERCENT' }
textNode.lineHeight = { value: 24, unit: 'PIXELS' }
textNode.lineHeight = { unit: 'AUTO' }

// Letter spacing
textNode.letterSpacing = { value: 0, unit: 'PERCENT' }
textNode.letterSpacing = { value: 1, unit: 'PIXELS' }

// Paragraph spacing
textNode.paragraphSpacing = 16

// Paragraph indentation
textNode.paragraphIndent = 24
```

### Text Decoration

Underlines and strikethroughs support styling (wavy, dotted), offset, and color.

```javascript
textNode.textDecoration = 'UNDERLINE' // NONE, UNDERLINE, STRIKETHROUGH
textNode.textDecorationStyle = 'WAVY' // SOLID, DOTTED, WAVY
textNode.textDecorationOffset = { unit: 'PIXELS', value: 2 }
textNode.textDecorationColor = { value: { type: 'SOLID', color: { r: 1, g: 0, b: 0 } } } // Custom color
textNode.textDecorationColor = { value: 'AUTO' } // Inherit from text color
```

### Text Case

```javascript
// Case transformation
textNode.textCase = 'ORIGINAL' // ORIGINAL, UPPER, LOWER, TITLE, SMALL_CAPS, SMALL_CAPS_FORCED
```

### Text Sizing Behavior

```javascript
// Auto-resize mode
textNode.textAutoResize = 'WIDTH_AND_HEIGHT' // Auto-size both
textNode.textAutoResize = 'HEIGHT' // Fixed width, auto height
textNode.textAutoResize = 'NONE' // Fixed size
// Truncation pattern (preferred over deprecated textAutoResize = 'TRUNCATE')
textNode.textAutoResize = 'NONE' // Keep fixed bounds
textNode.textTruncation = 'ENDING' // Truncate overflow with ellipsis
textNode.maxLines = 2 // Optional: cap visible lines
```

### Styled Ranges (Mixed Styles)

For text with different styles in different parts:

```javascript
await figma.loadFontAsync({ family: 'Inter', style: 'Bold' })
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' })

textNode.characters = 'Hello World'

// Make "Hello" bold (characters 0-5)
textNode.setRangeFontName(0, 5, { family: 'Inter', style: 'Bold' })

// Make "World" red (characters 6-11)
textNode.setRangeFills(6, 11, [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }])

// Change size of "World"
textNode.setRangeFontSize(6, 11, 24)

// Get properties for a range
const fontAtStart = textNode.getRangeFontName(0, 1)
const sizeAtEnd = textNode.getRangeFontSize(10, 11)
```

### Available Range Methods

- `setRangeFontName(start, end, fontName)`
- `setRangeFontSize(start, end, size)`
- `setRangeFills(start, end, fills)`
- `setRangeTextDecoration(start, end, decoration)`
- `setRangeTextCase(start, end, textCase)`
- `setRangeLetterSpacing(start, end, spacing)`
- `setRangeLineHeight(start, end, lineHeight)`
- `setRangeHyperlink(start, end, hyperlink)`
- `setRangeListOptions(start, end, listOptions)`
- `setRangeIndentation(start, end, indentation)`

### Hyperlinks

```javascript
// Set hyperlink
textNode.setRangeHyperlink(0, 5, { type: 'URL', value: 'https://figma.com' })

// Node link
textNode.setRangeHyperlink(0, 5, { type: 'NODE', value: '123:456' })

// Remove hyperlink
textNode.setRangeHyperlink(0, 5, null)
```

### Lists

```javascript
// Bulleted list
textNode.setRangeListOptions(0, textNode.characters.length, { type: 'UNORDERED' })

// Numbered list
textNode.setRangeListOptions(0, textNode.characters.length, { type: 'ORDERED' })

// Remove list
textNode.setRangeListOptions(0, textNode.characters.length, { type: 'NONE' })
```

### Getting Text Segments

```javascript
// Get all styled segments
const segments = textNode.getStyledTextSegments(['fontName', 'fontSize', 'fills', 'textDecoration'])

for (const segment of segments) {
  console.log(`"${segment.characters}" - ${segment.fontName.family} ${segment.fontSize}px`)
}
```

### Inserting and Deleting Characters

```javascript
// Load all fonts (handles mixed fonts via styled segments)
const segments = textNode.getStyledTextSegments(['fontName'])
await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))

// Insert text at a position
textNode.insertCharacters(0, 'Hello ') // Insert at start
textNode.insertCharacters(textNode.characters.length, '!') // Insert at end
textNode.insertCharacters(6, 'beautiful ') // Insert in middle

// Delete characters (start, end)
textNode.deleteCharacters(0, 6) // Delete first 6 characters
textNode.deleteCharacters(5, 10) // Delete characters 5-9

figma.closePlugin()
```

### Splitting Text into Multiple Nodes

To split a text node into separate nodes (one per line/paragraph):

```javascript
const nodeId = '123:456'
const node = await figma.getNodeByIdAsync(nodeId)

if (node && node.type === 'TEXT') {
  // Load all fonts (handles mixed fonts via styled segments)
  const segments = node.getStyledTextSegments(['fontName'])
  await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))

  const lines = node.characters.split(/\r?\n/)
  const parent = node.parent
  const index = parent.children.indexOf(node)

  // Calculate line height for positioning
  const lineHeight =
    typeof node.lineHeight === 'object' && node.lineHeight.unit === 'PIXELS'
      ? node.lineHeight.value
      : node.fontSize * 1.2

  const createdNodes = []
  for (const line of lines) {
    if (!line.trim()) continue

    // Clone preserves ALL properties (lineHeight, letterSpacing, etc.)
    const newNode = node.clone()
    newNode.characters = line.trim()

    // Position vertically using lineHeight (for non-auto-layout parents)
    if (parent.layoutMode === 'NONE' || !parent.layoutMode) {
      newNode.y = node.y + createdNodes.length * lineHeight
    }

    parent.insertChild(index + createdNodes.length, newNode)
    createdNodes.push(newNode)
  }

  node.remove()
  console.log(`Split into ${createdNodes.length} nodes`)
}

figma.closePlugin()
```

**Key points:**

1. Use `clone()` to preserve all text properties (lineHeight, letterSpacing, textCase, etc.)
2. Position using `lineHeight` directly - use PIXELS value if set, otherwise `fontSize * 1.2`
3. For verification exports, export the parent frame - don't use temporary grouping

### Find and Replace Across Page

To search and replace text content across many nodes:

```javascript
;(async () => {
  const searchText = 'Sign Up'
  const replaceText = 'Register'
  const caseSensitive = false

  const textNodes = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })
  console.log(`Searching ${textNodes.length} text nodes for "${searchText}"...`)

  const regex = new RegExp(
    searchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'),
    caseSensitive ? 'g' : 'gi',
  )

  let totalReplacements = 0
  let nodesModified = 0

  for (const node of textNodes) {
    if (!regex.test(node.characters)) continue
    regex.lastIndex = 0

    // Load all fonts used in this node (handles mixed fonts via styled segments)
    const segments = node.getStyledTextSegments(['fontName'])
    await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))

    const matches = node.characters.match(regex)?.length || 0
    console.log(`  ${node.name}: "${node.characters}" → ${matches} match(es)`)

    node.characters = node.characters.replace(regex, replaceText)
    totalReplacements += matches
    nodesModified++
  }

  console.log(`Replaced ${totalReplacements} occurrence(s) across ${nodesModified} node(s)`)
  figma.closePlugin()
})()
```

#### Scoped Find and Replace (Within a Frame)

```javascript
const frame = await figma.getNodeByIdAsync('123:456')
if (frame && 'findAllWithCriteria' in frame) {
  const textNodes = frame.findAllWithCriteria({ types: ['TEXT'] })
  // ... same replacement logic as above
}
```

#### Preserving Styled Ranges

When text has mixed styling (bold + regular), replacing `characters` wholesale resets all styling to the first character's style. To preserve ranges, use `deleteCharacters` + `insertCharacters`:

```javascript
async function replacePreservingStyles(node, search, replace) {
  // Load all fonts (handles mixed fonts via styled segments)
  const segments = node.getStyledTextSegments(['fontName'])
  await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))

  let idx = node.characters.indexOf(search)
  while (idx !== -1) {
    node.deleteCharacters(idx, idx + search.length)
    node.insertCharacters(idx, replace)
    idx = node.characters.indexOf(search, idx + replace.length)
  }
}
```

### OpenType Features

```javascript
// Get current features for a range
const features = textNode.getRangeOpenTypeFeatures(0, 1)

// Inspect node-level OpenType features
const nodeFeatures = textNode.openTypeFeatures
if (nodeFeatures !== figma.mixed) {
  console.log('LIGA:', nodeFeatures.LIGA, 'CALT:', nodeFeatures.CALT)
}
```

---

## Reference — Create Label Nodes

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Creating small circle callout markers with a number or letter.

**Scope:** Label nodes are small fixed-size circle shapes containing a single number or letter, used as callout markers, step indicators, or annotation anchors on a FigJam board. They are created with `figma.createShapeWithText()` using `shapeType = 'ELLIPSE'` and a fixed size. For shapes that need to fit longer text content, see [create-shape-with-text](#reference--create-shapes-with-text).

**When to use labels:** Annotating steps in a process, numbering items on a diagram, marking locations on a map or wireframe, or providing lettered callouts that reference an accompanying legend.

**When NOT to use labels:** If the content is more than 2 characters (e.g. a word or phrase), use a regular [shape-with-text](#reference--create-shapes-with-text) instead.

### Creating a Label

```javascript
// Position the label — determine a location relative to existing content
const labelLocation = { x: 100, y: 100 }

const label = figma.createShapeWithText()
label.shapeType = 'ELLIPSE'

await figma.loadFontAsync(label.text.fontName)
label.text.characters = '1'

// Labels use a fixed size — do NOT use fitShapeToText
label.resize(48, 48)
label.text.fontSize = 20

label.x = labelLocation.x
label.y = labelLocation.y

figma.currentPage.appendChild(label)
return { id: label.id, x: label.x, y: label.y }
```

### Size

Labels use **fixed dimensions** — do not use `fitShapeToText` (that utility is for shapes with variable-length text).

| Content                | Width × Height | Font size |
| ---------------------- | -------------- | --------- |
| Single char (`1`, `A`) | 48 × 48        | 20        |
| Two chars (`10`, `AB`) | 64 × 64        | 20        |

Both width and height must always be equal (square bounding box) so the ellipse renders as a perfect circle.

### Color Presets

Labels use the same coordinated fill/stroke/text color system as other FigJam shapes. Always set all three together. Use `hex/255` notation for exact palette matching — rounded decimals cause FigJam to treat the color as "custom". For the canonical palette across all FigJam node types, see [figjam-colors](#reference--figjam-colors).

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const DARK = h(0x1e, 0x1e, 0x1e)

const LABEL_COLOR_PRESETS = {
  black: { fill: h(0x1e, 0x1e, 0x1e), stroke: h(0xb3, 0xb3, 0xb3), text: WHITE },
  darkGray: { fill: h(0x75, 0x75, 0x75), stroke: h(0x5e, 0x5e, 0x5e), text: WHITE },
  green: { fill: h(0x66, 0xd5, 0x75), stroke: h(0x3e, 0x9b, 0x4b), text: WHITE },
  teal: { fill: h(0x5a, 0xd8, 0xcc), stroke: h(0x36, 0x9e, 0x94), text: WHITE },
  blue: { fill: h(0x3d, 0xad, 0xff), stroke: h(0x00, 0x7a, 0xd2), text: WHITE },
  violet: { fill: h(0x87, 0x4f, 0xff), stroke: h(0x54, 0x27, 0xb4), text: WHITE },
  pink: { fill: h(0xf8, 0x49, 0xc1), stroke: h(0xb4, 0x24, 0x87), text: WHITE },
  red: { fill: h(0xff, 0x75, 0x56), stroke: h(0xdc, 0x30, 0x09), text: WHITE },
  orange: { fill: h(0xff, 0x9e, 0x42), stroke: h(0xeb, 0x75, 0x00), text: WHITE },
  gray: { fill: h(0xb3, 0xb3, 0xb3), stroke: h(0x8f, 0x8f, 0x8f), text: DARK },
  lightGray: { fill: h(0xd9, 0xd9, 0xd9), stroke: h(0xb3, 0xb3, 0xb3), text: DARK },
  yellow: { fill: h(0xff, 0xc9, 0x43), stroke: h(0xe8, 0xa3, 0x02), text: DARK },
  white: { fill: h(0xff, 0xff, 0xff), stroke: h(0xb3, 0xb3, 0xb3), text: DARK },
}

function applyLabelColor(label, preset) {
  label.fills = [{ type: 'SOLID', color: preset.fill }]
  label.strokes = [{ type: 'SOLID', color: preset.stroke }]
  label.text.fills = [{ type: 'SOLID', color: preset.text }]
}
```

#### Applying a color

```javascript
const label = figma.createShapeWithText()
label.shapeType = 'ELLIPSE'
await figma.loadFontAsync(label.text.fontName)
label.text.characters = '1'
label.resize(48, 48)
label.text.fontSize = 20
applyLabelColor(label, LABEL_COLOR_PRESETS.blue)

figma.closePlugin()
```

### Batch Creation: Numbered Sequence

The most common use case is a horizontal row of numbered labels. Use a two-pass layout: create all labels first, then position them using their actual dimensions.

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const PRESET_BLUE = { fill: h(0x3d, 0xad, 0xff), stroke: h(0x00, 0x7a, 0xd2), text: WHITE }

const count = 5
const size = 48
const spacing = 16
const labelLocation = { x: 100, y: 100 }

// Pass 1: create all labels.
// All labels share the same default font — load once before the loop instead
// of awaiting per-iteration.
const probe = figma.createShapeWithText()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
const labels = []
for (let i = 1; i <= count; i++) {
  const label = figma.createShapeWithText()
  label.shapeType = 'ELLIPSE'
  label.text.characters = String(i)
  label.resize(size, size)
  label.text.fontSize = 20
  label.fills = [{ type: 'SOLID', color: PRESET_BLUE.fill }]
  label.strokes = [{ type: 'SOLID', color: PRESET_BLUE.stroke }]
  label.text.fills = [{ type: 'SOLID', color: PRESET_BLUE.text }]
  labels.push(label)
}

// Pass 2: position in a horizontal row
let curX = labelLocation.x
for (const label of labels) {
  label.x = curX
  label.y = labelLocation.y
  curX += size + spacing
}

return labels.map((l) => ({ id: l.id }))
```

### Batch Creation: Lettered Sequence

Same two-pass pattern as the numbered sequence, using `String.fromCharCode` to generate A, B, C…

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const PRESET_VIOLET = { fill: h(0x87, 0x4f, 0xff), stroke: h(0x54, 0x27, 0xb4), text: WHITE }

const letters = ['A', 'B', 'C', 'D', 'E']

const size = 48
const spacing = 16
const labelLocation = { x: 100, y: 100 }

// Pass 1: create all labels.
// All labels share the same default font — load once before the loop instead
// of awaiting per-iteration.
const probe = figma.createShapeWithText()
await figma.loadFontAsync(probe.text.fontName)
probe.remove()
const labels = []
for (const letter of letters) {
  const label = figma.createShapeWithText()
  label.shapeType = 'ELLIPSE'
  label.text.characters = letter
  label.resize(size, size)
  label.text.fontSize = 20
  label.fills = [{ type: 'SOLID', color: PRESET_VIOLET.fill }]
  label.strokes = [{ type: 'SOLID', color: PRESET_VIOLET.stroke }]
  label.text.fills = [{ type: 'SOLID', color: PRESET_VIOLET.text }]
  labels.push(label)
}

// Pass 2: position in a horizontal row
let curX = labelLocation.x
for (const label of labels) {
  label.x = curX
  label.y = labelLocation.y
  curX += size + spacing
}

return labels.map((l) => ({ id: l.id }))
```

### Positioning Relative to an Existing Node

Labels are most often placed adjacent to the node they're annotating. Use the target node's bounds to derive `labelLocation`:

```javascript
// Place a label at the top-right corner of an existing node
const targetNode = figma.getNodeById(targetNodeId)
if (!targetNode) throw new Error('Node not found')

const label = figma.createShapeWithText()
label.shapeType = 'ELLIPSE'
await figma.loadFontAsync(label.text.fontName)
label.text.characters = '1'
label.resize(48, 48)
label.text.fontSize = 20

// Top-left corner, offset so the label overlaps the corner slightly
label.x = targetNode.x - label.width / 2
label.y = targetNode.y - label.height / 2

figma.currentPage.appendChild(label)
return { id: label.id }
```

### Label + Sticky Legend

When annotations need descriptive text (e.g. "1. Introduction", "A. Problem statement"), place label circles on or near the target nodes as markers, then group the corresponding stickies in a cluster nearby — offset 200–300px below (or to the side of) the labeled content. The stickies act as a legend; the labels are the pins. Do NOT place the sticky immediately adjacent to its label circle — if they're glued together there's no need for the circle at all.

```javascript
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const PRESET_BLUE = { fill: h(0x3d, 0xad, 0xff), stroke: h(0x00, 0x7a, 0xd2), text: WHITE }

const annotations = [
  { number: '1', text: 'Introduction' },
  { number: '2', text: 'Problem statement' },
  { number: '3', text: 'Proposed solution' },
]

// targetNodes: the nodes being annotated, one per annotation
// (derive from node IDs passed in the user message)

// Pre-load the label and sticky default fonts in parallel — both fonts are
// the same for every iteration, so awaiting inside the loop would needlessly
// serialize the work.
const labelProbe = figma.createShapeWithText()
const stickyProbe = figma.createSticky()
await Promise.all([
  figma.loadFontAsync(labelProbe.text.fontName),
  figma.loadFontAsync(stickyProbe.text.fontName),
])
labelProbe.remove()
stickyProbe.remove()

// Pass 1: create labels and stickies
const pairs = []
for (const item of annotations) {
  const label = figma.createShapeWithText()
  label.shapeType = 'ELLIPSE'
  label.text.characters = item.number
  label.resize(48, 48)
  label.text.fontSize = 20
  label.fills = [{ type: 'SOLID', color: PRESET_BLUE.fill }]
  label.strokes = [{ type: 'SOLID', color: PRESET_BLUE.stroke }]
  label.text.fills = [{ type: 'SOLID', color: PRESET_BLUE.text }]

  const sticky = figma.createSticky()
  sticky.text.characters = `${item.number}. ${item.text}`

  pairs.push({ label, sticky })
}

// Pass 2: place labels on their target nodes (top-left corner)
for (let i = 0; i < pairs.length; i++) {
  const targetNode = targetNodes[i]
  pairs[i].label.x = targetNode.x - 24
  pairs[i].label.y = targetNode.y - 24
}

// Pass 3: cluster stickies in a vertical column to the right of the labeled content.
// Use the right edge of the target nodes as the anchor, then push further right past
// any existing nodes that overlap vertically with the legend area.
const targetRight = Math.max(...targetNodes.map((n) => n.x + n.width))
const targetTop = Math.min(...targetNodes.map((n) => n.y))
const targetBottom = Math.max(...targetNodes.map((n) => n.y + n.height))

// Find the rightmost edge of any page node that overlaps vertically with the legend area
const legendGap = 250
const conflictRight = figma.currentPage.children
  .filter((n) => n.y < targetBottom + legendGap && n.y + n.height > targetTop)
  .reduce((max, n) => Math.max(max, n.x + n.width), targetRight)

const legendX = conflictRight + legendGap
const stickySpacing = 32
let curY = targetTop
for (const { sticky } of pairs) {
  sticky.x = legendX
  sticky.y = curY
  curY += sticky.height + stickySpacing
}

return pairs.map(({ label, sticky }) => ({ labelId: label.id, stickyId: sticky.id }))
```

### Key Points

- **Always wrap code in an async IIFE:** `(async () => { ... })();`
- **Always call `figma.closePlugin()`** at the end of every code path.
- **Follow the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`)** for `label.text.characters` — always load `label.text.fontName` dynamically; never hardcode the family/style.
- **Use fixed size — do NOT use `fitShapeToText`.** Labels are compact by design; their size is fixed at 48×48 (single char) or 64×64 (two chars).
- **Width must equal height** so the ELLIPSE renders as a perfect circle.
- **Set `fontSize` explicitly** after loading the font to ensure the character is legible in the small circle.
- **Set fill, stroke, AND text color together** — setting only fills leaves mismatched stroke/text colors.
- **Use `shapeType = 'ELLIPSE'`** — the default shapeType is also `'ELLIPSE'`, but set it explicitly for clarity.
- **Use node IDs** from the user message, not `figma.currentPage.selection`.

---

## Reference — Batch Operations Pattern

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Patterns for modifying many existing nodes at once.

**Typical workflow:**

1. Find nodes using traversal APIs (`findAll`, `findAllWithCriteria`)
2. Apply modifications using the patterns below

### Performance Tips

#### 1. Use findAllWithCriteria for Type-Based Searches

`findAllWithCriteria` is significantly faster than `findAll` when filtering by node type only.

```javascript
// ✅ FAST - Use findAllWithCriteria for type filtering
const textNodes = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })
const shapes = figma.currentPage.findAllWithCriteria({
  types: ['RECTANGLE', 'ELLIPSE', 'POLYGON', 'STAR'],
})

// ❌ SLOWER - findAll with type check
const textNodesSlow = figma.currentPage.findAll((n) => n.type === 'TEXT')

figma.closePlugin()
```

#### 2. Limit Search Scope

Search within a specific node rather than the entire page.

```javascript
// ✅ FAST - Search within specific frame, using indexed type lookup
const frame = await figma.getNodeByIdAsync('123:456')
if (frame && 'findAllWithCriteria' in frame) {
  const textInFrame = frame.findAllWithCriteria({ types: ['TEXT'] })
}

// ❌ SLOWER - Whole-page predicate scan
const allText = figma.currentPage.findAll((n) => n.type === 'TEXT')

figma.closePlugin()
```

### Batch Modify Pattern

#### Basic Batch Modification

```javascript
const page = figma.currentPage

// Find all buttons
const buttons = page.findAll((n) => n.name.toLowerCase().includes('button'))
console.log(`Found ${buttons.length} buttons`)

// Modify each one
let modified = 0
for (const btn of buttons) {
  if ('fills' in btn) {
    btn.fills = [{ type: 'SOLID', color: { r: 0, g: 0.5, b: 1 } }]
    modified++
  }
}

console.log(`Modified ${modified} buttons`)
figma.closePlugin()
```

#### With Progress Logging

For long operations, log progress so you can track what's happening.

```javascript
const nodes = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })
console.log(`Processing ${nodes.length} text nodes...`)

let processed = 0
for (const node of nodes) {
  // Load all fonts (handles mixed fonts via styled segments)
  const segments = node.getStyledTextSegments(['fontName'])
  await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))
  node.fontSize = 16

  processed++
  if (processed % 50 === 0) {
    console.log(`Processed ${processed}/${nodes.length}`)
  }
}

console.log(`Done! Processed ${processed} nodes`)
figma.closePlugin()
```

### Chunked Processing

For very large operations, process in chunks to avoid timeouts.

```javascript
async function processInChunks(nodes, chunkSize, processFn) {
  const results = []

  for (let i = 0; i < nodes.length; i += chunkSize) {
    const chunk = nodes.slice(i, i + chunkSize)
    console.log(
      `Processing chunk ${Math.floor(i / chunkSize) + 1}/${Math.ceil(nodes.length / chunkSize)}`,
    )

    for (const node of chunk) {
      const result = await processFn(node)
      results.push(result)
    }
  }

  return results
}

// Usage
const allText = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })

await processInChunks(allText, 100, async (node) => {
  // Load all fonts (handles mixed fonts via styled segments)
  const segments = node.getStyledTextSegments(['fontName'])
  await Promise.all(segments.map((s) => figma.loadFontAsync(s.fontName)))
  node.textCase = 'UPPER'
  return node.id
})

figma.closePlugin()
```

### Collecting Results

#### Build Summary Object

```javascript
const textNodes = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })

// Collect statistics
const fontUsage = {}
for (const node of textNodes) {
  if (node.fontName && node.fontName.family) {
    const key = `${node.fontName.family} ${node.fontName.style}`
    fontUsage[key] = (fontUsage[key] || 0) + 1
  }
}

console.log('Font usage:')
for (const [font, count] of Object.entries(fontUsage).sort((a, b) => b[1] - a[1])) {
  console.log(`  ${font}: ${count}`)
}

figma.closePlugin()
```

#### Group by Property

```javascript
const nodes = figma.currentPage.findAll((n) => 'fills' in n)

// Group by fill color
const byColor = {}
for (const node of nodes) {
  if (Array.isArray(node.fills) && node.fills.length > 0) {
    const fill = node.fills[0]
    if (fill.type === 'SOLID') {
      const key = `rgb(${Math.round(fill.color.r * 255)}, ${Math.round(fill.color.g * 255)}, ${Math.round(fill.color.b * 255)})`
      if (!byColor[key]) byColor[key] = []
      byColor[key].push(node.name)
    }
  }
}

console.log('Nodes by color:', JSON.stringify(byColor, null, 2))
figma.closePlugin()
```

### Safe Batch Updates

#### Check Before Modify

```javascript
const nodes = figma.currentPage.findAll((n) => n.name.includes('Button'))

for (const node of nodes) {
  // Log before state
  console.log(`${node.name} before:`, 'fills' in node ? JSON.stringify(node.fills) : 'no fills')

  // Check if modification is possible
  if (!('fills' in node)) {
    console.log(`  Skipping ${node.name} - no fills property`)
    continue
  }

  // Modify
  node.fills = [{ type: 'SOLID', color: { r: 0, g: 0.5, b: 1 } }]

  // Log after state
  console.log(`${node.name} after:`, JSON.stringify(node.fills))
}

figma.closePlugin()
```

### Common Patterns: Renaming Layers

#### Bulk Find-and-Replace in Names

```javascript
const nodes = figma.currentPage.findAll((n) => n.name.includes('Button'))
console.log(`Found ${nodes.length} nodes to rename`)

for (const node of nodes) {
  const oldName = node.name
  node.name = node.name.replace('Button', 'Btn')
  console.log(`  "${oldName}" → "${node.name}"`)
}

figma.closePlugin()
```

#### Auto-Numbering Children

```javascript
const frame = await figma.getNodeByIdAsync('123:456')

if ('children' in frame) {
  for (let i = 0; i < frame.children.length; i++) {
    frame.children[i].name = `Item ${i + 1}`
  }
  console.log(`Numbered ${frame.children.length} children`)
}

figma.closePlugin()
```

#### Content-Based Naming (Name from Text Content)

```javascript
const frames = figma.currentPage.findAllWithCriteria({ types: ['FRAME'] })

let renamed = 0
for (const frame of frames) {
  // Use the type-indexed criteria for type-based searches; take the first match.
  const heading = frame.findAllWithCriteria({ types: ['TEXT'] })[0]
  if (heading) {
    frame.name = heading.characters.slice(0, 40)
    renamed++
  }
}

console.log(`Renamed ${renamed} frames from heading text`)
figma.closePlugin()
```

#### Strip Auto-Generated Names

```javascript
const autoNamePattern = /^(Frame|Rectangle|Ellipse|Group|Vector|Line|Polygon|Star)\s+\d+$/
const nodes = figma.currentPage.findAll((n) => autoNamePattern.test(n.name))
console.log(`Found ${nodes.length} auto-named nodes`)

for (const node of nodes) {
  node.name = node.type.toLowerCase()
}

figma.closePlugin()
```

#### Add Prefix with `/` Separator (Layer Panel Grouping)

Figma groups layers in the panel by `/` in names (e.g., `icons/arrow`, `icons/check`).

```javascript
// Use the type-indexed criteria for the type filter, then narrow by name.
const icons = figma.currentPage
  .findAllWithCriteria({ types: ['INSTANCE'] })
  .filter((n) => n.name.toLowerCase().includes('icon'))

for (const icon of icons) {
  if (!icon.name.startsWith('icons/')) {
    icon.name = `icons/${icon.name}`
  }
}

console.log(`Prefixed ${icons.length} icon layers`)
figma.closePlugin()
```

---

## Reference — FigJam Colors

> Part of the [figma-use-figjam skill](#use_figma--figma-plugin-api-skill-for-figjam). Canonical color palettes for FigJam node types — stickies, sections, connectors, shapes-with-text, and labels.

This is the shared color reference for every FigJam node type. Each node type has its own palette (FigJam doesn't share one universal palette across all node types), so use the table for the node type you're working with. The hex/255 conversion helper at the top is shared across all of them.

The hex values below mirror FigJam's built-in UI3 palette. The renderer's behavior is what defines whether a color is recognized as a "palette color" in the FigJam UI, so this doc is downstream of the product. If a value drifts from what FigJam renders, the doc is wrong, not the product.

The per-node-type reference files (`create-sticky.md`, `create-section.md`, `create-connector.md`, `create-shape-with-text.md`, `create-label.md`) intentionally keep their own inline palette tables so each file is self-sufficient for single-file loads. This file is the canonical place those tables converge — when a color value changes, update this file and the relevant per-node-type files together.

### Contents

- [Universal rules](#universal-rules) — `hex/255` notation, the `h()` helper, why this matters
- [Sticky palette](#sticky-palette) — `figma.createSticky()` fills
- [Section background palette](#section-background-palette) — `figma.createSection()` fills
- [Connector stroke palette](#connector-stroke-palette) — `figma.createConnector()` strokes
- [Shape coordinated palette](#shape-coordinated-palette) — `figma.createShapeWithText()` fill + stroke + text together
- [Label coordinated palette](#label-coordinated-palette) — small numbered/lettered ellipse markers
- [Plan-board accent colors](#plan-board-accent-colors) — semantic accents for badges, status dots, and emphasis markers (not section fills)
- [Default text color](#default-text-color) — Charcoal `#1E1E1E`

### Universal rules

#### Use `hex/255` notation, not pre-computed decimals

FigJam recognizes a color as a "palette color" only when its RGB channels match a palette entry exactly. Pre-rounded decimals like `{ r: 0.65, g: 0.85, b: 1 }` drift just enough that FigJam treats the color as **custom** instead of **palette**, which (a) breaks color-by-name lookups, (b) prevents users from clicking the palette swatch to change it, and (c) makes diagrams look subtly "off".

**Always** write color values as `hex/255`:

```js
// CORRECT — exact palette match
sticky.fills = [{ type: 'SOLID', color: { r: 0xa8/255, g: 0xda/255, b: 0xff/255 } }]  // Blue #A8DAFF

// WRONG — pre-rounded, FigJam will mark this "custom"
sticky.fills = [{ type: 'SOLID', color: { r: 0.66, g: 0.85, b: 1.0 } }]
```

#### The `h()` helper

Almost every script that touches FigJam colors uses this one-liner. Copy-paste it into the top of your script:

```js
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

// Now write colors clean:
sticky.fills = [{ type: 'SOLID', color: h(0xa8, 0xda, 0xff) }]  // Blue #A8DAFF
```

#### Don't invent custom colors

Strongly prefer the palette colors below over arbitrary hex values. If the user explicitly asks for a brand color, use it; otherwise, sticking to FigJam's built-in palette keeps boards visually coherent and lets users re-color via the FigJam UI.

---

### Sticky palette

Used for `figma.createSticky()` fills — see [create-sticky](#reference--create-sticky-notes).

| Color  | Hex       |
| ------ | --------- |
| White  | `#FFFFFF` |
| Gray   | `#E6E6E6` |
| Green  | `#B3EFBD` |
| Teal   | `#B3F4EF` |
| Blue   | `#A8DAFF` |
| Violet | `#D3BDFF` |
| Pink   | `#FFA8DB` |
| Red    | `#FFB8A8` |
| Orange | `#FFD3A8` |
| Yellow | `#FFE299` |

Sticky semantics commonly used: blue=discussion, yellow=question, green=positive, pink=concern, red=blocker, teal=decision, violet=ideation.

### Section background palette

Used for `figma.createSection()` fills — see [create-section](#reference--create-sections). Sections typically use lighter tints than stickies. When creating multiple sections, vary the colors so the user can visually distinguish them.

| Color        | Hex       |
| ------------ | --------- |
| White        | `#FFFFFF` |
| Light gray   | `#F9F9F9` |
| Light green  | `#EBFFEE` |
| Light teal   | `#F1FEFD` |
| Light blue   | `#F5FBFF` |
| Light violet | `#F8F5FF` |
| Light pink   | `#FFF0FA` |
| Light red    | `#FFF5F5` |
| Light orange | `#FFF7F0` |
| Light yellow | `#FFFBF0` |

### Connector stroke palette

Used for `figma.createConnector()` `strokes` — see [create-connector](#reference--create-connectors). Connector text labels have their own background and color independently of the line.

| Color      | Hex       |
| ---------- | --------- |
| Black      | `#1E1E1E` |
| Dark gray  | `#757575` |
| Gray       | `#B3B3B3` |
| Light gray | `#D9D9D9` |
| Green      | `#66D575` |
| Teal       | `#5AD8CC` |
| Blue       | `#3DADFF` |
| Violet     | `#874FFF` |
| Pink       | `#F849C1` |
| Red        | `#FF7556` |
| Orange     | `#FF9E42` |
| Yellow     | `#FFC943` |
| White      | `#FFFFFF` |

### Shape coordinated palette

Used for `figma.createShapeWithText()` — see [create-shape-with-text](#reference--create-shapes-with-text) and [create-label](#reference--create-label-nodes). FigJam shapes coordinate three colors together: **fill**, **stroke**, and **text**. Setting only one will produce an off-palette shape (e.g., dark text on a dark fill, or unmatched stroke).

```js
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const DARK = h(0x1e, 0x1e, 0x1e)

const SHAPE_PRESETS = {
  // White-text presets (saturated fills)
  black:    { fill: h(0x1e, 0x1e, 0x1e), stroke: h(0xb3, 0xb3, 0xb3), text: WHITE },
  darkGray: { fill: h(0x75, 0x75, 0x75), stroke: h(0x5e, 0x5e, 0x5e), text: WHITE },
  green:    { fill: h(0x66, 0xd5, 0x75), stroke: h(0x3e, 0x9b, 0x4b), text: WHITE },
  teal:     { fill: h(0x5a, 0xd8, 0xcc), stroke: h(0x36, 0x9e, 0x94), text: WHITE },
  blue:     { fill: h(0x3d, 0xad, 0xff), stroke: h(0x00, 0x7a, 0xd2), text: WHITE },
  violet:   { fill: h(0x87, 0x4f, 0xff), stroke: h(0x54, 0x27, 0xb4), text: WHITE },
  pink:     { fill: h(0xf8, 0x49, 0xc1), stroke: h(0xb4, 0x24, 0x87), text: WHITE },
  red:      { fill: h(0xff, 0x75, 0x56), stroke: h(0xdc, 0x30, 0x09), text: WHITE },
  orange:   { fill: h(0xff, 0x9e, 0x42), stroke: h(0xeb, 0x75, 0x00), text: WHITE },

  // Dark-text presets (lighter fills)
  gray:      { fill: h(0xb3, 0xb3, 0xb3), stroke: h(0x8f, 0x8f, 0x8f), text: DARK },
  lightGray: { fill: h(0xd9, 0xd9, 0xd9), stroke: h(0xb3, 0xb3, 0xb3), text: DARK },
  yellow:    { fill: h(0xff, 0xc9, 0x43), stroke: h(0xe8, 0xa3, 0x02), text: DARK },
  white:     { fill: h(0xff, 0xff, 0xff), stroke: h(0xb3, 0xb3, 0xb3), text: DARK },
}

function applyShapeColor(shape, preset) {
  shape.fills = [{ type: 'SOLID', color: preset.fill }]
  shape.strokes = [{ type: 'SOLID', color: preset.stroke }]
  shape.text.fills = [{ type: 'SOLID', color: preset.text }]
}
```

### Label coordinated palette

Labels (small numbered/lettered circle callouts created with `figma.createShapeWithText({shapeType:'ELLIPSE'})`) use the same coordinated fill/stroke/text system as shapes — see [create-label](#reference--create-label-nodes). The `SHAPE_PRESETS` map above works for labels too.

If you want to inline only the most-common label preset (blue numbered circles for annotation legends):

```js
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })
const WHITE = h(0xff, 0xff, 0xff)
const PRESET_BLUE = { fill: h(0x3d, 0xad, 0xff), stroke: h(0x00, 0x7a, 0xd2), text: WHITE }
```

### Plan-board accent colors

Board-content layouts (templates, retros, brainstorms — see [plan-board-content](#reference--plan-content-for-figjam-boards)) use a small set of saturated accent colors for badges, status dots, and emphasis markers. These are designer-chosen, **not** FigJam palette swatches — applying them won't show as palette colors in the FigJam UI, and that's intentional (they're for in-content accents, not for fills the user will recolor).

For section backgrounds, use the [Section background palette](#section-background-palette) above. For badge/dot accents:

```js
const h = (r, g, b) => ({ r: r / 255, g: g / 255, b: b / 255 })

const black     = h(0x12, 0x12, 0x12)
const gray      = h(0x59, 0x59, 0x59)
const red       = h(0xbf, 0x2e, 0x2e)
const orange    = h(0xb8, 0x61, 0x14)
const green     = h(0x1f, 0x80, 0x4d)
const blue      = h(0x38, 0x66, 0xbf)
const purple    = h(0x73, 0x4d, 0xa6)
const attention = h(0xd9, 0xa6, 0x1a) // gold
```

Use these for badges, status indicators, and other small accent marks — not for section backgrounds, sticky fills, or shape fills (those have their own coordinated palettes above).

### Default text color

For text nodes, sticky text, shape text, and any FigJam content where the user hasn't specified a text color, default to **Charcoal `#1E1E1E`** — see [edit-text](#reference--text-operations).

```js
textNode.fills = [{ type: 'SOLID', color: { r: 0x1e/255, g: 0x1e/255, b: 0x1e/255 } }]
```

Avoid mid-grays (`#757575`, `#B3B3B3`, `#D9D9D9`) for body text — they read as unfinished or low-contrast on FigJam's near-white canvas.
