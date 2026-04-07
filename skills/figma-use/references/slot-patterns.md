# Slot API Patterns

> Part of the [use_figma skill](../SKILL.md). How to correctly use the Plugin API for slots — flexible content areas within components.
>
> **Slots are currently in open beta.** The API may change in future releases.
>
> For component property basics (TEXT, BOOLEAN, INSTANCE_SWAP, VARIANT), see [component-patterns.md](component-patterns.md).

## Contents

- When to Use Slots vs INSTANCE_SWAP
- Creating a Slot
- Setting preferredValues on a Slot Property
- Working with Slots in Instances
- Slot-Based Component Design Examples
- Gotchas

## When to Use Slots vs INSTANCE_SWAP

| | INSTANCE_SWAP | Slot |
|---|---|---|
| **Content model** | User picks one component from a set | User places arbitrary nodes freely |
| **Use case** | Icons, avatars, badges, status indicators | Card bodies, table cells, dashboard widget areas |
| **Flexibility** | Constrained to swappable components | Fully freeform — text, images, components, any combination |
| **Property type** | `'INSTANCE_SWAP'` | `'SLOT'` |

**Rule of thumb:** If the content area should accept a single, interchangeable component, use INSTANCE_SWAP. If the user needs to compose multiple elements or arrange content freely, use a Slot.

## Creating a Slot

`createSlot()` is only available on `ComponentNode`. It creates a `SlotNode` (type `'SLOT'`) that behaves like a Frame — it supports auto-layout, fills, strokes, and children.

```javascript
const comp = figma.createComponent();
comp.name = "Card";
comp.layoutMode = "VERTICAL";
comp.paddingLeft = 16;
comp.paddingRight = 16;
comp.paddingTop = 16;
comp.paddingBottom = 16;
comp.itemSpacing = 12;
comp.layoutSizingHorizontal = "HUG";
comp.layoutSizingVertical = "HUG";

// Create the slot
const slot = comp.createSlot();
slot.name = "Content";

// Configure layout (same properties as Frame)
slot.layoutMode = "VERTICAL";
slot.itemSpacing = 16;
slot.fills = [];
slot.layoutSizingHorizontal = "FILL";
slot.layoutSizingVertical = "HUG";

// Add default content
await figma.loadFontAsync({ family: "Inter", style: "Regular" });
const text = figma.createText();
text.characters = "Default content";
slot.appendChild(text);
```

After calling `createSlot()`, a `'SLOT'` entry is automatically added to `componentPropertyDefinitions`:

```javascript
const propDefs = comp.componentPropertyDefinitions;
// e.g. { "Content#1:0": { type: "SLOT" } }
```

## Setting preferredValues on a Slot Property

You can suggest which components users should place in a slot by setting `preferredValues` on the slot property:

```javascript
const comp = figma.createComponent();
const slot = comp.createSlot();
slot.name = "Status";

// Find the slot property key
const propKey = Object.keys(comp.componentPropertyDefinitions)
  .find(k => comp.componentPropertyDefinitions[k].type === "SLOT");

// Set preferred components
comp.editComponentProperty(propKey, {
  preferredValues: [
    { type: "COMPONENT", key: badgeComp.key },
    { type: "COMPONENT_SET", key: badgeSet.key },
  ]
});
```

This does not restrict what users can place in the slot — it only suggests preferred options in the Figma UI.

## Working with Slots in Instances

### Finding slots in an instance

```javascript
const inst = comp.createInstance();
const slot = inst.findChild(n => n.type === "SLOT");
```

### Adding content to a slot

```javascript
const inst = comp.createInstance();
const slot = inst.findChild(n => n.type === "SLOT");

// Append new content (added alongside default content)
await figma.loadFontAsync({ family: "Inter", style: "Regular" });
const newText = figma.createText();
newText.characters = "Added content";
slot.appendChild(newText);
```

### Resetting slot content to default

```javascript
const slot = inst.findChild(n => n.type === "SLOT");
slot.resetSlot(); // Reverts to the component's default slot content
```

### Adding content after resetting

`resetSlot()` removes user-added content and restores the component's defaults. To reset and then add new content alongside the defaults:

```javascript
const slot = inst.findChild(n => n.type === "SLOT");
slot.resetSlot();
// slot reference itself is still valid; child references captured before reset are not
// Default content is restored — new content is added alongside it
await figma.loadFontAsync({ family: "Inter", style: "Regular" });
const additional = figma.createText();
additional.characters = "Additional content";
slot.appendChild(additional);
// Slot now contains: default content + "Additional content"
```

Note: there is no built-in way to remove the component's default slot content from an instance. `resetSlot()` restores defaults; `appendChild()` adds to them.

## Slot-Based Component Design Examples

### StatCard: label as TEXT property, value area as Slot

```javascript
const statCard = figma.createComponent();
statCard.name = "StatCard";
statCard.layoutMode = "VERTICAL";
statCard.paddingLeft = 16;
statCard.paddingRight = 16;
statCard.paddingTop = 16;
statCard.paddingBottom = 16;
statCard.itemSpacing = 8;
statCard.layoutSizingHorizontal = "HUG";
statCard.layoutSizingVertical = "HUG";

// Label — controlled via TEXT property
await figma.loadFontAsync({ family: "Inter", style: "Regular" });
const label = figma.createText();
label.characters = "Label";
statCard.appendChild(label);
const labelProp = statCard.addComponentProperty("label", "TEXT", "Label");
label.componentPropertyReferences = { characters: labelProp };

// Value area — Slot for freeform content
const valueSlot = statCard.createSlot();
valueSlot.name = "Value";
valueSlot.layoutMode = "HORIZONTAL";
valueSlot.itemSpacing = 8;
valueSlot.fills = [];
valueSlot.layoutSizingHorizontal = "FILL";
valueSlot.layoutSizingVertical = "HUG";
```

### TableRow: text columns as TEXT properties, status column as Slot

```javascript
const tableRow = figma.createComponent();
tableRow.name = "TableRow";
tableRow.layoutMode = "HORIZONTAL";
tableRow.itemSpacing = 16;
tableRow.layoutSizingHorizontal = "FILL";
tableRow.layoutSizingVertical = "HUG";

await figma.loadFontAsync({ family: "Inter", style: "Regular" });

// Text column — TEXT property
const orderId = figma.createText();
orderId.characters = "#ORD-0000";
tableRow.appendChild(orderId);
const orderIdProp = tableRow.addComponentProperty("orderId", "TEXT", "#ORD-0000");
orderId.componentPropertyReferences = { characters: orderIdProp };

// Status column — Slot (users can drop in Badge, Tag, or any component)
const statusSlot = tableRow.createSlot();
statusSlot.name = "Status";
statusSlot.layoutMode = "HORIZONTAL";
statusSlot.fills = [];
statusSlot.layoutSizingHorizontal = "HUG";
statusSlot.layoutSizingVertical = "HUG";
```

## Gotchas

### `createSlot()` only works on ComponentNode

```javascript
// WRONG — calling createSlot on an instance or frame throws
const inst = comp.createInstance();
inst.createSlot(); // Error!

const frame = figma.createFrame();
frame.createSlot(); // Error!

// CORRECT — call on a ComponentNode
const comp = figma.createComponent();
const slot = comp.createSlot();
```

### Re-find children after `resetSlot()` — old references become invalid

`resetSlot()` replaces the slot's children internally. Any references to child nodes captured **before** the reset become invalid and will throw `"Node not found"` errors.

```javascript
const slot = inst.findChild(n => n.type === "SLOT");
const oldChild = slot.children[0]; // reference captured before reset

slot.resetSlot();

// WRONG — oldChild reference is now invalid
oldChild.characters = "new text"; // Error: Node not found

// CORRECT — re-find children after reset
const newChildren = slot.children; // fresh references
```

### `resetSlot()` removes user-added content, keeps component defaults

`resetSlot()` reverts the slot to the component's default content. It removes any content added by the instance user, but does **not** empty the slot — the default content defined in the component remains.

```javascript
const slot = inst.findChild(n => n.type === "SLOT");

// Slot has 1 default child + 1 user-added child = 2
slot.resetSlot();
// Slot now has 1 default child

// To add replacement content after reset:
slot.appendChild(newContent); // default + newContent
```

### Slots are open beta

The Slot API is in open beta as of 2025. The API surface may change in future Figma releases. Monitor the [official documentation](https://developers.figma.com/docs/plugins/api/SlotNode) for updates.
