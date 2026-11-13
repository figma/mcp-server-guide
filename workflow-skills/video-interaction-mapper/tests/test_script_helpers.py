import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_script(name: str):
    script_path = SKILL_DIR / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


resolve_frames = load_script("resolve_moment_frames")
run_manifest = load_script("update_run_manifest")


class ResolveMomentFramesTests(unittest.TestCase):
    def test_safe_stem_normalizes_labels_and_uses_fallback(self):
        self.assertEqual(resolve_frames.safe_stem(" Open / Key! "), "open_key")
        self.assertEqual(resolve_frames.safe_stem("!!!"), "moment")

    def test_numeric_value_rejects_invalid_input_and_clamps_negative_values(self):
        self.assertIsNone(resolve_frames.numeric_value("not-a-number"))
        self.assertIsNone(resolve_frames.numeric_value(None))
        self.assertEqual(resolve_frames.numeric_value(-3), 0.0)
        self.assertEqual(resolve_frames.numeric_value("2.5"), 2.5)

    def test_timestamp_for_prefers_role_specific_timestamp(self):
        moment = {
            "before_timestamp_s": 1.25,
            "timestamp_s": 10,
        }
        self.assertEqual(
            resolve_frames.timestamp_for(moment, "before", 0.2, 0.0),
            1.25,
        )

    def test_timestamp_for_applies_offsets_and_clamps_before_to_zero(self):
        moment = {"timestamp_s": 0.1}
        self.assertEqual(
            resolve_frames.timestamp_for(moment, "before", 0.5, 0.25),
            0.0,
        )
        self.assertEqual(
            resolve_frames.timestamp_for(moment, "after", 0.5, 0.25),
            0.35,
        )

    def test_timestamp_for_returns_none_without_a_valid_timestamp(self):
        self.assertIsNone(
            resolve_frames.timestamp_for({"label": "missing"}, "before", 0.2, 0.0)
        )


class RunManifestTests(unittest.TestCase):
    def test_load_json_unwraps_text_tool_responses(self):
        payload = {"pageId": "12:34", "createdNodeIds": ["12:34"]}
        wrapped = [{"type": "text", "text": json.dumps(payload)}]

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "result.json"
            source.write_text(json.dumps(wrapped))
            self.assertEqual(run_manifest.load_json(str(source)), payload)

    def test_normalize_uploaded_images_accepts_camel_and_snake_case(self):
        payload = {
            "results": [
                {"nodeId": "1:2", "imageHash": "hash-a", "assetKey": "before"},
                {"node_id": "1:3", "image_hash": "hash-b", "assetKey": "after"},
                {"nodeId": "1:4"},
                "invalid",
            ]
        }

        normalized = run_manifest.normalize_uploaded_images(payload)

        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0]["nodeId"], "1:2")
        self.assertEqual(normalized[0]["imageHash"], "hash-a")
        self.assertEqual(normalized[1]["nodeId"], "1:3")
        self.assertEqual(normalized[1]["imageHash"], "hash-b")
        self.assertEqual(normalized[1]["scaleMode"], "FILL")

    def test_update_upload_targets_records_node_ids_and_completes_storyboard(self):
        state = {
            "figma": {},
            "stages": {"storyboard": "pending"},
            "expected_uploads": [
                {"assetKey": "before", "status": "pending"},
                {"assetKey": "after", "status": "pending"},
            ],
        }
        targets = [
            {"assetKey": "before", "nodeId": "2:1"},
            {"assetKey": "after", "nodeId": "2:2"},
        ]

        run_manifest.update_upload_targets(state, targets)

        self.assertEqual(state["figma"]["upload_targets"], targets)
        self.assertEqual(state["expected_uploads"][0]["nodeId"], "2:1")
        self.assertEqual(state["expected_uploads"][0]["status"], "ready_to_upload")
        self.assertEqual(state["expected_uploads"][1]["nodeId"], "2:2")
        self.assertEqual(state["stages"]["storyboard"], "complete")

    def test_update_uploaded_images_matches_by_node_id_and_asset_key(self):
        state = {
            "figma": {},
            "stages": {"uploads": "pending"},
            "expected_uploads": [
                {"assetKey": "before", "nodeId": "3:1", "status": "ready_to_upload"},
                {"assetKey": "after", "nodeId": "3:2", "status": "ready_to_upload"},
            ],
        }
        uploaded = [
            {"assetKey": None, "nodeId": "3:1", "imageHash": "hash-a"},
            {"assetKey": "after", "nodeId": "new-node-id", "imageHash": "hash-b"},
        ]

        run_manifest.update_uploaded_images(state, uploaded)

        self.assertEqual(state["expected_uploads"][0]["imageHash"], "hash-a")
        self.assertEqual(state["expected_uploads"][1]["imageHash"], "hash-b")
        self.assertTrue(
            all(item["status"] == "uploaded" for item in state["expected_uploads"])
        )
        self.assertEqual(state["stages"]["uploads"], "complete")

    def test_write_fill_script_inserts_uploaded_image_hashes(self):
        uploaded = [
            {"nodeId": "4:5", "imageHash": "image-hash", "scaleMode": "FILL"}
        ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.js"
            output = root / "apply-fills.js"
            template.write_text(
                "const uploadedImages = [];\n"
                "if (!uploadedImages.length) throw new Error('No images');\n"
            )
            state = {
                "figma": {
                    "fill_script_template": str(template),
                    "uploaded_images": uploaded,
                }
            }

            run_manifest.write_fill_script(state, str(output))

            generated = output.read_text()
            prefix = "const uploadedImages = "
            suffix = ";\nif (!uploadedImages.length)"
            serialized = generated.split(prefix, 1)[1].split(suffix, 1)[0]
            self.assertEqual(json.loads(serialized), uploaded)
            self.assertEqual(state["figma"]["fill_script"], str(output))

    def test_write_fill_script_rejects_missing_template_or_uploads(self):
        with self.assertRaisesRegex(RuntimeError, "fill_script_template"):
            run_manifest.write_fill_script({"figma": {}}, "unused.js")

        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "template.js"
            template.write_text("const uploadedImages = [];")
            state = {
                "figma": {
                    "fill_script_template": str(template),
                    "uploaded_images": [],
                }
            }
            with self.assertRaisesRegex(RuntimeError, "uploaded_images"):
                run_manifest.write_fill_script(state, "unused.js")


if __name__ == "__main__":
    unittest.main()
