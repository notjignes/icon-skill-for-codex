# Icon Skill for Codex

Private working repo for the `uc-icons` Codex skill.

This repository stores the unpacked Codex skill used to generate, edit, optimize, and export Urban Company icons in the new UC tactile skeuomorphic style. It is intended for Codex only: the skill depends on Codex skill loading, the companion `imagegen` skill, and GPT Image 2 / Image Gen behavior.

## What It Does

- Generates new UC-style category icons from a short description and, ideally, attached image references.
- Edits existing UC icon bases while preserving composition, material finish, crop, and orientation.
- Exports known service icons from bundled archive assets without regenerating them.
- Handles people-centric service icons through canonical character bust bases.
- Normalizes final assets to `1024x768` PNG on a fixed `#f5f5f5` background.

The skill works best when the request includes:

- one or more image references,
- a short description of the desired object, service, material, or edit,
- any must-preserve details such as orientation, crop, or existing base identity.

## Repo Layout

```text
uc-icons/
  SKILL.md                         # Codex skill entrypoint
  agents/openai.yaml               # Codex UI metadata
  scripts/                         # deterministic lookup/export helpers
  references/                      # bundled style, character, and archive assets
```

The top-level repo files are for human orientation only. The installable skill is the `uc-icons/` folder.

## Install

From this repo, install the skill by copying `uc-icons/` into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R uc-icons "${CODEX_HOME:-$HOME/.codex}/skills/uc-icons"
```

Restart Codex after installing or updating the skill.

For a private GitHub install, use the Codex skill installer with credentials that can access this repo:

```bash
python3 install-skill-from-github.py --repo notjignes/icon-skill-for-codex --path uc-icons
```

## Validation

Validate the skill structure:

```bash
python3 quick_validate.py uc-icons
```

Smoke-test archive export from a workspace:

```bash
python3 uc-icons/scripts/export_skeuo_uc_icon.py \
  --subject "native water purifier test" \
  --source "uc-icons/references/archive/PNGs_renamed/Native RO Water Purifiers (India).png" \
  --preserve-source
```

Expected output: a `1024x768` PNG in `./assets/` with background `#f5f5f5`.

## Notes

- This is not a standalone image-generation app.
- This is not meant for direct use outside Codex.
- Do not replace GPT Image 2 / Image Gen with placeholder SVG, HTML/CSS, or other image models unless explicitly testing a fallback.
- Keep generated output assets outside this repo unless they are deliberately being promoted into the skill archive.
- This repo is private and intended as a personal log/update source before later migration into a shared team repo.
