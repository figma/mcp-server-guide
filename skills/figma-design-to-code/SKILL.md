---
name: figma-design-to-code
description: "**MANDATORY prerequisite** — you MUST invoke this skill BEFORE calling the `get_design_context` Figma MCP tool. You MUST trigger this skill whenever the user wants to implement, build, port, or code up a Figma design as code. Example prompts (not exhaustive) are 'implement this Figma design', 'build this screen from Figma', 'turn this Figma into code', 'design to code'. This skill provides critical instructions and steps to the agent on how to correctly implement Figma designs in code and must NOT be skipped."
disable-model-invocation: false
---

# Implement a Figma Design as Code (Design → Code)

Use this skill to turn a Figma design into code in a target codebase. This is the **read-FROM-Figma** direction: pull design context out of Figma with `get_design_context`, then adapt it into the project's real stack. For the reverse direction — building or updating a design *in* Figma from code — use [figma-generate-design](../figma-generate-design/SKILL.md) instead.

This skill owns the **workflow** for design-to-code. Parameter mechanics (nodeId / fileKey / branchKey extraction, URL parsing, `format`/`query` options, response shape) live on the `get_design_context` tool description itself — follow them there.

**Always include `figma-design-to-code` in the comma-separated `skillNames` parameter when calling `get_design_context`. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-design-to-code`).** This is a logging parameter used to track skill usage — it does not affect execution.

## Direction and Scope

- You MUST use this skill for design → code: implementing, translating, or porting a Figma node into code.
- You MUST NOT use this skill to write to Figma.

## Workflow

### Gate Protocol

- Emit exactly three terse gate messages: G1 after design context returns; one combined G2-G4 check before editing; and G5 before finishing. Do not narrate gates between checkpoints.
- A `PASS` MUST cite evidence produced by the required work. You MUST NOT make tool calls solely to emit a gate.
- Gather sufficient evidence for the implementation, not exhaustive evidence. If a requirement is unmet, emit `FAIL`, fix it, then restate the gate.
- You MUST NOT write code until G1 and G2-G4 pass. You MUST NOT finish until G5 passes.
- Gates are self-checks. You MUST NOT change the implementation solely to produce gate evidence.

### 1. Call get_design_context first

- You MUST call `get_design_context` on the target node before writing any code. It is your primary tool — a single call returns reference code, a screenshot, and contextual hints.
- You MUST NOT reach for `get_metadata` or `get_screenshot` as a substitute. Use them only to orient (e.g. picking a node) or to validate, not in place of `get_design_context`.
- If the response is sparse metadata, request only the visible child regions needed to implement the target, preferably in one parallel batch.

#### G1 - Design Context

G1 PASS - `<target node; one-line summary of retrieved HTML-format design regions>`

### 2. Treat the output as a reference, not final code

- The returned code is React + Tailwind enriched with hints. You MUST treat it as a REFERENCE, not as final code to paste verbatim.
- You MUST adapt it to the target project's language, framework, component library, styling system, and conventions. Match the surrounding code.

### 3. Reuse what the project already has

- Before writing new code, You MUST check likely project-owned paths for existing components, layout patterns, and design tokens that match the design intent.
- You MUST reuse the project's existing components and tokens instead of generating new equivalents from scratch.

### 4. Honor the response hints by priority

You MUST apply only hint sources that are present and relevant, in this order — earlier sources override later ones:

1. **Code Connect snippets** → use the mapped codebase component directly.
2. **Component documentation links** → follow them for usage and guidelines.
3. **Design annotations** → follow any designer notes or constraints.
4. **Design tokens (CSS variables)** → map them to the project's token system.
5. **Raw hex / absolute positioning** → loosely structured; lean on the screenshot for intent.

#### G2-G4 - Pre-edit

- **G2:** You MUST identify the target stack and adapt the reference to it.
- **G3:** You MUST search likely project-owned paths and identify what will be reused.
- **G4:** You MUST apply present, relevant hints by priority. You MUST NOT search merely to prove a hint is absent.

G2-G4 PASS - `<stack/path; reuse search/result; present hints/application>`

### 5. Reproduce images and icons faithfully

Images and icons come back as exported assets. Apply these rules as you write the code:

- **Render every icon/image from its exported asset.** Never author, redraw, omit, or replace it with a placeholder or screenshot.
- **Sourcing:** remote asset URLs expire in ~7 days. For committed code, download the exact bytes or use the project's data source.
- **Reuse a project icon component only if its glyph clearly matches**; otherwise use the exported asset.
- **Preserve designed geometry:** You MUST preserve the outer asset box and inner leaf separately, including both dimensions, padding, and aspect ratio.
- Relative fill sizing is allowed only if you verified the container constrains the leaf; otherwise set both leaf dimensions explicitly. You MUST NOT use `auto` for a fixed-size leaf.
- You MUST NOT apply one global size to unlike assets or stretch assets through broad descendant rules.

#### G5 - Asset Fidelity

To pass G5:
- You MUST use the correct source for every asset.
- You MUST verify one representative of each shared sizing rule and every exception preserves intended outer and leaf dimensions.
- You MUST NOT pass on source evidence alone when geometry is unverified.

G5 PASS - `<sources; sizing rules and exceptions; rendered or explicit-dimension evidence>`

Otherwise G5 is `FAIL`. You MUST fix it before finishing.

## Error Recovery

- On a `get_design_context` error, STOP and read the message before retrying.
- If the design URL has no `node-id` (a file-only URL), ask the user for a node-specific URL — You MUST NOT guess or pass an empty `nodeId`.
- On a timeout, retry against a smaller node or selection.
- You MUST NOT silently fall back to hand-writing the screen from the screenshot alone when `get_design_context` can still provide context.
