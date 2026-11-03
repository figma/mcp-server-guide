---
name: figma-code-workflows
description: Import or upload local HTML or project files into Figma, choose editable Design frames, runnable Code Layers or standalone Code (also known as Make), and repair imported previews. Use only when the user explicitly names editable Design layers, a runnable Code Layer, or a standalone Code/Make file, or supplies a Figma file key/link as the import destination. Generic code or code-component requests need output clarification before using this workflow.
disable-model-invocation: false
---

# Import a project into Figma

Only use this workflow for an explicitly requested Figma output (standalone Code/Make, runnable Code Layer, or editable Design layers), or a Figma file key/link given as its destination. Generic “make a code project” or “create a code component” requests, and Figma Code/Make names alone, do not specify that output. If output intent is unclear, ask whether the user wants local code or a Figma output, then wait before starting this workflow.

Preserve the user's project. Use each tool's current description and schema for prerequisites and parameters.

Keep the user updated at the main stages: preparing and validating the project, uploading the archive, and completing the import in Figma. Report pending imports, recovery work and blockers as they occur; do not describe an unconfirmed stage as complete.

## 1. Choose the output and destination

Identify the user's intended output, then load the appropriate skill according to the table below. If the output is unclear, ask the user before proceeding.

| Input | User's requested output | Next action |
| --- | --- | --- |
| Running app or static HTML | Unspecified — just put/import it in Figma | Ask **"Editable design layers or a code layer?" and end your turn.** Wait for the answer. |
| Running app | Editable Design layers | Load `figma-generate-design`, then call `generate_figma_design` in a Design file. |
| Static HTML | Editable Design layers | Call `html_to_figma` in a Design file. |
| Running app | Runnable Code Layer or standalone Code/Make | Continue with this skill and call `send_code_to_figma`. |
| Static HTML | Runnable Code Layer or standalone Code/Make | Continue with this skill and call `send_code_to_figma`. |

An HTML project with working buttons is still ambiguous when the user has not chosen the output. A Design link only chooses the destination, not the output.

Before choosing a runnable destination, call `whoami`. Only choose or import a Design Code Layer when `whoami.code_layers_enabled` is true; otherwise use standalone Code/Make, or explain the limitation and ask before changing an explicitly supplied Design destination.

Honor an explicit code-layer or standalone request before applying the screen-count heuristic. For runnable code with a Design link, use a Code Layer. For a standalone Code link, use standalone. With no destination or explicit code-layer/standalone choice, estimate screens: fewer than 10 or unknown → Code Layer; 10 or more → standalone. Never ask Code Layer versus standalone or ask the user to count screens. Explicit destinations and links take precedence after the output choice.

Use the supplied file URL. If a new file is needed, use `create_new_file` with the selected destination type and the user's chosen plan.

Create a Design file for a requested code layer when no destination is provided.

Keep the confirmed output choice fixed; do not ask the user to choose again after creating the file.

For editable Design layers, follow the selected tool's instructions: `generate_figma_design` captures the running app's rendered page; `html_to_figma` converts a self-contained static HTML document. Inspect the resulting layers and share the Design link. Continue below only for runnable code output.

## 2. Follow the import response

Call `send_code_to_figma` with the selected local source and destination using its current schema. Follow the returned preparation and archive instructions; preserve the app and validate locally before uploading when instructed.

Follow each response's instructions and returned `nextStep` exactly for preparation, validation, upload, pending imports and setup recovery. Complete the returned prerequisites before advancing and pass complete continuation arguments unchanged. Do not invent a missing recovery step. When no `nextStep` is present, follow the response's instructions and the tool's current description.

Finish with the returned file/layer link and report only the import and preview outcomes established by the result.
