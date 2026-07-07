-- 048_records_audit_log.sql - append-only, metadata-minimal audit log + the
-- SECURITY DEFINER capture function. audit_log is FORCE-RLS so its owner
-- (records_fn_owner) is itself subject to the INSERT policy: the definer runs
-- as that owner, so without FORCE the policy would be a no-op (false-green).
--
-- SUPABASE-COMPAT (compat lane Task 2.4, plan REV 5 / Task-2.0 Step 3 + D6):
-- adapted to apply as the NON-SUPER managed postgres applier. After 046 the
-- records schema is owned by records_owner and (after 047) records_fn_owner is
-- the target object owner, so bare non-super postgres can neither CREATE in the
-- schema, nor ALTER OWNER to records_fn_owner, nor run the owner-only DDL without
-- transient authority. 046 revoked ITS OWN temp authority on completion, so 048
-- re-establishes its own:
--   * Temp authority (Step 3 / P1-c): grant records_owner + records_fn_owner to
--     postgres WITH SET (postgres can SET ROLE into either), and grant
--     records_fn_owner to records_owner WITH SET (so the CREATING owner
--     records_owner can transfer objects TO records_fn_owner). All INHERIT FALSE,
--     ADMIN FALSE. All revoked before the terminal asserts.
--   * Create under the schema owner: SET ROLE records_owner, then CREATE audit_log
--     + indexes + fn_audit_capture (owned by records_owner initially).
--   * Cross-role transfer AS records_owner (the current owner, holding WITH SET in
--     records_fn_owner): grant records_fn_owner a TRANSIENT CREATE (+USAGE) on
--     schema records issued BY the schema owner records_owner (PG16+ rule: the
--     RECEIVING owner must hold CREATE on the object's schema to RECEIVE ownership,
--     proven REQUIRED for cross-role transfer in PHASE0-FINDINGS Task 0.4 points
--     3/6; a non-owner GRANT only WARNs/no-ops so it MUST be issued by
--     records_owner); then alter table/function owner to records_fn_owner. Per the
--     corrected ownership-transfer rule the transfer runs AS the current owner
--     records_owner, NOT while set-role'd INTO records_fn_owner. The transient
--     CREATE is REVOKED before the asserts so the at-rest posture (:137-138 fn_owner
--     must NOT hold CREATE; :142-148 exact allowlist = USAGE-on-schema only) holds.
--   * Owner-only DDL under the NEW owner: SET ROLE records_fn_owner -> enable+force
--     RLS, create policies, revoke PUBLIC execute, grant SELECT on audit_log to
--     records_auditor (the table owner grants it).
--   * Schema-USAGE grants under the SCHEMA owner (D6): SET ROLE records_owner ->
--     grant usage on schema records to records_fn_owner + records_auditor (a
--     non-owner grant only WARNs/no-ops, so the schema owner must issue them).
--   * Revoke ALL temp authority BEFORE the terminal asserts; the definer-safety /
--     FORCE-RLS / no-PUBLIC / exact-allowlist asserts are READ-ONLY introspection
--     that runs as plain non-super postgres. A temp-authority residue assert (046
--     [4] form: flag only USABLE (set_option OR inherit_option) edges, postgres
--     EXEMPT) closes out.
BEGIN;
SET client_encoding TO 'UTF8';

-- [t0] re-establish 048's OWN transient authority (046 revoked its own). postgres
-- takes WITH SET into both owner roles (to SET ROLE into either); records_owner
-- takes WITH SET into records_fn_owner (so, AS the creating owner, it can transfer
-- objects to records_fn_owner). All INHERIT FALSE / ADMIN FALSE. All revoked in [t5].
do $$
begin
  execute format('grant records_owner to %I with set true, inherit false, admin false', current_user);
  execute format('grant records_fn_owner to %I with set true, inherit false, admin false', current_user);
  execute 'grant records_fn_owner to records_owner with set true, inherit false, admin false';
end $$;

-- [t1] CREATE the audit objects under the SCHEMA owner records_owner (they are
-- created owned by records_owner; bare non-super postgres cannot CREATE in the
-- records_owner-owned schema). Stay SET ROLE records_owner through the transfer.
do $$
begin
  set role records_owner;

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

  -- the shared SECURITY DEFINER capture function (created owned by records_owner).
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
      -- changed_columns is the caller-intent signal. Exclude updated_at: the BEFORE
      -- trigger fn_set_updated_at sets NEW.updated_at := now() on EVERY update, so it
      -- always differs from OLD and would pollute the diff. ORDER BY for determinism.
      select array_agg(o.key order by o.key) into changed
        from jsonb_each(to_jsonb(OLD)) o join jsonb_each(to_jsonb(NEW)) n on n.key=o.key
       where o.value is distinct from n.value
         and o.key <> 'updated_at';
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

  -- [t2] cross-role transfer AS records_owner. PG16+ rule: the RECEIVING owner
  -- records_fn_owner must hold CREATE on schema records to RECEIVE ownership (proven
  -- REQUIRED for cross-role transfer, PHASE0-FINDINGS Task 0.4 points 3/6). Grant it
  -- a TRANSIENT CREATE + USAGE here, issued BY the schema owner records_owner (we are
  -- SET ROLE records_owner, so this is the correct grantor; a non-owner grant only
  -- WARNs/no-ops). The USAGE is also the permanent grant [t4] re-issues; the CREATE
  -- is transient and REVOKED in [t5] before the asserts. Then transfer AS records_owner
  -- (the current owner, holding WITH SET in records_fn_owner) - NOT set-role'd into it.
  grant usage  on schema records to records_fn_owner;
  grant create on schema records to records_fn_owner;   -- TRANSIENT (revoked in [t5])
  alter table    records.audit_log       owner to records_fn_owner;
  alter function records.fn_audit_capture() owner to records_fn_owner;

  reset role;
end $$;

-- [t3] owner-only DDL under the NEW owner records_fn_owner (INHERIT FALSE membership
-- alone does not confer owner authority; SET ROLE does). enable+force RLS, the
-- INSERT/SELECT policies, revoke PUBLIC execute on the definer, and the audit_log
-- SELECT grant to records_auditor (the TABLE owner records_fn_owner grants it).
do $$
begin
  set role records_fn_owner;
  alter table records.audit_log enable row level security;
  alter table records.audit_log force row level security;   -- owner is subject to RLS
  drop policy if exists p_audit_log_ins on records.audit_log;
  create policy p_audit_log_ins on records.audit_log for insert to records_fn_owner with check (true);
  drop policy if exists p_audit_log_sel on records.audit_log;
  create policy p_audit_log_sel on records.audit_log for select to records_auditor using (true);
  -- append-only: no UPDATE/DELETE policy for anyone. No app-role grant/policy.
  -- new functions get default PUBLIC EXECUTE; Gate-3 Tier-5 asserts no PUBLIC on
  -- records routines, so revoke it (both a hardening + keeps Tier 5 green).
  revoke execute on function records.fn_audit_capture() from public;
  grant select on records.audit_log to records_auditor;
  reset role;
end $$;

-- [t4] schema-USAGE grants under the SCHEMA owner records_owner (D6: cross-owner
-- object/schema grants issue AS the current owner; a non-owner GRANT only WARNs +
-- no-ops). records_fn_owner needs USAGE to REACH audit_log (045 revoked PUBLIC usage
-- on records; ownership != schema usage). records_auditor needs USAGE or its SELECT
-- is unreachable. (records_fn_owner's USAGE was already granted in [t2], but re-issue
-- idempotently here so the grant is owned by this step's authority; grant is a no-op
-- if already present.)
do $$
begin
  set role records_owner;
  grant usage on schema records to records_fn_owner;
  grant usage on schema records to records_auditor;   -- required or SELECT is unreachable
  reset role;
end $$;

-- [t5] revoke the transfer-only transient authority: the transient CREATE on schema
-- records granted to records_fn_owner in [t2] (issued as the schema owner
-- records_owner), plus the two records_fn_owner memberships taken in [t0]
-- (postgres->records_fn_owner and records_owner->records_fn_owner). After this,
-- records_fn_owner holds EXACTLY USAGE on schema records (no CREATE) and no usable
-- membership survives into it. The postgres->records_owner membership from [t0] is
-- deliberately KEPT alive here: the definer-safety assert below resolves records.*
-- objects via ::regclass/::regprocedure casts, which require schema USAGE, so that
-- block runs UNDER SET ROLE records_owner (the schema owner, implicit USAGE). It is
-- revoked in [t5b] immediately after, BEFORE the temp-authority residue assert.
do $$
begin
  -- revoke the transient CREATE as the schema owner (records_fn_owner keeps USAGE).
  set role records_owner;
  revoke create on schema records from records_fn_owner;
  reset role;
  -- revoke the two records_fn_owner memberships (revoke-if-exists is safe unconditionally).
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_fn_owner'
               join pg_roles m on m.oid=am.member and m.rolname='records_owner') then
    execute 'revoke records_fn_owner from records_owner';
  end if;
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_fn_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_fn_owner from %I', current_user);
  end if;
end $$;

-- asserts: definer safety (three load-bearing checks) + FORCE-RLS + no-PUBLIC-execute.
-- These resolve records.* objects via ::regprocedure/::regclass casts, which require
-- USAGE on schema records; bare non-super postgres had its PUBLIC USAGE revoked by 045,
-- so the block runs UNDER SET ROLE records_owner (the schema owner, implicit USAGE). The
-- checks are otherwise READ-ONLY; running as the owner does not change any result
-- (has_schema_privilege takes an explicit role argument; ownership/secdef/FORCE/PUBLIC-
-- EXECUTE are role-independent facts).
do $$
declare owner text; secdef bool; cfg text[]; forced bool; pub int;
begin
  set role records_owner;
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
  reset role;
end $$;

-- [t5b] revoke the last transient membership: postgres->records_owner (kept alive for the
-- definer-safety assert above). After this, NO usable transient owner-role membership from
-- postgres survives, so the temp-authority residue assert [t6] runs clean. The exact-
-- allowlist assert below needs NO schema USAGE (name-string catalog reads + has_schema_
-- privilege + pg_catalog ::regclass only), so it runs as plain non-super postgres.
do $$
begin
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_owner from %I', current_user);
  end if;
end $$;

-- records_fn_owner EXACT ALLOWLIST (rev 5; adversarial-audit-hardened). The prior
-- per-object relacl/proacl scans were structurally blind to cross-schema grants,
-- column grants (attacl), type/domain grants (typacl), DATABASE-level grants
-- (datacl), default privileges (pg_default_acl - incl. the schema-agnostic
-- defaclnamespace=0 case), and shared (dbid=0) grants. A single pg_shdepend
-- deptype='a' exclusivity assert closes them ALL: the ONLY permitted ACL edge is
-- USAGE on schema records in THIS database. Ownership is deptype='o' (excluded), and
-- a self-GRANT on the owned audit_log produces NO 'a' row, so there is no false-fail
-- (validated on PG17). USAGE-present/CREATE-deny/PUBLIC-deny/owner/existence are kept
-- as complementary positive/negative gates the exclusivity count alone cannot isolate.
do $$
declare
  gcnt int;
  v_schema  text := 'records';
  v_owner   text := 'records_owner';
  v_fnowner text := 'records_fn_owner';
  v_schema_oid oid;
begin
  -- (0) existence + ownership FIRST (well-defined schema oid; fail-closed).
  select oid into v_schema_oid from pg_namespace where nspname = v_schema;
  if v_schema_oid is null then
    raise exception '048: schema % does not exist (run after 045/048 GRANT)', v_schema; end if;
  if (select nspowner from pg_namespace where oid = v_schema_oid) <> (select oid from pg_roles where rolname = v_owner)
    then raise exception '048: schema % owner drifted (expected %); ownership confers implicit USAGE+CREATE', v_schema, v_owner; end if;
  -- (1) positive reachability: the definer must effectively hold USAGE.
  if not has_schema_privilege(v_fnowner, v_schema, 'USAGE')
    then raise exception '048: % lacks USAGE on schema % (definer cannot reach audit_log)', v_fnowner, v_schema; end if;
  -- (1b) the USAGE must be an EXPLICIT grant, not effective-via-PUBLIC/membership.
  if not exists (select 1 from pg_namespace ns, lateral aclexplode(ns.nspacl) a join pg_roles g on g.oid = a.grantee
                 where ns.oid = v_schema_oid and g.rolname = v_fnowner and a.privilege_type = 'USAGE')
    then raise exception '048: % lacks an EXPLICIT USAGE ACL grant on schema % (effective USAGE may leak via PUBLIC/membership)', v_fnowner, v_schema; end if;
  -- (2) deny CREATE (an ACL bit on the same namespace row exclusivity cannot isolate).
  if has_schema_privilege(v_fnowner, v_schema, 'CREATE')
    then raise exception '048: % must NOT hold CREATE on schema %', v_fnowner, v_schema; end if;
  -- (3) 045 regression guard: PUBLIC holds no schema privilege.
  if has_schema_privilege('public', v_schema, 'USAGE') or has_schema_privilege('public', v_schema, 'CREATE')
    then raise exception '048: PUBLIC holds USAGE/CREATE on schema % (migration 045 REVOKE reverted)', v_schema; end if;
  -- (4) exact allowlist: the ONLY permitted ACL edge is USAGE on records in this DB.
  select count(*) into gcnt from pg_shdepend s join pg_roles r on r.oid = s.refobjid
   where r.rolname = v_fnowner and s.deptype = 'a'
     and not (s.classid = 'pg_namespace'::regclass
              and s.dbid  = (select oid from pg_database where datname = current_database())
              and s.objid = v_schema_oid);
  if gcnt > 0 then raise exception '048: % holds % ACL grant edge(s) beyond USAGE on schema % (cross-schema/column/type/default-priv/database/shared-object escalation)', v_fnowner, gcnt, v_schema; end if;
end $$;

-- [t6] temp-authority residue assert (046 [4] form): no NON-admin role holds a USABLE
-- (set_option OR inherit_option) membership INTO records_owner or records_fn_owner.
-- The three transient transfer grants (postgres->records_owner, postgres->
-- records_fn_owner, records_owner->records_fn_owner) were revoked in [t5]; the trusted
-- postgres applier is EXEMPT (member <> postgres) and admin-only creator edges
-- (set=inherit=false) are not flagged. A surviving SET/INHERIT edge from a non-admin
-- role would be a real escalation path.
do $$
declare n int;
begin
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname in ('records_owner','records_fn_owner')
     join pg_roles m on m.oid=am.member
   where (am.set_option or am.inherit_option)
     and m.oid <> 'postgres'::regrole;
  if n>0 then raise exception '048: % non-admin role(s) hold a usable membership into an owner role (escalation path)', n; end if;
end $$;

COMMIT;
