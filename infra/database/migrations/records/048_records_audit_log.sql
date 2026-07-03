-- 048_records_audit_log.sql - append-only, metadata-minimal audit log + the
-- SECURITY DEFINER capture function. audit_log is FORCE-RLS so its owner
-- (records_fn_owner) is itself subject to the INSERT policy: the definer runs
-- as that owner, so without FORCE the policy would be a no-op (false-green).
BEGIN;
SET client_encoding TO 'UTF8';

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

alter table records.audit_log owner to records_fn_owner;
alter table records.audit_log enable row level security;
alter table records.audit_log force row level security;   -- owner is subject to RLS
drop policy if exists p_audit_log_ins on records.audit_log;
create policy p_audit_log_ins on records.audit_log for insert to records_fn_owner with check (true);
drop policy if exists p_audit_log_sel on records.audit_log;
create policy p_audit_log_sel on records.audit_log for select to records_auditor using (true);
-- append-only: no UPDATE/DELETE policy for anyone. No app-role grant/policy.
-- The SECURITY DEFINER capture function runs as its owner records_fn_owner; it
-- OWNS audit_log (INSERT is implicit) but still needs schema USAGE to REACH it
-- (045 revoked PUBLIC usage on records; ownership != schema usage). Exact
-- allowlist: USAGE only, no table grants beyond ownership (ops-012 precedent).
grant usage on schema records to records_fn_owner;
grant usage on schema records to records_auditor;   -- required or SELECT is unreachable
grant select on records.audit_log to records_auditor;

-- the shared SECURITY DEFINER capture function.
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
    select array_agg(o.key) into changed
      from jsonb_each(to_jsonb(OLD)) o join jsonb_each(to_jsonb(NEW)) n on n.key=o.key
     where o.value is distinct from n.value;
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
alter function records.fn_audit_capture() owner to records_fn_owner;
-- new functions get default PUBLIC EXECUTE; Gate-3 Tier-5 asserts no PUBLIC on
-- records routines, so revoke it (both a hardening + keeps Tier 5 green).
revoke execute on function records.fn_audit_capture() from public;

-- asserts: definer safety (three load-bearing checks) + FORCE-RLS + no-PUBLIC-execute.
do $$
declare owner text; secdef bool; cfg text[]; forced bool; pub int;
begin
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

COMMIT;
