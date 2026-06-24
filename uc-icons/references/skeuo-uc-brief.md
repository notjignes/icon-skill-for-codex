---
name: uc-icons
description: "UC tactile skeuomorphic 3D category icons for the Urban Company services marketplace; saves PNG to assets."
---

# Waterlemon UC

## Mandatory Behavior

When this skill is invoked, export an existing matching icon, edit a selected base image, or generate one fresh image only when needed, then save one final PNG into `./assets/` in the current working directory. Keep the UC icon contract: fixed solid #f5f5f5 background, no scene building, no readable text, no copied logos, no branding, no human presence except deliberate character icons, and exactly 1024x768 final workspace asset matching the 4:3 reference archive format. For new object generation, do not add cast shadows, drop shadows, contact shadows, floor shadows, or glow below the icon. Preserve existing shadows only for exact archive exports or base-image edits unless the user asks to remove them.

## Inputs

- `Subject` is required. This is the object or service category to render (e.g. *"basin mixer tap"*, *"salon chair"*, *"power drill"*).
- `Color Palette` is optional. If omitted, derive a compact edited palette from the subject's real-world material identity — one dominant colour family with limited accents. Moderate saturation; selective brighter accents only where they aid recognition.
- `Object + Service-Cue Combo` is optional. For service/repair categories, a single secondary tool (wrench, brush, drill) may be specified alongside the primary object. Keep to two masses max.
- `Background Mode` is optional. Default: fixed solid **#f5f5f5** background. Only use another background mode when explicitly requested.
- Inputs can be provided in any order; parse by label, not position.
- If the request has only a colour palette and no subject, ask for the subject.

## Execution

1. Build the compact **Generation Prompt** below by filling the labeled inputs. Replace `<SUBJECT>`, `<COLOR PALETTE>`, and `<BACKGROUND>` with the values derived from the inputs section. If no palette was provided, describe the real-world material colour of the subject.
2. Generate automatically with Image Gen. The user invoking this skill is enough; do not ask them to type `/Image Gen`.
3. After Image Gen succeeds, run the Waterlemon UC Asset Exporter from the user's workspace so `./assets` points to the project:

```bash
python3 "<THIS_SKILL_DIR>/scripts/export_skeuo_uc_icon.py" --subject "<SUBJECT>"
```

If Image Gen exposes an explicit PNG path, add `--source "<PNG_PATH>"`. Resolve `<THIS_SKILL_DIR>` to the folder containing this `SKILL.md`.

4. Do not manually search, copy, rename, resize, or inspect the generated image unless the script fails. The exporter finds the newest PNG, copies without deleting the source, avoids overwrites, preserves aspect ratio, reframes onto a 1024x768 canvas, and prints the saved path.

## Generation Prompt

Use this compact prompt. Fill the labeled inputs. Replace `<SUBJECT>`, `<COLOR PALETTE>`, and `<BACKGROUND>`.

```text
Use case: UI category icon
Asset type: premium 3D skeuomorphic app/web icon for a services marketplace (Urban Company)
Primary request: Create one original tactile skeuomorphic 3D icon of a miniature object.
Subject: <SUBJECT>
Style language: tactile_skeuomorphic_micro-object — a soft, premium, miniature 3D object language sitting between product rendering and iconography. Real-world materials preserved but simplified for the screen. Tangible, clean, calm, recognisable at a glance in a UI grid.
Scene / background: <BACKGROUND> (default: fixed solid #f5f5f5 background with no cast shadow, no drop shadow, no contact shadow, no floor shadow, no room, no tabletop, no environment).
Camera / view: straight front view — camera faces the object head-on, centred, with a very slight elevation only if needed to show the top face of the object. No side angle, no ¾ rotation, no isometric tilt. Object presented from its most recognisable frontal face. Minimal distortion; near-orthographic perspective.
Lighting / mood: soft studio lighting, front-top biased, angled just enough to describe form. Gentle contrast; broad soft premium highlights; no theatrical drama. Shadow: none below the object for new generation; preserve an existing source shadow only for exact archive exports or base-image edits.
Materials: believable but edited realism — tactile and premium, not raw. Finish mostly matte-to-satin; controlled gloss only where the material demands it (glass, polished metal, ceramic). Per-material: wood is smooth and lightly finished (not raw or heavily grained); fabric is plush but simplified; metal is premium and clean (avoid mirror-heavy chrome unless identity-defining); plastic is moulded and smooth; glass/liquid is readable and simplified. Texture density: low-to-moderate; keep only texture that aids material recognition.
Simplification level: medium-high. Keep primary silhouette, major functional parts, identity-defining components, and clear material separation. Reduce micro seams, fine engravings, tiny buttons, and secondary mechanical complexity. Remove logos, text labels, barcodes, tiny interface details, and decorative clutter.
Edges: softened and approachable — rounded corners, subtle bevels; no razor-sharp untreated edges unless recognition absolutely requires them.
Composition / framing: single centred object (or one tightly curated mini-group only if essential to recognition). Full object visible with comfortable margin; 4:3 icon-friendly composition matching the reference archive.
Color palette: <COLOR PALETTE>
Color rules: compact and edited — one dominant colour family + limited accents. Clean colour blocking; preserve real-world material identity; avoid muddy neutrals and random multicolour fragmentation; allow one focal accent if it aids recognition.
Screen legibility (hard requirements): clear silhouette; limited important shape masses; strong separation between major parts; no dependency on tiny details; thin parts may be slightly thickened for visibility; transparent materials must stay visible against the #f5f5f5 background; grouped props must still read as one icon.
Quality: 1024×768 PNG, polished premium UI icon, simple readable subject, balanced margins, consistent optical size across icon sets.
Avoid: hyperreal product / catalogue photography; busy environments, room interiors, kitchen or bathroom context; tabletop lifestyle styling; hands or people (unless icon IS a deliberate character — see rules); logos, branding, printed text, barcodes; tiny unreadable details, over-detailed manufacturing realism; heavy texture noise, grime, wear; harsh / deep dramatic shadows, high-contrast cinematic mood; excessive gloss, mirror chrome everywhere, complex reflections; flat 2D / vector illustration look; toy-like cartoon exaggeration, plastic toy proportions; cheap mobile-game icon aesthetic, hard-edged cheap CGI; random decorative props, visual clutter; multiple competing focal points; extreme perspective distortion; cluttered multi-object arrangements.
```

## Shared Rules

- Output must be a single centred icon. Default background: fixed solid #f5f5f5.
- For new object generation, do not include cast, drop, contact, floor shadows, or glow. Preserve existing shadows only for exact archive exports or base-image edits unless the user asks to remove them.
- No scene, no room, no tabletop styling.
- Keep the full subject visible with a comfortable margin; 4:3 icon-friendly composition.
- No readable text, logo, watermark, copied brand icon, or branding of any kind.
- No human presence except for deliberate character icons (see Style Notes below).
- For object + service-cue combos (e.g. basin + wrench): maximum two masses; same materials and lighting; tool is clearly secondary; overall image still reads as one silhouette.
- For character icons (people-centric services — maid, stylist, masseuse): render a single stylised 3D character bust in the same soft skeuomorphic material language. Friendly, simplified, no real-person likeness, same lighting and grounding rules. This is the only exception to "no human presence." Full character rules, canonical uniforms, style-reference images, and the character generation prompt live in `references/skeuo-uc-characters.md` — read it and use its prompt instead of the object prompt for any character icon.
- Preserve subject intent. Fix obvious typos only when unambiguous. If the subject has multiple objects, compose them as one centred icon.
- Do not add eyes, mouth, nose, smile, expression, limbs, mascot cues, or character attributes unless the icon is explicitly a character icon.

## Style Notes

- Keep the subject simple, chunky, and readable at small sizes. Recognition at small sizes beats realism.
- Use material detail only where it helps identify form; avoid tiny clutter and fragile thin strokes.
- Straight front view is the family standard. Do not mix front and ¾/isometric views across an icon set — every icon in the set must use the same straight head-on angle.
- Background mode must be consistent across an icon set. Use fixed solid #f5f5f5 unless another mode is explicitly requested.
- Colour palette should feel cohesive with the object's real-world identity. Avoid introducing colours that have no grounding in the material.
- When generating a whole category set, the icons must share the same simplified-skeuomorphic family feel: same lighting direction, same fixed #f5f5f5 background treatment, same material finish level, same simplification depth.

## If Image Gen Is Not Available

Use the main `SKILL.md` availability rules. Do not switch to SVG, HTML/CSS, placeholder art, copied exemplars, or another image model unless the user explicitly approves that fallback.
