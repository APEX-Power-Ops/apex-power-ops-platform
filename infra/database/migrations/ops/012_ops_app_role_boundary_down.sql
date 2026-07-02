-- 012_ops_app_role_boundary_down.sql
-- Restores the pre-012 (insecure) posture: ladder symmetry, NOT a security recommendation.
-- Ordered per spec S7: [d1] fn owner -> postgres + SECURITY INVOKER (added in Task 3);
-- [d2] restore the pre-012 completion guard (added in Task 5); [d3] DROP OWNED BY the
-- three roles; [d4] guarded DROP ROLE; [d5] restore PUBLIC EXECUTE + CONNECT.
-- Every step is guarded so this file is safe to run even when 012 was never applied
-- (test _clean_slate runs it unconditionally).

-- [d1] revert the 9 fns: owner -> postgres, SECURITY INVOKER, unpin search_path.
-- Guarded per-signature so a partially-applied ladder is safe.
do $$
declare
  sig text;
  sigs text[] := array[
    'ops.attest_apparatus_complete(uuid,uuid,text)',
    'ops.revoke_completion_attestation(uuid,uuid,text)',
    'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
    'ops.reverse_recognition(uuid,uuid,text)',
    'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
    'ops.issue_billing_application(uuid,uuid,text)',
    'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
    'ops.discard_draft_billing_application(uuid,uuid)',
    'ops.void_billing_application(uuid,uuid,text)'
  ];
begin
  foreach sig in array sigs loop
    if to_regprocedure(sig) is not null then
      execute format('alter function %s owner to postgres', sig);
      execute format('alter function %s security invoker', sig);
      execute format('alter function %s reset search_path', sig);
    end if;
  end loop;
end $$;

-- [d2] restore the pre-012 completion guard (verbatim 009 body), guarded on schema presence
do $$
begin
  if to_regnamespace('ops') is not null and to_regclass('ops.apparatus') is not null then
    execute $guard$
create or replace function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $fn$
declare
  new_g boolean := (new.status='Complete' and new.provenance_status='approved');
  old_g boolean;
begin
  if tg_op = 'INSERT' then
    if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
    end if;
  else  -- UPDATE
    old_g := (old.status='Complete' and old.provenance_status='approved');
    if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
    end if;
  end if;
  return new;
end; $fn$;
$guard$;
  end if;
end $$;

-- [d3] revoke THIS database's grants from the roles. F-012-3 (operator-ratified 2026-07-02):
-- DROP OWNED BY a LOGIN role also revokes DATABASE CONNECT, which is a SHARED-object ACL on
-- pg_database - so DROP OWNED strips the role's CONNECT on EVERY database in the cluster, not
-- just this one. Once 012 is applied on ops_dev (removing PUBLIC CONNECT), a routine ops_test
-- teardown running this down would lock ops_intake_writer/ops_api out of live ops_dev. So the
-- two LOGIN roles get DATABASE-SCOPED revokes here (mirroring the up [2] pattern); DROP OWNED
-- remains ONLY for ops_fn_owner (NOLOGIN, never granted CONNECT).
do $$
begin
  if exists (select 1 from pg_roles where rolname = 'ops_intake_writer') then
    if to_regnamespace('ops') is not null then
      execute 'revoke all privileges on all tables in schema ops from ops_intake_writer';
      execute 'revoke all privileges on all routines in schema ops from ops_intake_writer';
      execute 'revoke usage on schema ops from ops_intake_writer';
    end if;
    if to_regnamespace('core') is not null then
      execute 'revoke all privileges on all tables in schema core from ops_intake_writer';
      execute 'revoke all privileges on all routines in schema core from ops_intake_writer';
      execute 'revoke usage on schema core from ops_intake_writer';
    end if;
    execute format('revoke connect on database %I from ops_intake_writer', current_database());
  end if;
  if exists (select 1 from pg_roles where rolname = 'ops_api') then
    if to_regnamespace('ops') is not null then
      execute 'revoke all privileges on all tables in schema ops from ops_api';
      execute 'revoke all privileges on all routines in schema ops from ops_api';
      execute 'revoke usage on schema ops from ops_api';
    end if;
    execute format('revoke connect on database %I from ops_api', current_database());
  end if;
  -- ops_fn_owner: NOLOGIN, never granted CONNECT; DROP OWNED is safe + database-scoped
  -- ([d1] already reassigned its functions to postgres).
  if exists (select 1 from pg_roles where rolname = 'ops_fn_owner') then
    drop owned by ops_fn_owner;
  end if;
end $$;

-- [d4] guarded/drop-if-safe role drop (DEV-7, operator-ratified). PRIMARY guard: never
-- drop a login role whose SCRAM password was set out-of-band (pg_authid.rolpassword IS NOT
-- NULL). Dropping it and letting the up-side recreate it password-less would break every
-- scram login (Tasks 9/10/12). SECONDARY guard (DEV-4): DROP ROLE also fails with
-- dependent_objects_still_exist if the role owns grants in ANOTHER database of this cluster.
-- Either way [d3] DROP OWNED already revoked THIS DB's grants, so posture is restored
-- whether or not the role object survives. ops_fn_owner (NOLOGIN, no password) drops cleanly.
-- Reading pg_authid requires superuser; the down runs as the admin identity.
do $$
declare r text;
begin
  foreach r in array array['ops_intake_writer', 'ops_api', 'ops_fn_owner'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      if exists (select 1 from pg_authid where rolname = r and rolpassword is not null) then
        raise notice '012_down: role % has an out-of-band password set; left in place (DEV-7)', r;
        continue;
      end if;
      begin
        execute format('drop role %I', r);
      exception when dependent_objects_still_exist then
        raise notice '012_down: role % retains dependencies in another database; left in place', r;
      end;
    end if;
  end loop;
end $$;

-- [d5] restore PUBLIC posture (pre-012): EXECUTE on all ops/core (+work) functions, CONNECT.
-- CREATE on schema public is NOT re-granted (PG15+ default lacks it; DEV-5).
do $$
begin
  if to_regnamespace('ops') is not null then
    execute 'grant execute on all routines in schema ops to public';
  end if;
  if to_regnamespace('core') is not null then
    execute 'grant execute on all routines in schema core to public';
  end if;
  if to_regnamespace('work') is not null then
    execute 'grant execute on all routines in schema work to public';
  end if;
  execute format('grant connect on database %I to public', current_database());
end $$;
