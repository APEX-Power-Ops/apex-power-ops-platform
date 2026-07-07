# DEV_PG_PASSWORD Dead-Fallback Removal -- Design

**Date:** 2026-07-07
**Lane:** `secrets/dev-pg-password-fallback-removal`
**Status:** design (pre-plan)
**Predecessor:** APEX_JOBS_PGPASSWORD Infisical cutover (PR #75, squash `9bfc29e1`)

## Goal

Remove the incoherent `DEV_PG_PASSWORD` fallback from every apex-jobs path that
connects as the `orchestration` role, so that role's password is unambiguously
`APEX_JOBS_PGPASSWORD` (Infisical `dev`, injected) with `APEX_JOBS_DSN` /
`ORCH_TEST_DSN` as the only whole-DSN overrides, and resolution fails closed when
neither is present. Reclassify `DEV_PG_PASSWORD` as the intentionally-retained
dev-cluster `postgres` superuser / `compose`-init credential. No credential is
removed from `infra/.env`; no consumer outside the orchestration path changes.

## Context and verified ground truth

From a value-silent live probe against the `apex-dev-pg` container (2026-07-07):

- `DEV_PG_PASSWORD` authenticates ONLY as `postgres` (`rolsuper=t`). It FAILS as
  `orchestration` and as `ops_app` (`AUTH_FAIL`). It is the cluster superuser password.
- `infra/compose.dev-lanes.yml:9` sets `POSTGRES_PASSWORD: ${DEV_PG_PASSWORD:?...}` on
  `postgres:17-alpine` (`container_name: apex-dev-pg`) -- `DEV_PG_PASSWORD` initializes
  the dev container superuser.
- `orchestration` authenticates via injected `APEX_JOBS_PGPASSWORD` (`CONNECT_OK`).
- Both `DEV_PG_PASSWORD` and `APEX_JOBS_PGPASSWORD` are present in Infisical `dev`.
- The injected launcher `infra/infisical/apex-jobs.sh` ALREADY EXISTS (built in #75);
  it injects `APEX_JOBS_PGPASSWORD` from `dev` and runs `uv run apex-jobs` against
  `orchestration_dev`, exporting `APEX_JOBS_REPO` to the checkout. This lane
  PRESERVES and RE-VERIFIES it; it does NOT add a launcher.

Consequence: any `... or os.environ.get("DEV_PG_PASSWORD")` fallback under a
`user=orchestration` connection is knowingly false -- it can never authenticate.
That dead fallback (not a stale-but-recoverable path) is the transitional debt this
lane closes.

## The rule this lane establishes

- `APEX_JOBS_PGPASSWORD` = the `orchestration` role password (Infisical `dev`).
- `APEX_JOBS_DSN` / `ORCH_TEST_DSN` = explicit whole-DSN overrides (unchanged).
- `DEV_PG_PASSWORD` = `postgres` superuser / `compose`-init / dev-cluster admin
  password. It is NEVER an orchestration-role fallback.
- `DEV_PG_PASSWORD` STAYS in `infra/.env` (the superuser and `compose` init both need
  it), remains the sole `ENV_ALLOWED_KEYS` entry in `infra/secret-audit.sh`, and is
  NOT armed in `.managed-secrets`. Its presence in the cache is intentional, not debt.

## Scope

### In scope -- code (behavior), TDD-gated

1. `packages/apex-jobs/src/apex_jobs/db.py` -- `resolve_dsn()`:
   - drop `or os.environ.get("DEV_PG_PASSWORD")`; `pw = os.environ.get("APEX_JOBS_PGPASSWORD")`.
   - when `pw` is absent, raise `RuntimeError` whose message names `APEX_JOBS_PGPASSWORD`,
     the `APEX_JOBS_DSN` override, and `infra/infisical/apex-jobs.sh`, and states that
     `DEV_PG_PASSWORD` is the postgres superuser password and does NOT authenticate as
     `orchestration`.
   - `APEX_JOBS_DSN` override path unchanged.
   - update the module docstring (line 6) to reference `APEX_JOBS_PGPASSWORD` (injected)
     rather than `DEV_PG_PASSWORD`.

2. `packages/apex-jobs/tests_unit/test_dsn_resolution.py` -- the always-runs, no-DB,
   value-silent contract lock. Rewrite to the new contract (SENTINEL values, precomputed
   booleans, no env dump). `DEV_PG_PASSWORD` STAYS in the `_KEYS` save/restore tuple (so a
   test can set it and prove it is ignored). Tests:
   - `test_apex_jobs_pw_resolves`: injected `APEX_JOBS_PGPASSWORD=SENTINEL_A` -> DSN targets
     `dbname=orchestration_dev`, `user=orchestration`, `password=SENTINEL_A`.
   - `test_dev_pg_password_alone_does_not_resolve` (**the load-bearing RED test**): only
     `DEV_PG_PASSWORD=SENTINEL_B` set -> `resolve_dsn()` raises `RuntimeError` AND
     `SENTINEL_B` never appears in the DSN or the raised message.
   - `test_missing_apex_jobs_pw_raises`: neither `APEX_JOBS_PGPASSWORD` nor `APEX_JOBS_DSN`
     set -> `RuntimeError`.
   - `test_apex_jobs_dsn_override_wins`: `APEX_JOBS_DSN=SENTINEL_DSN` set (no pw) -> returned
     verbatim.
   - update the module docstring (line 2) to state `DEV_PG_PASSWORD` is NOT a fallback.

3. `packages/apex-jobs/tests/conftest.py`:
   - `PGPW = os.environ.get("APEX_JOBS_PGPASSWORD")` (drop the `DEV_PG_PASSWORD` fallback).
   - update `ENV_HINT` (line 55) and the module docstring (line 5) to drop `DEV_PG_PASSWORD`.

4. `infra/database/migrations/jobs/_dbtest.py`:
   - `pw = os.environ.get("ORCH_TEST_PGPASSWORD") or os.environ.get("APEX_JOBS_PGPASSWORD")`
     (replace the dead `DEV_PG_PASSWORD` fallback with `APEX_JOBS_PGPASSWORD`). The helper
     connects as `-U orchestration`, so its password env must be an orchestration-role
     password; `APEX_JOBS_PGPASSWORD` lets the jobs migration tests run under the same
     `inject.sh dev` path as the package suite. `ORCH_TEST_DSN` whole-DSN override unchanged.
   - update `ENV_HINT` (line 24) and the module docstring (line 6).

### In scope -- cleanup sweep (stale user-facing strings)

5. `packages/apex-jobs/tests/test_review_worktree_lock.py:96` -- inside
   `test_e6_resolve_dsn_runtimeerror_value_silent`, the synthetic
   `RuntimeError("APEX_JOBS_PGPASSWORD or DEV_PG_PASSWORD required")` stand-in for
   `resolve_dsn()`'s error. Update to drop `DEV_PG_PASSWORD` so it mirrors the real
   message. Cosmetic (the test asserts on value-silent wrapping, not the string), but this
   is a DB-fixture test -- re-run it via injection after editing.

### In scope -- docs / comments (text only)

6. `infra/database/migrations/jobs/MANIFEST.md` -- the credential note (line 30) and the
   "Apply to a database" block (line 51, `PGPASSWORD=$DEV_PG_PASSWORD psql -U orchestration`,
   which cannot authenticate) -> `APEX_JOBS_PGPASSWORD` / injection.
7. `.env.dev.template` -- jobs-lane creds block (line 47): canonical source of the
   orchestration-role password is `APEX_JOBS_PGPASSWORD` (injected from Infisical); note that
   `DEV_PG_PASSWORD` is the postgres superuser and does not authenticate as `orchestration`.
8. `packages/apex-jobs/README.md:36` -- delete the stale "`DEV_PG_PASSWORD` (still cached)
   remains the fallback ..." clause in the CLI section. The Tests-section wording (line 61)
   is already correct and stays.
9. `infra/secret-audit.sh` -- add a comment above `ENV_ALLOWED_KEYS` (line 67) documenting
   WHY `DEV_PG_PASSWORD` is the sole allowed cache key: the postgres superuser / `compose`-init
   credential, intentionally retained. The allowlist VALUE is UNCHANGED.
10. `infra/infisical/README.md` -- one line noting `DEV_PG_PASSWORD` is intentionally retained
    (superuser / `compose`-init), not a cutover target.

### Explicitly KEPT (do not touch)

- `packages/apex-jobs/tests/test_env.py:13` and
  `packages/apex-jobs/tests/test_agent_runner.py:269` -- `_SECRET_BATTERY` entries. Here
  `DEV_PG_PASSWORD` is a real secret shape the sanitizer must strip; keeping it exercises
  the default-deny policy. These tests are unrelated to the orchestration fallback.

### Out of scope (deferred to a separate platform-wide lane)

- Removing `DEV_PG_PASSWORD` from `infra/.env`.
- Wrapping `docker compose up` (or `compose.dev-lanes.yml`) in `inject.sh`.
- Migrating any dev lane's `postgres`-admin (`user=postgres`) workflow (ops, learning,
  records, estimator) off `infra/.env`. Those references are correct today
  (`DEV_PG_PASSWORD` IS the superuser) and mostly live in historical `docs/superpowers/plans/*`.

## Validation (value-silent throughout; no secret value printed)

1. **Load-bearing RED->GREEN:** `test_dev_pg_password_alone_does_not_resolve` fails on the
   current code (fallback resolves a DSN) and passes after the change (raises). This test is
   what prevents the fallback from silently drifting back.
2. `tests_unit/test_dsn_resolution.py` full contract green with NO DB and NO credentials
   (it lives outside the DB conftest scope).
3. **Normal launcher proof (working path):**
   `env -u DEV_PG_PASSWORD infra/infisical/apex-jobs.sh queue` runs the launcher end to end and
   connects as `orchestration` via the injected `APEX_JOBS_PGPASSWORD`. This proves ONLY the
   working path, and the wording must not imply more: `inject.sh dev` injects the whole `dev`
   secret set, so `DEV_PG_PASSWORD` IS present in the child process here (the parent-side
   `env -u` does not reach the injected child) -- it is simply unused after the fix. A no-arg
   read verb is required: `status` takes a positional `ident` (`cli.py:340`) and exits in
   argparse before connecting; `queue` (`cli.py:297`) opens a DB connection.
4. **Strict fallback-removal proof (suites, `DEV_PG_PASSWORD` genuinely absent from the
   process):** `unset` it INSIDE the injected child (after injection), so the removed fallback
   cannot be load-bearing even when the value is truly unavailable to the process. Command
   shapes (the plan pins exact flags):
   - package suite:
     `infra/infisical/inject.sh dev -- bash -c 'unset DEV_PG_PASSWORD; cd packages/apex-jobs && APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest'`
   - jobs migration tests:
     `infra/infisical/inject.sh dev -- bash -c 'unset DEV_PG_PASSWORD; cd infra/database/migrations/jobs && uv run --with "psycopg[binary]" --with pytest pytest'`
   Both green prove the injected `APEX_JOBS_PGPASSWORD` path carries the suites and the removed
   `DEV_PG_PASSWORD` fallback was dead. The `tests_unit` contract (step 2) already proves the
   resolution layer with no DB and no credentials at all.
5. **No-regression `secret-audit.sh`:** identical FAIL set to the pre-lane baseline (the
   parked keys `SUPABASE_PROD_DSN`, `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`);
   `DEV_PG_PASSWORD` still allowed by name; `.managed-secrets` unchanged; only a comment added
   to the script.
6. **Focused Codex** cross-engine review via the `apex-jobs review-run` front door (run
   through injection), folded into the review record before PR.

## Execution model

- **Host-canonical single-writer over mesh.** ONE writer on the host worktree. Author locally
  (Windows scratchpad) -> `scp` per file -> commit host-side, OR edit host-side directly; never
  push a stale mirror.
- **Lane branch in the MAIN worktree** (`/home/olares/code/apex/apex-power-ops-platform`), NOT a
  linked worktree. The injection (`inject.sh` self-auth from `.env.agent`), `secret-audit.sh`
  (Check 1b reads `infra/.env`), the injected round-trip, and the live DB suites ALL require the
  gitignored 0600 caches that live only in the main worktree. Running the lane there keeps the
  caches present and avoids the per-worktree cache false-clean trap. `main` is restored after
  merge.
- **Value-silent:** assert on precomputed booleans / SENTINELs / name-lists, never `env` dumps;
  never echo a secret value or a full DSN; classify psql stderr, never dump it.
- **ASCII-only added lines** in code and shell; **shellcheck rc=0** on any edited shell file
  (`infra/secret-audit.sh`).
- **Merge governance:** author self-merges after green CI + Codex; squash; NO admin-bypass.

## File summary

Behavior (4): `db.py`, `tests_unit/test_dsn_resolution.py`, `tests/conftest.py`,
`infra/database/migrations/jobs/_dbtest.py`.
Cleanup (1): `tests/test_review_worktree_lock.py`.
Docs (5): `MANIFEST.md`, `.env.dev.template`, `packages/apex-jobs/README.md`,
`infra/secret-audit.sh`, `infra/infisical/README.md`.
Untouched by design: `test_env.py`, `test_agent_runner.py`, `secret-audit.sh` allowlist VALUE,
`.managed-secrets`, `infra/.env`, `apex-jobs.sh`.
