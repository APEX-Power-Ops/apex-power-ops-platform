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

-- [2] PUBLIC hygiene (tables + routines + schema) ----------------------------------------
revoke create on schema public from public;               -- database-scoped; no-op vs PG15+ default
revoke all privileges on all tables in schema records from public;
revoke execute on all routines in schema records from public;
revoke usage on schema records from public;                -- no-op (records nspacl null); explicit
grant usage on schema records to records_api, records_intake_writer;

-- [2a] posture assert: PUBLIC holds NOTHING on records routines, tables/views, or the schema.
-- Materialized default ACL so a NULL acl (the implicit default PUBLIC grant) is not a false-green.
do $$
begin
  if exists (select 1 from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace,
             lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
             where ns.nspname='records' and a.grantee=0 and a.privilege_type='EXECUTE') then
    raise exception '045 posture: PUBLIC retains EXECUTE on a records routine';
  end if;
  if exists (select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace,
             lateral aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a
             where n.nspname='records' and c.relkind in ('r','v') and a.grantee=0) then
    raise exception '045 posture: PUBLIC holds a grant on a records table/view';
  end if;
  if exists (select 1 from pg_namespace n,
             lateral aclexplode(coalesce(n.nspacl, acldefault('n', n.nspowner))) a
             where n.nspname='records' and a.grantee=0) then
    raise exception '045 posture: PUBLIC holds a privilege on schema records';
  end if;
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
