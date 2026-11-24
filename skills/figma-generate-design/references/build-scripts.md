# Build, Icon, and Update Scripts for `figma-generate-design`

## Step 3: Create Wrapper Frame

```js
// Find clear space
let maxX = 0;
for (const child of figma.currentPage.children) {
  maxX = Math.max(maxX, child.x + child.width);
}

const wrapper = figma.createAutoLayout("VERTICAL");

// --- Size the wrapper based on container type ---
// Full page:       wrapper.resize(1440, 100); wrapper.name = "Homepage";
// Modal/dialog:    wrapper.resize(640, 100);  wrapper.name = "Settings Modal";
// Drawer/sidebar:  wrapper.resize(360, 100);  wrapper.name = "Navigation Drawer";
// Panel:           wrapper.resize(400, 100);  wrapper.name = "Details Panel";
// Adapt width to match the source code's actual dimensions.

wrapper.name = "VIEW_NAME";
wrapper.primaryAxisAlignItems = "CENTER";
wrapper.counterAxisAlignItems = "CENTER";
wrapper.resize(WIDTH, 100);
wrapper.layoutSizingHorizontal = "FIXED";
wrapper.x = maxX + 200;
wrapper.y = 0;

return { success: true, wrapperId: wrapper.id };
```

## Step 4: Section Build Template

```js
const createdNodeIds = [];

// Resolve the wrapper and import every design system dependency in parallel.
// Sequential awaits here serialize N independent IPC round-trips at the top
// of every section build; one Promise.all is dramatically faster.
const [wrapper, buttonSet, bgColorVar, spacingVar, shadowStyle] = await Promise.all([
  figma.getNodeByIdAsync("WRAPPER_ID_FROM_STEP_3"),
  figma.importComponentSetByKeyAsync("BUTTON_SET_KEY"),
  figma.variables.importVariableByKeyAsync("BG_COLOR_VAR_KEY"),
  figma.variables.importVariableByKeyAsync("SPACING_VAR_KEY"),
  figma.importStyleByKeyAsync("SHADOW_STYLE_KEY"),
]);
const primaryButton = buttonSet.children.find(c =>
  c.type === "COMPONENT" && c.name.includes("variant=primary")
) || buttonSet.defaultVariant;

// Build section frame with variable bindings (not hardcoded values)
const section = figma.createAutoLayout();
section.name = "Header";
section.setBoundVariable("paddingLeft", spacingVar);
section.setBoundVariable("paddingRight", spacingVar);
const bgPaint = figma.variables.setBoundVariableForPaint(
  { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', bgColorVar
);
section.fills = [bgPaint];

// Apply the effect style imported above
section.effectStyleId = shadowStyle.id;

// Create component instances inside the section
const btnInstance = primaryButton.createInstance();
section.appendChild(btnInstance);
createdNodeIds.push(btnInstance.id);

// Append section to wrapper
wrapper.appendChild(section);
section.layoutSizingHorizontal = "FILL"; // AFTER appending

createdNodeIds.push(section.id);
return { success: true, createdNodeIds };
```

### Nested Instance Text Override

```js
// Use the type-indexed criteria for the type filter, then narrow by name.
const nestedHeading = cardInstance
  .findAllWithCriteria({ types: ["INSTANCE"] })
  .find(n => n.name === "Text Heading");
if (nestedHeading) {
  nestedHeading.setProperties({ "Text#2104:5": "Actual heading from source code" });
}
```

## Icons: Import SVG Directly

1. **Get the SVG from the codebase.** Read the icon's source — inline `<svg>`, the imported `.svg` asset, or the icon-library entry — and pass that exact SVG string. Prefer the codebase's own SVG over hand-authoring one.
2. **Import with `figma.createNodeFromSvg(svgString)`**, which returns a `FrameNode` of editable vector paths. The SVG string **must** include a `viewBox` plus explicit `width`/`height` (e.g. `<svg width="24" height="24" viewBox="0 0 24 24" ...>`). Without `width`/`height` it falls back to the `viewBox` size, which is often smaller than the slot — the usual cause of "the icon didn't size properly."
3. **Size it to the slot.** `createNodeFromSvg` frames scale their contents on resize, so `icon.resize(size, size)` fits the whole icon (stroke weight included) to the target box. Equivalently author `width`/`height` equal to the target. Match the source's icon size — commonly 16/20/24px.
4. **Never reconstruct an icon from rotated line/rect/ellipse primitives.** Figma's line rotation is unreliable in the `use_figma` context and produces broken, mis-rotated icons (a chevron collapses into a blob, an arrowhead detaches from its shaft). Importing the SVG is both more reliable and more editable.

```js
// Place / replace an icon from a codebase SVG into a 24px slot
const icon = figma.createNodeFromSvg(
  '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
  '<path d="m9 18 6-6-6-6" stroke="#1A1A1A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
);
icon.name = "icon/chevron-right";
icon.resize(24, 24);          // scales the whole icon to the slot
slotFrame.appendChild(icon);
```

**Codebase SVGs usually use `currentColor`** (e.g. `stroke="currentColor"` / `fill="currentColor"`), which `createNodeFromSvg` imports as **black** — it does not inherit the parent's color. Set the intended color after import: substitute the literal color into the SVG string before importing, or bind the imported vector fills/strokes to a design-system color variable with `setBoundVariableForPaint` (same as any paint). To turn an imported SVG into a reusable icon component (for INSTANCE_SWAP), see [figma-generate-library → Creating Icon Components](../../figma-generate-library/references/component-creation.md) and the [INSTANCE_SWAP pattern](../../figma-use/references/component-patterns.md#instance_swap-avoiding-variant-explosion).

## Step 6: Update Existing View Script

```js
// Example: Swap a button variant in an existing screen.
// Batch the node lookup and component-set import in parallel — they are
// independent and awaiting them sequentially serializes two IPC round-trips.
const [existingButton, buttonSet] = await Promise.all([
  figma.getNodeByIdAsync("EXISTING_BUTTON_INSTANCE_ID"),
  figma.importComponentSetByKeyAsync("BUTTON_SET_KEY"),
]);
if (existingButton && existingButton.type === "INSTANCE") {
  const newVariant = buttonSet.children.find(c =>
    c.name.includes("variant=primary") && c.name.includes("size=lg")
  ) || buttonSet.defaultVariant;
  existingButton.swapComponent(newVariant);
}
return { success: true, mutatedNodeIds: [existingButton.id] };
```
