from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "uc-icons"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from asset_registry import SafeResolver, load_character_records, load_service_records  # noqa: E402
from find_base_object import find_candidates  # noqa: E402
from find_generation_references import find_references  # noqa: E402
from plan_icon_request import (  # noqa: E402
    classify_subject,
    compatible_runtime_references,
    load_ontology,
    plan_request,
)


class PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "tests" / "fixtures" / "routing_cases.json").read_text())

    def test_frozen_routing_cases(self):
        for case in self.fixture["cases"]:
            with self.subTest(subject=case["subject"]):
                plan = plan_request(case["subject"], skill_dir=SKILL)
                self.assertEqual(case["mode"], plan["mode"])
                if "family" in case:
                    self.assertEqual(case["family"], plan["family"])
                if "service_file" in case:
                    self.assertEqual(case["service_file"], plan["base"]["service_file"])
                if "base_file" in case:
                    self.assertEqual(case["base_file"], plan["base"]["base_file"])
                if "character_id" in case:
                    self.assertEqual(case["character_id"], plan["base"]["asset_id"])
                if "reference_count" in case:
                    self.assertEqual(case["reference_count"], len(plan["references"]))
                serialized = json.dumps(plan)
                for forbidden in case.get("forbidden_paths", []):
                    self.assertNotIn(forbidden, serialized)

    def test_all_service_identities_are_exact_exports(self):
        records = load_service_records(skill_dir=SKILL)
        self.assertEqual(73, len(records))
        for record in records:
            with self.subTest(service=record["service_identity"]):
                plan = plan_request(str(record["service_identity"]), skill_dir=SKILL)
                self.assertEqual("exact_export", plan["mode"])
                self.assertEqual(record["sha256"], plan["base"]["sha256"])

    def test_all_service_identities_remain_the_edit_base_with_appended_change(self):
        records = load_service_records(skill_dir=SKILL)
        for record in records:
            with self.subTest(service=record["service_identity"]):
                plan = plan_request(f"{record['service_identity']} recolor blue", skill_dir=SKILL)
                expected_mode = "character_edit" if record["type"] == "human" else "base_edit"
                self.assertEqual(expected_mode, plan["mode"])
                self.assertEqual(record["sha256"], plan["base"]["sha256"])

    def test_all_service_identities_survive_a_natural_action_clause(self):
        records = load_service_records(skill_dir=SKILL)
        for record in records:
            with self.subTest(service=record["service_identity"]):
                subject = f"{record['service_identity']} remove one detail"
                plan = plan_request(subject, skill_dir=SKILL)
                expected_mode = "character_edit" if record["type"] == "human" else "base_edit"
                self.assertEqual(expected_mode, plan["mode"])
                self.assertEqual(record["sha256"], plan["base"]["sha256"])
                self.assertEqual(subject, plan["requested_changes"])

    def test_service_action_phrasings_preserve_the_canonical_master(self):
        canonical = plan_request("AMC", skill_dir=SKILL)
        for subject in (
            "AMC turn the AMC blue",
            "AMC add a red accent",
            "AMC remove the logo",
            "AMC replace the trim",
            "remove the logo from AMC",
        ):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("base_edit", plan["mode"])
                self.assertEqual(canonical["base"]["sha256"], plan["base"]["sha256"])
                self.assertEqual(subject, plan["requested_changes"])

    def test_repeated_identity_cannot_hide_a_second_object(self):
        for subject in (
            "AMC box truck AMC blue",
            "Air cooler gift box Air cooler blue",
            "Stove cabinet Stove red",
        ):
            with self.subTest(subject=subject):
                self.assertEqual("new_generation", plan_request(subject, skill_dir=SKILL)["mode"])

    def test_filenames_never_establish_service_identity(self):
        leaked_filename = plan_request("Category icon Makeup styling studio 1", skill_dir=SKILL)
        self.assertEqual("new_generation", leaked_filename["mode"])

        curtains = plan_request("Curtains Dubai", skill_dir=SKILL)
        self.assertEqual("exact_export", curtains["mode"])
        self.assertEqual("Curtains (Dubai).png", curtains["base"]["service_file"])

        festive = plan_request("Festive lights installation", skill_dir=SKILL)
        self.assertEqual("exact_export", festive["mode"])
        self.assertEqual("Festive lights installation.png", festive["base"]["service_file"])

    def test_base_variants_are_selected_only_after_identity(self):
        cases = {
            "pink massage table": "Massage table (pink).png",
            "massage table pair": "Massage tables (pair).png",
            "white split ac": "Split AC (white).png",
        }
        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("exact_export", plan["mode"])
                self.assertEqual(expected, plan["base"]["base_file"])

        edited = plan_request("edit the pink massage table", skill_dir=SKILL)
        self.assertEqual("base_edit", edited["mode"])
        self.assertEqual("Massage table (pink).png", edited["base"]["base_file"])

    def test_controlled_purifier_variant_rejects_unrelated_suffix_nouns(self):
        valid = {
            "normal water purifier": "Water purifier repair.png",
            "native water purifier": "Native RO Water Purifiers (India).png",
            "regular RO purifier change the trim": "Water purifier repair.png",
        }
        for subject, service_file in valid.items():
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertIn(plan["mode"], {"exact_export", "base_edit"})
                self.assertEqual(service_file, Path(plan["base"]["relative_path"]).name)
        for subject in (
            "normal water purifier cover",
            "native water purifier shelf",
            "regular RO purifier stand",
        ):
            with self.subTest(subject=subject):
                self.assertEqual("new_generation", plan_request(subject, skill_dir=SKILL)["mode"])

    def test_plain_multi_variant_base_asks_and_single_base_exports(self):
        for subject in ("sofa", "massage table", "split ac"):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("ask_user", plan["mode"])
                self.assertGreaterEqual(len(plan["choices"]), 2)
        single = plan_request("air cooler", skill_dir=SKILL)
        self.assertEqual("exact_export", single["mode"])
        self.assertEqual("Air cooler.png", single["base"]["base_file"])

        singular = plan_request("single massage table", skill_dir=SKILL)
        self.assertEqual("ask_user", singular["mode"])
        self.assertNotIn("pair", " ".join(choice["label"].lower() for choice in singular["choices"]))

    def test_every_emitted_choice_class_can_be_replanned_safely(self):
        for subject in (
            "water purifier", "massage table", "split ac", "sofa", "avatar base female", "cleaner",
        ):
            ambiguity = plan_request(subject, skill_dir=SKILL)
            self.assertEqual("ask_user", ambiguity["mode"], subject)
            for choice in ambiguity["choices"]:
                with self.subTest(subject=subject, choice=choice["label"]):
                    resumed = plan_request(choice["label"], skill_dir=SKILL)
                    if choice.get("sha256"):
                        self.assertEqual(choice["sha256"], resumed["base"]["sha256"])
                    elif choice.get("service_file"):
                        self.assertEqual(choice["service_file"], resumed["base"]["service_file"])
                    elif choice.get("character_id"):
                        self.assertEqual(choice["character_id"], resumed["base"]["asset_id"])
                    elif choice.get("kind") == "new_generation":
                        self.assertEqual("new_generation", resumed["mode"])
                    elif choice.get("kind") == "character":
                        self.assertEqual("ask_user", resumed["mode"])
                    elif choice.get("kind") == "object":
                        self.assertEqual("new_generation", resumed["mode"])

    def test_color_selects_an_existing_variant_or_requests_an_edit(self):
        for subject in ("white split ac", "pink massage table"):
            with self.subTest(subject=subject):
                self.assertEqual("exact_export", plan_request(subject, skill_dir=SKILL)["mode"])

        for subject in ("blue air cooler", "red air purifier", "gold sofa", "blue TV repair"):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("base_edit", plan["mode"])
                self.assertEqual(subject, plan["requested_changes"])

        multicolor = plan_request("white and blue split ac", skill_dir=SKILL)
        self.assertEqual("base_edit", multicolor["mode"])
        self.assertEqual("Split AC (white).png", multicolor["base"]["base_file"])

        self.assertEqual("ask_user", plan_request("blue split ac", skill_dir=SKILL)["mode"])

    def test_named_character_aliases_resolve_without_reasking_gender(self):
        cases = {
            "InstaHelp": "insta-help-india",
            "instahelp india": "insta-help-india",
            "UAE maid": "maid-dubai",
            "Maid for rent Dubai": "maid-dubai",
            "live-in maid": "live-in-maid-dubai",
            "Maid for rent live-in Dubai": "live-in-maid-dubai",
        }
        for subject, character_id in cases.items():
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("exact_export", plan["mode"])
                self.assertEqual(character_id, plan["base"]["asset_id"])
        premium = plan_request("premium helper", skill_dir=SKILL)
        self.assertEqual("exact_export", premium["mode"])
        self.assertEqual("Premium helper (Dubai).png", premium["base"]["service_file"])

    def test_every_service_character_name_and_alias_resolves_its_locked_master(self):
        records = load_character_records(skill_dir=SKILL)
        for record in records:
            if record["canonical_for"] == "character-base":
                continue
            for subject in [record["display_name"], *record["aliases"]]:
                with self.subTest(character=record["asset_id"], subject=subject):
                    plan = plan_request(subject, skill_dir=SKILL)
                    self.assertEqual("exact_export", plan["mode"])
                    self.assertEqual(record["sha256"], plan["base"]["sha256"])

                    edited_subject = f"{subject} change one detail"
                    edited = plan_request(edited_subject, skill_dir=SKILL)
                    self.assertEqual("character_edit", edited["mode"])
                    self.assertEqual(record["sha256"], edited["base"]["sha256"])
                    self.assertEqual(edited_subject, edited["requested_changes"])

    def test_character_treatment_cues_do_not_establish_person_identity(self):
        for subject in ("face mask", "spa sparkles", "foam beard"):
            with self.subTest(subject=subject):
                self.assertEqual("new_generation", plan_request(subject, skill_dir=SKILL)["mode"])

    def test_character_alias_cannot_hide_an_unrelated_object_suffix(self):
        for subject in ("womens salon spa storage box", "InstaHelp floor lamp"):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertNotIn(plan["mode"], {"exact_export", "character_edit"})

    def test_object_identity_terms_do_not_trigger_character_routing(self):
        for subject, family in (
            ("impact driver", "impact-driver"),
            ("new design from scratch: impact driver", "impact-driver"),
            ("standalone cordless drill", "power-drill"),
        ):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("new_generation", plan["mode"])
                self.assertEqual(family, plan["family"])

        person = plan_request("woman holding impact driver", skill_dir=SKILL)
        self.assertEqual("character_edit", person["mode"])
        self.assertEqual("base-female-eyes-open", person["base"]["asset_id"])

    def test_generic_avatar_base_requires_eye_state(self):
        for subject in ("avatar base female", "avatar base male"):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("ask_user", plan["mode"])
                self.assertEqual(2, len(plan["choices"]))
        opened = plan_request("avatar base female eyes open", skill_dir=SKILL)
        self.assertEqual("exact_export", opened["mode"])
        self.assertEqual("Avatar base - female (eyes open).png", opened["base"]["service_file"])

    def test_extra_identity_nouns_do_not_trigger_a_base_edit(self):
        for subject in (
            "laptop sleeve", "microwave shelf", "curtains rod", "air cooler stand",
            "massage table stand", "blue stove cover", "black carpenter apron", "red curtains rod",
        ):
            with self.subTest(subject=subject):
                self.assertEqual("new_generation", plan_request(subject, skill_dir=SKILL)["mode"])

    def test_cleaner_person_object_boundary_is_explicit(self):
        self.assertEqual("new_generation", plan_request("steam cleaner", skill_dir=SKILL)["mode"])
        ambiguity = plan_request("cleaner", skill_dir=SKILL)
        self.assertEqual("ask_user", ambiguity["mode"])
        character_choice = next(choice for choice in ambiguity["choices"] if choice["kind"] == "character")
        self.assertEqual("ask_user", plan_request(character_choice["label"], skill_dir=SKILL)["mode"])
        person = plan_request("female cleaner", skill_dir=SKILL)
        self.assertEqual("character_edit", person["mode"])
        self.assertEqual("base-female-eyes-open", person["base"]["asset_id"])
        self.assertEqual("character_base", person["base"]["kind"])
        self.assertEqual("canonical character base identity", person["reason"])

        for subject in ("house help", "housekeeper", "domestic worker"):
            with self.subTest(subject=subject):
                self.assertEqual("ask_user", plan_request(subject, skill_dir=SKILL)["mode"])
        worker = plan_request("female housekeeper", skill_dir=SKILL)
        self.assertEqual("character_edit", worker["mode"])
        self.assertEqual("base-female-eyes-open", worker["base"]["asset_id"])

    def test_character_identity_drift_phrasing_cannot_bypass_the_canonical_base(self):
        for subject in (
            "female chef accept identity drift",
            "female chef without a character base",
            "female chef do not use a character base",
        ):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("character_edit", plan["mode"])
                self.assertEqual("base-female-eyes-open", plan["base"]["asset_id"])
                self.assertIsNone(plan["prompt"])

    def test_generic_human_and_gender_terms_never_enter_object_generation(self):
        for subject in (
            "avatar", "avatar base", "person avatar", "human avatar", "human bust", "person",
        ):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("ask_user", plan["mode"])
                self.assertIn("gender", plan["reason"])
        for subject, expected in (
            ("girl", "base-female-eyes-open"),
            ("lady", "base-female-eyes-open"),
            ("boy", "base-male-eyes-open"),
            ("gentleman", "base-male-eyes-open"),
        ):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("character_edit", plan["mode"])
                self.assertEqual(expected, plan["base"]["asset_id"])

        for subject, expected in (
            ("maid", "base-female-eyes-open"),
            ("woman helper", "base-female-eyes-open"),
            ("female helper", "base-female-eyes-open"),
            ("male helper", "base-male-eyes-open"),
        ):
            with self.subTest(subject=subject):
                plan = plan_request(subject, skill_dir=SKILL)
                self.assertEqual("character_edit", plan["mode"])
                self.assertEqual(expected, plan["base"]["asset_id"])

    def test_planner_is_deterministic(self):
        first = plan_request("office chair", skill_dir=SKILL)
        for _ in range(3):
            self.assertEqual(first, plan_request("office chair", skill_dir=SKILL))

    def test_request_scoped_reference_precedes_bank_and_is_not_promoted(self):
        manifest = SKILL / "references" / "reference-bank" / "MANIFEST.csv"
        before = manifest.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "style.png"
            Image.new("RGB", (1024, 768), (245, 245, 245)).save(reference)
            plan = plan_request(
                "office chair",
                provided_references=[f"style={reference.resolve()}"],
                skill_dir=SKILL,
            )
        self.assertEqual("new_generation", plan["mode"])
        self.assertEqual("request_scoped", plan["references"][0]["source"])
        self.assertFalse(plan["references"][0]["bank_eligible"])
        self.assertEqual(
            ["composition", "form", "material", "style"],
            plan["coverage_gaps"][0]["missing_approved_roles"],
        )
        self.assertEqual(before, manifest.read_bytes())

    def test_request_scoped_base_routes_to_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "base.png"
            Image.new("RGB", (1024, 768), (245, 245, 245)).save(reference)
            plan = plan_request(
                "make this chair blue",
                provided_references=[f"base={reference.resolve()}"],
                skill_dir=SKILL,
            )
        self.assertEqual("base_edit", plan["mode"])
        self.assertEqual("request_scoped", plan["base"]["kind"])

    def test_non_base_request_reference_does_not_bypass_canonical_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "cue.png"
            Image.new("RGB", (1024, 768), (245, 245, 245)).save(reference)
            character = plan_request(
                "female chef with a white coat",
                provided_references=[f"style={reference.resolve()}"],
                skill_dir=SKILL,
            )
            base = plan_request(
                "make the air cooler blue",
                provided_references=[f"material={reference.resolve()}"],
                skill_dir=SKILL,
            )
            exact_with_cue = plan_request(
                "Native RO Water Purifiers (India)",
                provided_references=[f"style={reference.resolve()}"],
                skill_dir=SKILL,
            )
        self.assertEqual("character_edit", character["mode"])
        self.assertEqual("base-female-eyes-open", character["base"]["asset_id"])
        self.assertEqual("character_base", character["base"]["kind"])
        self.assertEqual("canonical character base identity", character["reason"])
        self.assertEqual("base_edit", base["mode"])
        self.assertEqual("Air cooler.png", base["base"]["base_file"])
        self.assertEqual("base_edit", exact_with_cue["mode"])
        self.assertEqual("request_scoped", exact_with_cue["references"][0]["source"])

    def test_external_reference_must_be_absolute(self):
        with self.assertRaisesRegex(ValueError, "absolute path"):
            plan_request("chair", provided_references=["style=relative.png"], skill_dir=SKILL)

    def test_request_scoped_reference_must_be_a_decodable_image(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "not-an-image.png"
            reference.write_text("this is not image data", encoding="utf-8")
            for role in ("style", "base"):
                with self.subTest(role=role):
                    with self.assertRaisesRegex(ValueError, "decodable image"):
                        plan_request(
                            "office chair",
                            provided_references=[f"{role}={reference}"],
                            skill_dir=SKILL,
                        )

    def test_request_scoped_reference_rejects_symlink_before_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.png"
            Image.new("RGB", (32, 24), (245, 245, 245)).save(target)
            reference = Path(directory) / "reference.png"
            reference.symlink_to(target)
            for role in ("style", "base"):
                with self.subTest(role=role):
                    with self.assertRaisesRegex(ValueError, "symlink"):
                        plan_request(
                            "office chair",
                            provided_references=[f"{role}={reference}"],
                            skill_dir=SKILL,
                        )

    def test_safe_resolver_rejects_absolute_and_traversal(self):
        resolver = SafeResolver(SKILL)
        with self.assertRaises(ValueError):
            resolver.resolve("/tmp/image.png", "bad", "exact_export")
        with self.assertRaises(ValueError):
            resolver.resolve("../image.png", "bad", "exact_export")

    def test_legacy_wrappers_abstain_on_confusion_probes(self):
        for subject in ["gift box", "tea glass", "black transportation van", "basin mixer tap", "office chair"]:
            with self.subTest(subject=subject):
                base = find_candidates(subject)
                refs = find_references(subject)
                self.assertEqual("no_base_found", base["decision"])
                self.assertEqual("no_reference", refs["mode"])
                self.assertEqual([], refs["references"])

    def test_legacy_generation_wrapper_uses_matching_base_only_for_form(self):
        result = find_references("air cooler")
        self.assertEqual("closest_product_reference", result["mode"])
        self.assertEqual(1, len(result["references"]))
        self.assertEqual("form", result["references"][0]["role"])

    def test_runtime_compatibility_is_role_specific_and_keeps_logical_rows(self):
        ontology = load_ontology(SKILL)
        office = classify_subject("office chair", ontology)
        lamp = classify_subject("standing lamp", ontology)
        soap = classify_subject("clear soap dispenser", ontology)
        shared = {"path": "/tmp/shared.png", "sha256": "a" * 64, "status": "approved"}
        records = [
            {
                **shared,
                "asset_id": "salon-form",
                "subject_family": "salon-chair",
                "domain": "furniture",
                "archetype": "compact-seated-furniture",
                "view": "front",
                "layout_axis": "compact",
                "projection": "mild-perspective",
                "composition_family": "single",
                "mass_count": "1",
                "materials": "upholstery;metal",
                "reference_roles": ["form"],
                "good_for": "",
                "avoid_for": "",
            },
            {
                **shared,
                "asset_id": "tea-material",
                "subject_family": "tea-glass",
                "domain": "drinkware",
                "archetype": "transparent-round-vessel",
                "view": "front",
                "layout_axis": "compact",
                "projection": "near-orthographic",
                "composition_family": "single",
                "mass_count": "1",
                "materials": "glass;liquid",
                "reference_roles": ["material"],
                "good_for": "soap-dispenser",
                "avoid_for": "",
            },
            {
                **shared,
                "asset_id": "tea-style",
                "subject_family": "tea-glass",
                "domain": "drinkware",
                "archetype": "transparent-round-vessel",
                "view": "front",
                "layout_axis": "compact",
                "projection": "near-orthographic",
                "composition_family": "single",
                "mass_count": "1",
                "materials": "glass;liquid",
                "reference_roles": ["style"],
                "good_for": "soap-dispenser",
                "avoid_for": "",
            },
        ]
        self.assertEqual([], compatible_runtime_references(office, [records[0]], set()))
        self.assertEqual([], compatible_runtime_references(lamp, [records[0]], set()))
        compatible = compatible_runtime_references(soap, records, set())
        self.assertIn("material", {item["role"] for item in compatible})
        self.assertIn("style", {item["role"] for item in compatible})

        unsafe_office = classify_subject("office chair cover", ontology)
        self.assertIsNotNone(unsafe_office)
        self.assertFalse(unsafe_office["_identity_safe"])
        self.assertEqual([], compatible_runtime_references(unsafe_office, [records[0]], set()))
        unsafe_cross_family = [
            {
                **records[1],
                "asset_id": "unsafe-material",
                "good_for": "office-chair",
                "materials": "mesh;metal",
            },
            {**records[2], "asset_id": "unsafe-style", "good_for": "office-chair"},
        ]
        self.assertEqual([], compatible_runtime_references(unsafe_office, unsafe_cross_family, set()))

    def test_every_transfer_subject_has_full_visual_taxonomy(self):
        benchmark = json.loads((ROOT / "evaluation" / "benchmarks" / "visual-v1.json").read_text())
        ontology = load_ontology(SKILL)
        for definition in benchmark["candidate_wave"]:
            for subject in [definition["target"], *definition["positive_held_out"]]:
                with self.subTest(subject=subject):
                    classification = classify_subject(subject, ontology)
                    self.assertIsNotNone(classification)
                    for field in (
                        "family", "domain", "archetype", "view", "layout_axis",
                        "projection", "composition_family", "mass_count", "materials",
                    ):
                        self.assertIn(field, classification)

    def test_wave_one_queue_is_role_typed_and_not_approved(self):
        queue = json.loads((ROOT / "evaluation" / "reference-bank" / "WAVE-1.json").read_text())
        ontology = load_ontology(SKILL)
        self.assertEqual("awaiting-generation-and-owner-review", queue["state"])
        self.assertFalse(queue["promotion_is_automatic"])
        self.assertEqual(12, len(queue["gaps"]))
        required = {
            "family", "subject", "domain", "archetype", "view", "layout_axis",
            "projection", "composition_family", "mass_count", "materials",
            "primary_role", "separately_testable_roles",
        }
        for gap in queue["gaps"]:
            self.assertTrue(required <= set(gap), gap["family"])
            self.assertIn(gap["primary_role"], gap["separately_testable_roles"])
            classification = classify_subject(gap["subject"], ontology)
            self.assertIsNotNone(classification, gap["subject"])
            self.assertTrue(classification["_identity_safe"], gap["subject"])
        self.assertIn("exactly one role", queue["logical_reference_rule"])


if __name__ == "__main__":
    unittest.main()
