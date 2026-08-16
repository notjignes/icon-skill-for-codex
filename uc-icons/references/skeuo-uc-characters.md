---
name: skeuo-uc-characters
description: "Character sub-spec for Waterlemon UC people-centric service icons. Pairs canonical gender bases, curated service references, and a full character style block."
---

# Waterlemon UC Character Icons (Sub-Spec)

This sub-spec extends the Waterlemon UC brief for **character icons only**. It applies exclusively on the character path — people-centric service categories such as maid/helper, salon, spa, massage, security guard, technician, driver, trainer, and similar service workers or service clients. It must never bleed into object icons, which keep the "no human presence" rule.

## Gating

Use this sub-spec only when the requested subject IS a person delivering or receiving a service:

- maid / helper / domestic help (InstaHelp, maid-for-rent, premium helper)
- women's salon & spa (female client being pampered)
- men's salon & massage (male client being pampered)
- security guard, technician, driver, trainer, cleaner, cook, nurse, attendant, or any clearly male/female service-worker bust

Everything else stays on the object path. If a subject mixes an object and a person (e.g. "maid with vacuum"), prefer the character alone — the uniform is the service cue; do not add a handheld tool as a second mass.

## Style References (primary source)

Canonical character names live in `references/characters/MANIFEST.csv`. Resolve them
through the planner/registry to their canonical archive masters; do not construct a
physical `references/characters/...png` path. An exact existing service-character
variant, or a requested local edit of it, uses that resolved service archive master as
the edit target so its established identity is preserved. A genuinely new or unlisted
character variant uses the closest matching canonical gender + eye-state asset as the
**base image** in Image Gen edit mode.

- `base-female-eyes-open` for female service workers or clients with alert/calm open eyes.
- `base-female-eyes-closed` for female pampering, spa, massage, rest, or eyes-closed variants.
- `base-male-eyes-open` for male service workers or clients with alert/calm open eyes.
- `base-male-eyes-closed` for male pampering, spa, massage, rest, or eyes-closed variants.

Default to the open-eyes base for active service-worker roles (maid/helper, security guard, technician, driver, trainer, cleaner, cook, nurse, attendant). Use the closed-eyes base for salon/spa/massage/pampering variants or when the requested expression is explicitly serene/resting. Do not edit eye state from scratch when the matching base already exists; choose the correct base first.

For a new or unlisted character, the canonical gender base is the primary source of truth for face family, crop, proportions, material finish, lighting, shadow treatment, optical size, and hair fidelity. A service exemplar may be the edit target only when the request resolves that exact existing service-character identity; it is never a loose fallback for a different or unresolved character.

When the user supplies an external human/person reference image, keep the canonical UC set-style bust crop by default. Unless the user explicitly labels that image as the request-scoped edit base, use it only for requested local cues such as treatment placement, cream/mask shape, wardrobe color, clothing type, expression mood, or hairstyle direction. An explicitly supplied `base` reference follows the runtime precedence contract for that request only and is never promoted automatically. Do not inherit an ordinary cue reference's face-only crop, tight photographic framing, body crop, camera distance, head size, or composition unless the user explicitly asks to match the reference crop/framing/composition. Always translate it into the UC tactile 3D character language and do not copy real-person likeness.

Curated service exemplar identities also resolve through the character manifest:

The written spec below is an edit guide and constraint checklist. It tells the model what may change for the requested service variant; it never substitutes for the planner-resolved edit target (exact service variant, canonical gender base, or explicitly supplied request-scoped base). If base-image editing is unavailable, stop and report that the character edit is blocked. Do not fall back to exemplar-as-style or text-only generation because either path can invent a different character identity.

| Character ID | Service | Market | Wardrobe / accent |
|---|---|---|---|
| `insta-help-india` | InstaHelp (maid) | India | Purple uniform + white apron |
| `maid-dubai` | Maid for rent / all-in-one help (live-out) | Dubai only | Blue uniform + yellow collar + light-blue apron |
| `live-in-maid-dubai` | Maid for rent — live-in | Dubai only | Same blue/yellow uniform + small house accent beside the bust |
| `premium-helper` | Premium helper (luxe or any premium tier) | India or any country | Black wrap top + gold piping |
| `female-salon-spa` | Women's salon & spa | Dubai | White bathrobe + towel turban + green face mask |
| `luxury-female-salon-spa` | Luxury women's salon & spa | Dubai | Same spa bust + golden sparkle accents |
| `male-salon-massage` | Men's salon & massage | Dubai | White bathrobe + foam beard + green eye patches |

If a new character icon is requested, edit the canonical gender base closest to the requested gender. Keep the base character identity intact and change only the requested wardrobe, treatment cue, sanctioned accent, hairstyle shape when needed for the role, and fixed #f5f5f5 background. If no canonical gender base resolves, stop instead of inventing a replacement. Never mix a drifting external reference into the set.

## Character DNA (shared across every character icon)

One base character family — every female character icon is visibly the *same woman* in different wardrobe; the male is her counterpart in the same family.

- **Form:** single stylised 3D character bust — a premium designer-vinyl figurine, same matte-satin material language as the object icons. Not a mascot, not a Pixar still, not an emoji.
- **Crop:** head + neck + shoulders + upper chest. The bust ends in a clean soft-rounded lower edge. No arms, no hands, no waist, no full body. Preserve this UC set crop for external reference-driven character requests unless the user explicitly asks to match the reference crop/framing.
- **Proportions:** gently stylised — head slightly oversized (roughly 40–45% of total icon height), narrow softly-sloped shoulders, slim neck. Friendly volume, not bobblehead exaggeration.
- **Skin:** light-medium warm beige, perfectly smooth matte vinyl with a soft subsurface warmth. One consistent skin tone across the whole set. No pores, no texture, no blush mottling, no wrinkles, no neck creases.
- **Face — include exactly:** thick soft sculpted eyebrows (dark brown, smooth solid shapes); large almond eyes with dark-brown iris, dark pupil, and one small white catchlight; simple sculpted nose with no nostril holes; full coral-pink lips with a calm, closed-mouth micro-smile; simplified sculpted ears.
- **Face — exclude:** teeth, tongue, nostril openings, inner-ear detail, eyelash strands (lash reads as a single dark lid line), freckles, moles, makeup detail, expression lines.
- **Eyes-closed variant (spa/pampering only):** eyes become two smooth downward lash-line crescents with soft sculpted lids; expression serene and relaxed.
- **Hair:** preserve the base image's hair material fidelity even when the hairstyle changes. Hair is warm dark brown or medium brown, sculpted as clean satin-plastic / polished-clay masses with large simplified flow bands, broad soft curved highlights, shallow low-contrast grooves, and rounded beveled edges. Female hairstyles may change between bun, low ponytail, compact loose sweep, or towel-covered hair; male hairstyles may change between short crop, side sweep, or cap-compressed hair. Never render photoreal fibers, flyaways, frizz, wet shine, sharp white streaks, thin strand highlights, noisy texture, scalp detail, or high-frequency sparkle.
- **Expression range:** calm, composed, quietly friendly. Never a wide grin, never sad, never surprised.
- **Material:** skin, hair, and fabric all obey the object brief's matte-to-satin language. Fabric is smooth moulded cloth with soft seam ridges; terry/towel fabric reads as fine uniform nubble, simplified. Gloss only as narrow satin highlights on hair and lips.

## Wardrobe Variants

The wardrobe IS the service cue. For the canonical variants below, reproduce the listed wardrobe exactly; do not restyle, recolour, or add accessories.

1. **InstaHelp (maid — India):** medium purple collared uniform dress with a small rounded collar; clean white square-bib apron over it. Hair in low bun. Eyes open.
2. **Maid for rent (Dubai only — live-out / all-in-one help):** royal/medium blue uniform dress with a mustard-yellow rounded collar; light sky-blue square-bib pinafore apron over it, exactly as in `maid-dubai.png`. Hair in low bun. Eyes open.
   - **Live-in variant (Dubai only):** same character and uniform, plus the small-house accent (see Accent Cues) placed beside the lower-right of the bust, as in `live-in-maid-dubai.png`.
3. **Premium helper (luxe/premium tier — India or any country):** black crossover/wrap top with a thin gold piping line tracing the lapel. No apron. Hair in low side ponytail. Eyes open.
4. **Women's salon & spa:** white terry bathrobe with shawl collar; cream towel turban wrapped on the head; smooth sage-green clay face mask covering the face with clean cut-outs around eyes, brows, lips; eyes closed (serene).
   - **Luxury variant:** same spa bust, plus the golden-sparkle accent (see Accent Cues), as in `luxury-female-salon-spa.png`.
5. **Men's salon & massage:** male character; white terry bathrobe with shawl collar; fluffy white shaving-foam beard around jaw and upper lip; two smooth sage-green under-eye gel patches; eyes closed (serene); short brown sculpted hair.

For new service-worker categories not listed above, create one clean role-specific uniform only when it is necessary for recognition. Keep it compact, professional, and readable: simple shirt/jacket/top, collar or apron if relevant, optional cap/hat only if role-defining, and no readable name tags, logos, badges, text, tools, weapons, or extra props. Use the canonical gender base as the source of face, crop, material, and hair fidelity; the new wardrobe is the editable service cue.

## Service-Cue Rules (character path)

- The uniform/wardrobe carries the service meaning. Maximum one *applied* treatment cue on the face or head (clay mask, foam beard, eye patches, towel turban) — these sit ON the character and never form a second focal mass.
- No handheld tools, no props beside the bust, no floating objects, no background environment — except the two sanctioned Accent Cues below.
- Treatment cues use the same matte material language: clay mask is smooth matte putty; foam is soft simplified meringue lobes; gel patches are satin with a single soft highlight.

## Accent Cues (the only allowed additions beside the bust)

Exactly two accents exist; use only when the variant calls for them, never both at once, never invented alternatives.

- **Small house (live-in maid only):** one miniature skeuomorphic cottage — smooth matte white/cream stucco walls, terracotta-orange tiled gable roof, simple wooden door, no windows needed — rendered in the same object-icon material language. Place it beside the bust at the lower-right, roughly shoulder height or below, clearly secondary (about one-third of the bust's height in visual weight). The character remains the single focal mass; the composition still reads as one icon silhouette. This is the only sanctioned second object mass on the character path.
- **Golden sparkles (luxury tier only):** two to three smooth four-point diamond sparkles in warm golden yellow with a soft satin gradient, floating around the upper half of the bust (e.g. upper-right large, mid-left and lower-right smaller). They are flat-ish accents, not objects — keep them small, clean, and asymmetric; never a halo, ring, or particle cloud. Used to mark a luxury/premium tier of an existing variant (e.g. luxury women's salon & spa).

## Camera, Lighting, Grounding

Use the resolved base's straight front bust view, crop, optical scale, material finish,
lighting, and legacy source treatment. Ordinary base edits preserve the base treatment.
For a newly redesigned character master, use exact `#f5f5f5` with no external cast,
contact, drop, or floor shadow, glow, or ambient grounding pool; internal self-shadow,
occlusion, and material shading remain allowed. Request a high-quality opaque
`2048x1536` PNG master and derive the `1024x768` delivery with the exporter.

## Character Avoid List

In addition to the brief's global avoid list: real-person likeness or celebrity resemblance; photoreal skin, pores, or hair strands; uncanny realism; hyper-cartoon or toy/Funko exaggeration; open-mouth smiles or teeth; arms, hands, or full body; jewellery, glasses, name tags, badges, logos or text on uniforms; varying the skin tone, face, or hair colour between icons of the set; multiple characters in one icon; ¾ or side angles; head tilt; dramatic emotion.

## Edit Prompt (character path)

Use this in place of the object prompt. Provide the planner-selected edit-target PNG (exact service variant, canonical gender base, or explicitly supplied request-scoped base) to Image Gen edit mode. If that edit target cannot be supplied, stop; do not replace it with a loosely related service exemplar or text-only generation. Fill `<SERVICE>`, `<WARDROBE>` (copy verbatim from Wardrobe Variants for canonical variants; otherwise specify one compact role-specific uniform), `<EYES>` (`open, calm` or `closed, serene`), `<ACCENT>` (`none` for standard variants; copy the small-house or golden-sparkle description verbatim from Accent Cues for live-in / luxury variants), and `<BACKGROUND>`.

```text
Use case: UI category icon
Asset type: premium 3D skeuomorphic character app/web icon for a services marketplace (Urban Company)
Primary request: Edit the supplied base character icon to create the requested service variant. Preserve the base image's face family, proportions, crop, material finish, lighting, shadow treatment, optical size, and hair fidelity. Change only the service-specific wardrobe, treatment cue, sanctioned accent, background, and hairstyle shape if required by the service role.
Crop mode: default to the supplied base character's UC set-style bust crop. If an external person reference is also supplied, use it only for local requested details unless the user explicitly asked to match that reference crop/framing.
Subject: <SERVICE> — single character bust
Character: stylised designer-vinyl figurine bust — head, neck, shoulders, upper chest only, ending in a clean soft-rounded lower edge. Head slightly oversized (~40-45% of height), narrow soft shoulders. Light-medium warm beige skin, perfectly smooth matte vinyl, no pores or texture. Face includes only: thick soft sculpted dark-brown eyebrows; large almond dark-brown eyes with a single white catchlight; simple sculpted nose without nostril holes; full coral-pink lips in a calm closed micro-smile; simplified ears. Eyes: <EYES>. Hair: preserve the base image's satin-plastic / polished-clay fidelity: warm brown, strand-free sculpted masses, large simplified flow bands, broad soft curved highlights, shallow low-contrast grooves, rounded beveled edges; no individual fibers, flyaways, wet shine, sharp streaks, or noisy texture.
Wardrobe (exact, no additions): <WARDROBE>
Accent: <ACCENT>
Service cue: the wardrobe is the primary service cue. No handheld tools, no props, no second object mass beyond the specified accent (if any). Any treatment element (mask, foam, towel, patches) sits directly on the character in the same matte material language. If an accent is specified, it stays clearly secondary — the character remains the single focal mass.
Style language: tactile_skeuomorphic_micro-object — soft, premium, miniature 3D language between product rendering and iconography; matte-to-satin finish; satin gloss only on hair and lips.
Scene / background: <BACKGROUND> (default: fixed solid #f5f5f5 with no environment; preserve legacy source treatment for an ordinary base edit).
Camera / view: straight front view, centred, head-on at eye level, near-orthographic. No 3/4 angle, no head tilt.
Lighting / mood: preserve the supplied base lighting and source treatment for an ordinary edit. For a redesigned master, use soft front-top studio light, gentle contrast, broad premium highlights, and no external cast/contact/drop/floor shadow, glow, or ambient grounding pool; internal self-shadow and occlusion are allowed.
Quality: high-quality opaque 2048x1536 PNG master, polished premium UI icon, balanced margins, and consistent optical size; derive a 1024x768 delivery without upscaling a smaller native result.
Avoid: replacing the base character with a newly invented face; real-person likeness; photoreal skin or hair strands; uncanny realism; cartoon/toy exaggeration; teeth or open mouth; arms, hands, full body; jewellery, glasses, name tags, logos, text; different skin tone or face from the base image; multiple characters; side or 3/4 angle; dramatic emotion; busy environment; harsh shadows; flat 2D vector look.
```

## Set Consistency

When generating multiple character icons, hold constant across the batch: face, skin tone, hair colour, head:bust ratio, crop height, lighting direction, shadow treatment, background mode, and optical size. Only wardrobe, hairstyle (bun vs ponytail vs male crop), eyes open/closed, applied treatment cues, and sanctioned accent cues (house / sparkles) may vary.
