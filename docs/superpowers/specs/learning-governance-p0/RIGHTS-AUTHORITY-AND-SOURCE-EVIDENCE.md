# Rights Authority And Source Evidence Reconciliation

Status: DESIGN EVIDENCE RECONCILIATION - NO SOURCE ADMISSIBILITY ACCEPTED HERE

## Authority

Jason Lyle Swenson is the accountable internal rights/source-policy authority
under `APEX-SR-STANDING-2026-07-11`. The standing policy authorizes internal
reference-only and independently written work within its conditions. It does not
grant rights owned by third parties and does not automatically approve a source
for a specific learning artifact.

## External Evidence Bundle

Verified on 2026-07-14 without reading learning source bodies:

| Evidence | Custody locator | SHA-256 | Assessment |
|---|---|---|---|
| Standing attestation | `/home/olares/code/notes/learning-lane/apex-standing-source-rights-attestation-2026-07-11.md` | `28e29dd2863bbf03632463c9f138ae14d51ca7f7f75c84b0e8be9a899cfa7464` | Internal policy evidence |
| Signature image | `/home/olares/code/notes/learning-lane/Jason Signature.png` | `7cfd4d542143c2dbed4e49df2f1773286026fb9cf89aa621f229f1bf28cfe32b` | Bound by checksum; keep outside the repository |
| Detached checksum manifest | `/home/olares/code/notes/learning-lane/apex-standing-source-rights-attestation-2026-07-11.sha256` | `445afe7c9d8ef7f6a75133e5cb4845a176cd8fde52eb558486f79d35a2e55055` | Current attestation and image both verified |
| Living source register | `/home/olares/code/notes/learning-lane/apex-learning-content-source-register.md` | `57b16f434eababd66cef873756089d27651241ee1e7230c565b101772d2b6e8e` | Snapshot identity only; register is mutable |

The checksum proves byte correspondence, not signer authentication. The operator
must accept the policy bundle as internal authority evidence. The signature image
must not be copied into a public or broadly accessible repository.

## Source Access Surface

`SOURCE-ACCESS-AND-CUSTODY-MAP.md` records the verified read-only alias between
the Windows Box tree and `/mnt/apex-platform-ro`. Metadata-only inspection
confirmed the expected workrepo, source-domain directory, and six Stage 0
artifact filenames. No source or artifact bodies were opened.

The mount establishes availability for an admitted metadata observation. It is
not lawful-access evidence, a license, a source-specific rights decision, a
content-integrity check, or authoring authority. The source-register snapshot
hash above remains unchanged by this separate location map.

## Current Register Census

The snapshot contains 12 rows over the exact ET-010..014 cohort:

| Target | Rows | Current posture |
|---|---:|---|
| ET-010 | 3 | two reference-only, one candidate |
| ET-011 | 3 | two reference-only, one candidate |
| ET-012 | 2 | one reference-only with unresolved lawful-access provenance, one candidate |
| ET-013 | 2 | one reference-only with unresolved lawful-access provenance, one candidate |
| ET-014 | 2 | one reference-only with unresolved lawful-access provenance, one candidate |

Totals: 7 `REFERENCE_ONLY`, 5 `CANDIDATE`.

## Fail-Closed Disposition

- The five derived-hold `CANDIDATE` records remain discovery/triage only.
- The five Kuphaldt PDF `REFERENCE_ONLY` records remain conditional because the
  register says lawful-access or procurement provenance is undocumented.
- The two OpenStax `REFERENCE_ONLY` records are stronger public-access evidence,
  but their license observations and exact intended use still require a
  source-specific rights decision.
- No row authorizes copying, close paraphrase, protected figures, examples,
  questions, equations, or learner-facing source-body reuse.
- No target is declared fully rights-ready by this reconciliation.

## Required Decision Form

Each accepted source decision must bind:

- exact register row ID and snapshot/blob identity;
- source locator, owner/publisher, edition, and intended use;
- lawful-access evidence;
- permission or license evidence where required;
- allowed and prohibited transformations;
- audience and distribution boundary;
- decision owner `LEARN-RIGHTS-2026-07-11` or a later valid appointment;
- disposition, conditions, timestamp, expiry, and re-review trigger; and
- affected target, content version, and release bundle.

Until those records exist, the rights track remains partial and
`ET-PILOT-HOLD` remains unchanged.
