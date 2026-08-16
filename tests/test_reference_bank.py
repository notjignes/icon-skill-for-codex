from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "uc-icons" / "scripts" / "manage_reference_bank.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("manage_reference_bank", SCRIPT)
assert SPEC and SPEC.loader
bank = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bank)


def stage_args(source: Path, workbench: Path, reference_id: str = "test-office-chair"):
    prompt = source.parent / f"{reference_id}-prompt.json"
    prompt.write_text(json.dumps({"prompt": "Generate an office chair on #f5f5f5."}) + "\n")
    return argparse.Namespace(
        source=str(source),
        reference_id=reference_id,
        subject_family="office-chair",
        aliases="office chair;task chair",
        domain="furniture",
        archetype="compact-seated-furniture",
        view="front",
        layout_axis="compact",
        projection="mild-perspective",
        composition_family="single",
        mass_count=1,
        materials="mesh;metal",
        palette_roles="dominant-neutral;recognition-accent",
        roles="form",
        good_for="office-chair;dining-chair;visitor-chair",
        avoid_for="sofa",
        source_kind="generated",
        model="gpt-image-2",
        prompt_record=str(prompt),
        parent_reference_ids="",
        generation_timestamp="2026-08-16T00:00:00Z",
        workbench=str(workbench),
    )


def approval_args(record_path: Path):
    return argparse.Namespace(
        candidate_record=str(record_path),
        owner_approved=True,
        approved_by="skill-owner",
        approval_note="Owner approved after blind transfer review.",
    )


def add_required_reviews(record_path: Path) -> None:
    for reviewer in ("reviewer-a", "reviewer-b"):
        bank.add_review(argparse.Namespace(
            candidate_record=str(record_path),
            reviewer=reviewer,
            status="approved",
            note=f"{reviewer} approved full-size and thumbnail views.",
        ))


def write_transfer_evidence(root: Path, reference_id: str) -> Path:
    evidence_dir = root / "evidence"
    artifacts = evidence_dir / "artifacts"
    artifacts.mkdir(parents=True)
    counter = 0

    def runs(prefix: str):
        nonlocal counter
        result = []
        for index in range(3):
            counter += 1
            artifact = artifacts / f"{counter:02d}-{prefix}-{index}.png"
            Image.new(
                "RGB",
                (1024, 768),
                ((counter * 17) % 256, (counter * 31) % 256, (counter * 47) % 256),
            ).save(artifact)
            result.append({
                "blind_id": f"blind-{counter:02d}",
                "artifact": artifact.relative_to(evidence_dir).as_posix(),
                "sha256": bank.sha256_file(artifact),
            })
        return result

    def ratings_in_blind_order(baseline, candidate, baseline_ratings, candidate_ratings, blind_order):
        by_id = {
            run["blind_id"]: rating
            for run, rating in zip(baseline + candidate, baseline_ratings + candidate_ratings)
        }
        return [{"blind_id": blind_id, "rating": by_id[blind_id]} for blind_id in blind_order]

    positive_cases = []
    for case_id, winner, baseline_mean, candidate_mean, baseline_ratings, candidate_ratings in (
        ("salon chair", "candidate", 3.8, 4.3, [3.7, 3.8, 3.9], [4.2, 4.3, 4.4]),
        ("dining chair", "candidate", 3.7, 4.2, [3.6, 3.7, 3.8], [4.1, 4.2, 4.3]),
        ("mesh visitor chair", "tie", 4.0, 4.1, [3.9, 4.0, 4.1], [4.0, 4.1, 4.2]),
    ):
        baseline = runs("baseline")
        candidate = runs("candidate")
        all_ids = [run["blind_id"] for run in baseline + candidate]
        blind_order = all_ids[1:] + all_ids[:1]
        positive_cases.append({
            "case_id": case_id,
            "winner": winner,
            "baseline_mean": baseline_mean,
            "candidate_mean": candidate_mean,
            "critical_regression": False,
            "form_leakage": False,
            "baseline": baseline,
            "candidate": candidate,
            "blind_order": blind_order,
            "ratings": ratings_in_blind_order(
                baseline,
                candidate,
                baseline_ratings,
                candidate_ratings,
                blind_order,
            ),
        })
    baseline = runs("negative-baseline")
    candidate = runs("negative-candidate")
    negative_ids = [run["blind_id"] for run in baseline + candidate]
    negative_order = negative_ids[2:] + negative_ids[:2]
    evidence = {
        "schema_version": 2,
        "benchmark_id": "visual-v1",
        "target": "office chair",
        "candidate_reference_id": reference_id,
        "tested_role": "form",
        "randomized_blind": True,
        "shuffle_seed": "fixed-test-seed",
        "generation_policy": {
            "model": "gpt-image-2",
            "prompt_template_sha256": bank.canonical_sha256({"template": "uc-icons-transfer-v1"}),
            "generation_config_sha256": bank.canonical_sha256({"quality": "high", "size": "2048x1536"}),
            "arm_difference": "candidate-reference-only",
        },
        "positive_cases": positive_cases,
        "negative_control": {
            "case_id": "sofa",
            "baseline_mean": 4.1,
            "candidate_mean": 4.0,
            "critical_regression": False,
            "form_leakage": False,
            "baseline": baseline,
            "candidate": candidate,
            "blind_order": negative_order,
            "ratings": ratings_in_blind_order(
                baseline,
                candidate,
                [4.0, 4.1, 4.2],
                [3.9, 4.0, 4.1],
                negative_order,
            ),
        },
    }
    path = evidence_dir / "transfer.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n")
    return path


def scored_case(baseline_rating, candidate_rating, winner="tie"):
    baseline = [{"blind_id": f"baseline-{index}"} for index in range(3)]
    candidate = [{"blind_id": f"candidate-{index}"} for index in range(3)]
    ids = [run["blind_id"] for run in baseline + candidate]
    blind_order = ids[1:] + ids[:1]
    by_id = {
        **{run["blind_id"]: baseline_rating for run in baseline},
        **{run["blind_id"]: candidate_rating for run in candidate},
    }
    return {
        "winner": winner,
        "baseline_mean": baseline_rating,
        "candidate_mean": candidate_rating,
        "baseline": baseline,
        "candidate": candidate,
        "blind_order": blind_order,
        "ratings": [
            {"blind_id": blind_id, "rating": by_id[blind_id]}
            for blind_id in blind_order
        ],
    }


def complete_candidate(
    source: Path,
    root: Path,
    reference_id: str = "test-office-chair",
) -> Path:
    record_path = bank.stage_candidate(stage_args(source, root / "workbench", reference_id))
    add_required_reviews(record_path)
    evidence = write_transfer_evidence(root, reference_id)
    bank.record_transfer(argparse.Namespace(
        candidate_record=str(record_path),
        note="Candidate won two of three positive cases with a clean negative control.",
        evidence=str(evidence),
    ))
    return record_path


@contextlib.contextmanager
def temporary_runtime_bank(root: Path):
    saved = (
        bank.SKILL_DIR,
        bank.BANK_DIR,
        bank.BANK_MANIFEST,
        bank.BANK_VERSION_FILE,
        bank.RUNTIME_RESOLVER,
    )
    skill = root / "uc-icons"
    runtime = skill / "references" / "reference-bank"
    runtime.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: uc-icons\n---\n")
    (skill / "VERSION").write_text("0.2.0-rc.1\n")
    (skill / "references" / "BANK_VERSION").write_text("0.2.0-rc.1\n")
    evaluation = skill / "references" / "evaluation"
    routing = skill / "references" / "routing"
    evaluation.mkdir(parents=True)
    routing.mkdir(parents=True)
    (evaluation / "visual-v1.json").write_bytes(
        (ROOT / "uc-icons" / "references" / "evaluation" / "visual-v1.json").read_bytes()
    )
    (routing / "ontology.json").write_bytes(
        (ROOT / "uc-icons" / "references" / "routing" / "ontology.json").read_bytes()
    )
    source_manifest = ROOT / "uc-icons" / "references" / "reference-bank" / "MANIFEST.csv"
    (runtime / "MANIFEST.csv").write_bytes(source_manifest.read_bytes())
    bank.SKILL_DIR = skill
    bank.BANK_DIR = runtime
    bank.BANK_MANIFEST = runtime / "MANIFEST.csv"
    bank.BANK_VERSION_FILE = skill / "references" / "BANK_VERSION"
    bank.RUNTIME_RESOLVER = bank.SafeResolver(skill)
    try:
        yield skill
    finally:
        (
            bank.SKILL_DIR,
            bank.BANK_DIR,
            bank.BANK_MANIFEST,
            bank.BANK_VERSION_FILE,
            bank.RUNTIME_RESOLVER,
        ) = saved


class ReferenceBankTests(unittest.TestCase):
    def test_candidate_is_staged_outside_skill_and_not_runtime_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "candidate.png"
            Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
            before = bank.BANK_MANIFEST.read_bytes()
            record_path = bank.stage_candidate(stage_args(source, root / "workbench"))
            record = json.loads(record_path.read_text())
            self.assertTrue(record["technical"]["passed"])
            self.assertTrue(record["technical"]["facts"]["format_png"])
            self.assertEqual("manual-required", record["technical"]["facts"]["external_shadow_check"])
            self.assertEqual(["form"], record["roles"])
            self.assertEqual([], record["good_for"])
            self.assertEqual(
                ["office-chair", "dining-chair", "visitor-chair"],
                record["proposed_good_for"],
            )
            self.assertNotIn(bank.SKILL_DIR, record_path.parents)
            self.assertFalse(Path(record["provenance"]["prompt_record"]).is_absolute())
            self.assertEqual(before, bank.BANK_MANIFEST.read_bytes())

    def test_unknown_source_kind_cannot_bypass_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "candidate.png"
            Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
            args = stage_args(source, root / "workbench")
            args.source_kind = "banana"
            with self.assertRaisesRegex(ValueError, "source_kind"):
                bank.stage_candidate(args)
            self.assertFalse((root / "workbench").exists())

    def test_gradient_background_fails_connected_background_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "gradient.png"
            image = Image.new("RGB", (1024, 768), (245, 245, 245))
            for y in range(40, 728):
                tone = 245 - min(12, abs(384 - y) // 30)
                for x in range(50, 974):
                    image.putpixel((x, y), (tone, tone, tone))
            image.save(source)
            record_path = bank.stage_candidate(stage_args(source, root / "workbench"))
            record = json.loads(record_path.read_text())
            self.assertFalse(record["technical"]["passed"])
            self.assertFalse(record["technical"]["facts"]["connected_background_f5"])

    def test_disguised_non_png_and_palette_transparency_fail_technical_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / "fake.png"
            Image.new("RGB", (1024, 768), (245, 245, 245)).save(fake, format="JPEG")
            fake_record = json.loads(bank.stage_candidate(
                stage_args(fake, root / "fake-workbench", reference_id="fake-jpeg")
            ).read_text())
            self.assertFalse(fake_record["technical"]["facts"]["format_png"])
            self.assertFalse(fake_record["technical"]["passed"])

            palette = root / "palette.png"
            image = Image.new("P", (1024, 768), 0)
            image.putpalette([245, 245, 245, 80, 100, 140] + [0, 0, 0] * 254)
            image.save(palette, transparency=0)
            palette_record = json.loads(bank.stage_candidate(
                stage_args(palette, root / "palette-workbench", reference_id="palette-alpha")
            ).read_text())
            self.assertFalse(palette_record["technical"]["facts"]["opaque"])
            self.assertFalse(palette_record["technical"]["passed"])

    def test_transfer_artifacts_must_be_delivery_sized_opaque_pngs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "tiny.png"
            Image.new("RGB", (2, 2), (245, 245, 245)).save(artifact)
            run = {
                "blind_id": "blind-one",
                "artifact": "tiny.png",
                "sha256": bank.sha256_file(artifact),
            }
            evidence = root / "evidence.json"
            evidence.write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "at least 1024x768"):
                bank.validate_evidence_run(evidence, run, verify_artifacts=True)

    def test_declared_transfer_winner_must_match_score_margin(self):
        case = scored_case(4.0, 4.2, winner="candidate")
        with self.assertRaisesRegex(ValueError, "0.4-point"):
            bank.validate_scored_winner(case)

    def test_exact_decimal_score_margin_is_accepted_on_both_boundaries(self):
        bank.validate_scored_winner(scored_case(3.7, 4.1, winner="candidate"))
        bank.validate_scored_winner(
            scored_case(4.4, 4.0),
            negative_control=True,
        )

    def test_transfer_means_must_match_per_run_ratings(self):
        case = scored_case(5.0, 1.0, winner="candidate")
        case["baseline_mean"] = 3.8
        case["candidate_mean"] = 4.3
        with self.assertRaisesRegex(ValueError, "mean derived from per-run ratings"):
            bank.validate_scored_winner(case)

    def test_transfer_ratings_require_exact_unique_blind_coverage_and_valid_values(self):
        original = scored_case(3.8, 4.3, winner="candidate")

        missing = json.loads(json.dumps(original))
        missing["ratings"].pop()
        with self.assertRaisesRegex(ValueError, "cover blind_order exactly"):
            bank.validate_scored_winner(missing)

        duplicate = json.loads(json.dumps(original))
        duplicate["ratings"][-1]["blind_id"] = duplicate["ratings"][0]["blind_id"]
        with self.assertRaisesRegex(ValueError, "duplicate transfer rating"):
            bank.validate_scored_winner(duplicate)

        for invalid in (0.9, 5.1, "NaN", "Infinity"):
            out_of_range = json.loads(json.dumps(original))
            out_of_range["ratings"][0]["rating"] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "finite decimals from 1 to 5"):
                    bank.validate_scored_winner(out_of_range)

    def test_transfer_evidence_requires_a_shared_generation_policy_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = write_transfer_evidence(root, "test-office-chair")
            payload = json.loads(evidence.read_text())
            payload.pop("generation_policy")
            evidence.write_text(json.dumps(payload, indent=2) + "\n")
            record = {
                "reference_id": "test-office-chair",
                "roles": ["form"],
                "subject_family": "office-chair",
            }
            with self.assertRaisesRegex(ValueError, "generation_policy"):
                bank.validate_transfer_evidence(evidence, record, verify_artifacts=True)

    def test_transfer_failure_flags_must_be_explicit_booleans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = write_transfer_evidence(root, "test-office-chair")
            payload = json.loads(evidence.read_text())
            payload["positive_cases"][0].pop("form_leakage")
            evidence.write_text(json.dumps(payload, indent=2) + "\n")
            record = {
                "reference_id": "test-office-chair",
                "roles": ["form"],
                "subject_family": "office-chair",
            }
            with self.assertRaisesRegex(ValueError, "explicit boolean form_leakage"):
                bank.validate_transfer_evidence(evidence, record, verify_artifacts=True)

    def test_blind_orders_require_exact_length_and_unique_ids(self):
        record = {
            "reference_id": "test-office-chair",
            "roles": ["form"],
            "subject_family": "office-chair",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = write_transfer_evidence(root, "test-office-chair")
            original = json.loads(evidence.read_text())

            positive = json.loads(json.dumps(original))
            positive_order = positive["positive_cases"][0]["blind_order"]
            positive_order.append(positive_order[0])
            evidence.write_text(json.dumps(positive, indent=2) + "\n")
            with self.assertRaisesRegex(ValueError, "complete unique blind_order"):
                bank.validate_transfer_evidence(evidence, record, verify_artifacts=True)

            negative = json.loads(json.dumps(original))
            negative_order = negative["negative_control"]["blind_order"]
            negative_order.append(negative_order[0])
            evidence.write_text(json.dumps(negative, indent=2) + "\n")
            with self.assertRaisesRegex(ValueError, "negative control requires"):
                bank.validate_transfer_evidence(evidence, record, verify_artifacts=True)

    def test_promotion_requires_explicit_owner_approval(self):
        args = argparse.Namespace(
            candidate_record="/does/not/matter.json",
            owner_approved=False,
            approved_by="owner",
            approval_note="approved",
        )
        with self.assertRaisesRegex(ValueError, "explicit --owner-approved"):
            bank.promote(args)

    def test_runtime_record_cannot_be_quarantined_in_place(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root) as skill:
                record = skill / "references" / "reference-bank" / "records" / "approved.json"
                record.parent.mkdir(parents=True)
                original = '{"state": "approved"}\n'
                record.write_text(original)
                with self.assertRaisesRegex(ValueError, "outside the installable skill"):
                    bank.quarantine(argparse.Namespace(
                        candidate_record=str(record),
                        note="must not mutate runtime",
                    ))
                self.assertEqual(original, record.read_text())

    def test_candidate_workbench_cannot_be_inside_installed_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root) as skill:
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                with self.assertRaisesRegex(ValueError, "outside the installable skill"):
                    bank.stage_candidate(stage_args(source, skill / "candidate-workbench"))

    def test_runtime_path_rejects_symlink_leaf_and_parent_components(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root) as skill:
                records = skill / "references" / "reference-bank" / "records"
                records.mkdir()
                real_file = records / "real.json"
                real_file.write_text("{}\n")

                leaf = records / "leaf.json"
                leaf.symlink_to(real_file.name)
                with self.assertRaisesRegex(ValueError, "symlink component"):
                    bank.resolve_runtime_path(
                        "references/reference-bank/records/leaf.json"
                    )

                real_parent = records / "real-parent"
                real_parent.mkdir()
                (real_parent / "nested.json").write_text("{}\n")
                linked_parent = records / "linked-parent"
                linked_parent.symlink_to(real_parent.name, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, "symlink component"):
                    bank.resolve_runtime_path(
                        "references/reference-bank/records/linked-parent/nested.json"
                    )

                contained = root / "contained"
                contained.mkdir()
                contained_real = contained / "real.json"
                contained_real.write_text("{}\n")
                contained_leaf = contained / "leaf.json"
                contained_leaf.symlink_to(contained_real.name)
                with self.assertRaisesRegex(ValueError, "symlink component"):
                    bank.resolve_contained_file(contained, "leaf.json", "test file")

                contained_parent = contained / "real-parent"
                contained_parent.mkdir()
                (contained_parent / "nested.json").write_text("{}\n")
                contained_linked_parent = contained / "linked-parent"
                contained_linked_parent.symlink_to(
                    contained_parent.name,
                    target_is_directory=True,
                )
                with self.assertRaisesRegex(ValueError, "symlink component"):
                    bank.resolve_contained_file(
                        contained,
                        "linked-parent/nested.json",
                        "test file",
                    )

    def test_empty_runtime_bank_keeps_unsuffixed_base_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                self.assertEqual("0.2.0-rc.1", bank.bank_content_version([]))
                self.assertEqual([], bank.validate_runtime_bank())
                for invalid_version, expected_error in (
                    ("0.2.0-rc.1+bank.000000000000", "unsuffixed base version"),
                    ("evil", "content-derived bank version"),
                ):
                    with self.subTest(invalid_version=invalid_version):
                        bank.BANK_VERSION_FILE.write_text(invalid_version + "\n")
                        errors = bank.validate_runtime_bank()
                        self.assertTrue(any(expected_error in error for error in errors))

    def test_candidate_family_must_match_benchmark_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                record_path = bank.stage_candidate(stage_args(source, root / "workbench"))
                record = json.loads(record_path.read_text())
                record["subject_family"] = "standing-lamp"
                record_path.write_text(json.dumps(record, indent=2) + "\n")
                evidence = write_transfer_evidence(root, "test-office-chair")
                with self.assertRaisesRegex(ValueError, "target family"):
                    bank.record_transfer(argparse.Namespace(
                        candidate_record=str(record_path),
                        note="invalid family fixture",
                        evidence=str(evidence),
                    ))
                _, rows = bank.load_manifest()
                self.assertEqual([], rows)

    def test_successful_promotion_is_owner_gated_valid_and_versioned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                record_path = complete_candidate(source, root)
                runtime_record, runtime_image = bank.promote(approval_args(record_path))
                self.assertEqual([], bank.validate_runtime_bank())
                self.assertTrue(runtime_image.is_file())
                self.assertIn("+bank.", bank.BANK_VERSION_FILE.read_text())
                payload = json.loads(runtime_record.read_text())
                self.assertEqual("approved", payload["state"])
                self.assertEqual(["dining-chair", "salon-chair"], payload["good_for"])
                self.assertEqual("form", payload["transfer_test"]["tested_role"])
                self.assertNotIn(str(root), json.dumps(payload))
                evidence_path = bank.resolve_runtime_path(payload["transfer_test"]["evidence_record"])
                runtime_evidence = json.loads(evidence_path.read_text())
                self.assertEqual(2, runtime_evidence["schema_version"])
                self.assertTrue(runtime_evidence["artifact_paths_omitted"])
                self.assertTrue(all("artifact" not in run for run in bank.transfer_runs(runtime_evidence)))
                for case in runtime_evidence["positive_cases"] + [runtime_evidence["negative_control"]]:
                    self.assertEqual(
                        set(case["blind_order"]),
                        {rating["blind_id"] for rating in case["ratings"]},
                    )
                _, rows = bank.load_manifest()
                self.assertEqual(1, len(rows))
                self.assertEqual("dining-chair;salon-chair", rows[0]["good_for"])
                self.assertEqual("form", rows[0]["roles"])
                self.assertEqual(bank.sha256_file(runtime_record), rows[0]["provenance_sha256"])

    def test_runtime_bank_rejects_orphans_and_version_drift_but_allows_shared_master(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                first = complete_candidate(source, root / "first")
                bank.promote(approval_args(first))
                second = complete_candidate(
                    source,
                    root / "second",
                    reference_id="test-office-chair-alt",
                )
                bank.promote(approval_args(second))

                self.assertEqual([], bank.validate_runtime_bank())
                fields, rows = bank.load_manifest()
                self.assertEqual(2, len(rows))
                self.assertEqual(1, len({row["image_path"] for row in rows}))
                self.assertEqual(1, len(list((bank.BANK_DIR / "assets").glob("*.png"))))
                global_version = bank.BANK_VERSION_FILE.read_text().strip()
                self.assertEqual(bank.bank_content_version(rows), global_version)
                self.assertTrue(all(row["bank_version"] == global_version for row in rows))

                original_manifest = bank.BANK_MANIFEST.read_bytes()
                original_version = bank.BANK_VERSION_FILE.read_bytes()

                drifted_rows = json.loads(json.dumps(rows))
                drifted_rows[0]["bank_version"] = "0.2.0-rc.1+bank.000000000000"
                bank.write_manifest(fields, drifted_rows)
                errors = bank.validate_runtime_bank()
                self.assertTrue(any("row bank_version disagrees" in error for error in errors))
                bank.BANK_MANIFEST.write_bytes(original_manifest)

                bank.BANK_VERSION_FILE.write_text("0.2.0-rc.1+bank.000000000000\n")
                errors = bank.validate_runtime_bank()
                self.assertTrue(any("content-derived bank version" in error for error in errors))
                bank.BANK_VERSION_FILE.write_bytes(original_version)

                fields, coordinated_rows = bank.load_manifest()
                content_suffix = global_version.split("+bank.", 1)[1]
                coordinated_version = f"evil+bank.{content_suffix}"
                for row in coordinated_rows:
                    row["bank_version"] = coordinated_version
                bank.write_manifest(fields, coordinated_rows)
                bank.BANK_VERSION_FILE.write_text(coordinated_version + "\n")
                errors = bank.validate_runtime_bank()
                self.assertTrue(any("content-derived bank version" in error for error in errors))
                bank.BANK_MANIFEST.write_bytes(original_manifest)
                bank.BANK_VERSION_FILE.write_bytes(original_version)

                fields, drifted_rows = bank.load_manifest()
                drifted_rows[0]["review_note"] += " tampered"
                bank.write_manifest(fields, drifted_rows)
                errors = bank.validate_runtime_bank()
                self.assertTrue(any("content-derived bank version" in error for error in errors))
                bank.BANK_MANIFEST.write_bytes(original_manifest)

                orphan_paths = (
                    bank.BANK_DIR / "assets" / "orphan.png",
                    bank.BANK_DIR / "records" / "orphan.json",
                    bank.BANK_DIR / "records" / "orphan-transfer.json",
                    bank.BANK_DIR / "records" / "orphan-prompt.json",
                )
                for orphan in orphan_paths:
                    orphan.write_bytes(b"orphan")
                errors = bank.validate_runtime_bank()
                for orphan in orphan_paths:
                    with self.subTest(orphan=orphan.name):
                        self.assertTrue(any(orphan.name in error for error in errors))

    def test_installed_transfer_evidence_is_strictly_path_free(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                record_path = bank.stage_candidate(stage_args(source, root / "workbench"))
                add_required_reviews(record_path)
                evidence = write_transfer_evidence(root, "test-office-chair")
                payload = json.loads(evidence.read_text())
                payload["workbench_path"] = str(root)
                payload["positive_cases"][0]["baseline"][0]["local_path"] = str(root / "secret.png")
                evidence.write_text(json.dumps(payload, indent=2) + "\n")
                bank.record_transfer(argparse.Namespace(
                    candidate_record=str(record_path),
                    note="Valid transfer with adversarial extra path fields.",
                    evidence=str(evidence),
                ))
                runtime_record, _ = bank.promote(approval_args(record_path))
                runtime_payload = json.loads(runtime_record.read_text())
                evidence_path = bank.resolve_runtime_path(
                    runtime_payload["transfer_test"]["evidence_record"]
                )
                installed = evidence_path.read_text()
                self.assertNotIn("workbench_path", installed)
                self.assertNotIn("local_path", installed)
                self.assertNotIn(str(root), installed)
                installed_payload = json.loads(installed)
                self.assertEqual(
                    payload["positive_cases"][0]["ratings"],
                    installed_payload["positive_cases"][0]["ratings"],
                )

    def test_failed_post_commit_validation_rolls_back_without_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                record_path = complete_candidate(source, root)
                before_manifest = bank.BANK_MANIFEST.read_bytes()
                before_version = bank.BANK_VERSION_FILE.read_bytes()
                original_validator = bank.validate_runtime_bank
                bank.validate_runtime_bank = lambda: ["forced post-commit failure"]
                try:
                    with self.assertRaisesRegex(ValueError, "forced post-commit failure"):
                        bank.promote(approval_args(record_path))
                finally:
                    bank.validate_runtime_bank = original_validator
                self.assertEqual(before_manifest, bank.BANK_MANIFEST.read_bytes())
                self.assertEqual(before_version, bank.BANK_VERSION_FILE.read_bytes())
                self.assertEqual([], list((bank.BANK_DIR / "assets").glob("*")))
                self.assertEqual([], list((bank.BANK_DIR / "records").glob("*")))

    def test_invalid_role_preflight_leaves_no_runtime_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                record_path = complete_candidate(source, root)
                payload = json.loads(record_path.read_text())
                payload["roles"] = ["invented-role"]
                record_path.write_text(json.dumps(payload, indent=2) + "\n")
                with self.assertRaisesRegex(ValueError, "exactly one tested role"):
                    bank.promote(approval_args(record_path))
                _, rows = bank.load_manifest()
                self.assertEqual([], rows)
                self.assertFalse((bank.BANK_DIR / "assets").exists())
                self.assertFalse((bank.BANK_DIR / "records").exists())

    def test_runtime_provenance_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with temporary_runtime_bank(root):
                source = root / "candidate.png"
                Image.new("RGB", (2048, 1536), (245, 245, 245)).save(source)
                record_path = complete_candidate(source, root)
                runtime_record, _ = bank.promote(approval_args(record_path))
                runtime_record.write_text("{}\n")
                errors = bank.validate_runtime_bank()
                self.assertTrue(any("provenance record hash mismatch" in error for error in errors))

    def test_two_distinct_visual_reviewers_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "candidate.png"
            Image.new("RGB", (1024, 768), (245, 245, 245)).save(source)
            record_path = bank.stage_candidate(stage_args(source, root / "workbench"))
            for note in ("first", "updated"):
                bank.add_review(argparse.Namespace(
                    candidate_record=str(record_path),
                    reviewer="same-reviewer",
                    status="approved",
                    note=note,
                ))
            record = json.loads(record_path.read_text())
            self.assertEqual(1, len(record["visual_reviews"]))

            bank.add_review(argparse.Namespace(
                candidate_record=str(record_path),
                reviewer=" SAME-REVIEWER ",
                status="approved",
                note="case and whitespace variant",
            ))
            record = json.loads(record_path.read_text())
            self.assertEqual(1, len(record["visual_reviews"]))
            self.assertEqual("SAME-REVIEWER", record["visual_reviews"][0]["reviewer"])

            with self.assertRaisesRegex(ValueError, "reviewer identity"):
                bank.add_review(argparse.Namespace(
                    candidate_record=str(record_path),
                    reviewer="   ",
                    status="approved",
                    note="invalid blank reviewer",
                ))
            with self.assertRaisesRegex(ValueError, "review note"):
                bank.add_review(argparse.Namespace(
                    candidate_record=str(record_path),
                    reviewer="reviewer-b",
                    status="approved",
                    note="   ",
                ))

    def test_installed_and_repo_benchmark_definitions_match(self):
        installed = json.loads(
            (ROOT / "uc-icons" / "references" / "evaluation" / "visual-v1.json").read_text()
        )
        workbench = json.loads(
            (ROOT / "evaluation" / "benchmarks" / "visual-v1.json").read_text()
        )
        self.assertEqual(workbench, installed)


if __name__ == "__main__":
    unittest.main()
