# use_figma — Figma Plugin API Skill

Execute JavaScript in Figma files via the Plugin API. **Always pass `skillNames: "figma-use"` when calling `use_figma`** (logging parameter, doesn't affect execution).

**If the task involves building or updating a full page, screen, or multi-section layout in Figma from code**, also load [figma-generate-design](figma-generate-design.md). It provides the workflow for discovering design system components via `search_design_system`, importing them, and assembling screens incrementally. Both skills work together: this one for the API rules, that one for the screen-building workflow.

## $fig — the plan-based builder API (ALL NODE CREATION MUST USE THIS)

`$fig` is a global that is responsible for all node creation. It auto-flushes at script end (no `$fig.done()` needed), handles font preloading, batches mutations, and orders property assignment correctly. **Use it for all node creation and mutation operations.** Never use `figma.createFrame()`, `figma.createText()` or any `figma.create*` methods. They do not exist in this environment.

### Copy these patterns

**Build an auto-layout frame with children — single call:**
```js
$fig.autoLayout(
  // fixed width; omit height to hug vertically
  { name: 'Todo List', layoutMode: 'VERTICAL', width: 480 },
  ['item 1', 'item 2', 'item 3'].map((item) =>
    $fig.autoLayout(
      // Set `layoutSizingHorizontal` to FILL since auto-layout is hug x hug by default
      { name: 'Todo Item', layoutSizingHorizontal: 'FILL' },
      [$fig.text({ characters: item, fontName: { family: 'Inter', style: 'Bold' } })],
    ),
  ),
).screenshot() // Screenshot new node trees to verify. Prefer `.screenshot()` over `get_screenshot` call after `use_figma`.
```

**N parallel items for repeated small UI elements like swatches, list items, etc.:**
```js
const ITEMS = [
  { name: 'A', bg: hex('#ffffff'), accent: hex('#0969da') },
  { name: 'B', bg: hex('#fff8f1'), accent: hex('#bf5af2') },
  // ...add more here
]
ITEMS.forEach((v, i) => $fig.autoLayout({ name: v.name, x: i * 410, width: 390, fills: [{ type:'SOLID', color: v.bg }] }, [
  $fig.text({ characters: v.name, fills: [{ type:'SOLID', color: v.accent }] }),
]))
```

**Update existing nodes — by query or by id:**
```js
$fig.query('FRAME[name=Header] TEXT[name=Title]').set({ characters: 'New Title', fontSize: 24 })
$fig.get('1:42').set({ opacity: 0.8, cornerRadius: 12 })
```

**Add a node inside an existing node**
```js
$fig.get('1:42').append($fig.autoLayout({ name: 'New Frame' }))
```

**Create a component with a few different variants**
```js
const SIZES = ['Small', 'Medium', 'Large']
$fig.variants({ name: 'Button' }, SIZES.map((size) => $fig.component({ name: `Size=${size}`, layoutMode: 'HORIZONTAL', /** other props */ })))
```
> ⚠️ `$fig.variants` does **not** position the variants — they stack at (0,0) and the set renders as one collapsed, overlapping element. You must grid the variants and resize the set afterward. See [`fig-builder.md`](figma-use/references/fig-builder.md#required-follow-up--grid-the-variants-fig-build--raw-layout) for the required follow-up recipe.

**Create an instance of a component**
```js
// First arg can be a node ID ('1:2') OR a library asset key
// from `search_design_system` results (the `componentKey` field).
$fig.instance('1:2', { name: 'Cancel Btn', props: { label: 'Cancel'}})
```

**Consume styles/variables**
```js
$fig.autoLayout({ name: 'Card', itemSpacing: spacingVar, fills: fillStyle })

// Looked up by asset key from `search_design_system` (the `key` field)
$fig.autoLayout({ fills: $fig.getStyle(BG_STYLE_KEY) })
$fig.rectangle({ fills: [{ type: 'SOLID', color: $fig.getVar(BRAND_VAR_KEY) }] })
```

**Use design-system assets by key (from `search_design_system`)**

`search_design_system` returns `componentKey` for components and component sets, and `key` for styles and variables. Pass these straight into the unified `$fig` lookup — the plan queues the library import automatically, so you don't need a separate `await figma.importComponentByKeyAsync(...)` / `importStyleByKeyAsync(...)` / `importVariableByKeyAsync(...)` step.
```js
// One call site, many input shapes — node IDs, real variable/style ids,
// AND 40-char asset keys (e.g. '49c8754d4b898e176148650df612a47998a8c4a1')
const btn        = $fig.get(BUTTON_KEY)                    // component / component set
const instance   = $fig.instance(BUTTON_SET_KEY, {         // create an instance from a set
  props: { Size: 'md', Variant: 'primary' },
})
const heading    = $fig.getStyle(HEADING_TEXT_STYLE_KEY)   // paint / text / effect / grid style
const brand      = $fig.getVar(BRAND_COLOR_VAR_KEY)        // variable

$fig.text({ characters: 'Hello', textStyle: heading })
$fig.rectangle({ fills: [{ type: 'SOLID', color: brand }] })
```

**Discover a set's variant props from its key** — `search_design_system` returns a set's `componentKey`, not its variant properties. This is **two `use_figma` calls**: call 1 `return`s the variants so their props come back to you in the tool result; then, knowing the valid props, call 2 instantiates the variant you want.
```js
// Call 1 — discover: return the projection so its values land in the tool result
return $fig.get(BUTTON_SET_KEY).query('COMPONENT')
  .values(['name', 'variantProperties', 'parent.componentPropertyDefinitions'])
```
```js
// Call 2 — instantiate with props you picked from call 1's output
$fig.instance(BUTTON_SET_KEY, { props: { Size: 'Large', Kind: 'Secondary' } })
```

**Bulk component swap — `$fig.query().set()`:**
```js
const chevron = $fig.get('CHEVRON_KEY')
$fig.query('INSTANCE[name=arrow_drop_down]').set({ mainComponent: chevron })
```

**`.query()` and `.values()` for search and projecting child values**
```js
const menuArrows = $fig
  .query('PAGE[name=Menu] INSTANCE[mainComponent.name*=arrow], PAGE[name=Menu] INSTANCE[mainComponent.name*=chevron]')
  .values(['id', 'name', 'mainComponent.name', 'mainComponent.id']);

// Use quotes for multi-word selector values
const expandComponents = $fig
  .query('COMPONENT[name*=expand], COMPONENT[name*=chevron_down], COMPONENT[name*=chevron_up], COMPONENT[name*="multi word name"]')
  .values(['id', 'name']);
```

**Perform operations on another page:**
```js
// Switch to a specific page (loads its content)
const targetPage = figma.root.children.find((p) => p.name === "My Page");
await figma.setCurrentPageAsync(targetPage);
$fig.query('INSTANCE[name=arrow_drop_down]').set({ ... })
```

**Gradient via helper — no manual transform matrix needed:**
```js
$fig.gradient(node, 'LINEAR', [
  { position: 0, color: { r: 0, g: 0, b: 0 } },
  { position: 1, color: { r: 1, g: 1, b: 1 } },
])
```

**Hex helper at script top:**
```js
const hex = h => { const n = parseInt(h.replace('#',''), 16); return { r:((n>>16)&255)/255, g:((n>>8)&255)/255, b:(n&255)/255 } }
// then: color: hex('#2563eb')
```

**Chaining on plan nodes — alternative to children array:**
```js
const card = $fig.autoLayout({ name: 'Card', layoutMode: 'VERTICAL' })
card.text({ characters: 'Title', fontSize: 20 })
card.text({ characters: 'Description', fontSize: 14 })
```

### `$fig` create + mutate API (full surface)

- **Create:** `$fig.autoLayout / .frame / .text / .rectangle / .ellipse / .polygon / .star / .line / .vector / .section / .component / .page` — all `(opts?, children?)`. Plan nodes are chainable.
- **Create from SVG — the preferred ICON path:** `$fig.svg(svgStr, opts?)` builds a vector node tree from an SVG string. **Prefer real vector icons:** import the icon's SVG source (inline `<svg>`, the `.svg` asset, or the source icon-library glyph — e.g. lucide/heroicons) via `$fig.svg(...)` rather than approximating an icon with a typed emoji/Unicode glyph (★ ⚙ 🔍 ☰ ▾) or a plain rectangle. A simple glyph or shape is a fine fallback when the real SVG genuinely can't be obtained — just reach for the SVG first. (Don't reconstruct an icon from rotated line/rect primitives, though — that renders broken.) Full recipe (viewBox+width/height sizing, `currentColor`, INSTANCE_SWAP for design-system icons): [figma-generate-design → Icons](figma-generate-design.md#icons-import-the-svg-never-reconstruct-from-rotated-primitives).
- **Create an instance of a component:** `$fig.instance(compRef, opts?)` — `compRef` is a component plan node, a node ID string, OR a library asset key (`componentKey` from `search_design_system`); the import is queued in the plan automatically.
- **Grouping/boolean:** `$fig.group / .union / .subtract / .intersect / .exclude / .variants` — all `(opts?, children?)`.
- **Read:** `$fig.get(id)` wraps an existing `SceneNode` — `id` can be a real node ID OR a library asset key (`componentKey` from `search_design_system`); the import is queued in the plan automatically. `$fig.query(selector, scope?)` returns `{ length, values(paths), first(), last(), each(fn), filter(fn), set(props), moveTo(parent, idx?), remove() }`. Selectors are CSS-like (e.g. `'FRAME[name*=Card] TEXT'`). `$fig.getStyle(nameOrIdOrKey)` and `$fig.getVar(nameOrIdOrKey)` accept the matching `key` values from `search_design_system`.
- **Mutate:** `$fig.set(target, props)`, `.delete(...nodes)`, `.move(target, parent, idx?)`, `.clone(target, props?)`, `.append(parent, child)`, `.addAt(parent, idx, child)`, `.replace(old, new)`, `.reorder(parent, children)`, `.setPage(name)`, `.gradient(node, type, stops, transform?)`, `.image(node, hash, scaleMode?)`.
- **Plan-node methods (chainable):** `.set()`, `.remove()`, `.clone()`, `.moveTo(parent, idx?)`, `.append(child)`, `.query(selector)`, `.screenshot({scale?, contentsOnly?})`, and the `.node` getter for the materialized `SceneNode` (null pre-flush).

### When to use the raw Figma Plugin API

Only these cases — and even then, mix raw API with `$fig` in the same script:

- **Mid-script async result needed:** `await figma.setCurrentPageAsync(...)`, `await figma.loadFontAsync(...)` — must complete before subsequent plan steps can use the result. (Importing library components is NOT one of these cases: pass the `componentKey` straight into `$fig.get(...)` / `$fig.instance(...)` and pass variant property values in `props`. `$fig` queues the library import in the plan and resolves the variant for you.)
- **Mid-script real node state read:** measured `width` / `height` after auto-layout, computed colors, getStyledTextSegments — materialize mid-script, then read `.node` on the plan node. See [references/fig-builder.md](figma-use/references/fig-builder.md) for the mid-script inspection pattern.
- **Things `$fig` genuinely doesn't expose:** `node.setRangeFontName(...)`, etc. — access via `planNode.node` (see [references/fig-builder.md](figma-use/references/fig-builder.md)).

## Critical Rules

1. **Only use `$fig` for creating / bulk-editing nodes** (`$fig.autoLayout(...)`, `$fig.text(...)`, `$fig.query(...).set(...)`). Raw Plugin API is the fallback — use it only when `$fig` can't express the operation (intermediate node-state reads, non-SceneNode types like Variables). Library components are NOT a reason to leave `$fig`: `$fig.get(componentKey)` / `$fig.instance(componentSetKey, { props })` queue the library import and resolve the variant for you. See [references/fig-builder.md](figma-use/references/fig-builder.md) and [references/critical-rules-deep.md](figma-use/references/critical-rules-deep.md) for worked WRONG/RIGHT examples.

2. **Do not use `findOne`, `findAll`, `findAllWithCriteria`, `findChildren`, `findChild` directly for node searching** They are more verbose, error-prone, and less efficient than `query()`.  Additionally, do not use recursion to search.

3. **Avoid `return` / `$fig.done()` if only using `$fig`** — runtime auto-flushes and returns a `FigDoneResult` with created/updated node IDs. Use `return` if you need raw plugin API mid-script or other data.

4. **Build up larger designs incrementally by section.** Refer to the [figma-generate-design](figma-generate-design.md) skill for the placeholder + replace workflow. Create screens with placeholders inside, e.g. `$fig.autoLayout({ name: 'Header', layoutSizingHorizontal: 'FILL', placeholder: true })`, then make subsequent `use_figma` calls to replace them and screenshot: `$fig.get("PLACEHOLDER_ID_FROM_PREVIOUS_STEP").replace( ... ).screenshot()`. You can make up to 5 `.screenshot()` calls per tool call. If you need to make more screenshots, you are doing too much work and need to break down the task into multiple `use_figma` calls.

5. **Plain JS with top-level `await`.** Code is auto-wrapped in async. Do NOT wrap in `(async () => {})()`.

6. **Colors are 0–1 RGB; ALL fields required.** `{r, g, b}` — no `hex:`, no `a:` in color. Opacity goes outside color: `{type:'SOLID', color:{r,g,b}, opacity: 0.5}`. Hex helper: `const hex = h => { const n = parseInt(h.replace('#',''), 16); return { r:((n>>16)&255)/255, g:((n>>8)&255)/255, b:(n&255)/255 } }`. See [references/critical-rules-deep.md](figma-use/references/critical-rules-deep.md) for WRONG/RIGHT.

7. **No `curl` / `wget` / `Read` of Figma URLs from `Bash`.** Figma file access ONLY via `use_figma` and `mcp__figma__*` tools. After `get_screenshot`, the image is inlined in the tool result — do NOT re-fetch or re-Read it.

8. **Empty / unsupported responses are terminal.** Accept and move on — don't try alternative bypass paths.

9. **Verify node-type before touching a property.** Only `FRAME / COMPONENT / COMPONENT_SET / INSTANCE / GROUP / SECTION / PAGE` have `.children`. `GROUP` has no `fills` / `strokes` / `cornerRadius`. `TEXT` has no `cornerRadius` / `padding*` / `layoutMode`. `layoutPositioning='ABSOLUTE'` needs parent with `layoutMode !== 'NONE'`. Check `'<prop>' in node` or grep [references/plugin-api-standalone.d.ts](figma-use/references/plugin-api-standalone.d.ts). Full list in [references/critical-rules-deep.md](figma-use/references/critical-rules-deep.md).

10. **Don't re-query the same info.** `get_metadata` / `get_comments` on the same target twice yields the same result. Cache mentally.

11. **Be decisive once you have enough info.** Don't keep gathering — the marginal information from a 3rd screenshot or 4th metadata call is near-zero.

12. **"An unexpected error occurred" from `use_figma` is server-side, not your script bug.** Don't retry unchanged — change approach (smaller batch, different selector, drop one node-prop).

13. **NEVER call `mcp__figma__get_design_context`. FORBIDDEN.** This tool requires a selection (no selection exists in this environment), so every call will fail. The error is not recoverable — calling it just burns a tool slot and forces a retry. For structured reads of the file, use `mcp__figma__get_metadata` (for top-level frame discovery) and `use_figma` with `$fig.query()` instead. **Never call `get_design_context` for any reason.**

14. **≤3 codebase `Read` calls when the task references source code.** Beyond that, grep only. The 4th codebase Read is forbidden — write your `use_figma` script with what you have.

15. **3 retries of the same error → switch approach.** Most often: switch to `$fig` (which handles ordering automatically). Patching the raw API isn't working.

16. **Must use auto-layout unless you have a compelling reason not to.** Create auto-layout frames with `$fig.autoLayout(...)` instead of absolutely-positioning nodes.  New auto-layout frames are created with both axes hugging content. Explicitly assign `layoutSizingHorizontal` or `layoutSizingVertical` to `'FILL'` for auto-layout children if you want them to fill the auto-layout container's counter axis.

17. **Gradient paints need ALL fields:** `type`, `gradientStops`, `gradientTransform` (a `[[a,b,tx],[c,d,ty]]` matrix). Missing any throws validation error. See [references/critical-rules-deep.md](figma-use/references/critical-rules-deep.md).

18. **Discover available fonts, esp. for style variations.** Use `await figma.listAvailableFontsAsync()` to discover available fonts for `$fig.text({ fontName: ... })`.

### Bulk mutation of existing nodes (swap/update/replace) is COMPLETE in 3 `use_figma` calls

For tasks like "swap N icons", "update M colors", "replace K instances":
1. **DISCOVER + MUTATE** in one script (find via `figma.currentPage.query()`, import any components, mutate via `$fig.query(...).each(...)`, return count).
2. **VERIFY** (optional) — read-only `.query()` count.
3. **FINAL REPORT** in assistant text, no tool call. STOP.

NO 4th call. NO chasing the last 20% of edge cases. If Call 1 errors, fix and redo — that's still your one mutation call. Full template in [references/critical-rules-deep.md](figma-use/references/critical-rules-deep.md).

## Node property gotchas

Do not guess node properties or assume CSS-like properties. Accessing non-existent properties will throw `TypeError: node.foo: no such property 'foo' on TYPE node`. Each throw burns a retry. [plugin-api-standalone.index.md](figma-use/references/plugin-api-standalone.index.md) contains the list of all symbols in the API. Use that file and grep the full API typings in [plugin-api-standalone.d.ts](figma-use/references/plugin-api-standalone.d.ts) for the full definitions.

- **Only `FRAME` / `COMPONENT` / `COMPONENT_SET` / `INSTANCE` / `GROUP` / `SECTION` / `PAGE` have `.children`.** `RECTANGLE`, `TEXT`, `ELLIPSE`, `POLYGON`, `STAR`, `VECTOR`, `LINE`, `SLICE`, `STICKY`, `SHAPE_WITH_TEXT`, `STAMP`, `CONNECTOR`, `TABLE`, `WIDGET`, `EMBED`, `MEDIA` do NOT. Check `'children' in node` before accessing a node's children.
- **`GROUP` has NO `fills` / `strokes` / `cornerRadius`.** Apply paints/radii on the child shapes inside.
- **Figma auto-layout != CSS flexbox.** There is no such thing as margin.
- **`TEXT` DOES NOT HAVE container properties.** Text has font / size / decoration / fills. Do not use container properties like padding, layout mode, item spacing, etc.
- **`INSTANCE` descendants are read-only for structural ops** — you cannot `appendChild` / `insertChild` into an instance child. Edit the source `COMPONENT` or detach first.
- **Never use `primaryAxisSizingMode` or `counterAxisSizingMode` on a node. ** Use `layoutSizingHorizontal` or `layoutSizingVertical` with 'FIXED' | 'HUG' | 'FILL'. Use 'FILL' only when the parent has auto-layout.
- **There is NO `instance.swapMainComponent(...)`.** Use `instance.setProperties({...})` with the component-property variant value, OR `$fig.query(...).set({props: {...}})`. There IS `instance.swapComponent(component)` (different method name).

## References

- [references/fig-builder.md](figma-use/references/fig-builder.md) — full `$fig` API and worked patterns
- [references/critical-rules-deep.md](figma-use/references/critical-rules-deep.md) — WRONG/RIGHT examples, full node-type pitfall list, bulk-mutation template, syntax-bug checklist
- [references/gotchas.md](figma-use/references/gotchas.md) — raw Plugin API edge cases
- [references/plugin-api-standalone.d.ts](figma-use/references/plugin-api-standalone.d.ts) — type definitions (grep, don't read whole)
- [references/plugin-api-standalone.index.md](figma-use/references/plugin-api-standalone.index.md) — API navigation
- [references/common-patterns.md](figma-use/references/common-patterns.md), [component-patterns.md](figma-use/references/component-patterns.md), [variable-patterns.md](figma-use/references/variable-patterns.md), [text-style-patterns.md](figma-use/references/text-style-patterns.md), [effect-style-patterns.md](figma-use/references/effect-style-patterns.md) — pattern playbooks
- [references/working-with-design-systems/](figma-use/references/working-with-design-systems/) — design system workflows
- [references/validation-and-recovery.md](figma-use/references/validation-and-recovery.md) — error recovery patterns
