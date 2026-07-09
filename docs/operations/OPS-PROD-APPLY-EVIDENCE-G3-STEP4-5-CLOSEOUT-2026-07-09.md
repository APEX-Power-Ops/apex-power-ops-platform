# OPS prod-apply evidence -- G3 Step 4/5 closeout (boundary/advisors + final evidence)

Target project: `fxoyniqnrlkxfligbxmg` (governed prod). Date: 2026-07-09.
Closes the two remaining named steps of the G3 packet
(`docs/operations/OPS-PROD-APPLY-PACKET-G2-G3-2026-07-08.md`, Step 4 = boundary/advisors sweep,
Step 5 = committed final evidence). This closeout is READ-ONLY: no further prod mutation is performed
or required for the ops role boundary. Follows G3 Step 1 (`...-G3-2026-07-09.md`) and Step 2/3
(`...-G3-STEP2-3-2026-07-09.md`).

## Step 4 -- boundary (read-only)

Confirmed live via the governed MCP channel and, for the serving roles, through the Step 2/3 real-login
round-trip:

- `ops_api` / `ops_intake_writer`: armed (SCRAM password set), LOGIN, non-super, non-bypass, DB CONNECT.
- `ops_fn_owner`: NOLOGIN, unarmed, non-super, non-bypass.
- Serving roles hold ZERO membership in `ops_fn_owner` (no SET ROLE path); the only `ops_fn_owner`
  member is `postgres` (the ratified trusted-applier edge).
- Behavioral boundary (from the Step 2/3 round-trip, as each serving role): API can read the recognition
  worklist but cannot insert `apparatus`; writer can insert `intake_runs` and read `ops.apparatus`
  (incl. `status`) but has NO INSERT and NO UPDATE on `apparatus.status`.

Structure snapshot (unchanged since Step 1): ops+core = 12 views / 28 functions / 9 SECDEF (all owned by
`ops_fn_owner`, `search_path=ops, pg_temp`); `supabase_migrations` = 198; `records_*` = 6 total /
6 NOLOGIN (dormant).

## Step 4 -- advisors

No ERROR-level advisor touches `ops` or `core` (security or performance). The ops/core exposure is
WARN/INFO only:

- Security: 19 `function_search_path_mutable` WARN on base (non-SECDEF) ops functions -- tracked
  follow-up (`task_7dd40f4f`); the 9 SECDEF functions already pin `search_path`.
- Performance: INFO-level index hygiene only (unindexed foreign keys, unused indexes) -- not a
  correctness or cutover blocker.

This advisor posture is unchanged from Step 1: Step 2/3 arming (`ALTER ROLE ... PASSWORD` +
`GRANT CONNECT`) created no schema objects, so it added no advisor surface. A cross-engine review
independently re-confirmed the same classification.

## Step 4 -- Data API exclusion (private-schema confirmation)

`ops` and `core` are NOT reachable through the Supabase Data API (PostgREST). Read-only probe:

| check | result |
|-------|--------|
| `anon` / `authenticated` schema USAGE on `ops` | false / false |
| `anon` / `authenticated` schema USAGE on `core` | false / false |
| ops/core relations with ANY `anon`/`authenticated` table privilege | 0 |
| ops/core functions with `anon`/`authenticated` EXECUTE | 0 |
| ops/core relations with a PUBLIC ACE | 0 |
| ops/core functions with a PUBLIC ACE | 0 |

The ops.* control-plane surface is served only via the dedicated serving roles (`ops_api` /
`ops_intake_writer`) over their own DSNs, never via the anonymous/authenticated Data API roles.

## Step 5 -- committed final evidence

The durable evidence chain is complete on `main`:

- Step 1 (apply): `docs/operations/OPS-PROD-APPLY-EVIDENCE-G3-2026-07-09.md` (PR #82).
- Step 2/3 (arming + round-trip): `docs/operations/OPS-PROD-APPLY-EVIDENCE-G3-STEP2-3-2026-07-09.md`
  (PR #83).
- Step 4/5 (this closeout): PR that lands this file.

## Waiver + status

Step 4 is satisfied read-only (boundary + advisors + Data API exclusion above); Step 5 is the merged
evidence set plus this closeout. No additional prod write is required or authorized for the ops role
boundary. **The G3 packet is COMPLETE.** The ops.* role boundary is LIVE on prod and the serving path
is proven end-to-end. The natural next lane is an app-side consumer cutover that uses the armed
`ops_api` / `ops_intake_writer` DSNs.
