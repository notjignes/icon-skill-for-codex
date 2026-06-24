#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SKILL_DIR / "references" / "base-objects"
MANIFEST = BASE_DIR / "MANIFEST.csv"

ALIASES = {
    "female": {"female", "woman", "women", "girl", "lady"},
    "male": {"male", "man", "men", "boy", "gentleman"},
    "massage": {"massage", "spa", "therapy", "therapist"},
    "table": {"table", "bed", "cot"},
    "water": {"water"},
    "ro": {"ro"},
    "purifier": {"purifier", "filter"},
    "native": {"native"},
    "chef": {"chef", "cook", "cooks"},
    "helper": {"helper", "maid", "help", "cleaner", "cleaners"},
}


def tokens(value: str) -> set[str]:
    raw = {part for part in re.split(r"[^a-z0-9]+", value.lower()) if part}
    expanded = set(raw)
    for canonical, values in ALIASES.items():
        if raw & values:
            expanded.add(canonical)
            expanded |= values
    return expanded


def row_text(row: dict[str, str]) -> str:
    return " ".join(value for value in row.values() if value)


def resolve_image_path(row: dict[str, str], filename: str) -> Path:
    image_path = row.get("image_path", "").strip()
    if image_path:
        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = SKILL_DIR / candidate
        return candidate
    return BASE_DIR / filename


def load_rows() -> list[dict[str, str]]:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Missing base-object manifest: {MANIFEST}")
    with MANIFEST.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        filename = row.get("base_file") or row.get("base_object_file")
        if not filename:
            continue
        row["base_file"] = filename
        row["path"] = str(resolve_image_path(row, filename))
        row.setdefault("canonical_for", "")
        row.setdefault("objects", "")
        row.setdefault("allowed_edits", "")
        row.setdefault("do_not_use_for", "")
        row.setdefault("type", "")
        row.setdefault("orientation", "")
    return rows


def is_human_request(query_tokens: set[str]) -> bool:
    if query_tokens & {"bed", "table", "cot", "chair", "sofa", "stool"}:
        return False
    human_terms = {
        "female",
        "woman",
        "women",
        "girl",
        "lady",
        "male",
        "man",
        "men",
        "boy",
        "helper",
        "maid",
        "chef",
        "cook",
        "cooks",
        "driver",
        "trainer",
        "guard",
        "technician",
        "salon",
        "therapist",
    }
    return bool(query_tokens & human_terms)


def score_row(row: dict[str, str], query: str, query_tokens: set[str]) -> int:
    text = row_text(row)
    candidate_tokens = tokens(text)
    score = 0

    score += len(query_tokens & candidate_tokens) * 3

    canonical_tokens = tokens(row.get("canonical_for", ""))
    object_tokens = tokens(row.get("objects", ""))
    score += len(query_tokens & canonical_tokens) * 4
    score += len(query_tokens & object_tokens) * 3

    stem = Path(row["base_file"]).stem.lower()
    if stem == query.lower().strip():
        score += 20
    if query.lower().strip() in stem:
        score += 8

    do_not_use = tokens(row.get("do_not_use_for", ""))
    if query_tokens & do_not_use:
        score -= 20

    row_type = row.get("type", "")
    if is_human_request(query_tokens):
        score += 5 if row_type == "human" else -12
        if "eyes" not in query_tokens and "open" in tokens(row["base_file"]):
            score += 4
        if "eyes" not in query_tokens and "closed" in tokens(row["base_file"]):
            score -= 4
        if query_tokens & {"female", "woman", "women", "girl", "lady"} and "male" in tokens(row["base_file"]):
            score -= 12
        if query_tokens & {"male", "man", "men", "boy"} and "female" in tokens(row["base_file"]):
            score -= 12
    elif row_type == "human":
        score -= 8

    if "pair" in tokens(row["base_file"]) and not (query_tokens & {"pair", "couple", "couples", "two"}):
        score -= 20

    return score


def force_ambiguous_family(query_tokens: set[str], candidates: list[dict[str, object]]) -> bool:
    if {"water", "purifier"} <= query_tokens and not (query_tokens & {"native", "normal", "regular", "simple", "wall", "mount", "repair"}):
        water_candidates = [
            candidate for candidate in candidates
            if {"water", "purifier"} <= tokens(str(candidate.get("canonical_for", "")) + " " + str(candidate.get("objects", "")))
        ]
        return len(water_candidates) > 1
    return False


def find_candidates(query: str, limit: int = 5) -> dict[str, object]:
    rows = [row for row in load_rows() if row.get("base_file") and Path(row["path"]).exists()]
    query_tokens = tokens(query)

    scored: list[tuple[int, dict[str, str]]] = []
    for row in rows:
        score = score_row(row, query, query_tokens)
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: (-item[0], item[1]["base_file"].lower()))
    candidates = [
        {
            "score": score,
            "base_file": row["base_file"],
            "path": row["path"],
            "type": row.get("type", ""),
            "objects": row.get("objects", ""),
            "orientation": row.get("orientation", ""),
            "allowed_edits": row.get("allowed_edits", ""),
            "canonical_for": row.get("canonical_for", ""),
        }
        for score, row in scored[:limit]
    ]

    if force_ambiguous_family(query_tokens, candidates):
        status = "ambiguous"
        candidates = [
            candidate for candidate in candidates
            if {"water", "purifier"} <= tokens(str(candidate.get("canonical_for", "")) + " " + str(candidate.get("objects", "")))
        ][:limit]
    elif not candidates:
        status = "not_found"
    elif len(candidates) == 1:
        status = "single"
    else:
        top = candidates[0]["score"]
        close = [candidate for candidate in candidates if top - candidate["score"] <= 3]
        status = "ambiguous" if len(close) > 1 else "single"
        candidates = close if status == "ambiguous" else candidates[:1]

    return {
        "query": query,
        "status": status,
        "candidates": candidates,
        "decision": (
            "ask_user_to_choose" if status == "ambiguous" else
            "use_base_image" if status == "single" else
            "no_base_found"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Find a Waterlemon base-object image deterministically.")
    parser.add_argument("--subject", required=True, help="Requested icon subject or variant.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum candidates to return.")
    args = parser.parse_args()

    print(json.dumps(find_candidates(args.subject, args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
