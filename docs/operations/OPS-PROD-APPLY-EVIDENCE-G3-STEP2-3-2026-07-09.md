# OPS prod-apply evidence -- G3 Step 2/3 (serving-role arming + real-login round-trip)

Target project: `fxoyniqnrlkxfligbxmg` (governed prod). Date: 2026-07-09.
Follows G3 Step 1 (ops 001-012 LIVE; `docs/operations/OPS-PROD-APPLY-EVIDENCE-G3-2026-07-09.md`).
Scope of this GO: DB-side serving-role arming (Step 2) plus the immediately coupled value-silent
real-login round-trip (Step 3), then stop. No other prod mutation.

## 1. Arming mechanism (value-silent)

- Admin auth: `SUPABASE_PROD_DSN` from Infisical prod (session-pooler), password in `PGPASSWORD` only
  -- never in the conninfo, never on argv. `infra/.env` remains stale and was not used.
- Role passwords: parsed as the password COMPONENT of `OPS_API_DSN` / `OPS_INTAKE_WRITER_DSN`, exported
  to the psql subprocess env, and loaded into psql via `\getenv` (psql 17.10) -- never via `-v`, never
  on argv.
- `arm_serving.sql` runs an in-band prod DO-guard BEFORE any write (asserts `current_database=postgres`,
  `current_user=postgres`, non-super, 6 `records_*` roles, `ops` present, both serving roles LOGIN),
  then executes exactly: `ALTER ROLE ops_api PASSWORD :'..'`, `ALTER ROLE ops_intake_writer PASSWORD
  :'..'`, `GRANT CONNECT ON DATABASE postgres TO ops_api, ops_intake_writer`.
- All captured psql stdout/stderr is redacted of the known secret values before printing.

Result (redacted): `DO / ALTER ROLE / ALTER ROLE / GRANT`, rc=0.

## 2. Pre-arming shape + reachability (read-only)

Both serving DSNs: host `db.fxoyniqnrlkxfligbxmg.supabase.co:5432` (direct), db `postgres`, users
`ops_api` / `ops_intake_writer`, has_pw=true, sslmode=require, TCP reachable from the host (`tcp_ok`).
The round-trip therefore used the real DSNs directly (no pooler fallback needed).

## 3. Armed state (independent MCP channel)

| role              | has_password | login | super | bypassrls | db CONNECT |
|-------------------|--------------|-------|-------|-----------|------------|
| ops_api           | true         | true  | false | false     | true       |
| ops_intake_writer | true         | true  | false | false     | true       |
| ops_fn_owner      | false        | false | false | false     | true (moot; NOLOGIN) |

`ops_fn_owner` remains NOLOGIN and unarmed. The two serving roles now have a SCRAM password and explicit
database CONNECT.

## 4. Real-login round-trip (Step 3, value-silent, via the real DSNs)

Both roles logged in successfully as their own role (rc=0):

- **ops_api**: `current_user=ops_api`, `current_database=postgres`, server present, `rolcanlogin=true`,
  member of `ops_fn_owner` = **false**, prod marker `records_*` = 6, `has_table_privilege(ops.apparatus,
  INSERT)` = **false**, `has_table_privilege(ops.v_completion_recognition_worklist, SELECT)` = **true**.
- **ops_intake_writer**: `current_user=ops_intake_writer`, `current_database=postgres`, server present,
  `rolcanlogin=true`, member of `ops_fn_owner` = **false**, prod marker `records_*` = 6,
  `has_table_privilege(ops.intake_runs, INSERT)` = **true**, `has_table_privilege(ops.apparatus, SELECT)`
  = **true**, `has_column_privilege(ops.apparatus.status, UPDATE)` = **false**,
  `has_column_privilege(ops.apparatus.status, INSERT)` = **false**.

## 5. Corrected boundary wording (supersedes Step 1 evidence)

The Step 1 evidence said "`apparatus.status` is denied to the writer." That is imprecise. Correct
statement, confirmed live through the round-trip above: **`ops_intake_writer` has table-level SELECT on
`ops.apparatus` (it can READ `status`), but has NO INSERT and NO UPDATE on the `status` column** -- the
D2 boundary is write-scoped, not read-scoped. Source authority: `012_ops_app_role_boundary.sql` (the
column-scoped grant block and the posture assert). The Step 1 doc's boundary-spot-check line has been
corrected to match in this same change.

## 6. No drift

Post-arming re-check (MCP): ops+core = 12 views / 28 functions / 9 SECDEF, `supabase_migrations` = 198,
`ops_fn_owner` membership held by serving roles = 0, `records_*` = 6 total / 6 NOLOGIN. Arming altered
only the two serving roles' passwords and their database CONNECT -- no schema, function, ownership, or
records change.

## 7. State after Step 2/3

- `ops_api` / `ops_intake_writer` are LIVE and usable via their real DSNs (armed + CONNECT); the
  boundary holds through a real login.
- `ops_fn_owner` remains NOLOGIN/unarmed; serving roles hold zero `ops_fn_owner` membership.
- The serving path is proven end-to-end. Any further G3 sweep (broad boundary/advisors) or final
  reconciliation remains available as a separate operator-gated step.
