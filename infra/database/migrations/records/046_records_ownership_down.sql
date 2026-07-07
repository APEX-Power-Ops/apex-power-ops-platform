-- 046_records_ownership_down.sql - reverse 046.
--
-- SUPABASE-COMPAT (compat lane Task 2.2, plan REV 5 D-B): `grant postgres to <custom>`
-- is REJECTED (42501) on managed Supabase, so 046_down CANNOT reclaim ownership to
-- postgres. Instead it parks every records object + the schema on the persistent
-- NOLOGIN records_reclaim_owner (the proven cross-role reverse transfer), then drops
-- records_owner (which then owns nothing) but KEEPS records_reclaim_owner. Records
-- objects therefore have TWO at-rest owners across down/up cycles: the applier identity
-- (fresh, pre-046) OR records_reclaim_owner (post-046_down). A subsequent 046 up branches
-- on whichever it finds.
--
-- Ordering (explicit + reviewer-checked): NO FORCE ROW LEVEL SECURITY is owner-only DDL,
-- so it runs FIRST, under SET ROLE records_owner, WHILE records_owner still owns the
-- tables - BEFORE the ownership reassign. The reassign then moves everything (schema LAST)
-- to records_reclaim_owner. The zero-owned GUARD + DROP ROLE close out.
BEGIN;
SET client_encoding TO 'UTF8';

-- [d0] pre-check: assert records_owner exists and owns the records objects uniformly
-- (mirror of 045's pre-check guards: no-objects / mixed / unexpected-single-owner,
-- matview 'm' included). 046_down is only meaningful with records_owner as the at-rest
-- owner; fail loud otherwise so a botched/partial state does not silently half-revert.
do $$
declare owner_oids oid[]; v_owner_oid oid; v_owner text;
begin
  if not exists (select 1 from pg_roles where rolname='records_owner') then
    raise exception '046_down: records_owner does not exist (nothing to reverse)';
  end if;
  select array_agg(distinct o) into owner_oids from (
    select nspowner as o from pg_namespace where nspname='records'
    union all
    select relowner from pg_class c join pg_namespace n on n.oid=c.relnamespace
      where n.nspname='records' and c.relkind in ('r','v','m','S','p')
    union all
    select proowner from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='records'
  ) s;
  if array_length(owner_oids,1) is null then
    raise exception '046_down owner pre-check: no records objects found';
  end if;
  if array_length(owner_oids,1) <> 1 then
    raise exception '046_down owner pre-check: records objects have MIXED owners %, expected exactly one',
      (select array_agg(pg_get_userbyid(x)) from unnest(owner_oids) x);
  end if;
  v_owner_oid := owner_oids[1];
  v_owner := pg_get_userbyid(v_owner_oid);
  if v_owner_oid is distinct from to_regrole('records_owner')::oid then
    raise exception '046_down owner pre-check: unexpected at-rest owner % (expected records_owner)', v_owner;
  end if;
  -- ensure the parking role exists (idempotent) before it can receive objects.
  if not exists (select 1 from pg_roles where rolname='records_reclaim_owner') then
    create role records_reclaim_owner nologin nobypassrls;
  end if;
  execute 'alter role records_reclaim_owner nologin nobypassrls nocreatedb nocreaterole noreplication';
  -- take transient WITH SET + INHERIT into records_owner so the applier can (a) SET ROLE into
  -- it for the owner-only DDL + the transfer, and (b) hold its PRIVILEGES for the terminal
  -- `drop owned by records_owner` ([d5]) - DROP OWNED requires role PRIVILEGES (has_privs_of_
  -- role), which WITH SET alone (INHERIT FALSE) does not confer. Revoked in [d6]; and records_
  -- owner is dropped in [d5] which removes the edge regardless. The transient is on the
  -- trusted applier (postgres on the branch = D-A exempt), and [d7] asserts only records_
  -- reclaim_owner isolation, so this INHERIT does not weaken any terminal invariant.
  execute format('grant records_owner to %I with set true, inherit true, admin false', current_user);
end $$;

-- [d1] NO FORCE (owner-only) run FIRST, under SET ROLE records_owner, WHILE records_owner
-- still owns the tables - the up-mirror of 046 [3]. Then set up the reassign (same
-- empirically-pinned choreography as 046 UP): ALL transfers run AS the current owner
-- records_owner (SET-only membership does NOT satisfy the ownership check). records_owner
-- needs WITH SET into records_reclaim_owner (the TARGET, to assign) and - for the schema-
-- owner ALTER - a TRANSIENT database CREATE (the applier onward-grants it; records_owner does
-- not hold it). records_reclaim_owner needs CREATE on schema records, granted by records_owner
-- (the current schema owner - a non-owner grant only WARNs + no-ops).
do $$
declare r record;
begin
  set role records_owner;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='r'
  loop execute format('alter table records.%I no force row level security', r.relname); end loop;
  -- as the current schema owner (records_owner), grant the receiver schema CREATE.
  execute 'grant create on schema records to records_reclaim_owner';
  reset role;
  -- records_owner needs WITH SET in records_reclaim_owner (assign) + transient database CREATE
  -- (schema-owner step). Both revoked before the guard/drop.
  execute 'grant records_reclaim_owner to records_owner with set true, inherit false, admin false';
  execute format('grant create on database %I to records_owner', current_database());
end $$;

-- [d2] reassign every records object + schema to records_reclaim_owner, ALL under SET ROLE
-- records_owner (it owns objects+schema, holds WITH SET into records_reclaim_owner, and holds
-- the transient database CREATE for the schema-owner step). Schema LAST so object transfers
-- keep schema CREATE.
do $$
declare r record;
begin
  set role records_owner;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind in ('r','m')
  loop execute format('alter table records.%I owner to records_reclaim_owner', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='v'
  loop execute format('alter view records.%I owner to records_reclaim_owner', r.relname); end loop;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='S'
  loop execute format('alter sequence records.%I owner to records_reclaim_owner', r.relname); end loop;
  for r in select p.proname, pg_get_function_identity_arguments(p.oid) as args
             from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='records'
  loop execute format('alter function records.%I(%s) owner to records_reclaim_owner', r.proname, r.args); end loop;
  execute 'alter schema records owner to records_reclaim_owner';   -- LAST
  reset role;
end $$;

-- [d3] revoke records_owner's transient grants taken in [d1] (WITH SET into records_reclaim_
-- owner + database CREATE) BEFORE the guard/drop. drop owned by records_owner in [d5] would
-- also clear them, but revoke explicitly so the pre-drop state is clean and the behavior does
-- not depend on DROP OWNED edge semantics across executor privilege levels.
do $$
begin
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_reclaim_owner'
               join pg_roles m on m.oid=am.member and m.rolname='records_owner') then
    execute 'revoke records_reclaim_owner from records_owner';
  end if;
  if (select has_database_privilege('records_owner', current_database(), 'CREATE')) then
    execute format('revoke create on database %I from records_owner', current_database());
  end if;
end $$;

-- [d4] GUARD: refuse DROP OWNED unless records_owner owns ZERO records objects across ALL
-- relevant catalogs (a DROP OWNED on an incomplete reassign would DELETE the missed
-- object). Covers pg_class (tables/views/MATVIEWS/sequences), pg_proc (functions), AND
-- pg_namespace (the records schema itself - a missed schema would be DROPped CASCADE).
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

-- [d5] clear any ACL residue (provably none), drop records_owner ONLY (KEEP
-- records_reclaim_owner - it is the persistent parking owner and now owns the objects),
-- fail loud if records_owner survives.
drop owned by records_owner;
drop role if exists records_owner;
do $$
begin
  if exists (select 1 from pg_roles where rolname='records_owner')
    then raise exception '046_down: records_owner survived drop'; end if;
  if not exists (select 1 from pg_roles where rolname='records_reclaim_owner')
    then raise exception '046_down: records_reclaim_owner must persist (parking owner)'; end if;
end $$;

-- [d6] revoke the transient applier->records_owner membership taken in [d0]. records_owner
-- is dropped, so this is defensive (a membership row referencing a dropped role is removed
-- by the DROP), and it also clears the edge on any true-superuser path where DROP ROLE and
-- the membership catalog interact differently.
do $$
begin
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_owner from %I', current_user);
  end if;
end $$;

-- [d7] D-A / D-D residue: records_reclaim_owner (now the at-rest owner) must hold no
-- USABLE membership path from/to a NON-admin role (postgres EXEMPT). Any admin-only creator
-- edge (set=inherit=false) into records_reclaim_owner is NOT flagged; the applier/postgres
-- identity is exempt. Asserts the non-admin roles stay isolated.
do $$
declare n int;
begin
  select count(*) into n from pg_auth_members am
     join pg_roles a on a.oid=am.roleid
     join pg_roles b on b.oid=am.member
   where (a.rolname='records_reclaim_owner' or b.rolname='records_reclaim_owner')
     and (am.set_option or am.inherit_option)
     and am.roleid <> 'postgres'::regrole
     and am.member <> 'postgres'::regrole;
  if n>0 then raise exception '046_down: % usable membership edge(s) touch records_reclaim_owner from/to a non-admin role', n; end if;
end $$;

COMMIT;
