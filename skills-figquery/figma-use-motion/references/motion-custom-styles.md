# Custom Animation Styles

Use this reference when a `use_figma` task discovers, creates, edits, organizes, applies, or removes a **local custom animation style** — a reusable, named motion style saved in the file.

Same Plugin API rules as the rest of this skill: top-level `await`, `return` for output, no `figma.closePlugin()` / `figma.notify()`, return every mutated node ID. Motion APIs might not be enabled for the calling user — see Runtime Gating in [figma-use-motion/SKILL.md](../SKILL.md).

## API Availability

Custom animation styles might not be enabled even when keyframes and first-party styles work. When unavailable, `figma.createCustomAnimationStyle()` and `figma.getLocalCustomAnimationStylesAsync()` throw `"not a supported API"`, `applyAnimationStyle(id, { type: 'CUSTOM' })` throws `Custom animation styles are not available`, and `node.animationStyles` **silently omits custom bindings**, so an empty read is not proof the node has no custom style applied. On any of these, **stop and explain the limitation**—do not automatically fall back to manual keyframes or a first-party style, because adding a fallback can stack a second animation on motion the agent cannot inspect. Get explicit user agreement before writing any fallback.

## Exposed Custom Animation API Surface

- `figma.getLocalCustomAnimationStylesAsync()` — local `CustomAnimationStyle` objects authored in this file. Prefer this over the deprecated sync `getLocalCustomAnimationStyles()`, which fails under dynamic-page document access.
- `figma.createCustomAnimationStyle()` — create a local custom style. `style.addAnimationEntryAsync(definitionStyleId, props)` / `style.removeAnimationEntry(entryId)` change its contents; `style.animationEntries` reads them back; `style.remove()` deletes the style.
- `figma.moveLocalCustomAnimationStyleAfter(target, reference)` / `figma.moveLocalCustomAnimationFolderAfter(targetPath, referencePath)` — order local custom styles and their slash-delimited folders.

**Two different things are called an "animation style".** `figma.motion.figmaAnimationStyles()` returns Figma's read-only first-party *definitions* (Fade, Move, …) — you can apply and configure them, but you cannot author new ones. A local `CustomAnimationStyle` is a reusable style saved in the file, and it is an ordered list of those first-party definitions. Both are applied through `applyAnimationStyle` / `node.animationStyles`, discriminated by `type: 'FIGMA'` vs `type: 'CUSTOM'`.

So when the user wants a brand-new *reusable, named* animation style, build it as a local custom animation style composed of first-party definitions. What remains out of scope is authoring `"figma:motion"` preset module source code: you cannot invent a new first-party definition or a motion primitive no definition provides. If the requested motion can't be expressed by composing definitions, use manual keyframes instead of fabricating a definition.

## Two Kinds Of "Animation Style"

| | First-party definition | Local custom style |
|---|---|---|
| Comes from | `figma.motion.figmaAnimationStyles()` | `figma.getLocalCustomAnimationStylesAsync()` |
| What it is | A read-only definition (Fade, Move, …) with advertised `props` | A `CustomAnimationStyle` object (`type: "CUSTOM_ANIMATION"`) holding an **ordered list of first-party definitions** |
| Authorable | No — you cannot write new definitions | Yes — create, rename, add/remove entries, delete |
| Applied as | `{ type: 'FIGMA', duration, timelineOffset, props }` | `{ type: 'CUSTOM', timelineOffset }` |

`node.animationStyles` returns both as a discriminated union. **Narrow on `type` before reading type-specific fields** — custom bindings expose `type`, `id`, `styleId`, `name`, and optional `timelineOffset`, and do *not* carry the Figma-only `duration` / `props`.

Custom styles do not nest. `addAnimationEntryAsync()` takes a first-party definition's `styleId`, never another custom style's `id`.

## Standard Workflow

1. **Discover before creating.** List local custom styles and reuse a match instead of adding a near-duplicate.
2. **Inspect the definitions** with `figma.motion.figmaAnimationStyles()` and read each one's advertised `props` before configuring an entry.
3. **Add entries in the intended order** — ordering is append-only (see [Editing a style's contents](#editing-a-styles-contents)).
4. **Apply to the target node** with `{ type: 'CUSTOM' }`.
5. **Read back both** the style's entries and the node binding.
6. **Extend the timeline** with `setTimelineDuration` if the applied motion now exceeds it.

## Discover And Inspect

Always use the async getter; the sync `getLocalCustomAnimationStyles()` is deprecated and fails under dynamic-page document access.

```js
const styles = await figma.getLocalCustomAnimationStylesAsync();

return styles.map((style) => ({
  id: style.id,
  name: style.name,
  type: style.type, // "CUSTOM_ANIMATION"
  entries: style.animationEntries.map((entry) => ({
    id: entry.id,
    name: entry.name,
    duration: entry.duration,
    props: entry.props,
  })),
}));
```

Match by `id` whenever the task already established one. Names are **not unique** — if a name match returns more than one style, disambiguate from entry contents and consumers rather than picking arbitrarily:

```js
const styles = await figma.getLocalCustomAnimationStylesAsync();
const matches = styles.filter((style) => style.name === "Gentle entrance");

return {
  matchCount: matches.length,
  consumers: matches.length === 1 ? await matches[0].getStyleConsumersAsync() : [],
};
```

## Create A Style

Create it, name it, then append first-party definitions in order. The second argument to `addAnimationEntryAsync` is the **entry's props object** — `duration` and easing live *inside* it. This differs from applying a Figma style directly to a node, where `duration` is a top-level field.

```js
const defs = figma.motion.figmaAnimationStyles();
const fadeDef = defs.find((def) => def.styleId === "Opacity");

if (!fadeDef) {
  throw new Error("Could not find the Fade animation definition.");
}

const style = figma.createCustomAnimationStyle();

try {
  style.name = "Gentle entrance";
  await style.addAnimationEntryAsync(fadeDef.styleId, {
    duration: 0.4,
    easing: { type: "EASE_OUT" },
    // Only properties advertised by fadeDef.props.
  });
} catch (error) {
  style.remove(); // Don't leave an orphan empty style behind.
  throw error;
}

return {
  styleId: style.id,
  entries: style.animationEntries,
};
```

A returned entry's `styleId` identifies the generated entry, **not** the source definition. Never feed `entry.styleId` back into `addAnimationEntryAsync` to duplicate an entry — rediscover the definition from `figma.motion.figmaAnimationStyles()` instead.

## Apply A Style

Pass the custom style's `id` plus the `CUSTOM` discriminator. A custom style carries its own timing, so `timelineOffset` is the only thing configurable at application time.

```js
const node = await figma.getNodeByIdAsync("123:456");
const styles = await figma.getLocalCustomAnimationStylesAsync();
const style = styles.find((candidate) => candidate.id === "S:abc,");
const mutatedNodeIds = [node.id];

if (!style) {
  throw new Error("Could not find the requested custom animation style.");
}

const bindingId = node.applyAnimationStyle(style.id, {
  type: "CUSTOM",
  timelineOffset: 0.25,
});

const [timeline] = node.timelines;
const requiredDuration = 0.25 + 0.4; // offset + the style's own motion length
if (timeline && timeline.duration < requiredDuration) {
  node.setTimelineDuration(timeline.id, requiredDuration);
  mutatedNodeIds.push(timeline.id);
}

return {
  mutatedNodeIds,
  bindingId,
  animationStyles: node.animationStyles,
};
```

Two things to keep straight:

- The returned `bindingId` identifies **this application on this node**; it is not `style.id`. Keep it if the task will later edit or remove that specific application.
- Do **not** pass `duration` or `props` alongside `type: 'CUSTOM'`. The input schema is strict, so those fields are rejected rather than silently dropped.

## Read, Edit, Or Remove An Application

```js
const node = await figma.getNodeByIdAsync("123:456");

return {
  custom: node.animationStyles.filter((applied) => applied.type === "CUSTOM"),
  figma: node.animationStyles.filter((applied) => applied.type === "FIGMA"),
};
```

Remove one application by its binding id:

```js
const node = await figma.getNodeByIdAsync("123:456");
node.removeAnimationStyle(bindingId);

return { mutatedNodeIds: [node.id], animationStyles: node.animationStyles };
```

For batch edits, write the **complete desired array** and preserve unrelated bindings. A custom input needs `type: 'CUSTOM'` and `styleId`; include the existing binding `id` to update that application in place:

```js
const node = await figma.getNodeByIdAsync("123:456");

node.animationStyles = node.animationStyles.map((applied) =>
  applied.type === "CUSTOM" && applied.id === bindingId
    ? { type: "CUSTOM", id: applied.id, styleId: applied.styleId, timelineOffset: 0.5 }
    : applied,
);

return { mutatedNodeIds: [node.id], animationStyles: node.animationStyles };
```

- Omitting an existing binding **removes** it; writing `[]` clears both custom and Figma styles.
- To swap the underlying style while keeping the same binding, keep `id` and change `styleId`.
- Don't use an array write to reorder applications — matched entries update in place and new ones append.

## Editing A Style's Contents

`style.name` is writable. `style.animationEntries` and the entry fields are read-only, so content changes go through:

- `await style.addAnimationEntryAsync(def.styleId, props)` — append an entry.
- `style.removeAnimationEntry(entry.id)` — remove an entry.
- `style.remove()` — delete the reusable style itself. Only when the user asked for that; it affects every consumer.

There is no in-place entry update and no reorder — removing and re-adding appends to the end. When exact order must change, rebuild the entries in order only after mapping every existing entry back to an available first-party definition *and* preserving its configured props. If that mapping is ambiguous, stop and ask rather than silently substituting a different animation.

Entries can only be added to or removed from **local** styles; mutating a remote (library) style throws `Cannot add animation entries to a remote style`.

## Organize Local Styles

Slash-delimited names create folders:

```js
style.name = "Motion/Entrances/Gentle entrance";
```

Reorder only when the user asks for library organization. Target and reference must both be local custom animation styles in the same folder; pass `null` as the reference to move the target first.

```js
figma.moveLocalCustomAnimationStyleAfter(targetStyle, referenceStyle);
```

Folders reorder the same way, by full slash-delimited path, and must share a parent:

```js
figma.moveLocalCustomAnimationFolderAfter("Motion/Entrances", "Motion/Exits");
```

## Verification

- [ ] Custom-style work listed existing local styles via `figma.getLocalCustomAnimationStylesAsync()` before creating another, and matched by `id` rather than by non-unique `name`.
- [ ] Custom styles are applied with `{ type: 'CUSTOM' }` and at most a `timelineOffset`; `duration` and `props` are rejected on a custom binding, not ignored.
- [ ] Custom-style verification read back *both* the style's `animationEntries` and the node binding (`type: 'CUSTOM'` with the expected `styleId`) — one can succeed while the other silently didn't.

Verify the reusable definition and its application **separately** — one can succeed while the other silently didn't.

```js
const node = await figma.getNodeByIdAsync("123:456");
const styles = await figma.getLocalCustomAnimationStylesAsync();
const style = styles.find((candidate) => candidate.id === styleId);
const applied = node.animationStyles.find((candidate) => candidate.id === bindingId);

return {
  style: style && { id: style.id, name: style.name, entries: style.animationEntries },
  applied,
  timelines: node.timelines,
};
```

Treat it as verified only when all of these hold:

- the style exists with the expected ordered entries and props;
- the node binding has `type: 'CUSTOM'` and the expected `styleId`;
- its `timelineOffset` is what you wrote; and
- the containing timeline is long enough for the resulting motion.
