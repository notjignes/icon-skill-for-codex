# UC Icons v0.2.0-rc.1 handoff

## Continuation result — 2026-08-16

The next chat completed the mandatory hash-frozen audit before editing. The inherited
78-test checkpoint and all four validators passed, and all five pre/post hashes matched
the values recorded below. Seven evidence-backed adversarial blockers were then fixed:
object/character token collisions, unsafe automatic references, non-image request
references, resolver symlinks, runtime-bank orphans, bank-version drift, and attested
rather than per-run-derived transfer means.

The final staged-tree matrix passed 88 tests in 174.177 seconds, all 72 legacy
pixel-equivalence checks, the compact validator at `174,858,133` bytes, the empty bank
validator, diff checks, cache-residue checks, and a second unchanged pre/post hash
comparison. The
implementation is partitioned into the reversible commits listed in
`docs/IMPLEMENTATION-LOG.md`. No image candidate or Image Gen test output was created,
committed, or promoted. The active installed skill remains unchanged.

The original pause-point instructions are retained below as the audit trail.

## Original resume point

- Repository: `/Users/svigneshwaran/Downloads/Urban company/repos/icon-skill-for-codex`
- Branch: `codex/uc-icons-v0.2.0-rc1`
- Target: draft PR to `main`; never push directly to `main`.
- Source of truth: the tracked repository, not `~/.codex/skills/uc-icons`.
- Active installed skill: intentionally unchanged and still duplicate-heavy.
- Release phase: implementation and adversarial hardening checkpoint complete; a new
  chat must independently inspect the frozen checkpoint before reversible commits and
  draft-PR publication.
- Reference phase: not started. No Wave 1 candidate was generated and no reusable
  reference was promoted.

Read `docs/IMPLEMENTATION-LOG.md` before making changes. It records the rationale,
validation snapshot, and rollback boundary for each implementation layer.

Checkpoint verdict: **handoff-ready, not release-certified**. The final green matrix was
run by the maintainer after a sequence of audit fixes; the tree did not remain immutable
long enough for a separate uninterrupted invigilator matrix. Therefore this checkpoint
is a NO-GO for merge, tag, active installation, or reference promotion until the next
chat completes the hash-frozen re-audit below.

## Owner decisions that remain authoritative

1. Normal `$uc-icons` calls are fast and silent. Internal routing/reference work is not
   narrated or previewed.
2. Show exactly one short, playful waiting line only when Image Gen/edit is invoked.
   `Go touch some grass 🌱 — we’re generating your icon.` is an example of the desired
   modern/casual tone, not mandatory copy. Keep alternatives friendly and concise;
   exact exports show no progress line.
3. Approved internal references are selected automatically without asking the user.
4. User-provided references are request-scoped, take their declared role precedence,
   and are never learned/promoted automatically.
5. Reusable-bank additions, replacements, and promotions require explicit owner
   approval. Ordinary successful outputs stay ordinary outputs.
6. Keep one high-resolution physical master per approved asset. Derive delivery images;
   do not store duplicate bank derivatives.
7. Do not install, merge, tag, publish a stable release, or promote references without
   a new explicit owner approval.

## Implemented state

### Compact storage

- 72 unchanged physical legacy high-resolution PNG masters.
- 73 logical service identities, 70 base aliases, 72 material aliases, and 11 character
  aliases resolve through contained manifests.
- Pest Control Dubai is the sole special duplicate alias and resolves to Cockroach
  Control.
- No physical PNGs remain in base, material, or character alias directories.
- Compact skill validation snapshot: `174,841,049` bytes, below the 180 MB gate.

### Runtime planning

- Identity-first service/base/character routing with controlled ambiguity.
- Natural edit clauses retain the canonical service master across all 73 identities.
- Filenames, paths, colors, and materials cannot establish object identity.
- Human/object boundaries, unsafe suffixes, variant colors, avatar eye state, and generic
  multi-variant requests have regressions.
- Runtime references are approved-only, role-distinct, limited to three, and omitted
  when compatibility is insufficient.
- Supplied references never enter the runtime bank automatically.

### Master/export workflow

- Explicit source path; no recursive newest-image search.
- Preserve a valid native master byte-for-byte and never upscale a smaller native result.
- Derive one `1024x768` delivery and record native/output sizes and hashes.
- Detect transparency including palette `tRNS`, reject falsely certified dark
  backgrounds, and normalize eligible pale-neutral backgrounds to exact `#f5f5f5`.

### Reference lifecycle

- Candidates live outside the installed skill and are invisible to normal retrieval.
- Exactly one logical role is tested per candidate record; one master SHA may back
  separately approved logical roles without copied image bytes.
- Technical gate, two normalized independent reviewers, three positive held-outs,
  negative control, three runs per arm, score margin, explicit failure booleans, shared
  generation-policy fingerprint, and owner approval are required.
- Installed transfer evidence is hash-bound and reconstructed through a strict path-free
  allowlist.
- Promotion is transactional, versioned by bank content, and rolls back on validation
  failure.
- Runtime bank currently contains zero approved references.

## Verification completed at the pause point

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
# 78 tests passed in 114.408s

python3 uc-icons/scripts/validate_uc_icons.py --skill-dir uc-icons --compact-baseline
# status: ok; 72 physical legacy PNGs; 72 unique hashes; 174,850,354 bytes

python3 tests/verify_legacy_pixel_equivalence.py
# all 72 locked legacy masters pixel-equivalent

python3 uc-icons/scripts/manage_reference_bank.py validate
# valid: true; errors: []

git diff --check
# clean

find . -type d -name '__pycache__' -o -type f -name '*.pyc'
# no output
```

Rerun the complete matrix after any change. Do not weaken a gate merely to make a test
pass.

## Mandatory first step in the next chat

Do not begin candidate generation. First freeze and hash the planner, character manifest,
ontology, runtime-bank manifest, and tests; run one uninterrupted audit matrix; then hash
them again. Certify only if the hashes are unchanged during the matrix.

Pause-point SHA-256 values:

```text
7bc529758d50e7d00990c29d3472c2b334e08116f19dfa711c3eecc7f8cfe7fc  uc-icons/scripts/plan_icon_request.py
5dd3d270c5540008c90c2d05e2c37b839b6634951b728dfd268b5f37832e1942  uc-icons/references/characters/MANIFEST.csv
798db13d0712fb60ee3615f07328a58b789081a22938db408734879c26931b49  uc-icons/references/routing/ontology.json
d7872b9967f726cd824e3abd3dbd1995fcc53b3d8749e9cd3f2f9116c0134eb4  uc-icons/references/reference-bank/MANIFEST.csv
783a2bd9edd7a16524fac91ac888f562186d919fc09d40d61036f87e9538be3f  aggregate tests-tree hash
```

The technical invigilator reused two existing audit threads. The design invigilator's
two optional helper cycles could not start because the active-agent/thread cap remained
saturated; the design invigilator completed its own checkpoint audit directly. Do not
claim that those two optional helper cycles ran.

Inspect these already-recorded adversarial areas even though the current 78-test suite is
green:

- compound identities that could still trigger human routing, especially `impact driver`;
- identity-unsafe compounds reaching cross-family `material` or `style` references;
- request-scoped reference paths that exist but are not actually decodable image files;
- direct-repository contained symlinks in `SafeResolver` (the atomic installer already
  rejects every symlink);
- runtime-bank orphan assets and consistency between global/row `BANK_VERSION` values;
- whether transfer means should be derived from per-run ratings instead of remaining
  reviewer-attested aggregate values.

Treat the explicitly supplied `base=` behavior for a character as intentional owner
policy: request-scoped base precedence is allowed, never reusable, and never a likeness
license. Do not “fix” it by silently discarding the user's declared base role.

## Remaining work for the next chat

1. Read this handoff and `docs/IMPLEMENTATION-LOG.md`; inspect the frozen worktree and
   the adversarial checklist above. Resolve only reproduced, evidence-backed blockers.
2. Rerun the full tests, compact validator, 72-image pixel-equivalence probe, bank
   validator, `git diff --check`, and confirm no cache/generated residue.
3. Commit the frozen patch as separate reversible boundaries:
   - resolver/storage locks and tests;
   - base/material alias migration;
   - character alias resolver and duplicate removal;
   - deterministic planner plus silent UX;
   - high-resolution master/export workflow;
   - approval-gated bank/evaluation tooling;
   - documentation, CI, installer, and audit log.
4. Push only `codex/uc-icons-v0.2.0-rc1` and open a draft PR to `main`.
5. Stop. Do not start Wave 1 generation in the same step unless the owner explicitly
   asks to resume it.

## Next-phase queue (not authorized by this handoff)

The owner-specified Wave 1 remains 12 subjects × 3 candidates, shortlist at most one:
office chair, basin mixer tap, standalone cordless drill, side-profile passenger van,
standing lamp, slight-top mattress, upright broom, palette-neutral gift box,
transparent tea vessel, open-top salad bowl, single candle jar, and two-candle set.

Design advisory to decide before generation: the current queue has no separately tested
`style` candidate and has limited composition-family coverage. If the owner wants to
broaden the same wave, add a role-specific style transfer case and deliberately test
`carrier-contents`/`object-cue`; otherwise preserve the exact 12-subject queue and treat
that coverage as Wave 2. Do not silently change the queue.

At the original pause point, the checkpoint was intentionally uncommitted, unpushed,
uninstalled, and had no draft PR. The continuation committed the repository boundaries;
the active `~/.codex/skills/uc-icons` installation remains unchanged.

## Safety / rollback

- Never overlay-copy the compact skill into the active installation.
- Future installation is validated atomic replacement with automatic rollback.
- Keep the duplicate-heavy installed backup until restart and explicit owner confirmation.
- Human-approved reference promotion is a separate transaction from installation.
- No current action requires deleting the active installation or its backup.
