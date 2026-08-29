# Variable & Token API Patterns

> Part of the [use_figma skill](../SKILL.md). How to correctly create, bind, scope, and alias variables using the Plugin API.
>
> For design system context (aliasing strategy, mode decisions, code syntax philosophy, grouping conventions), see [wwds-variables](working-with-design-systems/wwds-variables.md).

Use `$fig` for everything in this file unless you hit one of the [gaps](#current-fig-gaps--use-figma-plugin-api-instead) listed at the bottom.

## Contents

- [Creating variables with `$fig`](#creating-variables-with-fig)
- [Binding variables to node properties with `$fig`](#binding-variables-to-node-properties-with-fig)
- [Current `$fig` gaps — use Figma Plugin API instead](#current-fig-gaps--use-figma-plugin-api-instead)
- [Effect Styles (For Shadows)](#effect-styles-for-shadows)

---

## Creating variables with `$fig`

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

### Updating after creation

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

### Scope reference

`variable.scopes` controls which Figma property pickers show the variable. **Always set scopes explicitly** — the default `["ALL_SCOPES"]` shows the variable everywhere, which is almost never correct.

**All valid scope values:**
`ALL_SCOPES`, `TEXT_CONTENT`, `CORNER_RADIUS`, `WIDTH_HEIGHT`, `GAP`, `ALL_FILLS`, `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL`, `STROKE_COLOR`, `STROKE_FLOAT`, `EFFECT_FLOAT`, `EFFECT_COLOR`, `OPACITY`, `FONT_FAMILY`, `FONT_STYLE`, `FONT_WEIGHT`, `FONT_SIZE`, `LINE_HEIGHT`, `LETTER_SPACING`, `PARAGRAPH_SPACING`, `PARAGRAPH_INDENT`

For a comprehensive scope-to-use-case mapping table, see [token-creation.md § Variable Scopes — Complete Reference Table](../../figma-generate-library/references/token-creation.md).

**Always check the existing file's scope patterns before creating variables** — match whatever convention is already in use. See [Discovering existing variables in the file](#discovering-existing-variables-in-the-file).

---

## Binding variables to node properties with `$fig`

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
await $fig.done()
const frame = figma.getNodeById(myFrame.id)
frame.setExplicitVariableModeForCollection(tokens.variableCollection, darkModeId)
// All variable-bound children of this frame will now resolve to the Dark mode values.
```

---

## Using library variables by key (preferred)

`search_design_system` with `includeVariables: true` returns a `key` per variable. Pass it directly into `$fig.getVar(variableKey)` — the plan queues the library import automatically. Same call also accepts a local variable id; one call site, both shapes.

```javascript
const brand = $fig.getVar(BRAND_COLOR_VAR_KEY)
$fig.rectangle({ fills: [{ type: 'SOLID', color: brand }] })

// Scalar variable on any numeric property
const gap = $fig.getVar(SPACING_400_KEY)
$fig.autoLayout({ name: 'Toolbar', layoutMode: 'HORIZONTAL', itemSpacing: gap })
```

## Raw-API fallback — discovering and importing variables manually

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

### Discovering existing variables in the file

**Always inspect the file's existing variables before creating new ones.** Match naming conventions, scope patterns, and collection structures already in use.

#### List collections with mode and variable details

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

#### Inspect scope patterns in use

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

#### Build a name→variable lookup for reuse

```javascript
const varByName = {}
for (const v of await figma.variables.getLocalVariablesAsync()) {
  varByName[v.name] = v
}
// Only create new variables for tokens that have no match
```

### Removing code syntax

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

## Effect Styles (For Shadows)

Shadows can't be stored as variables. Use effect styles. For comprehensive patterns, see [effect-style-patterns.md](effect-style-patterns.md).

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
