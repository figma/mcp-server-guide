# use_figma — Figma Plugin API Skill for Slides

This skill contains Slides-specific context for the `use_figma` MCP tool. The figma-use (load `readPowerSteering("figma", "figma-use.md")`) skill provides foundational context for plugin API execution via MCP as well as the full Figma plugin API for more advanced use-cases that are not described here.

**Always include `figma-use-slides` in the comma-separated `skillNames` parameter when calling `use_figma` for Slides operations. If this skill was loaded via an MCP resource, you MUST prefix the name with `resource:` (e.g. `resource:figma-use-slides`).** This is a logging parameter used to track skill usage — it does not affect execution.

## Critical Rules (Slides-specific)

1. **Newly created Slides files have a default light theme.** When a Slides file is created via `create_new_file`, a default light theme is automatically initialized. This theme is structural scaffolding — you should overwrite the theme's color variables and text styles with your own design direction for the deck you're building. Do not rely on or be influenced by the default light theme tokens.
2. **MUST `appendChild` BEFORE setting `x`/`y` — for every node, at every level of nesting.** Newly created nodes are silently auto-parented to a slide context at absolute `(240, 240)` (the slide grid's `GRID_PADDING`). Writing `x`/`y` before `appendChild` causes the value to be stored against that hidden origin; the node then lands at `(intended − 240, intended − 240)` once you attach the real parent. The bug is **intermittent** — some frames in the same script escape it, so a working test is not proof you're safe. **Signature to recognize:** if any node ends up `(−240, −240)` from where you set it, your code set `x`/`y` before the final `appendChild`. Do NOT try to compensate by adding 240 back — that produces worse output on retry. Fix the order instead. See [Slide Gotchas & Common Mistakes](#position-after-appendchild-critical) for the helper pattern that makes the order impossible to get wrong.
3. **SLIDE_GRID and SLIDE_ROW are opaque nodes** — do not access `.fills`, `.effects`, or layout properties on them. Only `SLIDE` nodes (type `'SLIDE'`) extend `BaseFrameMixin`. **Exception:** `SLIDE_ROW.name` IS settable — that's how plugins rename slide sections (e.g. `slideRow.name = "Intro"`). See [Slide Lifecycle](#reference--slide-lifecycle).
4. **`get_metadata` does NOT work on Slides files.** Use `use_figma` read-only scripts for validation. Return created node positions in `closePlugin()` output and verify no overlapping bounding boxes.
5. **Do NOT call `figma.createPage()` in Slides.** It throws `TypeError: figma.createPage no such property 'createPage' on the figma global object` — `createPage()` is a Design-file API only (`figma.com/design/...`); the Slides URL is `figma.com/slides/...`. Use the slide grid (`SLIDE_GRID` / `SLIDE_ROW` / `SLIDE`) to organize deck structure instead — see [Slide Lifecycle](#reference--slide-lifecycle) and [Slide Grid](#reference--slide-grid).
6. **Never delete existing slides to rebuild them.** When asked to improve, redesign, or restyle a deck, modify the existing slides in place. Only delete slides when the user explicitly asks to "start over" or "redo from scratch."

## Design Thinking

Not every task needs the same depth of design thinking. Before doing anything, identify which gear you're in:

- **Content/property edits** — changing text, swapping a color, updating a number, fixing alignment, resizing an element. Skip design thinking. Just make the change and match what's already there.
- **Structural additions** — adding slides, reworking a section's layout, changing the deck's color palette, introducing a new visual element. This includes requests to "improve," "redesign," or "restyle" a deck — those are in-place edits to what's already there, not a new deck. Design thinking applies, but in *inherit* mode: the existing deck is your design language. Inspect it, match its palette, type, spatial habits, and motifs. Extend the deck's existing character rather than reinventing it.
- **New deck creation** — building a deck from scratch or from a blank file. Full design thinking applies as described below.

For structural additions to existing decks: run the inspection scripts (below) and take screenshots before making changes. The answers to "what color story?" and "what type treatment?" are already in the file — your job is to read them and stay consistent. The design principles in [Slide Design Principles](#reference--slide-design-principles) describe what you're *matching*, not what you're *choosing*.

### New deck design process

Before writing any Plugin API code for a new deck, decide what it should *feel* like. Figma users have high visual expectations — a deck that looks like it came out of a generic template generator will stand out for the wrong reasons.

1. **Read the brief.** What is the deck communicating, and to whom? An investor pitch, a team retrospective, a product launch, and a technical deep-dive all demand different visual treatments. The design should be inseparable from the content.
2. **Check for a design language.** Before inventing anything, look at what the user already gave you. Brand guidelines in the prompt — color palettes, typography specs, logo rules, tone descriptors — are design decisions that have already been made. A link to a reference Figma file is a design language you should study, not glance at. The more specific the user's inputs, the less you should invent on your own. When the user provides a reference, your job shifts from *designer* to *interpreter*: extract the design language and apply it faithfully to new content.
3. **Take a position — on what's left.** If the user supplied a full brand system, your creative latitude is in layout, pacing, and composition — not in color or type. If they gave you a single reference slide for inspiration, you have more room but should still echo its character. If they gave you nothing, then you own every decision — choose a color story, a type treatment, a way of organizing space, and follow through on it across every slide. A deck with a clear perspective (even a quiet one) always reads better than one that plays it safe on every decision. The scope of "take a position" scales inversely with what the user provided.
4. **Give it a signature.** Every good deck has at least one element you'd recognize if you saw it out of context: a distinctive palette, an unexpected layout cadence, a recurring shape language. When working from brand guidelines, the signature should *come from* that brand language — amplify something that's already there rather than adding something foreign. When designing from scratch, decide what the signature is before you start building.

### Reading a reference file

When the user provides a link to a Figma file as a reference, study it before designing anything. What you extract depends on what the file is:

- **A Slides file**: `get_metadata` does not work on Slides files. Use `get_screenshot` to capture individual slides for visual reference, and `use_figma` with the reference file's `fileKey` to run read-only scripts that extract theme variables, color palettes, font choices, and layout patterns.
- **A Design file**: `get_design_context` gives you comprehensive design data — colors, typography, layout structure. `get_screenshot` gives you visual reference. Use both.

What to look for in a reference file: the color palette (which hue leads, what the accent is, how dark/light backgrounds are used), the type choices (families, weights, how hierarchy is handled), the spatial habits (where content anchors, how much whitespace, whether things bleed off edges), and any recurring motifs (shapes, line treatments, decorative elements). These are the decisions you inherit — everything else is yours.

How closely to follow the reference depends on what the user asked for. "Make it look like this" means replicate the design language with new content. "Use this for inspiration" means echo the character but make it your own. "Here's our brand deck" means extract the brand system and apply it consistently. When in doubt, stay closer to the reference — it's easier for a user to ask you to diverge than to ask you to undo invented choices that conflict with their brand.

Load [Slide Design Principles](#reference--slide-design-principles) for specific guidance on color, type, layout patterns, composition, and what to avoid. When you have a reference file or brand guidelines, treat slide-design.md's principles as defaults for the decisions the user *didn't* make — not as overrides for the ones they did.

## Deck-Building Workflow

When building a new deck of 5 or more slides, use this two-phase workflow. It replaces the general incremental workflow from figma-use (load `readPowerSteering("figma", "figma-use.md")`) Section 6 for deck-building specifically — the principles still apply, but the cadence changes.

### Phase 1 — Design & Plan

Complete the design thinking process above (read the brief, check for a design language, take a position, give it a signature), then **before writing any `use_figma` code**, produce a slide plan covering the entire deck:

1. **Slide-by-slide plan.** For every slide: its purpose/content, layout approach described spatially (e.g. "title anchored upper-left, spec card filling the right third, decorative circle bleeding off top-right edge"), and background treatment (dark/light/gradient). Do NOT compute pixel coordinates during planning — describe layouts in spatial terms. Coordinate math happens during code generation.
2. **Shared constants.** Declare the font families and styles you'll use, the color palette as named roles (primary, accent, bgDark, surface, textPrimary, textMuted, etc.), and the recurring motif or signature element.
3. **Layout variety check.** Read through the slide plans in sequence. If the layout descriptions feel repetitive — "two-column, two-column, grid, two-column" — rearrange before building. This is the cheapest moment to diversify. See [Slide Design Principles](#reference--slide-design-principles) for anti-patterns.
4. **Code preamble.** Write out the reusable preamble you'll paste at the top of every build script: a `const C = { ... }` color palette object, a `Promise.all([...])` font-loading block, and the `addFrame`/`addText`/`addRect` helpers from [Slide Gotchas & Common Mistakes](#position-after-appendchild-critical).

### Phase 2 — Build

Execute the plan in large batches. The goal is to minimize the number of think-then-build cycles — not to minimize elements per script.

- **3–5 slides per `use_figma` call.** Structurally similar slides (e.g. a series of product feature slides) can go in the same batch. Each slide is an isolated subtree — cross-slide dependencies don't exist, so large batches are safe.
- **Do NOT re-plan between batches.** The design was decided in Phase 1. If a batch succeeds and passes validation, move to the next batch immediately. Only re-plan if a batch fails or produces a visual problem that requires changing the approach.
- **Paste the code preamble** (colors, fonts, helpers) at the top of every build script. Copy it from Phase 1 verbatim — do not re-derive it.
- **Validate every batch** with the deterministic batch validation script from [Slide Gotchas & Common Mistakes](#batch-validation-script). This checks for overlapping elements, text clipping, and out-of-bounds nodes in ~3 seconds. If the check passes, proceed without a screenshot. If it fails, screenshot the affected slides and fix before continuing.
- **Screenshot at checkpoints only** — after the first batch (validates the visual system: colors, typography, design direction), and after the final batch (overall quality). Take a screenshot of 1–2 representative slides per checkpoint using inline `await slide.screenshot()`, not separate `get_screenshot` calls.
- **Return all created node IDs** from every build script, as always.

## Sections

A section is a horizontal row in the slide grid — every row is a section. Names show up in the editor (next to the row) and in Presenter View (so speakers can jump between groups). They're an organizational aid for whoever is editing the deck — the user owns where the breaks fall, not you.

### When asked to organize a deck

"Organize this deck" is ambiguous — grouping, reordering, deduping, or restructuring. Read the deck before reaching for `AskUserQuestion`.

**Default: propose, don't ask.** Most decks have cues — title bookend, numbered use cases, repeated *Before / After* pairs, transition slides ("Then X enters the chat"), a *Thank you*. When cues exist, pick a sectioning and surface it in one confirmation message. Bounded calls inside the proposal (one *Use Cases* row vs. three, where a transition slide lives) are reversible — pick one and move on.

**Fallback: ask when cues are absent.** If slides are in arbitrary order or there's no spine, ask which ranges go together and what to call them. Don't slice by thirds as a substitute for reading.

### Naming + scoping

Names should be short (1–3 words), concrete (*Demo* beats *Show & tell*), and consistent within a deck. Two to five sections is typical; more only for long or repeating decks. Names aren't slide titles — they help find a group, not describe its content.

### Renaming a section

`getSlideGrid()` returns `SlideNode[][]` — the inner arrays are plain JS arrays of slides, NOT `SLIDE_ROW` nodes. Setting `.name` on those arrays silently no-ops. To rename a section, traverse the node tree and set `.name` on the actual `SLIDE_ROW`:

```js
const slideGrid = figma.currentPage.children.find(c => c.type === "SLIDE_GRID");
slideGrid.children[0].name = "Intro";
```

## Speaker Notes

Speaker notes are the presenter's private companion to each slide. They appear in Presenter View (visible only to the speaker, not the audience) and serve as a script, cue sheet, or talking-points reference during a live presentation.

### When to write speaker notes

- **When asked**: If the user asks for speaker notes, presenter notes, talking points, or a script for a deck, write notes for every slide that has substantive content (skip section dividers or purely decorative slides unless there's something to say).
- **Presenter-ready decks**: If the user explicitly asks for a deck that is ready to present live, speaker notes are useful. Add them when they help the presenter understand pacing, transitions, or context that is not visible on the slide.
- **Sparse or visual slides**: If a slide is built around a chart, image, metaphor, or provocative question, notes can help explain what the presenter should say. Use screenshots or `node.screenshot()` for image-heavy, chart-heavy, or visually sparse slides when visual context matters, but don't screenshot every slide by default — images spend context budget.
- **Don't add notes unprompted**: For normal slide edits, layout work, or updates to existing decks, do not populate speaker notes unless the user asks. Adding notes changes the presentation flow and can surprise the deck owner.

### What good speaker notes look like

Speaker notes are for the *presenter*, not the audience. They should feel like a trusted colleague leaning over and whispering "here's what to say." Good notes:

- **Complement the slide, not repeat it.** If the slide says "Revenue grew 40%", the notes shouldn't say "Revenue grew 40%." They should say *why* it grew, what the audience should take away, or what question this usually prompts.
- **Are concise and scannable.** A presenter glancing down mid-sentence needs to find their place instantly. Use short bullet points, not dense paragraphs. Each point should be one idea.
- **Include transitions.** The best notes tell the presenter how to *move* between slides: "After the applause dies down..." or "This builds on the previous point — call back to the 40% figure."
- **Carry context the slide can't.** Data sources ("Source: Q4 FY25 internal metrics, not yet public"), caveats ("Skip this slide if the CFO is in the room"), timing cues ("This is the halfway point — you should be at ~10 minutes"), and anticipated questions ("They'll ask about margins — see appendix slide 14").
- **Match the presentation's register.** Notes for an investor pitch are precise and rehearsed. Notes for a team retro are casual and flexible. Notes for a keynote might include stage directions. Match the tone to the context.

### What to avoid in speaker notes

- **Full scripts**: Wall-of-text notes encourage reading verbatim, which makes for a terrible presentation. If the user explicitly asks for a script, write one, but default to bullet points.
- **Formatting for the audience**: Notes aren't visible to the audience. Don't optimize them for readability by non-presenters.
- **Redundancy with the slide**: If the slide is self-explanatory ("Thank You" with contact info), notes aren't needed. It's fine to leave a slide's notes empty.

### Formatting

`slide.speakerNotes` accepts a markdown string. Prefer bullet lists as the primary structure; bold is useful for emphasis on key phrases the presenter shouldn't skip. See [Slide-Specific Properties](#supported-formatting) for the full list of supported (lists, bold, italic, strikethrough) and unsupported (headings, code blocks, inline code, links) markdown.

## Inspecting Slides Files

There is no dedicated read tool for Slides files yet. Use `use_figma` with read-only scripts for inspection, and `get_screenshot` / `await node.screenshot()` for visual context.

- **Inspect before creating.** Before creating anything, run a read-only `use_figma` to discover what already exists — slides, text, components, naming conventions. The figma-use (load `readPowerSteering("figma", "figma-use.md")`) Section 6 "Inspect first" pattern applies here.
- **`get_metadata` does NOT work on Slides files** — it only supports `figma` (Design) editor type.
- **`console.log()` output is NOT returned** — only the `return` value comes back. Always `return` the data you need.
- **Use `get_screenshot` for visual context** — pass a valid `nodeId` to get a screenshot. You can also use `await node.screenshot()` inline within `use_figma` scripts.

### Quick inspection scripts

**List all slides in the deck:**
```js
const grid = figma.getSlideGrid();
return grid.map((row, rowIdx) =>
  row.map((slide, colIdx) => ({
    id: slide.id,
    name: slide.name,
    row: rowIdx,
    col: colIdx,
    isSkipped: slide.isSkippedSlide,
    speakerNotes: slide.speakerNotes,
  }))
);
```

**Get text content from a specific slide:**
```js
const slide = figma.getNodeById("TARGET_SLIDE_ID");
// findAllWithCriteria uses an indexed type lookup — much faster than
// findAll(n => n.type === 'TEXT') on slides with many shapes/images.
const textNodes = slide.findAllWithCriteria({ types: ["TEXT"] });
const fontsToLoad = new Set();
for (const t of textNodes) {
  if (t.fontName !== figma.mixed) {
    fontsToLoad.add(JSON.stringify(t.fontName));
  } else {
    const segments = t.getStyledTextSegments(["fontName"]);
    for (const seg of segments) fontsToLoad.add(JSON.stringify(seg.fontName));
  }
}
for (const f of fontsToLoad) {
  await figma.loadFontAsync(JSON.parse(f));
}
return textNodes.map(t => ({
  id: t.id,
  name: t.name,
  characters: t.characters,
  x: t.x,
  y: t.y,
  width: t.width,
  height: t.height,
}));
```

## Reference Docs

Load only the references your task needs:

- [slide-gotchas](#reference--slide-gotchas--common-mistakes) — Pitfalls specific to Slides (coordinate offsets, opaque node types, validation workarounds)
- [slide-lifecycle](#reference--slide-lifecycle) — Create, clone, delete, and reorder slides and slide rows
- [slide-grid](#reference--slide-grid) — Work with the slide grid layout (`getSlideGrid`, `setSlideGrid`)
- [slide-content](#reference--slide-content) — Build content within slides (text, shapes, auto-layout — SlideNode extends BaseFrameMixin)
- [slide-properties](#reference--slide-specific-properties) — Slide-specific properties (`speakerNotes`, `isSkippedSlide`, `focusedSlide`, `focusedNode`, `slideThemeId`, `InteractiveSlideElementNode`)
- [slide-design](#reference--slide-design-principles) — Design principles for visually interesting, varied decks (color strategy, typography, layout variety, spatial composition, anti-patterns)

---

## Reference — Slide Gotchas & Common Mistakes

> Part of the [figma-use-slides skill](#use_figma--figma-plugin-api-skill-for-slides). Pitfalls specific to working in Slides files.

### Contents

- Position after appendChild (critical)
- Canonical text-edit recipe (font load → await → mutate → return IDs)
- Sequential awaits — batch independent async calls with `Promise.all`
- Prefer indexed lookups over `findAll`/`findOne` full-tree scans
- Scope traversal to the smallest known ancestor (a slide, not the page)
- SLIDE_GRID and SLIDE_ROW are opaque nodes
- Validation without get_metadata
- Building multi-element slides
- Code preamble for deck-building scripts


### Canonical text-edit recipe (font load → await → mutate → return IDs)

The same canonical recipe used in Design files applies inside slides — see figma-use → gotchas.md → Canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`) for the full WRONG/CORRECT pair. Two slide-specific reminders:

1. **Inter preload doesn't cover deck-theme fonts.** Decks frequently switch the theme font to families like `Roboto Mono`, `Merriweather`, or a brand font — those still need an explicit `loadFontAsync` for every (family, style) you mutate.
2. **When restyling existing slide text, load the node's *current* font, not a hardcoded default.** Slide theme tokens push fonts onto nodes that may differ from what you'd guess. Use `getStyledTextSegments(['fontName'])` and `loadFontAsync` each segment's font before any mutation.

```js
// Restyle existing slide text without assuming the font
await Promise.all(
  textNode.getStyledTextSegments(['fontName'])
    .map(s => figma.loadFontAsync(s.fontName))
)
textNode.characters = "Updated"
return { mutatedNodeIds: [textNode.id] }
```


### Prefer indexed lookups over `findAll` / `findOne` full-tree scans

Same rule as in design files (see figma-use → gotchas.md → Prefer indexed lookups (load `readPowerSteering("figma", "figma-use.md")`)). On slide trees, the most common offenders are `slide.findAll(n => n.type === 'TEXT')` (use `slide.findAllWithCriteria({ types: ['TEXT'] })`) and `slide.findAll(n => n.type === 'INTERACTIVE_SLIDE_ELEMENT')` (same fix). If you have a slide or element ID, use `figma.getNodeByIdAsync(id)` — never re-scan the tree.


### Scope traversal to the smallest known ancestor

Slides specifically: **search inside the specific slide**, not the whole page. `slide.findAllWithCriteria(...)` walks one slide; `figma.currentPage.findAllWithCriteria(...)` walks every slide in the deck. When you have the target slide's ID (passed by the caller or returned from a prior call), always start the traversal there.

```js
// AVOID — scans every slide in the deck
const texts = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })

// PREFER — one slide only
const slide = await figma.getNodeByIdAsync(SLIDE_ID)
const texts = slide.findAllWithCriteria({ types: ['TEXT'] })
```

See figma-use → gotchas.md → Scope traversal to the smallest known ancestor (load `readPowerSteering("figma", "figma-use.md")`).


### Sequential awaits — batch independent async calls with `Promise.all`

Same rule as in design files (see figma-use → gotchas.md → Sequential awaits (load `readPowerSteering("figma", "figma-use.md")`)). When building decks, the typical offenders are `loadFontAsync` for theme/brand fonts, `getNodeByIdAsync` for cached slide IDs, and `import*ByKeyAsync` for library variables and styles — all independent per call and all batchable.

```js
// WRONG — sequential round-trips per slide
for (const id of slideIds) {
  const slide = await figma.getNodeByIdAsync(id)
  // ... mutate
}

// CORRECT — fetch all slides in one batch, then mutate sequentially
const slides = await Promise.all(slideIds.map(id => figma.getNodeByIdAsync(id)))
for (const slide of slides) {
  // ... mutate
}
```

`setCurrentPageAsync` is the exception — page-context switches must stay sequential.


### Position after appendChild (critical)

Setting `x`/`y` on a node **before** appending it to its real parent causes a `(−240, −240)` coordinate shift. This applies at **every level of nesting**, not just the slide root — a card you build at "page level" before attaching to a slide hits the bug, and a text you create then position before appending to that card hits it too.

**Why this happens:** Newly created nodes (`figma.createFrame()`, `figma.createRectangle()`, `figma.createText()`) in a Slides file are silently auto-parented to a slide context whose origin sits at absolute `(240, 240)` — the slide grid's `GRID_PADDING`. When you write `node.x = 200` on that "orphan", the underlying engine interprets `200` as the desired absolute x, then stores `relative.x = 200 − 240 = −40`. When you later `appendChild` to the real slide (or real card), the relative coordinate is preserved, so the node lands at `−40` instead of `200`. The bug is **intermittent** — different frames in the same script can escape it depending on engine state — so a passing visual check on one frame doesn't mean the next one is safe.

```js
// WRONG — building a subtree at "page level", attaching last.
// Both the outer card AND the inner text hit the (-240, -240) trap.
const card = figma.createFrame();
card.resize(400, 200);
card.x = 120; card.y = 260;          // card stores local = (-120, 20)
const text = figma.createText();
text.x = 32; text.y = 32;            // text on orphan card — same trap
card.appendChild(text);
slide.appendChild(card);
// Visual result: card bleeds off the left edge of the slide;
// text inside it is off-position relative to the card.

// CORRECT — appendChild walks down from the slide.
// Configure size/fills/x/y AFTER each appendChild, at every level.
const card = figma.createFrame();
slide.appendChild(card);             // 1. parent first
card.resize(400, 200);               // 2. then everything else
card.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
card.cornerRadius = 16;
card.x = 120; card.y = 260;

const text = figma.createText();
card.appendChild(text);              // same rule one level down
await figma.loadFontAsync({ family: "Inter", style: "Bold" });
text.fontName = { family: "Inter", style: "Bold" };
text.characters = "26.6%";
text.x = 32; text.y = 32;
```

**Required helper pattern.** Wrap the append-first order so the agent can't write it wrong. Use these (or local equivalents) for every node added to a slide or a frame on a slide:

```js
function addFrame(parent, x, y, w, h, fill, radius) {
  const f = figma.createFrame();
  parent.appendChild(f);                                    // 1. parent first
  f.resize(w, h);
  f.fills = [{ type: "SOLID", color: fill }];
  if (radius !== undefined) f.cornerRadius = radius;
  f.x = x; f.y = y;                                         // 2. position last
  return f;
}

function addText(parent, family, style, size, color, chars, x, y, w, h) {
  const t = figma.createText();
  parent.appendChild(t);
  t.fontName = { family, style };
  t.fontSize = size;
  t.characters = chars;
  t.fills = [{ type: "SOLID", color }];
  if (w !== undefined) t.resize(w, h);
  t.x = x; t.y = y;
  return t;
}

function addRect(parent, x, y, w, h, fill) {
  const r = figma.createRectangle();
  parent.appendChild(r);
  r.resize(w, h);
  r.fills = [{ type: "SOLID", color: fill }];
  r.x = x; r.y = y;
  return r;
}
```

With these helpers, building a card-with-text on a slide is one walk-down:

```js
const card = addFrame(slide, 120, 260, 400, 200, { r: 1, g: 1, b: 1 }, 16);
addText(card, "Inter", "Bold", 96, { r: 0.42, g: 0.42, b: 0.45 }, "26.6%", 32, 56, 336, 104);
```


### Diagnosing offset bugs

If you observe nodes off by exactly `(−240, −240)` from where you set them, this is the auto-parent bug above. **Do not** try to compensate by adding `240` back to `x`/`y` — the session referenced in the original incident did this and the next iteration was worse, not better, because the compensation hides the structural issue and re-triggers it under slightly different state.

Fix the order instead:

1. Read back the node positions after your script runs. For any node whose `node.x` differs from the value you assigned by `−240`, that node had `x`/`y` set before its final `appendChild`.
2. Rewrite the offending block to use the helper pattern above (append-then-configure, at every nesting level).
3. Verify by re-reading `node.x` — it must match the value you wrote.

Quick sanity script you can drop in at the end of any slide-build:

```js
const expectations = [
  { node: card,  intended: { x: 120, y: 260 } },
  { node: text,  intended: { x: 32,  y: 56  } },
];
const drift = expectations
  .map(e => ({ name: e.node.name, dx: e.node.x - e.intended.x, dy: e.node.y - e.intended.y }))
  .filter(r => r.dx !== 0 || r.dy !== 0);
return { drift }; // any non-empty result means the append-first rule was broken somewhere
```


### SLIDE_GRID and SLIDE_ROW are opaque nodes

Only `SLIDE` nodes extend `BaseFrameMixin`. The parent containers do not:

| Node type | Mixin | Has fills? | Has children? | Has layout props? |
|---|---|---|---|---|
| `SLIDE_GRID` | OpaqueNodeMixin | No | Yes (rows) | No |
| `SLIDE_ROW` | OpaqueNodeMixin + ChildrenMixin | No | Yes (slides) | No |
| `SLIDE` | BaseFrameMixin | Yes | Yes (content) | Yes |

```js
// WRONG — throws "no such property 'fills' on SLIDE_GRID node"
const grid = figma.currentPage.children[0];
const bg = grid.fills;

// WRONG — throws on SLIDE_ROW
const row = grid.children[0];
row.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];

// CORRECT — access fills on the SLIDE node itself
const slide = row.children[0];  // type: 'SLIDE'
slide.fills = [{ type: "SOLID", color: { r: 0.06, g: 0.09, b: 0.16 } }];
```


### Validation without get_metadata

`get_metadata` does not work on Slides files. Use `get_screenshot` for visual validation and `use_figma` read-only scripts for structural validation.

**Post-creation validation pattern:**
```js
const slide = figma.getNodeById("SLIDE_ID");
const children = slide.children.map(c => ({
  name: c.name,
  type: c.type,
  x: Math.round(c.x),
  y: Math.round(c.y),
  w: Math.round(c.width),
  h: Math.round(c.height),
  text: c.type === "TEXT" ? c.characters.substring(0, 50) : undefined,
}));

// Check for overlapping bounding boxes
const overlaps = [];
for (let i = 0; i < children.length; i++) {
  for (let j = i + 1; j < children.length; j++) {
    const a = children[i], b = children[j];
    if (a.x < b.x + b.w && a.x + a.w > b.x &&
        a.y < b.y + b.h && a.y + a.h > b.y) {
      overlaps.push([a.name, b.name]);
    }
  }
}

return { children, overlaps, hasOverlaps: overlaps.length > 0 };
```

Run this after creating slide content to catch layout issues before they compound.


#### Batch validation script

When building a deck, run this validation after every batch of slides. It checks the three most common layout failures — overlapping siblings, text clipping past containers, and elements beyond slide bounds — in ~3 seconds via a read-only `use_figma` call. Only take a screenshot if issues are found.

```js
// Pass the slide IDs built in the current batch
const slideIds = ["SLIDE_ID_1", "SLIDE_ID_2", "SLIDE_ID_3"];
const OVERLAP_PX = 4;
const OVERFLOW_PX = 1;
const SLIDE_W = 1920, SLIDE_H = 1080;

const issues = [];
const slides = await Promise.all(slideIds.map(id => figma.getNodeByIdAsync(id)));

for (const slide of slides) {
  const children = slide.children.map(c => ({
    id: c.id, name: c.name, type: c.type,
    x: c.x, y: c.y, w: c.width, h: c.height,
  }));

  // 1. Sibling overlaps (≥ OVERLAP_PX axis-aligned intersection)
  for (let i = 0; i < children.length; i++) {
    for (let j = i + 1; j < children.length; j++) {
      const a = children[i], b = children[j];
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox >= OVERLAP_PX && oy >= OVERLAP_PX)
        issues.push({ slide: slide.id, type: "overlap", nodes: [a.name, b.name] });
    }
  }

  // 2. Text clipping (text bbox extends past parent frame)
  for (const c of children) {
    if (c.type !== "FRAME") continue;
    const texts = c.findAllWithCriteria({ types: ["TEXT"] });
    for (const t of texts) {
      const abs = t.absoluteBoundingBox;
      const pAbs = c.absoluteBoundingBox;
      if (!abs || !pAbs) continue;
      if (abs.x + abs.width > pAbs.x + pAbs.width + OVERFLOW_PX ||
          abs.y + abs.height > pAbs.y + pAbs.height + OVERFLOW_PX)
        issues.push({ slide: slide.id, type: "textClip", node: t.name, parent: c.name });
    }
  }

  // 3. Beyond slide bounds
  for (const c of children) {
    if (c.x + c.w < -OVERLAP_PX || c.y + c.h < -OVERLAP_PX ||
        c.x > SLIDE_W + OVERLAP_PX || c.y > SLIDE_H + OVERLAP_PX)
      issues.push({ slide: slide.id, type: "outOfBounds", node: c.name });
  }
}

return { clean: issues.length === 0, issues };
```

**Verification cadence for deck building:**
- After every batch: run the validation script above. If `clean` is `true`, proceed to the next batch without re-deliberation or a screenshot.
- If `clean` is `false`: take a screenshot of the affected slide(s) and fix the issues before continuing.
- Screenshot at **checkpoints** regardless: after the first batch (validates the visual system — colors, typography, design direction) and after the final batch (overall quality check).
- Do NOT re-plan after successful verification. Proceed to the next batch.


### Building multi-element slides

When building a **single complex slide** (data-heavy chart, intricate one-off layout), work incrementally within that slide — create the background and structure first, then add content, then decorative elements, validating between steps.

When building a **deck** (multiple slides), build complete slides in each `use_figma` call. The helpers (`addFrame`, `addText`, `addRect`) enforce the appendChild-before-position rule, so building a complete slide in one pass is safe. Validate using the [batch validation script](#batch-validation-script) above, not per-element screenshots. See [Deck-Building Workflow](#use_figma--figma-plugin-api-skill-for-slides) for the full process.


### Code preamble for deck-building scripts

When building a deck, start every `use_figma` script with the same preamble — colors, fonts, and helpers. Define these once in your Phase 1 plan, then copy verbatim into every build script rather than re-deriving them.

```js
// --- Preamble (copy from Phase 1 plan) ---
// Color palette — fill in your own values
const C = {
  bg:      { r: 0.10, g: 0.10, b: 0.12 },
  surface: { r: 0.15, g: 0.15, b: 0.19 },
  text:    { r: 1,    g: 1,    b: 1    },
  muted:   { r: 0.60, g: 0.62, b: 0.68 },
  accent:  { r: 0.38, g: 0.71, b: 0.77 },
};

// Font loading — batch all styles in one await
await Promise.all([
  figma.loadFontAsync({ family: "Inter", style: "Bold" }),
  figma.loadFontAsync({ family: "Inter", style: "Semi Bold" }),
  figma.loadFontAsync({ family: "Inter", style: "Regular" }),
  figma.loadFontAsync({ family: "Inter", style: "Light" }),
]);

// Helpers — enforce appendChild-before-position
function addFrame(parent, x, y, w, h, fill, radius) {
  const f = figma.createFrame();
  parent.appendChild(f);
  f.resize(w, h);
  f.fills = [{ type: "SOLID", color: fill }];
  if (radius !== undefined) f.cornerRadius = radius;
  f.x = x; f.y = y;
  return f;
}
function addText(parent, family, style, size, color, chars, x, y, w, h) {
  const t = figma.createText();
  parent.appendChild(t);
  t.fontName = { family, style };
  t.fontSize = size;
  t.characters = chars;
  t.fills = [{ type: "SOLID", color }];
  if (w !== undefined) t.resize(w, h);
  t.x = x; t.y = y;
  return t;
}
function addRect(parent, x, y, w, h, fill) {
  const r = figma.createRectangle();
  parent.appendChild(r);
  r.resize(w, h);
  r.fills = [{ type: "SOLID", color: fill }];
  r.x = x; r.y = y;
  return r;
}
// --- End preamble ---
```

The palette values and font families above are placeholders — replace them with the actual design constants from your Phase 1 plan. The helpers are identical to the ones in the [Position after appendChild](#position-after-appendchild-critical) section and should be included in every deck-building script.

---

## Reference — Slide Lifecycle

### Creating slides

```js
// Append a slide to the end of the deck (last child of last row)
const slide = figma.createSlide();

// Create a slide at a specific position in the grid (row 0, column 2)
const slide = figma.createSlide(0, 2);
```

`createSlide` returns a `SlideNode` (extends `BaseFrameMixin`). The slide is automatically parented into the slide grid.

### Creating slide rows

```js
// Append a new row to the end of the slide grid
const row = figma.createSlideRow();

// Insert a row at a specific position (index 0 = first row)
const row = figma.createSlideRow(0);
```

`createSlideRow` returns a `SlideRowNode`. New rows start empty — create slides within them using `createSlide(rowIndex, colIndex)`.

### Slide sections

Every slide row is a section. Without a name set, a row shows up in the UI as "Section" (the default label); setting `name` replaces that with a custom one. Sections surface in two places: the editor shows the section name next to the row, and the presenter view shows which section the current slide belongs to (and lets the speaker jump between sections).

So when the user asks to organize a deck into sections, group slides under topics, or label parts of a deck, setting `name` on the `SLIDE_ROW` is the move. Although `SLIDE_ROW` is otherwise opaque (no fills, effects, or layout), `name` is settable.

```js
// Rename the second section in the deck
const grid = figma.currentPage.children[0];  // SLIDE_GRID
const row = grid.children[1];                // SLIDE_ROW
row.name = "Demo";
```

### Cloning slides

```js
const original = figma.getNodeById("SLIDE_ID");
const copy = original.clone();
```

Cloned slides are appended to the current page by default. Use `setSlideGrid` to position them in the grid.

**Important:** `SlideGridNode.clone()` throws at runtime — you cannot copy the slide grid itself.

### Deleting slides

```js
const slide = figma.getNodeById("SLIDE_ID");
slide.remove();
```

Removing a slide automatically updates the grid. If you remove all slides in a row, the row remains but is empty.

### Reordering slides

Use `getSlideGrid` / `setSlideGrid` to rearrange slides. See [Slide Grid](#reference--slide-grid) for details.

---

## Reference — Slide Grid

The slide grid is a 2D array of `SlideNode` objects, organized by rows.

### Newly created files have an empty grid

A Slides file produced by `create_new_file` starts with **zero rows and zero slides** — `figma.getSlideGrid()` returns `[]`, not a default first slide. The page's only child is the `SLIDE_GRID` node itself (typically id `0:3`), which is empty until you create content. The first call to `figma.createSlide()` implicitly creates row 0 and inserts the new slide there; subsequent `createSlide()` calls append to the end of the last row.

```js
// On a fresh Slides file
const grid = figma.getSlideGrid();
// → []   (NOT a one-element array — there is no default slide)

const slide = figma.createSlide();   // creates row 0 + the slide in one shot
const grid2 = figma.getSlideGrid();
// → [[slide]]
```

If your script assumes at least one slide exists (e.g. to read theme tokens off it), guard for the empty case or call `createSlide()` first.

### Reading the grid

```js
const grid = figma.getSlideGrid();
// Returns: SlideNode[][]
// Example shape:
// [
//   [slide1, slide2],          // Row 0
//   [slide3, slide4, slide5],  // Row 1
//   [slide6],                  // Row 2
// ]

return grid.map((row, rowIdx) => ({
  row: rowIdx,
  slides: row.map((slide, colIdx) => ({
    id: slide.id,
    name: slide.name,
    col: colIdx,
  })),
}));
```

The inner arrays are plain `SlideNode[]` — they are NOT `SLIDE_ROW` nodes. Setting `.name` or any other property on them mutates a JS array, not the underlying section. To touch the `SLIDE_ROW` itself (e.g. to rename a section), traverse the node tree via `SLIDE_GRID.children`. See [slide-lifecycle.md — Slide sections](#slide-sections).

### Reordering the grid

`setSlideGrid` accepts a new 2D array. All existing slides must be present — you can change row grouping and ordering but cannot drop slides.

```js
// Move the first row to the end
const grid = figma.getSlideGrid();
const [firstRow, ...rest] = grid;
figma.setSlideGrid([...rest, firstRow]);
```

```js
// Flatten all slides into a single row
const grid = figma.getSlideGrid();
const allSlides = grid.flat();
figma.setSlideGrid([allSlides]);
```

```js
// Reverse slide order within each row
const grid = figma.getSlideGrid();
const reversed = grid.map(row => [...row].reverse());
figma.setSlideGrid(reversed);
```

```js
// Move a specific slide to a different row
const grid = figma.getSlideGrid();
const targetSlide = figma.getNodeById("SLIDE_ID");

const newGrid = grid.map(row => row.filter(s => s.id !== targetSlide.id));
// Add to the beginning of row 0
newGrid[0] = [targetSlide, ...newGrid[0]];
// Remove empty rows
const cleanGrid = newGrid.filter(row => row.length > 0);
figma.setSlideGrid(cleanGrid);
```

### Notes

- `getSlideGrid` / `setSlideGrid` are marked deprecated in favor of `getCanvasGrid` / `setCanvasGrid`, but both work in Slides.
- All slides from the current grid must be passed back to `setSlideGrid` — you can reorganize freely but cannot omit slides.

---

## Reference — Slide Design Principles

> Part of the [figma-use-slides skill](#use_figma--figma-plugin-api-skill-for-slides). Design guidance for creating visually compelling, varied slide decks that meet the expectations of a design-literate audience.

### Contents

- Color
- Type
- Content density
- Layout
- Shape language and motifs
- Composition
- What to avoid


### When you're editing an existing deck

These principles describe what to *choose* when building from scratch. When editing an existing deck — adding a slide, reworking a section, changing colors — they describe what you're *matching*. Inspect the deck first: its palette, type choices, spatial habits, and motifs are the design language. Your job is to stay consistent with it, not to introduce new principles from this document that conflict with what's already there. Only reach for these principles to fill gaps the existing deck doesn't answer.

### When the user supplies a design direction

Everything below is guidance for designing from scratch. When the user provides brand guidelines, a color palette, typography specs, or a reference file, those inputs take precedence over the principles here. A user who says "our brand uses Helvetica and a navy/gold palette" has already made the type and color decisions — the guidance in this document applies to the decisions they *haven't* made (layout variety, composition, spatial pacing, content density).

The principles here still matter even when working within brand constraints — a branded deck still needs clear hierarchy, varied layouts, and deliberate composition. But "let one color lead" means let the user's primary brand color lead, not a color you chose. "Choose typefaces that match the deck's voice" means work within the brand's type system, not introduce a new one. Read each principle below through the lens of the user's inputs: where they've decided, follow; where they haven't, these principles guide you.


### Color

**Let one color lead.** A palette works when there's a clear protagonist — one hue that owns the majority of the visual real estate, supported by a secondary tone and punctuated by an accent. When every color gets equal stage time, the result feels indecisive.

**Make the palette earn its place.** The colors should feel like they belong to *this* presentation's subject matter. A deck about infrastructure reliability and a deck about a brand campaign shouldn't look like they share a Figma library. React to the content.

**Think about the deck's tonal arc.** Dark slides hit differently than light ones — use that. A common structure is to bookend the deck (title + closing) with darker, more atmospheric slides and keep the middle lighter for readability. But going all-dark or all-light is fine too, as long as it's a choice and not an accident.

**Treat backgrounds as a design surface.** A background isn't just "the thing behind the content." Gradients, color fields, soft geometric forms near the edges, or tonal shifts between sections all create mood and guide the eye without fighting the foreground.

**Readability is non-negotiable.** Body text on dark backgrounds must be high-contrast — close to white, not muted or tinted. Reserve brand/accent colors for headings, labels, and shapes. If you squint and can't instantly read the body copy, the contrast is too low. A beautiful palette that people can't read is just decoration.


### Type

**Choose typefaces that match the deck's voice.** Use `listAvailableFontsAsync()` to see what's installed — there are far more options than the usual defaults. A display face for headings paired with a workhorse for body copy gives the deck a distinct personality. Vary your choices between decks; don't converge on the same pairing every time.

**Make the hierarchy unmissable.** If someone squints at a slide from across the room, the title should still be the loudest thing. That means real scale difference — not a polite step between levels. A title should dominate the slide; body text should clearly defer to it.

**Align body copy to the left.** Centered paragraphs and bullet lists are harder to scan. Reserve center-alignment for titles, pull quotes, and single-line statements. Everything else should have a clean left edge.

**Use weight as a design tool.** Light, regular, semibold, and bold aren't just for emphasis — they shape the texture of a slide. A thin display title over heavy body text creates a very different mood than a bold slab heading with lightweight supporting copy.


### Content density

**Slides are not documents.** A slide exists to land one idea with visual impact — not to exhaustively cover a topic. The moment you're fitting "everything important" onto one slide, you've switched from designing a presentation to writing a report. Resist the urge.

**The test is simple: can someone absorb this slide in a few seconds?** If a slide requires careful reading, it has too much content. Presentations move at a pace the speaker controls — not the reader. Every element on a slide should be graspable at a glance. If it can't be, the content needs to be cut or split across slides.

**Your job is editorial.** When adapting source material into slides, deciding what to *leave out* is more important than deciding what to include. Every point you cut makes the remaining points stronger. A slide with one bold insight and generous whitespace lands harder than a slide with six good points crammed together. Bullet lists, comparison tables, and multi-column layouts all share the same trap: they make it easy to keep adding items because there's always room for one more row. The question is never "does it fit?" — it's "does each item earn its place at the cost of the others' impact?"

**More slides, not denser slides.** If content feels important but won't fit without crowding, the answer is splitting it across two well-composed slides — not shrinking the font or tightening the spacing. Slides are free; attention is not.


### Layout

**Derive layout from content, don't select from a menu.** Every slide has a rhetorical purpose — introducing an idea, proving a point, creating a pause, delivering a punchline. The layout should emerge from that purpose. A single key metric wants to be huge and surrounded by space. A comparison wants visual separation that reinforces the contrast. A turning point wants restraint and emptiness. Start with "what is this slide *doing*?" and let the spatial arrangement follow.

**Interesting layouts come from imbalance, not symmetry.** A 50/50 split is stable but static. An 70/30 division creates visual direction — the eye moves from the larger zone to the smaller one. Uneven distributions of content and space generate the tension that makes a composition feel designed rather than default. This applies to everything: how you divide the canvas, how you weight text against empty space, how you size elements relative to each other.

**The relationship between elements carries meaning.** Whether content is overlapping, adjacent, nested, or isolated changes how it reads. Elements that overlap feel connected and layered. Elements separated by generous space feel independent and important. Elements pushed to the edge feel dynamic and cropped — like you're seeing part of a larger composition. Think about what the spatial relationship *says*, not just where things fit.

**Vary structure across the deck.** The quickest way to make a deck feel automated is to repeat the same spatial structure on every slide. If you step back and every slide has the same content placement — heading top-left, body below, supporting content in a grid — the deck has a mechanical rhythm regardless of how different the content is. Each slide should feel like a fresh composition, not a filled-in template. This means varying where content anchors (left, right, center, edge), how the canvas is divided (or not divided), and how much of the slide is occupied vs. left open.

**Use the full 1920×1080 canvas.** Content that huddles in the center with uniform margins wastes the most impactful real estate: the edges. Shapes that bleed off the canvas, headings anchored to corners, color fields that extend to the frame boundary — these make the slide feel like a window into a larger world rather than a bordered container.

**Plan the layout sequence before building.** Before writing any code, decide the spatial strategy for each slide. If the sequence feels repetitive when described in words — "grid, grid, two-column, grid, two-column" — it will feel repetitive visually. Rearrange and diversify before you start building. This is far cheaper than rebuilding slides later.

**Pacing matters as much as individual layouts.** A deck needs rhythm — moments of density followed by moments of openness, dark slides followed by light ones, information-rich layouts followed by slides with a single idea and nothing else. These quieter slides aren't filler; they're the pauses that give the dense slides their impact. Without them, every slide competes equally for attention and none of them win.


### Shape language and motifs

**Add at least one non-text element per slide.** A shape, a line, a filled rectangle, an accent circle, a decorative border — something that gives the eye a resting point and adds structure. All-text slides disappear from memory instantly.

**Pick a recurring visual element and repeat it.** Cohesion across a deck comes from repetition with variation. Choose one signature treatment and thread it through the deck. A good motif is recognizable (you'd spot it out of context), repeatable (it works across different slide types without forcing the layout), and varied in application (same element used differently — cropped on one slide, full on another, large here, small there). The motif itself can be anything — a shape, a line treatment, a layering convention, a spatial rule — as long as it's distinctive enough to feel like a deliberate throughline.

**Use shapes structurally, not just decoratively.** Rectangles can be content containers, section dividers, background panels, or callout frames. Lines can separate regions, connect ideas, or create visual rhythm. Circles can anchor icons or draw focus to key numbers. Shapes are layout tools as much as visual ones.

**Commit to your motif — don't hedge with low opacity.** A recurring shape at 4–6% opacity is invisible; it's a gesture toward design without actually making a design decision. If you choose a circle motif, make it visible — large enough to crop off an edge, opaque enough to register as a deliberate element. If a shape wouldn't be missed if you deleted it, it's not pulling its weight.


### Composition

**Let things be off-center.** Symmetric, perfectly centered layouts are stable but static. Shifting a content block to the left third of the slide, or pushing a shape cluster toward the upper-right corner, creates movement and makes the composition feel considered rather than default.

**Layer elements for depth.** A colored rectangle behind a text block, an accent shape that partially overlaps a content boundary, a decorative element that bleeds off the canvas edge — these overlaps add dimension and make the slide feel like a composed scene instead of a flat arrangement of objects.

**Commit to density or openness.** A slide with a single insight surrounded by white space feels intentional. A slide with a tightly packed comparison grid feels intentional. A slide that's vaguely populated — neither spacious nor dense — just feels unfinished. Pick a gear and stay in it.

**Push toward the edges.** Elements near the edges of the canvas create tension and energy. A color block bleeding off the left side, a title anchored to the top-left corner, a decorative shape cropped by the bottom edge — these make the slide feel like a window into a larger composition rather than a bordered frame.

**Vary your anchor points.** If every slide starts its content at the same x/y position with the same margins, the deck develops a mechanical rhythm regardless of how different the content is. Shift the anchor — one slide starts content in the upper-left, the next centers a single element, the next pushes a heading to the right third. The variation should feel intentional, not random, but it should be *present*.


### What to avoid

These patterns signal that a deck was generated without design intent. Actively steer away from them:

- **Identical structure on every slide** — title centered at top, bullet list below, slide after slide. Rotate between different layout patterns.
- **Safe, noncommittal color** — everything in muted gray-blue with no clear primary or accent color. Take a stand on the palette.
- **Text-only slides** — no shapes, no visual structure, no spatial interest. Every slide needs at least one non-text element.
- **Centered everything with matching margins** — nothing approaches the edges. Let elements anchor to corners, push into margins, or bleed off the canvas.
- **A line under every heading** — this is a tell. Separate sections with space, color changes, or layout shifts instead.
- **Flat hierarchy** — all text within a narrow size range (18–24pt) with no clear visual priority. Headlines should be dramatically larger than body text.
- **Same typeface on every deck** — choosing the same "safe" font regardless of context. Match type choices to the deck's personality and vary them between projects.
- **Plain backgrounds throughout** — every slide the same flat color with nothing in the background layer. Even subtle treatments — a gradient, a soft shape, a tonal shift — add presence.
- **Even spacing everywhere** — no rhythm, no grouping, no visual pacing. Related items should cluster tightly; important ideas should have room around them.
- **One container shape for everything** — when every piece of content lives inside a slightly-tinted rounded rectangle, the deck becomes a grid of containers regardless of what's inside them. Not every piece of content needs a box around it. A pull quote can just be big italic text. A stat can just be a number. A comparison can be spatial separation rather than two columns of cards. Reach for a container only when grouping genuinely serves the content, not as a default wrapper.
- **Identical layouts with swapped colors** — when comparing two subjects, it's tempting to make structurally identical slides with different accent colors. This signals that you ran the same template twice. Give each subject a distinct composition — the visual difference reinforces the conceptual difference.
- **Sacrificing legibility for mood** — muted, tinted, or low-opacity body copy on dark backgrounds might look "designed" at a glance but fails the actual job of being read. Body text exists to be read. Use color expressively on headings, labels, and shapes — not on the text people need to absorb.
- **Too much content with nice typography** — dense comparison tables, long bullet lists, and multi-paragraph slides don't become good slides just because the font is beautiful. Good typography doesn't fix bad editorial choices. Cut the content first, then design what remains.
- **Same spatial starting point on every slide** — when every slide anchors content to the same position with the same margins, the deck develops a mechanical rhythm that undermines any other variety you've built. Vary where content lives on the canvas from slide to slide.
- **Decorative elements that wouldn't be missed** — shapes placed as "atmosphere" that are too small, too faint, or too generic to register as intentional. If removing an element wouldn't change how the slide reads, it's not contributing. Decorative elements should be bold enough that their presence is a deliberate design choice.

---

## Reference — Slide-Specific Properties

### isSkippedSlide

Read and set whether a slide is skipped during presentation playback.

```js
const slide = figma.getNodeById("SLIDE_ID");

// Read
const isSkipped = slide.isSkippedSlide;

// Set — skip a slide
slide.isSkippedSlide = true;

// Unskip
slide.isSkippedSlide = false;
```

### focusedSlide (Page property)

Get or set the currently focused slide on a page. This is a property of `PageNode`, not `SlideNode`.

```js
// Get the focused slide
const focused = figma.currentPage.focusedSlide;
if (focused) {
  return { focusedSlideId: focused.id, name: focused.name };
}

// Set the focused slide
const slide = figma.getNodeById("SLIDE_ID");
figma.currentPage.focusedSlide = slide;
```

### focusedNode (Page property)

Get or set the currently focused node on a page. Works with any focusable node.

```js
const focused = figma.currentPage.focusedNode;
if (focused) {
  return { id: focused.id, type: focused.type, name: focused.name };
}
```

### speakerNotes

Read and set the presenter/speaker notes for a slide. The value is a **markdown string**.

```js
const slide = figma.getNodeById("SLIDE_ID");

// Read speaker notes
const notes = slide.speakerNotes;
// Returns "" if no notes are set

// Set speaker notes (plain text)
slide.speakerNotes = "Remember to mention the Q4 goals.";

// Set speaker notes with list formatting
slide.speakerNotes = "Key points:\n- Revenue grew 20%\n- User base doubled\n- NPS at all-time high";

// Set speaker notes with numbered list
slide.speakerNotes = "Agenda:\n1. Introduction\n2. Demo\n3. Q&A";

// Clear speaker notes
slide.speakerNotes = "";
```

#### Supported formatting

The speaker notes editor in Figma Slides supports a subset of markdown formatting:

- **Unordered lists**: `- item` or `* item`
- **Ordered lists**: `1. item`, `2. item`
- **Bold**: `**text**`
- **Italic**: `*text*`
- **Bold + italic**: `***text***`
- **Strikethrough**: `~~text~~`

The following markdown is **not supported** and will be stored as raw text (the markdown syntax characters will appear literally in the notes):
- Headings (`# text`, `## text`)
- Code blocks (`` `code` `` or ` ``` `)
- Links (`[text](url)`)
- Underline

### InteractiveSlideElementNode

Interactive elements embedded in slides (polls, embeds, etc.). These are read-only — you cannot create them via the Plugin API, but you can detect and inspect them.

```js
const slide = figma.getNodeById("SLIDE_ID");
const interactive = slide.findAllWithCriteria({ types: ["INTERACTIVE_SLIDE_ELEMENT"] });
return interactive.map(n => ({
  id: n.id,
  type: n.interactiveSlideElementType,
}));
```

Possible `interactiveSlideElementType` values: `'POLL'`, `'EMBED'`, `'FACEPILE'`, `'ALIGNMENT'`, `'YOUTUBE'`.

### Known Limitations

- **`getSlideTransition()` / `setSlideTransition()`**: These methods are declared in the type definitions but throw "not implemented" at runtime. Do not use them.
- **`SlideGridNode.clone()`**: Throws at runtime — you cannot copy the slide grid.
- **Slide themes**: `slideThemeId` is available as a read-only property on slide nodes for identifying which theme is applied, but theme manipulation APIs are limited.
- **`figma.createTable()` and `figma.createGif()`**: These FigJam node types (TABLE, MEDIA) are currently blocked in Slides mode by the Plugin API, even though the Slides editor supports tables and media. To work with tables and media in Slides, use the editor UI directly. This is a pre-existing Plugin API limitation, not specific to `use_figma`.

<!-- TODO(dschwartz): Before production launch, fix NODE_TYPES_BLOCKED_IN_SLIDES in
     share/plugin-api/src/api/constants.ts to unblock TABLE and MEDIA for Slides
     (same pattern as the SYMBOL unblock for MCP/assistant). Remove this limitation
     note once fixed. -->

---

## Reference — Slide Content

`SlideNode` extends `BaseFrameMixin`, which means slides support the same content creation patterns as frames in Design mode: text, shapes, auto-layout, images, components, and instances.

### Adding text to a slide

Canonical recipe: load font → `await` → mutate → return affected IDs. Inter is preloaded; for any other family the same `loadFontAsync` step is required or you'll hit `Cannot write to node with unloaded font "<family> <style>"`. See figma-use → gotchas.md → Canonical text-edit recipe (load `readPowerSteering("figma", "figma-use.md")`).

```js
const slide = figma.getNodeById("SLIDE_ID");

// Load font BEFORE any text mutation — required for every font, not just Inter
await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
const title = figma.createText();
title.fontName = { family: "Inter", style: "Semi Bold" };
title.characters = "Quarterly Review";
title.fontSize = 48;

slide.appendChild(title);
title.x = 100;
title.y = 80;

return { createdNodeIds: [title.id] };
```

Use `listAvailableFontsAsync()` to discover exact style strings. Note: "Inter" uses "Semi Bold" (with a space), not "SemiBold" — guessing style names is a common cause of the unloaded-font error even when `loadFontAsync` is called.

### Bulleted and numbered lists

Slides are bullet-heavy by nature. Use a **single TextNode** with `\n`-separated lines and `setRangeListOptions(start, end, { type: 'UNORDERED' | 'ORDERED' })` for native bulleted text — it gives proper hanging indents on wrapped lines.

```js
await figma.loadFontAsync({ family: "Inter", style: "Regular" });

const text = figma.createText();
slide.appendChild(text);
text.fontName = { family: "Inter", style: "Regular" };
text.fontSize = 20;
text.characters = [
  "Explore ideal outputs",
  "Eval: benchmark vs current on large files",
  "Eval: DS context into code generation · React / Vue / iOS / Android",
].join("\n");
text.fills = [{ type: "SOLID", color: { r: 0.07, g: 0.09, b: 0.13 } }];
text.lineHeight = { unit: "PERCENT", value: 145 };
text.setRangeListOptions(0, text.characters.length, { type: "UNORDERED" });

return { createdNodeIds: [text.id] };
```

**Do NOT** build bullets by laying out an ellipse + text in a horizontal auto-layout row. That pattern misaligns when text wraps to multiple lines (the wrapped line starts at the dot's x, not the first character's x — no hanging indent), and it produces a tree of vector nodes instead of a single editable text block. Use `setRangeListOptions` instead.

If only some lines should be bullets (e.g. a heading line followed by bullet items), pass a partial range: `text.setRangeListOptions(headingLength + 1, text.characters.length, { type: "UNORDERED" })`. Pass `{ type: "NONE" }` to remove list formatting from a range.

### Adding shapes

```js
const slide = figma.getNodeById("SLIDE_ID");

const rect = figma.createRectangle();
rect.resize(400, 300);
rect.fills = [{ type: "SOLID", color: { r: 0.95, g: 0.95, b: 0.97 } }];
rect.cornerRadius = 12;

slide.appendChild(rect);
rect.x = 200;
rect.y = 200;

return { createdNodeIds: [rect.id] };
```

### Adding images to a slide

**`upload_assets` is the ONLY supported way to put an image on a slide.** Do NOT use `figma.createImage()` or `figma.createImageAsync()` from inside `use_figma` — they are unsupported as image-upload entry points in Slides. Call `upload_assets` with the Slides `fileKey`; the tool returns single-use upload URLs that you POST raw image bytes to, and the image is committed and placed automatically. Pass `nodeId` (with `count: 1`) to attach the upload to an existing slide node as a fill (e.g. a rectangle already on the slide); omit `nodeId` to drop the image onto the slide as a new layer.

For the full request/response shape, see figma-use → api-reference.md → Images (load `readPowerSteering("figma", "figma-use.md")`).

### Using auto-layout within slides

```js
const slide = figma.getNodeById("SLIDE_ID");

const container = figma.createAutoLayout("VERTICAL", {
  name: "Content Block",
  itemSpacing: 16,
  paddingLeft: 40,
  paddingRight: 40,
  paddingTop: 40,
  paddingBottom: 40,
});

slide.appendChild(container);
container.layoutSizingHorizontal = "FILL";
container.layoutSizingVertical = "HUG";

return { createdNodeIds: [container.id] };
```

Remember: `layoutSizingHorizontal/Vertical = 'FILL'` must be set **after** `appendChild`.

### Working with components

Components (`SYMBOL`) are intentionally allowed in Slides mode for MCP/assistant use. You can create components and instances within slides.

```js
const component = figma.createComponent();
component.name = "Card";
component.resize(400, 200);

const instance = component.createInstance();
const slide = figma.getNodeById("SLIDE_ID");
slide.appendChild(instance);

return { createdNodeIds: [component.id, instance.id] };
```

### Positioning within slides

Slides have a fixed canvas size (typically 1920x1080). Position content using absolute `x`/`y` coordinates within the slide, or use auto-layout containers to handle positioning automatically.

**Critical: MUST set `x`/`y` AFTER `appendChild` — at every level of nesting.** Setting position before parenting causes a `(−240, −240)` shift because new nodes are silently auto-parented to a slide context at absolute `(240, 240)`. The rule applies to frames inside other frames, not just the slide root. See [Slide Gotchas & Common Mistakes](#position-after-appendchild-critical) for the helper pattern (`addFrame` / `addText` / `addRect`) you should use to make the order impossible to write wrong.

Recommended pattern — append first, then configure:

```js
const slide = figma.getNodeById("SLIDE_ID");

const node = figma.createRectangle();
slide.appendChild(node);
node.resize(400, 300);
node.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.3 } }];
node.cornerRadius = 12;
node.x = 200;
node.y = 200;

return { width: slide.width, height: slide.height, nodeId: node.id };
```
