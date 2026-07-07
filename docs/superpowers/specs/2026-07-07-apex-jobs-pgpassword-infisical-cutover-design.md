# APEX_JOBS_PGPASSWORD Infisical Cutover - Design

Date: 2026-07-07
Status: DRAFT (operator review gate)
Branch: `secrets/apex-jobs-pgpassword-cutover` (host worktree `apex-secrets-apex-jobs-pw`)
Base: `main` 58d33c34
D1: RESOLVED - Option A, existing Infisical `dev` env (operator-ratified 2026-07-07).

## Goal

Cut the apex-jobs worker-ledger password from the `infra/.env` cache to Infisical
injection at launch, then remove the name from every cache AND from the audit
cache-allowlist. Establishes the injected-launch pattern for the later (bigger)
`DEV_PG_PASSWORD` lane. Bounded, dev-only, no prod schema, no consumer code change.

## Scope

IN:
- A thin injected launcher for apex-jobs (mirrors `infra/infisical/dev-psql.sh`).
- Remove `APEX_JOBS_PGPASSWORD` from `infra/.env` (operator-OOB) AND from the
  `secret-audit.sh` `ENV_ALLOWED_KEYS` default; arm the NAME in `.managed-secrets`.
- Flip the secret-audit allowlist test; value-silent proof; README runbook; Codex.

OUT (deferred, do NOT touch):
- `DEV_PG_PASSWORD`, `SUPABASE_PROD_DSN`, `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`.
- No prod schema. No change to `apex_jobs/db.py:resolve_dsn()` (already reads the var).
- The apex-jobs agent-sanitizer allowlist (`_env.py` / `test_env.py:13`) stays as-is.
  Subprocess inheritance is orthogonal to where the worker SOURCES the secret;
  tightening it (so agents cannot inherit the ledger cred) is a separate
  least-privilege lane - flagged here, not folded in.

## Ground truth (verified 2026-07-07)

- `packages/apex-jobs/src/apex_jobs/db.py:resolve_dsn()` reads `APEX_JOBS_PGPASSWORD`
  OR falls back to `DEV_PG_PASSWORD`, then builds a dev-tier DSN (`orchestration_dev`,
  `127.0.0.1:5432`, user `orchestration`, `sslmode=disable`). Full override via
  `APEX_JOBS_DSN`.
- Precedent launcher: `infra/infisical/dev-psql.sh` =
  `inject.sh dev -- bash -c 'PGPASSWORD="$DEV_PG_PASSWORD" exec psql "$@"' ...`.
- `inject.sh <dev|staging|prod> -- <cmd>` (project 985aac34...) passes the env slug
  straight to `infisical run --env=$SLUG`.
- `infra/infisical/.managed-secrets`: header rule - arm a NAME only after its value
  is gone from every cache, else Check 1c FAILs. Currently armed: `OPS_API_DSN`,
  `OPS_INTAKE_WRITER_DSN`.
- `infra/secret-audit.sh:67` default cache allowlist:
  `ENV_ALLOWED_KEYS="${APEX_ENV_ALLOWED_KEYS:-DEV_PG_PASSWORD APEX_JOBS_PGPASSWORD}"`.
  Check 1b PASSes only allowlisted keys found in `infra/.env`; Check 1c FAILs a
  `.managed-secrets` name that still lingers in the cache; the audit even hints the
  transition (line 99: "also in ENV_ALLOWED_KEYS - drop it there once removed").
- Baseline (verified 2026-07-07 on this dev host): `secret-audit.sh` already exits
  rc=1 because Check 1b FAILs the 3 parked keys `TCC_BREAKER_RO_PW` /
  `TCC_BREAKER_CODEX_PW` / `SUPABASE_PROD_DSN` (out of scope). `APEX_JOBS_PGPASSWORD`
  is absent from all 3 registered caches. `APEX_ENV_ALLOWED_KEYS` has NO override
  anywhere (only the `:67` default); CI runs only the fixture test (records-ci.yml),
  never the full audit against a real cache.
- `infra/database/migrations/records/test_secret_audit_env_allowlist.sh` currently
  asserts `APEX_JOBS_PGPASSWORD` is an ALLOWED cache key (exercises the DEFAULT
  allowlist) - must flip to managed / not-cache-allowed on cutover.

## Out-of-band prerequisites (operator; AI never handles the value)

1. Store `APEX_JOBS_PGPASSWORD` in Infisical project 985aac34... under the `dev` env.
2. Remove the `APEX_JOBS_PGPASSWORD=...` line from `infra/.env` (live credential
   file - AI does NOT sed-edit it per credential-file custody). The AI verifies the
   result value-silently: the NAME is absent, and the other cache keys
   (`DEV_PG_PASSWORD`, `SUPABASE_PROD_DSN`, `TCC_BREAKER_*`) are still present BY NAME.

(The AI sets preconditions and verifies a value-silent round-trip only; it never
reads, echoes, or transports any secret value.)

## Cutover choreography (ordered, fail-closed)

1. Add `infra/infisical/apex-jobs.sh`: `inject.sh dev -- uv run apex-jobs "$@"`.
   Whole file must pass `shellcheck` rc=0.
2. Value-silent proof (before any cache edit): under injection with `DEV_PG_PASSWORD`
   UNSET, `resolve_dsn()` uses the injected `APEX_JOBS_PGPASSWORD` and a live connect
   to `orchestration_dev` succeeds.
3. (operator-OOB) Remove `APEX_JOBS_PGPASSWORD` from `infra/.env`.
4. Allowlist SHRINK: remove `APEX_JOBS_PGPASSWORD` from the `ENV_ALLOWED_KEYS`
   default in `infra/secret-audit.sh:67` (default becomes just `DEV_PG_PASSWORD`),
   and flip `test_secret_audit_env_allowlist.sh` so `APEX_JOBS_PGPASSWORD` is
   asserted managed / no-longer-cache-allowed instead of allowed.
5. THEN arm `APEX_JOBS_PGPASSWORD` in `.managed-secrets`; verify NO new audit
   findings vs the parked baseline: `APEX_JOBS_PGPASSWORD` absent from all 3 caches
   (Check 1c/1d drift-clean, now 3 managed names) and Check 1b FAILs ONLY the
   pre-existing parked keys (`TCC_BREAKER_*`, `SUPABASE_PROD_DSN`) - unchanged, out of
   scope. Overall rc stays 1 for those parked keys: that is the accepted baseline,
   NOT a regression.
6. Update the apex-jobs README launch runbook to the injected launcher.
7. Whole-branch Codex cross-engine review before finishing (IRP).

Steps 3+4+5 are interdependent and land as one atomic cutover so `main` never sees
a red audit (a name dropped from `ENV_ALLOWED_KEYS` while still in `infra/.env` would
FAIL Check 1b; a name armed in `.managed-secrets` while still in `infra/.env` would
FAIL Check 1c).

## Tests (value-silent; assert on precomputed booleans, never on env/values)

- `resolve_dsn()` contract: with a non-secret SENTINEL in `APEX_JOBS_PGPASSWORD` and
  `DEV_PG_PASSWORD` UNSET, the resolved DSN targets `orchestration_dev` / user
  `orchestration` and carries the APEX_JOBS-sourced value; with both set, the
  APEX_JOBS one wins. Assert on booleans (substring-present bool, dbname), not a dump.
- Audit transition: `test_secret_audit_env_allowlist.sh` flipped so
  `APEX_JOBS_PGPASSWORD` is NOT cache-allowed (rejected if placed in a fixture `.env`)
  and `DEV_PG_PASSWORD` remains allowed; full `secret-audit.sh` returns rc=0 after the
  cutover (1b/1c/1d green). Value-silent throughout.
- `apex-jobs.sh` invokes `inject.sh dev -- uv run apex-jobs <args>` (PATH-stubbed
  `inject.sh`) and passes `shellcheck` rc=0.

## Rollback (reversible throughout)

Re-add the NAME to `infra/.env` (operator-OOB), restore it in the `ENV_ALLOWED_KEYS`
default, and unarm it in `.managed-secrets`. The `DEV_PG_PASSWORD` fallback in
`resolve_dsn()` keeps apex-jobs functional at every step, so there is no window where
the worker cannot start.

## Done / verification

Injected launch resolves + connects to `orchestration_dev`; `APEX_JOBS_PGPASSWORD`
absent from all local caches AND from `ENV_ALLOWED_KEYS`; NAME armed in `.managed-secrets`;
`secret-audit.sh` shows NO NEW findings vs the parked baseline (rc stays 1 ONLY for the
pre-existing out-of-scope parked keys `TCC_BREAKER_*` / `SUPABASE_PROD_DSN`; do NOT expect
rc=0), and `APEX_JOBS_PGPASSWORD` contributes zero findings; README updated; Codex review
clean. Host-canonical single-writer; ASCII-only added lines; no secret value ever handled.
