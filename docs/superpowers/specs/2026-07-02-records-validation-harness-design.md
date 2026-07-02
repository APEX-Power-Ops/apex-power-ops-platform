# Records Validation Harness - Design Spec

- **Date:** 2026-07-02
- **Lane:** `records/validation-harness` (worktree `/home/olares/code/apex/apex-records-validation`, off main `80388a18`)
- **Status:** design approved by operator 2026-07-02 (approach A, with the source-data
  provisioning amendment folded in as a first-class gate); spec pending operator review
- **Authority:** `reference/records/CURRENT-STATE.md` gate order (this is Gate 2,
  "Validation Harness"); operator scope ratification 2026-07-02
- **Scope class:** harness + hygiene only. NO schema changes, NO app-code feature work,
  NO RLS. The jobs-lane fallback (`infra/database/migrations/jobs/_dbtest.py`) is a
  separate spawned chip.

## 1. Problem

The records lane has a strong domain model but no trustworthy way to validate it:

1. **No single gate.** Root `package.json` scripts are placeholder echoes; no records CI
   exists. "Validated" currently means "someone ran the right per-chip commands in the
   right order on the right machine."
2. **The credential fallback is broken AND load-bearing.** All 38 records migration
   tests, 5 generators, and 3 records-import DB tests read `RECORDS_DEV_DSN` /
   `RECORDS_DEV_PGPASSWORD` but fall back to a hardcoded password (47 in-scope refs:
   44 in records migrations/generators + 3 in records-import). The fallback value no
   longer authenticates against the host `apex-dev-pg` cluster (verified 2026-07-02:
   `FATAL: password authentication failed`), so on the host the DB-backed tests ERROR
   instead of skipping - the July audit's "7 DB-backed errors" finding.
3. **Bulk runs corrupt the shared dev DB.** Each migration test destructively
   down/ups its own migration; the records MANIFEST warns that one combined `pytest .`
   pass tears tables down out of dependency order and corrupts `records_dev`.
4. **Source data is implicit.** 16 migration tests (023-038) verify seed accuracy
   against external NETA extracts resolved via `NETA_DATA_DIR` / `NETA_JSON`
   (conftest defaults: host `~/neta-source/NETA-Data`, else a Windows OneDrive
   checkout). The extracts are NOT committed to this PUBLIC repo (correctly - they are
   NETA-derived study material). Any CI design that provisions only Postgres would
   false-red (files missing) or force silent skips on exactly the tests that make the
   seed trustworthy.
5. **The converter dependency is out-of-band.** `records-import` tests import
   `power_test_converters` and reach into the sibling package's `tests/` directory via
   `sys.path.insert` for `_write_sample_ptm` / `_write_sample_template`.

## 2. Goals

- G1: One runner = the records gate. A single command validates converters,
  records-import, and the full migration stack, with an honest exit code.
- G2: Explicit env contract; zero hardcoded credential fallbacks in records scope.
- G3: Migration tests never run against shared `records_dev` by default; the runner
  uses a disposable database it creates and drops.
- G4: CI proves the whole contract on ephemeral infrastructure - including the
  source-data-backed tests, via intentional provisioning (never silent skips).
- G5: The converter test dependency is a declared, importable contract.
- G6: The gate is proven to gate (red proofs), not just seen green.
- G7: Closeout rotates the credential the burned fallback value still opens.

Non-goals: security/RLS design (Gate 3), value-model v2, import sessions, offline
proof, template replay, any records schema or app-code change, the jobs-lane helper.

## 3. Environment contract

| Variable | Meaning | Consumers |
| --- | --- | --- |
| `RECORDS_DEV_DSN` | Full DSN of the records database under test. Authoritative; used verbatim. | migration tests, records-import DB tests |
| `RECORDS_DEV_PGPASSWORD` | Password for psql subprocess env when the tests shell out. Optional if `RECORDS_DEV_DSN` alone suffices. | migration tests (psql apply paths) |
| `RECORDS_PG_ADMIN_DSN` | Maintenance-DB DSN (dbname `postgres` or another maintenance DB - NEVER `records_dev`) used ONLY by the runner to CREATE/DROP the disposable database. | runner only |
| `NETA_DATA_DIR` | Directory holding the NETA extracts. conftest keeps its host/laptop defaults (portability), but existence is now validated up front. | migration tests 023-038 |
| `NETA_JSON` | Path to `NETA-Master-Equipment-Table-Enhanced.json`; defaults to `$NETA_DATA_DIR/...` as today. | migration tests |
| `RECORDS_ALLOW_SHARED_DB` | `1` = explicit legacy opt-in allowing a migration test to target a DB named `records_dev` (per-chip dev flow only). Never set by the runner or CI. | shared test helper |

Absence semantics (the skip/fail matrix):

| Condition | Local default | `--require-db` (CI always) |
| --- | --- | --- |
| `RECORDS_DEV_DSN` unset (package DB tests) | SKIP with one loud reason line | FAIL |
| `RECORDS_PG_ADMIN_DSN` unset (migration tier) | SKIP tier with loud reason | FAIL |
| `NETA_DATA_DIR` missing/not a directory | FAIL the migration tier (source-backed tests must never silently skip) | FAIL |
| Target DB named `records_dev` without `RECORDS_ALLOW_SHARED_DB=1` | REFUSE (hard error) | REFUSE |

There is deliberately no "skip source-backed tests" path: if the migration tier runs
at all, the NETA inputs must be present. This is the operator's amendment, verbatim:
CI provisions the inputs intentionally, or the tier fails loudly.

## 4. Components

### 4.1 `infra/database/migrations/records/_dbtest.py` (new shared helper)

Mirrors the existing jobs-lane `_dbtest.py` convention. Centralizes what today is
copy-pasted across 38 test files:

- `dsn()` - returns `RECORDS_DEV_DSN` or raises/skips per the matrix above. NO
  fallback value. Never inherits ambient `PGHOST`/`PGUSER` (they point at Supabase
  prod - the existing per-file pinning discipline, now in one place).
- `guard_target(dsn)` - parses the dbname; refuses `records_dev` unless
  `RECORDS_ALLOW_SHARED_DB=1`.
- `run_psql(args...)` - psql subprocess invocation with explicit env
  (`PGPASSWORD` from `RECORDS_DEV_PGPASSWORD` when set, `PGSSLMODE=disable`),
  using `PSQL_EXE` resolution from conftest.
- `neta_data_dir()` / `neta_json()` - resolve and VALIDATE existence; clear error
  naming the variable when absent.

The 38 test files and 5 generators are then edited mechanically: delete the local
credential block, import from `_dbtest`. Generators get the same no-fallback
treatment (they are run manually, not by the runner, but must not carry a dead
credential).

### 4.2 `infra/database/migrations/records/run_validation.py` (the runner)

Stdlib + psycopg only. Tiers, in order, exit code unmasked (no pipes between the test
process and the exit-code check), one summary table at the end:

- **Tier 0 - syntax:** `python -m compileall` over both packages' `src` + `tests`
  and the records migrations directory (matches existing CI convention).
- **Tier 1 - converters:** `pytest packages/power-test-converters/tests -q`
  (pure, no DB).
- **Tier 2 - records-import pure:** the non-DB test files (`test_review_proposal`,
  `test_ptm_transformer_mapping`, `test_smoke`).
- **Tier 3 - migration stack (forward-incremental):** builds the disposable DB
  (details below).
- **Tier 4 - records-import DB:** the 3 DB-backed files, with `RECORDS_DEV_DSN`
  pointed at the disposable DB Tier 3 just finished migrating (schema fully built),
  keeping `records_dev` out of the loop entirely. The drop happens after this tier.
- **Tier 3 mechanics:**
  1. Preflight: validate `RECORDS_PG_ADMIN_DSN` points at a maintenance DB (dbname
     is NOT `records_dev`; expected `postgres`), and `NETA_DATA_DIR` exists.
  2. `CREATE DATABASE records_val_<utcstamp>` via the admin DSN.
  3. Walk `NNN_*.sql` (excluding `*_down.sql`) in numeric order: apply migration N
     with psql (`ON_ERROR_STOP=1`); if `test_NNN_*.py` exists, immediately run
     `pytest` on that one file with `RECORDS_DEV_DSN` pointed at the disposable DB.
     Each test therefore executes with nothing stacked above its own migration -
     the exact state it was developed in. The MANIFEST corruption class (out-of-order
     teardown) and the 020/021 snapshot-reversion quirk are impossible by
     construction.
  4. `DROP DATABASE` in a `finally:` block after Tier 4 completes - but ONLY if
     the name matches `records_val_*` (refuse anything else; second half of the
     operator's DB-safety tightening).
- Flags: `--require-db` (CI mode: absence anywhere = fail), `--only <tier>` (local
  iteration), `--keep-db` (debugging; prints the DB name it is leaving behind).

Ordering note: execution order derives from the filename numeric prefix. The MANIFEST
declares strict sequential order; the runner does not parse MANIFEST prose.

### 4.3 `packages/power-test-converters/src/power_test_converters/testing.py` (new)

`_write_sample_ptm` and `_write_sample_template` move here as public
`write_sample_ptm` / `write_sample_template` (plus the private XML fragment builders
they depend on). `test_ptm_to_dtax.py` imports them back from the package;
`records-import/tests/test_ingest_dtax_end_to_end.py` drops the `sys.path.insert`
and imports `power_test_converters.testing`.

### 4.4 `packages/records-import/pyproject.toml`

- `power-test-converters` added to the `test` extra.
- `[tool.uv.sources] power-test-converters = { path = "../power-test-converters", editable = true }`
  - per-package source pin, consistent with the repo's documented no-uv-workspace rule.
- CI and docs use the explicit pip form: `pip install -e ../power-test-converters -e .[test]`.

### 4.5 `.github/workflows/records-ci.yml` (new)

On the calc-engine-ci pattern: pinned action SHAs, python 3.11, `ubuntu-latest`.

- **Triggers:** push + pull_request, path-filtered to
  `packages/power-test-converters/**`, `packages/records-import/**`,
  `infra/database/migrations/records/**`, and the workflow file itself.
- **Postgres:** `postgres:17` service container, throwaway CI-only password, health
  check gate.
- **Source data (the amendment, first-class):** a second `actions/checkout` of the
  PRIVATE org repo `APEX-Power-Ops/neta-ett-study-material` (path:
  `neta-source`), authenticated with a repo secret `NETA_SOURCE_REPO_TOKEN`
  (fine-grained PAT, read-only Contents on that single repo; operator creates and
  installs it out-of-band per the credential-custody model - the AI never sees the
  value). `NETA_DATA_DIR` is set to
  `$GITHUB_WORKSPACE/neta-source/Development/NETA-Data` - verified 2026-07-02 to
  carry the identical 13-file extract set as the host mirror. The extracts never
  enter the public repo or its logs; the workflow prints only file COUNTS.
- **Run:** install both packages editable, then
  `python infra/database/migrations/records/run_validation.py --require-db` with
  `RECORDS_PG_ADMIN_DSN` / `RECORDS_DEV_DSN` pointed at the service container.
- Public-repo caveat (accepted): Actions secrets are not exposed to fork PRs, so the
  source-backed tier runs on same-repo branches only - which is how all lane PRs in
  this org work. A fork PR would fail the tier loudly, not false-green.

### 4.6 Fallback removal

All 47 in-scope `TCC_v5_2025` refs go to zero: 44 across
`infra/database/migrations/records/` (38 test files + generators; operator-verified
count 2026-07-02) + 3 in `packages/records-import/tests/`. Grep for the literal in
records scope becomes an assertion in the PR evidence. Out of scope: the jobs helper
(spawned chip `task_c65d1e68`) and the frozen 2026-06-17 plan doc (historical
artifact; value dies at rotation).

### 4.7 Documentation

- Records MANIFEST: new "Validation" section - the runner is the primary path; the
  per-chip corruption-recovery recipe demoted to legacy/manual appendix.
- `reference/records/CURRENT-STATE.md`: Gate 2 marked in-progress/done by this lane;
  minimum-resume-checklist item 3/4 satisfied.
- `infra/.env.dev.template` (or the repo's env template equivalent): the four new/
  formalized variables with one-line semantics each.
- `docs/lanes/README.md` records entry: validation-harness status line.

## 5. Red proofs (gate-proving, in PR evidence)

Two deliberate failures, run once and transcribed into the PR:

1. **Withheld migration:** run the runner against a scratch copy with one migration
   file removed -> the apply step fails, runner exits nonzero, disposable DB still
   dropped.
2. **Missing source data under `--require-db`:** run with `NETA_DATA_DIR` pointed at
   a nonexistent path -> migration tier fails loudly (names the variable), exit
   nonzero.

A gate that has never been seen red is the false-green class; these two cover the
two failure families this lane exists to close (DB provisioning, source provisioning).

## 6. Security considerations

- The platform repo is PUBLIC. NETA extracts stay in the private
  `neta-ett-study-material` repo; CI accesses them read-only at runtime; nothing
  source-derived is added to the public repo beyond what the committed seed SQL
  already contains (the formal posture for that is Gate 9, Source-Content Policy -
  not relitigated here).
- `NETA_SOURCE_REPO_TOKEN`: fine-grained, single-repo, read-only Contents; operator
  provisions out-of-band; rotation is a one-secret swap.
- No DSN or password value ever appears in code, logs, or PR text. The CI throwaway
  Postgres password is generated in the workflow and meaningless outside the job.
- Migration tests default-refuse `records_dev`; the runner physically cannot
  drop/create anything not named `records_val_*`.

## 7. Closeout: credential rotation (operator-only, out-of-band)

The burned fallback value still authenticates somewhere: it was the Windows-local
PG18 password (host `apex-dev-pg` already rejects it - verified 2026-07-02). Final
lane task, AFTER the harness is merged and green:

- Operator rotates the password on the Windows-local PG18 instance (and anywhere
  else the value still opens), Vault-first per the L6 custody model.
- AI involvement is preconditions + post-verification only (e.g., confirming the old
  value no longer authenticates); the AI never handles the new value.
- Blast-radius note: Windows PG18 consumers are the local `tcc_fidelity_staging` /
  `postgres` MCP entries - operator updates those env entries out-of-band.

## 8. Acceptance criteria

- AC1: `run_validation.py` full pass green on the host against a disposable DB;
  `records_dev` is not connected to by any tier (guard verified).
- AC2: `records-ci.yml` green on the lane PR, including tiers 3-4 with the
  source-backed tests actually executing (evidence: test counts in the CI log).
- AC3: both red proofs demonstrated and transcribed in PR evidence.
- AC4: `grep -r TCC_v5_2025` over `infra/database/migrations/records/` and
  `packages/records-import/` returns zero.
- AC5: the `sys.path.insert` hack is gone; `records-import` declares the converter
  dependency; both packages' suites pass under the runner.
- AC6: docs updated (MANIFEST validation section, CURRENT-STATE, env template,
  lanes README).
- AC7: rotation executed by operator and old value verified dead (post-check only).

## 9. Decisions log

| # | Decision | Status |
| --- | --- | --- |
| D1 | CI workflow ships with the runner in this lane (not local-first) | RATIFIED 2026-07-02 |
| D2 | Rotate the burned credential at lane close, operator-only | RATIFIED 2026-07-02 |
| D3 | Scope = records only; jobs helper is a spawned chip; frozen docs untouched | RATIFIED 2026-07-02 |
| D4 | Source-data provisioning = CI checkout of private `neta-ett-study-material` via read-only fine-grained PAT secret | PROPOSED (this spec) |
| D5 | conftest keeps portability defaults for `NETA_DATA_DIR`/`PSQL_EXE`; existence validated, no silent skip | PROPOSED (this spec) |
| D6 | Tier 3 (records-import DB tests) targets the runner's disposable DB, not `records_dev` | PROPOSED (this spec) |
