# Ring / 3D carousel

Arrange three or more items around a circle, each facing outward. On one node, `translateZ` moves along the parent's Z axis, regardless of that node's rotation. Instead, rotate a transparent preserve-3D slot and push its child outward with `translateZ`.

Use a transparent, unclipped frame for the ring, with manual positioning. Every item and slot must share the ring's centre. Put the ring inside a scene frame (FRAME, COMPONENT or INSTANCE); if it is on a page or inside a group, add a scene frame first. Keep a filled background on that outer scene, with `preserve3d: false`, so the rear cards don't intersect its fill.

The example assumes `ring` is a frame containing only the items to arrange and `scene` is its parent scene frame. For existing artwork, reuse the item nodes and preserve their descendants. The example sets a new scene's perspective to `-1` (none); choose a positive distance only when the main skill's perspective decision rules call for it, and preserve the existing projection when editing an established scene.

```javascript
const items = [...ring.children];
const perspective = -1; // Use the projection chosen by the main skill's decision rules.
scene.scene3d = { perspective, preserve3d: false };
ring.layoutMode = 'NONE';
ring.fills = [];
ring.clipsContent = false;
ring.transformOrigin = {
  x: { unit: 'PERCENT', value: 50 },
  y: { unit: 'PERCENT', value: 50 },
};
ring.scene3d = { perspective: -1, preserve3d: true };
const radius = 300; // Choose at least maxItemWidth / (2 * Math.tan(Math.PI / items.length)).
items.forEach((item, i) => {
  const slot = figma.createFrame();
  slot.name = `Slot ${i + 1}`;
  slot.fills = [];
  slot.clipsContent = false;
  slot.resize(item.width, item.height);
  ring.appendChild(slot);
  slot.x = (ring.width - slot.width) / 2;
  slot.y = (ring.height - slot.height) / 2;
  slot.appendChild(item);
  item.rotation = 0;
  item.x = 0;
  item.y = 0;
  item.transformOrigin = {
    x: { unit: 'PERCENT', value: 50 },
    y: { unit: 'PERCENT', value: 50 },
  };
  slot.scene3d = { perspective: -1, preserve3d: true };
  slot.transform3d = { type: 'FIXED_ORDER', translateZ: 0, rotateX: 0, rotateY: (360 / items.length) * i, rotateZ: 0 };
  item.transform3d = { type: 'FIXED_ORDER', translateZ: radius, rotateX: 0, rotateY: 0, rotateZ: 0 };
});
```

To turn the whole carousel, rotate `ring` (rotateY), not the items. Keep perspective on `scene`, one layer above the ring's transform.

Verify that the item centres lie on a radius-`radius` circle in the XZ plane and the faces point outward. Inspect a second whole-ring orientation to check that the slots share a pivot and the rear cards remain visible where unobstructed.
