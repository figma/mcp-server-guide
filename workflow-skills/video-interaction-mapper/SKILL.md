---
name: video-interaction-mapper
description: >
  This skill should be used when the user asks to analyze a UI screen recording and
  map interaction states into Figma. Trigger for requests such as "put video frames
  in Figma", "extract states from my recording", "map interactions from video to
  Figma", "analyze this screen recording", "create a storyboard from my video",
  "deconstruct this interaction in Figma", "annotate the UI states in my recording",
  or "pull the key moments from this video into Figma". Also trigger when the user
  references a video file (.mp4, .mov, .webm, .avi) together with Figma, design
  review, interaction analysis, prototypes, or UI states. The skill extracts key
  visual moments from a video, infers interaction triggers, and builds an annotated
  Figma Design storyboard using native Figma annotations and uploaded screenshot
  assets.
---

# Video Interaction Mapper

Turn a UI recording into a static, annotated Figma storyboard. Extract the important
before/after states, infer what triggered each change, then place clean screenshots,
blue interaction markers, and concise annotations into a Figma Design file.

## Required Inputs and Tools

Start with:

- A local video file path (`.mp4`, `.mov`, `.webm`, or `.avi`).
- `ffmpeg` and `ffprobe` available on the machine.
- Python with Pillow installed.
- Figma MCP tools available: `create_new_file`, `use_figma`, `upload_assets`, and
  `get_screenshot` or `get_design_context`.

Run the bundled files in `scripts/` as executable workflow helpers. They are part
of the skill's implementation, not reference material. Read or modify them only
when debugging, adapting to an unusual environment, or changing the skill itself.

Use a Figma Design file (`figma.com/design/...`) as the target. The generated
Plugin API code creates pages and image-fill frames, which are Design-file
operations. If the user provides a FigJam or Slides URL, ask for a Design file or
create a new one.

Before any `use_figma` call, load the Figma API guidance skill if available
(`figma-use`). Before creating a new Figma file, load the file-creation guidance
skill if available (`figma-create-new-file`). Pass `skillNames:
"figma-use,video-interaction-mapper"` on `use_figma` calls when the client supports
that parameter.

## Workflow

### 1. Validate and Prepare

Confirm the video path exists, then check `ffmpeg -version`. If Pillow is missing,
install it in the active Python environment:

```bash
pip install Pillow --break-system-packages -q
```

Do local analysis before creating or modifying the Figma file. Create a Figma file
only after `key_moments.json`, `upload_manifest.json`, and generated Figma scripts
are ready, unless the user explicitly asks to create the file first. This avoids
leaving partial pages behind when local frame analysis changes.

### 2. Scout the Timeline Quickly

Start with a low-resolution scout pass and contact sheet:

```bash
python <SKILL_DIR>/scripts/extract_key_frames.py \
  --input "<video_path>" \
  --output /tmp/vim_frames_<timestamp>/ \
  --mode scout
```

The scout pass extracts at 1 fps by default, resizes frames to 640 px wide, scores
scene changes, writes `<output_dir>/frames_manifest.json`, and creates
`<output_dir>/contact_sheet.jpg`. Inspect the contact sheet first to identify likely
interaction moments.

Use the slower full extraction only when the scout pass is insufficient:

```bash
python <SKILL_DIR>/scripts/extract_key_frames.py \
  --input "<video_path>" \
  --output /tmp/vim_frames_<timestamp>/full_frames/ \
  --mode full \
  --max-width 1600
```

For very long videos, ask whether to focus on a specific time range before
processing the whole recording. For too many key frames, re-run extraction with a
higher `--scene-threshold`, such as `0.4`.

### 3. Analyze Key Moments

Read `frames_manifest.json` and inspect `contact_sheet.jpg` or relevant extracted
frames. For each meaningful transition, identify:

- Visual change: modal, drawer, dropdown, tooltip, snackbar, overlay, navigation,
  loaded content, selected state, validation state, input focus, or scroll position.
- Trigger: click, tap, keyboard input, hover, scroll, swipe, form submit, auto/timer,
  or unknown trigger when the cause is ambiguous.
- Interaction target and result coordinates when visible and useful.

Use normalized coordinates from `0` to `1` relative to the screenshot. Percent-like
values such as `45` or `94` are accepted by the generated Figma script and converted
to `0.45` or `0.94`. Coordinates are machine metadata for marker placement only.
Do not include coordinate values in visible annotation text, moment labels, or user
summaries.

Only add marker coordinates when the point lands on a clearly visible UI element or
state. If a target is inferred, between visible controls, or based mainly on cursor
position, mark it with `inferred: true`, `uncertain: true`, `visible: false`, or
`confidence: "medium"`/`"low"`. The generated script suppresses markers for those
points by default so the canvas does not show a confident pulse over empty UI. If
the target or result cannot be located usefully, set `interaction` to `null`.

Use `confidence: "high"` or omit `confidence` only when the marker should be drawn.
Use `show_marker: true` only when an uncertain point is still worth marking; the
generated marker uses an alternate style for these forced uncertain markers.

Aim for 5 to 15 key moments. Prioritize high scene scores and genuinely different
states over tiny visual shifts.

Write the analysis to `<output_dir>/key_moments.json` as an array. When using the
scout flow, provide timestamps first; resolve high-quality frame files in the next
step.

```json
[
  {
    "moment_index": 1,
    "timestamp_s": 3.4,
    "before_timestamp_s": 3.2,
    "after_timestamp_s": 3.4,
    "trigger": "Click",
    "trigger_emoji": "",
    "short_label": "Dropdown menu opens",
    "annotation": "The account avatar is activated. A menu appears below it with profile, billing, and sign-out actions.",
    "interaction": {
      "target_frame": "before",
      "target": {
        "x": 0.91,
        "y": 0.08,
        "label": "Account avatar",
        "confidence": "high"
      },
      "result_frame": "after",
      "result": {
        "x": 0.86,
        "y": 0.2,
        "label": "Opened account menu"
      },
      "annotation": "Activating the avatar opens the account menu."
    }
  }
]
```

Keep annotations human-readable: `Target: Account avatar`, not a label with a raw
coordinate suffix. Coordinates stay hidden in JSON and appear only as visual marker
placement.

If a marker is drawn, the native Figma annotation is attached to that marker node
rather than the screenshot frame. If a marker is suppressed because the point is
uncertain or not visible, the annotation remains attached to the screenshot frame.

### 4. Resolve Selected Frames

If `key_moments.json` uses timestamps, extract only the selected before/after
frames at higher quality:

```bash
python <SKILL_DIR>/scripts/resolve_moment_frames.py \
  --video "<video_path>" \
  --moments-file /tmp/vim_frames_<timestamp>/key_moments.json \
  --output /tmp/vim_frames_<timestamp>/key_moments_resolved.json \
  --frames-dir /tmp/vim_frames_<timestamp>/selected_frames/ \
  --max-width 1600
```

Use `key_moments_resolved.json` in later steps. If a full extraction already
produced precise `before_frame_path` and `after_frame_path` values, this step can
be skipped.

### 5. Prepare Uploadable Screenshot Assets

Compress and resize the before/after screenshots for upload:

```bash
python <SKILL_DIR>/scripts/prepare_upload_frames.py \
  --manifest /tmp/vim_frames_<timestamp>/frames_manifest.json \
  --moments-file /tmp/vim_frames_<timestamp>/key_moments_resolved.json \
  --output /tmp/vim_frames_<timestamp>/upload_manifest.json
```

The script writes optimized JPEGs under `<output_dir>/upload_assets/` and creates
`upload_manifest.json`. Defaults are 1440 px wide for landscape recordings and 900
px wide for portrait recordings at JPEG quality 75. It records image dimensions,
actual JPEG quality, file size, and whether each asset fits the upload budget.

### 6. Generate Figma Call Files

Generate the self-contained Plugin API scripts:

```bash
python <SKILL_DIR>/scripts/generate_figma_calls.py \
  --prepared /tmp/vim_frames_<timestamp>/upload_manifest.json \
  --output-dir /tmp/vim_frames_<timestamp>/figma_calls/
```

This writes:

- `figma_storyboard.js`: one combined storyboard creation call.
- `figma_apply_fills_template.js`: a fill-pass template for uploaded image hashes.
- `figma_manifest.json`: execution order and upload instructions.
- `run_manifest.json`: resumable status, selected moments, expected uploads, node
  IDs, image hashes, fill status, and verification status.

The generated JavaScript does not embed image bytes and does not call
`figma.createImage`. The storyboard script creates all screenshot containers,
labels, native annotations, and marker overlays in one call, then returns
`uploadTargets` containing Figma node IDs and local JPEG paths. In a newly created
blank file, the script reuses and renames the default page instead of creating a
second page.

### 7. Execute in Figma and Upload Assets

Create a new Figma Design file or open the target Design file now. Run the generated
files in `figma_manifest.json`:

1. Read `figma_storyboard.js`.
2. Call `use_figma` against the target Design file with the full JavaScript content.
3. Save the result JSON if practical, then update the run manifest:

```bash
python <SKILL_DIR>/scripts/update_run_manifest.py \
  --run-manifest /tmp/vim_frames_<timestamp>/figma_calls/run_manifest.json \
  --storyboard-result /tmp/vim_frames_<timestamp>/storyboard_result.json
```

For each returned `uploadTargets` item:

- Call `upload_assets` with the target `fileKey`, `count: 1`, `nodeId`, and
  `scaleMode: "FILL"`.
- POST the local file at `target.path` to the returned upload URL.
- Record `{ "nodeId": "...", "imageHash": "...", "scaleMode": "FILL" }` in an
  uploads JSON file.

Generate and run the fill pass:

```bash
python <SKILL_DIR>/scripts/update_run_manifest.py \
  --run-manifest /tmp/vim_frames_<timestamp>/figma_calls/run_manifest.json \
  --uploads-file /tmp/vim_frames_<timestamp>/uploaded_images.json \
  --write-fill-script /tmp/vim_frames_<timestamp>/figma_calls/figma_apply_fills.js
```

Run `figma_apply_fills.js` once with `use_figma`. This explicit image-hash fill pass
is preferred because it makes uploaded screenshots render reliably in the generated
containers.

### 8. Verify

Run `get_screenshot`, `download_assets`, or `get_design_context` to verify that:

- Screenshots are visible and nonblank.
- Blue marker rings sit on the intended target/result locations.
- Native annotations use human labels and do not expose coordinate values.
- Ambiguous or inferred targets are suppressed unless explicitly forced with
  `show_marker: true`.

Update `run_manifest.json` with verification artifacts when available:

```bash
python <SKILL_DIR>/scripts/update_run_manifest.py \
  --run-manifest /tmp/vim_frames_<timestamp>/figma_calls/run_manifest.json \
  --verification-screenshot /tmp/vim_frames_<timestamp>/figma_storyboard.png \
  --verification-notes "Screenshots and markers verified"
```

## Output Expectations

The storyboard layout is left-to-right:

```text
[Title block]

[Before] [After]   [Before] [After]   [Before] [After]
moment 1           moment 2           moment 3

"Before state"     "01 Dropdown menu opens"
                   Annotation text...
```

Blue ring/dot overlays show the target and result locations when coordinates are
available and confident. Native Figma annotations attach to the marker nodes when
markers exist; otherwise they attach to the relevant before/after screenshot nodes.
Annotation labels should name the UI element or state change, never raw coordinate
percentages.

Report back with:

- The number of key moments mapped.
- The Figma file URL.
- Any moments whose trigger was ambiguous.
- Any uploads or frames that failed.
- The verification status and any inferred/uncertain markers.

## Edge Cases

- Long video: ask for a time range or warn that processing can take longer.
- Too many moments: raise `--scene-threshold` or manually keep the most meaningful
  5 to 15 transitions.
- Mobile recording: keep the portrait default width of 900 px so text remains
  readable without oversized assets.
- Missing trigger evidence: use `Unknown trigger` instead of guessing.
- Asset upload failure: retry the individual `upload_assets` target; the generated
  screenshot container remains in the file and can be reused.
- `upload_assets` succeeds but images do not render: run the generated fill pass
  with the returned image hashes.
- `upload_assets` is unavailable: warn that the fallback path is slower because it
  must embed image data directly in `use_figma` calls.
