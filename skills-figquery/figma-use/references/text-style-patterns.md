# Text Style API Patterns

> Part of the [use_figma skill](../SKILL.md). How to create, apply, and inspect text styles using the Plugin API.
>
See [fig-builder.md](fig-builder.md#styles---create-reference-apply) for the full surface (`paintStyle` / `textStyle` / `effectStyle` / `gridStyle` / `getStyle`, the `FigPlanStyle` handle methods, and the `fills` / `strokes` / `effects` / `layoutGrids` / `textStyle` property routing).

Use the raw Plugin API for discovery and `$fig` for creating and binding. Flush pending `$fig` work with `await $fig.done()` before reading live styles or making raw API mutations.

> For design system context (when to create text styles, how they relate to tokens, `use_figma` limitations), see [wwds-text-styles](working-with-design-systems/wwds-text-styles.md).

## Contents

- Listing Text Styles
- Creating a Text Style
- Discovering Available Font Styles
- Creating a Type Ramp (Multi-Step)
- Using Library Text Styles by Key (preferred)
- Applying Text Styles to Nodes

## Listing Text Styles

```javascript
/**
 * Lists all local text styles with their key properties.
 *
 * @returns {Promise<Array<{id: string, name: string, key: string, fontSize: number, fontName: FontName, lineHeight: LineHeight, letterSpacing: LetterSpacing}>>}
 */
async function listTextStyles() {
  const styles = await figma.getLocalTextStylesAsync();
  return styles.map(s => ({
    id: s.id,
    name: s.name,
    key: s.key,
    fontSize: s.fontSize,
    fontName: s.fontName,
    lineHeight: s.lineHeight,
    letterSpacing: s.letterSpacing
  }));
}
```

Full runnable script:

```javascript
const results = await listTextStyles();
return results;
```

## Creating a Text Style

`$fig` loads the font automatically when the plan is flushed. `lineHeight` and `letterSpacing` must be `{value, unit}` objects; line height also accepts `{ unit: 'AUTO' }`.

```javascript
const body = $fig.textStyle({
  name: "body/base",
  fontName: { family: "Inter", style: "Regular" },
  fontSize: 16,
  lineHeight: { unit: "AUTO" },
  letterSpacing: { value: 0, unit: "PIXELS" },
  description: "CSS: var(--font-body-base)",
});

$fig.text({ characters: "Body", textStyle: body })
```

## Discovering Available Font Styles

Font style names vary per provider and per file.  Use `figma.listAvailableFontsAsync()` to discover exact style strings — never guess or probe with try/catch:

```javascript
/**
 * Discovers available font styles for a given family using listAvailableFontsAsync.
 *
 * @param {string} family - Font family name, e.g. "Inter"
 * @returns {Promise<string[]>} - All available style names for the family
 */
async function getAvailableFontStyles(family) {
  const allFonts = await figma.listAvailableFontsAsync();
  return allFonts
    .filter(f => f.fontName.family === family)
    .map(f => f.fontName.style);
}
```

## Creating a Type Ramp (Multi-Step)

Handles font loading, deduplication, and idempotency. Each entry: `[name, fontFamily, fontStyle, fontSize_px, lineHeight, cssVar]`.

```javascript
async function createTypeRamp(defs) {
  const existing = new Set(
    (await figma.getLocalTextStylesAsync()).map(s => s.name)
  );
  const created = [];
  const skipped = [];

  for (const [name, family, style, fontSize, lineHeight, cssVar] of defs) {
    if (existing.has(name)) {
      skipped.push(name);
      continue;
    }
    $fig.textStyle({
      name,
      fontName: { family, style },
      fontSize,
      lineHeight: lineHeight ?? { unit: 'AUTO' },
      ...(cssVar ? { description: `CSS: var(${cssVar})` } : {}),
    });
    existing.add(name);
    created.push(name);
  }

  // Fonts are deduplicated and loaded automatically for the plan.
  await $fig.done();
  return { created, skipped };
}
```

Full runnable script:

```javascript
const defs = [
  ['heading/xl', 'Inter', 'Bold',      48, { unit: 'PIXELS', value: 56 }, '--font-heading-xl'],
  ['heading/lg', 'Inter', 'Bold',      36, { unit: 'PIXELS', value: 44 }, '--font-heading-lg'],
  ['body/base',  'Inter', 'Regular',   16, { unit: 'AUTO' },              '--font-body-base'],
  ['body/sm',    'Inter', 'Regular',   14, { unit: 'AUTO' },              '--font-body-sm'],
  ['code/base',  'Roboto Mono', 'Regular', 14, { unit: 'AUTO' },          '--font-code-base'],
];
const result = await createTypeRamp(defs);
return result;
```

## Using Library Text Styles by Key (preferred)

A style found via a `search_design_system` `queries` entry with `entity: "style"` returns a `key`. Pass it directly into `$fig.getStyle(styleKey)` and apply via the `textStyle` property on any `$fig.text(...)` / `$fig.query('TEXT').set(...)` — the plan queues the library import automatically.

```javascript
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY)
$fig.text({ characters: 'Title', textStyle: heading })

// Bulk apply to existing text nodes
$fig.query('TEXT[name=Heading]').set({ textStyle: heading })
await $fig.done()
```

Prefer reusing library text styles over creating new ones.

### Raw-API fallback

```javascript
// If you need the imported TextStyle's metadata mid-script
const headingStyle = await figma.importStyleByKeyAsync("TEXT_STYLE_KEY");
await textNode.setTextStyleIdAsync(headingStyle.id);
```

## Applying Text Styles to Nodes

Pass the handle returned by `$fig.textStyle()` or `$fig.getStyle()` as `textStyle`. `$fig` loads fonts and resolves the style when the plan is flushed.

```javascript
// Accepts a local style ID or a library key from search_design_system.
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY);

// Apply to every TEXT whose name contains 'Heading' on the current page.
const matching = $fig.query('TEXT[name*=Heading]').set({ textStyle: heading });
await $fig.done();
return { applied: matching.length };
```

Scope the query to a node:

```javascript
const card = $fig.get('1:42').query('TEXT[name*=Heading]').set({ textStyle: heading });
await $fig.done();
```
