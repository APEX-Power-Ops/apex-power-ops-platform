# Records Gate 5 - Serving Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all `records.*` objects off the superuser `postgres` owner onto a non-superuser `records_owner` + FORCE RLS (5A), and add a metadata-minimal, DB-trigger audit trail with correct actor attribution feeding an append-only `records.audit_log` owned by a non-superuser `records_fn_owner` and readable only by `records_auditor` (5B), plus a machine-readable serving contract for Gate 9.

**Architecture:** Authoritative migrations `046-049` (each reversible), a `run_validation.py` **Tier 6** posture proof, and a `reference/records/SERVING_CONTRACT.{yaml,md}` doc. Spec: `docs/superpowers/specs/2026-07-03-records-gate5-serving-security-design.md` (rev 3). Nothing is applied to prod Supabase.

**Tech Stack:** PostgreSQL 17 (disposable dev DB), Python 3 + psycopg (`run_validation.py` harness, `_dbtest.py` helpers), pytest, bash.

## Global Constraints

Copied verbatim from the spec (every task's requirements implicitly include these):

- **Authoritative migrations, not deltas.** REVOKE/normalize first, then apply, with **in-migration posture asserts** (`raise exception` on any violated invariant). Mirror 045's revoke-first + exactness-assert pattern.
- **Reversible `_down` for every migration.** NOLOGIN owner roles (`records_owner`, `records_fn_owner`): the down **RAISES** if the role survives; it never swallows `dependent_objects_still_exist` as a NOTICE. **Exception:** the password-bearing LOGIN role `records_auditor` uses the DEV-7 guard (revoke grants; drop only if passwordless/harness-created; RETAIN with a NOTICE if password-bearing). Any `DROP OWNED BY` is preceded by an assert that the role owns ZERO records objects.
- **ASCII-only added lines** (no U+2014 em-dashes).
- **Disposable dev DB only** (`records_val_*`); **NEVER `records_dev`** (harness `guard_target` refuses it); **NEVER prod Supabase**.
- **No migration sets a password.** `records_owner`/`records_fn_owner` are NOLOGIN; `records_auditor` is LOGIN with NO inline password (out-of-band). Role read/mutation proofs use `SET SESSION AUTHORIZATION` for mutating identities (sets `session_user`) and may use `SET ROLE` for read-only checks.
- **`TO <named-role>` idiom** on every new policy.
- **Audit metadata-minimal:** table, pk, operation, actor identity (`session_user`) + definer role (`current_user`), txid, timestamp, changed-column NAMES; **NO before/after row values and NO content row_hash**; `app_actor` is bounded + untrusted.
- **Honest scope:** closes the non-superuser-owner RLS bypass only; `postgres`-superuser / `service_role` bypass stays custody + detector + a deferred startup assertion.
- **Commit trailer:** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **Host-only canonical tree.** Author files locally (ASCII-checkable), `scp` to the host worktree `/home/olares/code/apex/apex-records-gate5`, run/commit host-side via `ssh olares-mesh`. Apply/test with the worktree `.venv/bin/python` after `set -a; . ./.env.dev; set +a` (provides `RECORDS_PG_ADMIN_DSN`); `export PATH=$HOME/.local/bin:$PATH` for uv.

---

## Plan rev 2 corrections (BINDING - apply to every task below)

These fold the operator's plan review (2026-07-03). They OVERRIDE the task code where they conflict; apply them uniformly:

1. **Transaction-wrap every migration file** (up and down), matching the established 045 shape - NOT bare `SET LOCAL`:
   ```sql
   begin;
   set client_encoding to 'UTF8';
   set local client_min_messages = warning;
   -- ... migration body ...
   commit;
   ```
   `SET LOCAL` is only meaningful inside a transaction; a mid-file failure then rolls back atomically (no partial security state). All of 046-049 + their `_down` files use `CREATE/ALTER ROLE`, `ALTER ... OWNER`, `CREATE TABLE/FUNCTION/TRIGGER`, `CREATE POLICY` - all transactional.

2. **Role normalization (guarded create is not enough).** A role may pre-exist on a persistent cluster in a wrong state. After each guarded `create role ... if not exists`, add an UNCONDITIONAL `ALTER ROLE` to pin the exact state, then assert it:
   ```sql
   alter role records_owner    nologin nosuperuser nobypassrls nocreatedb nocreaterole noreplication;
   alter role records_fn_owner nologin nosuperuser nobypassrls nocreatedb nocreaterole noreplication;
   alter role records_auditor  login   nosuperuser nobypassrls nocreatedb nocreaterole noreplication;  -- NO password
   -- assert: for each of the three roles, rolcanlogin matches, and
   -- rolsuper/rolbypassrls/rolcreatedb/rolcreaterole/rolreplication are all false.
   ```
   (This replaces the bare guarded-create in Tasks 1 and 2.)

3. **Per-migration test contract (the runner applies NNN, THEN runs `test_NNN`, THEN fingerprints to confirm the test LEFT the DB at the applied-NNN state).** Therefore every `test_NNN` must: (a) assert the applied-NNN posture (the runner already applied it - do NOT re-apply NNN first); (b) run `NNN_down`; (c) assert the reversed/pre-state; (d) run `NNN` (up) again; (e) leave the DB at applied-NNN. NEVER start a test by re-applying NNN, and NEVER leave it reversed (both move the fingerprint or trip a pre-state assert). This corrects the `test_046` code in Task 1.

---

## File Structure

Created under `infra/database/migrations/records/`:
- `046_records_ownership.sql` / `046_records_ownership_down.sql` - 5A ownership + FORCE RLS.
- `047_records_audit_roles.sql` / `047_records_audit_roles_down.sql` - `records_fn_owner` + `records_auditor`.
- `048_records_audit_log.sql` / `048_records_audit_log_down.sql` - `audit_log` (FORCE-RLS) + `fn_audit_capture` definer.
- `049_records_audit_triggers.sql` / `049_records_audit_triggers_down.sql` - triggers on the writer-grant set.
- `test_046_records_ownership.py`, `test_047_records_audit_roles.py`, `test_048_records_audit_log.py`, `test_049_records_audit_triggers.py` - per-migration destructive down->up validators (per-chip rule).
- `MANIFEST.md` - append rows 046-049.

Modified:
- `run_validation.py` - add `tier6_posture`, extend `parse_tiers` to `{0..6}`, wire into `main`.
- `test_run_validation_unit.py` - `parse_tiers` `{0..6}` cases.

Created under `reference/records/`:
- `SERVING_CONTRACT.yaml` + `SERVING_CONTRACT.md` - role -> Supabase-boundary map + DSN-form inventory.

Created under `docs/operations/`:
- `RECORDS-GATE5-EVIDENCE-2026-07.md` - AC1-AC11 mapping + transcripts (final task).

**Interfaces the whole plan shares** (names later tasks rely on):
- Roles: `records_owner` (NOLOGIN, owns all `records.*`), `records_fn_owner` (NOLOGIN, owns `audit_log` + `fn_audit_capture`), `records_auditor` (LOGIN, reads `audit_log` only). Pre-existing (045): `records_api`, `records_intake_writer`.
- `records.audit_log(audit_id bigint PK, event_at timestamptz, action text, table_name text, row_pk text, actor_role text, definer_role text, actor_is_superuser boolean, txid bigint, application_name text, client_addr inet, changed_columns text[], app_actor text)`.
- `records.fn_audit_capture()` - SECURITY DEFINER, owner `records_fn_owner`, `SET search_path=pg_catalog,records`; trigger arg `TG_ARGV[0]` = the table's PK column name.
- Harness `SET SESSION AUTHORIZATION <role>` proof helpers already exist in Tier 5 (`run_validation.py`); Tier 6 reuses them.

---

### Task 0: Pre-flight - worktree env + clean baseline

**Files:** none created. Verifies the host env.

- [ ] **Step 1: Confirm mesh + worktree + env.**

Run (host): `ssh olares-mesh 'cd /home/olares/code/apex/apex-records-gate5 && git log --oneline -1 && ls .env.dev 2>&1 && test -x .venv/bin/python && echo VENV_OK'`
Expected: HEAD at the rev-3 spec commit; `.env.dev` present (operator-provisioned admin DSN, chmod 600); `VENV_OK`. If `.env.dev` is absent, STOP and request the operator provision it (out-of-band, Vault-first) - do not proceed.

- [ ] **Step 2: Baseline the existing ladder (Tiers 0-5 green on a disposable DB).**

Run (host, from the worktree): `set -a; . ./.env.dev; set +a; export PATH=$HOME/.local/bin:$PATH; .venv/bin/python infra/database/migrations/records/run_validation.py --require-db`
Expected: Tiers 0-5 PASS (21/21 units + AC8 fixture + full ladder), proving the pre-Gate-5 tree is clean before any change. Record the result.

- [ ] **Step 3: Commit nothing** (baseline only). Proceed to Task 1.

---

### Task 1: Migration 046 - ownership posture + FORCE RLS

**Files:**
- Create: `infra/database/migrations/records/046_records_ownership.sql`
- Create: `infra/database/migrations/records/046_records_ownership_down.sql`
- Test: `infra/database/migrations/records/test_046_records_ownership.py`

**Interfaces:**
- Consumes: the 15 base tables + 2 views + `fn_set_updated_at` + `records` schema, all owned by `postgres` (asserted pre-state).
- Produces: `records_owner` (NOLOGIN NOSUPER NOBYPASSRLS) owning all `records.*`; all 15 tables `FORCE ROW LEVEL SECURITY`.

- [ ] **Step 1: Write `046_records_ownership.sql`.**

```sql
-- 046_records_ownership.sql
-- Gate 5A: move every records object off the superuser owner onto a
-- non-superuser records_owner, then FORCE ROW LEVEL SECURITY so RLS binds the
-- owner. Authoritative + reversible. Runs as the superuser admin; superuser
-- bypasses FORCE, so this migration's own DDL is unaffected.
set local client_min_messages = warning;

-- [0] pre-state: every records object + schema must be owned by postgres.
do $$
declare n int;
begin
  select count(*) into n
    from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
   where ns.nspname = 'records' and c.relkind in ('r','v','m','S')
     and pg_get_userbyid(c.relowner) <> 'postgres';
  if n > 0 then raise exception '046 pre-state: % records object(s) not owned by postgres', n; end if;
  if (select pg_get_userbyid(nspowner) from pg_namespace where nspname='records') <> 'postgres'
    then raise exception '046 pre-state: records schema not owned by postgres'; end if;
end $$;

-- [1] non-superuser owner role (guarded) + both-direction membership hardening.
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_owner') then
    create role records_owner nologin nosuperuser nobypassrls;
  end if;
end $$;
do $$
declare r record;
begin
  for r in select m.rolname as who from pg_auth_members am
             join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
             join pg_roles m on m.oid=am.member
  loop execute format('revoke records_owner from %I', r.who); end loop;
  for r in select g.rolname as who from pg_auth_members am
             join pg_roles ro on ro.oid=am.member and ro.rolname='records_owner'
             join pg_roles g on g.oid=am.roleid
  loop execute format('revoke %I from records_owner', r.who); end loop;
end $$;

-- [2] explicit ALTER OWNER of every records object + the schema (NOT reassign-owned).
do $$
declare r record;
begin
  for r in select c.relkind, c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind in ('r','m')
  loop execute format('alter table records.%I owner to records_owner', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='v'
  loop execute format('alter view records.%I owner to records_owner', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='S'
  loop execute format('alter sequence records.%I owner to records_owner', r.relname); end loop;
  for r in select p.proname, pg_get_function_identity_arguments(p.oid) as args
             from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='records'
  loop execute format('alter function records.%I(%s) owner to records_owner', r.proname, r.args); end loop;
  execute 'alter schema records owner to records_owner';
end $$;

-- [3] FORCE ROW LEVEL SECURITY on all base tables (RLS already enabled by 045).
do $$
declare r record;
begin
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='r'
  loop execute format('alter table records.%I force row level security', r.relname); end loop;
end $$;

-- [4] posture asserts (authoritative).
do $$
declare n int; su bool; brls bool;
begin
  select count(*) into n from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and c.relkind in ('r','v','m','S')
     and pg_get_userbyid(c.relowner) <> 'records_owner';
  if n>0 then raise exception '046: % records object(s) not owned by records_owner', n; end if;
  select rolsuper, rolbypassrls into su, brls from pg_roles where rolname='records_owner';
  if su or brls then raise exception '046: records_owner must be NOSUPERUSER + NOBYPASSRLS'; end if;
  select count(*) into n from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity;
  if n>0 then raise exception '046: % records table(s) not FORCE-RLS', n; end if;
  select count(*) into n from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid
   where ro.rolname='records_owner' and sd.deptype='a';
  if n>0 then raise exception '046: records_owner holds % ACL grant(s); must be a pure owner', n; end if;
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
     join pg_roles m on m.oid=am.member where m.rolcanlogin;
  if n>0 then raise exception '046: % LOGIN role(s) are members of records_owner', n; end if;
end $$;
```

- [ ] **Step 2: Write `046_records_ownership_down.sql`.**

```sql
-- 046_records_ownership_down.sql - reverse 046 to the postgres pre-state.
set local client_min_messages = warning;

-- [d1] NO FORCE on all base tables.
do $$
declare r record;
begin
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='r'
  loop execute format('alter table records.%I no force row level security', r.relname); end loop;
end $$;

-- [d2] reassign every records object + schema explicitly back to postgres.
do $$
declare r record;
begin
  for r in select c.relkind, c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind in ('r','m')
  loop execute format('alter table records.%I owner to postgres', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='v'
  loop execute format('alter view records.%I owner to postgres', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='S'
  loop execute format('alter sequence records.%I owner to postgres', r.relname); end loop;
  for r in select p.proname, pg_get_function_identity_arguments(p.oid) as args
             from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='records'
  loop execute format('alter function records.%I(%s) owner to postgres', r.proname, r.args); end loop;
  execute 'alter schema records owner to postgres';
end $$;

-- [d3] GUARD: refuse DROP OWNED unless records_owner owns ZERO objects across
-- ALL relevant catalogs (a DROP OWNED on an incomplete reassign would DELETE
-- the missed object). MUST cover pg_class (tables/views/matviews/sequences),
-- pg_proc (functions), AND pg_namespace (the records schema itself - a missed
-- schema would be DROPped CASCADE).
do $$
declare n int;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and c.relkind in ('r','v','m','S')
        and pg_get_userbyid(c.relowner)='records_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner)='records_owner')
  + (select count(*) from pg_namespace where nspname='records'
        and pg_get_userbyid(nspowner)='records_owner')
    into n;
  if n>0 then raise exception '046_down: % records object(s) still owned by records_owner (class/proc/schema); refusing DROP OWNED', n; end if;
end $$;

-- [d4] clear any ACL residue (provably none), drop the role, fail loud if it survives.
drop owned by records_owner;
drop role if exists records_owner;
do $$
begin
  if exists (select 1 from pg_roles where rolname='records_owner')
    then raise exception '046_down: records_owner survived drop'; end if;
end $$;
```

- [ ] **Step 3: Write `test_046_records_ownership.py`** (destructive down->up self-validator; per-chip rule).

```python
import os
import pytest
import _dbtest

MIG = "046_records_ownership.sql"
DOWN = "046_records_ownership_down.sql"

def _dsn():
    v = os.environ.get("RECORDS_DEV_DSN") or os.environ.get("RECORDS_VAL_DSN")
    if not v:
        pytest.skip("no disposable DSN (harness sets RECORDS_VAL_DSN for tier 3)")
    return _dbtest.guard_target(v)

def _q(dsn, sql):
    with _dbtest.connect(dsn) as c, c.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()

OWNED_NE = ("select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
            "where ns.nspname='records' and c.relkind in ('r','v','m','S') "
            "and pg_get_userbyid(c.relowner) <> '%s'")

def test_046_applied_then_down_up():
    # Runner contract: 046 is ALREADY applied by the walk. Assert the applied
    # posture, exercise DOWN then UP, and LEAVE 046 applied (do NOT re-apply
    # first, do NOT leave reversed - either moves the fingerprint / trips the
    # 046 pre-state assert).
    dsn = _dsn()
    # (1) applied posture
    assert _q(dsn, OWNED_NE % "records_owner")[0][0] == 0
    assert _q(dsn, "select rolsuper, rolbypassrls from pg_roles where rolname='records_owner'")[0] == (False, False)
    assert _q(dsn, "select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
                   "where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity")[0][0] == 0
    # FORCE teeth (SET SESSION AUTHORIZATION so session_user IS the role)
    with _dbtest.connect(dsn) as c, c.cursor() as cur:
        cur.execute("select count(*) from records.neta_tables"); base = cur.fetchone()[0]
        assert base > 0
        cur.execute("set session authorization records_owner")
        cur.execute("select count(*) from records.neta_tables"); assert cur.fetchone()[0] == 0
        cur.execute("reset session authorization")
        cur.execute("set session authorization records_api")
        cur.execute("select count(*) from records.neta_tables"); assert cur.fetchone()[0] == base
        cur.execute("reset session authorization")
    # (2) DOWN -> reversed to the postgres pre-state + role dropped (fail-loud)
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, OWNED_NE % "postgres")[0][0] == 0
    assert _q(dsn, "select count(*) from pg_roles where rolname='records_owner'")[0][0] == 0
    # (3) UP -> re-apply 046 (its pre-state assert now passes) and LEAVE it applied
    _dbtest.run_psql(MIG, dsn)
    assert _q(dsn, OWNED_NE % "records_owner")[0][0] == 0  # role actually dropped (fail-loud would have raised)
```
(Note: `_dbtest.connect` / `guard_target` / `run_psql` already exist; if `connect` is named differently in `_dbtest.py`, the implementer uses the existing helper - confirm the name during Step 4.)

- [ ] **Step 4: Apply + run the test on a disposable DB.**

Run (host, worktree; build a disposable DB first via the harness Tier-3 walk or a scratch `records_val_*` created with the admin DSN, set `RECORDS_VAL_DSN`): apply 001-045 then `pytest infra/database/migrations/records/test_046_records_ownership.py -v`.
Expected: PASS (ownership moved, FORCE teeth proven, reversed clean, role dropped).

- [ ] **Step 5: Commit.**

```bash
git add infra/database/migrations/records/046_records_ownership*.sql \
        infra/database/migrations/records/test_046_records_ownership.py
git commit -m "feat(records): 046 ownership posture - records_owner + FORCE RLS (Gate 5A)"
```

---

### Task 2: Migration 047 - audit roles (`records_fn_owner` + `records_auditor`)

**Files:**
- Create: `047_records_audit_roles.sql` / `047_records_audit_roles_down.sql`
- Test: `test_047_records_audit_roles.py`

**Interfaces:**
- Produces: `records_fn_owner` (NOLOGIN NOSUPER NOBYPASSRLS, will own audit objects) and `records_auditor` (LOGIN, no password; its `audit_log` SELECT policy is added in 048).

- [ ] **Step 1: Write `047_records_audit_roles.sql`.**

```sql
-- 047_records_audit_roles.sql - the two audit roles. No grants to operational
-- tables (auditor reads audit_log only, granted via policy in 048). No password.
set local client_min_messages = warning;
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_fn_owner') then
    create role records_fn_owner nologin nosuperuser nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname='records_auditor') then
    create role records_auditor login nosuperuser nobypassrls;  -- NO password (out-of-band)
  end if;
end $$;
-- both-direction membership hardening for both roles.
do $$
declare r record; owner text;
begin
  foreach owner in array array['records_fn_owner','records_auditor'] loop
    for r in select m.rolname as who from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname=owner
               join pg_roles m on m.oid=am.member
    loop execute format('revoke %I from %I', owner, r.who); end loop;
    for r in select g.rolname as who from pg_auth_members am
               join pg_roles ro on ro.oid=am.member and ro.rolname=owner
               join pg_roles g on g.oid=am.roleid
    loop execute format('revoke %I from %I', r.who, owner); end loop;
  end loop;
end $$;
-- asserts.
do $$
declare su bool; brls bool; n int;
begin
  for su, brls in select rolsuper, rolbypassrls from pg_roles
                   where rolname in ('records_fn_owner','records_auditor') loop
    if su or brls then raise exception '047: an audit role is super/bypassrls'; end if;
  end loop;
  select count(*) into n from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid
   where ro.rolname='records_fn_owner' and sd.deptype='a';
  if n>0 then raise exception '047: records_fn_owner holds ACL grants; must be a pure owner'; end if;
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_fn_owner'
     join pg_roles m on m.oid=am.member where m.rolcanlogin;
  if n>0 then raise exception '047: a LOGIN role is a member of records_fn_owner'; end if;
end $$;
```

- [ ] **Step 2: Write `047_records_audit_roles_down.sql`** (asymmetric drop discipline).

```sql
-- 047_records_audit_roles_down.sql
set local client_min_messages = warning;
-- records_fn_owner: NOLOGIN pure owner -> zero-owned guard (class+proc+schema) +
-- DROP OWNED + fail-loud.
do $$
declare n int;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and pg_get_userbyid(c.relowner)='records_fn_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner)='records_fn_owner')
  + (select count(*) from pg_namespace where nspname='records'
        and pg_get_userbyid(nspowner)='records_fn_owner')
    into n;
  if n>0 then raise exception '047_down: % object(s) still owned by records_fn_owner; refusing DROP OWNED', n; end if;
end $$;
drop owned by records_fn_owner;
drop role if exists records_fn_owner;
do $$ begin
  if exists (select 1 from pg_roles where rolname='records_fn_owner')
    then raise exception '047_down: records_fn_owner survived drop'; end if;
end $$;
-- records_auditor: LOGIN, password provisioned out-of-band -> DEV-7 guard,
-- mirroring 045_down. NO `DROP OWNED` (the LOGIN-role hazard Gate 3 avoided):
-- explicit DB-scoped revokes, then DROP ROLE ONLY if it is passwordless
-- (harness / disposable-DB case); RETAIN with a NOTICE if password-bearing.
do $$
declare has_pw bool;
begin
  if not exists (select 1 from pg_roles where rolname='records_auditor') then
    return;
  end if;
  revoke usage on schema records from records_auditor;   -- safe if not granted
  -- (048_down already revoked SELECT on audit_log / it drops with the table)
  select (rolpassword is not null) into has_pw from pg_authid where rolname='records_auditor';
  if coalesce(has_pw, true) then   -- unreadable pw => assume present => fail-safe RETAIN
    raise notice '047_down: records_auditor is password-bearing; RETAINED (DEV-7 guard).';
  else
    drop role records_auditor;
  end if;
end $$;
```
(Reading `pg_authid.rolpassword` requires superuser; the harness/admin DSN is superuser. If unreadable in some env, treat as password-bearing and RETAIN - fail-safe.)

- [ ] **Step 3: Write `test_047_records_audit_roles.py`** - assert both roles exist non-super/non-bypassrls; `records_auditor` is LOGIN; down drops `records_fn_owner` (fail-loud) and, on the disposable DB where `records_auditor` has no password, drops it too; re-up restores.

- [ ] **Step 4: Apply + test on a disposable DB.** Expected PASS.

- [ ] **Step 5: Commit** `feat(records): 047 audit roles - records_fn_owner + records_auditor (Gate 5B)`.

---

### Task 3: Migration 048 - `audit_log` (FORCE-RLS) + `fn_audit_capture` definer

**Files:**
- Create: `048_records_audit_log.sql` / `048_records_audit_log_down.sql`
- Test: `test_048_records_audit_log.py`

**Interfaces:**
- Consumes: `records_fn_owner`, `records_auditor` (047).
- Produces: `records.audit_log` (owned by `records_fn_owner`, FORCE-RLS, append-only) + `records.fn_audit_capture()` (SECURITY DEFINER, owned by `records_fn_owner`, search_path pinned). Trigger contract: `EXECUTE FUNCTION records.fn_audit_capture('<pk_col>')`.

- [ ] **Step 1: Write `048_records_audit_log.sql`.**

```sql
-- 048_records_audit_log.sql - append-only, metadata-minimal audit log + the
-- SECURITY DEFINER capture function. audit_log is FORCE-RLS so its owner
-- (records_fn_owner) is itself subject to the INSERT policy: the definer runs
-- as that owner, so without FORCE the policy would be a no-op (false-green).
set local client_min_messages = warning;

create table if not exists records.audit_log (
  audit_id          bigint generated always as identity primary key,
  event_at          timestamptz  not null default clock_timestamp(),
  action            text         not null check (action in ('insert','update','delete')),
  table_name        text         not null,
  row_pk            text,
  actor_role        text         not null,   -- session_user (mutating identity)
  definer_role      text         not null,   -- current_user (the definer)
  actor_is_superuser boolean     not null,
  txid              bigint       not null,
  application_name  text,
  client_addr       inet,
  changed_columns   text[],                  -- UPDATE only; column NAMES
  app_actor         text                     -- untrusted, bounded (<=128, token charset)
);
comment on table records.audit_log is
  'Metadata-minimal audit trail. NO row values, NO content hash. Partition key: event_at (monthly, deferred). Retention: indefinite until a retention job is added (deferred). Owned by records_fn_owner; readable only by records_auditor.';
create index if not exists audit_log_event_at_brin on records.audit_log using brin (event_at);
create index if not exists audit_log_tbl_pk on records.audit_log (table_name, row_pk);

alter table records.audit_log owner to records_fn_owner;
alter table records.audit_log enable row level security;
alter table records.audit_log force row level security;   -- owner is subject to RLS
drop policy if exists p_audit_log_ins on records.audit_log;
create policy p_audit_log_ins on records.audit_log for insert to records_fn_owner with check (true);
drop policy if exists p_audit_log_sel on records.audit_log;
create policy p_audit_log_sel on records.audit_log for select to records_auditor using (true);
-- append-only: no UPDATE/DELETE policy for anyone. No app-role grant/policy.
grant usage on schema records to records_auditor;   -- required or SELECT is unreachable
grant select on records.audit_log to records_auditor;

-- the shared SECURITY DEFINER capture function.
create or replace function records.fn_audit_capture() returns trigger
  language plpgsql security definer set search_path = pg_catalog, records as $fn$
declare
  rec       record;
  pk_col    text := TG_ARGV[0];
  changed   text[];
  actor     text := session_user;
  is_su     boolean;
  app       text := nullif(current_setting('records.app_actor', true), '');
begin
  if TG_OP = 'DELETE' then rec := OLD; else rec := NEW; end if;
  if TG_OP = 'UPDATE' then
    select array_agg(o.key) into changed
      from jsonb_each(to_jsonb(OLD)) o join jsonb_each(to_jsonb(NEW)) n on n.key=o.key
     where o.value is distinct from n.value;
  end if;
  select rolsuper into is_su from pg_roles where rolname = session_user;
  -- app_actor is untrusted caller free-text: bound length + charset.
  if app is not null and (length(app) > 128 or app !~ '^[A-Za-z0-9_.:@-]+$') then
    app := 'INVALID_APP_ACTOR';
  end if;
  insert into records.audit_log
    (action, table_name, row_pk, actor_role, definer_role, actor_is_superuser,
     txid, application_name, client_addr, changed_columns, app_actor)
  values
    (lower(TG_OP), TG_TABLE_NAME, (to_jsonb(rec) ->> pk_col), actor, current_user, coalesce(is_su,false),
     txid_current(), nullif(current_setting('application_name', true),''), inet_client_addr(),
     changed, app);
  return null;
end $fn$;
alter function records.fn_audit_capture() owner to records_fn_owner;
-- new functions get default PUBLIC EXECUTE; Gate-3 Tier-5 asserts no PUBLIC on
-- records routines, so revoke it (both a hardening + keeps Tier 5 green).
revoke execute on function records.fn_audit_capture() from public;

-- asserts: definer safety (three load-bearing checks) + FORCE-RLS + no-PUBLIC-execute.
do $$
declare owner text; secdef bool; cfg text[]; forced bool; pub int;
begin
  select pg_get_userbyid(proowner), prosecdef, proconfig into owner, secdef, cfg
    from pg_proc where oid = 'records.fn_audit_capture()'::regprocedure;
  if owner <> 'records_fn_owner' then raise exception '048: fn_audit_capture not owned by records_fn_owner'; end if;
  if not secdef then raise exception '048: fn_audit_capture is not SECURITY DEFINER'; end if;
  if cfg is null or not exists (select 1 from unnest(cfg) x where x like 'search_path=%')
    then raise exception '048: fn_audit_capture search_path not pinned'; end if;
  if (select rolbypassrls or rolsuper from pg_roles where rolname='records_fn_owner')
    then raise exception '048: records_fn_owner must be non-super/non-bypassrls'; end if;
  select relforcerowsecurity into forced from pg_class where oid='records.audit_log'::regclass;
  if not forced then raise exception '048: audit_log is not FORCE-RLS'; end if;
  -- no PUBLIC execute on the function (materialized ACL, NULL-acl-safe).
  select count(*) into pub
    from pg_proc p, lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
   where p.oid='records.fn_audit_capture()'::regprocedure and a.grantee=0 and a.privilege_type='EXECUTE';
  if pub>0 then raise exception '048: fn_audit_capture still has PUBLIC EXECUTE'; end if;
end $$;
```

- [ ] **Step 2: Write `048_records_audit_log_down.sql`** - transaction-wrapped: `revoke usage on schema records from records_auditor;` (048 granted it), then `drop function if exists records.fn_audit_capture();` and `drop table if exists records.audit_log;` (policies + the audit_log SELECT grant drop with the table). ASCII.

- [ ] **Step 3: Write `test_048_records_audit_log.py`** - the false-green guard is the centerpiece:
  - assert `audit_log` is `relforcerowsecurity`; the function is `prosecdef`, owner `records_fn_owner`, search_path pinned.
  - **positive:** manually invoke a capture path as the definer owner and assert a row lands (the INSERT policy TO `records_fn_owner` is exercised because FORCE RLS binds the owner).
  - **negative control:** `drop policy p_audit_log_ins`; repeat the definer insert; assert it RAISES (`new row violates row-level security policy`); recreate the policy. This proves the landing is due to the policy, not owner bypass.
  - assert no `before_row`/`after_row`/`row_hash` column exists (metadata-minimal column-set check).
  - `records_api`/`records_intake_writer` cannot SELECT `audit_log` (SET SESSION AUTHORIZATION -> 0 rows or permission error); `records_auditor` (SET ROLE) can SELECT.
  - down drops function + table; re-up restores.

- [ ] **Step 4: Apply + test on a disposable DB.** Expected PASS incl. the negative control.

- [ ] **Step 5: Commit** `feat(records): 048 audit_log (FORCE-RLS) + fn_audit_capture definer (Gate 5B)`.

---

### Task 4: Migration 049 - audit triggers on the writer-grant set

**Files:**
- Create: `049_records_audit_triggers.sql` / `049_records_audit_triggers_down.sql`
- Test: `test_049_records_audit_triggers.py`

**Interfaces:**
- Consumes: `fn_audit_capture()` (048); the writer-grant table set (045).
- Produces: one AFTER I/U/D FOR EACH ROW trigger per writer-grant table, passing that table's single-column PK name.

- [ ] **Step 1: Write `049_records_audit_triggers.sql`** - derive the audited set from writer grants; look up each table's single-column PK; create the trigger.

```sql
-- 049_records_audit_triggers.sql - attach fn_audit_capture to exactly the
-- tables records_intake_writer may INSERT/UPDATE (the writer-grant set),
-- passing each table's single-column PK name. Excludes audit_log (recursion)
-- and neta_table_source_links (owner-only, D7).
set local client_min_messages = warning;
do $$
declare t record; pk_col text; npk int;
begin
  for t in
    select distinct table_name from information_schema.role_column_grants
     where grantee='records_intake_writer' and table_schema='records'
       and privilege_type in ('INSERT','UPDATE')
  loop
    -- single-column PK name for this table
    select count(*) into npk
      from pg_index i join pg_class c on c.oid=i.indrelid
      join pg_namespace ns on ns.oid=c.relnamespace
     where ns.nspname='records' and c.relname=t.table_name and i.indisprimary;
    if npk <> 1 then raise exception '049: %.% has no single primary key', 'records', t.table_name; end if;
    select a.attname into pk_col
      from pg_index i join pg_class c on c.oid=i.indrelid
      join pg_namespace ns on ns.oid=c.relnamespace
      join pg_attribute a on a.attrelid=c.oid and a.attnum = any(i.indkey)
     where ns.nspname='records' and c.relname=t.table_name and i.indisprimary
       and array_length(i.indkey,1)=1;
    execute format('drop trigger if exists trg_audit on records.%I', t.table_name);
    execute format(
      'create trigger trg_audit after insert or update or delete on records.%I '
      'for each row execute function records.fn_audit_capture(%L)', t.table_name, pk_col);
  end loop;
end $$;
-- assert: trigger set == writer-grant set; no trigger on audit_log or source_links.
do $$
declare got int; want int;
begin
  select count(distinct table_name) into want from information_schema.role_column_grants
   where grantee='records_intake_writer' and table_schema='records'
     and privilege_type in ('INSERT','UPDATE');
  select count(*) into got from pg_trigger tg join pg_class c on c.oid=tg.tgrelid
    join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal;
  if got <> want then raise exception '049: trigger count % <> writer-grant table count %', got, want; end if;
  if exists (select 1 from pg_trigger tg join pg_class c on c.oid=tg.tgrelid
             join pg_namespace ns on ns.oid=c.relnamespace
             where ns.nspname='records' and c.relname in ('audit_log','neta_table_source_links')
               and tg.tgname='trg_audit')
    then raise exception '049: trg_audit present on audit_log or source_links'; end if;
end $$;
```

- [ ] **Step 2: Write `049_records_audit_triggers_down.sql`** - drop `trg_audit` from every table that has it (do-block over `pg_trigger`).

- [ ] **Step 3: Write `test_049_records_audit_triggers.py`** - the actor-attribution centerpiece:
  - trigger set equals the writer-grant set; none on `audit_log`/`source_links`.
  - **writer INSERT via `SET SESSION AUTHORIZATION records_intake_writer`** on a writable table -> exactly one audit row with `action='insert'`, `actor_role='records_intake_writer'`, `definer_role='records_fn_owner'`, `actor_is_superuser=false`, `row_pk` non-null.
  - **superuser/direct-SQL UPDATE and DELETE** (as the admin superuser, no SET) -> one row each; `actor_role`=the admin login, `actor_is_superuser=true`; DELETE row_pk non-null; UPDATE `changed_columns` is the changed set.
  - `app_actor`: `SET LOCAL records.app_actor='tech.42'` -> captured; an over-long/invalid value -> `INVALID_APP_ACTOR`.
  - down removes the triggers; re-up restores. Use FK-valid fixture rows (seed an `assets` row etc. as needed; roll back in a savepoint if convenient).

- [ ] **Step 4: Apply + test on a disposable DB.** Expected PASS incl. actor attribution.

- [ ] **Step 5: Commit** `feat(records): 049 audit triggers on the writer-grant set (Gate 5B)`.

---

### Task 5: Harness Tier 6 + unit tests + MANIFEST

**Files:**
- Modify: `run_validation.py` (add `tier6_posture`, extend `parse_tiers`, wire `main`).
- Modify: `test_run_validation_unit.py` (`parse_tiers` `{0..6}`).
- Modify: `MANIFEST.md` (rows 046-049).

**Interfaces:**
- Consumes: a fully migrated (001-049) disposable DB from the Tier-3 walk.
- Produces: `Tier("6-posture", ...)` covering all Gate-5 in-DB invariants durably (every CI run).

- [ ] **Step 1: Extend `parse_tiers` to `{0..6}`** (default set, error strings "0-6", full-set guard `{0,1,2,3,4,5,6}`). Mirror the existing Tier-5 addition.

- [ ] **Step 2: Add `tier6_posture(child_dsn)`** proving, on the migrated DB: (a) no `records.*` object (relkind r/v/m/S + pg_proc) owned by a `rolsuper`/`rolbypassrls` role; (b) `records_owner`/`records_fn_owner`/`records_auditor` non-super/non-bypassrls; (c) `fn_audit_capture` proowner=records_fn_owner + prosecdef + search_path pinned (durable re-check); (d) `SET ROLE records_owner`/`records_fn_owner` denied from `records_api` + a rogue role; (e) the `trg_audit` table set equals the writer-grant set; (f) audit isolation (`records_auditor` reads `audit_log` via SET ROLE; `records_api`/`records_intake_writer` cannot); (g) `records_auditor` has no grant/policy on `source_links` or any operational/reference table; (h) the FORCE-RLS negative-control (drop+recreate `p_audit_log_ins` inside a rolled-back savepoint, asserting the definer insert RAISES without it). Use `SET SESSION AUTHORIZATION` for mutating-identity checks. Return a `Tier`.

- [ ] **Step 3: Wire `tier6_posture` into `main`** after Tier 5 when `6 in db_wanted` and Tier 3 did not fail.

- [ ] **Step 4: Add `parse_tiers` `{0..6}` unit tests**; run `pytest test_run_validation_unit.py -v` -> PASS.

- [ ] **Step 5: Append MANIFEST rows 046-049** (filename, purpose, down, test, applied-to = dev disposable only).

- [ ] **Step 6: Full ladder** `run_validation.py --require-db` -> Tiers 0-6 PASS. Commit `feat(records): Tier 6 ownership+audit posture proofs (Gate 5)`.

---

### Task 6: Serving contract

**Files:**
- Create: `reference/records/SERVING_CONTRACT.yaml` + `reference/records/SERVING_CONTRACT.md`.
- Test: `reference/records/test_serving_contract.py` (or fold into an existing reference test) - schema/consistency check.

- [ ] **Step 1: Write `SERVING_CONTRACT.yaml`** - one entry per role with `connects: true|false`, `supabase_target` (for connecting roles), `tables_reachable`, `write_scope`, `policy_names` (from 045/048), and a top-level `dsn_form_inventory` listing the DSN shapes the future serving config is expected to use (keyword, URL userinfo, `postgresql+asyncpg://`, PG* env). `records_owner`/`records_fn_owner`: `connects: false`, owner-only, no DSN.

```yaml
# reference/records/SERVING_CONTRACT.yaml - Gate 9 consumes this for a
# mechanical records-role -> Supabase-boundary rebind. Not consumed by any
# runtime in Gate 5.
version: 1
roles:
  records_api:            { connects: true,  supabase_target: authenticated, write_scope: none,          policy_names: [p_<t>_read] }
  records_intake_writer:  { connects: true,  supabase_target: authenticated, write_scope: column_scoped, policy_names: [p_<t>_read, p_<t>_ins, p_<t>_upd] }
  records_auditor:        { connects: true,  supabase_target: authenticated, write_scope: none,          policy_names: [p_audit_log_sel] }
  records_owner:          { connects: false, owner_only: true, dsn: none }
  records_fn_owner:       { connects: false, owner_only: true, dsn: none }
drm_boundary:
  source_links_protects: lineage_provenance   # NOT the tolerance numeric values
  tolerance_values: first_class_record_content # in form_field_values; intentionally auditable
dsn_form_inventory: [keyword_user, url_userinfo, url_driver_qualified, pg_env_vars]
```
(Policy-name globs `p_<t>_*` expand per-table; the `.md` companion lists them explicitly.)

- [ ] **Step 2: Write `SERVING_CONTRACT.md`** - human companion: the invariant, the honest-scope caveat, the per-table policy names, and the Gate-9 rebind recipe.

- [ ] **Step 3: Write `test_serving_contract.py`** - parse the YAML; assert every `connects: true` role has a `supabase_target`; every `connects: false` role is `owner_only`/no-DSN; the `drm_boundary` + `dsn_form_inventory` keys exist. Assert `secret-audit.sh` Check-3 stays dormant (no `RECORDS_SERVING_GLOBS` default introduced).

- [ ] **Step 4: Run the test** -> PASS. Commit `docs(records): serving contract for Gate 9 (Gate 5)`.

---

### Task 7: Evidence doc + final wiring

**Files:**
- Create: `docs/operations/RECORDS-GATE5-EVIDENCE-2026-07.md`.
- Verify: `.github/workflows/records-ci.yml` runs Tiers 0-6 (via `--require-db`); add a Tier-6 note if the yaml pins an explicit tier set.

- [ ] **Step 1: Write the evidence doc** - AC1-AC11 -> the migration/test/transcript that satisfies each; the false-green negative-control transcript; the actor-attribution transcript; the down-reversibility transcript; the honest-scope + residual-superuser callout; DEV-7 auditor-retain note.
- [ ] **Step 2: Confirm CI** runs the full ladder incl. Tier 6; the AC8 fixture step stays.
- [ ] **Step 3: Commit** `docs(records): Gate 5 evidence + CI wiring`.

---

## Self-Review (author, against spec rev 3)

1. **Spec coverage:** AC1 (T1), AC2 (T1 FORCE teeth), AC3 (T5 Tier-6 (a)), AC4 (T4 trigger set + I/U + superuser DELETE), AC5 (T3 column-set + T4), AC6 (T3 negative control + three-assert), AC7 (T3 + T5 (f)/(g)), AC8 (T5 (b)/(c)/(d)), AC9 (T6), AC10 (every task's down + ASCII), AC11 (T4 actor attribution). G5-D1..D12 all land in T1-T5. Serving contract G5-D11 in T6. No gap found.
2. **Placeholder scan:** the only intentional glob is `p_<t>_*` policy-name shorthand (expanded in T6 Step 1/`.md`); `_dbtest.connect` helper name to be confirmed against `_dbtest.py` at T1 Step 4 (flagged inline). No TODO/TBD.
3. **Type consistency:** `fn_audit_capture()` no-arg function taking `TG_ARGV[0]` (trigger arg, not a function parameter) - consistent across 048 (definition) and 049 (CREATE TRIGGER ... EXECUTE FUNCTION records.fn_audit_capture('<pk>')). `actor_role`=`session_user`, `definer_role`=`current_user`, `actor_is_superuser` from `session_user` - consistent D6/AC11/T4. `records_auditor` LOGIN no-password + DEV-7 down - consistent 047/AC7/constraints.

## Execution Handoff

Plan complete. Two execution options:
1. **Subagent-Driven (recommended, the lane default - Gate 3 used it)** - fresh implementer subagent per task, task review (spec + quality) between tasks, broad whole-branch review + Codex cross-engine (the spec 5.3 gate) before merge.
2. **Inline execution** - batch with checkpoints.

Recommend option 1, opus for the security-critical tasks (1, 3, 4, 5), a cheaper tier for the mechanical ones (2, 6, 7).
