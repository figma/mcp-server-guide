# Design System Builder — Figma MCP Skill

Build professional-grade design systems in Figma that match code. This skill orchestrates multi-phase workflows across 20–100+ `use_figma` calls, enforcing quality patterns from real-world design systems (Material 3, Polaris, Figma UI3, Simple DS).

**Prerequisites**: The `figma-use` skill MUST also be loaded for every `use_figma` call. It provides Plugin API syntax rules (return pattern, page reset, ID return, font loading, color range). This skill provides design system domain knowledge and workflow orchestration.

**Always include `figma-generate-library` in the comma-separated `skillNames` parameter when calling `use_figma` as part of this skill. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-generate-library`).** This is a logging parameter — it does not affect execution.

---

## 1. The One Rule That Matters Most

**This is NEVER a one-shot task.** Building a design system requires 20–100+ `use_figma` calls across multiple phases, with mandatory user checkpoints between them. Any attempt to create everything in one call WILL produce broken, incomplete, or unrecoverable results. Break every operation to the smallest useful unit, validate, get feedback, proceed.

---

## 2. Mandatory Workflow

Every design system build follows this phase order. Skipping or reordering phases causes structural failures that are expensive to undo.

```
Phase 0: DISCOVERY (always first — no use_figma writes yet)
  0a. Analyze codebase → extract tokens, components, naming conventions
  0b. Inspect Figma file → pages, variables, components, styles, existing conventions
  0c. Search subscribed libraries → use search_design_system for reusable assets
  0d. Lock v1 scope → agree on exact token set + component list before any creation
  0e. Map code → Figma → resolve conflicts (code and Figma disagree = ask user)
  ✋ USER CHECKPOINT: present full plan, await explicit approval

Phase 1: FOUNDATIONS (tokens first — always before components)
  1a. Create variable collections and modes
  1b. Create primitive variables (raw values, 1 mode)
  1c. Create semantic variables (aliased to primitives, mode-aware)
  1d. Set scopes on ALL variables
  1e. Set code syntax on ALL variables
  1f. Create effect styles (shadows) and text styles (typography)
  → Exit criteria: every token from the agreed plan exists, all scopes set, all code syntax set
  ✋ USER CHECKPOINT: show variable summary, await approval

Phase 2: FILE STRUCTURE (before components)
  2a. Create page skeleton: Cover → Getting Started → Foundations → --- → Components → --- → Utilities
  2b. Create foundations documentation pages (color swatches, type specimens, spacing bars)
  → Exit criteria: all planned pages exist, foundations docs are navigable
  ✋ USER CHECKPOINT: show page list + screenshot, await approval

Phase 3: COMPONENTS (one at a time — never batch)
  For EACH component (in dependency order: atoms before molecules):
    3a. Create dedicated page
    3b. Build base component with auto-layout + full variable bindings
    3c. Create all variant combinations (combineAsVariants + grid layout)
    3d. Add component properties (TEXT, BOOLEAN, INSTANCE_SWAP)
    3e. Link properties to child nodes
    3f. Add page documentation (title, description, usage notes)
    3g. Validate: get_metadata (structure) + get_screenshot (visual)
    3h. Optional: lightweight Code Connect mapping while context is fresh
    → Exit criteria: variant count correct, all bindings verified, screenshot looks right
    ✋ USER CHECKPOINT per component: show screenshot, await approval before next component

Phase 4: INTEGRATION + QA (final pass)
  4a. Finalize all Code Connect mappings
  4b. Accessibility audit (contrast, min touch targets, focus visibility)
  4c. Naming audit (no duplicates, no unnamed nodes, consistent casing)
  4d. Unresolved bindings audit (no hardcoded fills/strokes remaining)
  4e. Final review screenshots of every page
  ✋ USER CHECKPOINT: complete sign-off
```

---

## 3. Critical Rules

**Plugin API basics** (from use_figma skill — enforced here too):
- Use `return` to send data back (auto-serialized). Do NOT wrap in IIFE or call closePlugin.
- Return ALL created/mutated node IDs in every return value
- Page context resets each call — always `await figma.setCurrentPageAsync(page)` at start. **Call it at most once per script**: each component or doc page is its own `use_figma` call. Never loop over `figma.root.children` and switch pages inside a mutating script — split that work into one focused call per target page (see figma-use → gotchas.md → Set current page once per `use_figma` call (load `readPowerSteering("figma", "figma-use.md")`))
- `figma.notify()` throws — never use it
- Colors are 0–1 range, not 0–255
- Font MUST be loaded before any text write: `await figma.loadFontAsync({family, style})`. Use `await figma.listAvailableFontsAsync()` to discover available fonts and verify exact style strings — if a load fails, query available fonts to find the correct name or a fallback.

**Design system rules**:
1. **Variables BEFORE components** — components bind to variables. No token = no component.
2. **Inspect before creating** — run read-only `use_figma` to discover existing conventions. Match them.
3. **One page per component** *(default)* — exception: tightly related families (e.g., Input + helpers) may share a page with clear section separation.
4. **Bind visual properties to variables** *(default)* — fills, strokes, padding, radius, gap. Exceptions: intentionally fixed geometry (icon pixel-grid sizes, static dividers).
5. **Scopes on every variable** — NEVER leave as `ALL_SCOPES`. Background: `FRAME_FILL, SHAPE_FILL`. Text: `TEXT_FILL`. Border: `STROKE_COLOR`. Spacing: `GAP`. Radii: `CORNER_RADIUS`. Primitives: `[]` (hidden).
6. **Code syntax on every variable** — WEB syntax MUST use the `var()` wrapper: `var(--color-bg-primary)`, not `--color-bg-primary`. Use the actual CSS variable name from the codebase. ANDROID/iOS do NOT use a wrapper.
7. **Alias semantics to primitives** — `{ type: 'VARIABLE_ALIAS', id: primitiveVar.id }`. Never duplicate raw values in semantic layer.
8. **Position variants after combineAsVariants** — they stack at (0,0). Manually grid-layout + resize.
9. **INSTANCE_SWAP for icons** — never create a variant per icon. Cap variant matrices: if Size × Style × State > 30 combinations, split into sub-component.
10. **Deterministic naming** — use consistent, unique node names for idempotent cleanup and resumability. Track created node IDs via return values and the state ledger.
11. **No destructive cleanup** — cleanup scripts identify nodes by name convention or returned IDs, not by guessing.
12. **Validate before proceeding** — never build on unvalidated work. `get_metadata` after every create, `get_screenshot` after each component.
13. **NEVER parallelize `use_figma` calls** — Figma state mutations must be strictly sequential. Even if your tool supports parallel calls, never run two use_figma calls simultaneously.
14. **Never hallucinate Node IDs** — always read IDs from the state ledger returned by previous calls. Never reconstruct or guess an ID from memory.
15. **Use the helper scripts** — embed scripts from `scripts/` into your use_figma calls. Don't write 200-line inline scripts from scratch.
16. **Explicit phase approval** — at each checkpoint, name the next phase explicitly. "looks good" is not approval to proceed to Phase 3 if you asked about Phase 1.

---

## 4. State Management (Required for Long Workflows)

> **`getPluginData()` / `setPluginData()` are NOT supported in `use_figma`.** Use `getSharedPluginData()` / `setSharedPluginData()` instead (these ARE supported), or use name-based lookups and the state ledger (returned IDs).

| Entity type | Idempotency key | How to check existence |
|-------------|----------------|----------------------|
| Scene nodes (pages, frames, components) | `setSharedPluginData('dsb', 'key', value)` or unique name | `node.getSharedPluginData('dsb', 'key')` or `page.findOne(n => n.name === 'Button')` |
| Variables | Name within collection | `(await figma.variables.getLocalVariablesAsync()).find(v => v.name === name && v.variableCollectionId === collId)` |
| Styles | Name | `getLocalTextStyles().find(s => s.name === name)` |

Tag every created **scene node** immediately after creation:
```javascript
node.setSharedPluginData('dsb', 'run_id', RUN_ID);        // identifies this build run
node.setSharedPluginData('dsb', 'phase', 'phase3');        // which phase created it
node.setSharedPluginData('dsb', 'key', 'component/button');// unique logical key
```

**State persistence**: Do NOT rely solely on conversation context for the state ledger. Write it to disk:
```
/tmp/dsb-state-{RUN_ID}.json
```
Re-read this file at the start of every turn. In long workflows, conversation context will be truncated — the file is the source of truth.

Maintain a state ledger tracking:
```json
{
  "runId": "ds-build-2024-001",
  "phase": "phase3",
  "step": "component-button",
  "entities": {
    "collections": { "primitives": "id:...", "color": "id:..." },
    "variables": { "color/bg/primary": "id:...", "spacing/sm": "id:..." },
    "pages": { "Cover": "id:...", "Button": "id:..." },
    "components": { "Button": "id:..." }
  },
  "pendingValidations": ["Button:screenshot"],
  "completedSteps": ["phase0", "phase1", "phase2", "component-avatar"]
}
```

**Idempotency check** before every create: query by name + state ledger ID. If exists, skip or update — never duplicate.

**Resume protocol**: at session start or after context truncation, run a read-only `use_figma` to scan all pages, components, variables, and styles by name to reconstruct the `{key → id}` map. Then re-read the state file from disk if available.

**Continuation prompt** (give this to the user when resuming in a new chat):
> "I'm continuing a design system build. Run ID: {RUN_ID}. Load the figma-generate-library skill and resume from the last completed step."

---

## 5. Library Discovery and search_design_system — Reuse Decision Matrix

Search FIRST in Phase 0, then again immediately before each component creation.

**Start with `get_libraries`** to understand what libraries are available before searching blindly:

```
// Discover all libraries accessible to the file
get_libraries({ fileKey })
// Returns:
//   libraries_added_to_file: [{ name, libraryKey, description, source }, ...]
//   libraries_available_to_add: [{ name, libraryKey, description, source }, ...]
//   libraries_available_to_add_next_offset: number | null
```

Use the returned `libraryKey` values to scope searches to specific libraries via `includeLibraryKeys`. This avoids noisy results when many libraries are available.

If `libraries_available_to_add_next_offset` is non-null, more org libraries are available — call `get_libraries` again with `offset` set to that value. Org libraries page in batches of 20; community UI kits only appear on the first page.

```
// Search across all libraries (default)
search_design_system({ query, fileKey, includeComponents: true, includeVariables: true, includeStyles: true })

// Search within a specific library only
search_design_system({ query, fileKey, includeLibraryKeys: ["lk-abc123..."], includeComponents: true })
```

**Reuse if** all of these are true:
- Component property API matches your needs (same variant axes, compatible types)
- Token binding model is compatible (uses same or aliasable variables)
- Naming conventions match the target file
- Component is editable (not locked in a remote library you don't own)

**Rebuild if** any of these:
- API incompatibility (different property names, wrong variant model)
- Token model incompatible (hardcoded values, different variable schema)
- Ownership issue (can't modify the library)

**Wrap if** visual match but API incompatible:
- Import the library component as a nested instance inside a new wrapper component
- Expose a clean API on the wrapper

**Three-way priority**: local existing → subscribed library import → create new.

---

## 6. User Checkpoints

Mandatory. Design decisions require human judgment.

| After | Required artifacts | Ask |
|-------|-------------------|-----|
| Discovery + scope lock | Token list, component list, gap analysis | "Here's my plan. Approve before I create anything?" |
| Foundations | Variable summary (N collections, M vars, K modes), style list | "All tokens created. Review before file structure?" |
| File structure | Page list + screenshot | "Pages set up. Review before components?" |
| Each component | get_screenshot of component page | "Here's [Component] with N variants. Correct?" |
| Each conflict (code ≠ Figma) | Show both versions | "Code says X, Figma has Y. Which wins?" |
| Final QA | Per-page screenshots + audit report | "Complete. Sign off?" |

**If user rejects**: fix before moving on. Never build on rejected work.

---

## 7. Naming Conventions

Match existing file conventions. If starting fresh:

**Variables** (slash-separated):
```
color/bg/primary     color/text/secondary    color/border/default
spacing/xs  spacing/sm  spacing/md  spacing/lg  spacing/xl  spacing/2xl
radius/none  radius/sm  radius/md  radius/lg  radius/full
typography/body/font-size    typography/heading/line-height
```

**Primitives**: `blue/50` → `blue/900`, `gray/50` → `gray/900`

**Component names**: `Button`, `Input`, `Card`, `Avatar`, `Badge`, `Checkbox`, `Toggle`

**Variant names**: `Property=Value, Property=Value` — e.g., `Size=Medium, Style=Primary, State=Default`

**Page separators**: `---` (most common) or `——— COMPONENTS ———`

> Full naming reference: [Naming Conventions Reference](#reference--naming-conventions-reference)

---

## 8. Token Architecture

| Complexity | Pattern |
|-----------|---------|
| < 50 tokens | Single collection, 2 modes (Light/Dark) |
| 50–200 tokens | **Standard**: Primitives (1 mode) + Color semantic (Light/Dark) + Spacing (1 mode) + Typography (1 mode) |
| 200+ tokens | **Advanced**: Multiple semantic collections, 4–8 modes (Light/Dark × Contrast × Brand). See M3 pattern in [Token Creation Reference](#reference--token-creation-reference) |

Standard pattern (recommended starting point):
```
Collection: "Primitives"    modes: ["Value"]
  blue/500 = #3B82F6, gray/900 = #111827, ...

Collection: "Color"         modes: ["Light", "Dark"]
  color/bg/primary → Light: alias Primitives/white, Dark: alias Primitives/gray-900
  color/text/primary → Light: alias Primitives/gray-900, Dark: alias Primitives/white

Collection: "Spacing"       modes: ["Value"]
  spacing/xs = 4, spacing/sm = 8, spacing/md = 16, ...
```

---

## 9. Per-Phase Anti-Patterns

**Phase 0 anti-patterns:**
- ❌ Starting to create anything before scope is locked with user
- ❌ Ignoring existing file conventions and imposing new ones
- ❌ Skipping `search_design_system` before planning component creation

**Phase 1 anti-patterns:**
- ❌ Using `ALL_SCOPES` on any variable
- ❌ Duplicating raw values in semantic layer instead of aliasing
- ❌ Not setting code syntax (breaks Dev Mode and round-tripping)
- ❌ Creating component tokens before agreeing on token taxonomy

**Phase 2 anti-patterns:**
- ❌ Skipping the cover page or foundations docs
- ❌ Putting multiple unrelated components on one page

**Phase 3 anti-patterns:**
- ❌ Creating components before foundations exist
- ❌ Hardcoding any fill/stroke/spacing/radius value in a component
- ❌ Creating a variant per icon (use INSTANCE_SWAP instead)
- ❌ Not positioning variants after combineAsVariants (they all stack at 0,0)
- ❌ Building variant matrix > 30 without splitting (variant explosion)
- ❌ Importing remote components then immediately detaching them

**General anti-patterns:**
- ❌ Retrying a failed script without understanding the error first
- ❌ Using name-prefix matching for cleanup (deletes user-owned nodes)
- ❌ Building on unvalidated work from the previous step
- ❌ Skipping user checkpoints to "save time"
- ❌ Parallelizing use_figma calls (always sequential)
- ❌ Guessing/hallucinating node IDs from memory (always read from state ledger)
- ❌ Writing massive inline scripts instead of using the provided helper scripts
- ❌ Starting Phase 3 because the user said "build the button" without completing Phases 0-2

---

## 10. Reference Docs

Load on demand — each reference is authoritative for its phase:

Use your file reading tool to read these docs when needed. Do not assume their contents from the filename.

| Doc | Phase | Required / Optional | Load when |
|-----|-------|---------------------|-----------|
| [Discovery Phase Reference](#reference--discovery-phase-reference) | 0 | **Required** | Starting any build — codebase analysis + Figma inspection |
| [Token Creation Reference](#reference--token-creation-reference) | 1 | **Required** | Creating variables, collections, modes, styles |
| [Documentation Creation Reference](#reference--documentation-creation-reference) | 2 | Required | Creating cover page, foundations docs, swatches |
| [Component Creation Reference](#reference--component-creation-reference) | 3 | **Required** | Creating any component or variant |
| [Code Connect Setup Reference](#reference--code-connect-setup-reference) | 3–4 | Required | Setting up Code Connect or variable code syntax |
| [Naming Conventions Reference](#reference--naming-conventions-reference) | Any | Optional | Naming anything — variables, pages, variants, styles |
| [Error Recovery Reference](#reference--error-recovery-reference) | Any | **Required on error** | Script fails, multi-step workflow recovery, cleanup of abandoned workflow state |

---

## 11. Scripts

Reusable Plugin API helper functions. Embed in `use_figma` calls:

| Script | Purpose |
|--------|---------|
| [inspectFileStructure.js](#script--inspectfilestructurejs) | Discover all pages, components, variables, styles; returns full inventory |
| [createVariableCollection.js](#script--createvariablecollectionjs) | Create a named collection with modes; returns `{collectionId, modeIds}` |
| [createSemanticTokens.js](#script--createsemantictokensjs) | Create aliased semantic variables from a token map |
| [createComponentWithVariants.js](#script--createcomponentwithvariantsjs) | Build a component set from a variant matrix; handles grid layout |
| [bindVariablesToComponent.js](#script--bindvariablestocomponentjs) | Bind design tokens to all component visual properties |
| [createDocumentationPage.js](#script--createdocumentationpagejs) | Create a page with title + description + section structure |
| [validateCreation.js](#script--validatecreationjs) | Verify created nodes match expected counts, names, structure |
| [cleanupOrphans.js](#script--cleanuporphansjs) | Remove orphaned nodes by name convention or state ledger IDs |
| [rehydrateState.js](#script--rehydratestatejs) | Scan file for all pages, components, variables by name; returns full `{key → nodeId}` map for state reconstruction |

---

## Reference — Naming Conventions Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

This reference documents every naming convention used in the figma-generate-library workflow. Cover all naming decisions in order: variables, components, pages, variants, styles, separators, status indicators. The last section explains when to match an existing file's conventions vs. using the defaults here.

---

### 1. Variable Naming

#### Slash hierarchy (the universal pattern)

All Figma variables use slash-separated paths. The slash creates visual grouping in the Variables panel and maps directly to the token hierarchy in code.

```
{category}/{subcategory}/{role}
```

Real examples from Simple DS and Material 3:

```
color/bg/primary
color/bg/secondary
color/text/primary
color/text/muted
color/border/default
color/border/focus
color/feedback/error
color/feedback/success
spacing/xs
spacing/sm
spacing/md
spacing/lg
spacing/xl
spacing/2xl
radius/none
radius/sm
radius/md
radius/lg
radius/full
typography/body/font-size
typography/body/line-height
typography/heading/font-size
typography/heading/font-weight
```

#### Primitives collection

Primitive variables hold raw values and are **not** exposed to consumers (scope = `[]`). They use a flat `{family}/{step}` format matching the color scale convention from Simple DS:

```
blue/50
blue/100
blue/200
...
blue/900
gray/50
gray/100
...
gray/900
red/500
green/500
```

Step numbers follow the convention of the target codebase. If the codebase uses `100–900`, use that. If it uses `50–950`, use that. If there is no codebase convention, use `100–900` in increments of 100.

#### Semantic collection

Semantic variables alias primitives. They use the role-based `{category}/{role}` or `{category}/{subcategory}/{role}` pattern:

```
color/bg/primary         → alias: primitives/white (light), primitives/gray/900 (dark)
color/bg/secondary       → alias: primitives/gray/100 (light), primitives/gray/800 (dark)
color/text/primary       → alias: primitives/gray/900 (light), primitives/white (dark)
color/text/secondary     → alias: primitives/gray/600 (light), primitives/gray/400 (dark)
color/border/default     → alias: primitives/gray/200 (light), primitives/gray/700 (dark)
```

**Rule:** Semantic variables must never hold raw hex values — they always alias a primitive. If you need a new color value, create the primitive first, then create the semantic alias.

#### Casing

**Default:** Use **lowercase** with forward slashes: `color/bg/primary`, `spacing/2xl`.

**When to deviate:**
- If the existing file uses PascalCase (e.g., Material 3 uses `Schemes/Primary`) — match it.
- If the design team prefers PascalCase for readability in the Variables panel — acceptable as long as the code syntax is separately defined and uses the platform-correct case.
- Mode names can use spaces and mixed case (e.g., `SDS Light`, `Mode 1 → Light`) — these are labels, not identifiers.

**Never:** camelCase inside variable names (`colorBgPrimary` as a Figma name is wrong — that belongs in Android code syntax only). Never use spaces inside a path segment: `color/bg primary` is wrong; `color/bg/primary` is correct.

**Key distinction:** The casing rule applies to *Figma variable names*. Code syntax names follow *platform conventions* regardless of the Figma name case — see §9 for the full picture.

---

### 2. Component Naming

#### Main components: PascalCase, no prefix

Published components intended for library consumers use plain PascalCase names:

```
Button
Input
Checkbox
Toggle
Avatar
Badge
Card
Dialog
Tooltip
Banner
```

Do not use a namespace prefix for public components (e.g., do not name them `DS/Button` or `sds-Button`). Slashes in component names create nested grouping in the Assets panel, which is correct for sub-components but not for top-level public components.

#### Sub-components: underscore prefix + slash namespace

Internal sub-components that are NOT meant for library consumers use the `_` prefix. This hides them from the Assets panel by default and signals to other designers that they should not be used directly.

```
_Button/Slot           (internal icon slot for Button)
_Input/Indicator       (internal state indicator for Input)
_Badge/Dot             (internal dot sub-component of Badge)
_Parts/Avatar.Status   (UI3 pattern: _Parts/{ParentName}.{SubPart})
_Slider/Handle         (UI3 pattern: _{ParentName}/{SubPart})
```

Pattern rules:
- Use `_` prefix for ALL internal sub-components — no exceptions.
- Use slash namespacing to group sub-components under their parent: `_Button/IconSlot`.
- For sub-components shared by multiple parents, use `_Parts/{ComponentName}.{SubPart}`.

#### Private documentation components

Components used only for internal documentation (not for production use) use the `.` prefix:

```
.ExampleCard
.GuidelineHeader
.DemoFrame
```

This hides them from consumers while keeping them accessible on the canvas.

---

### 3. Page Naming

Five reference design systems use three distinct naming patterns. Choose one pattern and apply it consistently across all pages in the file.

#### Pattern 1: Plain names (Simple DS, Material 3, Polaris)

The most common pattern. Clean, readable, no decoration.

```
Cover
---
Foundations
Icons
---
Accordion
Avatars
Buttons
Cards
Dialog
Inputs
Menu
---
Utilities
Component Playground
```

Use this pattern when starting from scratch or when the target file already uses this style.

#### Pattern 2: Emoji prefix + status (UI3 Library)

The most expressive pattern. The page name encodes asset type, design status, and code readiness.

Anatomy: `[Asset Type Emoji] [Optional FPL Label] [Status Circle] Component Name [Code Status Bracket]`

| Segment | Values |
|---------|--------|
| Asset type | Component pages use the C-flag emoji; pattern pages use the P-flag emoji |
| Design status | Green circle = Ready, Yellow circle = WIP, Red circle = Do not use |
| Code status | (none) = Ready in code, `[beta]` = Beta, `[future]` = Not yet built |

Examples:
```
Overview
Status Key
---
FPL COMPONENTS (go/fpl)
[C-flag] FPL [Green] Buttons
[C-flag] FPL [Green] Inputs
[C-flag] FPL [Yellow] Popovers [future]
---
UI3 COMPONENTS
[C-flag] [Green] Comments
---
PATTERNS
[P-flag] [Green] Editor / Layers
---
[Book] Cover
[Headstone] Deprecated
```

Use this pattern only when building a large, multi-team design system where lifecycle tracking is needed, or when the target file already uses it.

#### Pattern 3: Emoji prefix (Shop Minis)

A lighter version of the UI3 pattern without status circles.

```
📔 Cover
ℹ️ About
🚀 Getting started
——— THEME ———
Color
Typography
Spacing
——— COMPONENTS ———
Button
Input
Card
```

Use this pattern when the target file already uses emoji prefixes but does not need lifecycle tracking.

#### Universal rules (all patterns)

- **Cover** is always first.
- **Separator pages** come before and after each logical section.
- **Foundation/token pages** always come before component pages.
- **Utility and internal pages** always come last.
- Pick one convention and do not mix patterns within a file.

---

### 4. Variant Naming

#### Property=Value format

All component variant properties and their values use `Property=Value` format in the Figma component set:

```
Size=Small, Style=Primary, State=Default
Size=Medium, Style=Secondary, State=Hover
Size=Large, Style=Ghost, State=Disabled
```

Actual property names match code prop names where possible:

| Figma Property | Code Prop Equivalent |
|---------------|---------------------|
| `Size` | `size` |
| `Style` / `Variant` | `variant` |
| `State` | Typically controlled by `:hover`, `:focus`, `:disabled` in CSS, but `state` in some systems |
| `Type` | `type` |
| `Disabled` | `disabled` (boolean) |
| `Icon` | `icon` (boolean or instance swap) |

#### Property value casing

Property values use **Title Case** in Figma (to be readable in the Variants panel), mapping to lowercase in code:

| Figma value | Code value |
|-------------|-----------|
| `Small` | `"small"` / `"sm"` |
| `Medium` | `"medium"` / `"md"` |
| `Large` | `"large"` / `"lg"` |
| `Primary` | `"primary"` |
| `Disabled` | `disabled` (boolean prop) |
| `Default` | *(typically the absent/unset case)* |

#### Boolean properties

Boolean component properties in Figma use `true` / `false` as values (Figma's native boolean), not `Yes` / `No` or `On` / `Off`.

---

### 5. Style Naming (Text and Effect Styles)

#### Text styles: category/name

```
Display/Large
Display/Medium
Display/Small
Heading/1
Heading/2
Heading/3
Body/Large
Body/Medium
Body/Small
Label/Large
Label/Small
Code/Inline
```

The category segment maps to the typographic role. Use the same category names as the codebase's typography scale where possible.

#### Effect styles (shadows): category/name

```
Shadow/None
Shadow/Subtle
Shadow/Medium
Shadow/Strong
Shadow/Overlay
Elevation/0
Elevation/1
Elevation/2
Elevation/3
Elevation/4
Elevation/5
```

Use `Shadow/` for named semantic shadows. Use `Elevation/N` for Material Design-style numbered elevation levels.

---

### 6. Separator Pages

Separator pages are empty pages whose sole purpose is to create visual breaks in the Figma page panel. Two conventions:

| Convention | Example | Used by |
|------------|---------|---------|
| Three dashes | `---` | Simple DS, UI3, Polaris, Material 3 |
| Decorated text | `——— COMPONENTS ———` | Shop Minis |

The three-dash convention (`---`) is the most common and the default for new files. Use it unless the target file uses the decorated-text style.

**Where to place separators:**

```
Cover
---                    ← after cover
Foundations
Icons
---                    ← before components
[component pages]
---                    ← before utilities
Utilities
```

---

### 7. Status Indicators (UI3 Emoji System)

The UI3 Library uses colored circle emojis in page names to communicate design readiness at a glance. This system is optional but powerful for large teams.

| Emoji | Meaning | When to use |
|-------|---------|-------------|
| Green circle | Ready / Approved | Design is stable, reviewed, and safe to use |
| Yellow circle | WIP / In Progress | Design is being actively worked on, may change |
| Red circle | Do not use | Not ready, do not reference; may be deprecated |

Code readiness is communicated via brackets appended to the component name:

| Bracket | Meaning |
|---------|---------|
| (none) | Component is implemented in code and stable |
| `[beta]` | Component is in code but not yet stable (~3 weeks from ready) |
| `[future]` | Not yet implemented in code |

**Documentation status (within component pages):**

If building a UI3-style system, each documentation frame gets a status banner with one of these labels:

- `APPROVED` — fully vetted
- `READY FOR REVIEW` — awaiting sign-off
- `WORK IN PROGRESS` — actively being designed
- `NEEDS UPDATE` — outdated, requires revision
- `DO NOT REFERENCE` — should not be used

This system is only recommended for large, multi-team systems where lifecycle tracking provides real value. For smaller systems, skip the emoji status indicators and use plain page names.

---

### 8. When to Match Existing vs. Use Defaults

**Always inspect before naming anything.** Run `get_metadata` or `inspectFileStructure` to discover existing conventions before creating any pages or variables.

#### Match the existing file when:

- The file already has pages with a consistent naming pattern (emoji prefixes, separator style, casing).
- The file already has variable collections with an established naming scheme.
- The file was started by a design team and carries intentional decisions.
- Any existing component names use a specific pattern (PascalCase, kebab-case, namespace prefixes).

#### Use the defaults from this document when:

- Starting a brand-new Figma file with no existing content.
- The existing conventions are inconsistent (mix of styles = no convention to match).
- The user explicitly asks for a fresh design system following best practices.

#### When code and Figma disagree:

If the codebase uses `button-primary` but Figma has a component named `Button`, do not rename the Figma component. Instead:
- Keep the Figma name as `Button` (PascalCase, human-readable).
- Set variable code syntax to match the exact CSS token name from the codebase.
- Set Code Connect source path to the actual code file and use the exact code component name.

**The rule:** Figma names are for designers; code syntax and Code Connect source paths carry the exact code identifiers. These two identity systems operate in parallel.

---

### 9. Figma Variable Names vs Code Names — The Full Picture

This is one of the most misunderstood areas. Figma names and code names follow **different conventions on purpose** — they serve different audiences and live in different environments.

#### Why they differ

| | Figma variable name | Code syntax (WEB) |
|---|---|---|
| **Audience** | Designers in the Variables panel | Developers in CSS/Swift/Kotlin |
| **Separator** | `/` (slash) — creates visual grouping in Figma UI | `-` (hyphen) — required by CSS custom property syntax |
| **Case** | lowercase (or PascalCase for display — see below) | kebab-case for CSS; camelCase for JS/Android |
| **Depth** | 2–4 levels | Flat for CSS; dot-notation for JS |
| **Namespace** | Implicit (by collection) | Explicit prefix (`--p-`, `--md-`, `--cds-`) |

#### The transformation

```
Figma variable name              Code syntax (WEB)
──────────────────               ─────────────────
color/bg/primary          →      var(--color-bg-primary)
spacing/xs                →      var(--spacing-xs)
radius/md                 →      var(--radius-md)
typography/body/font-size →      var(--typography-body-font-size)

Pattern: replace "/" with "-", wrap in var(--)

**CRITICAL: The `var()` wrapper is REQUIRED for WEB code syntax.** Figma expects the full CSS function syntax — not just the property name. If you set `--color-bg-primary` (without `var()`), Dev Mode will show raw hex values instead of the variable reference. Always set `var(--color-bg-primary)`.
```

```
Figma variable name              Code syntax (ANDROID)
──────────────────               ─────────────────────
color/bg/primary          →      colorBgPrimary
spacing/xs                →      spacingXs
radius/md                 →      radiusMd

Pattern: replace "/" with "", capitalize each word after first
```

```
Figma variable name              Code syntax (iOS)
──────────────────               ─────────────────
color/bg/primary          →      Color.bgPrimary
spacing/xs                →      Spacing.xs
radius/md                 →      Radius.md

Pattern: first segment becomes class name, remainder becomes property (camelCase)
```

#### Real-world examples from the 5 reference files

| File | Figma variable name | WEB code syntax | ANDROID code syntax |
|------|--------------------|-----------------|--------------------|
| Simple DS | `color/bg/primary` | `var(--color-bg-primary)` | `colorBgPrimary` |
| Simple DS | `spacing/sm` | `var(--spacing-sm)` | `spacingSm` |
| Material 3 | `Schemes/Primary` | `var(--md-sys-color-primary)` | `colorPrimary` |
| Material 3 | `Corner/Extra-small` | `var(--md-sys-shape-corner-extra-small)` | `shapeCornerExtraSmall` |
| Polaris | `color/bg/surface` | `var(--p-color-bg-surface)` | — |

**Key observation from Material 3:** The Figma name `Schemes/Primary` uses PascalCase with a space, but the WEB code syntax is `var(--md-sys-color-primary)` — entirely kebab-case with a vendor prefix `md-sys-`. The Figma name and the code syntax bear almost no resemblance. This is intentional and common in mature design systems.

#### Casing in Figma: lowercase is default, PascalCase is valid for display

The guideline to use lowercase is a default, not a universal rule. Evidence from real files:

| File | Figma case | Code output case | Why |
|------|-----------|------------------|-----|
| Simple DS | `color/bg/primary` (lowercase) | `var(--color-bg-primary)` | Direct mapping — simple |
| Material 3 | `Schemes/Primary` (PascalCase) | `var(--md-sys-color-primary)` | PascalCase reads better in Variables panel; code name is independently defined |
| Polaris | `color/bg/surface` (lowercase) | `var(--p-color-bg-surface)` | Direct mapping with vendor prefix |

**Rule:** Use lowercase when the Figma name will map directly to the CSS name. Use PascalCase (or match existing file) when the design system has human-readable variable names that are distinct from the technical code names.

#### When the codebase doesn't use CSS custom properties

Some JavaScript-first systems (Chakra, Ant Design, MUI) don't use CSS `var(--...)` at all. Their tokens live in JS theme objects:

```
Chakra:    colors.gray[500]         →  JS: theme.colors.gray[500]
Ant:       colorPrimary             →  JS: token.colorPrimary
MUI:       palette.primary.main     →  JS: theme.palette.primary.main
```

In these cases, set WEB code syntax to the JS property path rather than a CSS variable:
```javascript
// For a JS-object-based system like Chakra:
v.setVariableCodeSyntax('WEB', 'colors.gray.500');

// For Ant Design:
v.setVariableCodeSyntax('WEB', 'colorPrimary');
```

#### Hierarchy depth: match the codebase

The number of slash levels should mirror the codebase's nesting depth:

| Codebase pattern | Figma depth | Example |
|-----------------|------------|---------|
| `--primary` (flat) | 1–2 levels | `color/primary` |
| `--color-bg-surface` (3-part) | 3 levels | `color/bg/surface` |
| `--md-sys-color-primary` (vendor + 3-part) | 3 levels (vendor prefix goes in code syntax only) | `color/primary` |
| `theme.palette.primary.main` (4-part) | 3–4 levels | `color/palette/primary/main` |

**Important:** Vendor prefixes (`--p-`, `--md-sys-`, `--cds-`) belong in the **code syntax**, not the Figma variable name. The Figma name `color/bg/surface` + code syntax `var(--p-color-bg-surface)` is the correct pattern.

#### Action at discovery time

During Phase 0 discovery, capture both sides of the mapping explicitly:

```
For each token found in the codebase:
  CSS variable:   --sds-color-background-brand-default
  Figma name:     color/bg/brand/default        (slash hierarchy, no vendor prefix)
  WEB syntax:     var(--sds-color-background-brand-default)  (exact CSS name)
  ANDROID syntax: sdsColorBackgroundBrandDefault  (camelCase)
  iOS syntax:     Color.backgroundBrandDefault    (dot-notation)
```

Store this mapping in the state ledger. Use it when calling `setVariableCodeSyntax` in Phase 1. Never derive the code syntax from the Figma name if you have the original CSS variable name — always use the original.

---

## Reference — Token Creation Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

This document covers Phase 1: creating variable collections, modes, primitives, semantic aliases, scopes, code syntax, styles, and validation. All code is copy-paste ready for `use_figma`.

---

### 1. Collection Architecture

Choose the pattern that matches your token count and complexity:

#### Simple Pattern (< 50 tokens)

One collection, 2 modes. Appropriate for small projects or brand kits.

```
Collection: "Tokens"    modes: ["Light", "Dark"]
  color/bg/primary → Light: #FFFFFF, Dark: #1A1A1A
  spacing/sm = 8
```

#### Standard Pattern (50–200 tokens) — Recommended Starting Point

Separate primitives from semantics. The real-world reference is Figma's Simple Design System (SDS): 7 collections, 368 variables, light/dark modes on semantic colors, single-mode primitives.

```
Collection: "Primitives"    modes: ["Value"]       ← raw hex values, no modes
  blue/500 = #3B82F6
  gray/900 = #111827
  white/1000 = #FFFFFF

Collection: "Color"         modes: ["Light", "Dark"] ← aliases to Primitives
  color/bg/primary → Light: alias Primitives/white/1000, Dark: alias Primitives/gray/900
  color/text/primary → Light: alias Primitives/gray/900, Dark: alias Primitives/white/1000

Collection: "Spacing"       modes: ["Value"]
  spacing/xs = 4, spacing/sm = 8, spacing/md = 16, spacing/lg = 24, spacing/xl = 32

Collection: "Typography Primitives"  modes: ["Value"]
  family/sans = "Inter", scale/01 = 12, scale/02 = 14, scale/03 = 16, weight/regular = 400

Collection: "Typography"    modes: ["Value"]        ← aliases to Typography Primitives
  body/font-family → alias family/sans
  body/size-md → alias scale/03
```

#### Advanced Pattern (200+ tokens) — M3 Model

Multiple semantic collections, 4–8 modes. Use when you need light/dark × contrast × brand or responsive breakpoints.

```
Collection: "M3"           modes: ["Light", "Dark", "Light High Contrast", "Dark High Contrast", ...]
Collection: "Typeface"     modes: ["Baseline", "Wireframe"]
Collection: "Typescale"    modes: ["Value"]  ← aliases into Typeface
Collection: "Shape"        modes: ["Value"]
```

Key insight from M3: ALL 196 semantic color variables live in a SINGLE collection with 8 modes. Switching a frame's mode once updates every color simultaneously.

---

### 2. Creating Collections + Modes

#### Creating a Primitives Collection

```javascript
const RUN_ID = "ds-build-2024-001"; // use the same RUN_ID throughout the build

// Create the collection
const primColl = figma.variables.createVariableCollection("Primitives");

// Rename the default "Mode 1" to "Value"
primColl.renameMode(primColl.modes[0].modeId, "Value");
const valueMode = primColl.modes[0].modeId;

// Tag for idempotency
primColl.setSharedPluginData('dsb', 'run_id', RUN_ID);
primColl.setSharedPluginData('dsb', 'key', 'collection/primitives');

return {
  collectionId: primColl.id,
  modeId: valueMode,
  name: primColl.name
};
```

#### Creating a Semantic Color Collection with Light/Dark Modes

```javascript
const RUN_ID = "ds-build-2024-001";

const colorColl = figma.variables.createVariableCollection("Color");

// Rename default "Mode 1" to "Light"
colorColl.renameMode(colorColl.modes[0].modeId, "Light");
const lightModeId = colorColl.modes[0].modeId;

// Add "Dark" mode — requires Professional plan or higher
// Throws "in addMode: Limited to N modes only" on Starter plan
const darkModeId = colorColl.addMode("Dark");

colorColl.setSharedPluginData('dsb', 'run_id', RUN_ID);
colorColl.setSharedPluginData('dsb', 'key', 'collection/color');

return {
  collectionId: colorColl.id,
  lightModeId,
  darkModeId
};
```

**Mode plan limits:** Starter = 1 mode, Professional = 4 modes, Organization/Enterprise = 40 modes. If `addMode` throws, the file is on a Starter plan — tell the user and ask how to proceed.

#### Creating a Spacing Collection (single mode)

```javascript
const RUN_ID = "ds-build-2024-001";

const spacingColl = figma.variables.createVariableCollection("Spacing");
spacingColl.renameMode(spacingColl.modes[0].modeId, "Value");
const valueMode = spacingColl.modes[0].modeId;

spacingColl.setSharedPluginData('dsb', 'run_id', RUN_ID);
spacingColl.setSharedPluginData('dsb', 'key', 'collection/spacing');

return {
  collectionId: spacingColl.id,
  modeId: valueMode
};
```

---

### 3. Creating All Variable Types

#### hex → {r, g, b} Conversion Helper

Colors in the Figma Plugin API are 0–1 range, not 0–255. Embed this helper in any script that creates color variables:

```javascript
function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  return {
    r: parseInt(clean.substring(0, 2), 16) / 255,
    g: parseInt(clean.substring(2, 4), 16) / 255,
    b: parseInt(clean.substring(4, 6), 16) / 255
  };
}

// With alpha channel (for semi-transparent primitives like Black/200 at 10%):
function hexToRgba(hex) {
  const clean = hex.replace('#', '');
  const hasAlpha = clean.length === 8;
  return {
    r: parseInt(clean.substring(0, 2), 16) / 255,
    g: parseInt(clean.substring(2, 4), 16) / 255,
    b: parseInt(clean.substring(4, 6), 16) / 255,
    a: hasAlpha ? parseInt(clean.substring(6, 8), 16) / 255 : 1
  };
}

// Usage:
// hexToRgb('#3B82F6')        → {r: 0.231, g: 0.510, b: 0.965}
// hexToRgb('#14AE5C')        → {r: 0.078, g: 0.682, b: 0.361}
// hexToRgba('#0c0c0d1a')     → {r: 0.047, g: 0.047, b: 0.051, a: 0.102}
```

#### Creating Primitive Color Variables (Real SDS Data)

This creates a subset of the Simple Design System's `Color Primitives` collection (Blue family, from the Standard pattern used by real design systems):

```javascript
function hexToRgb(hex) {
  const c = hex.replace('#', '');
  return { r: parseInt(c.slice(0,2),16)/255, g: parseInt(c.slice(2,4),16)/255, b: parseInt(c.slice(4,6),16)/255 };
}

const RUN_ID = "ds-build-2024-001";

// Get the Primitives collection created in the previous step
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const primColl = collections.find(c => c.getSharedPluginData('dsb', 'key') === 'collection/primitives');
if (!primColl) throw new Error("Primitives collection not found — run collection creation first");
const valueMode = primColl.modes[0].modeId;

    // Define primitives — use real values from your codebase
    const primitiveColors = [
      // Blue scale
      { name: 'blue/100', hex: '#EFF6FF' },
      { name: 'blue/200', hex: '#DBEAFE' },
      { name: 'blue/300', hex: '#93C5FD' },
      { name: 'blue/400', hex: '#60A5FA' },
      { name: 'blue/500', hex: '#3B82F6' },
      { name: 'blue/600', hex: '#2563EB' },
      { name: 'blue/700', hex: '#1D4ED8' },
      { name: 'blue/800', hex: '#1E40AF' },
      { name: 'blue/900', hex: '#1E3A8A' },
      // Gray scale
      { name: 'gray/100', hex: '#F9FAFB' },
      { name: 'gray/200', hex: '#F3F4F6' },
      { name: 'gray/300', hex: '#D1D5DB' },
      { name: 'gray/400', hex: '#9CA3AF' },
      { name: 'gray/500', hex: '#6B7280' },
      { name: 'gray/600', hex: '#4B5563' },
      { name: 'gray/700', hex: '#374151' },
      { name: 'gray/800', hex: '#1F2937' },
      { name: 'gray/900', hex: '#111827' },
      // White / Black
      { name: 'white/1000', hex: '#FFFFFF' },
      { name: 'black/1000', hex: '#000000' },
    ];

    const created = [];
    for (const { name, hex } of primitiveColors) {
      const v = figma.variables.createVariable(name, primColl, 'COLOR');
      v.setValueForMode(valueMode, hexToRgb(hex));
      // Primitives: EMPTY scopes (hidden from all pickers — designers use semantics)
      v.scopes = [];
      // Code syntax from the actual CSS variable name
      v.setVariableCodeSyntax('WEB', `var(--color-${name.replace('/', '-')})`);
      v.setSharedPluginData('dsb', 'run_id', RUN_ID);
      v.setSharedPluginData('dsb', 'key', `primitive/${name}`);
      created.push({ name, id: v.id });
    }

return { created, count: created.length };
```

**Critical scope rule for primitives:** Set `v.scopes = []`. This hides primitives from every picker. Designers should only see semantic tokens. The exception is semi-transparent overlay primitives (Black/White with alpha) — those get `["EFFECT_COLOR"]` so they appear in shadow pickers.

#### Creating FLOAT Variables (Spacing, Radius, Font Size)

```javascript
const RUN_ID = "ds-build-2024-001";
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const spacingColl = collections.find(c => c.getSharedPluginData('dsb', 'key') === 'collection/spacing');
if (!spacingColl) throw new Error("Spacing collection not found");
const valueMode = spacingColl.modes[0].modeId;

const spacingTokens = [
  { name: 'spacing/xs',  value: 4,  scope: 'GAP', cssVar: '--spacing-xs' },
  { name: 'spacing/sm',  value: 8,  scope: 'GAP', cssVar: '--spacing-sm' },
  { name: 'spacing/md',  value: 16, scope: 'GAP', cssVar: '--spacing-md' },
  { name: 'spacing/lg',  value: 24, scope: 'GAP', cssVar: '--spacing-lg' },
  { name: 'spacing/xl',  value: 32, scope: 'GAP', cssVar: '--spacing-xl' },
  { name: 'spacing/2xl', value: 48, scope: 'GAP', cssVar: '--spacing-2xl' },
];

const radiusTokens = [
  { name: 'radius/none', value: 0,    scope: 'CORNER_RADIUS', cssVar: '--radius-none' },
  { name: 'radius/sm',   value: 4,    scope: 'CORNER_RADIUS', cssVar: '--radius-sm' },
  { name: 'radius/md',   value: 8,    scope: 'CORNER_RADIUS', cssVar: '--radius-md' },
  { name: 'radius/lg',   value: 16,   scope: 'CORNER_RADIUS', cssVar: '--radius-lg' },
  { name: 'radius/full', value: 9999, scope: 'CORNER_RADIUS', cssVar: '--radius-full' },
];

const created = [];
for (const { name, value, scope, cssVar } of [...spacingTokens, ...radiusTokens]) {
  const v = figma.variables.createVariable(name, spacingColl, 'FLOAT');
  v.setValueForMode(valueMode, value);
  v.scopes = [scope];
  v.setVariableCodeSyntax('WEB', `var(${cssVar})`);
  v.setSharedPluginData('dsb', 'run_id', RUN_ID);
  v.setSharedPluginData('dsb', 'key', name);
  created.push({ name, value, id: v.id });
}

return { created, count: created.length };
```

#### Creating STRING Variables (Font Family, Font Style)

```javascript
const RUN_ID = "ds-build-2024-001";
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const typoPrimColl = collections.find(c => c.getSharedPluginData('dsb', 'key') === 'collection/typography-primitives');
if (!typoPrimColl) throw new Error("Typography Primitives collection not found");
const valueMode = typoPrimColl.modes[0].modeId;

const fontTokens = [
  { name: 'family/sans',  value: 'Inter',       scope: 'FONT_FAMILY', cssVar: '--font-family-sans' },
  { name: 'family/mono',  value: 'Roboto Mono',  scope: 'FONT_FAMILY', cssVar: '--font-family-mono' },
  // Font style strings — these are the Figma fontName.style values:
  { name: 'weight/regular',  value: 'Regular',   scope: 'FONT_STYLE',  cssVar: '--font-weight-regular' },
  { name: 'weight/medium',   value: 'Medium',    scope: 'FONT_STYLE',  cssVar: '--font-weight-medium' },
  { name: 'weight/semibold', value: 'Semi Bold', scope: 'FONT_STYLE',  cssVar: '--font-weight-semibold' },
  { name: 'weight/bold',     value: 'Bold',      scope: 'FONT_STYLE',  cssVar: '--font-weight-bold' },
];

const created = [];
for (const { name, value, scope, cssVar } of fontTokens) {
  const v = figma.variables.createVariable(name, typoPrimColl, 'STRING');
  v.setValueForMode(valueMode, value);
  v.scopes = [scope];
  v.setVariableCodeSyntax('WEB', `var(${cssVar})`);
  v.setSharedPluginData('dsb', 'run_id', RUN_ID);
  v.setSharedPluginData('dsb', 'key', `typo-prim/${name}`);
  created.push({ name, value, id: v.id });
}

return { created, count: created.length };
```

#### Creating BOOLEAN Variables

BOOLEAN variables have no scopes (scopes are not supported for BOOLEAN type).

```javascript
const RUN_ID = "ds-build-2024-001";
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const coll = collections.find(c => c.getSharedPluginData('dsb', 'key') === 'collection/tokens');
if (!coll) throw new Error("Collection not found");
const valueMode = coll.modes[0].modeId;

const v = figma.variables.createVariable('feature-flags/show-beta-badge', coll, 'BOOLEAN');
v.setValueForMode(valueMode, false);
// No scopes — BOOLEAN does not support scopes
v.setSharedPluginData('dsb', 'run_id', RUN_ID);
v.setSharedPluginData('dsb', 'key', 'feature-flags/show-beta-badge');

return { id: v.id, name: v.name };
```

---

### 4. Variable Aliasing (VARIABLE_ALIAS) — Primitive → Semantic Chain

Semantic tokens reference primitives via `VARIABLE_ALIAS`. This is the core pattern that makes light/dark theming work.

**Architecture:**
```
Color Primitives collection (1 mode: Value)
  blue/500 = #3B82F6          ← raw value

Color collection (2 modes: Light, Dark)
  color/bg/accent/default:
    Light → VARIABLE_ALIAS → Primitives/blue/500
    Dark  → VARIABLE_ALIAS → Primitives/blue/300
```

#### Complete Semantic Alias Creation Script (SDS-style)

```javascript
function hexToRgb(hex) {
  const c = hex.replace('#', '');
  return { r: parseInt(c.slice(0,2),16)/255, g: parseInt(c.slice(2,4),16)/255, b: parseInt(c.slice(4,6),16)/255 };
}

const RUN_ID = "ds-build-2024-001";
const collections = await figma.variables.getLocalVariableCollectionsAsync();

const primColl = collections.find(c => c.getSharedPluginData('dsb', 'key') === 'collection/primitives');
const colorColl = collections.find(c => c.getSharedPluginData('dsb', 'key') === 'collection/color');
if (!primColl || !colorColl) throw new Error("Collections not found — run primitive/color collection creation first");

const primValueMode = primColl.modes[0].modeId;
const lightModeId = colorColl.modes.find(m => m.name === 'Light').modeId;
const darkModeId = colorColl.modes.find(m => m.name === 'Dark').modeId;

// Load all primitive variables for lookup
const allVars = await figma.variables.getLocalVariablesAsync();
const primsByKey = {};
for (const v of allVars) {
  if (v.variableCollectionId === primColl.id) {
    primsByKey[v.getSharedPluginData('dsb', 'key')] = v;
  }
}

function getPrim(name) {
  const v = primsByKey[`primitive/${name}`];
  if (!v) throw new Error(`Primitive not found: primitive/${name}`);
  return v;
}

// Define semantic → [lightPrimitiveName, darkPrimitiveName]
// Following the SDS pattern: Background/{Intent}/{Emphasis}
const semanticColors = [
  // Background
  { name: 'color/bg/default/default',   lightPrim: 'white/1000', darkPrim: 'gray/900',
    cssVar: '--color-bg-default-default', scopes: ['FRAME_FILL', 'SHAPE_FILL'] },
  { name: 'color/bg/default/secondary', lightPrim: 'gray/100', darkPrim: 'gray/800',
    cssVar: '--color-bg-default-secondary', scopes: ['FRAME_FILL', 'SHAPE_FILL'] },
  { name: 'color/bg/brand/default',     lightPrim: 'blue/600', darkPrim: 'blue/300',
    cssVar: '--color-bg-brand-default', scopes: ['FRAME_FILL', 'SHAPE_FILL'] },
  // Text
  { name: 'color/text/default/default', lightPrim: 'gray/900', darkPrim: 'white/1000',
    cssVar: '--color-text-default-default', scopes: ['TEXT_FILL'] },
  { name: 'color/text/default/secondary', lightPrim: 'gray/500', darkPrim: 'gray/400',
    cssVar: '--color-text-default-secondary', scopes: ['TEXT_FILL'] },
  { name: 'color/text/brand/default',   lightPrim: 'blue/700', darkPrim: 'blue/200',
    cssVar: '--color-text-brand-default', scopes: ['TEXT_FILL'] },
  // Border
  { name: 'color/border/default/default', lightPrim: 'gray/300', darkPrim: 'gray/600',
    cssVar: '--color-border-default-default', scopes: ['STROKE_COLOR'] },
  { name: 'color/border/brand/default',   lightPrim: 'blue/500', darkPrim: 'blue/400',
    cssVar: '--color-border-brand-default', scopes: ['STROKE_COLOR'] },
];

const created = [];
for (const { name, lightPrim, darkPrim, cssVar, scopes } of semanticColors) {
  const v = figma.variables.createVariable(name, colorColl, 'COLOR');
  // Alias to primitive in Light mode
  v.setValueForMode(lightModeId, figma.variables.createVariableAlias(getPrim(lightPrim)));
  // Alias to primitive in Dark mode
  v.setValueForMode(darkModeId, figma.variables.createVariableAlias(getPrim(darkPrim)));
  // Set scopes (semantic layer — these ARE shown in pickers)
  v.scopes = scopes;
  // Code syntax
  v.setVariableCodeSyntax('WEB', `var(${cssVar})`);
  v.setSharedPluginData('dsb', 'run_id', RUN_ID);
  v.setSharedPluginData('dsb', 'key', name);
  created.push({ name, id: v.id });
}

return { created, count: created.length };
```

**Key API points:**
- `figma.variables.createVariableAlias(variable)` — takes a Variable object, returns `{type:'VARIABLE_ALIAS', id: variable.id}`
- The aliased variable MUST have the same `resolvedType` as the semantic variable
- Never duplicate raw values in the semantic layer — always alias

---

### 5. Variable Scopes — Complete Reference Table

| Semantic Role | Recommended Scopes | Variable Type |
|---|---|---|
| Primitive colors (raw) | `[]` — empty, hidden from all pickers | COLOR |
| Semi-transparent overlay primitives | `["EFFECT_COLOR"]` | COLOR |
| Background fills (frame, shape) | `["FRAME_FILL", "SHAPE_FILL"]` | COLOR |
| Text color | `["TEXT_FILL"]` | COLOR |
| Icon / shape fill | `["SHAPE_FILL", "STROKE_COLOR"]` | COLOR |
| Border / stroke color | `["STROKE_COLOR"]` | COLOR |
| Background + border combined | `["FRAME_FILL", "SHAPE_FILL", "STROKE_COLOR"]` | COLOR |
| Shadow color | `["EFFECT_COLOR"]` | COLOR |
| Spacing / gap between items | `["GAP"]` | FLOAT |
| Padding (if separate from gap) | `["GAP"]` | FLOAT |
| Corner radius | `["CORNER_RADIUS"]` | FLOAT |
| Width / height dimensions | `["WIDTH_HEIGHT"]` | FLOAT |
| Font size | `["FONT_SIZE"]` | FLOAT |
| Line height | `["LINE_HEIGHT"]` | FLOAT |
| Letter spacing | `["LETTER_SPACING"]` | FLOAT |
| Font weight (numeric) | `["FONT_WEIGHT"]` | FLOAT |
| Stroke width | `["STROKE_FLOAT"]` | FLOAT |
| Effect blur radius | `["EFFECT_FLOAT"]` | FLOAT |
| Opacity | `["OPACITY"]` | FLOAT |
| Font family | `["FONT_FAMILY"]` | STRING |
| Font style (font-specific name, e.g. `"Regular"` — varies per font) | `["FONT_STYLE"]` | STRING |
| Boolean flags | *(scopes not supported)* | BOOLEAN |

**Never use `ALL_SCOPES`** on any variable. It pollutes every picker with irrelevant tokens. The Simple Design System (SDS), the gold standard, uses targeted scopes on every variable.

**`ALL_FILLS` note:** `ALL_FILLS` is exclusive among fill scopes — it covers `FRAME_FILL`, `SHAPE_FILL`, and `TEXT_FILL` together. If set, you cannot also add individual fill scopes. Prefer specifying individual scopes for precision.

#### Batch Scope-Setting (After Variables are Created)

If you created variables without scopes and need to set them in batch:

```javascript
const allVars = await figma.variables.getLocalVariablesAsync();

// Scope mapping: partial name match → scopes
const scopeRules = [
  { match: 'color/bg/',     scopes: ['FRAME_FILL', 'SHAPE_FILL'] },
  { match: 'color/text/',   scopes: ['TEXT_FILL'] },
  { match: 'color/icon/',   scopes: ['SHAPE_FILL', 'STROKE_COLOR'] },
  { match: 'color/border/', scopes: ['STROKE_COLOR'] },
  { match: 'spacing/',      scopes: ['GAP'] },
  { match: 'radius/',       scopes: ['CORNER_RADIUS'] },
  { match: 'blue/',         scopes: [] },   // primitives — hide
  { match: 'gray/',         scopes: [] },
  { match: 'white/',        scopes: [] },
  { match: 'black/',        scopes: [] },
];

const updated = [];
for (const v of allVars) {
  if (v.remote) continue; // skip library variables
  for (const rule of scopeRules) {
    if (v.name.startsWith(rule.match)) {
      v.scopes = rule.scopes;
      updated.push({ name: v.name, scopes: rule.scopes });
      break;
    }
  }
}

return { updated, count: updated.length };
```

---

### 6. Code Syntax — WEB/ANDROID/iOS

Every variable must have code syntax set. This is what powers the developer handoff experience:

**What code syntax does:** When a developer inspects any element in Figma Dev Mode that has a variable-bound property (fill, padding, radius, etc.), the code snippet shown uses the variable's code syntax name — not the Figma variable name. For example, a button's background fill bound to `color/bg/primary` will show `background: var(--color-bg-primary)` in the CSS snippet, not `color/bg/primary`. Without code syntax set, Dev Mode shows raw hex values or nothing useful.

You can set up to **3 syntaxes per variable** — one per platform (Web, iOS, Android). Set all three if the codebase targets multiple platforms; set only WEB if it's a web-only project.

```javascript
// WEB: MUST include the var() wrapper — this is the full CSS function syntax
variable.setVariableCodeSyntax('WEB', 'var(--color-bg-primary)');
//                                     ^^^^                   ^
//                              var() wrapper is REQUIRED

// ANDROID: Kotlin property name — camelCase, no wrapper
variable.setVariableCodeSyntax('ANDROID', 'colorBgPrimary');

// iOS: Swift property — dot-notation, no wrapper
variable.setVariableCodeSyntax('iOS', 'Color.bgPrimary');
```

> **CRITICAL — WEB code syntax MUST use the `var()` wrapper.** Setting just `--color-bg-primary` (without `var()`) will cause Dev Mode to show raw hex values instead of the CSS variable reference. Always use the full `var(--name)` form. ANDROID and iOS do NOT use a wrapper.

**Platform derivation rules from the CSS variable name:**

| Platform | Pattern | Example |
|---|---|---|
| WEB | **`var(--{css-var-name})`** — `var()` wrapper required | `var(--sds-color-bg-primary)` |
| ANDROID | camelCase, no wrapper, strip `--` prefix | `sdsColorBgPrimary` |
| iOS | PascalCase after `.`, no wrapper, strip `--` prefix | `Color.SdsColorBgPrimary` or `Color.bgPrimary` |

**Always use the actual CSS variable name from the codebase** — do not derive it from the Figma variable name. If the code uses `--sds-color-background-brand-default`, that exact string is the WEB code syntax (minus the `var()` wrapper that you add).

#### Batch Code Syntax Setting

```javascript
const allVars = await figma.variables.getLocalVariablesAsync();
const updated = [];

for (const v of allVars) {
  if (v.remote) continue;
  // If code syntax already set, skip
  if (v.codeSyntax['WEB']) continue;

  // FALLBACK: derive from Figma name: color/bg/primary → var(--color-bg-primary)
  // PREFERRED: pass in a cssVarMap built from actual codebase CSS variable names
  // e.g. cssVarMap = { 'color/bg/primary': '--color-bg-primary', ... }
  const cssName = cssVarMap?.[v.name]
    ?? v.name.replace(/\//g, '-').replace(/\s/g, '-').toLowerCase();
  v.setVariableCodeSyntax('WEB', `var(--${cssName})`);
  updated.push({ name: v.name, web: `var(--${cssName})` });
}

return { updated, count: updated.length };
```

Note: derived names are a fallback only. Always prefer overriding with actual CSS variable names from the codebase when they are known.

---

### 7. Effect Styles (Shadows) and Text Styles

Shadows and composite typography cannot be variables — they are Styles.

#### Creating Effect Styles (Shadows)

Reference from SDS (15 effect styles) and the SDS shadow pattern `Shadow/{Level}`:

```javascript
const RUN_ID = "ds-build-2024-001";

// Shadow definitions — CSS equivalent in comments
// CSS: 0 1px 2px rgba(0,0,0,0.05)
const shadows = [
  {
    name: 'Shadow/Subtle',
    effects: [{
      type: 'DROP_SHADOW',
      color: { r: 0, g: 0, b: 0, a: 0.05 },
      offset: { x: 0, y: 1 },
      radius: 2,
      spread: 0,
      visible: true,
      blendMode: 'NORMAL'
    }]
  },
  {
    // CSS: 0 4px 6px -1px rgba(0,0,0,0.10), 0 2px 4px -1px rgba(0,0,0,0.06)
    name: 'Shadow/Medium',
    effects: [
      {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.10 },
        offset: { x: 0, y: 4 },
        radius: 6,
        spread: -1,
        visible: true,
        blendMode: 'NORMAL'
      },
      {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.06 },
        offset: { x: 0, y: 2 },
        radius: 4,
        spread: -1,
        visible: true,
        blendMode: 'NORMAL'
      }
    ]
  },
  {
    // CSS: 0 10px 15px -3px rgba(0,0,0,0.10), 0 4px 6px -2px rgba(0,0,0,0.05)
    name: 'Shadow/Strong',
    effects: [
      {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.10 },
        offset: { x: 0, y: 10 },
        radius: 15,
        spread: -3,
        visible: true,
        blendMode: 'NORMAL'
      },
      {
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.05 },
        offset: { x: 0, y: 4 },
        radius: 6,
        spread: -2,
        visible: true,
        blendMode: 'NORMAL'
      }
    ]
  }
];

// M3-style dual shadow (umbra + penumbra pattern):
const m3Shadows = [
  {
    name: 'Elevation/1',
    effects: [
      { type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.30}, offset:{x:0,y:1}, radius:2, spread:0, visible:true, blendMode:'NORMAL' },
      { type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.15}, offset:{x:0,y:1}, radius:3, spread:1, visible:true, blendMode:'NORMAL' }
    ]
  },
  {
    name: 'Elevation/2',
    effects: [
      { type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.30}, offset:{x:0,y:1}, radius:2, spread:0, visible:true, blendMode:'NORMAL' },
      { type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.15}, offset:{x:0,y:2}, radius:6, spread:2, visible:true, blendMode:'NORMAL' }
    ]
  },
  {
    name: 'Elevation/3',
    effects: [
      { type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.30}, offset:{x:0,y:1}, radius:3, spread:0, visible:true, blendMode:'NORMAL' },
      { type: 'DROP_SHADOW', color: {r:0,g:0,b:0,a:0.15}, offset:{x:0,y:4}, radius:8, spread:3, visible:true, blendMode:'NORMAL' }
    ]
  }
];

const created = [];
for (const { name, effects } of shadows) {
  const style = figma.createEffectStyle();
  style.name = name;
  style.effects = effects;
  style.setSharedPluginData('dsb', 'run_id', RUN_ID);
  style.setSharedPluginData('dsb', 'key', `effect-style/${name}`);
  created.push({ name, id: style.id });
}

return { created, count: created.length };
```

#### Creating Text Styles

Fonts must be loaded before creating text styles.

```javascript
const RUN_ID = "ds-build-2024-001";

// Define text styles — based on SDS typography hierarchy
const textStyles = [
  // Display / Hero
  { name: 'Display/Hero',    family: 'Inter', style: 'Bold',      size: 72, lineHeight: 80, letterSpacing: -1.5 },
  // Headings
  { name: 'Heading/H1',      family: 'Inter', style: 'Bold',      size: 48, lineHeight: 56, letterSpacing: -1.0 },
  { name: 'Heading/H2',      family: 'Inter', style: 'Bold',      size: 40, lineHeight: 48, letterSpacing: -0.5 },
  { name: 'Heading/H3',      family: 'Inter', style: 'Semi Bold', size: 32, lineHeight: 40, letterSpacing: 0 },
  { name: 'Heading/H4',      family: 'Inter', style: 'Semi Bold', size: 24, lineHeight: 32, letterSpacing: 0 },
  // Body
  { name: 'Body/Large',      family: 'Inter', style: 'Regular',   size: 18, lineHeight: 28, letterSpacing: 0 },
  { name: 'Body/Medium',     family: 'Inter', style: 'Regular',   size: 16, lineHeight: 24, letterSpacing: 0 },
  { name: 'Body/Small',      family: 'Inter', style: 'Regular',   size: 14, lineHeight: 20, letterSpacing: 0 },
  // Label
  { name: 'Label/Large',     family: 'Inter', style: 'Medium',    size: 14, lineHeight: 20, letterSpacing: 0.1 },
  { name: 'Label/Medium',    family: 'Inter', style: 'Medium',    size: 12, lineHeight: 16, letterSpacing: 0.5 },
  { name: 'Label/Small',     family: 'Inter', style: 'Medium',    size: 11, lineHeight: 16, letterSpacing: 0.5 },
  // Code
  { name: 'Code/Base',       family: 'Roboto Mono', style: 'Regular', size: 14, lineHeight: 20, letterSpacing: 0 },
];

// Verify fonts are available, then load them
const allFonts = await figma.listAvailableFontsAsync();
const availableFontNames = new Set(allFonts.map(f => JSON.stringify(f.fontName)));
const fontSet = new Set(textStyles.map(s => JSON.stringify({ family: s.family, style: s.style })));
for (const f of fontSet) {
  if (!availableFontNames.has(f)) {
    const parsed = JSON.parse(f);
    const familyFonts = allFonts.filter(af => af.fontName.family === parsed.family);
    throw new Error(`Font "${parsed.family} ${parsed.style}" not available. Available styles: ${familyFonts.map(af => af.fontName.style).join(', ') || 'none'}`);
  }
}
await Promise.all([...fontSet].map(f => figma.loadFontAsync(JSON.parse(f))));

const created = [];
for (const { name, family, style, size, lineHeight, letterSpacing } of textStyles) {
  const ts = figma.createTextStyle();
  ts.name = name;
  ts.fontName = { family, style };
  ts.fontSize = size;
  ts.lineHeight = { value: lineHeight, unit: 'PIXELS' };
  ts.letterSpacing = { value: letterSpacing, unit: 'PIXELS' };
  ts.setSharedPluginData('dsb', 'run_id', RUN_ID);
  ts.setSharedPluginData('dsb', 'key', `text-style/${name}`);
  created.push({ name, id: ts.id });
}

return { created, count: created.length };
```

---

### 8. Idempotency — Check-Before-Create Pattern

Every creation script should check whether the entity already exists before creating it. This prevents duplicates when a script is re-run after partial failure.

#### Check-Before-Create for Collections

```javascript
const DSB_KEY = 'collection/primitives';
const RUN_ID = "ds-build-2024-001";

// Check if already exists
const existing = await figma.variables.getLocalVariableCollectionsAsync();
let primColl = existing.find(c => c.getSharedPluginData('dsb', 'key') === DSB_KEY);

if (primColl) {
  return { status: 'already_exists', collectionId: primColl.id, name: primColl.name };
}

// Create only if not found
primColl = figma.variables.createVariableCollection("Primitives");
primColl.renameMode(primColl.modes[0].modeId, "Value");
primColl.setSharedPluginData('dsb', 'run_id', RUN_ID);
primColl.setSharedPluginData('dsb', 'key', DSB_KEY);

return { status: 'created', collectionId: primColl.id };
```

#### Check-Before-Create for Variables

```javascript
const VARIABLE_KEY = 'primitive/blue/500';
const RUN_ID = "ds-build-2024-001";

// Check if already exists by sharedPluginData key
const allVars = await figma.variables.getLocalVariablesAsync();
const existing = allVars.find(v => v.getSharedPluginData('dsb', 'key') === VARIABLE_KEY);

if (existing) {
  return { status: 'already_exists', id: existing.id, name: existing.name };
}

// ... create the variable ...
return { status: 'created' };
```

#### sharedPluginData Tagging Strategy

Tag every created node immediately after creation. The `key` is the stable logical identifier used for idempotency checks. The `run_id` identifies which build run created it (useful for cleanup).

```javascript
node.setSharedPluginData('dsb', 'run_id', RUN_ID);       // build run ID
node.setSharedPluginData('dsb', 'phase', 'phase1');       // which phase
node.setSharedPluginData('dsb', 'key', 'color/bg/primary'); // stable logical key
```

**Cleanup by run ID (safe — targets only tagged nodes, never user-owned nodes):**

```javascript
const TARGET_RUN_ID = "ds-build-2024-001"; // run to remove
const allVars = await figma.variables.getLocalVariablesAsync();
const removed = [];
for (const v of allVars) {
  if (v.getSharedPluginData('dsb', 'run_id') === TARGET_RUN_ID) {
    removed.push(v.name);
    v.remove();
  }
}
return { removed, count: removed.length };
```

**Never clean up by name prefix** (e.g., deleting everything starting with `color/`). This will destroy user-created variables that happen to share the prefix.

---

### 9. Validation — Verify Counts, Aliases, and Scopes

Run these scripts after Phase 1 to verify everything was created correctly before proceeding to Phase 2.

#### Verify Collection and Variable Counts

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const allVars = await figma.variables.getLocalVariablesAsync();

const summary = collections.map(c => {
  const vars = allVars.filter(v => v.variableCollectionId === c.id);
  return {
    name: c.name,
    id: c.id,
    modes: c.modes.map(m => m.name),
    variableCount: vars.length,
    missingScopes: vars.filter(v => v.scopes.length === 0 && v.resolvedType !== 'BOOLEAN').length,
    missingCodeSyntax: vars.filter(v => !v.codeSyntax['WEB'] && !v.remote).length,
    sampleVariables: vars.slice(0, 3).map(v => v.name)
  };
});

return {
  collectionCount: collections.length,
  totalVariables: allVars.length,
  collections: summary
};
```

Interpret: `missingScopes > 0` (for non-primitives and non-BOOLEANs) → scope-setting failed, re-run scope script. `missingCodeSyntax > 0` → code syntax not set, run batch code syntax script.

Note: primitives correctly have `scopes = []` (empty, hidden). `missingScopes` above counts non-BOOLEAN variables with empty scopes — review the list to confirm they are all primitives.

#### Verify Aliases Resolve

```javascript
const allVars = await figma.variables.getLocalVariablesAsync();
const collections = await figma.variables.getLocalVariableCollectionsAsync();

const brokenAliases = [];
const aliasedVars = [];

for (const v of allVars) {
  if (v.remote) continue;
  const coll = collections.find(c => c.id === v.variableCollectionId);
  if (!coll) continue;

  for (const [modeId, val] of Object.entries(v.valuesByMode)) {
    if (val && typeof val === 'object' && val.type === 'VARIABLE_ALIAS') {
      aliasedVars.push({ name: v.name, aliasTargetId: val.id });
      // Verify the target exists
      const target = allVars.find(t => t.id === val.id);
      if (!target) {
        brokenAliases.push({ variable: v.name, modeId, missingTargetId: val.id });
      }
    }
  }
}

return {
  totalAliased: aliasedVars.length,
  brokenAliases,
  brokenCount: brokenAliases.length,
  status: brokenAliases.length === 0 ? 'all_aliases_resolve' : 'BROKEN_ALIASES_FOUND'
};
```

Interpret: `brokenCount > 0` means a semantic variable references a primitive that was deleted or not yet created. Create the missing primitives, then re-run alias creation for the affected semantic variables.

#### Verify Style Counts

```javascript
const [textStyles, effectStyles] = await Promise.all([
  figma.getLocalTextStylesAsync(),
  figma.getLocalEffectStylesAsync()
]);

return {
  textStyles: textStyles.map(s => ({ name: s.name, fontSize: s.fontSize, fontFamily: s.fontName.family })),
  effectStyles: effectStyles.map(s => ({ name: s.name, effectCount: s.effects.length })),
  counts: { text: textStyles.length, effect: effectStyles.length }
};
```

#### Phase 1 Exit Criteria Checklist

Before proceeding to Phase 2, verify all of the following:

- Every planned collection exists with the correct number of modes
- Primitive variables: `scopes = []`, code syntax set
- Semantic variables: targeted scopes set, code syntax set, aliases pointing to primitives (not raw values)
- All broken alias count = 0
- All planned text styles exist with correct font family/size/weight
- All planned effect styles exist with correct shadow values
- No variable has `ALL_SCOPES` unless explicitly approved by the user

---

## Reference — Discovery Phase Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

This document covers everything needed for Phase 0 of a design system build: analyzing the codebase for tokens, inspecting the Figma file for existing conventions, searching subscribed libraries, building the plan, and resolving conflicts before any write operations begin.

---

### 1. Codebase Analysis — Finding Token Sources

#### Search Priority Order

Look for token sources in this order. Stop as soon as you find a definitive source; multiple formats can coexist:

1. Design token files: `*.tokens.json`, `tokens/*.json`, `src/tokens/**`
2. CSS variable files: `variables.css`, `tokens.css`, `theme.css`, `global.css`
3. Tailwind config: `tailwind.config.js`, `tailwind.config.ts`
4. CSS-in-JS theme objects: `theme.ts`, `createTheme`, `ThemeProvider`
5. Platform-specific: iOS Asset catalogs (`.xcassets`), Android `themes.xml`, `colors.xml`

#### CSS Custom Properties (Most Common for Web)

**What to search for:**

```
:root { ... }
@theme { ... }          ← Tailwind v4
--color-*, --spacing-*, --radius-*, --shadow-*, --font-*
```

**Pattern:** `/--[\w-]+:\s*[^;]+/g`

**Common file locations:** `src/styles/tokens.css`, `src/styles/variables.css`, `src/theme/*.css`

**Extraction and naming translation:**

| CSS Property | Figma Variable Name | Figma Type | WEB Code Syntax |
|---|---|---|---|
| `--color-bg-primary: #fff` | `color/bg/primary` | COLOR | `var(--color-bg-primary)` |
| `--color-text-secondary: #757575` | `color/text/secondary` | COLOR | `var(--color-text-secondary)` |
| `--spacing-sm: 8px` | `spacing/sm` | FLOAT | `var(--spacing-sm)` |
| `--radius-md: 8px` | `radius/md` | FLOAT | `var(--radius-md)` |
| `--font-body: "Inter"` | `typography/body/font-family` | STRING | `var(--font-body)` |

**Naming rule:** Replace hyphens with slashes at category boundaries. Keep hyphens within the final path segment: `--color-bg-primary` → `color/bg/primary`, but `--color-bg-primary-hover` → `color/bg/primary-hover`.

**Always store the original CSS variable name** as the code syntax value — never derive it from the Figma variable name. If the codebase uses `--sds-color-background-brand-default`, use exactly that string in `setVariableCodeSyntax('WEB', '--sds-color-background-brand-default')`.

#### Tailwind Configuration

**What to look for in `tailwind.config.js` or `tailwind.config.ts`:**

```javascript
// theme.extend.colors → Figma color variables
{ primary: { DEFAULT: '#3366FF', light: '#6699FF', dark: '#0033CC' } }
// → color/primary/default, color/primary/light, color/primary/dark

// theme.extend.spacing → Figma FLOAT variables
{ 'xs': '4px', 'sm': '8px', 'md': '16px' }
// → spacing/xs = 4, spacing/sm = 8, spacing/md = 16

// theme.extend.borderRadius → Figma FLOAT variables
{ 'sm': '4px', 'md': '8px', 'lg': '16px' }
// → radius/sm = 4, radius/md = 8, radius/lg = 16
```

Tailwind utility class names (`bg-blue-500`, `p-4`) are not tokens — extract values from the config object, not the class names.

#### Design Token Community Group (DTCG) Format

**Pattern:** `*.tokens.json` or `tokens/*.json`. Find source files, not generated outputs from Style Dictionary or Tokens Studio.

```json
{
  "color": {
    "bg": {
      "primary": { "$type": "color", "$value": "#ffffff" },
      "secondary": { "$type": "color", "$value": "#f5f5f5" }
    }
  },
  "spacing": {
    "sm": { "$type": "dimension", "$value": "8px" }
  }
}
```

Nested keys map to slash-separated Figma names: `color.bg.primary` → `color/bg/primary`.

#### CSS-in-JS / Theme Objects

**What to search for:** `createTheme`, `ThemeProvider`, `theme = {}`, styled-components, Emotion, Stitches, vanilla-extract

```typescript
// theme.colors.bg.primary → Figma variable: color/bg/primary
// theme.spacing.sm        → Figma variable: spacing/sm
// Multiple theme objects (lightTheme, darkTheme) → modes in the same collection
```

#### iOS Token Sources

```swift
// Asset catalog colors in .xcassets/Colors.xcassets
// extension Color { static let bgPrimary = Color("bg-primary") }
// Look for traitCollection.userInterfaceStyle for dark mode detection
```

#### Android Token Sources

```kotlin
// res/values/colors.xml  <color name="primary">#3366FF</color>
// res/values-night/colors.xml  (dark mode overrides)
// MaterialTheme.colorScheme.primary in Compose
// val Primary = Color(0xFF3366FF)
```

#### Detecting Dark Mode

| Platform | Signal |
|---|---|
| Web (CSS) | `@media (prefers-color-scheme: dark)`, `.dark { }`, `[data-theme="dark"]` |
| Web (Tailwind) | `darkMode: 'class'` or `darkMode: 'media'` in config |
| Web (JS) | Separate `darkTheme` object alongside `lightTheme` |
| iOS | `Color(uiColor:)` with `traitCollection.userInterfaceStyle`, dual-appearance asset catalog |
| Android | `themes.xml` with `Theme.*.Night`, `isSystemInDarkTheme()` in Compose, `values-night/` folder |

**Figma mapping:** If dark mode exists → minimum 2 modes (Light/Dark) in the semantic color collection. Primitive collections stay single-mode.

#### Shadow/Elevation Extraction

Shadows cannot be Figma variables — they become **Effect Styles**.

```css
/* Look for: box-shadow, --shadow-* */
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.10);
--shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.10);
```

CSS `0 4px 6px -1px rgba(0,0,0,0.1)` → Figma:
```
{ type: "DROP_SHADOW", offset: {x:0, y:4}, radius: 6, spread: -1, color: {r:0, g:0, b:0, a:0.1} }
```

#### Typography Extraction

| Code token | Maps to |
|---|---|
| `font-size: 16px` | FLOAT variable (scope `FONT_SIZE`) or Text Style `fontSize` |
| `line-height: 1.5` | Text Style `lineHeight: {value: 24, unit: "PIXELS"}` |
| `font-weight: 600` | STRING variable (scope `FONT_STYLE`, holds a font-specific style name like `"Regular"` — discover via `listAvailableFontsAsync()`) or Text Style `fontName.style` |
| `letter-spacing: -0.02em` | Text Style `letterSpacing: {value: -2, unit: "PERCENT"}` |
| `font-family: "Inter"` | STRING variable (scope `FONT_FAMILY`) or Text Style `fontName.family` |

Composite text styles (all properties bundled) → Figma Text Styles. Individual properties → Figma variables with appropriate scopes.

#### Component Extraction

For each component, extract:

1. **Name** → Figma component set name
2. **Union-type props** → VARIANT properties
3. **String content props** → TEXT properties
4. **Boolean props** → BOOLEAN properties (and VARIANT State when combined with interaction states)
5. **Child/slot props** → INSTANCE_SWAP properties

```typescript
// React example:
interface ButtonProps {
  size: 'sm' | 'md' | 'lg';          // → VARIANT: Size = sm|md|lg
  variant: 'primary' | 'secondary';   // → VARIANT: Style = primary|secondary
  disabled?: boolean;                  // → VARIANT: State (combine: default|hover|pressed|disabled)
  label: string;                       // → TEXT: Label
  icon?: ReactNode;                    // → INSTANCE_SWAP: Icon + BOOLEAN: Show Icon
}
// → Component Set "Button", variant count: 3 sizes × 2 styles × 4 states = 24
```

---

### 2. Figma File Inspection

Run these `use_figma` snippets at the start of every build. All are read-only and safe to run before any user checkpoint.

#### List All Pages

```javascript
const pages = figma.root.children.map((p, i) => ({
  index: i,
  name: p.name,
  id: p.id,
  childCount: p.children.length
}));
return { pages };
```

Interpret: note page names for naming convention (are they PascalCase? sentence case?), count separator pages (`---`), identify existing component pages vs foundations pages.

#### List Variable Collections With Modes

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const result = collections.map(c => ({
  id: c.id,
  name: c.name,
  modes: c.modes,                    // [{modeId, name}, ...]
  variableCount: c.variableIds.length,
  defaultModeId: c.defaultModeId
}));
return { collections: result };
```

Interpret: identify existing primitive/semantic split, note mode names (do they use "Light/Dark" or "SDS Light/SDS Dark"?), count variables to understand scope.

#### List Variables in a Collection (with names, types, scopes, and sample values)

```javascript
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const targetName = "Color"; // change to the collection you want to inspect
const coll = collections.find(c => c.name === targetName);
if (!coll) { return { error: `Collection "${targetName}" not found` }; }

const allVars = await figma.variables.getLocalVariablesAsync();
const vars = allVars.filter(v => v.variableCollectionId === coll.id);

const result = vars.map(v => ({
  id: v.id,
  name: v.name,
  resolvedType: v.resolvedType,
  scopes: v.scopes,
  codeSyntax: v.codeSyntax,
  // First mode value only, for a sample
  sampleValue: v.valuesByMode[coll.defaultModeId]
}));

return { collection: coll.name, variableCount: result.length, variables: result };
```

Interpret: check if variables use `ALL_SCOPES` (bad), check naming convention (slash-separated hierarchy?), check if code syntax is set, identify alias chains.

#### List Component Sets with Properties

```javascript
// To inspect a specific page, switch to it first:
// await figma.setCurrentPageAsync(targetPage);
const componentSets = figma.currentPage.findAllWithCriteria({ types: ['COMPONENT_SET'] });
const result = componentSets.map(cs => ({
  id: cs.id,
  name: cs.name,
  variantCount: cs.children.length,
  properties: Object.entries(cs.componentPropertyDefinitions).map(([key, def]) => ({
    name: key,
    type: def.type,
    variantOptions: def.variantOptions || null,
    defaultValue: def.defaultValue
  }))
}));
return { componentSets: result, count: result.length };
```

Note: to search ALL pages, **do not iterate `figma.root.children` and `setCurrentPageAsync` inside one script.** Run a cheap discovery call first (`figma.root.children.map(p => ({id: p.id, name: p.name}))`), then in the next assistant turn emit **one `use_figma` per page in parallel** — a single message with N tool-use blocks — each setting `currentPage` once. See figma-use → gotchas.md → Set current page once per `use_figma` call (load `readPowerSteering("figma", "figma-use.md")`).

#### List All Styles

```javascript
const [textStyles, effectStyles, paintStyles] = await Promise.all([
  figma.getLocalTextStylesAsync(),
  figma.getLocalEffectStylesAsync(),
  figma.getLocalPaintStylesAsync()
]);

return {
  textStyles: textStyles.map(s => ({ id: s.id, name: s.name, fontSize: s.fontSize, fontName: s.fontName })),
  effectStyles: effectStyles.map(s => ({ id: s.id, name: s.name, effectCount: s.effects.length })),
  paintStyles: paintStyles.map(s => ({ id: s.id, name: s.name })),
  counts: { text: textStyles.length, effect: effectStyles.length, paint: paintStyles.length }
};
```

#### Check Naming Conventions on an Existing Component

```javascript
// Replace with the node ID of an existing component to analyze
const node = await figma.getNodeByIdAsync("YOUR_NODE_ID");
if (!node) { return { error: "Node not found" }; }

// Check fills for variable bindings
const fillInfo = [];
if ('fills' in node && Array.isArray(node.fills)) {
  for (const fill of node.fills) {
    if (fill.type === 'SOLID' && fill.boundVariables?.color) {
      fillInfo.push({ type: 'variable_alias', id: fill.boundVariables.color.id });
    } else if (fill.type === 'SOLID') {
      fillInfo.push({ type: 'hardcoded', r: fill.color.r, g: fill.color.g, b: fill.color.b });
    }
  }
}

return {
  name: node.name,
  type: node.type,
  fills: fillInfo,
  sharedPluginData: node.getSharedPluginData('dsb', 'key') || null
};
```

---

### 3. Library Discovery and search_design_system

#### Step 1: Discover available libraries with `get_libraries`

Before searching, call `get_libraries` to see what libraries the file has access to:

```
get_libraries({ fileKey: "abc123" })
// offset is optional; omit (or pass 0) for the first page
```

Returns:
- **`libraries_added_to_file`** — libraries currently subscribed (team libraries, community UI kits already enabled)
- **`libraries_available_to_add`** — community UI kits and org libraries not yet subscribed
- **`libraries_available_to_add_next_offset`** — non-null when more org libraries are available; pass it back as `offset` to fetch the next page

Each library entry includes `name`, `libraryKey`, `description`, and `source` ("team", "community", or "organization"). Use the `libraryKey` values to scope searches in the next step.

**Pagination.** Org libraries paginate in batches of 20. Community UI kits are only returned on the first page (`offset=0`), so subsequent pages contain only org libraries. If the user is looking for a specific library by name and it isn't in the current page, page further (call `get_libraries` again with `offset: libraries_available_to_add_next_offset`) or ask them to subscribe it to the file.

```
// Page 1
get_libraries({ fileKey: "abc123" })
// → { ..., libraries_available_to_add_next_offset: 20 }

// Page 2
get_libraries({ fileKey: "abc123", offset: 20 })
// → { ..., libraries_available_to_add_next_offset: 40 | null }
```

#### Step 2: Search with `search_design_system`

`search_design_system` runs three parallel searches against design libraries for the given file:

1. **Components** — published library components, searched by name/description via a recommendation engine (relevance-ranked, not exact match)
2. **Variables** — design tokens (colors, spacing, etc.) across subscribed libraries
3. **Styles** — paint styles, text styles, and effect styles

By default it searches all accessible libraries. Pass `includeLibraryKeys` to search within specific libraries only. This is useful when you have many libraries and want targeted results.

#### Input

```
// Search all libraries
search_design_system({
  query: "button",              // required — text query
  fileKey: "abc123",            // required — your file key
  includeComponents: true,      // default true
  includeVariables: true,       // default true
  includeStyles: true           // default true
})

// Search a specific library only (use libraryKey from get_libraries)
search_design_system({
  query: "button",
  fileKey: "abc123",
  includeLibraryKeys: ["lk-abc123..."],
  includeComponents: true
})
```

#### What It Returns

```json
{
  "components": [
    {
      "name": "Button",
      "libraryName": "Design System",
      "assetType": "component_set",
      "componentKey": "abc123def",
      "description": "Primary action button"
    }
  ],
  "variables": [
    {
      "name": "colors/primary/500",
      "variableType": "COLOR",
      "variableSetKey": "set1key",
      "key": "var1key",
      "scopes": ["FRAME_FILL", "SHAPE_FILL"],
      "variableCollectionName": "Colors"
    }
  ],
  "styles": [
    {
      "name": "Heading/H1",
      "styleType": "TEXT",
      "key": "style1key"
    }
  ]
}
```

#### How to Interpret Results

**Components:** The `componentKey` can be used in `use_figma` to import the component:
```javascript
const component = await figma.importComponentByKeyAsync("abc123def");
// or for component sets:
const componentSet = await figma.importComponentSetByKeyAsync("abc123def");
```

**Variables:** The `variableSetKey` is the collection key. The `key` is the variable key. Use these to understand what naming conventions are in use, and what tokens are available to alias from.

**Styles:** The `key` is usable with `figma.importStyleByKeyAsync(key)` to import into the current file.

#### When to Search

- **Phase 0, step 0c**: Search broadly (`query: "button"`, `query: "color"`, `query: "spacing"`) before planning anything. This establishes the reuse baseline.
- **Immediately before each component creation**: Search for the specific component name before writing any `use_figma` creation code.

**Reuse decision:**

| Condition | Decision |
|---|---|
| Found component with matching variant API, same token model | Import and reuse |
| Found component but wrong variant properties or hardcoded values | Rebuild |
| Found component that matches visually but API is incompatible | Wrap: nest as instance inside a new wrapper component |

---

### 4. Building the Plan

After codebase analysis and Figma inspection, produce a mapping table and present it to the user.

#### Token → Variable Mapping Table

For each token found in code, record:

| Code Token | CSS Name | Raw Value | Figma Collection | Figma Variable Name | Figma Type | Mode(s) |
|---|---|---|---|---|---|---|
| `theme.colors.blue[500]` | `--color-blue-500` | `#3B82F6` | Primitives | `blue/500` | COLOR | Value |
| `theme.colors.bg.primary` | `--color-bg-primary` | (light: blue/50, dark: gray/900) | Color | `color/bg/primary` | COLOR | Light, Dark |
| `theme.spacing.sm` | `--spacing-sm` | `8px` | Spacing | `spacing/sm` | FLOAT | Value |
| `theme.radii.md` | `--radius-md` | `8px` | Spacing | `radius/md` | FLOAT | Value |
| `theme.shadows.md` | `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | — | — | Effect Style | — |

#### Component → Component Set Mapping Table

| Code Component | Props → Variant Axes | Variant Count | Figma Page | Reuse? |
|---|---|---|---|---|
| `Button` | size (sm/md/lg) × variant (primary/secondary) × state (default/hover/disabled) | 18 | Buttons | Search first |
| `Avatar` | size (sm/md/lg) × type (image/initials/icon) | 9 | Avatars | Search first |

#### Gap Identification

Compare what was found in code vs what already exists in Figma:

- **New:** tokens or components that exist in code but not in Figma → create
- **Existing:** tokens or components already in Figma with matching names → verify scope/code-syntax, skip or update
- **Conflict:** same name, different value → escalate to user (see section 5)
- **Figma-only:** exists in Figma but not in code → flag for user, likely skip

#### User-Facing Checkpoint Message Template

Present this message before proceeding. Never begin Phase 1 without explicit user approval.

```
Here's what I found and what I plan to build:

CODEBASE ANALYSIS
  Colors: {N} primitives ({families}), {M} semantic tokens ({light/dark if applicable})
  Spacing: {N} tokens ({range})
  Typography: {N} text styles, {M} individual scale tokens
  Shadows: {N} levels → will become Effect Styles
  Components: {list of component names}

EXISTING FIGMA FILE
  Collections: {N} existing collections
  Variables: {M} existing variables
  Styles: {K} text, {L} effect, {J} paint styles
  Components: {list}

PLAN
  New collections: {list with mode counts}
  New variables: ~{N} ({breakdown by collection})
  New styles: {N} text, {M} effect
  New components: {list}
  Libraries to search before each component: {list}

GAPS / CONFLICTS NEEDING DECISIONS
  ⚠ {conflict description} — Code says X, Figma already has Y. Which wins?

WHAT I WON'T BUILD (and why)
  - {item}: already exists in Figma with matching conventions
  - {item}: not supported as a Figma variable (e.g. z-index, animation timing)

Shall I proceed?
```

---

### 5. Conflict Resolution — When Code and Figma Disagree

When the same token/component exists in both code and Figma but with different values, names, or structures, **always ask the user**. Never silently pick one.

#### Decision Framework

| Scenario | Ask the user |
|---|---|
| Same CSS name, different hex value (e.g., `--color-accent` is `#3366FF` in code but `#5B7FFF` in Figma) | "Code says `#3366FF`, Figma currently has `#5B7FFF` for `color/accent/default`. Which is correct?" |
| Same component name, different variant axes (code has `size: sm/md/lg`, Figma has `Size: Small/Large`) | "Code uses 3 sizes (sm/md/lg) but Figma has 2 (Small/Large). Should I add Medium, or rename to match code?" |
| Code has a semantic token with no primitive layer; Figma already has a fully-layered system | "The codebase uses a flat single-layer token model. The Figma file uses a primitive/semantic split. Should I match the Figma architecture or the code architecture?" |
| Figma variable exists but has `ALL_SCOPES` (incorrect per best practice) | "I found `color/bg/primary` already exists but it uses ALL_SCOPES. I recommend changing it to `FRAME_FILL, SHAPE_FILL`. May I update the scope?" |
| Code uses camelCase (`backgroundColor`), Figma uses slash-separated (`color/bg/default`) | "The codebase uses camelCase naming. The Figma file uses slash-separated hierarchy. For new variables, should I use slash-separated (Figma standard) and map via code syntax?" |

#### Code Wins

Default to code as the source of truth for:
- Hex values (code is the live production value)
- Token naming (the CSS variable names become code syntax)
- Mode values (light/dark split comes from code)

#### Figma Wins

Default to Figma as the source of truth for:
- Collection architecture (if a well-structured system already exists, extend it rather than replace it)
- Variable naming hierarchy (if designers are already using the system with specific names)
- Page structure (match the existing page organization pattern)

#### Neither: Negotiate

When neither is clearly correct, propose a resolution and ask:
> "I'd suggest [option]. This way both the code token name and the Figma naming convention are preserved. Does that work?"

---

## Reference — Documentation Creation Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

This reference covers Phase 2 of the design system build: the cover page, foundations documentation page (color swatches, type specimens, spacing bars, shadow cards, radius demo), page layout dimensions, and inline component documentation. Every code block is complete `use_figma`-ready JavaScript (helper-function form — meant to be embedded in a larger script that uses `return` to send results back).

> **Every text mutation in this file follows the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`):** load font → `await` → mutate → return affected IDs. Examples use `Inter` because it's available everywhere, but `loadFontAsync` is required for every (family, style) pair you mutate — not just Inter.

> **Design files only.** Every snippet here (including `figma.createPage()`) targets Figma Design files (`figma.com/design/...`). `figma.createPage()` throws in both FigJam (`figma.com/board/...`) and Slides (`figma.com/slides/...`).

---

### 1. Cover Page

The cover page is always the first page in the file. It is a branded title card that sets context for anyone opening the file.

#### What to include

- File/system name as a large heading (48–72px)
- Version string or date
- Brief tagline (1 sentence)
- Optional: color block background using the primary brand color variable

#### Cover page dimensions

The cover frame should be **1440 × 900px** — this matches the default Figma canvas and looks correct in the page thumbnail.

#### use_figma for cover page

```javascript
async function createCoverPage(systemName, tagline, version, primaryColorVar) {
  // primaryColorVar: a Figma Variable object for the brand primary fill
  const page = figma.createPage();
  page.name = 'Cover';
  await figma.setCurrentPageAsync(page);

  // Batch the font loads — sequential awaits would serialize three IPC
  // round-trips that can run in parallel.
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Bold' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Medium' }),
  ]);

  const frame = figma.createAutoLayout('VERTICAL');
  frame.name = 'Cover';
  frame.resize(1440, 900);
  frame.layoutSizingHorizontal = 'FIXED';
  frame.layoutSizingVertical = 'FIXED';
  frame.x = 0;
  frame.y = 0;
  frame.primaryAxisAlignItems = 'CENTER';
  frame.counterAxisAlignItems = 'CENTER';
  frame.itemSpacing = 16;

  // Background: bind to primary variable if provided, else solid dark
  if (primaryColorVar) {
    const bgPaint = figma.variables.setBoundVariableForPaint(
      { type: 'SOLID', color: { r: 0.05, g: 0.05, b: 0.05 } },
      'color',
      primaryColorVar
    );
    frame.fills = [bgPaint];
  } else {
    frame.fills = [{ type: 'SOLID', color: { r: 0.06, g: 0.06, b: 0.07 } }];
  }
  page.appendChild(frame);

  // System name heading
  const title = figma.createText();
  title.fontName = { family: 'Inter', style: 'Bold' };
  title.characters = systemName;
  title.fontSize = 64;
  title.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  title.textAlignHorizontal = 'CENTER';
  frame.appendChild(title);

  // Tagline
  const tag = figma.createText();
  tag.fontName = { family: 'Inter', style: 'Regular' };
  tag.characters = tagline;
  tag.fontSize = 20;
  tag.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1, a: 0.7 } }];
  tag.textAlignHorizontal = 'CENTER';
  frame.appendChild(tag);

  // Version
  const ver = figma.createText();
  ver.fontName = { family: 'Inter', style: 'Medium' };
  ver.characters = version;
  ver.fontSize = 13;
  ver.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1, a: 0.45 } }];
  ver.textAlignHorizontal = 'CENTER';
  frame.appendChild(ver);

  return { page, frameId: frame.id };
}
```

---

### 2. Foundations Page

The Foundations page is always placed **before any component pages**. It visually documents the design tokens — colors, typography, spacing, shadows, and border radii — so designers and engineers can see available primitives at a glance.

#### Page layout dimensions

The outer documentation frame should be **1440px wide**. Sections stack vertically with **64–100px gaps** between them. Each section frame fills the full 1440px width and hugs its content vertically.

#### Full Foundations page skeleton

```javascript
async function createFoundationsPage() {
  const page = figma.createPage();
  page.name = 'Foundations';
  await figma.setCurrentPageAsync(page);

  // Batch the font loads — sequential awaits would serialize three IPC
  // round-trips that can run in parallel.
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Bold' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Medium' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
  ]);

  // Root scroll frame
  const root = figma.createAutoLayout('VERTICAL');
  root.name = 'Foundations';
  root.primaryAxisAlignItems = 'MIN';
  root.counterAxisAlignItems = 'MIN';
  root.itemSpacing = 80;
  root.paddingTop = 80;
  root.paddingBottom = 120;
  root.paddingLeft = 80;
  root.paddingRight = 80;
  root.resize(1440, 1);
  root.layoutSizingHorizontal = 'FIXED';
  root.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  page.appendChild(root);

  return { page, root };
}
```

---

### 3. Color Swatches (bound to variables)

Color swatches must be **bound to actual Figma variables** — never hardcode hex values in swatch fills. This keeps documentation in sync automatically when variable values change.

#### Single color swatch

```javascript
/**
 * Creates a single color swatch card (rectangle + variable name label).
 * The swatch rectangle fill is bound to the provided variable.
 *
 * @param {FrameNode} parent - The auto-layout row to append to.
 * @param {string} varName - Display name (e.g. "color/bg/primary").
 * @param {Variable} variable - The Figma Variable object to bind to.
 * @returns {FrameNode} The swatch frame.
 */
async function createColorSwatch(parent, varName, variable) {
  await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });

  const swatchFrame = figma.createAutoLayout('VERTICAL');
  swatchFrame.name = `Swatch/${varName}`;
  swatchFrame.primaryAxisAlignItems = 'MIN';
  swatchFrame.counterAxisAlignItems = 'MIN';
  swatchFrame.itemSpacing = 6;
  swatchFrame.resize(88, 1);
  swatchFrame.layoutSizingHorizontal = 'FIXED';
  swatchFrame.fills = [];

  // Color rectangle — bound to variable
  const rect = figma.createRectangle();
  rect.resize(88, 88);
  rect.cornerRadius = 8;
  const paint = figma.variables.setBoundVariableForPaint(
    { type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } },
    'color',
    variable
  );
  rect.fills = [paint];
  swatchFrame.appendChild(rect);

  // Name label
  const label = figma.createText();
  label.fontName = { family: 'Inter', style: 'Regular' };
  label.characters = varName.split('/').pop(); // show leaf name only
  label.fontSize = 10;
  label.fills = [{ type: 'SOLID', color: { r: 0.35, g: 0.35, b: 0.35 } }];
  label.layoutSizingHorizontal = 'FILL';
  swatchFrame.appendChild(label);

  // Full path tooltip label (smaller, lighter)
  const pathLabel = figma.createText();
  pathLabel.fontName = { family: 'Inter', style: 'Regular' };
  pathLabel.characters = varName;
  pathLabel.fontSize = 9;
  pathLabel.fills = [{ type: 'SOLID', color: { r: 0.6, g: 0.6, b: 0.6 } }];
  pathLabel.layoutSizingHorizontal = 'FILL';
  swatchFrame.appendChild(pathLabel);

  parent.appendChild(swatchFrame);
  return swatchFrame;
}
```

#### Color section builder (primitives row + semantic grid)

```javascript
/**
 * Creates a complete color documentation section with a section heading,
 * a row of primitive swatches, and a grid of semantic swatches.
 *
 * @param {FrameNode} root - The root vertical stack frame.
 * @param {Variable[]} primitiveVars - Variables from the Primitives collection.
 * @param {Variable[]} semanticVars - Variables from the semantic Color collection.
 */
async function createColorSection(root, primitiveVars, semanticVars) {
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Bold' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
  ]);

  // Section container
  const section = figma.createAutoLayout('VERTICAL');
  section.name = 'Section/Colors';
  section.itemSpacing = 24;
  section.fills = [];
  root.appendChild(section);
  section.layoutSizingHorizontal = 'FILL';

  // Section heading
  const heading = figma.createText();
  heading.fontName = { family: 'Inter', style: 'Bold' };
  heading.characters = 'Colors';
  heading.fontSize = 32;
  heading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  section.appendChild(heading);

  // Description
  const desc = figma.createText();
  desc.fontName = { family: 'Inter', style: 'Regular' };
  desc.characters = 'Primitive color palette and semantic color tokens. Semantic tokens reference primitives — always use semantic tokens in components.';
  desc.fontSize = 14;
  desc.fills = [{ type: 'SOLID', color: { r: 0.4, g: 0.4, b: 0.4 } }];
  desc.layoutSizingHorizontal = 'FILL';
  section.appendChild(desc);

  // Primitive swatches row
  const primLabel = figma.createText();
  primLabel.fontName = { family: 'Inter', style: 'Bold' };
  primLabel.characters = 'Primitives';
  primLabel.fontSize = 13;
  primLabel.fills = [{ type: 'SOLID', color: { r: 0.55, g: 0.55, b: 0.55 } }];
  section.appendChild(primLabel);

  const primRow = figma.createAutoLayout();
  primRow.name = 'Primitives/Row';
  primRow.itemSpacing = 12;
  primRow.fills = [];
  primRow.layoutWrap = 'WRAP';
  section.appendChild(primRow);
  primRow.layoutSizingHorizontal = 'FILL';

  for (const v of primitiveVars) {
    await createColorSwatch(primRow, v.name, v);
  }

  // Semantic swatches grid
  if (semanticVars.length > 0) {
    const semLabel = figma.createText();
    semLabel.fontName = { family: 'Inter', style: 'Bold' };
    semLabel.characters = 'Semantic';
    semLabel.fontSize = 13;
    semLabel.fills = [{ type: 'SOLID', color: { r: 0.55, g: 0.55, b: 0.55 } }];
    section.appendChild(semLabel);

    const semRow = figma.createAutoLayout();
    semRow.name = 'Semantic/Row';
    semRow.itemSpacing = 12;
    semRow.fills = [];
    semRow.layoutWrap = 'WRAP';
    section.appendChild(semRow);
    semRow.layoutSizingHorizontal = 'FILL';

    for (const v of semanticVars) {
      await createColorSwatch(semRow, v.name, v);
    }
  }

  return section;
}
```

---

### 4. Type Specimens

Typography specimens show each text style rendered at its actual size with a sample string, the style name, and its specifications.

#### Single type specimen row

```javascript
/**
 * Creates a single type specimen row: style name (small label) + sample text +
 * specification line (family · style · size · line-height).
 *
 * @param {FrameNode} parent - The parent vertical stack.
 * @param {string} styleName - The text style name (e.g. "Display Large").
 * @param {string} fontFamily - Font family (e.g. "Inter").
 * @param {string} fontStyle - Font style (e.g. "Bold").
 * @param {number} fontSize - Font size in pixels.
 * @param {number} lineHeight - Line height in pixels.
 * @returns {FrameNode} The specimen row frame.
 */
async function createTypeSpecimen(parent, styleName, fontFamily, fontStyle, fontSize, lineHeight) {
  await Promise.all([
    figma.loadFontAsync({ family: fontFamily, style: fontStyle }),
    figma.loadFontAsync({ family: 'Inter', style: 'Medium' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
  ]);

  const row = figma.createAutoLayout('VERTICAL');
  row.name = `Type/${styleName}`;
  row.itemSpacing = 6;
  row.paddingTop = 16;
  row.paddingBottom = 16;
  row.fills = [];
  parent.appendChild(row);
  row.layoutSizingHorizontal = 'FILL';

  // Style name label (small, muted)
  const nameText = figma.createText();
  nameText.fontName = { family: 'Inter', style: 'Medium' };
  nameText.characters = styleName;
  nameText.fontSize = 11;
  nameText.fills = [{ type: 'SOLID', color: { r: 0.55, g: 0.55, b: 0.55 } }];
  nameText.layoutSizingHorizontal = 'FILL';
  row.appendChild(nameText);

  // Sample text rendered in the actual style
  const specimen = figma.createText();
  specimen.fontName = { family: fontFamily, style: fontStyle };
  specimen.characters = 'The quick brown fox jumps over the lazy dog';
  specimen.fontSize = fontSize;
  specimen.lineHeight = { value: lineHeight, unit: 'PIXELS' };
  specimen.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  specimen.layoutSizingHorizontal = 'FILL';
  row.appendChild(specimen);

  // Specification line
  const specs = figma.createText();
  specs.fontName = { family: 'Inter', style: 'Regular' };
  specs.characters = `${fontFamily} ${fontStyle} · ${fontSize}px · ${lineHeight}px line height`;
  specs.fontSize = 11;
  specs.fills = [{ type: 'SOLID', color: { r: 0.65, g: 0.65, b: 0.65 } }];
  specs.layoutSizingHorizontal = 'FILL';
  row.appendChild(specs);

  // Divider line
  const divider = figma.createRectangle();
  divider.resize(1280, 1);
  divider.fills = [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }];
  divider.layoutSizingHorizontal = 'FILL';
  row.appendChild(divider);

  return row;
}
```

#### Typography section builder

```javascript
/**
 * Creates a complete typography documentation section.
 * Pass an array of style definitions; the function renders one specimen per entry.
 *
 * @param {FrameNode} root - Root vertical stack.
 * @param {Array<{name, family, style, size, lineHeight}>} typeStyles - Style definitions.
 */
async function createTypographySection(root, typeStyles) {
  await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });

  const section = figma.createAutoLayout('VERTICAL');
  section.name = 'Section/Typography';
  section.itemSpacing = 0;
  section.fills = [];
  root.appendChild(section);
  section.layoutSizingHorizontal = 'FILL';

  const heading = figma.createText();
  heading.fontName = { family: 'Inter', style: 'Bold' };
  heading.characters = 'Typography';
  heading.fontSize = 32;
  heading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  section.appendChild(heading);

  for (const ts of typeStyles) {
    await createTypeSpecimen(section, ts.name, ts.family, ts.style, ts.size, ts.lineHeight);
  }

  return section;
}
```

---

### 5. Spacing Bars

Spacing bars show each spacing token as a filled rectangle whose width equals the spacing value. Shorter bars for small values, longer bars for large values — the visual encoding is immediate.

#### Spacing bar row

```javascript
/**
 * Creates a single spacing bar: a colored rectangle sized to the spacing value,
 * with a label showing name + pixel value + code syntax.
 *
 * @param {FrameNode} parent - Parent vertical stack.
 * @param {string} name - Token name (e.g. "spacing/sm").
 * @param {number} value - Spacing value in pixels.
 * @param {Variable} variable - Figma Variable to bind the width to.
 * @param {string} codeSyntax - CSS variable string (e.g. "var(--spacing-sm)").
 */
async function createSpacingBar(parent, name, value, variable, codeSyntax) {
  await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });

  const row = figma.createAutoLayout();
  row.name = `Spacing/${name}`;
  row.counterAxisAlignItems = 'CENTER';
  row.itemSpacing = 16;
  row.fills = [];
  parent.appendChild(row);
  row.layoutSizingHorizontal = 'FILL';

  // The bar rectangle — width bound to spacing variable
  const bar = figma.createRectangle();
  bar.resize(value, 16);
  bar.cornerRadius = 3;
  bar.fills = [{ type: 'SOLID', color: { r: 0.22, g: 0.47, b: 0.98 } }];
  // Bind width to the spacing variable so it reflects the actual token value
  if (variable) {
    bar.setBoundVariable('width', variable);
  }
  row.appendChild(bar);

  // Label: "spacing/sm  8px  var(--spacing-sm)"
  const label = figma.createText();
  label.fontName = { family: 'Inter', style: 'Regular' };
  label.characters = `${name}  ${value}px  ${codeSyntax}`;
  label.fontSize = 12;
  label.fills = [{ type: 'SOLID', color: { r: 0.35, g: 0.35, b: 0.35 } }];
  row.appendChild(label);

  return row;
}
```

#### Spacing section builder

```javascript
/**
 * Creates the full spacing documentation section.
 *
 * @param {FrameNode} root - Root vertical stack.
 * @param {Array<{name, value, variable, codeSyntax}>} spacingTokens - Token definitions.
 */
async function createSpacingSection(root, spacingTokens) {
  await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });

  const section = figma.createAutoLayout('VERTICAL');
  section.name = 'Section/Spacing';
  section.itemSpacing = 12;
  section.fills = [];
  root.appendChild(section);
  section.layoutSizingHorizontal = 'FILL';

  const heading = figma.createText();
  heading.fontName = { family: 'Inter', style: 'Bold' };
  heading.characters = 'Spacing';
  heading.fontSize = 32;
  heading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  section.appendChild(heading);

  for (const tok of spacingTokens) {
    await createSpacingBar(section, tok.name, tok.value, tok.variable, tok.codeSyntax);
  }

  return section;
}
```

---

### 6. Shadow Cards (Elevation)

Elevation documentation shows cards with progressively stronger drop shadows, labeled with name and effect parameters.

#### Single shadow card

```javascript
/**
 * Creates a shadow card: a white rectangle with a drop shadow effect,
 * labeled with the elevation name and shadow parameters.
 *
 * @param {FrameNode} parent - The horizontal row to append to.
 * @param {string} name - Elevation name (e.g. "Shadow/Medium").
 * @param {DropShadowEffect[]} effects - Array of Figma effect objects.
 */
async function createShadowCard(parent, name, effects) {
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Medium' }),
  ]);

  const card = figma.createAutoLayout('VERTICAL');
  card.name = `ShadowCard/${name}`;
  card.primaryAxisAlignItems = 'CENTER';
  card.counterAxisAlignItems = 'CENTER';
  card.itemSpacing = 8;
  card.paddingTop = 16;
  card.paddingBottom = 16;
  card.resize(120, 120);
  card.layoutSizingHorizontal = 'FIXED';
  card.layoutSizingVertical = 'FIXED';
  card.cornerRadius = 8;
  card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  card.effects = effects;
  parent.appendChild(card);

  // Elevation name
  const nameLabel = figma.createText();
  nameLabel.fontName = { family: 'Inter', style: 'Medium' };
  nameLabel.characters = name.split('/').pop();
  nameLabel.fontSize = 12;
  nameLabel.textAlignHorizontal = 'CENTER';
  nameLabel.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.2, b: 0.2 } }];
  card.appendChild(nameLabel);

  // Effect parameters as small text
  if (effects.length > 0) {
    const e = effects[0];
    if (e.type === 'DROP_SHADOW') {
      const params = figma.createText();
      params.fontName = { family: 'Inter', style: 'Regular' };
      params.characters = `x:${e.offset.x} y:${e.offset.y}\nblur:${e.radius}`;
      params.fontSize = 10;
      params.textAlignHorizontal = 'CENTER';
      params.fills = [{ type: 'SOLID', color: { r: 0.55, g: 0.55, b: 0.55 } }];
      card.appendChild(params);
    }
  }

  return card;
}
```

#### Shadow section builder

```javascript
/**
 * Creates the full elevation/shadow documentation section.
 *
 * @param {FrameNode} root - Root vertical stack.
 * @param {Array<{name, effects}>} shadowTokens - Shadow definitions.
 */
async function createShadowSection(root, shadowTokens) {
  await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });

  const section = figma.createAutoLayout('VERTICAL');
  section.name = 'Section/Elevation';
  section.itemSpacing = 24;
  section.fills = [];
  root.appendChild(section);
  section.layoutSizingHorizontal = 'FILL';

  const heading = figma.createText();
  heading.fontName = { family: 'Inter', style: 'Bold' };
  heading.characters = 'Elevation';
  heading.fontSize = 32;
  heading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  section.appendChild(heading);

  // Cards row — extra top padding so shadows are visible
  const row = figma.createAutoLayout();
  row.name = 'Elevation/Row';
  row.itemSpacing = 32;
  row.paddingTop = 24;
  row.paddingBottom = 40;
  row.paddingLeft = 24;
  row.paddingRight = 24;
  row.fills = [{ type: 'SOLID', color: { r: 0.97, g: 0.97, b: 0.97 } }];
  row.cornerRadius = 8;
  section.appendChild(row);
  row.layoutSizingHorizontal = 'FILL';

  for (const tok of shadowTokens) {
    await createShadowCard(row, tok.name, tok.effects);
  }

  return section;
}
```

---

### 7. Border Radius Demo

Border radius documentation shows rectangles at each corner radius value, labeled with the token name and pixel value.

#### Single radius card

```javascript
/**
 * Creates a single border radius card: a square with corner radius applied,
 * labeled with the token name and pixel value.
 *
 * @param {FrameNode} parent - The horizontal row to append to.
 * @param {string} name - Token name (e.g. "radius/md").
 * @param {number} value - Corner radius in pixels (0 for none, 9999 for full).
 * @param {Variable} [variable] - Optional Figma Variable to bind corner radius.
 */
async function createRadiusCard(parent, name, value, variable) {
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Medium' }),
  ]);

  const wrapper = figma.createAutoLayout('VERTICAL');
  wrapper.name = `Radius/${name}`;
  wrapper.primaryAxisAlignItems = 'CENTER';
  wrapper.counterAxisAlignItems = 'CENTER';
  wrapper.itemSpacing = 8;
  wrapper.fills = [];
  wrapper.resize(96, 1);
  wrapper.layoutSizingHorizontal = 'FIXED';
  parent.appendChild(wrapper);

  const rect = figma.createRectangle();
  rect.resize(72, 72);
  rect.fills = [{ type: 'SOLID', color: { r: 0.22, g: 0.47, b: 0.98, a: 0.15 } }];
  rect.strokes = [{ type: 'SOLID', color: { r: 0.22, g: 0.47, b: 0.98 } }];
  rect.strokeWeight = 1.5;

  // Cap display value — 9999 is how Figma represents "full/pill"
  const displayRadius = Math.min(value, 36);
  rect.cornerRadius = displayRadius;

  // Bind to variable if provided
  if (variable) {
    rect.setBoundVariable('cornerRadius', variable);
  }
  wrapper.appendChild(rect);

  const nameLabel = figma.createText();
  nameLabel.fontName = { family: 'Inter', style: 'Medium' };
  nameLabel.characters = name.split('/').pop();
  nameLabel.fontSize = 11;
  nameLabel.textAlignHorizontal = 'CENTER';
  nameLabel.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.2, b: 0.2 } }];
  wrapper.appendChild(nameLabel);

  const valueLabel = figma.createText();
  valueLabel.fontName = { family: 'Inter', style: 'Regular' };
  valueLabel.characters = value >= 9999 ? 'full' : `${value}px`;
  valueLabel.fontSize = 10;
  valueLabel.textAlignHorizontal = 'CENTER';
  valueLabel.fills = [{ type: 'SOLID', color: { r: 0.55, g: 0.55, b: 0.55 } }];
  wrapper.appendChild(valueLabel);

  return wrapper;
}
```

#### Radius section builder

```javascript
/**
 * Creates the full border radius documentation section.
 *
 * @param {FrameNode} root - Root vertical stack.
 * @param {Array<{name, value, variable}>} radiusTokens - Radius token definitions.
 */
async function createRadiusSection(root, radiusTokens) {
  await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });

  const section = figma.createAutoLayout('VERTICAL');
  section.name = 'Section/Radius';
  section.itemSpacing = 24;
  section.fills = [];
  root.appendChild(section);
  section.layoutSizingHorizontal = 'FILL';

  const heading = figma.createText();
  heading.fontName = { family: 'Inter', style: 'Bold' };
  heading.characters = 'Border Radius';
  heading.fontSize = 32;
  heading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  section.appendChild(heading);

  const row = figma.createAutoLayout();
  row.name = 'Radius/Row';
  row.itemSpacing = 24;
  row.paddingTop = 24;
  row.paddingBottom = 24;
  row.paddingLeft = 24;
  row.paddingRight = 24;
  row.fills = [{ type: 'SOLID', color: { r: 0.97, g: 0.97, b: 0.97 } }];
  row.cornerRadius = 8;
  section.appendChild(row);
  row.layoutSizingHorizontal = 'FILL';

  for (const tok of radiusTokens) {
    await createRadiusCard(row, tok.name, tok.value, tok.variable);
  }

  return section;
}
```

---

### 8. Documentation Alongside Components

Each component page should include a documentation frame directly on the canvas, placed to the left of the component set. This keeps docs and the component in sync without requiring a separate file.

#### Component page documentation frame

```javascript
/**
 * Creates the documentation frame for a component page: title, description,
 * and usage notes, positioned at x=0 with the component set to its right.
 *
 * @param {PageNode} page - The component page (must already be current).
 * @param {string} componentName - The component name.
 * @param {string} description - What the component does and when to use it.
 * @param {string[]} usageNotes - Bullet points for usage guidance.
 * @returns {FrameNode} The documentation frame.
 */
async function createComponentDocFrame(page, componentName, description, usageNotes) {
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Bold' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
  ]);

  const doc = figma.createAutoLayout('VERTICAL');
  doc.name = '_Doc';
  doc.itemSpacing = 16;
  doc.paddingTop = 40;
  doc.paddingBottom = 40;
  doc.paddingLeft = 40;
  doc.paddingRight = 40;
  doc.resize(360, 1);
  doc.layoutSizingHorizontal = 'FIXED';
  doc.fills = [];
  doc.x = 0;
  doc.y = 0;
  page.appendChild(doc);

  // Component name — large heading
  const title = figma.createText();
  title.fontName = { family: 'Inter', style: 'Bold' };
  title.characters = componentName;
  title.fontSize = 28;
  title.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
  title.layoutSizingHorizontal = 'FILL';
  doc.appendChild(title);

  // Description
  const descText = figma.createText();
  descText.fontName = { family: 'Inter', style: 'Regular' };
  descText.characters = description;
  descText.fontSize = 13;
  descText.lineHeight = { value: 20, unit: 'PIXELS' };
  descText.fills = [{ type: 'SOLID', color: { r: 0.35, g: 0.35, b: 0.35 } }];
  descText.layoutSizingHorizontal = 'FILL';
  doc.appendChild(descText);

  // Divider
  const divider = figma.createRectangle();
  divider.resize(280, 1);
  divider.fills = [{ type: 'SOLID', color: { r: 0.88, g: 0.88, b: 0.88 } }];
  divider.layoutSizingHorizontal = 'FILL';
  doc.appendChild(divider);

  // Usage notes
  if (usageNotes.length > 0) {
    const usageHeading = figma.createText();
    usageHeading.fontName = { family: 'Inter', style: 'Bold' };
    usageHeading.characters = 'Usage';
    usageHeading.fontSize = 13;
    usageHeading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }];
    doc.appendChild(usageHeading);

    for (const note of usageNotes) {
      const noteText = figma.createText();
      noteText.fontName = { family: 'Inter', style: 'Regular' };
      noteText.characters = `• ${note}`;
      noteText.fontSize = 12;
      noteText.lineHeight = { value: 18, unit: 'PIXELS' };
      noteText.fills = [{ type: 'SOLID', color: { r: 0.4, g: 0.4, b: 0.4 } }];
      noteText.layoutSizingHorizontal = 'FILL';
      doc.appendChild(noteText);
    }
  }

  return doc;
}
```

---

### 9. Critical Rules

1. **Bind swatches to variables** — use `setBoundVariableForPaint` for color fills, `setBoundVariable('width', ...)` for spacing bars, and `setBoundVariable('cornerRadius', ...)` for radius cards. Never hardcode values that have corresponding variables.
2. **Foundations page comes before component pages** — always insert it between the file structure separators and the first component page.
3. **Show both primitive and semantic layers** — if the system has a Primitives collection and a semantic Color collection, document both on the Foundations page with clear section labels.
4. **Page frame width = 1440px** — this is the convention across Simple DS, Polaris, and Material 3. Use it unless you detect a different existing convention via `get_metadata`.
5. **Section spacing = 64–80px** — the gap between color / typography / spacing / shadow / radius sections should be at minimum 64px so the page is scannable.
6. **Match existing page style** — if the target file uses emoji page name prefixes or a decorative separator style, carry that through to the Foundations page name.
7. **Include code syntax in labels** — where variables have code syntax set, display the CSS variable name in the swatch/bar label so developers can copy it directly.

---

## Reference — Component Creation Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

Complete guide for Phase 3: building components with variant matrices, variable bindings, component properties, and documentation.

> **Design files only.** Every snippet here (including `figma.createPage()`) targets Figma Design files (`figma.com/design/...`). `figma.createPage()` throws in both FigJam (`figma.com/board/...`) and Slides (`figma.com/slides/...`).
>
> **Every text mutation in this file follows the canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`):** load font → `await` → mutate → return affected IDs. Examples use `Inter` because it's available everywhere; `loadFontAsync` is required for every (family, style) pair you mutate, including non-Inter brand fonts.

---

### 1. Component Architecture

#### Dependency Ordering: Atoms Before Molecules

Always build in dependency order. A molecule that contains an atom instance cannot exist until the atom is published. Suggested ordering:

```
Tier 0 (atoms): Icon, Avatar, Badge, Spinner
Tier 1 (molecules): Button, Checkbox, Toggle, Input, Select
Tier 2 (organisms): Card, Dialog, Menu, Navigation, Form
```

If a component embeds an instance of another component, the embedded component must be created first. Build your dependency graph during Phase 0 and encode the creation order in the plan.

#### Building Blocks Sub-Components (M3 Pattern)

For complex components with independent sub-element state machines, extract the sub-element into its own component set prefixed with `Building Blocks/` (public) or `.Building Blocks/` (hidden from assets panel). The dot-prefix is a Figma convention for suppressing a component from the public assets panel.

**When to use Building Blocks:**
- The sub-element has its own variant axes (state, selection) that would cause combinatorial explosion in the parent
- The sub-element repeats (nav items, table cells, calendar cells, segmented button segments)
- The sub-element has different variant axes than the parent

**Example (M3 Segmented Button):**
```
Building Blocks/Segmented button/Button segment (start)   [27 variants: Config × State × Selected]
Building Blocks/Segmented button/Button segment (middle)  [27 variants]
Building Blocks/Segmented button/Button segment (end)     [27 variants]

Segmented button  [16 variants: Segments=2-5 × Density=0/-1/-2/-3]
  Each variant contains instances of the appropriate Building Block segment components.
```

The parent manages composition and configuration; the Building Block manages its own interaction states.

#### Private Components (`__` Prefix)

Use the `__` prefix for internal helper components that should not appear in the team library (Shop Minis pattern). Use `_` for documentation-only components (UI3 pattern).

```
__asset          // private icon/asset holder
_Label/Direction // documentation annotation helper
```

---

### 2. Creating the Component Page

Each component lives on its own dedicated page (one page per component is the default). The page contains: a documentation frame at top-left and the component set positioned to its right or below.

```javascript
// Create or find the component page
let page = figma.root.children.find(p => p.name === 'Button');
if (!page) {
  page = figma.createPage();
  page.name = 'Button';
}
await figma.setCurrentPageAsync(page);

// Documentation frame — positioned at (40, 40)
const docFrame = figma.createFrame();
docFrame.name = 'Button / Documentation';
docFrame.x = 40;
docFrame.y = 40;
docFrame.resize(600, 400);
docFrame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
docFrame.layoutMode = 'VERTICAL';
docFrame.primaryAxisSizingMode = 'AUTO';
docFrame.counterAxisSizingMode = 'FIXED';
docFrame.paddingTop = 40;
docFrame.paddingBottom = 40;
docFrame.paddingLeft = 40;
docFrame.paddingRight = 40;
docFrame.itemSpacing = 16;

// Title text node
await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
const title = figma.createText();
title.fontName = { family: 'Inter', style: 'Bold' };
title.fontSize = 32;
title.characters = 'Button';
docFrame.appendChild(title);

// Description text node
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
const desc = figma.createText();
desc.fontName = { family: 'Inter', style: 'Regular' };
desc.fontSize = 14;
desc.characters = 'Buttons allow users to take actions and make choices with a single tap.';
docFrame.appendChild(desc);

// Tag docFrame with sharedPluginData for idempotency
docFrame.setSharedPluginData('dsb', 'run_id', RUN_ID);
docFrame.setSharedPluginData('dsb', 'key', 'doc/button');

return { docFrameId: docFrame.id, pageId: page.id };
```

---

### 3. Base Component: Auto-Layout, Child Nodes, Variable Bindings

The base component is the template from which all variants are cloned. It must have:
1. Auto-layout (not manual positioning)
2. All child nodes present
3. ALL visual properties bound to variables (no hardcoded values)

#### Complete Button Base Component Example

```javascript
const RUN_ID = 'ds-build-2024-001'; // replace with your actual run ID
await figma.setCurrentPageAsync(
  figma.root.children.find(p => p.name === 'Button')
);

// Rehydrate variables from IDs stored in state ledger
const bgVar     = await figma.variables.getVariableByIdAsync('VAR_ID_color_bg_primary');
const textVar   = await figma.variables.getVariableByIdAsync('VAR_ID_color_text_on_primary');
const paddingVar = await figma.variables.getVariableByIdAsync('VAR_ID_spacing_md');
const radiusVar = await figma.variables.getVariableByIdAsync('VAR_ID_radius_md');
const gapVar    = await figma.variables.getVariableByIdAsync('VAR_ID_spacing_sm');

// --- Base component frame ---
const comp = figma.createComponent();
comp.name = 'Size=Medium, Style=Primary, State=Default';
comp.layoutMode = 'HORIZONTAL';
comp.primaryAxisSizingMode = 'AUTO';
comp.counterAxisSizingMode = 'AUTO';
comp.counterAxisAlignItems = 'CENTER';
comp.primaryAxisAlignItems = 'CENTER';

// Padding — bound to spacing variables
comp.setBoundVariable('paddingTop',    paddingVar);
comp.setBoundVariable('paddingBottom', paddingVar);
comp.setBoundVariable('paddingLeft',   paddingVar);
comp.setBoundVariable('paddingRight',  paddingVar);
comp.setBoundVariable('itemSpacing',   gapVar);

// Corner radius — bound to radius variable
comp.setBoundVariable('topLeftRadius',     radiusVar);
comp.setBoundVariable('topRightRadius',    radiusVar);
comp.setBoundVariable('bottomLeftRadius',  radiusVar);
comp.setBoundVariable('bottomRightRadius', radiusVar);

// Background fill — bound to color variable
const bgPaint = figma.variables.setBoundVariableForPaint(
  { type: 'SOLID', color: { r: 0, g: 0, b: 0 } },
  'color',
  bgVar
);
comp.fills = [bgPaint];

// --- Label text node ---
await figma.loadFontAsync({ family: 'Inter', style: 'Medium' });
const label = figma.createText();
label.name = 'label';
label.fontName = { family: 'Inter', style: 'Medium' };
label.fontSize = 14;
label.characters = 'Button';
label.layoutSizingHorizontal = 'HUG';
label.layoutSizingVertical = 'HUG';

// Text fill — bound to color variable
const textPaint = figma.variables.setBoundVariableForPaint(
  { type: 'SOLID', color: { r: 1, g: 1, b: 1 } },
  'color',
  textVar
);
label.fills = [textPaint];
comp.appendChild(label);

// --- Icon placeholder (Rectangle for now — will be INSTANCE_SWAP) ---
const iconBox = figma.createFrame();
iconBox.name = 'icon';
iconBox.resize(16, 16);
iconBox.fills = [];
iconBox.layoutSizingHorizontal = 'FIXED';
iconBox.layoutSizingVertical = 'FIXED';
comp.appendChild(iconBox);

// Tag for idempotency
comp.setSharedPluginData('dsb', 'run_id', RUN_ID);
comp.setSharedPluginData('dsb', 'phase', 'phase3');
comp.setSharedPluginData('dsb', 'key', 'component/button/base');

return { baseCompId: comp.id };
```

**ALL of these must be variable-bound (never hardcoded):**

| Property | Variable type | API method |
|---|---|---|
| Fill color | COLOR | `setBoundVariableForPaint(..., 'color', var)` |
| Stroke color | COLOR | `setBoundVariableForPaint(..., 'color', var)` |
| Text fill | COLOR | `setBoundVariableForPaint(..., 'color', var)` |
| Padding (all 4 sides) | FLOAT | `comp.setBoundVariable('paddingTop', var)` |
| Gap / itemSpacing | FLOAT | `comp.setBoundVariable('itemSpacing', var)` |
| Corner radius (all 4) | FLOAT | `comp.setBoundVariable('topLeftRadius', var)` etc. |
| Stroke weight | FLOAT | `comp.setBoundVariable('strokeWeight', var)` |

---

### 4. Variant Matrix

#### Defining Axes

For each component, identify its variant axes before writing any code. Standard axes:

```
Button:
  Size   → [Small, Medium, Large]
  Style  → [Primary, Secondary, Outline, Ghost]
  State  → [Default, Hover, Focused, Pressed, Disabled]
  Total  = 3 × 4 × 5 = 60 combinations — exceeds 30 limit → split by Style
```

#### The 30-Combination Cap and Split Strategy

When the product of all variant axes exceeds 30 combinations, split the matrix. Options:

1. **Split by a primary axis**: Create separate component sets, one per Style (Primary Button, Secondary Button, etc.)
2. **Use INSTANCE_SWAP**: Remove a visual axis (like Icon) from the variant matrix entirely and expose it as an INSTANCE_SWAP property instead
3. **Use Building Blocks**: Extract sub-elements with their own state axes into Building Block component sets

For Button with Size × State = 15 combinations, add Style as a variant axis only if Style ≤ 2 options (15 × 2 = 30). For more Styles, split.

#### Creating All Variants with use_figma

Build each variant by cloning the base component and adjusting the variable bindings that differ per variant. Pass in the base component ID from the previous call's state.

```javascript
const RUN_ID = 'ds-build-2024-001';
const BASE_COMP_ID = 'BASE_ID_FROM_STATE'; // from state ledger

await figma.setCurrentPageAsync(
  figma.root.children.find(p => p.name === 'Button')
);

const base = await figma.getNodeByIdAsync(BASE_COMP_ID);

// Variable IDs from state ledger
const vars = {
  // Primary style
  bg_primary:    await figma.variables.getVariableByIdAsync('VAR_ID_color_bg_primary'),
  text_primary:  await figma.variables.getVariableByIdAsync('VAR_ID_color_text_on_primary'),
  // Secondary style
  bg_secondary:  await figma.variables.getVariableByIdAsync('VAR_ID_color_bg_secondary'),
  text_secondary: await figma.variables.getVariableByIdAsync('VAR_ID_color_text_secondary'),
  // Disabled
  bg_disabled:   await figma.variables.getVariableByIdAsync('VAR_ID_color_bg_disabled'),
  text_disabled: await figma.variables.getVariableByIdAsync('VAR_ID_color_text_disabled'),
  // Sizes
  padding_sm: await figma.variables.getVariableByIdAsync('VAR_ID_spacing_sm'),
  padding_md: await figma.variables.getVariableByIdAsync('VAR_ID_spacing_md'),
  padding_lg: await figma.variables.getVariableByIdAsync('VAR_ID_spacing_lg'),
};

const axes = {
  Size:  ['Small', 'Medium', 'Large'],
  Style: ['Primary', 'Secondary'],
  State: ['Default', 'Hover', 'Disabled'],
};

const paddingBySize = { Small: vars.padding_sm, Medium: vars.padding_md, Large: vars.padding_lg };

const components = [];

for (const size of axes.Size) {
  for (const style of axes.Style) {
    for (const state of axes.State) {
      const clone = base.clone();
      clone.name = `Size=${size}, Style=${style}, State=${state}`;

      // Bind padding by size
      clone.setBoundVariable('paddingTop',    paddingBySize[size]);
      clone.setBoundVariable('paddingBottom', paddingBySize[size]);
      clone.setBoundVariable('paddingLeft',   paddingBySize[size]);
      clone.setBoundVariable('paddingRight',  paddingBySize[size]);

      // Bind fill by style + state
      const isDisabled = state === 'Disabled';
      const bgVar  = isDisabled ? vars.bg_disabled  : (style === 'Primary' ? vars.bg_primary  : vars.bg_secondary);
      const txtVar = isDisabled ? vars.text_disabled : (style === 'Primary' ? vars.text_primary : vars.text_secondary);

      const bgPaint = figma.variables.setBoundVariableForPaint(
        { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', bgVar
      );
      clone.fills = [bgPaint];

      const labelNode = clone.findOne(n => n.name === 'label');
      const textPaint = figma.variables.setBoundVariableForPaint(
        { type: 'SOLID', color: { r: 1, g: 1, b: 1 } }, 'color', txtVar
      );
      labelNode.fills = [textPaint];

      clone.setSharedPluginData('dsb', 'run_id', RUN_ID);
      clone.setSharedPluginData('dsb', 'key', `component/button/variant/${size}/${style}/${state}`);

      components.push(clone);
    }
  }
}

return { variantIds: components.map(c => c.id) };
```

---

### 5. `combineAsVariants` + Grid Layout

After all variant components exist, combine them into a ComponentSet and position them in a grid. This MUST be a separate `use_figma` call — you must pass in all variant IDs from the previous call's return value.

#### Grid Design Conventions

Professional design systems lay out variants in a readable grid where:
- **Columns** = the property users interact with most (typically **State**: Default, Hover, Focused, Pressed, Disabled)
- **Rows** = structural axes grouped together (typically **Size × Style**, where Size varies fastest)
- **Gap** = 16–40px between variants (20px is a safe default; match existing file if one exists)
- **Padding** = 40px around the grid inside the ComponentSet frame

```
Visual structure:
                    Default    Hover     Focused   Pressed   Disabled
  ┌──────────────────────────────────────────────────────────────────┐
  │  Small/Primary   [comp]    [comp]    [comp]    [comp]    [comp] │
  │  Small/Secondary [comp]    [comp]    [comp]    [comp]    [comp] │
  │  Medium/Primary  [comp]    [comp]    [comp]    [comp]    [comp] │
  │  Medium/Secondary[comp]    [comp]    [comp]    [comp]    [comp] │
  │  Large/Primary   [comp]    [comp]    [comp]    [comp]    [comp] │
  │  Large/Secondary [comp]    [comp]    [comp]    [comp]    [comp] │
  └──────────────────────────────────────────────────────────────────┘
```

**Why State on columns?** State is the axis designers scan horizontally to verify interaction consistency. Size/Style define the "identity" of each row. This matches how professional design systems (M3, Polaris, Simple DS) organize their grids.

#### Adding Row/Column Header Labels

After laying out the grid, add text labels OUTSIDE the ComponentSet to help navigation. These are siblings of the ComponentSet on the page — not children of it:

```javascript
// Add column headers above the component set
const colLabels = ['Default', 'Hover', 'Focused', 'Pressed', 'Disabled'];
await figma.loadFontAsync({ family: 'Inter', style: 'Medium' });
for (let i = 0; i < colLabels.length; i++) {
  const label = figma.createText();
  label.fontName = { family: 'Inter', style: 'Medium' };
  label.characters = colLabels[i];
  label.fontSize = 11;
  label.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
  label.x = cs.x + padding + i * (childWidth + gap);
  label.y = cs.y - 20;
}

// Add row headers to the left of the component set
const rowLabels = ['Small / Primary', 'Small / Secondary', 'Med / Primary', ...];
for (let i = 0; i < rowLabels.length; i++) {
  const label = figma.createText();
  label.fontName = { family: 'Inter', style: 'Medium' };
  label.characters = rowLabels[i];
  label.fontSize = 11;
  label.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
  label.x = cs.x - 120;
  label.y = cs.y + padding + i * (childHeight + gap) + childHeight / 2 - 6;
}
```

**Note:** These labels are documentation aids, not part of the component itself. They help designers navigate the variant grid.

#### Grid layout code

```javascript
const VARIANT_IDS = ['ID1', 'ID2', '...']; // from state ledger
const PAGE_ID = 'PAGE_ID'; // from state ledger

await figma.setCurrentPageAsync(await figma.getNodeByIdAsync(PAGE_ID));

// Collect component nodes
const components = await Promise.all(
  VARIANT_IDS.map(id => figma.getNodeByIdAsync(id))
);

// Combine as variants
const cs = figma.combineAsVariants(components, figma.currentPage);
cs.name = 'Button';

// Grid layout: position each variant based on its property values
// Determine column axis (State) and row axes (Size × Style)
const axes = {
  Size:  ['Small', 'Medium', 'Large'],
  Style: ['Primary', 'Secondary'],
  State: ['Default', 'Hover', 'Disabled'],
};
const COL_AXIS = 'State';  // columns
const ROW_AXES = ['Size', 'Style']; // rows (Size changes fastest)

const gap = 16;
const padding = 40;

// Measure child dimensions (all should be same height within Size tier)
// Use the first child as reference for column width
const childWidth  = 120; // approximate; refine after first screenshot
const childHeight = 40;

cs.children.forEach(child => {
  const props = {};
  child.name.split(', ').forEach(part => {
    const [k, v] = part.split('=');
    props[k] = v;
  });

  const colIdx = axes[COL_AXIS].indexOf(props[COL_AXIS]);
  // Row = Size index * number of styles + Style index
  const rowIdx = axes.Size.indexOf(props.Size) * axes.Style.length
               + axes.Style.indexOf(props.Style);

  child.x = padding + colIdx * (childWidth  + gap);
  child.y = padding + rowIdx * (childHeight + gap);
});

// Resize component set to fit all children + padding
let maxX = 0, maxY = 0;
for (const child of cs.children) {
  maxX = Math.max(maxX, child.x + child.width);
  maxY = Math.max(maxY, child.y + child.height);
}
cs.resizeWithoutConstraints(maxX + padding, maxY + padding);

// Style the component set frame
cs.fills = [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.98 } }];
cs.cornerRadius = 8;

// Position component set on page (to the right of doc frame)
cs.x = 680;
cs.y = 40;

cs.setSharedPluginData('dsb', 'run_id', 'ds-build-2024-001');
cs.setSharedPluginData('dsb', 'key', 'componentset/button');

return { componentSetId: cs.id };
```

**Critical rules for combineAsVariants:**
- `components` must be a non-empty array containing ONLY `ComponentNode` objects (not frames, not groups)
- After combining, children are placed at (0,0) and overlap — you MUST manually position them
- `resizeWithoutConstraints` is required after positioning to make the component set frame fit its contents
- There is no `figma.createComponentSet()` — you cannot create an empty component set

---

### 6. Component Properties

Add TEXT, BOOLEAN, and INSTANCE_SWAP properties to the ComponentSet (not to individual variants). The return value of `addComponentProperty` is the actual property key (it gets a `#id:id` suffix appended) — save this key and use it immediately when setting `componentPropertyReferences`.

#### TEXT Properties

Expose editable text in instances:

```javascript
// On the ComponentSetNode (cs):
const labelKey = cs.addComponentProperty('Label', 'TEXT', 'Button');
// labelKey is now something like "Label#0:1"

// Wire to the label child in each variant:
for (const child of cs.children) {
  const labelNode = child.findOne(n => n.name === 'label');
  if (labelNode) {
    labelNode.componentPropertyReferences = { characters: labelKey };
  }
}
```

#### BOOLEAN Properties

Toggle child node visibility:

```javascript
const showIconKey = cs.addComponentProperty('Show Icon', 'BOOLEAN', true);

for (const child of cs.children) {
  const iconNode = child.findOne(n => n.name === 'icon');
  if (iconNode) {
    iconNode.componentPropertyReferences = { visible: showIconKey };
  }
}
```

#### INSTANCE_SWAP Properties

Allow swapping a nested component instance (e.g., swap the icon):

```javascript
// defaultIconCompId is the ID of the default icon component (from state ledger)
const iconKey = cs.addComponentProperty('Icon', 'INSTANCE_SWAP', DEFAULT_ICON_COMP_ID);

for (const child of cs.children) {
  const iconSlot = child.findOne(n => n.name === 'icon');
  if (iconSlot && iconSlot.type === 'INSTANCE') {
    iconSlot.componentPropertyReferences = { mainComponent: iconKey };
  }
}
```

**Use INSTANCE_SWAP instead of creating a variant per icon.** Never add "Icon=ChevronRight, Icon=ChevronLeft, ..." as VARIANT axes — that causes combinatorial explosion. One INSTANCE_SWAP property covers all icons.

#### Creating Icon Components for INSTANCE_SWAP

INSTANCE_SWAP needs a real Component ID as its default value. Before wiring INSTANCE_SWAP, you need at least one icon component. Here's how to create icons from SVG:

```javascript
// Create a simple icon component from SVG
const svgNode = figma.createNodeFromSvg(
  '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
  '<path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
  '</svg>'
);

// Wrap in a component
const iconComp = figma.createComponent();
iconComp.name = 'Icon/ChevronRight';
iconComp.resize(24, 24);
iconComp.clipsContent = true;

// Move SVG children into the component
for (const child of [...svgNode.children]) {
  iconComp.appendChild(child);
}
svgNode.remove();

// Bind the icon fill to a color variable (so it respects themes)
// Find vector children and bind their fills
iconComp.findAllWithCriteria({ types: ['VECTOR'] }).forEach(vec => {
  // For stroke-based icons:
  if (vec.strokes.length > 0) {
    const strokePaint = figma.variables.setBoundVariableForPaint(
      { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', iconColorVar
    );
    vec.strokes = [strokePaint];
  }
});

iconComp.setSharedPluginData('dsb', 'run_id', RUN_ID);
iconComp.setSharedPluginData('dsb', 'key', 'icon/chevron-right');

return { iconCompId: iconComp.id };
```

**Then use the returned `iconCompId` as the default value for INSTANCE_SWAP:**
```javascript
const iconKey = cs.addComponentProperty('Icon', 'INSTANCE_SWAP', ICON_COMP_ID);
```

**Constraining swap options with `preferredValues`:**
After adding the INSTANCE_SWAP property, you can optionally limit which components appear in the swap picker:
```javascript
// Get the property definitions to find the exact key
const props = cs.componentPropertyDefinitions;
const iconPropKey = Object.keys(props).find(k => k.startsWith('Icon'));

// Set preferred values (array of component keys or instance IDs)
cs.editComponentProperty(iconPropKey, {
  preferredValues: [
    { type: 'COMPONENT', key: chevronRightComp.key },
    { type: 'COMPONENT', key: chevronLeftComp.key },
    { type: 'COMPONENT', key: closeComp.key },
  ],
});
```

**Icon library tip:** Create all icon components on a dedicated `Icons` page before building any UI components. Then reference their IDs when wiring INSTANCE_SWAP properties.

#### `componentPropertyReferences` mapping

The `componentPropertyReferences` object maps a node's own property to a component property key:

| Node property | Component property type | Used for |
|---|---|---|
| `characters` | TEXT | Editable text content |
| `visible` | BOOLEAN | Show/hide toggle |
| `mainComponent` | INSTANCE_SWAP | Swap nested instances |

---

### 7. `sharedPluginData` Tagging for Idempotency

Tag EVERY created node immediately after creation. This enables safe cleanup, resumability, and idempotency checks.

```javascript
// After creating any node:
node.setSharedPluginData('dsb', 'run_id', RUN_ID);   // identifies the build run
node.setSharedPluginData('dsb', 'phase', 'phase3');  // which phase created it
node.setSharedPluginData('dsb', 'key', KEY);         // unique logical key for this entity

// Reading back:
const runId = node.getSharedPluginData('dsb', 'run_id'); // '' if not set
const key   = node.getSharedPluginData('dsb', 'key');
```

**Key naming convention:** use `/`-separated logical paths that mirror the entity hierarchy:
```
'component/button/base'
'component/button/variant/Medium/Primary/Default'
'componentset/button'
'doc/button'
'page/button'
```

**Idempotency check before creating:** before creating a node, scan the current page for an existing node with the same `key`:

```javascript
// Indexed sharedPluginData lookup — the engine only visits nodes that
// actually carry the dsb namespace key, not every node on the page.
const existing = figma.currentPage
  .findAllWithCriteria({ sharedPluginData: { namespace: 'dsb', keys: ['key'] } })
  .filter(n => n.getSharedPluginData('dsb', 'key') === 'componentset/button');
if (existing.length > 0) {
  // Skip creation — already done. Return existing node's ID.
  return { componentSetId: existing[0].id };
}
```

---

### 8. Documentation

#### Page title + description frame

The documentation frame (see Section 2) should contain:
1. Component name as a large title (32px+ Bold)
2. 1–3 sentence description of what the component is and when to use it
3. Spec notes (sizes, spacing values, accessibility notes)

#### Component `description` property

Set the description on the ComponentSet — it appears in the Figma properties panel and is exported as documentation:

```javascript
cs.description = 'Buttons allow users to take actions and make choices. Use Primary for the highest-emphasis action on a page.';
```

#### `documentationLinks`

Link to external documentation (Storybook, design spec, tokens reference):

```javascript
cs.documentationLinks = [
  { uri: 'https://your-storybook.com/button' }
];
```

#### Node names and organization

- ComponentSet: plain component name — `'Button'`
- Individual variants: `'Property=Value, Property=Value'` format (match the file's existing casing)
- Child nodes: semantic names — `'label'`, `'icon'`, `'container'`, `'state-layer'`
- Documentation frames: `'ComponentName / Documentation'`

---

### 9. Validation

Always validate after creating or modifying a component before proceeding to the next one.

#### `get_metadata` structural checks

After creating the component set, call `get_metadata` on the ComponentSet node and verify:
- `variantGroupProperties` lists the expected axes with the correct value arrays
- `componentPropertyDefinitions` contains the expected TEXT/BOOLEAN/INSTANCE_SWAP properties
- `children.length` equals the expected variant count (e.g., 18 for 3×2×3)
- No children are named `'Component 1'` (unnamed components are a sign of a bug)

#### `get_screenshot` — Visual Validation (Critical)

`get_screenshot` returns an **image** of the specified node. Call it on the **component page node** (not the component set) to see the full page including documentation and grid labels.

```
Tool: get_screenshot
Args: { nodeId: "PAGE_NODE_ID", fileKey: "FILE_KEY" }
```

**How to use the screenshot:**

1. **Display it to the user** — this is the primary purpose. Show the screenshot as part of the user checkpoint: "Here's the Button component. Does it look right?"
2. **Analyze it yourself** — if you have vision capabilities, check the visual checklist below. If you don't (text-only agent), fall back to structural validation only via `get_metadata` and describe what you created textually.

**Visual validation checklist** (check each item when viewing the screenshot):

| # | Check | What "good" looks like | What "broken" looks like |
|---|-------|----------------------|------------------------|
| 1 | **Grid layout** | Variants in neat rows and columns with consistent spacing | All variants piled at top-left (0,0 stacking bug) |
| 2 | **Color fills** | Components show distinct, correct colors per style variant | All components are black or same color (variable binding failed) |
| 3 | **Size differentiation** | Small variants are visibly smaller than Large variants | All variants are the same size (height/padding not bound to variables) |
| 4 | **Text readability** | Labels are visible with correct font and color | Text is invisible (white on white), missing, or shows "undefined" |
| 5 | **Spacing/padding** | Interior padding visible, components aren't "shrink-wrapped" | Components look cramped or have no visible internal space |
| 6 | **State differentiation** | Hover/Pressed variants have visible color differences from Default | All states look identical (state-specific fills not applied) |
| 7 | **Disabled state** | Lower opacity or muted colors compared to active states | Disabled looks identical to Default |
| 8 | **Documentation frame** | Title + description text visible above or beside the component grid | No documentation, or it overlaps the component set |
| 9 | **Grid labels** | Row/column headers visible around the component set (if added) | Labels overlap the grid or are missing |
| 10 | **Component set boundary** | Gray background frame wraps all variants with even padding | Frame is too small (variants clipped) or way too large |

**Screenshot → diagnosis → fix mapping:**

| Screenshot shows | Diagnosis | Fix script |
|-----------------|-----------|------------|
| All variants stacked top-left | Grid layout wasn't applied after `combineAsVariants` | Re-run the grid layout script (§5) |
| Everything black/same color | Variable bindings failed or variables don't have values for the active mode | Re-run variable binding, check mode values |
| No text visible | Font wasn't loaded, or text fill is same color as background | Call `listAvailableFontsAsync()` to verify the font exists, then check `loadFontAsync` was called before text writes; bind text fill to `color/text/*` variable |
| Variants all same size | Padding/height not bound to size variables | Re-run `bindVariablesToComponent` with size-specific tokens |
| Component set frame tiny | `resizeWithoutConstraints` wasn't called or used wrong dimensions | Re-calculate bounds from children and resize |
| Doc frame overlaps components | Component set positioned at same x,y as doc frame | Move component set: `cs.x = docFrame.x + docFrame.width + 60` |

**When visual analysis isn't available:**
If your model can't process images (text-only mode), validate structurally instead:
1. Call `get_metadata` on the component set — verify child count, property definitions, variant names
2. Run an `use_figma` that samples key properties:
```javascript
const cs = await figma.getNodeByIdAsync(CS_ID);
const sample = cs.children.slice(0, 3).map(c => ({
  name: c.name,
  width: c.width, height: c.height,
  x: c.x, y: c.y,
  fills: c.fills?.map(f => f.type === 'SOLID' ?
    { r: f.color.r.toFixed(2), g: f.color.g.toFixed(2), b: f.color.b.toFixed(2), boundVar: f.boundVariables?.color?.id } : f.type
  ),
}));
return { sampleVariants: sample, totalChildren: cs.children.length };
```
This gives you positions (grid working?), dimensions (size differentiation?), and fill info (bindings working?) without needing vision.

**When to take a screenshot:**
- After EVERY completed component (mandatory — part of the user checkpoint)
- After creating the foundations documentation page
- After final QA (screenshot every page)
- Do NOT screenshot after every intermediate step (wastes tool calls)

#### Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| All variants stacked at (0,0) | `combineAsVariants` was called but children were never repositioned | Re-run grid layout script |
| Variants show wrong colors | Variable bindings applied after `combineAsVariants` instead of before | Rebind on component set children |
| Variant count wrong | Clone loop indexing error | Print `components.map(c => c.name)` before combining |
| BOOLEAN property has no effect | `componentPropertyReferences` was set on the component set frame, not on the child node | Find the actual child node and set references there |
| INSTANCE_SWAP shows no swap option | Default value was not a valid component ID | Pass a real existing component ID as `defaultValue` |
| `combineAsVariants` throws | At least one node in the array is not a `ComponentNode` | Filter array: `nodes.filter(n => n.type === 'COMPONENT')` |
| `addComponentProperty` returns unexpected key | Expected — the key gets a `#id:id` suffix | Save the returned value immediately: `const key = cs.addComponentProperty(...)` |

---

### 10. Complete Worked Example: Button Component

This shows the full sequence of `use_figma` calls for a Button component, including state passing between calls. Replace `RUN_ID` and variable IDs with your actual values from the state ledger.

#### Call 1: Create the component page

**Goal:** Create (or find) the Button page.
**State input:** None
**State output:** `{ pageId }`

```javascript
let page = figma.root.children.find(p => p.name === 'Button');
if (!page) { page = figma.createPage(); page.name = 'Button'; }
page.setSharedPluginData('dsb', 'run_id', 'ds-build-2024-001');
page.setSharedPluginData('dsb', 'key', 'page/button');
return { pageId: page.id };
```

#### Call 2: Create documentation frame

**Goal:** Add title + description frame.
**State input:** `{ pageId }`
**State output:** `{ docFrameId }`

```javascript
const PAGE_ID = 'PAGE_ID_FROM_STATE';
const page = await figma.getNodeByIdAsync(PAGE_ID);
await figma.setCurrentPageAsync(page);

// Idempotency check — use the sharedPluginData index instead of a per-node
// findAll callback.
const existing = page
  .findAllWithCriteria({ sharedPluginData: { namespace: 'dsb', keys: ['key'] } })
  .filter(n => n.getSharedPluginData('dsb', 'key') === 'doc/button');
if (existing.length > 0) {
  return { docFrameId: existing[0].id };
}

await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });

const docFrame = figma.createFrame();
docFrame.name = 'Button / Documentation';
docFrame.x = 40; docFrame.y = 40;
docFrame.layoutMode = 'VERTICAL';
docFrame.primaryAxisSizingMode = 'AUTO';
docFrame.counterAxisSizingMode = 'FIXED';
docFrame.resize(560, 100);
docFrame.paddingTop = 40; docFrame.paddingBottom = 40;
docFrame.paddingLeft = 40; docFrame.paddingRight = 40;
docFrame.itemSpacing = 16;
docFrame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];

const title = figma.createText();
title.fontName = { family: 'Inter', style: 'Bold' };
title.fontSize = 32;
title.characters = 'Button';
docFrame.appendChild(title);

const desc = figma.createText();
desc.fontName = { family: 'Inter', style: 'Regular' };
desc.fontSize = 14;
desc.characters = 'Buttons allow users to take actions with a single tap. Use Primary for the highest-emphasis action on a page, Secondary for supporting actions.';
desc.layoutSizingHorizontal = 'FILL';
docFrame.appendChild(desc);

docFrame.setSharedPluginData('dsb', 'run_id', 'ds-build-2024-001');
docFrame.setSharedPluginData('dsb', 'key', 'doc/button');

return { docFrameId: docFrame.id };
```

#### Call 3: Create base component

**Goal:** Create the base component with auto-layout and all variable bindings.
**State input:** `{ pageId }` + variable IDs from Phase 1
**State output:** `{ baseCompId }`

*(See Section 3 for full code — substituting the actual variable IDs from the state ledger.)*

#### Call 4: Create all variants

**Goal:** Clone base and produce all 18 variants (3 Size × 2 Style × 3 State).
**State input:** `{ pageId, baseCompId }` + variable IDs
**State output:** `{ variantIds: ['id1', 'id2', ..., 'id18'] }`

```javascript
const RUN_ID = 'ds-build-2024-001';
const BASE_ID = 'BASE_COMP_ID_FROM_STATE';
const PAGE_ID = 'PAGE_ID_FROM_STATE';
// Variable IDs from state ledger:
const VAR = {
  bg_primary:     'VAR_ID_1',
  text_primary:   'VAR_ID_2',
  bg_secondary:   'VAR_ID_3',
  text_secondary: 'VAR_ID_4',
  bg_disabled:    'VAR_ID_5',
  text_disabled:  'VAR_ID_6',
  padding_sm:     'VAR_ID_7',
  padding_md:     'VAR_ID_8',
  padding_lg:     'VAR_ID_9',
};

const page = await figma.getNodeByIdAsync(PAGE_ID);
await figma.setCurrentPageAsync(page);

const base = await figma.getNodeByIdAsync(BASE_ID);

// Load all variables in parallel — sequential awaits in the loop would
// serialize one IPC round-trip per variable.
const varEntries = Object.entries(VAR);
const fetched = await Promise.all(
  varEntries.map(([, id]) => figma.variables.getVariableByIdAsync(id))
);
const vars = {};
varEntries.forEach(([k], i) => { vars[k] = fetched[i]; });

const axes = {
  Size:  ['Small', 'Medium', 'Large'],
  Style: ['Primary', 'Secondary'],
  State: ['Default', 'Hover', 'Disabled'],
};
const paddingMap = { Small: vars.padding_sm, Medium: vars.padding_md, Large: vars.padding_lg };

const components = [];
for (const size of axes.Size) {
  for (const style of axes.Style) {
    for (const state of axes.State) {
      const clone = base.clone();
      clone.name = `Size=${size}, Style=${style}, State=${state}`;

      clone.setBoundVariable('paddingTop',    paddingMap[size]);
      clone.setBoundVariable('paddingBottom', paddingMap[size]);
      clone.setBoundVariable('paddingLeft',   paddingMap[size]);
      clone.setBoundVariable('paddingRight',  paddingMap[size]);

      const isDisabled = state === 'Disabled';
      const bgV  = isDisabled ? vars.bg_disabled  : (style === 'Primary' ? vars.bg_primary  : vars.bg_secondary);
      const txV  = isDisabled ? vars.text_disabled : (style === 'Primary' ? vars.text_primary : vars.text_secondary);

      clone.fills = [figma.variables.setBoundVariableForPaint(
        { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', bgV
      )];

      const labelNode = clone.findOne(n => n.name === 'label');
      labelNode.fills = [figma.variables.setBoundVariableForPaint(
        { type: 'SOLID', color: { r: 1, g: 1, b: 1 } }, 'color', txV
      )];

      clone.setSharedPluginData('dsb', 'run_id', RUN_ID);
      clone.setSharedPluginData('dsb', 'key', `component/button/variant/${size}/${style}/${state}`);
      components.push(clone);
    }
  }
}

return { variantIds: components.map(c => c.id) };
```

#### Call 5: combineAsVariants + grid layout

**Goal:** Combine all 18 variants into a ComponentSet and lay them out in a grid.
**State input:** `{ pageId, variantIds }` (18 IDs)
**State output:** `{ componentSetId }`

*(See Section 5 for full code.)*

#### Call 6: Add component properties

**Goal:** Add TEXT, BOOLEAN, INSTANCE_SWAP properties and wire them to child nodes.
**State input:** `{ pageId, componentSetId }`
**State output:** `{ componentSetId, properties: { labelKey, showIconKey, iconKey } }`

```javascript
const CS_ID = 'CS_ID_FROM_STATE';
const DEFAULT_ICON_ID = 'ICON_COMP_ID_FROM_STATE';
const page = figma.root.children.find(p => p.name === 'Button');
await figma.setCurrentPageAsync(page);

const cs = await figma.getNodeByIdAsync(CS_ID);
cs.description = 'Buttons allow users to take actions and make choices with a single tap.';
cs.documentationLinks = [{ uri: 'https://your-storybook.com/button' }];

// Add properties — save returned keys
const labelKey    = cs.addComponentProperty('Label', 'TEXT', 'Button');
const showIconKey = cs.addComponentProperty('Show Icon', 'BOOLEAN', true);
const iconKey     = cs.addComponentProperty('Icon', 'INSTANCE_SWAP', DEFAULT_ICON_ID);

// Wire to children
for (const child of cs.children) {
  const labelNode = child.findOne(n => n.name === 'label');
  if (labelNode) labelNode.componentPropertyReferences = { characters: labelKey };

  const iconNode = child.findOne(n => n.name === 'icon');
  if (iconNode) {
    iconNode.componentPropertyReferences = {
      visible: showIconKey,
      ...(iconNode.type === 'INSTANCE' ? { mainComponent: iconKey } : {}),
    };
  }
}

return {
  componentSetId: cs.id,
  properties: { labelKey, showIconKey, iconKey },
};
```

#### Call 7: Validate with get_metadata

**Goal:** Structural check — variant count, properties, axes.
**Action:** Call `get_metadata` on the ComponentSet node ID (from state). Verify in the result:
- `children.length === 18`
- `variantGroupProperties` has `Size`, `Style`, `State` keys with correct value arrays
- `componentPropertyDefinitions` has `Label`, `Show Icon`, `Icon` entries

#### Call 8: Validate with get_screenshot

**Goal:** Visual check — layout, colors, text.
**Action:** Call `get_screenshot` on the Button page. Inspect the screenshot. If variants are stacked, re-run Call 5. If colors look wrong, inspect variable bindings.

#### Checkpoint

After Call 8: show the screenshot to the user. Ask: "Here's the Button component with 18 variants. Does this look correct?" Do not proceed to the next component until the user approves.

---

## Reference — Code Connect Setup Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

This reference covers all Code Connect tooling available to the figma-generate-library agent: the `add_code_connect_map` tool, `get_code_connect_map` for verification, `send_code_connect_mappings` for bulk application, variable code syntax, framework labels, and the decision of when to map per-component vs. in a final pass.

---

### 1. What Code Connect Does

Code Connect links a Figma component node to its code implementation so that:

- **Dev Mode** shows a real code snippet (from your codebase) instead of an auto-generated approximation when a developer inspects a component.
- **MCP `get_design_context`** returns `componentName`, `source`, and a rendered snippet alongside design tokens, enabling accurate AI-assisted code generation.
- **`search_design_system`** can return code references alongside Figma component metadata.

---

### 2. The Three MCP Tools

#### 2a. add_code_connect_map — single mapping

Maps one Figma node to one code component.

**Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `nodeId` | string | Yes (remote) / Optional (desktop) | Format `123:456`. Must be a published component or component set. |
| `fileKey` | string | Yes (remote) | The Figma file key. |
| `source` | string | Yes | Path in the codebase (e.g. `src/components/Button.tsx`) or a URL. |
| `componentName` | string | Yes | The code component name (e.g. `Button`). |
| `label` | enum | Yes | Framework label — see Section 4 for valid values. |
| `template` | string | Optional | Executable JS template code. Providing this creates a **template** mapping instead of a simple **component-path** mapping. Gated behind a server-side feature flag — falls back to a simple mapping when disabled. |
| `templateDataJson` | string | Optional | JSON string with optional fields: `isParserless`, `imports`, `nestable`, `props`. |

**Two mapping tiers:**

1. **Simple mapping (component-path):** Only `source`, `componentName`, and `label` provided. Associates the Figma component with a code path + name. Dev Mode generates a basic JSX snippet from Figma prop names. This is the default — use it first.

2. **Template mapping:** `template` is also provided. The template is executed in a sandboxed QuickJS environment and dynamically renders the snippet based on the actual instance's property values. Use this when precise prop-level Code Connect is required by the user.

**Common error codes:**

| Error | Meaning | Fix |
|-------|---------|-----|
| `CODE_CONNECT_MAPPING_ALREADY_EXISTS` | Component is already mapped | Disconnect existing mapping in Figma UI first |
| `CODE_CONNECT_ASSET_NOT_FOUND` | Published component not found | Ensure the component is published to the library |
| `CODE_CONNECT_INSUFFICIENT_PERMISSIONS` | No edit access | Request edit permission on the file |
| `CODE_CONNECT_NO_LIBRARY_FOUND` | File is not published as a library | Publish the file as a Figma library first |

**Usage example:**

```
Tool: add_code_connect_map
Args: {
  nodeId: "123:456",
  fileKey: "abc123",
  source: "src/components/Button.tsx",
  componentName: "Button",
  label: "React"
}
```

---

#### 2b. get_code_connect_map — verification

Retrieves the current Code Connect mapping for a node. Use this immediately after `add_code_connect_map` to confirm the mapping was saved, and before `send_code_connect_mappings` to audit existing state.

**Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `nodeId` | string | Optional | The node to check. Omit to get all mappings in the file. |
| `fileKey` | string | Yes (remote) | The Figma file key. |
| `codeConnectLabel` | string | Optional | Filter results to a specific framework label. |

**Returns:** A map of `nodeId -> { componentName, source, label, snippet, snippetImports }`.

**How to verify:**

```
1. Call add_code_connect_map with the node.
2. Immediately call get_code_connect_map(nodeId, fileKey).
3. Confirm the returned object has the expected componentName and source.
4. If the mapping is missing, check for error codes from step 1.
```

---

#### 2c. send_code_connect_mappings — bulk application

Applies multiple Code Connect mappings in one call. Use after `get_code_connect_suggestions` returns a batch of unmapped components, or when doing a final-pass bulk mapping at the end of Phase 4.

**Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `nodeId` | string | Optional | Context node for design fallback if mappings array is empty. |
| `fileKey` | string | Yes (remote) | The Figma file key. |
| `mappings` | array | Yes | Array of mapping objects. |

**Each mapping object:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `nodeId` | string | Yes | The Figma node identifier. |
| `componentName` | string | Yes | Code component name. |
| `source` | string | Yes | Path in the codebase. |
| `label` | enum | Yes | Framework label. |
| `template` | string | Optional | JS template code for template mapping. |
| `templateDataJson` | string | Optional | JSON template metadata. |

**Behavior:**

- All mappings are processed in parallel via POSTs to the backend.
- If any mapping fails, errors are reported per mapping — the rest succeed.
- On full success, `get_design_context` is called for the nodes and fresh design context is returned.

**Bulk workflow:**

```
1. Collect all {nodeId, componentName, source, label} pairs.
2. Call send_code_connect_mappings({ fileKey, mappings: [...all pairs...] }).
3. Review reported errors and call add_code_connect_map individually for any failures.
4. Call get_code_connect_map on a sample of nodes to spot-check.
```

---

### 3. Variable Code Syntax (Token Round-Tripping)

Setting code syntax on variables creates the bidirectional link between Figma tokens and the codebase token system. This is what enables Dev Mode to show `var(--color-bg-primary)` next to a design value instead of a raw hex.

**The three platforms:**

```javascript
// In use_figma:
variable.setVariableCodeSyntax('WEB', 'var(--color-bg-primary)');
variable.setVariableCodeSyntax('ANDROID', 'Theme.colorBgPrimary');
variable.setVariableCodeSyntax('iOS', 'Color.bgPrimary');
```

- `WEB` — used for CSS custom properties, design token JSON, and any web framework.
- `ANDROID` — used for Jetpack Compose theme references and Android resource names.
- `iOS` — used for SwiftUI Color extensions and UIKit color methods.

**Derivation rules (in priority order):**

1. **Best:** Use the exact token name from the codebase. Search the codebase for CSS custom properties (`--`), Swift color extensions, or Kotlin theme references and use those exact strings.
2. **Good:** Derive from the Figma variable name with a consistent transformation: replace `/` and spaces with `-`, prefix with `var(--` and suffix with `)`.
   - Example: `color/bg/primary` → `var(--color-bg-primary)`
3. **Avoid:** Guessing or inventing names that don't exist in the codebase.

**Consistency rule:** The transformation must be uniform. If you use `var(--color-bg-primary)` for one variable, use the same `var(--{path-with-hyphens})` pattern for all variables in that collection.

**WEB syntax bulk example:**

```javascript
// In use_figma — set WEB code syntax on every variable in matching collections.
// flatMap all variable IDs across matching collections into a single
// Promise.all so the lookups run in parallel across collections too — same
// pattern as `listVariableCollectionsAndVariables` in variable-patterns.md.
// setVariableCodeSyntax is sync, so the writes don't need to be batched.
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const ids = collections
  .filter(c => c.name === 'Color')
  .flatMap(c => c.variableIds);
const vars = await Promise.all(
  ids.map(id => figma.variables.getVariableByIdAsync(id))
);
for (const v of vars) {
  if (!v) continue;
  // Derive: "color/bg/primary" → "var(--color-bg-primary)"
  const cssName = 'var(--' + v.name.toLowerCase().replace(/\//g, '-').replace(/\s+/g, '-') + ')';
  v.setVariableCodeSyntax('WEB', cssName);
}
```

---

### 4. Framework Labels

The following labels are valid for all Code Connect MCP operations. Use the label that matches your codebase framework.

| Label | Use for |
|-------|---------|
| `React` | React / JSX / TSX components |
| `Web Components` | Native Web Components, Lit, FAST |
| `Vue` | Vue 2 and Vue 3 SFCs |
| `Svelte` | Svelte components |
| `Storybook` | Storybook stories with Code Connect integration |
| `Javascript` | Plain JavaScript, framework-agnostic |
| `Swift` | Swift / UIKit |
| `Swift UIKit` | UIKit specifically |
| `Objective-C UIKit` | Objective-C with UIKit |
| `SwiftUI` | SwiftUI view components |
| `Compose` | Jetpack Compose (Android) |
| `Java` | Java Android components |
| `Kotlin` | Kotlin Android (non-Compose) |
| `Android XML Layout` | Android XML layout files |
| `Flutter` | Flutter / Dart widgets |
| `Markdown` | Documentation or MDX components |

**HTML note:** The label `HTML` is used by the Code Connect CLI's HTML parser (for Angular, Vue, and Web Components without a framework-specific parser), but the MCP tools use `Web Components` or `Vue` directly. Check the codebase framework before selecting.

---

### 5. Per-Component vs. Final-Pass Strategy

#### Per-component (preferred for new builds)

Map Code Connect immediately after creating a component, while the context is fresh (Phase 3, step 3h in the SKILL.md workflow):

**Advantages:**
- The node ID is already in hand from the creation script.
- You know exactly which code component this Figma component corresponds to (you just designed it to match).
- Errors surface early, before building dependent components.

**When to use:** Any time you create a Figma component that has a clear 1:1 match with an existing code component.

#### Final pass (for bulk mapping at Phase 4)

Collect all unmapped components and map them in one `send_code_connect_mappings` call:

**Advantages:**
- One bulk call instead of N individual calls.
- Can use `get_code_connect_suggestions` to discover unmapped components automatically.
- Better for importing existing Figma files where you didn't control creation.

**When to use:** Retrofitting Code Connect onto an existing file, or when the codebase mapping requires research that is better done after all components are created.

#### Hybrid (recommended for large systems)

- Map atoms (Button, Input, Badge, Avatar) **per-component** during Phase 3.
- Map molecules and organisms in a **final pass** during Phase 4 after all atoms are mapped, since molecule snippets reference atom Code Connect IDs.

---

### 6. Verification in Dev Mode

After mapping:

1. Open the Figma file in the browser or desktop app.
2. Switch to Dev Mode (the `</>` icon in the toolbar).
3. Select a component instance (not the main component — an instance placed on a page).
4. In the Inspect panel, the code snippet should show the Code Connect output instead of auto-generated code.
5. If the snippet is missing or shows `[auto-generated]`, run `get_code_connect_map` via MCP to confirm the mapping exists, then check that the component is published.

**Via MCP (faster during agent workflows):**

```
get_code_connect_map(nodeId: "<the component set node ID>", fileKey: "<file key>")
```

The response should include `componentName`, `source`, `label`, and a non-empty `snippet`.

---

### 7. Important Constraints

- **Published components only:** `add_code_connect_map` requires the component to be published to a library. If the file is not yet published, the mapping will fail with `CODE_CONNECT_NO_LIBRARY_FOUND`.
- **One mapping per label per node:** A node can have multiple mappings (one per framework label), but only one per label. Attempting to add a second React mapping to the same node returns `CODE_CONNECT_MAPPING_ALREADY_EXISTS`.
- **Template mappings are gated:** The `template` parameter is gated behind a server-side feature flag and may not be available in every environment. Use simple mappings unless the user explicitly requests template-level Code Connect.
- **Start simple, escalate:** Always begin with simple mappings (`source` + `componentName` + `label`). Add `template` only if the user needs precise prop-level snippet rendering.

---

## Reference — Error Recovery Reference

> Part of the [figma-generate-library skill](#design-system-builder--figma-mcp-skill).

Protocol for handling failures and incomplete runs across a 20–100+ call design system build.

> **Design files only.** Every snippet here (including `figma.createPage()`) targets Figma Design files (`figma.com/design/...`). `figma.createPage()` throws in both FigJam (`figma.com/board/...`) and Slides (`figma.com/slides/...`).

---

### 1. Core Protocol: STOP → Inspect → Fix → Retry

**`use_figma` is atomic — a failed script does not execute.** If a script errors, no changes are made to the file. There are no partial nodes or half-built state from the failed call itself. Retrying after a fix is safe.

However, in multi-step workflows (20–100+ calls), **previously successful calls** will have created state that persists. If a workflow is abandoned mid-way, nodes from earlier successful calls remain in the file. The cleanup and idempotency patterns in this document handle that scenario.

The recovery sequence for a failed script:

```
1. STOP    — Do not run any more use_figma writes.
2. INSPECT — Read the error message carefully. Optionally call get_metadata or get_screenshot to understand the current file state.
3. FIX     — Correct the script that failed.
4. RETRY   — Re-run the corrected script.
5. PERSIST — Update the state ledger with the outcome.
```

For **abandoned multi-step workflows** (where you need to roll back nodes from previous *successful* calls), use the cleanup protocol in Section 2.

---

### 2. `sharedPluginData`-Based Cleanup: Why Name Matching is Dangerous

#### Why name-prefix matching fails

A cleanup script that deletes "all nodes whose name starts with `Button`" will also delete nodes the user may have created manually with that name, or nodes from a previous approved phase. Name-based cleanup has no way to distinguish "orphan from a failed attempt" from "intentional user node."

Furthermore, variant names (`Size=Medium, Style=Primary, State=Default`) do not have consistent prefixes that are safe to target without also hitting legitimate nodes.

#### How `setSharedPluginData` / `getSharedPluginData` works

`sharedPluginData` is a key-value store attached to individual nodes. It persists across sessions and is invisible to the user in the Figma UI. Data is scoped by namespace — we use `'dsb'`. Use three keys:

```javascript
node.setSharedPluginData('dsb', 'run_id', 'ds-build-2024-001'); // identifies the build run
node.setSharedPluginData('dsb', 'phase',  'phase3');             // which phase created this node
node.setSharedPluginData('dsb', 'key',    'componentset/button');// unique logical key

// Reading:
const runId = node.getSharedPluginData('dsb', 'run_id'); // returns '' if never set
const key   = node.getSharedPluginData('dsb', 'key');
```

`getSharedPluginData` returns `''` (empty string, not null) for unset keys. Always check for `!== ''`.

**Tag every created node immediately after creation** — this enables safe cleanup if the multi-step workflow is abandoned later. Tag in the same statement sequence as creation:

```javascript
const comp = figma.createComponent();
comp.setSharedPluginData('dsb', 'run_id', RUN_ID);  // tag immediately
comp.setSharedPluginData('dsb', 'key', key);         // tag immediately
// ... then do the rest of the setup
```

#### Complete `cleanupOrphans` script using `run_id`

This script finds all nodes tagged with a given `run_id` and optionally a `phase` filter, then removes them. Run it on the specific page where the failure occurred.

```javascript
const TARGET_RUN_ID = 'ds-build-2024-001'; // run ID to clean
const TARGET_PHASE  = 'phase3';            // optionally filter by phase ('' = all phases)
const PAGE_NAME     = 'Button';            // page to clean (or null for all pages)

const pagesToSearch = PAGE_NAME
  ? [figma.root.children.find(p => p.name === PAGE_NAME)].filter(Boolean)
  : figma.root.children;

const removed = [];
const skipped = [];

for (const page of pagesToSearch) {
  await figma.setCurrentPageAsync(page);

  // Use the sharedPluginData index instead of findAll + getSharedPluginData
  // on every node. The engine narrows to nodes that actually carry the
  // namespace/keys before any JS callback runs.
  const candidates = page.findAllWithCriteria({
    sharedPluginData: { namespace: 'dsb', keys: ['run_id'] },
  });
  const orphans = candidates.filter(node => {
    if (node.getSharedPluginData('dsb', 'run_id') !== TARGET_RUN_ID) return false;
    if (TARGET_PHASE && node.getSharedPluginData('dsb', 'phase') !== TARGET_PHASE) return false;
    return true;
  });

  // Remove leaf-first to avoid removing parents before children
  // Sort by depth (deepest first) to avoid double-remove errors
  const sorted = orphans.slice().sort((a, b) => {
    let depthA = 0, depthB = 0;
    let n = a; while (n.parent) { depthA++; n = n.parent; }
    n = b; while (n.parent) { depthB++; n = n.parent; }
    return depthB - depthA;
  });

  for (const node of sorted) {
    try {
      if (node.removed) continue; // already removed (was a child of removed parent)
      node.remove();
      removed.push({ id: node.id, name: node.name, key: node.getSharedPluginData('dsb', 'key') });
    } catch (e) {
      skipped.push({ id: node.id, name: node.name, error: e.message });
    }
  }
}

return { removed: removed.length, skipped: skipped.length, details: removed };
```

After running cleanup, call `get_metadata` on the target page to confirm the orphaned nodes are gone before retrying.

---

### 3. Idempotency Patterns: Check-Before-Create

Run an idempotency check at the start of every create operation. If the entity already exists (tagged with the expected `key`), skip creation and return the existing ID.

#### Check-before-create for a variable collection

```javascript
const KEY = 'collection/color';
const RUN_ID = 'ds-build-2024-001';
const COLLECTION_NAME = 'Color';

// Check: does a collection tagged with this key already exist?
const allCollections = await figma.variables.getLocalVariableCollectionsAsync();
// Variables/collections support sharedPluginData too — check by name as fallback
// Note: VariableCollection sharedPluginData is set via collection.setSharedPluginData(...)
const existing = allCollections.find(c =>
  c.getSharedPluginData('dsb', 'key') === KEY
);

if (existing) {
  return {
    collectionId: existing.id,
    modeIds: existing.modes.map(m => ({ name: m.name, id: m.modeId })),
    alreadyExisted: true,
  };
}

// Create fresh
const collection = figma.variables.createVariableCollection(COLLECTION_NAME);
collection.setSharedPluginData('dsb', 'run_id', RUN_ID);
collection.setSharedPluginData('dsb', 'key', KEY);

// Rename default mode, add second mode
collection.renameMode(collection.modes[0].modeId, 'Light');
const darkModeId = collection.addMode('Dark');

return {
  collectionId: collection.id,
  modeIds: [
    { name: 'Light', id: collection.modes[0].modeId },
    { name: 'Dark',  id: darkModeId },
  ],
};
```

#### Check-before-create for a page

```javascript
const KEY = 'page/button';
const PAGE_NAME = 'Button';
const RUN_ID = 'ds-build-2024-001';

// Check by sharedPluginData key first, then by name as fallback
let page = figma.root.children.find(p => p.getSharedPluginData('dsb', 'key') === KEY);
if (!page) {
  page = figma.root.children.find(p => p.name === PAGE_NAME);
}

if (page) {
  // Ensure it's tagged if it was found by name only
  if (!page.getSharedPluginData('dsb', 'key')) {
    page.setSharedPluginData('dsb', 'run_id', RUN_ID);
    page.setSharedPluginData('dsb', 'key', KEY);
  }
  return { pageId: page.id, alreadyExisted: true };
}

page = figma.createPage();
page.name = PAGE_NAME;
page.setSharedPluginData('dsb', 'run_id', RUN_ID);
page.setSharedPluginData('dsb', 'key', KEY);

return { pageId: page.id, alreadyExisted: false };
```

#### Check-before-create for a component set

```javascript
const KEY = 'componentset/button';
const PAGE_ID = 'PAGE_ID_FROM_STATE';
const RUN_ID = 'ds-build-2024-001';

const page = await figma.getNodeByIdAsync(PAGE_ID);
await figma.setCurrentPageAsync(page);

// Indexed lookup: only COMPONENT_SET nodes with the dsb namespace + key.
const existing = page
  .findAllWithCriteria({
    types: ['COMPONENT_SET'],
    sharedPluginData: { namespace: 'dsb', keys: ['key'] },
  })
  .filter(n => n.getSharedPluginData('dsb', 'key') === KEY);

if (existing.length > 0) {
  return {
    componentSetId: existing[0].id,
    alreadyExisted: true,
  };
}

// ... proceed with creation
return { componentSetId: null, alreadyExisted: false };
```

---

### 4. State Ledger

#### JSON Schema

Maintain a state ledger in your context (not in the Figma file) across calls. This is your source of truth for node IDs, completed steps, and pending validations.

```json
{
  "runId": "ds-build-2024-001",
  "phase": "phase3",
  "step": "component-button/combine-variants",
  "completedSteps": [
    "phase0",
    "phase1/collections",
    "phase1/primitives",
    "phase1/semantics",
    "phase2/pages",
    "phase2/foundations-docs",
    "phase3/component-avatar",
    "phase3/component-icon"
  ],
  "entities": {
    "collections": {
      "primitives": "VariableCollectionId:1234:5678",
      "color":      "VariableCollectionId:1234:5679",
      "spacing":    "VariableCollectionId:1234:5680"
    },
    "variables": {
      "color/bg/primary":         "VariableId:2345:1",
      "color/bg/secondary":       "VariableId:2345:2",
      "color/bg/disabled":        "VariableId:2345:3",
      "color/text/on-primary":    "VariableId:2345:4",
      "color/text/on-secondary":  "VariableId:2345:5",
      "color/text/disabled":      "VariableId:2345:6",
      "spacing/sm":               "VariableId:2345:7",
      "spacing/md":               "VariableId:2345:8",
      "spacing/lg":               "VariableId:2345:9",
      "radius/md":                "VariableId:2345:10"
    },
    "modes": {
      "color/light": "2345:1",
      "color/dark":  "2345:2"
    },
    "pages": {
      "Cover":       "0:1",
      "Foundations": "0:2",
      "Button":      "0:3"
    },
    "components": {
      "Icon":        "3456:1",
      "Avatar":      "3456:2",
      "Button":      "3456:3"
    },
    "componentSets": {
      "Button": "4567:1"
    }
  },
  "pendingValidations": [
    "Button:metadata",
    "Button:screenshot"
  ],
  "userCheckpoints": {
    "phase0": "approved-2024-01-15",
    "phase1": "approved-2024-01-15",
    "phase2": "approved-2024-01-15",
    "component-avatar": "approved-2024-01-15"
  }
}
```

#### Persisting between calls

After every successful `use_figma` call:
1. Extract all IDs from the return value
2. Add them to the appropriate `entities` section of the ledger
3. Add the completed step to `completedSteps`
4. Remove from `pendingValidations` if this call validated something
5. Update `phase` and `step` to the current position

#### Rehydrating at session start

If a conversation is interrupted and resumed, read the state ledger and verify key entities still exist:

```javascript
// Verify that critical nodes from the ledger still exist
const toVerify = {
  'color-collection':  'VariableCollectionId:1234:5679',
  'button-page':       '0:3',
  'button-componentset': '4567:1',
};

// Batch the lookups — awaiting getNodeByIdAsync per entry serializes the
// round-trips. Resolve them all in parallel with Promise.all, then walk the
// results.
const entries = Object.entries(toVerify);
const nodes = await Promise.all(
  entries.map(([, id]) => figma.getNodeByIdAsync(id).catch(() => null))
);
const results = {};
for (let i = 0; i < entries.length; i++) {
  const [label] = entries[i];
  const node = nodes[i];
  results[label] = node ? { found: true, name: node.name } : { found: false };
}

return results;
```

If any entity is missing, treat the phase that created it as incomplete and re-run from that checkpoint.

---

### 5. Resume Protocol

#### Step 1: Inspect the file for `run_id` tags

```javascript
const TARGET_RUN_ID = 'ds-build-2024-001';
const inventory = { pages: [], variables: [], componentSets: [], frames: [] };

// Scan pages
for (const page of figma.root.children) {
  if (page.getSharedPluginData('dsb', 'run_id') === TARGET_RUN_ID) {
    inventory.pages.push({ id: page.id, name: page.name, key: page.getSharedPluginData('dsb', 'key') });
  }
}

// Scan variables
const allVars = await figma.variables.getLocalVariablesAsync();
for (const v of allVars) {
  if (v.getSharedPluginData('dsb', 'run_id') === TARGET_RUN_ID) {
    inventory.variables.push({ id: v.id, name: v.name, key: v.getSharedPluginData('dsb', 'key') });
  }
}

// Scan all component sets and frames on each page
for (const page of figma.root.children) {
  await figma.setCurrentPageAsync(page);
  // Indexed sharedPluginData lookup — much faster than findAll + getSharedPluginData per node.
  const candidates = page.findAllWithCriteria({
    sharedPluginData: { namespace: 'dsb', keys: ['run_id'] },
  });
  const nodes = candidates.filter(n => n.getSharedPluginData('dsb', 'run_id') === TARGET_RUN_ID);
  for (const n of nodes) {
    if (n.type === 'COMPONENT_SET') {
      inventory.componentSets.push({ id: n.id, name: n.name, key: n.getSharedPluginData('dsb', 'key') });
    } else if (n.type === 'FRAME') {
      inventory.frames.push({ id: n.id, name: n.name, key: n.getSharedPluginData('dsb', 'key') });
    }
  }
}

return inventory;
```

#### Step 2: Reconstruct state from inventory

Map the inventory keys back to the state ledger schema. For each entity found with a `key`, add its ID to the appropriate section. Mark the corresponding step as `completedSteps`.

Example mapping:
```
key: 'collection/color'        → entities.collections.color
key: 'variable/color/bg/primary' → entities.variables['color/bg/primary']
key: 'page/button'             → entities.pages.Button
key: 'componentset/button'     → entities.componentSets.Button
```

#### Step 3: Identify the resume point

The resume point is the first step in the workflow that is NOT in `completedSteps`. If the inventory shows the Button component set exists but the pending validations list shows `'Button:screenshot'`, the resume point is the screenshot validation call, not re-creation.

Use the checkpoint table from the workflow to determine which phase to continue from:

```
Phase 0 complete: all planned pages listed in entities.pages
Phase 1 complete: all planned variables listed in entities.variables with correct scopes
Phase 2 complete: all structural pages + foundations doc frames present
Phase 3 complete (per component): componentSet exists + no pending validations + user checkpoint recorded
```

---

### 6. Failure Taxonomy

#### Recoverable Errors

These can be fixed and retried without affecting already-created entities:

| Category | Examples | Recovery |
|---|---|---|
| Layout errors | Variants stacked at (0,0), wrong padding values | Re-run the positioning step only |
| Naming issues | Typo in variant name, wrong casing | Find nodes by `dsb_key`, update `name` property |
| Missing property wiring | `componentPropertyReferences` not set | Find component set by ID, re-run the property wiring step |
| Variable binding omission | A fill was hardcoded instead of bound | Find nodes by `dsb_key`, re-bind the fill |
| Wrong variable bound | Bound to wrong variable ID | Re-bind with correct variable ID |
| Text not visible | Font not loaded before text write | Call `listAvailableFontsAsync()` to verify the font exists, then re-run text creation with `loadFontAsync` |
| Script timeout | Script exceeded time limit before completing | Script is atomic — nothing was created. Reduce scope (fewer nodes per call) and retry |

#### Structural Corruption (Requires Rollback or Restart)

These errors leave the file in a state where continuing forward is unreliable:

| Category | Examples | Recovery |
|---|---|---|
| Component cycle | A component instance was accidentally nested inside itself | Full cleanup of the affected component, restart that component from Call 1 |
| combineAsVariants with non-components | Mixed node types passed to combineAsVariants, causing unexpected merges | Remove the malformed component set, re-run from variant creation |
| Variable collection ID drift | Collection was deleted and re-created, old IDs in state ledger are stale | Re-run Phase 1 completely; update all IDs in state ledger |
| Page deletion | A page was deleted after component sets were created on it | Treat as Phase 2 incomplete; re-create the page + re-run affected component creations |
| Mode limit exceeded | `addMode` threw because the plan is Starter or Professional | Redesign variable collection architecture to fit mode limits, restart Phase 1 |

**Recovery from structural corruption**: run `cleanupOrphans` for the entire run ID, then restart from the affected phase. Do NOT attempt to patch corrupted structure in-place.

---

### 7. Common Error Table

| Error message | Likely cause | Fix |
|---|---|---|
| `"Cannot create component from node"` | Tried to call `createComponentFromNode` on a node inside a component | Create a fresh component instead: `figma.createComponent()` |
| `"in addMode: Limited to N modes only"` | Plan mode limit hit (Starter=1, Professional=4) | Redesign to use fewer modes or upgrade plan |
| `"setCurrentPageAsync: page does not exist"` | Page was deleted or wrong ID | Re-create the page using the idempotency pattern |
| `"Cannot read properties of null"` | `getNodeByIdAsync` returned null — node was deleted | Run the resume protocol to find what exists, update state ledger |
| `"Expected nodes to be component nodes"` | Passed a non-ComponentNode to `combineAsVariants` | Filter the array: `nodes.filter(n => n.type === 'COMPONENT')` |
| `"in createVariable: Cannot create variable"` | Collection was deleted or ID is wrong | Verify collection exists with `getVariableCollectionByIdAsync` |
| `"font not loaded"` | Called a text property setter without `loadFontAsync` first | Call `await figma.listAvailableFontsAsync()` to discover available fonts and verify the font name, then `await figma.loadFontAsync({ family, style })` before the text operation |
| `"Cannot set properties of a read-only array"` | Tried to mutate fills/strokes in-place | Clone first: `const fills = JSON.parse(JSON.stringify(node.fills))` |
| `"Expected RGBA color"` | Color value out of 0–1 range | Divide RGB 0–255 values by 255: `{ r: 65/255, g: 85/255, b: 143/255 }` |
| `"Cannot add children to a non-parent node"` | Tried to append a child to a leaf node (text, rect) | Ensure the parent is a FrameNode, ComponentNode, or GroupNode |
| `"in combineAsVariants: nodes must be in the same parent"` | Components are on different pages | Move all components to the same page before combining |
| `"Script exceeded time limit"` | Loop creating too many nodes in one call | Split the work: create N/2 variants per call |
| Component set deletes itself | Tried to create a component set with no children | `combineAsVariants` requires at least 1 node — always pass 1+ |
| `addComponentProperty` returns unexpected name | This is normal — `BOOLEAN`/`TEXT`/`INSTANCE_SWAP` get `#id:id` suffix | Save the returned key immediately and use that, not the input name |

---

### 8. Per-Phase Recovery Guidance

#### Phase 1 fails (variable creation)

Since `use_figma` is atomic, a failed call creates nothing. The most common scenario is that some calls in Phase 1 succeeded (creating some variables) while a later call failed.

Recovery steps:
1. Run inspection script to find all variables tagged with your `run_id`
2. Compare against the plan to identify which variables were successfully created and which are still missing
3. If a successfully created variable has wrong values, call `variable.remove()` and recreate it
4. Fix the failed script and retry — it's safe since the failed call created nothing
5. Do NOT proceed to Phase 2 until ALL planned variables exist with correct scopes and code syntax

**The most common Phase 1 failure:** script timeout when creating many variables. Fix: batch variable creation — create at most 20–30 variables per call.

#### Phase 2 fails mid-execution (page/file structure)

Symptoms: some pages exist, others are missing; foundations doc frames are incomplete.

Recovery steps:
1. Identify which pages were successfully created (check for `key` tags)
2. Mark remaining pages as pending and create them in subsequent calls
3. If a foundations doc frame is malformed, run `cleanupOrphans` for `dsb_phase: 'phase2'` on that page, then recreate

Phase 2 failures rarely require Phase 1 rollback unless the page structure itself is corrupted (which is unusual).

#### Phase 3 fails (component creation)

This is the most common failure mode in long builds. Since `use_figma` is atomic, a failed call creates nothing — but previous successful calls in the component creation sequence will have created state. Handle by which call in the sequence failed:

```
If failure in Call 1 (page creation):
  → Nothing was created. Fix the script and retry.

If failure in Call 2 (doc frame):
  → Call 1's page exists. Fix Call 2 and retry — idempotency check handles it.

If failure in Call 3 (base component):
  → Calls 1-2 succeeded. Fix Call 3 and retry.

If failure in Call 4 (variant creation):
  → Call 3's base component exists. Fix Call 4 and retry.
  → If you need to restart from Call 3, clean up Call 3's nodes first
    using cleanupOrphans scoped to the component page.

If failure in Call 5 (combineAsVariants + layout):
  → Variant ComponentNodes from Call 4 exist but aren't combined yet.
  → Fix Call 5 and retry.
  → If the component set was already created by a prior attempt of Call 5
    that succeeded, remove it first, then re-run.

If failure in Call 6 (component properties):
  → The component set already exists and is structurally sound.
  → Fix Call 6 and retry — addComponentProperty is safe to retry if
    you first check componentPropertyDefinitions for existing properties.
  → Idempotency check: if 'Label' property already exists, skip addComponentProperty.
```

**Idempotency for component properties (Call 6 retry):**

```javascript
const existingDefs = cs.componentPropertyDefinitions;
const labelKey = existingDefs['Label']
  ? Object.keys(existingDefs).find(k => k.startsWith('Label'))
  : cs.addComponentProperty('Label', 'TEXT', 'Button');
```

#### Phase 4 fails mid-execution (QA / Code Connect)

Phase 4 is non-destructive. Failures here do not corrupt Phase 3 work. Common failures:

- **Accessibility audit finds contrast failures:** do not attempt auto-fix. Report the specific variable IDs and token names that fail, then ask the user which value to update.
- **Naming audit finds duplicates:** list all duplicates with their `key` values, ask user which to keep, then remove the duplicates.
- **Code Connect mapping fails:** treat as incomplete, not broken. Continue and leave as pending.

---

## Script — inspectFileStructure.js

```js
/**
 * inspectFileStructure
 *
 * Reads the current Figma file and returns a structural inventory:
 * all pages (with child counts), all local variable collections (with mode
 * names and variable counts), all component sets, all local text styles,
 * and all local effect styles.
 *
 * This is a read-only discovery function — it never creates or mutates nodes.
 * Run it at the start of Phase 0 to understand what already exists before
 * planning any creation work.
 *
 * @returns {Promise<{
 *   pages: Array<{id: string, name: string, childCount: number}>,
 *   variableCollections: Array<{
 *     id: string,
 *     name: string,
 *     modes: Array<{modeId: string, name: string}>,
 *     variableCount: number,
 *     variableNames: string[]
 *   }>,
 *   componentSets: Array<{id: string, name: string, variantCount: number, pageId: string, pageName: string}>,
 *   textStyles: Array<{id: string, name: string, fontFamily: string, fontStyle: string, fontSize: number}>,
 *   effectStyles: Array<{id: string, name: string, effectCount: number}>
 * }>}
 */
async function inspectFileStructure() {
  const result = {
    pages: [],
    variableCollections: [],
    componentSets: [],
    textStyles: [],
    effectStyles: [],
  }

  // --- Pages ---
  for (const page of figma.root.children) {
    result.pages.push({
      id: page.id,
      name: page.name,
      childCount: page.children.length,
    })
  }

  // --- Variable collections ---
  const collections = await figma.variables.getLocalVariableCollectionsAsync()
  for (const coll of collections) {
    const variables = await Promise.all(
      coll.variableIds.map((id) => figma.variables.getVariableByIdAsync(id)),
    )
    const variableNames = variables.filter(Boolean).map((v) => v.name)

    result.variableCollections.push({
      id: coll.id,
      name: coll.name,
      modes: coll.modes.map((m) => ({ modeId: m.modeId, name: m.name })),
      variableCount: coll.variableIds.length,
      variableNames,
    })
  }

  // --- Component sets (and standalone components) ---
  // We need to load all pages to inspect components across the whole file.
  const originalPage = figma.currentPage

  for (const page of figma.root.children) {
    await figma.setCurrentPageAsync(page)

    // findAllWithCriteria.types accepts an array — one indexed scan returns
    // both COMPONENT_SET and standalone COMPONENT nodes.
    const found = page.findAllWithCriteria({ types: ['COMPONENT_SET', 'COMPONENT'] })
    for (const node of found) {
      if (node.type === 'COMPONENT_SET') {
        result.componentSets.push({
          id: node.id,
          name: node.name,
          variantCount: node.children.length,
          pageId: page.id,
          pageName: page.name,
        })
      } else if (node.parent && node.parent.type !== 'COMPONENT_SET') {
        // Standalone component (not a variant inside a COMPONENT_SET)
        result.componentSets.push({
          id: node.id,
          name: node.name,
          variantCount: 1,
          pageId: page.id,
          pageName: page.name,
        })
      }
    }
  }

  // Restore original page
  await figma.setCurrentPageAsync(originalPage)

  // --- Text styles ---
  const textStyles = figma.getLocalTextStyles()
  for (const ts of textStyles) {
    result.textStyles.push({
      id: ts.id,
      name: ts.name,
      fontFamily: ts.fontName.family,
      fontStyle: ts.fontName.style,
      fontSize: ts.fontSize,
    })
  }

  // --- Effect styles ---
  const effectStyles = figma.getLocalEffectStyles()
  for (const es of effectStyles) {
    result.effectStyles.push({
      id: es.id,
      name: es.name,
      effectCount: es.effects.length,
    })
  }

  return result
}
```

---

## Script — createVariableCollection.js

```js
/**
 * createVariableCollection
 *
 * Creates a new Figma variable collection with the specified name and modes.
 * If `modeNames` has more than one entry, the first mode is renamed from
 * Figma's default "Mode 1" to the first name, and additional modes are added.
 *
 * Every created collection is tagged with `dsb_key` plugin data so it can be
 * found and cleaned up idempotently by `cleanupOrphans`.
 *
 * @param {string} name - The display name of the collection (e.g. "Color", "Spacing").
 * @param {string[]} modeNames - Ordered list of mode names (e.g. ["Light", "Dark"] or ["Value"]).
 * @param {string} [runId] - Optional dsb_run_id to tag for cleanup.
 * @returns {Promise<{
 *   collection: VariableCollection,
 *   modeIds: Record<string, string>
 * }>}
 *   `modeIds` maps each mode name to its modeId string.
 */
async function createVariableCollection(name, modeNames, runId) {
  if (!modeNames || modeNames.length === 0) {
    throw new Error('createVariableCollection: modeNames must have at least one entry.')
  }

  // Create the collection — Figma always creates it with one mode named "Mode 1".
  const collection = figma.variables.createVariableCollection(name)

  // Tag for idempotent cleanup
  collection.setPluginData('dsb_key', `collection/${name}`)
  if (runId) {
    collection.setPluginData('dsb_run_id', runId)
  }

  // modeIds accumulator
  const modeIds = {}

  // Rename the default first mode
  const defaultMode = collection.modes[0]
  collection.renameMode(defaultMode.modeId, modeNames[0])
  modeIds[modeNames[0]] = defaultMode.modeId

  // Add additional modes
  for (let i = 1; i < modeNames.length; i++) {
    const newModeId = collection.addMode(modeNames[i])
    modeIds[modeNames[i]] = newModeId
  }

  return { collection, modeIds }
}
```

---

## Script — createSemanticTokens.js

```js
/**
 * createSemanticTokens
 *
 * Creates a batch of Figma variables in the given collection, one per entry in
 * `tokenMap`. Supports raw values, variable alias references, code syntax, and
 * scopes. Returns a map of token name → Variable for use in subsequent steps.
 *
 * @param {VariableCollection} collection - The target variable collection.
 * @param {Record<string, string>} modeIds - Map of {modeName: modeId} from createVariableCollection.
 * @param {Array<{
 *   name: string,
 *   type: 'COLOR' | 'FLOAT' | 'STRING' | 'BOOLEAN',
 *   values: Record<string, string | number | boolean | {type: 'VARIABLE_ALIAS', id: string}>,
 *   scopes?: VariableScope[],
 *   codeSyntax?: {WEB?: string, ANDROID?: string, iOS?: string}
 * }>} tokenMap - Ordered list of token definitions.
 *   - `name`: Variable name using slash hierarchy (e.g. "color/bg/primary").
 *   - `type`: Figma variable type.
 *   - `values`: Map of {modeName: value}. Values can be raw (hex string for COLOR,
 *     number for FLOAT) or alias objects {type: 'VARIABLE_ALIAS', id: variableId}.
 *     For COLOR, raw values are accepted as hex strings ("#rrggbb" or "#rrggbbaa")
 *     and converted to {r, g, b, a} automatically.
 *   - `scopes`: Array of VariableScope strings. Omit to use [] (hidden/primitive).
 *   - `codeSyntax`: Platform code syntax strings. Omit to skip.
 * @param {string} [runId] - Optional dsb_run_id to tag every variable.
 * @returns {Promise<{variables: Record<string, Variable>}>}
 *   `variables` maps each token name to its created Variable object.
 */
async function createSemanticTokens(collection, modeIds, tokenMap, runId) {
  const variables = {}

  for (const token of tokenMap) {
    // Create the variable
    const variable = figma.variables.createVariable(token.name, collection, token.type)

    // Tag for cleanup
    variable.setPluginData('dsb_key', `variable/${token.name}`)
    if (runId) {
      variable.setPluginData('dsb_run_id', runId)
    }

    // Set values for each mode
    for (const [modeName, rawValue] of Object.entries(token.values)) {
      const modeId = modeIds[modeName]
      if (!modeId) {
        throw new Error(
          `createSemanticTokens: mode "${modeName}" not found in modeIds for token "${token.name}". ` +
            `Available modes: ${Object.keys(modeIds).join(', ')}`,
        )
      }

      let value = rawValue

      // Convert hex strings to Figma RGBA for COLOR type
      if (token.type === 'COLOR' && typeof rawValue === 'string' && rawValue.startsWith('#')) {
        value = hexToFigmaColor(rawValue)
      }

      variable.setValueForMode(modeId, value)
    }

    // Set scopes (default: empty array = hidden from property pickers / primitives)
    variable.scopes = token.scopes || []

    // Set code syntax per platform
    if (token.codeSyntax) {
      if (token.codeSyntax.WEB) {
        variable.setVariableCodeSyntax('WEB', token.codeSyntax.WEB)
      }
      if (token.codeSyntax.ANDROID) {
        variable.setVariableCodeSyntax('ANDROID', token.codeSyntax.ANDROID)
      }
      if (token.codeSyntax.iOS) {
        variable.setVariableCodeSyntax('iOS', token.codeSyntax.iOS)
      }
    }

    variables[token.name] = variable
  }

  return { variables }
}

/**
 * Converts a hex color string to a Figma RGBA object.
 * Supports "#rgb", "#rrggbb", and "#rrggbbaa".
 *
 * @param {string} hex
 * @returns {{ r: number, g: number, b: number, a: number }}
 */
function hexToFigmaColor(hex) {
  let h = hex.replace('#', '')

  // Expand shorthand #rgb → #rrggbb
  if (h.length === 3) {
    h = h
      .split('')
      .map((c) => c + c)
      .join('')
  }

  const r = parseInt(h.substring(0, 2), 16) / 255
  const g = parseInt(h.substring(2, 4), 16) / 255
  const b = parseInt(h.substring(4, 6), 16) / 255
  const a = h.length === 8 ? parseInt(h.substring(6, 8), 16) / 255 : 1

  return { r, g, b, a }
}
```

---

## Script — createComponentWithVariants.js

```js
/**
 * createComponentWithVariants
 *
 * Creates a component set by generating all combinations of `variantAxes`,
 * building one Figma component per combination, then calling
 * `figma.combineAsVariants` to produce the component set. After combining,
 * the variants are repositioned into a grid so they don't all stack at (0, 0).
 *
 * @param {{
 *   name: string,
 *   variantAxes: Record<string, string[]>,
 *   baseProps: {
 *     width: number,
 *     height: number,
 *     fills?: Paint[],
 *     padding?: {top?: number, bottom?: number, left?: number, right?: number},
 *     radius?: number,
 *     layoutMode?: 'HORIZONTAL' | 'VERTICAL' | 'NONE',
 *     itemSpacing?: number
 *   },
 *   page: PageNode
 * }} config
 *   - `name`: Component set name (e.g. "Button").
 *   - `variantAxes`: Each key is a variant property name; each value is an array of
 *     allowed values. All combinations are generated (Cartesian product).
 *     Example: { Size: ['Small', 'Medium', 'Large'], Style: ['Primary', 'Ghost'] }
 *     produces 6 variants.
 *   - `baseProps`: Visual properties applied to every variant.
 *   - `page`: The PageNode to create components on (must be set as current page by caller).
 * @param {string} [runId] - Optional dsb_run_id to tag every node.
 * @returns {Promise<{
 *   componentSet: ComponentSetNode,
 *   variants: ComponentNode[]
 * }>}
 */
async function createComponentWithVariants(config, runId) {
  const { name, variantAxes, baseProps, page } = config

  // Ensure we are on the correct page
  await figma.setCurrentPageAsync(page)

  // Compute Cartesian product of variant axes
  const axisNames = Object.keys(variantAxes)
  const axisValues = axisNames.map((k) => variantAxes[k])
  const combinations = cartesianProduct(axisValues)

  // Build one component per combination
  const components = []
  for (const combo of combinations) {
    const comp = figma.createComponent()

    // Name: "Property=Value, Property=Value, ..."
    comp.name = axisNames.map((ax, i) => `${ax}=${combo[i]}`).join(', ')

    // Base geometry
    comp.resize(baseProps.width, baseProps.height)

    // Fills
    if (baseProps.fills !== undefined) {
      comp.fills = baseProps.fills
    } else {
      comp.fills = [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }]
    }

    // Corner radius
    if (baseProps.radius !== undefined) {
      comp.cornerRadius = baseProps.radius
    }

    // Auto-layout
    if (baseProps.layoutMode && baseProps.layoutMode !== 'NONE') {
      comp.layoutMode = baseProps.layoutMode
      comp.primaryAxisAlignItems = 'CENTER'
      comp.counterAxisAlignItems = 'CENTER'
      if (baseProps.itemSpacing !== undefined) {
        comp.itemSpacing = baseProps.itemSpacing
      }
    }

    // Padding
    if (baseProps.padding) {
      comp.paddingTop = baseProps.padding.top ?? 0
      comp.paddingBottom = baseProps.padding.bottom ?? 0
      comp.paddingLeft = baseProps.padding.left ?? 0
      comp.paddingRight = baseProps.padding.right ?? 0
    }

    // Plugin data
    const variantKey = axisNames.map((ax, i) => `${ax}:${combo[i]}`).join('|')
    comp.setPluginData('dsb_key', `component/${name}/${variantKey}`)
    if (runId) {
      comp.setPluginData('dsb_run_id', runId)
    }

    page.appendChild(comp)
    components.push(comp)
  }

  // Combine into a component set
  const componentSet = figma.combineAsVariants(components, page)
  componentSet.name = name
  componentSet.setPluginData('dsb_key', `componentSet/${name}`)
  if (runId) {
    componentSet.setPluginData('dsb_run_id', runId)
  }

  // Grid layout — variants stack at (0, 0) after combineAsVariants; reposition them.
  const GRID_GAP = 16
  const cols = Math.max(1, axisValues[axisValues.length - 1]?.length ?? 1)
  const variantWidth = baseProps.width
  const variantHeight = baseProps.height

  componentSet.children.forEach((variant, idx) => {
    const col = idx % cols
    const row = Math.floor(idx / cols)
    variant.x = col * (variantWidth + GRID_GAP)
    variant.y = row * (variantHeight + GRID_GAP)
  })

  // Resize component set to wrap its children with padding
  const totalCols = Math.min(cols, combinations.length)
  const totalRows = Math.ceil(combinations.length / cols)
  const PADDING = 40
  componentSet.resize(
    totalCols * variantWidth + (totalCols - 1) * GRID_GAP + PADDING * 2,
    totalRows * variantHeight + (totalRows - 1) * GRID_GAP + PADDING * 2,
  )

  // Position component set at a safe canvas location
  componentSet.x = 480
  componentSet.y = 80

  return { componentSet, variants: componentSet.children }
}

/**
 * Computes the Cartesian product of multiple arrays.
 * cartesianProduct([[A, B], [1, 2]]) → [[A,1], [A,2], [B,1], [B,2]]
 *
 * @param {Array<string[]>} arrays
 * @returns {string[][]}
 */
function cartesianProduct(arrays) {
  return arrays.reduce(
    (acc, curr) => acc.flatMap((combo) => curr.map((val) => [...combo, val])),
    [[]],
  )
}
```

---

## Script — bindVariablesToComponent.js

```js
/**
 * bindVariablesToComponent
 *
 * Binds design token variables to the visual properties of a component node.
 * Supports fills, strokes, all padding directions, item spacing, and corner radius.
 * Only binds properties for which a variable ID is provided in `bindings`.
 *
 * This function should be called on each variant individually within a component
 * set, OR on the component set itself for properties shared by all variants.
 *
 * @param {ComponentNode | FrameNode | RectangleNode} component
 *   The Figma node to mutate. Usually a ComponentNode or one of its children.
 * @param {{
 *   fills?: string,
 *   strokes?: string,
 *   paddingTop?: string,
 *   paddingBottom?: string,
 *   paddingLeft?: string,
 *   paddingRight?: string,
 *   itemSpacing?: string,
 *   cornerRadius?: string
 * }} bindings
 *   Each key is a visual property name; each value is a Figma Variable ID
 *   (e.g. "VariableID:123:456"). Omit a key to skip binding that property.
 * @returns {Promise<{ mutatedNodeIds: string[] }>}
 *   List of node IDs that were mutated (for audit/validation purposes).
 */
async function bindVariablesToComponent(component, bindings) {
  const mutatedNodeIds = []

  if (!component) {
    return { mutatedNodeIds }
  }

  // Batch every getVariableByIdAsync call upfront in a single Promise.all rather
  // than awaiting per-property — the lookups are independent and IPC-bound.
  const floatBindings = [
    ['paddingTop', 'paddingTop'],
    ['paddingBottom', 'paddingBottom'],
    ['paddingLeft', 'paddingLeft'],
    ['paddingRight', 'paddingRight'],
    ['itemSpacing', 'itemSpacing'],
    ['cornerRadius', 'cornerRadius'],
  ]

  const requestedIds = []
  if (bindings.fills) requestedIds.push(['fills', bindings.fills])
  if (bindings.strokes) requestedIds.push(['strokes', bindings.strokes])
  for (const [bindingKey] of floatBindings) {
    if (bindings[bindingKey]) requestedIds.push([bindingKey, bindings[bindingKey]])
  }

  const resolved = await Promise.all(
    requestedIds.map(([, id]) => figma.variables.getVariableByIdAsync(id)),
  )
  const varByKey = {}
  for (let i = 0; i < requestedIds.length; i++) {
    varByKey[requestedIds[i][0]] = resolved[i]
  }

  const markMutated = () => {
    if (!mutatedNodeIds.includes(component.id)) {
      mutatedNodeIds.push(component.id)
    }
  }

  // --- Fills ---
  const fillVar = varByKey.fills
  if (fillVar) {
    const existingFills = component.fills
    if (Array.isArray(existingFills) && existingFills.length > 0) {
      // Bind the color of the first fill to the variable
      const boundFill = figma.variables.setBoundVariableForPaint(existingFills[0], 'color', fillVar)
      component.fills = [boundFill, ...existingFills.slice(1)]
    } else {
      // No existing fill — create a solid fill bound to the variable
      const boundFill = figma.variables.setBoundVariableForPaint(
        { type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } },
        'color',
        fillVar,
      )
      component.fills = [boundFill]
    }
    markMutated()
  }

  // --- Strokes ---
  const strokeVar = varByKey.strokes
  if (strokeVar) {
    const existingStrokes = component.strokes
    if (Array.isArray(existingStrokes) && existingStrokes.length > 0) {
      const boundStroke = figma.variables.setBoundVariableForPaint(
        existingStrokes[0],
        'color',
        strokeVar,
      )
      component.strokes = [boundStroke, ...existingStrokes.slice(1)]
    } else {
      const boundStroke = figma.variables.setBoundVariableForPaint(
        { type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } },
        'color',
        strokeVar,
      )
      component.strokes = [boundStroke]
    }
    markMutated()
  }

  // --- Spacing properties (FLOAT variables bound via setBoundVariable) ---
  for (const [bindingKey, figmaProp] of floatBindings) {
    const variable = varByKey[bindingKey]
    if (variable) {
      component.setBoundVariable(figmaProp, variable)
      markMutated()
    }
  }

  return { mutatedNodeIds }
}
```

---

## Script — createDocumentationPage.js

```js
/**
 * createDocumentationPage
 *
 * Creates a new Figma page with a standardized documentation layout: a page
 * title, optional description, and an ordered list of sections each built by
 * a caller-supplied `contentFn`. The content function receives the section
 * frame and may append any nodes to it.
 *
 * This function is used for standalone documentation pages (e.g. a Foundations
 * page, a Getting Started page, or a component page with documentation).
 * It does not handle component sets — those live on separate pages created by
 * createComponentWithVariants.
 *
 * @param {string} pageName - The Figma page name (e.g. "Foundations", "Getting Started").
 * @param {{
 *   title: string,
 *   description?: string,
 *   sections: Array<{
 *     name: string,
 *     contentFn: (sectionFrame: FrameNode) => Promise<void>
 *   }>
 * }} config
 *   - `title`: Large heading displayed at the top of the page.
 *   - `description`: Optional subtitle displayed below the heading.
 *   - `sections`: Ordered list of sections. Each section gets its own frame
 *     with a heading and is passed to `contentFn` for population.
 * @param {string} [runId] - Optional dsb_run_id to tag every created node.
 * @returns {Promise<{
 *   page: PageNode,
 *   titleNode: TextNode,
 *   frameIds: string[]
 * }>}
 *   `frameIds` is an ordered list of IDs for the root frame and each section frame.
 */
async function createDocumentationPage(pageName, config, runId) {
  // Verify required fonts are available before loading
  const allFonts = await figma.listAvailableFontsAsync()
  const requiredStyles = ['Bold', 'Regular', 'Medium']
  for (const style of requiredStyles) {
    const found = allFonts.some((f) => f.fontName.family === 'Inter' && f.fontName.style === style)
    if (!found) {
      const interFonts = allFonts.filter((f) => f.fontName.family === 'Inter')
      throw new Error(
        `Font "Inter ${style}" not available. Available Inter styles: ${interFonts.map((f) => f.fontName.style).join(', ') || 'none'}`,
      )
    }
  }
  await Promise.all([
    figma.loadFontAsync({ family: 'Inter', style: 'Bold' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Regular' }),
    figma.loadFontAsync({ family: 'Inter', style: 'Medium' }),
  ])

  // Create and activate the page
  const page = figma.createPage()
  page.name = pageName
  await figma.setCurrentPageAsync(page)

  if (runId) {
    page.setPluginData('dsb_run_id', runId)
    page.setPluginData('dsb_key', `page/${pageName}`)
  }

  const frameIds = []

  // Root scroll container — 1440px wide, auto-height
  const root = figma.createAutoLayout('VERTICAL')
  root.name = pageName
  root.primaryAxisAlignItems = 'MIN'
  root.counterAxisAlignItems = 'MIN'
  root.itemSpacing = 80
  root.paddingTop = 80
  root.paddingBottom = 120
  root.paddingLeft = 80
  root.paddingRight = 80
  root.resize(1440, 1)
  root.layoutSizingHorizontal = 'FIXED'
  root.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }]
  root.x = 0
  root.y = 0
  page.appendChild(root)

  if (runId) {
    root.setPluginData('dsb_run_id', runId)
    root.setPluginData('dsb_key', `frame/root/${pageName}`)
  }

  frameIds.push(root.id)

  // Page header: title + optional description
  const header = figma.createAutoLayout('VERTICAL')
  header.name = 'Header'
  header.itemSpacing = 12
  header.fills = []
  root.appendChild(header)
  header.layoutSizingHorizontal = 'FILL'

  const titleNode = figma.createText()
  titleNode.fontName = { family: 'Inter', style: 'Bold' }
  titleNode.characters = config.title
  titleNode.fontSize = 40
  titleNode.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }]
  titleNode.layoutSizingHorizontal = 'FILL'
  header.appendChild(titleNode)

  if (config.description) {
    const descNode = figma.createText()
    descNode.fontName = { family: 'Inter', style: 'Regular' }
    descNode.characters = config.description
    descNode.fontSize = 16
    descNode.lineHeight = { value: 24, unit: 'PIXELS' }
    descNode.fills = [{ type: 'SOLID', color: { r: 0.4, g: 0.4, b: 0.4 } }]
    descNode.layoutSizingHorizontal = 'FILL'
    header.appendChild(descNode)
  }

  // Sections
  for (const section of config.sections) {
    const sectionFrame = figma.createAutoLayout('VERTICAL')
    sectionFrame.name = `Section/${section.name}`
    sectionFrame.itemSpacing = 20
    sectionFrame.fills = []
    root.appendChild(sectionFrame)
    sectionFrame.layoutSizingHorizontal = 'FILL'

    if (runId) {
      sectionFrame.setPluginData('dsb_run_id', runId)
      sectionFrame.setPluginData('dsb_key', `frame/section/${pageName}/${section.name}`)
    }

    // Section heading
    const sectionHeading = figma.createText()
    sectionHeading.fontName = { family: 'Inter', style: 'Bold' }
    sectionHeading.characters = section.name
    sectionHeading.fontSize = 24
    sectionHeading.fills = [{ type: 'SOLID', color: { r: 0.07, g: 0.07, b: 0.07 } }]
    sectionHeading.layoutSizingHorizontal = 'FILL'
    sectionFrame.appendChild(sectionHeading)

    // Invoke the caller's content function to populate the section
    await section.contentFn(sectionFrame)

    frameIds.push(sectionFrame.id)
  }

  return { page, titleNode, frameIds }
}
```

---

## Script — validateCreation.js

```js
/**
 * validateCreation
 *
 * Verifies that a set of nodes exist and match expected structural properties.
 * Designed to run immediately after a creation script to catch partial failures
 * before proceeding to the next build phase.
 *
 * Each check specifies a node ID and any combination of expected properties.
 * A check passes when all specified expectations are met; it fails (with a
 * reason string) as soon as any expectation is violated.
 *
 * @param {Array<{
 *   nodeId: string,
 *   expectedChildCount?: number,
 *   expectedName?: string,
 *   expectedType?: NodeType
 * }>} checks
 *   - `nodeId`: The Figma node ID to look up via figma.getNodeById.
 *   - `expectedChildCount`: If set, the node must have exactly this many direct children.
 *     Applies to any node with a `children` property (frames, component sets, etc.).
 *   - `expectedName`: If set, the node's `.name` must exactly match this string.
 *   - `expectedType`: If set, the node's `.type` must exactly match this string.
 * @returns {{
 *   passed: string[],
 *   failed: Array<{nodeId: string, reason: string}>
 * }}
 *   `passed`: Array of nodeIds that passed all checks.
 *   `failed`: Array of objects with the nodeId and a human-readable reason string.
 */
function validateCreation(checks) {
  const passed = []
  const failed = []

  for (const check of checks) {
    const node = figma.getNodeById(check.nodeId)

    // Node must exist
    if (!node) {
      failed.push({
        nodeId: check.nodeId,
        reason: `Node not found. It may not have been created, or was deleted.`,
      })
      continue
    }

    const reasons = []

    // Type check
    if (check.expectedType !== undefined && node.type !== check.expectedType) {
      reasons.push(`type is "${node.type}", expected "${check.expectedType}"`)
    }

    // Name check
    if (check.expectedName !== undefined && node.name !== check.expectedName) {
      reasons.push(`name is "${node.name}", expected "${check.expectedName}"`)
    }

    // Child count check
    if (check.expectedChildCount !== undefined) {
      if (!('children' in node)) {
        reasons.push(
          `node type "${node.type}" does not have children, but expectedChildCount=${check.expectedChildCount} was specified`,
        )
      } else {
        const actualCount = node.children.length
        if (actualCount !== check.expectedChildCount) {
          reasons.push(`has ${actualCount} children, expected ${check.expectedChildCount}`)
        }
      }
    }

    if (reasons.length > 0) {
      failed.push({
        nodeId: check.nodeId,
        reason: reasons.join('; '),
      })
    } else {
      passed.push(check.nodeId)
    }
  }

  return { passed, failed }
}
```

---

## Script — cleanupOrphans.js

```js
/**
 * cleanupOrphans
 *
 * Finds and removes all Figma nodes (pages, frames, components, variables,
 * and variable collections) that were tagged with the given `dsb_run_id`
 * by a previous build run. This is safe cleanup: it uses plugin data tags,
 * never name-prefix matching, so it cannot accidentally delete user-owned nodes.
 *
 * Use this when a build run fails mid-way and you need to reset to a clean
 * slate before retrying. The function traverses the entire document looking
 * for `dsb_run_id` plugin data matching `runId`.
 *
 * Variables and variable collections are handled separately (they are not
 * scene nodes and cannot be discovered via node traversal).
 *
 * @param {string} runId - The dsb_run_id value to match (e.g. "ds-build-2024-001").
 * @returns {Promise<{
 *   removedCount: number,
 *   removedIds: string[]
 * }>}
 */
async function cleanupOrphans(runId) {
  if (!runId) {
    throw new Error('cleanupOrphans: runId is required.')
  }

  const removedIds = []
  const originalPage = figma.currentPage

  // --- Remove tagged scene nodes (pages, frames, components, etc.) ---
  // Collect pages to remove (can't remove during iteration)
  const pagesToRemove = []

  for (const page of figma.root.children) {
    if (page.getPluginData('dsb_run_id') === runId) {
      pagesToRemove.push(page)
      continue
    }

    // Traverse all nodes on this page
    await figma.setCurrentPageAsync(page)

    // Use the pluginData index to find candidates, then keep only those whose
    // run_id matches. Much faster than findAll + getPluginData on every node.
    const candidates = page.findAllWithCriteria({
      pluginData: { keys: ['dsb_run_id'] },
    })
    const tagged = candidates.filter((node) => node.getPluginData('dsb_run_id') === runId)
    // Drop descendants of already-collected nodes (removing the parent removes
    // its children, so we only need the topmost match in each chain).
    const taggedSet = new Set(tagged)
    const nodesToRemove = tagged.filter((node) => {
      let p = node.parent
      while (p) {
        if (taggedSet.has(p)) return false
        p = p.parent
      }
      return true
    })

    // Remove deepest nodes first (children before parents) to avoid
    // "parent no longer exists" errors
    const sorted = nodesToRemove.sort((a, b) => {
      // Sort by depth descending: deeper nodes first
      return getDepth(b) - getDepth(a)
    })

    for (const node of sorted) {
      if (node && node.parent) {
        removedIds.push(node.id)
        node.remove()
      }
    }
  }

  // Remove tagged pages last
  for (const page of pagesToRemove) {
    // Cannot remove the last page in the document
    if (figma.root.children.length <= 1) {
      break
    }
    removedIds.push(page.id)
    page.remove()
  }

  // --- Remove tagged variables ---
  const allVariables = await figma.variables.getLocalVariablesAsync()
  for (const variable of allVariables) {
    if (variable.getPluginData('dsb_run_id') === runId) {
      removedIds.push(variable.id)
      variable.remove()
    }
  }

  // --- Remove tagged variable collections ---
  // Must be done after variables are removed
  const allCollections = await figma.variables.getLocalVariableCollectionsAsync()
  for (const collection of allCollections) {
    if (collection.getPluginData('dsb_run_id') === runId) {
      removedIds.push(collection.id)
      collection.remove()
    }
  }

  // Restore original page (if it still exists)
  try {
    await figma.setCurrentPageAsync(originalPage)
  } catch (_) {
    // Original page was removed — switch to first available page
    if (figma.root.children.length > 0) {
      await figma.setCurrentPageAsync(figma.root.children[0])
    }
  }

  return {
    removedCount: removedIds.length,
    removedIds,
  }
}

/**
 * Returns the depth of a node in the document tree.
 * Root children (pages) have depth 1; their children have depth 2; etc.
 *
 * @param {BaseNode} node
 * @returns {number}
 */
function getDepth(node) {
  let depth = 0
  let current = node
  while (current.parent) {
    depth++
    current = current.parent
  }
  return depth
}
```

---

## Script — rehydrateState.js

```js
/**
 * Scans the entire Figma file for nodes tagged with dsb_* pluginData
 * and returns a complete state map for session recovery.
 *
 * Use this at the start of every new session, after context truncation,
 * or when resuming an interrupted build.
 *
 * @param {string} runId - The run ID to filter by (optional — if omitted, returns ALL dsb-tagged nodes)
 * @returns {{ runId: string, taggedNodes: Object<string, {nodeId: string, type: string, name: string, phase: string}>, variableCollections: Array, variables: Array, styles: Array }}
 */
async function rehydrateState(runId) {
  const taggedNodes = {}
  const variableCollections = []
  const variables = []
  const styles = []

  // Scan all pages for dsb-tagged scene nodes
  for (const page of figma.root.children) {
    await figma.setCurrentPageAsync(page)

    // Check the page itself
    const pageRunId = page.getPluginData('dsb_run_id')
    const pageKey = page.getPluginData('dsb_key')
    if (pageKey && (!runId || pageRunId === runId)) {
      taggedNodes[pageKey] = {
        nodeId: page.id,
        type: page.type,
        name: page.name,
        phase: page.getPluginData('dsb_phase') || 'unknown',
      }
    }

    // Use findAllWithCriteria with the pluginData index — drastically faster
    // than findAll + getPluginData on every node, because the engine narrows
    // to nodes that actually have these keys.
    const tagged = page.findAllWithCriteria({
      pluginData: { keys: ['dsb_key', 'dsb_run_id'] },
    })
    for (const node of tagged) {
      const nodeRunId = node.getPluginData('dsb_run_id')
      const nodeKey = node.getPluginData('dsb_key')
      if (nodeKey && (!runId || nodeRunId === runId)) {
        taggedNodes[nodeKey] = {
          nodeId: node.id,
          type: node.type,
          name: node.name,
          phase: node.getPluginData('dsb_phase') || 'unknown',
        }
      }
    }
  }

  // Inventory variable collections (variables don't support pluginData — use name-based lookup)
  const collections = await figma.variables.getLocalVariableCollectionsAsync()
  for (const coll of collections) {
    variableCollections.push({
      id: coll.id,
      name: coll.name,
      modes: coll.modes.map((m) => ({ modeId: m.modeId, name: m.name })),
      variableCount: coll.variableIds.length,
    })
  }

  // Inventory variables (name + collection for idempotency key)
  const allVars = await figma.variables.getLocalVariablesAsync()
  for (const v of allVars) {
    variables.push({
      id: v.id,
      name: v.name,
      collectionId: v.variableCollectionId,
      resolvedType: v.resolvedType,
    })
  }

  // Inventory styles
  for (const s of figma.getLocalTextStyles()) {
    styles.push({ id: s.id, name: s.name, type: 'TEXT' })
  }
  for (const s of figma.getLocalEffectStyles()) {
    styles.push({ id: s.id, name: s.name, type: 'EFFECT' })
  }
  for (const s of figma.getLocalPaintStyles()) {
    styles.push({ id: s.id, name: s.name, type: 'PAINT' })
  }

  return {
    runId: runId || 'all',
    taggedNodes,
    taggedNodeCount: Object.keys(taggedNodes).length,
    variableCollections,
    variableCount: variables.length,
    variables,
    styleCount: styles.length,
    styles,
  }
}
```
