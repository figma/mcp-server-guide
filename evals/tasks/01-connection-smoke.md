# Eval 01: Connection Smoke Test

## Goal

Confirm that Codex can connect to the Figma MCP server, authenticate, and explain the user's available plan/seat context.

## Prompt

```text
Use the Figma MCP server to run whoami. Tell me which Figma account is authenticated, what plans/seats are available, and whether anything about my access could limit MCP testing.
```

## Expected Tool Use

- `whoami`

## Pass Criteria

- Codex uses the Figma MCP server, not web search.
- Codex identifies the authenticated account.
- Codex reports plan and seat information when returned.
- Codex explains likely access constraints in plain English.
- If auth fails, Codex gives exact next steps to authenticate.

## Failure Modes To Watch

- Claims the server is connected without running a tool.
- Confuses Codex account identity with Figma identity.
- Gives generic plan advice without using the returned `whoami` data.

