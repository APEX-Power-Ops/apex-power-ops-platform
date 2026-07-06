-- 045_records_security_rls_down.sql
-- Restores the pre-045 posture. Ladder symmetry, NOT a security recommendation.
-- Checklist (spec 5.3): zero DROP OWNED (both app roles are LOGIN; DROP OWNED would strip
-- shared pg_database CONNECT cluster-wide, ops-012 F-012-3); database-scoped revokes run
-- UNCONDITIONALLY; all routines (not all functions); guarded DROP ROLE (DEV-7 password guard).
--
-- SUPABASE-COMPAT (compat lane Task 2.1, plan REV 5 D-B): 045_down runs AFTER 046_down in
-- the reverse ladder (049_down..046_down..045_down), so the records objects are then owned
-- by records_reclaim_owner. The object-level owner-requiring DDL (drop policies, disable /
-- reset RLS, reset security_invoker, restore PUBLIC EXECUTE, the records-object revokes)
-- runs AS the at-rest owner: under SET ROLE records_reclaim_owner (via a transient WITH SET
-- grant on the applier, revoked after) when reclaim-owned, or directly as the applier
-- identity when the objects are still applier-owned (a standalone 045-only down). The
-- app-role reversal (schema-level revokes + guarded DROP ROLE) always runs as the applier.

BEGIN;
SET client_encoding TO 'UTF8';

-- [d0] enter owner context: detect the single at-rest owner; on a reclaim-owned state take
-- a transient WITH SET membership so the object-level DDL can SET ROLE into it. Fail loud on
-- mixed ownership (a botched transfer must not silently half-revert).
do $$
declare owner_oids oid[]; v_owner_oid oid; v_owner text; v_me_oid oid;
begin
  -- current_user's OID by exact name lookup (never current_user::regrole - a text->regrole
  -- cast lowercases an unquoted mixed-case name and fails 42704 on the applier's name).
  select oid into v_me_oid from pg_roles where rolname = current_user;
  -- Compare by OID (::regrole::text quotes mixed-case names).
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
    raise exception '045_down owner pre-check: no records objects found';
  end if;
  if array_length(owner_oids,1) <> 1 then
    raise exception '045_down owner pre-check: records objects have MIXED owners %, expected exactly one',
      (select array_agg(pg_get_userbyid(x)) from unnest(owner_oids) x);
  end if;
  v_owner_oid := owner_oids[1];
  v_owner := pg_get_userbyid(v_owner_oid);
  if v_owner = 'records_reclaim_owner' and v_owner_oid <> v_me_oid then
    execute format('grant records_reclaim_owner to %I with set true, inherit false, admin false', current_user);
  end if;
end $$;

-- [d1] object-level reversal, run AS the at-rest owner ------------------------------------
-- drop policies + disable RLS on all 15 tables; revert views to definer; restore PUBLIC
-- EXECUTE on records routines; authoritative records-object revokes for both app roles.
do $$
declare v_owner text; t text;
begin
  select pg_get_userbyid(nspowner) into v_owner from pg_namespace where nspname='records';
  execute format('set role %I', v_owner);

  foreach t in array array['asset_classes','form_templates','pm_programs','neta_procedures',
    'neta_test_items','neta_tables','asset_class_neta_procedure','neta_procedure_xref',
    'assets','form_submissions','form_field_values','pm_schedules','pm_events','persons',
    'neta_table_source_links'] loop
    execute format('drop policy if exists p_%1$s_read on records.%1$s', t);
    execute format('drop policy if exists p_%1$s_ins on records.%1$s', t);
    execute format('drop policy if exists p_%1$s_upd on records.%1$s', t);
    execute format('alter table records.%I disable row level security', t);
  end loop;

  -- revert views to definer (non-invoker)
  execute 'alter view records.v_asset_test_history reset (security_invoker)';
  execute 'alter view records.v_pm_due reset (security_invoker)';

  -- restore pre-up PUBLIC EXECUTE on records routines
  execute 'grant execute on all routines in schema records to public';

  -- database/records-object grant revokes for BOTH app roles (records-owner scoped).
  foreach t in array array['records_api','records_intake_writer'] loop
    if exists (select 1 from pg_roles where rolname=t) then
      execute format('revoke all privileges on all tables in schema records from %I', t);
      execute format('revoke all privileges on all routines in schema records from %I', t);
      execute format('revoke usage on schema records from %I', t);
    end if;
  end loop;

  reset role;
end $$;

-- [d5] guarded DROP ROLE (DEV-7): never drop a role that may carry an operator-provisioned
-- out-of-band login password. Runs as the applier identity (role-object reversal).
-- SUPABASE-COMPAT: the non-super applier CANNOT read the true password state - pg_authid is
-- superuser-only (42501 for non-super postgres on managed Supabase) and pg_roles.rolpassword
-- is a hardcoded '********' mask (useless as a signal). So this guard is CONSERVATIVE and
-- FAIL-SAFE: because a password cannot be ruled out under non-super, the app roles are LEFT
-- IN PLACE rather than dropped, protecting any operator serving credential (records_api on a
-- serving target carries such a password). This trades ladder symmetry (the roles persist)
-- for never destroying a live credential; a subsequent 045 up re-adopts them (create-if-not-
-- exists). On a true-superuser local walk the same code path still leaves them (safe); role
-- teardown on a disposable target is the harness's job, not this data-/credential-preserving
-- down. Dependency-tolerant either way.
do $$
declare r text;
begin
  foreach r in array array['records_api','records_intake_writer'] loop
    if exists (select 1 from pg_roles where rolname=r) then
      -- Password state is not readable as the non-super applier; leave the role in place
      -- (fail-safe) so an out-of-band operator password can never be silently dropped.
      raise notice '045_down: role % left in place (password state unverifiable as non-super applier; DEV-7 fail-safe)', r;
    end if;
  end loop;
end $$;

-- [d6] revoke the transient reclaim membership taken in [d0] (reclaim-owned re-down only).
do $$
declare v_owner text;
begin
  select pg_get_userbyid(nspowner) into v_owner from pg_namespace where nspname='records';
  if v_owner = 'records_reclaim_owner' and v_owner <> current_user then
    execute format('revoke records_reclaim_owner from %I', current_user);
  end if;
end $$;

COMMIT;
