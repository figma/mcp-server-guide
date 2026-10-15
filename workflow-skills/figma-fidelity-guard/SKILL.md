---
name: figma-fidelity-guard
description: Audit and recover incomplete Figma evidence for high-fidelity design-to-code work. Use after or alongside figma-design-to-code when MCP output is truncated, sparse, or contains depth-limit markers; nested instances omit visible text or styles; implementation and screenshot disagree; or complex assets, variables, gradients, masks, effects, overlays, variants, or responsive behavior require an explicit context-completeness gate.
---

# Figma Fidelity Guard

## Outcome

Build from scoped design evidence instead of visual guesses. Declare the Figma context complete for the target scope before implementing. Treat fidelity as visual structure, content, states, responsive behavior, accessibility, and platform semantics—not blind pixel copying.

## Guardrails

- Resolve the exact Figma file and node from a selection or node-specific URL. Never guess a file key or node ID.
- This workflow extends `figma-design-to-code`; it does not replace that skill's primary extraction, asset, project-reuse, or implementation rules.
- Apply this workflow to Figma Design UI. Route FigJam and Slides to their dedicated skills. For Figma Make, use only the context tools supported by that surface; do not assume metadata, code execution, or editable layer access exists.
- Keep inspection read-only. Never mutate the design while gathering evidence.
- Apply the workflow proportionally. A simple, complete component may need only design context and its returned screenshot; complex or inconsistent regions require deeper inspection.
- Minimize calls and returned data. Reuse discovered node IDs and findings instead of repeating full-frame reads.
- Treat a `depth limit` marker as evidence of an incomplete branch, not as an error to ignore and not as proof that the entire response is unusable.
- Never declare context complete merely because a tool call succeeded. Completeness is based on whether the evidence accounts for the requested scope.

## Runtime Adapter

- Before calling `get_design_context`, load `figma-design-to-code` through the client's normal skill-loading mechanism. Preserve that skill's required logging and add `figma-fidelity-guard` to `skillNames` when the tool exposes the field.
- Before calling `use_figma`, load the `figma-use` foundation skill through the client's normal skill-loading mechanism.
- When the tool exposes a `skillNames` field, pass `figma-fidelity-guard,figma-use` on every `use_figma` call made by this workflow.
- Use bounded, read-only queries only when `use_figma` is available and the file key is known. Do not make `use_figma` mandatory when primary context is already complete or when the connected MCP surface does not provide it.

## Workflow

### 1. Fix the fidelity contract

Record the target region, platform or viewport, theme or variable mode, component state or variant, expected output, and applicable code design system. If any item would materially change the implementation and cannot be inferred, stop and obtain the missing context.

### 2. Collect the minimum primary evidence

Reuse an existing `get_design_context` result when it targets the exact node, state, and mode. Otherwise load `figma-design-to-code` and call `get_design_context` first for the exact target node.

Use the screenshot returned with design context when present. Call `get_screenshot` for the same node only when the primary result lacks a current render or an independent rendered comparison is needed. Never use metadata or a screenshot as a substitute for primary design context.

If both sources account for the visible design and expose the properties needed for implementation, proceed without metadata or deep traversal.

### 3. Close only demonstrated gaps

Maintain a small gap ledger containing unresolved visible regions, discovered node IDs, visited node IDs, and the evidence still required. Then use only the routes justified by that ledger:

- If design context is too large, truncated, sparse, or internally inconsistent, call `get_metadata` as an index when available and re-fetch only relevant child nodes with `get_design_context`.
- If a depth-limited branch exposes a child node ID, request that child directly rather than increasing an assumed global depth. Do not hard-code a presumed MCP depth ceiling.
- If nested node IDs or required properties remain hidden, use a bounded, read-only `use_figma` query against the smallest known ancestor. Enumerate immediate children or return selected scalar fields; never dump the document.
- If variables or styles affect the mapping, call `get_variable_defs` rather than inferring token values from rendered colors.
- Search by intersecting bounds only when the screenshot contains visible content not accounted for by the target subtree. Include page-level overlays deliberately and avoid scanning unrelated pages.
- Use `download_assets` when implementation needs an original or exported asset and the connected server provides it. Otherwise request the exact source or export instead of substituting a screenshot. Treat screenshots and temporary localhost asset references as inspection evidence, not production assets.

Read [deep-inspection.md](references/deep-inspection.md) when context is incomplete or the target contains complex effects, nested instances, masks, overlays, or ambiguous responsive behavior.

Stop expanding when a read adds no new evidence, the relevant visible scope is accounted for, or the agreed inspection budget is exhausted. Report the remaining gap instead of looping.

### 4. Pass the context-completeness gate

Compare the screenshot with the collected node evidence. Account for every visually or behaviorally relevant region in scope, including text, assets, fills, strokes, effects, masks, clipping, layer order, component states, and layout constraints.

For non-trivial UI, publish this concise table before implementation:

| Region or layer | Figma evidence | Key properties or behavior | Code mapping | Confidence or gap |
|---|---|---|---|---|
| background | node id/name + screenshot | fill/image/gradient/effective alpha | asset/gradient/token | confirmed |
| content | node id/name | text, typography, asset, ordering | component/token/asset | confirmed |
| behavior | frame/instance | constraints, auto layout, variants | responsive/state logic | unresolved node id |

End with exactly one status:

- `Context status: complete for scope`
- `Context status: partial — <specific gaps>`
- `Context status: blocked — <required node, permission, or evidence>`

Do not begin a fidelity-sensitive implementation until the status is `complete for scope`. With explicit user authorization, a partial status may support analysis or a clearly labeled prototype, but never an unqualified fidelity claim.

### 5. Map evidence to code

- Reuse existing project components, tokens, typography, and asset conventions when they represent the Figma intent. Verify rather than assume that a Figma variable maps to a code token. If no suitable token exists, preserve the measured value and report the gap; do not expand the design system unless requested.
- Preserve responsive intent from constraints and auto layout. Validate under finite parent constraints, relevant viewport sizes, text scaling, and realistic content where applicable.
- Preserve semantics, keyboard or assistive access, platform conventions, and reduced-motion behavior. Document intentional deviations from the visual design instead of degrading usability to achieve a screenshot match.
- Preserve complex composition when it is material. Compute effective alpha only for simple parent-opacity and child-paint cases; masks, blend modes, gradients, and filters require structural inspection or rendered comparison.

### 6. Verify proportionally

Keep implementation changes inside the requested scope. Run the project's relevant static checks and focused tests. When practical and authorized, compare implementation and Figma screenshots at the same viewport, state, content, scale, and theme.

Prefer stable assertions for token usage, asset identity, semantics, state behavior, and durable visual structure. Avoid tests coupled only to generated widget or DOM shape. On a mismatch, re-read the smallest implicated Figma region instead of restarting the entire extraction.

## Stop Conditions

Stop and report the exact gap when:

- the target node, state, viewport, or platform is ambiguous
- a visible screenshot region has no corresponding node or asset evidence
- truncation, an unexpanded instance, or missing style data remains relevant to the implementation
- an effect, mask, gradient, or asset would be approximated before its source is inspected
- a traversal repeats nodes, adds no evidence, or exceeds the agreed inspection budget
- verification reveals a material mismatch in brightness, layer order, clipping, spacing, typography, state, or responsive behavior
- continuing would require changing Figma, broadening the code scope, or inventing a design-system rule without authorization
