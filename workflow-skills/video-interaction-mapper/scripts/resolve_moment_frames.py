#!/usr/bin/env python3
"""
Resolve analyzed key moments into concrete before/after screenshot files.

This lets the workflow start with a low-resolution scout/contact sheet and only
extract the high-quality frames that will actually be uploaded to Figma.

Usage:
    python resolve_moment_frames.py \
      --video input.mp4 \
      --moments-file key_moments.json \
      --output key_moments_resolved.json \
      --frames-dir selected_frames/
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def safe_stem(label: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in label)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:48] or "moment"


def numeric_value(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else 0.0


def timestamp_for(moment: dict, role: str, before_offset: float, after_offset: float) -> float | None:
    for key in (
        f"{role}_timestamp_s",
        f"{role}_time_s",
        f"{role}_timestamp",
    ):
        timestamp = numeric_value(moment.get(key))
        if timestamp is not None:
            return timestamp

    base = numeric_value(moment.get("timestamp_s"))
    if base is None:
        return None
    if role == "before":
        return max(0.0, base - before_offset)
    return max(0.0, base + after_offset)


def optimize_jpeg(path: Path, max_width: int, quality: int) -> tuple[int | None, int | None]:
    try:
        from PIL import Image
    except ImportError:
        if max_width > 0:
            print("Pillow not available, selected frames will not be resized", flush=True)
        return None, None

    with Image.open(path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        if max_width > 0 and img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        img.save(path, "JPEG", quality=quality, optimize=True)
        return img.width, img.height


def extract_frame(video_path: str, timestamp_s: float, output_path: Path, max_width: int, quality: int) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-ss",
        f"{timestamp_s:.3f}",
        "-i",
        video_path,
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-y",
        "-v",
        "quiet",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"ffmpeg failed at {timestamp_s:.3f}s: {result.stderr}")

    width, height = optimize_jpeg(output_path, max_width, quality)
    return {
        "path": str(output_path),
        "timestamp_s": round(timestamp_s, 3),
        "width": width,
        "height": height,
        "size_bytes": output_path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract selected before/after frames for key moments")
    parser.add_argument("--video", required=True, help="Source video path")
    parser.add_argument("--moments-file", required=True, help="Input key_moments.json")
    parser.add_argument("--output", required=True, help="Output resolved key_moments JSON")
    parser.add_argument("--frames-dir", required=True, help="Directory for selected frame JPEGs")
    parser.add_argument("--max-width", type=int, default=1600, help="Max selected frame width (default: 1600)")
    parser.add_argument("--quality", type=int, default=86, help="JPEG quality for selected frames (default: 86)")
    parser.add_argument("--before-offset", type=float, default=0.2,
                        help="Fallback seconds before timestamp_s for before frames")
    parser.add_argument("--after-offset", type=float, default=0.0,
                        help="Fallback seconds after timestamp_s for after frames")
    parser.add_argument("--force", action="store_true", help="Re-extract even when frame paths already exist")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    with open(args.moments_file) as f:
        moments = json.load(f)

    if not isinstance(moments, list):
        print("Error: moments file must contain a JSON array", file=sys.stderr)
        sys.exit(1)

    frames_dir = Path(args.frames_dir)
    resolved = []
    warnings = []

    for index, moment in enumerate(moments, start=1):
        next_moment = dict(moment)
        moment_index = int(next_moment.get("moment_index", index))
        label = safe_stem(next_moment.get("short_label", f"moment_{moment_index}"))

        for role in ("before", "after"):
            path_key = f"{role}_frame_path"
            existing_path = next_moment.get(path_key)
            if existing_path and os.path.exists(existing_path) and not args.force:
                continue

            timestamp_s = timestamp_for(next_moment, role, args.before_offset, args.after_offset)
            if timestamp_s is None:
                warnings.append(f"moment {moment_index} {role}: no frame path or timestamp")
                continue

            output_path = frames_dir / f"moment_{moment_index:03d}_{role}_{label}.jpg"
            info = extract_frame(args.video, timestamp_s, output_path, args.max_width, args.quality)
            next_moment[path_key] = info["path"]
            next_moment[f"{role}_timestamp_s"] = info["timestamp_s"]
            next_moment[f"{role}_frame_size_bytes"] = info["size_bytes"]
            if info["width"] and info["height"]:
                next_moment[f"{role}_frame_width"] = info["width"]
                next_moment[f"{role}_frame_height"] = info["height"]
            print(f"  moment {moment_index:02d} {role}: {output_path.name}", flush=True)

        resolved.append(next_moment)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(resolved, indent=2))

    print(f"\nResolved {len(resolved)} moments")
    print(f"Output: {output_path}")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
