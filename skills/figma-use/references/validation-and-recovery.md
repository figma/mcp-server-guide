# Validation Workflow & Error Recovery

> Part of the [use_figma skill](../SKILL.md). How to debug, validate, and recover from errors.

## Contents

- `get_metadata` vs `get_screenshot`
- Error Recovery After Failed `use_figma`
- Recommended Workflow


## `get_metadata` vs `get_screenshot`

After each `use_figma` call, validate results using the right tool for the job. Do NOT reach for `get_screenshot` every time — it is expensive and should be reserved for visual checks.

### `get_metadata` — Use for intermediate validation (preferred)

`get_metadata` returns an XML tree of node IDs, types, names, positions, and sizes. Use it to confirm:

- **Structure & hierarchy**: correct parent-child relationships, component nesting, section contents
- **Node counts**: expected number of variants created, children present
- **Naming**: variant property names follow the `property=value` convention
- **Positioning & alignment**: x/y coordinates, width/height values match expectations
- **Layout properties**: auto-layout direction, sizing mode, padding, spacing
- **Component set membership**: all expected variants are inside the ComponentSet

```
Example: After creating a ComponentSet with 120 variants, call get_metadata on the
ComponentSet node to verify all 120 children exist with correct names, sizes, and positions
— without waiting for a full render.
```

**When to use `get_metadata`:**
- After creating/modifying nodes — to verify structure, counts, and names
- After layout operations — to verify positions and dimensions
- After combining variants — to confirm all components are in the ComponentSet
- After binding variables — to verify node properties (use use_figma to read bound variables if needed)
- Between multi-step workflows — to confirm step N succeeded before starting step N+1

### `get_screenshot` — Use after each major creation milestone

`get_screenshot` renders a pixel-accurate image. It is the only way to verify visual correctness (colors, typography rendering, effects, variable mode resolution). It is slower and produces large responses, so don't call it after every single `use_figma` — but do call it after each major milestone to catch visual problems early.

**When to use `get_screenshot`:**
- **After creating a component set** — verify variants look correct, grid is readable, nothing is collapsed or overlapping
- **After composing a layout** — verify overall structure and spacing
- **After binding variables/modes** — verify colors and tokens resolved correctly
- **After any fix or recovery** — verify the fix didn't introduce new visual issues
- **Before reporting results to the user** — final visual proof

**What to look for in screenshots** — these are the most commonly missed issues:
- **Cropped/clipped text** — line heights or frame sizing cutting off descenders, ascenders, or entire lines
- **Overlapping content** — elements stacking on top of each other due to incorrect sizing or missing auto-layout
- **Placeholder text** still showing ("Title", "Heading", "Button") instead of actual content

## Error Recovery After Failed `use_figma`

**Recovery steps when `use_figma` returns an error:**
- If `safeToRetryWithoutCanvasRead` is `true`, fix the error and retry.
- If `false`, read the canvas, determine what changed, then make changes.

## Recommended Workflow

```
1. use_figma  →  Create/modify nodes
2. get_metadata     →  Verify structure, counts, names, positions (fast, cheap)
3. use_figma  →  Fix any structural issues found
4. get_metadata     →  Re-verify fixes
5. ... repeat as needed ...
6. get_screenshot   →  Visual check after each major milestone

⚠️ ON ERROR at any step:
   a. safeToRetryWithoutCanvasRead=true  →  Fix the error and retry
   b. safeToRetryWithoutCanvasRead=false →  Read the canvas, determine changes, then change
```
