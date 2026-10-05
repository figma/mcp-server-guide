# Eval 04: Design System Search

## Goal

Confirm that Codex checks available libraries, components, variables, and styles before drawing primitives from scratch.

## Fixture

Use a Figma file that has at least one design library added. If no team library is available, use any file with local variables or components and mark library-specific checks as `blocked-by-access`.

## Prompt

```text
Use the Figma MCP server to inspect this file for reusable design system material: <PASTE_FILE_OR_FRAME_URL>

Find likely button, card, color, spacing, and text style resources. Tell me which are local, which are library-backed, and which are missing. Do not create anything.
```

## Expected Tool Use

- `get_libraries`
- `search_design_system`
- `use_figma` for local file inspection when appropriate
- `get_variable_defs` for a selected frame when relevant

## Pass Criteria

- Codex distinguishes local variables from remote/library variables.
- Codex does not conclude "no variables exist" solely from local variable APIs.
- Codex searches multiple short terms instead of one overloaded query.
- Codex summarizes what can be reused before suggesting new layers.

## Failure Modes To Watch

- Creates new primitives before searching.
- Treats an empty local variable collection as proof that no variables exist.
- Reports unsupported library access as a normal failure instead of an access blocker.

