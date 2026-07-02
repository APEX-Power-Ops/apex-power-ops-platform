# ops_app Role-Boundary - Current Surface Audit (2026-07-01)

Scope: ops.* lane on apex-dev-pg (ops_dev / ops_test), plus the code that connects to it. All DB facts are live-verified catalog reads (2026-07-01); all code facts are file:line-verified. This audit is the input to the hardening-packet spec (migration 012 + code cutover + tests). No code has been changed.

## 1. Verdict / exposure summary

VERDICT: The ops.* lane has NO privilege boundary today. Every sanctioned write path - and every forgery - runs as the postgres superuser, and the trigger "firewall" is workflow discipline, not security.

What is forgeable today, by whom:

- By the connecting app identity (postgres, superuser - the ONLY identity apps connect as; pg_roles + pg_stat_activity, ops_dev):
  - Fabricated revenue: direct INSERT into ops.revenue_recognition_event. The insert-integrity trigger re-validates lineage, but `SET session_replication_role=replica` or `ALTER TABLE ... DISABLE TRIGGER` silences it (all 29 non-internal triggers are tgenabled='O').
  - Forged/back-dated completion: `SET ops.completion_ctx='1'` (an UNPRIVILEGED custom GUC - any session may set it) opens governed-complete flips on ops.apparatus outside ops.attest_apparatus_complete. A package test already exploits exactly this (packages/ops-intake/tests/test_recognition_wrappers.py:63 `set local ops.completion_ctx='1'`).
  - Mutated/voided issued billing: `SET ops.billing_ctx='1'` opens direct INSERT/UPDATE on ops.billing_application, _line, _draft past the "function-only" triggers (trg_billapp_immutable et al. check only the GUC first: 006_progress_billing.sql:101).
  - Attestation rewrites, intake_runs provenance rewrites, trigger drops, function-body rewrites: superuser, one statement each.
- By any OTHER existing login role (infisical, orchestration, tcc_breaker_ro, tcc_breaker_codex_79audit) with ZERO grants:
  - Connect to ops_dev/ops_test (pg_database.datacl NULL = PUBLIC CONNECT+TEMP, live-verified has_database_privilege = t for all four).
  - Cross-lane DoS: `select pg_advisory_xact_lock(hashtext('<project_number>'))` in ops_dev indefinitely blocks intake create_run/approve_run (envelope.py:409,577; approve.py:186) - advisory-lock functions are PUBLIC-executable by PG default.
  - They CANNOT read or write ops.*/core.*/work.*: schemas have NULL nspacl (no PUBLIC USAGE), all 43 relations have NULL relacl. Net default posture for a new role = fail-closed, connect-only. BUT: all 35 user functions carry implicit PUBLIC EXECUTE (proacl NULL; has_function_privilege = t for all four roles) - the moment any role gets `GRANT USAGE ON SCHEMA ops`, it gets EXECUTE on every ops function for free.
- Reachability containment today is host-gating only: the ops routers mount only when OPS_DEV_DSN is set (apps/control-plane-api/main.py:110-111; intake_router.py:19-21; recognition_router.py:24). The ratified docs correctly call this the dev interim posture, not the boundary (spec 2026-06-23:178-183; IRP-B6 record :27).

THE DESIGN TRAP the packet must resolve: GATE-1 says "REVOKE INSERT, UPDATE (status, source, provenance_status) ON ops.apparatus" for ops_app - but the sole sanctioned intake writer is Python direct DML that performs exactly those writes (load.py:169 INSERT ops.apparatus with status/source/provenance_status; approve.py:110 UPDATE apparatus provenance_status). And all 28 ops.* functions are SECURITY INVOKER (pg_proc.prosecdef=f, live), so "EXECUTE-only ops_app with no table DML" is a contradiction until the mutation functions are converted to SECURITY DEFINER. Section 6 lays out the options.

## 2. Role + connection inventory

Live roles (pg_roles, non-pg_*): postgres (SUPER, LOGIN, CREATEROLE, CREATEDB, BYPASSRLS), infisical (LOGIN), orchestration (LOGIN), tcc_breaker_ro (LOGIN), tcc_breaker_codex_79audit (LOGIN), apex_pm_stage_user (NOLOGIN, dormant). ops_app: CONFIRMED ABSENT. pg_auth_members: no memberships.

Who connects as what:

| Consumer | Env / DSN | Effective role | Notes |
|---|---|---|---|
| control-plane-api core SQLAlchemy engine (work router, prod dashboards, PM idempotency) | APEX_OLARES_LIVE_DSN -> SEAM_DATABASE_URL -> APEX_DB_CONNECTION_STRING -> DATABASE_URL (config.py:31-35) | postgres on dev | pool_size 5+5, statement_timeout=30000 startup option EXCEPT *.pooler.supabase.com / :6543 (config.py:57-61) - generic PgBouncer would reject |
| ops intake router (6 routes incl POST /native; intake_router.py:79/150/172/236/291/323) | OPS_DEV_DSN per request | postgres | raw psycopg per op; mounted only when OPS_DEV_DSN set (main.py:110-111) |
| ops recognition router (4 mutations + 2 view reads) | OPS_DEV_DSN | postgres | mutations = DB fn calls autocommit (recognition.py:52); _read_view non-autocommit (read-only) |
| ops-intake package + CLI (`ops-intake intake/approve --dsn`) | explicit dsn arg (cli.py) | postgres in all documented runs | third entry point, bypasses API entirely |
| package/API/migration test harnesses (conftest, test_00x) | OPS_DEV_DSN, fallback literals user=postgres; ops_test-only guards | postgres | conftest fallback dbname=ops_dev is dead code (guard rejects it) |
| smoke-estimator-native.mjs (operations-web) | OPS_DEV_DSN (:314), repacks to PG* env, shells psql (:360-364) | postgres | sixth OPS_DEV_DSN consumer; must be in the cutover list |
| 4b1 backfill + migrations + gen_008 seed | ssh + docker exec psql -U postgres | postgres, explicitly | operator/admin path; stays superuser post-cutover |
| legacy apps/control-plane-api/migrations/*.py scripts | DATABASE_URL / SOURCE_URL / TARGET_URL direct psycopg2 | ambient - PROD-CAPABLE (MANIFEST.md:24 "ambient PG env points at prod") | dormant but unretired write identities |

Durable host secrets (infra/.env, names only): DEV_PG_PASSWORD (the cluster superuser password = the ops lane credential today), TCC_BREAKER_RO_PW, TCC_BREAKER_CODEX_PW, SUPABASE_PROD_DSN (a persisted PROD identity on the host - belongs in the rotation story, out of this packet). No .env.local / apps/control-plane-api/.env exist; OPS_DEV_DSN is exported ad hoc.

OPS_DEV_DSN is the single app-side choke point: rotating its value to ops_app credentials cuts over routers, package, CLI-documented runs, tests, and the smoke script at once.

## 3. The FULL sanctioned mutation surface

All DB functions below are SECURITY INVOKER (live pg_proc), so under the current shape the CALLER needs the listed table privileges. "FOR UPDATE" needs UPDATE privilege on at least one column of the locked table (PG SELECT docs; must be proven against column-scoped grants in the harness).

| # | Path | Mechanism | Tables + columns written | Guard | Privilege ops_app would need (as-is / after DEFINER) |
|---|---|---|---|---|---|
| 1 | POST /recognition/completion/attest | ops.attest_apparatus_complete (009:74) | UPDATE ops.apparatus(status,updated_at); INSERT ops.completion_attestation | ops.completion_ctx GUC (set in-fn, is_local) + apparatus FOR UPDATE + provenance approved + frozen basis + uq_completion_attestation_active | UPDATE(status,updated_at) apparatus + INSERT completion_attestation + SELECT persons / EXECUTE only |
| 2 | POST /recognition/completion/{id}/revoke | ops.revoke_completion_attestation (009:123) | UPDATE apparatus(status,updated_at); UPDATE completion_attestation(revoked_at,revoked_by,revoke_reason) | ctx GUC; net-recognition gate; trg_completion_attestation_immutable single sanctioned transition | same pattern / EXECUTE only |
| 3 | POST /recognition/events/recognize | ops.approve_and_recognize (005:71, redef 009:163) | INSERT ops.revenue_recognition_event (full snapshot row) | apparatus FOR UPDATE; status Complete; active attestation; net=0; trg_revrec_insert_integrity + revrec_immutable (append-only) | INSERT revenue_recognition_event + UPDATE apparatus (lock) / EXECUTE only |
| 4 | POST /recognition/events/{id}/reverse | ops.reverse_recognition (005:127) | INSERT revenue_recognition_event (reversal, negative) | event+apparatus FOR UPDATE; uq_revrec_one_reversal; non-blank reason | same / EXECUTE only. NOTE: absent from the plan's DEFINER list - must be added (verified MISS-3) |
| 5 | (no API router) record/issue x2/discard/void billing | ops.record_billing_application (006:989), issue_billing_application 6-param (006:508) + 3-param (006:1049), discard_draft (006:1099), void (006:1128) | INSERT/DELETE billing_application_draft; INSERT billing_application + _line; UPDATE billing_application(status,voided_*) with trigger-cascaded UPDATE _line(is_voided) (006:252) | ops.billing_ctx GUC set/reset in-fn on all paths; project FOR UPDATE; application_no max+1; deferred header=sum(lines) via trg_billing_consistency_header/_line (006:971/977) | INSERT/UPDATE/DELETE on all 3 billing tables + UPDATE lines for the void cascade (INVOKER trigger) / EXECUTE only; no live caller today - EXECUTE grant deferrable |
| 6 | POST /intake, /intake/native, /review, /reject | Python direct DML - envelope.py (:320,:432,:537,:586 INSERT intake_runs; :228,:424,:582,:691 UPDATE intake_runs; :333,:458 INSERT intake_source_files; :252 etc INSERT intake_validation_findings; :205 FOR UPDATE; :409,:577 advisory lock) | ops.intake_runs (INSERT+UPDATE, shape-bounded by trg_intake_run_immutable write-once), ops.intake_source_files (INSERT), ops.intake_validation_findings (INSERT) | trigger write-once provenance; uq_intake_one_active; pg_advisory_xact_lock | direct DML: INSERT+UPDATE intake_runs, INSERT source_files, INSERT findings - cleanly separable envelope grant block |
| 7 | POST /intake/{run}/approve = approve_run, THE crux | Python direct DML - approve.py + load.py | DELETE ops.scopes (approve.py:57; RI ON DELETE CASCADE fans to scope_quote/_line/tasks/apparatus with OWNER privileges); INSERT/UPDATE ops.projects (load.py:29 upsert; approve.py:126 provenance_status); INSERT scopes (load.py:72); INSERT scope_quote (load.py:95); INSERT+UPDATE tasks (load.py:122 upsert); INSERT scope_quote_line (load.py:138 - fires INVOKER trigger maintain_scope_quote_hours = UPDATE scope_quote.total_quoted_hours charged to caller); INSERT ops.apparatus incl status='Not Started', source, provenance_status='draft' (load.py:169); UPDATE apparatus(quoted_revenue,provenance_status,updated_at) (approve.py:110); UPDATE scope_quote(is_frozen,frozen_at) (:120); UPDATE intake_runs status approved / revision_blocked (:321,:158); FOR UPDATE locks intake_runs(:192), projects(:233), ALL project apparatus (:237) | advisory lock ordering; trg_intake_run_immutable; freeze/protect/scope-immutable trigger lattice; NO SECURITY DEFINER wrapper exists anywhere | DELETE scopes; INSERT+UPDATE projects, tasks; INSERT scopes, scope_quote, scope_quote_line; UPDATE scope_quote(total_quoted_hours,is_frozen,frozen_at); INSERT apparatus + UPDATE apparatus(quoted_revenue,provenance_status,updated_at); INSERT findings; INSERT+UPDATE intake_runs; SELECT on billing_application, revenue_recognition_event, scope_quote, scopes, projects, persons (conflict/foreign-source checks) |
| 8 | GET /recognition/worklist, /rollup | direct SELECT, hardcoded 2-view allowlist (recognition_router.py ~:94; correct names: v_completion_recognition_worklist, v_completion_recognition_rollup) | none | n/a | SELECT on 2 views (+ report views as UI grows) |
| 9 | catalog resolve (intake) | catalog.py:20 SELECT core.v_equipment_models_resolved | none (read-only; only runtime core.* access) | n/a | USAGE core + SELECT on view (+ base table via view owner) |
| 10 | work lane: POST/PATCH x14 /api/v1/work/* | services/work/mutations.py dynamic SQL via SQLAlchemy engine (mounted UNCONDITIONALLY, main.py:90) | work.projects, work_packages, tasks, assignments, dependencies, execution_issues, progress_snapshots | 10 work triggers: updated_at setters + UNCONDITIONAL lifecycle validators (no GUC escape hatch) | direct DML required - SECURITY DEFINER strategy does NOT cover this lane; tables empty in ops_dev (canonical home apex_pm_stage) - EXCLUDE from ops_app |
| 11 | operator/admin: 4b1 backfill, migrations, 008 seed, truncate fixtures | psql -U postgres; DDL (CREATE TABLE ops.backfill_4b1_snapshot) + UPDATE apparatus.equipment_model_ref | admin-only | preflights pin ops_dev | NONE - stays on postgres, excluded from ops_app |

Dormant: ops.standard_hours (153 rows, 002:14; no runtime read or write - D4 removed the catalog write) and ops.backfill_4b1_snapshot - grant matrix must dispose of both explicitly (SELECT-or-nothing). No sequences exist anywhere in ops_dev (all UUID PKs; billing application_no is max+1 under lock) - zero sequence grants needed.

## 4. Current grants/defaults reality (live catalog, ops_dev + ops_test)

- Schemas: ops, core, AND work (work was missed by the raw extraction; verification added it) - all owner postgres, nspacl NULL = owner-only, no PUBLIC USAGE. catalog schema does not exist. public = {pg_database_owner=UC,=U}: PUBLIC USAGE only, NO CREATE (PG15+ default, read from nspacl, not assumed).
- Relations: 43 total user relations (ops 17 tables + 11 views; core 1+1; work 8 tables + 5 views). ALL: owner postgres, relacl NULL (zero grants to anyone), relrowsecurity=false (RLS off everywhere). Zero column-level ACLs (pg_attribute.attacl empty).
- Functions: 35 total (ops 28 - not 29 as the raw extraction said - work 7). ALL: prosecdef=false (SECURITY INVOKER), proconfig NULL (search_path NOT pinned), owner postgres, proacl NULL = built-in default = EXECUTE TO PUBLIC. Live-verified: has_function_privilege = t for infisical/orchestration/tcc_breaker_* on ops.attest_apparatus_complete. The ONLY SECURITY DEFINER in the whole tree is an unrelated Supabase prod migration.
- Triggers: 29 non-internal (19 ops + 10 work), all tgenabled='O' (skipped in replica mode). GUC-gated, fail-closed (current_setting(...,true) IS DISTINCT FROM '1' -> raise): apparatus_completion_guard (completion_ctx); trg_billapp_immutable, trg_billdraft_gate, trg_billline_immutable (billing_ctx). The other 15 ops + 10 work triggers are unconditional integrity guards; work lifecycle validators have NO GUC escape hatch at all.
- Defaults: pg_default_acl EMPTY (zero ALTER DEFAULT PRIVILEGES) - future functions will silently re-acquire PUBLIC EXECUTE. pg_database.datacl NULL on ops_dev AND ops_test = PUBLIC CONNECT+TEMP. No event triggers, publications, subscriptions, FDWs, procedures, or large objects; only plpgsql extension.
- FK cascade levers: scopes->projects is ON DELETE CASCADE too (pg_constraint confdeltype='c') - DELETE on ops.projects is one level ABOVE the sanctioned approve.py:57 scopes cascade and must NEVER be granted. intake_source_files/findings -> intake_runs also cascade.
- ops_test STRUCTURAL caveat: ONLY public exists there; ops, core, work are torn down/rebuilt by the test ladder. Grants applied ad hoc will not persist - the entire grant layer must live in the migration files.
- Migrations 001-011 contain ZERO GRANT / REVOKE / ALTER OWNER / SECURITY DEFINER statements (grep-verified). There is no grant layer to amend; 012 creates it from nothing.

## 5. Gate requirements (ratified) vs current reality - compliance matrix

Sources: spec docs/superpowers/specs/2026-06-23-ops-recognition-bridge-design.md (S5.5:120, S5.7:150, S5.11:178-183, S9, S10:208-210, findings:221/224); IRP docs/review/IRP_RECOGNITION_BRIDGE_SPEC_2026-06-23.md:27 (B6/D2); plan slice1 :42/:2804; MANIFEST.md:4,:16-18,:24,:29; master index :10,:99-107; FIELD_MAPPING_PACKET :22/:256. All citations byte-verified.

| Gate | Requirement | Current reality | Status |
|---|---|---|---|
| GATE-1 | REVOKE INSERT, UPDATE(status,source,provenance_status) ON ops.apparatus for ops_app (spec:181) | No ops_app role; no grants exist at all; AND the sanctioned writer performs exactly these writes (load.py:169, approve.py:110) | NOT IMPLEMENTED + LITERALLY UNIMPLEMENTABLE as written - crux C1 |
| GATE-2 | No direct DML on completion_attestation or revenue_recognition_event (spec:181; plan:2804) | Tables owner-only, but the app IS the owner-superuser | NOT IMPLEMENTED |
| GATE-3 | Mutation fns become SECURITY DEFINER, owner-owned (spec:181; plan:2804 names attest/revoke/approve) | All 28 ops fns prosecdef=f | NOT IMPLEMENTED; ratified list UNDER-ENUMERATED: reverse_recognition (in the slice's own wrapper surface, INSERTs the ledger) + the 5 billing fns are missing (verified MISS-3) |
| GATE-4 | search_path = ops, pg_temp pin (NOT public; IRP-B3) (spec:181,:221) | proconfig NULL on all 35 functions | NOT IMPLEMENTED |
| GATE-5 | REVOKE CREATE ON SCHEMA public FROM PUBLIC (spec:181) | Already the live state: nspacl =U/ only (PG15+ default, dev-verified; also holds on Supabase prod) | ALREADY SATISFIED - keep as an idempotent assert, not an open hole |
| GATE-6 | Tests run AS ops_app; direct UPDATE status='Complete' / INSERT = permission denied, fn path succeeds (spec:181; plan:2804) | Every harness connects as postgres (user=postgres fallback literals) | NOT IMPLEMENTED |
| GATE-7 | HARD release gate: no ops.* recognition path to prod until boundary applied (spec:183; IRP:27) | Prod has no ops.* objects (MANIFEST:4; master index :10) | GATE HOLDING; boundary absent |
| GATE-8 | Boundary = dedicated LANE-WIDE hardening packet (spec:183,:209) | Zero GRANT/REVOKE in 001-011 | NOT STARTED - this audit is its input |
| GATE-9 | ctx-GUC = misuse guard, not boundary; interim = host-gating (spec:150,:178-180) | Verified true: GUC unprivileged (test exploits it, test_recognition_wrappers.py:63); host-gating enforced at main.py:110-111 | INTERIM POSTURE CONFIRMED ACCURATE |
| GATE-10/11 | Prod apply of 005-011 separate, gated; boundary is the precondition; dev interim OK (spec:210, S9, :12) | Consistent; MANIFEST rows 009/010/011 all carry "prod blocked behind ops_app gate"; SQL headers too (009:6, 011:4) | HOLDING |
| GATE-12 | Out of the bridge slice: billing, production tracking (spec:19,:208-210) | Billing fns live in dev but have NO API caller | CONSISTENT - lets billing EXECUTE grants be deferred |
| GATE-13 | Law 6 migration invariants for any prod convergence (master index :99-107) | n/a now | APPLIES AT PROD CONVERGENCE |

Ratified-doc GAPS the packet must add (not in any gate text today):
- G-A: REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ops (and core/work) FROM PUBLIC + ALTER DEFAULT PRIVILEGES - otherwise GRANT USAGE arms PUBLIC-default EXECUTE on everything, including future DEFINER fns, for every USAGE-holder (verified MISS-2).
- G-B: DEFINER conversion set completion: + reverse_recognition + 5 billing fns (verified MISS-3).
- G-C: The approve_run/GATE-1 collision itself - spec 5.7 blesses "normal intake INSERT" at the trigger layer while 5.11 revokes it at the role layer (verified MISS-4). Needs an operator-ratified amendment.
- G-D: core.* read grants (USAGE + SELECT on v_equipment_models_resolved) and explicit work.* EXCLUSION - unmentioned anywhere (verified MISS-6).
- G-E: REVOKE CONNECT ON DATABASE ops_dev/ops_test FROM PUBLIC - closes the zero-grant advisory-lock DoS and cross-lane connects; aligns with one-DB-per-workstream policy.

## 6. DESIGN CRUXES

C1. THE approve_run CRUX (role architecture). The sole sanctioned domain writer is Python direct DML performing the very writes GATE-1 revokes. Three viable architectures:

- (A) Single ops_app + column-scoped apparatus grants + DEFINER conversion for the fn layer.
  Grants: INSERT on ops.apparatus (needed by load.py:169) + UPDATE(quoted_revenue, provenance_status, updated_at) - NOT status, source, scope_id. Convert the 9 mutation fns (4 recognition-bridge + reverse + 4-of-5... i.e. attest, revoke, approve_and_recognize, reverse_recognition, record/issue x2/discard/void) to SECURITY DEFINER with search_path pinned; ops_app gets EXECUTE and ZERO DML on revenue_recognition_event, completion_attestation, billing_application/_line/_draft. GUC becomes internal to the definer layer (C3). DEFINER also fixes the INVOKER trigger-cascade ripple for billing (void's line-void cascade runs in definer context).
  Tradeoffs: smallest code delta (DSN cutover + fn DDL only); deviates from GATE-1's literal "REVOKE INSERT" - needs operator ratification of amended text ("governed-complete flips and ledger/attestation/billing writes are function-only; apparatus materialization INSERT is the sanctioned intake path, bounded by the trigger lattice"). Residual: ops_app could INSERT an apparatus row with status='Complete' + provenance_status='approved' after setting the GUC itself (completion guard fires on INSERT too) - a forged completion DISPLAY, but NOT forged revenue: the ledger is DEFINER-only and approve_and_recognize re-checks attestation + frozen basis + net=0. Optional tightening: column-list INSERT excluding status/provenance_status + column DEFAULTs + a 2-line load.py change.
- (B) Two roles: ops_api (routers: EXECUTE on DEFINER fns + envelope-table DML + view SELECTs) and ops_intake_writer (approve_run materializer DML only), separate DSNs in the same process.
  Tradeoffs: GATE-1 satisfied literally for the API-facing role; cleaner audit story. Costs: two credentials to distribute/rotate, per-route engine selection in intake_router, and the writer capability still exists on the same host - it moves the line, does not remove it. Reasonable as a LATER refinement when the estimator envelope path productionizes.
- (C) Move the materializer in-DB: a SECURITY DEFINER ops.approve_run(...) absorbing envelope.py/load.py/approve.py DML (~24 statements + JSON payload logic). ops_app becomes EXECUTE-only everywhere; GATE-1 fully literal.
  Tradeoffs: a product refactor of a proven, merged intake path, not a bounded hardening packet; large plpgsql surface for review; slow. Reject for 012.

Lean: (A) now, (B) noted as future refinement, (C) rejected. Whatever is chosen, the amendment to GATE-1 must be ratified by the operator - the spec text as written cannot be satisfied by any grant matrix that keeps approve_run alive.

C2. SECURITY INVOKER everywhere = "EXECUTE-only" is a contradiction today. Calling approve_and_recognize as ops_app without ledger INSERT fails INSIDE the function. The DEFINER conversion is therefore not an optional hardening flourish - it is the enabling move for GATE-2. The conversion set must be the full 9 (G-B), each with `SET search_path = ops, pg_temp` (GATE-4), owner postgres, and paired with G-A's PUBLIC EXECUTE revocation FIRST (a DEFINER fn with PUBLIC EXECUTE is a privilege-escalation gift to every future USAGE-holder).

C3. GUC ctx authority under least privilege. After (A): set_config stays inside the definer fns (is_local, transaction-scoped - pooling-safe); ops_app holds no DML on any GUC-guarded table, so its ability to `SET ops.billing_ctx='1'` is inert. The triggers stay as defense-in-depth against ADMIN-session accidents. No separate privileged setter fn/role is needed. Alternative (grant ops_app guarded-table DML and keep the GUC advisory) re-opens the forgery-by-app-role path and is strictly worse.

C4. Privilege ripple mechanics the grant matrix must encode (all verified):
  - FOR UPDATE needs UPDATE privilege (>=1 column) on intake_runs, projects, apparatus for approve_run - satisfied by the column-scoped UPDATE grants, but MUST be proven by a harness test against column-only grants.
  - INVOKER trigger DML charges the caller: maintain_scope_quote_hours needs ops_app UPDATE(total_quoted_hours) on scope_quote or every materialization fails.
  - RI cascades run with table-owner privileges: DELETE on scopes alone is sufficient AND is the sanctioned mass-delete; REVOKE DELETE on apparatus does not (and should not) stop it. DELETE on projects must never be granted (larger cascade lever).

C5. Superuser-only escape hatches. ALTER TABLE ... DISABLE TRIGGER, session_replication_role=replica, DDL, 4b1-style backfills, test TRUNCATE fixtures remain postgres-only by design. The packet does not close these; it makes the superuser a rare, deliberate, auditable identity instead of the default app identity. Migrations/backfills continue on an admin DSN.

C6. Pooling / session state. No pooler today (direct, sslmode=disable). Advisory locks are pg_advisory_xact_lock (transaction-scoped) and all set_config calls are is_local - transaction-pooling safe. Hazards if a pooler is ever fronted: config.py's statement_timeout startup option is only exempted for *.pooler.supabase.com/:6543; recognition wrappers are autocommit single-statement (safe). No packet action needed beyond recording this.

C7. ops_test harness impact. ops/core/work do not exist in ops_test between runs - ALL grants + DEFINER DDL must live in migration 012 so the up/down/up ladder recreates them. CREATE ROLE is cluster-level: 012 needs an idempotent guarded block (DO $$ ... IF NOT EXISTS), password set OUT-OF-BAND (operator, per credential-handling discipline - never in a migration file). Tests need dual identity: admin DSN for ladder/TRUNCATE fixtures, OPS_APP_DSN for behavior + boundary proofs (GATE-6). Fix the dead conftest fallback (dbname=ops_dev vs ops_test guard) in the same packet.

C8. Dev-vs-prod divergence (re-ground before prod). Everything above is dev-cluster fact. Supabase prod differs materially: postgres there is NOT a superuser (no DISABLE TRIGGER on others' tables, restricted session_replication_role), managed roles (anon/authenticated/service_role/supabase_admin) and pre-existing default privileges exist, the pooler is in path (:6543 - config.py already special-cases), and role/DDL surface is constrained by the platform. Migration 012 as authored for dev CANNOT be replayed verbatim on prod. Required before any prod apply: re-run this audit's catalog queries against fxoyniqnrlkxfligbxmg, then author a prod-variant packet (this is exactly GATE-7/11's sequencing, plus memory precedent: REST visibility != mutability at plan tier - pre-flight and post-verify).

C9. work.* neighbor surface. A full second domain (8 tables, 7 fns, 10 triggers, 14 unconditionally-mounted write endpoints via dynamic SQL) lives in the SAME database and SAME API binary, currently empty in ops_dev (canonical home apex_pm_stage). If ops_app is ever handed a DSN that the work router also uses, work.* writes would fail (no grants) - which is the CORRECT fail-closed outcome. The packet must grant work.* NOTHING; disposition of the schema itself (drop from ops_dev vs leave dormant) is a separate operator decision.

## 7. Proposed packet scope sketch (bounded; no product features)

Migration 012_ops_app_role_boundary.sql (runs on ops_test + ops_dev via the existing ladder; single transaction where possible; paired down-migration):
1. Idempotent CREATE ROLE ops_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS (guarded DO block; password out-of-band).
2. Hygiene: REVOKE CONNECT ON DATABASE <current> FROM PUBLIC; GRANT CONNECT TO ops_app (+ existing legit roles as needed). REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ops, core FROM PUBLIC (work too); ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ops REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC. Assert (not re-apply) public-schema no-CREATE.
3. DEFINER conversion x9: attest_apparatus_complete, revoke_completion_attestation, approve_and_recognize, reverse_recognition, record_billing_application, issue_billing_application (BOTH overloads), discard_draft_billing_application, void_billing_application -> SECURITY DEFINER, SET search_path = ops, pg_temp, owner postgres. (Optionally pin search_path on the remaining 19 trigger/helper fns - cheap hygiene.)
4. GRANT USAGE ON SCHEMA ops, core TO ops_app. EXECUTE to ops_app on the 4 live recognition fns; billing EXECUTE deferred until an API caller exists (GATE-12) - decision D3.
5. Table grant matrix exactly per section 3 rows 6-9: envelope block (intake_runs INSERT/UPDATE/SELECT; intake_source_files, intake_validation_findings INSERT/SELECT); domain block (projects INSERT/UPDATE/SELECT; scopes INSERT/DELETE/SELECT; scope_quote INSERT/SELECT + UPDATE(total_quoted_hours,is_frozen,frozen_at); scope_quote_line INSERT/SELECT; tasks INSERT/UPDATE/SELECT; apparatus INSERT/SELECT + UPDATE(quoted_revenue,provenance_status,updated_at) - per D2); read block (SELECT on the 11 ops views, persons, revenue_recognition_event, billing_application, standard_hours if kept); core block (SELECT on core.v_equipment_models_resolved + equipment_models). EXPLICITLY ZERO grants: revenue_recognition_event/completion_attestation/billing tables DML, DELETE on projects/apparatus/tasks/scope_quote*, backfill_4b1_snapshot, anything in work.*.
6. In-migration posture asserts (DO block): has_table_privilege('ops_app', 'ops.revenue_recognition_event','INSERT') = false, etc - fail the migration if the matrix drifts.

Code cutover (small): rotate OPS_DEV_DSN value to ops_app credentials (routers, package/CLI runbook, smoke-estimator-native.mjs); introduce OPS_DEV_ADMIN_DSN for migration harnesses/conftest ladder/fixtures; fix the dead conftest fallback; MANIFEST + spec S5.11 status updates (housekeeping is part of done).

Tests-as-ops_app (GATE-6): test_012 up->down->up on ops_test; boundary proofs AS ops_app with UNMASKED exit codes: (a) direct UPDATE apparatus SET status='Complete' -> permission denied (column revoked); (b) direct INSERT revenue_recognition_event -> denied; (c) SET ops.billing_ctx='1' then INSERT billing_application -> denied BY PRIVILEGE, proving the boundary moved off the GUC; (d) direct INSERT/UPDATE completion_attestation -> denied; (e) DELETE projects -> denied; (f) FOR UPDATE lock paths succeed under column-scoped grants. Positive: full intake -> approve -> attest -> recognize -> reverse pipeline green as ops_app; package + API suites run under OPS_APP_DSN (admin DSN for fixtures only). Post-merge: fresh adversarial audit pass (post-completion-audit precedent) before declaring the gate satisfied.

Explicitly NOT in 012: any prod DDL (C8 re-grounding first), billing EXECUTE/API, RLS.

## 8. Out of scope / non-goals

- Prod apply of ops 005-012: separate, operator-gated, AFTER a prod-grounding audit of the Supabase role model (GATE-7/10/11, C8).
- RLS on ops.* (single-role service posture for now; RLS is a later multi-tenant concern - FIELD_MAPPING_PACKET :256).
- Billing API router / Chip-4 productization (GATE-12); billing fns get converted+locked but not exposed.
- work.* lane hardening or schema drop from ops_dev - separate decision + packet (C9); 012 only guarantees zero grants.
- Legacy apps/control-plane-api/migrations/*.py direct-connect scripts and the SUPABASE_PROD_DSN custody in infra/.env - flagged to the secret-custody lane; not this packet.
- 4b1-style backfills, DDL, seeds: remain admin-identity by design (C5).
- Rotation/distribution mechanics of the new ops_app credential (Infisical lane owns propagation); 012 only requires the password be set out-of-band.
- records/learning/orchestration lanes (own DBs, own packets per one-DB-per-workstream).
