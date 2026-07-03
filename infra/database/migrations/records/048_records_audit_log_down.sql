-- 048_records_audit_log_down.sql - reverse 048. Drops the SECURITY DEFINER
-- capture function and the audit_log table (its INSERT/SELECT policies and the
-- SELECT grant to records_auditor drop WITH the table), then revokes the two
-- schema-USAGE grants 048 added. Runs BEFORE 047_down in the walk-reversal, so
-- both records_fn_owner and records_auditor still exist here. (047_down's own
-- `DROP OWNED BY records_fn_owner` would also clear the fn_owner USAGE, but 048
-- owns the grant, so 048_down revokes it for symmetry.) ASCII-only, transaction
-- wrapped to match 045/047 - a mid-file failure rolls back atomically.
BEGIN;
SET client_encoding TO 'UTF8';

-- revoke the schema USAGE grants 048 added (safe if already absent; both roles
-- still exist at this point in the reversal). audit_log SELECT grant + the
-- INSERT/SELECT policies are removed implicitly by the DROP TABLE below.
revoke usage on schema records from records_auditor;
revoke usage on schema records from records_fn_owner;

-- drop the capture function and the audit_log table. Order: function first
-- (it references records.audit_log by name at runtime, not a hard catalog dep,
-- so either order is safe, but drop the definer entry point first).
drop function if exists records.fn_audit_capture();
drop table if exists records.audit_log;

COMMIT;
