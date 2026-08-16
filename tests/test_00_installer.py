from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install_compact_skill.py"
SPEC = importlib.util.spec_from_file_location("install_compact_skill", SCRIPT)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_atomic_install_stages_complete_compact_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = installer.atomic_install(
                ROOT / "uc-icons",
                root / "active-skills",
                root / "inactive-backups",
            )
            installed = Path(result["installed"])
            self.assertEqual("0.2.0-rc.1", result["version"])
            expected_pngs = len(list((ROOT / "uc-icons").rglob("*.png")))
            self.assertEqual(expected_pngs, len(list(installed.rglob("*.png"))))
            self.assertEqual(72, len(list((installed / "references" / "archive" / "PNGs_renamed").glob("*.png"))))
            self.assertIsNone(result["backup"])
            self.assertFalse(
                any(path.name.startswith(".uc-icons.install-") for path in (root / "active-skills").iterdir())
            )

    def test_broad_or_same_roots_are_rejected(self):
        source = ROOT / "uc-icons"
        with self.assertRaises(ValueError):
            installer.ensure_safe_roots(source, Path("/"), ROOT / "backups")
        with self.assertRaises(ValueError):
            installer.ensure_safe_roots(source, ROOT / "same", ROOT / "same")
        with self.assertRaisesRegex(ValueError, "Source and install"):
            installer.ensure_safe_roots(source, source / "nested-install", ROOT / "backups")
        with self.assertRaisesRegex(ValueError, "Source and backup"):
            installer.ensure_safe_roots(source, ROOT / "active", source / "nested-backup")
        with self.assertRaisesRegex(ValueError, "outside the active"):
            installer.ensure_safe_roots(source, ROOT / "active", ROOT / "active" / "backups")

    def test_post_activation_failure_restores_previous_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_root = root / "active-skills"
            backup_root = root / "inactive-backups"
            previous = install_root / "uc-icons"
            previous.mkdir(parents=True)
            (previous / "SKILL.md").write_text("previous-install\n")

            original_validation = installer.run_validation
            calls = []

            def fail_after_activation(skill_dir: Path):
                calls.append(skill_dir)
                if len(calls) == 3:
                    raise RuntimeError("forced installed-tree smoke failure")
                original_validation(skill_dir)

            installer.run_validation = fail_after_activation
            try:
                with self.assertRaisesRegex(RuntimeError, "forced installed-tree smoke failure"):
                    installer.atomic_install(ROOT / "uc-icons", install_root, backup_root)
            finally:
                installer.run_validation = original_validation

            self.assertEqual("previous-install\n", (previous / "SKILL.md").read_text())
            failed = list(backup_root.glob("uc-icons-failed-*"))
            self.assertEqual(1, len(failed))
            self.assertTrue((failed[0] / "VERSION").is_file())


if __name__ == "__main__":
    unittest.main()
