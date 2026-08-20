# mcp-server-guide

Every time the plugin version is bumped, you MUST:

1. Set the same version in every file that lists it — `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.github/plugin/plugin.json`, `gemini-extension.json`, and `server.json` (these must always stay in sync so the latest version is picked up). When a new file carrying a version is added, add it to this list.
2. Set `X-Figma-Plugin-Bundle` in `.mcp.json` to `figma_prod@<version>` — strictly required to be the `plugin.json` version with `.` replaced by `_` (e.g. `2.2.96` → `2_2_96`)
