# Prod read-only census — run transcript (2026-07-11, redacted)

Read-only disposition census of prod `fxoyniqnrlkxfligbxmg` public schema, run per `CENSUS_RUNBOOK.md`
on explicit operator GO from the merged-main worktree at `main@a67d95ee310c8d77c0d6340a76220ad942f1748a`.
Value-silent: the prod DSN and the Ed25519 signing key were injected into the collector child by
`infra/infisical/inject.sh prod` and never appeared on argv, in output, or in this transcript.

## Provenance (step 2)
`git fetch origin main`; `MAIN_SHA=$(git rev-parse origin/main)` = `a67d95ee310c8d77c0d6340a76220ad942f1748a`.
Asserted on `main`, local HEAD == origin/main, worktree clean -> PROVENANCE OK.

## Collection (step 3) — read-only, one run
Result: `=== CENSUS: 118 relations -> prod-20260711T215509Z.json (db=postgres user=postgres bundle 217ff3add2ab) ===`, exit 0.
Snapshot + Ed25519 detached sidecar published no-clobber OUTSIDE the repo.

## Acceptance (step 4) — offline
`verify_census.py --key-id prod-disposition-ed25519-2026-07 --require-clean-checkout --expect-query-bundle-sha256 217ff3add2abdaca2fafa108f68e10490ee687ac9899b7762f1411d45e2de9db --expect-project-ref fxoyniqnrlkxfligbxmg --expect-database postgres --expect-schemas public --expect-repo-sha $MAIN_SHA --require-role-markers anon,authenticated,service_role`
Result: `=== CENSUS ACCEPTANCE: GREEN (118 relations, scope ['public']) ===`, exit 0.

## Facts (non-secret)
- project_ref `fxoyniqnrlkxfligbxmg`; repo_sha `a67d95ee...`; schemas `[public]`.
- relation_count == catalog_relation_count == 118 (emitted list == independent catalog count).
- target: current_user=postgres, current_database=postgres, transaction_read_only=True, guard_passed=True.
- platform_role_markers: anon, authenticated, authenticator, postgres, service_role.
- server_version: PostgreSQL 17.6 (prod is PG17.6; the catalog SQL + independent count ran read-only without issue).
- signer prod-disposition-ed25519-2026-07, public_key_sha256 `c75785cd...dc592ca` (== source-pinned TRUSTED_SIGNERS).
- signed_sha256 `5bb4191fea584f4cecf111c718382bc3f6d0d88707a7c6e9c4c5065132ac416e`.

## Secret-scan
No DSN / key / password / JWT / hostaddr patterns in the snapshot or sidecar. No secret entered the
operator shell (secrets lived only in the injected collector child). Prod was READ ONLY (REPEATABLE READ
read-only catalog SELECTs; no writes).
