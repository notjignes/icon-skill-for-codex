---
name: uc-icons-visual-brief
description: Compatibility visual brief for UC tactile skeuomorphic icon generation.
---

# UC Icons visual brief

`references/icon-contract.md` is the single authority for visual, camera, composition,
background, lighting, shadow, master, and delivery requirements. `SKILL.md` is the
authority for routing and user-facing behavior.

## Compact generation brief

Generate one original premium UC tactile skeuomorphic 3D micro-object for a services
marketplace. Preserve a familiar real-world silhouette and identity-defining parts,
then simplify seams, controls, mechanisms, and texture for small-screen recognition.

- Use the planner's `view`, `layout_axis`, `projection`, `composition_family`, and
  `mass_count`; do not force every object into a front view.
- Use one dominant mass and at most one subordinate service cue unless the approved
  composition family is explicitly grouped or carrier-contents.
- Use edited material realism: soft approachable bevels, mostly matte-to-satin
  finishes, and controlled gloss only for identity-bearing glass, polished metal,
  ceramic, or liquid.
- Use a compact material-led palette with one dominant family and restrained accents.
- Keep the whole subject visible and optically centered on exact `#f5f5f5`.
- Do not create a scene, room, tabletop, hands, people, text, logos, branding,
  watermarks, or decorative clutter.
- For newly generated or redesigned work, include no external cast, contact, drop,
  or floor shadow, glow, or ambient grounding pool. Internal self-shadow, occlusion,
  and material shading remain allowed.

Request a high-quality opaque `2048x1536` PNG master. If the tool returns a smaller
valid image, preserve it without upscaling. Pass its explicit path to
`scripts/export_skeuo_uc_icon.py`; never search broad folders for the newest image.

Exact legacy exports and ordinary legacy base edits may preserve their source
treatment. Character edits additionally follow `references/skeuo-uc-characters.md`.
