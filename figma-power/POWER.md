---
name: "figma"
displayName: "Figma"
description: "Comprehensive Figma integration for implementing designs as production-ready code, connecting Figma components to code via Code Connect, and generating project-specific design system rules. Use when implementing UI from Figma files, connecting components to code, creating design system rules, or when user provides Figma URLs."
keywords: ["figma", "design", "implement", "component", "ui", "code generation", "design system", "code connect", "mapping", "design to code", "rules", "guidelines", "implement design", "implement component", "generate code", "connect component", "design rules", "build design"]
author: "Figma"
---

# Figma

## Overview

This Power provides three core capabilities for working with Figma:

1. **Implement Design** — Translate Figma designs into production-ready code with pixel-perfect accuracy
2. **Code Connect Components** — Connect Figma design components to their code implementations using Code Connect
3. **Create Design System Rules** — Generate project-specific design system rules that guide consistent Figma-to-code workflows

## When to Use This Power

Activate this Power when the user:

- Provides a Figma URL and wants to implement the design as code
- Mentions: implement design, generate code, implement component, build Figma design, build components matching Figma specs
- Mentions: code connect, connect this component to code, map this component, link component to code, create code connect mapping
- Mentions: create design system rules, generate rules for my project, set up design rules, customize design system guidelines
- Wants to establish mappings between Figma designs and code implementations
- Wants to establish project-specific conventions for Figma-to-code workflows

## Available MCP Tools

The Figma MCP server provides these tools:

| Tool | Description |
|------|-------------|
| `get_design_context` | Fetches structured design data (layout, typography, colors, spacing, component structure) for a layer or selection |
| `get_metadata` | Returns a sparse XML representation with basic layer properties like IDs, names, and dimensions |
| `get_screenshot` | Captures a visual screenshot of a Figma selection to preserve layout fidelity |
| `get_variable_defs` | Retrieves variables and styles (colors, spacing, typography) from selections |
| `get_code_connect_suggestions` | Detects and suggests Code Connect mappings between Figma and code components |
| `send_code_connect_mappings` | Confirms Code Connect mappings after suggestions are generated |
| `get_code_connect_map` | Maps Figma node IDs to corresponding code components in your codebase |
| `add_code_connect_map` | Establishes new mappings between Figma elements and code implementations |
| `create_design_system_rules` | Generates rule files that guide agents in translating designs to frontend code |
| `generate_figma_design` | Converts UI descriptions into design layers in Figma files |
| `get_figjam` | Converts FigJam diagrams to XML format including metadata and node screenshots |
| `generate_diagram` | Creates FigJam diagrams from Mermaid syntax (flowcharts, Gantt charts, etc.) |
| `whoami` | Returns authenticated user identity and plan information |

## Steering

Load the appropriate workflow based on the user's intent:

- **Implementing a Figma design as code** → `readPowerSteering("figma", "implement-design.md")`
- **Connecting Figma components to code via Code Connect** → `readPowerSteering("figma", "code-connect-components.md")`
- **Creating design system rules for a project** → `readPowerSteering("figma", "create-design-system-rules.md")`

## Prerequisites

- Figma MCP server must be connected and accessible
- User must provide a Figma URL in the format: `https://figma.com/design/:fileKey/:fileName?node-id=1-2`
- Project should have an established design system or component library (preferred but not required)

## Quick Usage Examples

### Implement a Design

User: "Implement this Figma button: https://figma.com/design/kL9xQn2VwM8pYrTb4ZcHjF/DesignSystem?node-id=42-15"

→ Load `implement-design.md` steering, then follow the 7-step workflow to fetch context, capture screenshot, download assets, translate to project conventions, and validate.

### Connect Components via Code Connect

User: "Connect this Figma button to my code: https://figma.com/design/kL9xQn2VwM8pYrTb4ZcHjF/DesignSystem?node-id=42-15"

→ Load `code-connect-components.md` steering, then follow the 4-step workflow to get suggestions, scan codebase, present matches, and create mappings.

### Create Design System Rules

User: "Create design system rules for my React project"

→ Load `create-design-system-rules.md` steering, then follow the 5-step workflow to run the tool, analyze codebase, generate rules, save to CLAUDE.md, and validate.

## Troubleshooting

### Figma output is truncated

The design is too complex for a single response. Use `get_metadata` to get the node structure, then fetch specific nodes individually with `get_design_context`.

### Assets not loading

Verify the Figma MCP server's assets endpoint is accessible. The server serves assets at `localhost` URLs — use these directly without modification. Do not import new icon packages or create placeholders.

### No published components found (Code Connect)

Code Connect only works with published components. The user needs to publish the component to a team library in Figma first. Code Connect is only available on Organization and Enterprise plans.

### Design token values differ from Figma

When project tokens differ from Figma values, prefer project tokens for consistency but adjust spacing/sizing to maintain visual fidelity.

### Claude isn't following design system rules

Make rules more specific and actionable. Add "IMPORTANT:" prefix to critical rules. Verify rules are saved in the correct configuration file and restart the IDE or MCP client to reload.
