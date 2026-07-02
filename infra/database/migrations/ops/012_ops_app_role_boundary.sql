-- 012_ops_app_role_boundary.sql
-- The ops_app role boundary: D1=B two-role split (ops_intake_writer / ops_api) + dedicated
-- NOLOGIN SECURITY DEFINER owner (ops_fn_owner) + PUBLIC hygiene + column-scoped grant
-- matrix + H2 completion-guard tightening + in-migration posture asserts.
-- Spec: docs/superpowers/specs/2026-07-01-ops-app-role-boundary-design-v3.md
-- Roles are CLUSTER-level and this ladder runs on ops_test AND ops_dev on the same
-- cluster: creation is guarded, flags are corrected unconditionally (M3).
-- Passwords for the two LOGIN roles are set OUT-OF-BAND by the operator - never here.

-- [1] Roles + membership hardening (M3, M4/V3-1) -------------------------------------

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'ops_intake_writer') then
    create role ops_intake_writer;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'ops_api') then
    create role ops_api;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'ops_fn_owner') then
    create role ops_fn_owner;
  end if;
end $$;

alter role ops_intake_writer with login  nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role ops_api           with login  nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role ops_fn_owner      with nologin nosuperuser nocreatedb nocreaterole nobypassrls noreplication;

-- NOLOGIN alone does not stop a MEMBER from SET ROLE ops_fn_owner: revoke membership
-- explicitly. (Membership cannot be granted to PUBLIC in PostgreSQL, so the spec's
-- "FROM PUBLIC" is vacuously satisfied; the assert below enforces it durably.)
revoke ops_fn_owner from ops_intake_writer;
revoke ops_fn_owner from ops_api;

-- [1a] posture asserts: flags + non-membership (migration FAILS on drift)
do $$
declare
  r record;
  bad text;
begin
  for r in
    select rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolreplication
    from pg_roles where rolname in ('ops_intake_writer', 'ops_api', 'ops_fn_owner')
  loop
    if r.rolsuper or r.rolcreatedb or r.rolcreaterole or r.rolbypassrls or r.rolreplication then
      raise exception '012 posture: % holds a privileged flag', r.rolname;
    end if;
    if r.rolname = 'ops_fn_owner' and r.rolcanlogin then
      raise exception '012 posture: ops_fn_owner must be NOLOGIN';
    end if;
    if r.rolname in ('ops_intake_writer', 'ops_api') and not r.rolcanlogin then
      raise exception '012 posture: % must be LOGIN', r.rolname;
    end if;
  end loop;
  if (select count(*) from pg_roles where rolname in ('ops_intake_writer','ops_api','ops_fn_owner')) <> 3 then
    raise exception '012 posture: expected all three roles present';
  end if;
  if pg_has_role('ops_intake_writer', 'ops_fn_owner', 'member')
     or pg_has_role('ops_api', 'ops_fn_owner', 'member') then
    raise exception '012 posture: a login app role is a member of ops_fn_owner';
  end if;
  select rolname into bad from pg_roles
   where rolcanlogin and not rolsuper
     and pg_has_role(rolname, 'ops_fn_owner', 'member')
   limit 1;
  if bad is not null then
    raise exception '012 posture: login role % is a member of ops_fn_owner', bad;
  end if;
end $$;
