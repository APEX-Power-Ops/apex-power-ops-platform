-- 046_records_ownership_down.sql - reverse 046 to the postgres pre-state.
BEGIN;
SET client_encoding TO 'UTF8';

-- [d1] NO FORCE on all base tables.
do $$
declare r record;
begin
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='r'
  loop execute format('alter table records.%I no force row level security', r.relname); end loop;
end $$;

-- [d2] reassign every records object + schema explicitly back to postgres.
do $$
declare r record;
begin
  for r in select c.relkind, c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind in ('r','m')
  loop execute format('alter table records.%I owner to postgres', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='v'
  loop execute format('alter view records.%I owner to postgres', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='S'
  loop execute format('alter sequence records.%I owner to postgres', r.relname); end loop;
  for r in select p.proname, pg_get_function_identity_arguments(p.oid) as args
             from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='records'
  loop execute format('alter function records.%I(%s) owner to postgres', r.proname, r.args); end loop;
  execute 'alter schema records owner to postgres';
end $$;

-- [d3] GUARD: refuse DROP OWNED unless records_owner owns ZERO objects across
-- ALL relevant catalogs (a DROP OWNED on an incomplete reassign would DELETE
-- the missed object). MUST cover pg_class (tables/views/matviews/sequences),
-- pg_proc (functions), AND pg_namespace (the records schema itself - a missed
-- schema would be DROPped CASCADE).
do $$
declare n int;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and c.relkind in ('r','v','m','S')
        and pg_get_userbyid(c.relowner)='records_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner)='records_owner')
  + (select count(*) from pg_namespace where nspname='records'
        and pg_get_userbyid(nspowner)='records_owner')
    into n;
  if n>0 then raise exception '046_down: % records object(s) still owned by records_owner (class/proc/schema); refusing DROP OWNED', n; end if;
end $$;

-- [d4] clear any ACL residue (provably none), drop the role, fail loud if it survives.
drop owned by records_owner;
drop role if exists records_owner;
do $$
begin
  if exists (select 1 from pg_roles where rolname='records_owner')
    then raise exception '046_down: records_owner survived drop'; end if;
end $$;

COMMIT;
