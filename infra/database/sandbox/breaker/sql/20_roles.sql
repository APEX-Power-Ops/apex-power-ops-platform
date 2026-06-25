-- Scoped sandbox roles. NO BYPASSRLS/SUPERUSER/CREATEDB/CREATEROLE. No DB/schema grants here;
-- grants are clone-local (made by make_viewer.sh / make_codex_clone.sh).
-- Passwords read from ENV via \getenv (psql 16+; container psql is 17.10) — NEVER argv.
\getenv ro_pw    TCC_BREAKER_RO_PW
\getenv codex_pw TCC_BREAKER_CODEX_PW
do $$ begin
  if not exists (select 1 from pg_roles where rolname='tcc_breaker_ro') then
    create role tcc_breaker_ro login;
  end if;
  if not exists (select 1 from pg_roles where rolname='tcc_breaker_codex_79audit') then
    create role tcc_breaker_codex_79audit login;
  end if;
end $$;
alter role tcc_breaker_ro            password :'ro_pw';
alter role tcc_breaker_codex_79audit password :'codex_pw';
-- belt-and-suspenders: ensure no dangerous attributes
alter role tcc_breaker_ro            nosuperuser nocreatedb nocreaterole nobypassrls;
alter role tcc_breaker_codex_79audit nosuperuser nocreatedb nocreaterole nobypassrls;
