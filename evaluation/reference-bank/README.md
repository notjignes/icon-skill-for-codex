# Reference-bank workbench

Candidate and quarantined images live here, outside the installable `uc-icons/`
directory. Runtime retrieval never reads this tree.

Stage a native master with `uc-icons/scripts/manage_reference_bank.py stage`, record
two independent visual reviews and the held-out transfer result, then request explicit
owner approval before promotion. Promotion copies one approved high-resolution master
and its portable provenance record into `uc-icons/references/reference-bank/`.

Generated candidates require a portable prompt record, model name, and generation
timestamp at staging. Imported candidates use `--source-kind imported` and still
require a truthful producer/tool label in `--model` plus an import timestamp; unknown
source kinds are rejected. A passed transfer requires a `visual-v1` evidence JSON with the
three declared positive cases and one negative control, three distinct artifacts per
arm, verified artifact hashes, recorded blind IDs/order, a shuffle seed, and one blind
1–5 rating for every run. The tool derives each arm mean from those ratings; any
recorded mean or winner must agree with the derived values and the 0.4-point margin.
Artifacts must be distinct,
decodable, opaque 4:3 PNGs at least 1024×768. The tool
copies that evidence into the candidate directory and binds both reviews and transfer
approval to the candidate fingerprint. Promotion rechecks the current PNG bytes,
technical facts, prompt, evidence, reviews, and explicit owner approval before making
one atomic bank update. A failed validation rolls the manifest, bank version, and all
new runtime files back.

Each logical candidate tests exactly one role: `form`, `material`, `composition`, or
`style`. If one master may serve multiple roles, stage and transfer-test separate
logical IDs; promotion reuses the same SHA/path and does not copy the image bytes.
`good_for` is only a proposal at staging. Promotion derives runtime `good_for` families
from positive cases that actually won, so a tie or untested family never becomes a
retrieval permission.

Candidate, prompt, and transfer artifact paths remain relative to their records. The
candidate workbench retains the full A/B artifacts. The installed bank retains a
path-free transfer record with blind IDs, artifact hashes, and per-run ratings, plus
the portable prompt and SHA-locked approved provenance record. Never edit an approved
runtime record or image in place; quarantine
and replace it through a new reviewed candidate.

Ordinary `$uc-icons` generations are not staged or learned from automatically.
