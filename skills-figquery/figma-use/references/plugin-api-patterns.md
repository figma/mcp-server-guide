# Plugin API Patterns

> Part of the [use_figma skill](../SKILL.md). Quick reference for common Figma Plugin API operations.

## Contents

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


## Execution Basics

### Page Context

Page context resets between `use_figma` calls — `figma.currentPage` always starts on the first page. Use `await figma.setCurrentPageAsync(page)` at the start of each invocation to switch to the correct page. The sync setter `figma.currentPage = page` does **NOT work** and will throw — always use the async method.

```javascript
const targetPage = figma.root.children.find(p => p.name === "My Page");
await figma.setCurrentPageAsync(targetPage);
// targetPage.children is now populated
```

### Returning Results

Scripts are automatically wrapped in an async IIFE with error handling. Just write plain JS and use `return` to send data back to the agent:

```javascript
// Return an object — auto-serialized to JSON
return { nodeId: frame.id, count: 5 }

// Return a string
return "Created 3 components"
```

Errors are automatically captured — no try/catch needed. `figma.notify()` does **not** exist. Return all information via the `return` value.

### Working Incrementally

Don't build an entire screen in one call. Break work into small steps:
1. Create tokens/variables
2. Create text styles
3. Build individual components
4. Compose sections
5. Assemble screens

Verify structure with `get_metadata` between steps. Use `get_screenshot` after each major creation milestone to catch visual problems early.

## Creating Nodes

### Frames

```javascript
$fig.frame({
  name: "Container",
  width: 1440,
  height: 900,
  fills: [{ type: "SOLID", color: { r: 0.98, g: 0.98, b: 0.99 } }],
})
```

### Text

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

### Rectangles

```javascript
$fig.rectangle({
  name: "Background",
  width: 400,
  height: 300,
  cornerRadius: 12,
  fills: [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.96 } }],
})
```

### Ellipses

```javascript
$fig.ellipse({
  name: "Avatar Circle",
  width: 48,
  height: 48,
  fills: [{ type: 'SOLID', color: { r: 0.85, g: 0.87, b: 0.90 } }],
})
```

### Lines

```javascript
$fig.line({
  name: "Divider",
  width: 400,
  height: 0,
  strokes: [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 }, opacity: 0.08 }],
  strokeWeight: 1,
})
```

### SVG Import

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

## Fills & Strokes

### Solid Fill

```javascript
node.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.25 } }];
```

### Fill with Opacity

```javascript
node.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.25 }, opacity: 0.5 }];
```

### No Fill (Transparent)

```javascript
node.fills = [];
```

### Linear Gradient

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

### Strokes

```javascript
node.strokes = [{ type: "SOLID", color: { r: 0.85, g: 0.85, b: 0.87 } }];
node.strokeWeight = 1;
node.strokeAlign = "INSIDE";  // "CENTER", "OUTSIDE"
```

### Multiple Fills (Layered)

```javascript
node.fills = [
  { type: "SOLID", color: { r: 0.95, g: 0.95, b: 0.96 } },
  { type: "SOLID", color: { r: 0.2, g: 0.36, b: 0.96 }, opacity: 0.05 }
];
```

## Auto Layout

### Setting Up Auto Layout

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

### Alignment

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

### Child Sizing

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
      layoutSizingHorizontal: 'FILL',
      layoutSizingVertical: 'FILL',
    })
  ]
)
```

Use `HUG` only for nodes with intrinsic content, such as text and auto-layout frames. In imperative code, append a child to its auto-layout parent before assigning `FILL` or `HUG`.

### Wrapping (Grid-like Layout)

```javascript
frame.layoutMode = "HORIZONTAL";
frame.layoutWrap = "WRAP";
frame.itemSpacing = 24;          // Horizontal gap
frame.counterAxisSpacing = 24;   // Vertical gap (between rows)
```

### Absolute Positioning Within Auto Layout

```javascript
// ABSOLUTE requires the child to be attached to an auto-layout parent first.
const parent = figma.createAutoLayout("HORIZONTAL");
parent.appendChild(child);
child.layoutPositioning = "ABSOLUTE";
child.constraints = { horizontal: "MAX", vertical: "MIN" };  // Top-right
child.x = parentWidth - childWidth - 8;
child.y = 8;
```

## Effects

### Drop Shadow

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

### Inner Shadow

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

### Background Blur

```javascript
node.effects = [{
  type: "BACKGROUND_BLUR",
  radius: 16,
  visible: true
}];
```

### Layer Blur

```javascript
node.effects = [{
  type: "LAYER_BLUR",
  radius: 8,
  visible: true
}];
```

### Multiple Effects

```javascript
node.effects = [
  { type: "DROP_SHADOW", color: { r: 0, g: 0, b: 0, a: 0.04 }, offset: { x: 0, y: 1 }, radius: 3, spread: 0, visible: true, blendMode: "NORMAL" },
  { type: "DROP_SHADOW", color: { r: 0, g: 0, b: 0, a: 0.06 }, offset: { x: 0, y: 8 }, radius: 24, spread: -4, visible: true, blendMode: "NORMAL" }
];
```

## Opacity & Blend Modes

```javascript
node.opacity = 0.5;
node.blendMode = "NORMAL";    // "MULTIPLY", "SCREEN", "OVERLAY", "DARKEN", "LIGHTEN", etc.
```

## Corner Radius

```javascript
// Uniform
node.cornerRadius = 12;

// Per-corner
node.topLeftRadius = 12;
node.topRightRadius = 12;
node.bottomLeftRadius = 0;
node.bottomRightRadius = 0;
```

## Clipping

```javascript
frame.clipsContent = true;   // Children clipped to frame bounds
```

## Grouping & Organization

### Groups

```javascript
$fig.group({ name: 'Grouped Elements' }, [node1, node2, node3])
```

### Sections

```javascript
$fig.section({ name: 'My Section', width: 800, height: 600 })
// IMPORTANT: Sections don't auto-resize — always resize after adding content
```

### Appending Children

```javascript
// With $fig
parentFrame.append(child);
parentFrame.addAt(0, child); // Insert at beginning
child.moveTo(parentFrame, 0); // Insert at beginning

// With raw Plugin API
parentFrame.appendChild(childNode);
parentFrame.insertChild(0, childNode);  // Insert at beginning
```

## Components & Variants

### Create Component

```javascript
$fig.component({ name: 'Button/Primary', description: 'Primary action button' })
```

### Create Instance

```javascript
$fig.instance(component, { x: 200, y: 100 })
```

### Use Components by Key (Team Libraries)

Pass the `componentKey` straight into `$fig.get(...)` / `$fig.instance(...)`. The plan queues the library import automatically — there is no need to call `importComponentByKeyAsync` / `importComponentSetByKeyAsync` yourself, or to pick a variant child of a component set by hand.

```javascript
// Component
$fig.instance(componentKey, { x: 200, y: 100 })

// Component set: pass variant props; $fig.instance picks the matching variant
$fig.instance(componentSetKey, { x: 200, y: 100, props: { Size: 'md', Variant: 'primary' } })
```

For components in the current file, `$fig.get(nodeId)` accepts a real id too — same call site for both.

### Combine as Variants

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

### Component Properties

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

## Styles

Prefer `$fig` for style creation + binding — fonts preload automatically, and you can bind the style on the node by name (`fills`, `effects`, `textStyle`, etc.) in the same plan. See [fig-builder.md](fig-builder.md) for the full surface.

### Text Style

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

### Effect Style

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

### Paint and Grid Styles

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

### Referencing an existing style

```javascript
const existing = $fig.getStyle("Brand/Primary");   // by name or real id; null if miss
$fig.query("FRAME[name^=Card]").set({ fills: existing });
```

## Cloning & Duplication

```javascript
const clone = originalNode.clone();
clone.x = originalNode.x + originalNode.width + 40;
clone.name = "Copy of " + originalNode.name;
```

## Finding Nodes

```javascript
// Find by name on current page
const node = figma.currentPage.findOne(n => n.name === "My Frame");

// Find all by type
const allTexts = figma.currentPage.findAll(n => n.type === "TEXT");

// Find all by name pattern
const allButtons = figma.currentPage.findAll(n => n.name.startsWith("Button/"));
```

## Layout Grids

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

## Constraints (Non-Auto-Layout Frames)

```javascript
child.constraints = {
  horizontal: "LEFT_RIGHT",  // LEFT, RIGHT, CENTER, LEFT_RIGHT, SCALE
  vertical: "TOP"            // TOP, BOTTOM, CENTER, TOP_BOTTOM, SCALE
};
```

## Viewport & Zoom

```javascript
// Zoom to fit specific nodes
figma.viewport.scrollAndZoomIntoView([frame1, frame2]);
```
