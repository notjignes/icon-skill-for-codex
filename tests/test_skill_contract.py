from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "uc-icons"


class SkillContractTests(unittest.TestCase):
    def test_generation_status_is_one_playful_line_with_nonbinding_example(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        line = "Go touch some grass 🌱 — we’re generating your icon."
        self.assertEqual(1, text.count(line))
        self.assertIn("exactly one short, playful waiting line", text)
        self.assertIn("tone guidance, not fixed copy", text)
        self.assertIn("Exact exports show no status line", text)

    def test_no_recursive_newest_image_discovery(self):
        script_text = (SKILL / "scripts" / "export_skeuo_uc_icon.py").read_text(encoding="utf-8")
        forbidden = ["glob(\"**/*.png\")", "rglob(\"*.png\")", "getmtime"]
        for phrase in forbidden:
            self.assertNotIn(phrase, script_text)

    def test_contact_shadow_phrase_is_not_an_instruction_for_new_work(self):
        for path in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("clear soft contact shadow", text, path)

    def test_user_references_and_outputs_are_not_auto_promoted(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("never add them or their outputs to the reusable bank automatically", text)
        self.assertIn("never promote an ordinary successful output automatically", text)

    def test_exporter_command_requires_source(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        commands = re.findall(r"export_skeuo_uc_icon\.py[^`]+", text)
        self.assertTrue(commands)
        self.assertTrue(all("--source" in command for command in commands))

    def test_batch_family_locks_reject_drift_before_export(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        contract_text = (SKILL / "references" / "icon-contract.md").read_text(
            encoding="utf-8"
        ).lower()
        rubric_text = (
            ROOT / "evaluation" / "reference-bank" / "REVIEW-RUBRIC.md"
        ).read_text(encoding="utf-8").lower()

        for phrase in (
            "pose/view",
            "camera angle",
            "light direction",
            "texture-density band",
            "palette roles",
        ):
            self.assertIn(phrase, skill_text)
            self.assertIn(phrase, contract_text)
            self.assertIn(phrase, rubric_text)
        self.assertIn("discard it from evaluation", skill_text)
        self.assertIn("reject and regenerate", contract_text)
        self.assertIn("discard and regenerate", rubric_text)


if __name__ == "__main__":
    unittest.main()
