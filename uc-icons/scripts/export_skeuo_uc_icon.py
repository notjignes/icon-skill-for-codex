#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from image_contract import scan_border_component


BACKGROUND_RGBA = (245, 245, 245, 255)
DELIVERY_SIZE = (1024, 768)
DELIVERY_ASPECT = DELIVERY_SIZE[0] / DELIVERY_SIZE[1]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "icon"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_source(explicit: str | None) -> Path:
    if not explicit:
        raise ValueError("Pass --source <PNG_PATH>; automatic newest-image discovery is disabled.")
    source = Path(explicit).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source image not found: {source}")
    return source


def output_paths(assets: Path, subject: str, include_master: bool) -> tuple[Path | None, Path, Path]:
    slug = slugify(subject)
    for index in range(1, 1000):
        suffix = "" if index == 1 else f"-{index}"
        delivery = assets / f"{slug}-skeuo-uc{suffix}.png"
        master = assets / f"{slug}-skeuo-uc-master{suffix}.png" if include_master else None
        record = assets / f"{slug}-skeuo-uc{suffix}.json"
        if not delivery.exists() and not record.exists() and (master is None or not master.exists()):
            return master, delivery, record
    raise RuntimeError(f"Could not create unique output paths for {subject!r}")


def bake_background(image: Image.Image) -> Image.Image:
    background = Image.new("RGBA", image.size, BACKGROUND_RGBA)
    background.alpha_composite(image.convert("RGBA"))
    return background


def normalize_connected_background(image: Image.Image) -> Image.Image:
    """Normalize only border-connected pale neutral pixels to UC Grey 10.

    This deliberately does not attempt semantic shadow removal. Generated masters are
    expected to satisfy the no-external-shadow contract before export.
    """

    image = image.convert("RGBA")
    def is_background_candidate(pixel: tuple[int, ...]) -> bool:
        red, green, blue, alpha = pixel
        if alpha != 255:
            return True
        spread = max(red, green, blue) - min(red, green, blue)
        return min(red, green, blue) >= 218 and spread <= 8
    scan_border_component(image, is_background_candidate, replacement=BACKGROUND_RGBA)
    return image


def is_pale_neutral_or_transparent(pixel: tuple[int, ...]) -> bool:
    red, green, blue, alpha = pixel
    if alpha != 255:
        return True
    return min(red, green, blue) >= 218 and max(red, green, blue) - min(red, green, blue) <= 8


def border_pixels(image: Image.Image) -> list[tuple[int, ...]]:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    result = [pixels[x, y] for x in range(width) for y in (0, height - 1)]
    result.extend(pixels[x, y] for y in range(1, height - 1) for x in (0, width - 1))
    return result


def exact_background_facts(image: Image.Image) -> dict[str, object]:
    rgba = image.convert("RGBA")
    border = border_pixels(rgba)
    component_count, exact_count = scan_border_component(
        rgba,
        is_pale_neutral_or_transparent,
        is_exact=lambda pixel: pixel == BACKGROUND_RGBA,
    )
    ratio = exact_count / component_count if component_count else 0.0
    return {
        "border_normalizable": bool(border) and all(is_pale_neutral_or_transparent(pixel) for pixel in border),
        "border_f5": bool(border) and all(pixel == BACKGROUND_RGBA for pixel in border),
        "connected_background_exact_ratio": ratio,
        "connected_background_f5": ratio >= 0.995,
    }


def require_exact_background(image: Image.Image, label: str) -> None:
    facts = exact_background_facts(image)
    if not facts["border_f5"] or not facts["connected_background_f5"]:
        raise ValueError(f"{label} does not expose a verified exact #f5f5f5 background")


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
            background = (
                alpha == 255
                and abs(red - 245) <= 8
                and abs(green - 245) <= 8
                and abs(blue - 245) <= 8
            )
            if not background:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        return None
    return min_x, min_y, max_x + 1, max_y + 1


def fit_to_canvas(image: Image.Image, target: tuple[int, int], preserve_framing: bool) -> Image.Image:
    image = image.convert("RGBA")
    width, height = image.size
    target_width, target_height = target
    target_aspect = target_width / target_height
    source_aspect = width / height

    if abs(source_aspect - target_aspect) <= 0.01:
        return image.resize(target, Image.Resampling.LANCZOS)

    if preserve_framing:
        fitted = image.copy()
    else:
        bbox = content_bbox(image)
        if bbox is None:
            fitted = image.copy()
        else:
            left, top, right, bottom = bbox
            pad_x = max(24, round((right - left) * 0.12))
            pad_y = max(24, round((bottom - top) * 0.12))
            fitted = image.crop((
                max(0, left - pad_x),
                max(0, top - pad_y),
                min(width, right + pad_x),
                min(height, bottom + pad_y),
            ))

    fitted.thumbnail(
        (round(target_width * 0.94), round(target_height * 0.92)),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", target, BACKGROUND_RGBA)
    x = (target_width - fitted.size[0]) // 2
    y = (target_height - fitted.size[1]) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas


def is_opaque(image: Image.Image) -> bool:
    # Conversion catches palette PNGs whose transparency is stored in a tRNS chunk.
    alpha = image.convert("RGBA").getchannel("A")
    extrema = alpha.getextrema()
    return extrema == (255, 255)


def create_master(source: Path, destination: Path) -> tuple[bool, tuple[int, int], str]:
    """Preserve a valid native 4:3 PNG byte-for-byte; otherwise normalize without upscaling."""

    with Image.open(source) as opened:
        source_size = opened.size
        source_format = opened.format
        opaque = is_opaque(opened)
        aspect = opened.width / opened.height
        background = exact_background_facts(opened)
        if not background["border_normalizable"]:
            raise ValueError(
                "Generated source has a non-neutral or dark exposed border; regenerate on exact #f5f5f5"
            )
        direct_copy = (
            source_format == "PNG"
            and opaque
            and abs(aspect - DELIVERY_ASPECT) <= 0.01
            and background["border_f5"]
            and background["connected_background_f5"]
        )
        if direct_copy:
            shutil.copy2(source, destination)
            return False, source_size, opened.mode

        normalized = normalize_connected_background(bake_background(opened))
        if abs(aspect - DELIVERY_ASPECT) > 0.01:
            if aspect > DELIVERY_ASPECT:
                target_width = min(opened.width, 2048)
                target_height = max(16, round(target_width / DELIVERY_ASPECT))
            else:
                target_height = min(opened.height, 1536)
                target_width = max(16, round(target_height * DELIVERY_ASPECT))
            normalized = fit_to_canvas(normalized, (target_width, target_height), preserve_framing=False)
        require_exact_background(normalized, "Normalized master")
        normalized.save(destination, format="PNG", optimize=True)
        return True, normalized.size, normalized.mode


def create_delivery(source: Path, destination: Path, preserve_source: bool) -> tuple[tuple[int, int], str]:
    with Image.open(source) as opened:
        image = bake_background(opened)
        if preserve_source:
            if image.size != DELIVERY_SIZE:
                width, height = image.size
                if abs((width / height) - DELIVERY_ASPECT) <= 0.01:
                    image = image.resize(DELIVERY_SIZE, Image.Resampling.LANCZOS)
                else:
                    image.thumbnail(DELIVERY_SIZE, Image.Resampling.LANCZOS)
                    canvas = Image.new("RGBA", DELIVERY_SIZE, BACKGROUND_RGBA)
                    canvas.alpha_composite(
                        image,
                        ((DELIVERY_SIZE[0] - image.size[0]) // 2, (DELIVERY_SIZE[1] - image.size[1]) // 2),
                    )
                    image = canvas
        else:
            image = normalize_connected_background(image)
            image = fit_to_canvas(image, DELIVERY_SIZE, preserve_framing=False)
            image = normalize_connected_background(image)
        if not is_opaque(image):
            raise ValueError("Delivery must be opaque")
        if not preserve_source:
            require_exact_background(image, "Delivery")
        image.save(destination, format="PNG", optimize=True)
        return image.size, image.mode


def export_icon(source: Path, subject: str, preserve_source: bool = False) -> dict[str, object]:
    assets = Path.cwd() / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    master_path, delivery_path, record_path = output_paths(assets, subject, include_master=not preserve_source)

    try:
        master_transformed = False
        master_size: tuple[int, int] | None = None
        master_mode: str | None = None
        delivery_source = source
        if master_path is not None:
            master_transformed, master_size, master_mode = create_master(source, master_path)
            delivery_source = master_path

        delivery_size, delivery_mode = create_delivery(
            delivery_source,
            delivery_path,
            preserve_source=preserve_source,
        )
    except Exception:
        for partial in (master_path, delivery_path, record_path):
            if partial is not None:
                partial.unlink(missing_ok=True)
        raise

    record: dict[str, object] = {
        "schema_version": 1,
        "subject": subject,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preserve_source": preserve_source,
        "source_path": str(source),
        "source_sha256": sha256_file(source),
        "master_path": str(master_path) if master_path else None,
        "master_sha256": sha256_file(master_path) if master_path else None,
        "master_size": list(master_size) if master_size else None,
        "master_mode": master_mode,
        "master_transformed": master_transformed,
        "delivery_path": str(delivery_path),
        "delivery_sha256": sha256_file(delivery_path),
        "delivery_size": list(delivery_size),
        "delivery_mode": delivery_mode,
        "background": "legacy-source-treatment" if preserve_source else "#f5f5f5",
    }
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    record["record_path"] = str(record_path)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a high-resolution UC icon master and 1024x768 delivery.")
    parser.add_argument("--subject", required=True, help="Icon subject, used for output filenames.")
    parser.add_argument("--source", required=True, help="Explicit generated or archive PNG path.")
    parser.add_argument(
        "--preserve-source",
        action="store_true",
        help="Create only a delivery from an existing canonical archive master.",
    )
    parser.add_argument("--json", action="store_true", help="Print the export record as JSON.")
    args = parser.parse_args()

    try:
        record = export_icon(find_source(args.source), args.subject, preserve_source=args.preserve_source)
        if args.json:
            print(json.dumps(record, indent=2))
        else:
            if record["master_path"]:
                print(f"master={record['master_path']}")
                print(f"master_size={record['master_size'][0]}x{record['master_size'][1]}")
            print(f"saved={record['delivery_path']}")
            print("size=1024x768")
            print(f"mode={record['delivery_mode']}")
            print("background=#f5f5f5")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
