# Componentize repeated and reusable elements

Componentization is part of the **default** workflow, not an optional follow-up. Produce a componentized structure on the first pass — do not emit a flat tree of one-off frames and wait for a second "now make it componentized" prompt.
This applies to **empty files with no design system**: published-library discovery (Step 2) does not cover local components, so an empty library search is a reason to create local components, not a reason to skip them.

- **Design-system instances are already componentized.** Where Step 2 found a published component, instancing it satisfies this and is the preferred path.
- **For anything the design system does not cover, create a local component when the element repeats or maps to a reusable source component.** If the source defines a reusable component (`<ListRow>`, `<StatCard>`, `<NavItem>`) or the same element appears more than once, build it **once** with `$fig.component(...)` (or `$fig.variants(...)` for visual states), then place instances with `$fig.instance(...)` and override per-instance content — instead of hand-building N near-identical frames.
- **Mirror the source's component boundaries.** One source component maps to one Figma main component. This keeps the output editable and matches what designers expect to receive.

## Decide once per element: reuse, create once, or keep as a frame

Build the reuse inventory in Step 1 and decide each row before building sections:

| Element | Decision |
|---|---|
| A published or existing local component covers it | **Reuse** it: `$fig.instance(KEY_OR_ID, { props })` |
| It repeats (same element rendered 2+ times, e.g. a `.map()`) or the source defines it as a reusable component (`<DayCell>`, `<StatusBadge>`, `<NavItem>`, `<MetricCard>`, `<Button>`) | **Create it once** as a local main component, then place instances |
| It is a unique layout container (page wrapper, section, grid, header bar) or a one-off element | **Keep it a frame** — do not componentize one-offs |

- **Record what differs between repeated items** — text, which optional parts are shown, and visual state. That list becomes the component's properties.
- **Use variants only for meaningful visual states** (`State=Default/Today/Outside`, `Status=Active/Paused`, `Trend=Up/Down`, `Selected=True/False`). Labels, numbers, dates, and titles are **TEXT properties**, not variants. Optional parts are **BOOLEAN properties**.
- **Match the file's component organization.** Put new main components in the file's existing component page or area when it has one. Otherwise keep them off to the side of the wrapper in a dedicated components area, or on a dedicated components page when that matches the file. Place only **instances** inside the view, exactly as you do with design-system components; never leave a main component inside it.

## Recipe: create once, instance many, reuse the ID later

### Call 1 — create the main components outside the view and return their IDs

```js
// Build the main components ONCE, then collect them in a "Components" section
// off to the side of the wrapper. (In a file with an existing component area,
// append the sets there instead of creating a section.)
const COLORS = { Blue: ['#DBEAFE', '#1E40AF'], Green: ['#DCFCE7', '#166534'] }
const chip = $fig.variants({ name: 'Event Chip' }, Object.entries(COLORS).map(([color, [bg, fg]]) =>
  $fig.component(
    { name: `Color=${color}`, layoutMode: 'HORIZONTAL', paddingLeft: 6, paddingRight: 6, paddingTop: 2, paddingBottom: 2, cornerRadius: 4, fills: [figma.util.solidPaint(bg)] },
    [$fig.text({ characters: 'Event', fontSize: 12, fills: [figma.util.solidPaint(fg)] }).textProp('Title')],
  ),
))
await $fig.done()
const chipSet = chip.node
const blue = chipSet.children.find((c) => c.name === 'Color=Blue')
const STATES = { Default: '#FFFFFF', Today: '#EFF6FF', Outside: '#F8FAFC' }
const cell = $fig.variants({ name: 'Day Cell' }, Object.entries(STATES).map(([state, bg]) =>
  $fig.component(
    { name: `State=${state}`, layoutMode: 'VERTICAL', width: 160, height: 120, itemSpacing: 4, paddingLeft: 8, paddingRight: 8, paddingTop: 8, paddingBottom: 8, fills: [figma.util.solidPaint(bg)] },
    [
      $fig.text({ name: 'Date', characters: '1', fontSize: 14 }).textProp('Date'),
      ...[1, 2, 3].map((n) =>
        $fig.instance(blue.id, { name: `Event ${n}`, layoutSizingHorizontal: 'FILL' }).booleanProp(`Show Event ${n}`),
      ),
    ],
  ),
))
await $fig.done()

const wrapper = await figma.getNodeByIdAsync('WRAPPER_ID')
const components = $fig.section({ name: 'Components', x: wrapper.x + wrapper.width + 400, y: wrapper.y })
await $fig.done()
const section = components.node
const PAD = 80, GAP = 16
let y = PAD, width = 0
for (const set of [chipSet, cell.node]) {
  set.children.forEach((v, i) => { v.x = GAP + i * (v.width + GAP); v.y = GAP })
  set.resizeWithoutConstraints(GAP + set.children.reduce((w, v) => w + v.width + GAP, 0), Math.max(...set.children.map((v) => v.height)) + 2 * GAP)
  section.appendChild(set)
  set.x = PAD
  set.y = y
  y += set.height + PAD
  width = Math.max(width, set.width)
}
section.resizeWithoutConstraints(width + 2 * PAD, y)

return { componentsContainerId: section.id, eventChipSetId: chipSet.id, dayCellSetId: cell.node.id }
```

$fig.variants stacks variants at (0,0), so the loop grids them and resizes each set (see fig-builder.md) before moving it into the section. If the file keeps components on a dedicated page, build them there instead; a script can switch pages only once (figma-use Rule 9), so build on that page in its own call. Return the container's ID either way.

### Call 2 (a later `use_figma` call) — place instances with different values

A plan handle does not survive between calls. Reuse the **node ID** returned by call 1; instances can reference a main component wherever it lives, including on another page.

```js
const DAYS = [ // from the source data
  { date: '14', state: 'Default', events: [] },
  { date: '15', state: 'Today', events: [{ title: 'Standup', color: 'Blue' }, { title: 'Lunch', color: 'Green' }] },
  { date: '16', state: 'Default', events: [{ title: 'Review', color: 'Green' }] },
]
const days = DAYS.map((d) => $fig.instance('DAY_CELL_SET_ID', {
  name: `Day ${d.date}`,
  // Property names are the names you declared (no `#id` suffix); a variant
  // axis value (`State`) selects the variant.
  props: {
    State: d.state,
    Date: d.date,
    'Show Event 1': d.events.length > 0,
    'Show Event 2': d.events.length > 1,
    'Show Event 3': d.events.length > 2,
  },
}))
$fig.get('WEEK_ROW_PLACEHOLDER_ID').replace($fig.autoLayout({ name: 'Week Row', layoutSizingHorizontal: 'FILL' }, days))
await $fig.done()

// Nested overrides: find each nested Event Chip on the *materialized* instance
// and set its props through $fig.get(id). Each instance keeps its own values.
days.forEach((day, i) => DAYS[i].events.forEach((ev, j) => {
  const chipInst = day.node.children.find((c) => c.name === `Event ${j + 1}`)
  $fig.get(chipInst.id).set({ props: { Color: ev.color, Title: ev.title } })
}))
```

**Differing child counts** (events per day, tags per card, rows per table): give the component a fixed maximum of slots with a BOOLEAN property per slot and hide the unused ones, as above. Do **not** detach instances, and do **not** `append` into an instance — instance children are read-only for structural edits. If an item needs more slots than the maximum, raise the maximum on the **main component** (instances update).

**Pitfalls:**

- Raw `instance.setProperties()` needs the full property key (`'Title#0:0'`). Prefer `$fig.instance(..., { props })` and `$fig.get(id).set({ props })`, which accept the declared names.
- Scope nested lookups on a materialized node (`day.node.children.find(...)`). Do not rely on `$fig.query(selector, planNode)` to limit a nested override to one instance — it can update matching layers in every instance.

## Validate structure, not just the screenshot

A screenshot cannot show whether repeated items are instances. Before finishing, run one read-only check on the wrapper and fix what it reports:

```js
const wrapper = $fig.get('WRAPPER_ID')
// The components section/area beside the wrapper, or the dedicated components page.
const container = $fig.get('COMPONENTS_CONTAINER_ID')
const setOrSelf = (c) => (c?.parent?.type === 'COMPONENT_SET' ? c.parent : c)
// Which main component (or set) each instance inside the screen points at.
const used = {}
for (const name of $fig.query('INSTANCE', wrapper).map((n) => setOrSelf(n.mainComponent)?.name)) {
  used[name] = (used[name] ?? 0) + 1
}
const mains = $fig.query('COMPONENT_SET, COMPONENT', container).map((c) => setOrSelf(c).name)
// Main components must never sit inside the view.
const mainsInsideScreen = $fig.query('COMPONENT_SET, COMPONENT', wrapper).map((c) => c.name)
// A same-page components area must not overlap the view.
let overlapsScreen = false
if (container.node.type !== 'PAGE') {
  const [w, s] = [wrapper.node.absoluteBoundingBox, container.node.absoluteBoundingBox]
  overlapsScreen = s.x < w.x + w.width && w.x < s.x + s.width && s.y < w.y + w.height && w.y < s.y + s.height
}
// Repeated plain frames inside the screen are componentization candidates.
const frameCounts = {}
for (const name of $fig.query('FRAME', wrapper).map((f) => f.name)) frameCounts[name] = (frameCounts[name] ?? 0) + 1
return {
  instancesByMain: used,
  unusedMains: [...new Set(mains)].filter((n) => !used[n]),
  mainsInsideScreen,
  overlapsScreen,
  repeatedFrames: Object.entries(frameCounts).filter(([, n]) => n >= 3),
}
```

- Every repeated element in your inventory appears in `instancesByMain`.
- `unusedMains` is empty. A main component beside duplicated frames is not reuse.
- `mainsInsideScreen` is empty, and `overlapsScreen` is `false`.
- `repeatedFrames` lists only layout containers, not duplicated items.
- Spot-check one override (a different title or state on two instances) and confirm an edit to a main component would propagate: instances only inherit what they do not override.
