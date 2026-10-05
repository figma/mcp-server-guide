# Eval 03: Write To Canvas

## Goal

Confirm that Codex can create or update Figma content safely and validate the result.

## Prompt

```text
Use the Figma MCP server to create a new Figma Design file called "Codex MCP Eval - Card".

In that file, create one simple product card with:
- title: "Design System Audit"
- subtitle: "3 issues need review"
- one primary button labeled "Open report"

Use native Figma layers, return the file URL and created node IDs, then take a screenshot so I can verify it.
```

## Expected Tool Use

- `whoami` if a plan key is needed
- `create_new_file`
- `use_figma`
- inline screenshot through `use_figma` or `get_screenshot`

## Pass Criteria

- Codex creates a new file rather than asking the user to create one manually.
- The write script returns `createdNodeIds`.
- Text is visible and fonts are loaded correctly.
- The card is not placed blindly at a confusing origin when existing content exists.
- Codex provides the Figma file URL and a validation screenshot or screenshot confirmation.

## Failure Modes To Watch

- Missing node IDs.
- Invisible text from unloaded fonts or transparent fills.
- Uses `console.log()` as the only output channel.
- Retries a failed script without reading the error.

