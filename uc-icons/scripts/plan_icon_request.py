#!/usr/bin/env python3
"""Deterministic identity-gated request planner for UC Icons."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Iterable

from PIL import Image

from asset_registry import (
    SafeResolver,
    load_base_records,
    load_character_records,
    load_runtime_reference_records,
    load_service_records,
    split_values,
)


DEFAULT_SKILL_DIR = Path(__file__).resolve().parents[1]
REFERENCE_ROLES = {"base", "form", "material", "composition", "style"}
AUTO_REFERENCE_ROLES = {"form", "material", "composition", "style"}
GENERATION_MARKERS = {
    "from scratch", "new design", "redesign", "fresh design", "new icon", "original icon",
}
EDIT_MARKERS = {
    "edit", "change", "replace", "remove", "add", "swap", "recolor", "recolour",
    "make the", "make it", "turn the", "with a", "with an", "wearing", "holding",
}
EDIT_ACTION_LEADS = {
    "edit", "change", "replace", "remove", "add", "swap", "recolor", "recolour",
    "make", "turn", "with", "without", "wearing", "holding",
}
COLOR_WORDS = {
    "black", "white", "grey", "gray", "blue", "red", "green", "yellow", "orange",
    "pink", "purple", "beige", "brown", "gold", "golden", "silver", "charcoal",
}
CHARACTER_TERMS = {
    "maid", "helper", "domestic help", "chef", "cook", "security guard", "guard",
    "technician", "driver", "trainer", "nurse", "attendant", "stylist", "therapist",
    "salon client", "spa client", "service worker", "character", "woman", "female",
    "man", "male", "cleaner", "cleaning professional", "house help", "housekeeper",
    "domestic worker", "avatar", "person", "human", "bust", "instahelp", "insta help",
}
NON_HUMAN_CLEANER_PHRASES = {
    "vacuum cleaner", "steam cleaner", "carpet cleaner", "window cleaner",
    "pressure cleaner", "floor cleaner", "air cleaner", "pipe cleaner",
}
FEMALE_TERMS = {"female", "woman", "women", "girl", "lady", "maid"}
MALE_TERMS = {"male", "man", "men", "boy", "gentleman"}
CLOSED_EYE_TERMS = {"eyes closed", "closed eyes", "spa", "massage", "pamper", "serene", "resting"}


def normalize(value: str) -> str:
    value = value.lower().replace("&", " and ").replace("’", "'")
    value = re.sub(r"'s\b", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def phrase_in(text: str, phrase: str) -> bool:
    text_norm = normalize(text)
    phrase_norm = normalize(phrase)
    return bool(phrase_norm) and f" {phrase_norm} " in f" {text_norm} "


def longest_phrase_match(text: str, phrases: Iterable[str]) -> str | None:
    candidates = {normalize(phrase): phrase for phrase in phrases if normalize(phrase)}
    for normalized in sorted(candidates, key=lambda item: (-len(item.split()), -len(item), item)):
        if phrase_in(text, normalized):
            return candidates[normalized]
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_version(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def request_core(subject: str) -> str:
    words = normalize(subject).split()
    removable = {
        "please", "use", "uc", "icons", "icon", "create", "generate", "render", "export",
        "show", "give", "me", "for", "a", "an", "the", "category", "service",
    }
    while words and words[0] in removable:
        words.pop(0)
    while words and words[-1] in removable:
        words.pop()
    return " ".join(words)


def has_explicit_generation(subject: str) -> bool:
    return any(phrase_in(subject, marker) for marker in GENERATION_MARKERS)


def has_edit_action(subject: str) -> bool:
    return any(phrase_in(subject, marker) for marker in EDIT_MARKERS)


def requested_colors(subject: str) -> set[str]:
    return set(normalize(subject).split()) & COLOR_WORDS


def color_requires_edit(subject: str, record: dict[str, object]) -> bool:
    requested = requested_colors(subject)
    if not requested:
        return False
    existing = set(normalize(str(record.get("colors", ""))).split()) & COLOR_WORDS
    return not requested <= existing


def service_aliases(record: dict[str, object]) -> list[str]:
    result = [str(record.get("service_identity", ""))]
    cleaned: list[str] = []
    for item in result:
        item = Path(item).stem
        item = re.sub(r"\s+\d+$", "", item)
        if normalize(item):
            cleaned.append(item)
        item = re.sub(r"\s*\[[^]]+\]\s*", " ", item)
        if normalize(item):
            cleaned.append(item)
        without_market = re.sub(
            r"\s*\((?:dubai|india|singapore)\)\s*$",
            " ",
            item,
            flags=re.I,
        )
        if normalize(without_market):
            cleaned.append(without_market)
    return cleaned


def find_exact_service(subject: str, services: list[dict[str, object]]) -> dict[str, object] | None:
    return find_service_identity(subject, services, allow_contained=False)


def find_service_identity(
    subject: str,
    services: list[dict[str, object]],
    allow_contained: bool,
) -> dict[str, object] | None:
    core = normalize(request_core(subject))
    candidates: list[tuple[int, int, int, str, dict[str, object]]] = []
    for record in services:
        identity_norm = normalize(str(record.get("service_identity", "")))
        for alias in service_aliases(record):
            alias_norm = normalize(alias)
            exact = core == alias_norm
            contained = (
                allow_contained
                and phrase_in(core, alias_norm)
                and identity_context_is_safe(core, alias_norm, record)
            )
            if exact or contained:
                candidates.append((
                    2 if core == identity_norm else int(exact),
                    len(alias_norm.split()),
                    len(alias_norm),
                    alias_norm,
                    record,
                ))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3], str(item[4]["asset_id"])))
    return candidates[0][4]


def base_identity_phrases(record: dict[str, object]) -> list[str]:
    phrases = split_values(str(record.get("canonical_for", "")))
    objects = str(record.get("objects", "")).strip()
    if objects:
        phrases.append(objects.replace("-", " "))
    return [phrase for phrase in phrases if normalize(phrase)]


SAFE_IDENTITY_CONTEXT = {
    "a", "an", "the", "please", "icon", "service", "category", "for", "of", "to",
    "with", "without", "in", "on", "at", "from", "as", "and", "or", "it", "this",
    "make", "create", "generate", "render", "export", "show", "use", "try", "using",
    "edit", "change", "replace", "remove", "add", "swap", "recolor", "recolour",
    "colour", "color", "coloured", "colored", "tone", "shade", "material", "finish",
    "style", "reference", "look",
    "front", "side", "profile", "upright", "vertical", "horizontal", "view",
    "slight", "top", "open", "angle", "perspective", "near", "orthographic",
    "palette", "neutral", "transparent",
    "pair", "paired", "couple", "couples", "duo", "two", "single", "one", "set",
    "new", "fresh", "original", "design", "scratch", "different", "minor", "only",
    "same", "keep", "preserve", "standalone",
}


def is_human_base(record: dict[str, object]) -> bool:
    return normalize(str(record.get("type", ""))) == "human"


def identity_context_is_safe(subject: str, matched_phrase: str, record: dict[str, object]) -> bool:
    subject_norm = normalize(subject)
    match_norm = normalize(matched_phrase)
    identity_pattern = rf"(?<![a-z0-9]){re.escape(match_norm)}(?![a-z0-9])"
    matches = list(re.finditer(identity_pattern, subject_norm))
    if not matches:
        return False
    # Repeated identity words inside an explicit instruction (for example
    # "AMC — turn the AMC blue") are context, not a second object.
    remainder = re.sub(identity_pattern, " ", subject_norm)
    safe = set(SAFE_IDENTITY_CONTEXT) | COLOR_WORDS
    for field in ("materials", "colors", "allowed_edits", "market"):
        safe.update(normalize(str(record.get(field, ""))).split())
    if set(normalize(remainder).split()) <= safe:
        return True

    # Preserve an established service identity when the user appends or prepends
    # an explicit action clause. Arbitrary noun suffixes remain unsafe: "blue
    # stove cover" is a new object, while "Stove — remove the logo" is an edit.
    def explicit_clause(tokens: list[str]) -> bool:
        while tokens and tokens[0] in {"please", "kindly", "can", "could", "would", "you"}:
            tokens = tokens[1:]
        return bool(tokens) and tokens[0] in EDIT_ACTION_LEADS

    # Validate every segment around repeated aliases. Looking only before the first and
    # after the last match would let a second object hide between them, as in
    # "AMC box truck AMC blue". A repeated identity inside an action clause remains
    # valid: "AMC turn the AMC blue" produces an explicit middle segment.
    segments: list[list[str]] = []
    cursor = 0
    for match in matches:
        segments.append(normalize(subject_norm[cursor:match.start()]).split())
        cursor = match.end()
    segments.append(normalize(subject_norm[cursor:]).split())
    return all(
        not segment or set(segment) <= safe or explicit_clause(segment)
        for segment in segments
    )


def base_variant_score(subject: str, record: dict[str, object]) -> int:
    query_tokens = set(normalize(subject).split())
    record_colors = set(normalize(str(record.get("colors", ""))).split())
    requested_colors = query_tokens & COLOR_WORDS
    score = 0
    if requested_colors:
        score += 100 if requested_colors & record_colors else -100

    identity = normalize(" ".join([
        str(record.get("base_file", "")),
        str(record.get("objects", "")),
        str(record.get("canonical_for", "")),
    ]))
    wants_pair = bool(query_tokens & {"pair", "paired", "couple", "couples", "duo", "two"})
    is_pair = bool(set(identity.split()) & {"pair", "paired", "couple", "couples", "tables", "two"})
    if wants_pair:
        score += 120 if is_pair else -120
    elif is_pair:
        score -= 10
    return score


def choose_base_variant(
    subject: str,
    candidates: list[tuple[int, int, str, dict[str, object]]],
) -> dict[str, object] | None:
    if not candidates:
        return None
    ranked = [
        (words, chars, base_variant_score(subject, record), phrase, record)
        for words, chars, phrase, record in candidates
    ]
    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3], str(item[4]["asset_id"])))
    return ranked[0][4]


def ranked_base_variants(
    subject: str,
    candidates: list[tuple[int, int, str, dict[str, object]]],
) -> list[tuple[int, dict[str, object]]]:
    if not candidates:
        return []
    best_words = max(item[0] for item in candidates)
    best_chars = max(item[1] for item in candidates if item[0] == best_words)
    ranked = [
        (base_variant_score(subject, record), phrase, str(record["asset_id"]), record)
        for words, chars, phrase, record in candidates
        if words == best_words and chars == best_chars
    ]
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [(score, record) for score, _, _, record in ranked]


def base_choice_label(record: dict[str, object]) -> str:
    stem = Path(str(record.get("base_file", record.get("asset_id", "legacy base")))).stem
    return re.sub(r"[()]", " ", stem).replace("  ", " ").strip()


def direct_base_candidates(
    subject: str,
    bases: list[dict[str, object]],
) -> list[tuple[int, int, str, dict[str, object]]]:
    scored: list[tuple[int, int, str, dict[str, object]]] = []
    core = request_core(subject)
    for record in bases:
        if is_human_base(record):
            continue
        match = longest_phrase_match(core, base_identity_phrases(record))
        if not match or not identity_context_is_safe(core, match, record):
            continue
        match_norm = normalize(match)
        scored.append((len(match_norm.split()), len(match_norm), match_norm, record))
    return scored


def find_base(subject: str, bases: list[dict[str, object]]) -> dict[str, object] | None:
    return choose_base_variant(subject, direct_base_candidates(subject, bases))


def find_family_base(
    subject: str,
    classification: dict[str, object] | None,
    bases: list[dict[str, object]],
) -> dict[str, object] | None:
    """Select a controlled variant only after the canonical ontology family is known."""
    return choose_base_variant(subject, family_base_candidates(subject, classification, bases))


def family_base_candidates(
    subject: str,
    classification: dict[str, object] | None,
    bases: list[dict[str, object]],
) -> list[tuple[int, int, str, dict[str, object]]]:
    if not classification:
        return []
    aliases = [str(item) for item in classification.get("aliases", [])]
    subject_match = longest_phrase_match(subject, aliases)
    if not subject_match:
        return []
    normalized_subject_match = normalize(subject_match)
    candidates: list[tuple[int, int, str, dict[str, object]]] = []
    for record in bases:
        if is_human_base(record):
            continue
        identity_text = " ; ".join(base_identity_phrases(record))
        if not longest_phrase_match(identity_text, aliases):
            continue
        if not identity_context_is_safe(subject, subject_match, record):
            continue
        candidates.append((
            len(normalized_subject_match.split()),
            len(normalized_subject_match),
            normalized_subject_match,
            record,
        ))
    return candidates


def resolve_base_variants(
    subject: str,
    classification: dict[str, object] | None,
    bases: list[dict[str, object]],
) -> list[tuple[int, dict[str, object]]]:
    candidates = direct_base_candidates(subject, bases)
    if not candidates:
        candidates = family_base_candidates(subject, classification, bases)
    return ranked_base_variants(subject, candidates)


def generic_family_needs_variant_choice(
    subject: str,
    classification: dict[str, object] | None,
    record: dict[str, object],
) -> bool:
    """Do not silently turn a generic family request into one specific legacy variant."""

    if not classification:
        return False
    core = normalize(request_core(subject))
    aliases = {normalize(str(alias)) for alias in classification.get("aliases", [])}
    if core not in aliases:
        return False
    return core not in {normalize(phrase) for phrase in base_identity_phrases(record)}


def load_ontology(skill_dir: Path) -> dict[str, object]:
    path = skill_dir / "references" / "routing" / "ontology.json"
    return json.loads(path.read_text(encoding="utf-8"))


def classify_subject(subject: str, ontology: dict[str, object]) -> dict[str, object] | None:
    matches: list[tuple[int, int, str, dict[str, object]]] = []
    for family in ontology.get("families", []):
        aliases = [str(alias) for alias in family.get("aliases", [])]
        match = longest_phrase_match(subject, aliases)
        if match:
            normalized = normalize(match)
            family_with_match = dict(family)
            identity_metadata = {
                "materials": " ".join(str(item) for item in family.get("materials", [])),
                "colors": "",
                "allowed_edits": "",
            }
            matching_aliases = [alias for alias in aliases if phrase_in(subject, alias)]
            family_with_match["_identity_safe"] = any(
                identity_context_is_safe(subject, alias, identity_metadata)
                for alias in matching_aliases
            )
            matches.append((len(normalized.split()), len(normalized), normalized, family_with_match))
    if not matches:
        return None
    matches.sort(key=lambda item: (-item[0], -item[1], item[2], str(item[3]["family"])))
    return dict(matches[0][3])


def controlled_variant(
    subject: str,
    ontology: dict[str, object],
    services: list[dict[str, object]],
    bases: list[dict[str, object]],
) -> dict[str, object] | None:
    for group in ontology.get("ambiguity_groups", []):
        trigger_matches = [
            str(trigger) for trigger in group.get("triggers", [])
            if phrase_in(subject, str(trigger))
        ]
        if not trigger_matches:
            continue
        selector_context = {
            "materials": "",
            "colors": "",
            "allowed_edits": " ".join(
                str(selector)
                for variant in group.get("variants", [])
                for selector in variant.get("selectors", [])
            ),
        }
        if not any(
            identity_context_is_safe(subject, trigger, selector_context)
            for trigger in trigger_matches
        ):
            continue
        selected: list[dict[str, object]] = []
        for variant in group.get("variants", []):
            if longest_phrase_match(subject, variant.get("selectors", [])):
                selected.append(variant)
        if len(selected) == 1:
            service_file = selected[0]["service_file"]
            service = next((item for item in services if item.get("service_file") == service_file), None)
            base = next(
                (
                    item for item in bases
                    if Path(str(item.get("image_path", ""))).name == service_file
                    or Path(str(item.get("path", ""))).name == service_file
                ),
                None,
            )
            return {"status": "selected", "group": group, "variant": selected[0], "service": service, "base": base}
        if len(selected) > 1:
            return {"status": "ambiguous", "group": group, "variants": selected}
        return {"status": "ambiguous", "group": group, "variants": group.get("variants", [])}
    return None


def character_intent(
    subject: str,
    classification: dict[str, object] | None = None,
) -> bool:
    probe = normalize(subject)
    if classification:
        matching_aliases = {
            normalize(str(alias))
            for alias in classification.get("aliases", [])
            if phrase_in(probe, str(alias))
        }
        for alias in sorted(matching_aliases, key=lambda item: (-len(item.split()), -len(item), item)):
            pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
            probe = normalize(re.sub(pattern, " ", probe))
    if any(phrase_in(probe, phrase) for phrase in NON_HUMAN_CLEANER_PHRASES):
        return False
    return character_gender(probe) is not None or any(
        phrase_in(probe, term) for term in CHARACTER_TERMS
    )


def generic_cleaner_ambiguity(subject: str) -> bool:
    return request_core(subject) in {"cleaner", "cleaners", "cleaning"}


def character_gender(subject: str) -> str | None:
    female = any(phrase_in(subject, term) for term in FEMALE_TERMS)
    male = any(phrase_in(subject, term) for term in MALE_TERMS)
    if female == male:
        return None
    return "female" if female else "male"


def generic_avatar_eye_state_ambiguity(subject: str) -> bool:
    core = normalize(subject)
    identifies_base = any(
        phrase_in(core, phrase)
        for phrase in ("avatar base", "female base", "woman base", "male base", "man base")
    )
    states_eye = any(phrase_in(core, phrase) for phrase in ("eyes open", "eye open", "eyes closed", "eye closed"))
    return identifies_base and not states_eye


def choose_character(subject: str, records: list[dict[str, object]]) -> dict[str, object] | None:
    gender = character_gender(subject)
    specific: list[tuple[int, int, dict[str, object]]] = []
    for record in records:
        if record.get("canonical_for") == "character-base":
            continue
        if gender and record.get("gender") != gender:
            continue
        phrases = [str(record.get("display_name", "")), *record.get("aliases", [])]
        match = longest_phrase_match(subject, phrases)
        if match and identity_context_is_safe(subject, match, record):
            specific.append((len(normalize(match).split()), len(normalize(match)), record))
    if specific:
        specific.sort(key=lambda item: (-item[0], -item[1], str(item[2]["asset_id"])))
        return specific[0][2]
    if not gender:
        return None
    eye_state = "closed" if any(phrase_in(subject, term) for term in CLOSED_EYE_TERMS) else "open"
    return next(
        (
            record for record in records
            if record.get("canonical_for") == "character-base"
            and record.get("gender") == gender
            and record.get("eye_state") == eye_state
        ),
        None,
    )


def exact_character_identity(subject: str, record: dict[str, object]) -> bool:
    core = normalize(request_core(subject))
    phrases = [str(record.get("display_name", "")), *record.get("aliases", [])]
    return any(core == normalize(phrase) for phrase in phrases)


def parse_provided_references(values: Iterable[str] | None) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen_roles: set[str] = set()
    seen_hashes: set[str] = set()
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"Reference must use role=/absolute/path: {value!r}")
        role, raw_path = value.split("=", 1)
        role = role.strip().lower()
        if role not in REFERENCE_ROLES:
            raise ValueError(f"Reference role must be one of {sorted(REFERENCE_ROLES)}: {role!r}")
        if role in seen_roles:
            raise ValueError(f"Only one request-scoped reference is allowed per role: {role}")
        supplied_path = Path(raw_path).expanduser()
        if not supplied_path.is_absolute():
            raise ValueError(f"Request-scoped reference must be an absolute path: {raw_path!r}")
        if supplied_path.is_symlink():
            raise ValueError(f"Request-scoped reference must not be a symlink: {supplied_path}")
        path = supplied_path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Request-scoped reference not found: {path}")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    image.load()
        except (
            OSError,
            SyntaxError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise ValueError(f"Request-scoped reference is not a decodable image: {path}") from exc
        digest = sha256_file(path)
        if digest in seen_hashes:
            continue
        seen_roles.add(role)
        seen_hashes.add(digest)
        result.append({
            "role": role,
            "source": "request_scoped",
            "asset_id": None,
            "path": str(path),
            "sha256": digest,
            "request_scoped": True,
            "bank_eligible": False,
            "reason": "explicit user-provided reference",
        })
    return result


def compatible_runtime_references(
    classification: dict[str, object] | None,
    records: list[dict[str, object]],
    excluded_roles: set[str],
) -> list[dict[str, object]]:
    if not classification or classification.get("_identity_safe") is not True:
        return []
    ranked: list[tuple[int, str, str, dict[str, object]]] = []
    target_materials = {normalize(item) for item in classification.get("materials", [])}
    family = normalize(str(classification.get("family", "")))
    archetype = normalize(str(classification.get("archetype", "")))
    domain = normalize(str(classification.get("domain", "")))
    for record in records:
        record_family = normalize(str(record.get("subject_family", "")))
        record_archetype = normalize(str(record.get("archetype", "")))
        record_domain = normalize(str(record.get("domain", "")))
        record_view = normalize(str(record.get("view", "")))
        record_axis = normalize(str(record.get("layout_axis", "")))
        record_projection = normalize(str(record.get("projection", "")))
        record_composition = normalize(str(record.get("composition_family", "")))
        try:
            record_mass = int(record.get("mass_count", 0))
        except (TypeError, ValueError):
            record_mass = 0
        target_mass = int(classification.get("mass_count", 0) or 0)
        good_for = {normalize(value) for value in split_values(str(record.get("good_for", "")))}
        avoid_for = {normalize(value) for value in split_values(str(record.get("avoid_for", "")))}
        if {family, archetype, domain} & avoid_for:
            continue
        explicit_transfer = family in good_for
        record_materials = {normalize(item) for item in split_values(str(record.get("materials", "")))}
        material_overlap = bool(target_materials & record_materials)
        for role in record.get("reference_roles", []):
            if role not in AUTO_REFERENCE_ROLES or role in excluded_roles:
                continue
            if role == "form":
                compatible = record_family == family or explicit_transfer
            elif role == "composition":
                compatible = (
                    (record_family == family or explicit_transfer)
                    and record_view == normalize(str(classification.get("view", "")))
                    and record_axis == normalize(str(classification.get("layout_axis", "")))
                    and record_projection == normalize(str(classification.get("projection", "")))
                    and record_composition == normalize(str(classification.get("composition_family", "")))
                    and record_mass == target_mass
                )
            elif role == "material":
                compatible = material_overlap and (record_family == family or explicit_transfer)
            else:  # style
                compatible = record_family == family or explicit_transfer
            if not compatible:
                continue
            score = 0
            score += 100 if record_family == family else 0
            score += 45 if record_archetype == archetype else 0
            score += 20 if record_domain == domain else 0
            score += 10 if record.get("view") == classification.get("view") else 0
            score += 8 if record.get("layout_axis") == classification.get("layout_axis") else 0
            score += 7 if record.get("projection") == classification.get("projection") else 0
            score += 6 if record.get("composition_family") == classification.get("composition_family") else 0
            score += 5 if record_mass == target_mass else 0
            score += 30 if explicit_transfer else 0
            score += len(target_materials & record_materials) * 3
            ranked.append((score, role, str(record.get("asset_id")), record))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [
        {
            "role": role,
            "source": "approved_reference_bank",
            "asset_id": record["asset_id"],
            "path": record["path"],
            "sha256": record["sha256"],
            "request_scoped": False,
            "bank_eligible": True,
            "reason": "approved role-compatible reference",
            "score": score,
        }
        for score, role, _, record in ranked
    ]


def matching_legacy_form_reference(
    subject: str,
    classification: dict[str, object] | None,
    bases: list[dict[str, object]],
    excluded_roles: set[str],
) -> list[dict[str, object]]:
    if "form" in excluded_roles:
        return []
    ranked = resolve_base_variants(subject, classification, bases)
    if (
        not ranked
        or (len(ranked) > 1 and ranked[0][0] == ranked[1][0])
        or generic_family_needs_variant_choice(subject, classification, ranked[0][1])
    ):
        return []
    base = ranked[0][1]
    return [{
        "role": "form",
        "source": "approved_legacy_base",
        "asset_id": base["asset_id"],
        "path": base["path"],
        "sha256": base["sha256"],
        "request_scoped": False,
        "bank_eligible": True,
        "reason": "canonical identity match",
        "score": 200,
    }]


def select_references(
    subject: str,
    classification: dict[str, object] | None,
    provided: list[dict[str, object]],
    bases: list[dict[str, object]],
    runtime_records: list[dict[str, object]],
    max_references: int,
    allow_legacy_form: bool,
) -> list[dict[str, object]]:
    selected = [record for record in provided if record["role"] != "base"]
    roles = {str(record["role"]) for record in selected}
    candidates: list[dict[str, object]] = []
    if allow_legacy_form:
        candidates.extend(matching_legacy_form_reference(subject, classification, bases, roles))
    candidates.extend(compatible_runtime_references(classification, runtime_records, roles))
    for candidate in candidates:
        role = str(candidate["role"])
        if len(selected) >= max_references:
            break
        if role in roles:
            continue
        if any(candidate["path"] == item["path"] or candidate["sha256"] == item["sha256"] for item in selected):
            continue
        selected.append(candidate)
        roles.add(role)
    return selected[:max_references]


def public_asset(record: dict[str, object], kind: str) -> dict[str, object]:
    return {
        "asset_id": record.get("asset_id"),
        "kind": kind,
        "path": record.get("path"),
        "relative_path": record.get("relative_path"),
        "sha256": record.get("sha256"),
        "service_file": record.get("service_file"),
        "base_file": record.get("base_file"),
        "allowed_edits": record.get("allowed_edits", ""),
    }


def visual_defaults(classification: dict[str, object] | None) -> dict[str, object]:
    classification = classification or {}
    return {
        "family": classification.get("family"),
        "domain": classification.get("domain", "unknown"),
        "archetype": classification.get("archetype", "compact-object"),
        "view": classification.get("view", "front"),
        "layout_axis": classification.get("layout_axis", "compact"),
        "projection": classification.get("projection", "near-orthographic"),
        "composition_family": classification.get("composition_family", "single"),
        "mass_count": classification.get("mass_count", 1),
        "materials": classification.get("materials", []),
    }


def generation_prompt(subject: str, visual: dict[str, object], references: list[dict[str, object]]) -> str:
    role_clause = ""
    if references:
        role_clause = " Use each supplied image only for its declared role: " + ", ".join(
            f"{item['role']}={item['asset_id'] or 'request-scoped image'}" for item in references
        ) + "."
    return (
        f"Generate one original {subject} as a premium UC tactile skeuomorphic 3D micro-object. "
        "Output a high-quality opaque 2048x1536 PNG in a clean 4:3 composition on exact #f5f5f5. "
        f"Use {visual['view']} view, {visual['layout_axis']} layout, {visual['projection']} projection, "
        f"and {visual['composition_family']} composition with {visual['mass_count']} intended mass(es). "
        "Keep a familiar real-world silhouette, edited material realism, soft approachable bevels, and clear "
        "small-size recognition. No external cast, contact, drop, or floor shadow, glow, or ambient grounding "
        "pool; internal self-shadow, occlusion, and material shading are allowed. No scene, room, tabletop, "
        "people, hands, readable text, logos, branding, watermark, or clutter. Keep the full subject visible "
        f"with comfortable margins.{role_clause}"
    )


def plan_request(
    subject: str,
    provided_references: Iterable[str] | None = None,
    max_references: int = 3,
    skill_dir: Path | str | None = None,
) -> dict[str, object]:
    if not subject or not normalize(subject):
        raise ValueError("subject is required")
    if max_references < 0 or max_references > 3:
        raise ValueError("max_references must be between 0 and 3")
    skill_root = Path(skill_dir or DEFAULT_SKILL_DIR).expanduser().resolve()
    resolver = SafeResolver(skill_root)
    services = load_service_records(resolver=resolver)
    bases = load_base_records(resolver=resolver)
    characters = load_character_records(resolver=resolver)
    # Keep logical rows through role matching. A single canonical image may safely own
    # multiple reviewed logical roles; path/SHA dedupe happens only at attachment time.
    runtime_records = load_runtime_reference_records(resolver=resolver)
    ontology = load_ontology(skill_root)
    supplied = parse_provided_references(provided_references)
    classification = classify_subject(subject, ontology)
    visual = visual_defaults(classification)

    plan: dict[str, object] = {
        "schema_version": 1,
        "skill_version": read_version(skill_root / "VERSION"),
        "bank_version": read_version(skill_root / "references" / "BANK_VERSION"),
        "subject": subject,
        "normalized_subject": normalize(subject),
        "mode": None,
        "reason": None,
        **visual,
        "base": None,
        "choices": [],
        "requested_changes": subject if has_edit_action(subject) or supplied else None,
        "references": [],
        "coverage_gaps": [],
        "prompt": None,
    }

    base_reference = next((item for item in supplied if item["role"] == "base"), None)
    if base_reference:
        plan.update({
            "mode": "base_edit",
            "reason": "explicit request-scoped base reference",
            "base": {
                "asset_id": None,
                "kind": "request_scoped",
                "path": base_reference["path"],
                "relative_path": None,
                "sha256": base_reference["sha256"],
                "allowed_edits": "request-scoped edit target",
            },
            "references": [item for item in supplied if item["role"] != "base"][:max_references],
        })
        return plan

    force_generation = has_explicit_generation(subject)
    reference_intent = bool(supplied)
    edit_intent = (has_edit_action(subject) or reference_intent) and not force_generation

    variant = controlled_variant(subject, ontology, services, bases)
    if variant and not force_generation:
        if variant["status"] == "ambiguous":
            choices = [
                {"label": Path(str(item["service_file"])).stem, "service_file": item["service_file"]}
                for item in variant.get("variants", [])
            ]
            plan.update({
                "mode": "ask_user",
                "reason": f"controlled ambiguity: {variant['group']['group']}",
                "choices": choices,
            })
            return plan
        if edit_intent and (variant.get("base") or variant.get("service")):
            target = variant.get("base") or variant["service"]
            plan.update({
                "mode": "base_edit",
                "reason": f"controlled variant base: {variant['variant']['variant']}",
                "base": public_asset(target, "legacy_base" if variant.get("base") else "service_archive"),
                "references": supplied[:max_references],
            })
            return plan
        if variant.get("service"):
            plan.update({
                "mode": "exact_export",
                "reason": f"controlled service variant: {variant['variant']['variant']}",
                "base": public_asset(variant["service"], "service_archive"),
            })
            return plan

    exact = find_service_identity(
        subject,
        services,
        allow_contained=edit_intent or bool(requested_colors(subject)),
    ) if not force_generation else None
    if exact:
        service_edit = edit_intent or color_requires_edit(subject, exact)
        if service_edit:
            human_service = normalize(str(exact.get("type", ""))) == "human"
            plan.update({
                "mode": "character_edit" if human_service else "base_edit",
                "reason": "exact service identity with an explicit edit/reference cue",
                "base": public_asset(exact, "service_archive"),
                "references": supplied[:max_references],
                "requested_changes": subject,
            })
            return plan
        else:
            plan.update({
                "mode": "exact_export",
                "reason": "exact service identity",
                "base": public_asset(exact, "service_archive"),
            })
            return plan

    if generic_cleaner_ambiguity(subject) and not force_generation:
        plan.update({
            "mode": "ask_user",
            "reason": "cleaner can mean a person or a cleaning object",
            "choices": [
                {"label": "cleaning professional", "kind": "character"},
                {"label": "cleaning machine or tool", "kind": "object"},
            ],
        })
        return plan

    matched_character = choose_character(subject, characters)
    matched_service_character = (
        matched_character
        if matched_character and matched_character.get("canonical_for") != "character-base"
        else None
    )
    if matched_service_character and not edit_intent and (
        not requested_colors(subject) or exact_character_identity(subject, matched_service_character)
    ):
        plan.update({
            "mode": "exact_export",
            "reason": "exact canonical service-character identity",
            "base": public_asset(matched_service_character, "character_service"),
        })
        return plan
    if character_intent(subject, classification) or matched_character:
        gender = character_gender(subject)
        if gender and generic_avatar_eye_state_ambiguity(subject):
            eye_choices = []
            for eye_state in ("open", "closed"):
                character_id = f"base-{gender}-eyes-{eye_state}"
                character_record = next(
                    record for record in characters if record.get("asset_id") == character_id
                )
                eye_choices.append({
                    "label": f"Avatar base - {gender} (eyes {eye_state})",
                    "character_id": character_id,
                    "sha256": character_record["sha256"],
                })
            plan.update({
                "mode": "ask_user",
                "reason": "canonical avatar base requires an eye-state choice",
                "choices": eye_choices,
            })
            return plan
        character = matched_character
        if not gender and not character:
            plan.update({
                "mode": "ask_user",
                "reason": "character gender is material to canonical base selection",
                "choices": [
                    {"label": "female character", "character_id": "base-female-eyes-open"},
                    {"label": "male character", "character_id": "base-male-eyes-open"},
                ],
            })
            return plan
        if not character:
            raise RuntimeError(f"No canonical {gender} character base resolved")
        character_kind = "character_service" if matched_service_character else "character_base"
        plan.update({
            "mode": "character_edit",
            "reason": "canonical service-character edit" if matched_service_character else "canonical character base identity",
            "base": public_asset(character, character_kind),
            "references": supplied[:max_references],
            "requested_changes": subject,
        })
        return plan

    if not force_generation:
        ranked_bases = resolve_base_variants(subject, classification, bases)
        if ranked_bases:
            if len(ranked_bases) > 1 and ranked_bases[0][0] == ranked_bases[1][0]:
                top_score = ranked_bases[0][0]
                plan.update({
                    "mode": "ask_user",
                    "reason": "multiple canonical base variants require a selector",
                    "choices": [
                        {
                            "label": base_choice_label(record),
                            "asset_id": record.get("asset_id"),
                            "sha256": record.get("sha256"),
                        }
                        for score, record in ranked_bases
                        if score == top_score
                    ],
                })
                return plan
            base = ranked_bases[0][1]
            if generic_family_needs_variant_choice(subject, classification, base):
                plan.update({
                    "mode": "ask_user",
                    "reason": "generic family has only a specific legacy variant",
                    "choices": [
                        {
                            "label": base_choice_label(base),
                            "asset_id": base.get("asset_id"),
                            "sha256": base.get("sha256"),
                        },
                        {
                            "label": f"new design from scratch: {classification.get('family', 'object')}",
                            "kind": "new_generation",
                        },
                    ],
                })
                return plan
            base_edit = edit_intent or color_requires_edit(subject, base)
            plan.update({
                "mode": "base_edit" if base_edit else "exact_export",
                "reason": "canonical base-family edit" if base_edit else "exact canonical base identity",
                "base": public_asset(base, "legacy_base"),
                "references": supplied[:max_references],
                "requested_changes": subject if base_edit else None,
            })
            return plan

    references = select_references(
        subject,
        classification,
        supplied,
        bases,
        runtime_records,
        max_references,
        allow_legacy_form=force_generation,
    )
    available_candidates: list[dict[str, object]] = []
    if force_generation:
        available_candidates.extend(matching_legacy_form_reference(subject, classification, bases, set()))
    available_candidates.extend(compatible_runtime_references(classification, runtime_records, set()))
    available_approved_roles = {str(item["role"]) for item in available_candidates}
    missing_approved_roles = sorted(AUTO_REFERENCE_ROLES - available_approved_roles)
    coverage_gap = {
        "family": visual["family"],
        "domain": visual["domain"],
        "archetype": visual["archetype"],
        "view": visual["view"],
        "layout_axis": visual["layout_axis"],
        "projection": visual["projection"],
        "composition_family": visual["composition_family"],
        "mass_count": visual["mass_count"],
        "materials": visual["materials"],
        "missing_approved_roles": missing_approved_roles,
    }
    plan.update({
        "mode": "new_generation",
        "reason": "new subject with compatible approved references" if references else "new subject; no compatible approved references",
        "references": references,
        "coverage_gaps": [coverage_gap] if missing_approved_roles else [],
        "prompt": generation_prompt(subject, visual, references),
    })
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a UC icon request deterministically.")
    parser.add_argument("--subject", required=True)
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Request-scoped role=/absolute/path (base, form, material, composition, style).",
    )
    parser.add_argument("--max-references", type=int, default=3)
    parser.add_argument("--skill-dir", default=str(DEFAULT_SKILL_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        result = plan_request(
            args.subject,
            provided_references=args.reference,
            max_references=args.max_references,
            skill_dir=args.skill_dir,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
