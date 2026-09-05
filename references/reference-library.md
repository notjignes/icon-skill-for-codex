# UC Icons reference library

Use this guide only during library maintenance or deliberate reference intake. Ordinary icon requests run the planner; they do not scan, validate, resize or reindex the whole bank.

## Sources and identity

The service archive contains the 72 existing unique masters. Base and material manifests refer to those exact files using skill-relative `image_path`; do not recreate duplicate image folders. Eleven character compatibility paths remain intentionally available. `asset_id` and `sha256` identify the same bytes across aliases. Never replace an existing master to update tags or improve a render.

Existing archive evidence is marked `existing_curated`. This preserves its historical status; it does not imply new visual review. Legacy material tags are annotations, not proof of visual quality. Unknown metadata stays unknown. No material or composition evidence may be borrowed from SKU/Visual Director or unrelated workspaces.

## Roles and allowed transfer

| Role | Allowed transfer |
|---|---|
| `service_asset` | Exact unchanged service icon |
| `editable_base` | Object/character identity and preserved composition |
| `form_reference` | Shape and functional parts |
| `material_reference` | Surface, finish, texture density and highlight response |
| `composition_reference` | Camera, framing and visual-mass balance |

One approved image can have multiple roles separated by semicolons. Approval for form does not grant permission to transfer photographic style, materials or composition. An external product photograph defaults to form-only. Negative examples stay out of positive image attachments; capture what to avoid in annotations.

## Selected-reference intake

Accept an image the user deliberately supplies or selects, or a candidate generated in an explicitly requested library-expansion test. Generated test candidates remain `pending` until the user selects the concrete image and its intended roles. Do not scrape websites or harvest incidental outputs automatically.

1. Inspect that selected image and establish what the user wants it to teach. Preserve the original file unchanged. Check its SHA-256 against existing masters before copying; use a canonical alias when identical.
2. Add a row in `new-object-references/MANIFEST.csv`, initially `pending`. Set a relative `image_path`, hash and content-derived `asset_id`; include the original source location in `provenance_source`. New files belong in this folder, not the immutable service archive.
3. Record `object_family` and semicolon-separated `identity_aliases` for true equivalent names. Do not call sofas and office chairs synonyms. `materials`/`material_tags` describe substances; `finish_tags` describe finish. Use precise observations, not invented visual measurements.
4. Set `source_role` and `approved_for` to the intended transfer only. Capture exclusions in semicolon-separated `avoid_for` phrases. Label the verified `orientation` and optional `composition_family`; leave unknown values explicit. Keep notes short and evidence-based.
5. Present the concrete image and annotations for the user's selection/approval during intake. Existing explicit approval for that image and role is sufficient. Only then set `approval_status=approved`. Rejected and pending entries never participate in selection or teach identity aliases.
6. Validate the package. Confirm the new reference helps a held-out subject before broadening its use. Record the subject, selected roles, user feedback and whether it reduced retries; do not promote one successful output into a universal rule.

Required identity/path/state fields are checked by the validator. Keep the CSV header even when the bank has no rows. Existing legacy fields remain supported for compatibility.

## Composition options

| Recipe | Use |
|---|---|
| `front` | Compact or tall front-readable subjects |
| `wide-side` | Full-width, level side silhouettes |
| `slight-top` | Open/flat-top subjects needing limited top visibility |
| `three-quarter` | Explicitly requested controlled perspective |
| `crossed-pair` | Two front-readable tools arranged as one icon |

These are text recipes until selected imagery teaches them. They never override a preserved base view implicitly. Character busts retain the canonical crop by default; explicit framing changes remain user-directed.

## First expansion and evaluation

Start with 12–18 user-selected exemplars that cover useful gaps: glass, ceramic/enamel, metal finishes, rubber/silicone, textiles/leather and stone/plaster, across the composition recipes above. These are candidate priorities, not confirmed absences. Reuse one image across roles when approved instead of increasing attachment count.

Default runtime selection is one form reference plus one complementary material/composition reference; a single file may supply multiple approved roles. Partial coverage must remain visible in the planner's gaps. Do not attach more images merely to fill a quota.

Preserve masters for export and editing. Smaller reference copies remain an optional experiment: validate visual fidelity and generation latency before introducing them. Fewer bytes alone do not establish faster or better renders.

After modifications:

```bash
python3 "<SKILL_DIR>/scripts/validate_reference_bank.py"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "<SKILL_DIR>/tests" -v
```

Compare routing, first-pass user approval, retries and total time on the same export/edit/new-generation subjects. Separate local preparation/export timing from image-generation latency. Publish only measured improvements.
