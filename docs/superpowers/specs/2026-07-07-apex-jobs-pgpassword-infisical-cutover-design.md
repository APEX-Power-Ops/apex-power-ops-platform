# APEX_JOBS_PGPASSWORD Infisical Cutover - Design

Date: 2026-07-07
Status: DRAFT (operator review gate)
Branch: `secrets/apex-jobs-pgpassword-cutover` (host worktree `apex-secrets-apex-jobs-pw`)
Base: `main` 58d33c34

## Goal

Cut the apex-jobs worker-ledger password from the `infra/.env` cache to
Infisical injection at launch, then remove the name from every cache. This
establishes the injected-launch pattern for the later (bigger) `DEV_PG_PASSWORD`
lane. Bounded, dev-only, no prod schema, no consumer code change.

## Scope

IN:
- A thin injected launcher for apex-jobs (mirrors `infra/infisical/dev-psql.sh`).
- Remove `APEX_JOBS_PGPASSWORD` from `infra/.env`; arm the NAME in
  `infra/infisical/.managed-secrets`.
- Value-silent tests + secret-audit green + README runbook + Codex review.

OUT (deferred, do NOT touch): `DEV_PG_PASSWORD`, `SUPABASE_PROD_DSN`,
`TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`. No prod schema. No change to
`apex_jobs/db.py:resolve_dsn()` (it already reads the env var).

## Ground truth (verified 2026-07-07)

- `packages/apex-jobs/src/apex_jobs/db.py:resolve_dsn()` reads
  `APEX_JOBS_PGPASSWORD` OR falls back to `DEV_PG_PASSWORD`, then builds a
  dev-tier DSN (`orchestration_dev`, `127.0.0.1:5432`, user `orchestration`,
  `sslmode=disable`). A full override is available via `APEX_JOBS_DSN`.
- Precedent launcher: `infra/infisical/dev-psql.sh` =
  `inject.sh dev -- bash -c 'PGPASSWORD="$DEV_PG_PASSWORD" exec psql "$@"' ...`.
- `inject.sh <dev|staging|prod> -- <cmd>` (project 985aac34...) passes the env
  slug straight to `infisical run --env=$SLUG`.
- `.managed-secrets` ordering rule (verified in its header): arm a NAME ONLY
  after its value is removed from every cache, else secret-audit Check 1c FAILs.

## DECISION D1 - Infisical env slug (LEAN: Option A; pending operator ratification)

- Option A - existing `dev` env (LEAN): minimal, mirrors `dev-psql.sh`; one OOB
  action (store the secret in `dev`); launcher = `inject.sh dev -- apex-jobs ...`.
  apex-jobs inherits the whole dev secret set.
- Option B - dedicated `orchestration` env: better least-privilege isolation and
  matches the dedicated-per-workstream posture; costs an extra env to create +
  populate, and repurposes the tier axis (dev/staging/prod) as a workstream axis.

Rationale for A: least-privilege gain is marginal here (same tier as
`DEV_PG_PASSWORD`, which the later lane revisits wholesale); A is lowest-friction
and precedent-matching. Switching to B changes only the launcher default slug and
the store location.

## Out-of-band prerequisite (operator; AI never handles the value)

Store `APEX_JOBS_PGPASSWORD` in Infisical project 985aac34... under the env
chosen in D1. The AI sets preconditions and verifies a value-silent round-trip
only; it never reads, echoes, or transports the secret value.

## Cutover choreography (ordered, fail-closed)

1. Add `infra/infisical/apex-jobs.sh`: `inject.sh <env> -- uv run apex-jobs "$@"`
   (env defaulting per D1). Whole file must pass `shellcheck` rc=0.
2. Value-silent proof (before any cache edit): under injection with
   `DEV_PG_PASSWORD` UNSET, `resolve_dsn()` uses the injected
   `APEX_JOBS_PGPASSWORD` and a live connect to `orchestration_dev` succeeds.
3. Remove `APEX_JOBS_PGPASSWORD` from `infra/.env`.
4. THEN arm `APEX_JOBS_PGPASSWORD` in `.managed-secrets`; confirm secret-audit
   Check 1c (no stale cache copy) and Check 1d (cache-coverage) are green.
5. Update the apex-jobs README launch runbook to the injected launcher.
6. Whole-branch Codex cross-engine review before finishing (IRP).

## Tests (value-silent; assert on precomputed booleans / reachability, never env)

- `resolve_dsn()` prefers `APEX_JOBS_PGPASSWORD` over `DEV_PG_PASSWORD`: set the
  former, UNSET the latter, assert the resolved DSN targets `orchestration_dev`
  and a connection opens. Assert on a boolean + dbname string, never the password.
- secret-audit Check 1c/1d return rc=0 after the arm step.
- `apex-jobs.sh` passes `shellcheck` rc=0 (binding gate on the edited shell file).

## Rollback (reversible throughout)

Re-add the NAME to `infra/.env` and unarm it in `.managed-secrets`. The
`DEV_PG_PASSWORD` fallback in `resolve_dsn()` keeps apex-jobs functional at every
step, so no window where the worker cannot start.

## Done / verification

Injected launch resolves + connects to `orchestration_dev`; `APEX_JOBS_PGPASSWORD`
absent from `infra/.env`; NAME armed in `.managed-secrets`; secret-audit green;
Codex review clean. Host-canonical single-writer; ASCII-only added lines.
