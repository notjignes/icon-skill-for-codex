#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath

from PIL import Image

from asset_registry import SafeResolver
from image_contract import scan_border_component


SKILL_DIR = Path(__file__).resolve().parents[1]
BANK_DIR = SKILL_DIR / "references" / "reference-bank"
BANK_MANIFEST = BANK_DIR / "MANIFEST.csv"
BANK_VERSION_FILE = SKILL_DIR / "references" / "BANK_VERSION"
DEFAULT_WORKBENCH = Path.cwd() / "evaluation" / "reference-bank"
RUNTIME_RESOLVER = SafeResolver(SKILL_DIR)

ALLOWED_ROLES = {"form", "material", "composition", "style"}
ALLOWED_STATES = {"candidate", "approved", "quarantined", "deprecated"}
ALLOWED_EXECUTION_ROLES = {"exact_export", "base_edit", "generation_reference"}
ALLOWED_SOURCE_KINDS = {"generated", "imported"}
ALLOWED_VIEWS = {"front", "side", "front-3q", "slight-top"}
ALLOWED_AXES = {"compact", "vertical", "horizontal"}
ALLOWED_PROJECTIONS = {"near-orthographic", "mild-perspective"}
ALLOWED_COMPOSITIONS = {"single", "object-cue", "carrier-contents", "grouped"}
TECHNICAL_CHECKS = (
    "format_png", "opaque", "aspect_4_3", "minimum_size", "border_f5",
    "connected_background_f5",
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not result:
        raise ValueError("reference_id must contain letters or digits")
    return result


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def reviewer_identity(value: object) -> tuple[str, str]:
    display = " ".join(str(value).split())
    if not display:
        raise ValueError("reviewer identity must be non-empty")
    return display, display.casefold()


def split_values(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def require_enum(name: str, value: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}; got {value!r}")
    return value


def load_manifest() -> tuple[list[str], list[dict[str, str]]]:
    with BANK_MANIFEST.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    write_csv(BANK_MANIFEST, fieldnames, rows)


def resolve_runtime_path(value: str) -> Path:
    if not value or "\\" in value:
        raise ValueError(f"Runtime path must be a non-empty POSIX relative path: {value!r}")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"Unsafe runtime path: {value!r}")
    lexical = RUNTIME_RESOLVER.skill_dir
    for part in relative.parts:
        lexical = lexical / part
        if lexical.is_symlink():
            raise ValueError(f"Runtime path contains a symlink component: {value!r}")
    return Path(
        RUNTIME_RESOLVER.resolve(
            value,
            logical_asset_id="reference-bank-runtime-path",
            execution_role="generation_reference",
        ).path
    )


def resolve_contained_file(parent: Path, value: str, label: str) -> Path:
    if not value or "\\" in value:
        raise ValueError(f"{label} must be a non-empty POSIX relative path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"unsafe {label}: {value!r}")
    parent = parent.resolve()
    lexical = parent
    for part in relative.parts:
        lexical = lexical / part
        if lexical.is_symlink():
            raise ValueError(f"{label} contains a symlink component: {value!r}")
    candidate = lexical.resolve()
    if candidate == parent or parent not in candidate.parents:
        raise ValueError(f"{label} escapes its record directory: {value!r}")
    if not candidate.is_file() or candidate.is_symlink():
        raise FileNotFoundError(f"missing {label}: {candidate}")
    return candidate


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def candidate_fingerprint(record: dict[str, object]) -> str:
    keys = (
        "schema_version", "reference_id", "asset", "sha256", "subject_family", "aliases",
        "domain", "archetype", "view", "layout_axis", "projection", "composition_family",
        "mass_count", "materials", "palette_roles", "roles", "proposed_good_for", "avoid_for",
        "technical", "provenance",
    )
    return canonical_sha256({key: record.get(key) for key in keys})


def bank_content_version(rows: list[dict[str, str]]) -> str:
    base = (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip()
    if not base or "+bank." in base:
        raise ValueError("skill VERSION must be a non-empty unsuffixed release version")
    if not rows:
        return base
    content = [
        {key: value for key, value in sorted(row.items()) if key != "bank_version"}
        for row in sorted(rows, key=lambda item: item.get("reference_id", ""))
    ]
    return f"{base}+bank.{canonical_sha256(content)[:12]}"


def inspect_image(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        width, height = image.size
        alpha_extrema = image.convert("RGBA").getchannel("A").getextrema()
        opaque = alpha_extrema == (255, 255)
        rgb = image.convert("RGB")
        border = [rgb.getpixel((x, y)) for x in range(width) for y in (0, height - 1)]
        border += [rgb.getpixel((x, y)) for y in range(1, height - 1) for x in (0, width - 1)]

        def pale_neutral(pixel: tuple[int, ...]) -> bool:
            red, green, blue = pixel
            return min(red, green, blue) >= 200 and max(red, green, blue) - min(red, green, blue) <= 20
        component_count, exact_background = scan_border_component(
            rgb,
            pale_neutral,
            is_exact=lambda pixel: pixel == (245, 245, 245),
        )
        connected_exact_ratio = exact_background / component_count if component_count else 0.0
        return {
            "format": image.format,
            "format_png": image.format == "PNG",
            "size": [width, height],
            "mode": image.mode,
            "opaque": opaque,
            "aspect_4_3": abs((width / height) - (4 / 3)) <= 0.01,
            "minimum_size": width >= 1024 and height >= 768,
            "border_f5": all(pixel == (245, 245, 245) for pixel in border),
            "connected_background_exact_ratio": connected_exact_ratio,
            "connected_background_f5": connected_exact_ratio >= 0.995,
            "external_shadow_check": "manual-required",
        }


def validate_record_taxonomy(record: dict[str, object], expected_state: str | None = None) -> None:
    required_strings = ("reference_id", "subject_family", "domain", "archetype")
    for key in required_strings:
        if not isinstance(record.get(key), str) or not str(record[key]).strip():
            raise ValueError(f"candidate record requires non-empty {key}")
    if slug(str(record["reference_id"])) != record["reference_id"]:
        raise ValueError("reference_id must already be a stable lower-kebab slug")
    require_enum("state", str(record.get("state", "")), ALLOWED_STATES)
    if expected_state and record.get("state") != expected_state:
        raise ValueError(f"record state must be {expected_state!r}; got {record.get('state')!r}")
    require_enum("view", str(record.get("view", "")), ALLOWED_VIEWS)
    require_enum("layout_axis", str(record.get("layout_axis", "")), ALLOWED_AXES)
    require_enum("projection", str(record.get("projection", "")), ALLOWED_PROJECTIONS)
    require_enum("composition_family", str(record.get("composition_family", "")), ALLOWED_COMPOSITIONS)
    roles = set(record.get("roles", []))
    if len(roles) != 1 or not roles <= ALLOWED_ROLES:
        raise ValueError(f"each logical reference requires exactly one tested role: {sorted(roles)}")
    mass_count = record.get("mass_count")
    if not isinstance(mass_count, int) or not 1 <= mass_count <= 2:
        raise ValueError("mass_count must be an integer from 1 to 2")
    digest = str(record.get("sha256", ""))
    if not SHA256_PATTERN.fullmatch(digest):
        raise ValueError("candidate sha256 must be 64 lowercase hex characters")
    technical = record.get("technical")
    if not isinstance(technical, dict) or not isinstance(technical.get("facts"), dict):
        raise ValueError("candidate technical facts are missing")
    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("candidate provenance is missing")
    require_enum("source_kind", str(provenance.get("source_kind", "")), ALLOWED_SOURCE_KINDS)
    for key in ("source_sha256", "model", "generation_timestamp"):
        if not str(provenance.get(key, "")).strip():
            raise ValueError(f"candidate provenance requires {key}")
    if provenance.get("source_kind") == "generated":
        for key in ("prompt_record", "prompt_sha256"):
            if not str(provenance.get(key, "")).strip():
                raise ValueError(f"generated candidate provenance requires {key}")


def benchmark_definition(benchmark_id: str, target: str) -> tuple[dict[str, object], dict[str, object]]:
    if not re.fullmatch(r"[a-z0-9-]+", benchmark_id):
        raise ValueError(f"unsafe benchmark_id: {benchmark_id!r}")
    path = SKILL_DIR / "references" / "evaluation" / f"{benchmark_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    definitions = payload.get("candidate_wave", payload.get("subjects", []))
    definition = next((item for item in definitions if item.get("target") == target), None)
    if not definition:
        raise ValueError(f"benchmark target {target!r} is not declared by {benchmark_id}")
    return payload, definition


def ontology_family_for_subject(subject: str) -> str:
    ontology_path = SKILL_DIR / "references" / "routing" / "ontology.json"
    ontology = json.loads(ontology_path.read_text(encoding="utf-8"))
    subject_norm = normalize(subject)
    matches = [
        str(family["family"])
        for family in ontology.get("families", [])
        if subject_norm in {normalize(str(alias)) for alias in family.get("aliases", [])}
    ]
    if len(matches) != 1:
        raise ValueError(f"benchmark subject must resolve to exactly one ontology family: {subject!r}")
    return matches[0]


def verify_evidence_artifact(evidence_path: Path, run: dict[str, object]) -> None:
    artifact = resolve_contained_file(evidence_path.parent, str(run.get("artifact", "")), "transfer artifact")
    expected = str(run.get("sha256", ""))
    if not SHA256_PATTERN.fullmatch(expected) or sha256_file(artifact) != expected:
        raise ValueError(f"transfer artifact hash mismatch: {artifact.name}")
    with Image.open(artifact) as image:
        width, height = image.size
        opaque = image.convert("RGBA").getchannel("A").getextrema() == (255, 255)
        if image.format != "PNG" or width < 1024 or height < 768:
            raise ValueError("transfer artifacts must be decodable PNGs at least 1024x768")
        if abs((width / height) - (4 / 3)) > 0.01 or not opaque:
            raise ValueError("transfer artifacts must be opaque 4:3 images")


def validate_evidence_run(
    evidence_path: Path,
    run: dict[str, object],
    verify_artifacts: bool,
) -> None:
    if not str(run.get("blind_id", "")).strip():
        raise ValueError("each transfer run requires a blind_id")
    digest = str(run.get("sha256", ""))
    if not SHA256_PATTERN.fullmatch(digest):
        raise ValueError("each transfer run requires a SHA-256")
    if verify_artifacts:
        verify_evidence_artifact(evidence_path, run)
    elif "artifact" in run:
        raise ValueError("installed transfer evidence must not contain artifact paths")


def transfer_rating(value: object) -> Decimal:
    try:
        rating = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("transfer ratings must be finite decimals from 1 to 5") from exc
    if not rating.is_finite() or not Decimal("1") <= rating <= Decimal("5"):
        raise ValueError("transfer ratings must be finite decimals from 1 to 5")
    return rating


def validate_blind_ratings(
    case: dict[str, object],
    blind_order: list[str],
) -> dict[str, Decimal]:
    entries = case.get("ratings", [])
    if not isinstance(entries, list):
        raise ValueError("each transfer case requires per-run ratings keyed by blind_id")
    ratings: dict[str, Decimal] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each transfer rating must contain blind_id and rating")
        blind_id = str(entry.get("blind_id", "")).strip()
        if not blind_id:
            raise ValueError("each transfer rating requires a blind_id")
        if blind_id in ratings:
            raise ValueError(f"duplicate transfer rating for blind_id: {blind_id}")
        if "rating" not in entry:
            raise ValueError(f"missing transfer rating for blind_id: {blind_id}")
        ratings[blind_id] = transfer_rating(entry["rating"])
    if len(ratings) != len(blind_order) or set(ratings) != set(blind_order):
        raise ValueError("transfer ratings must cover blind_order exactly")
    return ratings


def validate_scored_winner(
    case: dict[str, object],
    ratings: dict[str, Decimal] | None = None,
    *,
    negative_control: bool = False,
) -> str:
    blind_order = [str(value) for value in case.get("blind_order", [])]
    ratings = ratings or validate_blind_ratings(case, blind_order)
    derived: dict[str, Decimal] = {}
    for arm in ("baseline", "candidate"):
        runs = case.get(arm, [])
        if not isinstance(runs, list) or not runs:
            raise ValueError(f"each transfer case requires scored {arm} runs")
        try:
            arm_ratings = [ratings[str(run["blind_id"])] for run in runs]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"{arm} ratings do not match the transfer runs") from exc
        derived[arm] = sum(arm_ratings, Decimal("0")) / Decimal(len(arm_ratings))
    for arm in ("baseline", "candidate"):
        field = f"{arm}_mean"
        try:
            declared = Decimal(str(case[field]))
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise ValueError(f"each transfer case requires numeric {field}") from exc
        if not declared.is_finite() or not Decimal("1") <= declared <= Decimal("5"):
            raise ValueError("transfer means must be within the 1-5 review scale")
        if declared != derived[arm]:
            raise ValueError(f"{field} does not match the mean derived from per-run ratings")
    baseline = derived["baseline"]
    candidate = derived["candidate"]
    delta = candidate - baseline
    if negative_control:
        if delta < Decimal("-0.4"):
            raise ValueError("candidate regressed the negative-control score by more than 0.4")
        return "candidate" if delta >= Decimal("0.4") else "baseline" if delta <= Decimal("-0.4") else "tie"
    expected = (
        "candidate" if delta >= Decimal("0.4")
        else "baseline" if delta <= Decimal("-0.4")
        else "tie"
    )
    if case.get("winner") != expected:
        raise ValueError("declared winner disagrees with the required 0.4-point score margin")
    return expected


def validate_binary_failure_fields(case: dict[str, object], label: str) -> None:
    for field in ("critical_regression", "form_leakage"):
        if field not in case or type(case[field]) is not bool:
            raise ValueError(f"{label} requires an explicit boolean {field}")
        if case[field]:
            raise ValueError(f"{label} contains {field.replace('_', ' ')}")


def validate_generation_policy(evidence: dict[str, object]) -> str:
    policy = evidence.get("generation_policy")
    if not isinstance(policy, dict):
        raise ValueError("transfer evidence requires a shared generation_policy")
    model = str(policy.get("model", "")).strip()
    if not model:
        raise ValueError("generation_policy requires a model")
    for field in ("prompt_template_sha256", "generation_config_sha256"):
        if not SHA256_PATTERN.fullmatch(str(policy.get(field, ""))):
            raise ValueError(f"generation_policy requires a valid {field}")
    if policy.get("arm_difference") != "candidate-reference-only":
        raise ValueError("generation_policy arm_difference must be candidate-reference-only")
    return canonical_sha256({
        "model": model,
        "prompt_template_sha256": policy["prompt_template_sha256"],
        "generation_config_sha256": policy["generation_config_sha256"],
        "arm_difference": policy["arm_difference"],
    })


def validate_transfer_evidence(
    evidence_path: Path,
    record: dict[str, object],
    verify_artifacts: bool,
) -> dict[str, object]:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("schema_version") != 2 or evidence.get("randomized_blind") is not True:
        raise ValueError("transfer evidence must be schema v2 and randomized_blind=true")
    generation_policy_fingerprint = validate_generation_policy(evidence)
    if not str(evidence.get("shuffle_seed", "")).strip():
        raise ValueError("transfer evidence requires a recorded shuffle_seed")
    if evidence.get("candidate_reference_id") != record.get("reference_id"):
        raise ValueError("transfer evidence candidate_reference_id does not match")
    roles = list(record.get("roles", []))
    tested_role = str(evidence.get("tested_role", ""))
    if len(roles) != 1 or tested_role != roles[0]:
        raise ValueError("transfer evidence tested_role must match the logical reference role")
    benchmark_id = str(evidence.get("benchmark_id", ""))
    target = str(evidence.get("target", ""))
    benchmark, definition = benchmark_definition(benchmark_id, target)
    if record.get("subject_family") != definition.get("target_family"):
        raise ValueError("candidate subject_family does not match the benchmark target family")
    expected_cases = list(definition.get("positive_held_out", []))
    cases = evidence.get("positive_cases", [])
    if not isinstance(cases, list) or len(cases) != 3:
        raise ValueError("transfer evidence requires exactly three positive cases")
    if {str(case.get("case_id", "")) for case in cases} != set(expected_cases):
        raise ValueError("transfer positive case IDs do not match the benchmark definition")
    runs_per_arm = int(benchmark.get("transfer_runs_per_arm", 3))
    wins = 0
    winning_case_ids: set[str] = set()
    seen_artifacts: set[str] = set()
    seen_hashes: set[str] = set()
    for case in cases:
        if case.get("winner") not in {"candidate", "baseline", "tie"}:
            raise ValueError("each transfer case requires a declared winner")
        validate_binary_failure_fields(case, "positive transfer case")
        runs_by_arm: list[list[dict[str, object]]] = []
        for arm in ("baseline", "candidate"):
            runs = case.get(arm, [])
            if not isinstance(runs, list) or len(runs) != runs_per_arm:
                raise ValueError(f"each {arm} arm requires {runs_per_arm} runs")
            runs_by_arm.append(runs)
            for run in runs:
                validate_evidence_run(evidence_path, run, verify_artifacts)
                digest = str(run.get("sha256", ""))
                if digest in seen_hashes:
                    raise ValueError("each benchmark run requires a distinct artifact SHA-256")
                seen_hashes.add(digest)
                if verify_artifacts:
                    artifact_value = str(run.get("artifact", ""))
                    if artifact_value in seen_artifacts:
                        raise ValueError("each benchmark run requires a distinct artifact")
                    seen_artifacts.add(artifact_value)
        ordered_ids = [str(run.get("blind_id", "")) for runs in runs_by_arm for run in runs]
        blind_order = [str(value) for value in case.get("blind_order", [])]
        expected_order_size = runs_per_arm * 2
        if (
            len(set(ordered_ids)) != expected_order_size
            or len(blind_order) != expected_order_size
            or len(set(blind_order)) != expected_order_size
            or set(blind_order) != set(ordered_ids)
        ):
            raise ValueError("each transfer case requires a complete unique blind_order")
        if blind_order == ordered_ids:
            raise ValueError("blind_order must be shuffled")
        ratings = validate_blind_ratings(case, blind_order)
        winner = validate_scored_winner(case, ratings)
        if winner == "candidate":
            wins += 1
            winning_case_ids.add(str(case["case_id"]))
    negative = evidence.get("negative_control", {})
    if negative.get("case_id") != definition.get("negative_control"):
        raise ValueError("negative-control ID does not match the benchmark definition")
    validate_binary_failure_fields(negative, "negative control")
    negative_runs: list[list[dict[str, object]]] = []
    for arm in ("baseline", "candidate"):
        runs = negative.get(arm, [])
        if not isinstance(runs, list) or len(runs) != runs_per_arm:
            raise ValueError(f"negative-control {arm} arm requires {runs_per_arm} runs")
        negative_runs.append(runs)
        for run in runs:
            validate_evidence_run(evidence_path, run, verify_artifacts)
            digest = str(run.get("sha256", ""))
            if digest in seen_hashes:
                raise ValueError("each benchmark run requires a distinct artifact SHA-256")
            seen_hashes.add(digest)
            if verify_artifacts:
                artifact_value = str(run.get("artifact", ""))
                if artifact_value in seen_artifacts:
                    raise ValueError("each benchmark run requires a distinct artifact")
                seen_artifacts.add(artifact_value)
    negative_ids = [str(run.get("blind_id", "")) for runs in negative_runs for run in runs]
    negative_order = [str(value) for value in negative.get("blind_order", [])]
    expected_negative_order_size = runs_per_arm * 2
    if (
        len(set(negative_ids)) != expected_negative_order_size
        or len(negative_order) != expected_negative_order_size
        or len(set(negative_order)) != expected_negative_order_size
        or set(negative_order) != set(negative_ids)
    ):
        raise ValueError("negative control requires a complete unique blind_order")
    if negative_order == negative_ids:
        raise ValueError("negative-control blind_order must be shuffled")
    negative_ratings = validate_blind_ratings(negative, negative_order)
    validate_scored_winner(negative, negative_ratings, negative_control=True)
    if wins < 2:
        raise ValueError("candidate must win at least two positive transfer cases")
    approved_good_for = sorted({
        ontology_family_for_subject(case_id)
        for case_id in winning_case_ids
    })
    return {
        "status": "passed",
        "benchmark_id": benchmark_id,
        "target": target,
        "tested_role": tested_role,
        "positive_cases": 3,
        "positive_wins": wins,
        "critical_regressions": 0,
        "negative_form_leakage": 0,
        "approved_good_for": approved_good_for,
        "generation_policy_fingerprint": generation_policy_fingerprint,
    }


def transfer_runs(evidence: dict[str, object]) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for case in evidence.get("positive_cases", []):
        runs.extend(case.get("baseline", []))
        runs.extend(case.get("candidate", []))
    negative = evidence.get("negative_control", {})
    runs.extend(negative.get("baseline", []))
    runs.extend(negative.get("candidate", []))
    return runs


def portable_transfer_evidence(evidence_path: Path) -> bytes:
    """Build a strict, path-free evidence record for the installed skill."""

    source = json.loads(evidence_path.read_text(encoding="utf-8"))

    def portable_runs(runs: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {"blind_id": run["blind_id"], "sha256": run["sha256"]}
            for run in runs
        ]

    def portable_case(case: dict[str, object], *, negative: bool = False) -> dict[str, object]:
        result = {
            "case_id": case["case_id"],
            "baseline_mean": case["baseline_mean"],
            "candidate_mean": case["candidate_mean"],
            "critical_regression": case["critical_regression"],
            "form_leakage": case["form_leakage"],
            "baseline": portable_runs(case["baseline"]),
            "candidate": portable_runs(case["candidate"]),
            "blind_order": list(case["blind_order"]),
            "ratings": [
                {"blind_id": rating["blind_id"], "rating": rating["rating"]}
                for rating in case["ratings"]
            ],
        }
        if not negative:
            result["winner"] = case["winner"]
        return result

    policy = source["generation_policy"]
    payload = {
        "schema_version": source["schema_version"],
        "benchmark_id": source["benchmark_id"],
        "target": source["target"],
        "candidate_reference_id": source["candidate_reference_id"],
        "tested_role": source["tested_role"],
        "randomized_blind": source["randomized_blind"],
        "shuffle_seed": source["shuffle_seed"],
        "generation_policy": {
            "model": policy["model"],
            "prompt_template_sha256": policy["prompt_template_sha256"],
            "generation_config_sha256": policy["generation_config_sha256"],
            "arm_difference": policy["arm_difference"],
        },
        "positive_cases": [portable_case(case) for case in source["positive_cases"]],
        "negative_control": portable_case(source["negative_control"], negative=True),
        "artifact_paths_omitted": True,
        "artifact_archive": "candidate-workbench",
    }
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")


def validate_runtime_record(
    row: dict[str, str],
    record_path: Path,
    image_path: Path,
) -> list[str]:
    errors: list[str] = []
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        validate_record_taxonomy(record, expected_state="approved")
        mapping = {
            "reference_id": "reference_id",
            "subject_family": "subject_family",
            "domain": "domain",
            "archetype": "archetype",
            "view": "view",
            "layout_axis": "layout_axis",
            "projection": "projection",
            "composition_family": "composition_family",
            "mass_count": "mass_count",
            "sha256": "sha256",
        }
        for row_key, record_key in mapping.items():
            if str(row.get(row_key, "")) != str(record.get(record_key, "")):
                errors.append(f"record {row_key} disagrees with manifest")
        for row_key, record_key in (("roles", "roles"), ("materials", "materials"), ("good_for", "good_for"), ("avoid_for", "avoid_for")):
            if split_values(row.get(row_key, "")) != list(record.get(record_key, [])):
                errors.append(f"record {row_key} disagrees with manifest")
        if record.get("asset") != row.get("image_path") or sha256_file(image_path) != record.get("sha256"):
            errors.append("record asset path/hash disagrees with runtime image")
        approval = record.get("owner_approval")
        if not isinstance(approval, dict) or not all(str(approval.get(key, "")).strip() for key in ("approved_by", "approval_note", "approved_at")):
            errors.append("owner approval record is incomplete")
        approved_fingerprint = str(record.get("approved_candidate_fingerprint", ""))
        reviewers = {
            reviewer_identity(review.get("reviewer"))[1]
            for review in record.get("visual_reviews", [])
            if review.get("status") == "approved" and review.get("candidate_fingerprint") == approved_fingerprint
        }
        if len(reviewers) < 2:
            errors.append("two fingerprint-bound approved visual reviews are required")
        transfer = record.get("transfer_test", {})
        if transfer.get("status") != "passed" or transfer.get("candidate_fingerprint") != approved_fingerprint:
            errors.append("fingerprint-bound transfer approval is missing")
        evidence_path = resolve_runtime_path(str(transfer.get("evidence_record", "")))
        if sha256_file(evidence_path) != transfer.get("evidence_sha256"):
            errors.append("transfer evidence hash mismatch")
        else:
            evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            if evidence_payload.get("artifact_paths_omitted") is not True:
                errors.append("installed transfer evidence is not marked path-free")
            summary = validate_transfer_evidence(evidence_path, record, verify_artifacts=False)
            for key in (
                "benchmark_id", "target", "tested_role", "positive_cases", "positive_wins",
                "critical_regressions", "negative_form_leakage", "approved_good_for",
                "generation_policy_fingerprint",
            ):
                if transfer.get(key) != summary.get(key):
                    errors.append(f"transfer summary {key} disagrees with evidence")
            if list(record.get("good_for", [])) != summary["approved_good_for"]:
                errors.append("runtime good_for is not derived from winning transfer cases")
        provenance = record.get("provenance", {})
        if provenance.get("source_kind") == "generated":
            prompt_path = resolve_runtime_path(str(provenance.get("prompt_record", "")))
            if sha256_file(prompt_path) != provenance.get("prompt_sha256"):
                errors.append("prompt provenance hash mismatch")
    except Exception as exc:
        errors.append(str(exc))
    return errors


def validate_runtime_bank() -> list[str]:
    errors: list[str] = []
    fields, rows = load_manifest()
    required = {
        "reference_id", "image_path", "subject_family", "view", "layout_axis",
        "projection", "composition_family", "roles", "status", "execution_roles",
        "provenance_record", "provenance_sha256", "bank_version", "sha256",
    }
    missing_fields = required - set(fields)
    if missing_fields:
        errors.append(f"manifest missing columns: {sorted(missing_fields)}")
        return errors

    try:
        global_bank_version = BANK_VERSION_FILE.read_text(encoding="utf-8").strip()
        if not global_bank_version:
            errors.append("global BANK_VERSION must be non-empty")
        derived_bank_version = bank_content_version(rows)
        if not rows and "+bank." in global_bank_version:
            errors.append("empty runtime bank BANK_VERSION must use the unsuffixed base version")
        if global_bank_version != derived_bank_version:
            errors.append(
                "global BANK_VERSION disagrees with the content-derived bank version: "
                f"{global_bank_version!r} != {derived_bank_version!r}"
            )
        for row in rows:
            if row.get("bank_version", "") != global_bank_version:
                errors.append(
                    f"row bank_version disagrees with global BANK_VERSION for "
                    f"{row.get('reference_id', '<missing>')}: "
                    f"{row.get('bank_version', '')!r} != {global_bank_version!r}"
                )
    except Exception as exc:
        errors.append(f"could not validate BANK_VERSION: {exc}")

    seen_ids: set[str] = set()
    seen_runtime_assets: dict[str, str] = {}
    referenced_runtime_files: set[Path] = set()
    for row in rows:
        reference_id = row["reference_id"]
        if reference_id in seen_ids:
            errors.append(f"duplicate reference_id: {reference_id}")
        seen_ids.add(reference_id)
        try:
            require_enum("status", row["status"], ALLOWED_STATES)
            if row["status"] != "approved":
                errors.append(f"runtime row is not approved: {reference_id}")
            require_enum("view", row["view"], ALLOWED_VIEWS)
            require_enum("layout_axis", row["layout_axis"], ALLOWED_AXES)
            require_enum("projection", row["projection"], ALLOWED_PROJECTIONS)
            require_enum("composition_family", row["composition_family"], ALLOWED_COMPOSITIONS)
            roles = set(split_values(row["roles"]))
            if len(roles) != 1 or not roles <= ALLOWED_ROLES:
                errors.append(f"invalid roles for {reference_id}: {sorted(roles)}")
            execution = set(split_values(row["execution_roles"]))
            if not execution or not execution <= ALLOWED_EXECUTION_ROLES:
                errors.append(f"invalid execution_roles for {reference_id}: {sorted(execution)}")
            image_path = resolve_runtime_path(row["image_path"])
            record_path = resolve_runtime_path(row["provenance_record"])
            referenced_runtime_files.update({image_path, record_path})
            if not image_path.is_file():
                errors.append(f"missing image for {reference_id}: {image_path}")
                continue
            if not record_path.is_file():
                errors.append(f"missing record for {reference_id}: {record_path}")
                continue
            if sha256_file(record_path) != row["provenance_sha256"]:
                errors.append(f"provenance record hash mismatch for {reference_id}")
            digest = sha256_file(image_path)
            if digest != row["sha256"]:
                errors.append(f"sha256 mismatch for {reference_id}")
            previous = seen_runtime_assets.get(digest)
            if previous and previous != row["image_path"]:
                errors.append(f"duplicate physical asset for hash {digest[:12]}: {previous}, {row['image_path']}")
            seen_runtime_assets[digest] = row["image_path"]
            facts = inspect_image(image_path)
            for check in TECHNICAL_CHECKS:
                if not facts[check]:
                    errors.append(f"{reference_id} failed {check}")
            record_payload = json.loads(record_path.read_text(encoding="utf-8"))
            evidence_value = str(record_payload.get("transfer_test", {}).get("evidence_record", ""))
            if evidence_value:
                referenced_runtime_files.add(resolve_runtime_path(evidence_value))
            provenance = record_payload.get("provenance", {})
            if provenance.get("source_kind") == "generated":
                prompt_value = str(provenance.get("prompt_record", ""))
                if prompt_value:
                    referenced_runtime_files.add(resolve_runtime_path(prompt_value))
            errors.extend(f"{reference_id}: {message}" for message in validate_runtime_record(row, record_path, image_path))
        except Exception as exc:
            errors.append(f"{reference_id}: {exc}")
    for directory, label in (
        (BANK_DIR / "assets", "asset"),
        (BANK_DIR / "records", "record/evidence/prompt"),
    ):
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_dir() and not path.is_symlink():
                continue
            lexical_path = Path(os.path.abspath(path)) if path.is_symlink() else path.resolve()
            if lexical_path not in referenced_runtime_files:
                try:
                    display = lexical_path.relative_to(SKILL_DIR).as_posix()
                except ValueError:
                    display = str(lexical_path)
                errors.append(f"orphan runtime {label}: {display}")
    return errors


def stage_candidate(args: argparse.Namespace) -> Path:
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    reference_id = slug(args.reference_id)
    roles = set(split_values(args.roles))
    if len(roles) != 1 or not roles <= ALLOWED_ROLES:
        raise ValueError(f"roles must contain exactly one of {sorted(ALLOWED_ROLES)}")
    require_enum("view", args.view, ALLOWED_VIEWS)
    require_enum("layout_axis", args.layout_axis, ALLOWED_AXES)
    require_enum("projection", args.projection, ALLOWED_PROJECTIONS)
    require_enum("composition_family", args.composition_family, ALLOWED_COMPOSITIONS)
    if not 1 <= args.mass_count <= 2:
        raise ValueError("mass_count must be from 1 to 2")
    prompt_source: Path | None = None
    require_enum("source_kind", args.source_kind, ALLOWED_SOURCE_KINDS)
    if not args.model.strip() or not args.generation_timestamp.strip():
        raise ValueError("candidates require --model and --generation-timestamp")
    if args.source_kind == "generated":
        if not args.prompt_record:
            raise ValueError("generated candidates require --prompt-record")
        prompt_source = Path(args.prompt_record).expanduser().resolve()
        if not prompt_source.is_file() or prompt_source.is_symlink():
            raise FileNotFoundError(f"prompt record not found: {prompt_source}")

    workbench = Path(args.workbench).expanduser().resolve()
    skill_root = SKILL_DIR.resolve()
    if workbench == skill_root or skill_root in workbench.parents:
        raise ValueError("candidate workbench must remain outside the installable skill")
    candidate_dir = workbench / "candidates" / reference_id
    if candidate_dir.exists():
        raise FileExistsError(f"candidate already exists: {candidate_dir}")
    candidate_dir.mkdir(parents=True)
    master = candidate_dir / "master.png"
    shutil.copy2(source, master)
    prompt_name = ""
    prompt_sha = ""
    if prompt_source:
        suffix = prompt_source.suffix.lower() if prompt_source.suffix.lower() in {".json", ".txt", ".md"} else ".txt"
        prompt_name = f"prompt{suffix}"
        shutil.copy2(prompt_source, candidate_dir / prompt_name)
        prompt_sha = sha256_file(candidate_dir / prompt_name)
    facts = inspect_image(master)
    technical_pass = all(facts[key] for key in TECHNICAL_CHECKS)
    record = {
        "schema_version": 1,
        "reference_id": reference_id,
        "state": "candidate",
        "asset": "master.png",
        "sha256": sha256_file(master),
        "subject_family": args.subject_family,
        "aliases": split_values(args.aliases),
        "domain": args.domain,
        "archetype": args.archetype,
        "view": args.view,
        "layout_axis": args.layout_axis,
        "projection": args.projection,
        "composition_family": args.composition_family,
        "mass_count": args.mass_count,
        "materials": split_values(args.materials),
        "palette_roles": split_values(args.palette_roles),
        "roles": sorted(roles),
        "proposed_good_for": split_values(args.good_for),
        "good_for": [],
        "avoid_for": split_values(args.avoid_for),
        "technical": {"passed": technical_pass, "facts": facts, "checked_at": utc_now()},
        "visual_reviews": [],
        "transfer_test": {"status": "pending"},
        "owner_approval": None,
        "provenance": {
            "source_kind": args.source_kind,
            "source_sha256": sha256_file(source),
            "model": args.model,
            "prompt_record": prompt_name,
            "prompt_sha256": prompt_sha,
            "parent_reference_ids": split_values(args.parent_reference_ids),
            "generation_timestamp": args.generation_timestamp,
            "skill_version": (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip(),
            "bank_version": BANK_VERSION_FILE.read_text(encoding="utf-8").strip(),
        },
        "history": [{"state": "candidate", "at": utc_now(), "reason": "staged"}],
    }
    record_path = candidate_dir / "record.json"
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record_path


def load_candidate(path_value: str) -> tuple[Path, dict[str, object]]:
    path = Path(path_value).expanduser().resolve()
    skill_root = SKILL_DIR.resolve()
    if path == skill_root or skill_root in path.parents:
        raise ValueError("candidate records must remain outside the installable skill")
    record = json.loads(path.read_text(encoding="utf-8"))
    return path, record


def save_candidate(path: Path, record: dict[str, object]) -> None:
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def add_review(args: argparse.Namespace) -> None:
    path, record = load_candidate(args.candidate_record)
    validate_record_taxonomy(record, expected_state="candidate")
    reviewer, reviewer_key = reviewer_identity(args.reviewer)
    note = str(args.note).strip()
    if not note:
        raise ValueError("visual review note must be non-empty")
    if args.status not in {"approved", "rejected"}:
        raise ValueError("visual review status must be approved or rejected")
    reviews = list(record.get("visual_reviews", []))
    reviews = [
        review for review in reviews
        if reviewer_identity(review.get("reviewer"))[1] != reviewer_key
    ]
    reviews.append({
        "reviewer": reviewer,
        "status": args.status,
        "note": note,
        "reviewed_at": utc_now(),
        "candidate_fingerprint": candidate_fingerprint(record),
    })
    record["visual_reviews"] = reviews
    save_candidate(path, record)


def record_transfer(args: argparse.Namespace) -> None:
    path, record = load_candidate(args.candidate_record)
    validate_record_taxonomy(record, expected_state="candidate")
    evidence_source = Path(args.evidence).expanduser().resolve()
    if not evidence_source.is_file() or evidence_source.is_symlink():
        raise FileNotFoundError(f"transfer evidence not found: {evidence_source}")
    summary = validate_transfer_evidence(evidence_source, record, verify_artifacts=True)
    destination = path.parent / "transfer-evidence.json"
    evidence_payload = json.loads(evidence_source.read_text(encoding="utf-8"))
    for run in transfer_runs(evidence_payload):
        value = str(run.get("artifact", ""))
        artifact_source = resolve_contained_file(evidence_source.parent, value, "transfer artifact")
        relative = PurePosixPath(value)
        artifact_destination = path.parent / Path(*relative.parts)
        artifact_destination.parent.mkdir(parents=True, exist_ok=True)
        if artifact_destination.exists() and sha256_file(artifact_destination) != sha256_file(artifact_source):
            raise FileExistsError(f"conflicting transfer artifact: {artifact_destination}")
        shutil.copy2(artifact_source, artifact_destination)
    destination.write_text(json.dumps(evidence_payload, indent=2) + "\n", encoding="utf-8")
    record["transfer_test"] = {
        **summary,
        "note": args.note,
        "evidence_record": destination.name,
        "evidence_sha256": sha256_file(destination),
        "candidate_fingerprint": candidate_fingerprint(record),
        "recorded_at": utc_now(),
    }
    save_candidate(path, record)


def quarantine(args: argparse.Namespace) -> None:
    path, record = load_candidate(args.candidate_record)
    validate_record_taxonomy(record, expected_state="candidate")
    record["state"] = "quarantined"
    record.setdefault("history", []).append({"state": "quarantined", "at": utc_now(), "reason": args.note})
    save_candidate(path, record)


def promote(args: argparse.Namespace) -> tuple[Path, Path]:
    if not args.owner_approved:
        raise ValueError("Promotion requires the explicit --owner-approved flag")
    if not args.approved_by.strip() or not args.approval_note.strip():
        raise ValueError("Promotion requires --approved-by and --approval-note")
    record_path, record = load_candidate(args.candidate_record)
    validate_record_taxonomy(record, expected_state="candidate")
    source = resolve_contained_file(record_path.parent, str(record.get("asset", "")), "candidate asset")
    digest = sha256_file(source)
    if digest != record.get("sha256"):
        raise ValueError("Candidate asset hash changed after review")
    current_facts = inspect_image(source)
    if not all(current_facts[key] for key in TECHNICAL_CHECKS):
        raise ValueError("Candidate no longer satisfies the technical image gate")
    if not record.get("technical", {}).get("passed") or record.get("technical", {}).get("facts") != current_facts:
        raise ValueError("Candidate technical record is stale or disagrees with the current asset")
    fingerprint = candidate_fingerprint(record)
    approved_reviewers = {
        reviewer_identity(review.get("reviewer"))[1]
        for review in record.get("visual_reviews", [])
        if review.get("status") == "approved" and review.get("candidate_fingerprint") == fingerprint
    }
    if len(approved_reviewers) < 2:
        raise ValueError("Candidate needs two current, independent approved visual reviews")
    if record.get("transfer_test", {}).get("status") != "passed":
        raise ValueError("Candidate has not passed transfer testing")
    transfer = record["transfer_test"]
    if transfer.get("candidate_fingerprint") != fingerprint:
        raise ValueError("Transfer approval is stale for the current candidate")
    if transfer.get("positive_cases") != 3 or transfer.get("positive_wins", 0) < 2 or transfer.get("critical_regressions") != 0 or transfer.get("negative_form_leakage") != 0:
        raise ValueError("Candidate transfer metrics do not satisfy the promotion gate")
    evidence_source = resolve_contained_file(
        record_path.parent,
        str(transfer.get("evidence_record", "")),
        "transfer evidence",
    )
    if sha256_file(evidence_source) != transfer.get("evidence_sha256"):
        raise ValueError("Transfer evidence changed after review")
    revalidated_transfer = validate_transfer_evidence(evidence_source, record, verify_artifacts=True)
    for key in (
        "benchmark_id", "target", "tested_role", "positive_cases", "positive_wins",
        "critical_regressions", "negative_form_leakage", "approved_good_for",
        "generation_policy_fingerprint",
    ):
        if transfer.get(key) != revalidated_transfer.get(key):
            raise ValueError(f"Stored transfer summary {key} disagrees with current evidence")
    derived_good_for = list(revalidated_transfer["approved_good_for"])
    runtime_evidence_bytes = portable_transfer_evidence(evidence_source)
    runtime_evidence_sha = hashlib.sha256(runtime_evidence_bytes).hexdigest()

    prompt_source: Path | None = None
    provenance = record.get("provenance", {})
    if provenance.get("source_kind") == "generated":
        prompt_source = resolve_contained_file(
            record_path.parent,
            str(provenance.get("prompt_record", "")),
            "prompt record",
        )
        if sha256_file(prompt_source) != provenance.get("prompt_sha256"):
            raise ValueError("Prompt provenance changed after review")

    fields, rows = load_manifest()
    if "provenance_sha256" not in fields:
        raise ValueError("Runtime manifest schema is missing provenance_sha256")
    reference_id = str(record["reference_id"])
    if any(row["reference_id"] == reference_id for row in rows):
        raise ValueError(f"reference_id already exists: {reference_id}")

    existing_path = next((row["image_path"] for row in rows if row["sha256"] == digest), None)
    if existing_path:
        runtime_image_value = existing_path
        runtime_image = resolve_runtime_path(existing_path)
    else:
        runtime_image = BANK_DIR / "assets" / f"{reference_id}.png"
        runtime_image_value = runtime_image.relative_to(SKILL_DIR).as_posix()

    runtime_record = BANK_DIR / "records" / f"{reference_id}.json"
    runtime_evidence = BANK_DIR / "records" / f"{reference_id}-transfer.json"
    runtime_prompt: Path | None = None
    if prompt_source:
        prompt_suffix = prompt_source.suffix if prompt_source.suffix in {".json", ".txt", ".md"} else ".txt"
        runtime_prompt = BANK_DIR / "records" / f"{reference_id}-prompt{prompt_suffix}"
    destinations = [runtime_record, runtime_evidence]
    if not existing_path:
        destinations.append(runtime_image)
    if runtime_prompt:
        destinations.append(runtime_prompt)
    occupied = [path for path in destinations if path.exists()]
    if occupied:
        raise FileExistsError(f"Promotion destination already exists: {occupied[0]}")

    approval = {
        "approved_by": args.approved_by,
        "approval_note": args.approval_note,
        "approved_at": utc_now(),
    }
    approved_record = copy.deepcopy(record)
    approved_record["state"] = "approved"
    approved_record["good_for"] = derived_good_for
    approved_record["owner_approval"] = approval
    approved_record["approved_candidate_fingerprint"] = fingerprint
    approved_record.setdefault("history", []).append({
        "state": "approved",
        "at": approval["approved_at"],
        "reason": args.approval_note,
    })
    approved_record["asset"] = runtime_image_value
    approved_record["transfer_test"].update(revalidated_transfer)
    approved_record["transfer_test"]["evidence_record"] = runtime_evidence.relative_to(SKILL_DIR).as_posix()
    approved_record["transfer_test"]["evidence_sha256"] = runtime_evidence_sha
    if runtime_prompt:
        approved_record["provenance"]["prompt_record"] = runtime_prompt.relative_to(SKILL_DIR).as_posix()
    runtime_record_bytes = (json.dumps(approved_record, indent=2) + "\n").encode("utf-8")
    provenance_sha = hashlib.sha256(runtime_record_bytes).hexdigest()

    new_row = {
        "schema_version": "1",
        "reference_id": reference_id,
        "image_path": runtime_image_value,
        "subject_family": str(record["subject_family"]),
        "aliases": ";".join(record.get("aliases", [])),
        "domain": str(record["domain"]),
        "archetype": str(record["archetype"]),
        "view": str(record["view"]),
        "layout_axis": str(record["layout_axis"]),
        "projection": str(record["projection"]),
        "composition_family": str(record["composition_family"]),
        "mass_count": str(record["mass_count"]),
        "materials": ";".join(record.get("materials", [])),
        "palette_roles": ";".join(record.get("palette_roles", [])),
        "roles": ";".join(record.get("roles", [])),
        "good_for": ";".join(derived_good_for),
        "avoid_for": ";".join(record.get("avoid_for", [])),
        "status": "approved",
        "execution_roles": "generation_reference",
        "provenance_record": runtime_record.relative_to(SKILL_DIR).as_posix(),
        "provenance_sha256": provenance_sha,
        "spec_version": "1",
        "bank_version": "",
        "sha256": digest,
        "reviewed_at": approval["approved_at"],
        "review_note": args.approval_note,
    }
    next_rows = rows + [new_row]
    next_bank_version = bank_content_version(next_rows)
    for row in next_rows:
        row["bank_version"] = next_bank_version

    old_manifest = BANK_MANIFEST.read_bytes()
    old_version = BANK_VERSION_FILE.read_bytes()
    BANK_DIR.joinpath("assets").mkdir(parents=True, exist_ok=True)
    BANK_DIR.joinpath("records").mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    with tempfile.TemporaryDirectory(prefix=".promotion-", dir=str(BANK_DIR)) as staging_value:
        staging = Path(staging_value)
        staged_record = staging / runtime_record.name
        staged_record.write_bytes(runtime_record_bytes)
        staged_evidence = staging / runtime_evidence.name
        staged_evidence.write_bytes(runtime_evidence_bytes)
        staged_manifest = staging / "MANIFEST.csv"
        write_csv(staged_manifest, fields, next_rows)
        staged_version = staging / "BANK_VERSION"
        staged_version.write_text(next_bank_version + "\n", encoding="utf-8")
        staged_image: Path | None = None
        if not existing_path:
            staged_image = staging / runtime_image.name
            shutil.copy2(source, staged_image)
        staged_prompt: Path | None = None
        if runtime_prompt and prompt_source:
            staged_prompt = staging / runtime_prompt.name
            shutil.copy2(prompt_source, staged_prompt)

        try:
            for staged, destination in (
                (staged_image, runtime_image if not existing_path else None),
                (staged_prompt, runtime_prompt),
                (staged_evidence, runtime_evidence),
                (staged_record, runtime_record),
            ):
                if staged is None or destination is None:
                    continue
                os.replace(staged, destination)
                created.append(destination)
            os.replace(staged_manifest, BANK_MANIFEST)
            os.replace(staged_version, BANK_VERSION_FILE)
            errors = validate_runtime_bank()
            if errors:
                raise ValueError("Promoted bank failed validation: " + "; ".join(errors))
        except Exception:
            atomic_write_bytes(BANK_MANIFEST, old_manifest)
            atomic_write_bytes(BANK_VERSION_FILE, old_version)
            for path in reversed(created):
                path.unlink(missing_ok=True)
            raise
    return runtime_record, resolve_runtime_path(runtime_image_value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage, review, validate, and owner-promote UC icon references.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.set_defaults(handler=lambda _args: validate_runtime_bank())

    stage = subparsers.add_parser("stage")
    stage.add_argument("--source", required=True)
    stage.add_argument("--reference-id", required=True)
    stage.add_argument("--subject-family", required=True)
    stage.add_argument("--aliases", default="")
    stage.add_argument("--domain", required=True)
    stage.add_argument("--archetype", required=True)
    stage.add_argument("--view", required=True)
    stage.add_argument("--layout-axis", required=True)
    stage.add_argument("--projection", required=True)
    stage.add_argument("--composition-family", required=True)
    stage.add_argument("--mass-count", type=int, default=1)
    stage.add_argument("--materials", default="")
    stage.add_argument("--palette-roles", default="")
    stage.add_argument(
        "--roles",
        required=True,
        help="Exactly one tested logical role: form, material, composition, or style.",
    )
    stage.add_argument(
        "--good-for",
        default="",
        help="Proposed families only; runtime permissions are derived from winning transfer cases.",
    )
    stage.add_argument("--avoid-for", default="")
    stage.add_argument("--source-kind", choices=sorted(ALLOWED_SOURCE_KINDS), default="generated")
    stage.add_argument("--model", default="gpt-image-2")
    stage.add_argument("--prompt-record", default="")
    stage.add_argument("--parent-reference-ids", default="")
    stage.add_argument("--generation-timestamp", default="")
    stage.add_argument("--workbench", default=str(DEFAULT_WORKBENCH))
    stage.set_defaults(handler=stage_candidate)

    review = subparsers.add_parser("review")
    review.add_argument("--candidate-record", required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--status", choices=["approved", "rejected"], required=True)
    review.add_argument("--note", required=True)
    review.set_defaults(handler=add_review)

    transfer = subparsers.add_parser("transfer")
    transfer.add_argument("--candidate-record", required=True)
    transfer.add_argument("--note", required=True)
    transfer.add_argument("--evidence", required=True, help="Randomized/blind benchmark evidence JSON.")
    transfer.set_defaults(handler=record_transfer)

    quarantine_parser = subparsers.add_parser("quarantine")
    quarantine_parser.add_argument("--candidate-record", required=True)
    quarantine_parser.add_argument("--note", required=True)
    quarantine_parser.set_defaults(handler=quarantine)

    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("--candidate-record", required=True)
    promote_parser.add_argument("--owner-approved", action="store_true")
    promote_parser.add_argument("--approved-by", required=True)
    promote_parser.add_argument("--approval-note", required=True)
    promote_parser.set_defaults(handler=promote)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
        if args.command == "validate":
            errors = result
            if errors:
                print(json.dumps({"valid": False, "errors": errors}, indent=2))
                return 1
            print(json.dumps({"valid": True, "errors": []}, indent=2))
        elif result is not None:
            if isinstance(result, tuple):
                print(json.dumps({"record": str(result[0]), "image": str(result[1])}, indent=2))
            else:
                print(result)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
