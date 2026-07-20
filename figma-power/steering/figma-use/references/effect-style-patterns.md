# Effect Style API Patterns

> Part of the [use_figma skill](../../figma-use.md). How to create, apply, and inspect effect styles using the Plugin API.
>
> For design system context (effect types, variable bindings on effects, gotchas), see [wwds-effect-styles](working-with-design-systems/wwds-effect-styles.md).

## Prefer `$fig` for creation + binding

For new effect styles + binding them to nodes, reach for `$fig` first — the style and the binding go in the same plan, and the binding uses the natural `effects` property (no `*StyleId` suffix):

```javascript
const shadow = $fig.effectStyle({
  name: "Shadow/Soft",
  effects: [{
    type: "DROP_SHADOW",
    color: { r: 0, g: 0, b: 0, a: 0.3 },
    offset: { x: 0, y: 4 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: "NORMAL",
  }],
})
$fig.rectangle({ name: "Card", effects: shadow })
```

See [fig-builder.md](fig-builder.md#styles---create-reference-apply) for the full surface.

The raw Plugin API patterns below are the fallback for when you genuinely need to interleave style ops with mid-script async calls or read computed properties off the live `EffectStyle` before deciding what to do next.

## Contents

- Listing Effect Styles
- Creating a Drop Shadow Style
- Importing Library Effect Styles
- Applying Effect Styles to Nodes

## Listing Effect Styles

```javascript
/**
 * Lists all local effect styles.
 *
 * @returns {Promise<Array<{id: string, name: string, key: string, effectCount: number}>>}
 */
async function listEffectStyles() {
  const styles = await figma.getLocalEffectStylesAsync();
  return styles.map(s => ({
    id: s.id,
    name: s.name,
    key: s.key,
    effectCount: s.effects.length
  }));
}
```

Full runnable script:

```javascript
const results = await listEffectStyles();
return results;
```

## Creating a Drop Shadow Style

Colors are **RGBA 0–1 range**. `effects` is a read-only array — always reassign, never mutate in place.

```javascript
/**
 * Creates a drop shadow effect style.
 *
 * @param {string} name - e.g. "Elevation/200"
 * @param {{ r: number, g: number, b: number, a: number }} color - RGBA, 0-1 range
 * @param {{ x: number, y: number }} offset
 * @param {number} radius - blur radius
 * @param {number} [spread=0]
 * @returns {EffectStyle}
 */
function createDropShadowStyle(name, color, offset, radius, spread) {
  const style = figma.createEffectStyle();
  style.name = name;
  style.effects = [{
    type: "DROP_SHADOW",
    color,
    offset,
    radius,
    spread: spread || 0,
    visible: true,
    blendMode: "NORMAL"
  }];
  return style;
}
```

Full runnable script:

```javascript
const style = createDropShadowStyle(
  "Elevation/200",
  { r: 0, g: 0, b: 0, a: 0.15 },
  { x: 0, y: 4 },
  12,
  0
);
return { id: style.id, name: style.name };
```

## Using Library Effect Styles by key (preferred)

`search_design_system` with `includeStyles: true` returns a `key` per style. Pass it directly into `$fig.getStyle(styleKey)` and apply via the `effects` property on any `$fig.rectangle(...)` / `$fig.frame(...)` / `$fig.query(...).set(...)` — the plan queues the library import automatically.

```javascript
const shadow = $fig.getStyle(ELEVATION_200_KEY)
$fig.frame({ name: 'Card', effects: shadow })

// Bulk apply
$fig.query('FRAME[name=Card]').set({ effects: shadow })
```

Prefer reusing library effect styles over creating new ones.

### Raw-API fallback

```javascript
// If you need the imported EffectStyle's metadata mid-script
const shadowStyle = await figma.importStyleByKeyAsync("EFFECT_STYLE_KEY");
node.effectStyleId = shadowStyle.id;
```

## Applying Effect Styles to Nodes

```javascript
/**
 * Applies an effect style to all nodes on the current page that match a given name pattern.
 *
 * @param {string} styleId - The ID of an EffectStyle.
 * @param {string} nodeNamePattern - Substring match against node names.
 * @returns {number} - Number of nodes the style was applied to.
 */
function applyEffectStyleToMatchingNodes(styleId, nodeNamePattern) {
  const nodes = figma.currentPage.findAll(n => n.name.includes(nodeNamePattern));
  let applied = 0;
  for (const node of nodes) {
    if ('effectStyleId' in node) {
      node.effectStyleId = styleId;
      applied++;
    }
  }
  return applied;
}
```

Full runnable script:

```javascript
const applied = applyEffectStyleToMatchingNodes('STYLE_ID', 'Card');
return { applied };
```
