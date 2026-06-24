# Figma MCP Codex Evals

This folder defines a lightweight black-box evaluation suite for improving the Figma MCP experience in Codex. It is designed for people who do not work at Figma and only have normal Figma account access.

Run these evals whenever you change:

- README setup instructions
- Figma skill instructions
- tool lists or routing guidance
- Codex-specific examples
- error recovery or validation guidance

## Setup

1. Connect the Figma MCP server in Codex.

```bash
codex mcp add figma --url https://mcp.figma.com/mcp
```

2. Authenticate with Figma when prompted.
3. Create or choose a disposable Figma draft file for write tests.
4. Use the task files in [`tasks/`](tasks/) as prompts.
5. Score each run with [`scorecard.md`](scorecard.md).

## Evaluation Principles

- Treat the MCP server as a black box. Do not rely on Figma-internal systems.
- Use your own Figma account and files.
- Prefer small, repeatable fixtures over large production files.
- Capture the exact prompt, Figma file URL, agent transcript summary, and final screenshot or file URL.
- Mark plan-gated features as `blocked-by-access`, not failed, when your account lacks the required Figma plan, seat, library, or Code Connect setup.

## Suggested Run Order

1. [`01-connection-smoke.md`](tasks/01-connection-smoke.md)
2. [`02-read-design-context.md`](tasks/02-read-design-context.md)
3. [`03-write-canvas.md`](tasks/03-write-canvas.md)
4. [`04-design-system-search.md`](tasks/04-design-system-search.md)
5. [`05-code-connect-gated.md`](tasks/05-code-connect-gated.md)

## Pass Criteria

A change is better for Codex if it improves at least one score without regressing another:

- setup success rate
- correct tool choice
- fewer dead-end calls
- clearer user-facing recovery
- stronger visual or structural validation
- fewer hallucinated components, assets, or tokens

