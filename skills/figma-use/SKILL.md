---
name: figma-use
description: "**MANDATORY prerequisite** — you MUST invoke this skill BEFORE every `use_figma` tool call. NEVER call `use_figma` directly without loading this skill first. Skipping it causes common, hard-to-debug failures. Trigger whenever the user wants to perform a write action or a unique read action that requires JavaScript execution in the Figma file context — e.g. create/edit/delete nodes, set up variables or tokens, build components and variants, modify auto-layout or fills, bind variables to properties, or inspect file structure programmatically."
disable-model-invocation: false
---
# use_figma — Figma Plugin API Skill
Use the `use_figma` tool to execute JavaScript in Figma files via the Plugin API. All detailed reference docs live in `references/`.

When available, call `create_session` with `fileKey` and `description` before file reads or edits (create the file first if needed), then pass the returned `sessionId` unchanged to every call that accepts it, including follow-ups and work across files.

**Always include `figma-use` in the comma-separated `skillNames` parameter when calling `use_figma`. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-use`).** This is a logging parameter used to track skill usage — it does not affect execution.

**If Figma MCP tools appear as deferred tools, batch-load all their schemas in a single `ToolSearch` call** using the `select:` syntax — e.g. `ToolSearch query="select:use_figma,get_screenshot,get_metadata,create_new_file"`. One round trip beats six.

**MANDATORY for visible design changes:** Before the first mutating `use_figma` call, load [figma-generate-design](../figma-generate-design/SKILL.md) alongside this skill and include both names in every mutating call’s `skillNames`. This applies from a single visible property or element to a full page, screen, or composed multi-section view—even when the user calls that view a component. `figma-use` provides the Plugin API rules; `figma-generate-design` provides design-system discovery through `search_design_system`, asset importing, and incremental assembly.

**Reusable library exception:** If the primary deliverable is a reusable component, component set, variant system, variable/token collection, style foundation, or other library asset intended for reuse or publication, load [figma-generate-library](../figma-generate-library/SKILL.md) instead. It provides the component-creation workflow—variable foundations, variant sets, and design-token bindings—that `figma-use` alone does not cover. For tasks that include both library assets and a composed design that uses them, load both companion skills. Read-only `use_figma` calls need neither.

**3D transforms:** For perspective, depth, X/Y tilt, isometric cubes, or other static 3D poses, load [figma-3d-transforms](../figma-3d-transforms/SKILL.md) when available. It owns the gated `transform3d`, `scene3d`, and `transformOrigin` API guidance, including fields that may be absent from the general typings. Follow this skill's node-creation rules, then apply the 3D poses to the resulting nodes. If the 3D skill or APIs are unavailable, explain that 3D authoring is not enabled in this session. Flat in-plane rotation uses `node.rotation` and does not need the 3D skill.

For other APIs, load [plugin-api-standalone.index.md](references/plugin-api-standalone.index.md) to understand what is possible. When you are asked to write plugin API code, use this context to grep [plugin-api-standalone.d.ts](references/plugin-api-standalone.d.ts) for relevant types, methods, and properties. This is the definitive source of truth for the general API surface. It is a large typings file, so do not load it all at once, grep for relevant sections as needed.

IMPORTANT: Whenever you work with design systems, start with [working-with-design-systems/wwds.md](references/working-with-design-systems/wwds.md) to understand the key concepts, processes, and guidelines for working with design systems in Figma. Then load the more specific references for components, variables, text styles, and effect styles as needed.

## 1. Critical Rules
1.  **Use `return` to send data back.** The return value is JSON-serialized automatically (objects, arrays, strings, numbers). Do NOT call `figma.closePlugin()` or wrap code in an async IIFE — this is handled for you.
2.  **Write plain JavaScript with top-level `await` and `return`.** Code is automatically wrapped in an async context. Do NOT wrap in `(async () => { ... })()`.
3.  `figma.notify()` **throws "not implemented"** — never use it
3a. **Return node IDs and keep workflow state outside the Figma file.** Set human-readable component purpose and usage in `node.description` only on a `COMPONENT` or `COMPONENT_SET` — never on a frame or instance.
3b. **Narrow before accessing type-specific properties.** Check `node.type`, use a capability guard such as `"characters" in node`, or prefilter with `findAllWithCriteria`. `characters` requires a text-capable node; optional chaining does not protect unsupported property access.
4.  `console.log()` is NOT returned — use `return` for output
5.  **Size construction calls for safe retry and validate from evidence.** Do not split a working operation solely to create validation checkpoints. Batch related work when the resulting script remains safe to retry; a complete section or page may be built in one call. Split when crossing page context, when partial execution would be difficult to recover, or after an actual failure requires a targeted retry. Return affected IDs and relevant counts, names, or bounds from each write—this counts as structural validation. Run a separate structural check only when required evidence is missing or after a relevant mutation. Normally take one screenshot after composition and one after a visual fix. The most recent passing screenshot is the final check; do not repeat it when nothing relevant changed. Stop once requirements pass.
6.  Colors are **0–1 range** (not 0–255): `{r: 1, g: 0, b: 0}` = red. Paint `color` objects use `{r, g, b}` **only — no `a` field**; opacity goes at the paint level (`{ type: 'SOLID', color: {...}, opacity: 0.5 }`).
7.  Fills/strokes are **read-only arrays** — clone, modify, reassign
8.  **Every text edit follows the canonical recipe: load font → `await` → mutate → return affected node IDs.** Skipping the load throws `Cannot write to node with unloaded font "<family> <style>"`. The rule covers more than `characters` — it applies to any operation on nodes with unloaded fonts (`appendChild`, `insertChild`, `setBoundVariable`, `setExplicitVariableModeForCollection`, `setValueForMode`, `findAll` callbacks touching text). When mutating existing text, load the node's *current* fonts via `getStyledTextSegments(['fontName'])`, not a hardcoded default. Inter is preloaded in most environments so other families surface this bug more often — the recipe is the same for every font. Use `await figma.listAvailableFontsAsync()` first if the style string is unverified — **never guess** (`"SemiBold"` vs `"Semi Bold"` is a common footgun). For `FONT_FAMILY`-scoped variables, load every value across every relevant mode before `setBoundVariable("fontFamily", …)`, `setValueForMode`, or `setExplicitVariableModeForCollection`. `lineHeight`/`letterSpacing` take `{unit, value}`, not bare numbers. See [Canonical text-edit recipe](references/gotchas.md#canonical-text-edit-recipe-font-load--await--mutate--return-ids).
9.  **Pages load incrementally** — use `await figma.setCurrentPageAsync(page)` to switch pages and load their content. The sync setter `figma.currentPage = page` does **NOT** work and throws `"Setting figma.currentPage is not supported"`. Page context resets to the **first page** at the start of every `use_figma` call, so re-switch each call; switch **at most once per call** and fan multi-page work out in parallel — see [Page Rules](#2-page-rules-critical) and [gotchas.md](references/gotchas.md#set-current-page-once-per-use_figma-call--split-multi-page-work-into-parallel-calls).
10. `setBoundVariableForPaint` returns a **NEW** paint — must capture and reassign
11. `createVariable` accepts collection **object or ID string** (object preferred)
12. **`layoutSizingHorizontal/Vertical` is value-restricted by structural context — `FIXED` always works, `HUG` and `FILL` do not.** `'HUG'` is valid only on an auto-layout frame itself OR on a **TEXT** child of one. `'FILL'` is valid only on a child of an auto-layout frame that is also not absolute-positioned, not inside an immutable frame, and not a canvas-grid child. Practical consequence: append to an auto-layout parent FIRST, then set `HUG`/`FILL` — a newly-created or unparented node can't satisfy the rule yet. The property itself exists on every `SceneNode`; the error is value-rejection, not "no such property". See [Gotchas](references/gotchas.md#layoutsizinghorizontallayoutsizingvertical-value-rules-fixed-hug-fill).
12a. **Use auto-layout for containers that hold related children.** When children have a structural relationship — stacked, side-by-side, aligned, gapped, hugged — wrap them in `figma.createAutoLayout()`, not `figma.createFrame()` with absolute `x`/`y`. Absolute coordinates govern where a container sits on the canvas; auto-layout governs how its children relate inside it. Skipping the container leaves no protection against text reflow, content changes, or overlap.
12b. **`layoutSizing*` and `*AxisSizingMode` are different enums — don't cross them.** `layoutSizingHorizontal`/`layoutSizingVertical` (set on a **child**) take `'FIXED'|'HUG'|'FILL'`; `primaryAxisSizingMode`/`counterAxisSizingMode` (set on the **frame** itself) take `'FIXED'|'AUTO'`. So `layoutSizingVertical = 'AUTO'` is invalid (use `'HUG'`), and `counterAxisSizingMode = 'FILL'` throws `Expected 'FIXED' | 'AUTO', received 'FILL'` (use `'FIXED'`/`'AUTO'`). Two more errors from the same setter — `Error: in set_layoutSizingHorizontal: node must be an auto-layout frame or a child of an auto-layout frame` and `Error: in set_layoutSizingHorizontal: FILL can only be set on children of auto-layout frames` — mean the node isn't in an auto-layout context yet; **recommendation: make the parent auto-layout (`figma.createAutoLayout()`) and `appendChild` the node before setting** (see Rule 12). See [Gotchas](references/gotchas.md#layoutsizing-vs-axissizingmode-two-different-sizing-enums).
12c. **`resize()` resets sizing modes to `FIXED`, so call it BEFORE setting `layoutSizing*`.** A wrapping **TEXT** block needs `textAutoResize = 'HEIGHT'` plus an explicit FIXED width (`resize()`), NOT `FILL` alone — the default `WIDTH_AND_HEIGHT` mode ignores `FILL` and collapses the node to a near-zero-width thread. Verify `node.width > 0` afterward.
13. **Position new top-level nodes away from (0,0).** Nodes appended directly to the page default to (0,0). Scan `figma.currentPage.children` to find a clear position (e.g., to the right of the rightmost node). This only applies to page-level nodes — nodes nested inside other frames or auto-layout containers are positioned by their parent. See [Gotchas](references/gotchas.md).
14. **On `use_figma` error, obey `safeToRetryWithoutCanvasRead`.** If `true`, fix the error and retry. If `false`, read the canvas, determine what changed, then make changes. See [Error Recovery](#7-error-recovery--self-correction).
15. **MUST `return` ALL created/mutated node IDs.** Whenever a script creates new nodes or mutates existing ones on the canvas, collect every affected node ID and return them in a structured object (e.g. `return { createdNodeIds: [...], mutatedNodeIds: [...] }`). This is essential for subsequent calls to reference, validate, or clean up those nodes. No state persists across `use_figma` calls, so pass IDs from previous calls as **string literals**, not variables. See [common-patterns.md](references/common-patterns.md) for worked multi-step examples.
16. **Always set `variable.scopes` explicitly when creating variables.** The default `ALL_SCOPES` pollutes every property picker — almost never what you want. Use specific scopes like `["FRAME_FILL", "SHAPE_FILL"]` for backgrounds, `["TEXT_FILL"]` for text colors, `["GAP"]` for spacing, etc. See [variable-patterns.md](references/variable-patterns.md) for the full list.
17. **`await` every Promise.** Never leave a Promise unawaited — unawaited async calls (e.g. `figma.loadFontAsync(...)` without `await`, or `figma.setCurrentPageAsync(page)` without `await`) will fire-and-forget, causing silent failures or race conditions. The script may return before the async operation completes, leading to missing data or half-applied changes.
18. **Never read `componentPropertyDefinitions` from a variant component.** Narrow the owner first: use the node itself when it is a `COMPONENT_SET`, use a `COMPONENT` only when its parent is not a `COMPONENT_SET`, and otherwise promote a variant `COMPONENT` to its parent set. Optional chaining does not make the getter safe. See [Component-property owner narrowing](references/component-patterns.md#component-property-owner-narrowing).
19. **Never read `componentPropertyDefinitions`, `componentProperties`, or `valuesByMode` across a collection.** Resolve specific node IDs first, then read the property bundle only for those IDs. Reading one resolved node is safe; mapping these getters over `findAll*` results, `children`, or `getLocalVariables*` is the single largest cause of oversized returns.
20. **Broad reads return `id`, `name`, `type` and counts only.** Fetch details for selected IDs in later calls. Return each file-wide inventory — variables, text styles, effect styles, paint styles, components, pages — in its own call; do not combine them into one return.
21. **When a read may be large, measure the serialized return before returning it.** Bytes, not array length: `.slice()` bounds row count but not per-item size. If over budget, narrow the ID set or split across calls. Never drop required IDs or silently truncate.
> For detailed WRONG/CORRECT examples of each rule, see [Gotchas & Common Mistakes](references/gotchas.md).

## 2. Page Rules (Critical)

The async-only setter and the per-call context reset are covered in Rule 9. This section elaborates the one rule that needs a worked example: **switch pages at most once per script, and fan multi-page work out in parallel.**

Never loop over `figma.root.children` and switch pages inside the loop — each switch reloads the file. If the work spans multiple pages, **split it into N `use_figma` calls (one per target page) and emit them in parallel** — a single assistant message containing N `use_figma` tool-use blocks. The harness runs them concurrently; each script sets `currentPage` exactly once.

> **Explicit instruction:** when fanning out, you MUST issue the N tool calls in **one message**. Do not send them across multiple turns. Do not await one before issuing the next. Sequential per-page calls waste the entire benefit of splitting.

```js
// AVOID — switches pages N times in one script, reloads the file each time
for (const page of figma.root.children) {
  await figma.setCurrentPageAsync(page);
  // ... touch this page ...
}

// PREFER — read-only discovery call to get page IDs, then in the NEXT message
// emit N parallel use_figma tool calls (one per page), each setting currentPage once.
```

Default to parallel fan-out for any multi-page work — reads and writes alike. You can also call `use_figma` multiple times to build incrementally (e.g. `return` metadata about existing nodes, then modify them in a subsequent script). See [gotchas.md → Set current page once per `use_figma` call](references/gotchas.md#set-current-page-once-per-use_figma-call--split-multi-page-work-into-parallel-calls) for the full rationale.

## 3. `return` Is Your Output Channel

The agent sees **ONLY** the value you `return` — `console.log()` is invisible (Rule 4), and thrown errors are auto-captured (let them propagate or `throw` explicitly). The hard requirement is Rule 15: every script that creates or mutates canvas nodes **MUST** return all affected node IDs plus any actionable status in a structured object — e.g. `return { createdNodeIds: [...], mutatedNodeIds: [...], count: 5, errors: [] }` — so subsequent calls can reference, validate, or clean them up.

## 4. Editor Mode

**Tell the editor from the URL:** Design = `figma.com/design/...`, FigJam = `figma.com/board/...`, Slides = `figma.com/slides/...`. Confirm before assuming an API or node type is available. `figma.createPage()` is Design-only and throws in FigJam and Slides. For Slides, use read-only `use_figma` + `get_screenshot` / `await node.screenshot()` and load [figma-use-slides](../figma-use-slides/SKILL.md). See [workflow-and-inspection.md](references/workflow-and-inspection.md#editor-mode-node-availability) for full allowed/blocked node lists.

## 5. Efficient APIs — Prefer These Over Verbose Alternatives

Always prefer these built-in helpers to reduce boilerplate, ordering errors, and token output (see [efficient-apis.md](references/efficient-apis.md) for full syntax, methods, and examples):

| Helper | Purpose |
|---|---|
| `node.query(selector)` | CSS-like subtree search (`.first()`, `.last()`, `.values(keys)`, `.set(props)`, `.toArray()`, `.filter()`, `.map()`; no global `figma.query()`) |
| `node.set(props)` | Batch property updates (`layoutMode` prioritized; `width`/`height` routed to `resize()`; chainable with `.query()`) |
| `figma.createAutoLayout(dir?, props?)` | Default auto-layout container with both axes hugging (Rule 12a); children can immediately use `FILL` after `appendChild` |
| `node.placeholder = true/false` | Shimmer overlay while building; **always set back to `false` when done** |
| `await node.screenshot(opts?)` | Inline PNG capture (default 0.5x capped at 1024px); follow Rule 5 cadence |

## 6. Incremental Workflow (How to Avoid Bugs)

Use Rule 5's safe-retry and evidence-based validation contract:

- **Choose call boundaries for recoverability, not validation cadence.** Batch related creation, property updates, parenting, and targeted diagnostics when safe. **Slides override:** slides are isolated subtrees — building 3–5 new slides or applying one edit across a deck in one call is safe (see [figma-use-slides](../figma-use-slides/SKILL.md)).
- **Pattern:** (1) Inspect existing file conventions first; (2) build top-down skeleton with `placeholder = true`; (3) populate retry-safe batches and clear `placeholder = false`; (4) return ALL created/mutated IDs + validation evidence (counts, names, hierarchy, bounds); (5) fix defects before moving on.

See [workflow-and-inspection.md](references/workflow-and-inspection.md#suggested-step-order--validation-matrix) for the step-order diagram and `get_metadata` / `get_screenshot` validation matrix.

## 7. Error Recovery & Self-Correction

On any `use_figma` error, obey `safeToRetryWithoutCanvasRead` (Rule 14): `true` → fix and retry without adding a diagnostic canvas read; `false` → read the canvas, determine what changed, then proceed. If the same API/property error repeats twice, inspect its definition once and fix the root cause instead of splitting further. When a script succeeds but the result looks wrong, use `get_metadata` + `get_screenshot` (check for clipped text and overlapping elements) and apply a targeted fix.

See [workflow-and-inspection.md](references/workflow-and-inspection.md#common-non-contract-error-messages) and [validation-and-recovery.md](references/validation-and-recovery.md) for the error table and full recovery workflow.

## 8. Pre-Flight Checklist

Before submitting ANY `use_figma` call, re-read the script against [Section 1](#1-critical-rules) (output/IDs, 0–1 color & fills, type narrowing, single page switch, auto-layout & sizing order, canonical font recipe, awaited promises). See [workflow-and-inspection.md](references/workflow-and-inspection.md#pre-flight-checklist) for the full item-by-item checklist.

## 9. Discover Conventions Before Creating

**Always inspect the Figma file before creating anything** (pages, components, variable collections, naming conventions), then check the user's codebase. Match existing conventions rather than imposing new ones. See [workflow-and-inspection.md](references/workflow-and-inspection.md#quick-inspection-scripts) for read-only inspection scripts (including the two-step parallel page fan-out for on-canvas components).

## 10. Reference Docs

Load these as needed based on what your task involves:

| Doc | When to load | What it covers |
|-----|-------------|----------------|
| [efficient-apis.md](references/efficient-apis.md) | Writing any `use_figma` script | `node.query()` selectors/methods, `node.set()`, `createAutoLayout()`, `placeholder`, `screenshot()` |
| [workflow-and-inspection.md](references/workflow-and-inspection.md) | Inspecting files, Slides/FigJam, or checking workflow tables | Editor-mode node availability, step-order/validation matrix, non-contract errors, inspection scripts |
| [gotchas.md](references/gotchas.md) | Before any `use_figma` | Every known pitfall with WRONG/CORRECT code examples — start with the [canonical text-edit recipe](references/gotchas.md#canonical-text-edit-recipe-font-load--await--mutate--return-ids) |
| [common-patterns.md](references/common-patterns.md) | Need working code examples | Script scaffolds: shapes, text, auto-layout, variables, components, multi-step workflows |
| [plugin-api-patterns.md](references/plugin-api-patterns.md) | Creating/editing nodes | Fills, strokes, Auto Layout, effects, grouping, cloning, styles |
| [api-reference.md](references/api-reference.md) | Need exact API surface | Node creation, variables API, core properties, what works and what doesn't |
| [validation-and-recovery.md](references/validation-and-recovery.md) | Multi-step writes or error recovery | `get_metadata` vs `get_screenshot` workflow, mandatory error recovery steps |
| [component-patterns.md](references/component-patterns.md) | Creating components/variants | combineAsVariants, component properties, INSTANCE_SWAP, variant layout, discovering existing components, metadata traversal |
| [variable-patterns.md](references/variable-patterns.md) | Creating/binding variables | Collections, modes, scopes, aliasing, binding patterns, discovering existing variables |
| [text-style-patterns.md](references/text-style-patterns.md) | Creating/applying text styles | Type ramps, font discovery via `listAvailableFontsAsync`, listing styles, applying styles to nodes |
| [effect-style-patterns.md](references/effect-style-patterns.md) | Creating/applying effect styles | Drop shadows, listing styles, applying styles to nodes |
| [plugin-api-standalone.index.md](references/plugin-api-standalone.index.md) | Need to understand the full API surface | Index of all types, methods, and properties in the Plugin API |
| [plugin-api-standalone.d.ts](references/plugin-api-standalone.d.ts) | Need exact type signatures | Full typings file — grep for specific symbols, don't load all at once |

## 11. Snippet examples

You will see snippets throughout documentation here. These snippets contain useful plugin API code that can be repurposed. Use them as is, or as starter code as you go. If there are key concepts that are best documented as generic snippets, call them out and write to disk so you can reuse in the future.
