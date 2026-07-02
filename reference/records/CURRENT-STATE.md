# Records Lane Current State - created 2026-06-24, updated 2026-07-02

Status: the SINGLE resume landing page for the records lane. Read this file before
starting any new records work. It is not a production-readiness approval.

This file exists to prevent the records lane from being read through stale punchlist or
branch state alone.

## Authority

Use Olares as the source-of-truth host for this lane work:

- Consolidated platform checkout: `/home/olares/code/apex/apex-power-ops-platform`
- Detached records-lane checkout observed during review: `/home/olares/code/apex/apex-records-lane`

The consolidated platform checkout is the fuller review surface because it contains the records-lane Chip 10c work plus later records migrations `043` and `044`. The detached `apex-records-lane` checkout observed during review stops at records migrations through `042`.

Commit SHAs and active branch names are observed snapshot metadata only. They are useful for reproduction, but they are not the authority claim.

**Authority ruling (operator, 2026-07-02):** the consolidated platform checkout IS the
source of truth for records work. The detached apex-records-lane checkout (b6980b28) is
STALE - do not build from it. After this cleanup lands on main, refresh that checkout onto
main or retire it.

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

## Resume Audit Update - 2026-07-02

An outside audit of the records lane was performed on 2026-07-02 (originally recorded as a
stranded RESUME-AUDIT-2026-07-02.md resume guard in the ops worktree; folded here so this
file stays the single landing page). The reviewed detached checkout was clean at b6980b28
while origin/main already contained later records work (migrations 043 and 044); the lane
charter and punch list still described Chip 10c as pending/unmerged. b6980b28 is verified an
ANCESTOR of origin/main - the charter status was stale, not the code.

### Findings to carry forward

1. Lane accounting stale: the charter said Chip 10c pending while main has read_dtax /
   propose_dtax and later records migrations. (Corrected by this cleanup.)
2. No reliable single records gate: root package.json has placeholder echo scripts and
   .github/workflows has no records-specific CI coverage.
3. Migration tests are not suite-safe: the records MANIFEST warns not to run pytest across
   the directory because per-file destructive down/up fixtures can corrupt records_dev.
4. Brittle DB env contract: tests and generators hardcode a legacy fallback password across
   many files (47 references found), while .env.dev.template documents generic apex_dev,
   not records_dev. Replace with a required, documented RECORDS_DEV_DSN /
   RECORDS_DEV_PGPASSWORD contract; DB-backed tests skip or fail clearly when absent.
5. records-import is not self-contained: it depends on sibling power-test-converters via
   out-of-band uv --with-editable usage, and the DTAX e2e test imports a sibling test
   helper through sys.path.
6. Import path is library-only: model_to_proposal / propose_dtax / commit are good seams,
   but there is no governed API/UI review gate, operator identity, audit trail, or
   non-superuser role proof yet.
7. Records docs/runbooks stale in operator-critical spots, including manifest
   quick-execution commands that still mention apex_neta_stage and only the earliest
   migrations.

### Positive signals

The domain model is strong: NETA reference/filtering, coverage invariants, standard-aware
ATS/MTS support, reversible migrations, and explicit deferrals. The import core is sound in
shape: it separates parsed readings from review proposals, classifies
mapped/unmapped/pending values, preserves provenance, skips phantom targets, and performs
idempotent upsert only after commit.

### Validation snapshot (2026-07-02, non-destructive only)

- infra/secret-audit.sh: clean.
- power-test-converters tests: 11 passed.
- records-import pure slice: 9 passed; full package: 9 passed plus 7 DB-backed errors from
  records_dev auth under the current fallback contract.
- root pytest run: failed on general harness issues (Windows virtualenv paths, missing
  SQLAlchemy behavior).
- destructive records migration tests: NOT run (the manifest warns the combined run can
  corrupt records_dev).

### Minimum resume checklist

Before approving new records-lane work:

1. Refresh or recreate the records worktree from the chosen current base (platform main).
2. Update the lane charter and records punch list to match reality (this cleanup).
3. Add a records validation runner: converter unit tests, records-import pure tests,
   records-import DB tests when a DSN is present, and migration tests against a disposable
   Postgres database - never shared records_dev. (DONE 2026-07)
4. Replace hardcoded DB password fallbacks with the RECORDS_DEV_DSN /
   RECORDS_DEV_PGPASSWORD contract. (DONE 2026-07)
5. Formalize the power-test-converters dependency or move shared test helpers into a
   package/fixture location that does not import sibling tests.
6. Plan serving/security before any API/UI surface: review gate, operator identity, audit
   trail, role/grant tests, non-superuser execution.

## Next Gates

Gate order (operator-ratified 2026-07-02). The validation harness comes FIRST - the next
real records work is a validation-harness lane, not feature work:

1. Current State - reconcile docs/punchlist to reality (this cleanup).
2. Validation Harness - records runner/CI; explicit RECORDS_DEV_DSN /
   RECORDS_DEV_PGPASSWORD contract; migration tests only against a disposable database,
   never shared records_dev. **DONE 2026-07 (this lane): runner +
   CI live; see infra/database/migrations/records/run_validation.py and the
   evidence record in docs/operations/.**
3. Security/RLS - design, implement, and test the records security posture.
4. Value Model V2 - support or reject every field kind used by templates.
5. Import Sessions - source-file hashes, reviewer accept/reject/edit decisions, reimport
   semantics.
6. Offline Proof - one end-to-end offline capture and reconcile flow.
7. Template Source/Replay
8. Acceptance Resolver
9. Source-Content Policy
