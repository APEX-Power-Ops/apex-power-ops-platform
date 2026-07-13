# Prod read-only census — run transcript (2026-07-13, redacted)

Read-only disposition census of prod `fxoyniqnrlkxfligbxmg` public schema, run per `CENSUS_RUNBOOK.md`
on explicit operator GO (Phase 6 of the gated evidence roadmap) from the merged-main worktree at
`main@7a70cb6322a29a59f36db67e8665a95e3c20cc01` (the PR #92 squash-merge SHA — the first census taken
after the overlay-publication tooling landed). Value-silent: the prod DSN and the Ed25519 signing key
were injected into the collector child by `infra/infisical/inject.sh prod` and never appeared on argv,
in output, or in this transcript.

## Provenance (runbook step 2)
`git fetch origin main`; `MAIN_SHA=$(git rev-parse origin/main)` = `7a70cb6322a29a59f36db67e8665a95e3c20cc01`.
Asserted on `main`, local HEAD == origin/main, worktree clean -> PROVENANCE OK.
Offline pins re-derived live before any prod access (operator Phase-6 preconditions):
query-bundle `217ff3add2abdaca2fafa108f68e10490ee687ac9899b7762f1411d45e2de9db` (== pinned) and
committed public-key SPKI `c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca`
(re-derived via `disposition_trust.resolve_pinned_key`, == source-pinned `TRUSTED_SIGNERS`).

## Collection (runbook step 3) — read-only, one run
Result: `=== CENSUS: 118 relations -> prod-20260713T154550Z.json (db=postgres user=postgres bundle 217ff3add2ab) ===`, exit 0.
Snapshot + Ed25519 detached sidecar published no-clobber OUTSIDE the repo (the injector reported
injecting its secret set into the child process only; nothing entered the operator shell).

## Acceptance (runbook step 4) — offline
`verify_census.py --key-id prod-disposition-ed25519-2026-07 --require-clean-checkout --expect-query-bundle-sha256 217ff3add2abdaca2fafa108f68e10490ee687ac9899b7762f1411d45e2de9db --expect-project-ref fxoyniqnrlkxfligbxmg --expect-database postgres --expect-schemas public --expect-repo-sha $MAIN_SHA --require-role-markers anon,authenticated,service_role`
Result: `=== CENSUS ACCEPTANCE: GREEN (118 relations, scope ['public']) ===`, exit 0.

## Facts (non-secret)
- project_ref `fxoyniqnrlkxfligbxmg`; repo_sha `7a70cb6322a29a59f36db67e8665a95e3c20cc01`; schemas `[public]`.
- observed_at `2026-07-13T15:45:51.086245+00:00` (DB clock).
- relation_count == catalog_relation_count == 118 (emitted list == independent catalog count); zero `query_failed` observations.
- target: current_user=postgres, current_database=postgres, transaction_read_only=True, guard_passed=True.
- platform_role_markers: anon, authenticated, authenticator, postgres, service_role.
- server_version: PostgreSQL 17.6 (170006, aarch64); read-only catalog SELECTs only, no writes.
- signer prod-disposition-ed25519-2026-07, public_key_sha256 `c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca` (== source-pinned TRUSTED_SIGNERS).

## Committed-artifact hashes (all three)
- `census-prod-20260713T154550Z.json` sha256 `52962abea7c8b81f62e6331c169f9b6963bf546763a76898cf707d076cf94130`
  (byte-for-byte copy of the out-of-repo original; also the sidecar `signed_sha256` — the exact bytes the signature covers).
- `census-prod-20260713T154550Z.json.sig` sha256 `f7cb9902fd7d72bfc63177368a7b7648c45930c3fb83ed547f047e4c78c0953b`.
- sidecar `signed_sha256` `52962abea7c8b81f62e6331c169f9b6963bf546763a76898cf707d076cf94130` (== census file sha256).

## Secret-scan
Transcript (7 lines) and snapshot both scanned CLEAN (Python pattern scan: DSN URLs, hostaddr,
private-key blocks, password/JWT/env-value patterns — zero hits). No secret entered the operator
shell (secrets lived only in the injected collector child). Prod was READ ONLY. The raw `.log`
remains out-of-repo at the collection host (`~/census-evidence/transcript-20260713T154550Z.log`);
this document is the committed, redacted record of it.
