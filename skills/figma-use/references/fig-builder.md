---
name: $fig builder API
description: Plan-based builder for creating and editing Figma nodes with automatic font loading, correct ordering, and one-batch materialization
---

# `$fig` Builder API

`$fig` is a plan-based builder exposed as a global in `use_figma` scripts. Every call builds a lightweight plan tree; nothing touches the Figma API until the plan is materialized. The plan is **automatically materialized** when the script finishes — you do not need to call `$fig.done()` explicitly.

## When to use `$fig` vs raw Plugin API

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

## Creating nodes

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

### Design-mode create methods

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

### Grouping and boolean operations

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

#### Required follow-up — grid the variants (`$fig` build + raw layout)

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

Skipping step 2–4 is the single most common variant bug — the set collapses to one visible variant with the rest hidden behind it. For the full multi-axis version (State on columns, Size/Style on rows) plus doc frames and grid labels, see [Laying Out Variants After combineAsVariants (Required)](component-patterns.md#laying-out-variants-after-combineasvariants-required) and the complete [`createComponentWithVariants.js`](../../figma-generate-library/scripts/createComponentWithVariants.js) script.

## Component properties

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

Prefer these over raw `comp.addComponentProperty(...)`, which must run on a materialized *product* component in the right order — mis-sequencing throws (`"Can only set component property definitions on a product component"`, `"no setter for property"`). The `$fig` methods handle the timing and the variant de-dup for you. To set property *values* on an instance (not define them), use `setProperties` — see [component-patterns.md](component-patterns.md).

## Styles — create, reference, apply

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

### Applying a style to a node

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

## Variables — create, reference, bind

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

### Binding a variable to a node property

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

### Variable aliasing (semantic → primitive)

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

### Building a component with bound variables (the default for components)

When you build a **component or reusable UI** — even a single component — binding its tokenized visual properties is part of finishing the work, not an optional nicety. The component is **not complete** while a value that *has* a corresponding token (colors, radii, spacing the source defines, or that you created) is still a hardcoded literal. Pass the variable **handle straight into the property** (same routing as above). **Do not** copy resolved token values into local JS constants (e.g. `const VARIANTS = [{ bg: '#2c2c2c' }]`) and paint with `hex(...)` — that bypasses variables entirely. **Only bind values that have a token**; values with genuinely no token (one-off geometry, static dividers) correctly stay literal — don't fabricate tokens to bind. Build a primitive tier, alias a semantic tier to it, then bind the semantic vars into `$fig.component`:

```js
const prims = $fig.varCollection({ name: 'Primitives', modes: ['Value'] })
const blue600 = prims.colorVar({ name: 'blue/600',  values: { Value: '#2563EB' }, scopes: ['FRAME_FILL'] })
const white   = prims.colorVar({ name: 'base/white', values: { Value: '#FFFFFF' }, scopes: ['TEXT_FILL'] })
const space3  = prims.numVar({ name: 'space/3',  values: { Value: 12 }, scopes: ['GAP'] })
const radius2 = prims.numVar({ name: 'radius/2', values: { Value: 8 }, scopes: ['CORNER_RADIUS'] })

const sem = $fig.varCollection({ name: 'Semantic', modes: ['Light', 'Dark'] })
const btnBg   = sem.colorVar({ name: 'button/bg',   values: { Light: blue600, Dark: blue600 }, scopes: ['FRAME_FILL'] })
const btnText = sem.colorVar({ name: 'button/text', values: { Light: white,   Dark: white  }, scopes: ['TEXT_FILL'] })

// Bind the handles straight into the component's props — no literal hex / numbers.
$fig.component({
  name: 'Size=md, State=default',
  layoutMode: 'HORIZONTAL',
  paddingLeft: space3, paddingRight: space3, itemSpacing: space3,
  cornerRadius: radius2,                       // numVar → binds all four corners
  fills: [{ type: 'SOLID', color: btnBg }],    // colorVar → bound paint
}, [
  $fig.text({
    characters: 'Button',
    fontName: { family: 'Inter', style: 'Medium' },
    fills: [{ type: 'SOLID', color: btnText }],
  }),
])
```

For a full variant set, build each variant this way, then wrap them in `$fig.variants(...)` and lay them out in a grid. Only intentionally-fixed geometry (icon pixel sizes, static 1px dividers) should stay literal.

**Building across multiple `use_figma` calls? Rehydrate the variable handles before binding.** A common failure: create the variable collection in one call, then build the component in a *later* call and bind nothing (falling back to literals) because the handles from the first call are out of scope. Each `use_figma` call is independent — a plan handle does not survive across calls. In the build call, re-fetch the variables by the IDs you returned (`$fig.getVar(realId)`, or `figma.variables.getVariableByIdAsync(id)` for the raw API) and bind those. Prefer doing var-creation and component-build in the **same** call when practical, so the handles are already in scope.

## Reading / referencing existing nodes

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

## Mutating nodes

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

## Plan-node methods (chainable)

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

## Inline screenshots — `planNode.screenshot(opts?)`

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

### `queryResult.screenshot(opts?)` — bulk screenshots from a query

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

## Reaching the real `SceneNode` — `planNode.node`

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

## Auto-flush and `done()`

The plan is automatically materialized when your `use_figma` script finishes — you do **not** need to call `$fig.done()`. The runtime registers a shutdown action that flushes any pending plan state before the script returns. The tool result will include a `FigDoneResult` object containing the created/updated/deleted node IDs and names.

You can still call `$fig.done()` explicitly if you need to materialize partway through a script and then read real node properties (e.g. measuring `width`/`height` that depend on auto-layout). `done()` returns a promise that you need to `await`.

```js
// Usually not needed — but if you need real node state mid-script:
await $fig.done()
```

If you want a custom tool result other than `FigDoneResult`, you can use the `.id` getter on plan nodes, which will return real node IDs after `done()` has run.

## Security gating

`$fig` is only exposed in the `evals`, `assistant`, and `mcp-server` plugin runtimes. It is **not** available to regular web plugins — this is a security boundary, not a bug.
