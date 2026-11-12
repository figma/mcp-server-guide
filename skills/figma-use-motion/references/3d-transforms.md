# 3D transforms in motion

Use this reference for animated X/Y tilt, card flips, depth, or perspective. Load `figma-use` and `figma-use-motion`, then load `figma-3d-transforms` when available to establish the static scene, projection, and pivots before writing keyframes.

## Availability

If `node.transform3d` reads back `undefined`, the 3D transform capability isn't enabled in this environment. Don't silently produce nothing — tell the user 3D transforms aren't available here. `scene3d` exists only on FRAME, COMPONENT, and INSTANCE containers; `null` there means no scene is configured. An `undefined` `scene3d` on another node type does not indicate that 3D is unavailable.

If writing a 3D track throws `Unsupported keyframe field property`, 3D transforms aren't enabled in this environment. Tell the user rather than silently substituting a 2D approximation. Stop the unsupported operation instead of retrying, and preserve existing animation. Ordinary 2D keyframes remain available when motion is enabled without 3D.

## Keyframe fields

These fields use ordinary manual keyframe tracks with `FLOAT` values:

| Field | Unit | Notes |
|---|---|---|
| `TRANSFORM_3D_ROTATION_X` | degrees | Positive tilts the top edge away from the viewer. |
| `TRANSFORM_3D_ROTATION_Y` | degrees | Rotation about the vertical axis. |
| `TRANSFORM_3D_ROTATION_Z` | degrees | In-plane rotation after X and Y, matching the static 3D pose. |
| `TRANSFORM_3D_TRANSLATION_Z` | pixels | Depth; negative values are valid. |
| `SCENE_3D_PERSPECTIVE` | pixels | Nonnegative perspective on a FRAME, COMPONENT, or INSTANCE; values below 1 render as 1px. |

Use these exact names, including the `TRANSFORM_3D_` prefix. The rotations use degrees without the sign inversion of ordinary 2D `ROTATION`.

Establish a `FIXED_ORDER` pose before animating; imported `FREEFORM` transforms are not supported for 3D keyframing. Keyframe values are absolute: a 3D track replaces that `transform3d` field for the whole timeline, so start each track from the node's current value. A node posed at `rotateY: -46.5` makes one full turn with `-46.5 → 313.5`, and a card at `translateZ: 800` moves 300px toward the viewer and back with `800 → 1100 → 800`. Keep perspective on the container above the transformed object, following the static skill's scene rules.

For a two-sided card, turn each face 180° from its own pose with the same timing: front `0 → 180`, back `180 → 360`. Alternatively, animate a `preserve3d` container holding both faces `0 → 180`.

`backfaceVisible`, `visible`, `preserve3d`, and `transformOrigin` are static properties, not keyframe fields.

Perspective keyframes preserve their authored values, but distances from `0` to below `1px` render as `1px`, matching CSS. Animating toward zero keeps perspective active; it does not switch to an orthographic view. For a camera push, prefer distances comfortably above `1px` to avoid extreme distortion.

Static `scene3d.perspective: -1` disables perspective. The manual keyframe API still rejects negative `SCENE_3D_PERSPECTIVE` values, so do not write `-1` keyframes to disable it. For no perspective throughout an animation, use the static `-1` value without a perspective track.

`OPACITY` and effects keyframes or transition overrides and fading animation styles (Opacity, Fade, New, or Move/Rotate with `fade`) have no effect on a preserve-3D frame, because 3D rendering ignores them there; animate them on a flat ancestor as the 3D skill describes. Children can still take them but blend on their own, so overlaps show through.

## Add a turn to an existing pose

For a node with its static scene already configured, add a Y-axis half-turn over 0.6 seconds:

```javascript
const node = await figma.getNodeByIdAsync('123:456');
const pose = node.transform3d;
if (pose === undefined) {
  throw new Error('3D transforms are not available in this environment.');
}
if (pose.type === 'FREEFORM') {
  throw new Error('Set a FIXED_ORDER pose with figma-3d-transforms first.');
}
// A node with no 3D transform starts from 0.
const startY = pose.type === 'FIXED_ORDER' ? pose.rotateY : 0;
node.applyManualKeyframeTrack(
  { type: 'PROPERTY', name: 'TRANSFORM_3D_ROTATION_Y' },
  {
    keyframes: [
      { timelinePosition: 0, value: { type: 'FLOAT', value: startY } },
      {
        timelinePosition: 0.6,
        value: { type: 'FLOAT', value: startY + 180 },
        easing: { type: 'EASE_IN_AND_OUT' },
      },
    ],
  },
);
return { nodeId: node.id, tracks: node.manualKeyframeTracks };
```

This adds or replaces the Y rotation track without rewriting unrelated tracks. When editing an existing track, preserve its identity and keyframe IDs as described in [motion-patterns.md](motion-patterns.md#manual-keyframes).

Read back the tracks and follow the main motion skill's video verification guidance when the result is not self-evident. A screenshot only shows the resting state.
