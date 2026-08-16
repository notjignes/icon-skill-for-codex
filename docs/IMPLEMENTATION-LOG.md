# UC Icons v0.2.0-rc.1 implementation log

This ledger records reversible implementation boundaries on
`codex/uc-icons-v0.2.0-rc1`. It does not authorize installation, promotion, merge, or
release. Git commit IDs are added as each boundary is committed.

## Reversible commit boundaries

- `67a0aaa` — resolver/storage locks and tests.
- `4d15847` — base/material alias migration and compatibility wrappers.
- `185d6d4` — character alias manifest and duplicate removal.
- `e177436` — deterministic planner, adversarial routing fixes, and silent UX.
- `a8c1020` — high-resolution master and delivery export workflow.
- `fc60bcc` — approval-gated bank/evaluation tooling and schema-v2 transfer evidence.
- Documentation, CI, atomic installer, and this audit ledger — the commit containing
  this file.

## 2026-08-16 — Compact legacy storage

- Kept the 72 legacy high-resolution PNG masters byte-for-byte in the service archive.
- Replaced physical base, material, and character copies with contained manifest aliases.
- Preserved 73 service identities, 70 base mappings, 72 material mappings, and 11 character names.
- Added SHA locks, safe relative-path resolution, exact Pest Control Dubai alias handling,
  and pixel-equivalence/storage tests.
- Verified compact baseline: `174,841,049` bytes, 72 PNG paths, 72 unique hashes.

Rollback boundary: restore the alias manifests and character PNG deletions together;
the untouched archive remains the byte source of truth.

## 2026-08-16 — Deterministic routing and silent runtime

- Added identity-first service/base/character planning and compatibility wrappers.
- Added token-boundary and unsafe-suffix gates, controlled variants, explicit ambiguity,
  request-scoped reference precedence, role-distinct retrieval, and abstention on filler.
- Preserved all 73 service identities across explicit local edits, including natural
  action clauses such as remove/add/replace/turn.
- Prevented object requests from selecting human bases and prevented human/avatar/gender
  requests from entering object generation.
- Kept exact exports silent and limited Image Gen progress to the single approved line.

Rollback boundary: planner, ontology, wrappers, runtime instructions, and routing tests
must move together.

## 2026-08-16 — High-resolution export contract

- Added explicit-source export, native master preservation, no-upscale behavior, and
  derived `1024x768` delivery output.
- Added opaque/background validation, palette-transparency handling, and rejection of
  falsely certified dark backgrounds.
- Kept exact legacy exports pixel-equivalent and without a duplicate master output.

Rollback boundary: exporter, image contract, skill instructions, and exporter tests
must move together.

## 2026-08-16 — Approval-gated reference lifecycle

- Kept candidates outside the installed skill and excluded them from normal retrieval.
- Required PNG/opacity/background gates, two normalized independent visual reviewers,
  three held-out transfer cases plus a negative control, score margins, explicit failure
  booleans, and owner approval.
- Bound transfer arms to a shared model/prompt/config fingerprint and reconstruct
  installed evidence from a strict path-free allowlist.
- Added atomic promotion/rollback, provenance hashing, bank-content versioning, and
  candidate/runtime containment checks.
- Promoted zero references; the Wave 1 queue remains awaiting generation and owner review.

Rollback boundary: bank manager, runtime schema, benchmark, rubric, and lifecycle tests
must move together.

## 2026-08-16 — Adversarial hardening checkpoint

- Preserved canonical service identity across natural action clauses and rejected hidden
  second objects between repeated identity tokens.
- Made all service-character display names and safe aliases resolve their locked archive
  master; unchanged variants export silently and requested changes use the character path.
- Made every emitted ambiguity choice safely resumable, including purifier variants,
  base colors, avatar eye state, character/object cleaner choices, and from-scratch output.
- Rejected purifier variant suffix compounds such as cover/shelf/stand.
- Added exact decimal transfer-score boundaries, strict blind-order length/uniqueness,
  explicit binary failure fields, normalized reviewer identity, generation-policy
  fingerprints, and strictly path-free installed evidence.
- Changed the “touch grass” copy from mandatory text to an example of one concise,
  playful modern waiting line; exact exports remain silent.

Rollback boundary: keep the planner, manifests, skill contract, bank manager, tests, and
handoff together because each regression documents a routing or approval invariant.

## Verification snapshot at pause/handoff

- Unit/regression suite: 78 tests passed in 114.408 seconds.
- Compact validator: passed.
- Legacy pixel equivalence: 72/72 passed.
- Runtime bank validator: passed with zero approved references.
- Compact skill size: `174,850,354` bytes.
- `git diff --check`: passed; no `__pycache__` or `.pyc` residue found.
- Installed skill: intentionally unchanged.

The worktree is intentionally left uncommitted on the feature branch for the next chat
to inspect as one frozen checkpoint before creating reversible commits.

## 2026-08-16 — Independent hash-frozen audit and adversarial closure

The continuation chat hashed the planner, character manifest, ontology, runtime-bank
manifest, and complete tests tree before any edit. All five values matched the handoff:

```text
7bc529758d50e7d00990c29d3472c2b334e08116f19dfa711c3eecc7f8cfe7fc  uc-icons/scripts/plan_icon_request.py
5dd3d270c5540008c90c2d05e2c37b839b6634951b728dfd268b5f37832e1942  uc-icons/references/characters/MANIFEST.csv
798db13d0712fb60ee3615f07328a58b789081a22938db408734879c26931b49  uc-icons/references/routing/ontology.json
d7872b9967f726cd824e3abd3dbd1995fcc53b3d8749e9cd3f2f9116c0134eb4  uc-icons/references/reference-bank/MANIFEST.csv
783a2bd9edd7a16524fac91ac888f562186d919fc09d40d61036f87e9538be3f  aggregate tests-tree hash
```

One uninterrupted matrix then passed 78 tests in 114.908 seconds, the compact validator,
all 72 pixel-equivalence probes, the empty runtime-bank validator, both diff checks, and
the cache-residue check. The five post-audit hashes were identical to the pre-audit
values, certifying the inherited checkpoint before changes.

The handoff's deferred adversarial probes reproduced seven release blockers, all fixed
with regressions before publication:

- `impact driver` no longer becomes a character merely because its object identity
  contains `driver`; explicit residual person cues still enter the character path.
- Identity-unsafe compounds receive no automatic bank reference in any role.
- Request-scoped references must be non-symlinked, decodable images.
- Canonical and bank-contained resolvers reject symlink leaf and parent components
  before dereferencing.
- Runtime validation rejects orphan assets, provenance, evidence, and prompt files while
  continuing to allow multiple logical roles to share one physical master.
- Global and row bank versions must equal the release-bound content-derived version;
  an empty bank uses the exact unsuffixed skill version.
- Transfer evidence schema v2 records a finite 1–5 rating for every blind run, derives
  arm means and winners, rejects forged aggregates, and preserves ratings in the
  path-free installed record.

No Wave 1 candidate, reusable reference, Image Gen test output, or ordinary generated
asset was created or promoted during this closure.

Rollback boundary: keep each added regression with its resolver, planner, or bank layer.
The rating schema, portable evidence allowlist, promotion checks, and rubric move as one
approval-lifecycle boundary.

## Final post-fix certification

The complete matrix was rerun without interruption after blocker closure:

- Unit/regression suite: 88 tests passed in 174.177 seconds.
- Compact validator: passed with 72 physical legacy PNGs, 72 unique hashes, and
  `174,858,133` bytes.
- Legacy pixel equivalence: all 72 locked masters passed.
- Runtime bank validator: passed with zero approved references.
- `git diff --check` and staged diff checks: passed.
- No `__pycache__` or `.pyc` residue was present.

Post-fix pre/post hashes were identical:

```text
43a6c0857c22208d7bf6e37769692be5864d3442c83d52590dc32b8c4715dbcd  uc-icons/scripts/plan_icon_request.py
5dd3d270c5540008c90c2d05e2c37b839b6634951b728dfd268b5f37832e1942  uc-icons/references/characters/MANIFEST.csv
798db13d0712fb60ee3615f07328a58b789081a22938db408734879c26931b49  uc-icons/references/routing/ontology.json
d7872b9967f726cd824e3abd3dbd1995fcc53b3d8749e9cd3f2f9116c0134eb4  uc-icons/references/reference-bank/MANIFEST.csv
0b7a477e32d60ecbbcc150e56209a6e46d0db0823b1960818404b6e850589452  aggregate tests-tree hash
```

Verdict: release-candidate code is audit-certified for draft-PR review. Installation,
merge, tag, stable release, and reusable-reference promotion still require explicit
owner approval.

## 2026-08-16 — Owner-directed family-lock enforcement

- Made pose/view, camera angle, projection, optical scale, and placement hard locks for
  candidate batches and transfer arms.
- Locked light direction and softness, texture-density band, material finish, and
  palette roles so related outputs remain visually coherent.
- Required drifting outputs to be excluded and regenerated with a targeted correction
  before export, staging, or blind scoring; export normalization cannot certify or hide
  family drift.

Rollback boundary: runtime batch instructions, the icon contract, the review rubric,
and this audit note move together. Generated transfer artifacts remain outside Git and
require the normal approval gates.

## 2026-08-16 — Office-chair experiment salvage handoff

- Paused the incomplete office-chair material-transfer experiment before further visual
  review or generation.
- Accounted for 79 persisted, distinct source masters while retaining the owner's
  approximate 86-call observation for failed/partial calls without canonical masters.
- Classified useful outputs as ordinary icons, category curation candidates, or
  material-only studies; kept rejected and structurally wrong outputs evaluator-only.
- Recorded a textual failure-rule dictionary because rejected images are not safe or
  reliable negative visual prompts for Image Gen.
- Bounded the next basin-mixer approval batch to three initial candidates and no more
  than one targeted retry per slot. Any reference-transfer gate remains a separate,
  explicitly approved phase.

Continuation details and local-only artifact paths are recorded in
`docs/HANDOFF-OFFICE-CHAIR-SALVAGE-2026-08-16.md`. No generated image was staged,
committed, or promoted; the runtime reference bank remains empty.
