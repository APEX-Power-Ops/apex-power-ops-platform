do $$
declare leaked int;
begin
  select count(*) into leaked from information_schema.tables t
   where t.table_schema not in ('pg_catalog','information_schema')
     and has_table_privilege('tcc_breaker_codex_79audit',
           format('%I.%I', t.table_schema, t.table_name), 'SELECT, INSERT, UPDATE, DELETE');
  if leaked <> 0 then raise exception 'sibling leak: codex role has table privs on % objects in %',
       leaked, current_database(); end if;
  raise notice 'check_sibling_no_table_priv OK on % (leaked=0)', current_database();
end $$;
