# Figma MCP Server Guide

The Figma MCP server brings Figma directly into your workflow by providing important design information and context to AI agents generating code from Figma design files.

> [!NOTE]
> Rate limits apply to Figma MCP server tools that read data from Figma. Some tools, such as those that write to Figma files, are exempt from the rate limits.
> <br><br>
> Users on the Starter plan or with View or Collab seats on paid plans will be limited to up to 6 tool calls per month.
> <br><br>
> Users with a [Dev or Full seat](https://help.figma.com/hc/en-us/articles/27468498501527-Updates-to-Figma-s-pricing-seats-and-billing-experience#h_01JCPBM8X2MBEXTABDM92HWZG4) on the [Professional, Organization, or Enterprise plans](https://help.figma.com/hc/en-us/articles/360040328273-Figma-plans-and-features) have per minute rate limits, which follow the same limits as the Tier 1 [Figma REST API](https://developers.figma.com/docs/rest-api/rate-limits/). As with Figma’s REST API, Figma reserves the right to change rate limits.

For the complete set of Figma MCP server docs, see our [developer documentation](https://developers.figma.com/docs/figma-mcp-server/). By using the Figma MCP server and the related resources (including these skills), you agree to the [Figma Developer Terms](https://www.figma.com/legal/developer-terms/). These skills are currently available as a Beta feature.

## Features

- **Write to the canvas** (remote server only): Create and modify native Figma content directly from your MCP client. With the right skills, agents can build and update frames, components, variables, and auto layout in your Figma files using your design system as the source of truth.

    **Note:** We're quickly improving how Figma supports AI agents. The write to canvas feature will eventually be a usage-based paid feature, but is currently available for free during the beta period.

- **Generate code from selected frames**

  Select a Figma frame and turn it into code. Great for product teams building new flows or iterating on app features.

- **Extract design context**

  Pull in variables, components, and layout data directly into your IDE. This is especially useful for design systems and component-based workflows.

- **Code smarter with Code Connect**

  Boost output quality by reusing your actual components. Code Connect keeps your generated code consistent with your codebase.

  [Learn more about Code Connect →](https://help.figma.com/hc/en-us/articles/23920389749655-Code-Connect)

- **Generate Figma designs from web pages** *(rolling out)*

  Capture, import, or convert a web page into a Figma design directly from your AI coding agent.

## Installation & Setup

### Connect to the Figma MCP server

Different MCP clients require slightly different setups. Follow the instructions below for your specific client to connect to the Figma MCP server.

#### VS Code

1. Use the shortcut `⌘ Shift P` to search for `MCP:Add Server`.
2. Select `HTTP`.
3. Paste the server url `https://mcp.figma.com/mcp` in the search bar. Then hit `Enter`.
4. When you're prompted for a server ID, enter `figma`.
5. Select whether you want to add this server globally or only for the current workspace. Once confirmed, you'll see a configuration like this in your `mcp.json` file:

```json
{
  "servers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

6. Open the chat toolbar using `⌥⌘B` or `⌃⌘I` and switch to **Agent** mode.
7. With the chat open, type in `#get_design_context` to confirm that the Figma MCP server tools are available. If no tools are listed, restart VS Code.

> [!NOTE]
> You must have [GitHub Copilot](https://github.com/features/copilot) enabled on your account to use MCP in VS Code.
>
> For more information, see [VS Code's official documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

#### Cursor

The recommended way to set up the Figma MCP server in Cursor is by installing the Figma Plugin, which includes MCP server settings as well as Agent Skills for common workflows.

Install the plugin by typing the following command in Cursor's agent chat:

```
/add-plugin figma
```

The plugin includes:

- MCP server configuration for the Figma MCP server
- Skills for implementing designs, connecting components via Code Connect, and creating design system rules
- Rules for proper asset handling from the Figma MCP server

<details>
<summary>Manual setup</summary>

1. Open **Cursor → Settings → Cursor Settings**.
2. Go to the **MCP** tab.
3. Click **+ Add new global MCP server**.
4. Enter the following configuration and save:

```json
{
  "mcpServers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

For more information, see [Cursor's official documentation](https://docs.cursor.com/context/model-context-protocol).

</details>

#### Claude Code

The recommended way to set up the Figma MCP server in Claude Code is by installing the Figma Plugin, which includes MCP server settings as well as Agent Skills for common workflows.

Run the following command to install the plugin from Anthropic's official plugin marketplace.

```bash
claude plugin install figma@claude-plugins-official
```

Learn more about Anthropic's [Claude Code Plugins](https://claude.com/blog/claude-code-plugins) and [Agent Skills](https://claude.com/blog/skills).

<details>
<summary>Manual setup</summary>

1. Open your terminal and run:

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

2. Use the following commands to check MCP settings and manage servers:

- List all configured servers
  ```bash
  claude mcp list
  ```
- Get details for a specific server
  ```bash
  claude mcp get my-server
  ```
- Remove a server
  ```bash
  claude mcp remove my-server
  ```

For more information, see [Anthropic's official documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/tutorials#set-up-model-context-protocol-mcp).

</details>

#### Gemini CLI

Install the Figma extension for Gemini CLI by running the following command:

```bash
gemini extensions install https://github.com/figma/mcp-server-guide
```

Once installed, authenticate with Figma by running `gemini` and then executing the following command within the CLI:

```
/mcp auth figma
```

To uninstall the extension:

```bash
gemini extensions uninstall figma
```

#### Other editors

Other code editors and tools that support Streamable HTTP can also connect to the Figma MCP server.

If you're using a different editor or tool, check its documentation to confirm it supports Streamable HTTP based communication. If it does, you can manually add the Figma MCP server using this configuration:

```json
{
  "mcpServers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

## Prompting your MCP client

The Figma MCP server introduces a set of tools that help LLMs translate designs in Figma. Once connected, you can prompt your MCP client to access a specific design node.

To provide Figma design context to your AI client:

1. Copy the link to a frame or layer in Figma.
2. Prompt your client to help you implement the design at the selected URL.

<img src="https://help.figma.com/hc/article_attachments/34049303807895" width="300" />

> [!NOTE]
> Your client won't be able to navigate to the selected URL, but it will extract the node-id that is required for the MCP server to identify which object to return information about.

## Tools and skills

Figma maintains a list of tools provided by the Figma MCP server in the [developer documentation](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/). 

You can also learn more about the skills included with the Figma plugin for [supported agents](https://help.figma.com/hc/en-us/articles/32132100833559#h_01K25F7RBRZKCATVJHNXCS6KXW) in the [Figma Help Center](https://help.figma.com/hc/en-us/articles/39166810751895). Depending on the agent, you may also see the terms `connector`, `extension`, or `power`; these include the same set of skills.

# MCP best practices

The quality of the generated code depends on several factors. Some controlled by you, and some by the tools you're using. Here are some suggestions for clean, consistent output.

## Structure your Figma file for better code

Provide the best context for your design intent, so the MCP and your AI assistant can generate code that's clear, consistent, and aligned with your system.

- **Use components** for anything reused (buttons, cards, inputs, etc.)
- **Link components to your codebase** via Code Connect. This is the best way to get consistent component reuse in code. Without it, the model is guessing.
- **Use variables** for spacing, color, radius, and typography.
- **Name layers semantically** (e.g. `CardContainer`, not `Group 5`)
- **Use Auto layout** to communicate responsive intent.

> [!TIP]
> Resize the frame in Figma to check that it behaves as expected before generating code.

- **Use annotations and dev resources** to convey design intent that's hard to capture from visuals alone, like how something should behave, align, or respond.

## Write effective prompts to guide the AI

MCP gives your AI assistant structured Figma data, but your prompt drives the result. Good prompts can:

- Align the result with your framework or styling system
- Follow file structure and naming conventions
- Add code to specific paths (e.g. `src/components/ui`)
- Add or modify code in existing files instead of creating new ones
- Follow specific layout systems (e.g. grid, flexbox, absolute)

**Examples:**

- "Generate iOS SwiftUI code from this frame"
- "Use Chakra UI for this layout"
- "Use `src/components/ui` components"
- "Add this to `src/components/marketing/PricingCard.tsx`"
- "Use our `Stack` layout component"

Think of prompts like a brief to a teammate. Clear intent leads to better results.

## Trigger specific tools when needed

The MCP supports different tools, and each one provides your AI assistant with a different kind of structured context. Sometimes, the assistant doesn't automatically pick the right one, especially as more tools become available. If results are off, try being explicit in your prompt.

- **get_design_context** provides a structured **React + Tailwind** representation of your Figma selection. This is a starting point that your AI assistant can translate into any framework or code style, depending on your prompt.
- **get_variable_defs** extracts the variables and styles used in your selection (color, spacing, typography, etc). This helps the model reference your tokens directly in the generated code.

For example, if you're getting raw code instead of tokens, try something like:

- "Get the variable names and values used in this frame."

## Add custom rules

Set project-level guidance to keep output consistent—just like onboarding notes for a new developer. These are things like:

- Preferred layout primitives
- File organization
- Naming patterns
- What not to hardcode

You can provide this in whatever format your MCP client uses for instruction files.

**Examples:**

#### Ensure consistently good output

```yaml
## Figma MCP Integration Rules
These rules define how to translate Figma inputs into code for this project and must be followed for every Figma-driven change.

### Required flow (do not skip)
1. Run get_design_context first to fetch the structured representation for the exact node(s).
2. If the response is too large or truncated, run get_metadata to get the high‑level node map and then re‑fetch only the required node(s) with get_design_context.
3. Run get_screenshot for a visual reference of the node variant being implemented.
4. Only after you have both get_design_context and get_screenshot, download any assets needed and start implementation.
5. Translate the output (usually React + Tailwind) into this project's conventions, styles and framework.  Reuse the project's color tokens, components, and typography wherever possible.
6. Validate against Figma for 1:1 look and behavior before marking complete.

### Implementation rules
- Treat the Figma MCP output (React + Tailwind) as a representation of design and behavior, not as final code style.
- Replace Tailwind utility classes with the project's preferred utilities/design‑system tokens when applicable.
- Reuse existing components (e.g., buttons, inputs, typography, icon wrappers) instead of duplicating functionality.
- Use the project's color system, typography scale, and spacing tokens consistently.
- Respect existing routing, state management, and data‑fetch patterns already adopted in the repo.
- Strive for 1:1 visual parity with the Figma design. When conflicts arise, prefer design‑system tokens and adjust spacing or sizes minimally to match visuals.
- Validate the final UI against the Figma screenshot for both look and behavior.
```

#### Cursor

```yaml
---
description: Figma MCP server rules
globs:
alwaysApply: true
---
- The Figma MCP server provides an assets endpoint which can serve image and SVG assets
- IMPORTANT: If the Figma MCP server returns a localhost source for an image or an SVG, use that image or SVG source directly
- IMPORTANT: DO NOT import/add new icon packages, all the assets should be in the Figma payload
- IMPORTANT: do NOT use or create placeholders if a localhost source is provided
```

#### Claude Code

```markdown
# MCP Servers

## Figma MCP server rules

- The Figma MCP server provides an assets endpoint which can serve image and SVG assets
- IMPORTANT: If the Figma MCP server returns a localhost source for an image or an SVG, use that image or SVG source directly
- IMPORTANT: DO NOT import/add new icon packages, all the assets should be in the Figma payload
- IMPORTANT: do NOT use or create placeholders if a localhost source is provided
```

#### General quality rules

```
- IMPORTANT: Always use components from `/path_to_your_design_system` when possible
- Prioritize Figma fidelity to match designs exactly
- Avoid hardcoded values, use design tokens from Figma where available
- Follow WCAG requirements for accessibility
- Add component documentation
- Place UI components in `/path_to_your_design_system`; avoid inline styles unless truly necessary
```

Adding these once can dramatically reduce the need for repetitive prompting and ensures that teammates or agents consistently follow the same expectations.

Be sure to check your IDE or MCP client's documentation for how to structure rules, and experiment to find what works best for your team. Clear, consistent guidance often leads to better, more reusable code with less back-and-forth.

### Break down large selections

Break screens into smaller parts (like components or logical chunks) for faster, more reliable results.

Large selections can slow the tools down, cause errors, or result in incomplete responses, especially when there's too much context for the model to process. Instead:

1. Generate code for smaller sections or individual components (e.g. Card, Header, Sidebar)
2. If it feels slow or stuck, reduce your selection size

This helps keep the context manageable and results more predictable, both for you and for the model.

If something in the output doesn't look quite right, it usually helps to revisit the basics: how the Figma file is structured, how the prompt is written, and what context is being sent. Following the best practices above can make a big difference, and often leads to more consistent, reusable code.

## Bringing Make context to your agent

The Make + MCP integration makes it easier to take prototypes from **design to production**. By connecting Make projects directly to your agent via MCP, you can extract resources and reuse them in your codebase. This reduces friction when extending prototypes into real applications, and ensures that design intent is faithfully carried through to implementation.

With this integration, you can:

- **Fetch project context** directly from Make (individual files or the whole project)
- **Prompt to use existing code components** instead of starting from scratch
- **Extend prototypes with real data** to validate and productionize designs faster

### How it works

> [!NOTE]
> This integration leverages the MCP **resources capability**, which allows your agent to fetch context directly from Make projects. It is available only on clients that support MCP resources.

#### Steps to fetch resources from Make

1. **Prompt your agent to fetch context** by providing a valid Make link
2. **Receive a list of available files** from your Make project
3. **Download the files you want to fetch** when prompted

### Example workflow

**Goal:** Implement a popup component in your production codebase that matches the design and behavior defined in Make.

1. Share your Make project link with your agent.
2. Prompt the agent: _"I want to get the popup component behavior and styles from this Make file and implement it using my popup component."_

Your agent will fetch the relevant context from Make and guide you in extending your existing popup component with the prototype's functionality and styles.

# Icon Guidelines

See the [Figma Brand Usage Guidelines](https://www.figma.com/using-the-figma-brand) for displaying any icons contained in this repo.
