-- 046_records_ownership.sql
-- Gate 5A: move every records object off the applier owner onto a NON-super
-- NOLOGIN records_owner, then FORCE ROW LEVEL SECURITY so RLS binds the owner.
-- Authoritative + reversible.
--
-- SUPABASE-COMPAT (compat lane Task 2.2, plan REV 5/5.1 + Task-2.0 decisions):
-- adapted to apply as the NON-SUPER managed postgres applier.
--   * Role attrs (A2): the NOSUPERUSER keyword is DROPPED from both create and
--     alter of records_owner (setting NOSUPERUSER needs superuser -> 42501; roles
--     are already non-super by default). The other NO* attrs (nologin/nobypassrls/
--     nocreatedb/nocreaterole/noreplication) are settable by non-super postgres
--     (Phase-0 A2) and are KEPT. The [4] posture asserts (rolsuper/rolbypassrls/
--     rolcanlogin/rolcreatedb/rolcreaterole/rolreplication all false) are the
--     forbidden-attr guard and STAY.
--   * records_reclaim_owner (D-B): 046 UP - not 045 - CREATES the persistent NOLOGIN
--     parking role if absent. It must exist before any 046_down can park objects on
--     it, and its existence lets 046 UP branch its transfer source (postgres/applier
--     FRESH vs records_reclaim_owner RE-UP after a prior down).
--   * Owner-aware transfer (D-B, choreography): a uniform-owner PRE-CHECK (mirror of
--     045's, matview 'm' included) asserts EVERY records object + schema is owned by
--     EXACTLY ONE of {the applier identity (postgres on managed Supabase; the
--     disposable applier locally - the FRESH case), records_reclaim_owner (a RE-UP
--     after 046_down)} and fails loud on mixed/other. The ALTER ... OWNER TO
--     records_owner transfer runs AS the current owner holding WITH SET membership
--     in records_owner (never SET ROLE'd into records_owner - it does not yet own
--     the objects); the RECEIVER records_owner is granted CREATE on schema records
--     by the CURRENT schema owner (a non-owner grant only WARNs + no-ops); the schema
--     owner is transferred LAST so object transfers keep schema CREATE.
--   * Owner-only follow-ups (FORCE RLS) run under SET ROLE records_owner AFTER the
--     transfer - INHERIT FALSE membership does not by itself confer owner authority.
--   * Membership assert (D-A trusted-applier): flags a pg_auth_members row only when
--     the edge is USABLE (set_option OR inherit_option) AND the member is a non-admin
--     role (member <> postgres). The trusted applier's transient WITH SET grant into
--     records_owner is revoked before the terminal asserts; postgres is EXEMPT.
BEGIN;
SET client_encoding TO 'UTF8';

-- [1] non-super NOLOGIN owner role (guarded + UNCONDITIONAL normalize) + both-
-- direction membership hardening. NOSUPERUSER dropped (needs superuser).
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_owner') then
    create role records_owner nologin nobypassrls;
  end if;
end $$;
-- normalize UNCONDITIONALLY: a pre-existing role may be in a wrong state.
alter role records_owner nologin nobypassrls nocreatedb nocreaterole noreplication;

-- [1a] records_reclaim_owner: the persistent down-direction parking owner (D-B).
-- Idempotent create + unconditional normalize. NOSUPERUSER dropped (needs superuser);
-- non-super-by-default covers it, and [4] asserts rolsuper=false.
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_reclaim_owner') then
    create role records_reclaim_owner nologin nobypassrls;
  end if;
end $$;
alter role records_reclaim_owner nologin nobypassrls nocreatedb nocreaterole noreplication;

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

-- [owner-pre] Uniform-owner PRE-CHECK (D-B rev 5.1) + set up the transfer source ---------
-- Assert EVERY records object (schema + all classes incl. matviews + all routines) is
-- owned by EXACTLY ONE role, and that role is the applier identity (FRESH) OR
-- records_reclaim_owner (a RE-UP after 046_down). Fail LOUD on mixed/other (a single-table
-- probe would false-green a botched transfer). Then grant records_owner the WITH SET
-- membership held BY the current owner and the schema CREATE it needs to receive ownership.
do $$
declare
  owner_oids oid[];
  v_owner_oid oid;
  v_owner text;
  v_me_oid oid;
begin
  -- current_user's OID by exact name lookup (never current_user::regrole - a text->regrole
  -- cast LOWERCASES an unquoted mixed-case name and would fail 42704 on the applier's name).
  select oid into v_me_oid from pg_roles where rolname = current_user;
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
    raise exception '046 owner pre-check: no records objects found (schema not applied)';
  end if;
  if array_length(owner_oids,1) <> 1 then
    raise exception '046 owner pre-check: records objects have MIXED owners %, expected exactly one',
      (select array_agg(pg_get_userbyid(x)) from unnest(owner_oids) x);
  end if;
  v_owner_oid := owner_oids[1];
  v_owner := pg_get_userbyid(v_owner_oid);
  if v_owner_oid <> v_me_oid
     and v_owner_oid is distinct from to_regrole('records_reclaim_owner')::oid then
    raise exception '046 owner pre-check: unexpected at-rest owner % (expected the applier % or records_reclaim_owner)',
      v_owner, current_user;
  end if;

  -- Transfer choreography (empirically pinned - Task 2.2 probes):
  --   * ALTER ... OWNER TO must run AS the object's CURRENT owner (SET-only membership does
  --     NOT satisfy the ownership check - "must be owner"; the current owner holds the schema
  --     rights the object-owner change needs). So ALL transfers (objects + schema) run under
  --     SET ROLE <current owner>.
  --   * ALTER SCHEMA ... OWNER TO additionally requires the EXECUTOR (= the current owner
  --     here) to hold CREATE on the DATABASE. records_owner / records_reclaim_owner do not
  --     hold it, so the applier - which CAN onward-grant database CREATE - grants the current
  --     owner a TRANSIENT database CREATE for the schema-owner step (revoked in [owner-post]).
  --   * The current owner also needs WITH SET in records_owner (the TARGET) to assign
  --     ownership; records_owner needs CREATE on schema records (granted by the current
  --     schema owner - a non-owner grant only WARNs + no-ops).
  -- FRESH: the current owner IS the applier (already holds database CREATE + owns the schema).
  -- RE-UP: the current owner is records_reclaim_owner (needs both transient grants).
  execute format('grant records_owner to %I with set true, inherit false, admin false', current_user);
  if v_owner_oid = v_me_oid then
    -- FRESH (applier-owned): applier already owns the schema + holds database CREATE.
    execute 'grant create on schema records to records_owner';
  else
    -- RE-UP (records_reclaim_owner-owned): the current owner records_reclaim_owner is the
    -- transfer EXECUTOR, so grant records_owner (the TARGET) TO it WITH SET (so it can
    -- SET ROLE/assign into records_owner); grant it a transient database CREATE (schema-owner
    -- step); grant records_owner schema CREATE AS the current schema owner. The applier takes
    -- transient WITH SET into records_reclaim_owner so it can SET ROLE into it. All transients
    -- revoked in [owner-post].
    execute format('grant records_reclaim_owner to %I with set true, inherit false, admin false', current_user);
    execute 'grant records_owner to records_reclaim_owner with set true, inherit false, admin false';
    execute format('grant create on database %I to records_reclaim_owner', current_database());
    execute 'set role records_reclaim_owner';
    execute 'grant create on schema records to records_owner';
    execute 'reset role';
  end if;
end $$;

-- [2] explicit ALTER OWNER of every records object + the schema, ALL under SET ROLE <current
-- owner> (FRESH: the applier; RE-UP: records_reclaim_owner). The current owner holds WITH SET
-- in records_owner (target) and - for the schema-owner ALTER - database CREATE (its own in
-- FRESH; the transient granted in [owner-pre] in RE-UP). Schema LAST so object transfers keep
-- schema CREATE.
do $$
declare r record; v_owner text;
begin
  select pg_get_userbyid(nspowner) into v_owner from pg_namespace where nspname='records';
  execute format('set role %I', v_owner);
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
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
  execute 'alter schema records owner to records_owner';   -- LAST
  reset role;
end $$;

-- [3] FORCE ROW LEVEL SECURITY on all base tables (RLS already enabled by 045).
-- Owner-only DDL: run under SET ROLE records_owner (INHERIT FALSE membership alone does
-- not confer the owner's authority for FORCE).
do $$
declare r record;
begin
  set role records_owner;
  for r in select c.relname from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
            where ns.nspname='records' and c.relkind='r'
  loop execute format('alter table records.%I force row level security', r.relname); end loop;
  reset role;
end $$;

-- [owner-post] revoke the transient grants taken in [owner-pre] BEFORE the terminal asserts,
-- so no usable applier->records_owner / applier->records_reclaim_owner / records_reclaim_
-- owner->records_owner membership edge and no transient database-CREATE grant survives 046.
do $$
begin
  -- FRESH transient: applier -> records_owner. Present only in the FRESH branch, but
  -- revoke-if-exists is safe unconditionally.
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_owner from %I', current_user);
  end if;
  -- RE-UP transients: applier -> records_reclaim_owner and records_reclaim_owner ->
  -- records_owner (membership), plus records_reclaim_owner's transient database CREATE.
  -- Revoke-if-exists (no-op in the FRESH branch).
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_reclaim_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_reclaim_owner from %I', current_user);
  end if;
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
               join pg_roles m on m.oid=am.member and m.rolname='records_reclaim_owner') then
    execute 'revoke records_owner from records_reclaim_owner';
  end if;
  if (select has_database_privilege('records_reclaim_owner', current_database(), 'CREATE')) then
    execute format('revoke create on database %I from records_reclaim_owner', current_database());
  end if;
end $$;

-- [4] posture asserts (authoritative) - three-catalog ownership + ALL role flags +
-- FORCE-RLS + pure-owner + D-A membership isolation + temp-authority residue.
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

  -- records_owner role flags: rolsuper=false is the compat-lane replacement for the
  -- dropped NOSUPERUSER keyword.
  select rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, rolcreaterole, rolreplication
    into su, brls, canlogin, cdb, crole, crepl from pg_roles where rolname='records_owner';
  if su or brls then raise exception '046: records_owner must be NOSUPERUSER + NOBYPASSRLS'; end if;
  if canlogin then raise exception '046: records_owner must be NOLOGIN'; end if;
  if cdb or crole or crepl then raise exception '046: records_owner must be NOCREATEDB/NOCREATEROLE/NOREPLICATION'; end if;

  -- records_reclaim_owner role flags (D-D): same forbidden-attr guard.
  select rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, rolcreaterole, rolreplication
    into su, brls, canlogin, cdb, crole, crepl from pg_roles where rolname='records_reclaim_owner';
  if su or brls then raise exception '046: records_reclaim_owner must be NOSUPERUSER + NOBYPASSRLS'; end if;
  if canlogin then raise exception '046: records_reclaim_owner must be NOLOGIN'; end if;
  if cdb or crole or crepl then raise exception '046: records_reclaim_owner must be NOCREATEDB/NOCREATEROLE/NOREPLICATION'; end if;

  select count(*) into n from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity;
  if n>0 then raise exception '046: % records table(s) not FORCE-RLS', n; end if;

  -- records_owner is a PURE owner (holds no ACL grants of its own).
  select count(*) into n from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid
   where ro.rolname='records_owner' and sd.deptype='a';
  if n>0 then raise exception '046: records_owner holds % ACL grant(s); must be a pure owner', n; end if;

  -- records_reclaim_owner owns NOTHING at the end of a successful UP (D-D): zero records
  -- objects across all three catalogs.
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and c.relkind in ('r','v','m','S')
        and pg_get_userbyid(c.relowner)='records_reclaim_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner)='records_reclaim_owner')
  + (select count(*) from pg_namespace where nspname='records'
        and pg_get_userbyid(nspowner)='records_reclaim_owner')
    into n;
  if n>0 then raise exception '046: records_reclaim_owner owns % records object(s) after UP; must own nothing', n; end if;

  -- D-A trusted-applier membership isolation: no NON-admin role holds a USABLE
  -- (set_option OR inherit_option) membership path INTO records_owner or
  -- records_reclaim_owner. The trusted postgres applier is EXEMPT (member <> postgres);
  -- admin-only edges (set=inherit=false) are not flagged.
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname in ('records_owner','records_reclaim_owner')
     join pg_roles m on m.oid=am.member
   where (am.set_option or am.inherit_option)
     and m.oid <> 'postgres'::regrole;
  if n>0 then raise exception '046: % non-admin role(s) hold a usable membership into an owner role (escalation path)', n; end if;

  -- temp-authority residue: the transient WITH SET grants taken for the transfer
  -- (applier->records_owner and records_reclaim_owner->records_owner) must be gone.
  -- Flag only USABLE (set_option OR inherit_option) edges: PG16 auto-grants the role's
  -- CREATOR an admin-only edge (set=inherit=false, admin=true, grantor=postgres) that a
  -- plain REVOKE does NOT remove; that admin-only creator edge is the trusted-applier
  -- residue D-A EXEMPTS and is NOT a usable transfer grant. A surviving SET/INHERIT edge
  -- from either transfer source WOULD be a real leak.
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
     join pg_roles m on m.oid=am.member
   where m.rolname in (current_user, 'records_reclaim_owner')
     and (am.set_option or am.inherit_option);
  if n>0 then raise exception '046: % usable transient owner-transfer grant(s) into records_owner survived', n; end if;
end $$;

COMMIT;
