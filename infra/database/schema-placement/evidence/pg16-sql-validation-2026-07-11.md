# Collector catalog SQL — PostgreSQL 16 validation (Round-2, 2026-07-11)

Validates the collector's committed dependents SQL on **PostgreSQL 16** (prod's major) in a throwaway
`postgres:16-alpine` container on the Olares host — **not** prod (`fxoyniqnrlkxfligbxmg`); no production
access. Server reported **PostgreSQL 16.13** (`server_version_num = 160013`). All statements ran to
`EXIT=0`; the container was removed after the run.

- **Current committed query bundle:** `query_bundle_sha256 = 217ff3add2abdaca2fafa108f68e10490ee687ac9899b7762f1411d45e2de9db`
  (census-enablement Q3: added the `census_count` independent count query; re-validated on PG16.13 —
  `select count(*) … where nspname = any(schemas) and relkind in (r,v,m,p,f)` returned a count, EXIT=0.
  Supersedes the prior `065d49e0…` bundle, which itself superseded the Round-1 `aa7f…` in
  `dev-sql-validation-2026-07-11.md`).

## Objects built
`public.foo` (bigserial PK → owned seq; `parent_id` self-ref FK; RLS policy; BEFORE trigger),
`public.bar` (external FK → foo), `public.v_foo` (VIEW over foo), `publication p_foo` (FOR TABLE foo),
`publication p_all` (FOR ALL TABLES), `public.part` partitioned parent + `public.part_2026` child.

## Catalog features proven on PG16
`pg_options_to_table`, `pg_get_function_identity_arguments`, `pg_publication_namespace` (pnpubid/pnnspid),
`pg_inherits`, `puballtables`, `has_table_privilege`, `pg_depend`/`pg_rewrite`, and the new
`c.relkind`-filtered publication CTEs — all execute.

## Dependents classification (deduped `union`, relkind-filtered publications)
```
 object_id  |  dep_type   | direction | is_consumer | n
 public.foo | constraint  | inbound   | f           | 1   <- self-referential FK (NOT a consumer)
 public.foo | constraint  | inbound   | t           | 1   <- external FK bar->foo (consumer)
 public.foo | constraint  | outbound  | f           | 1   <- foo's own FK (NOT a consumer)
 public.foo | policy      | inbound   | f           | 1   <- RLS policy ON foo (NOT a consumer)
 public.foo | publication | inbound   | t           | 2   <- p_foo (explicit) + p_all (FOR ALL TABLES)
 public.foo | sequence    | inbound   | f           | 1   <- owned bigserial seq (NOT a consumer)
 public.foo | trigger     | inbound   | f           | 1   <- trigger ON foo (NOT a consumer)
 public.foo | view        | inbound   | t           | 1   <- v_foo (consumer; deduped from per-column rows)
 public.part| publication | inbound   | t           | 1   <- p_all (FOR ALL TABLES includes the base table)
 public.part| table       | inbound   | t           | 1   <- part_2026 inheritance child (consumer)
 -- public.v_foo: ZERO rows — a VIEW gets NO publication edge (relkind r/p filter; Claude R2 over-count fix)
```

- **foo external-consumer count = 4** (view + external FK + 2 publications); owned seq/trigger/policy,
  self-ref FK, and outbound FK are inventoried but EXCLUDED (finding #2).
- **`public.v_foo` returns ZERO edges** — the relkind-filtered `pubs_all`/`pubs_schema` no longer
  attribute a `FOR ALL TABLES` publication consumer to a view (Claude R2). Logical replication only
  publishes base/partitioned tables (relkind `r`/`p`).

## Conclusion
The current committed catalog SQL — including relkind-filtered `FOR ALL TABLES`/schema publications,
inheritance children, self-ref-aware inbound FKs, and per-edge `is_consumer` classification — executes
correctly on PostgreSQL 16.13 and classifies consumers vs inventory exactly as intended. The live prod
census still requires a separate read-only GO.
