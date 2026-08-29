# Plugin API Index

> Full typings: `plugin-api-standalone.d.ts` (12,216 lines)
> Grep by symbol name to jump to definition. All `L#` line numbers refer to that file.
> This index describes the APIs available through `use_figma`. See the `.d.ts` for full type declarations.

---

## figma.\* — PluginAPI (L4)

### Identity & State

| Member                          | Type                                                                                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `apiVersion`                    | `'1.0.0'`                                                                                                                                        |
| `editorType`                    | `'figma' \| 'figjam' \| 'dev' \| 'slides' \| 'buzz'`                                                                                             |
| `fileKey`                       | `string \| undefined`                                                                                                                            |
| `root`                          | `DocumentNode`                                                                                                                                   |
| `currentPage`                   | `PageNode` — **read-only**; sync setter `figma.currentPage = page` does NOT work and throws; use `await figma.setCurrentPageAsync(page)` instead |
| `mixed`                         | `unique symbol` — sentinel for mixed values in selection                                                                                         |
| `skipInvisibleInstanceChildren` | `boolean`                                                                                                                                        |

### Navigation & Lookup

| Method                      | Returns                                                                                   |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| `setCurrentPageAsync(page)` | `Promise<void>` — **MUST use this**; sync setter `figma.currentPage = page` does NOT work |
| `getNodeByIdAsync(id)`      | `Promise<BaseNode \| null>`                                                               |
| `getStyleByIdAsync(id)`     | `Promise<BaseStyle \| null>`                                                              |

### Create Nodes

| Method                              | Returns                     |
| ----------------------------------- | --------------------------- |
| `createFrame()`                     | `FrameNode`                 |
| `createAutoLayout(direction?)`      | `FrameNode`                 |
| `createComponent()`                 | `ComponentNode`             |
| `createComponentFromNode(node)`     | `ComponentNode`             |
| `createRectangle()`                 | `RectangleNode`             |
| `createEllipse()`                   | `EllipseNode`               |
| `createLine()`                      | `LineNode`                  |
| `createPolygon()`                   | `PolygonNode`               |
| `createStar()`                      | `StarNode`                  |
| `createVector()`                    | `VectorNode`                |
| `createText()`                      | `TextNode`                  |
| `createSection()`                   | `SectionNode`               |
| `createPage()`                      | `PageNode`                  |
| `createSlice()`                     | `SliceNode`                 |
| `createBooleanOperation()`          | `BooleanOperationNode`      |
| `createTable(rows?, cols?)`         | `TableNode`                 |
| `createImage(data: Uint8Array)`     | `Image`                     |
| `createNodeFromSvg(svg)`            | `FrameNode`                 |
| `createNodeFromJSXAsync(jsx)`       | `Promise<SceneNode>`        |
| `importComponentByKeyAsync(key)`    | `Promise<ComponentNode>`    |
| `importComponentSetByKeyAsync(key)` | `Promise<ComponentSetNode>` |
| `importStyleByKeyAsync(key)`        | `Promise<BaseStyle>`        |

### Styles (Local)

| Method                        | Returns                  |
| ----------------------------- | ------------------------ |
| `createPaintStyle()`          | `PaintStyle`             |
| `createTextStyle()`           | `TextStyle`              |
| `createEffectStyle()`         | `EffectStyle`            |
| `createGridStyle()`           | `GridStyle`              |
| `getLocalPaintStylesAsync()`  | `Promise<PaintStyle[]>`  |
| `getLocalTextStylesAsync()`   | `Promise<TextStyle[]>`   |
| `getLocalEffectStylesAsync()` | `Promise<EffectStyle[]>` |
| `getLocalGridStylesAsync()`   | `Promise<GridStyle[]>`   |
| `createCustomAnimationStyle()` | `CustomAnimationStyle` |
| `getLocalCustomAnimationStylesAsync()` | `Promise<CustomAnimationStyle[]>` |
| `getLocalCustomAnimationStyles()` | `CustomAnimationStyle[]` (deprecated; use async) |
| `moveLocalCustomAnimationStyleAfter(targetNode, reference)` | `void`; reference may be `null` |
| `moveLocalCustomAnimationFolderAfter(targetFolder, reference)` | `void`; reference may be `null` |

### Fonts

| Method                      | Notes                              |
| --------------------------- | ---------------------------------- |
| `loadFontAsync(fontName)`   | **MUST call before any text edit** |
| `listAvailableFontsAsync()` | `Promise<Font[]>`                  |
| `hasMissingFont`            | `boolean`                          |

### Plugin Lifecycle

| Method                  | Notes                                                  |
| ----------------------- | ------------------------------------------------------ |
| `closePlugin(message?)` | Auto-called; use `return` instead to pass results back |

> Undo, notifications, external URLs, version-history saves, and `closePluginWithFailure` are not available through `use_figma`.

### Sub-APIs (properties on figma)

| Property            | Interface        | L#    |
| ------------------- | ---------------- | ----- |
| `figma.variables`   | `VariablesAPI`   | L1141 |
| `figma.motion`      | `MotionAPI`      | L1381 |
| `figma.util`        | `UtilAPI`        | L1419 |
| `figma.viewport`    | `ViewportAPI`    | L1543 |
| `figma.parameters`  | `ParametersAPI`  | L1661 |
| `figma.teamLibrary` | `TeamLibraryAPI` | L1337 |
| `figma.annotations` | `AnnotationsAPI` | L1271 |

> UI, client storage, codegen, payments, text review, timers, Buzz, and constants are not available through `use_figma`.

---

## VariablesAPI — figma.variables (L1141)

```
getVariableByIdAsync(id)                 Promise<Variable | null>    ← preferred; sync deprecated
getVariableCollectionByIdAsync(id)       Promise<VariableCollection | null>    ← preferred; sync deprecated
getLocalVariablesAsync(type?)            Promise<Variable[]>         ← preferred; filter by VariableResolvedDataType; sync deprecated
getLocalVariableCollectionsAsync()       Promise<VariableCollection[]>    ← preferred; sync deprecated
createVariable(name, collection, type)   Variable
createVariableCollection(name)           VariableCollection
createVariableAlias(variable)            VariableAlias
importVariableByKeyAsync(key)            Promise<Variable>
setBoundVariableForPaint(paint, field, variable)    → returns NEW paint — reassign
setBoundVariableForEffect(effect, field, variable)  → returns NEW effect — reassign
setBoundVariableForLayoutGrid(grid, field, variable)
```

**Variable (L9228):** `name`, `resolvedType`, `codeSyntax`, `scopes`, `hiddenFromPublishing`, `valuesByMode`, `variableCollectionId`

- `setVariableCodeSyntax(platform, value)` — platform: `'WEB' | 'ANDROID' | 'iOS'`
- `setValueForMode(modeId, value)`
- `remove()`

**VariableCollection (L9442):** `name`, `modes`, `variableIds`, `defaultModeId`, `hiddenFromPublishing`

- `addMode(name)` → `modeId`; `removeMode(modeId)`; `renameMode(modeId, name)`

---

## Node Types

### Concrete Scene Nodes

| Node                   | L#    | Key characteristics                                |
| ---------------------- | ----- | -------------------------------------------------- |
| `DocumentNode`         | L8040 | Root; `children: PageNode[]`                       |
| `PageNode`             | L8187 | `children`, local styles, `backgrounds`            |
| `FrameNode`            | L8321 | `DefaultFrameMixin` — auto-layout, clips, children |
| `GroupNode`            | L8331 | Children only, no auto-layout                      |
| `ComponentNode`        | L8695 | Like Frame + publishable                           |
| `ComponentSetNode`     | L8678 | Variant set container                              |
| `InstanceNode`         | L8730 | Like Frame; `mainComponent`, `detach()`            |
| `RectangleNode`        | L8388 | `DefaultShapeMixin` + corners                      |
| `EllipseNode`          | L8418 | + `arcData`                                        |
| `LineNode`             | L8407 |                                                    |
| `PolygonNode`          | L8439 |                                                    |
| `StarNode`             | L8460 |                                                    |
| `VectorNode`           | L8487 | Vector paths                                       |
| `TextNode`             | L8505 | Rich text, fonts, segments                         |
| `TextPathNode`         | L8577 | Text along path                                    |
| `BooleanOperationNode` | L8823 | `booleanOperation` property                        |
| `SliceNode`            | L8378 | Export only                                        |
| `SectionNode`          | L9719 | Grouping + fills                                   |
| `TableNode`            | L8884 | `TableCellNode` children                           |

**FigJam only:** `StickyNode` L8844, `ConnectorNode` L9145, `ShapeWithTextNode` L9026, `StampNode` L8870, `CodeBlockNode` L9104, `EmbedNode` L9626, `LinkUnfurlNode` L9666, `MediaNode` L9686

**Slides only:** `SlideNode` L9762, `SlideRowNode` L9792, `SlideGridNode` L9805

**Union types:**

```
type SceneNode  (L9893) = FrameNode | GroupNode | SliceNode | RectangleNode | LineNode
  | EllipseNode | PolygonNode | StarNode | VectorNode | TextNode | ComponentSetNode
  | ComponentNode | InstanceNode | BooleanOperationNode | SectionNode | ...
type BaseNode   (L9889) = DocumentNode | PageNode | SceneNode
```

---

## Mixin Interfaces

| Mixin                        | L#    | Provides                                                                                        |
| ---------------------------- | ----- | ----------------------------------------------------------------------------------------------- |
| `BaseNodeMixin`              | L4033 | `id`, `name`, `type`, `parent`, `remove()`, plugin data                                         |
| `SceneNodeMixin`             | L4181 | `visible`, `locked`, `opacity`, variable bindings                                               |
| `ChildrenMixin`              | L4559 | `children`, `appendChild()`, `insertChild()`, `findAll()`, `findOne()`, `findAllWithCriteria()` |
| `LayoutMixin`                | L4924 | `x`, `y`, `width`, `height`, `rotation`, `resize()`, `rescale()`                                |
| `AutoLayoutMixin`            | L5204 | `layoutMode`, axis alignment, padding, `itemSpacing`, `layoutSizingHorizontal/Vertical`         |
| `AutoLayoutChildrenMixin`    | L6024 | `layoutAlign`, `layoutGrow`, sizing — **set AFTER `appendChild()`**                             |
| `GridLayoutMixin`            | L5766 | CSS Grid tracks, gap, template                                                                  |
| `GridChildrenMixin`          | L6087 | grid child positioning                                                                          |
| `GeometryMixin`              | L6446 | `fills`, `strokes`, `strokeWeight`, `strokeAlign`                                               |
| `MinimalFillsMixin`          | L6290 | `fills` only                                                                                    |
| `MinimalStrokesMixin`        | L6208 | `strokes`, `strokeWeight`                                                                       |
| `BlendMixin`                 | L5120 | `opacity`, `blendMode`, `isMask`, `effects`                                                     |
| `CornerMixin`                | L6498 | `cornerRadius`, `cornerSmoothing`                                                               |
| `RectangleCornerMixin`       | L6521 | Per-corner radii                                                                                |
| `ExportMixin`                | L6542 | `exportSettings`, `exportAsync()`                                                               |
| `ReactionMixin`              | L6691 | `reactions` (prototyping)                                                                       |
| `PublishableMixin`           | L6862 | `description`, `key`, `getPublishStatusAsync()`                                                 |
| `ComponentPropertiesMixin`   | L7163 | `componentProperties`, `addComponentProperty()`                                                 |
| `PluginDataMixin`            | L4124 | `getSharedPluginData()`, `setSharedPluginData()`, `getSharedPluginDataKeys()`                   |
| `FramePrototypingMixin`      | L6638 | `overflowDirection`, `numberOfFixedChildren`                                                    |
| `BaseFrameMixin`             | L6928 | ChildrenMixin + LayoutMixin + AutoLayoutMixin + GeometryMixin + …                               |
| `DefaultFrameMixin`          | L6985 | BaseFrameMixin + FramePrototypingMixin + ReactionMixin                                          |
| `DefaultShapeMixin`          | L6916 | BlendMixin + GeometryMixin + LayoutMixin + ExportMixin + ReactionMixin                          |
| `ExplicitVariableModesMixin` | L8164 | `setExplicitVariableModeForCollection()`                                                        |

---

## Paint & Fill (L2741)

| Type            | L#    | Notes                                                                             |
| --------------- | ----- | --------------------------------------------------------------------------------- |
| `SolidPaint`    | L2538 | `type:'SOLID'`, `color: RGB`, `opacity`, `visible`, `blendMode`                   |
| `GradientPaint` | L2593 | `type: 'GRADIENT_LINEAR\|RADIAL\|ANGULAR\|DIAMOND'`, `gradientStops: ColorStop[]` |
| `ImagePaint`    | L2613 | `type:'IMAGE'`, `imageHash`, `scaleMode`                                          |
| `VideoPaint`    | L2649 | `type:'VIDEO'`                                                                    |
| `PatternPaint`  | L2685 | `type:'PATTERN'`                                                                  |
| `type Paint`    | L2741 | Union of all five                                                                 |
| `ColorStop`     | L2507 | `{ position: number, color: RGBA }`                                               |
| `ImageFilters`  | L2526 | exposure, contrast, saturation, etc.                                              |

> **CRITICAL**: Fills/strokes are **read-only arrays** — clone, modify, reassign.

---

## Effects (L2163)

| Type                               | L#    |
| ---------------------------------- | ----- |
| `DropShadowEffect`                 | L2163 |
| `InnerShadowEffect`                | L2206 |
| `BlurEffect` (Normal/Progressive)  | L2298 |
| `NoiseEffect` (Mono/Duo/Multitone) | L2379 |
| `TextureEffect`                    | L2383 |
| `GlassEffect`                      | L2419 |
| `type Effect`                      | L2485 |

---

## Typography

| Type                | L#    | Notes                                                                                  |
| ------------------- | ----- | -------------------------------------------------------------------------------------- |
| `FontName`          | L1850 | `{ family: string, style: string }`                                                    |
| `TextNode`          | L8505 | `characters`, `textAlignHorizontal`, `fontSize`, `fontName`, `getStyledTextSegments()` |
| `StyledTextSegment` | L3255 | Per-range text properties                                                              |
| `LetterSpacing`     | L3195 | `{ value, unit: 'PIXELS'\|'PERCENT' }`                                                 |
| `LineHeight`        | L3199 | `{ value, unit } \| { unit: 'AUTO' }`                                                  |
| `TextCase`          | L1898 | `'ORIGINAL'\|'UPPER'\|'LOWER'\|'TITLE'\|'SMALL_CAPS'`                                  |
| `TextDecoration`    | L1899 | `'NONE'\|'UNDERLINE'\|'STRIKETHROUGH'`                                                 |
| `OpenTypeFeature`   | L1925 | Ligatures, numerals, etc.                                                              |

---

## Variables & Bindings

| Type                          | L#    | Notes                                                                         |
| ----------------------------- | ----- | ----------------------------------------------------------------------------- |
| `Variable`                    | L9228 | Core variable object                                                          |
| `VariableCollection`          | L9442 | Collection of variables + modes                                               |
| `VariableAlias`               | L9196 | Reference to another variable                                                 |
| `VariableValue`               | L9200 | `boolean \| string \| number \| RGB \| RGBA \| MotionEasing \| VariableAlias` |
| `VariableResolvedDataType`    | L9195 | `'BOOLEAN' \| 'COLOR' \| 'FLOAT' \| 'STRING' \| 'TIMING' \| 'EASING'`         |
| `VariableDataType`            | L3396 | Includes `'VARIABLE_ALIAS' \| 'EXPRESSION'`                                   |
| `VariableScope`               | L9201 | Where variable can be applied                                                 |
| `CodeSyntaxPlatform`          | L9227 | `'WEB' \| 'ANDROID' \| 'iOS'`                                                 |
| `VariableBindableNodeField`   | L4497 | Node fields that accept variable binding                                      |
| `VariableBindableTextField`   | L4525 | Text-specific bindable fields                                                 |
| `VariableBindablePaintField`  | L4534 | `'color'`                                                                     |
| `VariableBindableEffectField` | L4537 | `'color'\|'radius'\|'spread'\|'offsetX'\|'offsetY'`                           |

---

## Styles

| Interface        | L#     | Notes                                                  |
| ---------------- | ------ | ------------------------------------------------------ |
| `BaseStyleMixin` | L9954  | `name`, `id`, `key`, `type`, `description`, `remove()` |
| `PaintStyle`     | L9974  | `type:'PAINT'`, `paints: Paint[]`                      |
| `TextStyle`      | L9990  | `type:'TEXT'`, font properties                         |
| `EffectStyle`    | L10063  | `type:'EFFECT'`, `effects: Effect[]`                   |
| `GridStyle`      | L10079  | `type:'GRID'`, `layoutGrids`                           |
| `CustomAnimationStyle` | L10095 | `type:'CUSTOM_ANIMATION'`, `animationEntries`, `addAnimationEntryAsync()`, `removeAnimationEntry()` |
| `type BaseStyle` | L10145 | Union of all five                                      |
| `type StyleType` | L9932  | `'PAINT' \| 'TEXT' \| 'EFFECT' \| 'GRID' \| 'CUSTOM_ANIMATION'`              |

---

## Animation Styles

`AnimationStyleConfiguration` and `AppliedAnimationStyle` distinguish Figma animations (`type: 'FIGMA'`) from custom styles (`type: 'CUSTOM'`). Narrow applied styles by `type` before reading Figma-only properties such as `props`. Custom styles accept `timelineOffset`; entry properties belong to `AnimationEntry`.

| Type | L# |
| ---- | -- |
| `FigmaAnimationStyleConfiguration` | L3639 |
| `CustomAnimationStyleConfiguration` | L3657 |
| `AnimationStyleConfiguration` | L3667 |
| `AppliedFigmaAnimationStyle` | L3672 |
| `AppliedCustomAnimationStyle` | L3684 |
| `AppliedAnimationStyle` | L3691 |
| `AnimationEntry` | L3698 |

---

## Primitives & Geometry

| Type             | L#    | Shape                                         |
| ---------------- | ----- | --------------------------------------------- |
| `Vector`         | L1799 | `{ x: number, y: number }`                    |
| `Rect`           | L1803 | `{ x, y, width, height }`                     |
| `RGB`            | L1812 | `{ r, g, b }` — **0–1 range, not 0–255**      |
| `RGBA`           | L1820 | `{ r, g, b, a }` — **0–1 range**              |
| `Transform`      | L1798 | `[[a,b,tx],[c,d,ty]]` 2×3 affine matrix       |
| `ArcData`        | L2155 | `{ startingAngle, endingAngle, innerRadius }` |
| `Constraints`    | L2500 | `{ horizontal, vertical }: ConstraintType`    |
| `ConstraintType` | L2496 | `'MIN'\|'CENTER'\|'MAX'\|'STRETCH'\|'SCALE'`  |
| `VectorPath`     | L3161 | `{ windingRule, data: string }`               |
| `VectorNetwork`  | L3144 | vertices + segments + regions                 |
| `Guide`          | L2851 | `{ axis, offset }`                            |

---

## Prototyping

| Type                  | L#    | Notes                                                     |
| --------------------- | ----- | --------------------------------------------------------- |
| `Reaction`            | L3392 | trigger + action pair                                     |
| `Trigger`             | L3504 | what initiates the reaction                               |
| `Action`              | L3431 | what happens                                              |
| `Transition`          | L3503 | `SimpleTransition \| DirectionalTransition`               |
| `Easing`              | L3540 | easing curve definition                                   |
| `Navigation`          | L3536 | `'NAVIGATE'\|'SWAP'\|'OVERLAY'\|'SCROLL_TO'\|'CHANGE_TO'` |
| `OverflowDirection`   | L3958 | `'NONE'\|'HORIZONTAL'\|'VERTICAL'\|'BOTH'`                |
| `OverlayPositionType` | L3962 | overlay placement                                         |

---

## Export

| Type                        | L#    | Notes                                         |
| --------------------------- | ----- | --------------------------------------------- |
| `ExportSettingsImage`       | L2930 | PNG/JPG/WEBP/BMP                              |
| `ExportSettingsSVG`         | L3003 |                                               |
| `ExportSettingsPDF`         | L3022 |                                               |
| `ExportSettingsREST`        | L3036 |                                               |
| `ExportSettingsConstraints` | L2923 | `{ type: 'SCALE'\|'WIDTH'\|'HEIGHT', value }` |

---

## Key Sub-API Surfaces

**ViewportAPI (L1543):** `center: Vector`, `zoom: number`, `scrollAndZoomIntoView(nodes)`, `bounds: Rect`

**UtilAPI (L1419):** `solidPaint(color, overrides?)`, `rgba(color)`, `rgb(color)`, `normalizeMarkdown(markdown)`, `getSfSymbolCharacter(name)`

**TeamLibraryAPI (L1337):** `getAvailableLibraryVariableCollectionsAsync()`, `importVariableByKeyAsync(key)`

**Image (L10146):** `hash`, `getBytesAsync()`, `getSizeAsync()`

---

## All Symbols (flat — grep these against the .d.ts file)

To find any symbol: `grep -n "^interface Foo\|^type Foo\|^declare type Foo" plugin-api-standalone.d.ts`

```
PluginAPI               VariablesAPI            AnnotationsAPI          TeamLibraryAPI
UIAPI                   UtilAPI                 ViewportAPI             ClientStorageAPI
ConstantsAPI            CodegenAPI              PaymentsAPI             TextReviewAPI
ParametersAPI           TimerAPI                BuzzAPI                 DevResourcesAPI

DocumentNode            PageNode                FrameNode               GroupNode
ComponentNode           ComponentSetNode        InstanceNode            RectangleNode
EllipseNode             LineNode                PolygonNode             StarNode
VectorNode              TextNode                TextPathNode            BooleanOperationNode
SliceNode               SectionNode             TableNode               TableCellNode
StickyNode              ConnectorNode           ShapeWithTextNode       StampNode
CodeBlockNode           EmbedNode               LinkUnfurlNode          MediaNode
WidgetNode              SlideNode               SlideRowNode            SlideGridNode
TransformGroupNode      HighlightNode           WashiTapeNode

BaseNodeMixin           SceneNodeMixin          ChildrenMixin           LayoutMixin
AutoLayoutMixin         AutoLayoutChildrenMixin GridLayoutMixin         GridChildrenMixin
GeometryMixin           MinimalFillsMixin       MinimalStrokesMixin     BlendMixin
MinimalBlendMixin       CornerMixin             RectangleCornerMixin    ExportMixin
ReactionMixin           PublishableMixin        VariantMixin            ComponentPropertiesMixin
PluginDataMixin         DevResourcesMixin       DevStatusMixin          StickableMixin
ConstraintMixin         DimensionAndPositionMixin AspectRatioLockMixin  FramePrototypingMixin
BaseFrameMixin          DefaultFrameMixin       DefaultShapeMixin       OpaqueNodeMixin
VectorLikeMixin         ComplexStrokesMixin     IndividualStrokesMixin  ContainerMixin
AnnotationsMixin        MeasurementsMixin       ExplicitVariableModesMixin

Variable                VariableCollection      VariableAlias           ExtendedVariableCollection
LibraryVariableCollection LibraryVariable
VariableValue           VariableResolvedDataType VariableDataType       VariableScope
CodeSyntaxPlatform      VariableBindableNodeField VariableBindableTextField
VariableBindablePaintField VariableBindableEffectField VariableBindableLayoutGridField

SolidPaint              GradientPaint           ImagePaint              VideoPaint
PatternPaint            Paint                   ColorStop               ImageFilters
DropShadowEffect        InnerShadowEffect       BlurEffect              NoiseEffect
TextureEffect           GlassEffect             Effect
LayoutGrid              RowsColsLayoutGrid      GridLayoutGrid

PaintStyle              TextStyle               EffectStyle             GridStyle
BaseStyle               BaseStyleMixin          StyleType

FontName                Font                    LetterSpacing           LineHeight
TextCase                TextDecoration          TextDecorationStyle     FontStyle
OpenTypeFeature         StyledTextSegment       LeadingTrim

Vector                  Rect                    RGB                     RGBA
Transform               ArcData                 Constraints             ConstraintType
VectorPath              VectorNetwork           VectorVertex            VectorSegment
VectorRegion            Guide                   BlendMode               MaskType

Reaction                Trigger                 Action                  Transition
Easing                  Navigation              OverflowDirection       OverlayPositionType
OverlayBackground       PublishStatus

ArgFreeEventType        RunEvent                DropEvent               DocumentChangeEvent
NodeChangeEvent         NodeChangeProperty      StyleChangeEvent        DocumentChange
TextReviewEvent         SlidesViewChangeEvent   CanvasViewChangeEvent

ExportSettingsImage     ExportSettingsSVG       ExportSettingsPDF       ExportSettingsREST
ExportSettingsConstraints

User                    ActiveUser              BaseUser                Image
Video                   VersionHistoryResult    FindAllCriteria

FigAPI                  FigDoneResult           FigQueryResult          FigPlanNode
FigPlanStyle            FigPlanPaintStyle       FigPlanTextStyle        FigPlanEffectStyle
FigPlanGridStyle        FigPlanVarCollection    FigPlanVariable
FigPlanColorVar         FigPlanNumVar           FigPlanBoolVar          FigPlanStringVar
GradientStop
```

---

## use_figma Conveniences

These helpers are available when running code with `use_figma`.

### Node Methods

| Method / Property                 | Returns / Type  | Description                                |
| --------------------------------- | --------------- | ------------------------------------------ |
| `node.query(selector)`            | `QueryResult`   | CSS-like selector search within subtree    |
| `node.matches(selector)`          | `boolean`       | Test if node matches a selector            |
| `node.set(props)`                 | `this`          | Set multiple properties at once, chainable |
| `await node.screenshot(options?)` | `Promise<void>` | Capture PNG inline in tool response        |
| `node.placeholder`                | `boolean`       | Show/hide shimmer overlay                  |

### figma.io Namespace

| Method                       | Returns | Description                                      |
| ---------------------------- | ------- | ------------------------------------------------ |
| `figma.io.write(path, data)` | `void`  | Write image/data to be returned in tool response |

### `$fig` Builder API

Plan-based builder — see [fig-builder.md](fig-builder.md) for details.

| Method | Returns | Description |
|---|---|---|
| `$fig.frame` / `.rectangle` / `.ellipse` / `.polygon` / `.star` / `.line` / `.vector` / `.text` / `.section` / `.component` / `.page` / `.slice` | `FigPlanNode` | Create a plan node of the given type: `(opts?, children?)` |
| `$fig.autoLayout(opts?, children?)` | `FigPlanNode` | `FRAME` with auto-layout pre-configured (both axes hugging content). Default direction `HORIZONTAL`; pass `layoutMode: 'VERTICAL'` in opts to switch. |
| `$fig.svg(svgString, opts?)`  | `FigPlanNode` | Create a node tree from SVG |
| `$fig.instance(compRef, opts?)` | `FigPlanNode` | Create an instance of a component (plan node or ID) |
| `$fig.group` / `.union` / `.subtract` / `.intersect` / `.exclude` / `.variants` | `FigPlanNode` | Wrap children in a group, boolean op, or component set |
| `$fig.get(id)` | `FigPlanNode` | Wrap an existing node by ID so it can be mutated |
| `$fig.query(selector, scope?)` | `FigQueryResult` | CSS selector search — same syntax as `node.query()` |
| `$fig.set(target, props)` | `FigPlanNode` | Update props on a plan node |
| `$fig.delete(...nodes)` | `void` | Remove nodes |
| `$fig.move(target, newParent, index?)` / `.clone(target, props?)` | `void` | Reparent / clone |
| `$fig.add(parent, child)` / `.append(parent, child)` / `.addAt(parent, index, child)` | `FigPlanNode` | Insert children |
| `$fig.replace(oldNode, newNode)` / `.reorder(parent, children)` | `FigPlanNode` | Swap / reorder |
| `$fig.gradient(node, type, stops, transform?)` / `.image(node, hash, scaleMode?)` | `void` | Paint shortcuts |
| `$fig.paintStyle` / `.textStyle` / `.effectStyle` / `.gridStyle` | `FigPlanPaintStyle` / `FigPlanTextStyle` / `FigPlanEffectStyle` / `FigPlanGridStyle` | Create a local style — `(opts)` with required `name`. Pass the returned handle into `fills` / `strokes` / `effects` / `layoutGrids` / `textStyle` to bind by id. |
| `$fig.getStyle(nameOrId)` | `FigPlanStyle \| null` | Wrap an existing local style. Tries id first, then scans by name. Narrow via `handle.style?.type`. |
| `planStyle.set(opts \| fn)` / `.remove()` / `.style` / `.id` | — | Style handle methods. Fn form receives the **live Figma `Style`** narrowed to the concrete subtype (`PaintStyle` / `TextStyle` / `EffectStyle` / `GridStyle`), not the plan handle. |
| `$fig.varCollection(opts)` | `FigPlanVarCollection` | Create a variable collection. `opts.name` + `opts.modes` (string array) required. |
| `$fig.getVarCollection(idOrName)` | `FigPlanVarCollection` | Wrap existing collection by id or name. Throws if not found. |
| `$fig.getVar(id)` | `FigPlanVariable` | Wrap existing variable by real Figma id. Throws if not found. Use `coll.getVar(name)` for name-based lookup. |
| `coll.colorVar` / `.numVar` / `.boolVar` / `.stringVar` | `FigPlanColorVar` / `FigPlanNumVar` / `FigPlanBoolVar` / `FigPlanStringVar` | Create a typed variable. `opts.name` required. `opts.values` as `{ modeName: value }`. Specify `opts.scopes` explicitly — `ALL_SCOPES` is almost never right. |
| `coll.getVar(nameOrId)` | `FigPlanVariable` | Wrap existing variable in this collection by name or id. |
| `planVar.value(mode, val)` / `.setValues(map \| fn)` / `.set(opts \| fn)` / `.remove()` | — | Variable handle methods. Pass another variable handle as a value to create a `VARIABLE_ALIAS`. |
| `$fig.done()` | `Promise<FigDoneResult>` | Explicitly materialize the plan. Auto-flushes on script shutdown if not called. |

Plan nodes returned by create methods are chainable — `.frame()`, `.text()`, `.set()`, `.remove()`, `.clone()`, `.moveTo()`, `.reorderChildren()`, `.replace()`, `.query()`, `.gradient()`, `.image()` operate within that subtree.

### Types

| Type                | Description                                                                                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `QueryResult`       | Iterable result from `node.query()` with `.first()`, `.last()`, `.each()`, `.map()`, `.filter()`, `.values()`, `.set()`, `.query()` |
| `FigQueryResult`    | Result from `$fig.query()` / `planNode.query()` with `.toArray()`, `.map()`, `.values()`, `.set()`, `.remove()`, `.moveTo()`, `.each()`, `.first()`, `.last()`, `.filter()` |
| `ScreenshotOptions` | `{ scale?: number, contentsOnly?: boolean }` — `contentsOnly` defaults to `false` |
