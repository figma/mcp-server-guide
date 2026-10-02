# Code Connect Batch Files

## Contents
- [Overview](#overview)
- [When to use batch files](#when-to-use-batch-files)
- [File structure](#file-structure)
- [Writing a batch template](#writing-a-batch-template)
  - [`figma.batch`](#figmabatch)
- [Writing the JSON file](#writing-the-json-file)
  - [Single template (shorthand)](#single-template-shorthand)
  - [Multiple templates](#multiple-templates)
- [Setup](#setup)
  - [Discovery](#discovery)
  - [Publishing](#publishing)
- [Complete example](#complete-example)
- [Rules and pitfalls](#rules-and-pitfalls)

## Overview

Batch files let you connect many Figma components to code using a single shared template. This is the recommended approach when you have a large number of components that follow the same structure — the most common example being icon libraries, where hundreds or thousands of icons share identical code patterns but each maps to a different Figma node.

Without batch files, each component would need its own `.figma.ts` file. Batch files collapse this into two files:

| File | Purpose |
|---|---|
| `*.figma.batch.ts` | Template describing the code shape |
| `*.figma.batch.json` | List of every component with its Figma URL and any custom data |

## When to use batch files

Use batch files instead of the per-component `.figma.ts` workflow (Steps 1–6 in the main skill) when **all** of the following are true:

- There are many components (typically dozens to thousands) that render with the **same code shape** — only the per-instance data (name, import path, id, variant flags, etc.) changes.
- The components are visually/structurally distinct Figma nodes but map to the same props pattern in code (e.g. one icon component per icon, each imported from its own path).
- Hand-writing one `.figma.ts` file per component would be pure repetition — the `example`/`imports`/`id` logic would be identical except for substituted values.

If each component has meaningfully different logic (different variant handling, different nesting, different prop shapes), use the regular per-component `.figma.ts` workflow instead — don't force it into a single batch template.

## File structure

A batch integration consists of two files, conventionally named after the shared pattern they cover (e.g. `icons.figma.batch.ts` / `icons.figma.batch.json`):

- **Template** (`*.figma.batch.ts`) — a template file, structured like a regular [template file](api.md), with two differences:
  1. There are **no metadata comments** (`// url=`, `// source=`, `// component=`) at the top — those values come from the JSON file instead.
  2. Per-component data is accessed via `figma.batch` rather than being hardcoded or read from component properties alone.
- **JSON file** (`*.figma.batch.json`) — lists every component covered by the batch, each with its Figma URL and any custom fields the template needs.

## Writing a batch template

```ts
import figma from 'figma'
const instance = figma.selectedInstance

const size = instance.getEnum('Size', {
  Small: '16px',
  Medium: '24px',
  Large: '32px',
})

export default {
  example: figma.code`
    <${figma.batch.name} size={${size}} />
  `,
  imports: [`import ${figma.batch.name} from "${figma.batch.importPath}"`],
  id: figma.batch.id,
}
```

Note that `instance` (and the rest of the regular Template API in [api.md](api.md)) is still available inside a batch template — use it to read component properties off the currently-evaluated instance exactly as in a normal template. `figma.batch` supplies the additional per-component data that comes from the JSON file rather than from Figma itself.

### `figma.batch`

`figma.batch` gives the template access to data defined in the JSON file for the component currently being evaluated. Three fields have special meaning, corresponding to the metadata comments used in regular template files:

| Field | Required | Replaces |
|---|---|---|
| `url` | Yes | `// url=` |
| `source` | No | `// source=` |
| `component` | No | `// component=` |

Any additional fields defined in the JSON file (e.g. `name`, `id`, `importPath` above) are also available on `figma.batch`, letting the template reference per-component values without hardcoding them:

```ts
figma.code`<MyComponent ${figma.batch.myCustomField} />`
```

The full type of `figma.batch` is:

```ts
figma.batch: {
  url: string
  source?: string
  component?: string
  [key: string]: any
}
```

## Writing the JSON file

The JSON file defines which components belong to a batch and what data each one provides to the template. Every entry **must** include a `url` — the rest of the fields are arbitrary and are passed straight through to `figma.batch`.

### Single template (shorthand)

When all components share one template, use the shorthand format with a `templateFile` and a `components` array:

```json
{
  "templateFile": "./icons.figma.batch.ts",
  "components": [
    {
      "url": "https://www.figma.com/design/ABC/File?node-id=1-1",
      "name": "Icon24Arrow",
      "id": "icon-arrow",
      "importPath": "@company/icons/arrow",
      "source": "./src/icons/Icon24Arrow.tsx"
    },
    {
      "url": "https://www.figma.com/design/ABC/File?node-id=1-2",
      "name": "Icon24Check",
      "id": "icon-check",
      "importPath": "@company/icons/check",
      "source": "./src/icons/Icon24Check.tsx"
    }
  ]
}
```

### Multiple templates

If a single `.figma.batch.json` file should cover components that use different templates (e.g. icons and buttons in the same design system), use an array at the top level instead of a single object:

```json
[
  {
    "templateFile": "./icons.figma.batch.ts",
    "components": [
      {
        "url": "https://www.figma.com/design/ABC/File?node-id=1-1",
        "name": "Icon24Arrow",
        "id": "icon-arrow",
        "importPath": "@company/icons/arrow"
      }
    ]
  },
  {
    "templateFile": "./buttons.figma.batch.ts",
    "components": [
      {
        "url": "https://www.figma.com/design/ABC/File?node-id=2-1",
        "name": "PrimaryButton",
        "id": "button-primary",
        "importPath": "@company/buttons/primary"
      }
    ]
  }
]
```

## Setup

### Discovery

The CLI discovers batch files through the same `include`/`exclude` mechanism as all other Code Connect files. The default include globs already include `**/*.figma.batch.json`, so batch files work out of the box for projects that don't define a custom `include` in `figma.config.json`.

If the project defines a custom `include` list, add the batch glob explicitly:

```json
{
  "codeConnect": {
    "include": ["**/*.figma.ts", "**/*.figma.batch.json"],
    "label": "React",
    "language": "jsx"
  }
}
```

The template files (`.figma.batch.ts`) referenced by `templateFile` do **not** need to appear in `include` — they are read on demand when the CLI processes the JSON file.

### Publishing

Once the files are in place, publish the same way as any other Code Connect file:

```bash
npx figma connect publish
```

Each entry in the `components` array is published as an independent Code Connect doc. Unpublishing also works automatically — each component is removed individually by its Figma node URL.

## Complete example

A library of icons where each icon supports a `Size` variant and is imported from a package path unique to that icon, with some icons offering an outlined variant wrapper:

`icons.figma.batch.ts`:
```ts
import figma from 'figma'
const instance = figma.selectedInstance

const size = instance.getEnum('Size', {
  Small: '16px',
  Medium: '24px',
  Large: '32px',
})

const iconSnippet = figma.code`
  <${figma.batch.name} size={${size}} />
`

const importsList = figma.batch.withOutline
  ? figma.batch.name
  : [figma.batch.name, 'IconOutline'].join(', ')

export default {
  example: figma.batch.withOutline
    ? figma.code`<IconOutline>${iconSnippet}</IconOutline>`
    : iconSnippet,
  imports: [`import { ${importsList} } from "${figma.batch.importPath}"`],
  id: figma.batch.id,
  metadata: {
    nestable: true,
  },
}
```

`icons.figma.batch.json`:
```json
{
  "templateFile": "./icons.figma.batch.ts",
  "components": [
    {
      "url": "https://www.figma.com/design/XYZ/Icons?node-id=10-1",
      "name": "ArrowIcon",
      "id": "icon-arrow",
      "withOutline": false,
      "importPath": "@acme/icons",
      "source": "./src/icons/ArrowIcon.tsx"
    },
    {
      "url": "https://www.figma.com/design/XYZ/Icons?node-id=10-2",
      "name": "CheckIcon",
      "id": "icon-check",
      "withOutline": true,
      "importPath": "@acme/icons",
      "source": "./src/icons/CheckIcon.tsx"
    },
    {
      "url": "https://www.figma.com/design/XYZ/Icons?node-id=10-3",
      "name": "CloseIcon",
      "id": "icon-close",
      "withOutline": true,
      "importPath": "@acme/icons",
      "source": "./src/icons/CloseIcon.tsx"
    }
  ]
}
```

## Rules and pitfalls

1. **Never name a batch template `*.figma.ts`.** It must end in `.figma.batch.ts`, and its companion data file must end in `.figma.batch.json` — the CLI distinguishes batch files from regular templates by these suffixes.
2. **Do not add `// url=`, `// source=`, or `// component=` comments to a batch template.** Those values live in the JSON file (`url`, `source`, `component` fields) and are injected via `figma.batch`; leftover metadata comments in a batch template are ignored/incorrect.
3. **Every JSON entry must have a `url`.** `source` and `component` are optional (mirroring the optional metadata comments in regular templates), but omitting `url` leaves the CLI unable to resolve which Figma node the entry maps to.
4. **Keep `id` unique per entry**, exactly as with regular templates — duplicate ids across a batch cause the same collision issues as duplicate `id`s across separate `.figma.ts` files.
5. **Don't hardcode per-component values in the template.** If a value differs between components (name, import path, id, variant flags), it belongs in the JSON file as a `figma.batch` field — not inlined in the `.ts` template, which must stay identical for every component it covers.
6. **Use the multiple-templates array form** when one `.figma.batch.json` needs to cover component families with genuinely different template logic (e.g. icons vs. buttons) — don't force unrelated shapes into one template just to keep a single JSON file.
7. **`templateFile` paths are resolved relative to the JSON file's location**, not the project root — keep the template and JSON file together (or use a correct relative path) when they live in different directories.
8. **Regular Template API methods are still available.** `instance.getString`, `getEnum`, `getBoolean`, `getInstanceSwap`, etc. all work inside a batch template exactly as in a per-component template — `figma.batch` only supplements them with data that comes from the JSON file rather than from the Figma node itself.
