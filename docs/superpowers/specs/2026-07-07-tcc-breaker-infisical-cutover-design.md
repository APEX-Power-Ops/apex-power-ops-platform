# TCC_BREAKER_* Infisical Cutover + Retire -- Design

**Date:** 2026-07-07
**Lane:** `secrets/tcc-breaker-infisical-cutover`
**Status:** design (OOB gated steps already completed + verified; see below)
**Predecessors:** APEX_JOBS_PGPASSWORD cutover (#75, `9bfc29e1`); DEV_PG_PASSWORD dead-fallback removal (#76, `d40dd6b8`)

## Goal

Close the two remaining parked breaker keys in the host `infra/.env` cache: cut `TCC_BREAKER_RO_PW`
over to Infisical `dev` (injected) and **retire** `TCC_BREAKER_CODEX_PW` (dead one-off, no Infisical
load). This shrinks the `secret-audit` Check-1b parked-key FAIL set from 3 to 1 (only `SUPABASE_PROD_DSN`).

## Verified ground truth (value-silent probes, 2026-07-07)

- Both keys are credentials for the SAME 2026-06-25 breaker sandbox on the `apex-dev-pg` container
  (roles `tcc_breaker_ro` / `tcc_breaker_codex_79audit`, DBs `tcc_breaker_baseline/viewer/codex_79audit_20260625`).
- `TCC_BREAKER_RO_PW` has ONE live consumer: the access-harness `snapshot_tcc.host_tcc_conn()`
  (`infra/database/access-harness/access_harness/snapshot_tcc.py`), which connects **read-only** to
  `dbname=tcc_breaker_viewer_20260625` on `100.64.0.1:5432` (the container's MESH ip) as `tcc_breaker_ro`.
  The `DB_NAME` is hardcoded to that sandbox viewer clone -- it is NOT a separate governed remote TCC.
  `host_tcc_conn` is cross-platform psycopg (the Access/pyodbc path is a SEPARATE, Windows-only prereq),
  so it is exercisable from the host via injection.
- `TCC_BREAKER_CODEX_PW` has NO live consumer: its only user was the completed 2026-06-25 breaker
  sandbox codex-harness (`infra/database/sandbox/breaker/codex-harness/`). The `breaker-viewer` MCP is
  GONE (0 entries + 0 refs in host `~/.claude.json`); nothing connects as `tcc_breaker_codex_79audit`.
- Neither key was in Infisical before this lane; both were cache-only in host `infra/.env`.

## Operator decisions (ratified)

1. **F-79-03 access-harness is treated as still live / reproducibility-relevant** -> `TCC_BREAKER_RO_PW`
   is a real cutover.
2. **`TCC_BREAKER_CODEX_PW` is retired** -- no Infisical load, not armed in `.managed-secrets`; removed
   from the cache after the lane documents the dead-consumer finding.
3. **Sandbox DB/role DROP is OUT of scope** -- the `tcc_breaker_*_20260625` DBs + `tcc_breaker_ro` /
   `tcc_breaker_codex_79audit` roles get their own separate destructive-cleanup packet.
4. **Cutover target = the host `infra/.env` copy** (what `secret-audit` governs). The Windows full-Access
   pipeline reads `TCC_BREAKER_RO_PW` as a *Windows environment variable* -- a separate machine cache,
   OUT of scope here (a Windows Infisical-CLI injection is a future/separate concern).

## OOB gated steps -- COMPLETED + VERIFIED (value-silent)

The operator has already (a) loaded `TCC_BREAKER_RO_PW` into Infisical `dev` and (b) removed BOTH
`TCC_BREAKER_*` from host `infra/.env`. Verified 2026-07-07:
- host `infra/.env` now holds only `DEV_PG_PASSWORD` + `SUPABASE_PROD_DSN`;
  `grep -c '^TCC_BREAKER_RO_PW='` == 0 and `'^TCC_BREAKER_CODEX_PW='` == 0.
- Infisical `dev`: `TCC_BREAKER_RO_PW` present, `TCC_BREAKER_CODEX_PW` ABSENT.
- Injected host round-trip: `inject.sh dev -- <host_tcc_conn probe>` -> `RO_ROUNDTRIP_OK` (connects to
  `tcc_breaker_viewer_20260625` via the injected RO_PW). The removed cache copy was NOT load-bearing.

## Committed changes (no code change; the harness already reads `os.environ`)

1. `infra/database/access-harness/README.md` -- Environment section + a host-run-via-injection note:
   host-side `snapshot-tcc` / harness tests use `infra/infisical/inject.sh dev -- ...` (RO_PW injected
   from Infisical `dev`); clarify `host_tcc_conn` targets the sandbox viewer clone
   `tcc_breaker_viewer_20260625`; note the Windows full-Access pipeline reads `TCC_BREAKER_RO_PW` as a
   Windows env var (a separate machine cache).
2. `infra/database/sandbox/breaker/README.md` -- record the CODEX_PW retirement finding: the sandbox is
   a completed 2026-06-25 one-off; `TCC_BREAKER_CODEX_PW` is retired (removed from host `infra/.env`,
   NOT in Infisical, NOT armed); the codex-harness + `_20260625` DBs/roles are leftover residue for the
   separate destructive-cleanup packet; re-running the sandbox requires re-seeding the vars.
3. `infra/infisical/.managed-secrets` -- arm `TCC_BREAKER_RO_PW` (git-tracked). `TCC_BREAKER_CODEX_PW`
   is NOT armed.

Untouched by design: `secret-audit.sh` `ENV_ALLOWED_KEYS` (RO_PW is armed -> governed by Check 1c, not
the allowlist); the access-harness Python (reads env, no change); `packages/apex-jobs/tests/test_env.py`
+ `test_agent_runner.py` `_SECRET_BATTERY` (KEEP both names -- real secret shapes the sanitizer strips).

## Verification (value-silent)

- Infisical `dev`: RO_PW present, CODEX_PW absent (re-confirmed).
- Injected host round-trip green with a clean shell (injection-only): `RO_ROUNDTRIP_OK`.
- host `infra/.env`: both `TCC_BREAKER_*` absent by name (`grep -c` == 0).
- **No-regression / drift audit:** `secret-audit.sh` -- Check-1b FAIL set = ONLY `SUPABASE_PROD_DSN`
  (down from 3); `TCC_BREAKER_RO_PW` passes Check 1c (armed name, not in any cache);
  `TCC_BREAKER_CODEX_PW` no longer appears anywhere (removed, not armed). `AUDIT_RC=1` (SUPABASE_PROD_DSN
  keeps it non-zero -- expected). Value-silent (names only).
- Focused Codex whole-branch review via `apex-jobs review-run` through injection before PR.

## Out of scope (separate destructive packet)

`DROP DATABASE tcc_breaker_baseline_20260625 / tcc_breaker_viewer_20260625 / tcc_breaker_codex_79audit_20260625`
and `DROP ROLE tcc_breaker_ro / tcc_breaker_codex_79audit`. Dropping the viewer clone would end the
F-79-03 harness data source, so that decision is deferred to its own operator-gated cleanup.

## Execution model

Host-canonical single-writer over mesh; lane branch runs IN the MAIN worktree (caches present for
injection + `secret-audit`); value-silent; ASCII-only added lines; merge governance: squash, author
self-merge after green CI + Codex, no admin-bypass; restore `main` after merge.
