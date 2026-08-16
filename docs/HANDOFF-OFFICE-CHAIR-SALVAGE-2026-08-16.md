# UC Icons office-chair salvage and next-chat handoff

Date: 2026-08-16

Branch: `codex/uc-icons-v0.2.0-rc1`

Previous handoff: `docs/HANDOFF-v0.2.0-rc1.md`

## Read this first

Office-chair generation is paused. Do not generate or regenerate another office chair,
mesh visitor chair, transfer case, or replacement before the owner gives a new explicit
instruction.

The material-reference transfer for
`wave1-office-chair-material-formlocked-01` is incomplete and is not promotion evidence.
Keep the selected office-chair image as an approved ordinary icon/direction, quarantine
the unfinished transfer, and move to the basin-mixer approval batch unless the owner
specifically reopens this experiment.

No generated image has been committed or promoted. The runtime reference bank still has
zero rows and validates successfully. Candidate and workbench images are ignored local
artifacts; the paths below are for continuation in this workspace.

## What the generation count means

The workspace contains 79 distinct persisted source masters:

- 13 initial/replacement candidate masters under
  `evaluation/reference-bank/candidates/.generation/`;
- 24 frozen masters in the completed office-chair form-transfer evidence set; and
- 42 current or archived masters in the material-transfer workbench.

The owner's approximately 86 observed generations is credible because failed, partial,
or interrupted calls do not always leave a new canonical master. The 334 local PNG files
are not 334 generations: that number also includes deliveries, staged copies, blind
copies, reductions, and evidence copies.

This experiment used too many generations for one prospective reference. The retries
became evidence of systematic instability, not a reason to continue brute-force
sampling.

## Salvage safety model

Every retained image has exactly one of these uses:

| Tier | Meaning | May be supplied to Image Gen? | Runtime-bank eligible now? |
| --- | --- | --- | --- |
| A | Owner-approved ordinary icon or direction | Yes, request-scoped and role-explicit | No |
| B | Strict-QA-passing category curation candidate | Only after a fresh category/role decision | No |
| C | Material-only study with the wrong form | Only in base-edit mode with a correct hard-locked form | No |
| D | Rejected evaluator fixture or textual learning | No | No |
| E | Unreviewed or incomplete experiment output | No | No |

Passing visual QA means an asset is worth retaining; it does not silently promote it to
the reusable reference bank. A future promotion still needs one declared role,
technical validation, independent reviews, transfer evidence, and explicit owner
approval.

## Tier A — office-chair results worth keeping

### Selected corrected office chair

Reference record:
`evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/record.json`

Canonical master:
`evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/master.png`

Generation master:
`evaluation/reference-bank/candidates/.generation/office-chair-form-corrected/01/assets/office-chair-form-corrected-candidate-01-skeuo-uc-master.png`

Status and safe use:

- owner selected Candidate 1;
- independent QA passed at 4.7/5;
- preferred ergonomic office-chair form and material direction;
- safe as an ordinary office-chair icon or request-scoped office-chair direction;
- transfer remains incomplete, so it is not a reusable material reference.

### Original preferred office-chair form

Reference record:
`evaluation/reference-bank/candidates/wave1-office-chair-01-form/record.json`

Canonical master:
`evaluation/reference-bank/candidates/wave1-office-chair-01-form/master.png`

Generation master:
`evaluation/reference-bank/candidates/.generation/office-chair/01/assets/office-chair-candidate-01-skeuo-uc-master.png`

Status and safe use:

- owner and independent reviewer approved the visual;
- remains the preferred office-chair form authority for request-scoped editing;
- its completed blinded form-transfer test produced zero positive wins;
- therefore it is quarantined as an ordinary icon, never a runtime form reference.

### Secondary corrected office chair

Reference record:
`evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-02/record.json`

Generation master:
`evaluation/reference-bank/candidates/.generation/office-chair-form-corrected/02/assets/office-chair-form-corrected-candidate-02-skeuo-uc-master.png`

It passed independent QA at 4.5/5 after its corrupted mesh was regenerated, but the
owner chose Candidate 1. Retain it only as a secondary ordinary variant/material study.
It is quarantined and must not compete with the selected candidate or enter runtime
retrieval.

## Tier B — best category-specific salvage candidates

These images were independently inspected at native size and at 96/64/48/32 px. They
passed the hard form, pose/view, camera, optical scale, placement, lighting, material,
texture-density, palette, silhouette, artifact, and small-size gates. They did not prove
office-chair transfer; they are useful because they are individually good examples of
their own categories.

### Salon chair

Keep these as the strongest local salon-chair curation candidates:

1. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/salon-chair/baseline/run-3/assets/salon-chair-baseline-run-3-skeuo-uc-master.png`
   — 4.5/5, clean wide salon form, centered, restrained pedestal.
2. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/salon-chair/candidate/run-2/assets/salon-chair-candidate-run-2-skeuo-uc-master.png`
   — 4.5/5, broad channel-backed identity with controlled matte/satin separation.
3. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/salon-chair/candidate/run-3/assets/salon-chair-candidate-run-3-skeuo-uc-master.png`
   — 4.5/5, tall-backed variant with stable neutral treatment.

All six final salon-chair slots passed, so the other three active final masters may be
retained as secondary variety. The rejected-attempt directory is evaluator-only.

### Dining chair

Keep these as the strongest local dining-chair curation candidates:

1. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/dining-chair/candidate/run-2/assets/dining-chair-candidate-run-2-skeuo-uc-master.png`
   — 4.5/5, clean fixed four-leg form and stable fabric/frame separation.
2. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/dining-chair/candidate/run-3/assets/dining-chair-candidate-run-3-skeuo-uc-master.png`
   — 4.5/5, centered channel-back variant with controlled light and materials.
3. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/dining-chair/baseline/run-1/assets/dining-chair-baseline-run-1-skeuo-uc-master.png`
   — 4.5/5, familiar fixed four-leg dining identity.

All six final dining-chair slots passed. The three above are the best first review set;
do not introduce every variation into a bank.

### Sofa

Keep these as the strongest local sofa curation candidates:

1. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/sofa/baseline/run-1/assets/sofa-baseline-run-1-skeuo-uc-master.png`
   — 4.5/5, strongest broad two-seat silhouette.
2. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/sofa/candidate/run-3/assets/sofa-candidate-run-3-skeuo-uc-master.png`
   — 4.5/5, clean frontal sofa with coherent footprint and no chair leakage.
3. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/sofa/baseline/run-3/assets/sofa-baseline-run-3-skeuo-uc-master.png`
   — 4.5/5, controlled charcoal fabric and stable scale.

The final active set eventually reached six passes. Candidate run 1 passed only after
repeated scale/placement correction and should remain secondary; its rejected attempts
are evaluator fixtures, not references.

### Mesh visitor chair

Use only the four previously reviewed passes from the archived `identity-v1` set:

1. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/mesh-visitor-chair/policy-restarts/identity-v1/baseline/run-2/assets/mesh-visitor-chair-baseline-run-2-skeuo-uc-master.png`
   — 4.5/5, strongest clean fixed-leg visitor-chair identity.
2. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/mesh-visitor-chair/policy-restarts/identity-v1/candidate/run-3/assets/mesh-visitor-chair-candidate-run-3-skeuo-uc-master.png`
   — 4.0/5, correct sled visitor-chair form and stable mesh.
3. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/mesh-visitor-chair/policy-restarts/identity-v1/candidate/run-2/assets/mesh-visitor-chair-candidate-run-2-skeuo-uc-master.png`
   — 4.0/5, correct sled identity; no office mechanism leakage.
4. `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/mesh-visitor-chair/policy-restarts/identity-v1/baseline/run-1/assets/mesh-visitor-chair-baseline-run-1-skeuo-uc-master.png`
   — 4.0/5 after scale correction, uniform mesh, fixed four-leg form.

The six currently active mesh masters were generated after a full identity-policy reset.
Their technical files passed, but the independent visual review was deliberately
interrupted when the owner paused the experiment. Classify all six as Tier E/unreviewed;
do not use them as references without a fresh blind-only review, and do not generate any
replacements while reviewing them.

### Secondary frozen salvage pool

The completed form-transfer evidence set contains 24 strict-QA-passing images under:

`evaluation/reference-bank/candidates/wave1-office-chair-01-form/transfer-workbench/evidence/artifacts/`

Its ratings are recorded in:
`evaluation/reference-bank/candidates/wave1-office-chair-01-form/transfer-workbench/evidence/transfer.json`

Every slot scored 4.0–4.5 without critical regression or form leakage. Preserve the set
as a dedupe/curation pool for salon chair, dining chair, mesh visitor chair, and sofa.
It showed no positive transfer win for the office-chair form candidate, so never cite it
as proof that the office-chair reference worked.

## Tier C — material studies that can still be useful

The modern fixed-chair batch is visually clean but categorically wrong for an office
chair. Its records are intentionally quarantined:

- `wave1-seating-material-01`: 4.6/5, strongest neutral material separation;
- `wave1-seating-material-02`: 4.2/5, coarser stable mesh; owner liked its materials;
- `wave1-seating-material-03`: 4.4/5, corrected scale; owner liked its materials.

Canonical generation masters:

- `evaluation/reference-bank/candidates/.generation/office-chair-material/01/assets/seating-material-candidate-01-skeuo-uc-master.png`
- `evaluation/reference-bank/candidates/.generation/office-chair-material/02/assets/seating-material-candidate-02-skeuo-uc-master.png`
- `evaluation/reference-bank/candidates/.generation/office-chair-material/03/assets/seating-material-candidate-03-skeuo-uc-master.png`

Safe salvage:

- use Candidate 2 or 3 only as a request-scoped material cue;
- supply a separate correct-form base and explicitly declare the material-only role;
- hard-lock the base silhouette, parts, pose/view, camera, scale, and placement;
- keep the distilled recipe: medium graphite mesh, neutral-gray woven fabric, charcoal
  matte molded plastic, restrained dark satin connectors, low-to-moderate texture;
- never use these images as office-chair form, category, or combined style authority.

Because prior material transfer repeatedly leaked structure, prefer the textual material
recipe over attaching these images when a clean base edit can express the same intent.

## Tier D — how to use failures without negative visual prompting

Image Gen has no reliable semantic role for “this attached image is what must not be
generated.” Supplying a structurally wrong image can reinforce the very feature being
rejected. Therefore rejected images must not be attached to generation prompts.

Use them in three safer ways:

1. **Textual rule extraction.** Convert each observed failure into a short, concrete
   prompt or validator constraint. Apply only the rules relevant to the requested
   subject.
2. **Evaluator regression fixtures.** Keep rejected images with failure tags so future
   reviewers and automated checks must reject the same defect consistently.
3. **Failure telemetry.** Track repeated defects by subject and arm. Repetition across
   both arms is evidence of an unstable identity/policy and a stop condition, not an
   invitation to sample indefinitely.

Reusable textual rule dictionary:

| Failure tag | Distilled instruction/check |
| --- | --- |
| `lighting-key-reversed` | Key light must remain soft above-left/front; reject right-heavy or reversed highlights. |
| `mesh-high-frequency` | Use one uniform medium-graphite mesh field with low-to-moderate texture; it must reduce tonally at 48/32 px without moire. |
| `mesh-pseudo-glyph` | Reject bands, glyph-like cells, mottling, rectangular patches, or irregular weave modulation at native size. |
| `lumbar-office-leakage` | For a visitor chair, keep one uninterrupted back panel; reject lumbar pads, curved bands, braces, ribs, controls, casters, or star bases. |
| `under-scale` | Match the approved family footprint and symmetric margins; reject visibly smaller optical mass. |
| `low-placement` | Match the family optical center; reject a low object even when the canvas is technically unclipped. |
| `over-wide` | Preserve comfortable symmetric side margins at 32 px; reject a silhouette that presses against the frame. |
| `bright-metal-dominance` | Keep metal dark and satin/restrained; reject bright chrome or specular hardware becoming the visual authority. |
| `external-shadow` | Keep the exact pale-neutral background clean; reject cast shadow, floor pool, glow, or halo. |
| `category-form-drift` | Restate the exact parts and silhouette of the target before materials; material references cannot redefine identity. |

Rejected/evaluator-only roots include:

- `evaluation/reference-bank/candidates/.generation/office-chair-material/rejected-attempts/`
- `evaluation/reference-bank/candidates/.generation/office-chair-form-corrected/rejected-attempts/`
- `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/raw/*/*/rejected-attempts/`
- `evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/blind-rejected/`
- failed slots inside archived mesh policy-restart directories.

Structurally wrong assets stay entirely outside the positive-reference pool. Duplicate,
partial-export, and prompt-policy-mismatch artifacts are process diagnostics only.

## Exact pause point

The unfinished material-transfer workbench is:

`evaluation/reference-bank/candidates/wave1-office-chair-material-formlocked-01/transfer-workbench/`

It contains 24 active hash-valid technical masters, but no completed final blind review
and no `transfer.json` suitable for recording. The six active mesh slots are the
unreviewed post-reset outputs. Do not derive an arm mean, winner, or promotion decision
from this partial state, and do not cherry-pick the many retries as formal evidence.

Recommended decision: close/quarantine this transfer as incomplete, retain the selected
office chair as an ordinary icon, and spend no more generations on its promotion.

## Next-chat checklist

1. Read this handoff and `docs/HANDOFF-v0.2.0-rc1.md`.
2. Confirm the branch and that the runtime bank is still empty/valid.
3. Do not resume office-chair or mesh transfer generation.
4. Treat the selected corrected office chair as an ordinary approved visual, not a
   runtime reference.
5. If category-bank curation is later requested, start with only the Tier B top picks,
   dedupe them, declare one role per asset, and ask for category-specific owner approval.
6. Keep all image artifacts local and uncommitted until the owner explicitly approves
   what should be retained.
7. Continue with the basin-mixer approval batch.

## Bounded basin-mixer approval flow

Use a small approval batch, not another full transfer experiment:

1. Generate at most three initial basin-mixer candidates.
2. Hard-lock target identity, exact parts, straight/front-compatible pose, camera angle,
   projection, optical scale, placement, lighting direction/softness, material finish,
   texture detail, and palette roles.
3. Scan each output at native size and 96/64/48/32 px before showing it. Reject form,
   lighting, material, texture, color, scale, placement, shadow, text, or clipping drift.
4. Allow at most one targeted retry per failed slot: three initial calls plus no more
   than three retry calls.
5. Show only the passing candidates and let the owner select at most one ordinary icon.
6. Keep all generated assets uncommitted.
7. Stop after selection. Reference promotion is a separate owner decision.

If the owner later requests a transfer pre-gate, first use one run per arm across three
positive cases and one negative control: eight images maximum. Run the full 24-image,
three-runs-per-arm gate only after the quick gate wins and the owner explicitly approves
that cost. Repeated systematic drift is an immediate stop/quarantine condition.

## Do not do

- Do not use structurally wrong images as visual “negative prompts.”
- Do not use a modern fixed chair as office-chair form authority.
- Do not turn a visually good transfer output into a reusable reference for another
  category without a new role-specific review and owner approval.
- Do not promote, install, merge, tag, or commit generated images from this handoff.
- Do not restart an uncapped retry loop.
