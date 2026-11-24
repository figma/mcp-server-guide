# State Ledger Schema & Resume Protocol

Do not store workflow state on Figma objects. Use deterministic names for discovery and exact returned IDs in the state ledger. Put human-readable component purpose and usage guidance in the component or component-set `description`.

| Entity type | Stable identity | How to check existence |
|-------------|----------------|----------------------|
| Pages and frames | Deterministic name + state-ledger ID | `figma.root.children.find(p => p.name === pageName)` or `await figma.getNodeByIdAsync(id)` |
| Components and component sets | Variant/set name + state-ledger ID | `page.findOne(n => n.name === name)` or `await figma.getNodeByIdAsync(id)` |
| Variables | Name within collection | `(await figma.variables.getLocalVariablesAsync()).find(v => v.name === name && v.variableCollectionId === collId)` |
| Styles | Name | `getLocalTextStyles().find(s => s.name === name)` |

Record every returned ID in the state ledger immediately after creation. Never use a fuzzy lookup to authorize deletion.

## State Persistence

Do NOT rely solely on conversation context for the state ledger. Write it to disk:

```text
/tmp/design-system-state-{RUN_ID}.json
```

Re-read this file at the start of every turn. In long workflows, conversation context will be truncated — the file is the source of truth.

Maintain a state ledger tracking:

```json
{
  "runId": "ds-build-2024-001",
  "scope": "single-component",
  "step": "component-button",
  "entities": {
    "collections": { "primitives": "id:...", "color": "id:..." },
    "variables": { "color/bg/primary": "id:...", "spacing/sm": "id:..." },
    "pages": { "Cover": "id:...", "Button": "id:..." },
    "components": { "Button": "id:..." }
  },
  "pendingValidations": ["Button:screenshot"],
  "completedSteps": ["discovery", "foundations/verified", "component-button/base"]
}
```

## Idempotency & Resume Protocol

- **Idempotency check** before every create: query by name + state ledger ID. If exists, skip or update — never duplicate.
- **Resume protocol**: at session start or after context truncation, run a read-only `use_figma` to scan all pages, components, variables, and styles by name to reconstruct the `{key → id}` map. Then re-read the state file from disk if available.
- **Continuation prompt** (give this to the user when resuming in a new chat):
  > "I'm continuing a design system build. Run ID: {RUN_ID}. Load the figma-generate-library skill and resume from the last completed step."
