# Records Gate 3 Security/RLS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install and prove the records least-privilege role + RLS backstop: migration `045` (two LOGIN app roles, both-direction membership hardening, PUBLIC hygiene over tables+routines, a fully-enumerated column-scoped grant matrix, RLS `ENABLE`d on all 15 tables with `USING(true)` reference reads + role-scoped write-path policies, `security_invoker` views, all self-asserted in-migration), a reversible `_down`, and a non-superuser harness **Tier 5** that proves the boundary on a disposable DB.

**Architecture:** One additive, reversible SQL migration in the records series (`045`), mirroring the proven ops role-boundary `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (guarded/idempotent/self-asserting). A static Tier-3 paired test (`test_045`) + a dynamic **Tier 5** in `run_validation.py` (`SET SESSION AUTHORIZATION` proofs, savepoint discipline, one rolled-back transaction) prove it. D2-A: tables stay `postgres`-owned; `FORCE` inert on the superuser owner; the owner/superuser/BYPASSRLS path is closed by AC8 custody, not the migration.

**Tech Stack:** PostgreSQL 17; psycopg 3; pytest; the Gate-2 harness (`run_validation.py`, `_dbtest.py`). Host canonical repo only (local Windows checkouts are divergent).

## Global Constraints

- **Spec of record:** `docs/superpowers/specs/2026-07-02-records-gate3-security-rls-design.md` rev 6 (`a83701a3`). Every AC (AC1–AC8), decision (D1–D10), and proof (PP1–PP2, DP1–DP9, DP-ESC) is binding.
- **No passwords in SQL/code/logs/commits.** App-role passwords are operator-provisioned out-of-band; the migration never sets them.
- **Never target `records_dev`.** Every DSN passes `_dbtest.guard_target`. Tier 5 runs only on the disposable `records_val_*` DB.
- **Not applied to prod Supabase** (AC7). `045` is NOT Supabase-apply-ready as written (its `TO records_api/records_intake_writer` policies need a role-rebinding to `authenticated` — deferred to the serving/Gate-9 stage).
- **Reserved columns (never writer-grantable):** `assets.status`/`condition`; `form_submissions.status`/`reviewed_by`; `pm_events.status` (D9); `form_field_values.assessment` (D9); `persons.worker_class`/`employee_ref`/`match_adjudicated_by`/`match_adjudicated_at`/`match_confidence` (D9 + ratified).
- **`neta_table_source_links` is RESTRICTED (D10):** RLS-enabled, owner-only, NO app-role grant/policy.
- **Every records policy names explicit roles via `TO` — never `TO PUBLIC`.**
- **ASCII-only on added lines.** Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Down-migration checklist (F3), enforced at build-review (spec §5.3):** zero `DROP OWNED`; unconditional database-scoped revokes for both LOGIN roles; `all routines` (not `all functions`); guarded `DROP ROLE` (DEV-7 password guard); create-before-membership-revoke ordering in the up.
- **Gate-2 invariants preserved:** `guard_target`, admin-dbname=`postgres`, `records_val_*` allowlist, no hardcoded creds, unmasked exit codes, `_child_env`.

---

## File Structure

- **Create** `infra/database/migrations/records/045_records_security_rls.sql` — the migration (6 sections + in-migration asserts).
- **Create** `infra/database/migrations/records/045_records_security_rls_down.sql` — reversible teardown (checklist a–d).
- **Create** `infra/database/migrations/records/test_045_records_security_rls.py` — Tier-3 paired static test (schema-shape introspection at the 045 stack state).
- **Modify** `infra/database/migrations/records/run_validation.py` — add Tier 5 (`tier5_roles`), extend `parse_tiers` (×3) + the full-set guard + `db_wanted` + role snapshot/teardown.
- **Modify** `infra/database/migrations/records/test_run_validation_unit.py` — update `parse_tiers` unit tests for the `{0..5}` set.
- **Modify** `infra/database/migrations/records/test_043_neta_table_source_links.py` + `test_044_person_anchor.py` — comment-rescope the RLS-disabled assertions (stack-position-scoped; 045 flips the invariant by design).
- **Modify** `infra/database/migrations/records/MANIFEST.md` — add the 045 entry + note the post-045 RLS flip.
- **Create** `docs/operations/RECORDS-GATE3-EVIDENCE-2026-07.md` — AC verification transcript.
- **No change** to `records-ci.yml` — its final step already runs `run_validation.py --require-db` (the full ladder), which will include Tier 5 once it is in the default set. Verify in Task 5.

---

### Task 1: Migration `045` + paired static test

**Files:**
- Create: `infra/database/migrations/records/045_records_security_rls.sql`
- Create: `infra/database/migrations/records/test_045_records_security_rls.py`

**Interfaces:**
- Consumes: the records schema at the mig-044 stack state (15 tables, 2 views, 1 function, all `postgres`-owned, no RLS).
- Produces: roles `records_api` / `records_intake_writer`; RLS + policies on all 15 tables; `security_invoker` on both views; the grant matrix. `test_045` runs in the Tier-3 walk after 045 (introspection only; does not mutate → the walk's fingerprint-restoration assert holds trivially since RLS/policies/grants are outside the fingerprint).

- [ ] **Step 1: Write the failing test** `test_045_records_security_rls.py`

```python
# infra/database/migrations/records/test_045_records_security_rls.py
"""Tier-3 static posture test for migration 045 (records security/RLS).

Introspection only - no mutation - so it is safe inside the forward-incremental
walk and does not move the schema fingerprint. Dynamic denial/escalation proofs
live in run_validation.py Tier 5. Skips loudly when RECORDS_DEV_DSN is absent.
"""
import os
import sys

import psycopg
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

RESERVED = {
    "assets": {"status", "condition"},
    "form_submissions": {"status", "reviewed_by"},
    "pm_events": {"status"},
    "form_field_values": {"assessment"},
    "persons": {"worker_class", "employee_ref", "match_adjudicated_by",
                "match_adjudicated_at", "match_confidence"},
}
NOT_NULL_INVARIANT = [
    ("assets", "asset_tag"), ("assets", "name"),
    ("form_submissions", "template_id"), ("form_submissions", "asset_id"),
    ("form_field_values", "form_submission_id"), ("form_field_values", "field_key"),
    ("pm_schedules", "pm_program_id"), ("pm_schedules", "asset_id"),
    ("pm_events", "pm_schedule_id"), ("pm_events", "asset_id"),
    ("persons", "display_name"),
]
WRITE_PATH = ["assets", "form_submissions", "form_field_values", "pm_schedules", "pm_events", "persons"]


@pytest.fixture(scope="module")
def conn():
    c = psycopg.connect(_dbtest.dsn(), autocommit=True)
    yield c
    c.close()


def test_rls_enabled_on_all_records_tables(conn):
    rows = conn.execute(
        "select c.relname, c.relrowsecurity from pg_class c "
        "join pg_namespace n on n.oid=c.relnamespace "
        "where n.nspname='records' and c.relkind='r' order by 1"
    ).fetchall()
    off = [r[0] for r in rows if not r[1]]
    assert off == [], f"tables without RLS enabled: {off}"


def test_no_policy_is_public(conn):
    # pg_policies.roles renders as name[] e.g. {records_api,records_intake_writer};
    # a policy with no TO clause (PUBLIC) renders as {public}.
    pub = conn.execute(
        "select tablename, policyname, roles from pg_policies "
        "where schemaname='records' and (roles is null or 'public' = any(roles))"
    ).fetchall()
    assert pub == [], f"records policy granted TO PUBLIC: {pub}"


def test_no_public_execute_on_routines(conn):
    n = conn.execute(
        "select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace, "
        "lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
        "where ns.nspname='records' and a.grantee=0 and a.privilege_type='EXECUTE'"
    ).fetchone()[0]
    assert n == 0, "a records routine retains PUBLIC EXECUTE"


def test_reader_has_no_write(conn):
    for tbl in WRITE_PATH:
        for priv in ("INSERT", "UPDATE", "DELETE"):
            has = conn.execute(
                "select has_table_privilege('records_api', %s, %s)", (f"records.{tbl}", priv)
            ).fetchone()[0]
            assert not has, f"records_api unexpectedly holds {priv} on {tbl}"


def test_writer_holds_all_not_null_columns(conn):
    for tbl, col in NOT_NULL_INVARIANT:
        has = conn.execute(
            "select has_column_privilege('records_intake_writer', %s, %s, 'INSERT')",
            (f"records.{tbl}", col),
        ).fetchone()[0]
        assert has, f"records_intake_writer missing INSERT({col}) on {tbl} (would break real import)"


def test_writer_denied_reserved_columns(conn):
    for tbl, cols in RESERVED.items():
        for col in cols:
            for priv in ("INSERT", "UPDATE"):
                has = conn.execute(
                    "select has_column_privilege('records_intake_writer', %s, %s, %s)",
                    (f"records.{tbl}", col, priv),
                ).fetchone()[0]
                assert not has, f"records_intake_writer holds {priv}({col}) on {tbl} - reserved"


def test_views_are_security_invoker(conn):
    for v in ("v_asset_test_history", "v_pm_due"):
        opts = conn.execute(
            "select reloptions from pg_class c join pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname='records' and c.relname=%s", (v,)
        ).fetchone()[0]
        assert opts and any("security_invoker=" in o and o.split("=")[1] in ("true", "on", "1")
                            for o in opts), f"{v} is not security_invoker"


def test_source_links_restricted(conn):
    for role in ("records_api", "records_intake_writer"):
        has = conn.execute(
            "select has_table_privilege(%s, 'records.neta_table_source_links', 'SELECT')", (role,)
        ).fetchone()[0]
        assert not has, f"{role} holds SELECT on neta_table_source_links (D10 restricts it)"
```

- [ ] **Step 2: Run test to verify it fails**

Run (host, in the lane worktree): `python infra/database/migrations/records/run_validation.py --only 3 --db-dsn "<records_val_* dsn>"` after applying 001–044 — OR simpler, run the full ladder once 045 exists. Expected before 045 exists: the walk applies through 044, `test_045` has no migration so it is an orphan → `enumerate_stack` FAILs with "orphan test file(s)". So write the migration in the SAME task before running (TDD here means: write test asserting the posture, write migration, run the walk which pairs them). Interim check: `python -m pytest infra/database/migrations/records/test_045_records_security_rls.py -q` against a pre-045 `records_dev`-shaped disposable DB → FAILS `test_rls_enabled_on_all_records_tables` (RLS off).

- [ ] **Step 3: Write the migration** `045_records_security_rls.sql`

```sql
-- 045_records_security_rls.sql
-- Records Gate 3: least-privilege app roles + RLS backstop for schema records.
-- Spec: docs/superpowers/specs/2026-07-02-records-gate3-security-rls-design.md (rev 6).
-- Mirrors ops/012. Roles are CLUSTER-level; creation guarded, flags corrected
-- unconditionally, memberships revoked BOTH directions. Passwords set OUT-OF-BAND
-- by the operator - never here. NOT applied to prod Supabase (AC7); NOT Supabase-
-- apply-ready as written (TO <app-role> policies need role-rebinding to authenticated).
-- D2-A: tables stay postgres-owned; FORCE RLS inert on the superuser owner; the
-- owner/superuser/BYPASSRLS path is closed by AC8 custody, not this migration.

BEGIN;
SET client_encoding TO 'UTF8';

-- [1] Roles + flags + membership hardening (create BEFORE revoke) -------------------------
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_api') then create role records_api; end if;
  if not exists (select 1 from pg_roles where rolname='records_intake_writer') then create role records_intake_writer; end if;
end $$;

alter role records_api           with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role records_intake_writer with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;

do $$
declare m record;
begin
  for m in
    select granted.rolname as g, member.rolname as mm
    from pg_auth_members am
    join pg_roles granted on granted.oid = am.roleid
    join pg_roles member  on member.oid  = am.member
    where granted.rolname in ('records_api','records_intake_writer')
       or member.rolname  in ('records_api','records_intake_writer')
  loop
    execute format('revoke %I from %I', m.g, m.mm);
  end loop;
end $$;

do $$
declare r record;
begin
  for r in select rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolreplication
             from pg_roles where rolname in ('records_api','records_intake_writer') loop
    if r.rolsuper or r.rolcreatedb or r.rolcreaterole or r.rolbypassrls or r.rolreplication then
      raise exception '045 posture: % holds a privileged flag', r.rolname;
    end if;
    if not r.rolcanlogin then raise exception '045 posture: % must be LOGIN', r.rolname; end if;
  end loop;
  if (select count(*) from pg_roles where rolname in ('records_api','records_intake_writer')) <> 2 then
    raise exception '045 posture: expected both app roles present';
  end if;
  if exists (select 1 from pg_auth_members am join pg_roles a on a.oid in (am.roleid, am.member)
             where a.rolname in ('records_api','records_intake_writer')) then
    raise exception '045 posture: an app role retains a role membership (escalation path)';
  end if;
end $$;

-- [2] PUBLIC hygiene (tables + routines) -------------------------------------------------
revoke create on schema public from public;               -- database-scoped; no-op vs PG15+ default
revoke execute on all routines in schema records from public;
grant usage on schema records to records_api, records_intake_writer;

do $$
declare n int;
begin
  select count(*) into n
  from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace,
       lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
  where ns.nspname='records' and a.grantee=0 and a.privilege_type='EXECUTE';
  if n > 0 then raise exception '045 posture: % records routine(s) retain PUBLIC EXECUTE', n; end if;
end $$;

-- [3] Grant matrix -----------------------------------------------------------------------
-- records_api: SELECT on the 8 reference + 6 write-path tables + 2 views. NOT source_links (D10).
grant select on
  records.asset_classes, records.form_templates, records.pm_programs,
  records.neta_procedures, records.neta_test_items, records.neta_tables,
  records.asset_class_neta_procedure, records.neta_procedure_xref,
  records.assets, records.form_submissions, records.form_field_values,
  records.pm_schedules, records.pm_events, records.persons,
  records.v_asset_test_history, records.v_pm_due
  to records_api;

-- records_intake_writer: SELECT on the same 14 tables (not the views, not source_links).
grant select on
  records.asset_classes, records.form_templates, records.pm_programs,
  records.neta_procedures, records.neta_test_items, records.neta_tables,
  records.asset_class_neta_procedure, records.neta_procedure_xref,
  records.assets, records.form_submissions, records.form_field_values,
  records.pm_schedules, records.pm_events, records.persons
  to records_intake_writer;

-- Column-scoped INSERT/UPDATE per write-path table (all columns minus reserved minus
-- auto-populated PK/created_at/updated_at). Reserved cols carry defaults/nullable so INSERT
-- omitting them succeeds; every NOT-NULL/no-default column is included (build-time invariant).
grant insert (asset_tag, name, asset_class_id, parent_asset_id, site_ref, client_ref,
  location_label, region, jobsite, plant, substation, gps_lat, gps_long, manufacturer, model,
  serial_number, rated_voltage, rated_current, year_manufactured, last_tested_at, apparatus_ref,
  equipment_model_id, source, provenance_status, legacy_source_id, notes),
  update (asset_tag, name, asset_class_id, parent_asset_id, site_ref, client_ref, location_label,
  region, jobsite, plant, substation, gps_lat, gps_long, manufacturer, model, serial_number,
  rated_voltage, rated_current, year_manufactured, last_tested_at, apparatus_ref, equipment_model_id,
  source, provenance_status, legacy_source_id, notes)
  on records.assets to records_intake_writer;

grant insert (template_id, asset_id, project_ref, work_package_ref, pm_event_id, overall_assessment,
  as_found_as_left, test_status_label, job_number, test_date, technician, ambient_temp_c,
  relative_humidity, test_equipment, summary_notes, source, provenance_status, legacy_source_id,
  origin_device, client_rev, client_captured_at, synced_at, neta_standard, technician_person_id),
  update (template_id, asset_id, project_ref, work_package_ref, pm_event_id, overall_assessment,
  as_found_as_left, test_status_label, job_number, test_date, technician, ambient_temp_c,
  relative_humidity, test_equipment, summary_notes, source, provenance_status, legacy_source_id,
  origin_device, client_rev, client_captured_at, synced_at, neta_standard, technician_person_id)
  on records.form_submissions to records_intake_writer;

grant insert (form_submission_id, field_key, field_label, test_group, sequence_no, value_kind,
  value_numeric, value_text, value_boolean, unit, expected_value, min_acceptable, max_acceptable,
  measured_at, notes, origin_device, client_rev, client_captured_at, synced_at),
  update (form_submission_id, field_key, field_label, test_group, sequence_no, value_kind,
  value_numeric, value_text, value_boolean, unit, expected_value, min_acceptable, max_acceptable,
  measured_at, notes, origin_device, client_rev, client_captured_at, synced_at)
  on records.form_field_values to records_intake_writer;

grant insert (pm_program_id, asset_id, last_performed_at, next_due_at, is_active, notes),
  update (pm_program_id, asset_id, last_performed_at, next_due_at, is_active, notes)
  on records.pm_schedules to records_intake_writer;

grant insert (pm_schedule_id, asset_id, scheduled_for, performed_at, form_submission_id,
  project_ref, outcome, notes, origin_device, client_rev, client_captured_at, synced_at),
  update (pm_schedule_id, asset_id, scheduled_for, performed_at, form_submission_id,
  project_ref, outcome, notes, origin_device, client_rev, client_captured_at, synced_at)
  on records.pm_events to records_intake_writer;

grant insert (display_name), update (display_name)
  on records.persons to records_intake_writer;

-- [3a] posture asserts: 11 NOT-NULL columns present; reserved cols absent; reader no-write.
do $$
declare
  nn  text[][] := array[['assets','asset_tag'],['assets','name'],
    ['form_submissions','template_id'],['form_submissions','asset_id'],
    ['form_field_values','form_submission_id'],['form_field_values','field_key'],
    ['pm_schedules','pm_program_id'],['pm_schedules','asset_id'],
    ['pm_events','pm_schedule_id'],['pm_events','asset_id'],['persons','display_name']];
  res text[][] := array[['assets','status'],['assets','condition'],
    ['form_submissions','status'],['form_submissions','reviewed_by'],
    ['pm_events','status'],['form_field_values','assessment'],
    ['persons','worker_class'],['persons','employee_ref'],['persons','match_adjudicated_by'],
    ['persons','match_adjudicated_at'],['persons','match_confidence']];
  i int; wp text;
begin
  for i in 1 .. array_length(nn,1) loop
    if not has_column_privilege('records_intake_writer', format('records.%I', nn[i][1]), nn[i][2], 'INSERT') then
      raise exception '045 posture: writer missing INSERT(%) on %', nn[i][2], nn[i][1];
    end if;
  end loop;
  for i in 1 .. array_length(res,1) loop
    if has_column_privilege('records_intake_writer', format('records.%I', res[i][1]), res[i][2], 'INSERT')
       or has_column_privilege('records_intake_writer', format('records.%I', res[i][1]), res[i][2], 'UPDATE') then
      raise exception '045 posture: writer holds reserved %.%', res[i][1], res[i][2];
    end if;
  end loop;
  foreach wp in array array['assets','form_submissions','form_field_values','pm_schedules','pm_events','persons'] loop
    if has_table_privilege('records_api', format('records.%I', wp), 'INSERT')
       or has_table_privilege('records_api', format('records.%I', wp), 'UPDATE')
       or has_table_privilege('records_api', format('records.%I', wp), 'DELETE') then
      raise exception '045 posture: records_api holds a write on %', wp;
    end if;
  end loop;
  if has_table_privilege('records_api', 'records.neta_table_source_links', 'SELECT')
     or has_table_privilege('records_intake_writer', 'records.neta_table_source_links', 'SELECT') then
    raise exception '045 posture: an app role holds SELECT on neta_table_source_links (D10)';
  end if;
end $$;

-- [4] RLS: enable on all 15 tables; reference USING(true); write-path role-scoped; restrict source_links.
-- (Generated per-table so the list stays in one place; every policy names explicit roles.)
do $$
declare
  ref text[] := array['asset_classes','form_templates','pm_programs','neta_procedures',
    'neta_test_items','neta_tables','asset_class_neta_procedure','neta_procedure_xref'];
  wp  text[] := array['assets','form_submissions','form_field_values','pm_schedules','pm_events','persons'];
  t text;
begin
  foreach t in array (ref || wp || array['neta_table_source_links']) loop
    execute format('alter table records.%I enable row level security', t);
  end loop;
  foreach t in array ref loop
    execute format('drop policy if exists p_%1$s_read on records.%1$s', t);
    execute format('create policy p_%1$s_read on records.%1$s for select to records_api, records_intake_writer using (true)', t);
  end loop;
  foreach t in array wp loop
    execute format('drop policy if exists p_%1$s_read on records.%1$s', t);
    execute format('create policy p_%1$s_read on records.%1$s for select to records_api, records_intake_writer using (true)', t);
    execute format('drop policy if exists p_%1$s_ins on records.%1$s', t);
    execute format('create policy p_%1$s_ins on records.%1$s for insert to records_intake_writer with check (true)', t);
    execute format('drop policy if exists p_%1$s_upd on records.%1$s', t);
    execute format('create policy p_%1$s_upd on records.%1$s for update to records_intake_writer using (true) with check (true)', t);
  end loop;
  -- neta_table_source_links: RLS enabled, NO app-role policy (D10 owner-only).
end $$;

do $$
begin
  if exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
             where n.nspname='records' and c.relkind='r' and not c.relrowsecurity) then
    raise exception '045 posture: a records table has RLS disabled';
  end if;
  -- every records policy must name explicit non-PUBLIC roles (F6)
  if exists (select 1 from pg_policies where schemaname='records'
             and (roles is null or 'public' = any(roles))) then
    raise exception '045 posture: a records policy is TO PUBLIC';
  end if;
end $$;

-- [5] Views: security_invoker so base-table RLS applies to the caller. -------------------
alter view records.v_asset_test_history set (security_invoker = true);
alter view records.v_pm_due set (security_invoker = true);

do $$
begin
  if exists (
    select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='records' and c.relkind='v'
      and not exists (select 1 from pg_options_to_table(c.reloptions) o
                      where o.option_name='security_invoker' and lower(o.option_value) in ('true','on','1'))
  ) then
    raise exception '045 posture: a records view is not security_invoker';
  end if;
end $$;

COMMIT;
```

- [ ] **Step 4: Run the full ladder to pair migration + test**

Run (host lane worktree, with `RECORDS_PG_ADMIN_DSN` + `NETA_DATA_DIR` exported per the Gate-2 runbook):
```bash
export PATH=$HOME/.local/bin:$PATH
python infra/database/migrations/records/run_validation.py --only 3 --db-dsn "$(build a records_val_* dsn)"   # or full ladder
```
Expected: Tier 3 applies 001→045; `test_045` runs after 045 and PASSES all 8 assertions; the fingerprint-restoration assert holds (045 posture is outside the fingerprint). Note: `--only 3` needs an explicit `--db-dsn`; easiest is the full ladder (Task 3 wires Tier 5 into it).

- [ ] **Step 5: Commit**

```bash
git add infra/database/migrations/records/045_records_security_rls.sql \
        infra/database/migrations/records/test_045_records_security_rls.py
git commit -m "feat(records): 045 security/RLS migration + Tier-3 static test"
```

---

### Task 2: Reversible `045_down` + down test

**Files:**
- Create: `infra/database/migrations/records/045_records_security_rls_down.sql`
- Add to `test_045_records_security_rls.py`: a down-symmetry check run manually (or a dedicated test invoked outside the forward walk).

**Interfaces:** Consumes a post-045 DB; produces the pre-045 posture (RLS off, no policies, PUBLIC EXECUTE restored, app-role grants revoked, roles dropped only when password-less).

- [ ] **Step 1: Write the down migration**

```sql
-- 045_records_security_rls_down.sql
-- Restores the pre-045 posture. Ladder symmetry, NOT a security recommendation.
-- Checklist (spec 5.3): zero DROP OWNED (both app roles are LOGIN; DROP OWNED would strip
-- shared pg_database CONNECT cluster-wide, ops-012 F-012-3); database-scoped revokes run
-- UNCONDITIONALLY; all routines (not all functions); guarded DROP ROLE (DEV-7 password guard).

BEGIN;
SET client_encoding TO 'UTF8';

-- [d1] drop policies + disable RLS on all 15 tables
do $$
declare t text;
begin
  foreach t in array array['asset_classes','form_templates','pm_programs','neta_procedures',
    'neta_test_items','neta_tables','asset_class_neta_procedure','neta_procedure_xref',
    'assets','form_submissions','form_field_values','pm_schedules','pm_events','persons',
    'neta_table_source_links'] loop
    execute format('drop policy if exists p_%1$s_read on records.%1$s', t);
    execute format('drop policy if exists p_%1$s_ins on records.%1$s', t);
    execute format('drop policy if exists p_%1$s_upd on records.%1$s', t);
    execute format('alter table records.%I disable row level security', t);
  end loop;
end $$;

-- [d2] revert views to definer (non-invoker)
alter view records.v_asset_test_history reset (security_invoker);
alter view records.v_pm_due reset (security_invoker);

-- [d3] restore pre-up PUBLIC EXECUTE on records routines
grant execute on all routines in schema records to public;

-- [d4] database-scoped grant revokes for BOTH LOGIN roles, UNCONDITIONAL (posture restored
-- even when [d5] retains the role object). NO DROP OWNED (F-012-3).
do $$
declare r text;
begin
  foreach r in array array['records_api','records_intake_writer'] loop
    if exists (select 1 from pg_roles where rolname=r) then
      execute format('revoke all privileges on all tables in schema records from %I', r);
      execute format('revoke all privileges on all routines in schema records from %I', r);
      execute format('revoke usage on schema records from %I', r);
    end if;
  end loop;
end $$;

-- [d5] guarded DROP ROLE: never drop a role carrying an out-of-band password (DEV-7); tolerate
-- cross-DB dependencies (leave in place). Password-less disposable-DB roles drop cleanly.
do $$
declare r text;
begin
  foreach r in array array['records_api','records_intake_writer'] loop
    if exists (select 1 from pg_roles where rolname=r) then
      if exists (select 1 from pg_authid where rolname=r and rolpassword is not null) then
        raise notice '045_down: role % has an out-of-band password; left in place (DEV-7)', r;
        continue;
      end if;
      begin
        execute format('drop role %I', r);
      exception when dependent_objects_still_exist then
        raise notice '045_down: role % retains dependencies in another database; left in place', r;
      end;
    end if;
  end loop;
end $$;

COMMIT;
```

- [ ] **Step 2: Verify down restores pre-up posture** — apply 045, then 045_down, on a disposable DB; assert RLS off on all tables, zero records policies, no `records_*` grants, PUBLIC EXECUTE back on `fn_set_updated_at`, and (password-less) roles dropped. Run via a scratch psql sequence or a one-off pytest; confirm `git show --check`.

- [ ] **Step 3: Commit** `feat(records): 045 reversible down (checklist a-d)`.

---

### Task 3: Harness Tier 5 (`run_validation.py`) + unit tests

**Files:**
- Modify: `infra/database/migrations/records/run_validation.py`
- Modify: `infra/database/migrations/records/test_run_validation_unit.py`

**Interfaces:** Consumes the migrated disposable DB (post-Tier-3, roles created by 045) + the admin DSN. Produces `Tier("5-roles", …)`; drops harness-created roles in `finally`.

- [ ] **Step 1: Extend `parse_tiers` (×3) + the full-set guard (×1)**

In `parse_tiers`: default `return {0,1,2,3,4,5}`; `unknown = wanted - {0,1,2,3,4,5}`; error strings `(valid: 0-5)` and `tiers 0-5`. In `main()`: `db_wanted = wanted & {3,4,5}`; and the guard `if wanted != {0, 1, 2, 3, 4, 5}:` (the full-ladder set — else a default run trips "requires --db-dsn").

- [ ] **Step 2: Add `tier5_roles` + role snapshot/teardown**

Snapshot before the walk (right after `admin` is read, before CREATE DATABASE):
```python
def snapshot_roles(admin, names=("records_api", "records_intake_writer")):
    with _connect(admin) as c:
        existing = {r[0] for r in c.execute(
            "select rolname from pg_roles where rolname = any(%s)", (list(names),)).fetchall()}
    return [n for n in names if n not in existing]   # roles 045 will create THIS run
```
`tier5_roles` (one non-autocommit connection; seed as superuser; SET SESSION AUTHORIZATION proofs with savepoint discipline; everything rolled back):
```python
ROGUE = "records_val_rogue"  # run-scoped suffix appended from val_name's stamp

def _expect_raise(cur, sql, label):
    cur.execute("savepoint p")
    try:
        cur.execute(sql)
        cur.execute("rollback to savepoint p")
        return f"DID NOT RAISE: {label}"
    except psycopg.errors.Error:
        cur.execute("rollback to savepoint p")
        return None

def tier5_roles(child_dsn, val_name):
    import psycopg
    rogue = f"records_val_rogue_{val_name.split('records_val_')[1]}"
    assert re.fullmatch(r"records_val_rogue_\d{8}T\d{6}_\d+", rogue), rogue
    fails = []
    conn = psycopg.connect(child_dsn, autocommit=True)
    try:
        # static asserts (DP7/DP8 + reader/writer boundary sampled; full matrix is test_045)
        if conn.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                        "where n.nspname='records' and c.relkind='r' and not c.relrowsecurity").fetchone()[0]:
            fails.append("DP7 a records table has RLS disabled")
        # DP-ESC (a): reader cannot SET ROLE writer (faithful, not superuser-masked)
        conn.execute("set session authorization records_api")
        try:
            conn.execute("set role records_intake_writer"); fails.append("DP-ESC reader escalated to writer")
        except psycopg.errors.Error:
            pass
        conn.execute("reset session authorization")
    finally:
        conn.close()
    # dynamic proofs in ONE rolled-back transaction (savepoint discipline)
    conn = psycopg.connect(child_dsn)   # autocommit=False
    try:
        cur = conn.cursor()
        cur.execute(f"create role {rogue} nosuperuser nologin nobypassrls")
        # seed a JOIN-satisfying set for the view positive-control (rolled back with the txn)
        cur.execute("insert into records.asset_classes(class_code,name) values('t5','Tier5') returning asset_class_id")
        acid = cur.fetchone()[0]
        cur.execute("insert into records.assets(asset_tag,name,asset_class_id) values('T5','t5',%s) returning asset_id", (acid,))
        aid = cur.fetchone()[0]
        cur.execute("insert into records.form_templates(template_code,title,asset_class_id) values('t5','t5',%s) returning template_id", (acid,))
        tid = cur.fetchone()[0]
        cur.execute("insert into records.form_submissions(template_id,asset_id) values(%s,%s)", (tid, aid))
        # PP2: writer creates a draft (status defaults)
        cur.execute("set session authorization records_intake_writer")
        cur.execute("savepoint w")
        cur.execute("insert into records.form_submissions(template_id,asset_id) values(%s,%s)", (tid, aid))
        cur.execute("select status from records.form_submissions order by created_at desc limit 1")
        if cur.fetchone()[0] != "draft":
            fails.append("PP2 writer insert did not default status to draft")
        # DP2: writer cannot set status/reviewed_by
        fails += list(filter(None, [
            _expect_raise(cur, f"update records.form_submissions set status='approved' where form_submission_id in (select form_submission_id from records.form_submissions limit 1)", "DP2 status"),
            _expect_raise(cur, "update records.persons set worker_class='1099' where false", "DP2/D9 worker_class"),
        ]))
        cur.execute("reset session authorization")
        # DP9 positive control + rogue denial through the view
        cur.execute("set session authorization records_api")
        cur.execute("select count(*) from records.v_asset_test_history")
        if cur.fetchone()[0] < 1:
            fails.append("DP9 positive control: records_api sees 0 rows through the view (join empty)")
        cur.execute("reset session authorization")
        cur.execute(f"grant usage on schema records to {rogue}")
        cur.execute(f"grant select on records.v_asset_test_history, records.assets, records.form_submissions, records.form_templates to {rogue}")
        cur.execute(f"set session authorization {rogue}")
        cur.execute("select count(*) from records.v_asset_test_history")
        if cur.fetchone()[0] != 0:
            fails.append("DP9 rogue saw rows through the security_invoker view (RLS leak)")
        cur.execute("reset session authorization")
    finally:
        conn.rollback()   # undoes rogue role + grants + seeds
        conn.close()
    status = "FAIL" if fails else "PASS"
    return Tier("5-roles", status, "; ".join(fails) if fails else "role/grant/denial proofs green")
```
Wire the call in `main()` inside the inner `try`, after the tier4 block, gated on tier 3 not FAILed:
```python
if 5 in db_wanted and not any(t.name=="3-migrations" and t.status=="FAIL" for t in tiers):
    if 3 in db_wanted or args.db_dsn:
        tiers.append(tier5_roles(child_dsn, val_name or _dbtest.dsn_params(child_dsn).get("dbname")))
    else:
        tiers.append(Tier("5-roles","SKIP","no migrated target"))
elif 5 in db_wanted:
    tiers.append(Tier("5-roles","SKIP","tier 3 failed"))
```
In the `finally`, AFTER the DB drop, drop harness-created roles (guarded):
```python
for role in created_roles:   # from snapshot_roles(), only roles this run created
    try:
        with _connect(admin) as c:
            has_pw = c.execute("select rolpassword is not null from pg_authid where rolname=%s", (role,)).fetchone()
            if has_pw and has_pw[0]:
                print(f"[keep-role] {role} carries a password; left in place"); continue
            c.execute(f'drop role if exists "{role}"')
            print(f"[drop-role] {role}")
    except Exception as e:
        print(f"[keep-role] {role}: {e}")
```

- [ ] **Step 3: Update `test_run_validation_unit.py`** — `parse_tiers("")` returns `{0,1,2,3,4,5}`; `parse_tiers("5")` returns `{5}`; `parse_tiers("9")` raises `HarnessError` with "valid: 0-5"; `parse_tiers("3,5")` returns `{3,5}`.

- [ ] **Step 4: Run** the harness unit tests + the full ladder; expect Tier 5 PASS. **Step 5: Commit** `feat(records): run_validation Tier 5 (role/grant/denial proofs)`.

---

### Task 4: Comment-rescope test_043/044 + MANIFEST

- [ ] Add a one-line comment above `test_043` `test_rls_disabled` (line ~115) and `test_044` `test_rls_disabled_on_persons` (line ~56): `# Stack-position assertion (mig 043/044): valid through mig 044; migration 045 (Gate 3) enables RLS by design. Run via the incremental runner, not standalone against a post-045 records_dev.` No logic change.
- [ ] Add the `045` entry to `MANIFEST.md` (roles/RLS/grants summary) and note the post-044 RLS-flip.
- [ ] Commit `docs(records): note post-045 RLS flip in test_043/044 + MANIFEST`.

---

### Task 5: Evidence doc + CI confirmation + AC verification

- [ ] Confirm `records-ci.yml` needs no change: its final step `python … run_validation.py --require-db` now runs Tiers 0→5 (Tier 5 is in the default set). Verify the CI harness-unit-test step still passes with the updated `parse_tiers`.
- [ ] Create `docs/operations/RECORDS-GATE3-EVIDENCE-2026-07.md` — capture: the full-ladder transcript (Tiers 0–5 PASS on a disposable `records_val_*`), the `test_045` assertions, the down-symmetry check, and an AC1–AC8 checklist mapping each AC to its proof. Confirm `records_dev` appears in no connection line and the disposable DB + created roles were dropped.
- [ ] Commit `docs(records): Gate 3 AC evidence`.

---

## Self-Review (author checklist, run before execution)

- **Spec coverage:** AC1 (Task 1 §[4]); AC2 (Task 1 §[2a] + test_045); AC3 (Task 1 §[3a] + test_045 + Tier 5 DP1–DP4/DP-ESC); AC4 (Task 1 §[5] + Tier 5 DP9); AC5 (Tier 5 PP1–PP2); AC6 (Task 3 + Task 5); AC7 (no prod apply — Global Constraints); AC8 (Global Constraints + Task 5 evidence names `secret-audit.sh`). D9/D10 encoded in RESERVED + the D10 restriction.
- **Type/name consistency:** policy names `p_<table>_{read,ins,upd}` identical in up + down; role names `records_api`/`records_intake_writer` throughout; `created_roles` produced by `snapshot_roles` and consumed in `finally`.
- **Build-review gate (spec §5.3):** the whole-branch review MUST re-audit the down checklist (a–d), the non-PUBLIC `polroles` preservation, and read `infra/secret-audit.sh` for the AC8 patterns.

## Execution Handoff

Plan complete. Two execution options: **(1) Subagent-Driven (recommended)** — fresh subagent per task + two-stage review, on the host lane worktree; **(2) Inline** — executing-plans with checkpoints. Recommend (1). After the build: mandatory whole-branch review + a Codex cross-engine pass (the spec §5.3 re-audit gate) before any merge; not applied to prod Supabase.
