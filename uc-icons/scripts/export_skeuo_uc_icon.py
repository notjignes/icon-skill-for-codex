#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import deque
import re
import sys
from pathlib import Path

from PIL import Image


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "icon"


def newest_png(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = [p for p in root.rglob("*.png") if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_source(explicit: str | None) -> Path:
    if explicit:
        source = Path(explicit).expanduser()
        if source.exists():
            return source
        raise FileNotFoundError(f"Source image not found: {source}")

    home = Path.home()
    roots = [
        home / ".codex" / "generated_images",
        home / ".codex",
        home / "Library" / "Application Support" / "Codex" / "generated_images",
    ]
    newest = [p for p in (newest_png(root) for root in roots) if p is not None]
    if newest:
        return max(newest, key=lambda p: p.stat().st_mtime)
    raise FileNotFoundError("No generated PNG found. Pass --source <PNG_PATH>.")


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
TARGET_ASPECT = TARGET_SIZE[0] / TARGET_SIZE[1]


def bake_background(image: Image.Image) -> Image.Image:
    background = Image.new("RGBA", image.size, BACKGROUND_RGBA)
    background.alpha_composite(image.convert("RGBA"))
    return background


def normalize_opaque_background(image: Image.Image, remove_shadow: bool = False) -> Image.Image:
    pixels = image.load()
    width, height = image.size

    def is_light_neutral(x: int, y: int) -> bool:
        red, green, blue, alpha = pixels[x, y]
        if alpha != 255:
            return False
        channel_spread = max(red, green, blue) - min(red, green, blue)
        if max(red, green, blue) >= 218 and channel_spread <= 5:
            return True
        if not remove_shadow:
            return False
        close_to_background = (
            abs(red - BACKGROUND_RGBA[0]) <= 45
            and abs(green - BACKGROUND_RGBA[1]) <= 45
            and abs(blue - BACKGROUND_RGBA[2]) <= 45
        )
        return close_to_background and channel_spread <= 18

    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()
    for x in range(width):
        for y in (0, height - 1):
            if is_light_neutral(x, y):
                queue.append((x, y))
                seen.add((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if (x, y) not in seen and is_light_neutral(x, y):
                queue.append((x, y))
                seen.add((x, y))

    while queue:
        x, y = queue.popleft()
        pixels[x, y] = BACKGROUND_RGBA
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in seen and is_light_neutral(nx, ny):
                seen.add((nx, ny))
                queue.append((nx, ny))

    return image


def content_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    pixels = image.load()
    width, height = image.size
    min_x, min_y = width, height
    max_x = max_y = -1

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            is_background = (
                alpha == 255
                and abs(red - BACKGROUND_RGBA[0]) <= 8
                and abs(green - BACKGROUND_RGBA[1]) <= 8
                and abs(blue - BACKGROUND_RGBA[2]) <= 8
            )
            if not is_background:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < min_x or max_y < min_y:
        return None
    return min_x, min_y, max_x + 1, max_y + 1


def fit_to_reference_canvas(image: Image.Image) -> Image.Image:
    width, height = image.size
    aspect = width / height

    if abs(aspect - TARGET_ASPECT) <= 0.03:
        return image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

    bbox = content_bbox(image)
    if bbox is not None:
        left, top, right, bottom = bbox
        pad_x = max(24, round((right - left) * 0.12))
        pad_y = max(24, round((bottom - top) * 0.12))
        crop = image.crop((
            max(0, left - pad_x),
            max(0, top - pad_y),
            min(width, right + pad_x),
            min(height, bottom + pad_y),
        ))
    else:
        crop = image

    crop.thumbnail((round(TARGET_SIZE[0] * 0.92), round(TARGET_SIZE[1] * 0.88)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", TARGET_SIZE, BACKGROUND_RGBA)
    x = (TARGET_SIZE[0] - crop.size[0]) // 2
    y = (TARGET_SIZE[1] - crop.size[1]) // 2
    canvas.alpha_composite(crop, (x, y))
    return canvas


def preserve_source_export(image: Image.Image) -> Image.Image:
    image = bake_background(image)

    if image.size == TARGET_SIZE:
        return image

    width, height = image.size
    if abs((width / height) - TARGET_ASPECT) <= 0.01:
        return image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

    image.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", TARGET_SIZE, BACKGROUND_RGBA)
    x = (TARGET_SIZE[0] - image.size[0]) // 2
    y = (TARGET_SIZE[1] - image.size[1]) // 2
    canvas.alpha_composite(image, (x, y))
    return canvas


def export_icon(source: Path, subject: str, preserve_source: bool = False) -> Path:
    assets = Path.cwd() / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    output = unique_path(assets / f"{slugify(subject)}-skeuo-uc.png")

    image = Image.open(source).convert("RGBA")

    if preserve_source:
        image = preserve_source_export(image)
        image.save(output)
        return output

    image = normalize_opaque_background(bake_background(image), remove_shadow=True)
    image = fit_to_reference_canvas(image)
    image = normalize_opaque_background(image, remove_shadow=True)

    image.save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a Skeuo-UC generated PNG into ./assets.")
    parser.add_argument("--subject", required=True, help="Icon subject, used for the output filename.")
    parser.add_argument("--source", help="Generated PNG path. If omitted, the newest generated PNG is used.")
    parser.add_argument("--preserve-source", action="store_true", help="Resize an existing archive/service PNG without background or material normalization.")
    parser.add_argument("--baked", action="store_true", help="Deprecated; Waterlemon icons always use #f5f5f5.")
    args = parser.parse_args()

    try:
        source = find_source(args.source)
        output = export_icon(source, args.subject, preserve_source=args.preserve_source)
        with Image.open(output) as exported:
            print(f"source={source}")
            print(f"saved={output}")
            print(f"size={exported.size[0]}x{exported.size[1]}")
            print(f"mode={exported.mode}")
            print("background=#f5f5f5")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
