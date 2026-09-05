---
name: uc-icons
description: Generate, edit, export, or maintain Urban Company Waterlemon tactile skeuomorphic icons and their approved reference bank. Use for UC icons, Skeuo-UC icons, and UC category-object or service-character icons; not unrelated product photos or SKU scenes.
---

# UC Icons

Create one recognizable UC service/category icon per request. Prefer exact archive export, then a compatible base edit, then new object generation. Keep object identity separate from material/style resemblance.

## Contract

- Deliver a 1024×768 PNG in `./assets/` relative to the user's workspace. Keep the complete source frame, proportions, comfortable margins and optical balance.
- Request a solid `#f5f5f5` background during generation. Export only resizes/contains and composites existing alpha onto that color. **Never automatically remove backgrounds or shadows, segment by color, flood-fill, replace pale pixels, or auto-crop.** Background removal is separate manual post-processing unless explicitly requested. Preserve imperfect rendered backgrounds; do not trigger corrective generation just to force exact pixels.
- New objects: one centered premium tactile 3D micro-object, soft studio light, believable simplified matte-to-satin materials, softened edges, compact palette. Request no cast/drop/contact/floor shadow. Preserve existing shadows in base edits and archive exports.
- Keep the subject recognizable at UI size. No rooms, scenes, tabletop styling, hands, readable text, logos, watermarks or clutter. Object plus service cue: at most two visual masses; the tool remains secondary.
- People-centric subjects use canonical UC character busts. Preserve face family, crop, proportions, hair fidelity and material finish; never invent a replacement identity by default.

## Input and reference isolation

The working directory is an output destination, not a reference bank. Use only bundled UC Icons images, a user-attached/named image, explicitly selected Icon Launch archive inputs, and the exact output of the current image call. Do not search home/workspace/generated-image folders or other tasks for an input. In SKU workspaces, do not load SKU entrypoints, Visual Director, historical sheets or taste evidence.

Pass local inputs only through explicit `referenced_image_paths`; never use `num_last_images_to_include`. Inspect the exact chosen edit target if the runtime requires it; do not browse unrelated candidates. Never infer a generated source by modification time. A current image result without an explicit local source path blocks export; report it plainly.

## Represent the category first

When the user names a service rather than an object, decide what visual best identifies that category before looking up an asset. Prefer one product/item: a chimney hood for chimney service, a dedicated upholstery extractor for upholstery cleaning. Use a second tool/item only when the first could imply the wrong category: a tap plus one wrench can distinguish plumbing repair from tap shopping. Keep a clear primary mass and subordinate cue; never add a prop just to decorate or fill space. Preserve an explicitly requested subject. Exact known service aliases still export their approved archive icon.

Internally record the service, chosen primary item, optional secondary item and why it is necessary. Pass the service using `--service` alongside the chosen `--subject`; the generation prompt must retain both. People-centric categories keep their established canonical-bust exception.

The user identifies Airbnb's skeuomorphic icon language as the inspiration: dimensional, tactile, miniature and approachable, translated into the UC family. UC archive masters remain the visual authority. Do not copy Airbnb logos, import its imagery as approved references, or force every icon into an isometric view. During a visual test, inspect the actual selected inputs and outputs; fix demonstrated inconsistencies with one focused edit rather than accumulating new universal rules.

## Resolve the request once

Parse the subject by meaning. Put requested modifications into `--change`; do not let a tool or material replace the main subject. An explicitly named source image takes precedence over archive matching: use that exact permitted path as the source/base, and preserve its identity.

Run one planner command, relative to this skill's directory:

```bash
python3 "<SKILL_DIR>/scripts/plan_icon.py" --subject "<OBJECT OR EXACT SERVICE NAME>" --change "<REQUESTED EDIT, IF ANY>"
```

Optional arguments: `--service "<SERVICE CATEGORY>"` to retain category intent; `--new-design` when explicitly requested; `--gender female|male`; `--eyes open|closed`; `--material "<material/finish>"`; `--composition front|wide-side|slight-top|three-quarter|crossed-pair`. Do not invent a gender or pass a composition override unless the brief chooses one. Keep the default reference budget of two; increase `--max-refs` only when distinct reference roles justify it.

Follow the returned operation:

- `export_existing`: export `base_path` directly; no Image Gen or prompt construction.
- `base_edit`: use `base_path` as the actual edit target, not merely a style reference. Retain the subject plus every requested change. Preserve all untouched content; only an explicit composition override releases the corresponding crop/view constraint.
- `new_generation`: use the returned prompt, selected references and their transfer roles. Missing coverage is honest; do not attach arbitrary substitutes. Load `references/skeuo-uc-brief.md` only when additional style language is needed.
- `ask_user`: ask the returned question about identity/variant. Do not guess among valid candidates. Clarify an unknown main subject rather than interpreting it as a superficially similar base.
- `blocked`: state the missing required asset/capability. Do not silently invent a character or substitute another generator.

Examples: `water purifier` asks normal versus Native RO; `native RO water purifier` exports the Native asset; `Spa for women --change "remove towel; upholstery beige"` edits the massage bed. `female chef` edits the canonical female open-eyes bust. `office chair`, `gift box`, or `black van` must not become a sofa, truck, or massage-table edit because of color or token overlap.

Legacy `find_base_object.py` and `find_generation_references.py` remain callable; ordinary runs need only the planner. Its rules are conservative helpers, not permission to discard details from the user's actual brief.

## Compose and render

Default new-object view: straight front, near-orthographic. Wide/long subjects such as vehicles, sofas, beds and benches use a level side profile. Tall/compact subjects remain front-facing; slight top visibility is allowed when needed for recognition. Base edits preserve the source view. Explicit composition choices override these defaults without changing UC material style or adding a scene. For unusual silhouettes, infer the actual main object first and pass the appropriate supported composition.

Read `references/skeuo-uc-characters.md` only for character edits. It contains canonical eye-state, outfit, treatment and accent guidance. New characters always edit a canonical base, even with `--new-design`. Use an external person reference for local clothing/treatment cues; preserve the UC crop unless the user explicitly requests its framing. Do not copy a real person's likeness.

Base-edit prompt:

> Edit the supplied UC icon base to depict <SUBJECT>. Change only <REQUESTED CHANGES>. Preserve <PLANNER PRESERVATION CONSTRAINTS> and all untouched details. Keep the source viewpoint/crop unless explicitly overridden. Preserve existing shadows; do not add shadows to a shadowless base. Request solid #f5f5f5 background, premium UC material fidelity, no text, logos, scene or unrequested props.

For raster generation/editing, apply the system `imagegen` skill automatically as an internal dependency. Prefer the built-in Image Gen path; follow companion discovery guidance if necessary. Do not switch models, CLI generators or placeholder SVG/HTML without explicit user approval. Required base-preserving edits cannot degrade to text-only generation when image input is unavailable.

## Export and delivery

Use only the explicit source returned by the current image call, or the selected archive/user PNG:

```bash
python3 "<SKILL_DIR>/scripts/export_skeuo_uc_icon.py" --subject "<SUBJECT>" --source "<EXACT_PATH>"
```

`--preserve-source` remains a compatible alias for the same non-destructive export. Explicit `--background "#RRGGBB"` changes canvas/compositing color; `--background transparent` retains existing alpha. Neither removes an opaque background.

Confirm actual saved path, dimensions, mode and opacity. `canvas_background` identifies the canvas color; `perimeter_match_fraction` measures only the outside edge, not all background pixels. Do not claim exact background validation when the rendered pixels differ. Show the final icon with concise factual delivery details.

Batches: resolve each subject separately, then render/export one at a time with consistent material, light, composition family and optical scale. Keep source paths associated with their own calls.

## Library maintenance

For audits, skill updates or reference intake, communicate findings normally; image-only delivery restrictions apply to rendering tasks. Read `references/reference-library.md` for catalog fields, source roles and approval flow. Use `scripts/validate_reference_bank.py` after changes, not before every icon. Never promote incidental outputs or external photos into style authority automatically.

## Quiet rendering updates

Ordinary generation/edit/export runs are silent apart from a small icon fact and the final asset. No setup narration, reference previews, tool summaries, progress labels or implementation chatter. Prefer one fact initially; use another only if the runtime requires a long-running update. Choose without a randomization tool call, and do not repeat a visible fact in the same conversation. State genuine blockers directly.

Codex owns tool-call cards and required inspection telemetry. A skill can suppress assistant narration, not hide those cards; never promise an invisible tool run or disable required inspection to simulate one. Maintenance/research requests may report their findings normally; the render phase uses facts only.

Format: `✦ Tiny icon fact: <FACT>`. Historical facts below are verified in `references/icon-history-sources.md`; do not browse or load that source file during ordinary rendering. Use only the approved wording, without embellishing dates or anecdotes.

- Susan Kare borrowed Apple’s Command symbol from a Swedish sightseeing sign she found in a symbol dictionary.
- Susan Kare developed early Macintosh graphics by colouring squares on graph paper.
- Annette Wagner enlarged Apple’s Dogcow spots so users could spot a 2% print-size reduction.
- Apple Lisa’s rectangular pixels helped push Annette Wagner to replace awkward 3D icons with flatter designs.
- On Xerox Star, users could print by moving a document icon to a printer icon.
- Xerox Star’s designers picked icons by looking around their office: documents, folders and file cabinets.
- Kurita’s 1999 emoji fit into 12×12-pixel grids; NTT DOCOMO released 176 of them.
- Kurita’s original 176-emoji set contained just five faces: happy, sad, angry, disappointed and dizzy.
- “Emoji” combines the Japanese words for “picture” and “character”—its name does not come from “emotion.”
- The Bluetooth symbol combines two runes representing H and B, the initials of King Harald Bluetooth.
- Paul Rand’s 1981 IBM rebus spelled the company’s name using an eye, a bee and the letter M.
- The recycling symbol began as architecture student Gary Anderson’s winning entry in a 1970 design competition.
- Gerald Holtom built the peace symbol from semaphore signals for N and D: nuclear disarmament.
- The wheelchair accessibility symbol gained its circular head when Karl Montan modified Susanne Koefoed’s original design.
- The forward-leaning Accessible Icon began as a street-art campaign placing transparent stickers over existing accessibility signs.
- Tokyo’s 1964 Olympics used 59 pictograms: 20 for sports and 39 to help visitors find their way.
