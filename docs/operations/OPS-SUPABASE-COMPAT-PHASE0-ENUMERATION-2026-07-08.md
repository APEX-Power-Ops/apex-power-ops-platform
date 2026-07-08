# ops Supabase-Compat -- Phase 0 Enumeration (read-only)

Date: 2026-07-08. Lane: `ops/supabase-compat` @ 83eaaf69 (worktree `apex-ops-supabase-compat`).
Scope: READ-ONLY. No branch created, no prod mutation, no cost. This record establishes
(1) the prod substrate facts and (2) the complete privileged-op inventory of ops 001-012,
with the adaptation deltas 012 needs to apply as the managed non-super `postgres`.

## 1. Prod substrate (governed project fxoyniqnrlkxfligbxmg, read-only probe)
- Engine: PostgreSQL 17.6.1, ACTIVE_HEALTHY, us-west-2. One governed DB (`postgres`).
- Schemas present: auth, extensions, graphql, graphql_public, pgbouncer, public, realtime,
  records, schedule, seam, storage, supabase_migrations, tcc, vault, work.
- `ops` schema: ABSENT (ops_tables=0). ops_* roles: ABSENT (no name collision).
- Applier identity: current_user=`postgres`, rolsuper=FALSE, rolcreaterole=TRUE,
  rolcreatedb=TRUE, rolbypassrls=TRUE.
- Coexisting-lane precedent: 6 `records_*` roles present (all NOLOGIN, nosuper, nobypassrls);
  `postgres` holds membership (admin_option) in all 6 (granted by supabase_admin) -- the
  trusted-applier posture that let the records lane transfer ownership on this substrate.
- default ACLs: 24 entries, only in auth/extensions/graphql/graphql_public/public/realtime/
  storage. None in ops/records/tcc/work/seam -> lane grants are explicit, not default-ACL.

Fidelity gap vs `ops_dev` (where postgres IS a superuser): on non-super postgres, writes to
role attributes super/bypassrls/replication, writes to database-level ACLs, and object
OWNERSHIP transfer all require superuser OR an explicit membership edge.

## 2. ops 001-011 (base) -- privileged-op summary
Create `ops` (+ `core`) schema, 7+ enums, tables, 11 views, 9 functions, triggers. All created
by `postgres` -> postgres-owned. No role/ownership/GRANT choreography; no superuser-only op.
Expected to apply clean on non-super postgres. These are the branch-proof "Phase A base".

## 3. ops 012 -- privileged-op inventory (468 lines) + verdict

| block | lines | operation | non-super verdict |
|---|---|---|---|
| [1]  | 15-27  | create role x3 + `alter role ... with login/nologin nosuperuser ... nobypassrls noreplication` | **A1** (attr clauses) |
| [1]  | 32-33  | revoke ops_fn_owner from the two login roles | OK (postgres is admin) |
| [1a] | 38-70  | posture asserts (pg_roles reads, membership) | OK (read-only) |
| [2]  | 84-88  | `revoke connect on database current_database() from public` + `grant connect ... to ops_*` (dynamic) | **A3** (critical) |
| [2]  | 91     | `revoke create on schema public from public` | **A4** |
| [2]  | 93-101 | work.* presence-gated revokes | **A7** (no-op watch) |
| [2a] | 103-142| posture asserts incl. datacl-null / PUBLIC-CONNECT / admin-CONNECT | **A3** (asserts fail on prod) |
| [3]  | 145-170| `alter function ... security definer set search_path` + `owner to ops_fn_owner` (9 fns) | **A2** (ownership) |
| [3..5]| 172-296| grant usage/select/insert/update/execute to the 3 roles | OK (owner grants) |
| [3a][5a][5b] | 192-419 | posture asserts (has_*_privilege) | OK (read-only) |
| [5a] | 422-437| view-count + postgres-owned/non-security_invoker asserts | OK (holds); see **A6** |
| [H2] | 445-464| completion-guard trigger function | OK |

## 4. Adaptation deltas (RED -> GREEN)
- **A1 role attributes**: strip `nosuperuser nobypassrls noreplication` from the three
  `alter role` lines (superuser-only to write; a freshly created role already defaults to
  them; the existing [1a] assert proves the posture durably). Keep
  `login/nologin nocreatedb nocreaterole` (a CREATEROLE role can set these).
- **A2 ownership transfer**: `alter function ... owner to ops_fn_owner` requires `postgres`
  to be a SET-capable member of ops_fn_owner. Add explicit `grant ops_fn_owner to postgres`
  before the [3] loop (the branch proof decides whether PG17 create-time auto-membership
  already suffices). Edge disposition after transfer = keep as the ratified trusted-applier
  edge (records precedent) unless a clean revoke is proven.
- **A3 database CONNECT (CRITICAL)**: drop the `revoke connect on database ... from public` +
  `grant connect ... to ops_*` block AND the three database-scoped asserts (datacl-null,
  PUBLIC-retains-CONNECT, admin-lost-CONNECT). On the SHARED prod `postgres` DB this is both
  (a) likely un-permitted (the DB is not postgres-owned) and (b) semantically wrong -- it
  would revoke CONNECT that Supabase's own roles depend on. The ops boundary is SCHEMA-scoped
  (USAGE on schema ops); the login roles reach the DB via the inherited PUBLIC CONNECT we do
  NOT touch.
- **A4 public-schema CREATE**: drop `revoke create on schema public from public` -- `public`
  is not ops's schema to harden and postgres may not own it on Supabase; outside the
  schema-scoped boundary.
- **A5 DOWN**: `012_down` reads `pg_authid` (superuser) for the DEV-7 password guard; adapt to
  a non-super probe/gate. Outside the proof's UP+boundary core; noted for completeness.
- **A6 serving/RLS posture**: ops tables + the 11 ops views are NOT exposed via the Data API;
  they are served by the control-plane API connecting as the `ops_api` LOGIN role (not
  anon/authenticated). Supabase security advisors will flag RLS-disabled ops relations;
  documented as intended (contrast records, which FORCE-RLS because it is Data-API-served).
  Confirm in the design spec (open decision D8-1).
- **A7 work.* coexistence**: the presence-gated work.* revokes run on prod (work exists).
  Verify they are clean no-ops -- postgres is not the work-schema owner, and REVOKE of a
  never-granted privilege is a notice, not an error. Branch proof confirms.

## 5. What did NOT need adaptation
Base 001-011; every object GRANT (owner-granted); every read-only posture assert
(has_*_privilege, pg_roles/pg_proc reads); the SECURITY DEFINER + search_path pinning itself.

## 6. Next gate
Adapt 012 (A1-A4 in-migration, A5 in the down) as a dual-substrate file, then STOP for the
`create_branch` cost/status GO before the RED/GREEN branch proof. No cost/mutation incurred by
this Phase-0 record.
