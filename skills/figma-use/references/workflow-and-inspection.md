# Editor Modes, Inspection Scripts, and Incremental Workflow Reference

## Editor Mode Node Availability

- **Design mode (`figma.com/design/...`, editorType `"figma"`):**
  - Available: Rectangle, Frame, Component, Text, Ellipse, Star, Line, Vector, Polygon, BooleanOperation, Slice, Page, Section, TextPath.
  - Blocked: Sticky, Connector, ShapeWithText, CodeBlock, Slide, SlideRow, SlideGrid, InteractiveSlideElement, Webpage.
- **Slides mode (`figma.com/slides/...`, editorType `"slides"`):**
  - Available: Rectangle, Frame, Component, Text, Ellipse, Star, Line, Vector, Polygon, BooleanOperation, Slice, Section, TextPath, Slide, SlideRow, SlideGrid, InteractiveSlideElement.
  - Blocked: Sticky, Connector, ShapeWithText, CodeBlock, Webpage, Page.
- **FigJam (`figma.com/board/...`, editorType `"figjam"`):** Most design nodes are blocked; use `figma-use-figjam`.
- **Design-only APIs:** `figma.createPage()` is available only in Design files (`figma.com/design/...`). In both FigJam and Slides it throws `TypeError: figma.createPage no such property 'createPage' on the figma global object`.

## Suggested Step Order & Validation Matrix

```text
Step 1: Inspect file — discover existing pages, components, variables, conventions
Step 2: Create tokens/variables (if needed)
       → return collection, variable, and mode counts
Step 3: Create individual components
       → return component IDs and relevant child/variant counts
Step 4: Compose layouts from component instances
       → return layout IDs/bounds + take a composition screenshot
Step 5: Apply a targeted visual fix only if needed
       → take one post-fix screenshot; this is final
Step 6: Stop if nothing relevant changed
```

| After... | Check with `get_metadata` | Check with `get_screenshot` |
|---|---|---|
| Creating variables | Collection count, variable count, mode names | — |
| Creating components | Child count, variant names, property definitions | Variants visible, not collapsed, grid readable |
| Binding variables | Node properties reflect bindings | Colors/tokens resolved correctly |
| Composing layouts | Instance nodes have mainComponent, hierarchy correct | No cropped/clipped text, no overlapping elements, correct spacing |

## Common Non-Contract Error Messages

| Error message | Likely cause | How to fix |
|---|---|---|
| Property value out of range | Color channel > 1 (used 0–255 instead of 0–1) | Divide by 255 |
| `"Cannot read properties of null"` | Node doesn't exist (wrong ID, wrong page) | Check page context, verify ID |
| Script hangs / no response | Infinite loop or unresolved promise | Check for `while(true)` or missing `await`; ensure code terminates |
| `"The node with id X does not exist"` | Parent instance was implicitly detached by a child `detachInstance()`, changing IDs | Re-discover nodes by traversal from a stable (non-instance) parent frame |

## Quick Inspection Scripts

### List all pages and top-level nodes
```js
const pages = figma.root.children.map(p => `${p.name} id=${p.id} children=${p.children.length}`);
return pages.join('\n');
```

### List existing components across all pages (Two-Step Parallel Fan-Out)

`search_design_system` is an option for published components. For on-canvas components, use the two-step fan-out — **don't loop pages inside one script.**

Step 1: one read-only `use_figma` to get page IDs:
```js
return figma.root.children.map(p => ({ id: p.id, name: p.name }));
```

Step 2: in the **next assistant turn, emit one `use_figma` per page in parallel** (a single message containing N tool-use blocks). Each runs:
```js
const page = await figma.getNodeByIdAsync(PAGE_ID);
await figma.setCurrentPageAsync(page);
// findAllWithCriteria uses an indexed type lookup — hundreds of times faster
// than the findAll(n => n.type === '…') side-effect-in-predicate antipattern.
const matches = page.findAllWithCriteria({ types: ['COMPONENT', 'COMPONENT_SET'] });
return matches.map(n => ({ page: page.name, name: n.name, type: n.type, id: n.id }));
```

### List existing variable collections and their conventions
```js
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const results = collections.map(c => ({
  name: c.name, id: c.id,
  varCount: c.variableIds.length,
  modes: c.modes.map(m => m.name)
}));
return results;
```

## Pre-Flight Checklist

Before submitting ANY `use_figma` call, verify the script against [Section 1 Critical Rules](../SKILL.md#1-critical-rules):

- [ ] **Output** — uses `return` (not `figma.closePlugin()`), not wrapped in an async IIFE, no `console.log()` as output; `return`s structured data with ALL created/mutated node IDs (Rules 1, 2, 4, 15)
- [ ] **Color & fills** — 0–1 range; paint `color` is `{r, g, b}` only (no `a`); fills/strokes reassigned as new arrays (Rules 6, 7)
- [ ] **Type narrowing** — `characters`, `description`, and `componentPropertyDefinitions` guarded/narrowed before access (Rules 3a, 3b, 18)
- [ ] **Pages** — switches use `await figma.setCurrentPageAsync(page)`, at most once per call (Rule 9)
- [ ] **Layout & sizing** — related children in `figma.createAutoLayout()`; top-level nodes positioned away from (0,0); `HUG`/`FILL` set after `appendChild`; `resize()` before sizing modes; wrapping TEXT uses `textAutoResize='HEIGHT'` + FIXED width (Rules 12, 12a, 12b, 12c, 13)
- [ ] **Text** — canonical font recipe with style names verified via `listAvailableFontsAsync()`; `lineHeight`/`letterSpacing` as `{unit, value}`; `FONT_FAMILY` variables load every mode's value first (Rule 8)
- [ ] **Async & state** — every Promise `await`ed; multi-step IDs passed as string literals (Rules 15, 17)
