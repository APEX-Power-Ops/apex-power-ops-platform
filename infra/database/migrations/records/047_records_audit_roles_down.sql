-- 047_records_audit_roles_down.sql
--
-- SUPABASE-COMPAT (compat lane Task 2.3, RATIFIED down posture): NOLOGIN owner roles
-- drop only after zero-owned guards; LOGIN credential roles are LEFT IN PLACE with
-- their records access revoked (never destroy a possibly operator-provisioned serving
-- credential; never read pg_authid - it is superuser-only, 42501 for non-super postgres).
BEGIN;
SET client_encoding TO 'UTF8';
-- records_fn_owner: NOLOGIN pure owner -> zero-owned guard (class+proc+schema) +
-- DROP OWNED + fail-loud.
--
-- Task 2.3 review fix: a bare `drop owned by records_fn_owner` deterministically 42501s
-- under the non-super managed-postgres applier, which holds only the admin-only creator
-- edge on records_fn_owner (set_option=inherit_option=false) - that edge does NOT confer
-- has_privs_of_role, which DROP OWNED BY requires. 047_down now mirrors 046_down's [d0]
-- treatment: take a TRANSIENT WITH SET + INHERIT TRUE grant into records_fn_owner for
-- current_user (the applier) immediately before DROP OWNED, so it holds records_fn_owner's
-- PRIVILEGES for that one statement. `drop role if exists records_fn_owner;` below then
-- destroys the role and, with it, the transient membership edge - same as 046_down relies
-- on. The DROP OWNED itself is KEPT (not removed): it is the defensive net that reaps any
-- ACL residue records_fn_owner holds (e.g. the schema-USAGE grant 048 gives it), making
-- 047_down self-sufficient regardless of 048_down's own revocation completeness.
do $$
declare n int;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and pg_get_userbyid(c.relowner)='records_fn_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner)='records_fn_owner')
  + (select count(*) from pg_namespace where nspname='records'
        and pg_get_userbyid(nspowner)='records_fn_owner')
    into n;
  if n>0 then raise exception '047_down: % object(s) still owned by records_fn_owner; refusing DROP OWNED', n; end if;
  execute format('grant records_fn_owner to %I with set true, inherit true, admin false', current_user);
end $$;
drop owned by records_fn_owner;
drop role if exists records_fn_owner;
do $$
begin
  if exists (select 1 from pg_roles where rolname='records_fn_owner')
    then raise exception '047_down: records_fn_owner survived drop'; end if;
  -- defensive: clear the transient current_user->records_fn_owner edge taken above.
  -- records_fn_owner is already dropped, so this is a no-op in the normal path (DROP ROLE
  -- removes the membership row); kept only so behavior does not depend on DROP OWNED / DROP
  -- ROLE edge-clearing semantics across executor privilege levels (mirrors 046_down [d6]).
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_fn_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_fn_owner from %I', current_user);
  end if;
end $$;
-- records_auditor: LOGIN credential role, password provisioned out-of-band -> RATIFIED
-- LOGIN-leave, mirroring 045_down [d5]. The non-super applier CANNOT read the true
-- password state (pg_authid is superuser-only, 42501; pg_roles.rolpassword is a masked
-- '********' and useless as a signal), so this is CONSERVATIVE and FAIL-SAFE: revoke the
-- role's records access and LEAVE the role object in place - never dropped - protecting
-- any operator serving credential. NO `select ... from pg_authid` anywhere; NO DROP ROLE.
-- A subsequent 047 up re-adopts it (create-if-not-exists). Role teardown on a disposable
-- target is the harness's job, not this credential-preserving down.
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_auditor') then
    return;
  end if;
  revoke usage on schema records from records_auditor;   -- safe if not granted
  -- (048_down already revoked SELECT on audit_log / it drops with the table)
  raise notice '047_down: records_auditor is a LOGIN credential role; records access revoked, role RETAINED (fail-safe leave).';
end $$;

COMMIT;
