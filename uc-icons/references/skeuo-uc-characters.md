---
name: skeuo-uc-characters
description: "Canonical UC character appearance, service wardrobe, treatment and accent rules for base-preserving edits."
---

# Waterlemon UC characters

Use only when the subject is a service worker or client. Object icons never inherit character features. Wardrobe carries the service meaning; use a single bust without handheld tools or unrelated props.

## Base and composition

An exact curated character asset is exported unchanged. Explicit edits to a named character asset preserve that asset as the edit target. New service-character variants use the planner-returned curated base as the edit target, never merely as a style reference. The user-selected InstaHelp master (`insta-help-india.png`) is the calibrated base for open-eyed female service variants: its neutral beige skin, soft light, larger face-to-bust ratio and shallow upper-chest crop win over the warmer generic bare-shoulder base. Use the generic canonical files for other gender/eye states, or an explicitly user-selected curated source. Canonical files in `characters/base/` are `base-female-eyes-open.png`, `base-female-eyes-closed.png`, `base-male-eyes-open.png`, and `base-male-eyes-closed.png`.

Choose requested gender and eye state first. Active workers default to open eyes; salon, spa, massage and resting clients default to closed eyes. Select the matching base instead of repainting its eyes. If the required base or base-preserving editing is unavailable, report the blocker; do not automatically substitute reference-only or text-only generation.

Preserve the base face, expression, skin, proportions, crop, camera, optical size, lighting, existing shadow and material fidelity. Change only the requested wardrobe, treatment, sanctioned accent or necessary hairstyle shape. Curated exemplars below establish service details, not replacement face identities.

External person references supply requested clothing, treatment, mood or hair cues. Keep the UC bust crop unless the user explicitly requests different framing/composition; then name that override in the edit prompt. Translate composition into UC style without copying real-person likeness.

## Character appearance

- Premium stylised designer-vinyl bust: head, neck, softly sloped shoulders and upper chest, with a clean rounded lower edge. Preserve the actual selected base’s head-to-shoulder and face-to-bust proportions; do not impose a universal numeric head-height ratio. No arms, hands, waist or full body by default.
- Match the selected curated base’s skin hue, saturation and neutral diffuse illumination. Do not warm it toward orange or increase contrast; descriptive “warmth” must not override the source pixels. No pores, mottling, wrinkles or neck creases.
- Thick sculpted dark-brown brows; almond dark-brown eyes with one white catchlight; simple nose without nostril openings; coral-pink lips in a closed micro-smile; simplified ears. Closed eyes use smooth downward lash-line crescents. No teeth, eyelash strands, inner-ear detail, freckles or makeup detail.
- Preserve warm/medium-brown hair as satin-plastic or polished-clay masses: broad flow bands and curved highlights, shallow low-contrast grooves, rounded edges. Female shapes may use bun, low ponytail, compact sweep or towel cover; male shapes may use short crop, side sweep or cap-compressed hair. No individual fibers, flyaways, frizz, wet shine, sharp white streaks, scalp detail or sparkle noise.
- Smooth moulded fabric with soft seam ridges; towels use fine uniform simplified nubble. Matte-to-satin finish, narrow satin highlights on hair/lips. Calm, composed expression; no dramatic emotion, photorealism, mascot/Funko exaggeration or random jewellery, glasses, badges, logos and text.

## Canonical wardrobe and treatment

Reproduce these details without restyling or extra accessories unless the user requests changes. Exemplar filenames are relative to `characters/`.

| Variant / exemplar | Required details |
|---|---|
| InstaHelp, India — `insta-help-india.png` | Medium-purple dress, small rounded collar, white square-bib apron; low bun; open eyes. |
| Live-out/all-in-one maid, Dubai — `maid-dubai.png` | Royal/medium-blue dress, mustard-yellow rounded collar, light sky-blue square-bib pinafore apron; low bun; open eyes. |
| Live-in maid, Dubai — `live-in-maid-dubai.png` | Same Dubai uniform and character; small house accent below. |
| Premium helper, any country — `premium-helper.png` | Black crossover/wrap top, thin gold lapel piping, no apron; low side ponytail; open eyes. |
| Women's salon/spa, Dubai exemplar — `female-salon-spa.png` | White terry shawl-collar bathrobe, cream towel turban, smooth sage-green clay mask with clean eye/brow/lip cut-outs; closed serene eyes. |
| Luxury women's salon/spa, Dubai exemplar — `luxury-female-salon-spa.png` | Same spa wardrobe and treatment; golden sparkle accent below. |
| Men's salon/massage, Dubai exemplar — `male-salon-massage.png` | White terry shawl-collar bathrobe, simplified fluffy white foam beard around jaw/upper lip, two sage-green under-eye patches; closed serene eyes, short brown sculpted hair. |

For unlisted roles, use one compact professional shirt/jacket/top, relevant collar/apron and role-defining hat if needed. No name tags, tools, weapons or extra props. Canonical treatment combinations above remain intact; otherwise limit additions to one applied face/head treatment. Masks read as matte putty, foam as simplified meringue lobes, patches as satin with one soft highlight.

Only two side accents are sanctioned, never together:

- **Live-in house:** lower-right beside the bust, shoulder height or below, about one-third its height; matte white/cream cottage, terracotta-orange tiled gable roof, simple wooden door. Keep clearly secondary; no windows needed.
- **Luxury sparkles:** two or three small asymmetric four-point golden-yellow diamonds around the upper bust, soft satin gradients. No halo, ring or particle cloud.

When adding a hat, keep the selected source’s face size, shoulder width and bottom crop. Fit a compact role cue around the existing head silhouette rather than shrinking the face to fit a tall hat or extending the torso. If that cannot fit the requested framing, use a smaller hat. Compare with the selected source after rendering; preserving a previous failed edit is insufficient.

## Compact edit prompt

```text
Subject: <SERVICE / ROLE>.
Edit the attached planner-selected curated UC base. Requested change: <CHANGE>.
Wardrobe/treatment: <REQUIRED DETAILS FROM ABOVE OR REQUESTED UNIFORM>.
Accent: <NONE / SANCTIONED ACCENT DETAILS>.
Crop: preserve base, except <EXPLICIT USER OVERRIDE OR NONE>.
Preserve face, expression, skin, proportions, optical size, camera, lighting, existing shadow, sculpted hair fidelity and all untouched details. Do not invent a replacement character or add a shadow.
Request solid #f5f5f5 background, 1024x768 PNG, UC matte-to-satin style; no environment, text or extra props.
```

Exporter operations only contain the full frame proportionally and composite existing alpha. Never clean backgrounds, segment pale surfaces or remove shadows automatically. Background removal is manual post-processing. Across a set, preserve face family, skin, hair material, framing, light and optical size.
