-- Schema-CREATE hardening (run while connected to EACH sibling DB in Task 7's privilege matrix).
-- Asserts the codex role cannot CREATE in the `public` schema of this DB (the pre-PG15 default
-- foothold). Already false on PG17.10 — cheap insurance against a base-image/grant drift. Fail-closed.
do $$
begin
  if has_schema_privilege('tcc_breaker_codex_79audit','public','CREATE') then
    raise exception 'schema-CREATE leak: codex role has CREATE on public in %', current_database();
  end if;
  raise notice 'check_schema_create OK on % (codex has no CREATE on public)', current_database();
end $$;
