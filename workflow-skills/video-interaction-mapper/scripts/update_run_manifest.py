#!/usr/bin/env python3
"""
Update a video-interaction-mapper run_manifest.json as Figma work completes.

This helper keeps the workflow resumable:
- record the storyboard use_figma result, including node IDs and upload targets
- record upload_assets image hashes
- generate a ready-to-run fill script from the fill template
- record fill and verification status

Usage:
    python update_run_manifest.py \
      --run-manifest figma_calls/run_manifest.json \
      --storyboard-result storyboard_result.json

    python update_run_manifest.py \
      --run-manifest figma_calls/run_manifest.json \
      --uploads-file uploaded_images.json \
      --write-fill-script figma_calls/figma_apply_fills.js
"""

import argparse
import json
import re
from pathlib import Path


def load_json(path: str) -> object:
    data = json.loads(Path(path).read_text())
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and "text" in data[0]:
        return json.loads(data[0]["text"])
    if isinstance(data, dict) and "text" in data and isinstance(data["text"], str):
        return json.loads(data["text"])
    return data


def as_list(value: object, keys: tuple[str, ...]) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, list):
                return candidate
    return []


def update_upload_targets(run_manifest: dict, upload_targets: list[dict]) -> None:
    run_manifest["figma"]["upload_targets"] = upload_targets
    expected_by_key = {
        item.get("assetKey"): item
        for item in run_manifest.get("expected_uploads", [])
        if item.get("assetKey")
    }
    for target in upload_targets:
        match = expected_by_key.get(target.get("assetKey"))
        if match:
            match["nodeId"] = target.get("nodeId")
            match["status"] = "ready_to_upload"
    if upload_targets:
        run_manifest["stages"]["storyboard"] = "complete"


def normalize_uploaded_images(value: object) -> list[dict]:
    uploads = as_list(value, ("uploadedImages", "uploads", "results", "items"))
    normalized = []
    for item in uploads:
        if not isinstance(item, dict):
            continue
        node_id = item.get("nodeId") or item.get("node_id")
        image_hash = item.get("imageHash") or item.get("image_hash") or item.get("hash")
        if node_id and image_hash:
            normalized.append(
                {
                    "assetKey": item.get("assetKey"),
                    "momentIndex": item.get("momentIndex"),
                    "role": item.get("role"),
                    "nodeId": node_id,
                    "imageHash": image_hash,
                    "scaleMode": item.get("scaleMode", "FILL"),
                }
            )
    return normalized


def update_uploaded_images(run_manifest: dict, uploaded_images: list[dict]) -> None:
    run_manifest["figma"]["uploaded_images"] = uploaded_images
    expected = run_manifest.get("expected_uploads", [])
    expected_by_node = {item.get("nodeId"): item for item in expected if item.get("nodeId")}
    expected_by_key = {item.get("assetKey"): item for item in expected if item.get("assetKey")}
    for uploaded in uploaded_images:
        match = expected_by_node.get(uploaded.get("nodeId"))
        if not match and uploaded.get("assetKey"):
            match = expected_by_key.get(uploaded.get("assetKey"))
        if match:
            match["imageHash"] = uploaded.get("imageHash")
            match["status"] = "uploaded"
    if expected and all(item.get("status") == "uploaded" for item in expected):
        run_manifest["stages"]["uploads"] = "complete"


def write_fill_script(run_manifest: dict, output_path: str) -> None:
    template_path = run_manifest["figma"].get("fill_script_template")
    if not template_path:
        raise RuntimeError("run manifest has no fill_script_template path")
    uploaded_images = run_manifest["figma"].get("uploaded_images", [])
    if not uploaded_images:
        raise RuntimeError("run manifest has no uploaded_images to apply")

    template = Path(template_path).read_text()
    replacement = "const uploadedImages = " + json.dumps(uploaded_images, indent=2) + ";"
    script = re.sub(r"const uploadedImages = \[\];", replacement, template, count=1)
    Path(output_path).write_text(script)
    run_manifest["figma"]["fill_script"] = output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Update a video interaction mapper run manifest")
    parser.add_argument("--run-manifest", required=True, help="Path to run_manifest.json")
    parser.add_argument("--storyboard-result", help="JSON file containing the storyboard use_figma result")
    parser.add_argument("--uploads-file", help="JSON file containing uploaded nodeId/imageHash pairs")
    parser.add_argument("--fill-result", help="JSON file containing the fill-pass use_figma result")
    parser.add_argument("--write-fill-script", help="Write a ready-to-run fill script to this path")
    parser.add_argument("--verification-screenshot", help="Path to a downloaded verification screenshot")
    parser.add_argument("--verification-notes", default="", help="Verification notes")
    parser.add_argument("--output", help="Optional output manifest path. Defaults to in-place update.")
    args = parser.parse_args()

    run_manifest_path = Path(args.run_manifest)
    run_manifest = json.loads(run_manifest_path.read_text())

    if args.storyboard_result:
        result = load_json(args.storyboard_result)
        if isinstance(result, dict):
            run_manifest["figma"]["page_id"] = result.get("pageId") or run_manifest["figma"].get("page_id")
            run_manifest["figma"]["created_node_ids"] = result.get("createdNodeIds", [])
            update_upload_targets(run_manifest, result.get("uploadTargets", []))

    if args.uploads_file:
        uploads = normalize_uploaded_images(load_json(args.uploads_file))
        update_uploaded_images(run_manifest, uploads)

    if args.write_fill_script:
        write_fill_script(run_manifest, args.write_fill_script)

    if args.fill_result:
        fill_result = load_json(args.fill_result)
        if isinstance(fill_result, dict):
            run_manifest["figma"]["fill_pass"] = {
                "status": "complete",
                "mutated_node_ids": fill_result.get("mutatedNodeIds", []),
                "applied_image_count": fill_result.get("appliedImageCount"),
            }
            run_manifest["stages"]["fills"] = "complete"

    if args.verification_screenshot:
        run_manifest["figma"]["verification"] = {
            "status": "complete",
            "screenshot_path": args.verification_screenshot,
            "notes": args.verification_notes,
        }
        run_manifest["stages"]["verification"] = "complete"

    output_path = Path(args.output) if args.output else run_manifest_path
    output_path.write_text(json.dumps(run_manifest, indent=2))
    print(f"Updated run manifest: {output_path}")


if __name__ == "__main__":
    main()
