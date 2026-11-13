---
name: figma-3d-transforms
disable-model-invocation: false
description: 'Add or edit 3D transforms — depth, perspective, z-axis rotation, tilt, isometric, and parallax looks that flat 2D rotation cannot express. Use whenever a request reaches into the third dimension — "make it 3D", "add depth/perspective", "tilt/rotate it back", "z-plane", "isometric", "flip it like a card", "parallax", "vanishing point", "receding into the distance", "make it pop out".'
---

# Adding / editing 3D transforms

Use this skill when a request needs the third dimension and plain 2D rotation can't express it: perspective, depth, z-axis tilt, isometric layouts, card flips, parallax stacks, "make it pop out of the screen."

Not this skill:
- Flat, in-plane rotation → set the node's 2D `rotation` instead; there's nothing 3D about it.

## Animating 3D transforms

A request may implicitly be a motion task. Assume it isn't unless the context suggests otherwise, the language describes a quality of movement ("smoothly flips", "gently sways"), or the field being changed is already keyframed. These are pointers; use the context you have. For a motion task, set the pose with this skill and keyframe it with `figma-use-motion`; don't deliver static poses or "state" frames in place of an animation.

Keyframes override static 3D fields during playback, so before changing a node's `transform3d` or a container's `scene3d.perspective`, use `use_figma` to read `manualKeyframeTracks` and `animationStyles` on the node whose field you change. Edit keyframes on the fields being changed; other tracks (e.g. opacity) don't require animating the pose. If `manualKeyframeTracks` is `undefined`, Motion is unavailable: make static edits, and tell the user animation isn't available if the request needs it.

## Runtime

Load `figma-use` before calling `use_figma` and follow its file context, node-creation, output, and verification rules. Include both skill names in `skillNames`, prefixing each with `resource:` when loaded through MCP resources. The recipes illustrate raw Plugin API geometry; adapt node creation to the workflow required by `figma-use` and apply poses after that workflow has materialized the nodes. Execute the Plugin API examples in the target file with `use_figma`.

3D APIs depend on the calling user's feature availability. If `transform3d` is unavailable, stop and explain that 3D transforms are not enabled in this session. Do not retry unsupported APIs or substitute a flat illustration without the user's agreement.

## User-facing language
- Talk in plain terms: "adding perspective", "tilting it back", "giving the scene depth". Don't name these fields or the plugin API to the user, and don't surface raw error text.
- Give brief progress updates ("Setting up the 3D scene…", "Tilting the cards…", "Checking the result…").
- For ambiguous styling, make a tasteful change; for ambiguous perspective, follow the decision rules below.

## The three fields

| Field | Lives on | Role |
|---|---|---|
| `node.transform3d` | any node | the per-element 3D pose |
| `node.scene3d` | FRAME / COMPONENT / INSTANCE only | a shared 3D space for the container's children |
| `node.transformOrigin` | any node | the pivot point the pose rotates around |

### transform3d — the per-element pose
Write shape: `{ type: 'FIXED_ORDER', translateZ, rotateX, rotateY, rotateZ, backfaceVisible?, visible? }`
- `translateZ` and all three `rotate*` are **required** on write; `backfaceVisible` and `visible` are optional and default to `true`.
- **There is no per-element `perspective`** — it is not part of this shape, and passing it throws. All perspective lives on the container via `scene3d`.
- Rotations are in **degrees**. The fields compose like CSS `transform: translateZ() rotateX() rotateY() rotateZ()`: the node is rotated first (Z, then Y, then X) and `translateZ` is applied last, along the **parent's** Z axis, not the direction the node faces. So a rotation plus `translateZ` on one node never pushes it out along its rotated normal; for that, rotate a wrapper instead (see the [carousel recipe](references/carousels.md)).
- **There is no X or Y translation** — `transform3d` only translates along Z. To move a node horizontally or vertically, set the node's own position (`node.x` / `node.y`); don't reach for a transform. So a scene of several children at different X/Y spots is built by positioning each node, then applying `transform3d` for depth/rotation on top.
- Assigning `transform3d` **replaces the entire object** — omitting `backfaceVisible` or `visible` resets them to `true`. To change one axis, read the current value, spread it, and write the whole object back.
- `{ type: 'NONE' }` clears the 3D transform.
- The write is strict — extra keys are rejected.
- Reads may return `type: 'FREEFORM'` on nodes imported from CSS / `matrix3d`. FREEFORM is **read-only**: you can detect it but cannot author it. Write a `FIXED_ORDER` object instead (it overwrites the freeform one).

### scene3d — the shared 3D space (containers only)
Write shape: `{ perspective, preserve3d, visible? }` on a FRAME / COMPONENT / INSTANCE.
- `perspective` and `preserve3d` are both **required** on write; `visible` is optional and defaults to `true`.
- `preserve3d: true` = children share one 3D space and can overlap in depth (like CSS `preserve-3d`). `preserve3d: false` (the default — a container opts in) = children are projected flat onto the container's plane.
- Reads return `null` when unconfigured — and an all-default scene reads back as `null`, so don't treat `null` as an error.
- Writing `null`/`undefined` clears it. On an INSTANCE, that opts the instance out of the backing component's scene.

### transformOrigin — the pivot
Write shape: `{ x: { unit, value }, y: { unit, value } }`, where `unit` is `'PERCENT'` (50 = center) or `'PIXELS'`.
- Defaults to centered (50% / 50%); reads return that default when unset. There is no way to reset it back to "unset" through the API.

## Setting perspective
Decide before posing the scene, in this order:
1. Honor an explicit projection choice: perspective → a positive distance; orthographic / isometric / "no perspective" → `-1`, even for a single-axis tilt.
2. Automatically add perspective for language implying **physical space**, **real depth**, or **going into / popping out of the screen**. Don't ask again.
3. Also automatically add perspective when **only one node receives only an X or Y rotation**. Without it, a flat node only foreshortens and the depth direction is hard to see.
4. For other new 3D requests, briefly ask whether to add perspective. Until confirmed, default to **no perspective**; "make it 3D" or "make a cube" alone does not authorize it. If asked to continue without an answer, proceed with no perspective. Preserve an existing projection when merely editing an established scene unless the user requests a change.

For perspective, start at least around 80% of the longest object/scene dimension; use larger distances for a subtler look. Tiny distances can make geometry explode toward the camera. For no perspective, use `perspective: -1`. Any negative distance means none; `0` and positive distances below `1px` render as `1px`. Preserve authored distances in storage rather than rewriting them to the rendering minimum. A full six-face cube needs `preserve3d: true`; a three-face isometric cube uses independently posed faces in a flat container. See [cube recipes](references/cubes.md) for both constructions.

**Perspective always lives on the container.** `scene3d.perspective` is the only perspective the API exposes; elements themselves only carry rotation and `translateZ`. So a single tilted object and a whole fan of cards are built the same way: `scene3d` on the parent, `transform3d` on the child / children. One shared vanishing point is what makes a group read as a single coherent space.

### Filled parent? Isolate the 3D children (do this by default)
Whenever 3D-rotated children sit inside a container that has a **fill**, do NOT place them directly in it. With `scene3d.preserve3d: true` on that container the children share its 3D space, so their rotated geometry cuts *through* its fill plane — visible clipping. Structure the scene like this instead:
- Leave the **filled parent** container at `scene3d.preserve3d: false`. It still carries the `perspective` — perspective projects the subtree whether or not the container preserves 3D.
- Wrap the 3D children in an **intermediate frame** set to `scene3d.preserve3d: true`, and put the rotated children in that wrapper.

The wrapper keeps the children's shared 3D space and composites flat onto the parent's fill instead of intersecting it.

### Never put `scene3d` perspective and `transform3d` on the same layer
Keep the perspective one layer above the thing being transformed: the outer container holds `scene3d` (the perspective), an **intermediate frame** carries the `transform3d`, and the actual children sit inside that frame. If a node has both a `scene3d` perspective *and* its own `transform3d`, the perspective gets baked into the children *before* they're transformed — a cube then renders as a **frustum**.

## Interpreting the ask
Common phrasings and the transform they usually mean (signs matter — getting them backwards tilts things the wrong way):
- "tilt it back" / "lean it back" (top edge recedes from the viewer) → **positive** `rotateX`. "Tilt forward" / "toward me" → **negative** `rotateX`.
- "turn/spin it to the side" / "swivel" → `rotateY` (rotation about the vertical axis).
- "parallax" / "layered depth" → several elements at different `translateZ` inside one `scene3d` container (not a single object). Larger `translateZ` gaps = stronger parallax.
- Anything that **hinges around an edge or corner** rather than spinning in place — "open like a door", "open like a book / pages", "fan out like petals", "unfold", "swing open" — is a `transformOrigin` job. Move the pivot to the hinge (e.g. a door → `x: 0% / y: 50%` for the left edge; book pages → the shared spine; petals/fan → the common base point), *then* apply the rotation. Leaving `transformOrigin` centered makes it rotate about the middle, which reads as spinning rather than hinging.
- Leave `backfaceVisible` **on** (the default) for ordinary tilted elements. Set it `false` for distinct front/back designs or the outward-facing surfaces of a solid cube (see the cube recipes); don't hide a normal card just because it turns past 90°.

## Workflow
1. Make any static (non-3D) design changes first; don't create or delete nodes unless the user asked.
2. Work through the decisions under *Setting perspective*: perspective vs. orthographic, then which container carries the `scene3d.perspective`.
3. Apply the appropriate rotation or translateZ via `transform3d`.
4. Set `transformOrigin` only if the pivot should be off-center.
5. Check work: read back `node.transform3d` / `node.scene3d` to confirm the values **and** export an image to confirm the pose actually *looks* right — a wrong rotation sign reads back fine but renders backwards.

## Recipes

**One element with depth** — the perspective goes on its parent container, the rotation on the element:
```javascript
const container = await figma.getNodeByIdAsync('123:456'); // a FRAME
const node = container.children[0];
container.scene3d = { perspective: 600, preserve3d: true };
node.transform3d = { type: 'FIXED_ORDER', translateZ: 0, rotateX: 0, rotateY: 20, rotateZ: 0 };
```

**A coherent scene / several elements sharing depth, when perspective is selected** (a fan of cards, a stack of cards at different depths) — one container and many children. Use `perspective: -1` if perspective hasn't been requested or confirmed:
```javascript
const container = await figma.getNodeByIdAsync('123:456'); // a FRAME
container.scene3d = { perspective: 800, preserve3d: true };
for (let i = 0; i < container.children.length; i++) {
  const child = container.children[i];
  child.transform3d = { type: 'FIXED_ORDER', translateZ: 10 * i, rotateX: 0, rotateY: 25 * i, rotateZ: 0 };
}
```

**Ring / 3D carousel** — follow the [carousel recipe](references/carousels.md). Rotate a transparent preserve-3D slot for each item, and apply only `translateZ` to the item inside it. Keep perspective on the scene above the ring and follow the perspective decision rules above.

**Isometric cube** — follow the [three-face isometric recipe](references/cubes.md#isometric-cube). Use exactly three square nodes with their own 3D poses in a transparent, flat frame/group. Use `perspective: -1` for no perspective and place the viewing rotations on the faces.

**Full six-face cube or arranging six selected faces** — follow the [six-face assembly recipe](references/cubes.md#assemble-six-square-faces). Assemble perpendicular faces in a transparent preserve-3D frame, then rotate that frame to choose a view. Preserve the selected faces' artwork and descendants; their names may change.

**Card flip / two-sided** — rotate past 90° and hide the backface so the reverse doesn't show through:
```javascript
frontFace.transform3d = { type: 'FIXED_ORDER', translateZ: 0, rotateX: 0, rotateY: 0, rotateZ: 0, backfaceVisible: false };
backFace.transform3d = { type: 'FIXED_ORDER', translateZ: 0, rotateX: 0, rotateY: 180, rotateZ: 0, backfaceVisible: false };
```

## Gotchas
- **Opacity, blend mode, effects and clipping don't render on a preserve-3D frame itself** (the editor disables them,
  and the API rejects them). Its children can still take them, unless they're preserve-3D frames too, but each child
  then blends on its own, so overlapping children show through each other rather than fading as one group. To fade
  the group, put them on an ancestor with `preserve3d: false` instead, keeping the existing hierarchy where you can:
  - If the frame holding the perspective has `preserve3d: false` and contains only what's being faded, apply them to it, or to a wrapper around it.
  - Otherwise, wrap just the faded content in a new transparent frame (`fills = []`) at `x = 0, y = 0` inside the
    frame holding the perspective, with that frame's width
    and height, and `scene3d = { ...frame.scene3d, preserve3d: false }`. The original keeps its perspective for the
    rest. The vanishing point stays put if the original uses the default centred perspective origin; a custom origin
    can't be copied through the API. If that frame uses auto layout, the wrapper needs
    `layoutPositioning = 'ABSOLUTE'`, which takes its content out of the flow, so only do this when the layout doesn't
    depend on that content; otherwise apply them to each child.
  - Also apply them to each child if the faded content must depth-sort with other 3D content.
- `scene3d` exists only on FRAME / COMPONENT / INSTANCE — reading or writing it on other node types does nothing useful.
- Assigning `transform3d` or `scene3d` replaces the whole object; spread the current value when editing a single field.
- A lone X/Y tilt without perspective only foreshortens; apply the perspective decision rules, not a blanket "all 3D needs perspective" rule.
- Rotations are degrees, not radians.
- If `node.transform3d` reads back `undefined`, the 3D transform capability isn't enabled in this environment. Don't silently produce nothing — tell the user 3D transforms aren't available here. `scene3d` exists only on FRAME, COMPONENT, and INSTANCE containers; `null` there means no scene is configured. An `undefined` `scene3d` on another node type does not indicate that 3D is unavailable.
- Clipping / two objects intersecting or bleeding into each other in a 3D scene is usually a depth-sorting issue. `translateZ` drives the depth order, so nudge one object's `translateZ` outward (toward the viewer) to lift it cleanly above the other. (For a child clipping into its *filled parent*, see "Filled parent? Isolate the 3D children" above.)
- `visible` should be left on for most cases, this is only turned off when the user explicitly wants to hide that `transform3d` or `scene3d` effect temporarily (rare).
- Don't grep the plugin API docs for 3D transforms — use this skill; the shapes above are the full surface.
