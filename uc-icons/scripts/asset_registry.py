#!/usr/bin/env python3
"""Canonical, contained-path asset resolver for the UC Icons logical registries."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


DEFAULT_SKILL_DIR = Path(__file__).resolve().parents[1]
PEST_ALIAS_PATH = "references/archive/PNGs_renamed/Cockroach control.png"
PEST_ALIAS_SERVICE_FILE = "_duplicates/Pest control (Dubai) [identical to Cockroach control].png"


def slugify(value: str) -> str:
    value = re.sub(r"\[[^]]+\]", " ", value)
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "asset"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_values(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


@dataclass(frozen=True)
class ResolvedAsset:
    logical_asset_id: str
    execution_role: str
    relative_path: str
    path: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class SafeResolver:
    """Resolve only existing regular files contained by one skill directory."""

    def __init__(self, skill_dir: Path | str | None = None):
        self.skill_dir = Path(skill_dir or DEFAULT_SKILL_DIR).expanduser().resolve()
        if not (self.skill_dir / "SKILL.md").is_file():
            raise ValueError(f"Not a UC Icons skill directory: {self.skill_dir}")
        self._hash_cache: dict[Path, str] = {}

    def resolve(
        self,
        relative_path: str,
        logical_asset_id: str,
        execution_role: str,
        expected_sha256: str | None = None,
    ) -> ResolvedAsset:
        if not relative_path or "\\" in relative_path:
            raise ValueError(f"Asset path must be a non-empty POSIX relative path: {relative_path!r}")
        posix = PurePosixPath(relative_path)
        if posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
            raise ValueError(f"Unsafe asset path: {relative_path!r}")
        lexical_candidate = self.skill_dir / Path(*posix.parts)
        component = self.skill_dir
        for part in posix.parts:
            component /= part
            if component.is_symlink():
                raise ValueError(f"Asset path contains a symlink: {relative_path!r}")
        candidate = lexical_candidate.resolve()
        if candidate == self.skill_dir or self.skill_dir not in candidate.parents:
            raise ValueError(f"Asset path escapes the skill: {relative_path!r}")
        if not candidate.is_file():
            raise FileNotFoundError(f"Missing canonical asset for {logical_asset_id}: {relative_path}")
        digest = self._hash_cache.get(candidate)
        if digest is None:
            digest = sha256_file(candidate)
            self._hash_cache[candidate] = digest
        if expected_sha256 and digest != expected_sha256:
            raise ValueError(
                f"SHA-256 mismatch for {logical_asset_id}: expected {expected_sha256}, got {digest}"
            )
        return ResolvedAsset(
            logical_asset_id=logical_asset_id,
            execution_role=execution_role,
            relative_path=posix.as_posix(),
            path=str(candidate),
            sha256=digest,
        )


def _service_relative_path(row: dict[str, str]) -> str:
    explicit = row.get("image_path", "").strip()
    if explicit:
        return explicit
    service_file = row.get("service_file", "").strip()
    if service_file == PEST_ALIAS_SERVICE_FILE:
        return PEST_ALIAS_PATH
    if service_file.startswith("_duplicates/"):
        raise ValueError(f"Unknown service duplicate alias: {service_file}")
    return f"references/archive/PNGs_renamed/{service_file}"


def load_service_records(
    skill_dir: Path | str | None = None,
    resolver: SafeResolver | None = None,
) -> list[dict[str, object]]:
    resolver = resolver or SafeResolver(skill_dir)
    manifest = resolver.skill_dir / "references" / "archive" / "PNGs_renamed" / "MANIFEST.csv"
    records: list[dict[str, object]] = []
    used_ids: dict[str, int] = {}
    for row in read_csv(manifest):
        service_file = row.get("service_file", "").strip()
        if not service_file:
            raise ValueError(f"Service manifest row has no service_file: {row}")
        display_stem = Path(service_file).stem
        display_stem = re.sub(r"\s*\[identical to[^]]+\]", "", display_stem, flags=re.I)
        base_id = f"service-{slugify(display_stem)}"
        used_ids[base_id] = used_ids.get(base_id, 0) + 1
        asset_id = base_id if used_ids[base_id] == 1 else f"{base_id}-{used_ids[base_id]}"
        resolved = resolver.resolve(_service_relative_path(row), asset_id, "exact_export")
        record: dict[str, object] = dict(row)
        record.update(resolved.to_dict())
        record.update({
            "asset_id": asset_id,
            "service_identity": display_stem,
            "aliases": [display_stem, Path(row.get("original_filename", "")).stem],
            "status": "approved",
            "execution_permissions": ["exact_export"],
        })
        records.append(record)
    return records


def load_base_records(
    skill_dir: Path | str | None = None,
    resolver: SafeResolver | None = None,
) -> list[dict[str, object]]:
    resolver = resolver or SafeResolver(skill_dir)
    manifest = resolver.skill_dir / "references" / "base-objects" / "MANIFEST.csv"
    records: list[dict[str, object]] = []
    for row in read_csv(manifest):
        base_file = (row.get("base_file") or row.get("base_object_file") or "").strip()
        if not base_file:
            raise ValueError(f"Base manifest row has no base file: {row}")
        asset_id = f"base-{slugify(Path(base_file).stem)}"
        relative = row.get("image_path", "").strip() or f"references/base-objects/{base_file}"
        resolved = resolver.resolve(relative, asset_id, "base_edit")
        record: dict[str, object] = dict(row)
        record.update(resolved.to_dict())
        record.update({
            "asset_id": asset_id,
            "base_file": base_file,
            "aliases": split_values(row.get("canonical_for", "")),
            "status": "approved",
            "execution_permissions": ["base_edit"],
        })
        records.append(record)
    return records


def load_material_records(
    skill_dir: Path | str | None = None,
    resolver: SafeResolver | None = None,
) -> list[dict[str, object]]:
    resolver = resolver or SafeResolver(skill_dir)
    manifest = resolver.skill_dir / "references" / "archive" / "PNGs_material_index" / "MANIFEST.csv"
    records: list[dict[str, object]] = []
    for row in read_csv(manifest):
        material_file = row.get("material_index_file", "").strip()
        if not material_file:
            continue
        asset_id = f"material-{slugify(Path(material_file).stem)}"
        relative = row.get("image_path", "").strip()
        if not relative:
            service_file = row.get("service_file", "").strip()
            if service_file == PEST_ALIAS_SERVICE_FILE:
                relative = PEST_ALIAS_PATH
            elif service_file.startswith("_duplicates/"):
                raise ValueError(f"Unknown material duplicate alias: {service_file}")
            else:
                relative = f"references/archive/PNGs_renamed/{service_file}"
        resolved = resolver.resolve(relative, asset_id, "generation_reference")
        record: dict[str, object] = dict(row)
        record.update(resolved.to_dict())
        record.update({
            "asset_id": asset_id,
            "reference_roles": ["material"],
            "status": "approved",
            "execution_permissions": ["generation_reference"],
        })
        records.append(record)
    return records


def load_character_records(
    skill_dir: Path | str | None = None,
    resolver: SafeResolver | None = None,
) -> list[dict[str, object]]:
    resolver = resolver or SafeResolver(skill_dir)
    manifest = resolver.skill_dir / "references" / "characters" / "MANIFEST.csv"
    records: list[dict[str, object]] = []
    for row in read_csv(manifest):
        asset_id = row.get("character_id", "").strip()
        if not asset_id:
            raise ValueError(f"Character manifest row has no character_id: {row}")
        resolved = resolver.resolve(
            row.get("image_path", "").strip(),
            asset_id,
            "base_edit",
            expected_sha256=row.get("sha256", "").strip() or None,
        )
        record: dict[str, object] = dict(row)
        record.update(resolved.to_dict())
        record.update({
            "asset_id": asset_id,
            "aliases": split_values(row.get("aliases", "")),
            "status": "approved",
            "execution_permissions": ["base_edit"],
        })
        records.append(record)
    return records


def load_runtime_reference_records(
    skill_dir: Path | str | None = None,
    resolver: SafeResolver | None = None,
) -> list[dict[str, object]]:
    resolver = resolver or SafeResolver(skill_dir)
    manifest = resolver.skill_dir / "references" / "reference-bank" / "MANIFEST.csv"
    records: list[dict[str, object]] = []
    for row in read_csv(manifest):
        execution = split_values(row.get("execution_roles", ""))
        if row.get("status") != "approved" or "generation_reference" not in execution:
            continue
        reference_id = row.get("reference_id", "").strip()
        if not reference_id:
            raise ValueError(f"Runtime reference row has no reference_id: {row}")
        resolved = resolver.resolve(
            row.get("image_path", "").strip(),
            reference_id,
            "generation_reference",
            expected_sha256=row.get("sha256", "").strip() or None,
        )
        record: dict[str, object] = dict(row)
        record.update(resolved.to_dict())
        record.update({
            "asset_id": reference_id,
            "aliases": split_values(row.get("aliases", "")),
            "reference_roles": split_values(row.get("roles", "")),
            "execution_permissions": execution,
        })
        records.append(record)
    return records


def deduplicate_records(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Keep the first logical use of each canonical path/SHA attachment pair."""

    result: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    seen_hashes: set[str] = set()
    for record in records:
        path = str(record.get("path", ""))
        digest = str(record.get("sha256", ""))
        if path in seen_paths or digest in seen_hashes:
            continue
        seen_paths.add(path)
        seen_hashes.add(digest)
        result.append(record)
    return result


def registry_summary(skill_dir: Path | str | None = None) -> dict[str, object]:
    resolver = SafeResolver(skill_dir)
    groups = {
        "service": load_service_records(resolver=resolver),
        "base": load_base_records(resolver=resolver),
        "material": load_material_records(resolver=resolver),
        "character": load_character_records(resolver=resolver),
        "runtime_reference": load_runtime_reference_records(resolver=resolver),
    }
    all_records = [record for records in groups.values() for record in records]
    return {
        "counts": {name: len(records) for name, records in groups.items()},
        "unique_paths": len({str(record["path"]) for record in all_records}),
        "unique_hashes": len({str(record["sha256"]) for record in all_records}),
    }


def main() -> int:
    print(json.dumps(registry_summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
