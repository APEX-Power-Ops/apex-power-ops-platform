do $$
declare bad int;
begin
  -- (1) NO tcc table remains RLS-enabled (clone-local DISABLE worked on every one)
  select count(*) into bad from pg_class c join pg_namespace s on s.oid=c.relnamespace
    where s.nspname='tcc' and c.relkind='r' and c.relrowsecurity;
  if bad <> 0 then raise exception 'viewer: % tcc tables still RLS-enabled', bad; end if;
  -- (2) ro can CONNECT
  if not has_database_privilege('tcc_breaker_ro', current_database(), 'CONNECT')
     then raise exception 'viewer: tcc_breaker_ro cannot CONNECT'; end if;
  -- (3) ro has SELECT on EVERY tcc table
  select count(*) into bad from pg_class c join pg_namespace s on s.oid=c.relnamespace
    where s.nspname='tcc' and c.relkind='r' and not has_table_privilege('tcc_breaker_ro', c.oid, 'SELECT');
  if bad <> 0 then raise exception 'viewer: ro lacks SELECT on % tcc tables', bad; end if;
  -- (4) ro has NO write on ANY tcc table
  select count(*) into bad from pg_class c join pg_namespace s on s.oid=c.relnamespace
    where s.nspname='tcc' and c.relkind='r' and has_table_privilege('tcc_breaker_ro', c.oid, 'INSERT, UPDATE, DELETE');
  if bad <> 0 then raise exception 'viewer: ro has write on % tcc tables', bad; end if;
  raise notice 'check_viewer OK (RLS disabled on all tcc tables; ro read-only on all)';
end $$;
