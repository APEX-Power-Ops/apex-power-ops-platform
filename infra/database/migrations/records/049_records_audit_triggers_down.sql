-- 049_records_audit_triggers_down.sql - reverse 049: drop trg_audit from every
-- records table that carries it. Iterates pg_trigger joined to the records
-- tables (name-agnostic: whatever the writer-grant set produced), so the down
-- stays correct if the grant set changes. Transaction-wrapped for atomic
-- rollback under ON_ERROR_STOP=1.
BEGIN;
SET client_encoding TO 'UTF8';
do $$
declare r record;
begin
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
end $$;
-- assert: no trg_audit trigger survives on any records table.
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
