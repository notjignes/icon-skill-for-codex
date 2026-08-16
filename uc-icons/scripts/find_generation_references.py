#!/usr/bin/env python3
"""Compatibility wrapper for identity-gated generation-reference selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from plan_icon_request import plan_request


def legacy_orientation(plan: dict[str, object]) -> str:
    if plan.get("view") == "side" and plan.get("layout_axis") == "horizontal":
        return "side-horizontal"
    if plan.get("view") == "slight-top":
        return "front-slight-top"
    return "front-near-orthographic"


def find_references(subject: str, max_refs: int = 3) -> dict[str, object]:
    maximum = min(max(max_refs, 0), 3)
    # This legacy entrypoint is explicitly for generation, so preserve canonical bases
    # only as role-labelled form references instead of routing to edit mode.
    plan = plan_request(f"new design from scratch: {subject}", max_references=maximum)
    references = [
        {
            "score": item.get("score", 0),
            "source": item.get("source"),
            "file": Path(str(item["path"])).name,
            "path": item["path"],
            "sha256": item["sha256"],
            "role": item["role"],
            "asset_id": item.get("asset_id"),
            "good_for": item.get("reason", ""),
        }
        for item in plan.get("references", [])
    ]
    if not references:
        mode = "no_reference"
    elif references[0].get("role") == "form":
        mode = "closest_product_reference"
    else:
        mode = "style_reference_set"
    return {
        "subject": subject,
        "mode": mode,
        "orientation": legacy_orientation(plan),
        "view": plan.get("view"),
        "layout_axis": plan.get("layout_axis"),
        "projection": plan.get("projection"),
        "composition_family": plan.get("composition_family"),
        "prompt": plan.get("prompt"),
        "references": references,
        "reference_count": len(references),
        "instruction": "Attach only these role-labelled references; an empty list means generate reference-free.",
        "planner": plan,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Find approved references for new UC icon generation.")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--max", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(find_references(args.subject, args.max), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
