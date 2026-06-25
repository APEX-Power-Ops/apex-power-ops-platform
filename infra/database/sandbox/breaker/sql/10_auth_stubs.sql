-- Stub Supabase auth.* functions so prod tcc policies (60 reference auth.uid()) restore on a
-- plain PG17 host. Bodies are inert; sandbox roles never execute policy bodies (viewer: RLS
-- disabled clone-local; codex: owner-exempt). Used at BOTH fixture-source build and baseline restore.
create schema if not exists auth;
create or replace function auth.uid()  returns uuid  language sql stable as $$ select null::uuid $$;
create or replace function auth.role() returns text  language sql stable as $$ select null::text $$;
create or replace function auth.jwt()  returns jsonb language sql stable as $$ select '{}'::jsonb $$;
