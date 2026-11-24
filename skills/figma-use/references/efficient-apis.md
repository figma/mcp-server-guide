# Efficient `use_figma` APIs Reference

These APIs reduce boilerplate, eliminate ordering errors, and compress token output. Always prefer them over verbose alternatives.

## `node.query(selector)` — CSS-like Node Search

Find nodes within a subtree using CSS-like selectors. Replaces verbose `findAll` + filter loops.

```js
// BEFORE — verbose traversal
const texts = frame.findAll(n => n.type === 'TEXT' && n.name === 'Title')

// AFTER — one-liner with query
const texts = frame.query('TEXT[name=Title]')
```

**Selector syntax:**
- Type: `FRAME`, `TEXT`, `RECTANGLE`, `ELLIPSE`, `COMPONENT`, `INSTANCE`, `SECTION` (case-insensitive)
- Attribute exact: `[name=Card]`, `[visible=true]`, `[opacity=0.5]`
- Attribute substring: `[name*=art]` (contains), `[name^=Header]` (starts-with), `[name$=Nav]` (ends-with)
- Dot-path traversal: `[fills.0.type=SOLID]`, `[fills.*.type=SOLID]` (wildcard index)
- Instance matching: `[mainComponent=nodeId]`, `[mainComponent.name=Button]`
- Combinators: `FRAME > TEXT` (direct child), `FRAME TEXT` (any descendant), `A + B` (adjacent sibling), `A ~ B` (general sibling)
- Pseudo-classes: `:first-child`, `:last-child`, `:nth-child(2)`, `:not(TYPE)`, `:is(FRAME, RECTANGLE)`, `:where(TEXT, ELLIPSE)`
- Node ID: `#nodeId` or bare GUID
- Comma: `TEXT, RECTANGLE` (union)
- Wildcard: `*` (any type)

**QueryResult methods:**
| Method | Description |
|---|---|
| `.length` | Number of matched nodes |
| `.first()` | First matched node (or `null`) |
| `.last()` | Last matched node (or `null`) |
| `.toArray()` | Convert to regular array |
| `.each(fn)` | Iterate with callback, returns `this` for chaining |
| `.map(fn)` | Map to new array |
| `.filter(fn)` | Filter to new QueryResult |
| `.values(keys)` | Extract property values: `.values(['name', 'x', 'y'])` → `[{name, x, y}, ...]` |
| `.set(props)` | Set properties on all matched nodes (see `node.set()` below) |
| `.query(selector)` | Sub-query within matched nodes |
| `for...of` | Iterable — works in `for` loops |

**Scope:** `node.query()` searches within that node's subtree. To search the whole page: `figma.currentPage.query('...')`. There is no global `figma.query()`.

**Examples:**
```js
// Recolor all text inside cards
figma.currentPage.query('FRAME[name^=Card] TEXT').set({
  fills: [{type: 'SOLID', color: {r: 0.2, g: 0.2, b: 0.8}}]
})

// Get names and positions of all frames
return figma.currentPage.query('FRAME').values(['name', 'x', 'y'])

// Find the first component named "Button"
const btn = figma.currentPage.query('COMPONENT[name=Button]').first()

// Find all instances of a specific component
figma.currentPage.query(`INSTANCE[mainComponent=${compId}]`)

// Find nodes with solid fills using dot-path traversal
figma.currentPage.query('[fills.0.type=SOLID]')
```

## `node.set(props)` — Batch Property Updates

Set multiple properties in one call. Returns `this` for chaining.

```js
// BEFORE — one line per property
frame.opacity = 0.5
frame.cornerRadius = 8
frame.name = "Card"

// AFTER — single call
frame.set({ opacity: 0.5, cornerRadius: 8, name: "Card" })
```

**Priority key ordering:** `layoutMode` is always applied before other properties (like `width`/`height`) regardless of object key order. This prevents the common bug where `resize()` behaves differently depending on whether `layoutMode` is set.

**Width/height handling:** `width` and `height` are routed through `node.resize()` automatically — setting `{ width: 200 }` calls `resize(200, currentHeight)`.

**Chaining with query:**
```js
// Find all rectangles named "Divider" and update them
figma.currentPage.query('RECTANGLE[name=Divider]').set({
  fills: [{type: 'SOLID', color: {r: 0.9, g: 0.9, b: 0.9}}],
  cornerRadius: 2
})
```

## `figma.createAutoLayout(direction?, props?)` — Auto-Layout Frames

Creates a frame with auto-layout already enabled and both axes hugging content. This is the default container whenever children have a structural relationship to each other (see Rule 12a).

```js
// BEFORE — manual setup, easy to get ordering wrong
const frame = figma.createFrame()
frame.layoutMode = 'VERTICAL'
frame.primaryAxisSizingMode = 'AUTO'
frame.counterAxisSizingMode = 'AUTO'
frame.layoutSizingHorizontal = 'HUG'
frame.layoutSizingVertical = 'HUG'

// AFTER — one call, layout ready
const frame = figma.createAutoLayout('VERTICAL')
```

Children can immediately use `layoutSizingHorizontal/Vertical = 'FILL'` after being appended — no need to set sizing modes manually.

Accepts an optional props object as the first or second argument:
```js
figma.createAutoLayout({ name: 'Card', itemSpacing: 12 })               // HORIZONTAL + props
figma.createAutoLayout('VERTICAL', { name: 'Column', itemSpacing: 8 })  // VERTICAL + props
```

## `node.placeholder` — Shimmer Overlay for AI-in-Progress Feedback

Sets a visual shimmer overlay on a node indicating work is in progress. **Always remove the shimmer when done** — leftover shimmers confuse users and indicate incomplete work.

```js
// Mark as in-progress
frame.placeholder = true

// ... build out the content ...

// MUST remove when done — never leave shimmers on finished nodes
frame.placeholder = false
```

When building complex layouts, set `placeholder = true` on sections before populating them, then set `placeholder = false` on each section as it's completed.

## `await node.screenshot(opts?)` — Inline Screenshots

Capture a node as a PNG and return it inline in the response. Eliminates the need for a separate `get_screenshot` call.

```js
// Take a screenshot of a frame (returned inline in the tool response)
await frame.screenshot()

// Custom scale (default auto-scales: 0.5x or capped so max dimension ≤ 1024px)
await frame.screenshot({ scale: 2 })

// Include overlapping content from sibling nodes
await frame.screenshot({ contentsOnly: false })
```

**When to use:** Follow Rule 5. Take a composition screenshot when visual evidence is needed. If a visual fix follows, take one post-fix screenshot; that passing screenshot is final. Do not take an additional unchanged “final” screenshot.

**Auto-naming:** The image caption includes node metadata — `"Card (300x150 at 0,60).png"` — giving spatial context without parsing the image.

**Default scaling:** Uses 0.5x scale, but automatically caps so the largest output dimension never exceeds 1024px. Explicit `{ scale: N }` bypasses the cap.
