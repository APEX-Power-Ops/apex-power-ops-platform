do $$
declare n_tables int; n_rls int; n_policies int; n_views int;
begin
  select count(*) into n_tables  from pg_class c join pg_namespace s on s.oid=c.relnamespace
         where s.nspname='tcc' and c.relkind='r';
  select count(*) into n_rls     from pg_class c join pg_namespace s on s.oid=c.relnamespace
         where s.nspname='tcc' and c.relkind='r' and c.relrowsecurity;
  select count(*) into n_policies from pg_policies where schemaname='tcc';
  select count(*) into n_views   from pg_class c join pg_namespace s on s.oid=c.relnamespace
         where s.nspname='tcc' and c.relkind='v';
  if n_tables < 2 then raise exception 'baseline: expected >=2 tcc tables, got %', n_tables; end if;
  if n_rls   < 1 then raise exception 'baseline: expected >=1 RLS table, got %', n_rls; end if;
  if n_policies < 1 then raise exception 'baseline: expected >=1 policy, got %', n_policies; end if;
  if n_views < 1 then raise exception 'baseline: expected >=1 view, got %', n_views; end if;
  -- prove the auth.uid()-referencing policy actually restored (the core preflight win)
  perform 1 from pg_policies where schemaname='tcc' and coalesce(qual,'') like '%auth.uid()%';
  if not found then raise exception 'baseline: auth.uid()-referencing policy did not restore'; end if;
  raise notice 'check_baseline OK: % tables, % rls, % policies, % views', n_tables, n_rls, n_policies, n_views;
end $$;
