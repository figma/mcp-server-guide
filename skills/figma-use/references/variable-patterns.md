# Variable & Token API Patterns

> Part of the [use_figma skill](../SKILL.md). How to correctly create, bind, scope, and alias variables using the Plugin API.
>
> For design system context (aliasing strategy, mode decisions, code syntax philosophy, grouping conventions), see [wwds-variables](working-with-design-systems/wwds-variables.md).

Use `$fig` for supported operations. Use the raw Plugin API for explicit variable modes, variable discovery, and code-syntax removal.

## Contents

- Creating Variables with `$fig`
- Binding Variables to Node Properties with `$fig`
- Variable Scopes: What They Are and How to Set Them
- Code Syntax
- Using Library Variables by Key (preferred)
- Raw-API fallback — Discovering and Importing Variables manually
- Discovering Existing Variables in the File
- Effect Styles (For Shadows)

---

## Creating Variables with `$fig`

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

// TIMING — for motion animation durations (value in seconds)
const timing = tokens.timingVar({
  name: 'motion/duration-fast',
  values: { Light: 0.2, Dark: 0.2 },
})

// EASING — for motion animation easing curves
const easeOut = {
  type: 'CUSTOM_CUBIC_BEZIER',
  easingFunctionCubicBezier: { x1: 0, y1: 0, x2: 0.58, y2: 1 },
}
const easing = tokens.easingVar({
  name: 'motion/ease-out',
  values: { Light: easeOut, Dark: easeOut },
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

**Note:** Paint colors use `{r, g, b}` (no alpha), but COLOR variable values use `{r, g, b, a}` (with alpha). Don't mix them up.

**Note:** TIMING values are durations in seconds (e.g., `0.2` for 200ms). EASING values use the same shape as keyframe easing objects — see [motion-easing.md](../../figma-use-motion/references/motion-easing.md) for the full easing object shape.

### Updating after creation

```javascript
// Update any property — name, scopes, description, codeSyntax, etc.
myVar.set({ codeSyntax: { WEB: 'var(--size-lg)' } })
myVar.set({ scopes: ['WIDTH_HEIGHT', 'GAP'] })

// Update a single mode value
myVar.value('Dark', '#1E3A5F')

// Update all mode values at once
myVar.setValues({ Light: 16, Dark: 24 })
// Or with an updater fn (receives the current modeId-keyed values map)
myVar.setValues(values => ({ ...values, [darkModeId]: 24 }))
```

## Binding Variables to Node Properties with `$fig`

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

### Applying a mode to a frame (raw API)

`setExplicitVariableModeForCollection` is not supported by `$fig` — use the raw API after `done()`:

```javascript
// All bound children of this frame will resolve to the specified mode's values
frame.setExplicitVariableModeForCollection(collection, modeId);
```

Without this, all nodes use the collection's default (first) mode.

## Variable Scopes: What They Are and How to Set Them

`variable.scopes` controls which Figma property pickers show the variable. The default is `["ALL_SCOPES"]` which shows it everywhere — this is almost never what you want.

```javascript
myVar.set({ scopes: ['FRAME_FILL', 'SHAPE_FILL'] })  // only fill pickers
myVar.set({ scopes: ['TEXT_FILL'] })                 // only text color picker
myVar.set({ scopes: ['GAP'] })                       // only gap/spacing pickers
myVar.set({ scopes: ['CORNER_RADIUS'] })             // only radius pickers
myVar.set({ scopes: [] })                            // hidden from all pickers
```

**All valid scope values:**
`ALL_SCOPES`, `TEXT_CONTENT`, `CORNER_RADIUS`, `WIDTH_HEIGHT`, `GAP`, `ALL_FILLS`, `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL`, `STROKE_COLOR`, `STROKE_FLOAT`, `EFFECT_FLOAT`, `EFFECT_COLOR`, `OPACITY`, `FONT_FAMILY`, `FONT_STYLE`, `FONT_WEIGHT`, `FONT_SIZE`, `LINE_HEIGHT`, `LETTER_SPACING`, `PARAGRAPH_SPACING`, `PARAGRAPH_INDENT`

**Always set scopes explicitly** — `ALL_SCOPES` is the default but almost never what you want. For a comprehensive scope-to-use-case mapping table, see [token-creation.md § Variable Scopes — Complete Reference Table](../../figma-generate-library/references/token-creation.md).

**Always check the existing file's scope patterns before creating variables** — match whatever convention is already in use. See "Discovering Existing Variables in the File" below.

## Code Syntax

Links a Figma variable back to its code counterpart. Use the `codeSyntax` property when creating or updating a variable (see "Creating Variables with `$fig`" section above).

`$fig` has no equivalent for removing a platform from a variable's `codeSyntax`. Use the raw API in the file the variable is defined in:

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

// CORRECT — replace all whitespace and slashes
`var(--${figmaName.replace(/[\s\/]+/g, '-').toLowerCase()})`

// BEST — use the original CSS variable name from the source, not a derived one
`var(${token.cssVar})`
```

## Using Library Variables by Key (preferred)

A variable found via a `search_design_system` `queries` entry with `entity: "variable"` returns a `key`. Pass it directly into `$fig.getVar(variableKey)` — the plan queues the library import automatically. Same call also accepts a local variable id; one call site, both shapes.

```javascript
const brand = $fig.getVar(BRAND_COLOR_VAR_KEY)
$fig.rectangle({ fills: [{ type: 'SOLID', color: brand }] })

// Scalar variable on any numeric property
const gap = $fig.getVar(SPACING_400_KEY)
$fig.autoLayout({ name: 'Toolbar', layoutMode: 'HORIZONTAL', itemSpacing: gap })
```

## Raw-API fallback — Discovering and Importing Variables manually

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

## Discovering Existing Variables in the File

**Always inspect the file's existing variables before creating new ones.** Different files use different naming conventions, scope patterns, and collection structures. Match what's already there.

### List collections with mode info

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const results = collections.map(c => ({
  name: c.name,
  id: c.id,
  varCount: c.variableIds.length,
  modes: c.modes.map(m => ({ name: m.name, id: m.modeId }))
}));
return results;
```

### Inspect scope patterns used in existing variables

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync();
// Batch every getVariableByIdAsync into a single Promise.all — sequential
// awaits inside the loop would serialize one IPC round-trip per variable.
const allIds = collections.flatMap(c => c.variableIds);
const allVars = await Promise.all(
  allIds.map(id => figma.variables.getVariableByIdAsync(id))
);
const scopeGroups = {};
for (const v of allVars) {
  if (!v) continue;
  const key = JSON.stringify(v.scopes);
  if (!scopeGroups[key]) scopeGroups[key] = [];
  scopeGroups[key].push(v.name);
}
return scopeGroups;
```

### Build a name→variable lookup for reuse

```javascript
const varByName = {};
for (const v of await figma.variables.getLocalVariablesAsync()) {
  varByName[v.name] = v;
}
// Only create new variables for tokens that have no match
```

## Listing Collections with Full Variable Details

The async API returns richer data including code syntax and scopes per variable:

```javascript
/**
 * Lists all local variable collections defined in the current Figma file,
 * including metadata for their modes and variables.
 *
 * @returns {Promise<Array<{
 *   name: string,
 *   id: string,
 *   modes: Array<[name: string, modeId: string]>,
 *   variables: Array<[name: string, id: string, codeSyntax: object, scopes: string[]]>
 * }>>}
 */
async function listVariableCollectionsAndVariables() {
  const collections = await figma.variables.getLocalVariableCollectionsAsync();
  // flatMap every variable ID across all collections into one Promise.all,
  // then look up per-collection from a Map. Avoids nested Promise.all and
  // still issues every lookup in parallel.
  const allIds = collections.flatMap(c => c.variableIds);
  const fetched = await Promise.all(
    allIds.map(id => figma.variables.getVariableByIdAsync(id))
  );
  const byId = new Map(allIds.map((id, i) => [id, fetched[i]]));
  return collections.map(collection => ({
    name: collection.name,
    id: collection.id,
    modes: collection.modes.map(m => [m.name, m.modeId]),
    variables: collection.variableIds
      .map(id => byId.get(id))
      .filter(v => v)
      .map(v => [v.name, v.id, v.codeSyntax, v.scopes])
  }));
}
```

Full runnable script:

```javascript
const results = await listVariableCollectionsAndVariables();
return results;
```


## Effect Styles (For Shadows)

Shadows can't be stored as variables. Use effect styles. For comprehensive patterns, see [effect-style-patterns.md](effect-style-patterns.md).

```javascript
const shadow = $fig.effectStyle({
  name: 'Shadow/Subtle',
  effects: [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.06 },
    offset: { x: 0, y: 2 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: 'NORMAL',
  }],
})

// Apply the style handle to an existing frame
$fig.get(frame.id).set({ effects: shadow })
await $fig.done()
```
