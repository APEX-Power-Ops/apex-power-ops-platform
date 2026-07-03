# Records Serving Contract (Gate 5 -> Gate 9)

Status: reference only. Nothing in Gate 5 reads this file at runtime. It exists
so that Gate 9 (Supabase rebind) is a mechanical lookup instead of a re-derivation
from the migrations. The machine-readable form is `SERVING_CONTRACT.yaml`; this
file is its human companion.

## The invariant

Every role that a Gate-9 serving layer is allowed to hand a live DSN to must be
one of the three `connects: true` roles below, and its Postgres grants already
say exactly what it may do. Gate 9's job is to bind each of those roles to a
Supabase JWT claim / connection pooler role, not to invent new privileges.
`records_owner` and `records_fn_owner` never get a DSN, in any environment,
ever. They are catalog-owner identities only; nothing outside a migration or
its own SECURITY DEFINER function context runs as them.

| Role | Connects | Supabase target | Write scope | Reachable tables |
|---|---|---|---|---|
| `records_api` | yes | `authenticated` | none (read-only) | 8 ref tables + 6 write-path tables (read only) |
| `records_intake_writer` | yes | `authenticated` | column-scoped (see 045's reserved-column block) | same 14, read + scoped insert/update |
| `records_auditor` | yes | `authenticated` | none (read-only) | `records.audit_log` only |
| `records_owner` | no | n/a | n/a | owns all of `records.*` (schema + all 15 tables + `records` schema itself) |
| `records_fn_owner` | no | n/a | n/a | owns `records.audit_log` + `records.fn_audit_capture()`; holds schema `USAGE` only (no other grant) so its `SECURITY DEFINER` function can reach the table it owns |

## Honest-scope caveat

This contract closes the **non-superuser-owner RLS bypass** only. It proves
that `records_api`, `records_intake_writer`, and `records_auditor` cannot see
or touch data outside their granted policies, and that `records_owner` /
`records_fn_owner` never appear as a serving identity. It does **not** and
cannot close:

- The `postgres` superuser bypass (superusers bypass RLS by definition in
  Postgres; this is custody-controlled, not policy-controlled).
- The Supabase `service_role` bypass (same category: `service_role` is
  designed to skip RLS; keeping it out of the serving path is a Gate-9
  configuration discipline, not something a migration can enforce).

Both of the above stay in the "custody + detector + deferred startup
assertion" bucket (see `infra/secret-audit.sh` Check 3, which scans a future
serving config for exactly these two leak shapes once one exists) rather than
being provable inside Postgres itself. Anyone consuming this contract should
not read the RLS posture as covering superuser or `service_role` access -
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
exists for either app role on any of these 15 tables - the writer never
deletes (045 posture assert enforces this).

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

Gate 9's serving config is expected to need to recognize (and `secret-audit.sh`
Check 3 is expected to scan for) all four DSN shapes a Supabase-fronted
Postgres connection can take:

- `keyword_user` - libpq keyword form, e.g. `user=records_api ...`.
- `url_userinfo` - URL form with credentials in userinfo, e.g.
  `postgresql://records_api:***@host/db`.
- `url_driver_qualified` - driver-qualified URL scheme, e.g.
  `postgresql+asyncpg://records_api:***@host/db`.
- `pg_env_vars` - `PGUSER` / `PGPASSWORD` / `PGHOST` / `PGDATABASE` env-var
  form with no literal DSN string in the file at all.

Any of the four can carry a non-sanctioned role name or a `service_role` /
`sb_secret_*` bypass credential; Check 3 does not care which form is used, it
checks the resolved user/role token and the raw text for bypass markers
against whichever glob set `RECORDS_SERVING_GLOBS` points at.

## Gate-9 rebind recipe

When Gate 9 stands up the real Supabase-fronted serving layer:

1. Read `SERVING_CONTRACT.yaml`. For each `connects: true` role, create (or
   reuse) a Supabase connection identity bound to `supabase_target` (today
   that is `authenticated` for all three - no role is `anon` and no role is
   `service_role`).
2. Do not grant that identity anything beyond what the role's Postgres grants
   already allow. The contract's `write_scope` and `tables_reachable` fields
   are the ceiling, not a suggestion - if the serving layer needs more, the
   fix is a new migration that changes the Postgres grant, followed by a
   contract update, not a wider Supabase role mapping.
3. Never map `records_owner` or `records_fn_owner` to any Supabase target.
   If a future need appears to require one of them to "connect" for real,
   that is a design smell - stop and re-open the Gate 5 posture decision
   rather than issuing that role a DSN.
4. Point `RECORDS_SERVING_GLOBS` (currently unset - Check 3 is dormant by
   design until a serving config exists) at the new serving config's file(s)
   so `infra/secret-audit.sh` starts scanning it. Do this in the same change
   that introduces the serving config, not as a follow-up.
5. Re-run `test_serving_contract.py` after any of the above - it is the
   schema-consistency guardrail that keeps this document from silently
   drifting from the migrations it describes.
