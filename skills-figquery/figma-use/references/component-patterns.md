# Component & Variant API Patterns

> Part of the [use_figma skill](../SKILL.md). How to correctly use the Plugin API for components, variants, and component properties.
>
> For design system context (when to use variants vs properties, code-to-Figma translation, property model), see [wwds-components](working-with-design-systems/wwds-components.md).

## Contents

- Plan nodes vs real nodes
- Creating a Component
- Combining Components into a Component Set (Variants)
- Laying Out Variants After combineAsVariants (Required)
- Component Properties: addComponentProperty API
- Linking Properties to Child Nodes (Required)
- INSTANCE_SWAP: Avoiding Variant Explosion
- Slots: createSlot and SLOT Properties
- Discovering Existing Conventions in the File
- Importing Components by Key
- Working with Instances (finding variants, setProperties, text overrides, detachInstance)


## Plan nodes vs real nodes

Use `$fig` for node creation. Its constructors and `componentHandle.createInstance()` alias return plan nodes. `done()` does not convert them to raw nodes, and `planNode.children` remains an array of plan nodes. Prefer `$fig.instance(componentPlanNode, opts)`, `.set(...)`, and `planNode.append(...)` for creation and placement. The raw property-inspection examples below explicitly access `.node` after materializing; never omit that step. See [fig-builder.md](fig-builder.md#creating-instances-from-component-plan-nodes).

## Creating a Component

`$fig.component()` returns a component plan node. Use options or `.set()` to configure it. For the raw component-property examples below, materialize and explicitly access `.node` to get a `ComponentNode`.

```javascript
const compPlan = $fig.component({
  name: 'MyComponent', layoutMode: 'HORIZONTAL',
  primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER',
  paddingLeft: 12, paddingRight: 12,
  layoutSizingHorizontal: 'HUG', layoutSizingVertical: 'HUG',
  fills: [{ type: 'SOLID', color: { r: 0.2, g: 0.36, b: 0.96 } }],
});
// Only needed if continuing with the raw component-property examples below:
await $fig.done();
const comp = compPlan.node;
if (!comp || comp.type !== 'COMPONENT') throw new Error('Expected a component');
```

## Combining Components into a Component Set (Variants)

`$fig.variants(opts, components)` groups component plan nodes into a component-set plan node. Use `$fig.component(...)` for each variant; frames are not valid variants.

Variant names use a `Property=Value` format. Every unique combination must exist as a child component — missing ones show as blank gaps in the variant picker.

```javascript
// Each component's name encodes its variant properties
const comp1 = $fig.component({ name: "size=md, style=primary" });
const comp2 = $fig.component({ name: "size=md, style=secondary" });
const set = $fig.variants({ name: "Button" }, [comp1, comp2]);
// Select a variant through the set; no intermediate flush is required.
const preview = $fig.instance(set, { name: "Button preview", props: { size: "md", style: "primary" } });
```

**Before creating variants, inspect the file** for existing naming patterns. Different files use different conventions (`State=Default` vs `state=default` vs `State/Default`). Always match what's already there.

## Laying Out Variants After combineAsVariants (Required)

After `$fig.variants` materializes, all children stack at `(0, 0)`. You **must** position them or the component set will appear as a single collapsed element with all variants overlapping.

```javascript
// Continue from the set plan node above. Flush to read measured sizes.
await $fig.done();
const cs = set.node; // cs.children contains raw ComponentNodes

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

## Component Properties: addComponentProperty API

> **Building with `$fig`?** Prefer the builder methods `layer.textProp(name)` / `.booleanProp(name)` / `.instanceSwapProp(name)` / `.slotProp(name)` — they add the property to the (set-aware) component with defaults inferred from the layer for TEXT, BOOLEAN, and INSTANCE_SWAP (SLOT uses an empty default), de-dup across variants, and handle materialization timing for you. See [fig-builder.md → Component properties](fig-builder.md#component-properties). Use the raw `addComponentProperty` API below when you are not in a `$fig` plan.

`addComponentProperty` adds a TEXT, BOOLEAN, or INSTANCE_SWAP property to a component. It returns a **string key** (e.g., `"label#4:0"`) — never hardcode or guess this key.

```javascript
// Returns the key as a string — capture it!
const labelKey = comp.addComponentProperty('Label', 'TEXT', 'Default text');
const showIconKey = comp.addComponentProperty('Show Icon', 'BOOLEAN', true);
const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', iconComponentId);
```

**Timing**: Add component properties to each variant component **before** calling `combineAsVariants`. After combining, the component set inherits all properties from its children. Do not add properties to the `ComponentSetNode` directly.

## Linking Properties to Child Nodes (Required)

A property that is added but not linked to a child node does **nothing**. You must set `componentPropertyReferences` on the child:

`$fig.text(...)` loads the required font during `await $fig.done()` before applying text properties. Raw text writes still require an explicit font load first.

```javascript
// TEXT property → link to a text node's characters
const labelKey = comp.addComponentProperty('Label', 'TEXT', 'Button');
const textPlan = $fig.text({ characters: "Button" });
await $fig.done();
const textNode = textPlan.node;
comp.appendChild(textNode);
textNode.componentPropertyReferences = { characters: labelKey };

// BOOLEAN + INSTANCE_SWAP → link to an instance node
const showIconKey = comp.addComponentProperty('Show Icon', 'BOOLEAN', true);
const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', iconComp.id);
const iconInstancePlan = $fig.instance(iconComp.id);
await $fig.done();
const iconInstance = iconInstancePlan.node; // raw node for componentPropertyReferences
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

## Slots: createSlot and SLOT Properties

Slots are designated drop zones inside a component where designers can place arbitrary content in instances — more flexible than INSTANCE_SWAP (which only swaps component instances). They appear as `SlotNode` (type `'SLOT'`) in the Plugin API and as a `SLOT`-typed component property.

### Option 1 — `planFrame.slotProp()` (preferred)

For new components, use `$fig.component` and attach `.slotProp(name)` to a descendant frame to create a slot property.

```javascript
const contentSlot = $fig.autoLayout({
  layoutMode: 'VERTICAL', width: 320, height: 200,
}).slotProp('Content');
const card = $fig.component({
  name: 'Card', layoutMode: 'VERTICAL', width: 320,
  primaryAxisSizingMode: 'AUTO', counterAxisSizingMode: 'FIXED',
}, [contentSlot]);
await $fig.done();
const slotPropKey = contentSlot.node.componentPropertyReferences.slotContentId;
```

Multiple slots are supported — bind a distinct direct child for each property:

```javascript
const cardWithFooter = $fig.component({ name: 'Card with footer' }, [
  $fig.frame({ name: 'Content' }).slotProp('Content'),
  $fig.frame({ name: 'Footer' }).slotProp('Footer'),
]);
await $fig.done();
return Object.keys(cardWithFooter.node.componentPropertyDefinitions);
```

### Option 2 — `component.createSlot()`

Creates a `SlotNode` as a direct child of the component and automatically creates a linked `SLOT` component property. No manual wiring needed.

```javascript
const card = figma.createComponent();
card.name = "Card";
card.layoutMode = "VERTICAL";
card.primaryAxisSizingMode = "AUTO";
card.counterAxisSizingMode = "FIXED";
card.resize(320, 100);

// Creates a SlotNode and auto-wires a SLOT component property
const contentSlot = card.createSlot();
contentSlot.name = "Content";
contentSlot.layoutMode = "VERTICAL"; // GRID is NOT allowed on slots
contentSlot.resize(320, 200);

// The auto-created property key is accessible via componentPropertyReferences
const slotPropKey = contentSlot.componentPropertyReferences["slotContentId"];
// e.g. "Content#7:1"
```

Multiple slots are supported — each call to `createSlot()` produces a separate slot and property:

```javascript
const contentSlot = card.createSlot();
contentSlot.name = "Content";

const footerSlot = card.createSlot();
footerSlot.name = "Footer";

// Component now has two SLOT properties automatically
return Object.keys(card.componentPropertyDefinitions);
// → ["Content#7:1", "Footer#7:2"]
```

### Option 3 — Manual binding via addComponentProperty

Link a regular frame to a `SLOT` property with `componentPropertyReferences`:

```javascript
const slotPropKey = component.addComponentProperty("Content", "SLOT", "");
const slotFrame = figma.createFrame();
component.appendChild(slotFrame);
// slotFrame must not have GRID layoutMode, and must be a direct child (not nested inside another slot)
slotFrame.componentPropertyReferences = { slotContentId: slotPropKey };
```

### Populating slots in instances

Find the slot by its property reference after materializing the instance. A `SLOT`-only type lookup would miss a frame bound by `.slotProp()`.

```javascript
const instance = $fig.instance(card);
await $fig.done();
const instanceSlot = instance.query("SLOT[name=Content]").first();
if (!instanceSlot.node) throw new Error('Content slot not found');
instanceSlot.append($fig.autoLayout({ name: 'Button', cornerRadius: 8 }));
await $fig.done();
```

### Slot restrictions

- `GRID` layoutMode is not allowed on slot nodes
- Widgets, Stickies, and ComponentNodes cannot be appended directly to a slot
- Frames nested inside another slot cannot themselves be bound to a slot property
- `instance.setProperties({ [slotPropKey]: ... })` throws — slot content is set by appending children, not via `setProperties`
- For a raw `SlotNode` in an instance, `slotNode.resetSlot()` reverts the slot to its default empty state. Do not assume a frame bound by `.slotProp()` exposes this method.

## INSTANCE_SWAP: Avoiding Variant Explosion

When a component has many possible sub-elements (e.g., 30 different icons), **never** create a variant per sub-element. Use a single INSTANCE_SWAP property instead — the user picks from any compatible component at design time.

```javascript
// Create icon as its own ComponentNode
const iconPlan = $fig.component(
  { name: "Icon/Search", width: 24, height: 24 },
  [$fig.svg('<svg>...</svg>')]
);
await $fig.done();
const iconComp = iconPlan.node;

// Use it as the default for INSTANCE_SWAP
const iconSlotKey = comp.addComponentProperty('Icon', 'INSTANCE_SWAP', iconComp.id);
const instancePlan = $fig.instance(iconComp.id);
await $fig.done();
const instance = instancePlan.node; // raw node for componentPropertyReferences
comp.appendChild(instance);
instance.componentPropertyReferences = { mainComponent: iconSlotKey };
```

This works for icons, avatars, badges, or any swappable nested element.

## Discovering Existing Conventions in the File

**Always inspect the file before creating components.** Different files have different naming styles, structures, and conventions. Your code should match what's already there.

### List all existing components across all pages

`search_design_system` (MCP tool) is an option for published components. For on-canvas components, **don't loop pages inside one script** — even for read-only discovery.

**Prefer the two-step fan-out:**

```javascript
// Step 1 — one cheap use_figma call, no page switch. Returns the page IDs to fan out over.
return figma.root.children.map(p => ({ id: p.id, name: p.name }));
```

Then issue one `use_figma` call per page in parallel. Each script runs:

```javascript
// Step 2 — one call per page, currentPage set exactly once.
// Issue these calls in parallel; do not loop pages inside the script.
const page = await figma.getNodeByIdAsync(PAGE_ID); // PAGE_ID supplied by caller
await figma.setCurrentPageAsync(page);
// Indexed type lookup — much faster than findAll with a side-effect predicate.
const matches = page.findAllWithCriteria({ types: ['COMPONENT', 'COMPONENT_SET'] });
return matches.map(n => ({ pageName: page.name, name: n.name, type: n.type, id: n.id }));
```

See [gotchas.md → Set current page once per `use_figma` call](gotchas.md#set-current-page-once-per-use_figma-call--split-multi-page-work-into-parallel-calls) for the full rule.

### Inspect an existing component set's variant naming pattern

```javascript
const cs = await figma.getNodeByIdAsync('COMPONENT_SET_ID');
if (!cs || cs.type !== 'COMPONENT_SET') {
  throw new Error('Expected a component set');
}
const variantNames = cs.children.map(c => c.name);
const propDefs = cs.componentPropertyDefinitions;
return { variantNames, propDefs };
```

### Find existing components in the file

`search_design_system` is an option for published components. For on-canvas components, use the two-step fan-out from the section above — **don't loop pages inside one script.**

**Step 1** — one cheap `use_figma` call returns page IDs:

```javascript
return figma.root.children.map(p => ({ id: p.id, name: p.name }));
```

**Step 2** — issue one `use_figma` call per page in parallel. Each script:

```javascript
const page = await figma.getNodeByIdAsync(PAGE_ID);
await figma.setCurrentPageAsync(page);
// Indexed type lookup — much faster than findAll with a side-effect predicate.
const components = page.findAllWithCriteria({ types: ['COMPONENT'] });
return components.map(n => ({ name: n.name, id: n.id, page: page.name, w: n.width, h: n.height }));
```

## Using Components by Key (Team Libraries)

`search_design_system` returns `componentKey` for `assetType: "component"` and `componentSetKey` for `assetType: "component_set"`. Pass it directly into `$fig.get(...)` / `$fig.instance(...)` — the plan queues the library import automatically, so no separate `importComponentByKeyAsync` call is needed.

```javascript
// Instance a library component by its componentKey
$fig.instance(BUTTON_COMPONENT_KEY, { name: 'Submit' });

// Instance a specific variant of a component set by passing the set's
// componentSetKey + variant props
$fig.instance(BUTTON_SET_KEY, { props: { Size: 'md', Variant: 'primary' } });
```

You do not need to import the component set, drill into `compSet.children`, or call `defaultVariant.createInstance()` yourself. `$fig.instance(setKey, { props })` picks the matching variant by `setProperties` after the instance is created from the default variant — the same path used for variant switches on an existing instance via `$fig.set(inst, { props })` or `inst.setInstanceProps({...})`.

## Working with Instances

### Selecting a variant in a component set

Pass the variant property values in `props` — `$fig.instance` resolves them on the underlying `setProperties` call:

```javascript
$fig.instance(BUTTON_SET_KEY, {
  props: { variant: 'primary', size: 'md' },
});
```

### Switching the variant of an existing instance

Use `$fig.set` / `$fig.query(...).set({ props })` or `planNode.setInstanceProps({...})`. Both go through the same plan-managed `setProperties` path:

```javascript
const instance = $fig.get('1:42')                // an existing INSTANCE
instance.setInstanceProps({ variant: 'primary', size: 'medium' })

// Bulk: every matching instance on the page
$fig.query('INSTANCE[name=Button]').set({ props: { variant: 'primary' } })
```

### Overriding text in a component instance

**Always discover component properties BEFORE writing text overrides.** Components expose text as `TEXT`-type component properties, and `setProperties()` is the correct way to override them. Direct `node.characters` changes on property-managed text may be overridden by the component property system on render.

**Step 1: Inspect componentProperties on a sample instance:**

```javascript
const instancePlan = $fig.instance(comp.id); // comp is a raw ComponentNode in this example
await $fig.done();
const instance = instancePlan.node; // raw InstanceNode for property inspection
const propDefs = instance.componentProperties;
// Returns e.g.: { "Label#2:0": { type: "TEXT", value: "Button" }, "Has Icon#4:64": { type: "BOOLEAN", value: true } }
return propDefs;
```

Also check nested instances — a parent component may not expose text properties directly, but its nested child instances might:

```javascript
const nestedInstances = instance.findAllWithCriteria({ types: ["INSTANCE"] });
const nestedProps = nestedInstances.map(ni => ({
  name: ni.name,
  id: ni.id,
  properties: ni.componentProperties
}));
```

**Step 2: Use setProperties() for TEXT-type properties:**

```javascript
const instancePlan = $fig.instance(comp.id); // comp is a raw ComponentNode in this example
await $fig.done();
const instance = instancePlan.node; // raw InstanceNode for property inspection
const propDefs = instance.componentProperties;
for (const [key, def] of Object.entries(propDefs)) {
  if (def.type === "TEXT") {
    instance.setProperties({ [key]: "New text value" });
  }
}
```

For nested instances that expose their own TEXT properties, call `setProperties()` on the nested instance:

```javascript
// Use the type-indexed criteria for the type filter, then narrow by name.
const nestedHeading = instance
  .findAllWithCriteria({ types: ["INSTANCE"] })
  .find(n => n.name === "Text Heading");
if (nestedHeading) {
  nestedHeading.setProperties({ "Text#2104:5": "Actual heading text" });
}
```

**Step 3: Only fall back to direct node.characters for unmanaged text.** If text is NOT controlled by any component property, find text nodes directly. **Always load the node's actual font first** — instance text nodes inherit fonts from the source component, so don't assume Inter Regular:

```javascript
const textNodes = instance.findAllWithCriteria({ types: ["TEXT"] });
// Dedupe fonts and load them in parallel before mutating text. Awaiting
// loadFontAsync per node in the loop serializes one IPC round-trip per
// text node and reloads the same font repeatedly.
const uniqueFonts = [...new Map(
  textNodes.map(t => [JSON.stringify(t.fontName), t.fontName])
).values()];
await Promise.all(uniqueFonts.map(f => figma.loadFontAsync(f)));
for (const t of textNodes) {
  t.characters = "Updated text";
}
```

### detachInstance() invalidates ancestor node IDs

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

## Inspecting Component Metadata (Deep Traversal)

For a library component, use `$fig.get(componentKey)` to wrap it, then read `.node` after `await $fig.done()`.

These helpers extract the full property schema and descendant structure of a component. Useful for understanding complex components before creating instances or setting properties.
<a id="component-property-owner-narrowing"></a>**Component-property owner narrowing:** `componentPropertyDefinitions` throws when read from a variant `COMPONENT`, including through optional chaining. Always resolve the property-owning node before touching the getter: a `COMPONENT_SET` owns its definitions, a variant component delegates to its parent set, and a non-variant component owns its own definitions.
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
  const owner = node.type === "COMPONENT" && node.parent.type === "COMPONENT_SET"
    ? node.parent
    : node;
  const definitions = owner.componentPropertyDefinitions;
  const result = {};
  for (const key in definitions) {
    const prop = {
      name: key.replace(/#[^#]+$/, ""),
      type: definitions[key].type,
      key: key
    };
    if (prop.type === "VARIANT") {
      prop.variantOptions = definitions[key].variantOptions;
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

### Full metadata extraction script

```javascript
// For local components, use getLocalComponentMetadata:
const result = await getLocalComponentMetadata('COMPONENT_OR_SET_ID');
return result;

// For published components, use getPublishedComponentMetadata:
// const result = await getPublishedComponentMetadata('COMPONENT_KEY');
// return result;
```
