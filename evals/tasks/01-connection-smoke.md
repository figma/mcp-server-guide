# Eval 01: Connection Smoke Test

## Goal

Confirm that an agent can connect to the Figma MCP server, authenticate, and explain the user's available plan/seat context.

## Prompt

```text
Use the Figma MCP server to run whoami. Tell me which Figma account is authenticated, what plans/seats are available, and whether anything about my access could limit MCP testing.
```

## Expected Tool Use

- `whoami`

## Pass Criteria

- The agent uses the Figma MCP server, not web search.
- The agent identifies the authenticated account.
- The agent reports plan and seat information when returned.
- The agent explains likely access constraints in plain English.
- If auth fails, the agent gives exact next steps to authenticate.

## Failure Modes To Watch

- Claims the server is connected without running a tool.
- Confuses the agent account identity with Figma identity.
- Gives generic plan advice without using the returned `whoami` data.
