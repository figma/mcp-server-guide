# Code Connect Worked Example & SelectorOptions Examples

## SelectorOptions Examples

```ts
{ path?: string[], traverseInstances?: boolean }
```

- `traverseInstances: true` — required when the target lives inside another nested instance. Without it, `findInstance`/`findText` only search the current instance's own layers and stop at nested instance boundaries.
- `path: string[]` — disambiguates when multiple descendants share the same layer name. Lists parent layer names that must appear on the path to the target.

```ts
// Layer hierarchy:
//   A > C (instance) > "mychild"
// "mychild" sits inside nested instance C, so plain findInstance returns ErrorHandle.
instance.findInstance('mychild', { traverseInstances: true })

// Layer hierarchy:
//   A > C (instance) > "mychild"
//   A > D (instance) > "mychild"
// Two "mychild" layers exist — use path to pick the one under C.
instance.findInstance('mychild', { traverseInstances: true, path: ['C'] })
```

**When to reach into a nested instance from a parent template:** only when the parent code component (from Step 4) takes the nested layer as a prop value itself (e.g. `<C show={<B />} />` — A forwards B into C). If the parent just composes C and C renders B internally, resolve C with `executeTemplate()` and let C's own template handle B — don't duplicate B's rendering at the parent level.

## Complete Worked Example

Given URL: `https://figma.com/design/abc123/MyFile?node-id=42-100`

**Step 1:** Parse the URL.
- `fileKey` = `abc123`
- `nodeId` = `42-100` → `42:100`

**Step 2:** Call `get_code_connect_suggestions` with `fileKey: "abc123"`, `nodeId: "42:100"`, `excludeMappingPrompt: true`.
Response returns one component with `mainComponentNodeId: "42:100"`. If the response were empty, stop and inform the user. If multiple components were returned, repeat Steps 3–6 for each.

**Step 3:** Call `get_context_for_code_connect` with `fileKey: "abc123"`, `nodeId: "42:100"` (from Step 2), `clientFrameworks: ["react"]`, `clientLanguages: ["typescript"]`.

Response includes properties:
- Label (TEXT)
- Variant (VARIANT): Primary, Secondary
- Size (VARIANT): Small, Medium, Large
- Disabled (BOOLEAN)
- Has Icon (BOOLEAN)
- Icon (INSTANCE_SWAP)

**Step 4:** Search codebase → find `Button` component. Read its source to confirm props: `variant`, `size`, `disabled`, `icon`, `children`. Import path: `"primitives"`.

**Step 5:** Create `src/figma/primitives/Button.figma.ts`:

```ts
// url=https://figma.com/design/abc123/MyFile?node-id=42-100
// source=src/components/Button.tsx
// component=Button
import figma from 'figma'
const instance = figma.selectedInstance

const label = instance.getString('Label')
const variant = instance.getEnum('Variant', {
  'Primary': 'primary',
  'Secondary': 'secondary',
})
const size = instance.getEnum('Size', {
  'Small': 'sm',
  'Medium': 'md',
  'Large': 'lg',
})
const disabled = instance.getBoolean('Disabled')
const hasIcon = instance.getBoolean('Has Icon')
const icon = hasIcon ? instance.getInstanceSwap('Icon') : null
let iconCode
if (icon && icon.type === 'INSTANCE') {
  iconCode = icon.executeTemplate().example
}

export default {
  example: figma.code`
    <Button
      variant="${variant}"
      size="${size}"
      ${disabled ? 'disabled' : ''}
      ${iconCode ? figma.code`icon={${iconCode}}` : ''}
    >
      ${label}
    </Button>
  `,
  imports: ['import { Button } from "primitives"'],
  id: 'button',
  metadata: { nestable: true }
}
```

**Step 6:** Read back file to verify syntax.
