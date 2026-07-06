-- 045_records_security_rls.sql
-- Records Gate 3: least-privilege app roles + RLS backstop for schema records.
-- Spec: docs/superpowers/specs/2026-07-02-records-gate3-security-rls-design.md (rev 6).
-- Mirrors ops/012. Roles are CLUSTER-level; creation guarded, flags corrected
-- unconditionally, memberships revoked BOTH directions. Passwords set OUT-OF-BAND
-- by the operator - never here.
--
-- SUPABASE-COMPAT (compat lane Task 2.1, plan REV 5/5.1): adapted to apply as the
-- NON-SUPER managed postgres applier.
--   * Role attrs: the NOSUPERUSER keyword is DROPPED (setting it needs superuser ->
--     42501; roles are already non-super by default) and replaced by a rolsuper=false
--     assert. The other NO* attrs (nobypassrls/noreplication/nocreatedb/nocreaterole)
--     are settable by non-super postgres (Phase-0 A2) and are KEPT.
--   * Policy binding stays TO records_api, records_intake_writer (Phase-0 Gate B:
--     CREATE POLICY ... TO <custom role> succeeds). The historical "rebind to
--     authenticated" note is superseded and kept here as DOCUMENTATION only.
--   * Membership assert (D-A trusted-applier): flags a pg_auth_members row only when
--     the edge is USABLE (set_option OR inherit_option) AND the member is a non-admin
--     role (member <> postgres). The trusted applier's admin-only creator edge (set=
--     inherit=false) and the postgres identity are EXEMPT; the non-admin app roles
--     stay isolated.
--   * Owner-aware (D-B rev 5.1): records objects are owned at rest by EITHER the
--     applier identity (postgres on managed Supabase; the disposable applier locally -
--     the FRESH case, 046 has not run) OR records_reclaim_owner (a RE-UP after a prior
--     046_down). A uniform-owner PRE-CHECK asserts a single owner in {applier, reclaim}
--     and fails loud otherwise; the object-level owner-requiring DDL (RLS enable, policy
--     create, the grant matrix, security_invoker views, records schema/PUBLIC grants)
--     runs AS that at-rest owner (directly when applier-owned; under SET ROLE
--     records_reclaim_owner via a transient WITH SET grant on a re-up). Role creation +
--     role-attr work always runs as the applier identity.

BEGIN;
SET client_encoding TO 'UTF8';

-- [1] Roles + flags + membership hardening (create BEFORE revoke) -------------------------
-- Runs as the applier identity (postgres on managed Supabase). NOSUPERUSER dropped.
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_api') then create role records_api; end if;
  if not exists (select 1 from pg_roles where rolname='records_intake_writer') then create role records_intake_writer; end if;
end $$;

alter role records_api           with login nocreatedb nocreaterole nobypassrls noreplication;
alter role records_intake_writer with login nocreatedb nocreaterole nobypassrls noreplication;

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
    -- rolsuper=false is the compat-lane replacement for the dropped NOSUPERUSER keyword.
    if r.rolsuper or r.rolcreatedb or r.rolcreaterole or r.rolbypassrls or r.rolreplication then
      raise exception '045 posture: % holds a privileged flag', r.rolname;
    end if;
    if not r.rolcanlogin then raise exception '045 posture: % must be LOGIN', r.rolname; end if;
  end loop;
  if (select count(*) from pg_roles where rolname in ('records_api','records_intake_writer')) <> 2 then
    raise exception '045 posture: expected both app roles present';
  end if;
  -- D-A trusted-applier: an app role must hold NO USABLE membership edge (set_option OR
  -- inherit_option) to/from a NON-admin role. The applier's admin-only creator edge
  -- (set=inherit=false) and the trusted postgres identity are EXEMPT (they cannot be
  -- constrained in-migration and are custody-controlled); the app roles stay isolated
  -- from every other non-admin role.
  if exists (
    select 1 from pg_auth_members am
    join pg_roles a on a.oid = am.roleid
    join pg_roles b on b.oid = am.member
    where (a.rolname in ('records_api','records_intake_writer')
           or b.rolname in ('records_api','records_intake_writer'))
      and (am.set_option or am.inherit_option)
      and am.member <> 'postgres'::regrole
  ) then
    raise exception '045 posture: an app role retains a usable role membership (escalation path)';
  end if;
end $$;

-- [owner-pre] Uniform-owner PRE-CHECK (D-B rev 5.1) + enter owner context ------------------
-- Assert EVERY records object (schema + all classes + all routines) is owned by EXACTLY
-- ONE role, and that role is the applier identity (the FRESH case) OR records_reclaim_owner
-- (a RE-UP after 046_down). Fail LOUD on mixed/other ownership (a single-table probe would
-- false-green a botched transfer). On a reclaim re-up, grant the applier a transient WITH SET
-- membership so the owner-requiring DDL below can SET ROLE into records_reclaim_owner.
do $$
declare
  owner_oids oid[];
  v_owner_oid oid;
  v_owner text;
  v_me_oid oid;
begin
  -- current_user's OID by exact name lookup (never current_user::regrole - a text->regrole
  -- cast LOWERCASES an unquoted mixed-case name and would fail 42704 on the applier's name).
  select oid into v_me_oid from pg_roles where rolname = current_user;
  -- Compare by OID (not ::regrole::text, which quotes mixed-case names).
  select array_agg(distinct o) into owner_oids from (
    select nspowner as o from pg_namespace where nspname='records'
    union all
    select relowner from pg_class c join pg_namespace n on n.oid=c.relnamespace
      where n.nspname='records' and c.relkind in ('r','v','S','p')
    union all
    select proowner from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='records'
  ) s;
  if array_length(owner_oids,1) is null then
    raise exception '045 owner pre-check: no records objects found (schema not applied)';
  end if;
  if array_length(owner_oids,1) <> 1 then
    raise exception '045 owner pre-check: records objects have MIXED owners %, expected exactly one',
      (select array_agg(pg_get_userbyid(x)) from unnest(owner_oids) x);
  end if;
  v_owner_oid := owner_oids[1];
  v_owner := pg_get_userbyid(v_owner_oid);
  if v_owner_oid <> v_me_oid
     and v_owner_oid is distinct from to_regrole('records_reclaim_owner')::oid then
    raise exception '045 owner pre-check: unexpected at-rest owner % (expected the applier % or records_reclaim_owner)',
      v_owner, current_user;
  end if;
  if v_owner = 'records_reclaim_owner' and v_owner_oid <> v_me_oid then
    -- RE-UP: the applier does not own the objects; take transient WITH SET membership
    -- so the owner-DDL block can SET ROLE into the at-rest owner. Revoked in [owner-post].
    execute format('grant records_reclaim_owner to %I with set true, inherit false, admin false', current_user);
  end if;
end $$;

-- [owner-ddl] All owner-requiring records DDL, run AS the at-rest owner --------------------
-- Consolidated under one SET ROLE bracket. When the applier already owns the objects
-- (fresh), SET ROLE <applier> is a no-op-equivalent; on a reclaim re-up, SET ROLE
-- records_reclaim_owner (transient membership granted above) confers owner authority.
-- Contains: [2] records PUBLIC hygiene + schema USAGE grant; [3] grant matrix; [4] RLS
-- enable + policy create; [5] security_invoker views. Public-schema hygiene stays OUTSIDE
-- the bracket (it is db/public-schema scoped, not records-owner scoped).
do $$
declare
  v_owner text;
  ref text[] := array['asset_classes','form_templates','pm_programs','neta_procedures',
    'neta_test_items','neta_tables','asset_class_neta_procedure','neta_procedure_xref'];
  wp  text[] := array['assets','form_submissions','form_field_values','pm_schedules','pm_events','persons'];
  t text;
begin
  select pg_get_userbyid(nspowner) into v_owner from pg_namespace where nspname='records';
  execute format('set role %I', v_owner);

  -- [2] PUBLIC hygiene on records objects + schema USAGE grant (owner-required).
  execute 'revoke all privileges on all tables in schema records from public';
  execute 'revoke execute on all routines in schema records from public';
  execute 'revoke usage on schema records from public';
  execute 'grant usage on schema records to records_api, records_intake_writer';

  -- [3] Grant matrix -----------------------------------------------------------------------
  -- Authoritative, not additive: REVOKE ALL first so any stale grant is cleared.
  execute 'revoke all privileges on all tables in schema records from records_api, records_intake_writer';
  execute 'revoke all privileges on all routines in schema records from records_api, records_intake_writer';

  -- records_api: SELECT on the 8 reference + 6 write-path tables + 2 views. NOT source_links (D10).
  execute 'grant select on '
    'records.asset_classes, records.form_templates, records.pm_programs, '
    'records.neta_procedures, records.neta_test_items, records.neta_tables, '
    'records.asset_class_neta_procedure, records.neta_procedure_xref, '
    'records.assets, records.form_submissions, records.form_field_values, '
    'records.pm_schedules, records.pm_events, records.persons, '
    'records.v_asset_test_history, records.v_pm_due '
    'to records_api';

  -- records_intake_writer: SELECT on the same 14 tables (not the views, not source_links).
  execute 'grant select on '
    'records.asset_classes, records.form_templates, records.pm_programs, '
    'records.neta_procedures, records.neta_test_items, records.neta_tables, '
    'records.asset_class_neta_procedure, records.neta_procedure_xref, '
    'records.assets, records.form_submissions, records.form_field_values, '
    'records.pm_schedules, records.pm_events, records.persons '
    'to records_intake_writer';

  -- Column-scoped INSERT/UPDATE per write-path table (all columns minus reserved minus
  -- auto-populated PK/created_at/updated_at). Reserved cols carry defaults/nullable so INSERT
  -- omitting them succeeds; every NOT-NULL/no-default column is included (build-time invariant).
  execute 'grant insert (asset_tag, name, asset_class_id, parent_asset_id, site_ref, client_ref, '
    'location_label, region, jobsite, plant, substation, gps_lat, gps_long, manufacturer, model, '
    'serial_number, rated_voltage, rated_current, year_manufactured, last_tested_at, apparatus_ref, '
    'equipment_model_id, source, provenance_status, legacy_source_id, notes), '
    'update (asset_tag, name, asset_class_id, parent_asset_id, site_ref, client_ref, location_label, '
    'region, jobsite, plant, substation, gps_lat, gps_long, manufacturer, model, serial_number, '
    'rated_voltage, rated_current, year_manufactured, last_tested_at, apparatus_ref, equipment_model_id, '
    'source, provenance_status, legacy_source_id, notes) '
    'on records.assets to records_intake_writer';

  execute 'grant insert (template_id, asset_id, project_ref, work_package_ref, pm_event_id, overall_assessment, '
    'as_found_as_left, test_status_label, job_number, test_date, technician, ambient_temp_c, '
    'relative_humidity, test_equipment, summary_notes, source, provenance_status, legacy_source_id, '
    'origin_device, client_rev, client_captured_at, synced_at, neta_standard, technician_person_id), '
    'update (template_id, asset_id, project_ref, work_package_ref, pm_event_id, overall_assessment, '
    'as_found_as_left, test_status_label, job_number, test_date, technician, ambient_temp_c, '
    'relative_humidity, test_equipment, summary_notes, source, provenance_status, legacy_source_id, '
    'origin_device, client_rev, client_captured_at, synced_at, neta_standard, technician_person_id) '
    'on records.form_submissions to records_intake_writer';

  execute 'grant insert (form_submission_id, field_key, field_label, test_group, sequence_no, value_kind, '
    'value_numeric, value_text, value_boolean, unit, expected_value, min_acceptable, max_acceptable, '
    'measured_at, notes, origin_device, client_rev, client_captured_at, synced_at), '
    'update (form_submission_id, field_key, field_label, test_group, sequence_no, value_kind, '
    'value_numeric, value_text, value_boolean, unit, expected_value, min_acceptable, max_acceptable, '
    'measured_at, notes, origin_device, client_rev, client_captured_at, synced_at) '
    'on records.form_field_values to records_intake_writer';

  execute 'grant insert (pm_program_id, asset_id, last_performed_at, next_due_at, is_active, notes), '
    'update (pm_program_id, asset_id, last_performed_at, next_due_at, is_active, notes) '
    'on records.pm_schedules to records_intake_writer';

  execute 'grant insert (pm_schedule_id, asset_id, scheduled_for, performed_at, form_submission_id, '
    'project_ref, outcome, notes, origin_device, client_rev, client_captured_at, synced_at), '
    'update (pm_schedule_id, asset_id, scheduled_for, performed_at, form_submission_id, '
    'project_ref, outcome, notes, origin_device, client_rev, client_captured_at, synced_at) '
    'on records.pm_events to records_intake_writer';

  execute 'grant insert (display_name), update (display_name) '
    'on records.persons to records_intake_writer';

  -- [4] RLS: enable on all 15 tables; reference USING(true); write-path role-scoped; restrict source_links.
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

  -- [5] Views: security_invoker so base-table RLS applies to the caller.
  execute 'alter view records.v_asset_test_history set (security_invoker = true)';
  execute 'alter view records.v_pm_due set (security_invoker = true)';

  reset role;
end $$;

-- [2b] Public-schema hygiene (db/public-schema scoped, applier identity, NOT records-owner).
revoke create on schema public from public;               -- database-scoped; no-op vs PG15+ default

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

-- [3a] posture asserts: 11 NOT-NULL columns present; reserved cols absent; reader no-write;
-- writer no-DELETE anywhere; neither role holds ANY privilege on source_links (exactness -
-- these fail-closed on a stale/extra grant that the [3] revoke-first should have cleared).
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
  -- the 15 records tables (8 ref + 6 write-path + source_links)
  all15 text[] := array['asset_classes','form_templates','pm_programs','neta_procedures',
    'neta_test_items','neta_tables','asset_class_neta_procedure','neta_procedure_xref',
    'assets','form_submissions','form_field_values','pm_schedules','pm_events','persons',
    'neta_table_source_links'];
  i int; wp text; t2 text; pv text;
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
  -- reader (records_api) holds NO write anywhere across all 15 records tables
  foreach t2 in array all15 loop
    if has_table_privilege('records_api', format('records.%I', t2), 'INSERT')
       or has_table_privilege('records_api', format('records.%I', t2), 'UPDATE')
       or has_table_privilege('records_api', format('records.%I', t2), 'DELETE') then
      raise exception '045 posture: records_api holds a write on % (reader must be read-only)', t2;
    end if;
  end loop;
  -- writer (records_intake_writer) holds NO DELETE anywhere across all 15 records tables
  foreach t2 in array all15 loop
    if has_table_privilege('records_intake_writer', format('records.%I', t2), 'DELETE') then
      raise exception '045 posture: records_intake_writer holds DELETE on % (writer never deletes)', t2;
    end if;
  end loop;
  -- neither app role holds ANY privilege on neta_table_source_links (D10 owner-only)
  foreach t2 in array array['records_api','records_intake_writer'] loop
    foreach pv in array array['SELECT','INSERT','UPDATE','DELETE'] loop
      if has_table_privilege(t2, 'records.neta_table_source_links', pv) then
        raise exception '045 posture: % holds % on neta_table_source_links (D10 owner-only)', t2, pv;
      end if;
    end loop;
  end loop;
end $$;

-- [4a] posture asserts on RLS enablement + non-PUBLIC policy targeting (read-only).
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

-- [5a] posture assert: every records view is security_invoker (read-only).
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

-- [owner-post] Revoke the transient reclaim membership taken in [owner-pre] (re-up only).
-- Runs BEFORE COMMIT and before this migration would be re-examined, so no usable
-- applier->records_reclaim_owner edge survives 045.
do $$
declare v_owner text;
begin
  select pg_get_userbyid(nspowner) into v_owner from pg_namespace where nspname='records';
  if v_owner = 'records_reclaim_owner' and v_owner <> current_user then
    execute format('revoke records_reclaim_owner from %I', current_user);
  end if;
end $$;

COMMIT;
