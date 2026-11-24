# Design System Discovery Scripts & Query Reference

## 2a-i: Resolve Code Connect Component Keys

Example: Code Connect file contains `// url=https://figma.com/design/ABC123/File?node-id=609-35535`. Parse `fileKey` = `ABC123`, `nodeId` = `609:35535`. Run `use_figma` against the **library file** (`fileKey` `ABC123`, not the target file) to resolve the key:

```js
const node = await figma.getNodeByIdAsync("609:35535");
const set = node?.parent?.type === "COMPONENT_SET" ? node.parent : node;
if (set?.type === "COMPONENT_SET") {
  return { assetType: "component_set", componentSetKey: set.key };
}
if (set?.type === "COMPONENT") {
  return { assetType: "component", componentKey: set.key };
}
throw new Error("Expected a component or component set");
```

Batch multiple lookups in a single call. Use the returned keys with either `importComponentByKeyAsync()` or `importComponentSetByKeyAsync()` depending on each item's `assetType` in Step 4.

## 2a-iii: Single-Pass Existing Screen Inventory

Run one read-only `use_figma` call to inventory an existing frame — its component keys, bound variables, and text/effect styles — and reuse the result in 2b and 2c:

```js
const frame = figma.currentPage.findOne(n => n.name === "Existing Screen");
const components = new Map();
const styles = { text: new Map(), effect: new Map() };
const variableIds = new Set();

// boundVariables and style ids can sit on any scene node, so walk them all.
for (const node of frame?.findAll(() => true) ?? []) {
  if (node.type === "INSTANCE") {
    const mc = node.mainComponent;
    const cs = mc?.parent?.type === "COMPONENT_SET" ? mc.parent : null;
    const key = cs ? cs.key : mc?.key;
    if (key && !components.has(key)) {
      components.set(key, { name: cs ? cs.name : mc.name, key, isSet: !!cs, sampleVariant: mc.name });
    }
  }
  for (const b of Object.values(node.boundVariables ?? {}).flat()) {
    if (b?.id) variableIds.add(b.id);
  }
  for (const [prop, bucket] of [["textStyleId", "text"], ["effectStyleId", "effect"]]) {
    if (prop in node && typeof node[prop] === "string" && node[prop]) {
      const s = await figma.getStyleByIdAsync(node[prop]);
      if (s) styles[bucket].set(s.id, { name: s.name, id: s.id, key: s.key });
    }
  }
}
const vars = await Promise.all([...variableIds].map(id => figma.variables.getVariableByIdAsync(id)));

return {
  components: [...components.values()],
  variables: vars.filter(Boolean).map(v => ({ name: v.name, id: v.id, key: v.key, type: v.resolvedType, remote: v.remote })),
  textStyles: [...styles.text.values()],
  effectStyles: [...styles.effect.values()],
};
```

## 2a-iv: `get_libraries` and `search_design_system` Usage

```js
// Step 1: Discover available libraries
get_libraries({ fileKey })
// Returns: {
//   libraries_added_to_file: [...],
//   libraries_available_to_add: [...],
//   libraries_available_to_add_next_offset: number | null
// }

// Step 2: Search within a specific library using its libraryKey
search_design_system({ queries: [{ entity: "component", query: "button" }], fileKey, includeLibraryKeys: ["lk-abc123..."] })
```

Org libraries in `libraries_available_to_add` are paginated (20 per page). When `libraries_available_to_add_next_offset` is non-null, more org libraries are available — call `get_libraries` again with `offset` set to that value to fetch the next page. Community UI kits only appear on the first page. If the user names a specific library you don't see in the current page, page further before giving up.

### Example Component Map with Property Info

Include component properties in your map — create a temporary instance, read its `componentProperties` (and those of nested instances), then remove the temp instance:

```text
Component Map:
- Button → key: "abc123", type: COMPONENT_SET
  Properties: { "Label#2:0": TEXT, "Has Icon#4:64": BOOLEAN }
- PricingCard → key: "ghi789", type: COMPONENT_SET
  Properties: { "Device": VARIANT, "Variant": VARIANT }
  Nested "Text Heading" has: { "Text#2104:5": TEXT }
  Nested "Button" has: { "Label#2:0": TEXT }
```

## 2b: Variable Search Query Strategy

`search_design_system` matches against **variable names** (e.g., `"Gray/gray-9"`, `"core/gray/100"`, `"space/400"`), not categories. Put multiple short, simple searches in one `queries` call rather than one compound query. Every array entry must be an `{ "entity": "variable", "query": "..." }` object, never a bare string:

- **Primitive colors:** `{ "entity": "variable", "query": "gray" }`, `{ "entity": "variable", "query": "red" }`, etc.
- **Semantic colors:** `{ "entity": "variable", "query": "background" }`, `{ "entity": "variable", "query": "surface" }`, etc.
- **Spacing/sizing:** `{ "entity": "variable", "query": "space" }`, `{ "entity": "variable", "query": "radius" }`, etc.

If initial searches return empty, try shorter fragments or different naming conventions — libraries vary widely (`"grey"` vs `"gray"`, `"spacing"` vs `"space"`, `"color/bg"` vs `"background"`).
