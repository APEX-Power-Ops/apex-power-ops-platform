# Records Validation Harness - Design Spec

- **Date:** 2026-07-02 (rev 3 - rev 2 folded 17 confirmed findings from the 3-lens
  adversarial spec audit; rev 3 folds the operator's four review edits: post-test
  restoration assert, exact-filename source preflight, install-path precision,
  branch pushed as durable review target)
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
   tests, the generators, and 3 records-import DB tests read `RECORDS_DEV_DSN` /
   `RECORDS_DEV_PGPASSWORD` but fall back to a hardcoded password (47 in-scope refs:
   44 in records migrations/generators + 3 in records-import; operator-verified count
   2026-07-02). The fallback value no longer authenticates against the host
   `apex-dev-pg` cluster (verified 2026-07-02: `FATAL: password authentication
   failed`), so on the host the DB-backed tests ERROR instead of skipping - the July
   audit's "7 DB-backed errors" finding.
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
- G5: The converter test dependency is a declared, importable, origin-checked
  contract.
- G6: The gate is proven to gate (red proofs), not just seen green.
- G7: Closeout rotates the credential the burned fallback value still opens.

Non-goals: security/RLS design (Gate 3), value-model v2, import sessions, offline
proof, template replay, any records schema or app-code change, the jobs-lane helper.
Per-lane DB roles for records (one-DB-per-workstream role split) are a Gate 3
concern: this harness runs as the maintenance role end to end (see 4.2 single-role
model).

## 3. Environment contract

| Variable | Meaning | Consumers |
| --- | --- | --- |
| `RECORDS_DEV_DSN` | Full DSN of the records database under test. Authoritative; used verbatim. Under the runner's full flow this is SET BY THE RUNNER to the disposable DB - the operator-provided value is only consumed by standalone per-file pytest runs. | migration tests, records-import DB tests |
| `RECORDS_DEV_PGPASSWORD` | Password exported to psql subprocess env when tests shell out. Under the runner, derived from `RECORDS_PG_ADMIN_DSN` (see 4.2). | migration tests (psql apply paths) |
| `RECORDS_PG_ADMIN_DSN` | Maintenance DSN used ONLY by the runner to CREATE/DROP the disposable database and to derive the child DSN. Its dbname MUST be `postgres` (strict equality; anything else fails preflight). | runner only |
| `NETA_DATA_DIR` | Directory holding the NETA extracts. Default-resolution chain lives in `_dbtest.py` (4.1); existence validated before use. | source-backed migration tests 023-038 |
| `NETA_JSON` | Path to `NETA-Master-Equipment-Table-Enhanced.json`; defaults to `$NETA_DATA_DIR/NETA-Master-Equipment-Table-Enhanced.json`. FILE existence validated before use (a present directory with a missing master JSON fails). | source-backed migration tests |
| `PSQL_EXE` | psql binary; default-resolution chain (PATH, then the Windows install path) lives in `_dbtest.py`. | migration tests, runner |
| `RECORDS_ALLOW_SHARED_DB` | `1` = explicit legacy opt-in allowing a test to target a DB named `records_dev` (per-chip dev flow only). Never set by the runner or CI. Applies to BOTH test families (migration tests and records-import DB tests). | both test-side guards |

### Absence/refusal semantics

| Condition | Local default | `--require-db` (CI always) |
| --- | --- | --- |
| `RECORDS_DEV_DSN` unset (standalone package DB tests) | SKIP with one loud reason line | FAIL |
| `RECORDS_PG_ADMIN_DSN` unset (runner DB tiers) | SKIP Tiers 3-4 with one loud reason line | FAIL |
| `NETA_DATA_DIR` missing / not a directory | FAIL Tier 3 | FAIL |
| `NETA_JSON` missing / not a file | FAIL Tier 3 | FAIL |
| Target DB named `records_dev` without `RECORDS_ALLOW_SHARED_DB=1` | REFUSE (hard error) | REFUSE |

Evaluation order in the runner: the NETA checks (rows 3-4) are part of Tier 3
preflight and run BEFORE any skip decision is finalized, so a missing-source
condition is always reported as its own FAIL/SKIP-reason line - a source-data
problem can never hide behind a DB-provisioning skip. There is deliberately no
"skip source-backed tests" path: if the migration tier runs at all, the NETA inputs
must be present and validated. This is the operator's amendment, verbatim: CI
provisions the inputs intentionally, or the tier fails loudly.

## 4. Components

### 4.1 `infra/database/migrations/records/_dbtest.py` (new shared helper)

Mirrors the existing jobs-lane `_dbtest.py` convention. Centralizes what today is
copy-pasted across 38 test files, and becomes the SINGLE implementation of every
default-resolution chain (the runner and conftest both import it, so the path the
runner validates is provably the path the tests read):

- `dsn()` - returns `RECORDS_DEV_DSN` or skips/fails per the matrix. NO fallback
  value. Never inherits ambient `PGHOST`/`PGUSER` (they point at Supabase prod - the
  existing per-file pinning discipline, now in one place).
- `guard_target(dsn)` - parses the dbname; refuses `records_dev` unless
  `RECORDS_ALLOW_SHARED_DB=1`. Called by `dsn()` so every consumer gets it.
- `run_psql(args...)` - psql subprocess invocation with explicit env
  (`PGPASSWORD` from `RECORDS_DEV_PGPASSWORD` when set, `PGSSLMODE=disable`).
- `psql_exe()` / `neta_data_dir()` / `neta_json()` - own the default-resolution
  chains currently in conftest; VALIDATE existence; clear error naming the variable
  when absent. `neta_data_dir()` validates against an explicit `REQUIRED_NETA_FILES`
  tuple checked into `_dbtest.py` - every extract FILENAME the 023-038 tests
  actually read, enumerated from the test sources at build time - so preflight
  asserts the exact required files by name, never directory existence or counts.
  Layout note: the host mirror is FLAT (`~/neta-source/NETA-Data`) while the
  private repo nests `Development/NETA-Data`; both are just `NETA_DATA_DIR`
  values - the required-files assert makes layout differences irrelevant.

`conftest.py` becomes a thin shim that calls `_dbtest` for its setdefaults (kept so
standalone per-file pytest stays portable). The 38 test files and the generators are
edited mechanically: delete the local credential block, import from `_dbtest`. The
mechanical edit for the 16 source-backed tests (023-038) explicitly reroutes their
NETA path reads through `neta_data_dir()`/`neta_json()` so the validation actually
executes inside the tests. Generators get the same no-fallback treatment and FAIL
with a clear error naming the variable when the env is unset (they are manual tools,
not runner-invoked).

### 4.2 `packages/records-import/tests/conftest.py` (guard for the package DB tests)

The 3 DB-backed records-import test files - `test_db_write.py`,
`test_ingest_end_to_end.py`, `test_ingest_dtax_end_to_end.py` - get the same
semantics via a SMALL LOCAL conftest implementation (no import across the
packages/infra boundary; deliberately duplicated ~10 lines, kept identical by the
red proofs and review):

- `RECORDS_DEV_DSN` unset -> skip loudly (matrix row 1).
- dbname == `records_dev` without `RECORDS_ALLOW_SHARED_DB=1` -> hard refusal.

This closes the hole where `RECORDS_DEV_DSN=<records_dev> pytest packages/records-import`
would mutate the shared dev DB with no gate. The pure test files
(`test_review_proposal.py`, `test_ptm_transformer_mapping.py`, `test_smoke.py`)
are unaffected.

### 4.3 `infra/database/migrations/records/run_validation.py` (the runner)

Runs inside the records-import test environment (`pip install -e` both packages, or
`uv run` equivalent - psycopg comes from records-import's deps; the runner itself is
stdlib + psycopg). Tiers in order, exit code unmasked (no pipes between the test
process and the exit-code check), one summary table at the end. The runner logs the
dbname of EVERY connection it opens or hands to a child (AC1's verification hook).

- **Tier 0 - syntax + origin:** `python -m compileall` over both packages'
  `src` + `tests` and the records migrations directory. Then import-asserts
  `power_test_converters` and `records_import` and FAILS unless BOTH resolve to
  paths inside this repo checkout - the tripwire that kills any accidental
  PyPI-sourced install of the sibling name (see 4.5).
- **Tier 1 - converters:** `pytest packages/power-test-converters/tests -q` (pure).
- **Tier 2 - records-import pure:** `test_review_proposal.py`,
  `test_ptm_transformer_mapping.py`, `test_smoke.py`.
- **Tier 3 - migration stack (forward-incremental, disposable DB):**
  1. **Completeness preflight (fail-closed):** enumerate `NNN_*.sql` (excluding
     `*_down.sql`) and `test_NNN_*.py` up front. FAIL on: any gap in the numeric
     sequence 001..max (currently contiguous 001-044, verified 2026-07-02); any
     test file whose prefix matches no migration file. This makes red proof 1
     deterministic for ANY withheld migration and closes the silent-skip class
     (a renamed/drifted test can never quietly stop executing).
  2. **Env preflight:** `RECORDS_PG_ADMIN_DSN` dbname must equal `postgres`
     (strict); `neta_data_dir()` and `neta_json()` must validate (matrix rows 3-4).
  3. **Single-role model:** the disposable DB's DSN is the admin DSN with dbname
     replaced - same role, same host/port, same credentials. The runner exports
     `RECORDS_DEV_DSN` (disposable), `RECORDS_DEV_PGPASSWORD` (parsed from the
     admin DSN), and the resolved absolute `NETA_DATA_DIR`/`NETA_JSON`/`PSQL_EXE`
     into every child pytest/psql environment. No second role exists in the flow,
     so PG15+ public-schema ownership semantics cannot split behavior between
     host and CI. (Per-lane records roles are Gate 3.)
  4. `CREATE DATABASE records_val_<utcstamp>_<pid>` via the admin DSN. The name is
     generated by the runner; if it somehow pre-exists, REFUSE (no reuse).
  5. Walk migrations in numeric order: apply migration N via psql
     (`ON_ERROR_STOP=1`); if `test_NNN_*.py` exists, immediately run pytest on
     that one file against the disposable DB. Each test executes with nothing
     stacked above its own migration - the exact state it was developed in. The
     MANIFEST corruption class (out-of-order teardown) and the 020/021
     snapshot-reversion quirk are impossible by construction. **Stop on first
     failure:** a failed apply or failed test ends Tier 3 immediately (a failed
     test may have left its own migration downed - continuing would cascade
     misleading secondary failures), skips Tier 4, and proceeds to the drop.
     **Restoration assert (do not trust self-restore):** before each test_NNN the
     runner fingerprints the disposable DB (schema-only dump hash); after a
     SUCCESSFUL test it asserts the fingerprint round-trips - a PASSING test that
     failed to restore its migration is itself a Tier 3 FAILURE ("test did not
     restore its migration"). All 38 current tests self-restore (operator-swept
     2026-07-02, incl. 030/040/042/043); this closes the future class. If the
     schema-dump hash proves nondeterministic in practice, the documented
     fallback contract is an explicit reapply of migration N after each
     successful test - either implementation satisfies "the runner verifies
     restoration rather than trusting it".
  6. Ordering note: execution order derives from the filename numeric prefix. The
     MANIFEST declares strict sequential order; the runner does not parse MANIFEST
     prose - the completeness preflight is the machine-checkable stand-in.
- **Tier 4 - records-import DB:** the 3 DB-backed files, against the disposable DB
  Tier 3 just finished migrating (schema fully built). Runs only if Tier 3 passed.
- **Drop:** `DROP DATABASE` in a `finally:` covering Tiers 3-4. CREATE and DROP
  both assert the target name matches `records_val_*` AND is the exact name this
  run generated (allowlist, not a records_dev denylist - the operator's tightening).
  `--keep-db` skips the drop and prints the retained name for manual cleanup.
- **Flags:** `--require-db` (CI mode: absence anywhere = fail). `--only <tier>` for
  local iteration - a tier whose dependencies did not run REFUSES with a clear
  error rather than falling back to any ambient DSN; `--only 4` (and `--only 3`
  re-runs against a kept DB) require an explicit `--db-dsn` whose dbname matches
  `records_val_*`. There is no path by which a runner tier reads the ambient
  `RECORDS_DEV_DSN`.

### 4.4 `packages/power-test-converters/src/power_test_converters/testing.py` (new)

`_write_sample_ptm` and `_write_sample_template` move here as public
`write_sample_ptm` / `write_sample_template` (plus the private XML fragment builders
they depend on). `test_ptm_to_dtax.py` imports them back from the package;
`records-import/tests/test_ingest_dtax_end_to_end.py` drops the `sys.path.insert`
and imports `power_test_converters.testing`.

### 4.5 Converter dependency declaration (dependency-confusion safe)

`power-test-converters` is NOT published on PyPI, and this is a PUBLIC repo - a bare
name in the `[test]` extra would make every plain `pip install -e .[test]` resolve
the name against PyPI, where anyone can squat it. Therefore:

- The bare name goes in `[dependency-groups]` dev (PEP 735) in
  `records-import/pyproject.toml`, NOT in the pip-visible `[project.optional-dependencies]`
  test extra - plain pip never sees or resolves it.
- `[tool.uv.sources] power-test-converters = { path = "../power-test-converters", editable = true }`
  serves uv users (per-package source pin, consistent with the repo's documented
  no-uv-workspace rule).
- The pip path (CI and docs) is the explicit ordered pair, from REPO ROOT:
  `pip install -e packages/power-test-converters && pip install -e "packages/records-import[test]"`.
  (The `../power-test-converters` relative form is valid only when run from
  `packages/records-import`; docs state both, CI uses the repo-root form.)
- Tier 0's origin assert (4.3) is the runtime tripwire: even a wrongly-installed
  PyPI package fails the gate before any test imports it.
- Registering the name on PyPI as a defensive squat is noted as an operator option,
  not required by this lane.

### 4.6 `.github/workflows/records-ci.yml` (new)

On the calc-engine-ci pattern: pinned action SHAs, python 3.11, `ubuntu-latest`.

- **Triggers:** push + pull_request, path-filtered to
  `packages/power-test-converters/**`, `packages/records-import/**`,
  `infra/database/migrations/records/**`, and the workflow file itself.
- **Postgres:** `postgres:17` service container. Its password is a static throwaway
  literal in the workflow YAML (service-container env cannot be generated at
  runtime); this is safe because the container is job-scoped, unreachable from
  outside the runner, and holds only disposable data.
- **Source data (the amendment, first-class):** a second `actions/checkout` of the
  PRIVATE org repo `APEX-Power-Ops/neta-ett-study-material` (path: `neta-source`),
  PINNED to a commit SHA (bumped deliberately when extracts change), authenticated
  with repo secret `NETA_SOURCE_REPO_TOKEN` - a fine-grained PAT, read-only
  Contents on that single repo; operator creates and installs it out-of-band per
  the credential-custody model (the AI never sees the value); set to no-expiry or
  operator-calendared rotation so the gate has no silent time bomb.
  `NETA_DATA_DIR` is set to `$GITHUB_WORKSPACE/neta-source/Development/NETA-Data` -
  verified 2026-07-02 to carry the identical extract set as the (flat) host
  mirror. CI runs the SAME Tier 3 preflight as the host - the
  `REQUIRED_NETA_FILES` exact-filename assert (4.1) - before any migration work,
  so a wrong checkout path or missing file fails by NAME, not by count. The
  extracts never enter the public repo; the workflow logs the required-file check
  results by filename only, never extract content.
- **Run:** the ordered editable installs (4.5), then
  `python infra/database/migrations/records/run_validation.py --require-db` with
  `RECORDS_PG_ADMIN_DSN` pointed at the service container's `postgres` DB.
- Public-repo caveat (accepted): Actions secrets are not exposed to fork PRs, so
  the source-backed tier runs on same-repo branches only - which is how all lane
  PRs in this org work. A fork PR would fail the tier loudly, not false-green.

### 4.7 Fallback removal

All 47 in-scope `TCC_v5_2025` refs go to zero: 44 across
`infra/database/migrations/records/` (38 test files + generators; operator-verified
count 2026-07-02) + 3 in `packages/records-import/tests/`. The zero-grep over those
two trees is AC4. Out of scope: the jobs helper (spawned chip `task_c65d1e68`) and
the frozen 2026-06-17 plan doc `docs/superpowers/plans/2026-06-17-chip10a-capture-mode-import.md`
(historical artifact, outside the AC4 grep trees; its value dies at rotation).

### 4.8 Documentation

- Records MANIFEST: new "Validation" section - the runner is the primary path; the
  per-chip corruption-recovery recipe demoted to legacy/manual appendix.
- `reference/records/CURRENT-STATE.md`: Gate 2 marked done by this lane;
  minimum-resume-checklist items 3/4 satisfied.
- `infra/.env.dev.template` (or the repo's env template equivalent): the Section 3
  variables with one-line semantics each.
- `docs/lanes/README.md` records entry: validation-harness status line.

## 5. Red proofs (gate-proving, in PR evidence)

Two deliberate failures, run once and transcribed into the PR:

1. **Withheld migration:** run the runner against a scratch copy with one migration
   file removed -> the Tier 3 COMPLETENESS PREFLIGHT fails on the numeric gap (or
   the orphaned test file), deterministically, regardless of WHICH file is withheld
   - it never reaches apply. Runner exits nonzero; no disposable DB is left behind.
2. **Missing source data under `--require-db`:** run with `NETA_DATA_DIR` pointed at
   a nonexistent path -> Tier 3 preflight fails loudly naming the variable, exit
   nonzero.

A gate that has never been seen red is the false-green class; these two cover the
two failure families this lane exists to close (stack completeness / DB
provisioning, and source provisioning).

## 6. Security considerations

- The platform repo is PUBLIC. NETA extracts stay in the private
  `neta-ett-study-material` repo; CI accesses them read-only at runtime; nothing
  source-derived is added to the public repo beyond what the committed seed SQL
  already contains (the formal posture for that is Gate 9, Source-Content Policy -
  not relitigated here).
- `NETA_SOURCE_REPO_TOKEN`: fine-grained, single-repo, read-only Contents; operator
  provisions out-of-band; rotation is a one-secret swap.
- Dependency-confusion mitigation for the unpublished sibling package name (4.5).
- No DSN or password value ever appears in code, logs, or PR text (the CI service
  container's throwaway literal excepted - it protects nothing).
- Both test families default-refuse `records_dev`; the runner's CREATE/DROP is an
  allowlist on the exact `records_val_*` name it generated this run.

## 7. Closeout: credential rotation (operator-only, out-of-band)

The burned fallback value still authenticates somewhere: it was the Windows-local
PG18 password (host `apex-dev-pg` already rejects it - verified 2026-07-02). Final
lane task, AFTER the harness is merged and green:

- Operator rotates the password on the Windows-local PG18 instance (and anywhere
  else the value still opens), Vault-first per the L6 custody model.
- AI involvement is preconditions + post-verification only; the AI never handles
  the new value.
- Blast-radius note: Windows PG18 consumers are the local `tcc_fidelity_staging` /
  `postgres` MCP entries - operator updates those env entries out-of-band.

## 8. Acceptance criteria

- AC1: `run_validation.py` full pass green on the host. Verification method: the
  runner's connection log shows ONLY the maintenance DB (`postgres`) and the
  run-generated `records_val_*` name - `records_dev` appears nowhere; transcript
  attached to PR evidence.
- AC2: `records-ci.yml` green on the lane PR with the source-backed tests actually
  executing. Verification method: the runner summary prints per-tier
  executed/skipped counts; evidence asserts 16 source-backed migration test files
  and 3 records-import DB files EXECUTED (0 skipped) in the CI log.
- AC3: both red proofs demonstrated and transcribed in PR evidence.
- AC4: `grep -r TCC_v5_2025` over `infra/database/migrations/records/` and
  `packages/records-import/` returns zero.
- AC5: the `sys.path.insert` hack is gone; the converter dependency is declared per
  4.5; Tier 0's origin assert passes; both packages' suites pass under the runner.
- AC6: docs updated (MANIFEST validation section, CURRENT-STATE, env template,
  lanes README).
- AC7: rotation executed by operator; post-check transcribed: the old value fails
  authentication against the rotated instance.

## 9. Decisions log

| # | Decision | Status |
| --- | --- | --- |
| D1 | CI workflow ships with the runner in this lane (not local-first) | RATIFIED 2026-07-02 |
| D2 | Rotate the burned credential at lane close, operator-only | RATIFIED 2026-07-02 |
| D3 | Scope = records only; jobs helper is a spawned chip; frozen docs untouched | RATIFIED 2026-07-02 |
| D4 | Source-data provisioning = CI checkout of private `neta-ett-study-material` (SHA-pinned) via read-only fine-grained PAT secret, gated by the exact-filename `REQUIRED_NETA_FILES` preflight | RATIFIED 2026-07-02 (conditional on the exact-file preflight - folded this rev) |
| D5 | Default chains (`NETA_DATA_DIR`/`NETA_JSON`/`PSQL_EXE`) live in `_dbtest.py` as the single implementation; conftest is a shim; existence always validated | RATIFIED 2026-07-02 |
| D6 | Records-import DB tests = Tier 4, run against the disposable DB after the Tier 3 walk | RATIFIED 2026-07-02 |
| D7 | Single-role model: disposable DSN derived from the admin DSN (same role); per-lane records roles deferred to Gate 3 | RATIFIED 2026-07-02 |
| D8 | Converter dependency via dependency-groups + uv source + ordered pip installs (repo-root form in CI) + Tier 0 origin assert; NOT a bare name in the pip-visible test extra | RATIFIED 2026-07-02 (with install-path clarification) |
| D9 | Post-test restoration assert: runner verifies each passing migration test restored its migration (schema fingerprint round-trip; explicit-reapply fallback) | RATIFIED 2026-07-02 (operator review edit) |
