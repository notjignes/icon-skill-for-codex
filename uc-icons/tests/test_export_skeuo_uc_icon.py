from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_skeuo_uc_icon.py"
SPEC = importlib.util.spec_from_file_location("export_skeuo_uc_icon", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


def export_image(image: Image.Image, **options: object) -> Image.Image:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source = temp_path / "source.png"
        image.save(source)
        with patch.object(EXPORTER.Path, "cwd", return_value=temp_path):
            output = EXPORTER.export_icon(source, "test icon", **options)
        with Image.open(output) as exported:
            return exported.copy()


class ExportIsolationTests(unittest.TestCase):
    def test_find_source_fails_closed_without_explicit_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "Explicit source image required"):
            EXPORTER.find_source(None)

    def test_cli_requires_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--subject", "test icon"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("--source", completed.stderr)
            self.assertFalse((Path(temp_dir) / "assets").exists())

    def test_cli_exports_only_the_explicit_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "explicit-source.png"
            Image.new("RGBA", (40, 30), (80, 120, 160, 255)).save(source)
            Image.new("RGBA", (1024, 768), (0, 255, 0, 255)).save(temp_path / "newer-unrelated.png")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--subject", "test icon", "--source", str(source), "--preserve-source"],
                cwd=temp_path,
                capture_output=True,
                text=True,
                check=False,
            )
            output = temp_path / "assets" / "test-icon-skeuo-uc.png"
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(f"source={source}", completed.stdout)
            with Image.open(output) as exported:
                self.assertEqual(exported.size, (1024, 768))
                self.assertEqual(exported.mode, "RGBA")
                self.assertEqual(exported.getpixel((512, 384)), (80, 120, 160, 255))

    def test_invalid_source_creates_no_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with patch.object(EXPORTER.Path, "cwd", return_value=temp_path):
                with self.assertRaises(FileNotFoundError):
                    EXPORTER.export_icon(temp_path / "missing.png", "missing")
            self.assertFalse((temp_path / "assets").exists())

    def test_filename_collision_keeps_previous_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source.png"
            Image.new("RGB", (1024, 768), (80, 120, 160)).save(source)
            with patch.object(EXPORTER.Path, "cwd", return_value=temp_path):
                first = EXPORTER.export_icon(source, "test icon")
                first_bytes = first.read_bytes()
                second = EXPORTER.export_icon(source, "test icon")
            self.assertEqual(first.name, "test-icon-skeuo-uc.png")
            self.assertEqual(second.name, "test-icon-skeuo-uc-2.png")
            self.assertEqual(first.read_bytes(), first_bytes)
            self.assertTrue(second.is_file())


class NonDestructiveExportTests(unittest.TestCase):
    def test_same_size_pale_subject_is_pixel_identical(self) -> None:
        source = Image.new("RGBA", (1024, 768), (245, 245, 245, 255))
        draw = ImageDraw.Draw(source)
        draw.ellipse((200, 100, 824, 668), fill=(230, 230, 230, 255))
        draw.rectangle((390, 220, 634, 548), fill=(255, 255, 255, 255))
        self.assertEqual(export_image(source).tobytes(), source.tobytes())

    def test_shadow_and_colored_surface_are_preserved(self) -> None:
        source = Image.new("RGBA", (1024, 768), (245, 245, 245, 255))
        draw = ImageDraw.Draw(source)
        draw.ellipse((150, 500, 874, 680), fill=(218, 220, 223, 255))
        draw.rectangle((260, 130, 764, 540), fill=(227, 225, 220, 255))
        for preserve in (False, True):
            with self.subTest(preserve_source=preserve):
                self.assertEqual(export_image(source, preserve_source=preserve).tobytes(), source.tobytes())

    def test_opaque_white_background_is_not_recolored(self) -> None:
        source = Image.new("RGBA", (1024, 768), (255, 255, 255, 255))
        output = export_image(source)
        self.assertEqual(output.tobytes(), source.tobytes())
        report = EXPORTER.inspect_export(output)
        self.assertEqual(report["canvas_background"], "#f5f5f5")
        self.assertEqual(report["perimeter_match_fraction"], 0.0)
        self.assertTrue(report["opaque"])

    def test_existing_alpha_is_composited_without_erasing_opaque_pixels(self) -> None:
        source = Image.new("RGBA", (1024, 768), (255, 0, 0, 0))
        source.putpixel((10, 10), (100, 150, 200, 128))
        source.putpixel((11, 10), (230, 230, 230, 255))
        output = export_image(source)
        self.assertEqual(output.getpixel((0, 0)), (245, 245, 245, 255))
        self.assertEqual(output.getpixel((10, 10)), (172, 197, 222, 255))
        self.assertEqual(output.getpixel((11, 10)), (230, 230, 230, 255))
        self.assertEqual(output.getchannel("A").getextrema(), (255, 255))

    def test_complete_frame_is_contained_without_stretching(self) -> None:
        # Expected bounds distinguish containment from the previous near-4:3
        # stretching and subject-based cropping behavior.
        cases = [
            ((1024, 1024), (128, 0, 896, 768)),
            ((512, 1024), (320, 0, 704, 768)),
            ((2048, 512), (0, 256, 1024, 512)),
            ((1000, 760), (6, 0, 1017, 768)),
            ((40, 30), (0, 0, 1024, 768)),
        ]
        for size, expected_bounds in cases:
            with self.subTest(source_size=size):
                source = Image.new("RGBA", size, (80, 120, 160, 255))
                output = export_image(source)
                canvas = Image.new("RGB", output.size, (245, 245, 245))
                bounds = ImageChops.difference(output.convert("RGB"), canvas).getbbox()
                self.assertEqual(output.size, (1024, 768))
                self.assertEqual(bounds, expected_bounds)

    def test_full_frame_corner_details_survive_square_resize(self) -> None:
        source = Image.new("RGBA", (1024, 1024), (245, 245, 245, 255))
        draw = ImageDraw.Draw(source)
        for box in ((0, 0, 63, 63), (960, 0, 1023, 63), (0, 960, 63, 1023), (960, 960, 1023, 1023)):
            draw.rectangle(box, fill=(20, 40, 60, 255))
        output = export_image(source)
        for point in ((140, 12), (884, 12), (140, 755), (884, 755)):
            self.assertEqual(output.getpixel(point), (20, 40, 60, 255))

    def test_transparent_mode_retains_alpha_but_never_removes_opaque_background(self) -> None:
        source = Image.new("RGBA", (1024, 768), (245, 245, 245, 255))
        source.putpixel((10, 10), (100, 150, 200, 128))
        source.putpixel((11, 10), (255, 0, 0, 0))
        output = export_image(source, background="transparent")
        self.assertEqual(output.tobytes(), source.tobytes())
        self.assertFalse(EXPORTER.inspect_export(output, (0, 0, 0, 0))["opaque"])
        self.assertEqual(output.getpixel((0, 0)), (245, 245, 245, 255))

    def test_explicit_canvas_color_and_transparent_padding(self) -> None:
        source = Image.new("RGBA", (1024, 1024), (80, 120, 160, 255))
        colored = export_image(source, background="#123456")
        self.assertEqual(colored.getpixel((0, 0)), (18, 52, 86, 255))
        self.assertEqual(colored.getpixel((512, 384)), (80, 120, 160, 255))
        transparent = export_image(source, background="transparent")
        self.assertEqual(transparent.getpixel((0, 0))[3], 0)
        self.assertEqual(transparent.getpixel((512, 384)), (80, 120, 160, 255))

    def test_invalid_background_is_rejected_before_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "#RRGGBB or transparent"):
            export_image(Image.new("RGB", (40, 30)), background="remove-background")

    def test_cli_reports_measurements_without_claiming_full_background_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "white.png"
            Image.new("RGB", (1024, 768), (255, 255, 255)).save(source)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--source", str(source), "--subject", "white"],
                cwd=temp_dir, capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            fields = dict(line.split("=", 1) for line in completed.stdout.splitlines())
            self.assertEqual(fields["size"], "1024x768")
            self.assertEqual(fields["mode"], "RGBA")
            self.assertEqual(fields["opaque"], "true")
            self.assertEqual(fields["canvas_background"], "#f5f5f5")
            self.assertEqual(fields["perimeter_match_fraction"], "0.000000")
            self.assertNotIn("background", fields)


if __name__ == "__main__":
    unittest.main()
