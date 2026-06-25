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
  -- Prove the auth.*-referencing policies actually restored (the core preflight win — a missing auth
  -- stub fails the CREATE POLICY at restore). Match any auth.* fn in qual OR with_check (prod uses
  -- auth.role()/auth.jwt(), not necessarily auth.uid()).
  perform 1 from pg_policies where schemaname='tcc'
    and (coalesce(qual,'') || coalesce(with_check,'')) like '%auth.%';
  if not found then raise exception 'baseline: auth.*-referencing policy did not restore'; end if;
  raise notice 'check_baseline OK: % tables, % rls, % policies, % views', n_tables, n_rls, n_policies, n_views;
end $$;
