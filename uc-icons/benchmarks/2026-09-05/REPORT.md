# UC Icons render benchmark — 2026-09-05

**Later user review rejected the plumber, hood and both chef attempts.** The observations below are the historical first-pass model review, not acceptance. Two object candidates are now rejected; only the extractor remains pending. See [corrections](CORRECTIONS.md).

Four first-pass cases plus one targeted character edit, using built-in Image Gen and skill commit `0961b3e`. This is a new baseline, not a before/after generation-speed claim. Outputs are model-reviewed candidates; none has user approval.

[Open the visual review](index.html) · [Exact prompts, input roles, hashes and measurements](benchmark.json)

| Case | Image Gen seconds | Export seconds | Review |
|---|---:|---:|---|
| upholstery-extractor | 27.139 | 0.093 | First-pass model review: one coherent machine; dense rubber/plastic microtexture is more realistic than simplified UC styling. Category specificity still needs user review. |
| chimney-hood | 31.491 | 0.091 | First-pass model review: recognizable single hood close to existing archive form; brushed texture more pronounced. Existing archive remains preferred for ordinary export. |
| tap-and-wrench | 24.879 | 0.090 | First-pass model review: tap dominates and wrench supplies a clear repair cue. Tap is predominantly side-profile with outlet underside visible despite strict-front request. Chrome reflections are denser than the matte-to-satin brief. |
| female-chef | 22.297 | 0.089 | Chef role reads clearly; open eyes, side ponytail and UC face family retained. Oversized hat leaves only a narrow top margin and the bust fills nearly the whole image height. One focused hat-size correction requested. Exact pixel identity is not established. |
| female-chef-retry | 23.856 | 0.105 | Hat height and top margin improve visibly. Face remains in the UC family but the edit also subtly changes facial proportions and folds; exact preservation is not established. Bottom margin remains tighter than object candidates. |

First-pass render median: **26.01s** (n=4). First-pass tool time totals **105.81s**; five calls including the retry total **129.66s**. Timing surrounds the tool call only and excludes planning, inspection, polling and communication. Export median **0.090s**, including decode, full-frame contain/composite and PNG write.

All five workspace exports are 1024×768, RGBA and opaque. Background requested as #f5f5f5; measured perimeter agreement varies from 0% to 30.1%. No background cleanup or retry for background pixels was performed. This edge metric does not validate the whole background.

The library gains three **pending** object candidates covering clear plastic/rubber, brushed steel, polished chrome, a frontal single product and a primary item with a secondary repair cue. Original 72 archive masters remain unchanged. Pending rows cannot enter runtime reference retrieval. Character results are benchmark evidence only.

The extractor and tap used imperfect legacy material matches (nail polish and truck respectively). The prompts restricted transfer to material appearance. The hood used its form master plus dumbbell steel; it remains a forced-new-generation regression case, while an ordinary chimney request should export the archive. Forward testing found and fixed the missing `chimney hood` alias.

Next evaluation priorities: user selection by role; a held-out subject for any selected material/composition reference; softer extractor surfaces, controlled tap reflections and deliberate camera choice; then selected ceramic/enamel, textile/leather, stone/plaster and additional composition exemplars. Do not claim those coverage gaps are filled by this pilot.

Validation: 46 regression tests and the reference validator passed after candidate intake. Three candidate hashes are indexed as pending. No universal UC style rules were inferred from a single generated sample.
