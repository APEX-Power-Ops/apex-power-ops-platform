-- Residual-ownership VISIBILITY (run on the real codex clone in Task 7; result recorded in the
-- manifest, NOT fail-closed). The ownership transfer in make_codex_clone.sh covers tcc r/S/v; any
-- postgres-owned FUNCTION/TYPE in tcc stays postgres-owned. Harmless for a read+write-table-data+
-- create-scratch audit (codex can still EXECUTE functions), but make the residual visible.
select
  (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
     where n.nspname='tcc' and pg_get_userbyid(p.proowner)='postgres') as residual_functions_postgres,
  (select count(*) from pg_type t join pg_namespace n on n.oid=t.typnamespace
     where n.nspname='tcc' and pg_get_userbyid(t.typowner)='postgres') as residual_types_postgres;
