---
name: figma-spec
description: "This skill is required to create, read, edit, review, or comment on Figma specs. You must read it when working on a PRD, brief, RFC or any kind of document in either a standalone Figma spec or a Figma spec embedded in a Figma Design or Figjam file."
disable-model-invocation: false
---

# Work with a Figma spec

You MUST always call `whoami` before using any `figma.spec.*` API and confirm that the target file’s plan (or the destination plan for a new file) has `specs_enabled: true`. `whoami` does not identify which plan owns a file. If the plan is unclear, you MUST ask the user; never infer it from the file key or another plan’s access. If `specs_enabled` is false or absent for that plan, explain that Specs is unavailable and stop the workflow.

A native Figma spec is GitHub-Flavored Markdown (GFM) under a `SPEC_BLOCK` node. A standalone Figma spec is just one spec; a FigJam or Design file can contain several embedded specs.

## Discover and choose the Figma spec

Resolve a supplied URL `node-id` when present with `figma.getNodeByIdAsync` and require `type === "SPEC_BLOCK"` plus `specBlockType === "DOCUMENT"`. Otherwise, search the current page with `findAllWithCriteria({ types: ['SPEC_BLOCK'] })`, filtering for `specBlockType === "DOCUMENT"` (and examine content with `figma.spec.getContent` if needed) until you find your target. If it's not on the current page, load other pages one at a time with `page.loadAsync()` and repeat your query, stopping once the target is resolved.

Pass the resolved root ID to every content call. Omit `specNodeId` only when the file is known to contain exactly one Figma spec; omission throws otherwise. Never edit ordinary canvas text nodes as a fallback.

## Create a Figma spec on a canvas

```js
// Creates an embedded Figma spec on a Design or FigJam canvas (not a standalone Figma spec file).
const { specNodeId } = await figma.spec.createOnCanvasAsync({
  title: 'Untitled spec',
  content: '# Title\n\nA paragraph.\n',
})

const specNode = await figma.getNodeByIdAsync(specNodeId)
if (!specNode) throw new Error('The created Figma spec could not be resolved')

const after = await figma.spec.getContent({ specNodeId })
if (!after.markdown.includes('A paragraph.')) {
  throw new Error('The new Figma spec content was not applied')
}
```

Always pass a non-empty `title` and a `content` string (`''` is allowed). `title` names the root; include any desired `# H1` in `content`.

## Content methods

```js
// READ — returns specNodeId, markdown, title, etc.
// The body is `markdown`, not `content`.
const before = await figma.spec.getContent({ specNodeId: chosenSpec.id })
const page = await figma.spec.getContent({
  specNodeId: before.specNodeId,
  offset: 100,
  maxLines: 50,
})

// REPLACE — clears + recreates the document; use only for an empty first draft.
await figma.spec.setContent({
  specNodeId: before.specNodeId,
  content: '# Title\n\nA paragraph.\n',
})

// EDIT — find/replace; each oldText must match exactly once.
await figma.spec.editContent({
  specNodeId: before.specNodeId,
  edits: [{ oldText: 'First paragraph.', newText: 'Edited first paragraph.' }],
})

const after = await figma.spec.getContent({ specNodeId: before.specNodeId })
if (!after.markdown.includes('Edited first paragraph.')) {
  throw new Error('The targeted Figma spec edit was not applied')
}
```

- Use **`getContent`** with the same `specNodeId` before edits and to verify writes; DON'T rely on screenshots.
- Default to multiplayer-safe, surgical **`editContent`**.
- Use destructive **`setContent`** only for an empty first draft or an explicit whole-document replacement.

## Critical rules

1. **`editContent` requires exactly one match.** Zero or multiple `oldText` matches fail without changes. Add surrounding context to make it unique.
2. **Pass Markdown as plain strings.** Never encode it with `Buffer`/base64 or decode it with `atob()`. Base64 is only for image data URLs inside Markdown.
3. **Keep Markdown and traversal separate.** `figma.spec.*` handles content; node traversal exposes only document roots and embedded-canvas branches.
4. **Preserve comment markers.** Keep overlapping `[comment:<uuid>]…[/comment:<uuid>]` pairs unchanged around the same text, or the thread may detach or disappear. When in doubt copy the marked span exactly and edit around it.
5. **Use portable references.** Shared Figma specs must use links such as GitHub permalinks, never machine-local paths or `localhost` URLs.

## Style

- Keep the title block first and formatted as H1, even when its text is empty. Never remove it or insert blocks before it.
- Prefer bold text in table header row.
- Use `<ins>` for underline, including combined formatting: `<ins>**bold and underlined**</ins>`. Do not use `<u>`, which only works in HTML imports.

## Images

Images use GFM image syntax inside `setContent` or `editContent`:

- `![alt](data:image/png;base64,...)` embeds bytes that are decoded and uploaded.
- `![alt](https://host/img.png)` is fetched server-side; disallowed hosts are rejected.

`getContent` emits image URLs as `https://<host>/spec/<fileKey>/image/<sha>?w=<width>&h=<height>`.

## Comments

Use `figma.spec.comments.*` for anchored threads. Prefer comments over leaving silent edits when you're unsure of a change.

```js
const comment = await figma.spec.comments.create({
  specNodeId: before.specNodeId,
  anchorText: 'the exact rendered text to anchor to', // MUST appear exactly once
  contextText: 'a longer unique substring containing anchorText', // optional; disambiguates repeats
  message: 'Comment body (markdown).',
})

const { root, replies, hasMore } = await figma.spec.comments.getThread({ uuid: comment.uuid })
await figma.spec.comments.reply({ uuid: comment.uuid, message: 'A reply.' })
```

- `anchorText` must match exactly once in the rendered Figma spec. Use a longer `contextText` containing it to disambiguate repeated text.
- `getThread` and `reply` require the root comment UUID surfaced by a `[comment:<uuid>]` marker; never pass a reply UUID to `reply`.
