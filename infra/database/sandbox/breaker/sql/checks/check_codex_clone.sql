do $$
declare not_owned int;
begin
  select count(*) into not_owned
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='tcc' and c.relkind in ('r','S','v')
      and pg_get_userbyid(c.relowner) <> 'tcc_breaker_codex_79audit';
  if not_owned <> 0 then raise exception 'codex_clone: % tcc objects not owned by codex role', not_owned; end if;
  if not has_database_privilege('tcc_breaker_codex_79audit', current_database(), 'CONNECT')
     then raise exception 'codex_clone: codex role cannot CONNECT'; end if;
  raise notice 'check_codex_clone OK (codex owns all tcc objects)';
end $$;
