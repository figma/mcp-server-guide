---
name: figma-shaders
description: "**MANDATORY prerequisite** — load this skill before calling `create_shader` or `update_shader`. Use when the user asks to create, author, change, fix, or iterate on a shader effect, shader fill, custom effect, custom fill, or procedural shader in Figma."
disable-model-invocation: false
---

# Create and update Figma shaders

Load this skill before every `create_shader` or `update_shader` call. It covers account-library shader authoring through the Figma MCP server. Reading or applying an existing shader does not require this skill.

Shaders have two kinds:

- `effect` samples and transforms the rendered layer beneath it. Use it for blur, distortion, glow, color grading, pixelation, halftone, or other post-processing.
- `fill` generates pixels without an input raster. Use it for gradients, patterns, noise, textures, and procedural backgrounds.

Do not silently switch kinds during an update. The `kind` passed to `update_shader` must match the existing shader.

## Create workflow

1. Decide whether the request is an effect or fill. Ask only when the visual intent does not resolve the distinction.
2. Resolve `planKey`. Reuse one supplied by the user; otherwise call `whoami`. Use the sole eligible plan automatically, or ask the user to choose when several materially different plans are available.
3. Call `create_shader` once with a concise name, description, selected `kind`, and `planKey`. This creates a starter scaffold, not the requested final shader.
4. Call `get_shader` with the returned `id`, then read every source URI. If the client cannot read MCP resources, call `get_shader` with `includeSource: true` instead. This establishes the runtime imports and the scaffold's fixed metadata contract.
5. Author the complete replacement `main.ts` for the requested result.
6. Call `update_shader` with the returned `id`, the same `kind`, `files: [{ path: "main.ts", content: "..." }]`, and a specific `commitMessage`. Use `metadata` when changing the name or description.

Never stop after `create_shader`: the starter scaffold is only a structural starting point.

## Update workflow

1. Identify the shader with `list_shaders`, then call `get_shader`. Use its `type` (`effect` or `fill`) as the required update kind.
2. Read every source URI returned by `get_shader` before editing. If the client cannot read MCP resources, call it with `includeSource: true`. Treat those files as the current source of truth.
3. Preserve existing controls and behavior unless the user asks to change them.
4. Call `update_shader` with the complete replacement `main.ts` in the `files` array, not a diff or partial fragment. An empty `files` array is valid only for a metadata-only update.

## Authoring rules

- Before writing the `main.ts` replacement, read [Shader source authoring](references/authoring.md). It contains the required module shape, WebGPU lifecycle, supported parameter schemas, effect/fill alpha rules, and WGSL failure checklist.
- Shaders authored through these MCP tools must be static. `update_shader` replaces only `main.ts`; it cannot change the scaffold's `features.json`, where animation and mouse capabilities remain disabled. Do not read time or mouse inputs or claim they are supported. If the user asks for animation, build the static shader only after explaining that its exposed properties can instead be keyframed in Motion mode.
- Expose controls for values users are likely to tune per layer; hardcode implementation details.
- Keep numeric ranges bounded and defaults visually useful.
- For effects, sample the input raster intentionally. For fills, do not assume an input raster exists.
- Treat a non-error `update_shader` result as success. Record the returned version when present; a successful response may omit it.
- On a build error, use the returned compiler output to make the smallest source correction and retry once. If it still fails, surface the error instead of repeatedly rewriting the shader.

## Completion

Report the shader name, kind, and id, plus the returned version when present. Briefly identify the controls or behavior that were added.
