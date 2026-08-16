from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "uc-icons"
sys.path.insert(0, str(SKILL / "scripts"))

from asset_registry import (  # noqa: E402
    SafeResolver,
    deduplicate_records,
    load_base_records,
    load_character_records,
    load_material_records,
    load_service_records,
    registry_summary,
    sha256_file,
    _service_relative_path,
)


class RegistryTests(unittest.TestCase):
    def test_legacy_logical_counts_resolve_and_runtime_growth_is_additive(self):
        summary = registry_summary(SKILL)
        self.assertEqual(73, summary["counts"]["service"])
        self.assertEqual(70, summary["counts"]["base"])
        self.assertEqual(72, summary["counts"]["material"])
        self.assertEqual(11, summary["counts"]["character"])
        runtime_assets = {
            path.resolve()
            for path in (SKILL / "references" / "reference-bank" / "assets").glob("*.png")
        }
        self.assertEqual(72 + len(runtime_assets), summary["unique_paths"])
        self.assertGreaterEqual(summary["unique_hashes"], 72)
        self.assertLessEqual(summary["unique_hashes"], 72 + len(runtime_assets))

    def test_locked_legacy_masters_are_byte_identical(self):
        archive = SKILL / "references" / "archive" / "PNGs_renamed"
        locked = json.loads((SKILL / "references" / "archive" / "LEGACY_SHA256.json").read_text())["files"]
        self.assertEqual(72, len(locked))
        for filename, expected in locked.items():
            with self.subTest(filename=filename):
                self.assertEqual(expected, sha256_file(archive / filename))

    def test_alias_directories_have_no_physical_pngs(self):
        folders = [
            SKILL / "references" / "base-objects",
            SKILL / "references" / "archive" / "PNGs_material_index",
            SKILL / "references" / "characters",
        ]
        self.assertEqual([], [path for folder in folders for path in folder.rglob("*.png")])

    def test_every_alias_preserves_a_legacy_sha(self):
        legacy_hashes = {
            sha256_file(path)
            for path in (SKILL / "references" / "archive" / "PNGs_renamed").glob("*.png")
        }
        for records in [
            load_base_records(skill_dir=SKILL),
            load_material_records(skill_dir=SKILL),
            load_character_records(skill_dir=SKILL),
        ]:
            for record in records:
                self.assertIn(record["sha256"], legacy_hashes)

    def test_pest_control_dubai_is_a_logical_cockroach_alias(self):
        services = load_service_records(skill_dir=SKILL)
        pest = next(record for record in services if str(record["service_file"]).startswith("_duplicates/"))
        cockroach = next(record for record in services if record["service_file"] == "Cockroach control.png")
        self.assertEqual(cockroach["path"], pest["path"])
        self.assertEqual(cockroach["sha256"], pest["sha256"])

    def test_deduplication_uses_path_and_sha(self):
        services = load_service_records(skill_dir=SKILL)
        unique = deduplicate_records(services)
        self.assertEqual(72, len(unique))
        self.assertEqual(72, len({record["sha256"] for record in unique}))

    def test_safe_resolver_fails_loudly_on_missing_alias(self):
        resolver = SafeResolver(SKILL)
        with self.assertRaises(FileNotFoundError):
            resolver.resolve("references/archive/PNGs_renamed/does-not-exist.png", "missing", "base_edit")

    def test_safe_resolver_rejects_symlinked_file(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "uc-icons"
            assets = skill / "assets"
            assets.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: uc-icons\n---\n", encoding="utf-8")
            (assets / "canonical.bin").write_bytes(b"canonical")
            (assets / "alias.bin").symlink_to("canonical.bin")

            with self.assertRaisesRegex(ValueError, "contains a symlink"):
                SafeResolver(skill).resolve("assets/alias.bin", "alias", "base_edit")

    def test_safe_resolver_rejects_symlinked_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "uc-icons"
            canonical = skill / "canonical"
            canonical.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: uc-icons\n---\n", encoding="utf-8")
            (canonical / "asset.bin").write_bytes(b"canonical")
            (skill / "alias").symlink_to("canonical", target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "contains a symlink"):
                SafeResolver(skill).resolve("alias/asset.bin", "alias", "base_edit")

    def test_only_the_declared_pest_duplicate_alias_is_special_cased(self):
        with self.assertRaisesRegex(ValueError, "Unknown service duplicate alias"):
            _service_relative_path({"service_file": "_duplicates/invented.png"})

    def test_compact_skill_baseline_is_under_180_decimal_mb(self):
        bank_assets = SKILL / "references" / "reference-bank" / "assets"
        total = 0
        for path in SKILL.rglob("*"):
            if not path.is_file() or path.is_symlink() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if bank_assets in path.parents:
                continue
            total += path.stat().st_size
        self.assertLess(total, 180_000_000)


if __name__ == "__main__":
    unittest.main()
