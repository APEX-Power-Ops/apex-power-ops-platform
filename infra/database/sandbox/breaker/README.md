# Breaker Sandbox (air-gapped) — runbook

An air-gapped copy of the breaker catalog (`tcc.*`) on the Olares host so Codex can work the
lvbreakertcc lane with ZERO risk to prod Supabase. Design spec:
`docs/superpowers/specs/2026-06-25-breaker-sandbox-codex-lane-design.md`.

## Databases (host `apex-dev-pg`, PG17)
- `tcc_breaker_baseline_<date>` — one-way restore of prod `tcc`. Frozen; no routine connections
  (clean `TEMPLATE` source).
- `tcc_breaker_viewer_<date>` — read-only clone for MCP/operator inspection (RLS disabled
  clone-locally; `tcc_breaker_ro` has SELECT only).
- `tcc_breaker_codex_<task>_<date>` — disposable writable clone owned by `tcc_breaker_codex_<task>`.

## Roles (no cluster-wide attributes)
- `tcc_breaker_ro` — SELECT on the viewer clone only.
- `tcc_breaker_codex_79audit` — owns its clone's tcc objects; no baseline, no viewer. Passwords in
  the gitignored 0600 `infra/.env` (`TCC_BREAKER_RO_PW` / `TCC_BREAKER_CODEX_PW`).

## Seed (operator-side; prod cred never lands on the host)
```
# CC pre-creates the landing dir:
ssh olares-mesh 'umask 077; install -d -m 700 /home/olares/dev-pg-backups/tcc'
# Operator (own machine, cred from Vault):
pg_dump --no-owner --no-privileges --schema=tcc -Fc "$PROD_RO_DSN" -f tcc_baseline_20260625.dump
scp tcc_baseline_20260625.dump olares-mesh:/home/olares/dev-pg-backups/tcc/
```

## Provision order
(run from `infra/database/sandbox/breaker/`)
1. `provision/restore_baseline.sh <baseline> <dump>` — freeze-on-create → auth-stub preflight →
   `pg_restore --exit-on-error`. On any failure it drops the partial baseline (fail-closed).
2. **One-time role setup** (skip if `tcc_breaker_ro` / `tcc_breaker_codex_79audit` already exist).
   The clone scripts in steps 3–4 grant to these roles, so they MUST exist first:
   ```bash
   # generate random passwords into the gitignored 0600 infra/.env if absent (MAIN worktree's infra/.env)
   ( cd /home/olares/code/apex/apex-power-ops-platform; umask 077; \
     grep -q TCC_BREAKER_RO_PW infra/.env || { \
       printf 'TCC_BREAKER_RO_PW=%s\n'    "$(openssl rand -base64 24)" >> infra/.env; \
       printf 'TCC_BREAKER_CODEX_PW=%s\n' "$(openssl rand -base64 24)" >> infra/.env; } )
   # create the roles — passwords via ENV -> psql \getenv, NEVER argv
   set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
   docker exec -i -e TCC_BREAKER_RO_PW -e TCC_BREAKER_CODEX_PW apex-dev-pg \
     psql -v ON_ERROR_STOP=1 -U postgres -d postgres -f - < sql/20_roles.sql
   ```
3. `provision/make_viewer.sh <baseline> <viewer>` (clone-local DISABLE RLS + grant ro)
4. `provision/make_codex_clone.sh <baseline> <clone> <codex_role>` (TEMPLATE clone + ownership transfer)
5. Run `sql/checks/*.sql` (baseline / viewer / codex / role-zero-reach / sibling-no-table-priv /
   schema-create / residual-owner) — all fail-closed except residual-owner (visibility).
6. `provision/write_manifest.sh <baseline> <dump> <stamp> <src>` → `SNAPSHOT_MANIFEST.md`; then delete the dump.

## Codex harness
`codex-harness/preflight.sh` (dry-run env proof) → `codex-harness/launch.sh <codex_worktree>` with
`BREAKER_SANDBOX_DSN` exported (the clone DSN). Codex sees ONLY the clone; no prod, no Supabase, no
other DB. Direction/fence: `codex-harness/direction.md`.

## Promotion gate
Prod is NEVER touched here. Any Codex finding bound for prod goes through the existing governed
prod-write packet — by the operator, never automatically.
