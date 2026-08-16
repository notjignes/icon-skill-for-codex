from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
import gc
from pathlib import Path

from PIL import Image
from PIL import ImageDraw


ROOT = Path(__file__).resolve().parents[1]
EXPORTER_PATH = ROOT / "uc-icons" / "scripts" / "export_skeuo_uc_icon.py"
sys.path.insert(0, str(EXPORTER_PATH.parent))
SPEC = importlib.util.spec_from_file_location("export_skeuo_uc_icon", EXPORTER_PATH)
assert SPEC and SPEC.loader
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExporterTests(unittest.TestCase):
    def tearDown(self):
        gc.collect()

    def run_in_temp(self, callback):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                return callback(Path(directory))
            finally:
                os.chdir(previous)

    def test_generated_valid_master_is_preserved_byte_for_byte(self):
        def exercise(directory: Path):
            source = directory / "native.png"
            image = Image.new("RGB", (2048, 1536), (245, 245, 245))
            ImageDraw.Draw(image).rectangle((640, 420, 1408, 1116), fill=(90, 130, 180))
            image.save(source, optimize=True)
            image.close()
            before = sha256(source)
            result = exporter.export_icon(source.resolve(), "native master")
            master = Path(result["master_path"])
            delivery = Path(result["delivery_path"])
            self.assertEqual(before, sha256(master))
            self.assertFalse(result["master_transformed"])
            self.assertEqual([2048, 1536], result["master_size"])
            with Image.open(delivery) as opened:
                self.assertEqual((1024, 768), opened.size)
                self.assertEqual((245, 245, 245), opened.convert("RGB").getpixel((0, 0)))

        self.run_in_temp(exercise)

    def test_smaller_valid_native_result_is_never_upscaled_as_master(self):
        def exercise(directory: Path):
            source = directory / "small.png"
            image = Image.new("RGB", (1024, 768), (245, 245, 245))
            image.save(source)
            image.close()
            result = exporter.export_icon(source.resolve(), "small native")
            self.assertEqual([1024, 768], result["master_size"])
            with Image.open(result["master_path"]) as opened:
                self.assertEqual((1024, 768), opened.size)

        self.run_in_temp(exercise)

    def test_exact_export_writes_no_master(self):
        def exercise(directory: Path):
            source = directory / "legacy.png"
            image = Image.new("RGBA", (400, 300), (40, 60, 90, 190))
            image.save(source)
            image.close()
            result = exporter.export_icon(source.resolve(), "legacy exact", preserve_source=True)
            self.assertIsNone(result["master_path"])
            self.assertFalse(list((directory / "assets").glob("*-master*.png")))
            with Image.open(result["delivery_path"]) as opened:
                self.assertEqual((1024, 768), opened.size)
                self.assertEqual((255, 255), opened.getchannel("A").getextrema())

        self.run_in_temp(exercise)

    def test_explicit_source_is_required(self):
        with self.assertRaisesRegex(ValueError, "automatic newest-image discovery is disabled"):
            exporter.find_source(None)

    def test_record_hashes_and_native_sizes_are_consistent(self):
        def exercise(directory: Path):
            source = directory / "record-source.png"
            image = Image.new("RGB", (1600, 1200), (245, 245, 245))
            image.save(source)
            image.close()
            result = exporter.export_icon(source.resolve(), "record check")
            record = json.loads(Path(result["record_path"]).read_text())
            self.assertEqual(sha256(source), record["source_sha256"])
            self.assertEqual(sha256(Path(record["master_path"])), record["master_sha256"])
            self.assertEqual(sha256(Path(record["delivery_path"])), record["delivery_sha256"])
            self.assertEqual([1600, 1200], record["master_size"])
            self.assertEqual([1024, 768], record["delivery_size"])

        self.run_in_temp(exercise)

    def test_dark_generated_background_is_rejected_without_false_f5_record(self):
        def exercise(directory: Path):
            source = directory / "dark.png"
            Image.new("RGB", (1024, 768), (10, 10, 10)).save(source)
            with self.assertRaisesRegex(ValueError, "non-neutral or dark"):
                exporter.export_icon(source.resolve(), "dark background")
            self.assertEqual([], list((directory / "assets").iterdir()))

        self.run_in_temp(exercise)

    def test_pale_neutral_background_is_normalized_to_exact_f5(self):
        def exercise(directory: Path):
            source = directory / "off-white.png"
            image = Image.new("RGB", (1024, 768), (232, 232, 232))
            ImageDraw.Draw(image).ellipse((300, 180, 724, 604), fill=(50, 100, 160))
            image.save(source)
            result = exporter.export_icon(source.resolve(), "off white")
            self.assertTrue(result["master_transformed"])
            with Image.open(result["master_path"]) as opened:
                self.assertEqual((245, 245, 245), opened.convert("RGB").getpixel((0, 0)))

        self.run_in_temp(exercise)

    def test_palette_transparency_is_detected_and_baked(self):
        def exercise(directory: Path):
            source = directory / "palette.png"
            image = Image.new("P", (1024, 768), 0)
            palette = [245, 245, 245, 60, 100, 180] + [0, 0, 0] * 254
            image.putpalette(palette)
            ImageDraw.Draw(image).rectangle((300, 200, 724, 568), fill=1)
            image.save(source, transparency=0)
            with Image.open(source) as opened:
                self.assertFalse(exporter.is_opaque(opened))
            result = exporter.export_icon(source.resolve(), "palette alpha")
            self.assertTrue(result["master_transformed"])
            with Image.open(result["master_path"]) as opened:
                self.assertEqual((255, 255), opened.convert("RGBA").getchannel("A").getextrema())
                self.assertEqual((245, 245, 245), opened.convert("RGB").getpixel((0, 0)))

        self.run_in_temp(exercise)


if __name__ == "__main__":
    unittest.main()
