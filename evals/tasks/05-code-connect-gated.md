# Eval 05: Code Connect Gated Flow

## Goal

Confirm that Codex handles Code Connect correctly, including access and publishing requirements.

## Fixture

Use a Figma component or component set URL. Best case: the component is published to a team library and your account has the right access. If not, this task should still evaluate whether Codex explains the blocker clearly.

## Prompt

```text
Use the Figma MCP server to check whether this component can be connected to code with Code Connect: <PASTE_COMPONENT_URL>

Do not write a mapping yet. First tell me whether the component is eligible, what code component you would search for, and what access or publishing blockers exist.
```

## Expected Tool Use

- `get_code_connect_suggestions`
- `get_context_for_code_connect` only if suggestions show eligible components
- local codebase search if a matching code component is needed

## Pass Criteria

- Codex confirms the URL has a `node-id` and converts it correctly for tool calls.
- Codex checks for published component eligibility.
- Codex does not promise Code Connect if the account, plan, or component publishing state blocks it.
- Codex asks for confirmation before creating mappings.

## Failure Modes To Watch

- Writes mappings without confirmation.
- Uses the frame node instead of the resolved main component node.
- Treats no published component as a repo/code problem.
- Invents a source file path without searching the codebase.

