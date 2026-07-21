# use_figma — Figma Plugin API Skill

Execute JavaScript in Figma files via the Plugin API. **Always pass `skillNames: "figma-use"` when calling `use_figma`** (logging parameter, doesn't affect execution).

**If the task involves building or updating a full page, screen, or multi-section layout in Figma from code**, also load figma-generate-design (load `readPowerSteering("figma", "figma-generate-design.md")`). It provides the workflow for discovering design system components via `search_design_system`, importing them, and assembling screens incrementally. Both skills work together: this one for the API rules, that one for the screen-building workflow.

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
> ⚠️ `$fig.variants` does **not** position the variants — they stack at (0,0) and the set renders as one collapsed, overlapping element. You must grid the variants and resize the set afterward. See [`$fig` Builder API](#required-follow-up--grid-the-variants-fig-build--raw-layout) for the required follow-up recipe.

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
- **Create from SVG — the preferred ICON path:** `$fig.svg(svgStr, opts?)` builds a vector node tree from an SVG string. **Prefer real vector icons:** import the icon's SVG source (inline `<svg>`, the `.svg` asset, or the source icon-library glyph — e.g. lucide/heroicons) via `$fig.svg(...)` rather than approximating an icon with a typed emoji/Unicode glyph (★ ⚙ 🔍 ☰ ▾) or a plain rectangle. A simple glyph or shape is a fine fallback when the real SVG genuinely can't be obtained — just reach for the SVG first. (Don't reconstruct an icon from rotated line/rect primitives, though — that renders broken.) Full recipe (viewBox+width/height sizing, `currentColor`, INSTANCE_SWAP for design-system icons): figma-generate-design → Icons (load `readPowerSteering("figma", "figma-generate-design.md")`).
- **Create an instance of a component:** `$fig.instance(compRef, opts?)` — `compRef` is a component plan node, a node ID string, OR a library asset key (`componentKey` from `search_design_system`); the import is queued in the plan automatically.
- **Grouping/boolean:** `$fig.group / .union / .subtract / .intersect / .exclude / .variants` — all `(opts?, children?)`.
- **Read:** `$fig.get(id)` wraps an existing `SceneNode` — `id` can be a real node ID OR a library asset key (`componentKey` from `search_design_system`); the import is queued in the plan automatically. `$fig.query(selector, scope?)` returns `{ length, values(paths), first(), last(), each(fn), filter(fn), set(props), moveTo(parent, idx?), remove() }`. Selectors are CSS-like (e.g. `'FRAME[name*=Card] TEXT'`). `$fig.getStyle(nameOrIdOrKey)` and `$fig.getVar(nameOrIdOrKey)` accept the matching `key` values from `search_design_system`.
- **Mutate:** `$fig.set(target, props)`, `.delete(...nodes)`, `.move(target, parent, idx?)`, `.clone(target, props?)`, `.append(parent, child)`, `.addAt(parent, idx, child)`, `.replace(old, new)`, `.reorder(parent, children)`, `.setPage(name)`, `.gradient(node, type, stops, transform?)`, `.image(node, hash, scaleMode?)`.
- **Plan-node methods (chainable):** `.set()`, `.remove()`, `.clone()`, `.moveTo(parent, idx?)`, `.append(child)`, `.query(selector)`, `.screenshot({scale?, contentsOnly?})`, and the `.node` getter for the materialized `SceneNode` (null pre-flush).

### When to use the raw Figma Plugin API

Only these cases — and even then, mix raw API with `$fig` in the same script:

- **Mid-script async result needed:** `await figma.setCurrentPageAsync(...)`, `await figma.loadFontAsync(...)` — must complete before subsequent plan steps can use the result. (Importing library components is NOT one of these cases: pass the `componentKey` straight into `$fig.get(...)` / `$fig.instance(...)` and pass variant property values in `props`. `$fig` queues the library import in the plan and resolves the variant for you.)
- **Mid-script real node state read:** measured `width` / `height` after auto-layout, computed colors, getStyledTextSegments — materialize mid-script, then read `.node` on the plan node. See [`$fig` Builder API](#reference--fig-builder-api) for the mid-script inspection pattern.
- **Things `$fig` genuinely doesn't expose:** `node.setRangeFontName(...)`, etc. — access via `planNode.node` (see [`$fig` Builder API](#reference--fig-builder-api)).

## Critical Rules

1. **Only use `$fig` for creating / bulk-editing nodes** (`$fig.autoLayout(...)`, `$fig.text(...)`, `$fig.query(...).set(...)`). Raw Plugin API is the fallback — use it only when `$fig` can't express the operation (intermediate node-state reads, non-SceneNode types like Variables). Library components are NOT a reason to leave `$fig`: `$fig.get(componentKey)` / `$fig.instance(componentSetKey, { props })` queue the library import and resolve the variant for you. See [`$fig` Builder API](#reference--fig-builder-api) and [figma-use — Deep Critical Rules & Worked Examples](#reference--figma-use--deep-critical-rules--worked-examples) for worked WRONG/RIGHT examples.

2. **Do not use `findOne`, `findAll`, `findAllWithCriteria`, `findChildren`, `findChild` directly for node searching** They are more verbose, error-prone, and less efficient than `query()`.  Additionally, do not use recursion to search.

3. **Avoid `return` / `$fig.done()` if only using `$fig`** — runtime auto-flushes and returns a `FigDoneResult` with created/updated node IDs. Use `return` if you need raw plugin API mid-script or other data.

4. **Build up larger designs incrementally by section.** Refer to the figma-generate-design (load `readPowerSteering("figma", "figma-generate-design.md")`) skill for the placeholder + replace workflow. Create screens with placeholders inside, e.g. `$fig.autoLayout({ name: 'Header', layoutSizingHorizontal: 'FILL', placeholder: true })`, then make subsequent `use_figma` calls to replace them and screenshot: `$fig.get("PLACEHOLDER_ID_FROM_PREVIOUS_STEP").replace( ... ).screenshot()`. You can make up to 5 `.screenshot()` calls per tool call. If you need to make more screenshots, you are doing too much work and need to break down the task into multiple `use_figma` calls.

5. **Plain JS with top-level `await`.** Code is auto-wrapped in async. Do NOT wrap in `(async () => {})()`.

6. **Colors are 0–1 RGB; ALL fields required.** `{r, g, b}` — no `hex:`, no `a:` in color. Opacity goes outside color: `{type:'SOLID', color:{r,g,b}, opacity: 0.5}`. Hex helper: `const hex = h => { const n = parseInt(h.replace('#',''), 16); return { r:((n>>16)&255)/255, g:((n>>8)&255)/255, b:(n&255)/255 } }`. See [figma-use — Deep Critical Rules & Worked Examples](#reference--figma-use--deep-critical-rules--worked-examples) for WRONG/RIGHT.

7. **No `curl` / `wget` / `Read` of Figma URLs from `Bash`.** Figma file access ONLY via `use_figma` and `mcp__figma__*` tools. After `get_screenshot`, the image is inlined in the tool result — do NOT re-fetch or re-Read it.

8. **Empty / unsupported responses are terminal.** Accept and move on — don't try alternative bypass paths.

9. **Verify node-type before touching a property.** Only `FRAME / COMPONENT / COMPONENT_SET / INSTANCE / GROUP / SECTION / PAGE` have `.children`. `GROUP` has no `fills` / `strokes` / `cornerRadius`. `TEXT` has no `cornerRadius` / `padding*` / `layoutMode`. `layoutPositioning='ABSOLUTE'` needs parent with `layoutMode !== 'NONE'`. Check `'<prop>' in node` or grep Plugin API type reference (load `readPowerSteering("figma", "figma-use-api.md")`). Full list in [figma-use — Deep Critical Rules & Worked Examples](#reference--figma-use--deep-critical-rules--worked-examples).

10. **Don't re-query the same info.** `get_metadata` / `get_comments` on the same target twice yields the same result. Cache mentally.

11. **Be decisive once you have enough info.** Don't keep gathering — the marginal information from a 3rd screenshot or 4th metadata call is near-zero.

12. **"An unexpected error occurred" from `use_figma` is server-side, not your script bug.** Don't retry unchanged — change approach (smaller batch, different selector, drop one node-prop).

13. **NEVER call `mcp__figma__get_design_context`. FORBIDDEN.** This tool requires a selection (no selection exists in this environment), so every call will fail. The error is not recoverable — calling it just burns a tool slot and forces a retry. For structured reads of the file, use `mcp__figma__get_metadata` (for top-level frame discovery) and `use_figma` with `$fig.query()` instead. **Never call `get_design_context` for any reason.**

14. **≤3 codebase `Read` calls when the task references source code.** Beyond that, grep only. The 4th codebase Read is forbidden — write your `use_figma` script with what you have.

15. **3 retries of the same error → switch approach.** Most often: switch to `$fig` (which handles ordering automatically). Patching the raw API isn't working.

16. **Must use auto-layout unless you have a compelling reason not to.** Create auto-layout frames with `$fig.autoLayout(...)` instead of absolutely-positioning nodes.  New auto-layout frames are created with both axes hugging content. Explicitly assign `layoutSizingHorizontal` or `layoutSizingVertical` to `'FILL'` for auto-layout children if you want them to fill the auto-layout container's counter axis.

17. **Gradient paints need ALL fields:** `type`, `gradientStops`, `gradientTransform` (a `[[a,b,tx],[c,d,ty]]` matrix). Missing any throws validation error. See [figma-use — Deep Critical Rules & Worked Examples](#reference--figma-use--deep-critical-rules--worked-examples).

18. **Discover available fonts, esp. for style variations.** Use `await figma.listAvailableFontsAsync()` to discover available fonts for `$fig.text({ fontName: ... })`.

### Bulk mutation of existing nodes (swap/update/replace) is COMPLETE in 3 `use_figma` calls

For tasks like "swap N icons", "update M colors", "replace K instances":
1. **DISCOVER + MUTATE** in one script (find via `figma.currentPage.query()`, import any components, mutate via `$fig.query(...).each(...)`, return count).
2. **VERIFY** (optional) — read-only `.query()` count.
3. **FINAL REPORT** in assistant text, no tool call. STOP.

NO 4th call. NO chasing the last 20% of edge cases. If Call 1 errors, fix and redo — that's still your one mutation call. Full template in [figma-use — Deep Critical Rules & Worked Examples](#reference--figma-use--deep-critical-rules--worked-examples).

## Node property gotchas

Do not guess node properties or assume CSS-like properties. Accessing non-existent properties will throw `TypeError: node.foo: no such property 'foo' on TYPE node`. Each throw burns a retry. [Plugin API Index](#reference--plugin-api-index) contains the list of all symbols in the API. Use that file and grep the full API typings in Plugin API type reference (load `readPowerSteering("figma", "figma-use-api.md")`) for the full definitions.

- **Only `FRAME` / `COMPONENT` / `COMPONENT_SET` / `INSTANCE` / `GROUP` / `SECTION` / `PAGE` have `.children`.** `RECTANGLE`, `TEXT`, `ELLIPSE`, `POLYGON`, `STAR`, `VECTOR`, `LINE`, `SLICE`, `STICKY`, `SHAPE_WITH_TEXT`, `STAMP`, `CONNECTOR`, `TABLE`, `WIDGET`, `EMBED`, `MEDIA` do NOT. Check `'children' in node` before accessing a node's children.
- **`GROUP` has NO `fills` / `strokes` / `cornerRadius`.** Apply paints/radii on the child shapes inside.
- **Figma auto-layout != CSS flexbox.** There is no such thing as margin.
- **`TEXT` DOES NOT HAVE container properties.** Text has font / size / decoration / fills. Do not use container properties like padding, layout mode, item spacing, etc.
- **`INSTANCE` descendants are read-only for structural ops** — you cannot `appendChild` / `insertChild` into an instance child. Edit the source `COMPONENT` or detach first.
- **Never use `primaryAxisSizingMode` or `counterAxisSizingMode` on a node. ** Use `layoutSizingHorizontal` or `layoutSizingVertical` with 'FIXED' | 'HUG' | 'FILL'. Use 'FILL' only when the parent has auto-layout.
- **There is NO `instance.swapMainComponent(...)`.** Use `instance.setProperties({...})` with the component-property variant value, OR `$fig.query(...).set({props: {...}})`. There IS `instance.swapComponent(component)` (different method name).

## References

- [`$fig` Builder API](#reference--fig-builder-api) — full `$fig` API and worked patterns
- [figma-use — Deep Critical Rules & Worked Examples](#reference--figma-use--deep-critical-rules--worked-examples) — WRONG/RIGHT examples, full node-type pitfall list, bulk-mutation template, syntax-bug checklist
- [Gotchas & Common Mistakes](#reference--gotchas--common-mistakes) — raw Plugin API edge cases
- Plugin API type reference (load `readPowerSteering("figma", "figma-use-api.md")`) — type definitions (grep, don't read whole)
- [Plugin API Index](#reference--plugin-api-index) — API navigation
- [Common Patterns](#reference--common-patterns), [Component & Variant API Patterns](#reference--component--variant-api-patterns), [Variable & Token API Patterns](#reference--variable--token-api-patterns), [Text Style API Patterns](#reference--text-style-api-patterns), [Effect Style API Patterns](#reference--effect-style-api-patterns) — pattern playbooks
- [references/working-with-design-systems/](references/working-with-design-systems/) — design system workflows
- [Validation Workflow & Error Recovery](#reference--validation-workflow--error-recovery) — error recovery patterns

---

## Reference — `$fig` Builder API

`$fig` is a plan-based builder exposed as a global in `use_figma` scripts. Every call builds a lightweight plan tree; nothing touches the Figma API until the plan is materialized. The plan is **automatically materialized** when the script finishes — you do not need to call `$fig.done()` explicitly.

### When to use `$fig` vs raw Plugin API

**Default to `$fig`.** Any `use_figma` script that creates nodes or mutates more than one node at a time should reach for `$fig` first. The builder handles:

- Font preloading (collects every `fontName` used anywhere in the plan and loads them in one batch before materialization)
- Correct property ordering (`layoutMode` before sizing, `connectorLineType` before start/end, etc.)
- Parenting and auto-layout child sizing

Fall back to the raw Plugin API (`figma.createFrame()`, direct property assignment, `findAll`) **only** when `$fig` genuinely cannot express the operation:

- You need the result of an async call mid-build — e.g. `setCurrentPageAsync` or `loadFontAsync` that must complete before the next create decision. (You do NOT need raw `importComponentByKeyAsync` / `importComponentSetByKeyAsync` to use a library component: pass the `componentKey` straight into `$fig.get(...)` / `$fig.instance(...)`. For component sets, variant selection happens via `{ props: {...} }` — no need to inspect `compSet.children` yourself.)
- You need to read a real node's computed property (e.g. measured `width` after auto-layout) to decide what to create next
- You need tight per-node control flow where each node's shape depends on the previous one's state

These cases are the minority. If your first instinct is "I'll just call `figma.createRectangle()` once," rewrite it as `$fig.rectangle(...)`. If you're assigning properties one line at a time, rewrite it as `$fig.set(node, { ... })` or inline the props into the create call.

You can freely mix: call `$fig` for the bulk of the build, `await $fig.done()` to materialize, then inspect or tweak real nodes before a second `$fig` pass.

### Creating nodes

Every create method has the same shape: `(name?, opts?, children?)`. `children` is an array of plan nodes that become the node's children.

```js
// Frame with children — children passed as an array
$fig.autoLayout({ name: 'Card', layoutMode: 'VERTICAL', itemSpacing: 8 }, [
  $fig.text({ characters: 'Title', fontSize: 20, fontName: { family: 'Inter', style: 'Bold' } }),
  $fig.text({ characters: 'Description', fontSize: 14 }),
  $fig.rectangle({ name: 'Divider', width: 320, height: 1, fills: [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }] }),
])
```

Plan nodes are also **chainable** — calling a create method on a plan node adds the new node as a child of that plan node:

```js
const card = $fig.autoLayout({ name: 'Card', layoutMode: 'VERTICAL', itemSpacing: 8 })
card.text({ characters: 'Title', fontSize: 20 })
card.text({ characters: 'Description', fontSize: 14 })
```

#### Design-mode create methods

| Method | Node type |
|---|---|
| `$fig.frame(opts?, children?)` | `FRAME` |
| `$fig.autoLayout(opts?, children?)` | `FRAME` with auto-layout pre-configured (both axes hugging content). Default direction `HORIZONTAL`; pass `layoutMode: 'VERTICAL'` in opts to switch. |
| `$fig.rectangle(opts?)` | `RECTANGLE` |
| `$fig.ellipse(opts?)` | `ELLIPSE` |
| `$fig.polygon(opts?)` | `REGULAR_POLYGON` |
| `$fig.star(opts?)` | `STAR` |
| `$fig.line(opts?)` | `LINE` |
| `$fig.vector(opts?)` | `VECTOR` |
| `$fig.text(opts?)` | `TEXT` |
| `$fig.section(opts?, children?)` | `SECTION` |
| `$fig.slice(opts?)` | `SLICE` |
| `$fig.component(opts?, children?)` | `SYMBOL` (main component) |
| `$fig.page(opts?, children?)` | `PAGE` (new page node) |
| `$fig.svg(svgString, opts?)` | Node tree parsed from SVG |
| `$fig.instance(compRef, opts?)` | `INSTANCE` — `compRef` is a component plan node, a node ID string, OR a library asset key (`componentKey` from `search_design_system`); the import is queued in the plan automatically. |

FigJam-only types (`$fig.sticky`, `$fig.connector`, `$fig.shapeWithText`, `$fig.codeBlock`, `$fig.table`) are available when the script runs in a FigJam file; Slides-only types (`$fig.slide`, `$fig.slideRow`) are available in Slides.

#### Grouping and boolean operations

Each wraps its `children` in a single parent node of the given type. Use the same `(name?, opts?, children?)` signature.

```js
$fig.union({ name: 'U' }, [
  $fig.rectangle({ name: 'R1', x: 0, y: 0, width: 100, height: 100 }),
  $fig.rectangle({ name: 'R2', x: 50, y: 50, width: 100, height: 100 }),
])
```

| Method | Effect |
|---|---|
| `$fig.group(opts?, children?)` | Regular group |
| `$fig.union(opts?, children?)` | Boolean union |
| `$fig.subtract(opts?, children?)` | Boolean subtract |
| `$fig.intersect(opts?, children?)` | Boolean intersect |
| `$fig.exclude(opts?, children?)` | Boolean exclude |
| `$fig.variants(opts?, children?)` | `combineAsVariants` on the child components. **Does NOT position the variants — see the caveat below.** |

**⚠️ `$fig.variants` does NOT lay out the variants — they stack at (0,0).** Unlike `$fig.autoLayout` (which arranges its children), `$fig.variants` is a thin wrapper over `figma.combineAsVariants`: it groups the child components into a ComponentSet but leaves every variant at `(0, 0)`, so the set renders as a single collapsed element with all variants overlapping. After creating the set you **must** position the variants into a readable grid and resize the set — the requirement is identical whether you use `$fig.variants` or the raw `figma.combineAsVariants`.

##### Required follow-up — grid the variants (`$fig` build + raw layout)

`$fig.variants` can't lay the set out itself, and you can't know each variant's size until it's built — so the pattern is: **build with `$fig`, `await $fig.done()` to materialize, then measure the real variants and grid them with the raw Plugin API.** This is a legitimate `$fig` + raw-API mix — "read a real node's computed property (e.g. measured `width` after auto-layout) to decide what to create next" is exactly the escape hatch called out in [When to use `$fig` vs raw Plugin API](#when-to-use-fig-vs-raw-plugin-api).

```js
// 1) Build each variant as a $fig.component. Encode the axes in the NAME
//    ("Prop=Value, Prop=Value") — that's how combineAsVariants derives the set's properties.
const set = $fig.variants({ name: 'KPICard' }, [
  $fig.component({ name: 'Trend=Up' },   [ /* …header, value, footer… */ ]),
  $fig.component({ name: 'Trend=Down' }, [ /* …header, value, footer… */ ]),
])

// 2) Materialize NOW so every variant has a real, measured width/height.
await $fig.done()

// 3) Grid the variants with the raw Plugin API, using MEASURED sizes.
const cs = set.node                 // the live ComponentSetNode
const variants = cs.children        // the live variant ComponentNodes
const GRID_GAP = 16, PADDING = 40
const cols = 2                      // # of values on the axis you want across the top (e.g. State)
const cellW = Math.max(...variants.map((v) => v.width))   // uniform cells → aligned columns
const cellH = Math.max(...variants.map((v) => v.height))
variants.forEach((v, i) => {
  v.x = PADDING + (i % cols) * (cellW + GRID_GAP)
  v.y = PADDING + Math.floor(i / cols) * (cellH + GRID_GAP)
})

// 4) Resize the set to wrap the grid (+ padding), then place it on the canvas.
const totalCols = Math.min(cols, variants.length)
const totalRows = Math.ceil(variants.length / cols)
cs.resizeWithoutConstraints(
  totalCols * cellW + (totalCols - 1) * GRID_GAP + PADDING * 2,
  totalRows * cellH + (totalRows - 1) * GRID_GAP + PADDING * 2,
)
cs.x = 480
cs.y = 80
```

Skipping step 2–4 is the single most common variant bug — the set collapses to one visible variant with the rest hidden behind it. For the full multi-axis version (State on columns, Size/Style on rows) plus doc frames and grid labels, see [Laying Out Variants After combineAsVariants (Required)](#laying-out-variants-after-combineasvariants-required) and the complete `createComponentWithVariants.js` (load `readPowerSteering("figma", "figma-generate-library.md")`) script.

### Component properties

Expose component properties directly from the builder with `.textProp` / `.booleanProp` / `.instanceSwapProp` — no raw `addComponentProperty` needed. Call these chainable methods on the **layer inside a component definition** that carries the property; the property is added to the containing component (or, if that component is part of a set, to the ComponentSet), with its default inferred from that layer:

| Method | Property | Default from | Controls |
|---|---|---|---|
| `layer.textProp(name)` | `TEXT` | the layer's `characters` | the layer's text |
| `layer.booleanProp(name)` | `BOOLEAN` | the layer's `visible` | the layer's visibility |
| `layer.instanceSwapProp(name)` | `INSTANCE_SWAP` | the layer's `mainComponent` (layer must be an INSTANCE) | which instance is shown |

Each returns the layer, so calls chain. Rules:

- **Must be inside a component.** The method walks up to the enclosing `$fig.component(...)`; calling it on a node that is not within a component definition throws (`property ref of type … can only be used on nodes within a component definition`).
- **Variant sets de-dup.** If the enclosing component is part of a set, the definition lands on the set. Applying the same property name to the corresponding layer in each variant is de-duplicated into a single definition — so you can add props per-variant safely.

```js
// A Button component exposing Label (TEXT), Show Icon (BOOLEAN), and Icon (INSTANCE_SWAP)
$fig.component({ name: 'Button' }, [
  $fig.autoLayout({ name: 'Content', layoutMode: 'HORIZONTAL', itemSpacing: 8 }, [
    $fig.instance(iconComp, { name: 'Icon' })
      .instanceSwapProp('Icon')     // swap which icon is shown
      .booleanProp('Show Icon'),    // toggle the icon on/off
    $fig.text({ characters: 'Button' })
      .textProp('Label'),           // override the label text
  ]),
])
```

Prefer these over raw `comp.addComponentProperty(...)`, which must run on a materialized *product* component in the right order — mis-sequencing throws (`"Can only set component property definitions on a product component"`, `"no setter for property"`). The `$fig` methods handle the timing and the variant de-dup for you. To set property *values* on an instance (not define them), use `setProperties` — see [Component & Variant API Patterns](#reference--component--variant-api-patterns).

### Styles — create, reference, apply

Plan-step style API. Creators return per-style handles — `FigPlanPaintStyle` / `FigPlanTextStyle` / `FigPlanEffectStyle` / `FigPlanGridStyle` — with the union exported as `FigPlanStyle`. Existing styles can be wrapped by name or id via `$fig.getStyle()` (returns the union or `null`; narrow via `handle.style?.type`). Every handle supports `.set`, `.remove`, and a `.style` getter for escape-to-live-Figma access post-`done()`. The per-style handles tighten `.style` and the `.set` fn arg to the concrete style class so type-specific fields (e.g. `paints` on paint, `fontName` on text) autocomplete without casts.

| Method | Returns | Effect |
|---|---|---|
| `$fig.paintStyle(opts)` | `FigPlanPaintStyle` | Create a paint style. `opts.name` required. `opts.paints` optional. |
| `$fig.textStyle(opts)` | `FigPlanTextStyle` | Create a text style. `opts.name` required. `opts.fontName` / `opts.fontSize` / etc. |
| `$fig.effectStyle(opts)` | `FigPlanEffectStyle` | Create an effect style. `opts.name` required. `opts.effects` optional. |
| `$fig.gridStyle(opts)` | `FigPlanGridStyle` | Create a grid style. `opts.name` required. `opts.layoutGrids` optional. |
| `$fig.getStyle(nameOrIdOrKey)` | `FigPlanStyle \| null` | Wrap an existing local style OR a library style by `key` (the value returned by `search_design_system` with `includeStyles: true`). Tries id, then asset key (queues a plan-managed library import if the style isn't yet in the file), then scans paint → text → effect → grid styles by name. |
| `planStyle.set(opts \| fn)` | `this` | Apply props in place. Fn form receives the **live Figma `Style`** narrowed to the concrete subtype (`PaintStyle` / `TextStyle` / `EffectStyle` / `GridStyle`). |
| `planStyle.remove()` | `this` | Delete the style. |
| `planStyle.id` | `string` | Real style id (after `done()`) or planId (before). Use this when binding by id manually. |
| `planStyle.style` | concrete `Style` or `null` | `null` before `done()`, the live `Style` object after. |

`opts.sharedPluginData: { namespace: { key: value } }` is supported on every `$fig` creator (scene-graph nodes and styles), every `.set()`, every `figma.createX(props)` creator, and raw `node.set(props)` — applied via `setSharedPluginData(ns, key, value)` per entry. Values are coerced to strings.

#### Applying a style to a node

Pass the style handle directly in the property. `$fig` routes through the corresponding `*StyleId` setter at flush time:

```js
const brand = $fig.paintStyle({ name: 'Brand/Primary', paints: [solidBlue] })
$fig.rectangle({ fills: brand, effects: shadowStyle })
$fig.text({ characters: 'Title', textStyle: headingStyle })

// Existing styles work the same way
const existing = $fig.getStyle('Brand/Secondary')
$fig.query('FRAME[name^=Card]').set({ fills: existing })
```

Properties that accept a `FigPlanStyle`: `fills` → `fillStyleId`, `strokes` → `strokeStyleId`, `effects` → `effectStyleId`, `layoutGrids` → `gridStyleId`, `textStyle` → `textStyleId`. Plain paint/effect/grid arrays in those properties still apply as direct values (no style binding).

**Why route through `fills` rather than `fillStyleId`?** `fills` is where agents already think about the visual layer, and the property is non-style-binding by default — passing a plain paint array applies as the fill verbatim, so routing only fires when the value is a `FigPlanStyle`. Using the property name keeps the call site readable (`fills: brand` reads as "the fill is brand"), and the `*StyleId` form remains the Plugin API spelling underneath. `textStyle` is the one property that's genuinely synthetic — `TextNode` has no `textStyle` prop natively, only `textStyleId`, so it's accepted purely to spare agents the `*StyleId` suffix.

**Raw `node.set` caveat.** The same routing also fires on a raw `node.set({ fills: handle })` call outside a `$fig` plan, but only **`$fig.getStyle()` handles** are detected (they carry a `_type` marker and a real id). Two cases that don't work:

- A raw Figma `PaintStyle` from `figma.createPaintStyle()` — no `_type` marker; the value falls through and `node.set` tries to assign the style object to `fills`, which fails type validation. Use either `$fig.getStyle(ps.id)` to wrap it, or assign `rect.fillStyleId = ps.id` directly.
- A freshly-created `$fig.paintStyle(...)` handle whose plan isn't flushed yet — detected by `_type`, but the handle's `id` is still a `planId`; Figma's `*StyleId` setter silently accepts and ignores unknown ids, so the bind never lands and the property's existing array is left untouched.

Go through a `$fig` plan (`$fig.rectangle({...})`, `$fig.set(target, ...)`, `$fig.query(...).set(...)`) when binding a style you just created — the plan path resolves the `planId` → real id at flush time via the plan registry.

### Variables — create, reference, bind

Plan-step variable API. `$fig.varCollection(opts)` creates a new collection; `opts.modes` (non-empty string array) is required alongside `opts.name`. Variable creators on the collection handle return per-type `FigPlanVariable` handles. The union is `FigPlanVariable = FigPlanColorVar | FigPlanNumVar | FigPlanBoolVar | FigPlanStringVar`.

| Method | Returns | Effect |
|---|---|---|
| `$fig.varCollection(opts)` | `FigPlanVarCollection` | Create a variable collection. `opts.name` + `opts.modes` required. |
| `$fig.getVarCollection(idOrName)` | `FigPlanVarCollection` | Wrap existing collection by id or name. Throws if not found. |
| `$fig.getVar(idOrKey)` | `FigPlanVariable` | Wrap an existing variable by real Figma variable id OR a library variable `key` (the value returned by `search_design_system` with `includeVariables: true`). For an asset key, the plan queues a library import automatically. Throws if not found. |
| `coll.colorVar(opts)` | `FigPlanColorVar` | Create a COLOR variable. `opts.name` required. `opts.values` as `{ modeName: hexString }`. |
| `coll.numVar(opts)` | `FigPlanNumVar` | Create a FLOAT variable. `opts.name` required. `opts.values` as `{ modeName: number }`. |
| `coll.boolVar(opts)` | `FigPlanBoolVar` | Create a BOOLEAN variable. `opts.values` as `{ modeName: boolean }`. |
| `coll.stringVar(opts)` | `FigPlanStringVar` | Create a STRING variable. `opts.values` as `{ modeName: string }`. |
| `coll.getVar(nameOrId)` | `FigPlanVariable` | Wrap existing variable in this collection by name or id. Throws if not found. |
| `coll.set(opts \| fn)` | `this` | Update collection properties (name, etc.). |
| `coll.remove()` | `this` | Delete the collection. |
| `variable.set(opts \| fn)` | `this` | Update variable properties. Accepts `name`, `scopes`, `description`, `codeSyntax: { WEB?, ANDROID?, iOS? }`, and other writable `Variable` properties. |
| `variable.value(modeName, value)` | `this` | Set a single mode value. |
| `variable.setValues(map \| fn)` | `this` | Set all mode values at once. Fn form receives the live `Variable` object. |
| `variable.remove()` | `this` | Delete the variable. |
| `variable.id` | `string` | Real variable id (after `done()`) or planId (before). |
| `variable.resolvedType` | `string` | `'COLOR'` / `'FLOAT'` / `'BOOLEAN'` / `'STRING'`. |
| `variable.variable` | `Variable \| null` | `null` before `done()`, the live Figma `Variable` object after. |

`opts.scopes: VariableScope[]` on variable creators controls which Figma property pickers show the variable. Specify intentionally — defaults can bind to unwanted properties. Common scopes: `['WIDTH_HEIGHT']`, `['GAP']`, `['CORNER_RADIUS']`, `['SHAPE_FILL', 'FRAME_FILL']`, `['TEXT_FILL']`, `['OPACITY']`.

`opts.sharedPluginData` is supported on every creator and on `set()`.

`opts.codeSyntax: { WEB?, ANDROID?, iOS? }` links a variable to its code counterpart. Pass at creation time or via `variable.set()` afterward:

```js
// At creation time
tokens.colorVar({
  name: 'color/brand',
  values: { Light: '#3B82F6', Dark: '#60A5FA' },
  codeSyntax: { WEB: 'var(--color-brand)', ANDROID: 'colorBrand', iOS: 'Color.brand' },
})

// Or after creation
myVar.set({ codeSyntax: { WEB: 'var(--color-brand)' } })
```

#### Binding a variable to a node property

Pass the variable handle directly as the property value. `$fig` detects the handle and routes to `setBoundVariable` at flush time:

```js
const tokens = $fig.varCollection({ name: 'Tokens', modes: ['Light', 'Dark'] })
const w = tokens.numVar({ name: 'size/lg', values: { Light: 200, Dark: 200 }, scopes: ['WIDTH_HEIGHT'] })
const blue = tokens.colorVar({ name: 'color/brand', values: { Light: '#3B82F6', Dark: '#60A5FA' }, scopes: ['SHAPE_FILL'] })
const alpha = tokens.numVar({ name: 'opacity/btn', values: { Light: 1, Dark: 0.8 }, scopes: ['OPACITY'] })

// Scalar props (numVar)
$fig.rectangle({ name: 'Card', width: w, opacity: alpha })

// Paint color (colorVar): bind via the paint's `color` field
$fig.rectangle({ fills: [{ type: 'SOLID', color: blue }] })

// Effect color + numeric fields (mix colorVar + numVar)
$fig.frame({
  effects: [{
    type: 'DROP_SHADOW',
    color: shadowColorVar, radius: shadowRadiusVar,
    offset: { x: 0, y: 4 }, spread: 0, visible: true, blendMode: 'NORMAL',
  }],
})

// Layout grid numeric fields
$fig.frame({
  layoutGrids: [{ pattern: 'COLUMNS', sectionSize: colSizeVar, count: colCountVar,
    gutterSize: 24, alignment: 'CENTER', visible: true }],
})

// queryResult.set works too
$fig.query('FRAME[name^=Card]').set({ width: w })
```

Properties that route `FigPlanNumVar` to `setBoundVariable`: any numeric-typed bindable field — `width`, `height`, `opacity`, `topLeftRadius` / `topRightRadius` / `bottomLeftRadius` / `bottomRightRadius`, `paddingLeft` / `paddingRight` / `paddingTop` / `paddingBottom`, `itemSpacing`, `counterAxisSpacing`, `strokeWeight`, `minWidth` / `maxWidth` / `minHeight` / `maxHeight`.

`cornerRadius` is a shorthand: passing `cornerRadius: numVar` binds all four individual corner properties to that variable (there is no `boundVariables.cornerRadius` slot — Figma only exposes the per-corner bindings). Individual corner props override the shorthand when both are present.

Paint `color` fields and effect / layout-grid numeric fields are detected per-item in the array at flush time — the array itself is applied as a plain property, but any variable handle inside is bound via `setBoundVariable{ForPaint,ForEffect,ForLayoutGrid}`.

**Raw `node.set` caveat.** Same-plan variable handles (planId before `done()`) don't work reliably via raw `node.set` — use the `$fig` plan path. Handles from `$fig.getVar(id)` / `coll.getVar(nameOrId)` (real id already set) work fine with raw `node.set`.

#### Variable aliasing (semantic → primitive)

Pass a variable handle as the `values` entry of another variable to create a `VARIABLE_ALIAS`:

```js
const prims = $fig.varCollection({ name: 'Primitives', modes: ['Value'] })
const blue500 = prims.colorVar({ name: 'blue/500', values: { Value: '#3B82F6' } })

const semantic = $fig.varCollection({ name: 'Semantic', modes: ['Light', 'Dark'] })
const bgPrimary = semantic.colorVar({
  name: 'bg/primary',
  values: { Light: blue500, Dark: darkBlue500 },
})
```

### Reading / referencing existing nodes

`$fig.get(idOrKey)` accepts a real node ID (`'123:456'`) or a library `componentKey` from `search_design_system`. For an asset key, the plan queues a library import automatically — you don't need a separate `await figma.importComponentByKeyAsync(...)` step.

```js
// Wrap an existing node by ID so it can be mutated in the plan
const card = $fig.get('123:456')
$fig.set(card, { name: 'Updated Card', opacity: 0.8 })

// Wrap a library component / component set by its componentKey
const button = $fig.get(BUTTON_KEY)
$fig.instance(button, { name: 'Submit' })

// CSS-like search over the current page (or a scope node)
$fig.query('FRAME[name*=Card] TEXT').set({
  fills: [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }],
})

// Scoped search
$fig.query('TEXT', card)
```

`$fig.query(selector, scope?)` returns a result object with `.length`, `.first()`, `.last()`, `.each(fn)`, `.set(props)`, `.remove()`, and `.screenshot(opts?)`. Selector syntax matches `node.query()` (see the main SKILL — types, attributes, combinators, pseudo-classes).

### Mutating nodes

All mutate methods enqueue operations; they are applied during the auto-flush at the end of the script.

| Method | Effect |
|---|---|
| `$fig.set(target, props)` | Apply props to a plan node or existing-node wrapper |
| `$fig.delete(...nodes)` | Remove nodes (variadic) |
| `$fig.move(target, newParent, index?)` | Move a node under a new parent at `index` |
| `$fig.clone(target, props?)` | Clone a node; merges `props` over the original's opts |
| `$fig.add(parent, child)` / `$fig.append(parent, child)` | Append child to parent |
| `$fig.addAt(parent, index, child)` | Insert child at a specific index |
| `$fig.replace(oldNode, newNode)` | Swap `oldNode` with `newNode` |
| `$fig.reorder(parent, children)` | Reorder `parent`'s children to match `children` |
| `$fig.gradient(node, type, stops, transform?)` | Apply a gradient paint. `type` is `'LINEAR'` / `'RADIAL'` / `'ANGULAR'` / `'DIAMOND'` |
| `$fig.image(node, hash, scaleMode?)` | Apply an image paint by hash |

> To switch the current page during a script, use `await figma.setCurrentPageAsync(page)` directly — `$fig` doesn't expose a `setPage` because the plan flushes node creates before the switch would land, so any `$fig` ops queued after a hypothetical `setPage` would still target the page that was active at flush start. `$fig.page` (the create method) makes a new page node — different concept.

### Plan-node methods (chainable)

The object returned by every create method has its own methods that operate on that subtree:

| Method | Effect |
|---|---|
| `planNode.<create>(...)` | Any basic create method (`.frame(...)`, `.text(...)`, `.rectangle(...)`, etc.) appends as a child |
| `planNode.svg(svgStr, opts?)` / `.instance(compRef, opts?)` | Append as a child |
| `planNode.set(props)` | Apply props to this node |
| `planNode.remove()` | Delete this node |
| `planNode.clone(props?)` | Clone this node (sibling by default) |
| `planNode.moveTo(newParent, index?)` | Reparent this node |
| `planNode.reorderChildren(children)` | Reorder children of this node |
| `planNode.replace(newNode)` | Replace this node with `newNode` |
| `planNode.add(child)` / `.append(child)` / `.addAt(index, child)` | Child insertion |
| `planNode.gradient(type, stops, transform?)` / `.image(hash, scaleMode?)` | Paint shortcuts |
| `planNode.query(selector)` | Sub-query. String selectors are only valid **after materialization**; pre-materialization only function selectors (`n => ...`) work. |
| `planNode.screenshot(opts?)` | Queue a screenshot. Chainable plan-step — returns `this`, **not a Promise**. Image bytes flow through `figma.io` into the tool response at flush time. `opts` is `{ scale?, contentsOnly? }`; `contentsOnly` defaults to `false`. |
| `planNode.node` | Getter. Returns the materialized `SceneNode`, or `null` if the plan node hasn't been built yet (pre-`done()`) or the real node was deleted. Use for any `SceneNode` API not exposed as a plan step (`exportAsync`, `setRelaunchData`, `getStyledTextSegments`, etc.). |

### Inline screenshots — `planNode.screenshot(opts?)`

Plan-step screenshot. Like `set` / `add` / `move` / `gradient` / `image`, it queues an op and returns the plan node itself (`this`) — **not a Promise**. The bytes travel through the `figma.io` side channel into the tool response at flush time, so you don't need to `await` anything:

```js
// Single screenshot per node — chains naturally with set().
$fig.autoLayout({ name: 'Card', layoutMode: 'VERTICAL' })
  .set({ opacity: 0.5, cornerRadius: 12 })
  .screenshot({ scale: 2 })

// Different nodes — each shot has a distinct caption, all arrive.
$fig.rectangle({ name: 'R1', width: 60, height: 60 }).screenshot()
$fig.rectangle({ name: 'R2', width: 60, height: 60 }).screenshot()
```

`opts` is `{ scale?: number, contentsOnly?: boolean }`. `scale` defaults to `0.5` capped so the largest output dimension stays ≤ 1024 px; `contentsOnly` defaults to `false` (overlapping content included). Distinct from `node.screenshot()` (the `SceneNode` method on materialized nodes), which returns a Promise and must be `await`ed. `await rect.screenshot()` is harmless (`await` on a non-Promise resolves to the value), but misleading — nothing is being waited on, and the bytes still arrive at flush time.

Child-creation methods like `.text()` return the new child, not `this`, so they shift the chain. Stick to `.set()` / `.screenshot()` to keep chaining on the same plan node.

**Don't queue multiple `.screenshot()` calls on the same node.** `done()` processes all queued mutations before any screenshot fires (`done.ts` runs `screenshotOps` after `updates` / `reparentOps` / `gradientOps` / etc.), so every shot of the same node captures the same post-flush state — interleaving `.set().screenshot().set().screenshot()` does not give you intermediate frames. And `figma.io.write` keys output bytes by `"<name> (<W>x<H> at <x>,<y>).png`", so two shots of the same node collide on caption and the second overwrites the first in `assistantPluginFiles`. Net effect: only one PNG arrives in the response. Take one shot per node; for before/after comparisons, run two scripts or screenshot different nodes.

#### `queryResult.screenshot(opts?)` — bulk screenshots from a query

Same chainable plan-step contract as `planNode.screenshot()`, but emits one shot per matched node. Available on both `$fig.query()` and raw `node.query()` (same surface; same cap behavior).

```js
// Canonical pattern from the eval workload — set + screenshot the matches.
$fig.query('FRAME[name=Button]').set({ fills: brand }).screenshot()

// Raw plugin API works too.
figma.currentPage.query('RECTANGLE[name^=Card-]').screenshot({ scale: 2 })
```

**Capped at 5 matches by default.** Pass `{ max: N }` to raise (or lower) the cap. Over-cap **throws** rather than silently truncating, so the agent has to make a deliberate choice: filter the result, call `.first()`, or pass `max` explicitly. Examples:

```js
// Throws: "queryResult.screenshot() matched 7 nodes, which exceeds the cap of 5..."
qr.screenshot()

// Works — explicit override.
qr.screenshot({ max: 10 })

// Works — narrow first via filter.
qr.filter(n => n.opacity < 1).screenshot()
```

`opts` accepts everything `planNode.screenshot()` does (`scale`, `contentsOnly`) plus `max`. `max` is stripped before forwarding to the underlying per-node screenshot.

The same caption-collision warning above applies: each match's PNG is keyed by `<name> (<W>x<H> at <x>,<y>).png`, so matches that share name + position + size will overwrite each other in `assistantPluginFiles`. In practice this only happens for duplicates that you wouldn't really want N images of anyway.

### Reaching the real `SceneNode` — `planNode.node`

For any `SceneNode` API not surfaced as a plan step (`exportAsync`, `setBoundVariable`, `getStyledTextSegments`, etc.), reach the materialized scene node through `.node`:

```js
const rect = $fig.rectangle({ name: 'R', width: 50, height: 50 })
await $fig.done()
const png = await rect.node.exportAsync({ format: 'PNG' })
```

`.node` is a sync getter that returns `null` when the plan node hasn't been materialized yet (pre-`done()`) or when the real node was deleted. That null doubles as a materialization probe — there's no other clean way to ask "has this been built yet?":

```js
const rect = $fig.rectangle({ name: 'R', width: 50, height: 50 })
if (!rect.node) await $fig.done()                    // probe — null means not yet
const png = await rect.node?.exportAsync({ ... })    // any SceneNode method
```

`$fig.get(realId)` wraps an existing scene node and pre-populates `realNodeId` at construction, so `.node` works without `done()` for those.

### Auto-flush and `done()`

The plan is automatically materialized when your `use_figma` script finishes — you do **not** need to call `$fig.done()`. The runtime registers a shutdown action that flushes any pending plan state before the script returns. The tool result will include a `FigDoneResult` object containing the created/updated/deleted node IDs and names.

You can still call `$fig.done()` explicitly if you need to materialize partway through a script and then read real node properties (e.g. measuring `width`/`height` that depend on auto-layout). `done()` returns a promise that you need to `await`.

```js
// Usually not needed — but if you need real node state mid-script:
await $fig.done()
```

If you want a custom tool result other than `FigDoneResult`, you can use the `.id` getter on plan nodes, which will return real node IDs after `done()` has run.

### Security gating

`$fig` is only exposed in the `evals`, `assistant`, and `mcp-server` plugin runtimes. It is **not** available to regular web plugins — this is a security boundary, not a bug.

---

## Reference — figma-use — Deep Critical Rules & Worked Examples

The SKILL.md body has the terse rules. This file has the worked WRONG/RIGHT examples and edge cases. Load this when:
- You're about to write a multi-section script and want to see the full $fig builder pattern
- You hit a `Property X failed validation` error and want the validation reference
- You're doing bulk-mutation work and need the concrete 3-call template

---

### $fig — full worked examples

```js
// WRONG — verbose raw Plugin API (don't do this)
const frame = figma.createFrame()
frame.layoutMode = "VERTICAL"; frame.itemSpacing = 8
await figma.loadFontAsync({ family: "Inter", style: "Bold" })
const title = figma.createText(); title.fontName = { family: "Inter", style: "Bold" }
title.characters = "Title"; title.fontSize = 20
frame.appendChild(title)
// ...30+ lines

// RIGHT — one $fig expression (DEFAULT)
$fig.autoLayout(
  { name: 'Card', layoutMode: 'VERTICAL', itemSpacing: 8 },
  [
    $fig.text({ characters: 'Title', fontSize: 20, fontName: { family: 'Inter', style: 'Bold' } }),
    $fig.text({ characters: 'Description', fontSize: 14 }),
  ]
)
```

#### Bulk component swap — use $fig.query().each(), not findAll() + setProperties loop

```js
// WRONG — raw findAll + manual loop (no batching, no font preload, verbose)
const chevron = await figma.importComponentByKeyAsync(CHEVRON_KEY)
const instances = figma.root.findAll(n => n.type === 'INSTANCE' && n.name === 'arrow_drop_down')
for (const inst of instances) {
  inst.setProperties({ [swapKey]: chevron.id })  // verbose, hits per-node overhead
}

// RIGHT — $fig.query batched + asset-key direct from `search_design_system`
// CHEVRON_KEY here is the `componentKey` field returned by search_design_system.
// $fig.get queues the library import in the plan; no separate await needed.
const chevron = $fig.get(CHEVRON_KEY)
$fig.query('INSTANCE[name=arrow_drop_down]').each(inst => {
  $fig.set(inst, { mainComponent: chevron })  // batched into plan; auto-materialized at script end
})
```

#### Bulk variable creation — loop with `$fig.set`

```js
// WRONG — raw figma.variables.createVariable() per variable, 4 lines × 100 = 400 lines
const coll = figma.variables.createVariableCollection('FX Colors')
const v1 = figma.variables.createVariable('blue/10', coll.id, 'COLOR')
v1.setValueForMode(coll.modes[0].modeId, { r: 0.1, g: 0.3, b: 0.9 })
// ...repeat 100x

// RIGHT — loop in a single script
const coll = figma.variables.createVariableCollection('FX Colors')
const modeId = coll.modes[0].modeId
for (const { name, color } of FX_COLORS) {
  const v = figma.variables.createVariable(name, coll.id, 'COLOR')
  v.setValueForMode(modeId, color)
}
// no per-call $fig overhead because variables aren't SceneNodes
```

#### When NOT to use $fig
Mid-script reading real `SceneNode` state, or operations on non-SceneNode types (Variables, Components themselves). For those, raw Plugin API in a single `use_figma` call is correct.

Note: "I need a library component" alone is **not** a reason to leave `$fig`. Pass the `componentKey` from `search_design_system` straight into `$fig.get(...)` / `$fig.instance(...)` — same for style `key` (`$fig.getStyle`) and variable `key` (`$fig.getVar`). For component sets, pass variant property values in `props` and `$fig.instance` resolves the matching variant via `setProperties` — you do not need to import the set and drill into `compSet.children`.

---

### Variants via data, not enumeration

When the task asks for N parallel things ("build 3 styles", "create 4 button states", "5 color swatches"):

1. Define varying parts as a JS array of objects.
2. Define a single builder function that takes one object → one output.
3. Loop: `VARIANTS.forEach((v, i) => build(v, i))` or `VARIANTS.map(build)`.

The expensive way is writing N separate procedural blocks — that requires reasoning through each variant independently in thinking (1–3KB per variant). The data-array pattern compresses that to one builder + one array literal.

Each KB of pre-mutation thinking costs ~$0.02–0.04. Replacing 15KB of "Style 1 has blue accents... Style 2 has warm orange tones..." with `const STYLES = [{...}, {...}, {...}]; STYLES.forEach(build)` saves ~$0.30 on a typical multi-variant task.

---

### Color validation — WRONG vs RIGHT

```js
// WRONG — these all throw "fills: Property color.r failed validation: Required value missing"
fills = [{ type: 'SOLID', color: { hex: '#ff0000' } }]           // ❌ no hex shorthand
fills = [{ type: 'SOLID', color: '#ff0000' }]                    // ❌ color must be object
fills = [{ type: 'SOLID', color: { r: 1 } }]                     // ❌ missing g, b
fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0, a: 0.5 } }] // ❌ no `a` in color

// RIGHT — full RGB + opacity outside color
fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 }, opacity: 0.5 }]
```

Helper at top of script:
```js
const hex = h => { const n = parseInt(h.replace('#',''), 16); return { r: ((n>>16)&255)/255, g: ((n>>8)&255)/255, b: (n&255)/255 } }
// then: color: hex('#2563eb')
```

---

### Gradient paints — all fields required

```js
const grad = {
  type: 'GRADIENT_LINEAR',
  gradientStops: [
    { position: 0, color: { r: 0, g: 0, b: 0, a: 1 } },
    { position: 1, color: { r: 1, g: 1, b: 1, a: 1 } },
  ],
  gradientTransform: [[1, 0, 0], [0, 1, 0]],  // identity = top-to-bottom
}
frame.fills = [grad]
```

Omitting any of `type`, `gradientStops`, or `gradientTransform` throws `Property "gradientTransform" failed validation: Required value missing`.

---

### Node-type property gotchas (full list)

Touching a property that doesn't exist on a node's type throws `TypeError: node.foo: no such property 'foo' on TYPE node`. Each throw burns a retry.

- **Only `FRAME` / `COMPONENT` / `COMPONENT_SET` / `INSTANCE` / `GROUP` / `SECTION` / `PAGE` have `.children`.** `RECTANGLE`, `TEXT`, `ELLIPSE`, `POLYGON`, `STAR`, `VECTOR`, `LINE`, `SLICE`, `STICKY`, `SHAPE_WITH_TEXT`, `STAMP`, `CONNECTOR`, `TABLE`, `WIDGET`, `EMBED`, `MEDIA` do NOT.
- **`GROUP` has NO `fills` / `strokes` / `cornerRadius`.** Apply paints/radii on the child shapes inside.
- **`TEXT` has NO `cornerRadius`, `paddingLeft/Right/Top/Bottom`, `itemSpacing`, `layoutMode`, `layoutSizingHorizontal/Vertical`** (those are container properties). Text has font / size / decoration / fills.
- **`INSTANCE` descendants are read-only for structural ops** — you cannot `appendChild` / `insertChild` into an instance child. Edit the source `COMPONENT` or detach first.
- **`layoutPositioning = 'ABSOLUTE'` requires the parent to have `layoutMode !== 'NONE'`.** Setting ABSOLUTE under a plain frame / page throws.
- **`layoutSizingHorizontal/Vertical = 'FILL'` requires parent with auto-layout.** Either set parent's `layoutMode` first, or use explicit `resize(w, h)`.
- **`counterAxisAlignItems` is an enum**: only `'MIN' | 'CENTER' | 'MAX' | 'BASELINE'`. `'STRETCH'` / `'SPACE_BETWEEN'` fail. `primaryAxisAlignItems` has different valid values — don't confuse.
- **There is NO `instance.swapMainComponent(...)`.** Use `instance.setProperties({...})` with the component-property variant value, OR `$fig.query(...).set({componentProperties: {...}})`. There IS `instance.swapComponent(component)` (different method name).

Before referencing any property: (a) check `'<prop>' in node`, (b) gate by `if (node.type === 'FRAME' || ...)`, or (c) consult Plugin API type reference (load `readPowerSteering("figma", "figma-use-api.md")`).

---

### Bulk-mutation stopping rule (full template)

A bulk-mutation task (swap N icons, update M colors, replace K instances) is COMPLETE in **3 `use_figma` calls**:

1. **Call 1 — DISCOVER + MUTATE in one script.** Combine: find targets via `figma.root.findAll`, import components, mutate. Use `$fig.query(...).each(...)` for the loop. Return the count.

2. **Call 2 — VERIFY (optional).** Read-only `findAll` to count remaining targets. Skip if Call 1's return showed full coverage.

3. **Call 3 — FINAL REPORT in assistant text, no tool call.** State what was swapped + any remaining edges. STOP.

NO 4th call. NO chasing the last 20% of edge cases. If Call 1 errors, fix and redo — that's still your one mutation call. Cap: 2 mutation attempts + 1 verify.

#### Concrete arrow→chevron template:
```js
// Call 1: discover + mutate, all in one script. CHEVRON_FWD_KEY / CHEVRON_BWD_KEY
// are componentKeys from search_design_system — $fig queues the library import.
const chevronFwd = $fig.get(CHEVRON_FWD_KEY)
const chevronBwd = $fig.get(CHEVRON_BWD_KEY)
let swapped = 0
$fig.query('INSTANCE[name*=arrow_forward], INSTANCE[name*=arrow_right], INSTANCE[name*=arrow_drop_down]')
  .each(inst => { $fig.set(inst, { mainComponent: chevronFwd }); swapped++ })
$fig.query('INSTANCE[name*=arrow_back], INSTANCE[name*=arrow_left], INSTANCE[name*=arrow_drop_up]')
  .each(inst => { $fig.set(inst, { mainComponent: chevronBwd }); swapped++ })
return { swapped }
```

Observed worst case before this rule: 35 `use_figma` calls chasing the same 2-3 nested arrows for 25+ minutes. With 3-call max, worst-case cost is bounded.

---

### Cross-page bulk operations — one query, all pages

```js
// RIGHT — one query, all pages, all instances
await Promise.all(figma.root.children.map(p => figma.loadAllPagesAsync ? null : figma.setCurrentPageAsync(p)))  // ensure pages loaded
const instances = figma.root.findAll(n => n.type === 'INSTANCE' && n.name === 'arrow_drop_down')
// OR — using $fig.query (preferred):
$fig.query('INSTANCE[name=arrow_drop_down]', figma.root)
```

NOT: "Explore page 1", "Explore page 2"... each costs ~30s + thinking tax. One `findAll` from `figma.root` searches the entire document in one call.

---

### "An unexpected error occurred" handling

When `use_figma` returns exactly `"An unexpected error occurred. Figma Debug UUID: <uuid>"` (no JS stack), the request hit a server-side path error. Do NOT retry the same script unchanged — that has near-zero success probability.

Change approach: break into smaller batches, switch from `$fig.query(...).set(...)` to per-node `node.set(...)` (or vice versa), pick a tighter selector, or drop one node-property to isolate which triggers the server error. If the same shape recurs after 2 different attempts, stop and report.

---

### Common JS syntax bugs to avoid before submitting >5KB scripts

- **Unbalanced braces in template literals** — `${{...}}` or missing `}` in multi-line strings throws `SyntaxError: expecting '}'`.
- **Trailing commas in function calls** — `foo(a, b,)` may fail in some JS engines.
- **Missing `await`** before async ops — `figma.loadFontAsync(...)` without `await` is a silent bug.
- **`=` vs `==`** inside object literals — `{ size: =14 }` should be `{ size: 14 }`.

SyntaxError costs a full retry ($0.10–0.20). Scan visually before submitting large scripts.

---

### Why decisiveness matters (cost breakdown)

Each KB of upfront thinking ≈ $0.02–0.04. A 20KB upfront plan = ~$0.30–$0.80 spent before any tool call.

For multi-section tasks: decide high-level approach in <2KB, write the FIRST section's script, then plan the second once you've seen the first work. Plan-as-you-build is materially cheaper than plan-then-build-all.

---

### Workflow — incremental + recovery

- Break large ops into multiple `use_figma` calls; validate after each *logical phase* (not every micro-step).
- On error: read the message carefully, identify which property/type triggered it, fix once, retry. Don't blindly resubmit.
- On 3 retries of same error: switch approach (most often: switch to `$fig`).
- Cap script size around 8 KB / ~250 lines. Larger → split by section.

---

## Reference — Plugin API Index

> Full typings: `plugin-api-standalone.d.ts` (11,292 lines)
> Grep by symbol name to jump to definition. All `L#` line numbers refer to that file.

---

### figma.\* — PluginAPI (L24)

#### Identity & State

| Member                          | Type                                                                             |
| ------------------------------- | -------------------------------------------------------------------------------- |
| `apiVersion`                    | `'1.0.0'`                                                                        |
| `editorType`                    | `'figma' \| 'figjam' \| 'dev' \| 'slides' \| 'buzz'`                             |
| `mode`                          | `'default' \| 'textreview' \| 'inspect' \| 'codegen' \| 'linkpreview' \| 'auth'` |
| `fileKey`                       | `string \| undefined`                                                            |
| `root`                          | `DocumentNode`                                                                   |
| `currentPage`                   | `PageNode` — **read-only**; sync setter `figma.currentPage = page` does NOT work and throws; use `await figma.setCurrentPageAsync(page)` instead |
| `currentUser`                   | `User \| null`                                                                   |
| `mixed`                         | `unique symbol` — sentinel for mixed values in selection                         |
| `skipInvisibleInstanceChildren` | `boolean`                                                                        |

#### Navigation & Lookup

| Method                      | Returns                                                 |
| --------------------------- | ------------------------------------------------------- |
| `setCurrentPageAsync(page)` | `Promise<void>` — **MUST use this**; sync setter `figma.currentPage = page` does NOT work |
| `getNodeByIdAsync(id)`      | `Promise<BaseNode \| null>`                             |
| `getNodeById(id)`           | `BaseNode \| null`                                      |
| `getStyleByIdAsync(id)`     | `Promise<BaseStyle \| null>`                            |
| `getStyleById(id)`          | `BaseStyle \| null`                                     |

#### Create Nodes

| Method                              | Returns                     |
| ----------------------------------- | --------------------------- |
| `createFrame()`                     | `FrameNode`                 |
| `createAutoLayout(direction?)`      | `FrameNode`                 |
| `createComponent()`                 | `ComponentNode`             |
| `createComponentFromNode(node)`     | `ComponentNode`             |
| `createRectangle()`                 | `RectangleNode`             |
| `createEllipse()`                   | `EllipseNode`               |
| `createLine()`                      | `LineNode`                  |
| `createPolygon()`                   | `PolygonNode`               |
| `createStar()`                      | `StarNode`                  |
| `createVector()`                    | `VectorNode`                |
| `createText()`                      | `TextNode`                  |
| `createSection()`                   | `SectionNode`               |
| `createPage()`                      | `PageNode`                  |
| `createSlice()`                     | `SliceNode`                 |
| `createBooleanOperation()`          | `BooleanOperationNode`      |
| `createTable(rows?, cols?)`         | `TableNode`                 |
| `createImage(data: Uint8Array)`     | `Image`                     |
| `createNodeFromSvg(svg)`            | `FrameNode`                 |
| `createNodeFromJSXAsync(jsx)`       | `Promise<SceneNode>`        |
| `importComponentByKeyAsync(key)`    | `Promise<ComponentNode>`    |
| `importComponentSetByKeyAsync(key)` | `Promise<ComponentSetNode>` |
| `importStyleByKeyAsync(key)`        | `Promise<BaseStyle>`        |

#### Styles (Local)

| Method                             | Returns         |
| ---------------------------------- | --------------- |
| `createPaintStyle()`               | `PaintStyle`    |
| `createTextStyle()`                | `TextStyle`     |
| `createEffectStyle()`              | `EffectStyle`   |
| `createGridStyle()`                | `GridStyle`     |
| `getLocalPaintStyles()` / `Async`  | `PaintStyle[]`  |
| `getLocalTextStyles()` / `Async`   | `TextStyle[]`   |
| `getLocalEffectStyles()` / `Async` | `EffectStyle[]` |
| `getLocalGridStyles()` / `Async`   | `GridStyle[]`   |

#### Fonts

| Method                      | Notes                              |
| --------------------------- | ---------------------------------- |
| `loadFontAsync(fontName)`   | **MUST call before any text edit** |
| `listAvailableFontsAsync()` | `Promise<Font[]>`                  |
| `hasMissingFont`            | `boolean`                          |

#### Plugin Lifecycle

| Method                                  | Notes                                                        |
| --------------------------------------- | ------------------------------------------------------------ |
| `closePlugin(message?)`                 | Auto-called; use `return` instead to pass results back       |
| `closePluginWithFailure(message?)`      | Auto-called on errors; do not call manually                  |
| `commitUndo()`                          | Snapshot to undo history                                     |
| `triggerUndo()`                         | Revert to last snapshot                                      |
| `saveVersionHistoryAsync(title, desc?)` | `Promise<VersionHistoryResult>`                              |
| `notify(message, options?)`             | **throws "not implemented" in use_figma — do not use** |
| `openExternal(url)`                     | Opens URL in browser                                         |

#### Sub-APIs (properties on figma)

| Property              | Interface                | L#    |
| --------------------- | ------------------------ | ----- |
| `figma.variables`     | `VariablesAPI`           | L2016 |
| `figma.ui`            | `UIAPI`                  | L2604 |
| `figma.util`          | `UtilAPI`                | L2691 |
| `figma.constants`     | `ConstantsAPI`           | L2809 |
| `figma.clientStorage` | `ClientStorageAPI`       | L2531 |
| `figma.viewport`      | `ViewportAPI`            | L3086 |
| `figma.parameters`    | `ParametersAPI`          | L3292 |
| `figma.teamLibrary`   | `TeamLibraryAPI`         | L2372 |
| `figma.annotations`   | `AnnotationsAPI`         | L2187 |
| `figma.codegen`       | `CodegenAPI`             | L2871 |
| `figma.textreview?`   | `TextReviewAPI`          | L3166 |
| `figma.payments?`     | `PaymentsAPI`            | L2420 |
| `figma.buzz`          | `BuzzAPI`                | L2211 |
| `figma.timer?`        | `TimerAPI` (FigJam only) | L3053 |

---

### VariablesAPI — figma.variables (L2016)

```
getVariableByIdAsync(id)                 Promise<Variable | null>    ← preferred; sync deprecated
getVariableCollectionByIdAsync(id)       Promise<VariableCollection | null>    ← preferred; sync deprecated
getLocalVariablesAsync(type?)            Promise<Variable[]>         ← preferred; filter by VariableResolvedDataType; sync deprecated
getLocalVariableCollectionsAsync()       Promise<VariableCollection[]>    ← preferred; sync deprecated
createVariable(name, collection, type)   Variable
createVariableCollection(name)           VariableCollection
createVariableAlias(variable)            VariableAlias
importVariableByKeyAsync(key)            Promise<Variable>
setBoundVariableForPaint(paint, field, variable)    → returns NEW paint — reassign
setBoundVariableForEffect(effect, field, variable)  → returns NEW effect — reassign
setBoundVariableForLayoutGrid(grid, field, variable)
```

**Variable (L10204):** `name`, `resolvedType`, `codeSyntax`, `scopes`, `hiddenFromPublishing`, `valuesByMode`, `variableCollectionId`

- `setVariableCodeSyntax(platform, value)` — platform: `'WEB' | 'ANDROID' | 'iOS'`
- `setValueForMode(collectionId, modeId, value)`
- `remove()`

**VariableCollection (L10418):** `name`, `modes`, `variableIds`, `defaultModeId`, `hiddenFromPublishing`

- `addMode(name)` → `modeId`; `removeMode(modeId)`; `renameMode(modeId, name)`

---

### Node Types

#### Concrete Scene Nodes

| Node                   | L#     | Key characteristics                                |
| ---------------------- | ------ | -------------------------------------------------- |
| `DocumentNode`         | L8960  | Root; `children: PageNode[]`                       |
| `PageNode`             | L9119  | `children`, local styles, `backgrounds`            |
| `FrameNode`            | L9311  | `DefaultFrameMixin` — auto-layout, clips, children |
| `GroupNode`            | L9321  | Children only, no auto-layout                      |
| `ComponentNode`        | L9678  | Like Frame + publishable                           |
| `ComponentSetNode`     | L9653  | Variant set container                              |
| `InstanceNode`         | L9719  | Like Frame; `mainComponent`, `detach()`            |
| `RectangleNode`        | L9378  | `DefaultShapeMixin` + corners                      |
| `EllipseNode`          | L9410  | + `arcData`                                        |
| `LineNode`             | L9396  |                                                    |
| `PolygonNode`          | L9430  |                                                    |
| `StarNode`             | L9450  |                                                    |
| `VectorNode`           | L9476  | Vector paths                                       |
| `TextNode`             | L9493  | Rich text, fonts, segments                         |
| `TextPathNode`         | L9564  | Text along path                                    |
| `BooleanOperationNode` | L9792  | `booleanOperation` property                        |
| `SliceNode`            | L9368  | Export only                                        |
| `SectionNode`          | L10754 | Grouping + fills                                   |
| `TableNode`            | L9862  | `TableCellNode` children                           |

**FigJam only:** `StickyNode` L9812, `ConnectorNode` L10121, `ShapeWithTextNode` L9999, `StampNode` L9838, `CodeBlockNode` L10080, `EmbedNode` L10661, `LinkUnfurlNode` L10701, `MediaNode` L10721

**Slides only:** `SlideNode` L10784, `SlideRowNode` L10809, `SlideGridNode` L10822

**Union types:**

```
type SceneNode  (L10917) = FrameNode | GroupNode | SliceNode | RectangleNode | LineNode
  | EllipseNode | PolygonNode | StarNode | VectorNode | TextNode | ComponentSetNode
  | ComponentNode | InstanceNode | BooleanOperationNode | SectionNode | ...
type BaseNode   (L10913) = DocumentNode | PageNode | SceneNode
```

---

### Mixin Interfaces

| Mixin                        | L#    | Provides                                                                                        |
| ---------------------------- | ----- | ----------------------------------------------------------------------------------------------- |
| `BaseNodeMixin`              | L5284 | `id`, `name`, `type`, `parent`, `remove()`, plugin data                                         |
| `SceneNodeMixin`             | L5561 | `visible`, `locked`, `opacity`, variable bindings                                               |
| `ChildrenMixin`              | L5773 | `children`, `appendChild()`, `insertChild()`, `findAll()`, `findOne()`, `findAllWithCriteria()` |
| `LayoutMixin`                | L6135 | `x`, `y`, `width`, `height`, `rotation`, `resize()`, `rescale()`                                |
| `AutoLayoutMixin`            | L6436 | `layoutMode`, axis alignment, padding, `itemSpacing`, `layoutSizingHorizontal/Vertical`         |
| `AutoLayoutChildrenMixin`    | L7064 | `layoutAlign`, `layoutGrow`, sizing — **set AFTER `appendChild()`**                             |
| `GridLayoutMixin`            | L6939 | CSS Grid tracks, gap, template                                                                  |
| `GridChildrenMixin`          | L7127 | grid child positioning                                                                          |
| `GeometryMixin`              | L7485 | `fills`, `strokes`, `strokeWeight`, `strokeAlign`                                               |
| `MinimalFillsMixin`          | L7328 | `fills` only                                                                                    |
| `MinimalStrokesMixin`        | L7246 | `strokes`, `strokeWeight`                                                                       |
| `BlendMixin`                 | L6339 | `opacity`, `blendMode`, `isMask`, `effects`                                                     |
| `CornerMixin`                | L7537 | `cornerRadius`, `cornerSmoothing`                                                               |
| `RectangleCornerMixin`       | L7560 | Per-corner radii                                                                                |
| `ExportMixin`                | L7577 | `exportSettings`, `exportAsync()`                                                               |
| `ReactionMixin`              | L7704 | `reactions` (prototyping)                                                                       |
| `PublishableMixin`           | L7875 | `description`, `key`, `getPublishStatusAsync()`                                                 |
| `VariantMixin`               | L8182 | `variantProperties`                                                                             |
| `ComponentPropertiesMixin`   | L8229 | `componentProperties`, `addComponentProperty()`                                                 |
| `PluginDataMixin`            | L5443 | `getSharedPluginData()`, `setSharedPluginData()` supported; `getPluginData()`, `setPluginData()` **NOT supported** |
| `FramePrototypingMixin`      | L7651 | `overflowDirection`, `numberOfFixedChildren`                                                    |
| `BaseFrameMixin`             | L7939 | ChildrenMixin + LayoutMixin + AutoLayoutMixin + GeometryMixin + …                               |
| `DefaultFrameMixin`          | L7997 | BaseFrameMixin + FramePrototypingMixin + ReactionMixin                                          |
| `DefaultShapeMixin`          | L7928 | BlendMixin + GeometryMixin + LayoutMixin + ExportMixin + ReactionMixin                          |
| `ExplicitVariableModesMixin` | L9084 | `setExplicitVariableModeForCollection()`                                                        |

---

### Paint & Fill (L4302)

| Type            | L#    | Notes                                                                             |
| --------------- | ----- | --------------------------------------------------------------------------------- |
| `SolidPaint`    | L4302 | `type:'SOLID'`, `color: RGB`, `opacity`, `visible`, `blendMode`                   |
| `GradientPaint` | L4357 | `type: 'GRADIENT_LINEAR\|RADIAL\|ANGULAR\|DIAMOND'`, `gradientStops: ColorStop[]` |
| `ImagePaint`    | L4377 | `type:'IMAGE'`, `imageHash`, `scaleMode`                                          |
| `VideoPaint`    | L4413 | `type:'VIDEO'`                                                                    |
| `PatternPaint`  | L4449 | `type:'PATTERN'`                                                                  |
| `type Paint`    | L4481 | Union of all five                                                                 |
| `ColorStop`     | L4271 | `{ position: number, color: RGBA }`                                               |
| `ImageFilters`  | L4290 | exposure, contrast, saturation, etc.                                              |

> **CRITICAL**: Fills/strokes are **read-only arrays** — clone, modify, reassign.

---

### Effects (L3966)

| Type                               | L#    |
| ---------------------------------- | ----- |
| `DropShadowEffect`                 | L3966 |
| `InnerShadowEffect`                | L4009 |
| `BlurEffect` (Normal/Progressive)  | L4048 |
| `NoiseEffect` (Mono/Duo/Multitone) | L4105 |
| `TextureEffect`                    | L4180 |
| `GlassEffect`                      | L4209 |
| `type Effect`                      | L4250 |

---

### Typography

| Type                | L#    | Notes                                                                                  |
| ------------------- | ----- | -------------------------------------------------------------------------------------- |
| `FontName`          | L3697 | `{ family: string, style: string }`                                                    |
| `TextNode`          | L9493 | `characters`, `textAlignHorizontal`, `fontSize`, `fontName`, `getStyledTextSegments()` |
| `StyledTextSegment` | L4882 | Per-range text properties                                                              |
| `LetterSpacing`     | L4826 | `{ value, unit: 'PIXELS'\|'PERCENT' }`                                                 |
| `LineHeight`        | L4830 | `{ value, unit } \| { unit: 'AUTO' }`                                                  |
| `TextCase`          | L3701 | `'ORIGINAL'\|'UPPER'\|'LOWER'\|'TITLE'\|'SMALL_CAPS'`                                  |
| `TextDecoration`    | L3702 | `'NONE'\|'UNDERLINE'\|'STRIKETHROUGH'`                                                 |
| `OpenTypeFeature`   | L3728 | Ligatures, numerals, etc.                                                              |

---

### Variables & Bindings

| Type                          | L#     | Notes                                                         |
| ----------------------------- | ------ | ------------------------------------------------------------- |
| `Variable`                    | L10204 | Core variable object                                          |
| `VariableCollection`          | L10418 | Collection of variables + modes                               |
| `VariableAlias`               | L10172 | Reference to another variable                                 |
| `VariableValue`               | L10176 | `boolean \| string \| number \| RGB \| RGBA \| VariableAlias` |
| `VariableResolvedDataType`    | L10171 | `'BOOLEAN' \| 'COLOR' \| 'FLOAT' \| 'STRING'`                 |
| `VariableDataType`            | L5023  | Includes `'VARIABLE_ALIAS' \| 'EXPRESSION'`                   |
| `VariableScope`               | L10177 | Where variable can be applied                                 |
| `CodeSyntaxPlatform`          | L10203 | `'WEB' \| 'ANDROID' \| 'iOS'`                                 |
| `VariableBindableNodeField`   | L5712  | Node fields that accept variable binding                      |
| `VariableBindableTextField`   | L5739  | Text-specific bindable fields                                 |
| `VariableBindablePaintField`  | L5748  | `'color'`                                                     |
| `VariableBindableEffectField` | L5751  | `'color'\|'radius'\|'spread'\|'offsetX'\|'offsetY'`           |

---

### Styles

| Interface        | L#     | Notes                                                  |
| ---------------- | ------ | ------------------------------------------------------ |
| `BaseStyleMixin` | L10977 | `name`, `id`, `key`, `type`, `description`, `remove()` |
| `PaintStyle`     | L11002 | `type:'PAINT'`, `paints: Paint[]`                      |
| `TextStyle`      | L11018 | `type:'TEXT'`, font properties                         |
| `EffectStyle`    | L11087 | `type:'EFFECT'`, `effects: Effect[]`                   |
| `GridStyle`      | L11103 | `type:'GRID'`, `layoutGrids`                           |
| `type BaseStyle` | L11119 | Union of all four                                      |
| `type StyleType` | L10955 | `'PAINT' \| 'TEXT' \| 'EFFECT' \| 'GRID'`              |

---

### Primitives & Geometry

| Type             | L#    | Shape                                         |
| ---------------- | ----- | --------------------------------------------- |
| `Vector`         | L3667 | `{ x: number, y: number }`                    |
| `Rect`           | L3671 | `{ x, y, width, height }`                     |
| `RGB`            | L3680 | `{ r, g, b }` — **0–1 range, not 0–255**      |
| `RGBA`           | L3688 | `{ r, g, b, a }` — **0–1 range**              |
| `Transform`      | L3666 | `[[a,b,tx],[c,d,ty]]` 2×3 affine matrix       |
| `ArcData`        | L3958 | `{ startingAngle, endingAngle, innerRadius }` |
| `Constraints`    | L4264 | `{ horizontal, vertical }: ConstraintType`    |
| `ConstraintType` | L4260 | `'MIN'\|'CENTER'\|'MAX'\|'STRETCH'\|'SCALE'`  |
| `VectorPath`     | L4792 | `{ windingRule, data: string }`               |
| `VectorNetwork`  | L4775 | vertices + segments + regions                 |
| `Guide`          | L4482 | `{ axis, offset }`                            |

---

### Prototyping

| Type                  | L#    | Notes                                                     |
| --------------------- | ----- | --------------------------------------------------------- |
| `Reaction`            | L5015 | trigger + action pair                                     |
| `Trigger`             | L5146 | what initiates the reaction                               |
| `Action`              | L5064 | what happens                                              |
| `Transition`          | L5145 | `SimpleTransition \| DirectionalTransition`               |
| `Easing`              | L5182 | easing curve definition                                   |
| `Navigation`          | L5178 | `'NAVIGATE'\|'SWAP'\|'OVERLAY'\|'SCROLL_TO'\|'CHANGE_TO'` |
| `OverflowDirection`   | L5215 | `'NONE'\|'HORIZONTAL'\|'VERTICAL'\|'BOTH'`                |
| `OverlayPositionType` | L5219 | overlay placement                                         |

---

### Events & Changes

| Type                  | L#    | Notes                                                           |
| --------------------- | ----- | --------------------------------------------------------------- |
| `ArgFreeEventType`    | L11   | `'selectionchange'\|'currentpagechange'\|'close'\|timer events` |
| `RunEvent`            | L3321 | plugin run with parameters                                      |
| `DropEvent`           | L3339 | drag-and-drop                                                   |
| `DocumentChangeEvent` | L3359 | any document change                                             |
| `NodeChangeEvent`     | L3626 | node property changes                                           |
| `NodeChangeProperty`  | L3499 | all watchable property names                                    |
| `StyleChangeEvent`    | L3365 | style create/delete/update                                      |
| `DocumentChange`      | L3489 | `CreateChange \| DeleteChange \| PropertyChange`                |
| `TextReviewEvent`     | L3657 | text review mode                                                |

---

### Export

| Type                        | L#    | Notes                                         |
| --------------------------- | ----- | --------------------------------------------- |
| `ExportSettingsImage`       | L4561 | PNG/JPG/WEBP/BMP                              |
| `ExportSettingsSVG`         | L4634 |                                               |
| `ExportSettingsPDF`         | L4653 |                                               |
| `ExportSettingsREST`        | L4667 |                                               |
| `ExportSettingsConstraints` | L4554 | `{ type: 'SCALE'\|'WIDTH'\|'HEIGHT', value }` |

---

### Key Sub-API Surfaces

**ClientStorageAPI (L2531):** `getAsync(key)`, `setAsync(key, value)`, `keysAsync()`, `deleteAsync(key)`

**ViewportAPI (L3086):** `center: Vector`, `zoom: number`, `scrollAndZoomIntoView(nodes)`, `bounds: Rect`

**UtilAPI (L2691):** `solidPaint(hex, opacity?)`, `rgba(r,g,b,a?)`, `rgb(r,g,b)`, `colorToHex(color)`, `loadImageAsync(url)`, `clone(val)`

**TeamLibraryAPI (L2372):** `getAvailableLibraryVariableCollectionsAsync()`, `importVariableByKeyAsync(key)`

**Image (L11120):** `hash`, `getBytesAsync()`, `getSizeAsync()`

---

### All Symbols (flat — grep these against the .d.ts file)

To find any symbol: `grep -n "^interface Foo\|^type Foo\|^declare type Foo" plugin-api-standalone.d.ts`

```
PluginAPI               VariablesAPI            AnnotationsAPI          TeamLibraryAPI
UIAPI                   UtilAPI                 ViewportAPI             ClientStorageAPI
ConstantsAPI            CodegenAPI              PaymentsAPI             TextReviewAPI
ParametersAPI           TimerAPI                BuzzAPI                 DevResourcesAPI

DocumentNode            PageNode                FrameNode               GroupNode
ComponentNode           ComponentSetNode        InstanceNode            RectangleNode
EllipseNode             LineNode                PolygonNode             StarNode
VectorNode              TextNode                TextPathNode            BooleanOperationNode
SliceNode               SectionNode             TableNode               TableCellNode
StickyNode              ConnectorNode           ShapeWithTextNode       StampNode
CodeBlockNode           EmbedNode               LinkUnfurlNode          MediaNode
WidgetNode              SlideNode               SlideRowNode            SlideGridNode
TransformGroupNode      HighlightNode           WashiTapeNode

BaseNodeMixin           SceneNodeMixin          ChildrenMixin           LayoutMixin
AutoLayoutMixin         AutoLayoutChildrenMixin GridLayoutMixin         GridChildrenMixin
GeometryMixin           MinimalFillsMixin       MinimalStrokesMixin     BlendMixin
MinimalBlendMixin       CornerMixin             RectangleCornerMixin    ExportMixin
ReactionMixin           PublishableMixin        VariantMixin            ComponentPropertiesMixin
PluginDataMixin         DevResourcesMixin       DevStatusMixin          StickableMixin
ConstraintMixin         DimensionAndPositionMixin AspectRatioLockMixin  FramePrototypingMixin
BaseFrameMixin          DefaultFrameMixin       DefaultShapeMixin       OpaqueNodeMixin
VectorLikeMixin         ComplexStrokesMixin     IndividualStrokesMixin  ContainerMixin
AnnotationsMixin        MeasurementsMixin       ExplicitVariableModesMixin

Variable                VariableCollection      VariableAlias           ExtendedVariableCollection
LibraryVariableCollection LibraryVariable
VariableValue           VariableResolvedDataType VariableDataType       VariableScope
CodeSyntaxPlatform      VariableBindableNodeField VariableBindableTextField
VariableBindablePaintField VariableBindableEffectField VariableBindableLayoutGridField

SolidPaint              GradientPaint           ImagePaint              VideoPaint
PatternPaint            Paint                   ColorStop               ImageFilters
DropShadowEffect        InnerShadowEffect       BlurEffect              NoiseEffect
TextureEffect           GlassEffect             Effect
LayoutGrid              RowsColsLayoutGrid      GridLayoutGrid

PaintStyle              TextStyle               EffectStyle             GridStyle
BaseStyle               BaseStyleMixin          StyleType

FontName                Font                    LetterSpacing           LineHeight
TextCase                TextDecoration          TextDecorationStyle     FontStyle
OpenTypeFeature         StyledTextSegment       LeadingTrim

Vector                  Rect                    RGB                     RGBA
Transform               ArcData                 Constraints             ConstraintType
VectorPath              VectorNetwork           VectorVertex            VectorSegment
VectorRegion            Guide                   BlendMode               MaskType

Reaction                Trigger                 Action                  Transition
Easing                  Navigation              OverflowDirection       OverlayPositionType
OverlayBackground       PublishStatus

ArgFreeEventType        RunEvent                DropEvent               DocumentChangeEvent
NodeChangeEvent         NodeChangeProperty      StyleChangeEvent        DocumentChange
TextReviewEvent         SlidesViewChangeEvent   CanvasViewChangeEvent

ExportSettingsImage     ExportSettingsSVG       ExportSettingsPDF       ExportSettingsREST
ExportSettingsConstraints

User                    ActiveUser              BaseUser                Image
Video                   VersionHistoryResult    FindAllCriteria

FigAPI                  FigDoneResult           FigQueryResult          FigPlanNode
FigPlanStyle            FigPlanPaintStyle       FigPlanTextStyle        FigPlanEffectStyle
FigPlanGridStyle        FigPlanVarCollection    FigPlanVariable
FigPlanColorVar         FigPlanNumVar           FigPlanBoolVar          FigPlanStringVar
GradientStop
```

---

### Additional APIs (available via use_figma)

#### Node Methods

| Method / Property             | Returns / Type    | Description |
| ----------------------------- | ----------------- | ----------- |
| `node.query(selector)`        | `QueryResult`     | CSS-like selector search within subtree |
| `node.matches(selector)`      | `boolean`         | Test if node matches a selector |
| `node.set(props)`             | `this`            | Set multiple properties at once, chainable |
| `await node.screenshot(opts?)` | `Promise<void>`  | Capture PNG inline in tool response |
| `node.placeholder`            | `boolean`         | Show/hide shimmer overlay |

#### figma.io Namespace

| Method                        | Returns           | Description |
| ----------------------------- | ----------------- | ----------- |
| `figma.io.write(path, data)`  | `void`            | Write image/data to be returned in tool response |

#### `$fig` Builder API

Plan-based builder — see [`$fig` Builder API](#reference--fig-builder-api) for details.

| Method | Returns | Description |
|---|---|---|
| `$fig.frame` / `.rectangle` / `.ellipse` / `.polygon` / `.star` / `.line` / `.vector` / `.text` / `.section` / `.component` / `.page` / `.slice` | `FigPlanNode` | Create a plan node of the given type: `(opts?, children?)` |
| `$fig.autoLayout(opts?, children?)` | `FigPlanNode` | `FRAME` with auto-layout pre-configured (both axes hugging content). Default direction `HORIZONTAL`; pass `layoutMode: 'VERTICAL'` in opts to switch. |
| `$fig.svg(svgString, opts?)`  | `FigPlanNode` | Create a node tree from SVG |
| `$fig.instance(compRef, opts?)` | `FigPlanNode` | Create an instance of a component (plan node or ID) |
| `$fig.group` / `.union` / `.subtract` / `.intersect` / `.exclude` / `.variants` | `FigPlanNode` | Wrap children in a group, boolean op, or component set |
| `$fig.get(id)` | `FigPlanNode` | Wrap an existing node by ID so it can be mutated |
| `$fig.query(selector, scope?)` | `FigQueryResult` | CSS selector search — same syntax as `node.query()` |
| `$fig.set(target, props)` | `FigPlanNode` | Update props on a plan node |
| `$fig.delete(...nodes)` | `void` | Remove nodes |
| `$fig.move(target, newParent, index?)` / `.clone(target, props?)` | `void` | Reparent / clone |
| `$fig.add(parent, child)` / `.append(parent, child)` / `.addAt(parent, index, child)` | `FigPlanNode` | Insert children |
| `$fig.replace(oldNode, newNode)` / `.reorder(parent, children)` | `FigPlanNode` | Swap / reorder |
| `$fig.gradient(node, type, stops, transform?)` / `.image(node, hash, scaleMode?)` | `void` | Paint shortcuts |
| `$fig.paintStyle` / `.textStyle` / `.effectStyle` / `.gridStyle` | `FigPlanPaintStyle` / `FigPlanTextStyle` / `FigPlanEffectStyle` / `FigPlanGridStyle` | Create a local style — `(opts)` with required `name`. Pass the returned handle into `fills` / `strokes` / `effects` / `layoutGrids` / `textStyle` to bind by id. |
| `$fig.getStyle(nameOrId)` | `FigPlanStyle \| null` | Wrap an existing local style. Tries id first, then scans by name. Narrow via `handle.style?.type`. |
| `planStyle.set(opts \| fn)` / `.remove()` / `.style` / `.id` | — | Style handle methods. Fn form receives the **live Figma `Style`** narrowed to the concrete subtype (`PaintStyle` / `TextStyle` / `EffectStyle` / `GridStyle`), not the plan handle. |
| `$fig.varCollection(opts)` | `FigPlanVarCollection` | Create a variable collection. `opts.name` + `opts.modes` (string array) required. |
| `$fig.getVarCollection(idOrName)` | `FigPlanVarCollection` | Wrap existing collection by id or name. Throws if not found. |
| `$fig.getVar(id)` | `FigPlanVariable` | Wrap existing variable by real Figma id. Throws if not found. Use `coll.getVar(name)` for name-based lookup. |
| `coll.colorVar` / `.numVar` / `.boolVar` / `.stringVar` | `FigPlanColorVar` / `FigPlanNumVar` / `FigPlanBoolVar` / `FigPlanStringVar` | Create a typed variable. `opts.name` required. `opts.values` as `{ modeName: value }`. Specify `opts.scopes` explicitly — `ALL_SCOPES` is almost never right. |
| `coll.getVar(nameOrId)` | `FigPlanVariable` | Wrap existing variable in this collection by name or id. |
| `planVar.value(mode, val)` / `.setValues(map \| fn)` / `.set(opts \| fn)` / `.remove()` | — | Variable handle methods. Pass another variable handle as a value to create a `VARIABLE_ALIAS`. |
| `$fig.done()` | `Promise<FigDoneResult>` | Explicitly materialize the plan. Auto-flushes on script shutdown if not called. |

Plan nodes returned by create methods are chainable — `.frame()`, `.text()`, `.set()`, `.remove()`, `.clone()`, `.moveTo()`, `.reorderChildren()`, `.replace()`, `.query()`, `.gradient()`, `.image()` operate within that subtree.

#### Types

| Type                | Description |
| ------------------- | ----------- |
| `QueryResult`       | Iterable result from `node.query()` with `.first()`, `.last()`, `.each()`, `.map()`, `.filter()`, `.values()`, `.set()`, `.query()` |
| `ScreenshotOptions` | `{ scale?: number, contentsOnly?: boolean }` — `contentsOnly` defaults to `false` |

---

## Reference — Gotchas & Common Mistakes

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). Every known pitfall with WRONG/CORRECT code examples.

### Contents

- Component properties and variant creation pitfalls
- Paint, color, and variable binding pitfalls
- Page context and plugin lifecycle pitfalls
- Auto Layout and sizing order pitfalls (including HUG/FILL interactions)
- Variant layout and geometry pitfalls
- Font loading and text/typography pitfalls
- Variable scopes and mode pitfalls
- Node cleanup and empty-fill pitfalls
- Type-specific method calls without node type guards
- Non-existent property writes and "object is not extensible"
- width/height are read-only — use resize()
- detachInstance() and node ID invalidation


### New nodes default to (0,0) and overlap existing content

Every `figma.create*()` call places the node at position (0,0). If you append multiple nodes directly to the page, they all stack on top of each other and on top of any existing content.

**This only matters for nodes appended directly to the page** (i.e., top-level nodes). Nodes appended as children of other frames, components, or auto-layout containers are positioned by their parent — don't scan for overlaps when nesting nodes.

```js
// WRONG — top-level node lands at (0,0), overlapping existing page content
const frame = figma.createFrame()
frame.name = "My New Frame"
frame.resize(400, 300)
figma.currentPage.appendChild(frame)

// CORRECT — find existing content bounds and place the new top-level node to the right
const page = figma.currentPage
let maxX = 0
for (const child of page.children) {
  const right = child.x + child.width
  if (right > maxX) maxX = right
}
const frame = figma.createFrame()
frame.name = "My New Frame"
frame.resize(400, 300)
figma.currentPage.appendChild(frame)
frame.x = maxX + 100  // 100px gap from rightmost existing content
frame.y = 0

// NOT NEEDED — child nodes inside a parent don't need overlap scanning
const card = figma.createAutoLayout('VERTICAL')
const label = figma.createText()
card.appendChild(label)  // positioned by auto-layout, no x/y needed
```

### `addComponentProperty` returns a string key, not an object — never hardcode or guess it

Figma generates the property key dynamically (e.g. `"label#4:0"`). The suffix is unpredictable. Always capture and use the return value directly.

```js
// WRONG — guessing / hardcoding the key
comp.addComponentProperty('label', 'TEXT', 'Button')
labelNode.componentPropertyReferences = { characters: 'label#0:1' }  // Error: key not found

// WRONG — treating the return value as an object
const result = comp.addComponentProperty('Label', 'TEXT', 'Button')
const propKey = Object.keys(result)[0]  // BUG: returns '0' (first char index of string!)
labelNode.componentPropertyReferences = { characters: propKey }  // Error: property '0' not found

// CORRECT — the return value IS the key string, use it directly
const propKey = comp.addComponentProperty('Label', 'TEXT', 'Button')
// propKey === "label#4:0" (exact value varies; never assume it)
labelNode.componentPropertyReferences = { characters: propKey }
```

The same applies to `COMPONENT_SET` nodes — `addComponentProperty` always returns the property key as a string.

### MUST return ALL created/mutated node IDs

Every script that creates or mutates nodes on the canvas must track and return all affected node IDs in the return value. Without these IDs, subsequent calls cannot reference, validate, or clean up those nodes.

```js
// WRONG — only returns the parent frame ID, loses track of children
const frame = figma.createFrame()
const rect = figma.createRectangle()
const text = figma.createText()
frame.appendChild(rect)
frame.appendChild(text)
return { nodeId: frame.id }

// CORRECT — returns all created node IDs in a structured response
const frame = figma.createFrame()
const rect = figma.createRectangle()
const text = figma.createText()
frame.appendChild(rect)
frame.appendChild(text)
return {
  createdNodeIds: [frame.id, rect.id, text.id],
  rootNodeId: frame.id
}

// CORRECT — when mutating existing nodes, return those IDs too
const nodes = figma.currentPage.findAll(n => n.name === 'Card')
for (const n of nodes) {
  n.fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
}
return {
  mutatedNodeIds: nodes.map(n => n.id),
  count: nodes.length
}
```

### Colors are 0–1 range

```js
// WRONG — will throw validation error (ZeroToOne enforced)
node.fills = [{ type: 'SOLID', color: { r: 255, g: 0, b: 0 } }]

// CORRECT
node.fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
```

### Fills/strokes are immutable arrays

```js
// WRONG — modifying in place does nothing
node.fills[0].color = { r: 1, g: 0, b: 0 }

// CORRECT — clone, modify, reassign
const fills = JSON.parse(JSON.stringify(node.fills))
fills[0].color = { r: 1, g: 0, b: 0 }
node.fills = fills
```

### setBoundVariableForPaint returns a NEW paint

```js
// WRONG — ignoring return value
figma.variables.setBoundVariableForPaint(paint, "color", colorVar)
node.fills = [paint]  // paint is unchanged!

// CORRECT — capture the returned new paint
const boundPaint = figma.variables.setBoundVariableForPaint(paint, "color", colorVar)
node.fills = [boundPaint]
```

### Variable collection starts with 1 mode

```js
// A new collection already has one mode — rename it, don't try to add first
const collection = figma.variables.createVariableCollection("Colors")
// collection.modes = [{ modeId: "...", name: "Mode 1" }]
collection.renameMode(collection.modes[0].modeId, "Light")
const darkModeId = collection.addMode("Dark")
```

### combineAsVariants requires ComponentNodes

```js
// WRONG — passing frames
const f1 = figma.createFrame()
figma.combineAsVariants([f1], figma.currentPage) // Error!

// CORRECT — passing components
const c1 = figma.createComponent()
c1.name = "variant=primary, size=md"
const c2 = figma.createComponent()
c2.name = "variant=secondary, size=md"
figma.combineAsVariants([c1, c2], figma.currentPage)
```

### Page switching: sync setter does NOT work

The sync setter `figma.currentPage = page` does **NOT work** in `use_figma` — it throws `"Setting figma.currentPage is not supported"`. You **must** use `await figma.setCurrentPageAsync(page)` instead, which switches the page and loads its content.

Note: **reading** `figma.currentPage` is fine — it's only the **assignment** (`figma.currentPage = ...`) that throws.

```js
// WRONG — throws "Setting figma.currentPage is not supported"
figma.currentPage = targetPage

// CORRECT — async method switches and loads content
await figma.setCurrentPageAsync(targetPage)

// ALSO CORRECT — reading currentPage is fine
const page = figma.currentPage  // works
```

### `get_metadata` only sees one page — use `use_figma` to discover all pages

A Figma file can have multiple pages (canvas nodes). `get_metadata` operates on a single node/page — it cannot scan the entire document. To discover all pages and their top-level contents, use `use_figma`:

```js
// WRONG — calling get_metadata with the file root or expecting it to list all pages
// get_metadata only returns the subtree of the node you pass it

// CORRECT — use use_figma to list pages, then inspect each one
const pages = figma.root.children.map(p => `${p.name} id=${p.id} children=${p.children.length}`);
return pages.join('\n');
```

Icons, variables, and components may live on pages other than the first. Always enumerate all pages before concluding that the file has no existing assets.

### Never use figma.notify()

```js
// WRONG — throws "not implemented" error
figma.notify("Done!")

// CORRECT — return a value to send data back to the agent
return "Done!"
```

### `getPluginData()` / `setPluginData()` are not supported

These APIs are not available in `use_figma`. Use `getSharedPluginData()` / `setSharedPluginData()` instead (these ARE supported), or track nodes by returning IDs.

```js
// WRONG — not supported in use_figma
node.setPluginData('my_key', 'my_value')
const val = node.getPluginData('my_key')

// CORRECT — use shared plugin data (requires a namespace)
node.setSharedPluginData('my_namespace', 'my_key', 'my_value')
const val = node.getSharedPluginData('my_namespace', 'my_key')

// ALSO CORRECT — return node IDs and track them across calls
const rect = figma.createRectangle()
return { nodeId: rect.id }
// Then pass nodeId as a string literal in the next use_figma call
```

### Script must always return a value

```js
// WRONG — no return, caller gets no useful response
figma.createRectangle()

// CORRECT — return a result (objects are auto-serialized, errors are auto-captured)
const rect = figma.createRectangle()
return { nodeId: rect.id }
```

### setBoundVariable for paint fields only works on SOLID paints

```js
// Only SOLID paint type supports color variable binding
// Gradient paints, image paints, etc. will throw
const solidPaint = { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }
const bound = figma.variables.setBoundVariableForPaint(solidPaint, "color", colorVar)
```

### Explicit variable modes must be set per component

```js
// WRONG — all variants render with the default (first) mode
const colorCollection = figma.variables.createVariableCollection("Colors")
// ... create variables and modes ...
// Components all show the first mode's values by default!

// CORRECT — set explicit mode on each component to get variant-specific values
component.setExplicitVariableModeForCollection(colorCollection, targetModeId)
```

### `lineHeight` and `letterSpacing` must be objects, not bare numbers

```js
// WRONG — throws or silently does nothing
style.lineHeight = 1.5
style.lineHeight = 24
style.letterSpacing = 0

// CORRECT
style.lineHeight = { unit: "AUTO" }                    // auto/intrinsic
style.lineHeight = { value: 24, unit: "PIXELS" }       // fixed pixel height
style.lineHeight = { value: 150, unit: "PERCENT" }     // percentage of font size

style.letterSpacing = { value: 0, unit: "PIXELS" }     // no tracking
style.letterSpacing = { value: -0.5, unit: "PIXELS" }  // tight
style.letterSpacing = { value: 5, unit: "PERCENT" }    // percent-based
```

This applies to both `TextStyle` and `TextNode` properties. The same rule applies inside `use_figma`, interactive plugins, and any other plugin API context.

### Font style names are file-dependent — use `listAvailableFontsAsync` to discover them

Font style names vary per provider and per Figma file. Always call `figma.listAvailableFontsAsync()` to discover exact style strings before loading — never guess or probe with try/catch. See [Text Style API Patterns](#discovering-available-font-styles) for the discovery + load pattern.

### combineAsVariants does NOT auto-layout in `use_figma`

```js
// WRONG — all variants stack at position (0, 0), resulting in a tiny ComponentSet
const components = [comp1, comp2, comp3]
const cs = figma.combineAsVariants(components, figma.currentPage)
// cs.width/height will be the size of a SINGLE variant!

// CORRECT — manually layout children in a grid after combining
const cs = figma.combineAsVariants(components, figma.currentPage)
const colWidth = 120
const rowHeight = 56
cs.children.forEach((child, i) => {
  const col = i % numCols
  const row = Math.floor(i / numCols)
  child.x = col * colWidth
  child.y = row * rowHeight
})
// CRITICAL: resize from actual child bounds, not formula — formula errors leave variants outside the boundary
let maxX = 0, maxY = 0
for (const child of cs.children) {
  maxX = Math.max(maxX, child.x + child.width)
  maxY = Math.max(maxY, child.y + child.height)
}
cs.resizeWithoutConstraints(maxX + 40, maxY + 40)
```

### Paint `color` must not include `a` — use `opacity` at the paint level instead

Paint `color` only accepts `{r, g, b}`. Adding `a` to it throws `"Unrecognized key(s) in object: 'a' at [0].color"`. This is a common mistake coming from CSS `rgba()` muscle memory.

Alpha/opacity belongs at the **paint level** as `opacity`, not inside `color`.

```js
// WRONG — 'a' is not valid inside color; throws validation error
node.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1, a: 0.1 } }]

// CORRECT — opacity goes at the paint level
node.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 }, opacity: 0.1 }]

// CORRECT — fully opaque (no opacity needed)
node.fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
```

**COLOR variable values are the exception** — they do use `{r, g, b, a}`:

```js
// Variable values use {r, g, b, a} — this is correct for variables only
const colorVar = figma.variables.createVariable("bg", collection, "COLOR")
colorVar.setValueForMode(modeId, { r: 1, g: 0, b: 0, a: 1 })  // opaque red
colorVar.setValueForMode(modeId, { r: 0, g: 0, b: 0, a: 0 })  // fully transparent
```

### `layoutSizingVertical`/`layoutSizingHorizontal` = `'FILL'` requires auto-layout parent FIRST

```js
// WRONG — setting FILL before the node is a child of an auto-layout frame
const child = figma.createFrame()
child.layoutSizingVertical = 'FILL'  // ERROR: "FILL can only be set on children of auto-layout frames"
parent.appendChild(child)

// CORRECT — append to auto-layout parent FIRST, then set FILL
const child = figma.createFrame()
parent.appendChild(child)            // parent must have layoutMode set
child.layoutSizingVertical = 'FILL'  // Works!
```

**Tip:** use `figma.createAutoLayout()` (or `figma.createAutoLayout('VERTICAL')`) instead of `figma.createFrame()` when you want a parent that supports `FILL` children. It returns a frame with `layoutMode` already set and both axes hugging content, so you don't have to remember the property dance.

```js
const parent = figma.createAutoLayout()  // layoutMode = 'HORIZONTAL', sizing = AUTO
const child = figma.createFrame()
parent.appendChild(child)
child.layoutSizingHorizontal = 'FILL'    // Works immediately
```

### HUG parents collapse FILL children

A `HUG` parent cannot give `FILL` children meaningful size. If children have `layoutSizingHorizontal = "FILL"` but the parent is `"HUG"`, the children collapse to minimum size. The parent must be `"FILL"` or `"FIXED"` for FILL children to expand. This is a common cause of truncated text in select fields, inputs, and action rows.

```js
// WRONG — parent hugs, so FILL children get zero extra space
const parent = figma.createAutoLayout()
parent.layoutSizingHorizontal = 'HUG'
const child = figma.createFrame()
parent.appendChild(child)
child.layoutSizingHorizontal = 'FILL'  // collapses to min size!

// CORRECT — parent must be FIXED or FILL for FILL children to expand
const parent = figma.createAutoLayout()
parent.resize(400, 50)
parent.layoutSizingHorizontal = 'FIXED'  // or 'FILL' if inside another auto-layout
const child = figma.createFrame()
parent.appendChild(child)
child.layoutSizingHorizontal = 'FILL'  // expands to fill remaining 400px
```

### `layoutGrow` with a hugging parent causes content compression

```js
// WRONG — layoutGrow on a child when parent has primaryAxisSizingMode='AUTO' (hug)
// causes the child to SHRINK below its natural size instead of expanding
const parent = figma.createComponent()
parent.layoutMode = 'VERTICAL'
parent.primaryAxisSizingMode = 'AUTO'  // hug contents
const content = figma.createAutoLayout('VERTICAL')
parent.appendChild(content)
content.layoutGrow = 1  // BUG: content compresses, children hidden!

// CORRECT — only use layoutGrow when parent has FIXED sizing with extra space
content.layoutGrow = 0  // let content take its natural size
// OR: set parent to FIXED sizing first
parent.primaryAxisSizingMode = 'FIXED'
parent.resizeWithoutConstraints(300, 500)
content.layoutGrow = 1  // NOW it correctly fills remaining space
```

### `width` and `height` are read-only — use `resize()`

`node.width` and `node.height` are read-only. Assigning to them throws `"TypeError: no setter for property"`. Use `resize()` or `resizeWithoutConstraints()` instead.

Note: `x` and `y` are **not** read-only and can be set directly.

```js
// WRONG — throws "no setter for property"
node.width = 300
node.height = 64

// CORRECT — use resize() to change dimensions
node.resize(300, 64)           // change both
node.resize(300, node.height)  // change width only
node.resize(node.width, 64)    // change height only

// CORRECT — x and y are writable directly
node.x = 100
node.y = 200
```

For sections and component sets, use `resizeWithoutConstraints()` instead of `resize()` (see the sections gotcha above).

### `resize()` resets `primaryAxisSizingMode` and `counterAxisSizingMode` to FIXED

`resize(w, h)` silently resets **both** sizing modes to `FIXED`. If you call it after setting `HUG`, the frame locks to the exact pixel value you passed — even a throwaway like `1`.

```js
// WRONG — resize() after setting sizing mode overwrites it back to FIXED
const frame = figma.createComponent()
frame.layoutMode = 'VERTICAL'
frame.primaryAxisSizingMode = 'AUTO'  // hug height
frame.counterAxisSizingMode = 'FIXED'
frame.resize(300, 10)  // BUG: resets BOTH axes to 'FIXED'! Height stays at 10px forever.

// ESPECIALLY DANGEROUS — throwaway values when you only care about one axis
const comp = figma.createComponent()
comp.layoutMode = 'VERTICAL'
comp.layoutSizingHorizontal = 'FIXED'
comp.layoutSizingVertical = 'HUG'
comp.resize(280, 1)  // BUG: "I only want width=280" but this locks height to 1px!
// HUG was reset to FIXED by resize(), frame is now permanently 280×1

// CORRECT — call resize() FIRST, then set sizing modes
const frame = figma.createComponent()
frame.layoutMode = 'VERTICAL'
frame.resize(300, 40)  // use a reasonable default, never 0 or 1
frame.counterAxisSizingMode = 'FIXED'  // keep width fixed at 300
frame.primaryAxisSizingMode = 'AUTO'   // NOW set height to hug — this sticks!
// Or use the modern shorthand (equivalent):
// frame.layoutSizingHorizontal = 'FIXED'
// frame.layoutSizingVertical = 'HUG'
```

**Rule of thumb**: Never pass a throwaway/garbage value (like `1` or `0`) to `resize()` for an axis you intend to be `HUG`. Either call `resize()` before setting sizing modes, or use a reasonable default that won't cause visual bugs if the mode reset goes unnoticed.

### Node positions don't auto-reset after reparenting

```js
// WRONG — assuming positions reset when moving a node into a new parent
const node = figma.createRectangle()
node.x = 500; node.y = 500;
figma.currentPage.appendChild(node)
section.appendChild(node)  // node still at (500, 500) relative to section!

// CORRECT — explicitly set x/y after ANY reparenting operation
section.appendChild(node)
node.x = 80; node.y = 80;  // reset to desired position within section
```

### Grid layout with mixed-width rows causes overlaps

```js
// WRONG — using a single column offset for rows with different-width items
// e.g. vertical cards (320px) and horizontal cards (500px) in a 2-row grid
for (let i = 0; i < allCards.length; i++) {
  allCards[i].x = (i % 4) * 370  // 370 works for 320px cards but NOT 500px cards!
}

// CORRECT — compute each row's spacing independently based on actual child widths
const gap = 50
let x = 0
for (const card of horizontalCards) {
  card.x = x
  x += card.width + gap  // use actual width, not a fixed column size
}
```

### Sections don't auto-resize to fit content

```js
// WRONG — section stays at default size, content overflows
const section = figma.createSection()
section.name = "My Section"
section.appendChild(someNode) // node may be outside section bounds

// CORRECT — explicitly resize after adding content
const section = figma.createSection()
section.name = "My Section"
section.appendChild(someNode)
section.resize(
  Math.max(someNode.width + 100, 800),
  Math.max(someNode.height + 100, 600)
)
```

### `counterAxisAlignItems` does NOT support `'STRETCH'`

```js
// WRONG — 'STRETCH' is not a valid enum value
comp.counterAxisAlignItems = 'STRETCH'
// Error: Invalid enum value. Expected 'MIN' | 'MAX' | 'CENTER' | 'BASELINE', received 'STRETCH'

// CORRECT — use 'MIN' on the parent, then set children to FILL on the cross axis
comp.counterAxisAlignItems = 'MIN'
comp.appendChild(child)
// For vertical layout, stretch width:
child.layoutSizingHorizontal = 'FILL'
// For horizontal layout, stretch height:
child.layoutSizingVertical = 'FILL'
```

### Variable collection mode limits are plan-dependent

```js
// Figma limits modes per collection based on the team/org plan:
//   Free: 1 mode only (no addMode)
//   Professional: up to 4 modes
//   Organization/Enterprise: up to 40+ modes
//
// WRONG — creating 20 modes on a Professional plan will fail silently or throw
const coll = figma.variables.createVariableCollection("Variants")
for (let i = 0; i < 20; i++) coll.addMode("mode" + i) // May fail!

// CORRECT — if you need many modes, split across multiple collections
// E.g., instead of 1 collection with 20 modes (variant×color):
//   Collection A: 4 modes (variant: plain/outlined/soft/solid)
//   Collection B: 5 modes (color: neutral/primary/danger/success/warning)
// Then use setExplicitVariableModeForCollection for BOTH on each component
```

### Variables default to `ALL_SCOPES` — always set scopes explicitly

```js
// WRONG — variable appears in every property picker (fills, text, strokes, spacing, etc.)
const bgColor = figma.variables.createVariable("Background/Default", coll, "COLOR")
// bgColor.scopes defaults to ["ALL_SCOPES"] — pollutes all dropdowns

// CORRECT — restrict to relevant property pickers
const bgColor = figma.variables.createVariable("Background/Default", coll, "COLOR")
bgColor.scopes = ["FRAME_FILL", "SHAPE_FILL"]  // fill pickers only

const textColor = figma.variables.createVariable("Text/Default", coll, "COLOR")
textColor.scopes = ["TEXT_FILL"]  // text color picker only

const borderColor = figma.variables.createVariable("Border/Default", coll, "COLOR")
borderColor.scopes = ["STROKE_COLOR"]  // stroke picker only

const spacing = figma.variables.createVariable("Space/400", coll, "FLOAT")
spacing.scopes = ["GAP"]  // gap/spacing pickers only

// Hide primitives that are only referenced via aliases
const primitive = figma.variables.createVariable("Brand/500", coll, "COLOR")
primitive.scopes = []  // hidden from all pickers
```

### Binding fills on nodes with empty fills

```js
// WRONG — binding to a node with no fills does nothing
const comp = figma.createComponent()
comp.fills = [] // transparent
// Can't bind a color variable to fills that don't exist

// CORRECT — add a placeholder SOLID fill, then bind the variable
const comp = figma.createComponent()
const basePaint = { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }
const boundPaint = figma.variables.setBoundVariableForPaint(basePaint, "color", colorVar)
comp.fills = [boundPaint]
// The variable's resolved value (which may be transparent) will control the actual color
```

### Mode names must be descriptive — never leave 'Mode 1'

Every new `VariableCollection` starts with one mode named `'Mode 1'`. Always rename it immediately. For single-mode collections use `'Default'`; for multi-mode collections use names from the source (e.g. `'Light'`/`'Dark'`, `'Desktop'`/`'Tablet'`/`'Mobile'`).

    // WRONG — generic names give no semantic meaning
    const coll = figma.variables.createVariableCollection('Colors')
    // coll.modes[0].name === 'Mode 1' — left as-is
    const darkId = coll.addMode('Mode 2')

    // CORRECT — rename immediately to match the source
    const coll = figma.variables.createVariableCollection('Colors')
    coll.renameMode(coll.modes[0].modeId, 'Light')   // was 'Mode 1'
    const darkId = coll.addMode('Dark')

    // For single-mode collections (primitives, spacing, etc.)
    const spacing = figma.variables.createVariableCollection('Spacing')
    spacing.renameMode(spacing.modes[0].modeId, 'Default')  // was 'Mode 1'

### CSS variable names must not contain spaces

When constructing a `var(--name)` string from a Figma variable name, replace BOTH slashes AND spaces with hyphens and convert to lowercase.

    // WRONG — only replacing slashes leaves spaces like 'var(--color-bg-brand secondary hover)'
    v.setVariableCodeSyntax('WEB', `var(--${figmaName.replace(/\//g, '-').toLowerCase()})`)

    // CORRECT — replace all whitespace and slashes in one pass
    v.setVariableCodeSyntax('WEB', `var(--${figmaName.replace(/[\s\/]+/g, '-').toLowerCase()})`)

**Best practice**: Preserve the original CSS variable name from the source token file rather than deriving it from the Figma name.

    // Preferred — use the source CSS name directly
    v.setVariableCodeSyntax('WEB', `var(${token.cssVar})`)  // e.g. '--color-bg-brand-secondary-hover'

### Calling type-specific methods without checking node type

Some methods only exist on specific node types. Calling them on the wrong type throws "TypeError: not a function". Always guard with a type check before calling type-specific methods.

```js
// WRONG — node might not be a TextNode
const node = await figma.getNodeByIdAsync('952:1253');
const segments = node.getStyledTextSegments(['hyperlink']); // TypeError if node isn't TEXT

// CORRECT — check type first
const node = await figma.getNodeByIdAsync('952:1253');
if (!node || node.type !== 'TEXT') return { error: `Expected TextNode, got ${node?.type ?? 'null'}` };
const segments = node.getStyledTextSegments(['hyperlink']);
```

Common type-specific methods and the types that have them:

| Method | Node type required |
|--------|-------------------|
| `getStyledTextSegments()` | `TEXT` |
| `setRangeFontName()`, `setRangeFontSize()` | `TEXT` |
| `createInstance()` | `COMPONENT` |
| `addComponentProperty()` | `COMPONENT`, `COMPONENT_SET` |
| `createVariant()` | `COMPONENT_SET` |

### Setting a non-existent property throws "object is not extensible"

Figma plugin API node objects are non-extensible — you cannot add new properties to them. Setting a property name that doesn't exist on a node type throws `"Cannot add property X, object is not extensible"` (surfaced as `"object is not extensible"`). This only fires on **write**, and only for properties not defined on that node type.

```js
// WRONG — 'strokeDashes' does not exist on VectorNode; throws "object is not extensible"
const v = figma.createVector()
v.strokeDashes = [4, 8]  // Error!

// CORRECT — the actual property is dashPattern
v.dashPattern = [4, 8]

// WRONG — any invented property name throws the same error
node.customColor = '#ff0000'  // Error — not a real API property
```

**How to avoid this**: Before setting any property, verify it exists on the node type by grepping Plugin API type reference (load `readPowerSteering("figma", "figma-use-api.md")`). Property names that sound plausible but aren't in the typings will always throw.

### `detachInstance()` invalidates ancestor node IDs

When `detachInstance()` is called on a nested instance inside a library component instance, the parent instance may also get implicitly detached (converted from INSTANCE to FRAME with a **new ID**). Any previously cached ID for the parent becomes invalid.

```js
// WRONG — using cached parent ID after child detach
const parentId = parentInstance.id;
nestedChild.detachInstance();
const parent = await figma.getNodeByIdAsync(parentId); // null! ID changed.

// CORRECT — re-discover by traversal from a stable (non-instance) frame
const stableFrame = await figma.getNodeByIdAsync(manualFrameId);
nestedChild.detachInstance();
const parent = stableFrame.findOne(n => n.name === "ParentName");
```

If detaching multiple nested instances across siblings, do it in a **single** `use_figma` call — discover all targets by traversal before any detachment mutates the tree.

---

## Reference — Common Patterns

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). Working code examples for frequently used operations.

### Contents

- Basic Script Structure
- Create a Styled Shape
- Create a Text Node
- Create Frame with Auto-Layout
- Create Variable Collections and Bindings
- Create Components and Import by Key
- Component Sets with Variable Modes
- Multi-Step Large ComponentSet Pattern
- Read Existing Nodes and Return Data


### Basic Script Structure

When using only `$fig` for mutations:

```js
// Your code here
// $fig...
```

When using the raw plugin API for mutations:

```js
const createdNodeIds = []
const mutatedNodeIds = []

// Your code here — track every node you create or mutate
// createdNodeIds.push(newNode.id)
// mutatedNodeIds.push(existingNode.id)

return {
  success: true,
  createdNodeIds,
  mutatedNodeIds,
  // Plus any other useful data for subsequent calls
  count: createdNodeIds.length
}
```

### Create a Styled Shape using `$fig`

```js
$fig.rectangle({
  name: "Blue Box",
  width: 200,
  height: 100,
  fills: [{ type: 'SOLID', color: { r: 0.047, g: 0.549, b: 0.914 } }],
  cornerRadius: 8,
})
```

### Create a Styled Shape using the raw plugin API

Prefer using `$fig` over the raw plugin API for node creation and mutation. This code sample is for reference only if `$fig` cannot be used.

```js
// Find clear space to the right of existing content
const page = figma.currentPage
let maxX = 0
for (const child of page.children) {
  maxX = Math.max(maxX, child.x + child.width)
}

const rect = figma.createRectangle()
rect.name = "Blue Box"
rect.resize(200, 100)
rect.fills = [{ type: 'SOLID', color: { r: 0.047, g: 0.549, b: 0.914 } }]
rect.cornerRadius = 8
rect.x = maxX + 100  // offset from existing content
rect.y = 0
figma.currentPage.appendChild(rect)
return { nodeId: rect.id }
```

### Create a Text Node

```js
$fig.text({
  characters: "Hello World",
  fontSize: 16,
  fills: [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }],
  textAutoResize: 'WIDTH_AND_HEIGHT',
})
```

### Create Frame with Auto-Layout

```js
$fig.autoLayout({
  name: "Card",
  layoutMode: 'VERTICAL',
  primaryAxisAlignItems: 'MIN',
  counterAxisAlignItems: 'MIN',
  paddingLeft: 16,
  paddingRight: 16,
  paddingTop: 12,
  paddingBottom: 12,
  itemSpacing: 8,
  fills: [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }],
  cornerRadius: 8,
})
```

### Create Variable Collection with Multiple Modes

```js
const collection = figma.variables.createVariableCollection("Theme/Colors")
// Rename the default mode
collection.renameMode(collection.modes[0].modeId, "Light")
const darkModeId = collection.addMode("Dark")
const lightModeId = collection.modes[0].modeId

const bgVar = figma.variables.createVariable("bg", collection, "COLOR")
bgVar.setValueForMode(lightModeId, { r: 1, g: 1, b: 1, a: 1 })
bgVar.setValueForMode(darkModeId, { r: 0.1, g: 0.1, b: 0.1, a: 1 })

const textVar = figma.variables.createVariable("text", collection, "COLOR")
textVar.setValueForMode(lightModeId, { r: 0, g: 0, b: 0, a: 1 })
textVar.setValueForMode(darkModeId, { r: 1, g: 1, b: 1, a: 1 })

return {
  collectionId: collection.id,
  lightModeId,
  darkModeId,
  bgVarId: bgVar.id,
  textVarId: textVar.id
}
```

### Bind Color Variable to a Fill

```js
const variable = await figma.variables.getVariableByIdAsync("VariableID:1:2")
const rect = figma.createRectangle()
const basePaint = { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }

// setBoundVariableForPaint returns a NEW paint — capture it!
const boundPaint = figma.variables.setBoundVariableForPaint(basePaint, "color", variable)
rect.fills = [boundPaint]

return { nodeId: rect.id }
```

### Create Component Variants with Component Properties

Component properties (TEXT, BOOLEAN, INSTANCE_SWAP) MUST be added inside the per-variant loop, BEFORE `combineAsVariants`. The component set inherits them from its children.

```js
await figma.loadFontAsync({ family: "Inter", style: "Regular" })

// Assume defaultIconComp is an existing icon component (discovered earlier)
const defaultIconComp = figma.getNodeById('ICON_COMPONENT_ID')

const components = []
const variants = ["primary", "secondary"]

for (const variant of variants) {
  const comp = figma.createComponent()
  comp.name = `variant=${variant}`
  comp.layoutMode = 'HORIZONTAL'
  comp.primaryAxisAlignItems = 'CENTER'
  comp.counterAxisAlignItems = 'CENTER'
  comp.paddingLeft = 12
  comp.paddingRight = 12
  comp.paddingTop = 8
  comp.paddingBottom = 8
  comp.layoutSizingHorizontal = 'HUG'
  comp.layoutSizingVertical = 'HUG'
  comp.cornerRadius = 6
  comp.itemSpacing = 8

  // TEXT property — label
  const labelKey = comp.addComponentProperty('Label', 'TEXT', 'Button')
  const label = figma.createText()
  label.characters = "Button"
  label.fontSize = 14
  comp.appendChild(label)
  label.componentPropertyReferences = { characters: labelKey }

  // BOOLEAN + INSTANCE_SWAP — icon slot
  const showIconKey = comp.addComponentProperty('Show Icon', 'BOOLEAN', false)
  const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', defaultIconComp.id)
  const iconInstance = defaultIconComp.createInstance()
  comp.insertChild(0, iconInstance)  // icon before label
  iconInstance.componentPropertyReferences = {
    visible: showIconKey,
    mainComponent: iconSlotKey
  }

  components.push(comp)
}

const componentSet = figma.combineAsVariants(components, figma.currentPage)
componentSet.name = "Button"

// Layout variants in a row after combining (they stack at 0,0 by default)
const colW = 140
componentSet.children.forEach((child, i) => {
  child.x = i * colW
  child.y = 0
})
// Resize from actual child bounds — formula-based sizing is error-prone
let maxX = 0, maxY = 0
for (const c of componentSet.children) {
  maxX = Math.max(maxX, c.x + c.width)
  maxY = Math.max(maxY, c.y + c.height)
}
componentSet.resizeWithoutConstraints(maxX + 40, maxY + 40)

return {
  componentSetId: componentSet.id,
  componentIds: components.map(c => c.id)
}
```

### Use a Component by Key (Team Libraries)

`search_design_system` returns a `componentKey` per result. Pass it directly into `$fig.get(...)` / `$fig.instance(...)` — the plan queues the library import automatically, so no separate `importComponentByKeyAsync` call is needed. The same call site accepts node IDs for components in the current file.

```js
// PREFERRED — asset key flows straight from search_design_system into $fig
const instance = $fig.instance(BUTTON_COMPONENT_KEY, { name: 'Submit', x: 40, y: 40 })

// Component set: pass the set's componentKey + variant props
const variantInstance = $fig.instance(BUTTON_SET_KEY, {
  name: 'Submit (md)',
  x: 240, y: 40,
  props: { Size: 'md', Variant: 'primary' },
})

// Wrap a set without instantiating, e.g. to inspect it after $fig.done()
const set = $fig.get(BUTTON_SET_KEY)
```

You do not need to import the component set, drill into `compSet.children`, or call `defaultVariant.createInstance()` yourself. `$fig.instance(setKey, { props })` picks the matching variant by `setProperties` after the instance is created from the default variant — the same path you'd use for variant switches on an existing instance via `$fig.set(inst, { props })` or `inst.setInstanceProps({...})`.

#### Discover a set's variant props when you only have its key

`search_design_system` returns the set's `componentKey` but not its variant properties. Discover them across **two `use_figma` calls** — you can't pick props in the same script that discovers them, because the projected values only reach you (the model) in the tool result:

```js
// Call 1 — discovery: `return` the projection so its values come back in the tool result
return $fig.get(BUTTON_SET_KEY).query('COMPONENT')
  .values(['name', 'variantProperties', 'parent.componentPropertyDefinitions'])
//  → [{ name: 'Size=Small, Kind=Primary',
//       variantProperties: { Size: 'Small', Kind: 'Primary' },
//       parent: { componentPropertyDefinitions: { Size: { variantOptions: ['Small', 'Large'] }, ... } } }, ...]
```

```js
// Call 2 — read the props from call 1's result, then instantiate the variant you want
$fig.instance(BUTTON_SET_KEY, { props: { Size: 'Large', Kind: 'Secondary' } })
```

The library must be reachable from the current file — a key from an inaccessible library errors with `failed to import DS asset <key>`. (`children` in a projection returns only `{id}` refs; query the `COMPONENT`s directly to project their fields.)

### Component Set with Variable Modes (Full Pattern)

```js
await figma.loadFontAsync({ family: "Inter", style: "Medium" })

// 1. Create color collection with modes per variant
const colors = figma.variables.createVariableCollection("Component/Colors")
colors.renameMode(colors.modes[0].modeId, "primary")
const primaryMode = colors.modes[0].modeId
const secondaryMode = colors.addMode("secondary")

const bgVar = figma.variables.createVariable("bg", colors, "COLOR")
bgVar.setValueForMode(primaryMode, { r: 0, g: 0.4, b: 0.9, a: 1 })
bgVar.setValueForMode(secondaryMode, { r: 0, g: 0, b: 0, a: 0 })

const textVar = figma.variables.createVariable("text-color", colors, "COLOR")
textVar.setValueForMode(primaryMode, { r: 1, g: 1, b: 1, a: 1 })
textVar.setValueForMode(secondaryMode, { r: 0.1, g: 0.1, b: 0.1, a: 1 })

// 2. Create components with variable bindings
const modeMap = { primary: primaryMode, secondary: secondaryMode }
const components = []

for (const [variantName, modeId] of Object.entries(modeMap)) {
  const comp = figma.createComponent()
  comp.name = "variant=" + variantName
  comp.layoutMode = "HORIZONTAL"
  comp.primaryAxisAlignItems = "CENTER"
  comp.counterAxisAlignItems = "CENTER"
  comp.paddingLeft = 12; comp.paddingRight = 12
  comp.layoutSizingHorizontal = "HUG"
  comp.layoutSizingVertical = "HUG"
  comp.cornerRadius = 6

  // Bind background fill to variable
  const bgPaint = figma.variables.setBoundVariableForPaint(
    { type: "SOLID", color: { r: 0, g: 0, b: 0 } }, "color", bgVar
  )
  comp.fills = [bgPaint]

  // Add text with bound color
  const label = figma.createText()
  label.fontName = { family: "Inter", style: "Medium" }
  label.characters = "Button"
  label.fontSize = 14
  const textPaint = figma.variables.setBoundVariableForPaint(
    { type: "SOLID", color: { r: 0, g: 0, b: 0 } }, "color", textVar
  )
  label.fills = [textPaint]
  comp.appendChild(label)

  // 3. CRITICAL: Set explicit mode so this variant renders correctly
  comp.setExplicitVariableModeForCollection(colors, modeId)

  components.push(comp)
}

// 4. Combine into component set
const componentSet = figma.combineAsVariants(components, figma.currentPage)
componentSet.name = "Button"

return {
  componentSetId: componentSet.id,
  colorCollectionId: colors.id
}
```

### Large ComponentSet with Variable Modes (Multi-Step Pattern)

For component sets with many variants (50+), split into multiple `use_figma` calls:

**Call 1: Create variable collections and return IDs**

```js
// Hex-to-0-1 helper
const hex = (h) => {
  if (!h) return { r: 0, g: 0, b: 0, a: 0 }; // transparent
  return {
    r: parseInt(h.slice(1,3), 16) / 255,
    g: parseInt(h.slice(3,5), 16) / 255,
    b: parseInt(h.slice(5,7), 16) / 255,
    a: 1
  };
};

const coll = figma.variables.createVariableCollection("MyComponent/Colors");
coll.renameMode(coll.modes[0].modeId, "mode1");
const mode2Id = coll.addMode("mode2");

// Create variables from data map
const colorData = { "bg/default": ["#0B6BCB", "#636B74"], /* ... */ };
const modeOrder = ["mode1", "mode2"];
const modeIds = { mode1: coll.modes[0].modeId, mode2: mode2Id };
const varIds = {};

for (const [name, values] of Object.entries(colorData)) {
  const v = figma.variables.createVariable(name, coll, "COLOR");
  values.forEach((hex_val, i) => {
    v.setValueForMode(modeIds[modeOrder[i]], hex_val ? hex(hex_val) : { r:0, g:0, b:0, a:0 });
  });
  varIds[name] = v.id;
}

// Return ALL IDs — needed by subsequent calls
return { collId: coll.id, modeIds, varIds };
```

**Call 2: Create components using stored IDs, combine and layout**

```js
await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });

// Paste IDs from Call 1 as literals
const collId = "VariableCollectionId:X:Y";
const modeIds = { mode1: "X:0", mode2: "X:1" };
const varIds = { /* ... from Call 1 ... */ };

const getVar = async (id) => await figma.variables.getVariableByIdAsync(id);
const bindColor = async (varId) => figma.variables.setBoundVariableForPaint(
  { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', await getVar(varId)
);
const collection = await figma.variables.getVariableCollectionByIdAsync(collId);

const components = [];
for (const mode of ["mode1", "mode2"]) {
  for (const state of ["default", "hover"]) {
    const comp = figma.createComponent();
    comp.name = `mode=${mode}, state=${state}`;
    comp.layoutMode = 'HORIZONTAL';
    comp.primaryAxisAlignItems = 'CENTER';
    comp.counterAxisAlignItems = 'CENTER';
    comp.layoutSizingHorizontal = 'HUG';
    comp.layoutSizingVertical = 'HUG';
    comp.fills = [await bindColor(varIds[`bg/${state}`])];
    comp.setExplicitVariableModeForCollection(collection, modeIds[mode]);
    // ... add text children ...
    components.push(comp);
  }
}

// Combine — all children stack at (0,0)!
const cs = figma.combineAsVariants(components, figma.currentPage);
cs.name = "MyComponent";

// CRITICAL: layout variants in a structured grid mapped to variant axes.
const stateOrder = ["default", "hover"];
const modeOrder2 = ["mode1", "mode2"];
const colW = 140, rowH = 56;

for (const child of cs.children) {
  const props = Object.fromEntries(
    child.name.split(', ').map(p => p.split('='))
  );
  const col = stateOrder.indexOf(props.state);
  const row = modeOrder2.indexOf(props.mode);
  child.x = col * colW;
  child.y = row * rowH;
}
// Resize from actual child bounds
let maxX = 0, maxY = 0;
for (const child of cs.children) {
  maxX = Math.max(maxX, child.x + child.width);
  maxY = Math.max(maxY, child.y + child.height);
}
cs.resizeWithoutConstraints(maxX + 40, maxY + 40);

// Wrap in section
const section = figma.createSection();
section.name = "MyComponent Section";
section.appendChild(cs);
section.resize(cs.width + 200, cs.height + 200);

return { csId: cs.id, count: components.length };
```

### Read Existing Nodes and Return Data

```js
const page = figma.currentPage
const nodes = page.findAll(n => n.type === 'FRAME')
const data = nodes.map(n => ({
  id: n.id,
  name: n.name,
  width: n.width,
  height: n.height,
  childCount: n.children?.length || 0
}))
return { frames: data }
```

---

## Reference — Component & Variant API Patterns

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). How to correctly use the Plugin API for components, variants, and component properties.
>
> For design system context (when to use variants vs properties, code-to-Figma translation, property model), see [wwds-components](#reference--components).

### Contents

- Creating a Component
- Combining Components into a Component Set (Variants)
- Laying Out Variants After combineAsVariants (Required)
- Component Properties: addComponentProperty API
- Linking Properties to Child Nodes (Required)
- INSTANCE_SWAP: Avoiding Variant Explosion
- Discovering Existing Conventions in the File
- Importing Components by Key
- Working with Instances (finding variants, setProperties, text overrides, detachInstance)


### Creating a Component

`figma.createComponent()` returns a `ComponentNode`, which behaves like a `FrameNode` but can be published, instanced, and combined into variant sets.

```javascript
const comp = figma.createComponent();
comp.name = "MyComponent";
comp.layoutMode = "HORIZONTAL";
comp.primaryAxisAlignItems = "CENTER";
comp.counterAxisAlignItems = "CENTER";
comp.paddingLeft = 12;
comp.paddingRight = 12;
comp.layoutSizingHorizontal = "HUG";
comp.layoutSizingVertical = "HUG";
comp.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.36, b: 0.96 } }];
```

### Combining Components into a Component Set (Variants)

`figma.combineAsVariants(components, parent)` takes an array of `ComponentNode`s (not frames — frames will throw) and groups them into a `ComponentSetNode`.

Variant names use a `Property=Value` format. Every unique combination must exist as a child component — missing ones show as blank gaps in the variant picker.

```javascript
// Each component's name encodes its variant properties
const comp1 = figma.createComponent();
comp1.name = "size=md, style=primary";
const comp2 = figma.createComponent();
comp2.name = "size=md, style=secondary";

const componentSet = figma.combineAsVariants([comp1, comp2], figma.currentPage);
componentSet.name = "Button";
```

**Before creating variants, inspect the file** for existing naming patterns. Different files use different conventions (`State=Default` vs `state=default` vs `State/Default`). Always match what's already there.

### Laying Out Variants After combineAsVariants (Required)

After `combineAsVariants`, all children stack at `(0, 0)`. You **must** position them or the component set will appear as a single collapsed element with all variants overlapping.

```javascript
const cs = figma.combineAsVariants(components, figma.currentPage);

// Simple row layout
cs.children.forEach((child, i) => {
  child.x = i * 150;
  child.y = 0;
});

// CRITICAL: resize the component set from actual child bounds
let maxX = 0, maxY = 0;
for (const child of cs.children) {
  maxX = Math.max(maxX, child.x + child.width);
  maxY = Math.max(maxY, child.y + child.height);
}
cs.resizeWithoutConstraints(maxX + 40, maxY + 40);
```

For multi-axis variants (e.g., size × style × state), parse the child's name to determine grid position:

```javascript
for (const child of cs.children) {
  const props = Object.fromEntries(
    child.name.split(', ').map(p => p.split('='))
  );
  const col = stateValues.indexOf(props.state);
  const row = styleValues.indexOf(props.style);
  child.x = col * colWidth;
  child.y = row * rowHeight;
}
```

### Component Properties: addComponentProperty API

> **Building with `$fig`?** Prefer the builder methods `layer.textProp(name)` / `.booleanProp(name)` / `.instanceSwapProp(name)` — they add the property to the (set-aware) component with the default inferred from the layer, de-dup across variants, and handle materialization timing for you. See [fig-builder.md → Component properties](#component-properties). Use the raw `addComponentProperty` API below when you are not in a `$fig` plan.

`addComponentProperty` adds a TEXT, BOOLEAN, or INSTANCE_SWAP property to a component. It returns a **string key** (e.g., `"label#4:0"`) — never hardcode or guess this key.

```javascript
// Returns the key as a string — capture it!
const labelKey = comp.addComponentProperty('Label', 'TEXT', 'Default text');
const showIconKey = comp.addComponentProperty('Show Icon', 'BOOLEAN', true);
const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', iconComponentId);
```

**Timing**: Add component properties to each variant component **before** calling `combineAsVariants`. After combining, the component set inherits all properties from its children. Do not add properties to the `ComponentSetNode` directly.

### Linking Properties to Child Nodes (Required)

A property that is added but not linked to a child node does **nothing**. You must set `componentPropertyReferences` on the child:

```javascript
// TEXT property → link to a text node's characters
const labelKey = comp.addComponentProperty('Label', 'TEXT', 'Button');
const textNode = figma.createText();
textNode.characters = "Button";
comp.appendChild(textNode);
textNode.componentPropertyReferences = { characters: labelKey };

// BOOLEAN + INSTANCE_SWAP → link to an instance node
const showIconKey = comp.addComponentProperty('Show Icon', 'BOOLEAN', true);
const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', iconComp.id);
const iconInstance = iconComp.createInstance();
comp.appendChild(iconInstance);
iconInstance.componentPropertyReferences = {
  visible: showIconKey,        // BOOLEAN controls show/hide
  mainComponent: iconSlotKey   // INSTANCE_SWAP controls which component
};
```

**Valid `componentPropertyReferences` keys:**
- `characters` — TEXT property on a TextNode
- `visible` — BOOLEAN property (any node)
- `mainComponent` — INSTANCE_SWAP property on an InstanceNode

### INSTANCE_SWAP: Avoiding Variant Explosion

When a component has many possible sub-elements (e.g., 30 different icons), **never** create a variant per sub-element. Use a single INSTANCE_SWAP property instead — the user picks from any compatible component at design time.

```javascript
// Create icon as its own ComponentNode
const iconComp = figma.createComponent();
iconComp.name = "Icon/Search";
iconComp.resize(24, 24);
const svgNode = figma.createNodeFromSvg('<svg>...</svg>');
iconComp.appendChild(svgNode);

// Use it as the default for INSTANCE_SWAP
const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', iconComp.id);
const instance = iconComp.createInstance();
comp.appendChild(instance);
instance.componentPropertyReferences = { mainComponent: iconSlotKey };
```

This works for icons, avatars, badges, or any swappable nested element.

### Discovering Existing Conventions in the File

**Always inspect the file before creating components.** Different files have different naming styles, structures, and conventions. Your code should match what's already there.

#### List all existing components across all pages

```javascript
const results = [];
for (const page of figma.root.children) {
  await figma.setCurrentPageAsync(page);
  page.findAll(n => {
    if (n.type === 'COMPONENT') results.push(`[${page.name}] ${n.name} (COMPONENT) id=${n.id}`);
    if (n.type === 'COMPONENT_SET') results.push(`[${page.name}] ${n.name} (COMPONENT_SET) id=${n.id}`);
    return false;
  });
}
return results.join('\n');
```

#### Inspect an existing component set's variant naming pattern

```javascript
const cs = await figma.getNodeByIdAsync('COMPONENT_SET_ID');
const variantNames = cs.children.map(c => c.name);
const propDefs = cs.componentPropertyDefinitions;
return { variantNames, propDefs };
```

#### Find existing components in the file

```javascript
const components = [];
for (const page of figma.root.children) {
  await figma.setCurrentPageAsync(page);
  page.findAll(n => {
    if (n.type === 'COMPONENT') {
      components.push({ name: n.name, id: n.id, page: page.name, w: n.width, h: n.height });
    }
    return false;
  });
}
return components;
```

### Using Components by Key (Team Libraries)

`search_design_system` returns a `componentKey` per result. Pass it directly into `$fig.get(...)` / `$fig.instance(...)` — the plan queues the library import automatically, so no separate `importComponentByKeyAsync` call is needed.

```javascript
// Instance a library component by its componentKey
$fig.instance(BUTTON_COMPONENT_KEY, { name: 'Submit' });

// Instance a specific variant of a component set by passing the set's
// componentKey + variant props
$fig.instance(BUTTON_SET_KEY, { props: { Size: 'md', Variant: 'primary' } });
```

You do not need to import the component set, drill into `compSet.children`, or call `defaultVariant.createInstance()` yourself. `$fig.instance(setKey, { props })` picks the matching variant by `setProperties` after the instance is created from the default variant — the same path used for variant switches on an existing instance via `$fig.set(inst, { props })` or `inst.setInstanceProps({...})`.

### Working with Instances

#### Selecting a variant in a component set

Pass the variant property values in `props` — `$fig.instance` resolves them on the underlying `setProperties` call:

```javascript
$fig.instance(BUTTON_SET_KEY, {
  props: { variant: 'primary', size: 'md' },
});
```

#### Switching the variant of an existing instance

Use `$fig.set` / `$fig.query(...).set({ props })` or `planNode.setInstanceProps({...})`. Both go through the same plan-managed `setProperties` path:

```javascript
const instance = $fig.get('1:42')                // an existing INSTANCE
instance.setInstanceProps({ variant: 'primary', size: 'medium' })

// Bulk: every matching instance on the page
$fig.query('INSTANCE[name=Button]').set({ props: { variant: 'primary' } })
```

#### Overriding text in a component instance

**Always discover component properties BEFORE writing text overrides.** Components expose text as `TEXT`-type component properties, and `setProperties()` is the correct way to override them. Direct `node.characters` changes on property-managed text may be overridden by the component property system on render.

**Step 1: Inspect componentProperties on a sample instance:**

```javascript
const instance = comp.createInstance();
const propDefs = instance.componentProperties;
// Returns e.g.: { "Label#2:0": { type: "TEXT", value: "Button" }, "Has Icon#4:64": { type: "BOOLEAN", value: true } }
return propDefs;
```

Also check nested instances — a parent component may not expose text properties directly, but its nested child instances might:

```javascript
const nestedInstances = instance.findAll(n => n.type === "INSTANCE");
const nestedProps = nestedInstances.map(ni => ({
  name: ni.name,
  id: ni.id,
  properties: ni.componentProperties
}));
```

**Step 2: Use setProperties() for TEXT-type properties:**

```javascript
const instance = comp.createInstance();
const propDefs = instance.componentProperties;
for (const [key, def] of Object.entries(propDefs)) {
  if (def.type === "TEXT") {
    instance.setProperties({ [key]: "New text value" });
  }
}
```

For nested instances that expose their own TEXT properties, call `setProperties()` on the nested instance:

```javascript
const nestedHeading = instance.findOne(n => n.type === "INSTANCE" && n.name === "Text Heading");
if (nestedHeading) {
  nestedHeading.setProperties({ "Text#2104:5": "Actual heading text" });
}
```

**Step 3: Only fall back to direct node.characters for unmanaged text.** If text is NOT controlled by any component property, find text nodes directly. **Always load the node's actual font first** — instance text nodes inherit fonts from the source component, so don't assume Inter Regular:

```javascript
const textNodes = instance.findAll(n => n.type === "TEXT");
for (const t of textNodes) {
  await figma.loadFontAsync(t.fontName);
  t.characters = "Updated text";
}
```

#### detachInstance() invalidates ancestor node IDs

**Warning:** When `detachInstance()` is called on a nested instance inside a library component instance, the parent instance may also get implicitly detached (converted from INSTANCE to FRAME with a **new ID**). Subsequent `getNodeByIdAsync(oldParentId)` returns null.

```javascript
// WRONG — cached parent ID becomes invalid after child detach
const parentId = parentInstance.id;
nestedChild.detachInstance();
const parent = await figma.getNodeByIdAsync(parentId); // null!

// CORRECT — re-discover nodes by traversal from a stable (non-instance) parent
const stableFrame = await figma.getNodeByIdAsync(manualFrameId); // a frame YOU created
nestedChild.detachInstance();
// Re-find the parent by traversing from the stable frame
const parent = stableFrame.findOne(n => n.name === "ParentName");
```

If you must detach multiple nested instances across sibling components, do it in a **single** `use_figma` call — discover all targets by traversal at the start before any detachment mutates the tree.

### Inspecting Component Metadata (Deep Traversal)

These helpers extract the full property schema and descendant structure of a component. Useful for understanding complex components before creating instances or setting properties. For a library component, use `$fig.get(componentKey)` to wrap it, then read `.node` after `await $fig.done()`.

```javascript
/**
 * Given a main component node, returns the component set parent if one exists,
 * otherwise returns the component itself. Used to get the top-level node that
 * holds `componentPropertyDefinitions`.
 *
 * @param {ComponentNode} mainComponent
 * @returns {ComponentNode|ComponentSetNode}
 */
function getRelevantComponentNode(mainComponent) {
  return mainComponent.parent.type === "COMPONENT_SET"
    ? mainComponent.parent
    : mainComponent;
}

/**
 * Extracts `componentPropertyDefinitions` from a component or component set node
 * into a flat map keyed by property key.
 *
 * @param {ComponentNode|ComponentSetNode} node
 * @returns {Record<string, {name: string, type: string, key: string, variantOptions?: string[]}>}
 */
function getComponentProps(node) {
  const result = {};
  for (let key in node.componentPropertyDefinitions) {
    const prop = {
      name: key.replace(/#[^#]+$/, ""),
      type: node.componentPropertyDefinitions[key].type,
      key: key
    };
    if (prop.type === "VARIANT") {
      prop.variantOptions = node.componentPropertyDefinitions[key].variantOptions;
    }
    result[key] = prop;
  }
  return result;
}

/**
 * Recursively walks a component tree and collects all INSTANCE and TEXT nodes
 * into `result`, keyed by `TYPE[name]`. Handles variant namespacing and
 * deduplicates nodes with identical names but differing property references.
 *
 * @param {SceneNode} node - The node to traverse.
 * @param {string[]} namespace - Accumulated variant names for the current path.
 * @param {Record<string, object>} result - Accumulator object populated in place.
 */
function collectDescendants(node, namespace, result) {
  if (node.type === "INSTANCE" || node.type === "TEXT") {
    const references = node.componentPropertyReferences || {};
    if (!node.visible && !references.visible) return;

    const object = { type: node.type, name: node.name, references };
    let key = `${node.type}[${node.name}]`;

    if (result[key] && JSON.stringify(references) !== JSON.stringify(result[key].references)) {
      key += btoa(btoa(unescape(encodeURIComponent(JSON.stringify(references)))));
    }

    if (node.type === "INSTANCE") {
      const mainComponent = getRelevantComponentNode(node.mainComponent);
      object.properties = getComponentProps(mainComponent);
      object.descendants = {};
      object.mainComponentName = mainComponent.name;
      collectDescendants(mainComponent, [], object.descendants);
    }

    const start = namespace.length ? { variants: [] } : {};
    result[key] = Object.assign(object, result[key] || start);
    if (namespace.length) result[key].variants.push(namespace[namespace.length - 1]);
  } else if ("children" in node && node.visible) {
    if (node.type === "COMPONENT" && node.parent.type === "COMPONENT_SET") namespace.push(node.name);
    node.children.forEach(child => collectDescendants(child, namespace, result));
  }
}

/**
 * Returns structured metadata for a component or component set defined in the current file.
 *
 * @param {string} componentId - The node ID of a COMPONENT or COMPONENT_SET node.
 * @returns {Promise<{name: string, nodeId: string, properties: object, descendants: object}|undefined>}
 */
async function getLocalComponentMetadata(componentId) {
  const node = await figma.getNodeByIdAsync(componentId);
  if (node.type === "COMPONENT_SET" || node.type === "COMPONENT") {
    const result = {
      name: node.name,
      nodeId: node.id,
      properties: {},
      descendants: {}
    };
    result.properties = getComponentProps(node);
    collectDescendants(node, [], result.descendants);
    return result;
  } else {
    throw new Error("Node is not a Component or Component Set");
  }
}

/**
 * Returns structured metadata for a published component or component set loaded by its key.
 *
 * @param {string} componentKey - The published key of the component or component set.
 * @returns {Promise<{name: string, nodeId: string, properties: object, descendants: object}>}
 */
async function getPublishedComponentMetadata(componentKey) {
  // $fig.get queues the library import in the plan; await $fig.done() to
  // materialize, then read the live SceneNode via planNode.node.
  const planNode = $fig.get(componentKey);
  await $fig.done();
  const node = planNode.node;
  if (!node || (node.type !== 'COMPONENT' && node.type !== 'COMPONENT_SET')) {
    throw new Error(`No Component or Component Set available with key '${componentKey}'`);
  }
  const result = {
    name: node.name,
    nodeId: node.id,
    properties: getComponentProps(node),
    descendants: {},
  };
  collectDescendants(node, [], result.descendants);
  return result;
}
```

#### Full metadata extraction script

```javascript
// For local components, use getLocalComponentMetadata:
const result = await getLocalComponentMetadata('COMPONENT_OR_SET_ID');
return result;

// For published components, use getPublishedComponentMetadata:
// const result = await getPublishedComponentMetadata('COMPONENT_KEY');
// return result;
```

---

## Reference — Variable & Token API Patterns

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). How to correctly create, bind, scope, and alias variables using the Plugin API.
>
> For design system context (aliasing strategy, mode decisions, code syntax philosophy, grouping conventions), see [wwds-variables](#reference--working-with-design-systems-variables).

Use `$fig` for everything in this file unless you hit one of the [gaps](#current-fig-gaps--use-figma-plugin-api-instead) listed at the bottom.

### Contents

- [Creating variables with `$fig`](#creating-variables-with-fig)
- [Binding variables to node properties with `$fig`](#binding-variables-to-node-properties-with-fig)
- [Current `$fig` gaps — use Figma Plugin API instead](#current-fig-gaps--use-figma-plugin-api-instead)
- [Effect Styles (For Shadows)](#effect-styles-for-shadows)

---

### Creating variables with `$fig`

A single plan covers collection creation, variable creation, values, scopes, code syntax, and aliasing. Everything runs in `$fig.done()`.

```javascript
const tokens = $fig.varCollection({ name: 'Tokens', modes: ['Light', 'Dark'] })

// COLOR — hex strings are auto-converted to {r,g,b,a}
const blue = tokens.colorVar({
  name: 'color/brand',
  values: { Light: '#3B82F6', Dark: '#60A5FA' },
  scopes: ['SHAPE_FILL', 'FRAME_FILL', 'TEXT_FILL'],
  codeSyntax: { WEB: 'var(--color-brand)', ANDROID: 'colorBrand', iOS: 'Color.brand' },
})

// FLOAT — spacing, sizing, radius, opacity
const spacing = tokens.numVar({
  name: 'space/lg',
  values: { Light: 16, Dark: 16 },
  scopes: ['GAP', 'WIDTH_HEIGHT'],
})
const radius = tokens.numVar({ name: 'radius/lg', values: { Light: 8, Dark: 8 }, scopes: ['CORNER_RADIUS'] })
const opacity = tokens.numVar({ name: 'opacity/btn', values: { Light: 1, Dark: 0.8 }, scopes: ['OPACITY'] })

// BOOLEAN
const visible = tokens.boolVar({ name: 'flag/show', values: { Light: true, Dark: false } })

// STRING
const font = tokens.stringVar({
  name: 'font/base',
  values: { Light: 'Inter', Dark: 'Inter' },
  scopes: ['FONT_FAMILY'],
})

// Aliasing — pass a variable handle as a value; $fig resolves the alias at done() time
const prims = $fig.varCollection({ name: 'Primitives', modes: ['Value'] })
const blue500 = prims.colorVar({ name: 'blue/500', values: { Value: '#3B82F6' } })

const semantic = $fig.varCollection({ name: 'Semantic', modes: ['Light', 'Dark'] })
const bgPrimary = semantic.colorVar({
  name: 'bg/primary',
  values: { Light: blue500, Dark: blue500 },  // alias to primitive
  scopes: ['SHAPE_FILL'],
})

await $fig.done()
```

#### Updating after creation

```javascript
// Update any property — name, scopes, description, codeSyntax, etc.
myVar.set({ codeSyntax: { WEB: 'var(--size-lg)' } })
myVar.set({ scopes: ['WIDTH_HEIGHT', 'GAP'] })

// Update a single mode value
myVar.value('Dark', '#1E3A5F')

// Update all mode values at once
myVar.setValues({ Light: 16, Dark: 24 })
// Or with an updater fn (receives the live Variable; return value is modeId-keyed)
myVar.setValues(v => ({ ...v.valuesByMode, [darkModeId]: 24 }))
```

#### Scope reference

`variable.scopes` controls which Figma property pickers show the variable. **Always set scopes explicitly** — the default `["ALL_SCOPES"]` shows the variable everywhere, which is almost never correct.

**All valid scope values:**
`ALL_SCOPES`, `TEXT_CONTENT`, `CORNER_RADIUS`, `WIDTH_HEIGHT`, `GAP`, `ALL_FILLS`, `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL`, `STROKE_COLOR`, `STROKE_FLOAT`, `EFFECT_FLOAT`, `EFFECT_COLOR`, `OPACITY`, `FONT_FAMILY`, `FONT_STYLE`, `FONT_WEIGHT`, `FONT_SIZE`, `LINE_HEIGHT`, `LETTER_SPACING`, `PARAGRAPH_SPACING`, `PARAGRAPH_INDENT`

For a comprehensive scope-to-use-case mapping table, see token-creation.md § Variable Scopes — Complete Reference Table (load `readPowerSteering("figma", "figma-generate-library.md")`).

**Always check the existing file's scope patterns before creating variables** — match whatever convention is already in use. See [Discovering existing variables in the file](#discovering-existing-variables-in-the-file).

---

### Binding variables to node properties with `$fig`

Pass a variable handle directly as the property value. `$fig` routes it to the correct `setBoundVariable` / `setBoundVariableForPaint` / `setBoundVariableForEffect` call at flush time.

```javascript
const tokens = $fig.varCollection({ name: 'Tokens', modes: ['Light', 'Dark'] })
const blue = tokens.colorVar({ name: 'color/brand', values: { Light: '#3B82F6', Dark: '#60A5FA' }, scopes: ['SHAPE_FILL', 'STROKE_COLOR'] })
const w = tokens.numVar({ name: 'size/lg', values: { Light: 200, Dark: 200 }, scopes: ['WIDTH_HEIGHT'] })
const alpha = tokens.numVar({ name: 'opacity/btn', values: { Light: 1, Dark: 0.8 }, scopes: ['OPACITY'] })
const radius = tokens.numVar({ name: 'radius/lg', values: { Light: 8, Dark: 8 }, scopes: ['CORNER_RADIUS'] })
const tlRadius = tokens.numVar({ name: 'radius/tl', values: { Light: 4, Dark: 4 }, scopes: ['CORNER_RADIUS'] })
const gap = tokens.numVar({ name: 'gap/md', values: { Light: 16, Dark: 16 }, scopes: ['GAP'] })
const shadowColor = tokens.colorVar({ name: 'shadow/color', values: { Light: '#000', Dark: '#1A1A2E' }, scopes: ['EFFECT_COLOR'] })
const shadowBlur = tokens.numVar({ name: 'shadow/blur', values: { Light: 8, Dark: 12 }, scopes: ['EFFECT_FLOAT'] })

// Scalar numeric props
$fig.rectangle({ name: 'Card', width: w, height: w, opacity: alpha })

// cornerRadius shorthand — binds all four individual corners to the same variable
// (there is no boundVariables.cornerRadius slot; Figma exposes per-corner bindings only)
$fig.rectangle({ name: 'Pill', cornerRadius: radius })

// Individual corners override the shorthand when both are present
$fig.rectangle({ name: 'Card', cornerRadius: radius, topLeftRadius: tlRadius })

// Paint color — pass the variable handle as the `color` field of a paint object
$fig.rectangle({
  name: 'Chip',
  fills: [{ type: 'SOLID', color: blue }],
  strokes: [{ type: 'SOLID', color: blue }],
})

// Effects — variable handles in color/radius/spread/offsetX/offsetY fields
$fig.frame({
  name: 'Card',
  effects: [{
    type: 'DROP_SHADOW',
    color: shadowColor,
    radius: shadowBlur,
    offset: { x: 0, y: 4 },
    spread: 0,
    visible: true,
    blendMode: 'NORMAL',
  }],
})

// Layout grids — sectionSize and count accept numVar handles
$fig.frame({
  name: 'Grid',
  effects: [],
  layoutGrids: [{
    pattern: 'COLUMNS',
    sectionSize: gap,
    count: gap,
    gutterSize: 8,
    alignment: 'CENTER',
    visible: true,
  }],
})

// Padding / gap on auto-layout frames
$fig.frame({
  name: 'AutoLayout',
  layoutMode: 'HORIZONTAL',
  paddingLeft: gap, paddingRight: gap, paddingTop: gap, paddingBottom: gap,
  itemSpacing: gap,
})

await $fig.done()
```

**Not bindable via `$fig` node properties:** `fontSize`, `fontWeight`, `lineHeight` — set these directly on text nodes.

#### Applying a mode to a frame (raw API)

`setExplicitVariableModeForCollection` is not supported by `$fig` — use the raw API after `done()`:

```javascript
await $fig.done()
const frame = figma.getNodeById(myFrame.id)
frame.setExplicitVariableModeForCollection(tokens.variableCollection, darkModeId)
// All variable-bound children of this frame will now resolve to the Dark mode values.
```

---

### Using library variables by key (preferred)

`search_design_system` with `includeVariables: true` returns a `key` per variable. Pass it directly into `$fig.getVar(variableKey)` — the plan queues the library import automatically. Same call also accepts a local variable id; one call site, both shapes.

```javascript
const brand = $fig.getVar(BRAND_COLOR_VAR_KEY)
$fig.rectangle({ fills: [{ type: 'SOLID', color: brand }] })

// Scalar variable on any numeric property
const gap = $fig.getVar(SPACING_400_KEY)
$fig.autoLayout({ name: 'Toolbar', layoutMode: 'HORIZONTAL', itemSpacing: gap })
```

### Raw-API fallback — discovering and importing variables manually

Use this when you need to enumerate a library's variables before deciding which to use, or when `$fig` genuinely cannot express the operation:

```javascript
// List available library collections
const libCollections = await figma.teamLibrary.getAvailableLibraryVariableCollectionsAsync()
// Each has: name, key, libraryName

// Get variables in a specific library collection
const libVars = await figma.teamLibrary.getVariablesInLibraryCollectionAsync(libCollections[0].key)
// Each has: name, key, resolvedType

// Import via raw plugin API, then use like a local variable
const imported = await figma.variables.importVariableByKeyAsync(libVars[0].key)
const paint = figma.variables.setBoundVariableForPaint(
  { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', imported
)
node.fills = [paint]
```

**When to import vs. use local:** If `variable.remote === true`, it's from a library — pass the `key` to `$fig.getVar(key)` (or use raw `importVariableByKeyAsync` if you need the variable mid-script for some other decision). If `remote === false`, it's local — use `getVariableByIdAsync` or `$fig.getVar(id)` directly. The `$fig.getVar` call accepts both id and key.

#### Discovering existing variables in the file

**Always inspect the file's existing variables before creating new ones.** Match naming conventions, scope patterns, and collection structures already in use.

##### List collections with mode and variable details

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync()
const results = []
for (const collection of collections) {
  const vars = []
  for (const id of collection.variableIds) {
    const v = await figma.variables.getVariableByIdAsync(id)
    vars.push([v.name, v.id, v.codeSyntax, v.scopes])
  }
  results.push({
    name: collection.name,
    id: collection.id,
    modes: collection.modes.map(m => [m.name, m.modeId]),
    variables: vars,
  })
}
return results
```

##### Inspect scope patterns in use

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync()
const scopeGroups = {}
for (const c of collections) {
  for (const id of c.variableIds) {
    const v = await figma.variables.getVariableByIdAsync(id)
    const key = JSON.stringify(v.scopes)
    if (!scopeGroups[key]) scopeGroups[key] = []
    scopeGroups[key].push(v.name)
  }
}
return scopeGroups
```

##### Build a name→variable lookup for reuse

```javascript
const varByName = {}
for (const v of await figma.variables.getLocalVariablesAsync()) {
  varByName[v.name] = v
}
// Only create new variables for tokens that have no match
```

#### Removing code syntax

`$fig` has no equivalent for removing a platform from a variable's `codeSyntax`. Use the raw API:

```javascript
const variable = await figma.variables.getVariableByIdAsync(variableId)
variable.removeVariableCodeSyntax('WEB')    // remove one platform
variable.removeVariableCodeSyntax('ANDROID')
variable.removeVariableCodeSyntax('iOS')
```

**When deriving CSS names from Figma names**, replace both slashes AND spaces with hyphens:

```javascript
// WRONG — leaves spaces in CSS variable name
`var(--${figmaName.replace(/\//g, '-').toLowerCase()})`

// CORRECT
`var(--${figmaName.replace(/[\s\/]+/g, '-').toLowerCase()})`

// BEST — use the original CSS variable name from the source, not a derived one
`var(${token.cssVar})`
```

---

### Effect Styles (For Shadows)

Shadows can't be stored as variables. Use effect styles. For comprehensive patterns, see [Effect Style API Patterns](#reference--effect-style-api-patterns).

```javascript
const shadow = figma.createEffectStyle()
shadow.name = 'Shadow/Subtle'
shadow.effects = [{
  type: 'DROP_SHADOW',
  color: { r: 0, g: 0, b: 0, a: 0.06 },
  offset: { x: 0, y: 2 },
  radius: 8,
  spread: 0,
  visible: true,
  blendMode: 'NORMAL',
}]

// Apply to a node
frame.effectStyleId = shadow.id
```

---

## Reference — Text Style API Patterns

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). How to create, apply, and inspect text styles using the Plugin API.
>
> For design system context (when to create text styles, how they relate to tokens, `use_figma` limitations), see [wwds-text-styles](#reference--working-with-design-systems-text-styles).

### Prefer `$fig` for creation + binding

For new text styles + binding them to text nodes, reach for `$fig` first — fonts preload automatically, the style and the binding go in the same plan, and the binding uses the natural `textStyle` property (no `*StyleId` suffix to remember):

```javascript
const heading = $fig.textStyle({
  name: "Heading/1",
  fontName: { family: "Inter", style: "Bold" },
  fontSize: 48,
})
$fig.text({ characters: "Title", textStyle: heading })
```

See [`$fig` Builder API](#styles---create-reference-apply) for the full surface (`paintStyle` / `textStyle` / `effectStyle` / `gridStyle` / `getStyle`, the `FigPlanStyle` handle methods, and the `fills` / `strokes` / `effects` / `layoutGrids` / `textStyle` property routing).

The raw Plugin API patterns below are the fallback for when you genuinely need to interleave style ops with mid-script async calls or read computed properties off the live `TextStyle` before deciding what to do next.

### Contents

- Listing Text Styles
- Creating a Text Style
- Discovering Available Font Styles
- Creating a Type Ramp (Multi-Step)
- Importing Library Text Styles
- Applying Text Styles to Nodes

### Listing Text Styles

```javascript
/**
 * Lists all local text styles with their key properties.
 *
 * @returns {Promise<Array<{id: string, name: string, key: string, fontSize: number, fontName: FontName, lineHeight: LineHeight, letterSpacing: LetterSpacing}>>}
 */
async function listTextStyles() {
  const styles = await figma.getLocalTextStylesAsync();
  return styles.map(s => ({
    id: s.id,
    name: s.name,
    key: s.key,
    fontSize: s.fontSize,
    fontName: s.fontName,
    lineHeight: s.lineHeight,
    letterSpacing: s.letterSpacing
  }));
}
```

Full runnable script:

```javascript
const results = await listTextStyles();
return results;
```

### Creating a Text Style

Font **MUST** be loaded before setting `fontName`. `lineHeight` and `letterSpacing` must be `{value, unit}` objects — bare numbers throw.

```javascript
/**
 * Creates a text style with all typographic properties set.
 * Font MUST be loaded before calling.
 *
 * @param {string} name - Slash-delimited name, e.g. "body/base"
 * @param {{ family: string, style: string }} fontName
 * @param {number} fontSize - In pixels
 * @param {{ value: number, unit: 'PIXELS' | 'PERCENT' } | { unit: 'AUTO' }} lineHeight
 * @param {{ value: number, unit: 'PIXELS' | 'PERCENT' }} [letterSpacing]
 * @param {string} [description] - e.g. the CSS variable name "CSS: var(--font-body-base)"
 * @returns {TextStyle}
 */
function createTextStyleFull(name, fontName, fontSize, lineHeight, letterSpacing, description) {
  const style = figma.createTextStyle();
  style.name = name;
  style.fontName = fontName;
  style.fontSize = fontSize;
  style.lineHeight = lineHeight; // { unit: 'AUTO' } | { value, unit: 'PIXELS'|'PERCENT' }
  if (letterSpacing) style.letterSpacing = letterSpacing;
  if (description) style.description = description;
  return style;
}
```

### Discovering Available Font Styles

Font style names vary per provider and per file.  Use `figma.listAvailableFontsAsync()` to discover exact style strings — never guess or probe with try/catch:

```javascript
/**
 * Discovers available font styles for a given family using listAvailableFontsAsync.
 *
 * @param {string} family - Font family name, e.g. "Inter"
 * @returns {Promise<string[]>} - All available style names for the family
 */
async function getAvailableFontStyles(family) {
  const allFonts = await figma.listAvailableFontsAsync();
  return allFonts
    .filter(f => f.fontName.family === family)
    .map(f => f.fontName.style);
}
```

### Creating a Type Ramp (Multi-Step)

Handles font loading, deduplication, and idempotency. Each entry: `[name, fontFamily, fontStyle, fontSize_px, lineHeight, cssVar]`.

```javascript
/**
 * Creates a full type ramp from a token definition array.
 * Handles font loading, deduplication, and idempotency.
 *
 * Each entry: [name, fontFamily, fontStyle, fontSize_px, lineHeight, cssVar]
 *   - lineHeight: { unit: 'AUTO' } or { value: number, unit: 'PIXELS' | 'PERCENT' }
 *
 * @param {Array} defs - Array of [name, fontFamily, fontStyle, fontSize, lineHeight, cssVar] tuples
 * @returns {Promise<{ created: string[], skipped: string[] }>}
 */
async function createTypeRamp(defs) {
  const uniqueFonts = new Set();
  for (const [, family, style] of defs) {
    uniqueFonts.add(JSON.stringify({ family, style }));
  }
  await Promise.all(
    [...uniqueFonts].map(f => figma.loadFontAsync(JSON.parse(f)))
  );

  const existing = new Set(
    (await figma.getLocalTextStylesAsync()).map(s => s.name)
  );

  const created = [];
  const skipped = [];

  for (const [name, family, style, fontSize, lineHeight, cssVar] of defs) {
    if (existing.has(name)) {
      skipped.push(name);
      continue;
    }
    const ts = figma.createTextStyle();
    ts.name = name;
    ts.fontName = { family, style };
    ts.fontSize = fontSize;
    ts.lineHeight = lineHeight ?? { unit: 'AUTO' };
    if (cssVar) ts.description = `CSS: var(${cssVar})`;
    created.push(name);
  }

  return { created, skipped };
}
```

Full runnable script:

```javascript
const defs = [
  ['heading/xl', 'Inter', 'Bold',      48, { unit: 'PIXELS', value: 56 }, '--font-heading-xl'],
  ['heading/lg', 'Inter', 'Bold',      36, { unit: 'PIXELS', value: 44 }, '--font-heading-lg'],
  ['body/base',  'Inter', 'Regular',   16, { unit: 'AUTO' },              '--font-body-base'],
  ['body/sm',    'Inter', 'Regular',   14, { unit: 'AUTO' },              '--font-body-sm'],
  ['code/base',  'Roboto Mono', 'Regular', 14, { unit: 'AUTO' },          '--font-code-base'],
];
const result = await createTypeRamp(defs);
return result;
```

### Using Library Text Styles by key (preferred)

`search_design_system` with `includeStyles: true` returns a `key` per style. Pass it directly into `$fig.getStyle(styleKey)` and apply via the `textStyle` property on any `$fig.text(...)` / `$fig.query('TEXT').set(...)` — the plan queues the library import automatically.

```javascript
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY)
$fig.text({ characters: 'Title', textStyle: heading })

// Bulk apply to existing text nodes
$fig.query('TEXT[name=Heading]').set({ textStyle: heading })
```

Prefer reusing library text styles over creating new ones.

#### Raw-API fallback

```javascript
// If you need the imported TextStyle's metadata mid-script
const headingStyle = await figma.importStyleByKeyAsync("TEXT_STYLE_KEY");
await textNode.setTextStyleIdAsync(headingStyle.id);
```

### Applying Text Styles to Nodes

Prefer `$fig.query(...).set({ textStyle })` over `findAllWithCriteria` + a manual loop — the selector matches name patterns directly, and `$fig` batches the writes and resolves the style id at flush time. The `textStyle` property accepts a `$fig.getStyle(...)` handle (local id OR library `key` from `search_design_system`) or a raw style id string.

```javascript
// Library style by key — $fig queues the import; no separate await needed.
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY)

// Apply to every TEXT whose name contains 'Heading' on the current page
const result = $fig.query('TEXT[name*=Heading]').set({ textStyle: heading })
return { applied: result.length }
```

Scope to a subtree or another page via a second arg / a parent handle:

```javascript
// Scoped to one frame
const card = $fig.get('1:42')
$fig.query('TEXT[name*=Heading]', card).set({ textStyle: heading })

// Across the whole document (all pages)
$fig.query('TEXT[name*=Heading]', figma.root).set({ textStyle: heading })
```

If you already have a local style id (not a key) and don't want a `$fig.getStyle` wrap, the raw setter still works:

```javascript
$fig.query('TEXT[name*=Heading]').each(async (n) => {
  await n.node?.setTextStyleIdAsync('STYLE_ID')   // only after $fig.done() / auto-flush
})
```

---

## Reference — Effect Style API Patterns

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). How to create, apply, and inspect effect styles using the Plugin API.
>
> For design system context (effect types, variable bindings on effects, gotchas), see [wwds-effect-styles](#reference--working-with-design-systems-effect-styles).

### Prefer `$fig` for creation + binding

For new effect styles + binding them to nodes, reach for `$fig` first — the style and the binding go in the same plan, and the binding uses the natural `effects` property (no `*StyleId` suffix):

```javascript
const shadow = $fig.effectStyle({
  name: "Shadow/Soft",
  effects: [{
    type: "DROP_SHADOW",
    color: { r: 0, g: 0, b: 0, a: 0.3 },
    offset: { x: 0, y: 4 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: "NORMAL",
  }],
})
$fig.rectangle({ name: "Card", effects: shadow })
```

See [`$fig` Builder API](#styles---create-reference-apply) for the full surface.

The raw Plugin API patterns below are the fallback for when you genuinely need to interleave style ops with mid-script async calls or read computed properties off the live `EffectStyle` before deciding what to do next.

### Contents

- Listing Effect Styles
- Creating a Drop Shadow Style
- Importing Library Effect Styles
- Applying Effect Styles to Nodes

### Listing Effect Styles

```javascript
/**
 * Lists all local effect styles.
 *
 * @returns {Promise<Array<{id: string, name: string, key: string, effectCount: number}>>}
 */
async function listEffectStyles() {
  const styles = await figma.getLocalEffectStylesAsync();
  return styles.map(s => ({
    id: s.id,
    name: s.name,
    key: s.key,
    effectCount: s.effects.length
  }));
}
```

Full runnable script:

```javascript
const results = await listEffectStyles();
return results;
```

### Creating a Drop Shadow Style

Colors are **RGBA 0–1 range**. `effects` is a read-only array — always reassign, never mutate in place.

```javascript
/**
 * Creates a drop shadow effect style.
 *
 * @param {string} name - e.g. "Elevation/200"
 * @param {{ r: number, g: number, b: number, a: number }} color - RGBA, 0-1 range
 * @param {{ x: number, y: number }} offset
 * @param {number} radius - blur radius
 * @param {number} [spread=0]
 * @returns {EffectStyle}
 */
function createDropShadowStyle(name, color, offset, radius, spread) {
  const style = figma.createEffectStyle();
  style.name = name;
  style.effects = [{
    type: "DROP_SHADOW",
    color,
    offset,
    radius,
    spread: spread || 0,
    visible: true,
    blendMode: "NORMAL"
  }];
  return style;
}
```

Full runnable script:

```javascript
const style = createDropShadowStyle(
  "Elevation/200",
  { r: 0, g: 0, b: 0, a: 0.15 },
  { x: 0, y: 4 },
  12,
  0
);
return { id: style.id, name: style.name };
```

### Using Library Effect Styles by key (preferred)

`search_design_system` with `includeStyles: true` returns a `key` per style. Pass it directly into `$fig.getStyle(styleKey)` and apply via the `effects` property on any `$fig.rectangle(...)` / `$fig.frame(...)` / `$fig.query(...).set(...)` — the plan queues the library import automatically.

```javascript
const shadow = $fig.getStyle(ELEVATION_200_KEY)
$fig.frame({ name: 'Card', effects: shadow })

// Bulk apply
$fig.query('FRAME[name=Card]').set({ effects: shadow })
```

Prefer reusing library effect styles over creating new ones.

#### Raw-API fallback

```javascript
// If you need the imported EffectStyle's metadata mid-script
const shadowStyle = await figma.importStyleByKeyAsync("EFFECT_STYLE_KEY");
node.effectStyleId = shadowStyle.id;
```

### Applying Effect Styles to Nodes

```javascript
/**
 * Applies an effect style to all nodes on the current page that match a given name pattern.
 *
 * @param {string} styleId - The ID of an EffectStyle.
 * @param {string} nodeNamePattern - Substring match against node names.
 * @returns {number} - Number of nodes the style was applied to.
 */
function applyEffectStyleToMatchingNodes(styleId, nodeNamePattern) {
  const nodes = figma.currentPage.findAll(n => n.name.includes(nodeNamePattern));
  let applied = 0;
  for (const node of nodes) {
    if ('effectStyleId' in node) {
      node.effectStyleId = styleId;
      applied++;
    }
  }
  return applied;
}
```

Full runnable script:

```javascript
const applied = applyEffectStyleToMatchingNodes('STYLE_ID', 'Card');
return { applied };
```

---

## Reference — Validation Workflow & Error Recovery

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). How to debug, validate, and recover from errors.

### Contents

- `get_metadata` vs `get_screenshot`
- Error Recovery After Failed `use_figma`
- Recommended Workflow


### `get_metadata` vs `get_screenshot`

After each `use_figma` call, validate results using the right tool for the job. Do NOT reach for `get_screenshot` every time — it is expensive and should be reserved for visual checks.

#### `get_metadata` — Use for intermediate validation (preferred)

`get_metadata` returns an XML tree of node IDs, types, names, positions, and sizes. Use it to confirm:

- **Structure & hierarchy**: correct parent-child relationships, component nesting, section contents
- **Node counts**: expected number of variants created, children present
- **Naming**: variant property names follow the `property=value` convention
- **Positioning & alignment**: x/y coordinates, width/height values match expectations
- **Layout properties**: auto-layout direction, sizing mode, padding, spacing
- **Component set membership**: all expected variants are inside the ComponentSet

```
Example: After creating a ComponentSet with 120 variants, call get_metadata on the
ComponentSet node to verify all 120 children exist with correct names, sizes, and positions
— without waiting for a full render.
```

**When to use `get_metadata`:**
- After creating/modifying nodes — to verify structure, counts, and names
- After layout operations — to verify positions and dimensions
- After combining variants — to confirm all components are in the ComponentSet
- After binding variables — to verify node properties (use use_figma to read bound variables if needed)
- Between multi-step workflows — to confirm step N succeeded before starting step N+1

#### `get_screenshot` — Use after each major creation milestone

`get_screenshot` renders a pixel-accurate image. It is the only way to verify visual correctness (colors, typography rendering, effects, variable mode resolution). It is slower and produces large responses, so don't call it after every single `use_figma` — but do call it after each major milestone to catch visual problems early.

**When to use `get_screenshot`:**
- **After creating a component set** — verify variants look correct, grid is readable, nothing is collapsed or overlapping
- **After composing a layout** — verify overall structure and spacing
- **After binding variables/modes** — verify colors and tokens resolved correctly
- **After any fix or recovery** — verify the fix didn't introduce new visual issues
- **Before reporting results to the user** — final visual proof

**What to look for in screenshots** — these are the most commonly missed issues:
- **Cropped/clipped text** — line heights or frame sizing cutting off descenders, ascenders, or entire lines
- **Overlapping content** — elements stacking on top of each other due to incorrect sizing or missing auto-layout
- **Placeholder text** still showing ("Title", "Heading", "Button") instead of actual content

### Error Recovery After Failed `use_figma`

**`use_figma` is atomic — failed scripts do not execute.** If a script errors, no changes are made to the file. The file remains in exactly the same state as before the call. There are no partial nodes, no orphaned elements, and retrying after a fix is safe.

**Recovery steps when `use_figma` returns an error:**
1. **STOP — do NOT immediately fix the code and retry.** Read the error message carefully first.
2. **Understand the error.** Most errors are caused by wrong API usage, missing font loads, invalid property values, or referencing nodes that don't exist.
3. **If the error is unclear**, call `get_metadata` or `get_screenshot` to understand the current file state and confirm nothing has changed.
4. **Fix the script** based on the error message.
5. **Retry** the corrected script.

### Recommended Workflow

```
1. use_figma  →  Create/modify nodes
2. get_metadata     →  Verify structure, counts, names, positions (fast, cheap)
3. use_figma  →  Fix any structural issues found
4. get_metadata     →  Re-verify fixes
5. ... repeat as needed ...
6. get_screenshot   →  Visual check after each major milestone

⚠️ ON ERROR at any step:
   a. Read the error message carefully
   b. get_metadata / get_screenshot  →  If the error is unclear, inspect file state
   c. Fix the script based on the error
   d. Retry the corrected script (safe — failed scripts don't modify the file)
```

---

## Reference — Figma Plugin API Reference

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). What works and what doesn't in the `use_figma` environment.

### Contents

- Node Creation
- Grouping and Boolean Operations
- Library Imports
- Variables API
- Core Properties
- Node Manipulation
- Descriptions and Documentation Links
- SVG and Images
- Utilities and Plugin Lifecycle
- Node Traversal
- Unsupported APIs


### Node Creation (Design Mode)

```js
figma.createRectangle()
figma.createFrame()
figma.createAutoLayout()        // Frame with auto layout enabled, both axes hug — prefer over createFrame() for layout containers
figma.createAutoLayout("VERTICAL") // Same but vertical direction
figma.createComponent()         // Creates a ComponentNode
figma.createText()
figma.createEllipse()
figma.createStar()
figma.createLine()
figma.createVector()
figma.createPolygon()
figma.createBooleanOperation()
figma.createSlice()
figma.createPage()              // Page node can be created, but child persistence is limited in use_figma
figma.createSection()
figma.createTextPath()
```

### Grouping & Boolean Operations

```js
figma.group(nodes, parent, index?)              // Group nodes
figma.flatten(nodes, parent?, index?)           // Flatten to vector
figma.union(nodes, parent?, index?)             // Boolean union
figma.subtract(nodes, parent?, index?)          // Boolean subtract
figma.intersect(nodes, parent?, index?)         // Boolean intersect
figma.exclude(nodes, parent?, index?)           // Boolean exclude
figma.combineAsVariants(components, parent?)    // Combine ComponentNodes into ComponentSet (Design/Sites only)
```

### Library Component / Style / Variable Lookup by Key

`search_design_system` returns `componentKey` for components / component sets and `key` for styles and variables. Pass any of these straight into the unified `$fig` lookup — the plan queues the library import automatically. Same call sites also accept node IDs and real style / variable IDs for assets already in the current file.

```js
// Components / component sets
const comp     = $fig.get(COMPONENT_KEY)                       // wrap a component / set
const instance = $fig.instance(COMPONENT_SET_KEY, {            // instance + variant props
  props: { Size: 'md', Variant: 'primary' },
})

// Styles (paint / text / effect / grid)
const fill   = $fig.getStyle(PAINT_STYLE_KEY)
$fig.rectangle({ fills: fill })
$fig.text({ characters: 'Title', textStyle: $fig.getStyle(TEXT_STYLE_KEY) })
$fig.frame({ effects: $fig.getStyle(EFFECT_STYLE_KEY) })

// Variables
const brand = $fig.getVar(BRAND_COLOR_VAR_KEY)
$fig.rectangle({ fills: [{ type: 'SOLID', color: brand }] })
$fig.autoLayout({ itemSpacing: $fig.getVar(SPACING_400_KEY) })
```

For component sets, pass the variant property values in `props` — `$fig.instance` resolves them via the underlying `setProperties` after creating the instance from `defaultVariant`. You do not need to import the set, drill into `compSet.children`, or pick a variant child by hand.

#### Raw-API fallback for styles + variables (mid-script metadata)

When you need an imported style's or variable's metadata before deciding what to build next, the raw plugin APIs are still legal. Use sparingly — most flows are simpler via `$fig.getStyle(key)` / `$fig.getVar(key)`.

```js
// Styles
const style = await figma.importStyleByKeyAsync("STYLE_KEY")
await node.setFillStyleIdAsync(style.id)
await node.setTextStyleIdAsync(style.id)
await node.setEffectStyleIdAsync(style.id)
await node.setGridStyleIdAsync(style.id)

// Variables
const variable = await figma.variables.importVariableByKeyAsync("VARIABLE_KEY")
node.setBoundVariable("width", variable)
const newPaint = figma.variables.setBoundVariableForPaint(paintCopy, "color", variable)
node.fills = [newPaint]
```

### Variables API

```js
// Collections
const collection = figma.variables.createVariableCollection("Name")
collection.name                           // Get/set name
collection.modes                          // Array of {modeId, name} — starts with 1 mode
collection.addMode("Dark")               // Returns new modeId string
collection.renameMode(modeId, "Light")

// Variables
const variable = figma.variables.createVariable("name", collection, "COLOR")
//                                                       ^ must be a collection object (passing an ID string is deprecated)
// resolvedType: "COLOR" | "FLOAT" | "STRING" | "BOOLEAN"
variable.setValueForMode(modeId, value)

// Scopes — controls where variable appears in property pickers
variable.scopes = ["FRAME_FILL", "SHAPE_FILL"]   // only fill pickers
variable.scopes = ["TEXT_FILL"]                    // only text color picker
variable.scopes = ["STROKE_COLOR"]                 // only stroke picker
variable.scopes = []                               // hidden from all pickers (use for primitives)
// All valid scope values:
//   ALL_SCOPES, TEXT_CONTENT, CORNER_RADIUS, WIDTH_HEIGHT, GAP,
//   ALL_FILLS, FRAME_FILL, SHAPE_FILL, TEXT_FILL,
//   STROKE_COLOR, STROKE_FLOAT, EFFECT_FLOAT, EFFECT_COLOR,
//   OPACITY, FONT_FAMILY, FONT_STYLE, FONT_WEIGHT, FONT_SIZE,
//   LINE_HEIGHT, LETTER_SPACING, PARAGRAPH_SPACING, PARAGRAPH_INDENT

// Querying (always use the Async variants — sync versions are deprecated)
await figma.variables.getVariableByIdAsync(id)
await figma.variables.getLocalVariablesAsync(resolvedType?)
await figma.variables.getVariableCollectionByIdAsync(id)
await figma.variables.getLocalVariableCollectionsAsync()

// Binding variables to paints (COLOR variables)
const newPaint = figma.variables.setBoundVariableForPaint(paintCopy, "color", variable)
// ⚠️ Returns a NEW paint — must capture return value!
node.fills = [newPaint]

// Binding variables to effects (COLOR/FLOAT variables)
const newEffect = figma.variables.setBoundVariableForEffect(effectCopy, field, variable)
// field for shadows: "color" (COLOR), "radius" | "spread" | "offsetX" | "offsetY" (FLOAT)
// field for blurs: "radius" (FLOAT)
// ⚠️ Returns a NEW effect — must capture return value!
node.effects = [newEffect]

// Binding variables to layout grids (FLOAT variables)
const newGrid = figma.variables.setBoundVariableForLayoutGrid(gridCopy, field, variable)
// field: "sectionSize" | "offset" | "count" | "gutterSize"
// ⚠️ Returns a NEW layout grid — must capture return value!
node.layoutGrids = [newGrid]

// Binding variables to node properties (FLOAT/STRING/BOOLEAN)
// Layout & sizing (FLOAT):
node.setBoundVariable("width", variable)
node.setBoundVariable("height", variable)
node.setBoundVariable("minWidth", variable)
node.setBoundVariable("maxWidth", variable)
node.setBoundVariable("minHeight", variable)
node.setBoundVariable("maxHeight", variable)
node.setBoundVariable("paddingLeft", variable)
node.setBoundVariable("paddingRight", variable)
node.setBoundVariable("paddingTop", variable)
node.setBoundVariable("paddingBottom", variable)
node.setBoundVariable("itemSpacing", variable)
node.setBoundVariable("counterAxisSpacing", variable)
// Corner radii (FLOAT) — use individual corners, NOT cornerRadius:
node.setBoundVariable("topLeftRadius", variable)
node.setBoundVariable("topRightRadius", variable)
node.setBoundVariable("bottomLeftRadius", variable)
node.setBoundVariable("bottomRightRadius", variable)
// Other (FLOAT):
node.setBoundVariable("opacity", variable)
node.setBoundVariable("strokeWeight", variable)
// ⚠️ fontSize, fontWeight, lineHeight are NOT bindable via setBoundVariable
// — set these directly as values on text nodes

// Aliases
figma.variables.createVariableAlias(variable)

// Explicit modes — CRITICAL for variant components
node.setExplicitVariableModeForCollection(collection, modeId)  // pass collection object, NOT an ID string
// Without this, all nodes use the default (first) mode of the collection
```

### Core Properties

```js
figma.root                      // DocumentNode
figma.currentPage               // Current page — READ ONLY; the sync setter (figma.currentPage = page) does NOT work and throws
figma.setCurrentPageAsync(page) // Switch page and load its content (MUST await) — this is the ONLY way to change pages
figma.fileKey                   // File key string
figma.mixed                     // Mixed sentinel value
```

### Node Manipulation

```js
// Fills & Strokes (read-only arrays — must clone)
node.fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
node.strokes = [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }]
node.strokeWeight = 1
node.strokeAlign = 'INSIDE'             // 'INSIDE' | 'CENTER' | 'OUTSIDE'

// Effects
node.effects = [{ type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.25}, offset:{x:0,y:4}, radius:4, visible:true }]

// Layout
node.layoutMode = 'HORIZONTAL'          // 'NONE' | 'HORIZONTAL' | 'VERTICAL'
node.primaryAxisAlignItems = 'CENTER'    // 'MIN' | 'CENTER' | 'MAX' | 'SPACE_BETWEEN'
node.counterAxisAlignItems = 'CENTER'    // 'MIN' | 'CENTER' | 'MAX' | 'BASELINE'
node.paddingLeft = 8
node.paddingRight = 8
node.paddingTop = 4
node.paddingBottom = 4
node.itemSpacing = 4
node.layoutSizingHorizontal = 'HUG'     // 'FIXED' | 'HUG' | 'FILL'
node.layoutSizingVertical = 'HUG'       // 'FIXED' | 'HUG' | 'FILL'

// Sizing
node.resize(width, height)                     // ⚠️ Resets sizing modes to FIXED
node.resizeWithoutConstraints(width, height)   // Doesn't affect constraints

// Corner radius
node.cornerRadius = 8

// Visibility & Opacity
node.visible = true
node.opacity = 0.5

// Naming & Hierarchy
node.name = "My Node"
parent.appendChild(child)
parent.insertChild(index, child)
node.remove()
```

### Descriptions & Documentation Links

```js
// Description — plain text, shown in Figma's component panel
node.description = "A short summary of this component's purpose and usage."

// Documentation links — array of {uri, label} shown as clickable links
componentSet.documentationLinks = [
  { uri: "https://example.com/docs", label: "Component Docs" }
]
// ⚠️ uri MUST be a valid URL (https://...) — relative paths will throw
```

### SVG Import

```js
const svgNode = figma.createNodeFromSvg('<svg>...</svg>')
```

### Images

```js
const image = figma.createImage(uint8Array)
node.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: image.hash }]
```

### Fonts

```js
// Discover all available fonts and their exact style strings
const allFonts = await figma.listAvailableFontsAsync()  // Font[] — each has { fontName: { family, style } }
const interStyles = allFonts.filter(f => f.fontName.family === "Inter")

// MUST load a font before any text property edit
await figma.loadFontAsync({ family: "Inter", style: "Regular" })

// Check if the file has missing fonts
figma.hasMissingFont  // boolean
```

### Utilities

```js
figma.base64Encode(uint8Array)     // Uint8Array → base64 string
figma.base64Decode(base64String)   // base64 string → Uint8Array
figma.createComponentFromNode(node) // Convert existing node to component (Design/Sites only)
```

### Plugin Lifecycle

Scripts are automatically wrapped in an async IIFE with error handling. Use `return` to send data back:

```js
return { nodeId: frame.id }     // Return object — auto-serialized to JSON
return "success message"        // Return string
// Errors are auto-captured — no try/catch or closePlugin needed
```

### Node Traversal

```js
node.findAll(pred?)            // Find all descendants matching predicate
node.findOne(pred?)            // Find first descendant matching predicate
node.findChildren(pred?)       // Find direct children matching predicate
node.findChild(pred?)          // Find first direct child matching predicate
node.children                  // Direct children array
node.parent                    // Parent node
```

---

### What Does NOT Work

| API | Status |
|-----|--------|
| `figma.notify()` | **Throws "not implemented"** — most common mistake |
| `figma.showUI()` | No-op (silently ignored) |
| `figma.openExternal()` | No-op (silently ignored) |
| `figma.loadAllPagesAsync()` | Not implemented |
| `figma.variables.extendLibraryCollectionByKeyAsync()` | Not implemented |
| `figma.teamLibrary.*` | Not implemented (requires LiveGraph) |
| `figma.getLocalComponents*()` | **Does not exist** — unlike styles, there is no `getLocalComponents()` or `getLocalComponentSetsAsync()` (or any `getLocalComponent*` variant). Use `findAll(n => n.type === 'COMPONENT')` / `findAll(n => n.type === 'COMPONENT_SET')` to locate components in the current file. |

---

## Reference — Plugin API Patterns

> Part of the [use_figma skill](#use_figma--figma-plugin-api-skill). Quick reference for common Figma Plugin API operations.

### Contents

- Execution Basics
- Creating Nodes
- Fills and Strokes
- Auto Layout
- Effects
- Opacity and Blend Modes
- Corner Radius and Clipping
- Grouping and Organization
- Components and Variants
- Styles
- Cloning, Finding Nodes, and Grids
- Constraints and Viewport


### Execution Basics

#### Page Context

Page context resets between `use_figma` calls — `figma.currentPage` always starts on the first page. Use `await figma.setCurrentPageAsync(page)` at the start of each invocation to switch to the correct page. The sync setter `figma.currentPage = page` does **NOT work** and will throw — always use the async method.

```javascript
const targetPage = figma.root.children.find(p => p.name === "My Page");
await figma.setCurrentPageAsync(targetPage);
// targetPage.children is now populated
```

#### Returning Results

Scripts are automatically wrapped in an async IIFE with error handling. Just write plain JS and use `return` to send data back to the agent:

```javascript
// Return an object — auto-serialized to JSON
return { nodeId: frame.id, count: 5 }

// Return a string
return "Created 3 components"
```

Errors are automatically captured — no try/catch needed. `figma.notify()` does **not** exist. Return all information via the `return` value.

#### Working Incrementally

Don't build an entire screen in one call. Break work into small steps:
1. Create tokens/variables
2. Create text styles
3. Build individual components
4. Compose sections
5. Assemble screens

Verify structure with `get_metadata` between steps. Use `get_screenshot` after each major creation milestone to catch visual problems early.

### Creating Nodes

#### Frames

```javascript
$fig.frame({
  name: "Container",
  width: 1440,
  height: 900,
  fills: [{ type: "SOLID", color: { r: 0.98, g: 0.98, b: 0.99 } }],
})
```

#### Text

```javascript
$fig.text({
  characters: "Hello World",
  fontName: { family: "Inter", style: "Regular" },
  fontSize: 16,
  lineHeight: { value: 24, unit: "PIXELS" },
  letterSpacing: { value: 0, unit: "PERCENT" },
  fills: [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }],
  textAutoResize: 'WIDTH_AND_HEIGHT',
})
```

#### Rectangles

```javascript
$fig.rectangle({
  name: "Background",
  width: 400,
  height: 300,
  cornerRadius: 12,
  fills: [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.96 } }],
})
```

#### Ellipses

```javascript
$fig.ellipse({
  name: "Avatar Circle",
  width: 48,
  height: 48,
  fills: [{ type: 'SOLID', color: { r: 0.85, g: 0.87, b: 0.90 } }],
})
```

#### Lines

```javascript
$fig.line({
  name: "Divider",
  width: 400,
  height: 0,
  strokes: [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 }, opacity: 0.08 }],
  strokeWeight: 1,
})
```

#### SVG Import

```javascript
const svgString = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M5 12h14M12 5l7 7-7 7" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

$fig.svg(svgString, {
  name: "Icon/Arrow Right",
  width: 24,
  height: 24,
})
```

### Fills & Strokes

#### Solid Fill

```javascript
node.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.25 } }];
```

#### Fill with Opacity

```javascript
node.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.25 }, opacity: 0.5 }];
```

#### No Fill (Transparent)

```javascript
node.fills = [];
```

#### Linear Gradient

```javascript
node.fills = [{
  type: "GRADIENT_LINEAR",
  gradientStops: [
    { color: { r: 0.2, g: 0.36, b: 0.96, a: 1 }, position: 0 },
    { color: { r: 0.56, g: 0.24, b: 0.88, a: 1 }, position: 1 }
  ],
  gradientTransform: [[1, 0, 0], [0, 1, 0]]
}];
```

#### Strokes

```javascript
node.strokes = [{ type: "SOLID", color: { r: 0.85, g: 0.85, b: 0.87 } }];
node.strokeWeight = 1;
node.strokeAlign = "INSIDE";  // "CENTER", "OUTSIDE"
```

#### Multiple Fills (Layered)

```javascript
node.fills = [
  { type: "SOLID", color: { r: 0.95, g: 0.95, b: 0.96 } },
  { type: "SOLID", color: { r: 0.2, g: 0.36, b: 0.96 }, opacity: 0.05 }
];
```

### Auto Layout

#### Setting Up Auto Layout

**Prefer `$fig.autoLayout()`** — it returns a plan node with `layoutMode` already set and both axes hugging content. Use `figma.createAutoLayout()` if you need a raw scene node.

```javascript
$fig.autoLayout({
  name: 'Container',
  layoutMode: 'VERTICAL', // 'HORIZONTAL' or 'VERTICAL'
  width: 360, // Set width for fixed width and omit height to hug vertically
  itemSpacing: 16,
  paddingTop: 24,
  paddingBottom: 24,
  paddingLeft: 24,
  paddingRight: 24,
})
```

If you need a non-auto-layout frame, use `$fig.frame()`:

```javascript
$fig.frame({
  name: 'Container',
  width: 360,
  height: 200,
})
```

#### Alignment

```javascript
// Main axis (direction of layout)
frame.primaryAxisAlignItems = "MIN";            // Start
frame.primaryAxisAlignItems = "CENTER";         // Center
frame.primaryAxisAlignItems = "MAX";            // End
frame.primaryAxisAlignItems = "SPACE_BETWEEN";  // Distribute

// Cross axis
frame.counterAxisAlignItems = "MIN";     // Start
frame.counterAxisAlignItems = "CENTER";  // Center
frame.counterAxisAlignItems = "MAX";     // End
// NOTE: 'STRETCH' is NOT valid — use 'MIN' + child.layoutSizingX = 'FILL'
```

#### Child Sizing

```javascript
$fig.autoLayout(
  {
    name: 'Container',
    layoutMode: 'VERTICAL',
    width: 200, // Fixed width
    height: 200, // Fixed height
  },
  [
    $fig.frame({
      name: 'Child',
      layoutSizingHorizontal: 'FILL', // or 'HUG' or 'FIXED'
      layoutSizingVertical: 'FILL', // or 'HUG' or 'FIXED'
    })
  ]
)
```

#### Wrapping (Grid-like Layout)

```javascript
frame.layoutMode = "HORIZONTAL";
frame.layoutWrap = "WRAP";
frame.itemSpacing = 24;          // Horizontal gap
frame.counterAxisSpacing = 24;   // Vertical gap (between rows)
```

#### Absolute Positioning Within Auto Layout

```javascript
child.layoutPositioning = "ABSOLUTE";
child.constraints = { horizontal: "MAX", vertical: "MIN" };  // Top-right
child.x = parentWidth - childWidth - 8;
child.y = 8;
```

### Effects

#### Drop Shadow

```javascript
node.effects = [{
  type: "DROP_SHADOW",
  color: { r: 0, g: 0, b: 0, a: 0.08 },
  offset: { x: 0, y: 4 },
  radius: 16,
  spread: -2,
  visible: true,
  blendMode: "NORMAL"
}];
```

#### Inner Shadow

```javascript
node.effects = [{
  type: "INNER_SHADOW",
  color: { r: 0, g: 0, b: 0, a: 0.05 },
  offset: { x: 0, y: 1 },
  radius: 2,
  spread: 0,
  visible: true,
  blendMode: "NORMAL"
}];
```

#### Background Blur

```javascript
node.effects = [{
  type: "BACKGROUND_BLUR",
  radius: 16,
  visible: true
}];
```

#### Layer Blur

```javascript
node.effects = [{
  type: "LAYER_BLUR",
  radius: 8,
  visible: true
}];
```

#### Multiple Effects

```javascript
node.effects = [
  { type: "DROP_SHADOW", color: { r: 0, g: 0, b: 0, a: 0.04 }, offset: { x: 0, y: 1 }, radius: 3, spread: 0, visible: true, blendMode: "NORMAL" },
  { type: "DROP_SHADOW", color: { r: 0, g: 0, b: 0, a: 0.06 }, offset: { x: 0, y: 8 }, radius: 24, spread: -4, visible: true, blendMode: "NORMAL" }
];
```

### Opacity & Blend Modes

```javascript
node.opacity = 0.5;
node.blendMode = "NORMAL";    // "MULTIPLY", "SCREEN", "OVERLAY", "DARKEN", "LIGHTEN", etc.
```

### Corner Radius

```javascript
// Uniform
node.cornerRadius = 12;

// Per-corner
node.topLeftRadius = 12;
node.topRightRadius = 12;
node.bottomLeftRadius = 0;
node.bottomRightRadius = 0;
```

### Clipping

```javascript
frame.clipsContent = true;   // Children clipped to frame bounds
```

### Grouping & Organization

#### Groups

```javascript
$fig.group({ name: 'Grouped Elements' }, [node1, node2, node3])
```

#### Sections

```javascript
$fig.section({ name: 'My Section', width: 800, height: 600 })
// IMPORTANT: Sections don't auto-resize — always resize after adding content
```

#### Appending Children

```javascript
// With $fig
parentFrame.append(child);
parentFrame.addAt(0, child); // Insert at beginning
child.moveTo(parentFrame, 0); // Insert at beginning

// With raw Plugin API
parentFrame.appendChild(childNode);
parentFrame.insertChild(0, childNode);  // Insert at beginning
```

### Components & Variants

#### Create Component

```javascript
$fig.component({ name: 'Button/Primary', description: 'Primary action button' })
```

#### Create Instance

```javascript
$fig.instance(component, { x: 200, y: 100 })
```

#### Use Components by Key (Team Libraries)

Pass the `componentKey` straight into `$fig.get(...)` / `$fig.instance(...)`. The plan queues the library import automatically — there is no need to call `importComponentByKeyAsync` / `importComponentSetByKeyAsync` yourself, or to pick a variant child of a component set by hand.

```javascript
// Component
$fig.instance(componentKey, { x: 200, y: 100 })

// Component set: pass variant props; $fig.instance picks the matching variant
$fig.instance(componentSetKey, { x: 200, y: 100, props: { Size: 'md', Variant: 'primary' } })
```

For components in the current file, `$fig.get(nodeId)` accepts a real id too — same call site for both.

#### Combine as Variants

```javascript
// IMPORTANT: Pass ComponentNodes (not frames)
const componentSet = figma.combineAsVariants(
  [variantA, variantB, variantC],
  figma.currentPage
);
componentSet.name = "Button";
componentSet.description = "Button component with multiple variants.";

// CRITICAL: Layout variants in a grid after combining (they stack at 0,0)
let maxX = 0, maxY = 0;
componentSet.children.forEach((child, i) => {
  child.x = (i % numCols) * colWidth;
  child.y = Math.floor(i / numCols) * rowHeight;
});
for (const child of componentSet.children) {
  maxX = Math.max(maxX, child.x + child.width);
  maxY = Math.max(maxY, child.y + child.height);
}
componentSet.resizeWithoutConstraints(maxX + 40, maxY + 40);
```

#### Component Properties

```javascript
// addComponentProperty returns a STRING key — capture it!
const labelKey = component.addComponentProperty("label", "TEXT", "Button");
const showIconKey = component.addComponentProperty("showIcon", "BOOLEAN", true);
const iconSlotKey = component.addComponentProperty("iconSlot", "INSTANCE_SWAP", defaultIconId);

// MUST link properties to child nodes via componentPropertyReferences
labelNode.componentPropertyReferences = { characters: labelKey };
iconInstance.componentPropertyReferences = {
  visible: showIconKey,
  mainComponent: iconSlotKey
};
```

### Styles

Prefer `$fig` for style creation + binding — fonts preload automatically, and you can bind the style on the node by name (`fills`, `effects`, `textStyle`, etc.) in the same plan. See [`$fig` Builder API](#reference--fig-builder-api) for the full surface.

#### Text Style

```javascript
// $fig — single plan, auto font loading, binds via textStyle property
const body = $fig.textStyle({
  name: "Body/Default",
  fontName: { family: "Inter", style: "Regular" },
  fontSize: 16,
  lineHeight: { value: 24, unit: "PIXELS" },
  letterSpacing: { value: 0, unit: "PERCENT" },
});
$fig.text({ characters: "Hello", textStyle: body });
```

#### Effect Style

```javascript
// $fig — bind via the effects property in the same plan
const shadow = $fig.effectStyle({
  name: "Shadow/Subtle",
  effects: [{
    type: "DROP_SHADOW",
    color: { r: 0, g: 0, b: 0, a: 0.06 },
    offset: { x: 0, y: 2 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: "NORMAL",
  }],
});
$fig.frame({ name: "Card", effects: shadow });
```

#### Paint and Grid Styles

```javascript
const brand = $fig.paintStyle({
  name: "Brand/Primary",
  paints: [{ type: "SOLID", color: { r: 0.2, g: 0.36, b: 0.96 }, opacity: 1 }],
});
$fig.rectangle({ name: "Card", fills: brand });

const grid = $fig.gridStyle({
  name: "Grid/12",
  layoutGrids: [{ pattern: "COLUMNS", count: 12, gutterSize: 24, sectionSize: 80, alignment: "CENTER", visible: true }],
});
$fig.frame({ name: "Page", width: 1280, layoutGrids: grid });
```

#### Referencing an existing style

```javascript
const existing = $fig.getStyle("Brand/Primary");   // by name or real id; null if miss
$fig.query("FRAME[name^=Card]").set({ fills: existing });
```

### Cloning & Duplication

```javascript
const clone = originalNode.clone();
clone.x = originalNode.x + originalNode.width + 40;
clone.name = "Copy of " + originalNode.name;
```

### Finding Nodes

```javascript
// Find by name on current page
const node = figma.currentPage.findOne(n => n.name === "My Frame");

// Find all by type
const allTexts = figma.currentPage.findAll(n => n.type === "TEXT");

// Find all by name pattern
const allButtons = figma.currentPage.findAll(n => n.name.startsWith("Button/"));
```

### Layout Grids

```javascript
frame.layoutGrids = [
  {
    pattern: "COLUMNS",
    alignment: "STRETCH",
    count: 12,
    gutterSize: 24,
    offset: 80,
    visible: true
  }
];
```

### Constraints (Non-Auto-Layout Frames)

```javascript
child.constraints = {
  horizontal: "LEFT_RIGHT",  // LEFT, RIGHT, CENTER, LEFT_RIGHT, SCALE
  vertical: "TOP"            // TOP, BOTTOM, CENTER, TOP_BOTTOM, SCALE
};
```

### Viewport & Zoom

```javascript
// Zoom to fit specific nodes
figma.viewport.scrollAndZoomIntoView([frame1, frame2]);
```

---

## Reference — Working with design systems: Creating Components

When creating Figma components, you need to start by understanding the source and its intent.

If the user is asking you to create a component based on a design or specification, you need to understand the property model before you build anything. What variants are needed? What text, boolean, or instance swap properties exist? Getting the structure right upfront matters because restructuring a component after instances exist is destructive.

If you are given a code component as reference (React props, tokens, etc.), your goal is to reflect the property surface as closely as makes sense in Figma's model. Not all code properties translate directly — hover and focus states are not props in web code, but they are variants in Figma. Understand those gaps and make deliberate decisions about how to represent them.

Variants are the most important thing to get right. Each combination of variant values creates a node on the canvas. Redundant combinations still exist as explicit nodes — there is no way to conditionally exclude them. Define only the axes you actually need.

Non-variant properties (text, boolean, instance swap) should be added after the variant structure is established. These are defined at the component/component set level and referenced by descendant nodes via `componentPropertyReferences`. Always connect them — a property that isn't wired to a descendant is invisible to users of the component.

If the user asks you to make architectural decisions, lean toward fewer variants and more boolean/text properties where possible. Variants multiply combinatorially; the other property types do not. An optional slot property in code might be a combination of instance swap and boolean visibility.

When naming properties, casing is less important since translation layers like Code Connect can do the mapping to represent the code form. Feel free to take a sentence or capitalized case approach for better readability in Figma.

Keep in mind that components often need to be published and connected to Code Connect for the full design-to-code workflow to work. Creating the component is only one part of the system.

---

## Reference — Working with design systems: Using Components

When using Figma components, you need to start by understanding the state of the source and the state of Figma.

For the source, you need to know what component is being referenced. This could come from a component key, a node ID, a name, or a Code Connect mapping. If you have a component key from a design system library, pass it straight into `$fig.get(componentKey)` or `$fig.instance(componentKey, opts)` — preferred over finding by name, since names are not unique. If you only have a name, search the page or use `search_design_system` to find the right match; `search_design_system` returns each result's `componentKey`, which you can hand directly to `$fig`.

For Figma, you need to know whether the component is local or in a library. Local components can be accessed directly by node ID. Published library components are looked up the same way — pass the `componentKey` into `$fig.get(...)` or `$fig.instance(...)` and the plan queues the library import automatically; no separate `importComponentByKeyAsync` / `importComponentSetByKeyAsync` step is required. For component sets, pass the variant property values in `props` (`$fig.instance(setKey, { props: { Size: 'md' } })`) — `$fig` resolves the variant via `setProperties` after the instance is created. You do not need to fetch the set, drill into `compSet.children`, or pick a variant child by hand.

Before setting properties on an instance, read `componentPropertyDefinitions` from the main component first. Property names are not simple strings — TEXT, BOOLEAN, and INSTANCE_SWAP properties have a `#uid` suffix (e.g. `"Label#1234"`). Only VARIANT properties are plain names (e.g. `"Size"`). Using the wrong key in `setProperties` will silently do nothing.

A component might have multiple text properties, which are not possible to derive from text node layer names. Look to the properties to help you understand what values to set, rather than thinking of setting text node characters directly.

When you need to set a nested instance swap (e.g. an icon property), you need the component key of the swap target, not just its name. The simplest path is `$fig.get(swapTargetComponentKey)` and pass that handle as the swap value — `$fig` resolves the import behind the scenes.

Be aware that instances inside other instances are nested and changes made to a nested instance may be treated as overrides. If the intent is to change the default appearance, you need to modify the main component, not the instance.

When selecting which variant to use, read the `componentProperties` on the instance to see the current state, and `componentPropertyDefinitions` on the main component to see all available options.

---

## Reference — Components

Components overlap a lot with the idea of components in a codebase, but with some gaps and other Figma-specific use cases. Components in Figma can be reusable entities that do not have a comparable library pattern, or they can be published and distributed in a library that is aligned to a code forms.

Properties can vary from code in different ways, but alignment to code can still happen without a direct relationship. For example, an interactive pattern in code (like a button) can have many states. A lot of these states (active, focused etc) would be expressed in Figma as variants, which is a concept more closely aligned to properties in a code library. In the case of web this is confusing since hover is not a prop, it is a pseudo selector. At the same time, a color variant might be perfectly aligned between design and code (a property in both places). These discrepancies are accounted for in translation with Figma's Code Connect (deterministic context mapping), but in the case of these tools, must be understood to be properly used.

Figma has four property types, which can be inspected in the component definition's `componentPropertyDefinitions`. To fully understand the component, its descendants must be traversed. Property types include:

- Variant
  - This is reflected as permutations of the component in a Component Set on the canvas. Each variant is explicitly visualized, including an redundant permutations ("Small + Primary + Disabled" may look the same as "Small Secondary Sisabled"). These permutations create different variants implicitly in Figma and it is handled through layer naming (`Variant=Primary,Size=Small,State=Disabled`).
- Text/String
  - Text properties are stored on the component parent, but can be mapped to Text node descendants.
  - `node.componentPropertyReferences.characters` on a descendant text node are how you determine where the text property is referenced (can be multiple, though unlikely).
- Boolean
  - Boolean properties are stored on the component parent, but can be mapped to any node descendant that can have its visibility toggled.
  - `node.componentPropertyReferences.visible` on a descendant node are how you determine where the boolean property is referenced.
- Instance Swap
  - Instance swap properties are stored on the component parent, but can be mapped to Instance node descendants.
  - `node.componentPropertyReferences.mainComponent` on a descendant instance node are how you determine where the instance property is referenced. A classic example of this is an icon property.

### Descriptions

Components, component sets, and instances all inherit `PublishableMixin`, which includes a writable `description` string. Setting a description is important for any component intended to be used by others — it appears in Figma's dev mode and component panel, and is surfaced when reading component metadata.

Descriptions should explain the component's intent and any non-obvious usage constraints. They are not a substitute for Code Connect annotations, but they are always visible without any tooling setup.

```js
component.description =
  "Primary action button. Use for the single most important action on a page.";
```

Variant components (children of a component set) also have a `description` field, but in practice the component set description is what users see. Set it on the component set, not on individual variant nodes.

To read descriptions when auditing:

```js
// Get all component sets and their descriptions
figma.root
  .findAllWithCriteria({ types: ["COMPONENT_SET"] })
  .map((n) => ({ name: n.name, description: n.description }));
```

### Usage guidelines

- [Creating components](#reference--working-with-design-systems-creating-components): What you must consider when creating new components.
- [Using components](#reference--working-with-design-systems-using-components): What you must consider when trying to use the right components.

### Code patterns

For runnable code examples (creating, importing, discovering, inspecting components), see [Component & Variant API Patterns](#reference--component--variant-api-patterns).

---

## Reference — Working with design systems: Effect Styles

Effect styles in Figma are named, reusable definitions of one or more visual effects — drop shadows, inner shadows, and blurs. They are the closest equivalent to a shadow or elevation token in a design system.

Effect styles are distinct from variables. There is no single variable type that represents a shadow. However, individual numeric and color properties within an effect _can_ be bound to variables, allowing shadow values to participate in a token system.

### Model

An `EffectStyle` has one core writable property beyond the base style fields:

| Property      | Type                    | Notes                                                 |
| ------------- | ----------------------- | ----------------------------------------------------- |
| `name`        | `string`                | Slash-delimited for grouping (e.g. `"Elevation/200"`) |
| `effects`     | `ReadonlyArray<Effect>` | **Read-only array** — clone, modify, reassign         |
| `description` | `string`                | Inherited from `BaseStyleMixin`                       |

#### Effect types

An `Effect` is a discriminated union. The most common types:

| `type`            | Key properties                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------------- |
| `DROP_SHADOW`     | `color: RGBA`, `offset: Vector`, `radius: number`, `spread: number`, `visible: boolean`, `blendMode` |
| `INNER_SHADOW`    | Same as `DROP_SHADOW`                                                                                |
| `LAYER_BLUR`      | `radius: number`, `visible: boolean`                                                                 |
| `BACKGROUND_BLUR` | `radius: number`, `visible: boolean`                                                                 |

All colors are in 0–1 range (`RGBA`), not 0–255.

#### Variable bindings on effects

Effect properties that can be bound to variables (via `setBoundVariableForEffect(effect, field, variable)` on a node, or inline when constructing):

`color`, `radius`, `spread`, `offsetX`, `offsetY`

Note: `setBoundVariableForEffect` returns a **new** effect object — you must capture it and reassign the `effects` array.

#### Applying an effect style to a node

Assign the style's `id` to the node's `effectStyleId`. The node's `effects` property will then reflect the style's values.

#### Looking up a library effect style by key

When an effect style is found via `search_design_system` (`includeStyles: true` returns each result's `key`), pass that key directly into `$fig.getStyle(styleKey)` — the plan queues the library import automatically, no separate `await figma.importStyleByKeyAsync(...)` step required. The handle can then be applied via the `effects` property on any `$fig.rectangle(...)` / `$fig.frame(...)` / `$fig.query(...).set(...)` call.

```js
const shadow = $fig.getStyle(ELEVATION_200_KEY)
$fig.frame({ name: 'Card', effects: shadow })
```

### Common gotchas

- **`effects` is read-only**: You cannot mutate the array in place. Clone it, modify the clone, then reassign: `style.effects = [...style.effects, newEffect]`.
- **Effects stack in order**: The order of effects in the array matters visually. Drop shadows render bottom-to-top.
- **Colors are RGBA 0–1**: `{ r: 0, g: 0, b: 0, a: 0.15 }` — not hex, not 0–255.
- **`getLocalEffectStyles()` is deprecated**: Always use `getLocalEffectStylesAsync()`.
- **Styles are not automatically applied**: Creating an `EffectStyle` has no effect on any node until you assign its ID to a node.

### Code patterns

For runnable code examples (listing, creating, applying effect styles), see [Effect Style API Patterns](#reference--effect-style-api-patterns).

---

## Reference — Working with design systems: Text Styles

Text styles in Figma are named, reusable typography definitions. They are the closest equivalent to a type ramp in a design token library. A text style bundles font family, size, weight, line height, letter spacing, and other typographic properties into a single named entity that can be applied to text nodes.

Text styles are distinct from variables. You cannot put typography into a single variable — there is no composite variable type. However, individual properties on a text style _can_ be bound to variables (e.g. binding `fontSize` to a size variable, or `fontFamily` to a string variable), which allows the style to participate in a token system.

### Model

A `TextStyle` has the following writable properties:

| Property           | Type             | Notes                                                                        |
| ------------------ | ---------------- | ---------------------------------------------------------------------------- |
| `name`             | `string`         | Slash-delimited for grouping (e.g. `"Heading/XL"`)                           |
| `fontSize`         | `number`         | In pixels                                                                    |
| `fontName`         | `FontName`       | `{ family: string, style: string }` — **font must be loaded before setting** |
| `letterSpacing`    | `LetterSpacing`  | `{ value: number, unit: 'PIXELS' \| 'PERCENT' }`                             |
| `lineHeight`       | `LineHeight`     | `{ value: number, unit: 'PIXELS' \| 'PERCENT' }` or `{ unit: 'AUTO' }`       |
| `textCase`         | `TextCase`       | `'ORIGINAL' \| 'UPPER' \| 'LOWER' \| 'TITLE' \| 'SMALL_CAPS'`                |
| `textDecoration`   | `TextDecoration` | `'NONE' \| 'UNDERLINE' \| 'STRIKETHROUGH'`                                   |
| `paragraphSpacing` | `number`         |                                                                              |
| `paragraphIndent`  | `number`         |                                                                              |
| `description`      | `string`         | Inherited from `BaseStyleMixin`                                              |

#### lineHeight and letterSpacing format

These properties must be objects — not bare numbers:

```js
// WRONG — bare number throws
style.lineHeight = 1.5;
style.letterSpacing = 0;

// CORRECT
style.lineHeight = { unit: "AUTO" }; // auto line height
style.lineHeight = { value: 24, unit: "PIXELS" }; // fixed pixel height
style.lineHeight = { value: 150, unit: "PERCENT" }; // 150% line height

style.letterSpacing = { value: 0, unit: "PIXELS" }; // zero tracking
style.letterSpacing = { value: -2, unit: "PIXELS" }; // tight tracking
style.letterSpacing = { value: 5, unit: "PERCENT" }; // percent-based tracking
```

When reading a `lineHeight` back, always check `unit` first — `{ unit: 'AUTO' }` has no `value` key.

#### Variable bindings on text styles

The following fields can be bound to variables via `style.setBoundVariable(field, variable)`:

`fontFamily`, `fontSize`, `fontStyle`, `fontWeight`, `letterSpacing`, `lineHeight`, `paragraphSpacing`, `paragraphIndent`

To unbind: `style.setBoundVariable(field, null)`

**Important: where possible, use `setBoundVariable` instead of raw values**

```js
const ts = figma.createTextStyle();
ts.fontSize = 24; // set directly; not bound to a variable

const ts = figma.createTextStyle();
ts.setBoundVariable("fontSize", fontSizeVariable); // preferred if the variable exists.
```

#### Applying a text style to a node

Once you have a `TextStyle`, apply it to a `TextNode` by assigning its `id` to the node's `textStyleId` property. You can also use the async setter `setTextStyleIdAsync(id)`. Setting `textStyleId` on a node does **not** require the font to be loaded — only editing the text content or font properties directly does.

#### Looking up a library text style by key

When a text style is found via `search_design_system` (`includeStyles: true` returns each result's `key`), pass that key directly into `$fig.getStyle(styleKey)` — the plan queues the library import automatically, no separate `await figma.importStyleByKeyAsync(...)` step required. The handle can then be applied via the `textStyle` property on any `$fig.text(...)` / `$fig.query('TEXT').set(...)` call.

```js
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY)
$fig.text({ characters: 'Title', textStyle: heading })
```

### Common gotchas

- **Font must be loaded before setting `fontName`**: Call `await figma.loadFontAsync({ family, style })` before creating or modifying a text style's font.
- **Font style names are file-dependent**: Font style names vary by font provider and Figma file. Always call `await figma.listAvailableFontsAsync()` to discover exact style strings before loading — never guess or probe with try/catch.
- **Styles are not automatically applied**: Creating a `TextStyle` has no effect on any node until you assign its ID to a text node.
- **`getLocalTextStyles()` is deprecated**: Always use `getLocalTextStylesAsync()`.
- **Names are not unique**: Two text styles can share the same name. Match by ID or `key` when looking up a known style, not by name alone.
- **Slash grouping is visual only**: `"Heading/XL"` and `"HeadingXL"` are different names; the slash is just a UI affordance.
- **`lineHeight` and `letterSpacing` must be objects**: `style.lineHeight = 1.5` throws. Always use `{ value, unit }` format or `{ unit: 'AUTO' }`.

### Code patterns

For runnable code examples (listing, creating, discovering available fonts, type ramps, applying styles), see [Text Style API Patterns](#reference--text-style-api-patterns).

---

## Reference — Working with design systems: Creating Variables

When creating Figma variables, you need to start by understanding the state of the source data.

If the user is asking you to create variables based on values, they likely want you to indicate the structure. Whether or not you use semantic aliasing primitive will be based on the inputs you are given about the source data.

If you are given code inputs (JSON, CSS, etc) your goal should be to reflect the existing patterns as closely as possible, but also embrace the design context as distinct from code. For example, casing is less important since you have code syntax that can directly represent the code form. Feel free to take a sentence or capitalized case approach for better readability in Figma.

It is important to understand the underlying structure before you create anything. If there is an implied aliased setup, you want to get that right. You may also need to anticipate modes to know how to split things up. Sizes and Colors likely have different mode requirements in complex systems, so you want to consider that as you create the structure.

If someone asks you to just make a decision based on best practices, that answer will be relative to the complexity of the environment. A simple theme is great best practice for simple needs. Similarly, a complex extended collection setup for someone on an enterprise plan might also be best practice as well.

Keep in mind that systems might also require you to handle text and effect styles for some of the things specified in token libraries.

---

## Reference — Working with design systems: Using Variables

When using Figma variables, you need to start by understanding the state of the source and the state of Figma.

For the source, you need to know the breadth of variables code representation. CSS, JSON, theme providers etc will all be able to indicate what the user will expect you to cover in Figma. Some beginner users might not even know what does and doesn't exist in Figma, and if you cant discover that on your own, you will need their help making the right decision.

For Figma, you need to know what collections exist, what their modes are, and what values and names and code syntaxes are in them. This will help you make sure you are using the right things. For properties that "should" have variables but don't, you likely will need to ask the user what to do. Your understanding of Figma's current state should come first.

You can use code syntax and your understanding of the environment you are expected to be referencing to know which variable in Figma to use. You can also use Figma's variable scopes as indicators if they are specified. It is best to audit those up front.

When using variables you should also be aware of mode mismatches, the default mode in Figma may not be the mode referenced by the user in their expectations. Similarly, many collections may refer to values, but the most specific collection is what you should be using. For example, a semantic collection that aliases a primitive collection, the semantic collection would be what you reference. A component token collection (eg. button/background/primary) might alias a semantic collection, and it is the component collection you need to reference. In some other examples, there may be no aliasing and you're simply value matching.

Gap and padding values for frames are really important and often have to be interpreted semantically or based on layout component values.

### Looking up variables by key

When a variable is found via `search_design_system` (returns a `key` per result) or you already have a library variable key, pass it directly into `$fig.getVar(variableKey)`. The plan queues the library import automatically — you do not need a separate `await figma.variables.importVariableByKeyAsync(...)` step. The same call also accepts a local variable id; the input shape is unified.

```js
const brand = $fig.getVar(BRAND_COLOR_VAR_KEY)
$fig.rectangle({ fills: [{ type: 'SOLID', color: brand }] })
```

---

## Reference — Working with design systems: Variables

Variables overlap a lot with the idea of tokens in a codebase, but with some gaps and other Figma-specific use cases. Variables are single value, number, string, color, boolean.

In Figma you can do conditional logic and use variables to get basic prototyping functionality. String values can also be used as sophisticated placeholder setups that have different modes for different languages. Not everything you use a variable for in Figma would be used exactly the same way in code. However, for design systems, they are often synced to code in some way.

One gap is the lack of composite tokens. You can't put a box shadow behind a single variable. That is an [effect style](#reference--working-with-design-systems-effect-styles), but style values can be bound to variables. Similarly for a type ramp, you have to use [Text Styles](#reference--working-with-design-systems-text-styles).

### Model

#### Collections

Collections can be thought of a groups in Figma. An example Collection would be "Colors" where there might be a light and dark "Mode." Each value would have two definitions.

#### Extended Collections

Extended collections allow you to create a colleciton based on another collection and only override _some_ of the values. Just like inheritance and overrides in CSS. This aligns well for scenarios like branded color themes.

#### Modes

Modes in Figma can be thought of like light and dark, but users can specify modes for anything, including sizes, languages (string variables exist in Figma too).

#### Aliasing

Aliasing in Figma variables is simply when you point a variable to another variable. Common example is pointing a semantic variable to a primitive variable. Some teams also do component level tokens which adds a third component specific layer.

**Decision rule:** If the source data has two tiers (primitives + semantics), create all primitives first, then create semantic variables that alias into them. If the source data is a single flat tier, create flat variables with no aliases. When in doubt, ask.

#### Code Syntax

Code syntax is a surface area in Figma for codebase translation context. You can set WEB, iOS, and ANDROID code syntax on any variable, and when that variable is referenced in other places (visually in Figma's dev mode, or as design context when reading component metadata), this codebase form will appear. These are best thought of as "instance" documentation, eg. `var(--the-thing)` instead of `--the-thing` in the case of CSS.

#### Scope

`variable.scopes: VariableScope[]` specifies which properties in Figma the variable can be used for. This is important when you create and when you use variables. **Always set specific scopes rather than leaving the default `ALL_SCOPES`** — it pollutes every property picker with irrelevant tokens. The more specific the better. For the canonical scope-to-use-case mapping, see token-creation.md § Variable Scopes — Complete Reference Table (load `readPowerSteering("figma", "figma-generate-library.md")`).

Common scope values:

- `ALL_SCOPES` — unrestricted; **avoid this** — it is the default but almost never the right choice. Only acceptable for very simple files with a handful of variables where the overhead of precise scoping isn't justified
- `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL`, `STROKE_COLOR` — color bindings (use specific fill scopes; `ALL_FILLS` covers all three fill scopes together)
- `TEXT_CONTENT` — string variables for text layers
- `FONT_SIZE`, `FONT_WEIGHT`, `LINE_HEIGHT`, `LETTER_SPACING` — typography
- `CORNER_RADIUS`, `WIDTH_HEIGHT`, `GAP` — layout/spacing
- `OPACITY` — layer opacity

#### Grouping

Variable names in Figma are slash delimited and each slash represents a group that is visualized in Figma. When you are doing matching, consider a part of a code prefix might be the name of the collection, not a top level group. Sometimes you will have prefixes in code that aren't in Figma, and that can be ok, just be sure to ask if it is unclear. You can always validate existing variables by referencing the code syntax.

### Common gotchas

- **`createVariableCollection` always creates a default mode** — you will need to rename it (or delete it and add your own) rather than creating from scratch.
- **Duplicate variable names throw silently** — Figma does not error; it creates a second variable with the same name. Always check for existence before creating.
- **Variable aliases require the target to be in the same file** — cross-file aliasing is not supported via the plugin API. If you need to alias to a library variable, import it first.
- **`setValueForMode` with an alias requires the exact shape** — `{ type: 'VARIABLE_ALIAS', id: '<variableId>' }`. Any deviation will silently set the wrong value or throw.

### Usage guidelines

- [Creating variables](#reference--working-with-design-systems-creating-variables): What you must consider when creating new variables.
- [Using variables](#reference--working-with-design-systems-using-variables): What you must consider when trying to use the right variables.

### Code patterns

For runnable code examples (creating collections, binding variables, scopes, aliasing, discovering existing variables), see [Variable & Token API Patterns](#reference--variable--token-api-patterns).

---

## Reference — Working with design systems

When working with design systems in Figma, there can be many nuances when deciding how to do the right thing. Figma's model for patterns is form-agnostic, this is one of its strengths, allowing people to refer to a pattern in a spec that may take distinct forms in different codebases. However, this can result in complex procedures and nuances when translating something to Figma and back. Figma has components, tokens, and other reusable patterns (text and effect styles, prototyping actions, etc). The way that Figma's paradigms function can be difficult to translate one to one.

To make translation of patterns work between design and code forms, it is important that teams think about alignment while also embracing the function of representation (design) and implementation (production) forms independently as complementary pieces of a shared puzzle.

For the process of design, the desirable state of a system is something that is structured with experimentation in mind, something that is highly visual, easy to iterate, test, and confirm new ideas. Depending on the product and team, exploration might be mandatory to be done within the confines of an existing system, for other scenarios, exploration of new territory is the priority, a place for the system to grow into, or a new system to be made. Figma's platform allows for teams to validate, align, and collaborate on new ideas, then solidify them in product designs, which are ultimately specs. That work is supported by design libraries and that process can include code in prototypes and other less permanent forms as much as it does Figma's native paradigms.

For the process of implementation, the desirable state for production code is rigidity, efficiency, and related to secure data and functional layers. Developer experience implementing a design and the designer experience surfacing and committing to an idea are paths from distinct points of to the same shared outcome. Their optimization looks different, and that is reflected when you engage with Figma's APIs.

The key is not to avoid gaps, but to make sure they are definitively bridgable. Translation layers help agents and people go between representational and production forms.

The Figma paradigms you will need to understand when working with design systems. In each file below there will be further links to instructions for using and creating:

- [Components](#reference--components)
- [Variables](#reference--working-with-design-systems-variables)
- [Effect Styles](#reference--working-with-design-systems-effect-styles)
- [Text Styles](#reference--working-with-design-systems-text-styles)

Things you might be asked to do with respect to design systems:

- Create patterns in Figma that match patterns in code
  - Likely (but not exclusively) to get up to speed so that visual riffing can be done in Figma
  - Create variables based on a stylesheet, JSON format, some other theme definition
  - Create Figma text styles that match a type hierarchy defined somewhere
  - Create components based on existing code components
- Sync between code and design forms
  - Making sure that Figma's concepts match a production form
- Use an existing Figma design library to create something
  - This something could be matching an existing code form, an image, or just a prompt
- Clean up a design to match some code pattern

### Things to remember

Many people will use these tools to try out ideas, and not everything you get asked to do will feel realistic for the environment you are running in. It is important to contextualize that, but then also know when you are definitively working in a production environment and there is a very real task you need to perform consistently.

Not everyone asking you to do something knows what they should be doing. You must figure out if the request is to generically perform design systems actions, uphold existing the rules that are codified in Figma or in a codebase, demonstrate an idea, enforce existing guidelines, etc.

Not every environment you are working in has the same degree of expertise and maturity. Some systems will be very complex and the priority and have a lot of things to parse through to get to the right outcome. Some scenarios will be very immature and even starting from scratch. Something as simple as creating a component could be very elementary or very sophisticated depending on the environment. The instructions you find here are attempting to be unbiased.

For example, how you reflect the "hover" state of a button could be left entirely up to you to make a reasonable decision for a user that is playing around with getting a decent example scaffolded using best practices, but it could also be something that exists definitively in the codebase and you need to go match it. That codebase definition could be refering to design tokens that do not yet exist in code that change dark and light mode values. In this second example you are now needing to do a bunch of variables work just to add a hover state to a component with proper dark and light mode support, where in the first scenario, you can kinda just do whatever is easiest. This is the line you will be walking, and making good judgement here is about doing whatever is the smartest thing in the environment you are in.

---

## Bundled references

Large references split into their own steering files — load on demand:
- **plugin-api-standalone.d.ts** → `readPowerSteering("figma", "figma-use-api.md")`
