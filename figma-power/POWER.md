---
name: "figma"
displayName: "Figma"
description: "Comprehensive Figma integration for building and updating designs, screens, components, design systems, diagrams, FigJam boards, and Slides directly in Figma via the Plugin API, plus SwiftUI translation and Code Connect mapping. Use when creating or editing anything in a Figma, FigJam, or Slides file from code or a description, building a design system, generating diagrams, or connecting components to code."
keywords: ["figma", "figjam", "slides", "design", "component", "design system", "variables", "tokens", "ui", "use_figma", "plugin api", "create in figma", "build in figma", "write to figma", "push to figma", "code to design", "generate design", "build screen", "build page", "build component", "component library", "theming", "diagram", "flowchart", "sequence diagram", "erd", "gantt", "mermaid", "new figma file", "create file", "swiftui", "swift", "ios", "code connect", "component mapping"]
author: "Figma"
---

# Figma

## Overview

This Power builds and edits content directly in Figma via the Plugin API, and bridges code and design. Capabilities:

### Plugin API — build & edit in Figma
1. **Use the Plugin API** — execute JavaScript in the Figma file context to create/edit/read nodes, variables, components, auto-layout, and fills (`figma-use`; foundational, load it alongside the others)
2. **Generate designs from code** — build or update pages, screens, modals, and multi-section views from code or a description using design-system tokens (`figma-generate-design`)
3. **Build design systems** — create variables/tokens, component libraries, variant sets, and theming from a codebase (`figma-generate-library`)
4. **FigJam** — create and edit FigJam boards (stickies, connectors, sections, tables) via the Plugin API (`figma-use-figjam`)
5. **Slides** — create and edit Figma Slides via the Plugin API (`figma-use-slides`)
6. **Create a new file** — create a blank design, FigJam, or Slides file (`figma-create-new-file`)

### Diagrams
7. **Generate diagrams** — create FigJam diagrams from Mermaid syntax: flowcharts, sequence, ERD, state, gantt, architecture (`figma-generate-diagram`)

### Code ↔ Design
8. **SwiftUI ↔ Figma** — translate a Figma design into SwiftUI, or push SwiftUI views/tokens back into Figma (`figma-swiftui`)
9. **Code Connect** — create and maintain Code Connect templates mapping Figma components to code (`code-connect-components`)

## When to Use This Power

Activate this Power when the user:

- Wants to create, edit, or delete anything in a Figma, FigJam, or Slides file — nodes, variables, components, auto-layout, fills, tokens
- Says: write to Figma, create in Figma from code, push page/screen/component to Figma, build a landing page/modal/dialog/panel in Figma
- Wants to build or update a design system, component library, variables/tokens, or theming (light/dark)
- Wants to create a new blank Figma, FigJam, or Slides file
- Wants to create a diagram — flowchart, sequence, ERD, state machine, gantt, architecture — or mentions Mermaid
- Mentions Swift, SwiftUI, iOS, iPhone, or iPad in either direction (design → SwiftUI or SwiftUI → Figma)
- Mentions Code Connect, component mapping, or `.figma.ts` / `.figma.js` files
- Provides a Figma URL and wants to build on or modify the file

## Available MCP Tools

The Figma MCP server provides these tools:

| Tool | Description |
|------|-------------|
| `use_figma` | Executes JavaScript against the Figma Plugin API in the file context — create/edit/read nodes, variables, components, auto-layout, fills |
| `create_new_file` | Creates a new blank Figma design, FigJam, or Slides file |
| `generate_figma_design` | Converts UI descriptions or code into design layers in a Figma file |
| `generate_diagram` | Creates FigJam diagrams from Mermaid syntax (flowcharts, sequence, ERD, state, gantt) |
| `search_design_system` | Searches a design-system library for components, variables, and styles to reuse |
| `get_design_context` | Fetches structured design data (layout, typography, colors, spacing, component structure) for a selection |
| `get_metadata` | Returns a sparse XML representation with basic layer properties like IDs, names, and dimensions |
| `get_screenshot` | Captures a visual screenshot of a Figma selection to preserve layout fidelity |
| `get_figjam` | Converts FigJam content to XML including metadata and node screenshots |
| `get_code_connect_suggestions` | Detects and suggests Code Connect mappings between Figma and code components |
| `upload_assets` | Uploads image assets into a Figma file |
| `whoami` | Returns authenticated user identity and plan information |

## Steering

Load the appropriate workflow based on the user's intent. `figma-use.md` is foundational — load it alongside any Plugin API write task:

- **Executing Plugin API reads/writes in a Figma file** → `readPowerSteering("figma", "figma-use.md")`
- **Building or updating a page / screen / view from code or a description** → `readPowerSteering("figma", "figma-generate-design.md")` + `readPowerSteering("figma", "figma-use.md")`
- **Building or updating a design system, components, variables, or tokens** → `readPowerSteering("figma", "figma-generate-library.md")` + `readPowerSteering("figma", "figma-use.md")`
- **Working in FigJam via the Plugin API** → `readPowerSteering("figma", "figma-use-figjam.md")` + `readPowerSteering("figma", "figma-use.md")`
- **Working in Slides via the Plugin API** → `readPowerSteering("figma", "figma-use-slides.md")` + `readPowerSteering("figma", "figma-use.md")`
- **Creating a new blank Figma, FigJam, or Slides file** → `readPowerSteering("figma", "figma-create-new-file.md")`
- **Creating a FigJam diagram from Mermaid** → `readPowerSteering("figma", "figma-generate-diagram.md")`
- **Translating between SwiftUI and Figma** → `readPowerSteering("figma", "figma-swiftui.md")` (+ `readPowerSteering("figma", "figma-use.md")` for code → design)
- **Mapping Figma components to code via Code Connect** → `readPowerSteering("figma", "code-connect-components.md")`

## Prerequisites

- Figma MCP server must be connected and accessible
- For file-specific work, the user should provide a Figma URL: `https://figma.com/design/:fileKey/:fileName?node-id=1-2`
- For build-from-code tasks, an established design system or component library improves fidelity (preferred but not required)

## Quick Usage Examples

### Build a screen from code

User: "Take this settings page and build it in Figma."

→ Load `figma-generate-design.md` + `figma-use.md`, discover design-system components/variables, then assemble the view section-by-section using tokens.

### Build a design system

User: "Create a component library with variables and light/dark theming from my codebase."

→ Load `figma-generate-library.md` + `figma-use.md`, then create variable collections, components with variants, and bind tokens.

### Generate a diagram

User: "Draw a sequence diagram of our auth handshake in FigJam."

→ Load `figma-generate-diagram.md`, then produce valid Mermaid and call `generate_diagram`.

### SwiftUI ↔ Figma

User: "Implement this Figma screen in SwiftUI." / "Push my SwiftUI view into Figma."

→ Load `figma-swiftui.md` (+ `figma-use.md` for the code → design direction).

## Troubleshooting

### Figma output is truncated

The design is too complex for a single response. Use `get_metadata` for the node structure, then fetch specific nodes with `get_design_context`.

### Always load `figma-use` before `use_figma`

`use_figma` calls fail in common, hard-to-debug ways without the Plugin API guidance. Load `figma-use.md` before any Plugin API write.

### Assets not loading

Verify the Figma MCP server's assets endpoint is accessible. The server serves assets at `localhost` URLs — use these directly. Do not import new icon packages or create placeholders.

### No published components found (Code Connect)

Code Connect only works with published components. Publish the component to a team library first. Code Connect is only available on Organization and Enterprise plans.

### Design token values differ from Figma

Prefer project tokens for consistency, but adjust spacing/sizing to maintain visual fidelity.
