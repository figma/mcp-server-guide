# Figma MCP Server Guide

The Figma MCP server brings Figma directly into your workflow by providing important design information and context to AI agents generating code from Figma design files.

> [!NOTE]
> Users on the Starter plan or with View or Collab seats on paid plans will be limited to up to 6 tool calls per month.
> <br><br>
> Users with a [Dev or Full seat](https://help.figma.com/hc/en-us/articles/27468498501527-Updates-to-Figma-s-pricing-seats-and-billing-experience#h_01JCPBM8X2MBEXTABDM92HWZG4) seat on the [Professional, Organization, or Enterprise plans](https://help.figma.com/hc/en-us/articles/360040328273-Figma-plans-and-features) have per minute rate limits, which follow the same limits as the Tier 1 [Figma REST API](https://developers.figma.com/docs/rest-api/rate-limits/). As with Figma’s REST API, Figma reserves the right to change rate limits.

For the complete set of Figma MCP server docs, see our [developer documentation](https://developers.figma.com/docs/figma-mcp-server/).

## Features

- **Generate code from selected frames**

  Select a Figma frame and turn it into code. Great for product teams building new flows or iterating on app features.

- **Extract design context**

  Pull in variables, components, and layout data directly into your IDE. This is especially useful for design systems and component-based workflows.

- **Code smarter with Code Connect**

  Boost output quality by reusing your actual components. Code Connect keeps your generated code consistent with your codebase.

  [Learn more about Code Connect →](https://help.figma.com/hc/en-us/articles/23920389749655-Code-Connect)

## Installation & Setup

### Step 1: Enabling the MCP server

Figma provides two ways to use the MCP server. Remotely using our hosted server, and locally using Figma's desktop app.

If you want to use our remote server, there's nothing to enable, it's already available! To get the local desktop server set up, you'll need to follow the steps below.

#### Enabling the desktop server

1. Open the [Figma desktop app](https://www.figma.com/downloads/) and make sure you've [updated to the latest version](https://help.figma.com/hc/en-us/articles/5601429983767-Guide-to-the-Figma-desktop-app#h_01HE5QD60DG6FEEDTZVJYM82QW).
2. Create or open a Figma Design file.
3. In the toolbar at the bottom, toggle to [Dev Mode](https://help.figma.com/hc/en-us/articles/15023124644247-Guide-to-Dev-Mode) or use the keyboard shortcut <kbd>Shift</kbd><kbd>D</kbd>.
4. In the **MCP server** section of the inspect panel, click **Enable desktop MCP server**.

<img width="500" height="251" alt="enable-desktop-mcp-server" src="https://github.com/user-attachments/assets/964c7665-1aaa-42e5-ad45-e87ea68d4bdd" />

You should see a confirmation message at the bottom of the screen letting you know the server is enabled and running.

> [!TIP]
> The server runs locally at this location:
>
> ```bash
> http://127.0.0.1:3845/mcp
> ```
>
> Keep this address handy for your configuration file in the next step.

### Step 2: Set up your MCP client

Different MCP clients require slightly different setups to get connected to your MCP server. Follow the instructions below for your specific client to add the Figma MCP server.

#### VS Code

1. Use the shortcut `⌘ Shift P` to search for `MCP:Add Server`.
2. Select `HTTP`.
3. Copy the correct server url from below, and paste the server url in the search bar. Then hit `Enter`.

   Remote server url - `https://mcp.figma.com/mcp`

   Local server url - `http://127.0.0.1:3845/mcp`

4. When you're prompted for a server ID, enter one of the following:

   - `figma` for the remote MCP server
   - `figma-desktop` for the desktop MCP server

5. Select whether you want to add this server globally or only for the current workspace. Once confirmed, you'll see a configuration like this in your `mcp.json` file:

<table>
<tr><th>Using the remote MCP Server</th><th>Using the desktop MCP Server</th></tr>
<tr>
<td>

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

</td>
<td>

```json
{
  "servers": {
    "figma-desktop": {
      "type": "http",
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

</td>
</tr>
</table>

6. Open the chat toolbar using `⌥⌘B` or `⌃⌘I` and switch to **Agent** mode.
7. With the chat open, type in `#get_design_context` to confirm that the Figma MCP server tools are available. If no tools are listed, restart the Figma desktop app and VS Code.

> [!NOTE]
> You must have [GitHub Copilot](https://github.com/features/copilot) enabled on your account to use MCP in VS Code.
>
> For more information, see [VS Code's official documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers).

#### Cursor

1. Open **Cursor → Settings → Cursor Settings**.
2. Go to the **MCP** tab.
3. Click **+ Add new global MCP server**.
4. Enter the following configuration and save:

<table>
<tr><th>Using the remote MCP Server</th><th>Using the desktop MCP Server</th></tr>
<tr>
<td>

```json
{
  "mcpServers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

</td>
<td>

```json
{
  "mcpServers": {
    "figma-desktop": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

</td>
</tr>
</table>

For more information, see [Cursor's official documentation](https://docs.cursor.com/context/model-context-protocol).

#### Claude Code

1. Open your terminal and run:

<table>
<tr><th>Using the remote MCP Server</th><th>Using the desktop MCP Server</th></tr>
<tr>
<td>

```bash
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

</td>
<td>

```bash
claude mcp add --transport http figma-desktop http://127.0.0.1:3845/mcp
```

</td>
</tr>
</table>

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

#### Claude Code (Plugin Installation)

You can also set up the Figma MCP server by installing the Figma Plugin for Claude Code, which includes both remote and desktop MCP server settings as well as Agent Skills for common workflows.

Run the following command to install the plugin from Anthropic's official plugin marketplace.

```bash
claude plugin install figma@claude-plugins-official
```

Learn more about Anthropic's [Claude Code Plugins](https://claude.com/blog/claude-code-plugins) and [Agent Skills](https://claude.com/blog/skills).

#### Other editors

Other code editors and tools that support Streamable HTTP can also connect to the Figma MCP server.

If you're using a different editor or tool, check its documentation to confirm it supports Streamable HTTP based communication. If it does, you can manually add the Figma MCP server using this configuration:

<table>
<tr><th>Using the remote MCP Server</th><th>Using the desktop MCP Server</th></tr>
<tr>
<td>

```json
{
  "mcpServers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

</td>
<td>

```json
{
  "mcpServers": {
    "figma-desktop": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

</td>
</tr>
</table>

## Prompting your MCP client

The Figma MCP server introduces a set of tools that help LLMs translate designs in Figma. Once connected, you can prompt your MCP client to access a specific design node.

There are two ways to provide Figma design context to your AI client:

### Link-based

1. Copy the link to a frame or layer in Figma.
2. Prompt your client to help you implement the design at the selected URL.

<img src="https://help.figma.com/hc/article_attachments/34049303807895" width="300" />

> [!NOTE]
> Your client won't be able to navigate to the selected URL, but it will extract the node-id that is required for the MCP server to identify which object to return information about.

### Selection-based (desktop only)

1. Select a frame or layer inside Figma using the desktop app.
2. Prompt your client to help you implement your current selection.

   <img src="https://help.figma.com/hc/article_attachments/32209690330263" width="300" />

## Tools and usage suggestions

### `get_design_context`

**Supported file types:** Figma Design, Figma Make

Use this to get design context for your Figma selection using the MCP server. The default output is **React + Tailwind**, but you can customize this through your prompts:

- Change the framework

  - "Generate my Figma selection in Vue."
  - "Generate my Figma selection in plain HTML + CSS."
  - "Generate my Figma selection in iOS."

- Use your components

  - "Generate my Figma selection using components from src/components/ui"
  - "Generate my Figma selection using components from src/ui and style with Tailwind"

  You can paste links or select the frame or component in Figma before prompting.

> [!NOTE]
> Selection-based prompting only works with the desktop MCP server. The remote server requires a link to a frame or layer to extract context.

[Learn how to set up Code Connect for better component reuse →](https://help.figma.com/hc/en-us/articles/23920389749655-Code-Connect)

### `get_variable_defs`

**Supported file types:** Figma Design

Returns variables and styles used in your selection—like colors, spacing, and typography.

- List all tokens used
  - "Get the variables used in my Figma selection."
- Focus on a specific type
  - "What color and spacing variables are used in my Figma selection?"
- Get both names and values
  - "List the variable names and their values used in my Figma selection."

### `get_code_connect_map`

**Supported file types:** Figma Design

Retrieves a mapping between Figma node IDs and their corresponding code components in your codebase. Specifically, it returns an object where each key is a Figma node ID, and the value contains:

- `codeConnectSrc`: The location of the component in your codebase (e.g., a file path or URL).
- `codeConnectName`: The name of the component in your codebase.

This mapping is used to connect Figma design elements directly to their React (or other framework) implementations, enabling seamless design-to-code workflows and ensuring that the correct components are used for each part of the design. If a Figma node is connected to a code component, this function helps you identify and use the exact component in your project.

### `get_screenshot`

**Supported file types:** Figma Design, FigJam

This takes a screenshot of your selection to preserve layout fidelity. Keep this on unless you're managing token limits.

### `create_design_system_rules`

**Supported file types:** No file context required

Use this tool to create a rule file that gives agents the context they need to generate high-quality front end code. Rule files help align output with your design system and tech stack, improving accuracy and ensuring code is tailored to your needs.

After running the tool, save the output to the appropriate `rules/` or `instructions/` directory so your agent can access it during code generation.

### `get_metadata`

**Supported file types:** Figma Design

Returns an XML representation of your selection containing basic properties such as layer IDs, names, types, position and sizes. You can use `get_design_context` on the resulting outline to retrieve only the styling information of the design you need.

This is useful for very large designs where `get_design_context` produces output with a large context size. It also works with multiple selections or the whole page if nothing is selected.

### `get_figjam`

**Supported file types:** FigJam

This tool returns metadata for FigJam diagrams in XML format, similar to `get_metadata`. In addition to returning basic properties like layer IDs, names, types, positions, and sizes, it also includes screenshots of the nodes.

### `whoami` (remote only)

**Supported file types:** No file context required

This tool returns the identity of the user that's authenticated to Figma, including:

- The user's email address
- All of the plans the user belongs to
- The seat type the user has on each plan

## Desktop Figma MCP server settings

These are additional settings you can toggle under Preferences and use with the MCP client.

**Image settings**

- **Use local image server**: Hosts images on a local server with URLs like `http://localhost:3845/assets/89f254d1a998c9a6d1d324d43c73539c3993b16e.png`.

- **Download**: Saves images directly to disk.

- **(DEPRECATED) Use placeholder images:** Skips image extraction and adds generic placeholders instead - helpful if you prefer swapping them manually in code.

**Enable Code Connect**

Includes Code Connect mappings in the response, so the generated code can reuse components from your connected codebase where possible.

> As you use the Figma MCP server, you may see a popup inside Figma asking you for feedback. To give us feedback, [please use this form](https://form.asana.com/?k=jMdFq_1SBUOyh8_k3q76QA&d=10497086658021).

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
