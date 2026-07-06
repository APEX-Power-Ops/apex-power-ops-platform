-- 048_records_audit_log_down.sql - reverse 048. Drops the SECURITY DEFINER
-- capture function and the audit_log table (its INSERT/SELECT policies and the
-- SELECT grant to records_auditor drop WITH the table), then revokes the two
-- schema-USAGE grants 048 added. Runs BEFORE 047_down in the walk-reversal, so
-- both records_fn_owner and records_auditor still exist here. (047_down's own
-- `DROP OWNED BY records_fn_owner` would also clear the fn_owner USAGE, but 048
-- owns the grant, so 048_down revokes it for symmetry.) ASCII-only, transaction
-- wrapped to match 045/047 - a mid-file failure rolls back atomically.
--
-- SUPABASE-COMPAT (compat lane Task 2.4, plan Task-2.0 Step 3 mirror + D6):
-- adapted to apply as the NON-SUPER managed postgres applier. Two operations that
-- 42501 under bare non-super postgres, each fixed under the correct authority:
--   * The object DROPs: audit_log + fn_audit_capture are records_fn_owner-owned;
--     DROP TABLE / DROP FUNCTION require OWNERSHIP -> SET ROLE records_fn_owner (via
--     a TRANSIENT `grant records_fn_owner to postgres with set true, inherit false`).
--     SET suffices for DROP because you BECOME the owner - INHERIT is NOT needed
--     here (unlike 047_down's `drop owned by`, which needs has_privs_of_role).
--   * The schema-USAGE REVOKEs: `revoke usage on schema records from <role>` requires
--     the executor to OWN schema records (or hold GRANT OPTION), which bare non-super
--     postgres does not - schema records is owned by records_owner in the walk. So run
--     the revokes under the SCHEMA owner's authority (D6; the 048_down instance of
--     047_down's auditor-revoke fix): derive the current schema owner and, if it is
--     not the applier, take a transient WITH SET grant, SET ROLE into it, revoke,
--     reset, revoke the transient. SET (not INHERIT) suffices - REVOKE authority comes
--     from acting AS the schema owner. records_owner is present at 048_down in the walk
--     (046_down runs AFTER 048_down).
-- All transient grants are revoked before COMMIT. records_fn_owner + records_auditor
-- are NOT dropped here (047_down owns records_fn_owner's drop; records_auditor is a
-- LOGIN-leave credential role) - they persist through 048_down.
BEGIN;
SET client_encoding TO 'UTF8';

-- [d1] drop the fn_owner-owned objects under SET ROLE records_fn_owner (DROP requires
-- OWNERSHIP; bare non-super postgres is not the owner). Transient WITH SET into
-- records_fn_owner; SET suffices (you BECOME the owner). This runs FIRST, BEFORE the
-- schema-USAGE revoke [d2]: records_fn_owner needs USAGE on schema records to RESOLVE
-- and DROP objects within it, and [d2] revokes that USAGE - so dropping after the
-- revoke would 42501 ("permission denied for schema records"). Order within the block:
-- function first (it references records.audit_log by name at runtime, not a hard catalog
-- dep, so either order is safe, but drop the definer entry point first). The INSERT/
-- SELECT policies and the audit_log SELECT grant to records_auditor drop WITH the table.
do $$
begin
  execute format('grant records_fn_owner to %I with set true, inherit false, admin false', current_user);
  set role records_fn_owner;
  drop function if exists records.fn_audit_capture();
  drop table if exists records.audit_log;
  reset role;
  -- revoke the transient membership taken above.
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_fn_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_fn_owner from %I', current_user);
  end if;
end $$;

-- [d2] revoke the two schema-USAGE grants 048 added, under the SCHEMA owner's authority
-- (D6). Runs AFTER the object drops [d1] (see above). Idempotent: harmless no-op if a
-- grant is already absent. Derive the owner dynamically (records_owner in the walk; the
-- applier only in a theoretical fresh case). SET (not INHERIT) suffices - REVOKE authority
-- comes from acting AS the schema owner, not from has_privs_of_role.
do $$
declare v_schema_owner text;
begin
  select pg_get_userbyid(nspowner) into v_schema_owner from pg_namespace where nspname='records';
  if v_schema_owner is null then
    return;   -- schema absent (nothing to revoke)
  end if;
  if v_schema_owner = current_user then
    revoke usage on schema records from records_auditor;    -- safe if not granted
    revoke usage on schema records from records_fn_owner;
  else
    execute format('grant %I to %I with set true, inherit false, admin false', v_schema_owner, current_user);
    execute format('set role %I', v_schema_owner);
    revoke usage on schema records from records_auditor;    -- idempotent no-op if absent
    revoke usage on schema records from records_fn_owner;
    reset role;
    execute format('revoke %I from %I', v_schema_owner, current_user);
  end if;
end $$;

COMMIT;
