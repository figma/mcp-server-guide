# Common Patterns

> Part of the [use_figma skill](../SKILL.md). Working code examples for frequently used operations.

## Contents

- Basic Script Structure
- Create a Styled Shape
- Create a Text Node
- Create Frame with Auto-Layout
- Create Variable Collections and Bindings
- Create Components and Import by Key
- Component Sets with Variable Modes
- Multi-Step Large ComponentSet Pattern
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

## Create a Styled Shape using `$fig`

```js
$fig.rectangle({
  name: "Blue Box",
  width: 200,
  height: 100,
  fills: [{ type: 'SOLID', color: { r: 0.047, g: 0.549, b: 0.914 } }],
  cornerRadius: 8,
})
```

## Create a Styled Shape using the raw plugin API

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

## Bind Color Variable to a Fill

```js
const variable = await figma.variables.getVariableByIdAsync("VariableID:1:2")
const rect = figma.createRectangle()
const basePaint = { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }

// setBoundVariableForPaint returns a NEW paint — capture it!
const boundPaint = figma.variables.setBoundVariableForPaint(basePaint, "color", variable)
rect.fills = [boundPaint]

return { nodeId: rect.id }
```

## Create Component Variants with Component Properties

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

## Use a Component by Key (Team Libraries)

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

### Discover a set's variant props when you only have its key

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

## Component Set with Variable Modes (Full Pattern)

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

## Large ComponentSet with Variable Modes (Multi-Step Pattern)

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

## Read Existing Nodes and Return Data

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
