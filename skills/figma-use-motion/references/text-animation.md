# Text animation

Use this reference for motion within a text layer: character, word, line, or paragraph reveals, entrances, exits, and edits to the styles inside a text animation. For moving or fading the entire text layer together, ordinary node keyframes or animation styles are sufficient.

These examples run through `use_figma`: use top-level `await` and `return`, include `figma-use,figma-use-motion` in `skillNames`, and replace page/node/application IDs with inspected IDs. Each call has fresh JavaScript state and starts on the first page, so resolve the target and switch to its page in each call.

## Discover and preserve

1. Inspect the target text node, its containing timeline, and existing `animationStyles` before writing. Keep its characters, formatting, wrapping, and hierarchy intact. Native text animation uses the existing text layout; do not split text into separate nodes, outline glyphs, or replace characters to imitate a reveal.
2. If the request also changes characters or typography, make those static edits first. Before those edits, await `figma.loadFontAsync(fontName)` for each font from `node.getStyledTextSegments(['fontName'])`. A pure motion edit leaves the text and fonts intact.
3. Discover the native definition with `figma.motion.figmaAnimationStyles()` and match `styleId === 'TextStagger'`. Names may be localized. Read its advertised properties; discovery returns documentation strings, not values to copy into setters.

Text animation follows the main skill's node restrictions. Animate a text descendant of a top-level frame. Preserve component instances and instance sublayers; do not detach them to bypass an API error. The internal `Text` typewriter preset is not the discoverable `TextStagger` definition.

## One preset, multiple text styles

One applied `TextStagger` contains any combination of Position, Rotation, Scale, Opacity, and Blur. These are fields in one flat `props` object, not a nested array of independently applied styles.

For each style, `*Enabled: true` adds its tracks. `*Visible: false` keeps the style present but disables its tracks; `*Visible: true` enables playback. To remove only one style from the text animation, set its `*Enabled` field to `false`. To temporarily mute it, keep `*Enabled: true` and set `*Visible: false`.

| Style | Include / play | Settings and units |
| --- | --- | --- |
| Position | `positionEnabled` / `positionVisible` | `direction`: `left`, `right`, `top`, `bottom`, `top_left`, `top_right`, `bottom_left`, `bottom_right`; `distance` in pixels |
| Rotation | `rotationEnabled` / `rotationVisible` | `rotationDirection`: `clockwise` or `counterClockwise`; `rotationAmount` in degrees |
| Scale | `scaleEnabled` / `scaleVisible` | `scaleAmount` in percent; `100` is unchanged size |
| Opacity | `opacityEnabled` / `opacityVisible` | `opacityAmount` in percent of the resting opacity; `0` is transparent, `100` leaves the existing opacity unchanged |
| Blur | `blurEnabled` / `blurVisible` | `blurAmount` in pixels |

Position is included by default; the other four styles are not. All visibility controls default to `true`. Explicitly disable Position for an opacity-only or blur-only animation.

Shared properties apply to every included style:

- `animationDirection`: `'in'` animates from the configured amounts to the resting appearance; `'out'` reverses that motion. Position's `direction` describes the offset side: `'bottom'` with `'in'` starts below and moves up.
- `textDelayGrouping`: `'CHARACTER'`, `'CHARACTER_NO_WHITESPACE'`, `'WORD'`, `'LINE'`, or `'PARAGRAPH'`. Character grouping follows shaped text clusters; line grouping follows the current visual layout. Preserve wrapping and let the native renderer resolve groups.
- `textDelayOrder`: `'LEFT_RIGHT'`, `'RIGHT_LEFT'`, `'CENTER_OUT'`, or `'RANDOM'`.
- `duration`: the total text stagger span in seconds, not a duration to multiply by the number of words or characters. For direct application, it can be supplied as a top-level field; a value or variable binding in `props.duration` takes precedence.
- `presetStaggerOverlap`: `0` to `100` percent. Each group's animation duration is this fraction of the total duration; the remaining time distributes the groups' starts according to the chosen order. `100` animates all groups simultaneously; `0` makes each group's change instantaneous at its staggered start. It is not a delay in milliseconds.
- `delay`: seconds inside `props`; `timelineOffset`: a top-level start offset in seconds. Account for both when fitting the containing timeline.
- `easing`: use the public shape, such as `{ type: 'EASE_OUT' }`. See [motion-easing.md](motion-easing.md); never copy an internal enum from a discovery documentation string.

There is one setting per style type and shared timing/easing for the whole preset. Do not invent per-style durations, a nested `styles` array, or duplicate Position rows inside one preset. Separate entrance and exit phases can use separate `TextStagger` applications; preserve and identify each application independently.

## Add Position, Opacity, and Blur

This example adds one text animation with three styles. Replace the node id with the inspected target; adjust grouping and values to the request.

```js
const page = await figma.getNodeByIdAsync('0:1');
if (!page || page.type !== 'PAGE') throw new Error('Expected the inspected page');
await figma.setCurrentPageAsync(page);
const node = await figma.getNodeByIdAsync('123:456');
if (!node || node.type !== 'TEXT') {
  throw new Error('Expected a text node');
}
const definition = figma.motion.figmaAnimationStyles().find(
  (style) => style.styleId === 'TextStagger',
);
if (!definition) {
  throw new Error('Text motion is unavailable in this session');
}
const timeline = node.timelines[0];
const timelineRoot = timeline && await figma.getNodeByIdAsync(timeline.id);
if (!timelineRoot) {
  throw new Error('Expected text inside an animation timeline');
}

for (const segment of node.getStyledTextSegments(['fontName'])) {
  await figma.loadFontAsync(segment.fontName);
}

const duration = 0.6;
const appliedId = node.applyAnimationStyle(definition.styleId, {
  duration,
  timelineOffset: 0,
  props: {
    animationDirection: 'in',
    textDelayGrouping: 'WORD',
    textDelayOrder: 'LEFT_RIGHT',
    presetStaggerOverlap: 50,
    delay: 0,
    easing: { type: 'EASE_OUT' },

    positionEnabled: true,
    positionVisible: true,
    direction: 'bottom',
    distance: 24,

    opacityEnabled: true,
    opacityVisible: true,
    opacityAmount: 0,

    blurEnabled: true,
    blurVisible: true,
    blurAmount: 12,

    rotationEnabled: false,
    scaleEnabled: false,
  },
});

// This example starts at zero with no delay; its total span is duration.
const mutatedNodeIds = [node.id];
if (timeline.duration < duration) {
  node.setTimelineDuration(timeline.id, duration);
  mutatedNodeIds.push(timeline.id);
}
return {
  mutatedNodeIds,
  appliedId,
  applied: node.animationStyles.find((style) => style.id === appliedId),
  timelines: node.timelines,
};
```

`applyAnimationStyle` adds a new application and preserves the node's existing animation. Keep the returned applied `id` for later edits or removal. The definition's `styleId` identifies the preset type, not a particular application.

## Typewriter and other starting points

Configure the same discovered `TextStagger` for these requests. Keep timing in seconds and adjust the total duration to the text and requested pace.

| Request | Configuration |
| --- | --- |
| Typewriter reveal | `animationDirection: 'in'`, `textDelayGrouping: 'CHARACTER'`, `textDelayOrder: 'LEFT_RIGHT'`, `presetStaggerOverlap: 0`, and only Opacity enabled/visible with `opacityAmount: 0`. Each character appears instantly at its staggered start; disable Position, Rotation, Scale, and Blur. Use `'CHARACTER_NO_WHITESPACE'` to skip spaces in the stagger. |
| Words rise and sharpen | The three-style example above: `'WORD'`, Position from `'bottom'`, Opacity from `0`, Blur to sharp, and nonzero overlap. |
| Lines fade in | `'LINE'`, only Opacity enabled/visible with `opacityAmount: 0`, and nonzero overlap. Wrapping determines the visual lines. |
| Paragraphs leave in reverse order | `'PARAGRAPH'`, `'RIGHT_LEFT'`, `animationDirection: 'out'`, and the requested enabled styles. |
| Characters expand from the center | `'CHARACTER'`, `'CENTER_OUT'`, Scale enabled/visible with `scaleAmount` below `100`, optionally with Opacity. Disable Position unless requested. |

A typewriter reveal preserves the final text layout; it does not reflow the sentence as if typing or create a blinking cursor. Do not repeatedly rewrite `characters`, use timers, or create one node per letter. The internal `Text` preset is not a substitute for the discoverable `TextStagger`.

## Edit or remove existing text motion

Select the intended application from the inspected `node.animationStyles` and retain its `id`. If there are multiple text animations, use their properties, phase, and start offsets to identify the requested one. Do not assume the applied `styleId` must still be the literal `'TextStagger'`: it can identify a backing component. Preserve the read-back identifiers and name.

For example, change the grouping and mute Blur on the previously identified application, preserving all other styles and properties. This is a separate `use_figma` call: replace `appliedId` with the literal id returned by the earlier call.

```js
const page = await figma.getNodeByIdAsync('0:1');
if (!page || page.type !== 'PAGE') throw new Error('Expected the inspected page');
await figma.setCurrentPageAsync(page);
const node = await figma.getNodeByIdAsync('123:456');
if (!node || node.type !== 'TEXT') throw new Error('Expected a text node');
const appliedId = '123:789'; // The identified application's id, not its styleId.
const existing = node.animationStyles.find((style) => style.id === appliedId);
if (!existing || existing.type !== 'FIGMA') {
  throw new Error('Expected the identified Figma text animation');
}
for (const segment of node.getStyledTextSegments(['fontName'])) {
  await figma.loadFontAsync(segment.fontName);
}
node.animationStyles = node.animationStyles.map((style) =>
  style.id === appliedId
    ? {
        ...style,
        props: {
          ...style.props,
          textDelayGrouping: 'CHARACTER_NO_WHITESPACE',
          blurVisible: false,
        },
      }
    : style,
);
return {
  mutatedNodeIds: [node.id],
  applied: node.animationStyles.find((style) => style.id === appliedId),
  timelines: node.timelines,
};
```

To remove Blur rather than mute it, set `blurEnabled: false`. To remove the entire identified text animation, call `node.removeAnimationStyle(appliedId)`. Preserve unrelated manual tracks and other applied animations.

A `type: 'CUSTOM'` binding points to a reusable style and does not expose editable `props` on the node. Do not convert it to a direct Figma preset or overwrite its definition as a side effect of a local text edit. The example above deliberately checks for a direct `FIGMA` application.
