# Collector catalog SQL — PostgreSQL 16 validation (2026-07-11)

Per the audit tranche: validate the collector's catalog SQL on **PostgreSQL 16** (prod's major),
not only PG17. Executed in a throwaway `postgres:16-alpine` container on the Olares host — **not**
prod (`fxoyniqnrlkxfligbxmg`); no production access. Server reported **PostgreSQL 16.13** (identical
major/minor to prod). All statements ran to `EXIT=0`; the container was removed after the run.

## Objects built (representative of every edge class)
`public.foo` (bigserial PK → owned sequence; `parent_id` self-referential FK; RLS policy; BEFORE
trigger), `public.bar` (external FK → foo), `public.v_foo` (view over foo), `publication p_foo` (FOR
TABLE foo), `publication p_all` (FOR ALL TABLES), `public.part` partitioned parent + `public.part_2026`
child.

## Catalog features proven on PG16
- `current_setting('server_version_num')`, `version()`, `pg_roles` marker array — OK.
- `pg_options_to_table(c.reloptions)` security_invoker detection — `v_foo` → `is_security_definer_view = t`.
- `has_table_privilege('anon', 'public.foo', 'SELECT')` — OK.
- `pg_get_function_identity_arguments`, `pg_publication_namespace` (pnpubid/pnnspid), `pg_inherits`,
  `puballtables` — all execute.

## Dependents classification (committed SQL, deduped `union`)
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
 public.part| publication | inbound   | t           | 1   <- p_all (FOR ALL TABLES includes part)
 public.part| table       | inbound   | t           | 1   <- part_2026 inheritance child (consumer)
```

**External-consumer count for `public.foo` = 4** (deduped `union`): view(1) + external FK(1) +
publications(2). The owned sequence, trigger, policy, self-referential FK, and outbound FK are
inventoried in `dependent_objects` but correctly EXCLUDED from `found_consumers` (finding #2). The
view is counted once — the per-column `pg_depend` rows are collapsed by the `union` + Python
edge-key dedup. (An ad-hoc `union all` count during validation reported 5 because it skipped the
dedup and double-counted the view's two column references; the collector's real path dedups.)

## Conclusion
The expanded catalog SQL — including `FOR ALL TABLES` / schema-level publications (finding #7),
inheritance children (finding #7), self-ref-aware inbound FKs, and per-edge `is_consumer`
classification (finding #2) — executes correctly on PostgreSQL 16.13 and classifies consumers vs
inventory exactly as intended. The live prod census still requires a separate read-only GO.
