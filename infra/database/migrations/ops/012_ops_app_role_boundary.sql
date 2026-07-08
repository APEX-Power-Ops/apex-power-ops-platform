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

-- Attribute correction (M3). A1 (D8/managed): the SUPERUSER / BYPASSRLS / REPLICATION clauses
-- are settable ONLY by a superuser; on managed non-super postgres they raise 42501 even though
-- the target value is the default. A freshly created role already defaults to
-- NOSUPERUSER / NOBYPASSRLS / NOREPLICATION, so on the managed path we set only the
-- createrole-settable attributes (login/nologin, nocreatedb, nocreaterole); the [1a] assert
-- below proves the full posture on BOTH substrates. On a superuser applier v_tail is the
-- original full clause list (byte-equivalent behavior on ops_dev/ops_test).
do $$
declare
  v_super boolean := (select rolsuper from pg_roles where rolname = current_user);
  v_tail  text := case when v_super
                       then 'nosuperuser nocreatedb nocreaterole nobypassrls noreplication'
                       else 'nocreatedb nocreaterole' end;
begin
  execute format('alter role ops_intake_writer with login  %s', v_tail);
  execute format('alter role ops_api           with login  %s', v_tail);
  execute format('alter role ops_fn_owner      with nologin %s', v_tail);
end $$;

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
  -- A2 (D8/managed): exempt the applier (current_user). On managed non-super postgres the
  -- applier holds a SET-capable ops_fn_owner membership so it can transfer ownership in [3];
  -- that is the ratified trusted-applier edge (D8-2), analogous to the records postgres->
  -- records_* edges. The serving roles (ops_intake_writer / ops_api) are still caught by the
  -- pg_has_role checks above and here. On a superuser applier (ops_dev/ops_test) this added
  -- predicate is a no-op: current_user is already excluded by `not rolsuper`.
  select rolname into bad from pg_roles
   where rolcanlogin and not rolsuper and rolname <> current_user
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
-- A3/A4 (D8/managed): database-level CONNECT hygiene and the public-schema CREATE revoke are a
-- DEDICATED-DB posture (safe when the applier is a superuser owning a private ops DB). On a
-- SHARED managed DB (non-super postgres; records/tcc/... co-tenant) they are both unpermitted
-- (the database and the public schema are not postgres-owned) AND unsafe (revoking PUBLIC
-- CONNECT would lock out co-tenant Supabase roles). The managed path NEVER changes database-
-- level or public-schema ACLs; its else-branch asserts PUBLIC still holds CONNECT (the static
-- and runtime regression guard for D8-3). The login roles reach the DB via the inherited
-- PUBLIC CONNECT we deliberately leave in place; the boundary is schema-scoped (USAGE below).
do $$
declare v_super boolean := (select rolsuper from pg_roles where rolname = current_user);
begin
  if v_super then
    execute format('revoke connect on database %I from public', current_database());
    execute format('grant connect on database %I to ops_intake_writer, ops_api', current_database());
    execute 'revoke create on schema public from public';
  else
    -- managed shared-DB path: prove we did NOT run the dedicated-DB revoke. PUBLIC holds
    -- CONNECT when datacl IS NULL (cluster default) or grants it explicitly.
    if not (
      (select datacl is null from pg_database where datname = current_database())
      or exists (select 1 from pg_database d, aclexplode(d.datacl) a
                 where d.datname = current_database()
                   and a.grantee = 0 and a.privilege_type = 'CONNECT')
    ) then
      raise exception '012 managed: PUBLIC must retain CONNECT - database hygiene must not run on a shared DB';
    end if;
  end if;
end $$;

-- D6/C1: work.* zero grants, presence-gated (work exists on ops_dev, absent on ops_test).
do $$
declare v_super boolean := (select rolsuper from pg_roles where rolname = current_user);
begin
  if to_regnamespace('work') is not null then
    -- work.* PUBLIC hardening is out-of-lane on a shared DB (work belongs to another lane and
    -- is not postgres-owned): only the dedicated-DB (superuser) path revokes PUBLIC there.
    if v_super then
      execute 'revoke execute on all routines in schema work from public';
    end if;
    -- ops-scoped: ensure the three ops roles hold NOTHING on work (no-op when they are fresh).
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
  -- Database-level CONNECT posture asserts apply ONLY to the dedicated-DB (superuser) path;
  -- on the managed shared DB PUBLIC deliberately RETAINS CONNECT (A3), so these would
  -- false-fail. The managed non-run of the revoke is asserted in the [2] else-branch above.
  if (select rolsuper from pg_roles where rolname = current_user) then
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
  v_super boolean := (select rolsuper from pg_roles where rolname = current_user);
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
  -- A2 (D8/managed): a non-super applier cannot ALTER ... OWNER TO ops_fn_owner unless it has
  -- BOTH (a) a SET-capable membership in ops_fn_owner AND (b) ops_fn_owner holds CREATE on the
  -- function's schema (Postgres forbids giving an object to a role that could not have created
  -- it there). Grant both transiently on the managed path. KEEP the membership as the ratified
  -- trusted-applier edge (D8-2; [1a] exempts the applier); REVOKE the transient CREATE after
  -- the loop so the durable owner posture is USAGE-only, identical to the superuser path (where
  -- superuser bypass needs neither, so no edge and no CREATE are added). Branch-proof verified:
  -- without the CREATE grant the transfer fails 42501 "permission denied for schema ops".
  if not v_super then
    execute format('grant ops_fn_owner to %I', current_user);
    grant create on schema ops to ops_fn_owner;
  end if;
  foreach sig in array sigs loop
    if to_regprocedure(sig) is null then
      raise exception '012: expected function % is missing - signature drift', sig;
    end if;
    execute format('alter function %s security definer set search_path = ops, pg_temp', sig);
    execute format('alter function %s owner to ops_fn_owner', sig);
  end loop;
  -- A2 (D8/managed): restore USAGE-only durable posture (the CREATE was only needed to place
  -- the reassigned functions). No-op on the superuser path (nothing was granted there).
  if not v_super then
    revoke create on schema ops from ops_fn_owner;
  end if;
end $$;

-- Owner object grants: ONLY what the 9 fn bodies need (S5; read-surface verified against
-- live pg_get_functiondef 2026-07-01 - no core.* reads, so no core USAGE for the owner).
grant usage on schema ops to ops_fn_owner;

-- RV-1: SELECT on every table the fn bodies read/join. scopes is REQUIRED (attest,
-- approve_and_recognize, and the revrec insert-integrity trigger all join ops.scopes).
-- F-012-2 (operator-ratified 2026-07-02): ops.tasks is REQUIRED - the owner's apparatus
-- UPDATEs (attest/revoke/approve) fire INVOKER trigger trg_apparatus_task_same_scope (007),
-- which reads ops.tasks as the DML executor.
grant select on ops.apparatus, ops.scopes, ops.completion_attestation,
  ops.revenue_recognition_event, ops.scope_quote, ops.projects, ops.persons, ops.tasks
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
  if not has_table_privilege('ops_fn_owner', 'ops.tasks', 'SELECT') then
    raise exception '012 posture: ops_fn_owner missing SELECT on ops.tasks (F-012-2)';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.revenue_recognition_event', 'UPDATE')
     or not has_table_privilege('ops_fn_owner', 'ops.projects', 'UPDATE') then
    raise exception '012 posture: ops_fn_owner missing a FOR UPDATE lock grant';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.billing_application', 'SELECT') then
    raise exception '012 posture: ops_fn_owner missing billing SELECT (RV-2)';
  end if;
end $$;

-- [4] USAGE + EXECUTE (D3) --------------------------------------------------------------

grant usage on schema ops to ops_intake_writer;
grant usage on schema core to ops_intake_writer;
grant usage on schema ops to ops_api;

grant execute on function
  ops.attest_apparatus_complete(uuid,uuid,text),
  ops.revoke_completion_attestation(uuid,uuid,text),
  ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text),
  ops.reverse_recognition(uuid,uuid,text)
  to ops_api;
-- Billing EXECUTE deferred (GATE-12): the 5 billing fns get NO EXECUTE grant here.

-- [5] Login-role grant matrix (S5; FINAL per Task 0 PASS) --------------------------------

-- ops_intake_writer: intake surface
grant insert, update, select on ops.intake_runs to ops_intake_writer;
grant insert, select on ops.intake_source_files to ops_intake_writer;
grant insert, select on ops.intake_validation_findings to ops_intake_writer;

-- projects: column-scoped INSERT (load.py upsert_project) + column-scoped UPDATE
-- (upsert DO-UPDATE cols + approve.py _freeze provenance stamp). NOT retainage_pct /
-- lifecycle / is_active; NO DELETE.
grant insert (project_number, project_name, status, quote_revision, contract_value,
  description, source_client_name, source_site_name, source_site_address, source_site_city,
  source_site_state, source_site_zip, source, legacy_source_id, provenance_status),
  update (project_name, status, quote_revision, contract_value, description,
  source_client_name, source_site_name, source_site_address, source_site_city,
  source_site_state, source_site_zip, source, provenance_status, updated_at),
  select on ops.projects to ops_intake_writer;

-- scopes: DELETE = sanctioned full-replacement; RI cascade runs as table owner.
grant insert, delete, select on ops.scopes to ops_intake_writer;
grant insert, select, update (total_quoted_hours, is_frozen, frozen_at)
  on ops.scope_quote to ops_intake_writer;
grant insert, select on ops.scope_quote_line to ops_intake_writer;
grant insert, update, select on ops.tasks to ops_intake_writer;

-- apparatus (D2): INSERT on the 11 load.py columns EXCLUDING status; UPDATE on exactly
-- the approve.py _freeze columns. NO status, NO source/scope_id UPDATE, NO DELETE.
grant insert (scope_id, task_id, apparatus_designation, apparatus_type, equipment_model_ref,
  drawing_reference, quoted_hours, quote_line_id, source, legacy_source_id, provenance_status),
  select,
  update (quoted_revenue, provenance_status, updated_at)
  on ops.apparatus to ops_intake_writer;

-- read-only conflict checks
grant select on ops.revenue_recognition_event to ops_intake_writer;
grant select on ops.billing_application to ops_intake_writer;

-- catalog resolve
grant select on core.v_equipment_models_resolved to ops_intake_writer;
grant select on core.equipment_models to ops_intake_writer;

-- the 11 ops views (postgres-owned, non-security_invoker - asserted in [5a])
grant select on ops.v_apparatus_quote, ops.v_apparatus_recognition,
  ops.v_billing_application_sov, ops.v_completion_recognition_rollup,
  ops.v_completion_recognition_worklist, ops.v_draft_preview, ops.v_project_billing,
  ops.v_project_recognition, ops.v_recognition_review_queue, ops.v_scope_recognition,
  ops.v_unbilled_recognition to ops_intake_writer;

-- F-012-1 (operator-ratified 2026-07-02): required by the
-- uq_intake_runs_proj_quote_version_native partial-index predicate.
-- INSERT/UPDATE on ops.intake_runs evaluates this helper as the DML executor.
grant execute on function ops._intake_source_format_text(ops.intake_source_format)
  to ops_intake_writer;

-- ops_api: recognition read surface only
grant select on ops.v_completion_recognition_worklist, ops.v_completion_recognition_rollup
  to ops_api;

-- [5a] posture asserts: the boundary, positively and negatively
do $$
declare
  col text;
  r text;
  t text;
  p text;
  n int;
begin
  -- positive: writer intake INSERT + the pinned projects UPDATE columns (V3-9)
  if not has_table_privilege('ops_intake_writer', 'ops.intake_runs', 'INSERT') then
    raise exception '012 posture: writer missing INSERT on intake_runs';
  end if;
  if not has_column_privilege('ops_intake_writer', 'ops.apparatus', 'quoted_revenue', 'UPDATE') then
    raise exception '012 posture: writer missing apparatus UPDATE(quoted_revenue)';
  end if;
  foreach col in array array['project_name','status','quote_revision','contract_value',
    'description','source_client_name','source_site_name','source_site_address',
    'source_site_city','source_site_state','source_site_zip','source','provenance_status',
    'updated_at'] loop
    if not has_column_privilege('ops_intake_writer', 'ops.projects', col, 'UPDATE') then
      raise exception '012 posture: writer missing projects UPDATE(%)', col;
    end if;
  end loop;
  -- negative: D2 - status leaves every login role (H3: has_column_privilege for column scope)
  foreach r in array array['ops_intake_writer', 'ops_api'] loop
    if has_column_privilege(r, 'ops.apparatus', 'status', 'INSERT')
       or has_column_privilege(r, 'ops.apparatus', 'status', 'UPDATE') then
      raise exception '012 posture: % holds apparatus.status privilege', r;
    end if;
    foreach t in array array['ops.revenue_recognition_event', 'ops.completion_attestation',
      'ops.billing_application', 'ops.billing_application_line', 'ops.billing_application_draft'] loop
      foreach p in array array['INSERT', 'UPDATE', 'DELETE'] loop
        if has_table_privilege(r, t, p) then
          raise exception '012 posture: % holds % on %', r, p, t;
        end if;
      end loop;
    end loop;
    if has_table_privilege(r, 'ops.projects', 'DELETE')
       or has_table_privilege(r, 'ops.apparatus', 'DELETE')
       or has_table_privilege(r, 'ops.tasks', 'DELETE')
       or has_table_privilege(r, 'ops.scope_quote', 'DELETE')
       or has_table_privilege(r, 'ops.scope_quote_line', 'DELETE') then
      raise exception '012 posture: % holds a forbidden DELETE', r;
    end if;
  end loop;
  if has_table_privilege('ops_api', 'ops.apparatus', 'INSERT')
     or has_table_privilege('ops_api', 'ops.scopes', 'INSERT') then
    raise exception '012 posture: ops_api can fabricate (INSERT on apparatus/scopes)';
  end if;
  -- F-012-5: defense-in-depth negative asserts for ops_api, mirroring the status asserts
  -- above (clean today per the grant matrix; guards against future drift adding an
  -- accidental ops_api grant on the provenance column or the scope/quote/task tables).
  if has_column_privilege('ops_api', 'ops.apparatus', 'provenance_status', 'UPDATE') then
    raise exception '012 posture: ops_api holds apparatus UPDATE(provenance_status)';
  end if;
  foreach t in array array['ops.scopes', 'ops.scope_quote', 'ops.scope_quote_line',
    'ops.tasks', 'ops.projects'] loop
    foreach p in array array['INSERT', 'UPDATE', 'DELETE'] loop
      if has_table_privilege('ops_api', t, p) then
        raise exception '012 posture: ops_api holds % on %', p, t;
      end if;
    end loop;
  end loop;
  -- writer must NOT execute any of the 9; api must execute EXACTLY the 4 recognition fns
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
    where has_function_privilege('ops_intake_writer', to_regprocedure(s.sig), 'EXECUTE')
  ) then
    raise exception '012 posture: ops_intake_writer can EXECUTE a mutation fn';
  end if;
  if exists (
    select 1 from unnest(array[
      'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.issue_billing_application(uuid,uuid,text)',
      'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.discard_draft_billing_application(uuid,uuid)',
      'ops.void_billing_application(uuid,uuid,text)'
    ]) s(sig)
    where has_function_privilege('ops_api', to_regprocedure(s.sig), 'EXECUTE')
  ) then
    raise exception '012 posture: ops_api can EXECUTE a deferred billing fn';
  end if;
  -- F-012-1: writer needs the index-predicate helper; ops_api must NOT hold it.
  if not has_function_privilege(
    'ops_intake_writer',
    'ops._intake_source_format_text(ops.intake_source_format)'::regprocedure,
    'EXECUTE'
  ) then
    raise exception '012 posture: writer missing EXECUTE on intake source-format helper';
  end if;
  if has_function_privilege(
    'ops_api',
    'ops._intake_source_format_text(ops.intake_source_format)'::regprocedure,
    'EXECUTE'
  ) then
    raise exception '012 posture: ops_api unexpectedly holds EXECUTE on intake source-format helper';
  end if;
  -- M2 (S7.7 positive): ops_api MUST hold EXECUTE on the 4 recognition fns. This is the
  -- ONLY guard on ops_dev/prod applies (pytest does not run there); a dropped GRANT EXECUTE
  -- fails LOUD here instead of silently breaking the recognition API.
  if exists (
    select 1 from unnest(array[
      'ops.attest_apparatus_complete(uuid,uuid,text)',
      'ops.revoke_completion_attestation(uuid,uuid,text)',
      'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
      'ops.reverse_recognition(uuid,uuid,text)'
    ]) s(sig)
    where not has_function_privilege('ops_api', to_regprocedure(s.sig), 'EXECUTE')
  ) then
    raise exception '012 posture: ops_api is MISSING EXECUTE on a recognition fn';
  end if;
  -- R2: the 11 ops views are postgres-owned and NOT security_invoker
  select count(*) into n
  from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
  where ns.nspname = 'ops' and c.relkind = 'v';
  if n <> 11 then
    raise exception '012 posture: expected 11 ops views, found % (view drift - re-ground R2)', n;
  end if;
  if exists (
    select 1
    from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
    where ns.nspname = 'ops' and c.relkind = 'v'
      and (c.relowner <> 'postgres'::regrole
        or exists (select 1 from pg_options_to_table(c.reloptions) o
                   where o.option_name = 'security_invoker'
                     and lower(o.option_value) in ('true', 'on', '1')))
  ) then
    raise exception '012 posture: an ops view is not postgres-owned/non-invoker (R2)';
  end if;
end $$;

-- [6] H2: completion-guard tightening (required) -----------------------------------------
-- Replaces the 009 guard. NEW: provenance_status may not change while status='Complete',
-- REGARDLESS of ops.completion_ctx - this makes "the ctx GUC is inert to login roles" true
-- by construction (D4). Grounded: no DEFINER fn legitimately changes provenance while
-- status='Complete' (approve stamps provenance at status='Not Started'; attest/revoke
-- change status, not provenance); recognized-then-reapprove is blocked earlier by the
-- _conflict_kind frozen gate. The trigger itself (009:70-71) is untouched.
create or replace function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $$
declare
  new_g boolean := (new.status='Complete' and new.provenance_status='approved');
  old_g boolean;
begin
  if tg_op = 'INSERT' then
    if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
    end if;
  else  -- UPDATE
    -- H2 (012): ctx-independent.
    if old.status = 'Complete' and new.provenance_status is distinct from old.provenance_status then
      raise exception 'apparatus %: provenance_status may not change while status=Complete', new.id;
    end if;
    old_g := (old.status='Complete' and old.provenance_status='approved');
    if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
    end if;
  end if;
  return new;
end; $$;
