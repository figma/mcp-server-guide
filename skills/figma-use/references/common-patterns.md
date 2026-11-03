# Common Patterns

> Part of the [use_figma skill](../SKILL.md). Working code examples for frequently used operations.

## Contents

- Basic Script Structure
- Create a Styled Shape
- Create a Text Node
- Create Frame with Auto-Layout
- Create Variable Collection with Multiple Modes
- Bind Color Variable to a Fill
- Create Component Variants with Component Properties
- Use a Component by Key (Team Libraries)
- Component Set with Variable Modes (Full Pattern)
- Large ComponentSet with Variable Modes (Multi-Step Pattern)
- Read Existing Nodes and Return Data


## Basic Script Structure

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

## Create a Styled Shape

```js
$fig.rectangle({
  name: "Blue Box",
  width: 200,
  height: 100,
  fills: [{ type: 'SOLID', color: { r: 0.047, g: 0.549, b: 0.914 } }],
  cornerRadius: 8,
})
```

## Create a Text Node

```js
$fig.text({
  characters: "Hello World",
  fontSize: 16,
  fills: [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }],
  textAutoResize: 'WIDTH_AND_HEIGHT',
})
```

## Create Frame with Auto-Layout

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

## Create Variable Collection with Multiple Modes

```js
const collection = $fig.varCollection({ name: 'Theme/Colors', modes: ['Light', 'Dark'] })
const bgVar = collection.colorVar({
  name: 'bg',
  values: { Light: '#FFFFFF', Dark: '#1A1A1A' },
})
const textVar = collection.colorVar({
  name: 'text', values: { Light: '#000000', Dark: '#FFFFFF' },
})
await $fig.done()

// Real collection, mode, and variable IDs are available after materialization.
const modes = Object.fromEntries(collection.variableCollection.modes.map(m => [m.name, m.modeId]))
return {
  collectionId: collection.id,
  lightModeId: modes.Light,
  darkModeId: modes.Dark,
  bgVarId: bgVar.id,
  textVarId: textVar.id,
}
```

## Bind Color Variable to a Fill

```js
const variable = $fig.getVar('VariableID:1:2')
const rect = $fig.rectangle({ fills: [{ type: 'SOLID', color: variable }] })
await $fig.done()
return { nodeId: rect.id }
```

## Create Component Variants with Component Properties

Use the builder's property helpers on the layers inside each variant. Keep all creation in the plan; only unwrap to measure and lay out the materialized variants.

```js
const components = ['primary', 'secondary'].map((variant) =>
  $fig.component({
    name: `variant=${variant}`, layoutMode: 'HORIZONTAL',
    primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER',
    paddingLeft: 12, paddingRight: 12, paddingTop: 8, paddingBottom: 8,
    layoutSizingHorizontal: 'HUG', layoutSizingVertical: 'HUG',
    cornerRadius: 6, itemSpacing: 8,
  }, [
    $fig.instance('ICON_COMPONENT_ID', { visible: false })
      .booleanProp('Show Icon').instanceSwapProp('Icon'),
    $fig.text({ characters: 'Button', fontSize: 14,
      fontName: { family: 'Inter', style: 'Regular' } }).textProp('Label'),
  ]),
)
const set = $fig.variants({ name: 'Button' }, components)
const preview = $fig.instance(set, { name: 'Button preview', props: { variant: 'primary' } })
$fig.get('DESTINATION_FRAME_ID').append(preview)
await $fig.done()
const componentSet = set.node // raw node; set.children still contains plan nodes

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

## Use a Component by Key (Team Libraries)

`search_design_system` returns `componentKey` for `assetType: "component"` and `componentSetKey` for `assetType: "component_set"`. Pass it directly into `$fig.get(...)` / `$fig.instance(...)` — the plan queues the library import automatically, so no separate `importComponentByKeyAsync` call is needed. The same call site accepts node IDs for components in the current file.

```js
// PREFERRED — asset key flows straight from search_design_system into $fig
const instance = $fig.instance(BUTTON_COMPONENT_KEY, { name: 'Submit', x: 40, y: 40 })

// Component set: pass the set's componentSetKey + variant props
const variantInstance = $fig.instance(BUTTON_SET_KEY, {
  name: 'Submit (md)',
  x: 240, y: 40,
  props: { Size: 'md', Variant: 'primary' },
})

// Wrap a set without instantiating, e.g. to inspect it after $fig.done()
const set = $fig.get(BUTTON_SET_KEY)
```

You do not need to import the component set, drill into `compSet.children`, or call `defaultVariant.createInstance()` yourself. `$fig.instance(setKey, { props })` picks the matching variant by `setProperties` after the instance is created from the default variant — the same path you'd use for variant switches on an existing instance via `$fig.set(inst, { props })` or `inst.setInstanceProps({...})`.

### Discover a set's variant props when you only have its key

`search_design_system` returns the set's `componentSetKey` but not its variant properties. Discover them across **two `use_figma` calls** because the first call returns the valid values in the tool result:

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
    .filter((child) => child.type === 'COMPONENT')
    .map((child) => ({ name: child.name, variantProperties: child.variantProperties })),
}
```

```js
// Call 2 — read the props from call 1's result, then instantiate the variant you want
$fig.instance(BUTTON_SET_KEY, { props: { Size: 'Large', Kind: 'Secondary' } })
```

The library must be reachable from the current file — a key from an inaccessible library errors with `failed to import DS asset <key>`.

## Component Set with Variable Modes (Full Pattern)

Create collections, variables, and components in the plan. FigQuery loads the requested fonts and binds variable handles in paints. After materialization, use the raw node API to select explicit modes and lay out the variants; FigQuery has no builder method for explicit variable modes.

```js
// 1. Create color collection with modes per variant
const modeNames = ['primary', 'secondary']
const colors = $fig.varCollection({ name: 'Component/Colors', modes: modeNames })
const bgVar = colors.colorVar({
  name: 'bg',
  values: { primary: '#0066E6', secondary: '#000000' },
})
const textVar = colors.colorVar({
  name: 'text-color',
  values: { primary: '#FFFFFF', secondary: '#1A1A1A' },
})

// 2. Create components with variable bindings
const components = modeNames.map(mode => $fig.component({
  name: `variant=${mode}`, layoutMode: 'HORIZONTAL',
  primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER',
  paddingLeft: 12, paddingRight: 12,
  layoutSizingHorizontal: 'HUG', layoutSizingVertical: 'HUG', cornerRadius: 6,
  fills: [{ type: 'SOLID', color: bgVar }],
}, [
  $fig.text({
    characters: 'Button', fontName: { family: 'Inter', style: 'Medium' }, fontSize: 14,
    fills: [{ type: 'SOLID', color: textVar }],
  }),
]))
const set = $fig.variants({ name: 'Button' }, components)
await $fig.done()

const collection = colors.variableCollection
const modeIds = Object.fromEntries(collection.modes.map(m => [m.name, m.modeId]))
let nextX = 40
for (const [i, component] of components.entries()) {
  const node = component.node
  node.setExplicitVariableModeForCollection(collection, modeIds[modeNames[i]])
  node.x = nextX
  node.y = 40
  nextX += node.width + 40
}
set.node.resizeWithoutConstraints(nextX, Math.max(...components.map(c => c.node.height)) + 80)
return { componentSetId: set.id, colorCollectionId: colors.id }
```

## Large ComponentSet with Variable Modes (Multi-Step Pattern)

For component sets with many variants (50+), split into multiple `use_figma` calls. Plan nodes do not survive between calls; return real IDs after `$fig.done()` and resolve them again in the next call.

**Call 1: Create variable collections and return IDs**

```js
const modeNames = ['mode1', 'mode2']
const coll = $fig.varCollection({ name: 'MyComponent/Colors', modes: modeNames })
const colorData = {
  'bg/default': ['#0B6BCB', '#636B74'],
  'bg/hover': ['#084E96', '#424A53'],
  'text': ['#FFFFFF', '#FFFFFF'],
}
const variables = Object.fromEntries(Object.entries(colorData).map(([name, values]) => [
  name,
  coll.colorVar({ name, values: Object.fromEntries(modeNames.map((mode, i) => [mode, values[i]])) }),
]))
await $fig.done()
return {
  collId: coll.id,
  modeIds: Object.fromEntries(coll.variableCollection.modes.map(m => [m.name, m.modeId])),
  varIds: Object.fromEntries(Object.entries(variables).map(([name, variable]) => [name, variable.id])),
}
```

**Call 2: Create components using stored IDs, combine and layout**

```js
// Replace these literals with the IDs returned by Call 1.
const collId = 'VariableCollectionId:X:Y'
const modeIds = { mode1: 'X:0', mode2: 'X:1' }
const varIds = {
  'bg/default': 'VariableID:X:2',
  'bg/hover': 'VariableID:X:3',
  'text': 'VariableID:X:4',
}
const collection = $fig.getVarCollection(collId)
const backgrounds = {
  default: $fig.getVar(varIds['bg/default']),
  hover: $fig.getVar(varIds['bg/hover']),
}
const textColor = $fig.getVar(varIds.text)
const modeNames = ['mode1', 'mode2']
const states = ['default', 'hover']
const variants = []
for (const [row, mode] of modeNames.entries()) {
  for (const [col, state] of states.entries()) {
    const component = $fig.component({
      name: `mode=${mode}, state=${state}`, layoutMode: 'HORIZONTAL',
      primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER',
      layoutSizingHorizontal: 'HUG', layoutSizingVertical: 'HUG',
      paddingLeft: 12, paddingRight: 12, paddingTop: 8, paddingBottom: 8,
      fills: [{ type: 'SOLID', color: backgrounds[state] }],
    }, [
      $fig.text({
        characters: 'Button', fontName: { family: 'Inter', style: 'Semi Bold' }, fontSize: 14,
        fills: [{ type: 'SOLID', color: textColor }],
      }),
    ])
    variants.push({ component, mode, row, col })
  }
}
const set = $fig.variants({ name: 'MyComponent' }, variants.map(v => v.component))
const section = $fig.section({ name: 'MyComponent Section' }, [set])
await $fig.done()

// Explicit modes require raw nodes. Variants also need manual grid layout.
const colW = Math.max(...variants.map(v => v.component.node.width)) + 40
const rowH = Math.max(...variants.map(v => v.component.node.height)) + 40
for (const { component, mode, row, col } of variants) {
  const node = component.node
  node.setExplicitVariableModeForCollection(collection.variableCollection, modeIds[mode])
  node.x = 40 + col * colW
  node.y = 40 + row * rowH
}
const cs = set.node
cs.resizeWithoutConstraints(
  Math.max(...cs.children.map(c => c.x + c.width)) + 40,
  Math.max(...cs.children.map(c => c.y + c.height)) + 40,
)
cs.x = 100
cs.y = 100
section.node.resize(cs.width + 200, cs.height + 200)
return { csId: set.id, sectionId: section.id, count: variants.length }
```

## Read Existing Nodes and Return Data

```js
// Query the current page. map receives raw FRAME nodes, so children is safe to read.
const data = $fig.query('FRAME').map(node => ({
  id: node.id,
  name: node.name,
  width: node.width,
  height: node.height,
  childCount: node.children.length,
}))
return { frames: data }
```
