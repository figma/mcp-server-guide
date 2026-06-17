# Video Interaction Mapper

Video Interaction Mapper turns UI screen recordings into annotated Figma
storyboards. It extracts key before/after states from a local video, prepares
uploadable screenshot assets, creates a single-page Figma Design storyboard, and
adds native annotations plus visual target markers for the interactions.

## What it creates

- A Figma Design page with a left-to-right sequence of interaction states.
- Before and after screenshot pairs for each selected moment.
- Blue target markers on visible, high-confidence click or tap targets.
- Native Figma annotations that describe the interaction without exposing raw
  coordinate values.
- A resumable local run manifest for uploads, fill application, and verification.

## Requirements

- `ffmpeg` and `ffprobe`.
- Python 3.
- Pillow for image resizing and compression.
- Figma MCP tools:
  - `create_new_file`
  - `use_figma`
  - `upload_assets`
  - `get_screenshot`

## Scripts

The files in `scripts/` are executable helper scripts used by the skill workflow.
They are intended to be run as-is for repeatable local processing steps such as
frame extraction, upload asset preparation, Figma script generation, and run
manifest updates. They are not reference docs.

## Use

Install this folder as an agent skill, then ask the agent to map a UI recording
into Figma. Example:

```text
Use $video-interaction-mapper on /path/to/screen-recording.mp4 and create a new
Figma file.
```

The skill first analyzes the video locally, then creates or updates the Figma
file only after the key moments and upload assets are ready. This avoids leaving
partial pages behind when frame selection changes.
