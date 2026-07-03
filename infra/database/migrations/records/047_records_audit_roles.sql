-- 047_records_audit_roles.sql - the two audit roles. No grants to operational
-- tables (auditor reads audit_log only, granted via policy in 048). No password.
BEGIN;
SET client_encoding TO 'UTF8';
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_fn_owner') then
    create role records_fn_owner nologin nosuperuser nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname='records_auditor') then
    create role records_auditor login nosuperuser nobypassrls;  -- NO password (out-of-band)
  end if;
end $$;
-- normalize UNCONDITIONALLY (pre-existing roles may be in a wrong state).
alter role records_fn_owner nologin nosuperuser nobypassrls nocreatedb nocreaterole noreplication;
alter role records_auditor  login   nosuperuser nobypassrls nocreatedb nocreaterole noreplication;  -- NO password
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
-- asserts: ALL role flags per role (canlogin differs) + pure-owner + zero
-- membership edges touching EITHER audit role in EITHER direction.
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
  -- zero membership edges (either direction) for EITHER audit role - proves the
  -- both-direction revoke above actually landed (not just a LOGIN-member check).
  select count(*) into n from pg_auth_members am
   where am.roleid in (select oid from pg_roles where rolname in ('records_fn_owner','records_auditor'))
      or am.member in (select oid from pg_roles where rolname in ('records_fn_owner','records_auditor'));
  if n>0 then raise exception '047: % membership edge(s) touch an audit role; must be zero', n; end if;
end $$;

COMMIT;
