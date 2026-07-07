-- 049_records_audit_triggers_down.sql - reverse 049: drop trg_audit from every
-- records table that carries it. Iterates pg_trigger joined to the records
-- tables (name-agnostic: whatever the writer-grant set produced), so the down
-- stays correct if the grant set changes. Transaction-wrapped for atomic
-- rollback under ON_ERROR_STOP=1.
--
-- SUPABASE-COMPAT (compat lane Task 2.5, plan Task-2.0 Step 3 mirror + D5):
-- adapted to apply as the NON-SUPER managed postgres applier. DROP TRIGGER needs
-- table OWNERSHIP; the trg_audit tables are records_owner-owned, so bare non-super
-- postgres 42501s. Wrap the drop loop in SET ROLE records_owner (via a transient
-- `grant records_owner to <applier> with set true, inherit false`; SET suffices -
-- you BECOME the owner - INHERIT is not needed). records_owner is present at
-- 049_down in the walk (046_down runs much later). The transient membership is
-- revoked before the terminal assert. The pg_trigger iteration + the zero-survive
-- assert are catalog reads (nspname/relname joins, NO records.*::regclass cast) that
-- run fine as plain non-super postgres, but the iteration runs inside the same owner
-- bracket for simplicity; the assert runs after RESET ROLE + revoke.
BEGIN;
SET client_encoding TO 'UTF8';

-- [d1] drop trg_audit from every records table carrying it, UNDER the table owner
-- records_owner (DROP TRIGGER requires ownership). Transient WITH SET into
-- records_owner; SET suffices. The transient membership is revoked immediately after.
do $$
declare r record;
begin
  execute format('grant records_owner to %I with set true, inherit false, admin false', current_user);
  set role records_owner;
  for r in
    select c.relname as table_name
      from pg_trigger tg
      join pg_class c on c.oid = tg.tgrelid
      join pg_namespace ns on ns.oid = c.relnamespace
     where ns.nspname = 'records'
       and tg.tgname = 'trg_audit'
       and not tg.tgisinternal
  loop
    execute format('drop trigger if exists trg_audit on records.%I', r.table_name);
  end loop;
  reset role;
  -- revoke the transient membership taken above.
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_owner from %I', current_user);
  end if;
end $$;

-- assert: no trg_audit trigger survives on any records table. Catalog read by
-- nspname/relname (NO records.*::regclass cast) - runs as plain non-super postgres.
do $$
declare leftover int;
begin
  select count(*) into leftover
    from pg_trigger tg
    join pg_class c on c.oid = tg.tgrelid
    join pg_namespace ns on ns.oid = c.relnamespace
   where ns.nspname = 'records'
     and tg.tgname = 'trg_audit'
     and not tg.tgisinternal;
  if leftover <> 0 then raise exception '049_down: % trg_audit trigger(s) survived the drop', leftover; end if;
end $$;

COMMIT;
