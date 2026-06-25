-- Real-mode EXACT-count gate (run ONLY against the real prod baseline in Task 7). Fail-closed on any
-- deviation from the probed prod facts — catches a partial/duplicated 813MB restore that the loose
-- check_baseline.sql (>= thresholds) would miss. (On the synthetic fixture this RAISEs by design.)
do $$
declare t int; v int; s int; i int; rls int; pol int;
begin
  select count(*) into t   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='r';
  select count(*) into v   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='v';
  select count(*) into s   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='S';
  select count(*) into i   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='i';
  select count(*) into rls from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='tcc' and c.relkind='r' and c.relrowsecurity;
  select count(*) into pol from pg_policies where schemaname='tcc';
  if t<>91    then raise exception 'exact: tables %, want 91', t; end if;
  if v<>2     then raise exception 'exact: views %, want 2', v; end if;
  if s<>30    then raise exception 'exact: sequences %, want 30', s; end if;
  if i<>190   then raise exception 'exact: indexes %, want 190', i; end if;
  if rls<>60  then raise exception 'exact: rls tables %, want 60', rls; end if;
  if pol<>120 then raise exception 'exact: policies %, want 120', pol; end if;
  raise notice 'check_baseline_exact OK (91/2/30/190, rls 60, pol 120)';
end $$;
