---
name: figma-use-motion
description: "Motion / animation context for the `use_figma` MCP tool — animating Figma nodes via manual keyframes, animation styles, easing, and timeline duration. Load alongside figma-use whenever a task involves adding, editing, or inspecting animation on a node."
disable-model-invocation: false
---

# use_figma — Figma Plugin API Skill for Motion

Motion context for the `use_figma` MCP tool. [figma-use](../figma-use/SKILL.md) covers the foundational Plugin API rules — load both together.

**Always pass `skillNames: "figma-use-motion"` (comma-separated alongside `figma-use`) when calling `use_figma` for motion work.** Logging only.

## Runtime Gating

Motion APIs are gated behind the `metronome` user feature flag. When the calling user doesn't have it, every motion property and helper referenced in this skill throws `"<name>" is not a supported API`.

**Bail out fast on that error.** Do not retry; tell the user motion isn't enabled for them and stop. Otherwise you'll burn calls and confuse the user with repeated identical failures.

## When to use this skill

Load this skill whenever a `use_figma` task involves:

- Adding, editing, or removing keyframes on a node (`manualKeyframeTracks`, `applyManualKeyframeTrack`, `removeManualKeyframeTrack`).
- Animating fill or stroke colors over time.
- Applying, editing, or removing animation styles (`applyAnimationStyle`, `removeAnimationStyle`, `animationStyles`).
- Reading or writing timeline duration via `node.timelines` / `node.setTimelineDuration(id, seconds)`.
- Choosing easing for any of the above.

Static design work (creating shapes, components, variables, layout) goes through [figma-use](../figma-use/SKILL.md) alone — this skill is only for the time dimension.

## Exposed motion API surface

- `node.manualKeyframeTracks` — read/write manual keyframes (including fill, stroke, and effect tracks).
- `node.applyManualKeyframeTrack(field, track)` / `node.removeManualKeyframeTrack(field)` — add, replace, or remove one manual keyframe track without rewriting the whole object.
- `node.animationStyles` — read/write animation-style metadata applied to a node.
- `node.applyAnimationStyle(styleId, presetData?)` / `node.removeAnimationStyle(id)` — apply a discovered style and remove an applied style instance by its returned/read-back `id`.
- `node.timelines` — read-only timeline list for the containing top-level frame, with durations in seconds.
- `node.setTimelineDuration(id, durationSeconds)` — write the containing top-level frame timeline duration.
- `node.animations` — read-only resolved keyframe data (currently manual tracks only — see [motion-patterns.md](references/motion-patterns.md)).
- `figma.motion.figmaAnimationStyles()` — read-only list of Figma's first-party animation styles.

Authoring custom `"figma:motion"` preset module source code is out of scope. If the user wants a brand-new animation style, say so and stop; don't fabricate one.

## Reference docs

Load these as needed based on what the task involves:

| Doc | When to load | What it covers |
|-----|-------------|----------------|
| [motion-patterns.md](references/motion-patterns.md) | Adding/editing motion animation | Manual keyframes, animated fills/strokes, applying animation styles, timeline duration |
| [motion-easing.md](references/motion-easing.md) | Setting animation easing | Keyframe easing objects, custom cubic/spring, `HOLD`, applying easing inside an animation style |

## Verifying the animation

`get_screenshot` shows only the timeline's **resting state**, never motion. The Figma MCP server has no tool that renders an animated video, so verify the motion from the authored data instead:

1. **Read the keyframes back.** `node.animations` / `node.manualKeyframeTracks` resolve the tracks you authored — confirm the expected fields, easing, and timing are present on the right nodes, and that mutated node IDs are returned.
2. **Check the timeline.** Confirm the containing top-level frame's duration via `node.timelines` (extend with `node.setTimelineDuration` when needed).
3. **When only a visual check will do,** ask the user to export a video locally from Figma — video rendering isn't available through the MCP server (see [unsupported-and-fallbacks](../figma-implement-motion/references/unsupported-and-fallbacks.md)). Otherwise, walk through each keyframe phase against the timeline and reason about the motion.

**Iterate until it's right.** The read-back is a diagnostic, not a sign-off: if the tracks are wrong (bad order, off timing, a missing element, a mask blanking the composite), fix the keyframes/styles and re-read. Read *all* the resolved tracks and batch every fix into one pass.

Skip the extra verification entirely for trivial or self-evident changes.

## Pre-flight checklist

In addition to the [figma-use pre-flight checklist](../figma-use/SKILL.md#8-pre-flight-checklist), verify:

- [ ] Easing uses the public `{ type: 'EASE_OUT', easingFunctionCubicBezier?: …, easingFunctionSpring?: … }` shape — not internal scenegraph names like `OUT_CUBIC`.
- [ ] Ease-in-out uses the exact public enum `EASE_IN_AND_OUT` (or `EASE_IN_AND_OUT_BACK`); never emit the invalid alias `EASE_IN_OUT`.
- [ ] The node being animated is not a top-level frame (direct child of a page). Animate descendants instead.
- [ ] Timeline values are seconds in the public Plugin API. Extend via `setTimelineDuration`; never shorten unless the user asked.
- [ ] Transform keyframe fields use public names (`TRANSLATION_X`, `TRANSLATION_Y`, `ROTATION`, `SCALE_X`, `SCALE_Y`, `SCALE_XY`), not internal `MOTION_*` scenegraph names.
- [ ] Manual keyframe fields come from the public allowlist in [motion-patterns.md](references/motion-patterns.md#animatable-fields); generated/internal scenegraph fields intentionally throw.
- [ ] Mutated node IDs are returned (per `figma-use` Rule 15).
- [ ] When motion correctness isn't self-evident, verify by reading back the resolved keyframes and timeline — or ask the user to export a video locally from Figma (see the Verifying the animation section above). `get_screenshot` shows only the resting state.
