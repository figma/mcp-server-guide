# Cube recipes

Choose the construction from the request: an isometric cube uses exactly three independently posed square faces; a six-sided cube or six selected faces uses a full preserve-3D assembly. Both use exact positions and rotations, not visual adjustment by trial and error.

## Assemble six square faces

Use six equally sized square nodes. For existing faces, preserve their content and fills, assign them to the named roles below, and reset their old poses and pivots. Do not create replacement faces when asked to arrange existing ones.

For side length `faceSize` and `halfSize = faceSize / 2`, the cube frame is `faceSize × faceSize`, with its volume centered at `(halfSize, halfSize, 0)`. Every face has a centered pivot and zero ordinary 2D `rotation`:

| Face | x | y | translateZ | rotateX | rotateY | Outward normal |
|---|---|---|---|---|---|---|
| front | 0 | 0 | +halfSize | 0 | 0 | +Z |
| back | 0 | 0 | -halfSize | 0 | 180 | -Z |
| right | +halfSize | 0 | 0 | 0 | 90 | +X |
| left | -halfSize | 0 | 0 | 0 | -90 | -X |
| top | 0 | -halfSize | 0 | 90 | 0 | -Y |
| bottom | 0 | +halfSize | 0 | -90 | 0 | +Y |

`rotateZ` is zero for every face. Position the face centers using `x`/`y`; `translateZ` is along the shared scene's Z axis, not the face's rotated normal.

The code assumes `faces` maps the six role names to existing nodes and `parent` is an appropriate scene container (use the main skill's filled-parent isolation rule). For a new cube, create and style six squares first; for an existing cube frame, reuse it instead of creating another.

```javascript
const faceSize = faces.front.width;
const faceNodes = Object.values(faces);
if (faceSize <= 0 || faceNodes.some(face => face.width !== faceSize || face.height !== faceSize)) {
  throw new Error('Cube faces must be equally sized squares');
}
const halfSize = faceSize / 2;
const pose = overrides => ({
  type: 'FIXED_ORDER', translateZ: 0, rotateX: 0, rotateY: 0, rotateZ: 0,
  ...overrides,
});
const placements = {
  front: [0, 0, halfSize, 0, 0],
  back: [0, 0, -halfSize, 0, 180],
  right: [halfSize, 0, 0, 0, 90],
  left: [-halfSize, 0, 0, 0, -90],
  top: [0, -halfSize, 0, 90, 0],
  bottom: [0, halfSize, 0, -90, 0],
};
const cube = figma.createFrame();
parent.appendChild(cube);
cube.name = 'Cube';
cube.resize(faceSize, faceSize);
cube.layoutMode = 'NONE';
cube.fills = [];
cube.clipsContent = false;
cube.scene3d = { perspective: -1, preserve3d: true };
for (const [name, face] of Object.entries(faces)) {
  const [positionX, positionY, translateZ, rotateX, rotateY] = placements[name];
  cube.appendChild(face);
  face.rotation = 0;
  face.transformOrigin = {
    x: { unit: 'PERCENT', value: 50 },
    y: { unit: 'PERCENT', value: 50 },
  };
  face.x = positionX;
  face.y = positionY;
  face.transform3d = pose({ translateZ, rotateX, rotateY, backfaceVisible: false });
}
```

For a solid, opaque cube, hiding backfaces avoids drawing inward-facing surfaces. If the user wants an open or transparent cube, keep backfaces visible instead.

## Isometric cube

Use exactly three equally sized squares: front, left, and a top or bottom cap. Pose each face independently in a transparent frame/group with no preserve-3D, no X/Y rotation on its containers, and no perspective (`perspective: -1`) on every ancestor. Keep each face's ordinary 2D rotation zero, its transform origin centered, and its `translateZ` zero.

Let `tilt = atan(1 / sqrt(2))` in degrees, `horizontal = faceSize / (2 * sqrt(2))`, and `vertical = faceSize * sqrt(3 / 8)`. Choose `viewSign = -1` for the top view (default) or `+1` for the bottom view:

| Face | x offset from cap | y offset from cap | rotateX | rotateY | rotateZ |
|---|---|---|---|---|---|
| front | +horizontal | -viewSign × vertical | viewSign × tilt | 45 | 0 |
| left | -horizontal | -viewSign × vertical | viewSign × tilt | -45 | 0 |
| cap | 0 | 0 | viewSign × (tilt - 90) | 0 | viewSign × 45 |

These are offsets between equally sized faces' positions (and therefore also their centers). All three projected edges join exactly. Compute the angles from the expressions above; rounding `tilt` to 35.264 degrees introduces an avoidable gap.

The code assumes `parent` is a flat scene container, `faceSize` is the desired square width, and `viewSign` is either -1 or +1. It creates the three faces. Set `faceColors.front`, `faceColors.left`, and `faceColors.cap` to RGB colors from the user's requested palette or the existing design; use lighter and darker shades to distinguish the faces:

```javascript
const tilt = Math.atan(1 / Math.SQRT2) * 180 / Math.PI;
const horizontal = faceSize / (2 * Math.SQRT2);
const vertical = -viewSign * faceSize * Math.sqrt(3 / 8);
// Shift the three faces together so the projected cube fits its frame exactly.
const capX = faceSize * (1 / Math.SQRT2 - 1 / 2);
const capY = faceSize * ((2 + viewSign) / Math.sqrt(6) - 1 / 2);
const cube = figma.createFrame();
parent.appendChild(cube);
cube.name = 'Isometric cube';
cube.resize(faceSize * Math.SQRT2, faceSize * Math.sqrt(8 / 3));
cube.layoutMode = 'NONE';
cube.fills = [];
cube.clipsContent = false;
cube.scene3d = { perspective: -1, preserve3d: false };
const placements = [
  ['Front', horizontal, vertical, viewSign * tilt, 45, 0, faceColors.front],
  ['Left', -horizontal, vertical, viewSign * tilt, -45, 0, faceColors.left],
  [viewSign === -1 ? 'Top' : 'Bottom', 0, 0, viewSign * (tilt - 90), 0, viewSign * 45,
    faceColors.cap],
];
for (const [name, x, y, rotateX, rotateY, rotateZ, color] of placements) {
  const face = figma.createRectangle();
  cube.appendChild(face);
  face.name = name;
  face.resize(faceSize, faceSize);
  face.x = capX + x;
  face.y = capY + y;
  face.transformOrigin = {
    x: { unit: 'PERCENT', value: 50 },
    y: { unit: 'PERCENT', value: 50 },
  };
  face.fills = [{ type: 'SOLID', color }];
  face.transform3d = {
    type: 'FIXED_ORDER', translateZ: 0, rotateX, rotateY, rotateZ,
  };
}
```

Position the cube and shift all three faces by the same X/Y offset as needed. Keep their relative offsets and poses unchanged. The top and bottom views are complete alternatives; do not mix their signs or add hidden fourth, fifth, or sixth faces.

## Viewing a full six-face cube

Use the six-face assembly above for a six-sided cube or six selected faces. Choose a visible whole-cube pose on its preserve-3D frame, for example `rotateX: -Math.atan(1 / Math.SQRT2) * 180 / Math.PI, rotateY: 45`. This remains a six-face assembly even though only three faces are visible from that view.

For a perspective cube, put the positive perspective distance on **parent**, never on the cube frame. Follow the main skill's perspective decision rules; geometry alone does not require perspective.

For a six-face cube, verify all eight corners are shared by three faces, adjacent face normals are perpendicular, and every normal points outward. Inspect a front view and a second whole-cube orientation; faces must still join without gaps or intersections. For the independent isometric recipe, verify the three poses and relative offsets above, then inspect the image for clean shared edges.
