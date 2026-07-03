-- 046_records_ownership.sql
-- Gate 5A: move every records object off the superuser owner onto a
-- non-superuser records_owner, then FORCE ROW LEVEL SECURITY so RLS binds the
-- owner. Authoritative + reversible. Runs as the superuser admin; superuser
-- bypasses FORCE, so this migration's own DDL is unaffected.
BEGIN;
SET client_encoding TO 'UTF8';

-- [0] pre-state: every records object (tables/views/matviews/sequences +
-- FUNCTIONS) AND the records schema itself must be owned by postgres. Counts
-- span pg_class + pg_proc + pg_namespace (fn_set_updated_at is a function; a
-- pg_class-only check would miss it and the schema).
do $$
declare n int;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and c.relkind in ('r','v','m','S')
        and pg_get_userbyid(c.relowner) <> 'postgres')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner) <> 'postgres')
  + (select case when pg_get_userbyid(nspowner) <> 'postgres' then 1 else 0 end
      from pg_namespace where nspname='records')
    into n;
  if n > 0 then raise exception '046 pre-state: % records object(s)/schema not owned by postgres', n; end if;
end $$;

-- [1] non-superuser owner role (guarded + UNCONDITIONAL normalize) + both-
-- direction membership hardening.
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_owner') then
    create role records_owner nologin nosuperuser nobypassrls;
  end if;
end $$;
-- normalize UNCONDITIONALLY: a pre-existing role may be in a wrong state.
alter role records_owner nologin nosuperuser nobypassrls nocreatedb nocreaterole noreplication;
do $$
declare r record;
begin
  for r in select m.rolname as who from pg_auth_members am
             join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
             join pg_roles m on m.oid=am.member
  loop execute format('revoke records_owner from %I', r.who); end loop;
  for r in select g.rolname as who from pg_auth_members am
             join pg_roles ro on ro.oid=am.member and ro.rolname='records_owner'
             join pg_roles g on g.oid=am.roleid
  loop execute format('revoke %I from records_owner', r.who); end loop;
end $$;

-- [2] explicit ALTER OWNER of every records object + the schema (NOT reassign-owned).
do $$
declare r record;
begin
  for r in select c.relkind, c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind in ('r','m')
  loop execute format('alter table records.%I owner to records_owner', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='v'
  loop execute format('alter view records.%I owner to records_owner', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='S'
  loop execute format('alter sequence records.%I owner to records_owner', r.relname); end loop;
  for r in select p.proname, pg_get_function_identity_arguments(p.oid) as args
             from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='records'
  loop execute format('alter function records.%I(%s) owner to records_owner', r.proname, r.args); end loop;
  execute 'alter schema records owner to records_owner';
end $$;

-- [3] FORCE ROW LEVEL SECURITY on all base tables (RLS already enabled by 045).
do $$
declare r record;
begin
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='r'
  loop execute format('alter table records.%I force row level security', r.relname); end loop;
end $$;

-- [4] posture asserts (authoritative) - three-catalog ownership + ALL role flags.
do $$
declare n int; su bool; brls bool; canlogin bool; cdb bool; crole bool; crepl bool;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and c.relkind in ('r','v','m','S')
        and pg_get_userbyid(c.relowner) <> 'records_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner) <> 'records_owner')
  + (select case when pg_get_userbyid(nspowner) <> 'records_owner' then 1 else 0 end
      from pg_namespace where nspname='records')
    into n;
  if n>0 then raise exception '046: % records object(s)/schema not owned by records_owner', n; end if;
  select rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, rolcreaterole, rolreplication
    into su, brls, canlogin, cdb, crole, crepl from pg_roles where rolname='records_owner';
  if su or brls then raise exception '046: records_owner must be NOSUPERUSER + NOBYPASSRLS'; end if;
  if canlogin then raise exception '046: records_owner must be NOLOGIN'; end if;
  if cdb or crole or crepl then raise exception '046: records_owner must be NOCREATEDB/NOCREATEROLE/NOREPLICATION'; end if;
  select count(*) into n from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity;
  if n>0 then raise exception '046: % records table(s) not FORCE-RLS', n; end if;
  select count(*) into n from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid
   where ro.rolname='records_owner' and sd.deptype='a';
  if n>0 then raise exception '046: records_owner holds % ACL grant(s); must be a pure owner', n; end if;
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
     join pg_roles m on m.oid=am.member where m.rolcanlogin;
  if n>0 then raise exception '046: % LOGIN role(s) are members of records_owner', n; end if;
end $$;

COMMIT;
