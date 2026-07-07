-- 047_records_audit_roles.sql - the two audit roles. No grants to operational
-- tables (auditor reads audit_log only, granted via policy in 048). No password.
--
-- SUPABASE-COMPAT (compat lane Task 2.3, plan REV 5 / PHASE0-FINDINGS A2 + D3):
-- adapted to apply as the NON-SUPER managed postgres applier.
--   * Role attrs: the NOSUPERUSER keyword is DROPPED from all four role statements
--     (setting it needs superuser -> 42501; a role created by non-super postgres is
--     NOSUPERUSER by default). The other NO* attrs (nobypassrls/noreplication/
--     nocreatedb/nocreaterole) are settable by non-super postgres (Phase-0 A2) and
--     are KEPT. rolsuper=false is proven by the [asserts] below (which read pg_roles).
--   * NO ownership transfer here (047 only creates the two audit roles), so there is
--     NO owner-context choreography - unlike 046/048.
--   * Final membership assert refined per D-A (REV 5, PHASE0-FINDINGS D3): count only
--     USABLE (set_option OR inherit_option) edges and EXEMPT the trusted postgres
--     applier. When non-super postgres CREATEs a role, PG16 leaves an un-removable
--     admin-only creator edge (grantor=supabase_admin, member=postgres,
--     set=inherit=false); that edge is non-usable and postgres is custody-controlled,
--     so it is exempt. A REAL usable membership involving an audit role and a non-admin
--     role still trips. The both-direction revoke loop is KEPT (harmless) but not relied on.
BEGIN;
SET client_encoding TO 'UTF8';
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_fn_owner') then
    create role records_fn_owner nologin nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname='records_auditor') then
    create role records_auditor login nobypassrls;  -- NO password (out-of-band)
  end if;
end $$;
-- normalize UNCONDITIONALLY (pre-existing roles may be in a wrong state).
alter role records_fn_owner nologin nobypassrls nocreatedb nocreaterole noreplication;
alter role records_auditor  login   nobypassrls nocreatedb nocreaterole noreplication;  -- NO password
-- both-direction membership hardening for both roles.
do $$
declare r record; owner text;
begin
  foreach owner in array array['records_fn_owner','records_auditor'] loop
    for r in select m.rolname as who from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname=owner
               join pg_roles m on m.oid=am.member
    loop execute format('revoke %I from %I', owner, r.who); end loop;
    for r in select g.rolname as who from pg_auth_members am
               join pg_roles ro on ro.oid=am.member and ro.rolname=owner
               join pg_roles g on g.oid=am.roleid
    loop execute format('revoke %I from %I', r.who, owner); end loop;
  end loop;
end $$;
-- asserts: ALL role flags per role (canlogin differs) + pure-owner + zero USABLE
-- membership edges touching EITHER audit role in EITHER direction (postgres-exempt).
do $$
declare n int; rec record;
begin
  for rec in select rolname, rolsuper, rolbypassrls, rolcanlogin,
                    rolcreatedb, rolcreaterole, rolreplication
               from pg_roles where rolname in ('records_fn_owner','records_auditor') loop
    if rec.rolsuper or rec.rolbypassrls then
      raise exception '047: % is super/bypassrls', rec.rolname; end if;
    if rec.rolcreatedb or rec.rolcreaterole or rec.rolreplication then
      raise exception '047: % has createdb/createrole/replication', rec.rolname; end if;
    if rec.rolname='records_fn_owner' and rec.rolcanlogin then
      raise exception '047: records_fn_owner must be NOLOGIN'; end if;
    if rec.rolname='records_auditor' and not rec.rolcanlogin then
      raise exception '047: records_auditor must be LOGIN'; end if;
  end loop;
  -- At 047 the role is BARE (zero grants). 048 adds EXACTLY one grant - USAGE on
  -- schema records - so the SECURITY DEFINER can reach records.audit_log; 048 +
  -- Tier 6 assert that exact allowlist. Here we only prove 047 itself grants nothing.
  select count(*) into n from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid
   where ro.rolname='records_fn_owner' and sd.deptype='a';
  if n>0 then raise exception '047: records_fn_owner holds ACL grants at 047 (must be bare; schema USAGE is added in 048)'; end if;
  -- D-A trusted-applier membership isolation (REV 5, PHASE0-FINDINGS D3): no USABLE
  -- (set_option OR inherit_option) membership edge touches EITHER audit role in EITHER
  -- direction, EXCEPT the trusted postgres applier when it is the MEMBER of the edge.
  -- The (set_option OR inherit_option) usable-filter already drops the non-usable
  -- admin-only creator edge (roleid=audit_role, member=postgres, set=inherit=false), so
  -- the ONLY exemption needed is member-only (am.member <> postgres): exempt the trusted
  -- applier when IT is the member. We deliberately do NOT exempt roleid=postgres: a
  -- USABLE edge where roleid=postgres and member=records_auditor (the LOGIN auditor is a
  -- usable member OF postgres -> a SET ROLE postgres escalation) MUST be caught; a
  -- roleid-side exemption would have masked it. This matches 045/046/048/049 (member-only).
  select count(*) into n from pg_auth_members am
     join pg_roles rl on rl.oid=am.roleid
     join pg_roles m on m.oid=am.member
   where (rl.rolname in ('records_fn_owner','records_auditor')
          or m.rolname in ('records_fn_owner','records_auditor'))
     and (am.set_option or am.inherit_option)
     and am.member <> 'postgres'::regrole;
  if n>0 then raise exception '047: % usable membership edge(s) touch an audit role; must be zero', n; end if;
end $$;

COMMIT;
