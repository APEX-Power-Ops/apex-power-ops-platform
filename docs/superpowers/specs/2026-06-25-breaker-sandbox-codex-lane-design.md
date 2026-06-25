# Breaker Sandbox + Codex Background Lane — Design Spec

**Date:** 2026-06-25
**Lane:** `lvbreaker/breaker-sandbox` (apex-power-ops-platform)
**Status:** DESIGN — green-lit for `writing-plans` (3 cross-engine review rounds, 16 findings, all
folded in). Substrate build gated on the operator's dump action.
**Origin:** Operator asked for a path to let the breaker (lvbreakertcc) lane progress in the
background via Codex, working against breaker data in an Olares DB, with **zero risk to the online
(prod Supabase) data**. Three Codex cross-engine review rounds (5 + 6 + 5 findings, all accepted)
hardened the run mechanics so the safety is **structural**, not just intent — notably: no
cluster-wide `BYPASSRLS` (clone-local ownership / RLS-disable instead).

---

## Goal

Stand up an air-gapped breaker-data substrate on the Olares host so Codex can run a bounded,
low-risk audit/work lane against a copy of the breaker catalog — never reaching prod, by
construction and by run mechanics.

## Global Constraints (load-bearing)

- **Prod `tcc.*` is the persisted PROJECTION; Access `TCC_NEW.accdb` is the BEHAVIORAL source of
  truth.** → The sandbox suffices for projection / contract / UI / serving-layer work. It is **NOT**
  sufficient for calc-engine *behavioral* rulings (those need Access fixtures read-only — out of
  scope for this lane).
- **No prod credentials on Olares.** Host holds only `DEV_PG_PASSWORD`. Seed via an **operator-side
  dump streamed into the host restore**; the prod credential never lands in host env, files, shell
  history, or Codex context.
- **Frozen baseline + disposable clones** — never one writable sandbox.
- **Baseline stays connection-free** after validation (so it is always a clean `TEMPLATE` source —
  Postgres refuses `CREATE DATABASE … TEMPLATE x` while any session is connected to `x`). All human
  / MCP inspection goes to a separate **viewer** clone.
- **Codex runs in a sanitized environment** (`env -i`, a dedicated worktree with no `infra/.env`,
  only the clone DSN passed in) — proven, not assumed.
- **Role scoping is PROVEN** with a full privilege matrix (CONNECT + CREATE-on-DB + schema
  USAGE/CREATE + table privileges across sibling DBs), not just CONNECT.
- **A snapshot manifest is mandatory** (restore preflight, role/policy assumptions, privilege
  matrix, checksum, row counts, dump-deletion proof).
- **Codex prompt fence:** no prod, no Supabase, no network DB except the clone DSN; produce findings
  + candidate patches only.
- **Promotion gate:** any prod change happens ONLY by the operator via the existing governed
  prod-write packet. Codex never writes prod.

## Provenance (read-only prod probe, 2026-06-25, project `fxoyniqnrlkxfligbxmg`, PG 17.6)

- Schema `tcc`: **91 tables, 2 views, 30 sequences, 190 indexes**; ~813 MB.
- Bulk: relay catalog (`relay_curve_points_tcp` 1.57M rows + `relay_ranges` + `relay_discrete_values`)
  ≈ 566 MB — inert for breaker work but included. Breaker projection (`etu_*`/`tmt_*`/`emt_*`) ≈ 250 MB.
- **RLS:** 60 of 91 tables RLS-enabled; **120 policies, all granted `to public`** (no `anon` /
  `authenticated` / `service_role` references). 60 policies call `auth.*` functions; 0 call `vault.*`.
- **Defaults:** core-only — `now()` (89), `nextval()` (28), `gen_random_uuid()` (21, core in PG13+).
  No `uuid_generate_*`; **no contrib extension required** on host.
- **Drift note:** repo docs describe `tcc.*` as ~60 tables; prod has 91. Logged; reconcile docs
  separately (not a blocker).

---

## Architecture

### Databases (host `apex-dev-pg`, PG17)

1. **`tcc_breaker_baseline_20260625`** — one-way restore of the full prod `tcc` schema. **Frozen;
   no routine connections after validation.** Owned by the provisioning superuser. Sole purpose
   after validation: serve as a clean `TEMPLATE` for clones. Immutable provenance.
2. **`tcc_breaker_viewer_20260625`** — read-only clone (`CREATE DATABASE … TEMPLATE baseline`) for
   **MCP + operator/CC inspection**. This is where humans/MCP look — never the baseline.
3. **`tcc_breaker_codex_79audit_20260625`** — writable **disposable** clone for Codex. Dropped /
   recreated freely from baseline.

Clones are created only while the baseline has **zero sessions** (guaranteed by keeping baseline
non-interactive).

### Roles (NO cluster-wide attributes — clone-local handling only)

- **`tcc_breaker_ro`** — `CONNECT` + `SELECT` on the **viewer** clone only. Used by the MCP entry
  and operator/CC. No baseline access.
- **`tcc_breaker_codex_79audit`** — login role that **owns the codex clone's objects** (see RLS
  handling), giving full write freedom inside that clone. **No baseline, no viewer.** The only
  credential in Codex's environment.
- Baseline: reachable only by the provisioning superuser, and only when spawning clones.
- `REVOKE CONNECT FROM PUBLIC` on baseline + all clones. **No `BYPASSRLS` on any role.**

**RLS handling (clone-local, no cluster-wide attribute):** the sandbox is single-tenant and
isolated; prod RLS posture is a separate concern (see the prod-RLS-exposure lane).
- **Baseline** keeps RLS + policies verbatim (exact restore / provenance). So the 60
  auth-referencing policies restore under `--exit-on-error`, create 3 deterministic stub functions
  in the baseline before restore (exact signatures):
  ```sql
  create schema if not exists auth;
  create or replace function auth.uid()  returns uuid  language sql stable as $$ select null::uuid $$;
  create or replace function auth.role() returns text  language sql stable as $$ select null::text $$;
  create or replace function auth.jwt()  returns jsonb language sql stable as $$ select '{}'::jsonb $$;
  ```
- **Viewer clone** — `ALTER TABLE tcc.<t> DISABLE ROW LEVEL SECURITY` on the 60 RLS tables
  (clone-local) so `tcc_breaker_ro` (SELECT-only) reads every row. Read-only stays enforced by
  GRANTs, not RLS.
- **Codex clone** — `REASSIGN OWNED BY <provisioning superuser> TO tcc_breaker_codex_79audit`
  (clone-local) so Codex owns every object and writes freely; owners are exempt from RLS on their
  own tables — **no cluster-wide bypass needed.**

### Proven role scoping (run + record in manifest)

```sql
-- CONNECT + CREATE across all dev DBs
select datname,
       has_database_privilege('tcc_breaker_codex_79audit', datname, 'CONNECT') as can_connect,
       has_database_privilege('tcc_breaker_codex_79audit', datname, 'CREATE')  as can_create
from pg_database where datistemplate=false order by datname;
-- schema-level on the codex clone vs a sibling (run while connected to each)
select has_schema_privilege('tcc_breaker_codex_79audit','public','USAGE') as pub_usage,
       has_schema_privilege('tcc_breaker_codex_79audit','public','CREATE') as pub_create,
       has_schema_privilege('tcc_breaker_codex_79audit','tcc','USAGE')     as tcc_usage;
-- sibling-DB TABLE privileges — run while connected to EACH sibling (ops_dev, records_dev, …);
-- expect leaked_table_privs = 0 everywhere
select count(*) as leaked_table_privs
from information_schema.tables t
where t.table_schema not in ('pg_catalog','information_schema')
  and has_table_privilege('tcc_breaker_codex_79audit',
        format('%I.%I', t.table_schema, t.table_name), 'SELECT, INSERT, UPDATE, DELETE');
```

**Acceptance:** accept the PUBLIC-CONNECT residual **only if**, on every sibling DB, `can_create =
false`, schema `CREATE = false`, and `leaked_table_privs = 0`. The operative guards: object-level
privileges + clone-only DSN + sanitized Codex env.

### Seed procedure

- **CC preflight (host-side, BEFORE the operator scp):** create the controlled landing dir —
  `ssh olares-mesh 'umask 077; install -d -m 700 /home/olares/dev-pg-backups/tcc'`.
- **Operator (their machine, cred from Vault):**
  ```bash
  pg_dump --no-owner --no-privileges --schema=tcc -Fc "$PROD_RO_DSN" -f tcc_baseline_20260625.dump
  scp tcc_baseline_20260625.dump olares-mesh:/home/olares/dev-pg-backups/tcc/
  ```
  Dump is **proprietary catalog data** — lands in `/home/olares/dev-pg-backups/tcc/` (mode 700);
  CC `chmod 600` immediately on receipt. Never world-readable `/tmp`.
- **CC (host) restore preflight + restore:**
  1. Ensure host has the (none-required) extensions; create stub `auth` schema + `auth.uid/role/jwt`
     in the new baseline DB.
  2. `createdb tcc_breaker_baseline_20260625`; `pg_restore --no-owner --no-privileges
     --exit-on-error -d tcc_breaker_baseline_20260625 .../tcc_baseline_20260625.dump`.
  3. Validate (row counts vs manifest); freeze (revoke connect from public; no routine logins).
  4. Spawn `tcc_breaker_viewer_*` + `tcc_breaker_codex_79audit_*` via `TEMPLATE baseline`.
  5. `sha256sum` the dump → manifest; **delete the dump**; record deletion proof.

### `SNAPSHOT_MANIFEST.md` contents

Source project ref + schema + UTC timestamp; dump command shape; object counts by relkind
(91/2/30/190); RLS/policy facts (60 tables / 120 policies / `to public` / 60 auth-ref / 0 vault);
restore preflight (auth-fn stubs created, **no login-role stubs needed**, **no contrib extension
required**, `--exit-on-error` clean); key-table row counts (`etu_*`/`tmt_*`); full privilege matrix
result; sha256 of the dump; dump-file **deletion proof**; the 60→91 doc-drift note.

---

## Codex lane (sanitized run mechanics)

- **Dedicated worktree** `apex-breaker-codex` (a fresh worktree → naturally contains **no**
  `infra/.env`; we never symlink one in). Codex's `-C` points here.
- **Harness preflight (dry-run proof, BEFORE the real run):**
  1. `install -d -m 700 /home/olares/.breaker-codex-home` (the sanitized HOME must exist).
  2. Verify the binary resolves under the sanitized PATH: `env -i PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin codex --version`.
  3. No-op exec under full sanitization: `env -i PATH=… HOME=/home/olares/.breaker-codex-home codex exec -s read-only 'reply OK'` returns cleanly.
  4. Env proof (use portable `grep -E`, since `rg` may not be on the sanitized PATH):
     `env -i PATH=… HOME=… BREAKER_SANDBOX_DSN=… bash -c 'printenv | grep -E "PG|DSN|DATABASE|SUPABASE"'`
     must show **only** `BREAKER_SANDBOX_DSN` — no `DEV_PG_PASSWORD`, no prod/supabase vars.
- **Sanitized launch (after preflight passes):**
  ```bash
  env -i \
    PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin \
    HOME=/home/olares/.breaker-codex-home \
    BREAKER_SANDBOX_DSN="postgresql://tcc_breaker_codex_79audit:***@127.0.0.1:5432/tcc_breaker_codex_79audit_20260625?sslmode=disable" \
    codex exec -s workspace-write -C /home/olares/code/apex/apex-breaker-codex - < direction.md
  ```
- **First direction — #79 lvbreakertcc contract audit (projection scope):** verify the lvbreakertcc
  serving contract row-by-row against the TCC Master Reference + the live clone columns; characterize
  the parked **TMT F-010/011** safety hazard; emit a findings report + candidate patch SQL applied to
  the clone.
- **Prompt fence (verbatim intent):** no prod, no Supabase, no network DB except `BREAKER_SANDBOX_DSN`;
  projection/contract scope only — defer behavioral calc-engine rulings and flag where Access
  fixtures would be required; produce findings + candidate patches only.
- **Outputs:** `findings-79.md` + `candidate-patches/*.sql` (against the clone, never prod).

## Review + promotion

CC + operator review the findings; any prod-bound change goes through the existing governed
prod-write packet. Codex output is advisory + clone-local.

## Division of labor

- **CC:** baseline + viewer + codex clone DBs, roles, restore preflight, manifest, setup scripts,
  the sanitized Codex harness + bounded prompt; restore the dump; run the privilege matrix; review.
- **Operator:** the single prod-touching step (the read-only dump to `~/dev-pg-backups/tcc/`) +
  spec sign-off + prod promotion.
- **Codex:** execute the bounded #79 audit inside its clone.

## Open items

- Schema-doc drift (60→91) — reconcile repo docs separately.
- Behavioral-authority boundary (Access `TCC_NEW.accdb`) — calc rulings out of scope for this lane.
- Orchestration cadence — first run as a one-shot `codex exec`; graduate to an apex-jobs durable
  background job if it recurs.
- RLS is intentionally inert in the sandbox via **auth-fn stubs + clone-local ownership/RLS-disable
  — NO cluster-wide BYPASSRLS** (viewer = clone-local `DISABLE ROW LEVEL SECURITY`; codex clone =
  ownership transfer, owner-RLS-exempt). Prod RLS posture is owned by the separate
  prod-RLS-exposure lane.
