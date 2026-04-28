---
name: generate-project-plan
description: "Generate a FigJam project plan board from a PRD plus codebase context. Interactive flow: research → propose sections → per-section deep research → per-section content + block-shape proposal → create FigJam → skeleton → fill → diagrams → wrap. Each content block (section, nested section, intro callout, table, multi-column text, sticky column, diagram section, metadata strip) has its own subskill reference file. Use when the user asks for 'project plan in FigJam', 'interactive project plan', '/generate-project-plan', or provides a PRD and wants per-section confirmation on content + rendering."
disable-model-invocation: false
---

# generate-project-plan

Turn a PRD (plus optional codebase grounding) into a FigJam project plan board. Section set is not fixed — the skill proposes candidates from the research and the user picks which to include. For each picked section, the skill proposes content + rendering shape (block) and the user confirms.

## Mandatory prerequisites

**Foundation skills** (load by name; available in `figma/mcp-server-guide`):

- `figma-use` — **Load once per session.** Stays in context for all `use_figma` calls.
- `figma-use-figjam` — **Re-load before every `use_figma` call.**
- `figma-generate-diagram` — **Re-load before every `generate_diagram` call.**

**Foundation references** (in this plugin):

- [`foundation/palette.md`](references/foundation/palette.md) — section + sticky + text palette constants (`hex/255`).
- [`foundation/layout.md`](references/foundation/layout.md) — canvas geometry, sizing rules, placeholder lifecycle.
- [`foundation/plugin-api-traps.md`](references/foundation/plugin-api-traps.md) — documented traps for FigJam `use_figma`.
- [`foundation/codebase-grounding.md`](references/foundation/codebase-grounding.md) — Step 1 expansion rules.

**Section catalog**:

- [`section-catalog.md`](references/section-catalog.md) — the ~10 candidate sections with default blocks and palette.

**Block subskills** (one per content type — re-load the one(s) you need before each `use_figma` fill call):

| Block | File | When to load |
|---|---|---|
| Top-level section | [`blocks/section.md`](references/blocks/section.md) | Skeleton pass (Step 6) and every fill call (Step 7) |
| Nested section | [`blocks/nested-section.md`](references/blocks/nested-section.md) | Fills that group sub-content (e.g. "Design Decisions 1/2/3") |
| Intro callout | [`blocks/intro-callout.md`](references/blocks/intro-callout.md) | Fills that open with a highlighted intro (e.g. Motivation) |
| Text primitives | [`blocks/text-primitives.md`](references/blocks/text-primitives.md) | Any fill that uses body paragraphs, H3 subheaders, or bulleted lists |
| Table | [`blocks/table.md`](references/blocks/table.md) | Fills with structured data (Resources, Goals, Dependencies, Rollout, Milestones) |
| Multi-column text | [`blocks/multi-column-text.md`](references/blocks/multi-column-text.md) | Fills with 2–4 option columns (Design Decisions alternatives) |
| Sticky column | [`blocks/sticky-column.md`](references/blocks/sticky-column.md) | Fills with lists of stickies (Success Metrics, Risks, Open Questions) |
| Diagram section | [`blocks/diagram-section.md`](references/blocks/diagram-section.md) | Right-column diagram sections (Step 8) |
| Metadata strip | [`blocks/metadata-strip.md`](references/blocks/metadata-strip.md) | Skeleton pass — one metadata strip at top of board |

**Also pass** `skillNames: "figma-use,figma-use-figjam,generate-project-plan"` on `use_figma` calls (logging only).

## Visual UI conventions — STRICT, do not deviate

These are derived from a canonical reference board. Read the source-of-truth files for the full constants; this section is a single-place summary so an agent can answer "what color / size / font / padding?" without hunting.

### Colors (two-tone per section)

Every left-column section uses **two coordinated colors** of the same hue: a very-pale `ARCH_PALE` background, and a slightly-more-saturated FigJam-`SECTION` palette color for any table header inside that section. Right-column diagram sections are pure white.

| Section bg (`ARCH_PALE.X`) | Table header (`TABLE_HEADER.lightX`) | Hue |
|---|---|---|
| `#F8F5FF` | `#DCCCFF` | violet |
| `#EBFFEE` | `#CDF4D3` | green |
| `#DBF0FF` | `#C2E5FF` | blue |
| `#F5FBFF` (alt) | `#C2E5FF` | pale blue |
| `#FFF7F0` | `#FFE0C2` | orange |
| `#F1FEFD` | `#C6FAF6` | teal |
| `#FFFBF0` | `#FFEC BD` | yellow |
| `#FFEEF8` | `#FFC2EC` | pink |
| `#FFEEE8` | `#FFCDC2` | red |

Source: `references/foundation/palette.md`. Never use the dark-saturated palette (`#874FFF`, `#3DADFF`, etc.) for table headers — that's for FigJam's standalone tables, not project-plan boards.

Architecture-diagram subgraph colors are auto-applied by `generate_diagram` and **must not be overridden**. Their canonical values: `client #AFF4C6` rounded-rect, `gateway #FFFFFF` square (diamond if labeled "Load Balancer"/"ALB"/"LB"), `service #E4CCFF` square, `datastore #BDE3FF` cylinder, `external #FFFFFF` PREDEFINED_PROCESS, `async #BDE3FF` ENG_QUEUE.

### Typography (font sizes)

| Element | Size | Font | Color |
|---|---|---|---|
| H1 (board title) | **40** | Inter Medium | `#1E1E1E` |
| H2 (section title — first child of every section) | 40 | Inter Medium | `#1E1E1E` |
| H3 — full-width subhead (e.g. "Resources" inside Motivation) | **40** | Inter Medium | `#1E1E1E` |
| H3 — nested-section header (e.g. "Design Decision 1: …") | **32** | Inter Medium | `#1E1E1E` |
| H3 — column title in 2/3/4-col layouts (Risks col, Goals col) | **24** | Inter Medium | `#1E1E1E` |
| Body text | 16 | Inter Medium | `#1E1E1E` |
| Table cells (header AND body) | 16 | **Inter Bold** | `#1E1E1E` |

The three different H3 sizes are deliberate. 40 = matches H2 weight when subhead is alone in the section. 32 = sub-section header inside a child section (672px inner width). 24 = column title in narrow contexts (≤ 224px col width). Pick by **container width**, not by semantic depth.

Always load both `Inter Medium` AND `Inter Bold` at the top of any `use_figma` script that creates tables (Bold) plus any other text (Medium).

### Section properties

| Property | Value |
|---|---|
| `section.fills` | `[{ type: 'SOLID', color: ARCH_PALE.X }]` (left column) or `ARCH_PALE.white` (right column / diagrams) |
| `section.name` | `""` — empty string. NO FigJam title-bar label. The H2 inside is the only title. |
| Inner padding (all 4 sides) | 32 (current default; reference uses 40-50, kept at 32 for now) |
| First child position | `(32, 32)` |
| Width (left column) | 800 |
| Width (right column / diagram) | `max(1200, diag.width + 64)` after diagram is reparented |
| Vertical gap between sections (inside the wrapper) | **64** |
| Hug behavior | Manual: call `section.resizeWithoutConstraints(w, maxChildBottom + 32)` after appending children. Sections do NOT auto-grow. |
| Placeholder during build | `placeholder = true` in skeleton pass; `placeholder = false` at the end of the section's fill. |

### Outer wrapper + column alignment (STRICT defaults)

The board has **one outer wrapper** (unlabeled, white) plus the diagram column:

1. **Column wrapper** — an unlabeled white SECTION at `(_, 0)`. Contains, in order from top:
   - H1 project title (40px Inter Medium, charcoal) at `(64, 64)` (= section padding)
   - Body row of metadata: Owner / Status / Last updated / Source (16px Inter Medium, charcoal), at `(64, h1.y + h1.height + 16)` — 16px gap below H1; 32px gap between each body cell
   - 64px gap below the body row, then the 6 left-column sections stacked with 64px gutter
2. **Diagram column** at `(columnWrapperRight + 64, 0)`. Each diagram is its own un-wrapped white SECTION; the **top diagram's y aligns with the column wrapper's y (= 0)**. Diagrams stack with 64px gutter.

The metadata is **embedded** in the column wrapper (NOT a separate section). One column wrapper holds everything text-related.

**Constants:**
- Wrapper inner padding (all 4 sides): **64**
- Vertical gap between sections inside the wrapper: **64**
- Horizontal gap between wrapper right edge and diagram-column left edge: **64**
- Top of the diagram column aligns with `wrapper.y` (same horizontal axis as the wrapper top edge)
- Vertical gap between stacked diagram sections: **64** (matches the inner gutter)

```js
const PAD = 64;
const leftIds = [/* all left-column section ids in order */];
const sections = [];
for (const id of leftIds) sections.push(await figma.getNodeByIdAsync(id));

// Compute bbox of the column in page coords
let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
for (const s of sections) {
  minX = Math.min(minX, s.x); minY = Math.min(minY, s.y);
  maxX = Math.max(maxX, s.x + s.width); maxY = Math.max(maxY, s.y + s.height);
}

const wrapper = figma.createSection();
wrapper.name = "";                                                              // STRICT
wrapper.fills = [{ type: 'SOLID', color: WHITE }];                              // ARCH_PALE.white
wrapper.resizeWithoutConstraints((maxX - minX) + 2*PAD, (maxY - minY) + 2*PAD);
wrapper.x = minX - PAD;
wrapper.y = minY - PAD;

// Reparent + translate to keep visual positions
for (const s of sections) {
  const newX = (s.x - minX) + PAD;
  const newY = (s.y - minY) + PAD;
  wrapper.appendChild(s);
  s.x = newX;
  s.y = newY;
}
```

The wrapper has no header (no H2 inside) and no name — it's a pure container. Don't repeat the project title here; that lives in the metadata strip.

**Position the diagram column** after the wrapper exists:

```js
const wrapperRight = wrapper.x + wrapper.width;
const diagramX = wrapperRight + 64;       // 64px horizontal gap matches inter-section gutter
let y = wrapper.y;                          // align top with wrapper's top edge
for (const id of diagramSectionIdsInOrder) {
  const d = await figma.getNodeByIdAsync(id);
  d.x = diagramX;
  d.y = y;
  y += d.height + 64;                     // 64px vertical gutter between stacked diagrams
}
```

### Vertical spacing (STRICT)

| Between | Gap |
|---|---|
| Section top edge → H2 (first child) | 32 (= padding) |
| H2 → next child (body / intro callout / H3 / table / first column) | **24** |
| Body paragraph → H3 | **24** |
| H3 (any size: 40 / 32 / 24) → next child (body / table / list / column content) | **24** |
| Body → body | **24** |
| List → next block | **24** |
| Last child bottom → section bottom edge | 32 (= padding) |

**Always position children using `prevChild.y + prevChild.height + 24`** — never use a fixed offset like `prevChild.y + 60`. The H3 has three different sizes (40 / 32 / 24), so a fixed offset is wrong by definition; always read `prevChild.height` after the font size is set.

**When you change a header's font size after the fact, you MUST re-stack downstream children.** Setting `h3.fontSize = 40` grows the node's height; if the next child's `y` was computed before the resize, it will overlap.

### Tables

- **Both header AND body cells** use `Inter Bold` 16px (NOT Medium).
- Header text is `#1E1E1E` charcoal on a light fill (matching the section's hue).
- Body cells leave fill at default white; text is charcoal.
- Headers do NOT use white-on-dark — that's wrong for this board style.

### Diagrams (right column)

`generate_diagram` with `useArchitectureLayoutCode: "FIGMA_DIAGRAM_2026"` produces **multiple page-level nodes** (1–2 subgraph SECTIONs + bare SHAPE_WITH_TEXTs + CONNECTORs), NOT a single container. To wrap them in a section:
1. Collect all new page-level nodes (exclude known plan-section IDs).
2. Compute the bbox.
3. Create a new SECTION sized to `bboxW + 64 × bboxH + 64 + 64` (HEADER_BLOCK = 40 H2 + 24 gap), fill `ARCH_PALE.white`.
4. Reparent each diagram node, translating local coords to maintain visual layout.
5. **CRITICAL — delete and recreate every connector after reparent.** The assign-to-self trick (`c.connectorStart = c.connectorStart`) is NOT reliable: short connectors re-route fine, but long-bend connectors retain stale elbow waypoints and extend hundreds of pixels outside the section. Delete + `figma.createConnector()` from captured spec produces a clean route every time. See [`blocks/diagram-section.md`](references/blocks/diagram-section.md) for the spec-capture + recreate pattern.
6. **Connector labels — explicit `fontName` + `fontSize` + `fills` ALL required.** A fresh connector's `text` sublayer has no usable defaults. Set ALL FOUR: `c.text.fontName = { family: 'Inter', style: 'Medium' }`, `c.text.fontSize = 14`, `c.text.characters = label`, `c.text.fills = [{ type: 'SOLID', color: CHARCOAL }]`. Default `text.fills` is **`[]` (empty array)** so the label renders **transparent** and is invisible — read-back of `c.text.characters` lies; verify with a screenshot.

Diagram-section convention: `section.name = ""`, H2 text node inside as the title (matches the rest of the board).

### What NOT to use (common wrong defaults)

| Don't use | Use instead | Why |
|---|---|---|
| `#CDF4D3` (FigJam lightGreen) for section bg | `#EBFFEE` (ARCH_PALE.green) | Too saturated next to diagrams |
| `#C2E5FF` (FigJam lightBlue) for section bg | `#DBF0FF` or `#F5FBFF` (ARCH_PALE.blue / blueLite) | Same |
| `#874FFF` (FigJam dark violet) for table header | `#DCCCFF` (FigJam lightViolet) | Reference uses light-on-pale, not dark-on-pale |
| White text on dark table header | `#1E1E1E` charcoal text on light header | Same — pale-on-pale convention |
| `Inter Medium` for table cells | `Inter Bold` | Reference uses Bold for all cells |
| `section.name = "Goals"` (or any non-empty string) | `section.name = ""` | Reference uses empty names; H2 inside is the title |
| Reparenting only one subgraph from a generated diagram | Reparent ALL page-level nodes (SECTIONs + SHAPEs + CONNECTORs) | Architecture diagrams are not single nodes |
| Trusting `c.connectorStart = c.connectorStart` to re-route every connector | After reparent, **delete and recreate every connector** from a captured spec | Long-bend connectors retain stale elbow waypoints; only `figma.createConnector()` produces a fresh route |
| Setting only `c.text.characters = label` on a fresh connector | Set `c.text.fontName`, `c.text.fontSize`, `c.text.characters`, AND `c.text.fills` | Defaults: fontSize=missing, fills=`[]` (empty array → transparent) → label invisible despite correct read-back |

## Step template

Every step below uses this shape. Read the step, then execute.

```
## Step N — <Name>  [Type: Research | Confirm | Write]
Inputs required: …
Ask if missing: …
Tools / refs loaded: …
Do: (3–6 action bullets)
Checkpoint: (Research → self-check; Confirm → AskUserQuestion; Write → screenshot + AskUserQuestion)
```

Three step types:
- **Research** — read-only; checkpoint = self-check list.
- **Confirm** — no board writes, user decision gate; checkpoint = `AskUserQuestion`.
- **Write** — creates/mutates FigJam; checkpoint = screenshot + `AskUserQuestion`.

---

## Step 1 — Gather context  [Research]

**Inputs required**
- PRD file path or pasted text.
- Optional: codebase entry points (file paths, service names, doc paths).

**Ask if missing**
- "Where's the PRD? (path or paste)."
- "Any codebase entry points I should ground in? (paths / services / docs / 'none')."

**Tools / refs loaded**
- `Read`, `Glob`, `Grep`.
- [`foundation/codebase-grounding.md`](references/foundation/codebase-grounding.md).

**Do**
1. Read the PRD. Extract: title, problem, goals, non-goals, owner, audience, success metrics, rollout hints, risks.
2. If entry points provided: follow `codebase-grounding.md` — bounded 20-file cap, depth-1 imports, walk up to `CLAUDE.md`/`ARCHITECTURE.md`/`OWNERS`.
3. Produce the **tech-context object**: `files_read`, `services`, `external_deps`, `key_modules`, `architecture_notes`, `ownership`, `expansion_truncated`.

**Self-check**
- Have: project title, problem statement, at least 1 concrete goal, owner (or "TBD"), services touched (or empty list with a reason).
- Enough signal to draft candidate section cards in Step 2. If not, loop back and ask.

---

## Step 2 — Propose candidate sections  [Confirm]

**Inputs required**
- Tech-context object from Step 1.

**Tools / refs loaded**
- [`section-catalog.md`](references/section-catalog.md).
- `AskUserQuestion`.

**Do**
1. For each section in the catalog, decide if there is *real content* for it from Step 1. Skip catalog entries that would be empty or padding.
2. For each qualifying candidate, produce a card:
   - **Title** (catalog name)
   - **1-line description** (what this section will contain, specific to the PRD)
   - **Why suggested** (which PRD facts or tech-context items justify it)
   - **Default block shape** (from the catalog)
3. Print all cards to chat.
4. Fire `AskUserQuestion` with a multiSelect question **per batch of ≤4 candidates** (max 4 questions per call, 4 options each → up to 16 candidates per call). Each option's label is the section title; description is the 1-line summary.

**Checkpoint (AskUserQuestion)**
- The multiSelect questions above. User ticks the sections they want. Store the selected set as `approved_sections`.
- If zero sections selected → stop with a clean exit message. No file is created.

---

## Step 3 — Per-section deep research  [Research]

**Inputs required**
- `approved_sections` from Step 2; tech-context from Step 1.

**Tools / refs loaded**
- `Read`, `Grep`, `Glob` (optional).

**Do**
1. For each section in `approved_sections`, look up its catalog entry. The catalog declares what the section needs (e.g. Dependencies needs cross-team services + external deps + blockers).
2. Compare what the section needs vs. what the tech-context has.
3. Produce a **gap list per section**: specific facts the user must supply, framed as answerable questions (no "figure it out yourself" gaps).

**Self-check**
- Every `approved_sections` entry has either `ready` (no gaps) or a specific non-empty gap list.
- Gaps are answerable — not vague prompts like "tell me more about X."

---

## Step 4 — Per-section content + block proposal  [Confirm]

**Inputs required**
- Gap lists from Step 3.

**Tools / refs loaded**
- `AskUserQuestion`.
- [`section-catalog.md`](references/section-catalog.md).
- Block reference(s) for the section's default shape (e.g. `blocks/table.md` for Dependencies).

**Do**, per section (one at a time, or small batch if trivial):
1. Fill the gap list — free-text prompt for prose; `AskUserQuestion` for bounded choices.
2. Propose:
   - **Content**: the concrete bullets / rows / stickies that will appear.
   - **Block shape**: the rendering block (body paragraph / table / multi-column / sticky column / …). Default from `section-catalog.md`; offer alternative shapes where sensible (e.g. "As a table, or as a multi-column layout?").
3. Show a short preview — section title + first line of body + block type summary.
4. Fire `AskUserQuestion`: "Use this content + shape? [Yes / Edit / Skip this section]."
5. Edit → accept free-text amendments, re-show, re-ask. Skip → mark the section as `skipped`; do not write it to the board.

**Checkpoint**
- Every section is `approved`, `edited+approved`, or `skipped`. No board writes yet.

---

## Step 5 — Create FigJam file  [Write]

**Inputs required**
- `approved_sections` (non-skipped); project title; `planKey` (Figma team plan).

**Tools / refs loaded**
- `create_new_file` MCP tool.
- `whoami` MCP tool (for `planKey` if not known).
- `use_figma` (once).
- `figma-use` (already in context from Step 5 onward).
- `figma-use-figjam` (re-loaded for the probe).
- `AskUserQuestion`.

**Do**
1. Resolve `planKey`: call `whoami`. If one plan → use it. If multiple → `AskUserQuestion` which team.
2. Call `create_new_file` with `{ planKey, fileName: "<project title>", editorType: "figjam" }`. Capture `file_key` + `file_url`.
3. Run the first-run probe (`use_figma`):

```js
const page = figma.currentPage;
return {
  rootName: figma.root.name,
  editorType: figma.editorType,
  pageCount: figma.root.children.length,
  firstPageName: figma.root.children[0].name,
  currentPageChildrenCount: page.children.length,
};
```

Expect `editorType === "figjam"` and empty page. If not, halt and report.

**Checkpoint (probe output + AskUserQuestion)**
- Print probe return + `file_url`.
- AskUserQuestion: "File created at `<file_url>` — proceed to skeleton? [Yes / Cancel]." Cancel = stop, leave empty file.

---

## Step 6 — Skeleton pass  [Write]

**Inputs required**
- `approved_sections` in taxonomy order; palette from `foundation/palette.md`; layout constants from `foundation/layout.md`.

**Tools / refs loaded**
- `use_figma` (one call).
- Re-load `figma-use-figjam/SKILL.md`.
- Re-load `blocks/section.md` and `blocks/metadata-strip.md`.
- [`foundation/palette.md`](references/foundation/palette.md), [`foundation/layout.md`](references/foundation/layout.md).

**Do**
1. Create metadata strip per `blocks/metadata-strip.md` (H1 + 4 body texts at board `(0, 0)`–`(0, ~100)`).
2. For each approved section, create a top-level SECTION per `blocks/section.md` — colored bg from ARCH_PALE, `section.name = ""` (no title-bar label — STRICT), `placeholder = true`, `resizeWithoutConstraints(LEFT_COL_W, DEFAULT_H)` for left-column sections or `resizeWithoutConstraints(RIGHT_COL_W_MIN, DEFAULT_H)` for right-column diagram sections.
3. Position each left-column section at `(0, SECTION_TOP_Y + cumulative_y)`. Right-column sections at `(832, SECTION_TOP_Y + cumulative_y_right)`.
4. Return all created node IDs: `{ createdNodeIds: { metadataStrip: {...}, sections: { <slug>: "<id>", ... } }, status: "skeleton-complete" }`. (The `slug` is internal, used to look up palette + drive Step 7 fills. It is never written to `section.name`.)
5. Take an inline screenshot at `await figma.currentPage.screenshot({ scale: 0.3 })`.

**Checkpoint (screenshot + AskUserQuestion)**
- AskUserQuestion: "Skeleton looks right? [Yes / Fix / Cancel]." Fix = targeted fix script; Cancel = stop.

---

## Step 7 — Fill pass (one call per section)  [Write]

**Inputs required**
- Approved content + block shape for each section; section ID from Step 6.

**Tools / refs loaded**
- `use_figma` (one call per section).
- Re-load `figma-use-figjam/SKILL.md`.
- Re-load whichever block refs this section uses:
  - `blocks/section.md` always.
  - `blocks/text-primitives.md` if body/H3/list.
  - `blocks/table.md` if table.
  - `blocks/multi-column-text.md` if multi-column.
  - `blocks/nested-section.md` if nested subsections.
  - `blocks/intro-callout.md` if highlighted intro.
  - `blocks/sticky-column.md` if stickies.

**Do**, per section:
1. `await figma.getNodeByIdAsync(sectionId)` — confirm type is SECTION.
2. Build content: H2 header first, then children per approved block shape. Append to section FIRST, then set x/y.
3. Two-pass measure for stickies per `blocks/sticky-column.md`.
4. `section.resizeWithoutConstraints(LEFT_COL_W, computed_height)`.
5. `section.placeholder = false`.
6. `await section.screenshot()` inline.
7. `return { mutatedNodeIds: [...], sectionHeight, screenshotIncluded: true }`.

**Checkpoint (screenshot + AskUserQuestion)**
- Per section: AskUserQuestion: "Section `<name>` done? [Yes / Edit this section / Skip rest]." Edit = targeted fix; Skip rest = exit fill loop (user will finalize manually).

**After all left-column fills**: run the re-stack pass (single `use_figma`) to fix cumulative Y based on actual resized heights:

```js
let y = SECTION_TOP_Y;
for (const id of leftColumnSectionIdsInOrder) {
  const sec = await figma.getNodeByIdAsync(id);
  sec.y = y;
  sec.x = 0;
  y += sec.height + 32;
}
return { mutatedNodeIds: leftColumnSectionIdsInOrder };
```

**Then run the outer-wrapper pass** (single `use_figma`) — wrap all left-column sections in an unlabeled white outer SECTION (see "Outer column wrapper" in the visual conventions block above). This is STRICT; do not skip.

---

## Step 8 — Diagrams  [Write]

**Inputs required**
- Diagram intents from Step 2/4 (Current State, Target State, 0–N Key Flows); tech-context for Mermaid composition.

**Tools / refs loaded**
- Re-load `generate-diagram/SKILL.md` before each `generate_diagram` call.
- Re-load `figma-use-figjam/SKILL.md` + `blocks/diagram-section.md` before each reparent `use_figma` call.
- `generate_diagram` MCP tool, `use_figma`.

**Do**, per diagram:
1. `use_figma`: create the right-column section (white fill, H2 header, `placeholder = true`) per `blocks/diagram-section.md`.
2. `generate_diagram`: compose Mermaid from tech-context; architecture diagrams use `useArchitectureLayoutCode: "FIGMA_DIAGRAM_2026"`.
3. `use_figma`: locate the generated diagram node, reparent into the section (`section.appendChild(diag)`), position below H2, resize section to fit. `placeholder = false`.
4. `await section.screenshot()`.

**Failure handling**: if `generate_diagram` fails, leave a text placeholder in the section reading `"Diagram generation failed: <message>. Regenerate manually."` Continue to the next diagram.

**Checkpoint (screenshot + AskUserQuestion)**
- Per diagram: AskUserQuestion: "Diagram `<name>` looks right? [Yes / Regenerate / Skip]."

---

## Step 9 — Final review + report  [Write, then Read]

**Inputs required**
- `file_url` from Step 5.

**Tools / refs loaded**
- `use_figma` (one call for full-page screenshot).

**Do**
1. `await figma.currentPage.screenshot({ scale: 0.25 })` — full board.
2. Inspect: two-column structure, no overlaps, no sections left with `placeholder = true`, metadata strip visible.
3. Fix any issues with a targeted `use_figma` script. Do **not** regenerate from scratch.
4. Post to chat:

```
✅ Project plan written to FigJam.
File: <file_url>
Sections: <N text + N diagram>
Files referenced during grounding: <count>
```

**Checkpoint (screenshot + AskUserQuestion)**
- AskUserQuestion: "Done, or tweak? [Done / Tweak]." Tweak = targeted fix script on user's request, not regeneration.

---

## Operational rules

- ≤10 logical operations per `use_figma` call.
- Always return `createdNodeIds` / `mutatedNodeIds` from every write script.
- Use `hex/255` notation for all palette colors (see `foundation/palette.md`).
- **STRICT: section backgrounds use the `ARCH_PALE` palette, NOT the FigJam standard SECTION palette.** ARCH_PALE colors (`#EBFFEE`, `#F8F5FF`, `#F5FBFF`, `#FFF7F0`, etc.) visually pair with the architecture-diagram subgraph wrappers that `generate_diagram` produces. The FigJam SECTION palette (`#CDF4D3`, `#C2E5FF`, `#DCCCFF`, `#FFE0C2`) is too saturated and causes visible color clash next to diagrams. See `foundation/palette.md`.
- **STRICT: `section.name = ""` on every project-plan section (left-column, right-column, and nested children).** The user-facing title is rendered as the H2 text node *inside* the section, NOT via FigJam's section title-bar label. The reference board uses empty section names; setting a non-empty `name` produces a duplicate label that visually clutters the board.
- Read, edit, or cancel at every Confirm/Write checkpoint — never write past an unanswered AskUserQuestion.
- If a `use_figma` script errors: atomic — no changes made. Read the error, fix, retry.

## Trigger phrases

"/generate-project-plan", "interactive project plan", "project plan", "make a FigJam project plan", "PRD to FigJam".
