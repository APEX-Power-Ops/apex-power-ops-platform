# ops_app Role-Boundary Hardening - Design Spec v3 (2026-07-01)

Status: DRAFT v3 for fast targeted confirm, then operator review. No build/apply/prod-touch until v3
passes review. Supersedes v2. v3 folds the second cross-engine re-gate residuals V3-1..V3-11:
explicit ops_fn_owner non-membership hardening, owner lock grants, API route-test cutover, mount-gate
cutover, literal projects UPDATE columns, smoke-script DSN repair, acceptance greps, down-order wording,
and the H2 rationale. Lane: ops_app-role-boundary.
AMENDED 2026-07-01 by cross-engine review of the Codex-authored v3 (opus reviewer): folded 3 residuals the
first v3 draft missed - (RV-1, broken-pipeline) ops_fn_owner was missing SELECT on ops.scopes, which the
live attest/approve_and_recognize/insert-integrity-trigger paths join; (RV-2, latent) ops_fn_owner needed
SELECT on the billing tables for the billing fns' SELECT...FOR UPDATE; (RV-3, minor) the migration
test_001..011 harness reads OPS_DEV_DSN and was absent from the cutover map + acceptance grep. All three
folded below. No other v3 content changed; all eleven prior re-gate folds verified present + grounded.
Inputs: OPS_APP_ROLE_BOUNDARY_AUDIT_2026-07-01.md, DECISIONS_RATIFIED_2026-07-01.md,
IRP_COMBINED_2026-07-01.md, IRP_REGATE_V2_2026-07-01.md.

Goal: give the ops.* lane a real privilege boundary that closes revenue-integrity forgery, so no
application identity can both fabricate apparatus AND recognize revenue on it, and no app identity is a
superuser. This is the HARD prod release gate for the ops.* spine (005-011 are built/merged/live on
ops_dev; prod holds none).

---

## 0. TASK 0 - BLOCKING EMPIRICAL GRANT SPIKE (hard gate)

The ops_intake_writer grant matrix (Section 5) is NOT FINAL until this spike is answered. No downstream
task is settled before Task 0 resolves. This is a gate.

Question: does a role holding ONLY column-scoped UPDATE(quoted_revenue, provenance_status, updated_at)
on ops.apparatus (plus table-level SELECT on apparatus + scopes) satisfy the relation-level check for
`SELECT ... FOR UPDATE OF a` at approve.py:237? (This lock runs as ops_intake_writer. The recognition
FOR UPDATE inside approve_and_recognize runs as ops_fn_owner, which holds table-level apparatus UPDATE,
so it is NOT in question - Task 0 scope stays narrowed to the writer.)

Method (disposable ops_test, admin session, single transaction, ROLLBACK):
```
begin;
create role _spike nologin;
grant usage on schema ops to _spike;
grant update (quoted_revenue, provenance_status, updated_at) on ops.apparatus to _spike;
grant select on ops.apparatus, ops.scopes to _spike;
set local role _spike;
select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id
  where s.project_id = (select id from ops.projects limit 1) for update of a;
reset role; rollback;
```
Runs AS the admin ladder identity on ops_test, inside a ROLLBACK - transient, nothing persists. This is
the FIRST BUILD TASK, AFTER this spec passes review (not before - respects the no-writes hold).

- PASS: writer matrix stands. Add the probe as a permanent regression (test_012), plus a SEPARATE
  two-session concurrency regression (Section 9) since a single-session probe cannot exercise the
  interleave.
- FAIL (relation-level UPDATE required): DO NOT broaden ops_intake_writer to table-level UPDATE on
  apparatus (reopens D2). Bounded fallback: change approve.py's row-lock strategy. Per the IRP (M1),
  the apparatus row-lock at approve.py:237 is the ONLY cross-path serializer between approve_run's
  full-replacement and a concurrent ops.approve_and_recognize (005:89 - recognition takes NO advisory
  lock, only `for update of a2`; attest 009:138; reverse 005:139; the revrec-insert-integrity trigger
  005:173 - 5 real counterparties, not 2). The DURABLE fail-closed barrier is the NO ACTION FK on
  revenue_recognition_event.apparatus_id + completion_attestation.apparatus_id: a concurrent interleave
  ABORTS (does not corrupt). So the fallback is: drop/narrow the writer's apparatus row-lock, relying on
  the advisory lock (project_number) + the FK backstop for correctness; the row-lock's real role was
  spurious-abort avoidance. Re-prove: (a) no two concurrent approves of the same project_number
  interleave; (b) a concurrent approve+recognize fails closed (abort), not corrupt. Fallback touches
  approve.py only; the grant matrix and D2 are unchanged.

---

## 1. Verdict / why

ops.* has no privilege boundary today: every write and every forgery runs as the postgres superuser via
a single OPS_DEV_DSN; the ctx-GUC "firewall" is unprivileged workflow discipline. This packet builds the
boundary. Per the IRP, a SINGLE app role (v1's D1=A) is a huge improvement over superuser but does NOT
close revenue forgery: one role holding both materialization grants and recognition EXECUTE can
manufacture a fake project->scope->apparatus and drive it through attest+recognize. v3 preserves v2's
two-role split and closes the residual SET ROLE / false-green holes, so no login identity can both
fabricate AND recognize.

## 2. Ratified decisions (v3, folding the re-gate rulings)

- D1 = **B (two-role split), ratified 2026-07-01** (was A). ops_intake_writer materializes; ops_api
  recognizes; neither can do the other. (Operator: the single-role forge path is not an acceptable prod
  residual - same standard as D2.)
- D2 (tightened, unchanged): apparatus.status leaves every login role. In v3 the ONLY writer of
  apparatus.status is ops_fn_owner via the DEFINER attest/revoke fns.
- D3: all 9 mutation fns -> SECURITY DEFINER, search_path=ops,pg_temp. ops_api EXECUTEs the 4
  recognition fns; billing EXECUTE deferred (GATE-12). (Billing fns still converted + owner-locked.)
- D4 (made true by construction via H2): the ctx-GUCs are inert to the login roles because neither holds
  DML on a guarded table that could reach a governed-complete transition (H2 closes the
  provenance-on-Complete path the IRP found).
- D5: PUBLIC hygiene in 012 (REVOKE CONNECT, explicit REVOKE EXECUTE - NOT via ADP, which is a no-op
  for functions [H1] - assert no-CREATE-on-public).
- D6: work.* zero grants; AND all work references presence-gated (C1).
- D7: behavior suites run AS the app roles; admin DSN only for ladder/TRUNCATE/setup-DML. v3 makes this
  explicit for packages/ops-intake/tests/conftest.py, apps/control-plane-api/tests/test_ops_intake_routes.py,
  and apps/control-plane-api/tests/test_ops_recognition_routes.py so the TestClient app process cannot
  silently run API-boundary behavior as superuser.
- D8: dev-first; prod parked behind a Supabase re-grounding + a prod-variant packet. NOTE: prod-complete
  now MEANS the two-role split applied on prod, not just 012's base boundary.
- M4 (ratified): the 9 DEFINER fns owned by a dedicated NOLOGIN ops_fn_owner, not postgres, and no login
  role may be a member of ops_fn_owner.

## 3. D2 mechanism (pinned, grounded; unchanged from v1 + owner note)

Live facts (grounded): ops.apparatus.status is NOT NULL DEFAULT 'Not Started'; load.py:169-172 names
status + literal 'Not Started'; approve.py:111 UPDATEs only (quoted_revenue, provenance_status,
updated_at), never status; apparatus_completion_guard is BEFORE INSERT OR UPDATE (009:55-65).

Change: (a) ops_intake_writer INSERT on apparatus is column-scoped to every load.py column EXCEPT
status; its UPDATE is (quoted_revenue, provenance_status, updated_at). No status privilege on any login
role. (b) load.py insert_apparatus drops `status` from the column list + `'Not Started'` from VALUES
(default supplies it). The sole status writer is ops_fn_owner (attest/revoke). Result: `INSERT ...
status='Complete'` as any login role is permission-denied BEFORE the completion guard - status='Complete'
is reachable only via attest.

## 4. Role architecture (D1=B; the core boundary)

Four identities. Roles are selected by WHICH DSN the caller opens (the ops-intake package functions are
role-agnostic - they take a connection; recognition.py wrappers and approve_run are separate modules
driven by different routers).

- **ops_fn_owner** (NOLOGIN, NOSUPERUSER): owns the 9 SECURITY DEFINER functions; holds ONLY the object
  privileges those functions need (Section 5). This is where apparatus.status write authority and all
  ledger/attestation/billing DML live. NOLOGIN alone is not sufficient, because a login role that is a
  member can still `SET ROLE ops_fn_owner`; therefore 012 must explicitly `REVOKE ops_fn_owner FROM
  ops_intake_writer, ops_api, PUBLIC` and assert no login role is a member. Only vetted DEFINER fns may
  run as this role.
- **ops_intake_writer** (LOGIN, NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS): materializes intake ->
  project/scope/apparatus. Column-scoped table grants (Section 5). NO EXECUTE on recognition fns, NO
  status, NO ledger/attestation/billing DML, and NOT a member of ops_fn_owner. Drives: intake_router,
  ops-intake CLI (intake/approve).
- **ops_api** (LOGIN, NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS): EXECUTE on the 4 recognition
  fns + SELECT on the recognition views. NO table DML at all, and NOT a member of ops_fn_owner. Drives:
  recognition_router (the recognition.py wrappers).
- **admin** (postgres superuser / OPS_DEV_ADMIN_DSN): migrations/ladder, TRUNCATE fixtures, setup-DML
  (person INSERT, forced-Complete apparatus for tests), backfills. Stays superuser by design (C5).

Forge-closure invariant (the point of D1=B): ops_intake_writer can create apparatus but cannot
attest/recognize (no EXECUTE; fns are DEFINER so no direct ledger DML); ops_api can recognize but cannot
create apparatus (no INSERT/UPDATE on apparatus/scopes/projects). ops_fn_owner cannot be reached by
SET ROLE from either login role. Neither login role alone can fabricate-and-recognize. Cross-compromise
of BOTH credentials is required to forge - the boundary the lane exists to establish.

## 5. Grant matrix (NON-FINAL until Task 0)

USAGE: ops_intake_writer -> ops, core. ops_api -> ops. ops_fn_owner -> ops (+ core if any fn reads it).

**ops_intake_writer** table/column grants:

| Object | Grant | Note |
|---|---|---|
| ops.intake_runs | INSERT, UPDATE, SELECT | write-once shape bounded by trg_intake_run_immutable |
| ops.intake_source_files | INSERT, SELECT | |
| ops.intake_validation_findings | INSERT, SELECT | |
| ops.projects | INSERT(project_number, project_name, status, quote_revision, contract_value, description, source_client_name, source_site_name, source_site_address, source_site_city, source_site_state, source_site_zip, source, legacy_source_id, provenance_status), UPDATE(project_name, status, quote_revision, contract_value, description, source_client_name, source_site_name, source_site_address, source_site_city, source_site_state, source_site_zip, source, provenance_status, updated_at), SELECT | M2: column-scoped to load.py upsert_project plus approve.py provenance stamp; NOT retainage_pct/lifecycle/is_active; NO DELETE |
| ops.scopes | INSERT, DELETE, SELECT | DELETE = sanctioned full-replacement; RI cascade runs as owner |
| ops.scope_quote | INSERT, SELECT, UPDATE(total_quoted_hours, is_frozen, frozen_at) | covers maintain_scope_quote_hours on INSERT/UPDATE/cascade-DELETE |
| ops.scope_quote_line | INSERT, SELECT | |
| ops.tasks | INSERT, UPDATE, SELECT | |
| ops.apparatus | INSERT(the 11 load.py cols, pinned in load.py insert_apparatus, EXCLUDING status), SELECT, UPDATE(quoted_revenue, provenance_status, updated_at) | D2: NO status (INSERT or UPDATE), NO source in UPDATE, NO scope_id in UPDATE, NO DELETE |
| ops.revenue_recognition_event | SELECT | conflict checks; NO DML |
| ops.billing_application | SELECT | conflict checks; NO DML |
| core.v_equipment_models_resolved (+ core.equipment_models) | SELECT | catalog resolve |
| ops views (11) | SELECT | views are postgres-owned, non-security_invoker (asserted, R2) |

**ops_api** grants: EXECUTE on ops.attest_apparatus_complete, ops.revoke_completion_attestation,
ops.approve_and_recognize, ops.reverse_recognition; SELECT on ops.v_completion_recognition_worklist,
ops.v_completion_recognition_rollup (+ future recognition report views). NO table DML.

**ops_fn_owner** grants (only what the fns need):
- UPDATE on ops.apparatus (table-level acceptable - NOLOGIN, fn-gated - covering status/updated_at writes
  + the recognition FOR UPDATE).
- INSERT, UPDATE on ops.completion_attestation.
- INSERT on ops.revenue_recognition_event, plus UPDATE on ops.revenue_recognition_event solely to satisfy
  reverse_recognition's `FOR UPDATE` lock. The append-only/integrity triggers still bar real mutation.
- UPDATE on ops.projects solely to satisfy progress-billing project `FOR UPDATE` locks. This grant is
  owner-only; it is never granted to ops_intake_writer or ops_api.
- SELECT on apparatus, scopes, completion_attestation, revenue_recognition_event, scope_quote, projects,
  persons (fn reads). NOTE: `scopes` is REQUIRED and was missing in the first v3 draft - attest (009:88-89),
  approve_and_recognize (009:177-178), and the revrec insert-integrity trigger (009:228/246, which fires AS
  ops_fn_owner during the DEFINER INSERT) all `join ops.scopes`; without it the live recognition path fails
  permission-denied once run as the owner.
- Billing: SELECT + INSERT/UPDATE/DELETE on billing_application, billing_application_line,
  billing_application_draft. SELECT is required (in addition to UPDATE) because the billing fns do
  `SELECT ... FOR UPDATE` on billing_application (006:537/1146) - FOR UPDATE needs BOTH SELECT and UPDATE.
  Latent this packet (billing EXECUTE deferred, GATE-12) but the fns are owner-converted now, so the owner
  grant is completed here. USAGE ops.

If the implementation attempts column-scoped UPDATE for the owner lock grants, it must prove the relevant
`SELECT ... FOR UPDATE` succeeds under ops_fn_owner before accepting the narrower grant. Relation-level
UPDATE is authorized for ops_fn_owner only on revenue_recognition_event and projects if the lock semantics
require it.

EXPLICIT ZERO (negatively asserted, Section 7): no login role has status priv, ledger/attestation/billing
DML, DELETE on projects/apparatus/tasks/scope_quote*, EXECUTE on any fn PUBLIC-side, ANY work.* privilege,
or membership in ops_fn_owner. DROPPED from v1 (over-grants): ops.persons SELECT for the login roles
(RI + DEFINER attest read persons AS owner; login roles never need it). standard_hours,
backfill_4b1_snapshot: no grant.

## 6. SECURITY DEFINER conversion + dedicated owner + H2 (exact)

Convert these 9 to SECURITY DEFINER, SET search_path = ops, pg_temp, and ALTER FUNCTION ... OWNER TO
ops_fn_owner (exact signatures, grounded from pg_proc):

1. ops.attest_apparatus_complete(p_apparatus_id uuid, p_attested_by uuid, p_reason text)
2. ops.revoke_completion_attestation(p_attestation_id uuid, p_revoked_by uuid, p_reason text)
3. ops.approve_and_recognize(p_apparatus_id uuid, p_actor_person_id uuid, p_datasheet_clearance ops.obligation_clearance, p_datasheet_ref text, p_cx_clearance ops.obligation_clearance, p_cx_ref text)
4. ops.reverse_recognition(p_event_id uuid, p_actor_person_id uuid, p_reason text)
5. ops.record_billing_application(p_project_id uuid, p_actor_person_id uuid, p_period_through date, p_external_invoice_ref text, p_exclude_apparatus uuid[], p_retainage_draw_request numeric)
6. ops.issue_billing_application(p_draft_id uuid, p_actor_person_id uuid, p_ref text)
7. ops.issue_billing_application(p_project_id uuid, p_actor_person_id uuid, p_period_through date, p_external_invoice_ref text, p_exclude_apparatus uuid[], p_retainage_draw_request numeric)
8. ops.discard_draft_billing_application(p_draft_id uuid, p_actor_person_id uuid)
9. ops.void_billing_application(p_application_id uuid, p_actor_person_id uuid, p_reason text)

Ordering (load-bearing): (i) explicit `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ops, core FROM PUBLIC`
FIRST (H1: ADP does NOT close this for functions - PUBLIC EXECUTE is a hard-wired default ADP cannot
displace); (ii) create/alter roles and explicitly `REVOKE ops_fn_owner FROM ops_intake_writer, ops_api,
PUBLIC`; (iii) DEFINER + search_path + OWNER TO ops_fn_owner; (iv) grant ops_fn_owner its object
privileges (Section 5), including owner-only UPDATE locks on revenue_recognition_event and projects;
(v) GRANT EXECUTE on the 4 recognition fns TO ops_api only. Optional cheap hygiene: pin search_path on
the remaining trigger/helper fns too.

**H2 (required) - completion guard tightening.** In 012, CREATE OR REPLACE
ops.trg_apparatus_completion_guard so it additionally raises on `TG_OP='UPDATE' AND OLD.status='Complete'
AND NEW.provenance_status IS DISTINCT FROM OLD.provenance_status` REGARDLESS of ops.completion_ctx. This
makes the "GUC is inert" claim true by construction: even ops_intake_writer's UPDATE(provenance_status)
grant cannot change provenance on a Complete row. Build-time verification: confirm no DEFINER fn
legitimately changes provenance while status='Complete' (grounded: approve sets provenance at
status='Not Started'; attest/revoke change status not provenance). The recognized-then-reapprove path is
blocked earlier by the _conflict_kind frozen gate, so H2 breaks no sanctioned path.

## 7. Migration 012 structure

012_ops_app_role_boundary.sql (+ _down + test_012). Runs on ops_test + ops_dev via the ladder.

1. Idempotent roles (M3): for each of ops_intake_writer, ops_api (LOGIN) and ops_fn_owner (NOLOGIN), a
   guarded CREATE ROLE IF NOT EXISTS, THEN an UNCONDITIONAL `ALTER ROLE <r> WITH <flags>` (so a
   pre-existing role with bad flags is corrected), then assert the pg_roles flags. Immediately
   `REVOKE ops_fn_owner FROM ops_intake_writer, ops_api, PUBLIC` and assert no login role is a member of
   ops_fn_owner via pg_has_role / pg_auth_members. Passwords for the two LOGIN roles set out-of-band
   (Section 8).
2. PUBLIC hygiene (D5, C3, H1): `EXECUTE format('revoke connect on database %I from public',
   current_database())` (C3: dynamic SQL - current_database() is invalid in REVOKE grammar and a bare
   name breaks the one-ladder-two-DBs invariant); GRANT CONNECT to the two login roles + assert the admin
   identity retains CONNECT (M-Low). Explicit `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ops, core FROM
   PUBLIC` (NOT ADP for functions - H1). ALTER DEFAULT PRIVILEGES is still useful for future TABLES; for
   FUNCTIONS add the CI convention + the posture assert in step 7. Idempotent `REVOKE CREATE ON SCHEMA
   public FROM PUBLIC`. ALL work references (below, and the negative asserts) presence-gated on
   `to_regnamespace('work') IS NOT NULL` (C1) - schema-absent = pass, so ops_dev covers work and ops_test
   succeeds.
3. DEFINER conversion x9 + search_path + OWNER TO ops_fn_owner (Section 6); ops_fn_owner object grants,
   including UPDATE on ops.revenue_recognition_event and ops.projects for owner-only `FOR UPDATE` locks.
4. USAGE grants; EXECUTE to ops_api on the 4 recognition fns.
5. The Section 5 table/column grant matrix for ops_intake_writer, including the literal ops.projects
   UPDATE column set: project_name, status, quote_revision, contract_value, description,
   source_client_name, source_site_name, source_site_address, source_site_city, source_site_state,
   source_site_zip, source, provenance_status, updated_at.
6. H2 completion-guard replacement.
7. In-migration posture asserts (DO block; migration FAILS on drift). Use has_column_privilege for
   column-scoped objects (H3), has_table_privilege only for fully-granted relations.
   Positive: writer has INSERT on intake_runs; has_column_privilege(writer,'ops.apparatus',
   'quoted_revenue','UPDATE')=true; writer has UPDATE on every pinned ops.projects column, including
   status, project_name, quote_revision, contract_value, description, source_client_name,
   source_site_name, source_site_address, source_site_city, source_site_state, source_site_zip, source,
   provenance_status, updated_at; ops_api has EXECUTE on the 4 fns; ops_fn_owner has UPDATE on
   ops.revenue_recognition_event and ops.projects AND SELECT on ops.scopes (the recognition-path join;
   plus SELECT on the billing tables for the deferred billing fns). NEGATIVE (the boundary):
   has_column_privilege(writer,'ops.apparatus','status','INSERT')=false and ...'UPDATE')=false; ops_api
   has NO INSERT on apparatus; neither login role has INSERT/UPDATE/DELETE on revenue_recognition_event,
   completion_attestation, or billing_application; no DELETE on projects; pg_has_role('ops_intake_writer',
   'ops_fn_owner','member')=false and pg_has_role('ops_api','ops_fn_owner','member')=false; no login role
   is a direct/indirect ops_fn_owner member. PUBLIC EXECUTE assert:
   has_function_privilege('public', 'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)','EXECUTE')=false
   (and each of the 9 exact signatures); NO ops or core function retains PUBLIC EXECUTE (loop over
   pg_proc in schemas ('ops','core') - core currently has zero functions, but the loop closes drift).
   work presence-gated: if work exists, no login role has any work priv; the 11 ops views are
   postgres-owned + non-security_invoker (R2 assert).

Down (_down), ordered and unambiguous: FIRST ALTER each of the 9 functions OWNER TO postgres, THEN
`DROP OWNED BY ops_intake_writer, ops_api, ops_fn_owner`, THEN `DROP ROLE ops_intake_writer, ops_api,
ops_fn_owner` (after any needed explicit role-membership revokes). Then revert the 9 fns to SECURITY
INVOKER; restore the pre-012 completion guard; `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ops, core
[+ work if present] TO PUBLIC` (INFO: mirror the up's ALL-functions revoke, not just the 9, for a clean
round-trip); GRANT CONNECT TO PUBLIC. Restores pre-012 (insecure) posture = ladder symmetry, not a
security recommendation. ops_test rebuilds schemas each run, so ALL of this lives in the migration files
(C7). Dead conftest fallback DELETED (hard-require explicit DSNs).

## 8. Credential + cutover (three DSNs; M6, C2)

- Env scheme (standardized, M6): `OPS_INTAKE_WRITER_DSN` (ops_intake_writer), `OPS_API_DSN` (ops_api),
  `OPS_DEV_ADMIN_DSN` (postgres - ladder/TRUNCATE/setup-DML). Retire the single OPS_DEV_DSN as an app
  identity. Post-cutover, the ops routers, route tests, package conftest, and smoke DB check must not
  read OPS_DEV_DSN. Keep OPS_DEV_DSN only if a separate read-only legacy path explicitly documents it.
  Passwords for the two login roles set out-of-band by the operator (ALTER ROLE ... PASSWORD; never in a
  file or a model-visible terminal). Distribution/rotation = Infisical lane.
- Code cutover map:
  - apps/control-plane-api/services/ops/intake_router.py: `_dsn()` -> OPS_INTAKE_WRITER_DSN.
  - apps/control-plane-api/services/ops/recognition_router.py: mutation wrappers AND `_read_view()` ->
    OPS_API_DSN. No recognition-router code path may use the admin DSN.
  - apps/control-plane-api/main.py `_ops_intake_enabled()` -> true only when BOTH OPS_INTAKE_WRITER_DSN
    and OPS_API_DSN are present. If an explicit `OPS_ROUTES_ENABLED` flag is added, it may only narrow
    exposure; it must not enable the routers without both DSNs. Re-author the host-gating guard tests in
    the same atomic change as the router cutover.
  - packages/ops-intake package + CLI (intake/approve = materialize) -> OPS_INTAKE_WRITER_DSN for
    behavior; package migrations/TRUNCATE/setup fixtures -> OPS_DEV_ADMIN_DSN.
  - apps/control-plane-api/tests/test_ops_intake_routes.py and
    apps/control-plane-api/tests/test_ops_recognition_routes.py: their duplicate migration/admin
    fixtures and inline seed connections -> OPS_DEV_ADMIN_DSN; the TestClient app process gets
    OPS_INTAKE_WRITER_DSN + OPS_API_DSN and is asserted non-superuser (Section 9).
  - apps/operations-web/scripts/smoke-estimator-native.mjs: HTTP intake/approve leg remains writer-scoped
    because the API process starts with OPS_INTAKE_WRITER_DSN; the script's psql verification read uses
    OPS_DEV_ADMIN_DSN.
  - infra/database/migrations/ops/test_001..test_011 (+ any conftest there): ALL read OPS_DEV_DSN today
    and run DDL/behavior on ops_test - cut over to OPS_DEV_ADMIN_DSN (the ladder is admin-only DDL). These
    were missing from the first v3 draft's cutover map; if OPS_DEV_DSN is retired without moving them they
    fail loud (KeyError on os.environ), not a false-green, but they must move.
  - MANUAL runbook edit for the CLI documented invocation to use the writer credential.
- Acceptance grep (part of done, not optional): in the cutover commit, `rg -n "OPS_DEV_DSN"
  infra/database/migrations/ops/
  apps/control-plane-api/services/ops/intake_router.py apps/control-plane-api/services/ops/recognition_router.py
  apps/control-plane-api/main.py apps/control-plane-api/tests/test_ops_intake_routes.py
  apps/control-plane-api/tests/test_ops_recognition_routes.py apps/operations-web/scripts/smoke-estimator-native.mjs`
  must return zero matches. Separately assert packages/ops-intake/tests/conftest.py has no OPS_DEV_DSN
  fallback. A half-applied cutover fails the gate instead of silently reopening single-role behavior.
- Housekeeping (part of done): MANIFEST 012 row; recognition-bridge spec S5.11 status; this spec + the
  decisions + IRP records move into docs/ on the lane branch.

## 9. Test plan (tests-as-role; GATE-6; C2 fixture split)

Three-identity harness (C2): behavior connections use the role under test; ALL admin fixtures use
OPS_DEV_ADMIN_DSN and open their OWN connections.

- apply_migrations ladder (test_00x/012 DDL) -> OPS_DEV_ADMIN_DSN (H-DDL: the ladder cannot run as a
  login role). clean_ops / clean_ops_between_tests TRUNCATE fixtures -> admin (TRUNCATE is a distinct
  privilege no login role holds). _person / _eligible / forced-Complete setup INSERTs -> admin (status
  writes + person seeds no login role can do).
- packages/ops-intake/tests/conftest.py: delete the OPS_DEV_DSN `or (...)` fallback; fixture DSNs are
  explicit. Behavior: intake + approve_run tests -> OPS_INTAKE_WRITER_DSN (AC5: the positive pipeline
  MUST drive apparatus creation through approve_run/load.py as the writer so the column-scoped matrix is
  actually exercised - not admin-seeded). recognition wrappers (attest/recognize/reverse/revoke) ->
  OPS_API_DSN.
- apps/control-plane-api/tests/test_ops_intake_routes.py: superseded by name. Its apply_migrations,
  clean_ops_between_tests, person fixture, and any inline psycopg seed/setup connection use
  OPS_DEV_ADMIN_DSN. The TestClient app process is started with OPS_INTAKE_WRITER_DSN and OPS_API_DSN;
  POST/GET route behavior uses the router DSNs, never the admin DSN. Its host-gate test now proves
  `_ops_intake_enabled()` is false unless BOTH new DSNs exist and true when both exist.
- apps/control-plane-api/tests/test_ops_recognition_routes.py: superseded by name. Its apply_migrations,
  person_id, eligible fixture, and inline forced-Complete setup use OPS_DEV_ADMIN_DSN. The TestClient app
  process is started with OPS_API_DSN for recognition mutations/reads; no duplicate `_dsn()` helper may
  point behavior at OPS_DEV_DSN.
- Route-boundary false-green test: add a route-level test that imports the same router `_dsn()` functions
  used by the TestClient app process, opens those DSNs, and asserts `current_user` is not postgres and
  `rolsuper=false` for both intake and recognition. This is the loud failure if a builder runs
  API-boundary behavior under OPS_DEV_DSN/postgres.
- Task 0: privilege probe (Section 0) resolves first; add a two-session concurrency regression.
- Boundary-denial proofs (unmasked exit codes; the DENY is the pass):
  (a) MANDATORY forged-Complete: as ops_intake_writer, `INSERT ... status='Complete'` -> denied; AND
      after `SET ops.completion_ctx='1'` -> STILL denied.
  (b) as ops_intake_writer, `UPDATE apparatus SET status=...` -> denied.
  (c) FORGE-CLOSURE (the D1=B proof): as ops_intake_writer, attempt to EXECUTE attest_apparatus_complete
      / approve_and_recognize -> denied (no EXECUTE).
  (d) FORGE-CLOSURE: as ops_api, `INSERT ops.apparatus` / `INSERT ops.scopes` -> denied (no table DML).
  (e) as ops_intake_writer, `SET ops.completion_ctx='1'; UPDATE apparatus SET provenance_status=...
      WHERE status='Complete'` -> denied by the H2 guard.
  (f) as any login role, INSERT revenue_recognition_event / completion_attestation / billing_application
      -> denied; SET ops.billing_ctx='1' does not help.
  (g) DELETE ops.projects -> denied; any work.* write -> denied.
  (h) `SET ROLE ops_fn_owner` as ops_intake_writer and as ops_api -> denied; pg_has_role non-membership
      asserts pass.
- Positive pipeline: full intake -> approve (as writer) -> attest -> recognize -> reverse (as ops_api)
  runs green, exercising both matrices end to end. Plus the recognized-then-reapprove edge (NO ACTION FK
  hard-fails the cascade - exercise it).
- Suite posture: package + API behavior under the two app DSNs; admin only for fixtures. No fixture
  silently reconnects as postgres for behavior (the false-green trap).
- Post-merge: a fresh adversarial audit before declaring GATE-7/8 satisfied.

## 10. Out of scope / non-goals

- Prod apply of ops 005-012: separate, operator-gated, AFTER a prod-grounding catalog audit of Supabase
  fxoyniqnrlkxfligbxmg (postgres non-superuser, managed roles, pooler, constrained DDL) + a prod-variant
  packet. PROD-COMPLETE = the two-role split applied on prod (not just 012's base boundary on dev).
- RLS on ops.*; billing API/Chip-4 productization (billing fns owner-locked, EXECUTE deferred); work.*
  schema drop (separate chip; 012 only guarantees zero grants + presence-gated hygiene); legacy
  control-plane-api migrations/*.py + SUPABASE_PROD_DSN custody (secret-custody lane); credential
  rotation (Infisical lane).

## 11. Acceptance criteria

1. Task 0 answered; writer matrix finalized (as authored, or with the bounded approve.py fallback).
2. 012 applies on ops_test (work presence-gated) + ops_dev; posture asserts pass, including
   ops_fn_owner non-membership, owner UPDATE lock grants, positive projects UPDATE column grants, and no
   PUBLIC EXECUTE across ops/core functions.
3. Down/up ladder reversible with the explicit order: ALTER FUNCTION OWNER TO postgres first, then
   DROP OWNED, then DROP ROLE.
4. D2: forged-Complete INSERT denied as ops_intake_writer even with completion_ctx set.
5. FORGE-CLOSURE proven: ops_intake_writer cannot recognize; ops_api cannot fabricate apparatus; neither
   can SET ROLE ops_fn_owner.
6. H2: provenance-on-Complete denied regardless of GUC, and the _conflict_kind frozen gate still blocks
   recognized-then-reapprove before H2 is relevant.
7. All boundary-denial proofs green (unmasked); H1 posture assert (no ops/core fn has PUBLIC EXECUTE)
   passes.
8. Positive pipeline green with apparatus created via approve_run AS the writer and recognition AS
   ops_api; recognized-then-reapprove exercised.
9. Suites green under OPS_INTAKE_WRITER_DSN + OPS_API_DSN; admin only for fixtures. Route tests named in
   Section 9 include a non-superuser app-process DSN test.
10. Acceptance grep from Section 8 is clean: no OPS_DEV_DSN references remain in infra migration tests,
    the routers, mount gate, named route-test files, or smoke-estimator-native.mjs;
    packages/ops-intake/tests/conftest.py has no OPS_DEV_DSN fallback.
11. Fast targeted re-confirm clean on changed sections (owner grants + membership; route-test/mount-gate
    cutover; projects column list), then operator review before writing-plans.
12. Prod NOT touched; parked behind D8.

## 12. Carried risks

- R1 (Task 0): writer column UPDATE vs FOR UPDATE -> bounded approve.py fallback (never table-level UPDATE
  on a login role).
- R2 (view security): 11 ops views asserted postgres-owned + non-security_invoker; a future
  security_invoker view would need base-table SELECTs.
- R3 (down re-opens the gap): expected; ladder symmetry only.
- R4 (prod divergence): dev 012 not prod-portable; a separate grounded prod packet is mandatory.
- R5 (two-credential surface): D1=B adds a second app credential to distribute/rotate (Infisical lane
  owns this); the forge-closure requires BOTH to be compromised, which is the intended raise in attacker
  cost.
- R6 (owner-lock UPDATE surface): ops_fn_owner receives UPDATE on revenue_recognition_event/projects only
  to satisfy `FOR UPDATE` locks inside vetted SECURITY DEFINER fns. It remains NOLOGIN, non-membered from
  login roles, and fn-gated; ledger append-only/integrity triggers still protect real mutation.
