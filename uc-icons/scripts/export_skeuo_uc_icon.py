#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "icon"


def find_source(explicit: str | None) -> Path:
    if not explicit:
        raise ValueError("Explicit source image required. Pass --source <PNG_PATH>.")
    source = Path(explicit).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Source image not found: {source}")
    if not source.is_file():
        raise ValueError(f"Source image is not a file: {source}")
    return source


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not create a unique filename near {path}")


BACKGROUND_RGBA = (245, 245, 245, 255)
TARGET_SIZE = (1024, 768)


def parse_background(value: str) -> tuple[int, int, int, int]:
    if value.lower() == "transparent":
        return (0, 0, 0, 0)
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Background must be #RRGGBB or transparent.")
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5)) + (255,)


def fit_to_reference_canvas(
    image: Image.Image,
    background_rgba: tuple[int, int, int, int] = BACKGROUND_RGBA,
) -> Image.Image:
    """Contain the whole source frame without segmentation, cropping or cleanup."""
    image = image.convert("RGBA")
    width, height = image.size
    scale = min(TARGET_SIZE[0] / width, TARGET_SIZE[1] / height)
    fitted_size = (
        max(1, min(TARGET_SIZE[0], round(width * scale))),
        max(1, min(TARGET_SIZE[1], round(height * scale))),
    )
    if image.size != fitted_size:
        image = image.resize(fitted_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", TARGET_SIZE, background_rgba)
    position = (
        (TARGET_SIZE[0] - image.width) // 2,
        (TARGET_SIZE[1] - image.height) // 2,
    )
    if background_rgba[3] == 0:
        # Retain source alpha. Opaque backgrounds are never removed.
        canvas.paste(image, position)
    else:
        # Composite existing alpha only; opaque source pixels keep their colors.
        canvas.alpha_composite(image, position)
    return canvas


def preserve_source_export(image: Image.Image) -> Image.Image:
    """Compatibility helper: every export now preserves the complete source frame."""
    return fit_to_reference_canvas(image)


def inspect_export(
    image: Image.Image,
    background_rgba: tuple[int, int, int, int] = BACKGROUND_RGBA,
) -> dict[str, object]:
    """Measure output properties; edge agreement is not full background validation."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    perimeter = [pixels[x, 0] for x in range(width)]
    if height > 1:
        perimeter.extend(pixels[x, height - 1] for x in range(width))
    for y in range(1, height - 1):
        perimeter.append(pixels[0, y])
        if width > 1:
            perimeter.append(pixels[width - 1, y])
    if background_rgba[3] == 0:
        matches = sum(pixel[3] == 0 for pixel in perimeter)
        canvas_background = "transparent"
    else:
        matches = sum(pixel == background_rgba for pixel in perimeter)
        canvas_background = "#" + "".join(f"{channel:02x}" for channel in background_rgba[:3])
    return {
        "size": f"{image.width}x{image.height}",
        "mode": image.mode,
        "opaque": rgba.getchannel("A").getextrema() == (255, 255),
        "canvas_background": canvas_background,
        "perimeter_match_fraction": matches / len(perimeter),
    }


def export_icon(
    source: Path,
    subject: str,
    preserve_source: bool = False,
    background: str = "#f5f5f5",
) -> Path:
    # preserve_source is retained for existing callers. All modes now preserve
    # opaque source content, including shadows and the rendered background.
    background_rgba = parse_background(background)
    with Image.open(source) as original:
        image = fit_to_reference_canvas(original, background_rgba)

    assets = Path.cwd() / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    output = unique_path(assets / f"{slugify(subject)}-skeuo-uc.png")
    image.save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Contain a complete UC icon image in ./assets without background cleanup.")
    parser.add_argument("--subject", required=True, help="Icon subject, used for the output filename.")
    parser.add_argument("--source", required=True, help="Explicit generated, archive, or user-supplied image path.")
    parser.add_argument("--preserve-source", action="store_true", help="Compatibility flag; all exports now preserve the complete source frame.")
    parser.add_argument("--background", default="#f5f5f5", help="Canvas padding and existing-alpha composite color (#RRGGBB), or transparent to retain alpha. Never removes an opaque background.")
    parser.add_argument("--baked", action="store_true", help="Deprecated compatibility flag; no effect. Use --background for explicit variants.")
    args = parser.parse_args()

    try:
        source = find_source(args.source)
        output = export_icon(source, args.subject, preserve_source=args.preserve_source, background=args.background)
        with Image.open(output) as exported:
            measured = inspect_export(exported, parse_background(args.background))
            print(f"source={source}")
            print(f"saved={output}")
            print(f"size={measured['size']}")
            print(f"mode={measured['mode']}")
            print(f"opaque={str(measured['opaque']).lower()}")
            print(f"canvas_background={measured['canvas_background']}")
            print(f"perimeter_match_fraction={measured['perimeter_match_fraction']:.6f}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
