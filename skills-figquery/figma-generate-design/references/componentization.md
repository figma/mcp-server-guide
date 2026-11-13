# Componentize repeated and reusable elements

Componentization is part of the **default** workflow, not an optional follow-up. Produce a componentized structure on the first pass — do not emit a flat tree of one-off frames and wait for a second "now make it componentized" prompt.
This applies to **empty files with no design system**: published-library discovery (Step 2) does not cover local components, so an empty library search is a reason to create local components, not a reason to skip them.

- **Design-system instances are already componentized.** Where Step 2 found a published component, instancing it satisfies this and is the preferred path.
- **For anything the design system does not cover, create a local component when the element repeats or maps to a reusable source component.** If the source defines a reusable component (`<ListRow>`, `<StatCard>`, `<NavItem>`) or the same element appears more than once, build it **once** with `$fig.component(...)` (or `$fig.variants(...)` for visual states), then place instances with `$fig.instance(...)` and override per-instance content — instead of hand-building N near-identical frames.
- **Mirror the source's component boundaries.** One source component maps to one Figma main component. This keeps the output editable and matches what designers expect to receive.

```js
// Build the reusable element ONCE as a main component, off to the side of the wrapper...
const wrapper = await figma.getNodeByIdAsync('WRAPPER_ID')
const row = $fig.component({ name: 'List Row', layoutMode: 'HORIZONTAL', itemSpacing: 8, x: wrapper.x + wrapper.width + 200, y: wrapper.y }, [
  $fig.text({ characters: 'Title' }).textProp('Title'),
  $fig.text({ characters: 'Meta' }).textProp('Meta').booleanProp('Show Meta'),
])
// ...then place instances with per-item props instead of rebuilding frames.
$fig.get('LIST_PLACEHOLDER_ID').replace(
  $fig.autoLayout({ name: 'List', layoutMode: 'VERTICAL', layoutSizingHorizontal: 'FILL' },
    ITEMS.map((item) => $fig.instance(row, {
      layoutSizingHorizontal: 'FILL',
      props: { Title: item.title, Meta: item.meta ?? '', 'Show Meta': Boolean(item.meta) },
    })),
  ),
)
await $fig.done()
return { listRowId: row.node.id }
```

Keep the main component off to the side of the wrapper (or in the file's existing components area) and place only **instances** inside the view, exactly as you do with design-system components. Labels and values are TEXT properties, optional parts are BOOLEAN properties, and only meaningful visual states are variants. A plan handle does not survive between calls: return the component's node ID and use `$fig.instance('ID', { props })` in later calls. For differing child counts, give the component a fixed maximum of slots with a BOOLEAN per slot instead of detaching or appending into an instance.
