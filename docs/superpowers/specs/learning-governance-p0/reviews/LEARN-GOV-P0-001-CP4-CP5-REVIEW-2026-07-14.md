# LEARN-GOV-P0-001 CP4 And CP5 Review

Date: 2026-07-14

Status: CP5 REVIEW COMPLETE - OPERATOR CP6 ACCEPTED WITH CONDITIONS

## Review Identity

- Goal ID: `LEARN-GOV-P0-001`
- Checkpoints: `CP4` independent audit and `CP5` Program Manager synthesis
- Program Manager: `LEARN-PM-2026-07-14`
- Reviewed branch: `learning/governance-p0-design`
- Baseline before this review: `0a805c0f`
- Technical Authority: Codex CLI `gpt-5.5` run
  `019f6129-76e2-75c1-88b3-cb9df9cb6dff`
- Technical Authority scope: technical architecture, state-machine coherence,
  checkpoint semantics, evidence/decision binding, false-green paths,
  integration feasibility, and faithful hold preservation
- Independent auditor: Codex CLI `gpt-5.5` run
  `019f612c-853c-7683-92de-02c5541573c9`
- Independent audit scope: authority separation, scope compliance,
  evidence/version binding, reserved-decision holds, checkpoint completeness,
  unique goal identity, cohort/parked-state fidelity, and false-green routes
- Pre-CP6 reviewed packet manifest at accepted commit `afe73da2`:
  `reviews/LEARN-GOV-P0-001-REVIEWED-PACKET.sha256`
- Manifest SHA-256:
  `5c69fd7f8a08434d48a4916e7d38c8277f000b5bbddc9c74d906b751ad2123df`
- Pre-CP6 manifest method: sorted lines of `<file_sha256><two spaces><packet-relative
  path>` for every packet file except this review record and the manifest itself;
  verify from the packet root checked out at `afe73da2` with `sha256sum -c`.
- Review mode: documentation-only, findings-first, no external-system access

The configured `gpt-5.6-sol` model could not be used by the installed Codex CLI
`0.141.0`; the independent review was pinned explicitly to `gpt-5.5`. This is a
tooling-maintenance item, not a waiver of independent review.

## Technical Authority Result

The appointed Technical Authority reported no actionable findings and approved
the technical boundary for operator CP6 review. The approval explicitly excludes
implementation, checker/schema work, metadata migration, source-body access,
content authoring, learner-data activity, database/API/import/render/deploy or
release action, and every reserved human decision.

## Independent Audit Result

The appointed independent auditor found the missing auditor identity in this
record as its only actionable issue. It independently verified that the
Technical Authority identity and scope were sufficient and distinct, that the
active and parked target sets were preserved, that the sixth owner-return track
was present, that proposed goals remained held, and that implementation and
reserved actions remained unauthorized. `git diff --check` passed in the audit.

An earlier independent-audit attempt, Codex CLI run
`019f612b-6f42-7cf2-846f-cbf9f8e9ac03`, failed closed because its read-only
sandbox could not continue filesystem reads. It issued no acceptance and is not
the appointed audit result.

## Source Access Amendment

A post-review documentation amendment records the verified read-only mapping
from the Windows Box source root to `/mnt/apex-platform-ro`. It updates executor,
rights-evidence, rights-goal, and Program Manager instructions and adds a
canonical source access/custody map.

The amendment does not change the source register, its snapshot hash, the active
or parked cohort, source classifications, allowed body-access classes, or any
owner-return state. Metadata-only verification observed directories and six
Stage 0 filenames without opening artifact or source bodies.

Focused non-authoring review: Codex CLI `gpt-5.5` run
`019f6136-b7bc-7da0-b050-5b6c92b16d8c`. The review found one P2 in the
aggregate-digest description and independently found the path mapping,
read-only boundary, permissions, six-track rule, and unchanged source-register
hash clean. The P2 disposition is recorded below. Focused re-verification:
Codex CLI `gpt-5.5` run `019f6139-f783-7b01-a03e-7a7e608f5363`, clean. It
verified all 28 manifest entries, the manifest's recorded hash and exclusions,
the unchanged source-register hash, and the unchanged source-access permission
boundary without opening the mount.

## Findings And Dispositions

### P2: Missing Sixth Owner-Return Track

The migration map preserved only the five historical owner-return tracks and
omitted the current learner identity, purpose, privacy, retention, and access
track. A later checker could therefore have treated the held pilot as ready with
that gate unresolved.

Disposition: fixed. The migration map now preserves all six current tracks and
states that any missing or partial track keeps `ET-PILOT-HOLD`.

### P2: Duplicate Checker Goal ID

The roadmap listed `LEARN-GOV-P1-CHECKER-001` twice with different descriptions
and checkpoint wording. A human or future checker would have had two competing
records for one stable goal identity.

Disposition: fixed. The roadmap now contains one authoritative row. The checker
goal also binds acceptance to every negative case in the accepted P0 design,
while recording that this revision contains 28 cases.

### P2: Canonical Goal Status Lagged The Checkpoint

The canonical P0 goal record advanced its checkpoint to CP5 but retained an
`IN PROGRESS` header while the roadmap correctly recorded `checkpoint_review`.
A future checker or operator reading the goal record directly could therefore
have treated execution as active after the mandatory stop.

Disposition: fixed. The canonical goal status now records checkpoint review,
completed CP5 synthesis, and the required operator CP6 decision.

### P1: Independent Auditor Identity Missing From CP4 Record

The goal record claimed that the independent auditor was identified here, but
this record originally contained no auditor run ID or scope. That left CP4
incomplete and created a false-green route to CP6.

Disposition: fixed. The independent auditor's exact run ID, model, scope, and
result are now recorded above. The goal record binds the same identity.

### P2: Aggregate Packet Digest Was Not Reproducible

The earlier review record named a digest algorithm but did not fully specify
path normalization. A second valid `sha256sum` invocation therefore produced a
different aggregate value.

Disposition: fixed. The packet now contains an explicit sorted checksum
manifest over 28 packet-relative files. The review record and README name the
manifest, exclude the manifest and review record from the reviewed set, record
the manifest's own SHA-256, and provide the exact `sha256sum -c` verification
context. All 28 entries verify.

## Authority And Scope Check

- Goal authorization: valid for design-only work.
- Cohort: unchanged at ET-010 through ET-014.
- Parked targets: ET-017 and ET-028 remain parked.
- Source-body and learner-facing work: not performed.
- Learner-data, database, API, browser, and external-system access: not performed.
- Implementation, import, render, deploy, release, and production work: not
  performed.
- Rights policy: represented as policy authority, not source-specific admission.
- Human SME, privacy, release, and rights decisions: still reserved and held.

## CP5 Program Manager Synthesis

After the recorded corrections, no unresolved high-severity contradiction is known
in the P0 design packet. The packet is suitable for an operator CP6 decision.

Recommended operator disposition: `accept_with_conditions`.

Conditions:

1. P0 acceptance authorizes governance design only.
2. `LEARN-GOV-P1-CHECKER-001` requires a separate CP1 implementation GO.
3. Rights and SME packets require their own CP1 authorizations and decision
   owners.
4. The held Level II state must remain set-equal through metadata migration.
5. No content, learner data, database, API, import, render, deploy, or release
   work is admitted by this recommendation.

## Proposed Next Goals

Primary serial goal after CP6 acceptance:

- `LEARN-GOV-P1-CHECKER-001` - offline schema, registry, decision, checkpoint,
  and transition checker.

Parallel metadata-only goals after their own CP1 authorizations:

- `LEARN-RIGHTS-DECISIONS-001` - source-specific rights decision preparation.
- `LEARN-SME-APPOINTMENT-001` - human SME qualification, appointment, and rubric.

The next goal proposal is not authorization. The primary executor must remain
stopped until the operator issues the applicable standalone GO.

## CP6 Operator Disposition

The operator accepted the design with conditions at
`2026-07-14T15:29:03Z`, bound to commit `afe73da2`, tree `ecf49114`, and the
reviewed manifest recorded above. The authoritative decision is
`decisions/LEARN-GOV-P0-001-CP6-2026-07-14.md`.

No implementation or operational hold was lifted. CP7 closeout is recorded at
`closeouts/LEARN-GOV-P0-001-CP7-2026-07-14.md`.
