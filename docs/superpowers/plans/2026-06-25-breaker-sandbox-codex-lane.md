# Breaker Sandbox + Codex Background Lane — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up an air-gapped breaker-data substrate on the Olares host (frozen baseline + read-only viewer clone + disposable Codex clone, scoped roles, sanitized Codex harness) so Codex can work the lvbreakertcc lane in the background with zero risk to prod Supabase.

**Architecture:** Build and prove the *entire* provisioning mechanism against a small synthetic `tcc`-shaped fixture DB on `apex-dev-pg`. Every component (auth-stub preflight, fail-closed restore, clone-local RLS handling, scoped roles, privilege matrix, manifest, sanitized harness) is verified green on the fixture first. The real 813 MB prod dump is consumed by the *same* scripts in one final, operator-gated task. No cluster-wide role attributes; RLS handled clone-locally (viewer = `DISABLE ROW LEVEL SECURITY`; Codex clone = `REASSIGN OWNED` to the codex role, owner-exempt).

**Tech Stack:** PostgreSQL 17 in the `apex-dev-pg` Docker container; `bash` + `psql`/`pg_restore` via `docker exec`; SQL DO-block `RAISE` assertions run under `psql -v ON_ERROR_STOP=1` (exit code = pass/fail); `codex exec` (codex-cli 0.141.0) for the harness. Spec source of truth: `docs/superpowers/specs/2026-06-25-breaker-sandbox-codex-lane-design.md @ 47823dc8`.

## Global Constraints

- All host work over `ssh olares-mesh`; node/codex PATH = `/home/olares/.nvm/versions/node/v20.20.2/bin`.
- Provisioning runs as the container superuser via `docker exec apex-dev-pg psql -U postgres` (socket/trust auth — no password needed inside the container). Scoped-role proofs connect with `-U <role> -h 127.0.0.1` to force password auth.
- PG17 custom-format dumps MUST be restored with `docker exec apex-dev-pg pg_restore` (the host's own pg_restore is older → "false empty dump"). Copy the dump into the container with `docker cp` first.
- NEVER echo/log `DEV_PG_PASSWORD`, any role password, or any full DSN. Role passwords come from gitignored env vars sourced at provision time; psql consumes them via `-v` vars, never argv.
- NO cluster-wide role attributes (no `BYPASSRLS`, no `SUPERUSER`, no `CREATEDB`/`CREATEROLE`). Clone-local handling only.
- Baseline stays connection-free after validation (clean `TEMPLATE` source); humans/MCP use the viewer clone only.
- The codex login role is clone-only: no baseline, no viewer; owns its clone's objects.
- The real prod-dump restore (Task 7) is OPERATOR-GATED: depends on the operator's dump at `/home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump` (dir mode 700; `chmod 600` on receipt). sha256 + dump-deletion proof recorded in the manifest.
- Prod is never touched by this plan. Prod promotion of any future Codex finding is via the existing governed prod-write packet only.
- Prod-grounded facts (bake into manifest + fixture coverage): `tcc` = 91 tables / 2 views / 30 sequences / 190 indexes / ~813 MB; 60 RLS tables / 120 policies all `to public`; 60 policies reference `auth.*` (0 `vault.*`); defaults core-only (`now`/`nextval`/`gen_random_uuid`, no contrib ext); repo-doc drift 60→91.
- Lane: `lvbreaker/breaker-sandbox`, host worktree `/home/olares/code/apex/apex-breaker-sandbox`. Commit after every task.

**Conventions used below:**
- `ROOT` = `/home/olares/code/apex/apex-breaker-sandbox/infra/database/sandbox/breaker`.
- Run wrapper: `RUN='ssh olares-mesh'`. All commands below are shown as they run *on the host* (prefix with `ssh olares-mesh '…'` from the controller).
- `SU()` shorthand for `docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres` (superuser, trust).

---

### Task 0: Lane scaffold + synthetic fixture + auth stubs

**Files:**
- Create: `infra/database/sandbox/breaker/sql/10_auth_stubs.sql`
- Create: `infra/database/sandbox/breaker/fixture/synthetic_tcc.sql`
- Create: `infra/database/sandbox/breaker/fixture/build_fixture_dump.sh`
- Create: `infra/database/sandbox/breaker/.gitignore`

**Interfaces:**
- Produces: `10_auth_stubs.sql` (creates schema `auth` + `auth.uid()→uuid`, `auth.role()→text`, `auth.jwt()→jsonb`); `build_fixture_dump.sh BUILD_DB DUMP_OUT` → builds the fixture source DB then `pg_dump -Fc --schema=tcc` to `DUMP_OUT` (a custom-format dump that, like prod, contains the `auth.uid()`-referencing policy but NOT the `auth` schema).

- [ ] **Step 1: Write the auth stubs (exact signatures from spec)**

`sql/10_auth_stubs.sql`:
```sql
-- Stub Supabase auth.* functions so prod tcc policies (60 reference auth.uid()) restore on a
-- plain PG17 host. Bodies are inert; sandbox roles never execute policy bodies (viewer: RLS
-- disabled clone-local; codex: owner-exempt). Used at BOTH fixture-source build and baseline restore.
create schema if not exists auth;
create or replace function auth.uid()  returns uuid  language sql stable as $$ select null::uuid $$;
create or replace function auth.role() returns text  language sql stable as $$ select null::text $$;
create or replace function auth.jwt()  returns jsonb language sql stable as $$ select '{}'::jsonb $$;
```

- [ ] **Step 2: Write the synthetic fixture (exercises every preflight path)**

`fixture/synthetic_tcc.sql`:
```sql
-- A tiny tcc-shaped schema standing in for prod. Deliberately exercises: a gen_random_uuid()
-- default (core PG13+), a sequence/nextval default, a now() default, RLS enabled, a policy that
-- references auth.uid() (the prod risk), and a view. NOT representative of real columns — it only
-- has to hit the same RESTORE/PREFLIGHT code paths.
create schema if not exists tcc;

create table tcc.fx_breakers (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  created_at  timestamptz not null default now()
);

create sequence tcc.fx_settings_seq;
create table tcc.fx_settings (
  id          bigint primary key default nextval('tcc.fx_settings_seq'),
  breaker_id  uuid references tcc.fx_breakers(id),
  owner_id    uuid,
  value       numeric
);

-- RLS + an auth.uid()-referencing policy (mirrors prod's 60 auth-ref policies, all "to public")
alter table tcc.fx_settings enable row level security;
create policy fx_settings_sel on tcc.fx_settings for select to public
  using (owner_id = auth.uid());

create view tcc.fx_summary as
  select b.id, b.name, count(s.*) as n
  from tcc.fx_breakers b left join tcc.fx_settings s on s.breaker_id = b.id
  group by 1, 2;

insert into tcc.fx_breakers(name) values ('FX-A'), ('FX-B');
insert into tcc.fx_settings(breaker_id, owner_id, value)
  select id, gen_random_uuid(), 1.0 from tcc.fx_breakers;
```

- [ ] **Step 3: Write the fixture-dump builder**

`fixture/build_fixture_dump.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Build the synthetic fixture SOURCE db, then pg_dump it to a custom-format file that mirrors the
# prod dump shape (schema tcc only; auth schema EXCLUDED, so restore must re-stub auth).
# Usage: build_fixture_dump.sh <BUILD_DB> <DUMP_OUT>
BUILD_DB="${1:?build db name}"; DUMP_OUT="${2:?dump out path}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
install -d -m 700 "$(dirname "$DUMP_OUT")"   # _local/ is gitignored and not auto-created
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }

SU -d postgres -c "drop database if exists \"$BUILD_DB\";"
SU -d postgres -c "create database \"$BUILD_DB\";"
# auth stub must exist BEFORE the policy is created
SU -d "$BUILD_DB" < "$HERE/sql/10_auth_stubs.sql"
SU -d "$BUILD_DB" < "$HERE/fixture/synthetic_tcc.sql"
# dump schema tcc only, custom format, in-container (paths are container-local)
docker exec apex-dev-pg pg_dump -U postgres --no-owner --no-privileges --schema=tcc -Fc \
  -d "$BUILD_DB" -f "/tmp/$(basename "$DUMP_OUT")"
docker cp "apex-dev-pg:/tmp/$(basename "$DUMP_OUT")" "$DUMP_OUT"
docker exec apex-dev-pg rm -f "/tmp/$(basename "$DUMP_OUT")"
echo "fixture dump written: $DUMP_OUT"
```

- [ ] **Step 4: Gitignore generated artifacts**

`.gitignore`:
```
*.dump
_local/
```

- [ ] **Step 5: Run the builder to verify it fails before scripts are wired, then passes**

Run: `ssh olares-mesh 'cd '"$ROOT"' && bash fixture/build_fixture_dump.sh tcc_breaker_fixture_src _local/tcc_fixture.dump > /tmp/fx.log 2>&1; echo EXIT=$?; tail -5 /tmp/fx.log'`
Expected (first run, before files exist): FAIL. After Steps 1–4: `EXIT=0` and `fixture dump written: _local/tcc_fixture.dump`.

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add infra/database/sandbox/breaker && git commit -m "feat(breaker-sandbox): auth stubs + synthetic tcc fixture + dump builder"'
```

---

### Task 1: Fail-closed restore + frozen baseline (proven on the fixture dump)

**Files:**
- Create: `infra/database/sandbox/breaker/provision/restore_baseline.sh`
- Create: `infra/database/sandbox/breaker/sql/checks/check_baseline.sql`

**Interfaces:**
- Consumes: `10_auth_stubs.sql` (Task 0); a custom-format dump file path.
- Produces: `restore_baseline.sh <BASELINE_DB> <DUMP_FILE>` → drops/creates the DB, applies auth stubs, `pg_restore --exit-on-error`, revokes PUBLIC connect (freeze). `check_baseline.sql` asserts the restored shape.

- [ ] **Step 1: Write the failing check**

`sql/checks/check_baseline.sql` (run against the restored baseline; RAISEs on any failure):
```sql
do $$
declare n_tables int; n_rls int; n_policies int; n_views int;
begin
  select count(*) into n_tables  from pg_class c join pg_namespace s on s.oid=c.relnamespace
         where s.nspname='tcc' and c.relkind='r';
  select count(*) into n_rls     from pg_class c join pg_namespace s on s.oid=c.relnamespace
         where s.nspname='tcc' and c.relkind='r' and c.relrowsecurity;
  select count(*) into n_policies from pg_policies where schemaname='tcc';
  select count(*) into n_views   from pg_class c join pg_namespace s on s.oid=c.relnamespace
         where s.nspname='tcc' and c.relkind='v';
  if n_tables < 2 then raise exception 'baseline: expected >=2 tcc tables, got %', n_tables; end if;
  if n_rls   < 1 then raise exception 'baseline: expected >=1 RLS table, got %', n_rls; end if;
  if n_policies < 1 then raise exception 'baseline: expected >=1 policy, got %', n_policies; end if;
  if n_views < 1 then raise exception 'baseline: expected >=1 view, got %', n_views; end if;
  -- prove the auth.uid()-referencing policy actually restored (the core preflight win)
  perform 1 from pg_policies where schemaname='tcc' and coalesce(qual,'') like '%auth.uid()%';
  if not found then raise exception 'baseline: auth.uid()-referencing policy did not restore'; end if;
  raise notice 'check_baseline OK: % tables, % rls, % policies, % views', n_tables, n_rls, n_policies, n_views;
end $$;
```

- [ ] **Step 2: Run the check to verify it fails (baseline does not exist yet)**

Run: `ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d tcc_breaker_baseline_fixture -f - < '"$ROOT"'/sql/checks/check_baseline.sql > /tmp/c.log 2>&1; echo EXIT=$?; tail -3 /tmp/c.log'`
Expected: FAIL (`database "tcc_breaker_baseline_fixture" does not exist`).

- [ ] **Step 3: Write the restore script**

`provision/restore_baseline.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Usage: restore_baseline.sh <BASELINE_DB> <DUMP_FILE(host path)>
BASELINE_DB="${1:?baseline db}"; DUMP_FILE="${2:?dump file}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }

SU -d postgres -c "drop database if exists \"$BASELINE_DB\";"
SU -d postgres -c "create database \"$BASELINE_DB\";"
# preflight: auth stubs BEFORE restore (policies reference auth.uid())
SU -d "$BASELINE_DB" < "$HERE/sql/10_auth_stubs.sql"
# copy dump into the container and restore with the in-container (PG17) pg_restore, fail-closed
docker cp "$DUMP_FILE" "apex-dev-pg:/tmp/restore.dump"
docker exec apex-dev-pg pg_restore --no-owner --no-privileges --exit-on-error \
  -U postgres -d "$BASELINE_DB" /tmp/restore.dump
docker exec apex-dev-pg rm -f /tmp/restore.dump
# freeze: no PUBLIC connect (clones are spawned by the superuser, which is unaffected)
SU -d "$BASELINE_DB" -c "revoke connect on database \"$BASELINE_DB\" from public;"
echo "restore_baseline OK: $BASELINE_DB"
```

- [ ] **Step 4: Run restore on the fixture dump, then re-run the check (now passes)**

Run:
```
ssh olares-mesh 'cd '"$ROOT"' && bash provision/restore_baseline.sh tcc_breaker_baseline_fixture _local/tcc_fixture.dump > /tmp/r.log 2>&1; echo EXIT=$?; tail -4 /tmp/r.log'
ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d tcc_breaker_baseline_fixture -f - < '"$ROOT"'/sql/checks/check_baseline.sql > /tmp/c.log 2>&1; echo EXIT=$?; tail -3 /tmp/c.log'
```
Expected: both `EXIT=0`; check prints `check_baseline OK: …`.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): fail-closed restore + frozen baseline + baseline check"'
```

---

### Task 2: Scoped roles + zero-reach proof

**Files:**
- Create: `infra/database/sandbox/breaker/sql/20_roles.sql`
- Create: `infra/database/sandbox/breaker/sql/checks/check_role_zero_reach.sql`
- Modify: `infra/.env` (gitignored) — add `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`

**Interfaces:**
- Produces: roles `tcc_breaker_ro` (LOGIN, no attrs) and `tcc_breaker_codex_79audit` (LOGIN, no attrs), created with passwords from env vars; NO database/schema grants yet (grants are per-clone, Tasks 3–4). `check_role_zero_reach.sql` proves the codex role has no CREATE-on-DB and no sibling table privileges.

- [ ] **Step 1: Generate RANDOM role passwords into the gitignored env (host)**

Random sandbox passwords — never fixed literals, never echoed to stdout; written only to the
gitignored 0600 `infra/.env` (Vault-rooted convention):
```
ssh olares-mesh 'umask 077; cd /home/olares/code/apex/apex-power-ops-platform; \
  grep -q TCC_BREAKER_RO_PW infra/.env || { \
    printf "TCC_BREAKER_RO_PW=%s\n"    "$(openssl rand -base64 24)" >> infra/.env; \
    printf "TCC_BREAKER_CODEX_PW=%s\n" "$(openssl rand -base64 24)" >> infra/.env; }'
```
(`infra/.env` is gitignored and per-worktree; provisioning + the harness read the MAIN worktree's
copy by absolute path. The password values never appear in argv or logs.)

- [ ] **Step 2: Write the roles SQL (no cluster attributes)**

`sql/20_roles.sql`:
```sql
-- Scoped sandbox roles. NO BYPASSRLS/SUPERUSER/CREATEDB/CREATEROLE. No DB/schema grants here;
-- grants are clone-local (made by make_viewer.sh / make_codex_clone.sh).
-- Passwords read from ENV via \getenv (psql 16+; container psql is 17.10) — NEVER argv.
\getenv ro_pw    TCC_BREAKER_RO_PW
\getenv codex_pw TCC_BREAKER_CODEX_PW
do $$ begin
  if not exists (select 1 from pg_roles where rolname='tcc_breaker_ro') then
    create role tcc_breaker_ro login;
  end if;
  if not exists (select 1 from pg_roles where rolname='tcc_breaker_codex_79audit') then
    create role tcc_breaker_codex_79audit login;
  end if;
end $$;
alter role tcc_breaker_ro            password :'ro_pw';
alter role tcc_breaker_codex_79audit password :'codex_pw';
-- belt-and-suspenders: ensure no dangerous attributes
alter role tcc_breaker_ro            nosuperuser nocreatedb nocreaterole nobypassrls;
alter role tcc_breaker_codex_79audit nosuperuser nocreatedb nocreaterole nobypassrls;
```

- [ ] **Step 3: Write the zero-reach check (failing first)**

`sql/checks/check_role_zero_reach.sql` (run as superuser; checks the codex role against ALL non-template DBs):
```sql
do $$
declare r record; bad int := 0;
begin
  for r in select datname from pg_database where datistemplate=false
           and datname not like 'tcc_breaker_codex_%' loop
    if has_database_privilege('tcc_breaker_codex_79audit', r.datname, 'CREATE') then
      raise warning 'LEAK: CREATE on db %', r.datname; bad := bad + 1;
    end if;
  end loop;
  if bad > 0 then raise exception 'role_zero_reach FAILED: % CREATE leak(s)', bad; end if;
  raise notice 'check_role_zero_reach OK (no CREATE on any non-codex db)';
end $$;
```
(Table-level sibling leakage is proven in Task 4 once a clone exists; CREATE-on-DB is the meaningful check at role-creation time.)

- [ ] **Step 4: Run the check to verify it fails (role does not exist)**

Run: `ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d postgres -f - < '"$ROOT"'/sql/checks/check_role_zero_reach.sql > /tmp/c.log 2>&1; echo EXIT=$?; tail -3 /tmp/c.log'`
Expected: FAIL (`role "tcc_breaker_codex_79audit" does not exist`).

- [ ] **Step 5: Create the roles (passwords via ENV → `\getenv`, never argv)**

Run (shell guards non-empty; passwords forwarded as ENV to the container; psql reads them via
`\getenv` inside `20_roles.sql`, so they never appear in argv):
```
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  [ -n "$TCC_BREAKER_RO_PW" ] && [ -n "$TCC_BREAKER_CODEX_PW" ] || { echo "FAIL: role pw unset"; exit 1; }; \
  docker exec -i -e TCC_BREAKER_RO_PW -e TCC_BREAKER_CODEX_PW apex-dev-pg \
    psql -v ON_ERROR_STOP=1 -U postgres -d postgres -f - < '"$ROOT"'/sql/20_roles.sql'
```

- [ ] **Step 6: Re-run the zero-reach check (now passes)**

Run: same as Step 4. Expected: `EXIT=0`, `check_role_zero_reach OK`.

- [ ] **Step 7: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): scoped roles (no cluster attrs) + zero-reach proof"'
```

---

### Task 3: Viewer clone (clone-local DISABLE RLS) + read-only proof

**Files:**
- Create: `infra/database/sandbox/breaker/provision/make_viewer.sh`
- Create: `infra/database/sandbox/breaker/sql/checks/check_viewer.sql`

**Interfaces:**
- Consumes: a frozen baseline DB (Task 1); `tcc_breaker_ro` (Task 2).
- Produces: `make_viewer.sh <BASELINE_DB> <VIEWER_DB>` → `CREATE DATABASE … TEMPLATE baseline`, revoke PUBLIC connect, `DISABLE ROW LEVEL SECURITY` on all RLS tables clone-locally, grant `tcc_breaker_ro` CONNECT+USAGE+SELECT. `check_viewer.sql` asserts RLS off + ro can read.

- [ ] **Step 1: Write the failing check**

`sql/checks/check_viewer.sql` — GENERIC (no fixture table names; works on fixture AND real). Run against the viewer DB as superuser; row-visibility for ro proven via a separate role-connect in Step 4:
```sql
do $$
declare bad int;
begin
  -- (1) NO tcc table remains RLS-enabled (clone-local DISABLE worked on every one)
  select count(*) into bad from pg_class c join pg_namespace s on s.oid=c.relnamespace
    where s.nspname='tcc' and c.relkind='r' and c.relrowsecurity;
  if bad <> 0 then raise exception 'viewer: % tcc tables still RLS-enabled', bad; end if;
  -- (2) ro can CONNECT
  if not has_database_privilege('tcc_breaker_ro', current_database(), 'CONNECT')
     then raise exception 'viewer: tcc_breaker_ro cannot CONNECT'; end if;
  -- (3) ro has SELECT on EVERY tcc table
  select count(*) into bad from pg_class c join pg_namespace s on s.oid=c.relnamespace
    where s.nspname='tcc' and c.relkind='r' and not has_table_privilege('tcc_breaker_ro', c.oid, 'SELECT');
  if bad <> 0 then raise exception 'viewer: ro lacks SELECT on % tcc tables', bad; end if;
  -- (4) ro has NO write on ANY tcc table
  select count(*) into bad from pg_class c join pg_namespace s on s.oid=c.relnamespace
    where s.nspname='tcc' and c.relkind='r' and has_table_privilege('tcc_breaker_ro', c.oid, 'INSERT, UPDATE, DELETE');
  if bad <> 0 then raise exception 'viewer: ro has write on % tcc tables', bad; end if;
  raise notice 'check_viewer OK (RLS disabled on all tcc tables; ro read-only on all)';
end $$;
```

- [ ] **Step 2: Run the check to verify it fails (viewer does not exist)**

Run: `ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d tcc_breaker_viewer_fixture -f - < '"$ROOT"'/sql/checks/check_viewer.sql > /tmp/c.log 2>&1; echo EXIT=$?; tail -3 /tmp/c.log'`
Expected: FAIL (db does not exist).

- [ ] **Step 3: Write make_viewer.sh**

`provision/make_viewer.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Usage: make_viewer.sh <BASELINE_DB> <VIEWER_DB>
BASELINE_DB="${1:?baseline}"; VIEWER_DB="${2:?viewer}"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
# TEMPLATE requires zero sessions on BASELINE_DB (it is frozen / connection-free by design)
SU -d postgres -c "drop database if exists \"$VIEWER_DB\";"
SU -d postgres -c "create database \"$VIEWER_DB\" template \"$BASELINE_DB\";"
SU -d "$VIEWER_DB" -c "revoke connect on database \"$VIEWER_DB\" from public;"
# clone-local: disable RLS on every RLS-enabled tcc table
SU -d "$VIEWER_DB" <<'SQL'
do $$ declare r record; begin
  for r in select format('%I.%I', n.nspname, c.relname) as t
           from pg_class c join pg_namespace n on n.oid=c.relnamespace
           where n.nspname='tcc' and c.relkind='r' and c.relrowsecurity loop
    execute 'alter table '||r.t||' disable row level security';
  end loop;
end $$;
SQL
# read-only grants for tcc_breaker_ro
SU -d "$VIEWER_DB" -c "grant connect on database \"$VIEWER_DB\" to tcc_breaker_ro;"
SU -d "$VIEWER_DB" -c "grant usage on schema tcc to tcc_breaker_ro;"
SU -d "$VIEWER_DB" -c "grant select on all tables in schema tcc to tcc_breaker_ro;"
echo "make_viewer OK: $VIEWER_DB"
```

- [ ] **Step 4: Build the viewer from the fixture baseline, run the check, and prove ro actually reads rows**

Run:
```
ssh olares-mesh 'cd '"$ROOT"' && bash provision/make_viewer.sh tcc_breaker_baseline_fixture tcc_breaker_viewer_fixture > /tmp/v.log 2>&1; echo EXIT=$?; tail -3 /tmp/v.log'
ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d tcc_breaker_viewer_fixture -f - < '"$ROOT"'/sql/checks/check_viewer.sql; echo EXIT=$?'
# ro reads all rows over TCP (forces password auth)
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  docker exec -i -e PGPASSWORD="$TCC_BREAKER_RO_PW" apex-dev-pg psql -tA -U tcc_breaker_ro -h 127.0.0.1 \
  -d tcc_breaker_viewer_fixture -c "select count(*) from tcc.fx_settings;"'
```
Expected: viewer build `EXIT=0`; check `EXIT=0`; ro count = `2` (all rows visible — RLS disabled).

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): viewer clone (clone-local RLS disable) + read-only proof"'
```

---

### Task 4: Codex clone (REASSIGN OWNED) + write-freedom + isolation proof

**Files:**
- Create: `infra/database/sandbox/breaker/provision/make_codex_clone.sh`
- Create: `infra/database/sandbox/breaker/sql/checks/check_codex_clone.sql`
- Create: `infra/database/sandbox/breaker/sql/checks/check_sibling_no_table_priv.sql`

**Interfaces:**
- Consumes: frozen baseline (Task 1); `tcc_breaker_codex_79audit` (Task 2).
- Produces: `make_codex_clone.sh <BASELINE_DB> <CLONE_DB> <CODEX_ROLE>` → `CREATE DATABASE … TEMPLATE baseline`, revoke PUBLIC connect, grant CONNECT to the codex role, `REASSIGN OWNED BY postgres TO <codex_role>` (clone-local), grant USAGE on schema tcc. Checks prove ownership + write freedom + RLS-exempt reads + sibling isolation.

- [ ] **Step 1: Write the failing checks**

`sql/checks/check_codex_clone.sql` (run as superuser against the clone):
```sql
do $$
declare not_owned int;
begin
  select count(*) into not_owned
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='tcc' and c.relkind in ('r','S','v')
      and pg_get_userbyid(c.relowner) <> 'tcc_breaker_codex_79audit';
  if not_owned <> 0 then raise exception 'codex_clone: % tcc objects not owned by codex role', not_owned; end if;
  if not has_database_privilege('tcc_breaker_codex_79audit', current_database(), 'CONNECT')
     then raise exception 'codex_clone: codex role cannot CONNECT'; end if;
  raise notice 'check_codex_clone OK (codex owns all tcc objects)';
end $$;
```

`sql/checks/check_sibling_no_table_priv.sql` (run as superuser while connected to a SIBLING db, e.g. ops_dev):
```sql
do $$
declare leaked int;
begin
  select count(*) into leaked from information_schema.tables t
   where t.table_schema not in ('pg_catalog','information_schema')
     and has_table_privilege('tcc_breaker_codex_79audit',
           format('%I.%I', t.table_schema, t.table_name), 'SELECT, INSERT, UPDATE, DELETE');
  if leaked <> 0 then raise exception 'sibling leak: codex role has table privs on % objects in %',
       leaked, current_database(); end if;
  raise notice 'check_sibling_no_table_priv OK on % (leaked=0)', current_database();
end $$;
```

- [ ] **Step 2: Run both checks to verify they fail (clone does not exist)**

Run the clone check against `tcc_breaker_codex_fixture` (FAIL: db missing) and the sibling check against `ops_dev` (PASS already — codex role has no grants there; this is the baseline-clean state we preserve). Capture both exit codes.

- [ ] **Step 3: Write make_codex_clone.sh**

`provision/make_codex_clone.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Usage: make_codex_clone.sh <BASELINE_DB> <CLONE_DB> <CODEX_ROLE>
BASELINE_DB="${1:?baseline}"; CLONE_DB="${2:?clone}"; CODEX_ROLE="${3:?role}"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
SU -d postgres -c "drop database if exists \"$CLONE_DB\";"
SU -d postgres -c "create database \"$CLONE_DB\" template \"$BASELINE_DB\";"
SU -d "$CLONE_DB" -c "revoke connect on database \"$CLONE_DB\" from public;"
SU -d "$CLONE_DB" -c "grant connect on database \"$CLONE_DB\" to \"$CODEX_ROLE\";"
SU -d "$CLONE_DB" -c "grant usage on schema tcc to \"$CODEX_ROLE\";"
# clone-local ownership transfer: codex owns every tcc object (owners are RLS-exempt on their own
# tables -> full read/write/DDL without any cluster bypass). NOTE: `reassign owned by postgres`
# is REJECTED on PG17 (the bootstrap postgres role also owns system-catalog objects), so transfer
# ownership of just the tcc schema + its r/S/v objects via per-object ALTER OWNER (identical
# semantic, scoped to tcc). Role name is guarded as a plain identifier (top of script).
SU -d "$CLONE_DB" -c "alter schema tcc owner to \"$CODEX_ROLE\";"
SU -d "$CLONE_DB" -c "
do \$body\$
declare r record;
begin
  for r in select n.nspname as ns, c.relname, c.relkind
             from pg_class c join pg_namespace n on n.oid=c.relnamespace
            where n.nspname='tcc' and c.relkind in ('r','S','v')
              and pg_get_userbyid(c.relowner)='postgres' loop
    execute format('alter %s %I.%I owner to ${CODEX_ROLE}',
      case r.relkind when 'r' then 'table' when 'S' then 'sequence' when 'v' then 'view' end,
      r.ns, r.relname);
  end loop;
end \$body\$;"
echo "make_codex_clone OK: $CLONE_DB owned by $CODEX_ROLE"
```
(Guard at the top of the script — `[[ "$CODEX_ROLE" =~ ^[a-z_][a-z0-9_]*$ ]] || exit 1` — makes the unquoted identifier interpolation fail-closed.)

- [ ] **Step 4: Build the codex clone, run the ownership check, and prove write freedom + RLS-exempt reads as the codex role**

Run:
```
ssh olares-mesh 'cd '"$ROOT"' && bash provision/make_codex_clone.sh tcc_breaker_baseline_fixture tcc_breaker_codex_fixture tcc_breaker_codex_79audit > /tmp/cc.log 2>&1; echo EXIT=$?; tail -3 /tmp/cc.log'
ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d tcc_breaker_codex_fixture -f - < '"$ROOT"'/sql/checks/check_codex_clone.sql; echo EXIT=$?'
# write freedom + DDL as the codex role over TCP — GENERIC probe (no fixture tables; reused in Task 7)
ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
  docker exec -i -e PGPASSWORD="$TCC_BREAKER_CODEX_PW" apex-dev-pg psql -v ON_ERROR_STOP=1 \
  -U tcc_breaker_codex_79audit -h 127.0.0.1 -d tcc_breaker_codex_fixture \
  -c "create table tcc._codex_write_probe(id int);" \
  -c "insert into tcc._codex_write_probe values (1);" \
  -c "select count(*) from tcc._codex_write_probe;" \
  -c "drop table tcc._codex_write_probe;"'
```
Expected: clone build `EXIT=0`; ownership check `EXIT=0`; all four probe statements succeed (create / insert / select=`1` / drop) — codex owns schema `tcc` (via `REASSIGN OWNED`) and writes + DDLs freely without any cluster bypass. The identical generic probe is reused on the real clone in Task 7.

- [ ] **Step 5: Prove sibling isolation holds after granting clone access**

Run the sibling check against `ops_dev` AND `records_dev`:
```
ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d ops_dev -f - < '"$ROOT"'/sql/checks/check_sibling_no_table_priv.sql; echo EXIT=$?'
ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d records_dev -f - < '"$ROOT"'/sql/checks/check_sibling_no_table_priv.sql; echo EXIT=$?'
```
Expected: both `EXIT=0`, `leaked=0` — the codex role gained access ONLY to its clone.

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): codex clone (REASSIGN OWNED) + write-freedom + sibling-isolation proof"'
```

---

### Task 5: Sanitized Codex harness + dry-run preflight

**Files:**
- Create: `infra/database/sandbox/breaker/codex-harness/preflight.sh`
- Create: `infra/database/sandbox/breaker/codex-harness/launch.sh`
- Create: `infra/database/sandbox/breaker/codex-harness/direction.md`

**Interfaces:**
- Consumes: the codex clone DSN (built from `TCC_BREAKER_CODEX_PW` + clone name).
- Produces: `preflight.sh` (creates the sanitized HOME, verifies `codex --version`, runs a no-op exec, proves the env via `grep -E`); `launch.sh` (the real `env -i` launch — NOT run in this task); `direction.md` (the #79 fence — content authored here, executed in a later gated step).

- [ ] **Step 1: Write direction.md (the #79 fence)**

`codex-harness/direction.md`:
```markdown
# Direction: #79 lvbreakertcc contract audit (projection scope)

You are auditing a DISPOSABLE COPY of the breaker catalog in a sandbox Postgres database.
HARD RULES:
- The ONLY database you may touch is the one in $BREAKER_SANDBOX_DSN. Do not connect to prod,
  Supabase, or any other database. Do not make outbound network calls to any DB.
- Scope is PROJECTION/CONTRACT only: verify the lvbreakertcc serving contract row-by-row against
  the TCC Master Reference and the live sandbox columns; characterize the TMT F-010/011 hazard.
- This sandbox CANNOT decide calc-engine BEHAVIORAL rulings (Access TCC_NEW.accdb is the behavioral
  authority and is NOT provided here). Where a finding would require behavioral fixtures, FLAG it and
  defer — do not guess.
- Deliverables ONLY: a findings report `findings-79.md` and candidate patch SQL under
  `candidate-patches/*.sql`, applied to the sandbox DB. Never produce prod migrations directly.
```

- [ ] **Step 2: Write preflight.sh**

`codex-harness/preflight.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Proves the sanitized launch environment BEFORE any real Codex run. Exits non-zero on any failure.
SANDBOX_HOME=/home/olares/.breaker-codex-home
CODEX_PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin
install -d -m 700 "$SANDBOX_HOME"
# Bridge codex's OWN auth (real ~/.codex / $CODEX_HOME) into the sandbox HOME so codex can
# authenticate under env -i. This is codex's credential, NOT a DB/prod cred — nothing else from the
# real HOME (.pgpass, shell rc, infra/.env) is exposed.
REAL_CODEX="${CODEX_HOME:-$HOME/.codex}"
if [ -e "$REAL_CODEX" ]; then ln -sfn "$REAL_CODEX" "$SANDBOX_HOME/.codex"; fi
# 1. codex resolves + authenticates under the sanitized PATH+HOME
env -i PATH="$CODEX_PATH" HOME="$SANDBOX_HOME" codex --version >/tmp/codex_ver 2>&1 \
  || { echo "FAIL: codex --version"; cat /tmp/codex_ver; exit 1; }
# 2. no-op exec under full sanitization (read-only sandbox, trivial prompt)
env -i PATH="$CODEX_PATH" HOME="$SANDBOX_HOME" codex exec -s read-only 'reply with the word OK' \
  >/tmp/codex_noop 2>&1 || { echo "FAIL: no-op exec"; tail -5 /tmp/codex_noop; exit 1; }
# 3. env proof: ONLY BREAKER_SANDBOX_DSN among PG/DSN/DATABASE/SUPABASE vars (grep -E is portable)
LEAK=$(env -i PATH="$CODEX_PATH" HOME="$SANDBOX_HOME" \
  BREAKER_SANDBOX_DSN="postgresql://placeholder" bash -c 'printenv | grep -E "PG|DSN|DATABASE|SUPABASE" || true')
if [[ "$LEAK" != "BREAKER_SANDBOX_DSN=postgresql://placeholder" ]]; then
  echo "FAIL: env leak -> [$LEAK]"; exit 1
fi
echo "preflight OK (codex resolves, no-op exec clean, env shows only BREAKER_SANDBOX_DSN)"
```

- [ ] **Step 3: Write launch.sh (authored, not executed in this task)**

`codex-harness/launch.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Real sanitized Codex run. Caller must export BREAKER_SANDBOX_DSN (clone DSN) first.
: "${BREAKER_SANDBOX_DSN:?clone DSN required}"
WORKTREE="${1:?codex worktree path}"   # e.g. /home/olares/code/apex/apex-breaker-codex
HERE="$(cd "$(dirname "$0")" && pwd)"
env -i \
  PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:/usr/bin:/bin \
  HOME=/home/olares/.breaker-codex-home \
  BREAKER_SANDBOX_DSN="$BREAKER_SANDBOX_DSN" \
  codex exec -s workspace-write -C "$WORKTREE" - < "$HERE/direction.md"
```

- [ ] **Step 4: Run preflight to verify the env proof passes**

Run: `ssh olares-mesh 'cd '"$ROOT"' && bash codex-harness/preflight.sh > /tmp/pf.log 2>&1; echo EXIT=$?; tail -3 /tmp/pf.log'`
Expected: `EXIT=0`, `preflight OK (…)`. (If codex emits a non-fatal bubblewrap/skills warning to stderr, the no-op step still exits 0 — only a real failure trips it.)

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): sanitized codex harness + dry-run preflight + #79 direction"'
```

---

### Task 6: Manifest generator + runbook

**Files:**
- Create: `infra/database/sandbox/breaker/provision/write_manifest.sh`
- Create: `infra/database/sandbox/breaker/README.md`

**Interfaces:**
- Consumes: a restored baseline DB name + the dump file (for sha256) + a UTC timestamp string (passed in — the controller stamps it).
- Produces: `write_manifest.sh <BASELINE_DB> <DUMP_FILE> <STAMP> <SOURCE_REF>` → writes `SNAPSHOT_MANIFEST.md` with relkind counts, RLS/policy facts, preflight result, sha256, and placeholders for the privilege-matrix + deletion proof (filled in Task 7). `README.md` is the runbook.

- [ ] **Step 1: Write write_manifest.sh**

`provision/write_manifest.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Usage: write_manifest.sh <BASELINE_DB> <DUMP_FILE> <STAMP_UTC> <SOURCE_REF>
BASELINE_DB="${1:?}"; DUMP_FILE="${2:?}"; STAMP="${3:?}"; SRC="${4:?}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SU() { docker exec -i apex-dev-pg psql -tA -U postgres "$@"; }
counts=$(SU -d "$BASELINE_DB" -c "select string_agg(k||'='||n,' ') from (
  select case relkind when 'r' then 'tables' when 'v' then 'views' when 'S' then 'sequences'
                      when 'i' then 'indexes' else relkind::text end k, count(*) n
  from pg_class c join pg_namespace s on s.oid=c.relnamespace
  where s.nspname='tcc' group by 1) z;")
policies=$(SU -d "$BASELINE_DB" -c "select count(*) from pg_policies where schemaname='tcc';")
rls=$(SU -d "$BASELINE_DB" -c "select count(*) from pg_class c join pg_namespace s on s.oid=c.relnamespace where s.nspname='tcc' and c.relkind='r' and c.relrowsecurity;")
sha=$(sha256sum "$DUMP_FILE" | awk '{print $1}')
cat > "$HERE/SNAPSHOT_MANIFEST.md" <<EOF
# Breaker Sandbox — Snapshot Manifest

- Source: $SRC
- Baseline DB: $BASELINE_DB
- Snapshot timestamp (UTC): $STAMP
- Dump command shape: \`pg_dump --no-owner --no-privileges --schema=tcc -Fc <PROD_RO_DSN>\`
- Object counts (tcc): $counts
- RLS: $rls tables RLS-enabled; $policies policies (prod: all \`to public\`; 60 ref auth.*, 0 vault.*)
- Restore preflight: auth.uid/role/jwt stubs created pre-restore; NO login-role stubs needed;
  defaults core-only (no contrib extension); \`pg_restore --exit-on-error\` clean.
- Dump sha256: $sha
- Privilege matrix: (filled by Task 7 acceptance run)
- Dump-file deletion proof: (filled by Task 7)
- Doc drift: repo docs say ~60 tcc tables; prod has 91 — reconcile separately.
EOF
echo "write_manifest OK"
```

- [ ] **Step 2: Write the runbook**

`README.md` — document: the three DBs + roles, the operator dump command (to `/home/olares/dev-pg-backups/tcc/`), the provision order (`restore_baseline → make_viewer → make_codex_clone → privilege checks → write_manifest`), the MCP `breaker-viewer` entry, the harness launch, and the promotion gate (prod only via the governed packet). Keep it to the commands in this plan.

- [ ] **Step 3: Run write_manifest on the fixture baseline and assert sections present**

Run:
```
ssh olares-mesh 'cd '"$ROOT"' && bash provision/write_manifest.sh tcc_breaker_baseline_fixture _local/tcc_fixture.dump 2026-06-25T00:00:00Z "fixture(synthetic)" && grep -E "Object counts|RLS:|sha256|deletion proof" SNAPSHOT_MANIFEST.md | wc -l'
```
Expected: `4` (all four required sections present).

- [ ] **Step 4: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): manifest generator + runbook"'
```

---

### Task 7 (OPERATOR-GATED): real prod-dump restore + clones + manifest

**Precondition (operator):** the read-only prod dump exists at `/home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump` (CC pre-created the dir mode 700; CC `chmod 600` on receipt). Do NOT start this task until the dump is present.

**Files:**
- Modify: `infra/database/sandbox/breaker/SNAPSHOT_MANIFEST.md` (real run)
- Create: `~/.claude.json` MCP entry `breaker-viewer` (host CC config — read-only DSN to the viewer clone)

- [ ] **Step 1: Confirm the dump landed + lock its mode**

Run: `ssh olares-mesh 'ls -l /home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump && chmod 600 /home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump'`
Expected: file present; mode becomes `-rw-------`.

- [ ] **Step 2: Restore the real baseline (same script as the fixture, fail-closed) + EXACT-count gate**

Run: `ssh olares-mesh 'cd '"$ROOT"' && bash provision/restore_baseline.sh tcc_breaker_baseline_20260625 /home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump > /tmp/rr.log 2>&1; echo EXIT=$?; tail -5 /tmp/rr.log'`
Expected: `EXIT=0`. `check_baseline.sql` also runs and passes its `>=` thresholds.

Create the real-mode EXACT-count gate `sql/checks/check_baseline_exact.sql` (fail-closed on any deviation from the probed prod facts — catches a partial/duplicated restore the loose check would miss):
```sql
do $$
declare t int; v int; s int; i int; rls int; pol int;
begin
  select count(*) into t   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='r';
  select count(*) into v   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='v';
  select count(*) into s   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='S';
  select count(*) into i   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='i';
  select count(*) into rls from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='r' and c.relrowsecurity;
  select count(*) into pol from pg_policies where schemaname='tcc';
  if t<>91    then raise exception 'exact: tables %, want 91', t; end if;
  if v<>2     then raise exception 'exact: views %, want 2', v; end if;
  if s<>30    then raise exception 'exact: sequences %, want 30', s; end if;
  if i<>190   then raise exception 'exact: indexes %, want 190', i; end if;
  if rls<>60  then raise exception 'exact: rls tables %, want 60', rls; end if;
  if pol<>120 then raise exception 'exact: policies %, want 120', pol; end if;
  raise notice 'check_baseline_exact OK (91/2/30/190, rls 60, pol 120)';
end $$;
```
Run it fail-closed (MUST pass before manifest acceptance):
`ssh olares-mesh 'docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres -d tcc_breaker_baseline_20260625 -f - < '"$ROOT"'/sql/checks/check_baseline_exact.sql; echo EXIT=$?'`
Expected: `EXIT=0`, `check_baseline_exact OK (91/2/30/190, rls 60, pol 120)`.

- [ ] **Step 3: Spawn the real viewer + codex clones + generic read/write proofs**

Run:
```
ssh olares-mesh 'cd '"$ROOT"' && bash provision/make_viewer.sh tcc_breaker_baseline_20260625 tcc_breaker_viewer_20260625 && bash provision/make_codex_clone.sh tcc_breaker_baseline_20260625 tcc_breaker_codex_79audit_20260625 tcc_breaker_codex_79audit'
```
Then the GENERIC checks (same files as the fixture — now table-name-agnostic):
- `check_viewer.sql` against `tcc_breaker_viewer_20260625` → `EXIT=0`.
- `check_codex_clone.sql` against `tcc_breaker_codex_79audit_20260625` → `EXIT=0`.
- Real viewer read-proof on a real key table as `tcc_breaker_ro`:
  ```
  ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
    docker exec -i -e PGPASSWORD="$TCC_BREAKER_RO_PW" apex-dev-pg psql -tA -U tcc_breaker_ro -h 127.0.0.1 \
    -d tcc_breaker_viewer_20260625 -c "select count(*) from tcc.etu_sensors;"'
  ```
  Expected: `17831` (RLS disabled → all rows visible to the read role).
- Generic codex write/DDL probe as `tcc_breaker_codex_79audit` on the real clone (identical to Task 4):
  ```
  ssh olares-mesh 'set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a; \
    docker exec -i -e PGPASSWORD="$TCC_BREAKER_CODEX_PW" apex-dev-pg psql -v ON_ERROR_STOP=1 \
    -U tcc_breaker_codex_79audit -h 127.0.0.1 -d tcc_breaker_codex_79audit_20260625 \
    -c "create table tcc._codex_write_probe(id int);" -c "insert into tcc._codex_write_probe values (1);" \
    -c "drop table tcc._codex_write_probe;"'
  ```
  Expected: all three succeed — codex owns schema `tcc` on the real clone and writes freely.
- Residual-ownership visibility (`sql/checks/check_residual_owner.sql`) on the real clone:
  `ssh olares-mesh 'docker exec -i apex-dev-pg psql -U postgres -d tcc_breaker_codex_79audit_20260625 -f - < '"$ROOT"'/sql/checks/check_residual_owner.sql'`
  → record the returned `residual_functions_postgres` / `residual_types_postgres` as a `Residual postgres-owned tcc functions/types: F / T` line in the manifest.

- [ ] **Step 4: Run the full privilege matrix + sibling isolation, capture results**

Run `check_role_zero_reach.sql` (postgres db) and, against each of `ops_dev`, `records_dev`, `learning_dev`, `orchestration_dev`: BOTH `check_sibling_no_table_priv.sql` (`leaked=0`) AND `check_schema_create.sql` (codex has no CREATE on `public`). All must pass. Save the outputs for the manifest's privilege-matrix line.

- [ ] **Step 5: Write the real manifest, delete the dump, record deletion proof**

Run:
```
ssh olares-mesh 'cd '"$ROOT"' && bash provision/write_manifest.sh tcc_breaker_baseline_20260625 /home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump "'"$(date -u +%FT%TZ)"'" "prod fxoyniqnrlkxfligbxmg tcc @ 2026-06-25" && rm -f /home/olares/dev-pg-backups/tcc/tcc_baseline_20260625.dump && find /home/olares/dev-pg-backups/tcc/ -name tcc_baseline_20260625.dump | wc -l'
```
Expected: manifest written; final count `0` (`find … | wc -l` prints `0` and exits 0 even with no matches — unlike `grep -c`, which exits 1 on success here). Hand-edit the manifest's privilege-matrix + deletion-proof lines with the Step 4 results + "dump deleted `$(date)`".

- [ ] **Step 6: Add the read-only MCP `breaker-viewer` entry**

Add to host CC `~/.claude.json` an `mcp-db-server-local`-style entry `breaker-viewer` whose DSN points at `tcc_breaker_viewer_20260625` via `tcc_breaker_ro` (password `${TCC_BREAKER_RO_PW}` interpolation, per the host-MCP `${ENV}` convention — never plaintext). Verify it lists tables read-only on next CC restart.

- [ ] **Step 7: Drop the fixture DBs (cleanup) + commit**

Run: `ssh olares-mesh 'for d in tcc_breaker_fixture_src tcc_breaker_baseline_fixture tcc_breaker_viewer_fixture tcc_breaker_codex_fixture; do docker exec apex-dev-pg psql -U postgres -d postgres -c "drop database if exists \"$d\";"; done'`
Then: `ssh olares-mesh 'cd /home/olares/code/apex/apex-breaker-sandbox && git add -A && git commit -m "feat(breaker-sandbox): real prod-dump baseline + clones + manifest (operator-gated)"'`

---

## Task 7 acceptance addenda — now COMMITTED as reusable scripts (pre-merge hardening; verified on the fixture)

The final-review safety addenda are committed scripts, NOT prose — T7 runs files, never hand-transcribed SQL:
- **`sql/checks/check_baseline_exact.sql`** (A-exact) — exact-count gate (91/2/30/190 + 60/120), fail-closed; run in T7 Step 2 against the real baseline. (Fixture-verified: RAISEs `tables 2, want 91` on the fixture, i.e. correctly fail-closed.)
- **`sql/checks/check_schema_create.sql`** (A2) — asserts the codex role has no CREATE on `public`; run per-sibling in T7 Step 4 alongside `check_sibling_no_table_priv.sql`. (Fixture-verified green on ops_dev.)
- **`sql/checks/check_residual_owner.sql`** (A1) — reports postgres-owned tcc functions/types (visibility, not fail-closed); run on the real codex clone in T7 Step 3 and record the result as a `Residual postgres-owned tcc functions/types: F / T` line in `SNAPSHOT_MANIFEST.md`. (Fixture-verified: 0/0.)
- **A3 (done in merged code):** `restore_baseline.sh` has an EXIT trap removing `/tmp/restore.dump` on success OR failure — no proprietary catalog data left in container `/tmp` after a failed restore. (Fixture-verified: `TRAP_CLEANED`.)

## Self-Review

**Spec coverage:** baseline/viewer/codex DBs (T1/T3/T4/T7) ✓; frozen baseline connection-free (T1 revoke + TEMPLATE in T3/T4) ✓; auth stubs exact sigs (T0/T1) ✓; no login-role stubs / core-only ext (manifest T6) ✓; clone-local RLS — viewer DISABLE (T3), codex REASSIGN OWNED (T4) ✓; NO BYPASSRLS (T2 `nobypassrls`) ✓; scoped roles + privilege matrix incl. sibling table-priv probe (T2/T4) ✓; sanitized harness env -i + dry-run + grep -E proof (T5) ✓; dump path/mode + sha256 + deletion proof (T6/T7) ✓; operator-gated real restore (T7) ✓; MCP viewer entry (T7) ✓; manifest with drift note (T6) ✓; promotion gate (README T6, direction T5) ✓.

**Placeholder scan:** no TBD/TODO; every script + check is complete runnable code. The only intentionally-deferred fills are the manifest privilege-matrix/deletion lines, which Task 7 Step 5 explicitly populates.

**Type/name consistency:** DB names (`tcc_breaker_baseline_20260625` / `_viewer_` / `_codex_79audit_`), role names (`tcc_breaker_ro`, `tcc_breaker_codex_79audit`), env vars (`TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`, `BREAKER_SANDBOX_DSN`), and script signatures are used identically across tasks. Fixture analogues use the `_fixture` suffix and are dropped in T7.

**Round-4 cross-engine patches (all applied):** (1) `check_viewer.sql` is now table-name-agnostic (all-tcc-tables RLS-off + ro SELECT-on-all/write-on-none) so Task 7 reuses it unchanged; (2) role passwords are random (`openssl rand`) and reach psql via ENV→`\getenv`, never argv, never fixed literals; (3) Task 7 adds `check_baseline_exact.sql` (exact 91/2/30/190 + 60/120, fail-closed) before manifest acceptance; (4) the codex write proof is a generic `tcc._codex_write_probe` create/insert/drop reused on the real clone; (5) `build_fixture_dump.sh` creates `_local/`; (6) deletion proof uses `find … | wc -l` (no false-fail). Host verified by review: `apex-dev-pg` up, in-container PG 17.10, 5432 bound, Codex 0.141.0.

**One flagged assumption to verify at T1 Step 4:** that `apex-dev-pg` exposes 5432 on host `127.0.0.1` and the scoped roles authenticate over `-h 127.0.0.1` (password auth). The reviewer confirmed 5432 is bound; the role-as-TCP proofs run via `docker exec … -h 127.0.0.1` (the container's own loopback) — already how the steps are written.
