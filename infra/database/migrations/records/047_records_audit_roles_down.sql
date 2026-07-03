-- 047_records_audit_roles_down.sql
BEGIN;
SET client_encoding TO 'UTF8';
-- records_fn_owner: NOLOGIN pure owner -> zero-owned guard (class+proc+schema) +
-- DROP OWNED + fail-loud.
do $$
declare n int;
begin
  select
    (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
      where ns.nspname='records' and pg_get_userbyid(c.relowner)='records_fn_owner')
  + (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='records' and pg_get_userbyid(p.proowner)='records_fn_owner')
  + (select count(*) from pg_namespace where nspname='records'
        and pg_get_userbyid(nspowner)='records_fn_owner')
    into n;
  if n>0 then raise exception '047_down: % object(s) still owned by records_fn_owner; refusing DROP OWNED', n; end if;
end $$;
drop owned by records_fn_owner;
drop role if exists records_fn_owner;
do $$ begin
  if exists (select 1 from pg_roles where rolname='records_fn_owner')
    then raise exception '047_down: records_fn_owner survived drop'; end if;
end $$;
-- records_auditor: LOGIN, password provisioned out-of-band -> DEV-7 guard,
-- mirroring 045_down. NO `DROP OWNED` (the LOGIN-role hazard Gate 3 avoided):
-- explicit DB-scoped revokes, then DROP ROLE ONLY if it is passwordless
-- (harness / disposable-DB case); RETAIN with a NOTICE if password-bearing.
do $$
declare has_pw bool;
begin
  if not exists (select 1 from pg_roles where rolname='records_auditor') then
    return;
  end if;
  revoke usage on schema records from records_auditor;   -- safe if not granted
  -- (048_down already revoked SELECT on audit_log / it drops with the table)
  select (rolpassword is not null) into has_pw from pg_authid where rolname='records_auditor';
  if coalesce(has_pw, true) then   -- unreadable pw => assume present => fail-safe RETAIN
    raise notice '047_down: records_auditor is password-bearing; RETAINED (DEV-7 guard).';
  else
    drop role records_auditor;
  end if;
end $$;

COMMIT;
