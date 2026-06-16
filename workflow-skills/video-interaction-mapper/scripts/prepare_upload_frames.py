#!/usr/bin/env python3
"""
Prepare key frame images for Figma upload_assets.

Takes a frames manifest and a list of analyzed key moments, then writes resized
JPEG assets for each before/after state plus an upload_manifest.json consumed by
generate_figma_calls.py.

Usage:
    python prepare_upload_frames.py \
      --manifest /tmp/vim_frames/frames_manifest.json \
      --moments-file /tmp/vim_frames/key_moments.json \
      --output /tmp/vim_frames/upload_manifest.json
"""

import argparse
import json
import os
from pathlib import Path


def prepare_image(
    input_path: str,
    output_path: Path,
    max_width: int,
    quality: int,
    max_bytes: int,
) -> dict:
    """Resize and compress an image for upload_assets, returning final metadata."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required: pip install Pillow --break-system-packages") from exc

    with Image.open(input_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        if max_width > 0 and img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        current_quality = min(max(quality, 1), 95)
        while True:
            img.save(output_path, format="JPEG", quality=current_quality, optimize=True)
            size_bytes = output_path.stat().st_size
            if size_bytes <= max_bytes:
                break

            if current_quality > 45:
                current_quality = max(45, current_quality - 10)
                continue

            next_width = max(480, int(img.width * 0.85))
            if next_width >= img.width:
                break
            ratio = next_width / img.width
            img = img.resize((next_width, int(img.height * ratio)), Image.LANCZOS)

        return {
            "width": img.width,
            "height": img.height,
            "quality": current_quality,
            "size_bytes": output_path.stat().st_size,
            "within_budget": output_path.stat().st_size <= max_bytes,
        }


def safe_stem(label: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in label)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:48] or "moment"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare frame images for Figma upload_assets")
    parser.add_argument("--manifest", required=True, help="Path to frames_manifest.json")
    parser.add_argument("--moments-file", required=True, help="Path to key_moments.json")
    parser.add_argument("--output", required=True, help="Output path for upload_manifest.json")
    parser.add_argument(
        "--assets-dir",
        help="Directory for optimized JPEGs. Defaults to <output-dir>/upload_assets",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=0,
        help="Max frame width. Auto-detected from video orientation if not set.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=75,
        help="JPEG quality 1-95 (default: 75)",
    )
    parser.add_argument(
        "--max-file-mb",
        type=float,
        default=9.5,
        help="Maximum uploaded image size in MB (default: 9.5)",
    )
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)

    with open(args.moments_file) as f:
        moments = json.load(f)

    output_path = Path(args.output)
    assets_dir = Path(args.assets_dir) if args.assets_dir else output_path.parent / "upload_assets"

    video_info = manifest.get("video_info", {})
    orientation = video_info.get("orientation", "landscape")
    if args.max_width > 0:
        max_width = args.max_width
    elif orientation == "portrait":
        max_width = 900
    else:
        max_width = 1440

    prepared_moments = []
    frame_width = None
    frame_height = None
    max_bytes = int(args.max_file_mb * 1024 * 1024)

    print(
        f"Preparing {len(moments)} moments for upload_assets "
        f"({max_width}px wide, JPEG q{args.quality})...",
        flush=True,
    )

    for index, moment in enumerate(moments, start=1):
        prepared = dict(moment)
        moment_index = prepared.get("moment_index", index)
        label = safe_stem(prepared.get("short_label", f"moment_{moment_index}"))

        for role in ("before", "after"):
            source_key = f"{role}_frame_path"
            upload_key = f"{role}_upload_path"
            source_path = prepared.get(source_key)

            if source_path and os.path.exists(source_path):
                output_file = assets_dir / f"moment_{moment_index:03d}_{role}_{label}.jpg"
                info = prepare_image(source_path, output_file, max_width, args.quality, max_bytes)
                prepared[upload_key] = str(output_file)
                prepared[f"{role}_upload_width"] = info["width"]
                prepared[f"{role}_upload_height"] = info["height"]
                prepared[f"{role}_upload_quality"] = info["quality"]
                prepared[f"{role}_upload_size_bytes"] = info["size_bytes"]
                prepared[f"{role}_upload_within_budget"] = info["within_budget"]
                frame_width = frame_width or info["width"]
                frame_height = frame_height or info["height"]
                status = "ok" if info["within_budget"] else "over budget"
                print(
                    f"  [{index}/{len(moments)}] {role}: {output_file.name} "
                    f"({info['width']}x{info['height']}, q{info['quality']}, "
                    f"{info['size_bytes'] / 1024:.0f} KB, {status})",
                    flush=True,
                )
            else:
                prepared[upload_key] = None
                print(f"  [{index}/{len(moments)}] {role}: missing ({source_path})", flush=True)

        prepared_moments.append(prepared)

    if frame_width is None or frame_height is None:
        width = int(video_info.get("width", max_width) or max_width)
        height = int(video_info.get("height", max_width) or max_width)
        if width > max_width:
            ratio = max_width / width
            width = max_width
            height = int(height * ratio)
        frame_width = width
        frame_height = height

    output = {
        "video_path": manifest.get("video_path"),
        "video_info": video_info,
        "frame_width": frame_width,
        "frame_height": frame_height,
        "image_budget": {
            "max_width": max_width,
            "requested_quality": args.quality,
            "max_file_mb": args.max_file_mb,
            "max_file_bytes": max_bytes,
        },
        "total_moments": len(prepared_moments),
        "assets_dir": str(assets_dir),
        "moments": prepared_moments,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nPrepared {len(prepared_moments)} moments")
    print(f"Assets: {assets_dir}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
