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
