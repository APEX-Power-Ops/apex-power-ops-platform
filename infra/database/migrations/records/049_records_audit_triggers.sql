-- 049_records_audit_triggers.sql - attach fn_audit_capture to exactly the
-- tables records_intake_writer may INSERT/UPDATE (the writer-grant set),
-- passing each table's single-column PK name. Excludes audit_log (recursion)
-- and neta_table_source_links (owner-only, D7).
BEGIN;
SET client_encoding TO 'UTF8';
do $$
declare t record; pk_col text; npk int;
begin
  for t in
    select distinct table_name from information_schema.role_column_grants
     where grantee='records_intake_writer' and table_schema='records'
       and privilege_type in ('INSERT','UPDATE')
  loop
    -- single-column PK name for this table
    select count(*) into npk
      from pg_index i join pg_class c on c.oid=i.indrelid
      join pg_namespace ns on ns.oid=c.relnamespace
     where ns.nspname='records' and c.relname=t.table_name and i.indisprimary;
    if npk <> 1 then raise exception '049: %.% has no single primary key', 'records', t.table_name; end if;
    select a.attname into pk_col
      from pg_index i join pg_class c on c.oid=i.indrelid
      join pg_namespace ns on ns.oid=c.relnamespace
      join pg_attribute a on a.attrelid=c.oid and a.attnum = any(i.indkey)
     where ns.nspname='records' and c.relname=t.table_name and i.indisprimary
       and array_length(i.indkey,1)=1;
    execute format('drop trigger if exists trg_audit on records.%I', t.table_name);
    execute format(
      'create trigger trg_audit after insert or update or delete on records.%I '
      'for each row execute function records.fn_audit_capture(%L)', t.table_name, pk_col);
  end loop;
end $$;
-- assert: trigger set == writer-grant set; no trigger on audit_log or source_links.
do $$
declare got int; want int;
begin
  select count(distinct table_name) into want from information_schema.role_column_grants
   where grantee='records_intake_writer' and table_schema='records'
     and privilege_type in ('INSERT','UPDATE');
  select count(*) into got from pg_trigger tg join pg_class c on c.oid=tg.tgrelid
    join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal;
  if got <> want then raise exception '049: trigger count % <> writer-grant table count %', got, want; end if;
  if exists (select 1 from pg_trigger tg join pg_class c on c.oid=tg.tgrelid
             join pg_namespace ns on ns.oid=c.relnamespace
             where ns.nspname='records' and c.relname in ('audit_log','neta_table_source_links')
               and tg.tgname='trg_audit')
    then raise exception '049: trg_audit present on audit_log or source_links'; end if;
end $$;

COMMIT;
