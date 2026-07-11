# Collector SQL — dev execution transcript (2026-07-11)

Durable evidence that the collector's live SQL (`collect_disposition.py` `QUERY_BUNDLE`) **parses
and executes read-only** and that the dependency dedup + direction fixes behave as claimed.

- **Target:** `ops_dev` @ `100.64.0.1:5432` over mesh — a **dev** database, **NOT** prod
  (`fxoyniqnrlkxfligbxmg`). Read-only `SELECT` on catalog relations only. No production access.
- **Server:** PostgreSQL 17.10 (dev). Prod is PG16; every catalog used (`pg_depend`, `pg_rewrite`,
  `pg_proc`, `pg_constraint`, `pg_trigger.tgisinternal`, `pg_policy`, `pg_publication_rel`,
  `pg_class.relkind='S'`, `pg_get_function_identity_arguments`) exists in PG16/17/18 identically.
- **Query bundle at this transcript's time (Round-1, pre-expansion):** `aa7f657205329c4782696689eacdfa0785992914c1b5ebf0b9cbf91e9ca1b326`. **SUPERSEDED:** the dependents SQL was later expanded (pg_proc/outbound/direction/dedup, then FOR ALL TABLES / schema publications + inheritance + relkind-filtered `is_consumer`); the CURRENT bundle is `065d49e08c0ba8458aed25fc24bdacbfd8c3c69e2759a348b797fc496f3aa568`, validated on PG16 in `pg16-sql-validation-2026-07-11.md`. This dev transcript remains valid evidence for the Round-1 bundle only.
- **Why dev, not prod:** this is a SQL syntax/execution + semantics check, not a census. The census
  itself stays behind a separate read-only prod GO. Note the target guard would **correctly REFUSE**
  this dev session (`transaction_read_only=false`, `current_database=ops_dev != postgres`, and the
  dev DSN host carries no `fxoyniqnrlkxfligbxmg` label) — proving the guard is not a paper check.

## 1. `target_identity` query (as committed)

```
current_database | current_user | server_version                     | server_version_num | transaction_read_only | db_now                           | platform_role_markers
ops_dev          | postgres     | PostgreSQL 17.10 ... (Alpine) ...  | 170010             | false                 | 2026-07-11T03:34:29.424781+00:00 | {anon,authenticated,postgres,service_role}
```

`db_now` matches the `iso_datetime` contract pattern (fractional seconds + `+00:00` offset).
`transaction_read_only=false` here because the MCP session is not read-only — the live collector
sets `conn.read_only = True`, and the guard refuses anything else.

## 2. `dependents` (v2) enumerated catalog closure — breakdown on schema `ops`

Final committed query (view/matview rewrites + `pg_proc`-tracked function deps + INBOUND and
OUTBOUND FK constraints + triggers + policies + publications + owned sequences; `union` +
per-edge `direction`):

```
dep_type    | direction | n
constraint  | inbound   | 32
constraint  | outbound  | 33
trigger     | inbound   | 19
view        | inbound   | 40
```

- **Dedup proof (F3):** the identical closure with `union all` (no dedup) returned **171** `view`
  inbound edges — pg_rewrite emits one `pg_depend` row per column reference. With `union` (plus the
  Python edge-key dedup) it is **40** distinct view edges. 171 → 40 is the inflation being collapsed.
- **Outbound FK identities (F3):** 33 outbound FK edges now enumerated with `direction='outbound'`
  (previously the count was collected but identities/direction were dropped).
- `function` = 0 on `ops` (no `pg_proc`-tracked dependencies present there — expected; `pg_proc`
  edges are rare and cover tracked deps such as composite argument/return types, NOT function BODY
  references, which `pg_depend` does not track — those are supplied later as source/dynamic_sql
  evidence).
- Empty `public` schema on `ops_dev` returned 0 rows (no relations), confirming the query is not
  vacuously empty due to a join bug — it returns real rows against a populated schema.

## 3. What this does and does not prove

- **Proves:** the committed SQL parses, plans, and executes read-only on a live PG catalog; the
  dedup collapses pg_rewrite inflation; INBOUND/OUTBOUND FK direction is emitted; the CTE joins
  produce real rows.
- **Does not prove:** the specific prod (`fxoyniqnrlkxfligbxmg`) census contents — that requires the
  separate read-only prod GO. `database_deps` remains the ENUMERATED CATALOG closure, never a
  complete consumer census (function/procedure bodies, dynamic SQL, and app code are not
  `pg_depend`-visible).
