---
name: figma-generate-design
description: "Use this skill alongside figma-use when the task involves translating an application page, view, or multi-section layout into Figma. Triggers: 'write to Figma', 'create in Figma from code', 'push page to Figma', 'take this app/page and build it in Figma', 'create a screen', 'build a landing page in Figma', 'update the Figma screen to match code', 'convert this modal/dialog/drawer/panel to Figma'. This is the preferred workflow skill whenever the user wants to build or update a full page, modal, dialog, drawer, sidebar, panel, form, dashboard, list, table, card, header, message preview, or other composed product UI in Figma from code or a description—even when the user calls that composed UI a component. Discovers design system components, variables, and styles from Code Connect files, existing screens, and library search, then imports them and assembles views incrementally section-by-section using design system tokens instead of hardcoded values."
disable-model-invocation: false
---
# Build / Update Screens and Views from Design System
**Hard deliverable gate:** Code-to-design output must recreate the UI as editable text, components, icons, and hierarchy.
Treat any screenshot or flattened rendering of the complete UI only as a visual reference: never upload or import it into the deliverable, including as the wrapper fill or a child node, even if it exists in the repository or appears more pixel-accurate. Before completion, inspect the result; if the UI is not primarily represented by editable layers, rebuild it semantically or report failure.

Use this skill to create or update **screens, views, and multi-section UI containers** in Figma by **reusing the published design system** — components, variables, and styles — rather than drawing primitives with hardcoded values. This includes full pages, modals, dialogs, drawers, sidebars, panels, and any composed view with multiple sections. The key insight: the Figma file likely has a published design system with components, color/spacing variables, and text/effect styles that correspond to the codebase's UI components and tokens. Find and use those instead of drawing boxes with hex colors.

**MANDATORY**: You MUST also load [figma-use](../figma-use/SKILL.md) before any `use_figma` call. That skill contains critical rules (color ranges, font loading, etc.) that apply to every script you write.

When available, call `create_session` with `fileKey` and `description` before file reads or edits (create the file first if needed), then pass the returned `sessionId` unchanged to every call that accepts it, including follow-ups and work across files.

**Always include `figma-generate-design` in the comma-separated `skillNames` parameter when calling `use_figma` as part of this skill. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-generate-design`).** This is a logging parameter — it does not affect execution.
## Image and vector assets
Reuse available source, captured, or library assets first. If suitable assets are unavailable, use Figma’s `generate_image` for raster images or `generate_vector_illustration` for editable icons, logos, and illustrations.
## Skill Boundaries

- Use this skill when the deliverable is a **composed Figma view** (new or updated) — including a form, dashboard, list, table, card, header, panel, dialog, message preview, or other multi-section container — built from design system component instances. This applies even when the user calls the composed view a component.
- If the primary deliverable is a **reusable library primitive or foundation** intended for variants, tokens, or publication, use [figma-generate-library](../figma-generate-library/SKILL.md) with [figma-use](../figma-use/SKILL.md) instead.
- If the user wants to write **Code Connect mappings**, switch to [figma-code-connect](../figma-code-connect/SKILL.md).

## Prerequisites

- Figma MCP server must be connected
- The target Figma file must have a published design system with components (or access to a team library)
- User must provide a target Figma file (URL or `fileKey`). If they don't have one yet, invoke `/figma-create-new-file` (or call `create_new_file`) first and reuse the returned file_key. Both `use_figma` and `generate_figma_design` require an existing `fileKey`.
- Source code or description of the screen/view to build/update

## Parallel Workflow with generate_figma_design (Web Apps Only)

When building a screen from a renderable **web app**, run this skill's `use_figma` workflow and `generate_figma_design` in parallel against the **same `fileKey`** (create a file first if needed). Use the capture as a visual/layout reference and to copy `imageHash` values for discrete content images (photos, avatars, logos, icons), then delete the capture once confirmed. **This parallel workflow is MANDATORY when the source contains discrete content images** because `use_figma` cannot fetch external URLs. Never transfer the capture root or any complete-UI screenshot. See [references/web-capture-and-images.md](references/web-capture-and-images.md) for the full parallel workflow and image-transfer scripts.

## Required Workflow

**Follow these steps in order. Do not skip steps.**

> **Required invariants:**
>
> - Complete Code Connect discovery and select the target library before mutating the deliverable. Discovery-only imports and temporary instances are allowed; remove temporary instances immediately.
> - Apply each selected asset where it is imported. If an import fails, try the next applicable exact result before building a manual fallback.

### Step 1: Understand the Deliverable

Before touching Figma, understand what you're building:

1. If building from code, read the relevant source files to understand the structure, sections, and which components are used.
2. Identify the major sections of the view (e.g., for a page: Header, Hero, Content Panels, Footer; for a modal: Title Bar, Form Sections, Action Bar; for a sidebar: Navigation, Content Area, Footer Actions).
3. For each section, list the UI components involved (buttons, inputs, cards, navigation pills, accordions, etc.).
4. **Identify the product's font family from the source. Do not default to Inter.** Find *which* typeface the product uses before writing any script. See [references/discover-product-font.md](references/discover-product-font.md) for where to look (CSS variables, component files) and how to resolve messy Figma font names.
5. **Check whether the view contains any images** (e.g., `<img>`, `<Image>`, background images, product photos, avatars, icons loaded from URLs). If it does and this is a web app, you **must** run the parallel `generate_figma_design` capture workflow — start it immediately alongside Step 2 so the capture runs while you discover components. See "Parallel Workflow with generate_figma_design" above.

### Step 2: Collect Component Keys, Variables, and Styles

You need three things from the design system: **components** (buttons, cards, etc.), **variables** (colors, spacing, radii), and **styles** (text styles, effect styles like shadows). Don't hardcode hex colors or pixel values when design system tokens exist.

#### 2a: Discover components

**2a-i — REQUIRED: Check Code Connect for needed components.** Starting from the component list you built in Step 1, check whether each component has a Code Connect file in the codebase. Code Connect files live next to the component source and are named by platform:

- **TypeScript/JS**: `*.figma.ts`, `*.figma.js`
- **React (parser-based)**: `*.figma.tsx`
- **Kotlin/Compose**: `.kt` files containing `@FigmaConnect`
- **Swift**: `.swift` files containing `FigmaConnect`

For each component you need (e.g., Button, Card, Input), search for its Code Connect file — glob or grep by component name (e.g., `**/Button.figma.tsx`, `**/Card.figma.ts`). Only read files that match components you actually need.

From each matching Code Connect file, extract the Figma component URL, parse `fileKey` and `nodeId` (convert hyphens to colons: `123-456` → `123:456`), and batch-resolve component/component-set keys via `use_figma` against the **library file** (`fileKey` from the URL, not the target file). See [references/discovery-scripts.md](references/discovery-scripts.md#2a-i-resolve-code-connect-component-keys) for the lookup script. Mark resolved components and continue with unresolved ones.

**2a-ii — REQUIRED: Select the library scope, then search and inspect the whole view.** Call `get_libraries`. If the user names one or more libraries, use their exact keys whether they appear in `libraries_added_to_file` or `libraries_available_to_add`. Otherwise search across all libraries in `libraries_added_to_file` together. Pass the selected keys in `includeLibraryKeys` on every search. Only when unresolved gaps have no suitable match, add specifically relevant libraries from `libraries_available_to_add` and retry those unresolved queries; do not broaden to unrelated available libraries. In the first batched `search_design_system` call, include one component query for the requested view or flow alongside queries for unresolved items already known from source or Code Connect inspection. Name the whole-view query by purpose and container (for example, `billing settings drawer`). Inspect the strongest candidate. If it covers two or more requested sections, select it as a foundation; otherwise continue without a whole-view composite.

**2a-iii — Inspect existing screens.** If the target file already contains screens using the same design system, run one read-only `use_figma` pass to inventory an existing frame's component keys, bound variables, and text/effect styles, then reuse that result in 2b and 2c. See [references/discovery-scripts.md](references/discovery-scripts.md#2a-iii-single-pass-existing-screen-inventory) for the inventory script. Match `components` against your unresolved components; Code Connect keys from 2a-i stay authoritative.

**2a-iv — Search only the gaps needed for construction.** After Code Connect, whole-view discovery, and existing-screen inspection, search for unresolved components and tokens the design still needs. Batch independent one-intent entries (`search_design_system` does not apply OR semantics — never pack synonyms into one string), keep `includeLibraryKeys` restricted to the selected library scope, and carry selected keys into the build. Org libraries in `libraries_available_to_add` paginate (20 per page via `offset`). Map every selected key to a section or property, reuse applicable composite descendants, and include component properties (read `componentProperties` on a temporary instance, then remove it). See [references/discovery-scripts.md](references/discovery-scripts.md#2a-iv-get_libraries-and-search_design_system-usage) for `get_libraries`, `search_design_system`, and component map examples.

#### 2b: Discover variables (colors, spacing, radii)

**Inspect existing screens first.** Reuse `variables` from the 2a-iii inventory; for unresolved variables, use `search_design_system` with `{ "entity": "variable", "query": "..." }` entries scoped with `includeLibraryKeys`.

> **WARNING: Two different variable discovery methods — do not confuse them.**
> - `figma.variables.getLocalVariableCollectionsAsync()` returns **only local variables in the current file** — remote/published library variables are invisible to it.
> - `search_design_system` (`entity: "variable"`) searches remote/published library variables.
> - **Never conclude "no variables exist" based solely on `getLocalVariableCollectionsAsync()` returning empty.**

See [references/discovery-scripts.md](references/discovery-scripts.md#2b-variable-search-query-strategy) for variable search query strategies. Import library variables (`remote = true`) with `figma.variables.importVariableByKeyAsync(key)` and local variables with `figma.variables.getVariableByIdAsync(id)`. See [variable-patterns.md](../figma-use/references/variable-patterns.md) for binding patterns.

#### 2c: Discover styles (text styles, effect styles)

Reuse `textStyles` and `effectStyles` from the inventory in 2a-iii or 2b. If no inventory exists, inspect an available screen with the same script. Before hardcoding an unresolved reusable fill/stroke, typography, or effect role, issue a focused `search_design_system` entry with `entity: "style"`, such as "surface", "border", "heading", "body", "shadow", or "elevation". Batch independent entries, but do not exhaustively search roles covered by a selected component or existing-screen style. Search for any styles still missing.

Import library styles with `figma.importStyleByKeyAsync(key)`, then apply with `node.textStyleId = style.id` or `node.effectStyleId = style.id`.

See [text-style-patterns.md](../figma-use/references/text-style-patterns.md) and [effect-style-patterns.md](../figma-use/references/effect-style-patterns.md) for details.

### Step 3: Create the Wrapper Frame

**Do NOT build sections as top-level page children and reparent them later** — moving nodes across `use_figma` calls with `appendChild()` silently fails and produces orphaned frames. Create a mutable `VERTICAL` auto-layout wrapper frame first (sized to the container type, positioned clear of existing content), instantiate any selected whole-view composite inside it (never append children directly to an instance), and return `wrapperId`. See [references/build-scripts.md](references/build-scripts.md#step-3-create-wrapper-frame) for the wrapper creation script.

### Step 4: Customize Covered Sections and Build Missing Sections

**This is the most important step.** Start with the selected composite: customize the descendants it already covers and build only missing sections. Work in retry-safe construction phases, batching related sections when safe. Split only for page-context boundaries, hard-to-recover partial execution, or a targeted retry after a failure—not merely to create a validation checkpoint. At the start of each script, fetch the mutable wrapper frame and import all needed components, variables, and styles in parallel (`Promise.all`), append new sections directly to the wrapper, and set `layoutSizingHorizontal = "FILL"` after appending. See [references/build-scripts.md](references/build-scripts.md#step-4-section-build-template) for the full section build template.

Return the created node IDs plus the relevant counts, names, and bounds from each call — this is your default structural validation. Run a separate structural read only when that evidence is missing or when a relevant mutation has invalidated it. Save the visual pass for Step 5.

#### Override instance text with setProperties()

Component instances ship with placeholder text ("Title", "Heading", "Button"). Use the component property keys from Step 2 to override them with `setProperties()` on both top-level and nested instances (see [component-patterns.md](../figma-use/references/component-patterns.md#overriding-text-in-a-component-instance) and [references/build-scripts.md](references/build-scripts.md#nested-instance-text-override)). Only fall back to direct `node.characters` for text NOT managed by any component property.

#### Read source code defaults carefully

When translating code components to Figma instances, check the component's default prop values in the source code, not just what's explicitly passed. For example, `<Button size="small">Register</Button>` with no variant prop — check the component definition to find `variant = "primary"` as the default. Selecting the wrong variant (e.g., Neutral instead of Primary) produces a visually incorrect result that's easy to miss.

#### What to build manually vs. import from design system

| Build manually | Import from design system |
|----------------|--------------------------|
| Wrapper frame | **Components**: buttons, cards, inputs, nav, etc. |
| Section container frames | **Variables**: colors (fills, strokes), spacing (padding, gap), radii |
| Layout grids (rows, columns) | **Text styles**: heading, body, caption, etc. |
| | **Effect styles**: shadows, blurs, etc. |

**Never hardcode hex colors or pixel spacing** when a design system variable exists. Use `setBoundVariable` for spacing/radii and `setBoundVariableForPaint` for colors. Apply text styles with `node.textStyleId` and effect styles with `node.effectStyleId`.

#### Componentize repeated and reusable elements (required)

Componentization is part of the **default** workflow, not an optional follow-up. Produce a componentized structure on the first pass; do not emit a flat tree of one-off frames and wait for a second "now make it componentized" prompt.

- **Design-system instances are already componentized** (Step 2). Prefer them.
- **For anything the design system does not cover that repeats or maps to a reusable source component, create a local component once with `figma.createComponent()` and place instances**, instead of hand-building N near-identical frames. One source component maps to one Figma main component.

See [references/componentization.md](references/componentization.md) for the build-once-place-instances pattern and code.

#### Icons: import the SVG, never reconstruct from rotated primitives

If the design system exposes an icon component, instance it (`INSTANCE_SWAP`). Otherwise, import the codebase's SVG directly via `figma.createNodeFromSvg(svgString)` (ensure `viewBox` + explicit `width`/`height`, call `icon.resize(size, size)`, and replace `currentColor` or bind fills/strokes to a color variable). Never reconstruct icons from rotated primitives. See [references/build-scripts.md](references/build-scripts.md#icons-import-svg-directly) for the SVG import code and `currentColor` guidance.

### Step 5: Validate the Full View and Transfer Images

Before visual validation, use `use_figma` to read back the wrapper and return its total descendant count, counts for every descendant node type present, and the ID, name, node type, and dimensions of every image-filled node. These counts are evidence, not a numeric pass threshold; do not infer editability from a screenshot or accept token editable nodes layered over a complete-UI raster. If a screenshot or flattened rendering of the complete UI is present anywhere inside the wrapper, remove it and rebuild the UI semantically or report failure; do not claim completion.

After composing all sections, take **one full-view composition screenshot** of the wrapper frame and compare against the source. If it reveals a meaningful visual defect, apply targeted `use_figma` fixes — don't rebuild the entire view — then take **one** post-fix screenshot. The most recent passing screenshot is the final check: do not take an additional unchanged "final" shot, and do not screenshot every section individually.

Before visual fixes, compare the wrapper's instance, style, and bound-variable keys with the Step 2 map. Every applicable selected asset should appear in the output; replace manual equivalents and raw values before finishing.

Inspect the composition screenshot for:
- **Cropped/clipped text** — line heights or frame sizing cutting off descenders, ascenders, or entire lines
- **Overlapping content** — elements stacking on top of each other due to incorrect sizing or missing auto-layout
- Placeholder text still showing ("Title", "Heading", "Button")
- Truncated content from layout sizing bugs
- Wrong component variants (e.g., Neutral vs Primary button)
- **Wrong font family** — text rendered in a different typeface than the product uses (e.g. Inter where the product is SF Pro). The script ran without error, so this is invisible at a glance; assert it explicitly (see "Assert the font family is correct" below)
- **Blank image placeholders** — if images are missing, transfer them from the `generate_figma_design` capture before considering `generate_image` or `generate_vector_illustration` to generate placeholders (see "Transfer images from the generate_figma_design capture" below)

#### Assert the font family is correct

**You MUST explicitly assert that rendered text uses the product font(s) identified in Step 1**, and treat any mismatch as a failed validation. Do not assume a successfully loaded font is the correct font: loading Inter when the product uses SF Pro is a failure even if no errors occur. **If you have a source reference (the running web app, a design mock, or the `generate_figma_design` capture), you MUST also compare rendered screenshots** — a near-miss style within the right family can pass a family check but still look wrong.

See [references/discover-product-font.md](references/discover-product-font.md#verify-the-font-after-building) for the read-back script (which separates free-standing text you fix from design-system-governed text you flag) and the screenshot-comparison steps.

#### Transfer images & generating placeholders

If you ran `generate_figma_design` in parallel, transfer only discrete content `imageHash` fills into your output and delete the capture afterwards. Reuse existing assets before calling `generate_image` / `generate_vector_illustration` (inform the user when Figma AI credits are used; ask before using an alternative provider with `upload_assets`). See [references/web-capture-and-images.md](references/web-capture-and-images.md) for the transfer script and full rules.

### Step 6: Updating an Existing View

When updating rather than creating from scratch:

1. Use `get_metadata` to inspect the existing screen structure and identify which sections need updating.
2. Locate existing nodes by ID or name, swap component instances if changed, update text/variant/layout, remove deprecated sections, and add new ones.
3. Follow the same evidence and screenshot cadence as Steps 4–5 (returned IDs/counts/bounds + one full-view screenshot, plus one post-fix screenshot only if needed).

See [references/build-scripts.md](references/build-scripts.md#step-6-update-existing-view-script) for the parallel instance-swap example.

## Reference Docs

Load these skill references and [figma-use](../figma-use/SKILL.md) references as needed:

- [references/discovery-scripts.md](references/discovery-scripts.md) — Code Connect key lookup, single-pass existing-screen inventory, `get_libraries` / `search_design_system` & variable query examples
- [references/build-scripts.md](references/build-scripts.md) — wrapper creation, parallel section build template, nested text override, SVG icon import, and existing-view update scripts
- [references/web-capture-and-images.md](references/web-capture-and-images.md) — parallel `generate_figma_design` web capture workflow, `imageHash` transfer script, and placeholder asset rules
- [references/componentization.md](references/componentization.md) — build-once-place-instances pattern
- [references/discover-product-font.md](references/discover-product-font.md) — product font discovery and post-build verification
- [references/best-practices.md](references/best-practices.md) — summary of design-system-first best practices

- [component-patterns.md](../figma-use/references/component-patterns.md) — importing by key, finding variants, setProperties, text overrides, working with instances
- [variable-patterns.md](../figma-use/references/variable-patterns.md) — creating/binding variables, importing library variables, scopes, aliasing, discovering existing variables
- [text-style-patterns.md](../figma-use/references/text-style-patterns.md) — creating/applying text styles, importing library text styles, type ramps
- [effect-style-patterns.md](../figma-use/references/effect-style-patterns.md) — creating/applying effect styles (shadows), importing library effect styles
- [gotchas.md](../figma-use/references/gotchas.md) — layout pitfalls (HUG/FILL interactions, counterAxisAlignItems, sizing order), paint/color issues, page context resets

## Error Recovery

Follow [figma-use error recovery](../figma-use/references/validation-and-recovery.md#error-recovery-after-failed-use_figma):

- If `safeToRetryWithoutCanvasRead` is `true`, fix the error and retry.
- If `false`, read the canvas, determine what changed, then make changes.

Because this skill works in retry-safe construction phases, errors are naturally scoped to the current phase. Content from previous successful calls remains intact.

## Best Practices

See [references/best-practices.md](references/best-practices.md) for the complete best-practices checklist (search before building, one-intent queries, design system tokens & instances, componentize by default, retry-safe batches, evidence returns, single composition screenshot, font-family assertion, and convention matching).
