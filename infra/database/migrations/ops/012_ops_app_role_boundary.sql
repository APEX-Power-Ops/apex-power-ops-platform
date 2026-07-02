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

-- [2] PUBLIC hygiene (D5, C3, H1) ------------------------------------------------------
-- H1: PUBLIC EXECUTE on functions is a hard-wired creation default that ALTER DEFAULT
-- PRIVILEGES cannot displace for already-existing functions: the explicit REVOKE below is
-- the load-bearing statement, and it MUST precede the DEFINER conversion in section [3].
-- CI convention: any future migration creating a function must re-run this REVOKE or
-- grant explicitly; the [2a] assert loop closes drift at every ladder apply.
-- L3: ALL ROUTINES (not ALL FUNCTIONS) so the revoke also covers procedures - the [2a]
-- assert sweeps every prokind, so ALL FUNCTIONS would false-fail the day a procedure lands.

revoke execute on all routines in schema ops from public;
revoke execute on all routines in schema core from public;

-- C3: current_database() is invalid in REVOKE grammar and a bare name would break the
-- one-ladder-two-DBs invariant -> dynamic SQL.
do $$
begin
  execute format('revoke connect on database %I from public', current_database());
  execute format('grant connect on database %I to ops_intake_writer, ops_api', current_database());
end $$;

revoke create on schema public from public;

-- D6/C1: work.* zero grants, presence-gated (work exists on ops_dev, absent on ops_test).
do $$
begin
  if to_regnamespace('work') is not null then
    execute 'revoke execute on all routines in schema work from public';
    execute 'revoke all on all tables in schema work from ops_intake_writer, ops_api, ops_fn_owner';
    execute 'revoke usage on schema work from ops_intake_writer, ops_api, ops_fn_owner';
  end if;
end $$;

-- [2a] posture asserts
do $$
declare n int;
begin
  select count(*) into n
  from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
  where ns.nspname in ('ops','core')
    and (p.proacl is null
         or exists (select 1 from aclexplode(p.proacl) a
                    where a.grantee = 0 and a.privilege_type = 'EXECUTE'));
  if n > 0 then
    raise exception '012 posture: % ops/core function(s) retain PUBLIC EXECUTE', n;
  end if;
  if exists (select 1 from pg_database where datname = current_database() and datacl is null) then
    raise exception '012 posture: datacl is NULL (default ACL includes PUBLIC CONNECT)';
  end if;
  if exists (select 1 from pg_database d, aclexplode(d.datacl) a
             where d.datname = current_database()
               and a.grantee = 0 and a.privilege_type = 'CONNECT') then
    raise exception '012 posture: PUBLIC retains CONNECT on %', current_database();
  end if;
  if not has_database_privilege('postgres', current_database(), 'CONNECT') then
    raise exception '012 posture: admin lost CONNECT';
  end if;
  if to_regnamespace('work') is not null then
    if exists (
      select 1
      from pg_class c join pg_namespace ns on ns.oid = c.relnamespace,
           lateral (values ('ops_intake_writer'), ('ops_api')) roles(r)
      where ns.nspname = 'work' and c.relkind in ('r','v','m','p')
        and (has_table_privilege(roles.r, c.oid, 'SELECT')
          or has_table_privilege(roles.r, c.oid, 'INSERT')
          or has_table_privilege(roles.r, c.oid, 'UPDATE')
          or has_table_privilege(roles.r, c.oid, 'DELETE'))
    ) then
      raise exception '012 posture: a login role holds a work.* privilege';
    end if;
  end if;
end $$;

-- [3] SECURITY DEFINER conversion + dedicated owner (D3, M4) + owner grants (S5) --------
-- Exact signatures grounded from pg_proc. The loop FAILS LOUD if any signature drifted.

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
    if to_regprocedure(sig) is null then
      raise exception '012: expected function % is missing - signature drift', sig;
    end if;
    execute format('alter function %s security definer set search_path = ops, pg_temp', sig);
    execute format('alter function %s owner to ops_fn_owner', sig);
  end loop;
end $$;

-- Owner object grants: ONLY what the 9 fn bodies need (S5; read-surface verified against
-- live pg_get_functiondef 2026-07-01 - no core.* reads, so no core USAGE for the owner).
grant usage on schema ops to ops_fn_owner;

-- RV-1: SELECT on every table the fn bodies read/join. scopes is REQUIRED (attest,
-- approve_and_recognize, and the revrec insert-integrity trigger all join ops.scopes).
grant select on ops.apparatus, ops.scopes, ops.completion_attestation,
  ops.revenue_recognition_event, ops.scope_quote, ops.projects, ops.persons
  to ops_fn_owner;

-- Write/lock surface. Table-level UPDATE is acceptable HERE ONLY: NOLOGIN + fn-gated +
-- non-membered; the append-only/integrity triggers still bar real ledger mutation.
grant update on ops.apparatus to ops_fn_owner;                       -- status writes + recognition FOR UPDATE
grant insert, update on ops.completion_attestation to ops_fn_owner;
grant insert, update on ops.revenue_recognition_event to ops_fn_owner;  -- UPDATE solely for reverse_recognition's FOR UPDATE
grant update on ops.projects to ops_fn_owner;                        -- solely for billing project FOR UPDATE locks
grant select, insert, update, delete on ops.billing_application,
  ops.billing_application_line, ops.billing_application_draft to ops_fn_owner;

-- [3a] posture asserts
do $$
begin
  if exists (
    select 1 from unnest(array[
      'ops.attest_apparatus_complete(uuid,uuid,text)',
      'ops.revoke_completion_attestation(uuid,uuid,text)',
      'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
      'ops.reverse_recognition(uuid,uuid,text)',
      'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.issue_billing_application(uuid,uuid,text)',
      'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.discard_draft_billing_application(uuid,uuid)',
      'ops.void_billing_application(uuid,uuid,text)'
    ]) s(sig)
    join pg_proc p on p.oid = to_regprocedure(s.sig)
    where not p.prosecdef or p.proowner <> 'ops_fn_owner'::regrole
  ) then
    raise exception '012 posture: a mutation fn is not DEFINER-owned by ops_fn_owner';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.scopes', 'SELECT') then
    raise exception '012 posture: ops_fn_owner missing SELECT on ops.scopes (RV-1)';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.revenue_recognition_event', 'UPDATE')
     or not has_table_privilege('ops_fn_owner', 'ops.projects', 'UPDATE') then
    raise exception '012 posture: ops_fn_owner missing a FOR UPDATE lock grant';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.billing_application', 'SELECT') then
    raise exception '012 posture: ops_fn_owner missing billing SELECT (RV-2)';
  end if;
end $$;
