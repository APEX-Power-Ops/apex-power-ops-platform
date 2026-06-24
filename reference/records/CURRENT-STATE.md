# Records Lane Current State - 2026-06-24

Status: current-state snapshot for planning and audit framing

This file exists to prevent the records lane from being read through stale punchlist or branch state alone. It is not a production-readiness approval.

## Authority

Use Olares as the source-of-truth host for this lane work:

- Consolidated platform checkout: `/home/olares/code/apex/apex-power-ops-platform`
- Detached records-lane checkout observed during review: `/home/olares/code/apex/apex-records-lane`

The consolidated platform checkout is the fuller review surface because it contains the records-lane Chip 10c work plus later records migrations `043` and `044`. The detached `apex-records-lane` checkout observed during review stops at records migrations through `042`.

Commit SHAs and active branch names are observed snapshot metadata only. They are useful for reproduction, but they are not the authority claim.

## Observed Snapshot

Observed on 2026-06-24:

- Platform cleanup branch base: `ed6b760d8c9941497d9a98fee36be2544fa2a836`
- Records-specific cleanup branch: `codex/records-lane-audit-cleanup`
- Original detached records-lane checkout: `b6980b28e4ea69a3633b72a94ea7ae450f66c4ee`
- Consolidated platform records migrations: `001` through `044`
- Detached records-lane migrations observed: `001` through `042`

Durable current-state facts:

- Records has a substantial schema and template foundation.
- Records contains standard/reference/template work through migrations `001`-`044` in the platform checkout.
- `043` adds NETA table source-link companion metadata and intentionally omits RLS/grants.
- `044` adds a local person anchor plus `form_submissions.technician_person_id` and intentionally omits RLS/grants.
- Chip 10 import work is partial: PTM proposal/commit scaffolding exists, and DTAX parser/proposal plumbing exists, but the lane does not yet have audit-grade import sessions, source hashes, review-decision history, or full DTAX mapping.
- Chips 3 and 4 remain the decisive offline proof gates: PowerSync substrate plus installable field PWA capture/reconcile.

## Maturity

Current maturity: foundation/prototype, not production-governed.

Do not treat the records lane as production-ready until at least these gates are closed:

1. Current-state docs and punchlist are reconciled.
2. Records RLS/grants/security posture is designed, implemented, and tested.
3. Value model v2 supports or rejects every field kind used by templates.
4. Import sessions/review decisions/source hashes/reimport semantics are implemented.
5. One end-to-end offline capture and reconcile flow is proven.
6. Source-content policy is explicit for stored, served, synced, exported, and customer-visible content.

## Validated

Focused parser/proposal tests were rerun from the platform checkout:

```bash
PYTHONPATH=packages/power-test-converters/src:packages/records-import/src .venv/bin/pytest packages/power-test-converters/tests/test_dtax_read.py packages/power-test-converters/tests/test_ptm_to_dtax.py packages/records-import/tests/test_smoke.py packages/records-import/tests/test_review_proposal.py packages/records-import/tests/test_ptm_transformer_mapping.py -q
```

Result: `20 passed`.

This validates focused converter/import proposal behavior only.

## Not Validated

The focused test run does not validate:

- records-import DB write behavior
- full records migration replay
- RLS/grants or tenant/security posture
- PowerSync/offline capture/reconcile behavior
- import session history
- source-file hash identity
- reviewer accept/reject/edit decisions
- idempotent source-file reimport semantics
- acceptance/tolerance resolver behavior

DB-backed tests were not run in the audit cleanup because credentials were not available from the shell context and secret files were not read.

## Next Gates

Use this gate order for planning:

1. Current State
2. Security/RLS
3. Value Model V2
4. Import Sessions
5. Offline Proof
6. Template Source/Replay
7. Acceptance Resolver
8. Source-Content Policy
