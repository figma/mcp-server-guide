# Parallel Web Capture & Image Transfer (`generate_figma_design`)

## Parallel Workflow (Web Apps Only)

When building a screen from a **web app** that can be rendered in a browser, run both approaches in parallel:

1. **In parallel:**
   - Start building the screen using `figma-generate-design` (`use_figma` + design system components) against the target Figma file (`fileKey`).
   - Run `generate_figma_design` against the **same `fileKey`** to capture a pixel-perfect screenshot of the running web app into that file. `generate_figma_design` always requires `fileKey` — if the user does not yet have a Figma file, first invoke `/figma-create-new-file` (or call `create_new_file`) to get one, and reuse that `file_key` for both this skill and the capture.
2. **Once both complete:** Update the `use_figma` output to match the pixel-perfect layout from the `generate_figma_design` capture. The capture provides exact spacing, sizing, and visual treatment, while your `use_figma` output has proper component instances linked to the design system. If the capture contains images, transfer them to your `use_figma` output by copying `imageHash` values from the capture's image fills.
3. **Once confirmed looking good:** Delete the `generate_figma_design` output — it was only used as a visual reference.

**This parallel workflow is MANDATORY when the source contains discrete content images used by the app, such as photos, avatars, logos, or icons. A screenshot or flattened rendering of the complete UI is a visual reference, not a content image.** The `use_figma` Plugin API cannot fetch external image URLs — it can only set image fills by copying `imageHash` values from nodes already in the file. `generate_figma_design` rasterizes all visible images into Figma, providing the hashes you need. If you skip the capture when these content images are present, their image frames will be left blank.

For non-web apps (iOS, Android, etc.) or when updating existing screens, use the standard workflow.

## Transfer Images from the `generate_figma_design` Capture

Transfer only discrete content assets used by the app into your design system output. Never upload or transfer the capture root or any screenshot or flattened rendering of the complete UI.

1. Find all image nodes in the capture output by searching for fills with `type === "IMAGE"`:
   ```js
   const capture = await figma.getNodeByIdAsync("CAPTURE_NODE_ID");
   const imageNodes = capture.findAll(() => true).flatMap(n => {
     if (!Array.isArray(n.fills)) return [];
     const imageFill = n.fills.find(f => f.type === "IMAGE");
     return imageFill ? [{ name: n.name, id: n.id, imageHash: imageFill.imageHash }] : [];
   });
   return imageNodes;
   ```
2. Match each captured image to the corresponding frame in your `use_figma` output (by position, name, or order).
3. Apply the image hash to the target frame:
   ```js
   targetFrame.fills = [{ type: "IMAGE", imageHash: "hash_from_capture", scaleMode: "FILL" }];
   ```
4. Delete the `generate_figma_design` capture output after all images are transferred.

## Generating Placeholder Images and Vectors

Reuse existing assets if possible. If not, choose between `generate_image` and `generate_vector_illustration`. Then inform the user that Figma AI credits were used.

If Figma AI is unavailable or its credit limit is reached, ask before using an alternative image-generation provider. Upload only these alternative-provider images with `upload_assets`.
