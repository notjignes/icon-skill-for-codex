#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
NEW_REF_DIR = SKILL_DIR / "references" / "new-object-references"
NEW_REF_MANIFEST = NEW_REF_DIR / "MANIFEST.csv"
BASE_DIR = SKILL_DIR / "references" / "base-objects"
BASE_MANIFEST = BASE_DIR / "MANIFEST.csv"
MATERIAL_DIR = SKILL_DIR / "references" / "archive" / "PNGs_material_index"
MATERIAL_MANIFEST = MATERIAL_DIR / "MANIFEST.csv"

ALIASES = {
    "water": {"water"},
    "ro": {"ro"},
    "purifier": {"purifier", "filter"},
    "massage": {"massage", "spa", "therapy"},
    "table": {"table", "bed", "cot"},
    "chair": {"chair", "seat", "armchair", "sofa"},
    "cleaning": {"cleaning", "cleaner", "cleaners"},
    "tool": {"tool", "tools", "drill", "wrench", "screwdriver"},
    "appliance": {"appliance", "machine", "repair"},
    "lamp": {"lamp", "light", "lights", "lighting", "bulb"},
    "vehicle": {"vehicle", "van", "transport", "transportation", "truck", "car", "bus"},
}

STYLE_ANCHORS = [
    "Armchair (beige).png",
    "Split AC (white).png",
    "Toolbox with wrench.png",
    "Massage table (pink).png",
    "RO water purifier.png",
]

WIDE_OBJECT_TERMS = {
    "van", "truck", "car", "bus", "vehicle", "transport", "transportation",
    "bed", "table", "cot", "sofa", "couch", "bench", "cabinet", "dresser",
    "shelf", "curtain", "curtains", "railing", "rail", "balustrade", "stretcher",
}

TALL_OBJECT_TERMS = {
    "lamp", "fridge", "refrigerator", "wardrobe", "geyser", "heater", "tower",
    "purifier", "cooler",
}

FRONT_BOX_OBJECT_TERMS = {
    "box", "gift", "present", "cube", "basket", "bucket", "caddy", "stove",
    "microwave", "washer", "washing",
}


def tokens(value: str) -> set[str]:
    raw = {part for part in re.split(r"[^a-z0-9]+", value.lower()) if part}
    expanded = set(raw)
    for canonical, values in ALIASES.items():
        if raw & values:
            expanded.add(canonical)
            expanded |= values
    return expanded


def read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_image_path(row: dict[str, str], folder: Path, filename: str) -> Path:
    image_path = row.get("image_path", "").strip()
    if image_path:
        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = SKILL_DIR / candidate
        return candidate
    return folder / filename


def add_reference(
    refs: list[dict[str, str]],
    source: str,
    path: Path,
    row: dict[str, str],
    filename_key: str,
) -> None:
    filename = row.get(filename_key, "")
    if not filename:
        return
    ref_path = resolve_image_path(row, path, filename)
    if not ref_path.exists():
        return
    refs.append(
        {
            "source": source,
            "file": filename,
            "path": str(ref_path),
            "type": row.get("type", ""),
            "objects": row.get("objects", ""),
            "materials": row.get("materials", ""),
            "colors": row.get("colors", ""),
            "orientation": row.get("orientation", ""),
            "style_role": row.get("style_role", "style-texture"),
            "good_for": row.get("good_for", row.get("canonical_for", "")),
            "avoid_for": row.get("avoid_for", row.get("do_not_use_for", "")),
            "notes": row.get("notes", ""),
        }
    )


def load_references() -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for row in read_manifest(NEW_REF_MANIFEST):
        add_reference(refs, "new-object-references", NEW_REF_DIR, row, "reference_file")
    for row in read_manifest(BASE_MANIFEST):
        add_reference(refs, "base-objects", BASE_DIR, row, "base_file")
    for row in read_manifest(MATERIAL_MANIFEST):
        add_reference(refs, "material-index", MATERIAL_DIR, row, "material_index_file")
    return refs


def score(ref: dict[str, str], query_tokens: set[str], query: str) -> int:
    text = " ".join(ref.values())
    ref_tokens = tokens(text)
    score = len(query_tokens & ref_tokens) * 4

    object_tokens = tokens(ref.get("objects", ""))
    material_tokens = tokens(ref.get("materials", ""))
    good_tokens = tokens(ref.get("good_for", ""))
    avoid_tokens = tokens(ref.get("avoid_for", ""))

    score += len(query_tokens & object_tokens) * 7
    score += len(query_tokens & material_tokens) * 2
    score += len(query_tokens & good_tokens) * 4

    stem = Path(ref["file"]).stem.lower()
    if query.lower().strip() == stem:
        score += 30
    if query.lower().strip() in stem:
        score += 12
    if query_tokens & avoid_tokens:
        score -= 20

    ref_orientation = ref.get("orientation", "")
    desired_orientation = classify_orientation(query_tokens)
    if desired_orientation == ref_orientation:
        score += 12
    elif desired_orientation == "side-horizontal" and ref_orientation != "side-horizontal":
        score -= 10
    elif desired_orientation == "front-near-orthographic" and ref_orientation == "side-horizontal":
        score -= 50

    ref_type = ref.get("type", "")
    if query_tokens & {"van", "truck", "car", "bus", "vehicle", "transport", "transportation"}:
        score += 20 if object_tokens & {"van", "truck", "car", "bus", "vehicle"} else -8

    if ref["source"] == "new-object-references":
        score += 6
    elif ref["source"] == "base-objects":
        score += 3

    return score


def classify_orientation(query_tokens: set[str]) -> str:
    if query_tokens & WIDE_OBJECT_TERMS:
        return "side-horizontal"
    if query_tokens & TALL_OBJECT_TERMS:
        return "front-near-orthographic"
    if query_tokens & FRONT_BOX_OBJECT_TERMS:
        return "front-near-orthographic"
    return "front-near-orthographic"


def orientation_prompt(orientation: str) -> str:
    if orientation == "side-horizontal":
        return (
            "side-horizontal straight profile, full width visible, long axis perfectly horizontal, "
            "no 3/4 front view, no angled perspective, no top-down view"
        )
    return "straight-on front view, no 3/4 view, no angled perspective, no top-down view"


def find_references(subject: str, max_refs: int) -> dict[str, object]:
    query_tokens = tokens(subject)
    desired_orientation = classify_orientation(query_tokens)
    scored = []
    for ref in load_references():
        ref_score = score(ref, query_tokens, subject)
        if ref_score >= 5:
            scored.append((ref_score, ref))
    scored.sort(key=lambda item: (-item[0], item[1]["source"], item[1]["file"].lower()))

    references = [
        {"score": ref_score, **ref}
        for ref_score, ref in scored[:max_refs]
    ]

    if not references:
        anchor_refs = [ref for ref in load_references() if ref["file"] in STYLE_ANCHORS]
        anchor_refs.sort(key=lambda ref: STYLE_ANCHORS.index(ref["file"]))
        references = [
            {"score": 0, **ref}
            for ref in anchor_refs[:max_refs]
        ]
        mode = "style_reference_set"
    elif references[0]["score"] >= 30:
        mode = "closest_product_reference"
        references = references[:1]
    else:
        mode = "style_reference_set"

    return {
        "subject": subject,
        "mode": mode,
        "orientation": desired_orientation,
        "prompt": (
            f"Generate a {subject} in this style. "
            f"{orientation_prompt(desired_orientation)}, fixed #f5f5f5 background, "
            "no cast shadow, no drop shadow, no contact shadow, no floor shadow."
        ),
        "references": references,
        "reference_count": len(references),
        "instruction": (
            "Attach references silently if the tool path supports local reference images. "
            "Do not preview references in chat. If local references cannot be attached, "
            "use the prompt plus manifest-derived style notes only."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Find references for new UC icon object generation.")
    parser.add_argument("--subject", required=True, help="New object subject.")
    parser.add_argument("--max", type=int, default=5, help="Maximum references to return.")
    args = parser.parse_args()
    print(json.dumps(find_references(args.subject, args.max), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
