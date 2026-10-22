# Code Connect

## Overview

Create Code Connect template files (`.figma.ts`) that map Figma components to code snippets. Given a Figma URL, follow the steps below to create a template.

> **Note:** This project may also contain parser-based `.figma.tsx` files (using `figma.connect()`, published via CLI). This skill covers **templates files only** — `.figma.ts` files that use the MCP tools to fetch component context from Figma.

## Prerequisites

- **Figma MCP server must be connected** — verify that Figma MCP tools (e.g., `get_code_connect_suggestions`) are available before proceeding. If not, guide the user to enable the Figma MCP server and restart their MCP client.
- **Components must be published** — Code Connect only works with components published to a Figma team library. If a component is not published, inform the user and stop.
- **Organization or Enterprise plan required** — Code Connect is not available on Free or Professional plans.
- **URL must include `node-id`** — the Figma URL must contain the `node-id` query parameter.
- **TypeScript types** — for editor autocomplete and type checking in `.figma.ts` files `@figma/code-connect/figma-types` must be added to `types` in `tsconfig.json`:
  ```json
  {
    "compilerOptions": {
      "types": ["@figma/code-connect/figma-types"]
    }
  }
  ```

## Step 1: Parse the Figma URL

Extract `fileKey` and `nodeId` from the URL:

| URL Format | fileKey | nodeId |
|---|---|---|
| `figma.com/design/:fileKey/:name?node-id=X-Y` | `:fileKey` | `X-Y` → `X:Y` |
| `figma.com/file/:fileKey/:name?node-id=X-Y` | `:fileKey` | `X-Y` → `X:Y` |
| `figma.com/design/:fileKey/branch/:branchKey/:name` | use `:branchKey` | from `node-id` param |

Always convert `nodeId` hyphens to colons: `1234-5678` → `1234:5678`.

**Worked example:**

Given: `https://www.figma.com/design/QiEF6w564ggoW8ftcLvdcu/MyDesignSystem?node-id=4185-3778`
- `fileKey` = `QiEF6w564ggoW8ftcLvdcu`
- `nodeId` = `4185-3778` → `4185:3778`

## Step 2: Discover Unmapped Components

The user may provide a URL pointing to a frame, instance, or variant — not necessarily a component set or standalone component. Call the MCP tool `get_code_connect_suggestions` with:
- `fileKey` — from Step 1
- `nodeId` — from Step 1 (colons format)
- `excludeMappingPrompt` — `true` (returns a lightweight list of unmapped components)

This tool identifies published components in the selection that don't yet have Code Connect mappings.

**Handle the response:**

- **"No published components found in this selection"** — the node contains no published components. Inform the user they need to publish the component to a team library in Figma first, then stop.
- **"All component instances in this selection are already connected to code via Code Connect"** — everything is already mapped. Inform the user and stop.
- **Normal response with component list** — extract the `mainComponentNodeId` for each returned component. Use these resolved node IDs (not the original from the URL) for all subsequent steps. If multiple components are returned (e.g. the user selected a frame containing several different component instances), repeat Steps 3–6 for each one.

## Step 3: Fetch Component Properties

Call the MCP tool `get_context_for_code_connect` with:
- `fileKey` — from Step 1
- `nodeId` — the resolved `mainComponentNodeId` from Step 2
- `clientFrameworks` — determine from `figma.config.json` `parser` field (e.g. `"react"` → `["react"]`)
- `clientLanguages` — infer from project file extensions (e.g. TypeScript project → `["typescript"]`, JavaScript → `["javascript"]`)

For multiple components, call the tool once per node ID.

The response contains the Figma component's **property definitions** — note each property's name and type:
- **TEXT** — text content (labels, titles, placeholders)
- **BOOLEAN** — toggles (show/hide icon, disabled state)
- **VARIANT** — enum options (size, variant, state)
- **INSTANCE_SWAP** — swappable nested instances tied to a specific component (icon, avatar)
- **SLOT** — flexible content regions (freeform layout, mixed children); use `getSlot()` in templates (not the same as INSTANCE_SWAP)

Save this property list — you will use it in Step 5 to write the template.

## Step 4: Identify the Code Component

If the user did not specify which code component to connect:

1. Check `figma.config.json` for `paths` and `importPaths` to find where components live
2. Search the codebase for a component matching the Figma component name. Check common directories (`src/components/`, `components/`, `lib/ui/`, `app/components/`) if `figma.config.json` doesn't specify paths
3. Read candidate files and compare their props interface against the Figma properties from Step 3 — look for matching variant types, size options, boolean flags, and slot props
4. If multiple candidates match, pick the one with the closest prop-interface match and explain your reasoning to the user
5. If no match is found, show the 2 closest candidates and ask the user to confirm or provide the correct path

**Confirm with the user** before proceeding to Step 5. Present the match: which code component you found, where it lives, and why it matches (prop correspondence, naming, purpose).

Read `figma.config.json` for import path aliases — the `importPaths` section maps glob patterns to import specifiers, and the `paths` section maps those specifiers to directories.

Read the code component's source to understand its props interface — this informs how to map Figma properties to code props in Step 5.

## Step 5: Create the Template File (.figma.ts)

### File location

Place the file alongside existing Code Connect templates (`.figma.tsx` or `.figma.ts` files). Check `figma.config.json` `include` patterns for the correct directory. Name it `ComponentName.figma.ts`.

### Template structure

Every template file follows this structure:

```ts
// url=https://www.figma.com/file/{fileKey}/{fileName}?node-id={nodeId}
// source={path to code component from Step 4}
// component={code component name from Step 4}
import figma from 'figma'
const instance = figma.selectedInstance

// Extract properties from the Figma component (see property mapping below)
// ...

export default {
  example: figma.code`<Component ... />`,       // Required: code snippet
  imports: ['import { Component } from "..."'], // Optional: import statements
  id: 'component-name',                         // Required: unique identifier
  metadata: {                                    // Optional
    nestable: true,                              // true = inline in parent, false = show as pill
    props: {}                                    // data accessible to parent templates
  }
}
```

### Property mapping

Use the property list from Step 3 to extract values. For each Figma property type, use the corresponding method:

| Figma Property Type | Template Method | When to Use |
|---|---|---|
| TEXT | `instance.getString('Name')` | Labels, titles, placeholder text |
| BOOLEAN | `instance.getBoolean('Name', { true: ..., false: ... })` | Toggle visibility, conditional props |
| VARIANT | `instance.getEnum('Name', { 'FigmaVal': 'codeVal' })` | Size, variant, state enums |
| INSTANCE_SWAP | `instance.getInstanceSwap('Name')` | Swapped instance for a fixed component slot (then `hasCodeConnect()` / `executeTemplate()`) - do not confuse with the SLOT property below |
| SLOT | `instance.getSlot('Name')` | Freeform slot content only when the Figma property type is **SLOT** 
| (child layer) | `instance.findInstance('LayerName')` | Named child instances without a property |
| (text layer) | `instance.findText('LayerName')` → `.textContent` | Text content from named layers |

**TEXT** — get the string value directly:
```ts
const label = instance.getString('Label')
```

**VARIANT** — map Figma enum values to code values:
```ts
const variant = instance.getEnum('Variant', {
  'Primary': 'primary',
  'Secondary': 'secondary',
})

const size = instance.getEnum('Size', {
  'Small': 'sm',
  'Medium': 'md',
  'Large': 'lg',
})
```

**BOOLEAN** — simple boolean or mapped to values:
```ts
// Simple boolean
const disabled = instance.getBoolean('Disabled')

// Mapped to code values (e.g. when the code prop is an enum, not a boolean)
const size = instance.getBoolean('Show Label', { true: 'large', false: 'small' })
```

**Map Figma properties to code props where there's a valid correspondence.** Figma properties and code props don't always line up 1:1 — some Figma properties map directly (by name, or via the API methods above), others have no code equivalent. Where a mapping exists, use it; where none fits, omit the Figma property rather than invent a code prop. Never emit an attribute whose name doesn't appear in the code component's `Props` interface.

### Exhaustive variant handling

When a VARIANT property has multiple possible values, the `getEnum` mapping **must list every value** returned by `get_context_for_code_connect`. Don't omit values — an unmapped value silently returns `undefined`, producing broken output.

```ts
// WRONG — omits 'Warning', which will render as undefined
const status = instance.getEnum('Status', {
  'Success': 'success',
  'Error': 'error',
})

// CORRECT — every value is mapped
const status = instance.getEnum('Status', {
  'Success': 'success',
  'Error': 'error',
  'Warning': 'warning',
  'Info': 'info',
})
```

When **two or more VARIANT properties combine** to produce different code output, generate exhaustive conditional branches. For example, 2 variants × 2 values = 4 branches:

```ts
const type = instance.getEnum('Type', { 'Filled': 'filled', 'Outlined': 'outlined' })
const status = instance.getEnum('Status', { 'Success': 'success', 'Error': 'error' })

let colorClass
if (type === 'filled' && status === 'success') {
  colorClass = 'bg-green-500 text-white'
} else if (type === 'filled' && status === 'error') {
  colorClass = 'bg-red-500 text-white'
} else if (type === 'outlined' && status === 'success') {
  colorClass = 'bg-transparent border-green-500'
} else if (type === 'outlined' && status === 'error') {
  colorClass = 'bg-transparent border-red-500'
}
```

If the combinations produce **repetitive** output (e.g., `Size` doesn't change the snippet structure — it's just passed through as a prop), a single `getEnum` mapping per variant is sufficient — no need for cross-product branches.

**INSTANCE_SWAP** — access swappable component instances:
```ts
const icon = instance.getInstanceSwap('Icon')
let iconCode
if (icon && icon.type === 'INSTANCE') {
  iconCode = icon.executeTemplate().example
}
```

**SLOT** — `getSlot(propName)` is only valid when the Figma component property reported in Step 3 has type **`SLOT`**. Do not use `getSlot()` for **INSTANCE_SWAP** properties (those use `getInstanceSwap()`). Slots are explicit “content regions” in the component definition, not generic nested instances.

- **Signature:** `getSlot(propName: string): ResultSection[] | undefined`
```ts
// Figma property "Content" must be type SLOT in component properties
const content = instance.getSlot('Content')

export default {
  example: figma.code`<Card>${content}</Card>`,
  // ...
}
```

### Interpolation in tagged templates

When interpolating values in tagged templates, use the correct wrapping:
- **String values** (`getString`, `getEnum`, `textContent`): wrap in quotes → `variant="${variant}"`
- **Instance/section values** (`executeTemplate().example`): wrap in braces → `icon={${iconCode}}`
- **Slot sections** (`getSlot()` result — `ResultSection[] | undefined`): interpolate directly inside `` figma.code`...` `` (same shape as nested snippet sections), e.g. `` figma.code`<Select>${content}</Select>` `` — do not treat as a plain string
- **Boolean bare props**: use conditional → `${disabled ? 'disabled' : ''}`

### Finding descendant layers

When you need to access children that aren't exposed as component properties:

| Method | Use when |
|---|---|
| `instance.getInstanceSwap('PropName')` | Figma property type is **INSTANCE_SWAP** (fixed swapped instance) |
| `instance.getSlot('PropName')` | Figma property type is **SLOT** (freeform content region) |
| `instance.findInstance('LayerName')` | You know the child layer name (no component property) |
| `instance.findText('LayerName')` → `.textContent` | You need text content from a named text layer |
| `instance.findConnectedInstance('id')` | You know the child's Code Connect `id` |
| `instance.findConnectedInstances(fn)` | You need multiple connected children matching a filter |
| `instance.findLayers(fn)` | You need any layers (text + instances) matching a filter |

### Nested configurable instances

A component may contain child instances that are **not exposed as component properties** (no INSTANCE_SWAP) but are still **independently configurable** — they have their own variants, properties, or swap slots. These must be resolved dynamically, not hardcoded.

1. **Check whether the child already has a Code Connect template** — use `get_code_connect_suggestions` or check existing `.figma.ts` files in the project.
2. **If no template exists, create one** for the child so it renders correctly both standalone and when nested.
3. **Reference the child from the parent** using `findInstance()` or `findConnectedInstance()`, then call `executeTemplate()`.

```ts
// Parent template — the Badge child isn't a prop, but it's configurable
const badge = instance.findInstance('Status Badge')
let badgeCode
if (badge && badge.type === 'INSTANCE') {
  badgeCode = badge.executeTemplate().example
}

export default {
  example: figma.code`<Card>${badgeCode}</Card>`,
  // ...
}
```

This applies to icons, badges, labels, and any other nested instance that is configurable by itself — always connect them and render dynamically, never hardcode their content.

### Nested component example

For multi-level nested components or metadata prop passing between templates, see [Code Connect Examples](#reference--code-connect-examples).

```ts
const icon = instance.getInstanceSwap('Icon')
let iconSnippet
if (icon && icon.type === 'INSTANCE') {
  iconSnippet = icon.executeTemplate().example
}

export default {
  example: figma.code`<Button ${iconSnippet ? figma.code`icon={${iconSnippet}}` : ''}>${label}</Button>`,
  // ...
}
```

### Conditional props

```ts
const variant = instance.getEnum('Variant', { 'Primary': 'primary', 'Secondary': 'secondary' })
const disabled = instance.getBoolean('Disabled')

export default {
  example: figma.code`
    <Button
      variant="${variant}"
      ${disabled ? 'disabled' : ''}
    >
      ${label}
    </Button>
  `,
  // ...
}
```

## Step 6: Validate

Read back the `.figma.ts` file and review it against the following:

- **Property coverage** — every Figma property from Step 3 should be accounted for in the template. Flag any that are missing and ask the user if they were intentionally omitted.
- **Valid, correctly typed code** — all emitted code must be valid and correctly typed against the code component's `Props` interface. Never make up component properties — if a Figma property has no corresponding code prop, omit it rather than invent one.
- **No hardcoded children** — verify that every INSTANCE_SWAP property and child component slot uses the dynamic APIs (`getInstanceSwap()`, `findInstance()`, `findConnectedInstance()`, etc.) with `executeTemplate()`. No slot should contain hardcoded component content.
- **Rules and Pitfalls** — check for the common mistakes listed below (string concatenation of template results, unnecessary `hasCodeConnect()` guards, missing `type === 'INSTANCE'` checks, etc.)
- **Interpolation wrapping** — strings (`getString`, `getEnum`, `textContent`) wrapped in quotes, instance/section values (`executeTemplate().example`) wrapped in braces, slot sections (`getSlot`) interpolated as snippet sections inside `` figma.code`...` ``, booleans using conditionals

If anything looks uncertain, consult [Code Connect Template API Reference](#reference--code-connect-template-api-reference) for API details and [Code Connect Examples](#reference--code-connect-examples) for complex nesting.

## Inline Quick Reference

### `instance.*` Methods

| Method | Signature | Returns |
|---|---|---|
| `getString` | `(propName: string)` | `string` |
| `getBoolean` | `(propName: string, mapping?: { true: any, false: any })` | `boolean \| any` |
| `getEnum` | `(propName: string, mapping: { [figmaVal]: codeVal })` | `any` |
| `getInstanceSwap` | `(propName: string)` | `InstanceHandle \| null` |
| `getSlot` | `(propName: string)` | `ResultSection[] \| undefined` |
| `getPropertyValue` | `(propName: string)` | `string \| boolean` |
| `findInstance` | `(layerName: string, opts?: SelectorOptions)` | `InstanceHandle \| ErrorHandle` |
| `findText` | `(layerName: string, opts?: SelectorOptions)` | `TextHandle \| ErrorHandle` |
| `findConnectedInstance` | `(codeConnectId: string, opts?: SelectorOptions)` | `InstanceHandle \| ErrorHandle` |
| `findConnectedInstances` | `(selector: (node) => boolean, opts?: SelectorOptions)` | `InstanceHandle[]` |
| `findLayers` | `(selector: (node) => boolean, opts?: SelectorOptions)` | `(InstanceHandle \| TextHandle)[]` |

### InstanceHandle Methods

| Method | Returns |
|---|---|
| `hasCodeConnect()` | `boolean` |
| `executeTemplate()` | `{ example: ResultSection[], metadata: Metadata }` |
| `codeConnectId()` | `string \| null` |

### TextHandle Properties

| Property | Type |
|---|---|
| `.textContent` | `string` |
| `.name` | `string` |

### SelectorOptions

```ts
{ path?: string[], traverseInstances?: boolean }
```

- `traverseInstances: true` — required when the target lives inside another nested instance. Without it, `findInstance`/`findText` only search the current instance's own layers and stop at nested instance boundaries.
- `path: string[]` — disambiguates when multiple descendants share the same layer name. Lists parent layer names that must appear on the path to the target.

**Examples:**

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

### Export Structure

```ts
export default {
  example: figma.code`...`,                      // Required: ResultSection[]
  id: 'component-name',                         // Required: string
  imports: ['import { X } from "..."'],          // Optional: string[]
  metadata: { nestable: true, props: {} }        // Optional
}
```

## Rules and Pitfalls

1. **Never string-concatenate template results.** `executeTemplate().example` is a `ResultSection[]` object, not a string. Using `+` or `.join()` produces `[object Object]`. Always interpolate inside tagged templates: `` figma.code`${snippet1}${snippet2}` ``

2. **Do not use `hasCodeConnect()` guards.** Call `executeTemplate()` directly on any instance after a `type === 'INSTANCE'` check. The runtime handles instances without Code Connect automatically.

   ```ts
   // WRONG — hasCodeConnect() gate drops non-CC instances
   if (icon && icon.type === 'INSTANCE' && icon.hasCodeConnect()) {
     iconCode = icon.executeTemplate().example
   }

   // CORRECT — let the runtime handle all instances
   if (icon && icon.type === 'INSTANCE') {
     iconCode = icon.executeTemplate().example
   }
   ```

3. **Check `type === 'INSTANCE'` before calling `executeTemplate()`.** `findInstance()`, `findConnectedInstance()`, and `findText()` return an `ErrorHandle` (truthy, but not a real node) on failure — not `null`. Always add a type check to avoid crashes: `if (child && child.type === 'INSTANCE') { ... }`

4. **Prefer `getInstanceSwap()` over `findInstance()`** when a component property exists for the slot. `findInstance('Star Icon')` breaks when the icon is swapped to a different name; `getInstanceSwap('Icon')` always works regardless of which instance is in the slot.

5. **Use `getSlot()` only when the Figma property type is `SLOT`.** For **INSTANCE_SWAP** props, use `getInstanceSwap()` (returns an `InstanceHandle`). `getSlot()` returns structured slot sections, not instances — never call `executeTemplate()` on its return value.

6. **Property names are case-sensitive** and must exactly match what `get_context_for_code_connect` returns.

7. **Handle multiple template arrays correctly.** When iterating over children, set each result in a separate variable and interpolate them individually — do not use `.map().join()`:
   ```ts
   // Wrong:
   items.map(n => n.executeTemplate().example).join('\n')

   // Correct — use separate variables:
   const child1 = items[0]?.executeTemplate().example
   const child2 = items[1]?.executeTemplate().example
   export default { example: figma.code`${child1}${child2}` }
   ```

7. **Never hardcode slot or children content.** Always resolve child instances dynamically — use `getInstanceSwap()` for INSTANCE_SWAP properties, `findInstance()`/`findConnectedInstance()` for direct children — and render them via `executeTemplate()`. Never construct JSX from a layer name (e.g., `<StarIcon />`) or guess import paths. If an instance has no Code Connect, omit it — do not add a hardcoded fallback.

   ```ts
   // WRONG — hardcodes the icon from its layer name
   example: figma.code`<Button icon={<StarIcon />}>Submit</Button>`

   // CORRECT — resolves dynamically, works for any swapped icon
   const icon = instance.findInstance('Icon')
   let iconCode
   if (icon && icon.type === 'INSTANCE') {
     iconCode = icon.executeTemplate().example
   }
   example: figma.code`<Button${iconCode ? figma.code` icon={${iconCode}}` : ''}>...</Button>`
   ```

8. **Attempt to represent every Figma property via a code prop.** The code component's `Props` interface (from Step 4) is the authoritative list of attribute names. For each Figma property, figure out the right way to represent it using the API methods from Step 5 — direct name match, value transformation, or whatever fits. If no code prop fits at all, omit it — don't invent a prop name.

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

## Additional Reference

For advanced patterns (multi-level nested components, `findConnectedInstances` filtering, metadata prop passing between parent/child templates):

- [Code Connect Template API Reference](#reference--code-connect-template-api-reference) — Full Code Connect API reference
- [Code Connect Examples](#reference--code-connect-examples) — Advanced nesting, metadata props, and descendant patterns

---

## Reference — Code Connect Examples

### Contents
- [Basic component property retrieval](#basic-component-property-retrieval)
- [Descendants and recursive templating](#descendants-and-recursive-templating)
  - [instance.metadata](#instancemetadata)
  - [instance.example](#instanceexample)
  - [Descendant methods](#descendant-methods)

### Basic component property retrieval

- `instance.getEnum`: if you want to map a variant value to something specific
- `instance.getString`: if you want a text property value, or a boolean/variant value back as a string.
- `instance.getBoolean`: if you want to map a boolean value to something specific
- `instance.getInstanceSwap`: if you want to access a swappable instance descendant by property name

#### Examples

Both of these are valid, but depending on required outcome, one or the other would be preferred.

```js
const variantMapping = instance.getEnum("Variant", {
  Primary: "primary",
  Secondary: "secondary",
});
const variantTransform = instance.getString("Variant").toLowerCase();
```

Booleans can also be handled similarly. These aren't the best example, but either approach may be preferred depending on the logic of the snippet.

```js
const booleanMapping = instance.getBoolean("Is Highlighted", {
  true: "is-highlighted",
  false: undefined,
});
const boolean = instance.getString("Is Highlighted") === "true";
```

Text properties are always getString()

```js
const label = instance.getString("Label");
```

### Descendants and recursive templating

There are many ways to find descendant layers. Deciding which to use depends on what descendant information is relevant in the parent context. Descendant context could be many things: layer properties, layer name, text content, total descendant count, or a full Code Connect snippet example.

Descendant instances that have Code Connect on them can have `example` (the code snippet object), or `metadata` custom information.

If `node.hasCodeConnect()`, these can be accessed with `const { example, metadata } = node.executeTemplate()`.

#### `instance.metadata`

**`metadata.props` is how you can surface non-snippet information upwards**

Any string value can be stored in props. This is additional information to the example snippet. Handy for scenarios where you want single values to be referenced in parent contexts instead of an entire snippet.

> **Important:** For a child template to be discoverable by parent templates (via `findConnectedInstance`, `findConnectedInstances`, or `hasCodeConnect()`), `nestable: true` must be set in **both** the template's `metadata` export **and** in `templateDataJson` when registering via `add_code_connect_map` — e.g. `'{"isParserless": true, "nestable": true}'`. If `nestable` is missing from `templateDataJson`, the child template will not be loaded into the parent's evaluation context.

```js
export default {
  example: figma.html`<ds-child>normal stuff</ds-child>`,
  id: "child",
  metadata: { nestable: true, props: { special: "Special Stuff!!! 🤩" } },
};
```

```js
const child = instance.findConnectedInstance("child");

if (child && child.type === 'INSTANCE') {
  export default {
    example: figma.html`<ds-parent>${child.executeTemplate().metadata?.props?.special}</ds-parent>`,
    id: "parent",
  };
}
```

The output of these templates would be:

```html
<!-- Child snippet by itself -->
<ds-child>normal stuff</ds-child>

<!-- Parent snippet bringing in child metadata -->
<ds-parent>Special Stuff!!! 🤩</ds-parent>
```

#### `instance.example`

`instance.executeTemplate().example` contains the code snippet (or an error if the snippet is invalid). It is an array, but should always be treated like a single value and can render just fine in figma's tagged template literals.

**`example` is an object, and should be interpolated via tagged template literals**

If the example is being used as is, stringifying it in a tagged template literal is required, otherwise it'll yield `[object Object]`.

```js
const thing = `<span>${node.executeTemplate().example}</span>`; // Will not work downstream
const thing = figma.html`<span>${node.executeTemplate().example}</span>`; // WILL work downstream

return {
  example: figma.html`${thing}`,
};
```

Arrays should be avoided when referring to template examples, joining them will render to `[object Object]`.

```js
const thing = [];
thing.push(figma.html`<span>${node.executeTemplate().example}</span>`);

return {
  example: figma.html`${thing.join("\n")}`, // BAD: Will not work
  example: figma.html`${thing[0]}`, // Will work...but defeats the purpose of an array and we should use a variable instead.
};
```

Therefore, If you have multiple children examples, set each in a variable.

```js
return {
  example: figma.html`${thingStart}${thing}${thingEnd}`,
};
```

**`example[0].code` is a string when the example is valid**

Digging into the example to get to the snippet string can be useful in rare cases, but requires validation first in case the template can't render. This is rarely recommended and only good if the default template is undesired and `metadata.props` is not an appropriate approach.

```js
const example = node.executeTemplate()?.example[0];
if (example?.type === "CODE") {
  // do something with snippet string
  thing = example.code.replace("abc", "123");
} else {
  // handle error
  thing = `ERROR: ${example?.message}`;
}
```

#### Descendant methods

**`instance` nodes**

`instance.getInstanceSwap` and `instance.getString` are the preferred ways to access content when component properties are tied to the values you are looking for. However, if you need to access text node content or instances that are not bound to component properties, there are other methods to get you there:

- `instance.hasCodeConnect()`: Whether or not the instance has code connect on it.
- `instance.codeConnectId()`: String to identify the connected component, set in code connect docs, usefule in filtering or finding the component via methods below.
- `instance.findInstance()`: Only returns a single instance, found by layer name.
- `instance.findText()`: Only returns a single text node, found by layer name.
- `instance.findConnectedInstance()`: Can use the `id` of a descendant (defined in the descendant's export) to remove any variability (layer naming, etc) and find a single instance of a specific component. Returns `ErrorHandle` on failure — check `result.type === 'INSTANCE'` before use.
- `instance.findConnectedInstances()`: To filter or find a list of connected instance descendants. `node.type` and `instance.hasCodeConnect()` are already enforced in this. `node.name` and `instance.codeConnectId()` can be used to filter in the handler.
- `instance.findLayers()`: To filter or find a list of any text or instance descendants. Instances do not have to be connected. `instance.hasCodeConnect()`, `node.type`, `node.name`, and `instance.codeConnectId()` can be used to filter in the handler.

**`text` nodes**

Text nodes only have a single value available in the API:

- `text.textContent`: returns the text content for the node.

##### findInstance versus getInstanceSwap

```js
const hasIcon = instance.getBoolean("Has Icon");
let icon = null;
if (hasIcon) {
  const iconInstance = instance.findInstance("Star Icon"); // INCORRECT: Will be null when icons with other names are in this slot.
  const iconInstance = instance.getInstanceSwap("Icon"); // CORRECT: Will refer to any instance in this slot.
  if (iconInstance && iconInstance.type === 'INSTANCE' && iconInstance.hasCodeConnect()) {
    icon = iconInstance.executeTemplate().example;
  }
}
```

##### findLayers to get a list of strings

```js
const items = [];
instance.findLayers((node) => {
  if (node.type === "TEXT") {
    items.push(`<li>${node.textContent}</li>`);
  }
});
```

##### findLayers to iterate with an index

```js
const items = [];
let i = 0;
instance.findConnectedInstances((node) => {
  if (node.codeConnectId() === "button") {
    items.push(
      figma.code`<span slot="child-${i}">${
        node.executeTemplate().metadata.props.label
      }</span>`,
    );
    i++;
  }
});
```

##### Sophisticated inheritance, three generation example

```js
// url=https://www.figma.com/design?node-id=7699-6920
// source=src/components/Grandparent.js
// component=Grandparent

const figma = require("figma");
const instance = figma.selectedInstance;

const parents = instance.findConnectedInstances(
  (node) => node.codeConnectId() === "parent",
);

export default {
  example: figma.html`<ds-grandparent>
${parents
  .map(
    (node, i) => node.executeTemplate().metadata.props.special + " index: " + i,
  )
  .join("\n")}
</ds-grandparent>`,
  id: "grandparent",
  metadata: { nestable: true },
};
```

```js
// url=https://www.figma.com/design?node-id=7699-6921
// source=src/components/Parent.js
// component=Parent

const figma = require("figma");
const instance = figma.selectedInstance;

let childCode;
let special;
const node = instance.findConnectedInstance("child");
if (node && node.type === 'INSTANCE') {
  const { metadata, example } = node.executeTemplate();
  childCode = example;
  special = `<wow-special>${metadata.props.special}</wow-special>`;
}

export default {
  example: figma.html`<ds-parent>
${childCode}
</ds-parent>`,
  id: "parent",
  metadata: { nestable: true, props: { special } },
};
```

```js
// url=https://www.figma.com/design?node-id=7699-6922
// source=src/components/Child.js
// component=Child

const figma = require("figma");

export default {
  example: figma.html`<ds-child>normal stuff</ds-child>`,
  id: "child",
  metadata: { nestable: true, props: { special: "Special Stuff!!! 🤩" } },
};
```

```html
<!-- Child snippet: -->
<ds-child>normal stuff</ds-child>

<!-- Parent snippet: -->
<ds-parent>
  <ds-child>normal stuff</ds-child>
</ds-parent>

<!-- Grandparent snippet: -->
<ds-grandparent>
  <wow-special>Special Stuff!!! 🤩</wow-special> index: 0
  <wow-special>Special Stuff!!! 🤩</wow-special> index: 1
  <wow-special>Special Stuff!!! 🤩</wow-special> index: 2
</ds-grandparent>
```

---

## Reference — Code Connect Template API Reference

### Overview

Code Connect uses template files (`.figma.js`) to connect your code components to Figma designs. This API reference covers the complete template system for creating these mappings.

### Quick Start

A minimal Code Connect template:

```javascript
// url=https://www.figma.com/file/abc123/MyFile?node-id=123-456
// source=src/components/Button.tsx
// component=Button
const figma = require('figma')
const instance = figma.selectedInstance

const label = instance.getString('Label')

export default {
  example: figma.code`<Button label="${label}" />`,
  imports: ['import { Button } from "./Button"'],
  id: 'button'
}
```

### Table of Contents

1. [Project Configuration](#project-configuration)
2. [Template File Structure](#template-file-structure)
3. [Core API Reference](#core-api-reference)
4. [Working with Properties](#working-with-properties)
5. [Working with Nested Components](#working-with-nested-components)
6. [Publishing and Management](#publishing-and-management)
7. [Type Reference](#type-reference)

---

### Project Configuration

#### `figma.config.json`

Place this file in your project root to configure Code Connect.

##### Required Configuration

```json
{
  "codeConnect": {
    "include": ["**/*.figma.js"],
    "label": "React",
    "language": "tsx"
  }
}
```

##### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `include` | `string[]` | Globs for where to find Code Connect files (relative to config file) |
| `exclude` | `string[]` | Globs for files to exclude (e.g., `["test/**", "build/**"]`) |
| `label` | `string` | Label shown in Figma Dev Mode for your snippets |
| `language` | `string` | Language for syntax highlighting (see supported languages below) |
| `documentUrlSubstitutions` | `object` | URL substitutions for multiple Figma files |

##### Supported Languages

`jsx`, `tsx`, `typescript`, `javascript`, `swift`, `kotlin`, `html`, `css`, `json`, `python`, `go`, `rust`, `bash`, `xml`, `dart`, `ruby`, `cpp`, `sql`, `graphql`, `plaintext`

##### URL Substitutions Example

```json
{
  "codeConnect": {
    "documentUrlSubstitutions": {
      "<PROD_FILE>": "https://figma.com/design/abc123/Production",
      "<TEST_FILE>": "https://figma.com/design/xyz789/Testing"
    }
  }
}
```

Use placeholders in templates:
```javascript
// url=<PROD_FILE>?node-id=123-456
// source=<path to code component>
// component=<component name>
```

---

### Template File Structure

#### File Naming

Templates must use the `.figma.js` extension:
- `Button.figma.js`
- `Card.figma.js`
- `MyComponent.figma.js`

#### Required Metadata Comments

Every template starts with metadata comments:

```javascript
// url=https://www.figma.com/file/abc123/MyFile?node-id=123-456
// source=src/components/Button.tsx
// component=Button
```

**Getting the URL:** In Figma, right-click component → "Copy link to selection"

#### Export Structure

```typescript
export default {
  example: ResultSection[],      // Required: The code snippet
  id: string,                    // Required: Unique identifier
  imports?: string[],            // Optional: Import statements
  metadata?: {                   // Optional: Display settings
    nestable?: boolean,          // Show inline (true) or as pill (false)
    props?: Record<string, any>  // Data for parent templates
  }
}
```

#### Complete Example

```javascript
// url=https://www.figma.com/file/abc123/MyFile?node-id=123-456
// source=src/Button.tsx
// component=Button

const figma = require('figma')
const instance = figma.selectedInstance

// Extract properties from Figma
const label = instance.getString('Label')
const variant = instance.getEnum('Variant', {
  Primary: 'primary',
  Secondary: 'secondary'
})
const disabled = instance.getBoolean('Disabled')
const icon = instance.findInstance('Icon')

export default {
  example: figma.code`
    <Button
      variant="${variant}"
      ${disabled ? 'disabled' : ''}
      ${icon ? figma.code`icon={${icon.executeTemplate().example}}` : ''}
    >
      ${label}
    </Button>
  `,
  imports: ['import { Button } from "./Button"'],
  id: 'button',
  metadata: {
    nestable: true
  }
}
```

---

### Core API Reference

#### `figma` Object

Import with: `const figma = require('figma')`

##### `figma.selectedInstance: InstanceHandle`

The currently selected Figma component instance. This is your main entry point for accessing component data.

##### Tagged Template Literals

Use these to wrap your code snippets for proper syntax highlighting:

| Template | Use For |
|----------|---------|
| `figma.code` | Generic code (fallback) |
| `figma.tsx` | React/TypeScript JSX |
| `figma.jsx` | React JavaScript |
| `figma.html` | HTML markup |
| `figma.swift` | Swift code |
| `figma.kotlin` | Kotlin code |

**Example:**
```javascript
const example = figma.tsx`<MyComponent prop="${value}" />`
```

**Important:** Never use string concatenation on template results. Always wrap in `figma.code`:

```javascript
// Wrong
const snippet = iconSnippet + buttonSnippet

// Correct
const snippet = figma.code`${iconSnippet}${buttonSnippet}`
```

##### `figma.helpers`

Helper utilities for rendering code patterns:

**React Helpers:**
```javascript
figma.helpers.react.renderProp('propName', value)
figma.helpers.react.renderChildren(children)
figma.helpers.react.jsxElement('<Icon />')
```

##### `figma.properties`

Access child components by type:

```javascript
const buttons = figma.properties.children(['Button'])
const icons = figma.properties.children(['Icon', 'Avatar'])
```

---

### Working with Properties

#### Reading Component Properties

##### `getString(propName: string): string`

Gets a text property value from the Figma component.

```javascript
const label = instance.getString('Label')
const placeholder = instance.getString('Placeholder Text')
```

##### `getBoolean(propName: string, mapping?: object): boolean | any`

Gets a boolean property with optional value mapping.

```javascript
// Simple boolean
const isDisabled = instance.getBoolean('Disabled')

// Map to custom values
const hasIcon = instance.getBoolean('Has Icon', {
  true: figma.code`<Icon />`,
  false: null
})
```

##### `getEnum(propName: string, mapping: object): any`

Maps Figma variant values to code values.

```javascript
const size = instance.getEnum('Size', {
  Small: 'sm',
  Medium: 'md',
  Large: 'lg'
})

const variant = instance.getEnum('Variant', {
  Primary: 'primary',
  Secondary: 'secondary',
  Tertiary: 'tertiary'
})
```

##### `getInstanceSwap(propName: string): InstanceHandle`

Gets a swapped instance from an instance swap property.

```javascript
const icon = instance.getInstanceSwap('Icon')
if (icon) {
  const iconCode = icon.executeTemplate().example
}
```

##### `getSlot(propName: string): ResultSection[] | undefined`

Reads a Figma component property whose type is **`SLOT`** (not **INSTANCE_SWAP**). Returns a `ResultSection[]` containing a slot section (`type: 'SLOT'`). Returns `undefined` if the property is missing or invalid. Do not call `executeTemplate()` on this value — unlike `getInstanceSwap()`, it is not an `InstanceHandle`.

```javascript
const content = instance.getSlot('Content')

export default {
  example: figma.code`<Card>${content}</Card>`
}
```

##### `getPropertyValue(propName: string): string | boolean`

Gets the raw property value without mapping.

```javascript
const rawValue = instance.getPropertyValue('Some Property')
```

#### Property Patterns

##### Conditional Properties

```javascript
const showIcon = instance.getBoolean('Has Icon')
const icon = showIcon ? instance.findInstance('Icon') : null

export default {
  example: figma.code`
    <Button ${icon ? figma.code`icon={${icon.executeTemplate().example}}` : ''}>
      Click me
    </Button>
  `
}
```

##### Combining Properties

```javascript
const variant = instance.getEnum('Variant', { Primary: 'primary', Secondary: 'secondary' })
const size = instance.getEnum('Size', { Small: 'sm', Large: 'lg' })
const disabled = instance.getBoolean('Disabled')

export default {
  example: figma.code`
    <Button
      variant="${variant}"
      size="${size}"
      ${disabled ? 'disabled' : ''}
    />
  `
}
```

---

### Working with Nested Components

#### Finding Child Layers

##### `findInstance(layerName: string, opts?: SelectorOptions): InstanceHandle | ErrorHandle`

Finds a child component instance by layer name.

```javascript
const icon = instance.findInstance('Icon')
const avatar = instance.findInstance('Avatar')
```

**With selector options:**
```javascript
// Find by exact path
const icon = instance.findInstance('Icon', {
  path: ['Header', 'IconSlot']
})

// Search through nested instances
const deepIcon = instance.findInstance('Icon', {
  traverseInstances: true
})
```

##### `findText(layerName: string, opts?: SelectorOptions): TextHandle | ErrorHandle`

Finds a text layer by name.

```javascript
const heading = instance.findText('Heading')
const body = instance.findText('Body Text')

// Access text content
const headingText = heading.textContent
```

##### `findConnectedInstance(codeConnectId: string, opts?: SelectorOptions): InstanceHandle | ErrorHandle`

Finds a child by its Code Connect ID.

> **Note:** Returns `ErrorHandle` (not `null`) when no match is found. Check `result.type === 'INSTANCE'` before calling `hasCodeConnect()`.

```javascript
// Find component with specific Code Connect ID
const button = instance.findConnectedInstance('primary-button')
```

##### `findConnectedInstances(selector: (node: InstanceHandle) => boolean, opts?: SelectorOptions): InstanceHandle[]`

Finds all child instances matching a selector function.

```javascript
// Find all buttons
const buttons = instance.findConnectedInstances(node => {
  return node.codeConnectId() === 'button'
})

// Find all instances with certain property
const primaryButtons = instance.findConnectedInstances(node => {
  return node.getPropertyValue('Variant') === 'Primary'
})
```

##### `findLayers(selector: (node: InstanceHandle | TextHandle) => boolean, opts?: SelectorOptions): (InstanceHandle | TextHandle)[]`

Finds all layers (instances and text) matching a selector.

```javascript
// Find all layers with specific names
const layers = instance.findLayers(node => {
  return node.name === 'Icon' || node.name === 'Label'
})
```

#### Executing Nested Templates

##### `executeTemplate(): { example: ResultSection[], metadata: Metadata }`

Renders a nested instance and returns its code and metadata.

```javascript
const icon = instance.findInstance('Icon')

if (icon && icon.type === 'INSTANCE' && icon.hasCodeConnect()) {
  const result = icon.executeTemplate()
  const iconCode = result.example
  const iconProps = result.metadata.props
}
```

#### Instance Information

##### `hasCodeConnect(): boolean`

Checks if an instance has Code Connect configured.

```javascript
const icon = instance.findInstance('Icon')

if (icon && icon.type === 'INSTANCE' && icon.hasCodeConnect()) {
  const iconCode = icon.executeTemplate().example
} else {
  // Fallback when no Code Connect
  const iconCode = figma.code`<Icon />`
}
```

##### `codeConnectId(): string | null`

Returns the Code Connect ID of the instance.

```javascript
const id = instance.codeConnectId()
// Returns the 'id' from the template's export
```

#### Nested Component Patterns

##### Simple Nested Component

```javascript
const figma = require('figma')
const instance = figma.selectedInstance

const label = instance.getString('Label')
const icon = instance.findInstance('Icon')

export default {
  example: figma.code`
    <Button
      label="${label}"
      ${icon ? figma.code`icon={${icon.executeTemplate().example}}` : ''}
    />
  `,
  id: 'button-with-icon'
}
```

##### Multiple Nested Components

```javascript
const buttons = instance.findConnectedInstances(node => {
  return node.codeConnectId() === 'button'
})

const buttonElements = buttons.map(btn => btn.executeTemplate().example)

export default {
  example: figma.code`
    <ButtonGroup>
      ${buttonElements.join('\n')}
    </ButtonGroup>
  `
}
```

##### Nested with Metadata

```javascript
// Child component
export default {
  example: figma.code`<Icon name="${name}" />`,
  id: 'icon',
  metadata: {
    nestable: true,
    props: { iconName: name }
  }
}

// Parent component
const icon = instance.findConnectedInstance('icon')
if (icon) {
  const result = icon.executeTemplate()
  const iconName = result.metadata.props.iconName
  // Use iconName in parent logic
}
```

##### Children Pattern

```javascript
const children = figma.properties.children(['Card', 'Button'])

export default {
  example: figma.code`
    <Container>
      ${children.map(child => child.executeTemplate().example).join('\n')}
    </Container>
  `,
  id: 'container'
}
```

---

### Publishing and Management

#### Installation

```bash
npm install --global @figma/code-connect@latest
```

#### Publishing Code Connect Files

Publish all templates to make them visible in Figma Dev Mode:

```bash
npx figma connect publish --token=YOUR_ACCESS_TOKEN
```

**Using environment variable:**
```bash
export FIGMA_ACCESS_TOKEN=your_token_here
npx figma connect publish
```

**With custom config:**
```bash
npx figma connect publish --config path/to/figma.config.json
```

#### Unpublishing

**Unpublish all files in config:**
```bash
npx figma connect unpublish
```

**Unpublish specific component:**
```bash
npx figma connect unpublish --node=https://figma.com/file/abc/File?node-id=123-456 --label=React
```

#### Migration from Old Format

Convert existing Code Connect files to template format:

```bash
npx figma connect migrate --outDir ./templates
```

**Test migrations:**
1. Set temporary label in `figma.config.json`
2. Publish to test: `npx figma connect publish`
3. Verify in Figma
4. Unpublish when done: `npx figma connect unpublish`

#### CLI Help

```bash
npx figma connect --help
npx figma connect publish --help
npx figma connect unpublish --help
```

---

### Type Reference

#### SelectorOptions

```typescript
interface SelectorOptions {
  /** Full path of parent layer names to match */
  path?: string[]

  /** Whether to search inside nested component instances */
  traverseInstances?: boolean
}
```

**Example:**
```javascript
// Find icon only in specific hierarchy
const icon = instance.findInstance('Icon', {
  path: ['Header', 'Actions', 'IconSlot']
})

// Search everywhere including nested instances
const anyIcon = instance.findInstance('Icon', {
  traverseInstances: true
})
```

#### Metadata

```typescript
interface Metadata {
  /**
   * Controls display in Code Connect panel:
   * - true: Shows code inline with parent
   * - false: Shows as expandable pill
   */
  nestable?: boolean

  /** Custom data accessible to parent templates */
  props?: Record<string, any>
}
```

> **Important:** `nestable` must be set in **two places** for nested templates to work correctly:
> 1. **`templateDataJson`** when calling `add_code_connect_map` — e.g. `'{"isParserless": true, "nestable": true}'`. This controls whether the child template is loaded into the parent's evaluation context. If missing, the parent cannot find or execute the child via `findConnectedInstance`, `findConnectedInstances`, or `hasCodeConnect()`.
> 2. **`metadata.nestable`** in the template's `export default` — controls the runtime rendering behavior (inline code vs. clickable pill).

#### ResultSection Types

```typescript
type CodeSection = {
  type: "CODE"
  code: string
}

type InstanceSection = {
  type: "INSTANCE"
  guid: string      // Instance layer ID
  symbolId: string  // Component ID
}

type ErrorSection = {
  type: "ERROR"
  message: string
  errorObject?: ResultError
}

type ResultSection = CodeSection | InstanceSection | ErrorSection
```

#### Template Result

```typescript
type SectionsResult = {
  result: "SUCCESS"
  data: {
    type: "SECTIONS"
    sections: ResultSection[]
    language: string
    metadata?: {
      __props: Record<string, any>
      [key: string]: any
    }
  }
}
```

#### Error Types

```typescript
type PropertyNotFoundError = {
  type: "PROPERTY_NOT_FOUND"
  propertyName: string
}

type ChildLayerNotFoundError = {
  type: "CHILD_LAYER_NOT_FOUND"
  layerName: string
}

type PropertyTypeMismatchError = {
  type: "PROPERTY_TYPE_MISMATCH"
  propertyName: string
  expectedType: string
}

type TemplateExecutionError = {
  type: "TEMPLATE_EXECUTION_ERROR"
}

type ResultError =
  | PropertyNotFoundError
  | PropertyTypeMismatchError
  | ChildLayerNotFoundError
  | TemplateExecutionError
```

---

### Complete Examples

#### Button with States

```javascript
// url=https://www.figma.com/file/abc/Components?node-id=1-2
// source=src/components/Button.tsx
// component=Button

const figma = require('figma')
const instance = figma.selectedInstance

const label = instance.getString('Label')
const variant = instance.getEnum('Variant', {
  Primary: 'primary',
  Secondary: 'secondary',
  Tertiary: 'tertiary'
})
const size = instance.getEnum('Size', {
  Small: 'sm',
  Medium: 'md',
  Large: 'lg'
})
const disabled = instance.getBoolean('Has Disabled State')
const hasIcon = instance.getBoolean('Has Icon')
const icon = hasIcon ? instance.getInstanceSwap('Icon') : null

export default {
  example: figma.tsx`
    <Button
      variant="${variant}"
      size="${size}"
      ${disabled ? 'disabled' : ''}
      ${icon ? figma.tsx`icon={${icon.executeTemplate().example}}` : ''}
    >
      ${label}
    </Button>
  `,
  imports: ['import { Button } from "@/components/Button"'],
  id: 'button',
  metadata: {
    nestable: true
  }
}
```

#### Card with Children

```javascript
// url=https://www.figma.com/file/abc/Components?node-id=10-20
// source=src/components/Card.tsx
// component=Card

const figma = require('figma')
const instance = figma.selectedInstance

const heading = instance.findText('Heading')
const body = instance.findText('Body')
const actions = figma.properties.children(['Button'])
const variant = instance.getEnum('Variant', {
  Elevated: 'elevated',
  Outlined: 'outlined',
  Filled: 'filled'
})

export default {
  example: figma.tsx`
    <Card variant="${variant}">
      <Card.Header>
        ${heading.textContent}
      </Card.Header>
      <Card.Body>
        ${body.textContent}
      </Card.Body>
      <Card.Actions>
        ${actions.map(action => action.executeTemplate().example).join('\n')}
      </Card.Actions>
    </Card>
  `,
  imports: ['import { Card } from "@/components/Card"'],
  id: 'card',
  metadata: {
    nestable: false
  }
}
```

#### Form Field with Validation

```javascript
// url=https://www.figma.com/file/abc/Components?node-id=30-40
// source=src/components/TextField.tsx
// component=TextField

const figma = require('figma')
const instance = figma.selectedInstance

const label = instance.getString('Label')
const placeholder = instance.getString('Placeholder')
const helperText = instance.findText('Helper Text')
const errorState = instance.getEnum('State', {
  Default: false,
  Error: true
})
const required = instance.getBoolean('Required')
const disabled = instance.getBoolean('Disabled')

export default {
  example: figma.tsx`
    <TextField
      label="${label}"
      placeholder="${placeholder}"
      ${helperText ? `helperText="${helperText.textContent}"` : ''}
      ${errorState ? 'error' : ''}
      ${required ? 'required' : ''}
      ${disabled ? 'disabled' : ''}
    />
  `,
  imports: ['import { TextField } from "@/components/TextField"'],
  id: 'text-field'
}
```

#### Navigation with Dynamic Items

```javascript
// url=https://www.figma.com/file/abc/Components?node-id=50-60
// source=src/components/Navigation.tsx
// component=Navigation

const figma = require('figma')
const instance = figma.selectedInstance

const items = instance.findConnectedInstances(node => {
  return node.codeConnectId() === 'nav-item'
})

const direction = instance.getEnum('Direction', {
  Horizontal: 'horizontal',
  Vertical: 'vertical'
})

export default {
  example: figma.tsx`
    <Navigation direction="${direction}">
      ${items.map(item => item.executeTemplate().example).join('\n')}
    </Navigation>
  `,
  imports: ['import { Navigation } from "@/components/Navigation"'],
  id: 'navigation',
  metadata: {
    nestable: false
  }
}
```

---

### Best Practices

#### 1. Use Descriptive IDs

```javascript
// Good - clear and descriptive
export default {
  id: 'primary-button',
  // ...
}

// Avoid - too generic
export default {
  id: 'btn',
  // ...
}
```

#### 2. Handle Missing Properties Gracefully

```javascript
// Good - check type before calling hasCodeConnect
const icon = instance.findInstance('Icon')
const iconCode = icon && icon.type === 'INSTANCE' && icon.hasCodeConnect()
  ? icon.executeTemplate().example
  : null

// Avoid - assumes icon exists
const iconCode = instance.findInstance('Icon').executeTemplate().example
```

#### 3. Use Appropriate Tagged Templates

```javascript
// Good - use specific template for language
const example = figma.tsx`<Button />`

// Avoid - generic when specific is available
const example = figma.code`<Button />`
```

#### 4. Keep Templates Focused

```javascript
// Good - one component per file
export default {
  example: figma.tsx`<Button {...props} />`,
  id: 'button'
}

// Avoid - multiple components in one template
export default {
  example: figma.tsx`
    <Button />
    <Input />
    <Select />
  `
}
```

#### 5. Use Metadata Appropriately

```javascript
// Good - small inline components
export default {
  id: 'icon',
  metadata: { nestable: true }
}
// Also set in templateDataJson when registering: {"isParserless": true, "nestable": true}

// Good - complex components as pills
export default {
  id: 'modal',
  metadata: { nestable: false }
}
```

**Note:** If using `add_code_connect_map`, `nestable` must also be set in `templateDataJson` for the child to be discoverable by parent templates. Setting `metadata: { nestable: true }` in the template alone is not sufficient — the stored `templateData.nestable` controls whether the child is loaded into `instanceTemplates`.

---

### Troubleshooting

#### Property Not Found

**Error:** `Property "Label" not found`

**Solution:** Check property name in Figma matches exactly (case-sensitive):
```javascript
// Property name in Figma: "Button Label"
const label = instance.getString('Button Label')
```

#### Layer Not Found

**Error:** `Child layer "Icon" not found`

**Solution:** Verify layer name and try with path:
```javascript
const icon = instance.findInstance('Icon', {
  path: ['Content', 'IconSlot'],
  traverseInstances: true
})
```

#### Type Mismatch

**Error:** `Property type mismatch`

**Solution:** Use correct method for property type:
- Text properties → `getString()`
- Boolean properties → `getBoolean()`
- Variant properties → `getEnum()`
- Instance swap → `getInstanceSwap()`

#### Template Not Rendering

**Issue:** Template doesn't appear in Figma

**Solution:**
1. Ensure URL comment matches component exactly
2. Check `figma.config.json` includes the file pattern
3. Verify file was published: `npx figma connect publish`
4. Check Figma file permissions

#### Invalid Code Sections

**Issue:** Code appears broken in Figma

**Solution:** Never concatenate template results:
```javascript
// Wrong
const result = snippet1 + snippet2

// Correct
const result = figma.code`${snippet1}${snippet2}`
```
