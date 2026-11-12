# Effect Style API Patterns

> Part of the [use_figma skill](../SKILL.md). How to create, apply, and inspect effect styles using the Plugin API.
>
> For design system context (effect types, variable bindings on effects, gotchas), see [wwds-effect-styles](working-with-design-systems/wwds-effect-styles.md).

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

Use `$fig` to create styles and bind them to nodes in the same plan. Colors are **RGBA 0–1 range**.

```javascript
const style = $fig.effectStyle({
  name: "Elevation/200",
  effects: [{
    type: "DROP_SHADOW",
    color: { r: 0, g: 0, b: 0, a: 0.15 },
    offset: { x: 0, y: 4 },
    radius: 12,
    spread: 0,
    visible: true,
    blendMode: "NORMAL",
  }],
});
$fig.rectangle({ name: "Card", effects: style })
```
## Using Library Effect Styles by key (preferred)

A style found via a `search_design_system` `queries` entry with `entity: "style"` returns a `key`. Pass it directly into `$fig.getStyle(styleKey)` and apply via the `effects` property on any `$fig.rectangle(...)` / `$fig.frame(...)` / `$fig.query(...).set(...)` — the plan queues the library import automatically.

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
// `planStyle` from `$fig.effectStyle()` or `$fig.getStyle()`
// Bulk-apply an effect style to all nodes whose names contain `Card`
$fig.query('[name*=Card]').set({ effects: planStyle });

// Set an effect style on a specific node
$fig.get(NODE_ID).set({ effects: planStyle });
await $fig.done();
```
