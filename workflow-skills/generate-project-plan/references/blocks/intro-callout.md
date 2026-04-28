# Block: Intro callout

A highlighted intro paragraph rendered at the top of a section, with a distinct background fill that stands out from the section's own palette color. Used to orient the reader before the rest of the section's content.

## When to use

- Motivation section — a one- or two-sentence "why this project exists" paragraph before the "Resources" subsection.
- Any section where the first block is a short, high-visibility statement (mission, scope note, TL;DR).

Do NOT use for:
- Standalone body text (use [text-primitives.md](text-primitives.md)).
- Multi-paragraph intros (they dilute the highlight).

## Structure

A `FRAME` (with auto-layout OFF — just a background rect) containing a single body TEXT node, positioned just below the H2 header inside the section.

Alternative: a plain TEXT node with its own fill/padding via `setRangeFills` — but FRAME is simpler.

## Geometry

- Width: inner section width = `LEFT_COL_W - 2 * SECTION_PAD = 736`.
- Padding: 16px on all sides.
- Text: body (16px), wrapped at `frame.width - 32`.
- Background fill: a **softer/lighter** variant of the parent section palette. For `lightViolet` parent → use `SECTION.lightViolet` with a lower-opacity overlay, or a related lighter purple. Simplest: a white-ish overlay over the parent color (fill = `SECTION.white`).

## Create script

```js
const font = { family: 'Inter', style: 'Medium' };
await figma.loadFontAsync(font);

// Position after H2
const h2 = section.children.find(c => c.type === 'TEXT' && c.fontSize === 40);
const calloutY = (h2 ? h2.y + h2.height : 32) + 16;

const frame = figma.createFrame();
frame.name = "Intro callout";
frame.fills = [{ type: 'SOLID', color: SECTION.white }];
frame.cornerRadius = 8;
section.appendChild(frame);
frame.x = 32;
frame.y = calloutY;

const INNER_W = 800 - 2 * 32; // 736 — inner width of a left-column section
frame.resize(INNER_W, 100); // temp; resize after text measured

const text = figma.createText();
text.fontName = font;
text.fontSize = 16;
text.characters = introText;
text.fills = [{ type: 'SOLID', color: CHARCOAL }];
text.textAutoResize = 'HEIGHT';
frame.appendChild(text);
text.x = 16;
text.y = 16;
text.resize(INNER_W - 32, text.height);

// Hug frame around text + padding
frame.resize(INNER_W, text.height + 32);
```

## Color variants

| Parent slug | Callout fill | Reason |
|---|---|---|
| `motivation` (lightViolet) | `SECTION.white` | Max contrast — callout pops off the purple bg |
| `context` (lightGray) | `SECTION.white` | Same — white on gray |
| `goals` (lightGreen) | `SECTION.white` | Same |
| `rollout` (lightOrange) | `SECTION.lightYellow` | Warm-on-warm, subtle |
| any | Custom color the user specifies | Override |

Default: white if parent is a mid-tone palette; a closely related lighter palette if parent is already very light.

## Pre-flight checklist

- [ ] Callout is a `FRAME` (not a SECTION) — nested sections are handled separately.
- [ ] Frame appended to section BEFORE setting `x`/`y`.
- [ ] Frame fill uses `hex/255` palette color.
- [ ] Text is appended to FRAME (not the section).
- [ ] Frame height is hugged to text height + 32.
- [ ] Frame is part of `mutatedNodeIds` return.
