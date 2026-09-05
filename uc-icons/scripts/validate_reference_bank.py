#!/usr/bin/env python3
"""Validate the bundled reference index without modifying it or loading images in chat."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from pathlib import Path


COMMON_FIELDS = {
    "asset_id", "image_path", "sha256", "source_role", "approval_status",
    "provenance_source", "material_tags", "finish_tags",
}
ARCHIVE_FIELDS = {
    "original_filename", "service_file", "material_index_file", "type",
    "materials", "objects", "colors",
}
MANIFESTS = {
    "references/archive/PNGs_renamed/MANIFEST.csv": (
        ARCHIVE_FIELDS, "service_file", {"service_asset"},
    ),
    "references/archive/PNGs_material_index/MANIFEST.csv": (
        ARCHIVE_FIELDS, "material_index_file", {"material_reference"},
    ),
    "references/base-objects/MANIFEST.csv": (
        {"base_file", "original_filename", "type", "materials", "objects", "colors",
         "orientation", "canonical_for", "allowed_edits", "do_not_use_for", "notes"},
        "base_file", {"editable_base"},
    ),
    "references/new-object-references/MANIFEST.csv": (
        {"reference_file", "type", "objects", "materials", "colors", "orientation",
         "style_role", "good_for", "avoid_for", "notes", "object_family",
         "identity_aliases", "composition_family", "approved_for"},
        "reference_file", {"form_reference", "material_reference", "composition_reference"},
    ),
}
APPROVAL_STATES = {"pending", "approved", "existing_curated", "rejected"}
CHARACTER_ALIASES = {
    "base/base-female-eyes-closed.png": "Avatar base - female (eyes closed).png",
    "base/base-female-eyes-open.png": "Avatar base - female (eyes open).png",
    "base/base-male-eyes-closed.png": "Avatar base - male (eyes closed).png",
    "base/base-male-eyes-open.png": "Avatar base - male (eyes open).png",
    "female-salon-spa.png": "Womens salon & spa (Dubai).png",
    "insta-help-india.png": "Insta help (India).png",
    "live-in-maid-dubai.png": "Live-in help (Dubai).png",
    "luxury-female-salon-spa.png": "Luxury Womens salon & spa (Dubai).png",
    "maid-dubai.png": "All in one help (Dubai).png",
    "male-salon-massage.png": "Mens salon & massage (Dubai).png",
    "premium-helper.png": "Premium helper (Dubai).png",
}


def _reference_path(skill_dir: Path, value: str) -> Path:
    """Only bundled, skill-relative PNG paths are reference-bank inputs."""
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or "\\" in value:
        raise ValueError("image_path must be a safe skill-relative path")
    path = (skill_dir / relative).resolve()
    references = (skill_dir / "references").resolve()
    if not path.is_relative_to(references) or path.suffix.lower() != ".png":
        raise ValueError("image_path must resolve to a PNG within the skill references")
    if not path.is_file():
        raise ValueError(f"missing image: {value}")
    return path


def _image_hash(path: Path) -> str:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("source is not a PNG with an IHDR header")
    width, height = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0:
        raise ValueError("PNG dimensions must be positive")
    return hashlib.sha256(data).hexdigest()


def validate_reference_bank(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    errors: list[str] = []
    manifest_counts: dict[str, int] = {}
    hashes: dict[Path, str] = {}
    referenced_paths: set[Path] = set()
    ids: dict[str, str] = {}
    canonical_ids: dict[str, str] = {}
    material_ids: set[str] = set()
    base_ids: set[str] = set()

    def image_hash(path: Path) -> str:
        if path not in hashes:
            hashes[path] = _image_hash(path)
        return hashes[path]

    for relative, (legacy_fields, alias_key, allowed_roles) in MANIFESTS.items():
        manifest = skill_dir / relative
        if not manifest.is_file():
            errors.append(f"{relative}: missing manifest")
            continue
        with manifest.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)):
                errors.append(f"{relative}: duplicate column names")
            missing = (COMMON_FIELDS | legacy_fields) - set(headers)
            if missing:
                errors.append(f"{relative}: missing columns: {', '.join(sorted(missing))}")
            rows = list(reader)
        manifest_counts[relative] = len(rows)
        seen_aliases: set[str] = set()
        seen_ids: set[str] = set()
        for line, row in enumerate(rows, start=2):
            label = f"{relative}:{line}"
            if None in row or any(value is None for value in row.values()):
                errors.append(f"{label}: malformed CSV row")
                continue
            empty = [field for field in COMMON_FIELDS | {alias_key} if not row.get(field, "").strip()]
            if empty:
                errors.append(f"{label}: empty required values: {', '.join(sorted(empty))}")
            alias = row.get(alias_key, "")
            asset_id = row.get("asset_id", "")
            digest = row.get("sha256", "")
            if alias in seen_aliases:
                errors.append(f"{label}: duplicate alias {alias!r}")
            seen_aliases.add(alias)
            if asset_id in seen_ids:
                errors.append(f"{label}: duplicate asset_id within manifest: {asset_id}")
            seen_ids.add(asset_id)
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                errors.append(f"{label}: sha256 must be 64 lowercase hexadecimal characters")
            elif asset_id != f"uc-icon-{digest[:16]}":
                errors.append(f"{label}: asset_id does not match source sha256")
            if asset_id in ids and ids[asset_id] != digest:
                errors.append(f"{label}: inconsistent sha256 for asset_id {asset_id}")
            ids[asset_id] = digest
            roles = set(row.get("source_role", "").split(";"))
            if not roles or not roles.issubset(allowed_roles):
                errors.append(f"{label}: unsupported source_role for this manifest")
            if row.get("approval_status") not in APPROVAL_STATES:
                errors.append(f"{label}: unsupported approval_status")
            try:
                path = _reference_path(skill_dir, row.get("image_path", ""))
                referenced_paths.add(path)
                if image_hash(path) != digest:
                    errors.append(f"{label}: source sha256 mismatch")
            except (OSError, ValueError) as exc:
                errors.append(f"{label}: {exc}")
                continue
            if alias_key == "service_file":
                expected = (skill_dir / "references/archive/PNGs_renamed" / alias).resolve()
                if path != expected:
                    errors.append(f"{label}: service image_path must identify its canonical service_file")
                canonical_ids[asset_id] = row.get("image_path", "")
            elif alias_key == "material_index_file":
                material_ids.add(asset_id)
            elif alias_key == "base_file":
                base_ids.add(asset_id)
            if alias_key in {"base_file", "material_index_file"}:
                if canonical_ids.get(asset_id) != row.get("image_path"):
                    errors.append(f"{label}: alias must point to the matching canonical service image")

    if material_ids != set(canonical_ids):
        errors.append("material manifest must index every canonical service asset exactly once")
    if base_ids != set(canonical_ids):
        errors.append("base manifest must index every canonical service asset exactly once")

    compatibility_paths: set[Path] = set()
    for relative, service_name in CHARACTER_ALIASES.items():
        source = skill_dir / "references/archive/PNGs_renamed" / service_name
        alias = skill_dir / "references/characters" / relative
        if not source.exists() and not alias.exists():
            continue
        try:
            checked = _reference_path(skill_dir, alias.relative_to(skill_dir).as_posix())
            canonical = _reference_path(skill_dir, source.relative_to(skill_dir).as_posix())
            compatibility_paths.add(checked)
            if image_hash(checked) != image_hash(canonical):
                errors.append(f"{alias.relative_to(skill_dir)}: character compatibility source differs")
        except (OSError, ValueError) as exc:
            errors.append(f"{alias.relative_to(skill_dir)}: {exc}")

    all_pngs = list((skill_dir / "references").rglob("*.png"))
    for path in all_pngs:
        if path.resolve() not in referenced_paths | compatibility_paths:
            errors.append(f"{path.relative_to(skill_dir)}: PNG is not indexed or a declared character alias")

    return {
        "ok": not errors,
        "errors": errors,
        "counts": {
            "manifest_rows": manifest_counts,
            "canonical_assets": len(canonical_ids),
            "registered_assets": len(ids),
            "png_files": len(all_pngs),
            "character_compatibility_files": len(compatibility_paths),
            "unique_source_hashes": len(set(hashes.values())),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = validate_reference_bank(args.skill_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
