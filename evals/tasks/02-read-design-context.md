# Eval 02: Read Design Context

## Goal

Confirm that an agent can read a normal Figma frame and use the right mix of structural data, visual reference, and variable context.

## Fixture

Create a disposable Figma Design file with one frame that contains:

- a heading text layer
- a button-like component or frame
- one image or icon if available
- one color variable or text style if available

Copy the frame URL with `node-id`.

## Prompt

```text
Use the Figma MCP server to inspect this frame: <PASTE_FRAME_URL>

Tell me what is in it, which tokens/styles/components you can identify, and what you would need before implementing it in code. Do not implement anything.
```

## Expected Tool Use

- `get_metadata`
- `get_design_context`
- `get_screenshot`
- `get_variable_defs` when variables or styles are relevant

## Pass Criteria

- The agent extracts the exact `fileKey` and `nodeId`.
- The agent uses the selected node, not the whole file unless needed.
- The agent compares visual screenshot and structured context.
- The agent names uncertainty instead of inventing token/component names.
- The agent suggests smaller node reads if the selection is too large.

## Failure Modes To Watch

- Implements code when asked not to.
- Hallucinates project components or token names.
- Skips screenshot validation.
- Treats React/Tailwind MCP output as final project code.
