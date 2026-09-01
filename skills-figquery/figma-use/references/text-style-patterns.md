# Text Style API Patterns

> Part of the [use_figma skill](../SKILL.md). How to create, apply, and inspect text styles using the Plugin API.
>
> For design system context (when to create text styles, how they relate to tokens, `use_figma` limitations), see [wwds-text-styles](working-with-design-systems/wwds-text-styles.md).

## Prefer `$fig` for creation + binding

For new text styles + binding them to text nodes, reach for `$fig` first — fonts preload automatically, the style and the binding go in the same plan, and the binding uses the natural `textStyle` property (no `*StyleId` suffix to remember):

```javascript
const heading = $fig.textStyle({
  name: "Heading/1",
  fontName: { family: "Inter", style: "Bold" },
  fontSize: 48,
})
$fig.text({ characters: "Title", textStyle: heading })
```

See [fig-builder.md](fig-builder.md#styles---create-reference-apply) for the full surface (`paintStyle` / `textStyle` / `effectStyle` / `gridStyle` / `getStyle`, the `FigPlanStyle` handle methods, and the `fills` / `strokes` / `effects` / `layoutGrids` / `textStyle` property routing).

The raw Plugin API patterns below are the fallback for when you genuinely need to interleave style ops with mid-script async calls or read computed properties off the live `TextStyle` before deciding what to do next.

## Contents

- Listing Text Styles
- Creating a Text Style
- Discovering Available Font Styles
- Creating a Type Ramp (Multi-Step)
- Importing Library Text Styles
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

Font **MUST** be loaded before setting `fontName`. `lineHeight` and `letterSpacing` must be `{value, unit}` objects — bare numbers throw.

```javascript
/**
 * Creates a text style with all typographic properties set.
 * Font MUST be loaded before calling.
 *
 * @param {string} name - Slash-delimited name, e.g. "body/base"
 * @param {{ family: string, style: string }} fontName
 * @param {number} fontSize - In pixels
 * @param {{ value: number, unit: 'PIXELS' | 'PERCENT' } | { unit: 'AUTO' }} lineHeight
 * @param {{ value: number, unit: 'PIXELS' | 'PERCENT' }} [letterSpacing]
 * @param {string} [description] - e.g. the CSS variable name "CSS: var(--font-body-base)"
 * @returns {TextStyle}
 */
function createTextStyleFull(name, fontName, fontSize, lineHeight, letterSpacing, description) {
  const style = figma.createTextStyle();
  style.name = name;
  style.fontName = fontName;
  style.fontSize = fontSize;
  style.lineHeight = lineHeight; // { unit: 'AUTO' } | { value, unit: 'PIXELS'|'PERCENT' }
  if (letterSpacing) style.letterSpacing = letterSpacing;
  if (description) style.description = description;
  return style;
}
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
/**
 * Creates a full type ramp from a token definition array.
 * Handles font loading, deduplication, and idempotency.
 *
 * Each entry: [name, fontFamily, fontStyle, fontSize_px, lineHeight, cssVar]
 *   - lineHeight: { unit: 'AUTO' } or { value: number, unit: 'PIXELS' | 'PERCENT' }
 *
 * @param {Array} defs - Array of [name, fontFamily, fontStyle, fontSize, lineHeight, cssVar] tuples
 * @returns {Promise<{ created: string[], skipped: string[] }>}
 */
async function createTypeRamp(defs) {
  const uniqueFonts = new Set();
  for (const [, family, style] of defs) {
    uniqueFonts.add(JSON.stringify({ family, style }));
  }
  await Promise.all(
    [...uniqueFonts].map(f => figma.loadFontAsync(JSON.parse(f)))
  );

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
    const ts = figma.createTextStyle();
    ts.name = name;
    ts.fontName = { family, style };
    ts.fontSize = fontSize;
    ts.lineHeight = lineHeight ?? { unit: 'AUTO' };
    if (cssVar) ts.description = `CSS: var(${cssVar})`;
    created.push(name);
  }

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

## Using Library Text Styles by key (preferred)

`search_design_system` with `includeStyles: true` returns a `key` per style. Pass it directly into `$fig.getStyle(styleKey)` and apply via the `textStyle` property on any `$fig.text(...)` / `$fig.query('TEXT').set(...)` — the plan queues the library import automatically.

```javascript
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY)
$fig.text({ characters: 'Title', textStyle: heading })

// Bulk apply to existing text nodes
$fig.query('TEXT[name=Heading]').set({ textStyle: heading })
```

Prefer reusing library text styles over creating new ones.

### Raw-API fallback

```javascript
// If you need the imported TextStyle's metadata mid-script
const headingStyle = await figma.importStyleByKeyAsync("TEXT_STYLE_KEY");
await textNode.setTextStyleIdAsync(headingStyle.id);
```

## Applying Text Styles to Nodes

Prefer `$fig.query(...).set({ textStyle })` over `findAllWithCriteria` + a manual loop — the selector matches name patterns directly, and `$fig` batches the writes and resolves the style id at flush time. The `textStyle` property accepts a `$fig.getStyle(...)` handle (local id OR library `key` from `search_design_system`) or a raw style id string.

```javascript
// Library style by key — $fig queues the import; no separate await needed.
const heading = $fig.getStyle(HEADING_TEXT_STYLE_KEY)

// Apply to every TEXT whose name contains 'Heading' on the current page
const result = $fig.query('TEXT[name*=Heading]').set({ textStyle: heading })
return { applied: result.length }
```

Scope to a subtree or another page via a second arg / a parent handle:

```javascript
// Scoped to one frame
const card = $fig.get('1:42')
$fig.query('TEXT[name*=Heading]', card).set({ textStyle: heading })

// Across the whole document (all pages)
$fig.query('TEXT[name*=Heading]', figma.root).set({ textStyle: heading })
```

If you already have a local style id (not a key) and don't want a `$fig.getStyle` wrap, the raw setter still works:

```javascript
$fig.query('TEXT[name*=Heading]').each(async (n) => {
  await n.node?.setTextStyleIdAsync('STYLE_ID')   // only after $fig.done() / auto-flush
})
```
