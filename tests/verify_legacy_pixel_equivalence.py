#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
EXPORTER_PATH = ROOT / "uc-icons" / "scripts" / "export_skeuo_uc_icon.py"
sys.path.insert(0, str(EXPORTER_PATH.parent))
SPEC = importlib.util.spec_from_file_location("export_skeuo_uc_icon", EXPORTER_PATH)
assert SPEC and SPEC.loader
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


def main() -> int:
    archive = ROOT / "uc-icons" / "references" / "archive" / "PNGs_renamed"
    sources = sorted(archive.glob("*.png"))
    if len(sources) != 72:
        raise AssertionError(f"expected 72 legacy PNGs, found {len(sources)}")
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory) / "actual.png"
        for source in sources:
            with Image.open(source) as opened:
                expected = Image.new("RGBA", opened.size, exporter.BACKGROUND_RGBA)
                expected.alpha_composite(opened.convert("RGBA"))
            if expected.size != exporter.DELIVERY_SIZE:
                width, height = expected.size
                if abs((width / height) - exporter.DELIVERY_ASPECT) <= 0.01:
                    resized = expected.resize(exporter.DELIVERY_SIZE, Image.Resampling.LANCZOS)
                    expected.close()
                    expected = resized
                else:
                    expected.thumbnail(exporter.DELIVERY_SIZE, Image.Resampling.LANCZOS)
                    canvas = Image.new("RGBA", exporter.DELIVERY_SIZE, exporter.BACKGROUND_RGBA)
                    canvas.alpha_composite(
                        expected,
                        (
                            (exporter.DELIVERY_SIZE[0] - expected.size[0]) // 2,
                            (exporter.DELIVERY_SIZE[1] - expected.size[1]) // 2,
                        ),
                    )
                    expected.close()
                    expected = canvas
            exporter.create_delivery(source, destination, preserve_source=True)
            with Image.open(destination) as actual:
                difference = ImageChops.difference(expected, actual.convert("RGBA"))
                mismatch = difference.getbbox()
                difference.close()
            expected.close()
            if mismatch is not None:
                raise AssertionError(f"legacy exact export changed pixels: {source.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
