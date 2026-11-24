# Deep Inspection Reference

Use this reference only after primary design context and the target screenshot demonstrate a concrete gap.

## Route tools by purpose

| Need | Preferred route | Notes |
|---|---|---|
| base design-to-code workflow | `figma-design-to-code` | Load before primary context; this guard owns recovery and completeness verification only |
| visual appearance | `get_screenshot` | Match the exact target node; inspect a child separately only when needed |
| implementation context | `get_design_context` | Primary design-to-code source; request exact child nodes when output is large |
| hierarchy and node IDs | `get_metadata` | Sparse index only; absence of style data is expected; availability varies by MCP surface |
| variable/style values | `get_variable_defs` | Prefer named variables over sampling rendered pixels |
| omitted deep properties | `use_figma` | Load `figma-use`; execute bounded, read-only code only when the tool is available |
| source/exported assets | `download_assets` | Otherwise request an exact source/export rather than using a screenshot |

## Recover a depth-limited branch

Do not retry the same broad request or assume a fixed maximum depth. Use an evidence-driven queue:

1. Record the smallest known ancestor, the missing visible region, and any child IDs already exposed.
2. Obtain a shallow hierarchy index with `get_metadata` when available.
3. Add unresolved child IDs to a queue and keep a visited set so no node is fetched twice without a stated reason.
4. Request `get_design_context` directly for the smallest unresolved child. Compare the result with the same screenshot region.
5. When child IDs or required properties are still hidden, call `use_figma` on the smallest known ancestor to list immediate descendants or selected fields only.
6. Continue only while each read adds evidence. Stop with a partial or blocked status when the queue cannot progress, access is unavailable, or the inspection budget is exhausted.

Completion is visual and semantic coverage of the requested scope, not reaching an arbitrary tree depth.

## Detect incomplete context

Treat any of these as a reason for targeted follow-up:

- explicit `depth limit`, truncation, ellipsis, or output-size warning
- an `INSTANCE`, `FRAME`, `GROUP`, or asset placeholder with visible content missing from the returned representation
- screenshot text, imagery, edge detail, or overlay absent from the node evidence
- text content without typography, or styling without the variable/value needed to map it
- a flattened image reference where implementation requires editable or semantic substructure
- mutually inconsistent screenshot, metadata, design context, and variable results

Do not interpret sparse metadata as proof that descendants do not exist. Do not interpret a complete-looking instance shell as proof that its visible internals were inspected.

## Keep deep reads bounded and read-only

- Start from the smallest known target node and traverse descendants only within that subtree.
- Return selected scalar fields and compact paint/effect summaries. Avoid returning full plugin objects, binary data, or the entire document.
- Filter by node type, name, bounds, or unresolved node IDs before collecting expensive properties.
- Do not call creation, mutation, deletion, reparenting, detachment, variable-writing, or style-writing APIs during inspection.
- Do not scan every page. Page context can reset between calls; use one explicitly selected page per query when page access is necessary.
- Cache node IDs and summarized findings in the working response. Do not repeat identical reads.

## Inspect properties by risk

Collect only fields relevant to the visible layer or implementation decision:

- identity and order: `id`, `name`, `type`, child order, `visible`, `opacity`, `blendMode`
- geometry: local bounds, `absoluteBoundingBox`, rotation, clipping, constraints, auto-layout sizing and alignment
- paint: fills, strokes, stroke widths, paint opacity, gradient stops and transforms, bound variables
- composition: effects, masks, mask type, clipping, blend mode, parent opacity, layer order
- assets: image hashes, export settings, vector identity, source/export availability
- text: characters, font family/style/weight, size, line height, letter spacing, alignment, wrapping, fills, text style and bound variables
- states: component properties, variant values, visibility overrides, interactive or disabled states relevant to scope

For a simple solid layer, record parent opacity, paint opacity, and their product when useful. Do not reduce gradients, masks, blur, blend modes, or overlapping translucent layers to that product.

## Check layout and content behavior

- Distinguish fixed frame coordinates from intended responsive constraints or auto layout.
- Identify clipping that is intentional at the reference size but unsafe for text scaling or localization.
- Check narrow and wide finite constraints when the component can be embedded rather than full-screen.
- Check representative long, empty, malformed, and localized content when the UI receives dynamic data.
- Inspect relevant component variants instead of inferring pressed, selected, disabled, loading, or error states from one screenshot.

## Resolve disagreements

Use the screenshot as rendered evidence and node properties as structural evidence. Neither source alone overrides the other. When they disagree:

1. verify that both calls targeted the same node, variant, theme, and state
2. inspect variables, parent opacity, masks, effects, and overlapping nodes
3. re-read the smallest disputed child
4. record the unresolved difference instead of averaging or guessing values
