#!/usr/bin/env python3
"""Atomically replace the installed uc-icons skill after complete validation.

This updater never overlays an existing install. The previous installation is retained
outside the active skills directory until the owner removes it explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "uc-icons"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Skill packages may not contain links: {path}")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(root).as_posix()] = sha256_file(path)
    return result


def run_validation(skill_dir: Path) -> None:
    validator = skill_dir / "scripts" / "validate_uc_icons.py"
    if not validator.is_file():
        raise FileNotFoundError(f"Missing validator: {validator}")
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(validator), "--skill-dir", str(skill_dir), "--compact-baseline"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=environment,
    )
    if completed.returncode:
        raise RuntimeError(f"Validation failed for {skill_dir}:\n{completed.stdout}")


def ensure_safe_roots(source: Path, install_root: Path, backup_root: Path) -> None:
    source = source.resolve()
    install_root = install_root.resolve()
    backup_root = backup_root.resolve()
    if source.name != "uc-icons" or not (source / "SKILL.md").is_file():
        raise ValueError(f"Source must be a uc-icons skill directory: {source}")
    if install_root == Path("/") or backup_root == Path("/"):
        raise ValueError("Refusing to use a filesystem root as an install or backup root")

    def overlaps(left: Path, right: Path) -> bool:
        return left == right or left in right.parents or right in left.parents

    if overlaps(source, install_root):
        raise ValueError("Source and install roots must not contain one another")
    if overlaps(source, backup_root):
        raise ValueError("Source and backup roots must not contain one another")
    if overlaps(install_root, backup_root):
        raise ValueError("Backup root must be outside the active skills directory")


def atomic_install(source: Path, install_root: Path, backup_root: Path) -> dict[str, object]:
    source = source.resolve()
    install_root = install_root.expanduser().resolve()
    backup_root = backup_root.expanduser().resolve()
    ensure_safe_roots(source, install_root, backup_root)

    install_root.mkdir(parents=True, exist_ok=True)
    backup_root.mkdir(parents=True, exist_ok=True)
    if install_root.stat().st_dev != backup_root.stat().st_dev:
        raise ValueError("Install and backup roots must be on the same filesystem for atomic rollback")
    target = install_root / "uc-icons"
    token = uuid.uuid4().hex[:12]
    staged = install_root / f".uc-icons.install-{token}"
    failed = backup_root / f"uc-icons-failed-{token}"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_root / f"uc-icons-{timestamp}-{token}"

    if staged.exists() or failed.exists() or backup.exists():
        raise FileExistsError("Generated staging or backup path already exists")
    if target.exists() and target.is_symlink():
        raise ValueError(f"Refusing to replace a symlinked installation: {target}")

    run_validation(source)
    source_inventory = inventory(source)
    source_bytes = sum((source / path).stat().st_size for path in source_inventory)
    free_bytes = shutil.disk_usage(install_root).free
    if free_bytes < source_bytes * 2:
        raise OSError(f"Insufficient free space to stage safely: need at least {source_bytes * 2} bytes")

    shutil.copytree(
        source,
        staged,
        copy_function=shutil.copy2,
        symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    if inventory(staged) != source_inventory:
        shutil.rmtree(staged)
        raise RuntimeError("Staged tree does not match the source inventory")
    run_validation(staged)

    previous_moved = False
    installed_moved = False
    try:
        if target.exists():
            os.replace(target, backup)
            previous_moved = True
        os.replace(staged, target)
        installed_moved = True
        run_validation(target)
        if inventory(target) != source_inventory:
            raise RuntimeError("Installed tree does not match the source inventory")
    except Exception:
        if installed_moved and target.exists():
            os.replace(target, failed)
        elif staged.exists():
            shutil.rmtree(staged)
        if previous_moved and backup.exists():
            os.replace(backup, target)
        raise

    return {
        "installed": str(target),
        "backup": str(backup) if previous_moved else None,
        "backup_retained": previous_moved,
        "source_files": len(source_inventory),
        "source_bytes": source_bytes,
        "version": (target / "VERSION").read_text(encoding="utf-8").strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and atomically install the compact uc-icons skill.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--install-root", default=str(Path.home() / ".codex" / "skills"))
    parser.add_argument("--backup-root", default=str(Path.home() / ".codex" / "backups" / "skills"))
    parser.add_argument(
        "--owner-approved-install",
        action="store_true",
        help="Required acknowledgement; active installed-skill replacement is owner-gated.",
    )
    args = parser.parse_args()
    if not args.owner_approved_install:
        parser.error("active installation requires --owner-approved-install")
    try:
        result = atomic_install(Path(args.source), Path(args.install_root), Path(args.backup_root))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
