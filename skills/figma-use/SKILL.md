---
name: figma-use
description: "**MANDATORY prerequisite** — you MUST invoke this skill BEFORE every `use_figma` tool call. NEVER call `use_figma` directly without loading this skill first. Skipping it causes common, hard-to-debug failures. Trigger whenever the user wants to perform a write action or a unique read action that requires JavaScript execution in the Figma file context — e.g. create/edit/delete nodes, set up variables or tokens, build components and variants, modify auto-layout or fills, bind variables to properties, or inspect file structure programmatically."
disable-model-invocation: false
---
# use_figma — Figma Plugin API Skill
Use the `use_figma` tool to execute JavaScript in Figma files via the Plugin API. All detailed reference docs live in `references/`.

When available, call `create_session` with `fileKey` and `description` before file reads or edits (create the file first if needed), then pass the returned `sessionId` unchanged to every call that accepts it, including follow-ups and work across files.

**Always include `figma-use` in the comma-separated `skillNames` parameter when calling `use_figma`. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-use`).** This is a logging parameter used to track skill usage — it does not affect execution.

**If Figma MCP tools appear as deferred tools, batch-load all their schemas in a single `ToolSearch` call** using the `select:` syntax — e.g. `ToolSearch query="select:use_figma,get_screenshot,get_metadata,create_new_file"`. One round trip beats six.

**MANDATORY for visible design changes:** Before the first mutating `use_figma` call, load [figma-generate-design](../figma-generate-design/SKILL.md) alongside this skill and include both names in every mutating call’s `skillNames`. This applies from a single visible property or element to a full page, screen, or composed multi-section view—even when the user calls that view a component. `figma-use` provides the Plugin API rules; `figma-generate-design` provides design-system discovery through `search_design_system`, asset importing, and incremental assembly.

**If the task involves creating or building a standalone component or a component library in Figma** (even a single component as the deliverable), also load [figma-generate-library](../figma-generate-library/SKILL.md). It owns the component-creation workflow — variable foundations first, variant sets, then design token bindings — that `figma-use` alone doesn't cover. Build the token/variable foundation before the component, then bind the component's `fills`/`cornerRadius`/spacing to those variables rather than inlining literals where a token exists. For components that exist to be reused **inside a screen you are building**, follow [figma-generate-design → componentization](../figma-generate-design/references/componentization.md) instead.

**3D transforms:** For perspective, depth, X/Y tilt, isometric cubes, or other static 3D poses, load [figma-3d-transforms](../figma-3d-transforms/SKILL.md) when available. It owns the gated `transform3d`, `scene3d`, and `transformOrigin` API guidance, including fields that may be absent from the general typings. Follow this skill's node-creation rules, then apply the 3D poses to the resulting nodes. If the 3D skill or APIs are unavailable, explain that 3D authoring is not enabled in this session. Flat in-plane rotation uses `node.rotation` and does not need the 3D skill.

For other APIs, load [plugin-api-standalone.index.md](references/plugin-api-standalone.index.md) to understand what is possible. When you are asked to write plugin API code, use this context to grep [plugin-api-standalone.d.ts](references/plugin-api-standalone.d.ts) for relevant types, methods, and properties. This is the definitive source of truth for the general API surface. It is a large typings file, so do not load it all at once, grep for relevant sections as needed.

IMPORTANT: Whenever you work with design systems, start with [working-with-design-systems/wwds.md](references/working-with-design-systems/wwds.md) to understand the key concepts, processes, and guidelines for working with design systems in Figma. Then load the more specific references for components, variables, text styles, and effect styles as needed.

## $fig — the plan-based builder API (ALL NODE CREATION MUST USE THIS)

`$fig` is a global that is responsible for all node creation. It auto-flushes at script end (no `$fig.done()` needed), handles font preloading, batches mutations, and orders property assignment correctly. **Use it for all node creation and mutation operations.** Never use `figma.createFrame()`, `figma.createText()` or any `figma.create*` methods. They do not exist in this environment.

**Constructors queue creation, not inert templates.** Every `$fig` node constructor like `$fig.frame(...)` queues a node creation in the plan, even if its returned plan node is never used, returned, or screenshotted. Unattached nodes become top-level nodes at flush. Plan nodes meant to be used as children should be appended or used in `$fig.frame(opts, children)` **before flushing**.

**layoutSizingHorizontal/Vertical = 'FILL' is for auto-layout children only.** Do not set FILL for top-level nodes.

### Plan nodes vs real nodes

`$fig.component(...)`, `$fig.variants(...)`, `$fig.instance(...)`, `$fig.get(...)`, and `$fig.frame(...)` return **plan nodes**, not raw Plugin API nodes. `await $fig.done()` materializes the plan nodes and makes `planNode.node` available for accessing real nodes. Do not use plan nodes like real nodes.

- Use `planNode.set({ name, x, y })` and `planNode.append(childPlanNode)` for queued mutations. Do not make direct assignments like `planNode.x = 100`. Do not mix plan nodes into raw plugin APIs like `node.appendChild(planNode)`.
- Prefer `$fig.instance(componentPlanNode, opts)` or `planNode.instance(componentPlanNode, opts)` to create instances of plan component nodes, with no intermediate flush.
- Use `planNode.node` only when you need raw state or an operation `$fig` or plan nodes do not expose. Flush pending changes first. Do not mix raw plugin code amongst pending changes.

### Copy these patterns

**Build an auto-layout frame with children — single call:**
```js
$fig.autoLayout(
  // fixed width; omit height to hug vertically
  { name: 'Todo List', layoutMode: 'VERTICAL', width: 480 },
  ['item 1', 'item 2', 'item 3'].map((item) =>
    $fig.autoLayout(
      // FILL is valid because this item is attached to the auto-layout Todo List
      { name: 'Todo Item', layoutSizingHorizontal: 'FILL' },
      [$fig.text({ characters: item, fontName: { family: 'Inter', style: 'Bold' } })],
    ),
  ),
).screenshot() // Composition check; do not repeat unless a relevant change needs visual verification.
```

**Repeated UI (list items, cards, nav items, table rows, day cells): build ONE component, then place instances.** Do not build N near-identical frames. TEXT/BOOLEAN props carry the per-item differences:
```js
const ITEMS = [
  { title: 'Inbox', count: '12' },
  { title: 'Drafts', count: '' },
  // ...from the source data
]
const item = $fig.component({ name: 'Nav Item', layoutMode: 'HORIZONTAL', itemSpacing: 8 }, [
  $fig.text({ characters: 'Label' }).textProp('Label'),
  $fig.text({ characters: '0' }).textProp('Count').booleanProp('Show Count'),
])
$fig.autoLayout({ name: 'Nav', layoutMode: 'VERTICAL', width: 240 },
  ITEMS.map((v) => $fig.instance(item, {
    layoutSizingHorizontal: 'FILL',
    props: { Label: v.title, Count: v.count, 'Show Count': v.count !== '' },
  })),
).screenshot()
```
When building a screen, keep main components outside the view: in the file's existing component area, or off to the side of the wrapper. Return `item.node.id` (after `await $fig.done()`) when a later call needs more instances: `$fig.instance('ID', { props })`. Only genuinely one-off containers stay plain frames. Full recipe (variants for visual states, nested overrides, differing child counts, structural check): [figma-generate-design → componentization](../figma-generate-design/references/componentization.md).

**Update existing nodes — by query or by id:**
```js
$fig.query('FRAME[name=Header] TEXT[name=Title]').set({ characters: 'New Title', fontSize: 24 })
$fig.get('1:42').set({ opacity: 0.8, cornerRadius: 12 })
```

**Add a node inside an existing node**
```js
$fig.get('1:42').append($fig.autoLayout({ name: 'New Frame' }))
```

`parent.append(a, b, c)` and `$fig.append(parent, a, b, c)` append every child in order and return the parent for chaining.

**Create variants and place an instance**
```js
const SIZES = ['Small', 'Medium', 'Large']
const buttonComponentSet = $fig.variants({ name: 'Button' }, SIZES.map((size) => $fig.component({ name: `Size=${size}`, layoutMode: 'HORIZONTAL', /** other props */ })))
const buttonInst = $fig.instance(buttonComponentSet, { props: { Size: 'Medium' } })
$fig.get('DESTINATION_FRAME_ID').append(buttonInst)
// Creation and placement are queued; no intermediate done() is needed.
```
Select variants through `props` on the component set. This also works with published sets when individual variant references are unavailable.
If an earlier measurement required `await $fig.done()`, continue using plan node `.set(...)` and `.append(...)` for changes and placement.

> ⚠️ `$fig.variants` does **not** position the variants — they stack at (0,0) and the set renders as one collapsed, overlapping element. You must grid the variants and resize the set afterward. See [`fig-builder.md`](references/fig-builder.md#required-follow-up--grid-the-variants-fig-build--raw-layout) for the required follow-up recipe.

> **Building a component — even a single one? Binding tokenized values is part of finishing the job, not a preference.** A component is **not complete** while any value that *has* a corresponding design token — one that already exists in the file, or that you created from the source — is still a hardcoded literal. When a token exists for a `fills` color / `cornerRadius` / padding / `itemSpacing`, bind it: build a `$fig.varCollection` (primitive tier + semantic tier aliased to it) and pass the variable **handle straight into the property**. **Anti-pattern to avoid:** do NOT copy resolved token values into local JS constants (e.g. `const VARIANTS = [{ bg: '#2c2c2c' }]`) and paint with resolved literal colors — that silently bypasses variables even though the source defines tokens. This applies to a single component as much as a full design system. **Only bind values that actually have a token** — values with genuinely no token (one-off geometry, icon pixel sizes, static 1px dividers) correctly stay literal; don't invent tokens to bind. **If you create the variables in one `use_figma` call and build the component in a later one, rehydrate the handles first** (`$fig.getVar(id)` or `figma.variables.getVariableByIdAsync` using the IDs you returned) — a handle from a previous call isn't in scope. Worked recipe: [fig-builder.md → Building a component with bound variables](references/fig-builder.md#building-a-component-with-bound-variables-the-default-for-components).

**Create an instance of a component**
```js
// First arg can be a component plan wrapper, a node ID ('1:2'), OR a library asset key
// from `search_design_system` results (the `componentKey` or `componentSetKey` field, according to `assetType`).
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

`search_design_system` returns `componentKey` for components, `componentSetKey` for component sets, and `key` for styles and variables. Pass these straight into the unified `$fig` lookup — the plan queues the library import automatically, so you don't need a separate `await figma.importComponentByKeyAsync(...)` / `importStyleByKeyAsync(...)` / `importVariableByKeyAsync(...)` step.
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

**Discover a set's variant props from its key** — `search_design_system` returns a set's `componentSetKey`, not its variant properties. This is **two `use_figma` calls**: call 1 `return`s the set's property definitions and its variants so their props come back to you in the tool result; then, knowing the valid props, call 2 instantiates the variant you want.
```js
const setHandle = $fig.get(BUTTON_SET_KEY)
await $fig.done()
const set = setHandle.node
if (!set || set.type !== 'COMPONENT_SET') {
  throw new Error(`Key ${BUTTON_SET_KEY} is not a COMPONENT_SET`)
}
return {
  componentPropertyDefinitions: set.componentPropertyDefinitions,
  variants: set.children
    .filter((c) => c.type === 'COMPONENT')
    .map((c) => ({ name: c.name, variantProperties: c.variantProperties })),
}
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

Page context resets to the first page at the start of each `use_figma` call. When an operation needs another current page, switch with `await figma.setCurrentPageAsync(page)` before queuing the plan; never assign `figma.currentPage` directly. Switch at most once per call. Split work requiring multiple current-page contexts into independent calls, one per page; issue independent calls in parallel. A scoped FigQuery search does not itself require a separate call for every page.
```js
// Switch to a specific page (loads its content)
const targetPage = figma.root.children.find((p) => p.name === "My Page");
await figma.setCurrentPageAsync(targetPage);
$fig.query('INSTANCE[name=arrow_drop_down]').set({ ... })
```

**Gradient via helper — no manual transform matrix needed:**
```js
const node = $fig.rectangle({ width: 240, height: 120 })
$fig.gradient(node, 'LINEAR', [
  { pos: 0, color: figma.util.rgba('#000000') },
  { pos: 1, color: figma.util.rgba('#ffffff') },
])
```

**Literal colors — use the built-in utilities, available in every call:**
```js
$fig.rectangle({ fills: [figma.util.solidPaint('#2563eb80')] }) // alpha becomes paint opacity
const rgb = figma.util.rgb('#2563eb') // { r, g, b }; ignores input alpha
const rgba = figma.util.rgba('#2563eb80') // { r, g, b, a }; for gradient stops/effects
```
Use these utilities directly instead of defining a hex parser or relying on helpers from a previous `use_figma` call. For token-backed properties, keep passing the variable handle directly; converting its resolved color to a paint would lose the binding.

**Chaining on plan nodes — alternative to children array:**
```js
const card = $fig.autoLayout({ name: 'Card', layoutMode: 'VERTICAL' })
card.text({ characters: 'Title', fontSize: 20 })
card.text({ characters: 'Description', fontSize: 14 })
```

### `$fig` create + mutate API (full surface)

- **Create:** `$fig.autoLayout / .frame / .text / .rectangle / .ellipse / .polygon / .star / .line / .vector / .section / .component / .page` — all `(opts?, children?)`. Plan nodes are chainable.
- **Create from SVG — the preferred ICON path:** `$fig.svg(svgStr, opts?)` builds a vector node tree from an SVG string. **Prefer real vector icons:** import the icon's SVG source (inline `<svg>`, the `.svg` asset, or the source icon-library glyph — e.g. lucide/heroicons) via `$fig.svg(...)` rather than approximating an icon with a typed emoji/Unicode glyph (★ ⚙ 🔍 ☰ ▾) or a plain rectangle. A simple glyph or shape is a fine fallback when the real SVG genuinely can't be obtained — just reach for the SVG first. (Don't reconstruct an icon from rotated line/rect primitives, though — that renders broken.) Full recipe (viewBox+width/height sizing, `currentColor`, INSTANCE_SWAP for design-system icons): [figma-generate-design → Icons](../figma-generate-design/SKILL.md#icons-import-the-svg-never-reconstruct-from-rotated-primitives).
- **Create an instance of a component:** `$fig.instance(compRef, opts?)` — `compRef` is a component plan node, a node ID string, OR a library asset key (`componentKey` or `componentSetKey` from `search_design_system`); the import is queued in the plan automatically.
- **Grouping/boolean:** `$fig.group / .union / .subtract / .intersect / .exclude / .variants` — all `(opts?, children?)`.
- **Read:** `$fig.get(id)` wraps an existing `SceneNode` — `id` can be a real node ID OR a library asset key (`componentKey` or `componentSetKey` from `search_design_system`); the import is queued in the plan automatically. `$fig.query(selector, scope?)` returns `{ length, values(paths), first(), last(), each(fn), filter(fn), set(props), moveTo(parent, idx?), remove() }`. Selectors are CSS-like (e.g. `'FRAME[name*=Card] TEXT'`). `$fig.getStyle(nameOrIdOrKey)` and `$fig.getVar(nameOrIdOrKey)` accept the matching `key` values from `search_design_system`.
- **Mutate:** `$fig.set(target, props)`, `.delete(...nodes)`, `.move(target, parent, idx?)`, `.clone(target, props?)`, `.append(parent, child)`, `.addAt(parent, idx, child)`, `.replace(old, new)`, `.reorder(parent, children)`, `.gradient(node, type, stops, transform?)`, `.image(node, hash, scaleMode?)`.
- **Plan-node methods (chainable):** `.set()`, `.remove()`, `.clone()`, `.moveTo(parent, idx?)`, `.append(child)`, `.query(selector)`, `.screenshot({scale?, contentsOnly?})`, and the `.node` getter for the materialized `SceneNode` (null pre-flush).

### When to use the raw Figma Plugin API

Keep raw Plugin API code that reads or changes document state separate from planned creation and mutations. Run it before `$fig` code, or after an explicit `await $fig.done()` that flushes all pending changes. Do not pass plan nodes to raw methods such as `regularNode.appendChild(planNode)` or `insertChild`; use `$fig.get(regularNode.id).append(planNode)` or `.addAt(index, planNode)` instead. Planned changes are not visible to raw reads such as `regularNode.children` until the plan is flushed. After flushing, use `planNode.node` when a raw API needs the real node. Pure color helpers such as `figma.util.solidPaint`, `.rgb`, and `.rgba` can be used inside `$fig` expressions.

Use the raw API only in these cases:

- **Color conversion:** `figma.util.solidPaint`, `.rgb`, and `.rgba` convert literal colors for `$fig` properties without creating or mutating nodes.
- **Mid-script async result needed:** `await figma.setCurrentPageAsync(...)`, `await figma.loadFontAsync(...)` — must complete before subsequent plan steps can use the result. (Importing library components is NOT one of these cases: pass the matching `componentKey` or `componentSetKey` straight into `$fig.get(...)` / `$fig.instance(...)` and pass variant property values in `props`. `$fig` queues the library import in the plan and resolves the variant for you.)
- **Mid-script real node state read:** measured `width` / `height` after auto-layout, computed colors, getStyledTextSegments — materialize mid-script, then read `.node` on the plan node. See [references/fig-builder.md](references/fig-builder.md) for the mid-script inspection pattern.
- **Things `$fig` genuinely doesn't expose:** `node.setRangeFontName(...)`, etc. — access via `planNode.node` (see [references/fig-builder.md](references/fig-builder.md)).

## Critical Rules

1. **Only use `$fig` for creating / bulk-editing nodes** (`$fig.autoLayout(...)`, `$fig.text(...)`, `$fig.query(...).set(...)`). Raw Plugin API is the fallback — use it only when `$fig` can't express the operation (intermediate node-state reads, non-SceneNode types like Variables). Library components are NOT a reason to leave `$fig`: `$fig.get(componentKey)` / `$fig.instance(componentSetKey, { props })` queue the library import and resolve the variant for you. See [references/fig-builder.md](references/fig-builder.md) and [references/critical-rules-deep.md](references/critical-rules-deep.md) for worked WRONG/RIGHT examples.

2. **Do not use `findOne`, `findAll`, `findAllWithCriteria`, `findChildren`, `findChild` directly for node searching** They are more verbose, error-prone, and less efficient than `query()`.  Additionally, do not use recursion to search.
   `frame.query('[boundVariables.*]')` filters nodes by non-empty bindings: `{ boundVariables: { width: alias } }` matches; `{ boundVariables: {} }` or `{ fills: [paint] }` does not. Selector `*` expands array elements or object values.

3. **Keep automatic result reporting for pure `$fig` scripts.** The runtime auto-flushes and returns a `FigDoneResult` with created/updated node IDs. Use `await $fig.done()` before reading materialized state or deferred query results, and `return` any additional evidence needed. Include IDs for raw mutations in custom results. JS variables and plan handles do not survive between calls: pass returned IDs as string literals and resolve them again with `$fig.get`, `$fig.getVar`, or `$fig.getStyle`. Keep workflow state outside the Figma file.

4. **Size construction calls for safe retry and validate from evidence.** Batch related creation and edits when failures remain recoverable; a complete section or page may be one call. Split for page-context changes, difficult partial recovery, or a targeted retry after failure—not merely to create validation checkpoints. Use returned IDs and relevant counts, names, or bounds as structural evidence; add a separate check only when evidence is missing or a relevant mutation invalidates it. Normally take one screenshot after composition and one after a visual fix. The latest passing screenshot is final; stop when requirements pass. For work spanning calls, the placeholder workflow below remains useful: populate or replace each placeholder and clear `placeholder` when finished.

```js
$fig.autoLayout({ name: 'Screen', layoutMode: 'VERTICAL', width: 390 }, [
  $fig.autoLayout({ name: 'Header', layoutSizingHorizontal: 'FILL', placeholder: true }),
  $fig.autoLayout({ name: 'Content', layoutSizingHorizontal: 'FILL', placeholder: true }),
])
```

5. **Plain JS with top-level `await`.** Code is auto-wrapped in async. Do NOT wrap in `(async () => {})()`.

6. **Use built-in utilities for literal colors.** `figma.util.solidPaint('#2563eb80')` creates a complete solid paint with opacity. For individual color fields, use `figma.util.rgb(...)` for `{r,g,b}` (solid paints; ignores alpha) and `figma.util.rgba(...)` for `{r,g,b,a}` (gradient stops/effects). Channels are 0–1; solid-paint opacity belongs outside `color`. The utilities are available in every call — no custom hex parser needed. Token-backed properties still take variable handles directly. See [references/critical-rules-deep.md](references/critical-rules-deep.md) for WRONG/RIGHT.

7. **No `curl` / `wget` / `Read` of Figma URLs from `Bash`.** Figma file access ONLY via `use_figma` and `mcp__figma__*` tools. After `get_screenshot`, the image is inlined in the tool result — do NOT re-fetch or re-Read it.

8. **Empty / unsupported responses are terminal.** Accept and move on — don't try alternative bypass paths.

9. **Verify node-type before touching a property.** Only `FRAME / COMPONENT / COMPONENT_SET / INSTANCE / GROUP / SECTION / PAGE` have `.children`. `GROUP` has no `fills` / `strokes` / `cornerRadius`. `TEXT` has no `cornerRadius` / `padding*` / `layoutMode`. `layoutPositioning='ABSOLUTE'` needs parent with `layoutMode !== 'NONE'`. Check `'<prop>' in node` or grep [references/plugin-api-standalone.d.ts](references/plugin-api-standalone.d.ts). Full list in [references/critical-rules-deep.md](references/critical-rules-deep.md).

10. **Reuse evidence while it remains valid.** Do not repeat metadata reads or screenshots when nothing relevant changed. Reinspect when a mutation, external change, or recovery requirement invalidates earlier evidence.

11. **Stop once requirements pass.** Gather enough evidence to establish correctness; avoid redundant checks, but do not leave known defects unresolved to meet a call limit.

12. **On any `use_figma` error, obey `safeToRetryWithoutCanvasRead`.** If `true`, correct the identified error and retry without adding a diagnostic canvas read. If `false`, read the canvas, determine what changed, then make changes. If the same API or property error occurs twice, inspect its definition and fix the root cause before retrying; do not keep shrinking batches or changing selectors around the same invalid mutation. A generic error message alone does not establish the cause or prove that nothing changed. See [validation-and-recovery.md](references/validation-and-recovery.md).

13. **NEVER call `mcp__figma__get_design_context`. FORBIDDEN.** This tool requires a selection (no selection exists in this environment), so every call will fail. The error is not recoverable — calling it just burns a tool slot and forces a retry. For structured reads of the file, use `mcp__figma__get_metadata` (for top-level frame discovery) and `use_figma` with `$fig.query()` instead. **Never call `get_design_context` for any reason.**

14. **≤3 codebase `Read` calls when the task references source code.** Beyond that, grep only. The 4th codebase Read is forbidden — write your `use_figma` script with what you have.

15. **Must use auto-layout unless you have a compelling reason not to.** Create auto-layout frames with `$fig.autoLayout(...)` instead of absolutely-positioning nodes.  New auto-layout frames are created with both axes hugging content. Explicitly assign `layoutSizingHorizontal` or `layoutSizingVertical` to `'FILL'` for auto-layout children if you want them to fill the auto-layout container's counter axis.

16. **Gradient paints need ALL fields:** `type`, `gradientStops`, `gradientTransform` (a `[[a,b,tx],[c,d,ty]]` matrix). Missing any throws validation error. See [references/critical-rules-deep.md](references/critical-rules-deep.md).

17. **Discover available fonts, esp. for style variations.** Use `await figma.listAvailableFontsAsync()` to discover available fonts for `$fig.text({ fontName: ... })`.

18. **Set variable `scopes` explicitly when creating variables.** The default `ALL_SCOPES` pollutes every property picker. Use specific scopes — `['FRAME_FILL', 'SHAPE_FILL']` for backgrounds, `['TEXT_FILL']` for text, `['GAP']` for spacing, `['CORNER_RADIUS']` for radii; primitives that shouldn't appear in pickers get `[]`. In `$fig`, pass `scopes` to `colorVar` / `numVar`; in the raw API, set `variable.scopes`. See [references/variable-patterns.md](references/variable-patterns.md).

19. **Never read `componentPropertyDefinitions`, `componentProperties`, or `valuesByMode` across a collection.** Resolve specific node IDs first, then read the property bundle only for those IDs. Reading one resolved node is safe; mapping these getters over `findAll*` results, `children`, or `getLocalVariables*` is the single largest cause of oversized returns.

20. **Broad reads return `id`, `name`, `type` and counts only.** Fetch details for selected IDs in later calls. Return each file-wide inventory — variables, text styles, effect styles, paint styles, components, pages — in its own call; do not combine them into one return.

21. **When a read may be large, measure the serialized return before returning it.** Bytes, not array length: `.slice()` bounds row count but not per-item size. If over budget, narrow the ID set or split across calls. Never drop required IDs or silently truncate.

### Bulk mutation of existing nodes (swap/update/replace)

For tasks like "swap N icons", "update M colors", "replace K instances":
1. **DISCOVER + MUTATE** together when safe: use scoped `$fig.query()` and planned mutations; return coverage evidence when the automatic result is insufficient.
2. **VERIFY** only what the mutation result does not establish. Check visual results when needed.
3. **FIX** any remaining defects with targeted changes, then report once requirements pass.

Choose call boundaries for recoverability, not a fixed call budget. On failure, follow Rule 12. See [validation-and-recovery.md](references/validation-and-recovery.md).

## Node property gotchas

Do not guess node properties or assume CSS-like properties. Accessing non-existent properties will throw `TypeError: node.foo: no such property 'foo' on TYPE node`. Each throw burns a retry. [plugin-api-standalone.index.md](references/plugin-api-standalone.index.md) contains the list of all symbols in the API. Use that file and grep the full API typings in [plugin-api-standalone.d.ts](references/plugin-api-standalone.d.ts) for the full definitions.

- **Only `FRAME` / `COMPONENT` / `COMPONENT_SET` / `INSTANCE` / `GROUP` / `SECTION` / `PAGE` have `.children`.** `RECTANGLE`, `TEXT`, `ELLIPSE`, `POLYGON`, `STAR`, `VECTOR`, `LINE`, `SLICE`, `STICKY`, `SHAPE_WITH_TEXT`, `STAMP`, `CONNECTOR`, `TABLE`, `WIDGET`, `EMBED`, `MEDIA` do NOT. Check `'children' in node` before accessing a node's children.
- **Narrow before accessing `characters` or `description`.** Use typed query selectors or a capability guard for text-capable nodes. Set component purpose/usage in `description` only on `COMPONENT` or `COMPONENT_SET`. Optional chaining does not protect unsupported property access.
- **`GROUP` has NO `fills` / `strokes` / `cornerRadius`.** Apply paints/radii on the child shapes inside.
- **Figma auto-layout != CSS flexbox.** There is no such thing as margin.
- **`TEXT` DOES NOT HAVE container properties.** Text has font / size / decoration / fills. Do not use container properties like padding, layout mode, item spacing, etc.
- **`INSTANCE` descendants are read-only for structural ops** — you cannot `appendChild` / `insertChild` into an instance child. Edit the source `COMPONENT` or detach first.
- **Never use `primaryAxisSizingMode` or `counterAxisSizingMode` on a node. ** Use `layoutSizingHorizontal` or `layoutSizingVertical` with 'FIXED' | 'HUG' | 'FILL'. Use 'FILL' only when the parent has auto-layout.
- **There is NO `instance.swapMainComponent(...)`.** Use `instance.setProperties({...})` with the component-property variant value, OR `$fig.query(...).set({props: {...}})`. There IS `instance.swapComponent(component)` (different method name).

## References

- [references/fig-builder.md](references/fig-builder.md) — full `$fig` API and worked patterns
- [references/critical-rules-deep.md](references/critical-rules-deep.md) — WRONG/RIGHT examples, full node-type pitfall list, bulk-mutation template, syntax-bug checklist
- [references/gotchas.md](references/gotchas.md) — raw Plugin API edge cases
- [references/plugin-api-standalone.d.ts](references/plugin-api-standalone.d.ts) — type definitions (grep, don't read whole)
- [references/plugin-api-standalone.index.md](references/plugin-api-standalone.index.md) — API navigation
- [references/common-patterns.md](references/common-patterns.md), [component-patterns.md](references/component-patterns.md), [variable-patterns.md](references/variable-patterns.md), [text-style-patterns.md](references/text-style-patterns.md), [effect-style-patterns.md](references/effect-style-patterns.md) — pattern playbooks
- [references/working-with-design-systems/](references/working-with-design-systems/) — design system workflows
- [references/validation-and-recovery.md](references/validation-and-recovery.md) — error recovery patterns
