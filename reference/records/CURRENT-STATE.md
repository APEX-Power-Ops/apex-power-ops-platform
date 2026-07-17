# Records Lane Current State - created 2026-06-24, updated 2026-07-16

Status: the SINGLE resume landing page for the records lane. Read this file before
starting any new records work. It is not a production-readiness approval.

This file exists to prevent the records lane from being read through stale punchlist or
branch state alone.

`Records-State-Key: migration_tip=049; evidence_as_of=2026-07-07; substrate=prod-applied-dormant; data_api=excluded; prod_role_login=none; product_runtime=not-admitted`

## Canonical status

The repository contains the contiguous Records migrations `001` through `049`.
Migrations `045`-`049` add the security/RLS, ownership, audit-role, audit-log, and
audit-trigger substrate after the foundation and template chain through `044`.

Evidence must be read by surface:

- **Repository implementation:** `001`-`049`, the disposable validation runner, serving
  boundary contract, and DB-free contract tests are merged. The repository does not contain
  an admitted Records API/runtime consumer, installable field PWA, or PowerSync product flow.
- **Retained production evidence:** the operator-gated 2026-07-07 campaign records `001`-`049`
  as production-applied but deliberately dormant. Its closeout observed all six Records roles
  `NOLOGIN`, Records excluded from the Data API, no credential minted during that campaign,
  and no serving consumer admitted.
- **Current external state:** this status packet did not query production or inventory secret
  stores. The retained campaign does not prove that no dormant external secret exists today;
  any later consumer packet must freshly verify role, credential, grant, Data API, and secret
  posture.
- **Dormant serving posture:** direct server-side role/DSN serving and Data API exclusion are
  ratified architectural precedents, not an active connection. No role activation, credential,
  consumer binding, or deployment follows from this page.
- **Product acceptance:** there is no operational Records product. PTM/DTAX proposal libraries
  are an office-import seam, not the zero-connectivity field proof. Product admission remains
  held on named ownership, identity/scope, lifecycle/value, source-use, retention, sync custody,
  first-slice, and acceptance decisions.

Migrations `001`-`049` must not be replayed. A live database substrate is not a live product.

## Authority

Use the consolidated platform repository as the source-of-truth checkout for this lane:

- Consolidated platform checkout: `/home/olares/code/apex/apex-power-ops-platform`
- Current authority/admission worktree: `/home/olares/code/apex/apex-records-p0-admission`
- Historical detached checkout: `/home/olares/code/apex/apex-records-lane`

The detached checkout stops at an obsolete pre-security snapshot. It is historical inspection
material only; do not build from it, copy late work into it, or use it to replay migrations.

Commit SHAs and active branch names are observed snapshot metadata only. They are useful for reproduction, but they are not the authority claim.

**Authority ruling (operator, 2026-07-02):** the consolidated platform checkout IS the
source of truth for records work. The detached apex-records-lane checkout (b6980b28) is
STALE - do not build from it. Refreshing or retiring that checkout remains an operator decision.

## Historical snapshot (2026-06-24)

These fields preserve the earlier audit point; they are not the current migration ceiling:

- Platform cleanup branch base: `ed6b760d8c9941497d9a98fee36be2544fa2a836`
- Records-specific cleanup branch: `codex/records-lane-audit-cleanup`
- Original detached records-lane checkout: `b6980b28e4ea69a3633b72a94ea7ae450f66c4ee`
- Consolidated platform migrations observed then: `001` through `044`
- Detached records-lane migrations observed: `001` through `042`

Durable repository facts as of the current base:

- Records has a substantial schema and template foundation.
- Records contains migrations `001` through `049` in the platform checkout.
- `043` and `044` omit RLS/grants only at their own stack positions; `045` supersedes that
  posture by enabling the lane-wide RLS/grant boundary.
- `046`-`049` add non-bypass ownership, audit roles, metadata-minimal audit capture, and the
  six writer-table audit triggers.
- Chip 10 import work is partial: PTM proposal/commit scaffolding exists, and DTAX parser/proposal plumbing exists, but the lane does not yet have audit-grade import sessions, source hashes, review-decision history, or full DTAX mapping.
- Chips 3 and 4 remain the decisive offline proof gates: PowerSync substrate plus installable field PWA capture/reconcile.

## Maturity

Current maturity: secure, production-applied dormant database substrate; product not admitted.

Do not treat the records lane as production-ready until at least these gates are closed:

1. The open product-admission decisions have accountable human authorities and immutable evidence.
2. Value Model V2 and governed lifecycle/amendment rules are implemented and proven.
3. A named, least-privilege consumer proves user/device-to-project authorization.
4. Import sessions/review decisions/source hashes/reimport semantics are implemented.
5. One end-to-end zero-connectivity capture, reconnect, review, acceptance, and readback flow is proven.
6. Source-content and retention/hold/delete/backup/restore policies are ratified and enforced.

## Retained and repository validation

The retained Records Gate 9 evidence reports the 49-migration disposable gate and tiers 0-7
passing. The later operator-gated production closeout records `001`-`049` applied, Data API
exclusion, and the all-six-`NOLOGIN` dormant toggle. Those are dated retained facts, not fresh
production introspection by this packet.

The earlier focused parser/proposal run from the platform checkout recorded:

```bash
PYTHONPATH=packages/power-test-converters/src:packages/records-import/src .venv/bin/pytest packages/power-test-converters/tests/test_dtax_read.py packages/power-test-converters/tests/test_ptm_to_dtax.py packages/records-import/tests/test_smoke.py packages/records-import/tests/test_review_proposal.py packages/records-import/tests/test_ptm_transformer_mapping.py -q
```

Result: `20 passed`.

That result validates focused converter/import proposal behavior only. It does not establish
an admitted product path.

## Not freshly verified by this packet

This authority/admission packet is DB-free. It does not freshly validate:

- current production role/grant/policy/catalog state
- current external credential or secret-store state
- any migration replay (replay is expressly forbidden)
- records-import DB write behavior
- principal/device-to-project authorization
- PowerSync/offline capture/reconcile behavior
- import session history
- source-file hash identity
- reviewer accept/reject/edit decisions
- idempotent source-file reimport semantics
- acceptance/tolerance resolver behavior

No database, credential, secret, private source checkout, or production system was accessed for
this reconciliation.

## Historical resume-audit update - 2026-07-02

The observations below describe that dated snapshot. Where they conflict with the canonical
status above, the canonical status controls.

An outside audit of the records lane was performed on 2026-07-02 (originally recorded as a
stranded RESUME-AUDIT-2026-07-02.md resume guard in the ops worktree; folded here so this
file stays the single landing page). The reviewed detached checkout was clean at b6980b28
while origin/main already contained later records work (migrations 043 and 044); the lane
charter and punch list still described Chip 10c as pending/unmerged. b6980b28 is verified an
ANCESTOR of origin/main - the charter status was stale, not the code.

### Findings to carry forward

1. Lane accounting stale: the charter said Chip 10c pending while main has read_dtax /
   propose_dtax and later records migrations. (Corrected by this cleanup.)
2. At that time there was no reliable single Records gate: root package.json had placeholder
   scripts and `.github/workflows` had no Records-specific CI coverage.
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

Historical 2026-07-02 checklist and current disposition:

1. Refresh or recreate the Records worktree from the chosen current base. **DONE for this packet.**
2. Update the lane charter and Records punch list to match reality. **DONE in this packet.**
3. Add a records validation runner: converter unit tests, records-import pure tests,
   records-import DB tests when a DSN is present, and migration tests against a disposable
   Postgres database - never shared records_dev. (DONE 2026-07)
4. Replace hardcoded DB password fallbacks with the RECORDS_DEV_DSN /
   RECORDS_DEV_PGPASSWORD contract. (DONE 2026-07)
5. Formalize the power-test-converters dependency or move shared test helpers into a
   package/fixture location that does not import sibling tests.
6. Keep serving dormant until admission decisions, identity/scope, lifecycle, and real-login
   tests are separately authorized and complete. **OPEN.**

## Next Gates

No item below is execution-authorized by this page:

1. Human ratification of the first consumer/owners, row scope, identity/device sources,
   source-content posture, lifecycle, retention, asset-tag reconciliation, exact first slice,
   PowerSync custody, and acceptance evidence/signatory.
2. Value Model V2 plus lifecycle and immutable-evidence design.
3. One named consumer packet with verified authentication, server-side scope, real-login
   negative tests, and rollback; preserve Data API exclusion and owner/bypass prohibitions.
4. One office provisioning slice for the ratified apparatus/template boundary.
5. One installable, zero-connectivity field slice with durable local state, reconnect,
   idempotent replay, conflict handling, governed review, acceptance, and readback.
6. Audit-grade import sessions and transactional review/commit semantics.
7. Versioned acceptance, PM, evidence, reporting, and reconciliation consumers.
8. Product-path acceptance and operational hardening.

Until separate operator decisions and implementation GOs exist, `decision_status` remains
`proposed` and `execution_authorized` remains `false`.
