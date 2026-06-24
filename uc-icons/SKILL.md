---
name: uc-icons
description: Generate UC tactile skeuomorphic 3D category icons for the Urban Company services marketplace using GPT Image 2 / Image Gen. Use when the user asks to create, render, regenerate, edit, export, or batch-generate UC icons, Waterlemon UC icons, Skeuo-UC icons, fixed-background 1024x768 PNG icons, or icons from a subject such as "office chair", "basin mixer tap", "power drill", or an object plus a simple service cue.
---

# UC Icons

## Required Companion Skill

This skill requires the system `imagegen` skill only when raster generation is needed. When `uc-icons` must create a new render, use `imagegen` silently and automatically as an internal dependency:

- Do not ask the user to invoke `imagegen` separately.
- Do not announce that you are reading or applying `imagegen`, `skill-creator`, character guides, manifests, or reference archives. Keep those setup steps internal.
- Prefer the built-in Image Gen tool path described by `imagegen`.
- Use GPT Image 2 / built-in Image Gen only when a new render is required.
- Treat the generated Waterlemon icon as a project-bound asset, so the final PNG must be exported into `./assets/`.
- If the callable Image Gen tool is not already exposed in the current turn, follow the `imagegen` skill's tool-discovery or fallback guidance before declaring generation unavailable.
- Only mention this companion skill to the user if generation is blocked or if they ask about implementation details.

## User-Facing Updates

- Keep archive lookup, skill loading, manifest parsing, base-image selection, reference selection, tool calls, prompt construction, and image/reference attachment silent.
- While working, show at most one concise status line for generation/edit/export. Prefer no intermediate narration when the task can complete in one pass.
- Do not narrate internal references, selected archive files, or companion-skill usage unless the user asks or action is blocked.
- Do not preview or display reference/base images in chat unless the user explicitly asks.
- In the final response, show the generated/exported image and validation details only: path, size, mode, and background.

## Core Contract

Generate, edit, or export one Waterlemon UC icon per requested subject, then save the final PNG into `./assets/` in the current working directory. If a matching service/archive asset already exists and the user asks for the same asset, treat that PNG as the base image and export it directly; do not use Image Gen, do not edit it, and do not treat it merely as a style reference. If the user asks for a small variant of an existing asset, use the matching PNG as the edit target/base image and preserve its composition. Use GPT Image 2 / Image Gen from scratch only for new icon requests with no suitable base asset, or when the user explicitly asks for a new design.

Hard requirements:

- Output exactly `1024x768` PNG, matching the 4:3 reference archive format.
- Use a fixed `#f5f5f5` background for every icon. For new object generation, do not add cast shadows, drop shadows, contact shadows, floor shadows, or glow below the icon; keep the object cleanly grounded by composition and lighting only. Preserve existing shadows only for exact archive exports or base-image edits unless the user asks to remove them.
- Bake the fixed `#f5f5f5` background silently during export for every asset, including exact archive exports, generated icons, edits, and batches. Do not ask the user to choose or confirm the background unless they explicitly request a different mode.
- Do not generate, request, validate, or repair transparency unless the user explicitly asks for a transparent variant.
- Render a single centered, premium tactile 3D micro-object. For new icons without a base image, default to straight front-facing unless a selected base/reference family clearly uses another orientation. For base-image edits, preserve the base image orientation exactly.
- For wide/long objects, use a side-horizontal straight profile with the long axis level across the 4:3 canvas. Do not use 3/4 front, angled perspective, or top-down views for wide objects.
- Avoid scenes, rooms, tabletops, hands, people, readable text, copied logos, branding, watermarks, barcodes, and clutter.
- Keep the full subject visible with comfortable 4:3 icon margins.
- Use no more than two visual masses for object plus service-cue combinations.
- Exception: for people-centric service categories (maid/helper, salon, spa, massage, security guard, technician, driver, trainer, and similar male/female service workers or clients), render a single stylised character bust instead of an object, following the character sub-spec.

For the full source brief, read `references/skeuo-uc-brief.md` only when you need the detailed style language or shared rules.

## Reference Archives

Use bundled PNGs as source assets first, edit bases second, and visual references only for genuinely new icon generation. Resolve these paths relative to the folder containing this `SKILL.md`:

- Service-name archive: `references/archive/PNGs_renamed/`
- Optional base-object archive: `references/base-objects/` if present. Use this for canonical editable object bases supplied by the user, such as massage bed without towel, appliance shell, or furniture variants. Some shareable packages omit duplicate PNG copies from this folder; in that case, use each manifest row's `image_path` to resolve the canonical bundled PNG.
- Base-object manifest: `references/base-objects/MANIFEST.csv`. Prefer this manifest over filename intuition for base-object selection. It records base file, object tokens, type, materials, colors, orientation, canonical use cases, allowed edits, exclusions, notes, and optional `image_path` aliases to canonical PNGs.
- New-object reference archive: `references/new-object-references/` if present. Use this for product/object references intended only for new object generation.
- New-object reference manifest: `references/new-object-references/MANIFEST.csv`. It may contain `reference_file`, `type`, `objects`, `materials`, `colors`, `orientation`, `style_role`, `good_for`, `avoid_for`, and `notes`.
- Material-index archive: `references/archive/PNGs_material_index/`. Some shareable packages omit duplicate PNG copies from this folder; in that case, use each manifest row's `image_path` to resolve the canonical bundled PNG.
- Structured manifests: `MANIFEST.csv` in both folders. Prefer the manifest over filename parsing when available; it contains `service_file`, `material_index_file`, `type`, `materials`, `objects`, `colors`, and optional `image_path` aliases to canonical PNGs.

Reference handling rules:

1. Keep archive lookup and reference-image selection silent. Do not preview, display, or narrate the selected archive image in chat unless the user explicitly asks to see references.
2. If the requested asset already exists in `PNGs_renamed/`, `references/base-objects/`, or a manifest `image_path` as an exact match and the user did not request changes, use that PNG as the final base image. Export it with `--preserve-source`; only resize to `1024x768` if needed. Do not send it through Image Gen, do not redraw it, do not tweak material treatment, crop, proportions, lighting, contact shadow, background, or object identity, and do not add props.
3. If more than one exact or clear near service match exists and the user's wording does not choose one, ask the user to pick the intended type before exporting or generating. Example: for `water purifier`, ask whether they want `Water purifier repair` / normal RO or `Native RO Water Purifiers (India)` / Native RO. If the user says `native`, `Native RO`, or a specific service name, use that exact service asset without asking.
4. If the request is a small variant of an existing service/base-object asset, use the closest PNG as the edit target/base image, not as a style reference. Small variants include recolor, remove one prop, add one simple accessory, swap one visible garment/tool, or other local changes where the same core object or character should remain. Preserve the base image's camera angle, orientation, crop, optical size, silhouette, proportions, lighting, shadow, material fidelity, and untouched parts. Change only the requested detail.
5. If the request is similar to an existing service icon but not identical, prefer the closest service/base-object PNG from `PNGs_renamed/`, `references/base-objects/`, or a manifest `image_path` as the base image only when it is acceptable to reuse the same object identity. If reusing that asset would misrepresent the requested subject, treat the request as new generation instead of editing the existing asset.
6. If the request is new, use `PNGs_material_index/MANIFEST.csv` to choose the closest material/form reference: parse the target into likely `type`, `materials`, `objects`, and `colors`; filter first by `type`; then rank by material and object token overlap. Use these references only for material treatment, texture density, edge softness, lighting, rendering fidelity, and broad orientation family while generating a new subject. Do not use material-index references to alter an existing service/base asset.
7. If a prompt or prompt-like note exists beside a matching archive item, read it silently and use it as additional context only for new generation or explicit base-image edits. For existing unchanged assets, the PNG itself is the source of truth.
8. Keep the existing Waterlemon rules above material-index references when generating new icons: no clutter, no readable text/logos, fixed `#f5f5f5` background, no transparency work by default, and no extra focal masses beyond the allowed object/service-cue constraints.

## Base-Object Lookup

Before any base-object edit or new generation, run the deterministic lookup script:

```bash
python3 "<THIS_SKILL_DIR>/scripts/find_base_object.py" --subject "<SUBJECT AND REQUESTED CHANGE>"
```

Use its JSON result as a hard preflight:

- `decision: "use_base_image"`: use the returned `path` as the edit target/base image. Do not use material-index references for that icon unless the user asks for a new design.
- `decision: "ask_user_to_choose"`: ask the user to choose among the returned candidates. Do not guess.
- `decision: "no_base_found"`: only then consider material-index references and the new-generation prompt.

Examples:

- `water purifier` must ask between `RO water purifier.png` and `Native RO water purifier.png`.
- `native RO water purifier` must use `Native RO water purifier.png`.
- `spa for women massage bed beige remove towel` must use `Massage table (pink).png` as a base edit and preserve the side-horizontal composition.
- `female chef` must use `Woman face (eyes open).png` as a human base edit.

Internal preflight shape:

```json
{
  "mode": "export_existing | base_edit | new_generation | ask_user",
  "base_path": "<resolved PNG path or empty>",
  "requested_change": "<short edit/new asset summary>",
  "must_preserve": "orientation, crop, proportions, lighting, shadow, material fidelity, and untouched parts",
  "prompt_template": "export | base-image-edit | new-generation"
}
```

Do not proceed to Image Gen until this preflight is resolved.

## New Object References

Use this path only for non-human object icons when there is no suitable exact export or base-image edit. Do not use it for human/character icons.

Before new object generation, run:

```bash
python3 "<THIS_SKILL_DIR>/scripts/find_generation_references.py" --subject "<SUBJECT>" --max 5
```

Use its JSON result as the new-object generation plan:

- `mode: "closest_product_reference"`: attach the single returned reference silently as the closest product/object reference.
- `mode: "style_reference_set"`: attach up to five returned references silently for texture, material, lighting, orientation, and icon style.
- `mode: "no_reference"`: generate with the compact prompt and fixed UC icon requirements only.

When the current Image Gen path supports local reference images, attach the selected references silently. If local reference attachment is not available without visible previews, do not preview them in chat; use the manifest-derived reference roles and notes in the prompt instead.

For new object generation, use this compact prompt shape:

```text
Generate a <SUBJECT> in this style.
1024x768 PNG, fixed #f5f5f5 background, single centered premium tactile 3D object, <ORIENTATION RULE>, no cast shadow, no drop shadow, no contact shadow, no floor shadow, no text, no logos, no people, no scene clutter.
```

If references are attached, do not repeat a long style brief. Let the attached closest reference or reference set carry the style, texture, lighting, orientation, and optical size.

## Orientation Rules

Decide orientation before prompting and treat it as a hard requirement:

- **Wide/long objects**: side-horizontal straight profile. Keep the full width visible and level. No 3/4 front view, no angled perspective, no top-down view. Examples: van, truck, car, bus, transport vehicle, sofa, couch, massage bed/table, bench, cot, long cabinet, dresser, shelf, curtains, railing, balustrade.
- **Tall vertical objects**: straight front view. Preserve height and vertical silhouette. No 3/4 angle unless a base/reference asset already uses it. No top-down view. Examples: refrigerator, wardrobe, geyser/water heater, tower purifier, standing lamp.
- **Boxy compact objects**: straight front view with only minimal top-face visibility if essential. No top-down view and no 3/4 perspective. Examples: gift box, bucket, cleaning caddy, microwave, washing machine, basket.
- **Round or flat-top objects**: front view or slight top visibility only when needed for recognition; avoid obvious top-down perspective. Examples: stove, pot, bowl, toilet.
- **Tool pairs/crossed objects**: preserve the reference orientation family. If no reference exists, use a flat front-readable arrangement, not a perspective scene.
- **Transparent/glass objects**: choose front or side based on the dominant silhouette; avoid top-down unless the reference family requires it.

For any object whose real-world silhouette is wider than it is tall, prefer side-horizontal unless the service/archive/base reference clearly requires otherwise. A wide-object request such as `black transportation van` must produce a horizontal side profile, similar in orientation discipline to the massage bed.

Aspect-ratio handling:

- The service-name archive is the asset source of truth and is primarily `4096x3072` (4:3). The final workspace asset must therefore be `1024x768`, not square.
- Never stretch a 4:3 archive icon or generated image into a square. Preserve the model/proportions from the exact service source, near service source, base-object source, material-index source, or character base/exemplar, then export onto the fixed `1024x768` canvas.
- When a matching base or exemplar exists, use it to preserve the same model/form family. For character icons, canonical files in `references/characters/base/` remain the model source for face, proportions, and material family; the final export is still `1024x768`.
- If Image Gen can be guided by size, request `1024x768`. If it returns another aspect ratio, run the exporter; it preserves aspect ratio, crops only excess background when needed, and centers the subject on `#f5f5f5`.

## Character Icons

When the subject is a person delivering or receiving a service (maid, helper, salon/spa client, massage client, security guard, technician, driver, trainer, or any other male/female service worker or client), switch to the character path:

1. Handle all reference-image selection silently. Do not display base images or service exemplars in chat, do not call image preview tools only to make a local reference visible, and do not narrate "loading" or "loaded the base image" in user-facing progress or final messages.
2. If the requested character asset already exists as a curated service exemplar in `references/characters/` or the bundled service-name archive (for example women's salon/spa, men's salon/massage, InstaHelp, Dubai maid, live-in maid, premium helper), use that exemplar as the final base image and export it with `--preserve-source`. Do not send it through Image Gen, do not tweak the background, optical size, crop, margins, contact shadow, face, wardrobe, treatment cue, pose, expression, or material family unless the user explicitly asks for a new edited variant.
3. For any new human/character icon where an exact preexisting character service icon is not being exported as-is, always use a canonical human base image as the edit target/base image. This is a hard rule. Do not generate a human character from scratch, and do not use the human base only as a style reference.
4. Choose the canonical base by requested gender and eye state first: `references/characters/base/base-female-eyes-open.png`, `references/characters/base/base-female-eyes-closed.png`, `references/characters/base/base-male-eyes-open.png`, or `references/characters/base/base-male-eyes-closed.png`. If those canonical files are unavailable, use the closest matching human base from `references/base-objects/` or the closest curated character exemplar as the edit target/base image, then preserve that base's identity.
5. Use the selected human base as the edit target/base image for Image Gen edit mode whenever editing/reference input is available. Lock the base face family, expression, head scale, bust crop, skin, hair fidelity, lighting, shadow, material finish, and optical size; change only the requested wardrobe, headwear, held/service cue, or sanctioned accent.
6. If the user supplies an external human/person reference image, default to the UC set-style bust crop from the selected canonical base. Treat the external reference only as a cue for the requested treatment, wardrobe color, clothing type, cream/mask placement, mood, or other local details. Do not follow the external reference's close crop, face-only framing, body crop, camera distance, head size, or composition unless the user explicitly asks to match the reference crop/framing/composition.
7. If the user explicitly asks to match the external reference crop/framing/composition, make that crop mode explicit in the edit prompt while still preserving the UC tactile 3D style, fixed `1024x768` canvas, `#f5f5f5` background, and non-photoreal character treatment. Do not copy real-person likeness; translate only the requested composition/framing.
8. Read `references/skeuo-uc-characters.md` only as the edit guide: it defines base-image priority, wardrobe, treatment cue, accent, hair fidelity, background, and crop rules. The selected base/reference image is the primary source of truth for face, proportions, material finish, lighting, shadow treatment, optical size, and overall character family.
9. If edit mode or image input is unavailable for a required character base edit, stop and tell the user that base-preserving edit mode is unavailable. Do not generate a new human icon from scratch unless the user explicitly overrides the base-image rule after being told identity/composition may drift. Do not silently downgrade the base/exemplar PNG to a style reference.
10. Never apply character treatment to object icons; the character path is gated to people-centric categories only.

## Inputs

Parse inputs by meaning, not position:

- `Subject`: required. The object or category, such as `office chair`, `basin mixer tap`, or `salon chair`.
- `Color Palette`: optional. If omitted, derive a compact palette from the subject's real-world materials.
- `Object + Service-Cue Combo`: optional. Add one secondary tool only when it helps the service category read clearly.
- `Background Mode`: optional. Default to fixed `#f5f5f5` background. Only use another background mode when explicitly requested.

If the user provides only a palette and no subject, ask for the subject.

## Workflow

1. Load and apply the system `imagegen` skill as an internal companion skill only when generation is required.
2. Keep internal setup quiet. Do not show or preview base/reference images in chat, and do not mention reference loading unless it is blocked and the user must act.
3. For every request, silently check the reference archives before prompting:
   - Exact/near service match in `PNGs_renamed/`: use it as the source asset and export it with `--preserve-source`; skip Image Gen.
   - Small requested variant of a service/base-object asset: use the matched PNG as the edit target/base image; preserve composition and untouched content.
   - Optional base object in `references/base-objects/` or a manifest `image_path`: run `scripts/find_base_object.py` and prefer its selected base over material-index references for editable object variants.
   - Multiple plausible exact/near service matches: ask the user to choose the intended service/type before proceeding.
   - No service match: choose the closest material/form reference from `PNGs_material_index/MANIFEST.csv` and use it to guide treatment, texture, fidelity, and lighting for new generation only.
   - Character request: apply the Character Icons rules first. If an exact preexisting character icon is not being exported as-is, use a canonical human base image as the edit target/base image. Never generate a human icon from scratch by default.
4. When an existing service asset is selected, run the exporter directly with `--source <SERVICE_PNG> --preserve-source`, then stop. Do not build a generation prompt.
5. For base-image edits, build an edit prompt from the Base-Image Edit Prompt below. Do not use the new-generation prompt. If the available tool path cannot use the local PNG as an edit target/base image, stop and tell the user that base-preserving edit mode is unavailable; ask whether to generate a new icon from scratch instead. Do not silently downgrade the base image to a style reference.
6. Build the new-generation prompt only when no suitable existing service/base asset exists or the user explicitly asks for a new design. For character icons, keep using the Character Icons rules. For non-human object icons, run `scripts/find_generation_references.py`, attach references silently when possible, and use the compact new-object prompt instead of the long style brief.
7. Generate with GPT Image 2 / built-in Image Gen automatically only when generation or base-image editing is required. Do not ask the user to invoke Image Gen separately.
   - For character icons without an exact service exemplar, require Image Gen edit mode using the selected canonical human base as the base image. For new character variants, preserve the base character's face family, crop, proportions, material finish, lighting, shadow treatment, hair fidelity, and optical size; change only the requested service-specific wardrobe, treatment cue, sanctioned accent, hairstyle shape when needed, and fixed `#f5f5f5` background. If an external person reference is supplied, keep this set-style bust crop by default; use the reference's crop only when explicitly requested.
   - For object icons with an exact/near archive source, do not generate. For new object icons, use the selected archive reference(s) to match material treatment, texture density, edge softness, shadow, and optical size while creating the requested subject.
   - Do not attempt local transparency removal or alpha repair by default. The final icon uses a fixed `#f5f5f5` background.
   - Do not downgrade to another model or CLI fallback unless the user explicitly approves it or has explicitly requested that path.
8. Before Image Gen/export, run this internal checklist:
   - Did an exact existing service asset only need export? If yes, skip Image Gen.
   - Did a base-object or human base exist for the requested variant? If yes, use the base-image edit prompt, not the new-generation prompt.
   - Is the selected base side/horizontal/3-4/non-front? If yes, preserve that orientation; do not force front view.
   - Is the requested object wide/long? If yes, force side-horizontal straight profile and reject 3/4 front or top-down generation.
   - Is the subject human? If yes, use a canonical human base edit; do not generate from scratch unless explicitly overridden.
   - Is lookup ambiguous? If yes, ask; do not guess.
9. If the image tool returns a file path, pass it to the exporter with `--source`.
10. If no source path is exposed, run the exporter without `--source`; it will try to locate the newest generated PNG under common Codex image-output folders.
11. Confirm the final path, `1024x768` size, mode, and fixed `#f5f5f5` background. Keep the final response focused on the saved asset and validation; do not recap internal reference-image loading.

Exporter:

```bash
python3 "<THIS_SKILL_DIR>/scripts/export_skeuo_uc_icon.py" --subject "<SUBJECT>"
```

With an explicit generated PNG:

```bash
python3 "<THIS_SKILL_DIR>/scripts/export_skeuo_uc_icon.py" --subject "<SUBJECT>" --source "<PNG_PATH>"
```

With an existing service/archive PNG that should not be edited:

```bash
python3 "<THIS_SKILL_DIR>/scripts/export_skeuo_uc_icon.py" --subject "<SUBJECT>" --source "<SERVICE_PNG_PATH>" --preserve-source
```

Resolve `<THIS_SKILL_DIR>` to the directory containing this `SKILL.md`. Run the exporter from the user's project/workspace directory so `./assets/` resolves correctly.

## Base-Image Edit Prompt

Use this only when editing an existing service/base-object/character PNG. The selected PNG is the edit target/base image, not a style reference.

Fill `<BASE_IMAGE_ROLE>`, `<REQUESTED_CHANGE>`, and `<UNCHANGED_DETAILS>`.

```text
Use case: precise base-image edit for a Waterlemon UC icon
Asset type: 1024x768 premium 3D skeuomorphic app/web icon for a services marketplace (Urban Company)
Input image role: <BASE_IMAGE_ROLE>; this is the base image to preserve, not just a style reference.
Primary request: <REQUESTED_CHANGE>
Crop mode: preserve the selected base image crop and optical size unless the user explicitly requested reference crop/framing/composition.
Preserve exactly: camera angle, orientation, perspective, crop, object/character proportions, silhouette, optical size, lighting direction, shadow softness, material fidelity, render style, background treatment, and all untouched parts.
Do not redesign the icon. Do not change the viewpoint. Do not change from side view to front view or from front view to side view. Do not replace the base object/character with a newly invented one.
Allowed changes only: <REQUESTED_CHANGE>
Must remain unchanged: <UNCHANGED_DETAILS>
Scene / background: keep the existing fixed #f5f5f5 Waterlemon icon background and clear soft contact shadow unless the requested edit explicitly targets them.
Quality: polished Waterlemon UC icon, no logos, no readable text, no watermark, no extra props, no clutter.
```

Example object edit:

```text
Input image role: Spa for women massage bed base image.
Primary request: remove the folded towel from the bed and recolor only the pink upholstery to warm beige.
Preserve exactly: the side-view horizontal massage-bed composition, pillow/headrest, wooden legs and diagonal supports, crop, perspective, leather grain, lighting, shadow, and background.
Allowed changes only: remove towel; change pink upholstery to beige.
Must remain unchanged: bed geometry, side orientation, wooden frame, cushion thickness, headrest, shadow, camera, crop, and material fidelity.
```

Example character edit:

```text
Input image role: canonical female bust base image.
Primary request: dress the same female character as a chef with a white chef hat and white chef coat.
Preserve exactly: face family, expression, eye style, skin, hair fidelity, head scale, bust crop, lighting, shadow, material finish, and optical size.
Allowed changes only: add chef hat and chef coat.
Must remain unchanged: identity, facial proportions, pose, crop, lighting, and Waterlemon character render family.
```

Hard character rule: for human icons, use this base-image edit prompt with a canonical human base whenever the exact requested preexisting icon is not simply being exported. Do not use the new-generation prompt for human characters unless the user explicitly overrides this rule after being warned that base preservation will be lost.

## Generation Prompt

Use this long prompt only as fallback for new non-human object icons when no usable image references can be attached or derived. Do not use it for human characters. Fill `<SUBJECT>`, `<COLOR PALETTE>`, `<BACKGROUND>`, and `<CAMERA / VIEW>`.

```text
Use case: UI category icon
Asset type: premium 3D skeuomorphic app/web icon for a services marketplace (Urban Company)
Primary request: Create one original tactile skeuomorphic 3D icon of a miniature object.
Subject: <SUBJECT>
Style language: tactile_skeuomorphic_micro-object; soft, premium, miniature 3D object language between product rendering and iconography. Preserve real-world materials but simplify for screen readability. Tangible, clean, calm, recognizable at a glance in a UI grid.
Scene / background: <BACKGROUND>. Default: fixed solid #f5f5f5 background with no cast shadow, no drop shadow, no contact shadow, no floor shadow, no room, no tabletop, no environment.
Camera / view: <CAMERA / VIEW>. Default for brand-new icons with no relevant base/reference family: straight front view, centered, near-orthographic, no top-down view. For wide/long objects, use side-horizontal straight profile and explicitly avoid 3/4 front, angled perspective, and top-down view. If the selected material/form reference or category family uses a non-front orientation that is essential to recognition, preserve that orientation family only when it does not conflict with the wide-object rule.
Lighting / mood: soft studio lighting, front-biased. Gentle contrast, broad premium highlights, no theatrical drama. Shadow: none below the object for new generation; avoid cast/drop/contact/floor shadows.
Materials: believable but edited realism. Mostly matte-to-satin; controlled gloss only where material identity requires it. Wood smooth and lightly finished; fabric plush but simplified; metal premium and clean; plastic molded and smooth; glass/liquid readable and simplified. Low-to-moderate texture density.
Simplification level: medium-high. Keep primary silhouette, major functional parts, identity-defining components, and clear material separation. Reduce micro seams, engravings, tiny buttons, secondary mechanical complexity, and decorative clutter.
Edges: softened, approachable, rounded corners, subtle bevels.
Composition / framing: single centered object, or one tightly curated mini-group only if essential to recognition. Full object visible with comfortable margin. 4:3 icon-friendly composition matching the reference archive format.
Color palette: <COLOR PALETTE>
Color rules: compact and edited; one dominant color family with limited accents. Preserve real-world material identity. Avoid muddy neutrals and random multicolor fragmentation. Allow one focal accent only if it aids recognition.
Screen legibility: clear silhouette; limited important shape masses; strong separation between major parts; no dependency on tiny details; thin parts may be slightly thickened for visibility; transparent materials must remain visible against a #f5f5f5 background.
Quality: 1024x768 PNG, polished premium UI icon, balanced margins, consistent optical size across icon sets.
Avoid: hyperreal product/catalog photography; busy environments; room interiors; tabletop lifestyle styling; hands or people; logos; branding; printed text; barcodes; tiny unreadable details; heavy texture noise; grime; wear; harsh dramatic shadows; excessive gloss; mirror chrome everywhere; flat 2D/vector look; toy-like cartoon exaggeration; cheap mobile-game CGI; random decorative props; multiple competing focal points; extreme perspective distortion; cluttered arrangements.
```

Use fixed solid `#f5f5f5` as the background. Do not generate a checkerboard or chroma-key background, and do not remove backgrounds locally unless the user explicitly asks for a transparent variant.

## Batches

For multiple subjects, generate and export one icon at a time. Do not use a single prompt containing many unrelated objects unless the requested icon itself is an object/service-cue combo.

Use consistent background mode, lighting direction, material finish, camera angle, simplification depth, and optical size across the batch.

## If GPT Image 2 / Image Gen Is Unavailable

First apply the required companion `imagegen` skill and try its built-in tool path or documented tool-discovery path. If Image Gen still is not callable, tell the user that GPT Image 2 / Image Gen is not exposed in the current session. Do not silently replace the output with hand-drawn SVG, HTML/CSS, copied exemplars, or placeholder art unless the user explicitly accepts a local fallback.
