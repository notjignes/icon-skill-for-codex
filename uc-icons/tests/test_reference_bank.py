from __future__ import annotations

import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_reference_bank", SKILL_DIR / "scripts/validate_reference_bank.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ReferenceBankTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "references/archive/PNGs_renamed/Example.png"
        self.image.parent.mkdir(parents=True)
        Image.new("RGBA", (4, 3), (60, 90, 120, 255)).save(self.image)
        digest = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.record = {
            "asset_id": f"uc-icon-{digest[:16]}",
            "sha256": digest,
            "image_path": self.image.relative_to(self.root).as_posix(),
            "approval_status": "existing_curated",
            "provenance_source": "test_fixture",
            "material_tags": "plastic", "finish_tags": "matte",
        }
        for relative, (legacy_fields, alias_key, roles) in VALIDATOR.MANIFESTS.items():
            fields = sorted(legacy_fields | VALIDATOR.COMMON_FIELDS)
            row = {field: "unknown" for field in fields}
            row.update(self.record)
            row["source_role"] = sorted(roles)[0]
            row[alias_key] = "Example.png"
            self._write(relative, fields, [] if alias_key == "reference_file" else [row])

    def _write(self, relative: str, fields: list[str], rows: list[dict]) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _edit(self, relative: str, change) -> None:
        path = self.root / relative
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        change(rows)
        self._write(relative, fields, rows)

    def test_bundled_bank_retains_every_source_and_character_path(self) -> None:
        result = VALIDATOR.validate_reference_bank(SKILL_DIR)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["counts"]["canonical_assets"], 72)
        self.assertGreaterEqual(result["counts"]["unique_source_hashes"], 72)
        self.assertEqual(result["counts"]["character_compatibility_files"], 11)
        self.assertGreaterEqual(result["counts"]["png_files"], 83)

    def test_aliases_resolve_without_copied_material_or_base_images(self) -> None:
        result = VALIDATOR.validate_reference_bank(self.root)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["counts"]["png_files"], 1)

    def test_modified_canonical_source_fails_hash_validation(self) -> None:
        Image.new("RGBA", (4, 3), (200, 20, 40, 255)).save(self.image)
        result = VALIDATOR.validate_reference_bank(self.root)
        self.assertFalse(result["ok"])
        self.assertTrue(any("sha256 mismatch" in error for error in result["errors"]))

    def test_path_traversal_and_external_symlinks_are_rejected(self) -> None:
        relative = "references/base-objects/MANIFEST.csv"
        self._edit(relative, lambda rows: rows[0].update(image_path="../outside.png"))
        result = VALIDATOR.validate_reference_bank(self.root)
        self.assertTrue(any("safe skill-relative" in error for error in result["errors"]))
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "external.png"
            Image.new("RGBA", (4, 3)).save(external)
            link = self.root / "references/base-objects/link.png"
            link.symlink_to(external)
            self._edit(relative, lambda rows: rows[0].update(image_path="references/base-objects/link.png"))
            result = VALIDATOR.validate_reference_bank(self.root)
            self.assertTrue(any("within the skill references" in error for error in result["errors"]))

    def test_duplicate_aliases_and_asset_ids_are_rejected(self) -> None:
        relative = "references/base-objects/MANIFEST.csv"
        self._edit(relative, lambda rows: rows.append(dict(rows[0])))
        result = VALIDATOR.validate_reference_bank(self.root)
        self.assertTrue(any("duplicate alias" in error for error in result["errors"]))
        self.assertTrue(any("duplicate asset_id" in error for error in result["errors"]))

    def test_inconsistent_id_missing_source_and_unknown_state_fail(self) -> None:
        relative = "references/base-objects/MANIFEST.csv"
        self._edit(relative, lambda rows: rows[0].update(
            asset_id="uc-icon-wrong", image_path="references/base-objects/missing.png",
            approval_status="automatically_approved",
        ))
        result = VALIDATOR.validate_reference_bank(self.root)
        self.assertTrue(any("asset_id does not match" in error for error in result["errors"]))
        self.assertTrue(any("missing image" in error for error in result["errors"]))
        self.assertTrue(any("unsupported approval_status" in error for error in result["errors"]))

    def test_unindexed_png_fails_instead_of_silently_entering_reference_bank(self) -> None:
        Image.new("RGBA", (4, 3)).save(self.image.parent / "Unapproved.png")
        result = VALIDATOR.validate_reference_bank(self.root)
        self.assertTrue(any("not indexed" in error for error in result["errors"]))

    def test_empty_new_reference_bank_has_required_intake_fields(self) -> None:
        path = self.root / "references/new-object-references/MANIFEST.csv"
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(list(reader), [])
            self.assertTrue({"source_role", "approval_status", "provenance_source",
                             "object_family", "identity_aliases", "composition_family",
                             "approved_for"}.issubset(reader.fieldnames))


if __name__ == "__main__":
    unittest.main()
