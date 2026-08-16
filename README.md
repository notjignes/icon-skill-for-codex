# Icon Skill for Codex

Working repository and progress log for the `uc-icons` Codex skill.

This repository stores the unpacked Codex skill for generating, refining, and exporting Urban Company icons in the new UC tactile skeuomorphic style. It is designed specifically for Codex workflows: the skill relies on Codex skill loading, the companion `imagegen` skill, and GPT Image 2 / Image Gen behavior.

The skill is strongest when paired with visual references and a compact brief. A useful request usually includes the icon subject, the service or material cue, and any details that must remain stable, such as crop, orientation, character identity, or base-object silhouette.

## Capabilities

- Plan exact exports, controlled base edits, canonical character edits, and genuinely new objects deterministically.
- Generate new UC-style category icons from approved internal references or request-scoped user references.
- Edit existing UC icon bases while preserving composition, material finish, crop, lighting, and orientation.
- Export known service icons from bundled archive assets without unnecessary regeneration.
- Build people-centric service icons from canonical character bust bases.
- Preserve a native high-resolution master and derive a `1024x768` PNG delivery on UC Grey (Grey 10).
- Keep routine lookup and reference selection silent; reusable-bank promotion remains owner-approved.

## Use-Case Results

The examples below show the kind of object language this skill is tuned for: clean silhouettes, soft tactile materials, simplified product detail, and consistent presentation on UC Grey (Grey 10).

<table>
  <tr>
    <td align="center"><img src="examples/use-case-results/salad-bowl.jpg" width="180"><br><sub>Food and lifestyle objects</sub></td>
    <td align="center"><img src="examples/use-case-results/gift-box.jpg" width="180"><br><sub>Promotional and reward icons</sub></td>
    <td align="center"><img src="examples/use-case-results/tea-glass.jpg" width="180"><br><sub>Glass, liquid, and transparent materials</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="examples/use-case-results/candle-set.jpg" width="180"><br><sub>Grouped product sets</sub></td>
    <td align="center"><img src="examples/use-case-results/candle-single.jpg" width="180"><br><sub>Single premium objects</sub></td>
    <td align="center"><img src="examples/use-case-results/dumbbell.jpg" width="180"><br><sub>Fitness and service category objects</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="examples/use-case-results/native-locks.jpg" width="180"><br><sub>Native product-style references</sub></td>
    <td align="center"><img src="examples/use-case-results/native-ro-water-purifier.jpg" width="180"><br><sub>Appliance and device icons</sub></td>
    <td align="center"><img src="examples/use-case-results/nail-polish.jpg" width="180"><br><sub>Beauty and grooming products</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="examples/use-case-results/vacuum-cleaner.jpg" width="180"><br><sub>Home service equipment</sub></td>
    <td align="center"><img src="examples/use-case-results/paint-roller.jpg" width="180"><br><sub>Tools and repair cues</sub></td>
    <td align="center"><img src="examples/use-case-results/mens-salon-massage.jpg" width="180"><br><sub>Character bust service icons</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="examples/use-case-results/womens-salon-spa.jpg" width="180"><br><sub>Salon and spa character variants</sub></td>
    <td></td>
    <td></td>
  </tr>
</table>

## Repo Layout

```text
uc-icons/
  SKILL.md                         # Codex skill entrypoint
  agents/openai.yaml               # Codex UI metadata
  scripts/                         # resolver, planner, exporter, bank and validation tools
  references/                      # one-copy archive plus logical alias manifests

examples/use-case-results/         # repo-facing examples for logs and review
evaluation/reference-bank/         # candidates and transfer evidence; never installed
tests/                             # storage, routing, export, approval and UX regressions
```

The installable skill is the `uc-icons/` folder. Top-level files and examples are for human orientation, review, and progress tracking.

## Install

Do not overlay this version onto an older installation: an overlay leaves duplicate
base/material/character PNGs behind. Validate and atomically replace it with the
owner-gated updater instead:

```bash
python3 scripts/install_compact_skill.py --owner-approved-install
```

The updater stages and validates a complete copy, moves the old install to
`~/.codex/backups/skills/`, atomically activates the new tree, validates it again, and
restores the backup on failure. It never removes the backup automatically. Restart
Codex and confirm normal operation before deleting that backup.

## Validation

Run the full local suite and compact-package validator:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 tests/verify_legacy_pixel_equivalence.py
python3 uc-icons/scripts/validate_uc_icons.py --compact-baseline
python3 uc-icons/scripts/manage_reference_bank.py validate
```

Smoke-test archive export from a workspace:

```bash
python3 uc-icons/scripts/export_skeuo_uc_icon.py \
  --subject "native water purifier test" \
  --source "uc-icons/references/archive/PNGs_renamed/Native RO Water Purifiers (India).png" \
  --preserve-source
```

Expected output: a `1024x768` PNG in `./assets/` on UC Grey (Grey 10).

## v0.2.0-rc.1 architecture

- 73 service identities, 70 base meanings, 72 material meanings, and 11 character
  names resolve to 72 unchanged high-resolution archive masters.
- Base, material, and character alias directories contain no duplicate PNG bytes.
- The compact baseline is about 174.8 MB before new approved reference masters,
  compared with about 551.3 MB in the previous duplicate-heavy installation.
- New masters request an opaque `2048x1536` 4:3 PNG when available; smaller valid
  native results are preserved without upscaling. OpenAI documents arbitrary valid
  GPT Image 2 sizes and high-fidelity input processing in the
  [image-generation guide](https://developers.openai.com/api/docs/guides/image-generation).
- The runtime attaches at most three approved, role-distinct references and abstains
  when none is compatible. Request-scoped references take precedence and are never
  learned from automatically.
- Candidate references stay outside the installed skill. Promotion requires technical
  success, two independent visual approvals, a passed held-out transfer test with
  per-run blind ratings and derived arm means, and an explicit owner approval record.
  Each logical record tests one role; multiple
  role-specific records may reuse one master SHA/path without duplicating the PNG.

The first expansion wave and frozen confusion/transfer probes are tracked under
`evaluation/`. No Wave-1 image is approved merely because it appears in the example
gallery.

## Notes

- This is not a standalone image-generation app.
- This is not intended for direct use outside Codex.
- Do not replace GPT Image 2 / Image Gen with placeholder SVG, HTML/CSS, or other image models unless explicitly testing a fallback.
- Keep ordinary generated outputs outside this repo. Only explicitly reviewed and owner-approved masters enter the runtime bank.
- Stable merge/tag, active installed-skill replacement, and reusable-reference promotion remain owner-gated.
