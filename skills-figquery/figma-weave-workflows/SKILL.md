---
name: figma-weave-workflows
description: "Use BEFORE building, editing or wiring up a Figma Weave workflow graph or AI pipeline with the weave_* MCP tools. Carries the DAG, handle-typing, node-choice and wiring rules those tools assume. NOT for running a built workflow, or for answering questions about what those tools do (weave_run_tool, weave_run_model, weave_list_tools)."
disable-model-invocation: false
---

# Figma Weave workflows

Use this skill to build and modify **Figma Weave** workflows: directed acyclic graphs of nodes for creative AI pipelines, authored through the `weave_*` MCP tools. Each tool's own description carries its parameters, modes, limits and response codes, so take them from there. This skill covers only what those descriptions cannot say.

### Reading the catalog

The catalog is the authoritative "Available Nodes" list and it is NOT static, so fetch it at runtime rather than working from memory of what Weave offers. Three things its responses leave you to work out:

- Edge handle keys (`sourceHandle` / `targetHandle`) are the KEYS of an entry's `outputs` / `inputs`, not the types and not the labels. Use them exactly: a wrong handle name breaks the workflow for the user.
- Read the listing once and hydrate everything you picked in a single follow-up call. The listing costs roughly 6k tokens, so re-fetching it per node buries the rest of the task.
- The listing's `inputs -> outputs` signature carries handle TYPES only, so it is for choosing between node types and nothing more; hydrate the ones you pick before wiring. Names are not unique either, so treat it as a set of ids to choose between, not a lookup.

## How Workflows Work

- A workflow is a directed acyclic graph (DAG) of nodes connected by edges.
- Each node has typed input and output handles.
- Connection rule: an output handle's type must be compatible with the target input handle's accepted types.
- Handle types: image, video, audio, 3D, text, seed, mask, lora, number, boolean, array, any. "any" connects to anything and "mask" is accepted by image and video inputs; otherwise an output's type must match the input's, so image→text is forbidden.
- A model's capabilities are DERIVED from its catalog entry, never printed as tags: what it produces is its `outputs` types, what it accepts is its `inputs` types. So a model whose only inputs are text cannot receive an image, however well its name fits the task, and "connect the image model to the video model" means the image OUTPUT reaching an image-typed INPUT on a model that also produces video. Before writing any edge, check the handle exists on both ends and the types line up.

## Instructions

1. Removals apply before additions within a call, so a node can be replaced and its successor rewired in one batch.
2. A `refId` is yours to choose (`"node_1"`, `"node_2"`) and it dies with the call that created it. Afterwards the node has a real persisted id: use that for later edits.
3. Wire edges with the exact handle keys from the catalog, never guessed. Each input takes ONE incoming connection, and each indexed slot of an expandable handle is its own slot, so `layer_2` is separate from `layer_1`; if an input is already connected in the current graph, do not add another edge to it.
4. Seed the nodes you create with their content, taking the keys from the catalog entry's `settableData` / `settableParams`; anything a node type does not accept is dropped into `ignoredKeys`. What the catalog cannot tell you is which content is worth seeding, and that is what decides whether the workflow runs:
   - A PROMPT node must never be left empty. Given explicit text ("set the prompt to 'a luxury bottle on marble'"), use it verbatim. Given a subject ("a prompt for a luxury perfume bottle"), write a real prompt from it: a few clauses naming subject, framing, lighting and materials, in positive framing. Never echo the user's instruction back as the prompt.
   - PROMPT VARIABLES compose a prompt from upstream nodes: put `{{variableN}}` in the text (N a positive integer from 1) and wire an edge whose `targetHandle` is that exact name in the same call. No other naming works (`{{color}}`, `variable_1`). Every placeholder should be wired, since an unwired one renders literally.
   - An ITERATOR or SELECTOR must carry its actual items; unseeded, it is a broken node the user cannot run.
   - An IMPORT node takes a file the user attached or you uploaded: set `files` to a list with one entry per file: `{ blobstore: { id } }` for an attachment line's `blobstore_id` or a file already in this workflow, and the whole object a `weave_upload_asset` result returned; core fills in the rest. `updateNodes` ignores `files`, so to change an existing import node's file, remove the node and add it back.
   - RESIZE is for symmetrical downscale only, preserving the source aspect ratio ("1080p" → 1920x1080, "4k" → 3840x2160, an upstream "Resize 1024x768" → 1024x768), and tell the user to turn on lockAspectRatio. Never use it to change aspect ratio, enlarge, or skew dimensions independently. For a reframe ("crop to instagram story", "make this square", "9:16"), use an image model's aspect-ratio parameter so the scene is recomposed properly.
   - The PROMPT ENHANCER's "Model instructions" is a param, not node data, so it is easily misplaced and silently dropped. Fill it only when the pipeline's purpose is clear, and omit it entirely when it is not so the node's default applies. 1-3 sentences, second person, describing the enhancer's role rather than the workflow's output: "You enhance user prompts for SVG icon generation, emphasizing geometric simplicity, flat color and clear silhouettes."

## Rules

- Build the fewest nodes that do the job, but from an empty canvas include everything the workflow needs to actually run, prompt and model included.
- When modifying an existing workflow, address nodes by the persisted ids in the current graph, and combine edits, removals and additions into one call (removals land first). Reseeding, retitling or repositioning is an `updateNodes` edit. Replacing a model is the exception that needs remove-then-add, since the node type itself changes: remove the old id, add the new model, and reconnect it to the existing prompt and input nodes by their ids.
- Inserting a node mid-chain changes what every downstream node receives, so re-check the type chain: an image model dropped between a prompt and a text-only video model leaves that model unable to accept its new input, and it has to be replaced too.
- Never leave a required `prompt` input unconnected. Usually a promptV3 feeds it, one per model when prompts differ. In a batch the iterator is the text source instead, either straight into the model or into a promptV3 variable when there is a shared base; either way that is the input's one edge, so do not add a promptV3 beside an iterator already feeding it.
- Never add a `workflow_output` node by default, since model nodes render inline. Add a SINGLE one, fed by the final model, only when the user frames the request as a reusable tool (an "app", "machine", "design tool", "publishable workflow").
- Use `promptV3` for every piece of text the workflow needs, even a short literal. A `string` node stores a static value and cannot take variable connections, so it dead-ends the workflow for the user. Leave existing ones alone.
- Never rename a MODEL node: leave `displayName` unset so the canvas shows the real model name, because labelling a Nano Banana 2 node "Gemini 3.1 Flash" misleads the user about what is running. On non-model nodes a custom name is fine when it adds clarity.
- Set `position` on every node except a new node added into a group: nodes render ~460 wide and up to ~700 tall, so place columns 650 apart by depth, parallel branches 800 apart, and nodes shared across branches in a column of their own, centered on what they feed.
- GROUPS frame the stages of a larger workflow (inputs, generation, post-processing): wrap each stage with `groupNodes`, named for its purpose, with a distinct `color` that fits it; leave a workflow of a few nodes ungrouped.
- DEFAULT IMAGE MODELS, when the user names none. First match wins: cinematic cues (cinematic, color grading, moody / filmic / anamorphic, film grain, teal-and-orange) → **ChatGPT Images 2.0**, or **2.0 Edit** when editing an existing image; cost or speed cues (cheap, save credits, fast, budget) → **Nano Banana 2**; everything else → **Nano Banana Pro**. This covers EVERY unnamed image task, including edits, face edits, inpainting, outpainting, aspect-ratio reframes, background replacement, style transfer and recoloring. Never reach for a specialized model (Flux Pro Outpaint, Qwen Image Edit Plus, Magnific, Krea, SDXL, Seedream V5 Edit) just because its name matches the task verb; those need the user to name them.
- MODEL-AWARE PROMPT STYLE, once the model is picked. Nano Banana / Gemini family: a flowing narrative scene opening on a strong action verb ("Photograph", "Render"), covering subject, action, context, framing, lighting and style, leaning on lens, camera and lighting vocabulary ("shallow depth of field, f/1.8", "1980s film grain", "golden-hour backlight") when style matters. gpt-image family: structured instead, intent first (ad / mockup / portrait / poster), then scene, subject, constraints, with "photorealistic" as the photorealism trigger and explicit locking verbs on edits. Either way, literal text to be rendered into the image goes in double quotes with its font named.

## Common Patterns

- INTEGRATE vs STACK, picked deliberately. `compv3` STACKS: it places layers as-is over `background` with no lighting, perspective or surface integration, which is what you want for layout (storyboards, moodboards, contact sheets, grids) or for rendering literal text over an image. An image-edit model INTEGRATES: it blends new content INTO the source, matching lighting, perspective and texture, which is what "add a logo to this product", "place a watermark", "put text on the billboard", "change the background" and "edit this face" all ask for. Wire the source image into the edit model's `image_1` / `image` input. Never render a base image with an edit model that has no image input wired and then stack the overlay on a `compv3` layer instead: the model cannot integrate what it cannot see, and a stacked layer is not an integrated edit.
- Rendering literal text over an image is a `compv3` job with a `text` layer fed by a promptV3; never hope a model draws legible letters.
- Video from image: the video model must both produce video and accept an image, so wire the image model's output into its image input and give it a promptV3 for motion guidance. An image model is never a substitute for a video model.
- Picker vs. Iterator — make this distinction FIRST when the user mentions a list of values:
  * "dropdown" / "selector" / "pick one of these" → list_selector (workflow runs ONCE with the user's chosen value).
  * "for each" / "try all" / "N variations" → text_iterator (workflow fans out, runs once per item — see Batch pattern below).
  Picking the wrong one breaks intent: a text_iterator when they wanted a picker fans out and runs N times by mistake; a list_selector when they wanted batching runs only once.
- Laying N variations out TOGETHER on one page (storyboard, moodboard, contact sheet, grid) is the one case an iterator cannot serve: `compv3` has distinct slots needing N parallel feeds, while an iterator yields one sequential stream. Build N pickers into N models into one compv3, and tell the user to set picker K to shot K since `selected` can't be set.
- Exhaustive category requests ("all the Y nodes", "each of our X", "etc") mean every catalog entry of that kind, not a sample. A few examples followed by "etc" is not a shortlist.
- Shared base prompt: when variants share a base and differ by modifier, seed the iterator with the MODIFIERS only and give the promptV3 the base text plus `{{variable1}}` ("a luxury perfume bottle on marble, {{variable1}}"), wiring the iterator's option into `variable1`. Never duplicate the base text into every iterator item.
- Batch over a MULTI-STAGE chain keeps the chain's SHAPE constant: ONE iterator → ONE image model → ONE video model, run once per item. Three scenes spelled out individually is the iterator's list, not a reason to build three parallel pipelines.
