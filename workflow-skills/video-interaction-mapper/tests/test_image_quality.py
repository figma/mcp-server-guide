import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SKILL_DIR / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prepare = load_script("prepare_upload_frames")
generate = load_script("generate_figma_calls")


class ImageQualityTests(unittest.TestCase):
    def test_impossible_budget_fails_instead_of_shrinking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "output.jpg"
            Image.effect_noise((1600, 1000), 100).convert("RGB").save(source)

            with self.assertRaisesRegex(RuntimeError, "cannot fit"):
                prepare.prepare_image(
                    str(source),
                    output,
                    max_width=1440,
                    minimum_width=1440,
                    quality=75,
                    max_bytes=1024,
                )

    def test_native_width_is_preserved_when_source_is_smaller(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "output.jpg"
            Image.new("RGB", (800, 600), "white").save(source)

            info = prepare.prepare_image(
                str(source),
                output,
                max_width=1440,
                minimum_width=1440,
                quality=75,
                max_bytes=1024 * 1024,
            )

            self.assertEqual(info["width"], 800)
            self.assertEqual(info["required_width"], 800)
            self.assertTrue(info["readability_passed"])

    def test_generator_rejects_undersized_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "tiny.jpg"
            asset.touch()
            prepared = {
                "video_info": {"orientation": "landscape"},
                "image_budget": {"minimum_width": 1440},
                "moments": [
                    {
                        "moment_index": 1,
                        "before_upload_path": str(asset),
                        "before_upload_width": 560,
                        "before_source_width": 1920,
                        "before_required_width": 1440,
                        "before_upload_within_budget": True,
                        "before_readability_passed": True,
                        "after_upload_path": str(asset),
                        "after_upload_width": 560,
                        "after_source_width": 1920,
                        "after_required_width": 1440,
                        "after_upload_within_budget": True,
                        "after_readability_passed": True,
                    }
                ],
            }

            with self.assertRaisesRegex(ValueError, "below the required 1440px"):
                generate.validate_prepared_assets(prepared)


if __name__ == "__main__":
    unittest.main()
