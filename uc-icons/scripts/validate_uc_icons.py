#!/usr/bin/env python3
"""Validate compact storage, registry integrity, routing, and export behavior."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image

from asset_registry import (
    SafeResolver,
    load_base_records,
    load_character_records,
    load_material_records,
    load_runtime_reference_records,
    load_service_records,
    sha256_file,
)


DEFAULT_SKILL_DIR = Path(__file__).resolve().parents[1]
MAX_COMPACT_BASELINE_BYTES = 180_000_000


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_bytes(root: Path, excluded_root: Path | None = None) -> int:
    total = 0
    excluded = excluded_root.resolve() if excluded_root else None
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        resolved = path.resolve()
        if excluded and (resolved == excluded or excluded in resolved.parents):
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        total += path.stat().st_size
    return total


def validate(skill_dir: Path, compact_baseline: bool) -> dict[str, object]:
    skill_dir = skill_dir.expanduser().resolve()
    resolver = SafeResolver(skill_dir)
    errors: list[str] = []

    legacy_dir = skill_dir / "references" / "archive" / "PNGs_renamed"
    legacy_files = sorted(legacy_dir.glob("*.png"))
    expected_hashes_path = skill_dir / "references" / "archive" / "LEGACY_SHA256.json"
    expected_hashes = json.loads(expected_hashes_path.read_text(encoding="utf-8"))["files"]
    actual_names = {path.name for path in legacy_files}
    if len(legacy_files) != 72:
        errors.append(f"expected 72 physical legacy PNGs, found {len(legacy_files)}")
    if actual_names != set(expected_hashes):
        errors.append("legacy filename inventory differs from LEGACY_SHA256.json")
    for path in legacy_files:
        expected = expected_hashes.get(path.name)
        actual = sha256_file(path)
        if expected != actual:
            errors.append(f"legacy master changed: {path.name}")
    legacy_hashes = {sha256_file(path) for path in legacy_files}
    if len(legacy_hashes) != 72:
        errors.append(f"legacy archive has {len(legacy_hashes)} unique hashes, expected 72")

    try:
        services = load_service_records(resolver=resolver)
        bases = load_base_records(resolver=resolver)
        materials = load_material_records(resolver=resolver)
        characters = load_character_records(resolver=resolver)
        runtime = load_runtime_reference_records(resolver=resolver)
    except Exception as exc:
        errors.append(f"registry resolution failed: {exc}")
        services = bases = materials = characters = runtime = []

    expected_counts = {"services": (len(services), 73), "bases": (len(bases), 70), "materials": (len(materials), 72), "characters": (len(characters), 11)}
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            errors.append(f"expected {expected} {label}, found {actual}")
    if services and len({record["sha256"] for record in services}) != 72:
        errors.append("73 service identities must resolve to exactly 72 canonical hashes")
    for group_name, records in (("base", bases), ("material", materials), ("character", characters)):
        for record in records:
            if record["sha256"] not in legacy_hashes:
                errors.append(f"{group_name} alias does not preserve a legacy SHA: {record['asset_id']}")

    alias_pngs = []
    for folder in [
        skill_dir / "references" / "base-objects",
        skill_dir / "references" / "archive" / "PNGs_material_index",
        skill_dir / "references" / "characters",
    ]:
        alias_pngs.extend(folder.rglob("*.png"))
    if alias_pngs:
        errors.append("physical PNGs remain in logical alias directories: " + ", ".join(str(path) for path in alias_pngs))

    all_skill_pngs = sorted(skill_dir.rglob("*.png"))
    approved_bank_assets = sorted((skill_dir / "references" / "reference-bank" / "assets").glob("*.png"))
    if len(all_skill_pngs) != 72 + len(approved_bank_assets):
        errors.append(
            f"unexpected physical PNG paths: total={len(all_skill_pngs)}, legacy=72, approved_bank={len(approved_bank_assets)}"
        )

    for csv_path in skill_dir.rglob("*.csv"):
        if b"\r" in csv_path.read_bytes():
            errors.append(f"CSV is not normalized to LF: {csv_path.relative_to(skill_dir)}")

    benchmark_path = skill_dir / "references" / "evaluation" / "visual-v1.json"
    ontology_path = skill_dir / "references" / "routing" / "ontology.json"
    try:
        benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
        ontology = json.loads(ontology_path.read_text(encoding="utf-8"))
        if benchmark.get("schema_version") != 1 or len(benchmark.get("candidate_wave", [])) != 12:
            errors.append("installed visual-v1 benchmark is missing or malformed")
        if ontology.get("schema_version") != 1 or not ontology.get("families"):
            errors.append("installed routing ontology is missing or malformed")
    except Exception as exc:
        errors.append(f"installed evaluation metadata failed to load: {exc}")

    bank_validator = load_module("manage_reference_bank", skill_dir / "scripts" / "manage_reference_bank.py")
    bank_errors = bank_validator.validate_runtime_bank()
    errors.extend(f"reference bank: {error}" for error in bank_errors)

    reference_hashes: dict[str, str] = {}
    for record in runtime:
        digest = str(record["sha256"])
        resolved_path = str(record["path"])
        previous_path = reference_hashes.get(digest)
        if previous_path and previous_path != resolved_path:
            errors.append(f"runtime hash has duplicate physical files: {record['asset_id']}")
        reference_hashes[digest] = resolved_path

    bank_assets_root = skill_dir / "references" / "reference-bank" / "assets"
    baseline_bytes = tree_bytes(skill_dir, excluded_root=bank_assets_root)
    if compact_baseline and baseline_bytes >= MAX_COMPACT_BASELINE_BYTES:
        errors.append(
            f"compact baseline is {baseline_bytes} bytes; must be below {MAX_COMPACT_BASELINE_BYTES}"
        )

    planner = load_module("plan_icon_request", skill_dir / "scripts" / "plan_icon_request.py")
    smoke = {
        "exact": planner.plan_request("Native RO Water Purifiers (India)", skill_dir=skill_dir),
        "base": planner.plan_request("make the air cooler blue", skill_dir=skill_dir),
        "character": planner.plan_request("female chef with a white coat", skill_dir=skill_dir),
        "internal_reference": planner.plan_request("new design from scratch: air cooler", skill_dir=skill_dir),
    }
    expected_modes = {"exact": "exact_export", "base": "base_edit", "character": "character_edit", "internal_reference": "new_generation"}
    for name, expected in expected_modes.items():
        if smoke[name]["mode"] != expected:
            errors.append(f"{name} smoke mode={smoke[name]['mode']}, expected={expected}")
    internal_refs = smoke["internal_reference"].get("references", [])
    if not internal_refs or internal_refs[0].get("source") != "approved_legacy_base":
        errors.append("approved internal reference smoke did not select the canonical air-cooler form")

    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        supplied = temp / "supplied.png"
        Image.new("RGB", (1024, 768), (245, 245, 245)).save(supplied)
        supplied_plan = planner.plan_request(
            "office chair",
            provided_references=[f"style={supplied.resolve()}"],
            skill_dir=skill_dir,
        )
        if supplied_plan["mode"] != "new_generation" or not supplied_plan["references"]:
            errors.append("request-scoped reference smoke failed")
        elif supplied_plan["references"][0].get("source") != "request_scoped":
            errors.append("request-scoped reference did not take precedence")

        exporter = load_module("export_skeuo_uc_icon", skill_dir / "scripts" / "export_skeuo_uc_icon.py")
        previous = Path.cwd()
        os.chdir(temp)
        try:
            exact_source = Path(str(smoke["exact"]["base"]["path"]))
            output = exporter.export_icon(exact_source, "validation exact", preserve_source=True)
        finally:
            os.chdir(previous)
        if output.get("master_path") is not None:
            errors.append("exact export unexpectedly created a master copy")
        with Image.open(output["delivery_path"]) as delivery:
            if delivery.size != (1024, 768) or delivery.format != "PNG":
                errors.append("exact export delivery is not a 1024x768 PNG")

    if errors:
        raise ValueError("\n".join(errors))

    return {
        "status": "ok",
        "skill_dir": str(skill_dir),
        "version": (skill_dir / "VERSION").read_text(encoding="utf-8").strip(),
        "legacy_png_paths": len(legacy_files),
        "legacy_unique_hashes": len(legacy_hashes),
        "service_identities": len(services),
        "base_aliases": len(bases),
        "material_aliases": len(materials),
        "character_aliases": len(characters),
        "approved_runtime_references": len(runtime),
        "compact_baseline_bytes": baseline_bytes,
        "installed_physical_pngs": len(all_skill_pngs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a UC Icons skill package.")
    parser.add_argument("--skill-dir", default=str(DEFAULT_SKILL_DIR))
    parser.add_argument("--compact-baseline", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(Path(args.skill_dir), args.compact_baseline)
    except Exception as exc:
        print(f"ERROR:\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
