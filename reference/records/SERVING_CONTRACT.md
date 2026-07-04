# Records Serving Contract (Gate 5 -> Gate 9)

Status: reference only, v2 / Option B (server-side direct-role DSN). Nothing in
Gate 5 reads this file at runtime. It exists so that Gate 9 (Supabase rebind)
is a mechanical lookup instead of a re-derivation from the migrations. The
machine-readable form is `SERVING_CONTRACT.yaml`; this file is its human
companion.

## Why v2 (Option B), not v1

The first cut of this contract (v1) planned to bind each connecting role to
the Supabase Data API as the `authenticated` claim. That was a false-green:
every one of the three connecting roles resolved to the exact same Supabase
target, which means the serving layer could not actually tell `records_api`
apart from `records_intake_writer` apart from `records_auditor` once a
request reached Postgres through the Data API's pooler identity. The
Postgres-level RLS policies are real, but a serving layer that hands out an
`authenticated` session token has no mechanical way to guarantee which
role's DSN a given request is entitled to use - the distinction lived only
in application code, not in the connection itself. That is not an
enforceable boundary; it is a naming convention.

v2 (Option B) removes the ambiguity by taking `records.*` off the Supabase
Data API entirely (`data_api_exposed: false`) and having Gate 9's serving
layer connect as the Postgres role itself, over a direct role DSN, one
DSN per connecting role. There is no shared claim to misroute: `connect_as`
names the exact Postgres role the connection authenticates as, and that
role's own grants (not application logic) are what RLS evaluates.

## The invariant

Every role that a Gate-9 serving layer is allowed to hand a live DSN to must
be one of the three `connects: true` roles below, and its Postgres grants
already say exactly what it may do. Gate 9's job is to bind each of those
roles to its own direct-role DSN, not to invent new privileges and not to
route it through a shared claim. `records_owner` and `records_fn_owner`
never get a DSN, in any environment, ever. They are catalog-owner identities
only; nothing outside a migration or its own `SECURITY DEFINER` function
context runs as them.

| Role | Connects | Serving transport | Connect as | Write scope | Reachable tables |
|---|---|---|---|---|---|
| `records_api` | yes | `direct_role_dsn` | `records_api` | none (read-only) | 8 ref tables + 6 write-path tables (read only) + 2 API views |
| `records_intake_writer` | yes | `direct_role_dsn` | `records_intake_writer` | column-scoped (see 045's reserved-column block) | same 14 base tables, read + scoped insert/update; no views |
| `records_auditor` | yes | `direct_role_dsn` | `records_auditor` | none (read-only) | `records.audit_log` only; no views |
| `records_owner` | no | n/a | n/a | n/a | owns all of `records.*` (schema + all 15 tables + `records` schema itself) |
| `records_fn_owner` | no | n/a | n/a | n/a | owns `records.audit_log` + `records.fn_audit_capture()`; holds schema `USAGE` only (no other grant) so its `SECURITY DEFINER` function can reach the table it owns |

Only `records_api` reaches the two API views (`v_asset_test_history`,
`v_pm_due`). Neither `records_intake_writer` nor `records_auditor` gets view
access - the writer and the auditor stay scoped to their base tables exactly
as before.

## Honest-scope caveat

This contract closes the **non-superuser-owner RLS bypass** only. It proves
that `records_api`, `records_intake_writer`, and `records_auditor` cannot see
or touch data outside their granted policies, and that `records_owner` /
`records_fn_owner` never appear as a serving identity. It does **not** and
cannot close:

- The `postgres` superuser bypass (superusers bypass RLS by definition in
  Postgres; this is custody-controlled, not policy-controlled).
- A Supabase pooler/service bypass identity that skips RLS by design;
  keeping any such identity out of the serving path is a Gate-9
  configuration discipline, not something a migration can enforce.

Both of the above stay in the "custody + detector + deferred startup
assertion" bucket (see `infra/secret-audit.sh` Check 3, which scans a future
serving config for exactly these two leak shapes once one exists) rather than
being provable inside Postgres itself. Anyone consuming this contract should
not read the RLS posture as covering superuser or bypass-identity access -
it does not, by design of the database engine.

## Per-table policy names

Policy names follow `p_<table>_<verb>` where `<verb>` is `read`, `ins`, or
`upd`. Source: `infra/database/migrations/records/045_records_security_rls.sql`
(app-role policies) and `048_records_audit_log.sql` (audit_log policies).

### Reference tables (8) - read-only for both app roles

`p_<t>_read` on: `asset_classes`, `form_templates`, `pm_programs`,
`neta_procedures`, `neta_test_items`, `neta_tables`,
`asset_class_neta_procedure`, `neta_procedure_xref`.

### Write-path tables (6) - read + scoped insert/update for records_intake_writer

`p_<t>_read`, `p_<t>_ins`, `p_<t>_upd` on: `assets`, `form_submissions`,
`form_field_values`, `pm_schedules`, `pm_events`, `persons`. No DELETE policy
exists for either app role on any of these 14 tables - the writer never
deletes (045 posture assert enforces this).

### API views (2) - read-only, records_api only

`v_asset_test_history`, `v_pm_due`. These are the only Data-API-shaped read
surfaces this contract names, and even they are not exposed through the
Supabase Data API in v2 - `records_api` reaches them the same way it reaches
every other table, over its own direct role DSN. `records_intake_writer` and
`records_auditor` have no grant on either view.

### Owner-only tables (2) - no app-role policy or grant

- `neta_table_source_links` - RLS is enabled but no policy targets
  `records_api` or `records_intake_writer` (Decision D10). Neither app role
  holds any privilege (SELECT/INSERT/UPDATE/DELETE) on this table. This is the
  DRM boundary table: it protects **lineage/provenance**, not the tolerance
  numeric values themselves (see `drm_boundary` in the YAML). The tolerance
  values live in `form_field_values`, which IS reachable and intentionally
  auditable - the boundary is about hiding where a value's authority came
  from, not about hiding the value.
- `audit_log` - `p_audit_log_ins` (INSERT, `records_fn_owner` only, via the
  `SECURITY DEFINER` capture function) and `p_audit_log_sel` (SELECT,
  `records_auditor` only). No UPDATE/DELETE policy for anyone: append-only.

## DSN form inventory

Gate 9's serving config is expected to need to recognize (and
`secret-audit.sh` Check 3 is expected to scan for) all five DSN shapes a
direct-role Postgres connection can take:

- `keyword_user` - libpq keyword form, e.g. `user=records_api ...`.
- `url_userinfo` - URL form with credentials in userinfo, e.g.
  `postgresql://records_api:***@host/db`.
- `url_driver_qualified` - driver-qualified URL scheme, e.g.
  `postgresql+asyncpg://records_api:***@host/db`.
- `pg_env_vars` - `PGUSER` / `PGPASSWORD` / `PGHOST` / `PGDATABASE` env-var
  form with no literal DSN string in the file at all.
- `supavisor_qualified_user` - Supavisor connection-pooler qualified user
  form, e.g. `records_api.<project_ref>`, used when the direct-role DSN is
  routed through the pooler rather than connecting straight to Postgres.

Any of the five can carry a non-sanctioned role name or a bypass credential;
Check 3 does not care which form is used, it checks the resolved user/role
token and the raw text for bypass markers against whichever glob set
`RECORDS_SERVING_GLOBS` points at.

## Gate-9 rebind recipe (direct-role)

When Gate 9 stands up the real serving layer:

1. Read `SERVING_CONTRACT.yaml`. For each `connects: true` role, provision a
   direct-role DSN whose `connect_as` is that exact Postgres role name -
   `records_api`, `records_intake_writer`, or `records_auditor`. There is no
   shared claim or pooler identity standing in for the role; the DSN
   authenticates as the role itself.
2. Keep `records.*` off the Data API. `data_api_exposed: false` is a
   contract invariant, not a default that can be flipped later without
   reopening the Gate 5 posture decision.
3. Grant nothing to `anon`, to any shared authenticated-session identity, to
   a service-level bypass identity, or to `PUBLIC`. The only grants that
   exist are the ones the 045/048 migrations already created for the three
   named roles.
4. Do not grant more than the contract's `write_scope` and
   `tables_reachable` fields already describe - they are the ceiling, not a
   suggestion. If the serving layer needs more, the fix is a new migration
   that changes the Postgres grant, followed by a contract update, not a
   wider mapping at the serving layer.
5. Never map `records_owner` or `records_fn_owner` to any serving identity,
   direct-role or otherwise. If a future need appears to require one of them
   to "connect" for real, that is a design smell - stop and re-open the
   Gate 5 posture decision rather than issuing that role a DSN.
6. Point `RECORDS_SERVING_GLOBS` (currently unset - Check 3 is dormant by
   design until a serving config exists) at the new serving config's
   file(s) so `infra/secret-audit.sh` starts scanning it, using the
   direct-role DSN forms in the DSN form inventory above. Do this in the
   same change that introduces the serving config, not as a follow-up.
7. Re-run `test_serving_contract.py` after any of the above - it is the
   schema-consistency guardrail that keeps this document from silently
   drifting from the migrations it describes.
