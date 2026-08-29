# figma-use — Deep Critical Rules & Worked Examples

The SKILL.md body has the terse rules. This file has the worked WRONG/RIGHT examples and edge cases. Load this when:
- You're about to write a multi-section script and want to see the full $fig builder pattern
- You hit a `Property X failed validation` error and want the validation reference
- You're doing bulk-mutation work and need the concrete 3-call template

---

## $fig — full worked examples

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

### Bulk component swap — use $fig.query().each(), not findAll() + setProperties loop

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

### Bulk variable creation — loop with `$fig.set`

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

### When NOT to use $fig
Mid-script reading real `SceneNode` state, or operations on non-SceneNode types (Variables, Components themselves). For those, raw Plugin API in a single `use_figma` call is correct.

Note: "I need a library component" alone is **not** a reason to leave `$fig`. Pass the `componentKey` from `search_design_system` straight into `$fig.get(...)` / `$fig.instance(...)` — same for style `key` (`$fig.getStyle`) and variable `key` (`$fig.getVar`). For component sets, pass variant property values in `props` and `$fig.instance` resolves the matching variant via `setProperties` — you do not need to import the set and drill into `compSet.children`.

---

## Variants via data, not enumeration

When the task asks for N parallel things ("build 3 styles", "create 4 button states", "5 color swatches"):

1. Define varying parts as a JS array of objects.
2. Define a single builder function that takes one object → one output.
3. Loop: `VARIANTS.forEach((v, i) => build(v, i))` or `VARIANTS.map(build)`.

The expensive way is writing N separate procedural blocks — that requires reasoning through each variant independently in thinking (1–3KB per variant). The data-array pattern compresses that to one builder + one array literal.

Each KB of pre-mutation thinking costs ~$0.02–0.04. Replacing 15KB of "Style 1 has blue accents... Style 2 has warm orange tones..." with `const STYLES = [{...}, {...}, {...}]; STYLES.forEach(build)` saves ~$0.30 on a typical multi-variant task.

---

## Color validation — WRONG vs RIGHT

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

## Gradient paints — all fields required

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

## Node-type property gotchas (full list)

Touching a property that doesn't exist on a node's type throws `TypeError: node.foo: no such property 'foo' on TYPE node`. Each throw burns a retry.

- **Only `FRAME` / `COMPONENT` / `COMPONENT_SET` / `INSTANCE` / `GROUP` / `SECTION` / `PAGE` have `.children`.** `RECTANGLE`, `TEXT`, `ELLIPSE`, `POLYGON`, `STAR`, `VECTOR`, `LINE`, `SLICE`, `STICKY`, `SHAPE_WITH_TEXT`, `STAMP`, `CONNECTOR`, `TABLE`, `WIDGET`, `EMBED`, `MEDIA` do NOT.
- **`GROUP` has NO `fills` / `strokes` / `cornerRadius`.** Apply paints/radii on the child shapes inside.
- **`TEXT` has NO `cornerRadius`, `paddingLeft/Right/Top/Bottom`, `itemSpacing`, `layoutMode`, `layoutSizingHorizontal/Vertical`** (those are container properties). Text has font / size / decoration / fills.
- **`INSTANCE` descendants are read-only for structural ops** — you cannot `appendChild` / `insertChild` into an instance child. Edit the source `COMPONENT` or detach first.
- **`layoutPositioning = 'ABSOLUTE'` requires the parent to have `layoutMode !== 'NONE'`.** Setting ABSOLUTE under a plain frame / page throws.
- **`layoutSizingHorizontal/Vertical = 'FILL'` requires parent with auto-layout.** Either set parent's `layoutMode` first, or use explicit `resize(w, h)`.
- **`counterAxisAlignItems` is an enum**: only `'MIN' | 'CENTER' | 'MAX' | 'BASELINE'`. `'STRETCH'` / `'SPACE_BETWEEN'` fail. `primaryAxisAlignItems` has different valid values — don't confuse.
- **There is NO `instance.swapMainComponent(...)`.** Use `instance.setProperties({...})` with the component-property variant value, OR `$fig.query(...).set({componentProperties: {...}})`. There IS `instance.swapComponent(component)` (different method name).

Before referencing any property: (a) check `'<prop>' in node`, (b) gate by `if (node.type === 'FRAME' || ...)`, or (c) consult [plugin-api-standalone.d.ts](plugin-api-standalone.d.ts).

---

## Bulk-mutation stopping rule (full template)

A bulk-mutation task (swap N icons, update M colors, replace K instances) is COMPLETE in **3 `use_figma` calls**:

1. **Call 1 — DISCOVER + MUTATE in one script.** Combine: find targets via `figma.root.findAll`, import components, mutate. Use `$fig.query(...).each(...)` for the loop. Return the count.

2. **Call 2 — VERIFY (optional).** Read-only `findAll` to count remaining targets. Skip if Call 1's return showed full coverage.

3. **Call 3 — FINAL REPORT in assistant text, no tool call.** State what was swapped + any remaining edges. STOP.

NO 4th call. NO chasing the last 20% of edge cases. If Call 1 errors, fix and redo — that's still your one mutation call. Cap: 2 mutation attempts + 1 verify.

### Concrete arrow→chevron template:
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

## Cross-page bulk operations — one query, all pages

```js
// RIGHT — one query, all pages, all instances
await Promise.all(figma.root.children.map(p => figma.loadAllPagesAsync ? null : figma.setCurrentPageAsync(p)))  // ensure pages loaded
const instances = figma.root.findAll(n => n.type === 'INSTANCE' && n.name === 'arrow_drop_down')
// OR — using $fig.query (preferred):
$fig.query('INSTANCE[name=arrow_drop_down]', figma.root)
```

NOT: "Explore page 1", "Explore page 2"... each costs ~30s + thinking tax. One `findAll` from `figma.root` searches the entire document in one call.

---

## "An unexpected error occurred" handling

When `use_figma` returns exactly `"An unexpected error occurred. Figma Debug UUID: <uuid>"` (no JS stack), the request hit a server-side path error. Do NOT retry the same script unchanged — that has near-zero success probability.

Change approach: break into smaller batches, switch from `$fig.query(...).set(...)` to per-node `node.set(...)` (or vice versa), pick a tighter selector, or drop one node-property to isolate which triggers the server error. If the same shape recurs after 2 different attempts, stop and report.

---

## Common JS syntax bugs to avoid before submitting >5KB scripts

- **Unbalanced braces in template literals** — `${{...}}` or missing `}` in multi-line strings throws `SyntaxError: expecting '}'`.
- **Trailing commas in function calls** — `foo(a, b,)` may fail in some JS engines.
- **Missing `await`** before async ops — `figma.loadFontAsync(...)` without `await` is a silent bug.
- **`=` vs `==`** inside object literals — `{ size: =14 }` should be `{ size: 14 }`.

SyntaxError costs a full retry ($0.10–0.20). Scan visually before submitting large scripts.

---

## Why decisiveness matters (cost breakdown)

Each KB of upfront thinking ≈ $0.02–0.04. A 20KB upfront plan = ~$0.30–$0.80 spent before any tool call.

For multi-section tasks: decide high-level approach in <2KB, write the FIRST section's script, then plan the second once you've seen the first work. Plan-as-you-build is materially cheaper than plan-then-build-all.

---

## Workflow — incremental + recovery

- Break large ops into multiple `use_figma` calls; validate after each *logical phase* (not every micro-step).
- On error: read the message carefully, identify which property/type triggered it, fix once, retry. Don't blindly resubmit.
- On 3 retries of same error: switch approach (most often: switch to `$fig`).
- Cap script size around 8 KB / ~250 lines. Larger → split by section.
