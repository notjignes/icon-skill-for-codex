# UC Icons reference promotion rubric

Candidate review is deliberately separate from ordinary runtime generation. Two
independent reviewers must approve the same frozen master and record useful notes.

## Technical gate

- PNG, opaque, 4:3, at least `1024x768`; keep the native high-resolution master.
- Exact `#f5f5f5` border and at least 99.5% exactness across the connected pale-neutral
  background component.
- Valid source/master hash, portable provenance, and no path traversal or missing file.
- No clipping, text, logo, branding, watermark, or unintended extra mass.
- Automated background checks do not certify “no shadow.” External shadow/glow remains
  a mandatory human binary check.

## Visual critical gates

- Correct subject family and canonical subtype.
- Correct `view`, `layout_axis`, `projection`, `composition_family`, and mass count.
- Full silhouette and recognition without a label at 64x48 and 48x36.
- No external cast/contact/drop/floor shadow, glow, or ambient grounding pool. Internal
  self-shadow, occlusion, and material shading are allowed.
- No form leakage from generation references.
- Pose/view, camera angle, projection, optical scale, and canvas placement match the
  active family lock.
- Light direction and softness, texture-density band, material finish, and palette
  roles remain consistent with the family. A drifting run is excluded and regenerated
  before blind scoring; it is never repaired through export normalization.

Review at full size plus 32, 48, 64, and 96 pixels. Compare in an equal-size row with
at least six nearby approved icons; also inspect silhouette, grayscale, slight blur,
palette, visual centroid, margins, lighting, bevel softness, and material roughness.

## Transfer gate

For the shortlisted candidate, run the same prompt/model policy with and without the
reference on three non-identical positive held-out subjects and one negative control,
with three generations per arm. Blind and shuffle the comparisons. Preserve distinct,
hash-locked opaque 4:3 PNG artifacts at least 1024×768 in the external workbench.
Record one finite 1–5 decimal rating for every blind ID, with the ratings covering each
case's `blind_order` exactly once. Baseline and candidate means are derived from those
per-run ratings; any supplied aggregate must match the derived value exactly. A declared
win requires at least a 0.4-point margin. Schema-v2 installed evidence preserves blind
IDs, artifact hashes, ratings, derived aggregates, and shuffle order while omitting every
artifact path, so the transfer decision remains independently reconstructible.

The evidence JSON must bind every arm to one shared generation policy: record the
model, SHA-256 of the prompt template, SHA-256 of the generation configuration, and
declare `arm_difference: candidate-reference-only`. Changing prompts, models, quality,
or other settings between arms invalidates the transfer test.

The shared generation policy must also encode the active family locks. Every artifact
must be checked against those locks before it enters the blinded set. If either arm
drifts in pose/view, camera, lighting, texture detail, palette roles, optical scale, or
placement, discard and regenerate that run under the same frozen policy.

Promotion requires:

- the reference wins at least two positive subjects;
- zero critical regressions;
- zero form leakage on the negative control;
- two independent approved visual reviews;
- explicit owner approval with reviewer identity and note.

One logical candidate tests one role. A single physical master can be tested under a
second logical ID for another role, and approved records then share the same master
SHA/path without duplicate image bytes. Runtime `good_for` permissions are derived
only from positive held-out families that win; proposals and ties grant nothing.

Anything else remains `candidate`, becomes `quarantined`, or is `deprecated` when a
reviewed replacement supersedes it. Runtime selection reads only approved records.
