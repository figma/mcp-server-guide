#!/usr/bin/env python3
"""
Extract key frames from a video file using ffmpeg.

This script:
1. Extracts frames at a given fps
2. Runs ffmpeg scene-change detection to score each frame
3. Flags frames with scene scores above the threshold as key frames
4. Optionally writes a compact contact sheet for quick visual review
5. Outputs JPEG frames + a frames_manifest.json

Usage:
    python extract_key_frames.py --input video.mp4 --output /tmp/frames/ --mode scout
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def get_video_info(video_path: str) -> dict:
    """Get basic video metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)

    # Find video stream
    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
        None
    )
    if not video_stream:
        raise RuntimeError("No video stream found in file")

    duration = float(data.get("format", {}).get("duration", 0))
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))

    # Parse framerate
    fps_str = video_stream.get("r_frame_rate", "30/1")
    fps_parts = fps_str.split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_str)

    return {
        "duration_s": duration,
        "width": width,
        "height": height,
        "native_fps": fps,
        "orientation": "portrait" if height > width else "landscape"
    }


def extract_all_frames(video_path: str, output_dir: str, fps: int = 5, max_frames: int = 3000) -> list[str]:
    """Extract all frames at the given fps as JPEG files."""
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, "frame_%06d.jpg")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "3",          # JPEG quality (1-31, lower = better)
        "-vframes", str(max_frames),
        output_pattern,
        "-y", "-v", "quiet"
    ]

    print(f"Extracting frames at {fps}fps...", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed: {result.stderr}")

    # Collect output frames in order
    frames = sorted(Path(output_dir).glob("frame_*.jpg"))
    print(f"Extracted {len(frames)} frames", flush=True)
    return [str(f) for f in frames]


def detect_scene_changes(video_path: str, fps: int = 5) -> dict[float, float]:
    """
    Use ffmpeg's scene filter to get scene change scores at each timestamp.
    Returns a dict mapping timestamp (seconds) -> scene score (0.0-1.0).
    """
    # ffmpeg scene detection — outputs to stderr with showinfo
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps},select='gte(scene,0)',metadata=print:file=-",
        "-an", "-f", "null", "-",
        "-v", "quiet"
    ]

    print("Running scene change detection...", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Scene metadata goes to stdout via metadata=print:file=-
    output = result.stdout

    scene_scores = {}
    current_ts = None

    for line in output.splitlines():
        # Look for pts_time and lavfi.scene_score
        ts_match = re.search(r'pts_time:([0-9.]+)', line)
        if ts_match:
            current_ts = float(ts_match.group(1))
        score_match = re.search(r'lavfi\.scene_score=([0-9.]+)', line)
        if score_match and current_ts is not None:
            scene_scores[current_ts] = float(score_match.group(1))
            current_ts = None

    print(f"Got scene scores for {len(scene_scores)} timestamps", flush=True)
    return scene_scores


def match_frames_to_scores(
    frame_paths: list[str],
    scene_scores: dict[float, float],
    fps: int,
    threshold: float
) -> list[dict]:
    """
    Build the manifest by matching each extracted frame to its scene score.
    Frame index N corresponds to timestamp N/fps seconds.
    """
    frames = []
    for i, path in enumerate(frame_paths):
        timestamp = i / fps

        # Find the closest scene score timestamp within a small window
        window = 1.0 / fps  # within one frame's width
        closest_score = 0.0
        for ts, score in scene_scores.items():
            if abs(ts - timestamp) <= window:
                if score > closest_score:
                    closest_score = score

        is_key = closest_score >= threshold

        frames.append({
            "index": i,
            "path": path,
            "timestamp_s": round(timestamp, 3),
            "scene_score": round(closest_score, 4),
            "is_key_frame": is_key
        })

    return frames


def resize_frames(frame_paths: list[str], max_width: int = 1600):
    """
    Resize extracted frames to a max width while preserving aspect ratio.
    Modifies files in-place using PIL.
    """
    if max_width <= 0:
        print("Skipping frame resize", flush=True)
        return

    try:
        from PIL import Image
    except ImportError:
        print("Pillow not available, skipping resize", flush=True)
        return

    print(f"Resizing frames to max {max_width}px wide...", flush=True)
    for path in frame_paths:
        with Image.open(path) as img:
            if img.width > max_width:
                ratio = max_width / img.width
                new_h = int(img.height * ratio)
                img = img.resize((max_width, new_h), Image.LANCZOS)
                img.save(path, "JPEG", quality=85, optimize=True)


def sample_frames_for_contact_sheet(frames: list[dict], max_frames: int) -> list[dict]:
    """Return up to max_frames frames, evenly sampled from the manifest."""
    if max_frames <= 0 or len(frames) <= max_frames:
        return frames
    if max_frames == 1:
        return [frames[0]]

    sampled = []
    step = (len(frames) - 1) / (max_frames - 1)
    seen = set()
    for sample_index in range(max_frames):
        frame_index = round(sample_index * step)
        if frame_index not in seen:
            sampled.append(frames[frame_index])
            seen.add(frame_index)
    return sampled


def write_contact_sheet(
    frames: list[dict],
    output_path: str,
    cols: int = 5,
    thumb_width: int = 260,
    max_frames: int = 80,
) -> str | None:
    """Create a timeline contact sheet for fast visual scanning."""
    if not frames:
        return None

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not available, skipping contact sheet", flush=True)
        return None

    selected = sample_frames_for_contact_sheet(frames, max_frames)
    cols = max(1, cols)
    rows = (len(selected) + cols - 1) // cols
    label_h = 34
    gutter = 10

    first = Image.open(selected[0]["path"])
    thumb_height = max(1, int(first.height * (thumb_width / first.width)))
    first.close()

    sheet_w = cols * thumb_width + (cols + 1) * gutter
    sheet_h = rows * (thumb_height + label_h) + (rows + 1) * gutter
    sheet = Image.new("RGB", (sheet_w, sheet_h), (246, 246, 248))
    draw = ImageDraw.Draw(sheet)

    for cell_index, frame in enumerate(selected):
        col = cell_index % cols
        row = cell_index // cols
        x = gutter + col * (thumb_width + gutter)
        y = gutter + row * (thumb_height + label_h + gutter)

        with Image.open(frame["path"]) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            thumb = img.resize((thumb_width, thumb_height), Image.LANCZOS)
            sheet.paste(thumb, (x, y))

        label = f"#{frame['index']}  t={frame['timestamp_s']:.1f}s  score={frame['scene_score']:.2f}"
        if frame.get("is_key_frame"):
            label = "* " + label
        draw.text((x, y + thumb_height + 6), label, fill=(32, 32, 36))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "JPEG", quality=86, optimize=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Extract key frames from a video file")
    parser.add_argument("--input", required=True, help="Path to input video file")
    parser.add_argument("--output", required=True, help="Output directory for frames")
    parser.add_argument(
        "--mode",
        choices=["scout", "full"],
        default="full",
        help="scout extracts a low-fps review timeline; full extracts denser frames (default: full)",
    )
    parser.add_argument("--fps", type=int, default=None, help="Frames per second to extract")
    parser.add_argument("--scene-threshold", type=float, default=0.25,
                        help="Scene change threshold 0.0-1.0 (default: 0.25). "
                             "Higher = fewer key frames detected.")
    parser.add_argument("--max-width", type=int, default=None,
                        help="Max frame width in pixels. Use 0 to keep native resolution.")
    parser.add_argument("--max-frames", type=int, default=3000,
                        help="Maximum extracted frames (default: 3000)")
    parser.add_argument("--contact-sheet", dest="contact_sheet", action="store_true",
                        help="Write contact_sheet.jpg next to the manifest")
    parser.add_argument("--no-contact-sheet", dest="contact_sheet", action="store_false",
                        help="Skip contact sheet generation")
    parser.set_defaults(contact_sheet=None)
    parser.add_argument("--contact-sheet-cols", type=int, default=5,
                        help="Columns in the contact sheet (default: 5)")
    parser.add_argument("--contact-sheet-max-frames", type=int, default=80,
                        help="Maximum thumbnails in the contact sheet (default: 80)")
    args = parser.parse_args()

    fps = args.fps if args.fps is not None else (1 if args.mode == "scout" else 5)
    max_width = args.max_width if args.max_width is not None else (640 if args.mode == "scout" else 1600)
    make_contact_sheet = args.contact_sheet if args.contact_sheet is not None else args.mode == "scout"

    if not os.path.exists(args.input):
        print(f"Error: video file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Check ffmpeg
    check = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if check.returncode != 0:
        print("Error: ffmpeg not found. Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)",
              file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    # Get video metadata
    print(f"Analyzing video: {args.input}", flush=True)
    video_info = get_video_info(args.input)
    print(f"  Duration: {video_info['duration_s']:.1f}s | "
          f"Resolution: {video_info['width']}x{video_info['height']} | "
          f"Orientation: {video_info['orientation']}", flush=True)

    # Extract all frames
    frame_paths = extract_all_frames(args.input, args.output, fps, args.max_frames)

    if not frame_paths:
        print("Error: no frames were extracted", file=sys.stderr)
        sys.exit(1)

    # Resize frames, preserving enough resolution for Figma inspection.
    if max_width > 0:
        resize_frames(frame_paths, max_width)
    else:
        print("Keeping extracted frames at native resolution", flush=True)

    # Detect scene changes
    scene_scores = detect_scene_changes(args.input, fps)

    # Build manifest
    frames = match_frames_to_scores(frame_paths, scene_scores, fps, args.scene_threshold)

    key_count = sum(1 for f in frames if f["is_key_frame"])
    print(f"Found {key_count} key frames out of {len(frames)} total "
          f"(threshold: {args.scene_threshold})", flush=True)

    contact_sheet_path = None
    if make_contact_sheet:
        contact_sheet_path = os.path.join(args.output, "contact_sheet.jpg")
        contact_sheet_path = write_contact_sheet(
            frames,
            contact_sheet_path,
            cols=args.contact_sheet_cols,
            max_frames=args.contact_sheet_max_frames,
        )
        if contact_sheet_path:
            print(f"Contact sheet written to: {contact_sheet_path}", flush=True)

    manifest = {
        "video_path": os.path.abspath(args.input),
        "output_dir": os.path.abspath(args.output),
        "mode": args.mode,
        "fps_extracted": fps,
        "scene_threshold": args.scene_threshold,
        "max_width": max_width,
        "video_info": video_info,
        "contact_sheet_path": os.path.abspath(contact_sheet_path) if contact_sheet_path else None,
        "total_frames": len(frames),
        "key_frame_count": key_count,
        "frames": frames
    }

    manifest_path = os.path.join(args.output, "frames_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to: {manifest_path}")
    print(f"Key frames: {key_count} / {len(frames)}")

    # Print a quick summary of key frame timestamps
    key_frames = [f for f in frames if f["is_key_frame"]]
    if key_frames:
        print("\nKey frame timestamps:")
        for kf in key_frames[:20]:  # show first 20
            print(f"  t={kf['timestamp_s']:.2f}s  score={kf['scene_score']:.3f}  {kf['path']}")
        if len(key_frames) > 20:
            print(f"  ... and {len(key_frames) - 20} more")


if __name__ == "__main__":
    main()
