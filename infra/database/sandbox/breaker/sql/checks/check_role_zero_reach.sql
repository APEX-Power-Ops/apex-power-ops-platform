do $$
declare r record; bad int := 0;
begin
  for r in select datname from pg_database where datistemplate=false
           and datname not like 'tcc_breaker_codex_%' loop
    if has_database_privilege('tcc_breaker_codex_79audit', r.datname, 'CREATE') then
      raise warning 'LEAK: CREATE on db %', r.datname; bad := bad + 1;
    end if;
  end loop;
  if bad > 0 then raise exception 'role_zero_reach FAILED: % CREATE leak(s)', bad; end if;
  raise notice 'check_role_zero_reach OK (no CREATE on any non-codex db)';
end $$;
