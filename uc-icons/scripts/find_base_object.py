#!/usr/bin/env python3
"""Compatibility wrapper around plan_icon_request.py for legacy callers."""

from __future__ import annotations

import argparse
import json

from plan_icon_request import plan_request


def _candidate(base: dict[str, object]) -> dict[str, object]:
    return {
        "score": 100,
        "asset_id": base.get("asset_id"),
        "base_file": base.get("base_file") or base.get("service_file"),
        "path": base.get("path"),
        "sha256": base.get("sha256"),
        "type": base.get("kind"),
        "objects": "",
        "orientation": "",
        "allowed_edits": base.get("allowed_edits", ""),
        "canonical_for": base.get("asset_id"),
    }


def find_candidates(query: str, limit: int = 5) -> dict[str, object]:
    plan = plan_request(query, max_references=min(max(limit, 0), 3))
    if plan["mode"] == "ask_user":
        return {
            "query": query,
            "status": "ambiguous",
            "candidates": plan.get("choices", [])[:limit],
            "decision": "ask_user_to_choose",
            "planner": plan,
        }
    if plan["mode"] in {"base_edit", "character_edit", "exact_export"} and plan.get("base"):
        return {
            "query": query,
            "status": "single",
            "candidates": [_candidate(plan["base"])],
            "decision": "use_base_image",
            "planner": plan,
        }
    return {
        "query": query,
        "status": "not_found",
        "candidates": [],
        "decision": "no_base_found",
        "planner": plan,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Find a UC icon base through the deterministic planner.")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(find_candidates(args.subject, args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
