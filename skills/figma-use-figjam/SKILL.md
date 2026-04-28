---
name: figma-use-figjam
description: "This skill helps agents use Figma's use_figma MCP tool in the FigJam context. Can be used alongside figma-use which has foundational context for using the use_figma tool."
disable-model-invocation: false
---

# use_figma — Figma Plugin API Skill for FigJam

This skill contains FigJam-specific context for the `use_figma` MCP tool. The [figma-use](../figma-use/SKILL.md) skill provides foundational context for plugin API execution via MCP as well as the full Figma plugin API for more advanced use-cases that are not described here.

**Always pass `skillNames: "figma-use-figjam"` when calling `use_figma` for FigJam operations.** This is a logging parameter used to track skill usage — it does not affect execution.

## Inspecting FigJam Files

**`get_figjam` is the inspection tool for FigJam files.** It returns the full node tree as XML, including IDs of pages, sections, stickies, connectors, and other nodes you need to reference in subsequent `use_figma` calls.

- **Use `get_figjam` upfront** before writing any `use_figma` code that needs to reference existing nodes (page IDs, section IDs, etc.). Don't try to discover IDs by running an inspection script — `console.log` output from `use_figma` is **not returned to the agent** (see [figma-use Critical Rule #4](../figma-use/SKILL.md)). Only the `return` value comes back.
- **`get_metadata` does NOT work on FigJam files** — it is design-mode only and will fail immediately with "unsupported for FigJam files".
- **`get_screenshot` requires a valid `nodeId`** — passing an empty nodeId returns "invalid nodeId" error. Get IDs from `get_figjam` first.
- If you forgot to `return` an ID from a previous `use_figma` call and need it now, call `get_figjam` rather than re-running an inspection script.

## Loading Reference Docs Efficiently

Load only the references your task needs — but when you do need to load multiple, **issue all reads in a single parallel tool-call batch**, not sequentially across turns. For a typical board-creation task, that means a single message containing reads for `plan-board-content` plus the 3-4 specific node-type references you'll use.

## Deferred Tools — Batch-Load Schemas

The Figma MCP tools (`use_figma`, `get_figjam`, `get_screenshot`, `get_metadata`, `create_new_file`, `whoami`) often appear as deferred tools that require `ToolSearch` to load their schemas before they can be called. **Load all schemas in a single `ToolSearch` call** using the `select:` syntax instead of one call per tool:

```
ToolSearch query="select:use_figma,get_figjam,get_screenshot,get_metadata,create_new_file"
```

Six sequential `ToolSearch` calls is six round trips before any work happens. One batched call is one round trip.

## Reference Docs

- [plan-board-content](references/plan-board-content.md) - Read this for any board content request — board template, retro, brainstorm, ice breaker, meeting board, scaffold
  - Covers planning of generated board content, including sequential outline, sections, intents, and hierarchical text
  - Delegates to other references for specific API details
- [create-section](references/create-section.md) — Create and configure FigJam sections (sizing, naming, colors, content visibility, organizing nodes, column layouts)
- [create-sticky](references/create-sticky.md) — Create and configure FigJam sticky notes (colors, sizing, text, author visibility, batch creation)
- [create-connector](references/create-connector.md) — Create and configure FigJam connectors (endpoints, arrows, line types, labels, colors, diagram wiring)
- [create-text](references/create-text.md) — Create and configure FigJam text nodes (font loading, preset fonts and colors, sizing, lists, mind map operations)
- [position-figjam-nodes](references/position-figjam-nodes.md) — Position, size, and reparent nodes on the canvas (including within sections)
- [create-shape-with-text](references/create-shape-with-text.md) — Create and configure FigJam shapes with embedded text (shape types, color presets, sizing to fit text, diagram layouts)
- [create-code-block](references/create-code-block.md) — Create and configure FigJam code block nodes (languages, syntax highlighting, positioning, embedding in sections)
- [create-table](references/create-table.md) — Create and configure FigJam tables (rows, columns, cell text, color presets, resizing)
- [edit-text](references/edit-text.md) — Edit existing text nodes (font loading, styled ranges, find/replace, FigJam Charcoal default color)
- [create-label](references/create-label.md) — Create and configure FigJam label nodes (small numbered/lettered circle callout markers, sequences, positioning)
- [batch-modify](references/batch-modify.md) — Patterns for modifying many existing nodes at once (bulk style changes, repositioning, property updates)
