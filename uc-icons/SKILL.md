---
name: uc-icons
description: Generate, edit, reference-match, or export Urban Company tactile skeuomorphic 3D category icons with GPT Image 2. Use for UC Icons, Waterlemon UC icons, Skeuo-UC icons, high-resolution 4:3 icon masters, 1024x768 UC Grey deliveries, service-category objects, and character-bust service icons.
---

# UC Icons

## Runtime contract

Produce one UC icon per subject. Keep lookup, planning, base selection, reference selection, prompt construction, image attachment, validation, and export silent.

- For an exact existing service, export the canonical archive master without Image Gen.
- For a local variant, edit the selected canonical base and preserve its identity and composition.
- For a genuinely new object, generate a new high-resolution master with up to three compatible approved references.
- For a new person/character variant, edit a canonical character base. Never generate a human from scratch.
- Save generated/edited masters and deliveries in `./assets/` in the current workspace.
- Treat references supplied with the request as request-scoped. Never add them or their outputs to the reusable bank automatically.

Read `references/icon-contract.md` for the complete visual, master/export, shadow, and orientation rules. Read `references/skeuo-uc-characters.md` only for a character edit.

## User-facing behavior

Do not narrate internal work or show base/reference images unless the user asks.

For Image Gen or an image edit, send exactly one short, playful waiting line before the
tool call. Use friendly current/modern lingo, keep it concise, and make it clear that
generation is running. Do not make it rude, guilt-inducing, or distracting. For example:

> Go touch some grass 🌱 — we’re generating your icon.

The example is tone guidance, not fixed copy. Then remain silent until the result is
ready. Exact exports show no status line. Send another message only when blocked or
when the service identity is genuinely ambiguous.

The final response contains only:

- the rendered delivery image;
- its absolute path, `1024x768` PNG size, and `#f5f5f5` background;
- the high-resolution master path when generation or editing created one.

Do not mention selected references, manifests, helper scripts, or companion skills in the final response.

## Required companion

Use the system `imagegen` skill silently whenever generation or editing is required. Prefer GPT Image 2 / built-in Image Gen. Do not ask the user to invoke it separately, and do not silently substitute another model.

## Preflight planner

Resolve every request through the deterministic planner before exporting or generating:

```bash
python3 "<THIS_SKILL_DIR>/scripts/plan_icon_request.py" \
  --subject "<SUBJECT AND REQUESTED CHANGE>" \
  --max-references 3
```

For every local image supplied by the user, add one request-scoped argument:

```bash
--reference "<base|form|material|composition|style>=<ABSOLUTE_IMAGE_PATH>"
```

Planner modes:

- `exact_export`: export `base.path` with `--preserve-source`; do not call Image Gen.
- `base_edit`: use `base.path` as the edit target, not merely a style reference.
- `character_edit`: use `base.path` as the canonical character edit target and follow the character sub-spec.
- `new_generation`: attach only the returned reference paths and follow their declared roles.
- `ask_user`: ask the concise choice in `choices`; do not guess.

An empty `references` list is valid. Never add filler references.

Request-scoped references have precedence for that run but never become bank records. Routine selection uses approved internal references automatically and never asks for approval.

## Exact exports

For `exact_export`, pass the resolved canonical source directly to the exporter:

```bash
python3 "<THIS_SKILL_DIR>/scripts/export_skeuo_uc_icon.py" \
  --subject "<SUBJECT>" \
  --source "<CANONICAL_SOURCE_PATH>" \
  --preserve-source
```

Do not redraw, relight, recrop, restyle, or add props. Preserve the archive source treatment and create only the `1024x768` workspace delivery.

## Base edits

Use the planner’s base as the Image Gen edit target. Preserve:

- object or character identity;
- camera, view, layout, crop, silhouette, proportions, and optical size;
- material fidelity, lighting, source shadow treatment, background, and untouched parts.

Change only the requested local detail. If local image edit input is unavailable, stop and explain that base-preserving edit mode is unavailable; do not downgrade the base to a style reference.

Request a high-quality, opaque `2048x1536` 4:3 PNG result on `#f5f5f5`. After Image Gen returns an explicit source path, export it without `--preserve-source` so the native master and delivery are both saved.

## New object generation

Use only planner-returned references. Their roles are `form`, `material`, `composition`, or `style`; attach no more than one per needed role and no more than three total.

Request:

```text
Generate one original <SUBJECT> as a premium UC tactile skeuomorphic 3D micro-object.
Output a high-quality opaque 2048x1536 PNG in a clean 4:3 composition on exact #f5f5f5.
Use <VIEW>, <LAYOUT_AXIS>, <PROJECTION>, and <COMPOSITION_FAMILY> from the preflight.
Keep a familiar real-world silhouette, edited material realism, soft approachable bevels,
one dominant mass and at most one subordinate service cue.
No external cast, contact, drop, or floor shadow, glow, or ambient grounding pool.
Internal self-shadow, occlusion, and material shading are allowed.
No people, scene, room, tabletop, hands, readable text, logos, branding, watermark, or clutter.
Keep the full subject visible with comfortable margins and clear small-size recognition.
```

When references are attached, state each role in the prompt. Do not ask the user to approve already approved internal references.

## Character path

Use `references/characters/MANIFEST.csv` through the planner; logical character names resolve to canonical archive masters.

- Choose canonical base by gender and eye state.
- Preserve an exact existing service-character variant by editing its resolved archive master.
- Use the canonical gender + eye-state base for genuinely new or unlisted character variants.
- Preserve face family, expression, skin, hair fidelity, head scale, bust crop, pose, lighting, material finish, shadow treatment, and optical size.
- Change only requested wardrobe, headwear, hairstyle shape, treatment cue, or sanctioned accent.
- Treat an external person image as a request-scoped wardrobe/treatment/composition cue unless it is explicitly supplied as the request-scoped edit base; never use it as a likeness source.
- If gender is material to the result and absent, ask rather than guessing.

## Master and delivery export

The exporter requires an explicit source. Never search broad Codex folders for the newest PNG.

For generated/edited results:

```bash
python3 "<THIS_SKILL_DIR>/scripts/export_skeuo_uc_icon.py" \
  --subject "<SUBJECT>" \
  --source "<GENERATED_PNG_PATH>"
```

It writes:

```text
./assets/<subject>-skeuo-uc-master.png
./assets/<subject>-skeuo-uc.png
./assets/<subject>-skeuo-uc.json
```

The master preserves a valid native opaque 4:3 PNG byte-for-byte. If normalization is required, do not upscale a smaller native result. The delivery is always `1024x768` on `#f5f5f5`. The JSON record stores source, master, and delivery hashes and sizes.

## Improvement and approval mode

Enter improvement mode only when the user explicitly asks to improve, curate, add, replace, approve, promote, quarantine, or reject references.

- Stage proposed masters outside the installable skill with `scripts/manage_reference_bank.py stage`.
- Candidate and quarantined assets are never runtime-selectable.
- Test exactly one reference role per logical candidate. Separate role records may reuse one master SHA without copying the image.
- Treat staged `good_for` values as proposals; runtime transfer permissions come only from held-out cases the candidate actually wins.
- Require technical validation, two independent approved visual reviews, a passed transfer test, and explicit owner approval before `promote` succeeds.
- Store only the approved high-resolution master inside `references/reference-bank/assets/`.
- Never promote an ordinary successful output automatically.

## Batches and failure behavior

For batches, plan and generate one subject at a time while holding background, light direction, material grammar, simplification, optical scale, and camera rules consistent.

Treat the approved pose/view, camera angle, projection, and canvas placement as hard
family locks. Hold the lighting direction and softness, texture-density band, material
finish, and palette roles constant across candidates, transfer arms, and related icons.
After every generation, compare the result with the active family lock before export or
staging. If any locked attribute drifts, stop that result, discard it from evaluation,
and regenerate with an explicit targeted correction; never normalize away a pose,
camera, lighting, texture, or palette drift during export.

If GPT Image 2 / Image Gen is unavailable after applying the companion skill, say it is unavailable in the current session. Do not fabricate a placeholder or silently switch models.
