# ops_app Role-Boundary Hardening (Migration 012) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the ops.* lane a real privilege boundary so no application identity can both fabricate apparatus AND recognize revenue, and no app identity is a superuser.

**Architecture:** Migration 012 creates three least-privilege roles (ops_intake_writer LOGIN, ops_api LOGIN, ops_fn_owner NOLOGIN owning the 9 SECURITY DEFINER mutation functions), applies PUBLIC hygiene, installs a column-scoped grant matrix with in-migration posture asserts, and tightens the completion guard (H2). A three-DSN cutover (OPS_INTAKE_WRITER_DSN / OPS_API_DSN / OPS_DEV_ADMIN_DSN) then retires OPS_DEV_DSN as an app identity across routers, mount gate, package harness, route tests, infra migration tests, and the smoke script.

**Tech Stack:** PostgreSQL 17 (role/grant DDL, SECURITY DEFINER, has_*_privilege / aclexplode asserts), Python 3 + psycopg + pytest (migration ladder tests, package suite), FastAPI (control-plane-api routers), the infra ops migration ladder convention (NNN.sql + NNN_down.sql + test_NNN.py, self-contained autouse fixtures).

**Spec (SSoT):** `2026-07-01-ops-app-role-boundary-design-v3.md` (v3, 425 lines) - moves to `docs/superpowers/specs/` in Task 1. Section references below (S0..S12) are to that file.

**Execution environment:** ALL commands run on the Olares host over `ssh olares-mesh`. Repo root: `/home/olares/code/apex/apex-power-ops-platform`. Lane branch: `ops/role-boundary-012` off `main`. `rg` AND `uv` are NOT on the ssh non-login PATH - prefix host commands with `export PATH=$HOME/.local/bin:$PATH` (uv lives there) and use `grep`, never `rg`.

**Dev-DB connection contract (grounded 2026-07-01; enforced by Task P preflight):** the dev PG is the Olares-managed container `apex-dev-pg` (PG17). `infra/compose.dev-lanes.yml:9-10` declares `ports: ["127.0.0.1:5432:5432", "100.64.0.1:5432:5432"]`, and every migration/test file assumes host TCP on `127.0.0.1:5432`. At authoring the running container had DRIFTED from that contract (no published ports; only `docker exec apex-dev-pg psql` worked; psycopg from the host shell failed on 127.0.0.1:5432, 100.64.0.1:5432, and 127.0.0.1:55432). **Task P (operator-gated) reconciles the container to its compose contract and verifies host TCP is live BEFORE any pytest task.** Admin auth = `DEV_PG_PASSWORD` (present in `infra/.env`). NEVER cat/echo `.env`, any password, or any DSN value. Do NOT point this lane at `127.0.0.1:55432` (that is `apex-dev-postgres-1`, a PG16 old stack).

**Standard env preamble** (`<ENV>` below; every pytest command runs it first from repo root; `$DEV_PG_PASSWORD` expands on the host, never printed):
```bash
cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; export OPS_DEV_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"
# role DSNs added AFTER the Operator Checkpoint (before Task 9): OPS_INTAKE_WRITER_DSN / OPS_API_DSN (user=<role>, dbname=ops_test, password out-of-band)
```
Test invocations (this repo is NOT a uv workspace - deps differ per tier):
- Infra migration tests: `<ENV> && cd infra/database/migrations/ops && uv run --with "psycopg[binary]" --with pytest pytest <file> -v`.
- Package tests: `<ENV> && cd packages/ops-intake && uv run pytest tests/ -v` (ops-intake has its own pyproject).
- **API (control-plane-api) tests:** `<ENV> && export DATABASE_URL=postgresql://localhost/ops_test && cd apps/control-plane-api && uv run --with-requirements requirements-dev.txt pytest <file> -v`. App deps live in `requirements.txt`/`requirements-dev.txt` (bare `uv run pytest` fails collecting psycopg), and importing `main` requires `DATABASE_URL` (config.py:31) - a placeholder here; ops behavior routes through the role DSNs. If `requirements-dev.txt` lacks pytest, add `--with pytest`.

(Test files read `OPS_DEV_ADMIN_DSN`; test_012's localhost fallback also honors `OPS_DEV_PGPASSWORD`/`PGPASSWORD` if the DSN is unset.)

## Global Constraints

Copied verbatim from spec v3 - every task's requirements implicitly include these:

1. **D2 (tightened):** apparatus.status leaves every login role. The ONLY writer of apparatus.status is ops_fn_owner via the DEFINER attest/revoke fns. ops_intake_writer INSERT on apparatus is column-scoped to every load.py column EXCEPT status; its UPDATE is (quoted_revenue, provenance_status, updated_at).
2. **Never table-level UPDATE on a login role** (S0 FAIL branch: "DO NOT broaden ops_intake_writer to table-level UPDATE on apparatus"). Relation-level UPDATE is authorized for ops_fn_owner ONLY on revenue_recognition_event and projects (FOR UPDATE locks).
3. **Forge-closure invariant:** ops_intake_writer can create apparatus but cannot attest/recognize; ops_api can recognize but cannot create apparatus; ops_fn_owner cannot be reached by SET ROLE from either login role.
4. **Passwords for the two LOGIN roles set out-of-band** by the operator (`ALTER ROLE ... PASSWORD`; never in a file or a model-visible terminal).
5. **ALL grants + DEFINER DDL live IN the migration files** (ops_test rebuilds schemas each run; CREATE ROLE is cluster-level -> idempotent guard).
6. **Ordering (load-bearing, S6):** (i) REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ops, core FROM PUBLIC first; (ii) roles + `REVOKE ops_fn_owner FROM ops_intake_writer, ops_api`; (iii) DEFINER + search_path + OWNER TO ops_fn_owner; (iv) owner object grants; (v) EXECUTE on the 4 recognition fns TO ops_api only.
7. **Down ordering (S7, DEV-7-amended; wording updated per F-012-3):** FIRST ALTER each fn OWNER TO postgres, THEN revoke this database's grants (the two LOGIN roles get DATABASE-SCOPED revokes - tables/routines/usage plus REVOKE CONNECT ON the current database - because DROP OWNED BY a login role also strips shared-object CONNECT cluster-wide; DROP OWNED BY is kept ONLY for the NOLOGIN ops_fn_owner), THEN **guarded/drop-if-safe DROP ROLE** - skip any password-bearing login role (`pg_authid.rolpassword IS NOT NULL`) with a NOTICE so a routine down/reset never deletes ops_intake_writer/ops_api after their SCRAM passwords are set out-of-band (DEV-7).
8. **Unmasked exit codes:** never pipe a test through `tail`/`head` in a `&&` chain; each test command's own exit code is the gate.
9. **ASCII-only** in every authored file (SQL, Python, docs). Audit per file before commit: `grep -nP '[^\x00-\x7F]' <file>` must return nothing.
10. **The grant matrix is FROZEN during execution.** If a test failure looks fixable by broadening a grant: STOP - that is a spec finding for the operator, not a build decision.
11. **Acceptance grep (S8) is part of done:** zero OPS_DEV_DSN references in the infra migration tests, both routers, mount gate, both named route-test files, smoke-estimator-native.mjs; no OPS_DEV_DSN fallback in packages/ops-intake/tests/conftest.py. (The no-DB mount-gate module `test_ops_route_mount_gate.py` intentionally references OPS_DEV_DSN to assert its own inertness and is excluded from this S8 grep scope, which the actual Task 11 grep enforces.)
12. **Dev only.** Migration applies to ops_test (via the test ladder) in this plan. ops_dev apply and prod are operator-gated, outside this plan's tasks.
13. Commit identity: `Jason Swenson <jasonlswenson@gmail.com>`; every commit ends with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## Grounded facts the plan relies on (verified 2026-07-01 against live source + ops_dev catalog)

- load.py `insert_apparatus` (packages/ops-intake/src/ops_intake/load.py:161-186): INSERT columns are `scope_id, task_id, apparatus_designation, apparatus_type, equipment_model_ref, status, drawing_reference, quoted_hours, quote_line_id, source, legacy_source_id, provenance_status`; `status` is the positional literal `'Not Started'` in VALUES (not in the params tuple); `provenance_status` is the literal `'draft'`. The 11 writer INSERT columns = that list minus status.
- load.py `upsert_project` (load.py:19-63): INSERT columns match the spec's 15-column projects INSERT list; DO UPDATE SET writes 13 columns (+`updated_at`); approve.py `_freeze` (approve.py:126) adds `provenance_status` -> the pinned 14-column projects UPDATE set.
- approve.py locks: intake_runs row lock ~:190; **projects `for update` at :233**; **apparatus `for update of a` at :235-239**. `_freeze` (:108-117) UPDATEs apparatus (quoted_revenue, provenance_status, updated_at) only - never status.
- intake_router.py `_dsn()` at :52-53 reads `OPS_DEV_DSN`; recognition_router.py `_dsn()` at :23-24 reads `OPS_DEV_DSN`, `_read_view()` at :93-106 calls `_dsn()` (single change point); main.py `_ops_intake_enabled()` at :109-111 + guarded includes :114-118.
- Completion guard: 009_recognition_bridge.sql:53-71, bare `create function` + `create trigger` (H2 lands as CREATE OR REPLACE; trigger untouched).
- Ladder convention: self-contained `test_NNN_*.py` with session-autouse `apply_migrations`; no conftest in the migrations dir; MANIFEST.md:24 documents the invocation. test_011 has its own OPS_DEV_DSN fallback (test_011:11-16).
- Ladder-length divergence (must fix): packages conftest + test_011 apply 001..011; test_ops_intake_routes.py applies 001..**010**; test_ops_recognition_routes.py applies 001..**009**. All must extend to 012.
- ops has exactly **11 views**: v_apparatus_quote, v_apparatus_recognition, v_billing_application_sov, v_completion_recognition_rollup, v_completion_recognition_worklist, v_draft_preview, v_project_billing, v_project_recognition, v_recognition_review_queue, v_scope_recognition, v_unbilled_recognition.
- **Zero sequences** in ops/core (no USAGE-on-sequence grants needed). **Zero functions in core** (the S7 REVOKE loop still runs for drift closure).
- **No `core.*` reference in any of the 9 fn bodies** (verified via pg_get_functiondef) -> NO `GRANT USAGE ON SCHEMA core TO ops_fn_owner`. Owner read-surface audit vs fn bodies: every ops.* table each fn touches is covered by the S5 owner grant list (RV-1 closure verified against live bodies).
- packages/ops-intake/tests/test_recognition_wrappers.py contains the superuser GUC-bypass setup (`set local ops.completion_ctx='1'; update ops.apparatus set status='Complete'`) - becomes admin-connection setup DML in Task 9.

## Plan-level deviations from spec text (mechanical; flagged for operator, see wrap)

- DEV-1: `REVOKE ops_fn_owner FROM ... PUBLIC` omitted - PostgreSQL cannot grant role membership to PUBLIC, so there is nothing to revoke; the pg_has_role posture asserts enforce non-membership durably.
- DEV-2: the PUBLIC-EXECUTE assert uses the pg_proc/aclexplode loop (grantee 0 = PUBLIC), because `has_function_privilege('public', ...)` errors ('public' is not a role). Same enforcement, valid SQL.
- DEV-3: Task 0 probe extended with a projects-lock variant - approve.py:233 does `select ... from ops.projects ... for update` as the writer, which holds only column-scoped projects UPDATE: the identical question at a second lock site.
- DEV-4: 012_down's DROP ROLE is guarded (see DEV-7, which supersedes the original `dependent_objects_still_exist`-only rationale). The dependency guard is retained as a secondary safety (cluster-level roles: once 012 is on ops_dev, an ops_test teardown cannot drop a role with grants in the other DB), but the PRIMARY guard is now password-presence.
- DEV-5: down does NOT `GRANT CREATE ON SCHEMA public TO PUBLIC` - PG15+ default already lacks it; re-granting would create a worse-than-default posture. (The up-side REVOKE stays: harmless if already absent.)
- DEV-6: both route-test ladders extended to the full 001..012 chain (grounded divergence above; the role DSNs cannot work without 012 applied).
- **DEV-7 (operator-ratified 2026-07-01, deviates from spec S7's literal DROP ROLE):** routine down/reset must NOT delete ops_intake_writer/ops_api once their SCRAM passwords are set out-of-band (else re-up recreates them password-less -> every scram login fails, breaking Tasks 9/10/12). 012_down's role drop is guarded: under the admin session, skip DROP ROLE for any role where `pg_authid.rolpassword IS NOT NULL`, leave it in place with a NOTICE. `DROP OWNED BY` still runs first and revokes current-DB grants, so `_down` STILL restores posture (grants gone) even when the role object survives. ops_fn_owner (NOLOGIN, no password) drops/recreates cleanly. The reversibility test asserts grants-revoked, NOT role-absence (Task 6).
- **DEV-8 (L1, ordering note):** section [1] (roles) precedes [2] (PUBLIC REVOKE EXECUTE), whereas spec S6 lists the PUBLIC revoke first. Reason: the membership hardening `REVOKE ops_fn_owner FROM ops_intake_writer, ops_api` needs the roles to exist first. The load-bearing S6 invariant is preserved: [2]'s `REVOKE EXECUTE ... FROM PUBLIC` still runs BEFORE the [3] DEFINER conversion, so there is no fail-open window. Cosmetic ordering only.

## File Structure

Create:
- `infra/database/migrations/ops/012_ops_app_role_boundary.sql` - roles, PUBLIC hygiene, DEFINER conversion, grant matrix, H2 guard, per-section posture asserts
- `infra/database/migrations/ops/012_ops_app_role_boundary_down.sql` - guarded reversal in the spec's explicit order
- `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` - ladder test: posture, denial proofs (SET ROLE tier), FOR-UPDATE regressions, H2, reversibility
- `docs/superpowers/plans/2026-07-01-ops-app-role-boundary.md` (this file) + `docs/superpowers/specs/2026-07-01-ops-app-role-boundary-design-v3.md` (+ audit/decisions/IRP records under `docs/superpowers/specs/ops-app-role-boundary/`)

Modify:
- `packages/ops-intake/src/ops_intake/load.py` (insert_apparatus: drop status)
- `packages/ops-intake/src/ops_intake/approve.py` (ONLY if Task 0 FAILs - bounded fallback)
- `apps/control-plane-api/services/ops/intake_router.py`, `apps/control-plane-api/services/ops/recognition_router.py`, `apps/control-plane-api/main.py`
- `packages/ops-intake/tests/conftest.py`, `packages/ops-intake/tests/test_recognition_wrappers.py`
- `apps/control-plane-api/tests/test_ops_intake_routes.py`, `apps/control-plane-api/tests/test_ops_recognition_routes.py`
- `infra/database/migrations/ops/test_001..test_011*.py` (DSN env rename), `infra/database/migrations/ops/MANIFEST.md`
- `apps/operations-web/scripts/smoke-estimator-native.mjs` (psql read leg)

### Task P: PREFLIGHT - dev-DB host-TCP + credential readiness (OPERATOR-GATED; blocks every pytest task)

**Why operator-gated:** Step 1 likely RESTARTS the durable `apex-dev-pg` dev DB, which other lanes share. Do not run Step 1 without an explicit operator go. Task 0 uses `docker exec` only and does NOT need this gate; Tasks 1+ (all pytest) DO.

**Files:** none in-repo (environment reconcile). May touch `infra/.env` (operator adds role DSNs at the later checkpoint, not here).

**Interfaces:** Produces a LIVE host-TCP endpoint at `127.0.0.1:5432 -> ops_test` reachable by psycopg with `DEV_PG_PASSWORD`, so the `<ENV>` preamble's `OPS_DEV_ADMIN_DSN` connects.

- [ ] **Step 1 (operator go required): reconcile apex-dev-pg to its compose port contract.** The running container has drifted (no published ports). Bring it back to `infra/compose.dev-lanes.yml:9-10` (`127.0.0.1:5432:5432`, `100.64.0.1:5432:5432`). NOTE the compose SERVICE name is `dev-pg` (the CONTAINER name is `apex-dev-pg`, compose:4-6) - target the service. From the repo root so `infra/.env` is read: `ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; docker compose -f infra/compose.dev-lanes.yml up -d dev-pg'` (or the Olares-managed equivalent the operator uses). This RESTARTS the durable dev DB - operator confirms nothing depends on the current drifted state first. Do NOT substitute a docker-network test harness (operator ruling 2026-07-01: keep the host-TCP convention).

- [ ] **Step 2: credential/loader readiness (Infisical wrinkle).** `infra/infisical/dev-psql.sh:16` fails before TCP in this checkout because `.env.agent` (the Infisical machine identity) is absent. Choose ONE, verify, and note which in the lane record:
  - (a) restore/provide the machine identity so `.env.agent` exists and `dev-psql.sh` works, OR
  - (b) use the approved env loader for this lane: `set -a; . ./infra/.env; set +a` (supplies `DEV_PG_PASSWORD`) - the `<ENV>` preamble already does this and does NOT depend on `.env.agent`.
  Confirm `DEV_PG_PASSWORD` is present without printing it: `ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; test -n "$DEV_PG_PASSWORD" && echo PW_PRESENT=yes || echo PW_PRESENT=NO'` -> `PW_PRESENT=yes`.

- [ ] **Step 3: HARD GATE - verify host TCP** (psycopg reaches ops_test; prints outcome only, never the DSN/password):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; uv run --with "psycopg[binary]" python - <<PYEOF
import os, psycopg
pw = os.environ.get("DEV_PG_PASSWORD", "")
dsn = f"host=127.0.0.1 port=5432 dbname=ops_test user=postgres password={pw} sslmode=disable"
try:
    with psycopg.connect(dsn, connect_timeout=5) as c:
        u, d, s = c.execute("select current_user, current_database(), (select rolsuper from pg_roles where rolname=current_user)").fetchone()
        print(f"ADMIN OK user={u} db={d} super={s}")
except Exception as e:
    print(f"ADMIN FAIL {type(e).__name__}")
PYEOF'
```
Expected: `ADMIN OK user=postgres db=ops_test super=True`. **If this raises OperationalError / prints ADMIN FAIL, STOP** - host TCP is not live; return to Step 1. No pytest task may run until this gate is green.

---

### Task 0: BLOCKING FOR-UPDATE grant spike (hard gate - no downstream task is settled until this resolves)

**Files:** none modified (transient ROLLBACK probe on ops_test).

**Interfaces:** Produces the PASS/FAIL verdict that finalizes the Section 5 writer matrix and decides whether Task 7b (approve.py fallback) exists.

- [ ] **Step 1: Bring ops_test to schema state 001..011** (probe needs DDL only, no rows):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform/infra/database/migrations/ops && for f in 001_identity_skeleton.sql 002_quote_model.sql 003_intake_unique_keys.sql 004_person_anchor.sql 005_recognition_ledger.sql 006_progress_billing.sql 007_intake_envelope.sql 008_core_equipment_models.sql 009_recognition_bridge.sql 010_native_envelope_intake.sql 011_scope_quote_line_description.sql; do docker exec -i apex-dev-pg psql -U postgres -d ops_test -v ON_ERROR_STOP=1 -f - < "$f" || exit 1; done; echo LADDER_OK'
```
Expected: `LADDER_OK`. (If ops_test already holds a partial schema, first run the downs in test_011's `_clean_slate` order: delete from ops.intake_runs; 011_down; 010_down; 009_down; 008_down; 001_down.)

- [ ] **Step 2: Run the spike probe** (spec S0 verbatim + DEV-3 projects variant), single transaction, ROLLBACK:

```bash
ssh olares-mesh "docker exec -i apex-dev-pg psql -U postgres -d ops_test" <<'SQL'
\set ON_ERROR_ROLLBACK on
begin;
create role _spike nologin;
grant usage on schema ops to _spike;
grant update (quoted_revenue, provenance_status, updated_at) on ops.apparatus to _spike;
grant select on ops.apparatus, ops.scopes to _spike;
-- DEV-3: second lock site (approve.py:233) - same question on ops.projects
grant update (project_name, status, quote_revision, contract_value, description,
  source_client_name, source_site_name, source_site_address, source_site_city,
  source_site_state, source_site_zip, source, provenance_status, updated_at)
  on ops.projects to _spike;
grant select on ops.projects to _spike;
set local role _spike;
\echo '=== PROBE A: apparatus FOR UPDATE OF a (spec S0) ==='
select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id
  where s.project_id = (select id from ops.projects limit 1) for update of a;
\echo '=== PROBE B: projects FOR UPDATE (DEV-3, approve.py:233) ==='
select id from ops.projects for update;
reset role;
rollback;
SQL
```
L4 fix: `\set ON_ERROR_ROLLBACK on` (NOT `-v ON_ERROR_STOP=1`) wraps each statement in an implicit savepoint, so if Probe A raises the txn recovers and Probe B STILL runs - both verdicts are visible in one output. Expected on PASS: both SELECTs return `(0 rows)` (empty schema is fine - the permission check runs regardless) under their `\echo` headers, session ends `ROLLBACK`. Expected on FAIL: `ERROR: permission denied for table apparatus` under PROBE A and/or `... projects` under PROBE B - the `\echo` header tells you which lock site failed.

- [ ] **Step 3: Record the verdict** in the lane dir (`/home/olares/code/ops-app-role-boundary/TASK0_SPIKE_RESULT_<date>.md`): the exact psql output, PASS or FAIL, and which probe(s) failed.

- [ ] **Step 4: Branch on verdict.**
  - **PASS:** writer matrix (S5) is FINAL as authored. Tasks 1-12 proceed unchanged; the probe becomes a permanent regression in test_012 (Task 4) plus a two-session concurrency regression. Task 7b does not exist.
  - **FAIL:** the writer matrix and D2 are UNCHANGED (never table-level UPDATE). Insert Task 7b (defined inside Task 7) - the bounded approve.py row-lock fallback per spec S0: drop/narrow the writer's apparatus row-lock (approve.py:235-239) - and, if Probe B also failed, the projects row-lock (:233) - relying on the advisory lock (project_number) + the NO ACTION FK backstop; re-prove (a) no two concurrent approves of the same project_number interleave, (b) concurrent approve+recognize fails closed (aborts, not corrupts). STOP and surface to operator before implementing the fallback (spec: "bounded", but it changes a serialization strategy - operator confirms scope).

- [ ] **Step 5: Tear ops_test back down** (leave no half-applied ladder):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform/infra/database/migrations/ops && docker exec -i apex-dev-pg psql -U postgres -d ops_test -v ON_ERROR_STOP=1 -c "delete from ops.intake_runs" && for f in 011_scope_quote_line_description_down.sql 010_native_envelope_intake_down.sql 009_recognition_bridge_down.sql 008_core_equipment_models_down.sql 001_identity_skeleton_down.sql; do docker exec -i apex-dev-pg psql -U postgres -d ops_test -v ON_ERROR_STOP=1 -f - < "$f" || exit 1; done; echo TEARDOWN_OK'
```
Expected: `TEARDOWN_OK`.

---

### Task 1: Open the lane branch, move the lane docs, create the 012 file set, roles section

**Files:**
- Create: `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (section [1])
- Create: `infra/database/migrations/ops/012_ops_app_role_boundary_down.sql` (role teardown portion)
- Create: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (harness + role tests)
- Create: `docs/superpowers/plans/2026-07-01-ops-app-role-boundary.md`, `docs/superpowers/specs/2026-07-01-ops-app-role-boundary-design-v3.md`, `docs/superpowers/specs/ops-app-role-boundary/` (audit, decisions, IRP records)

**Interfaces:** Produces roles `ops_intake_writer` (LOGIN), `ops_api` (LOGIN), `ops_fn_owner` (NOLOGIN) with hardened flags and non-membership; the test_012 harness (DSN constant, CHAIN, `_clean_slate`, `apply_migrations`, `_admin()` connection helper) that ALL later test steps consume.

- [ ] **Step 1: Open the branch + move lane docs**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && test -z "$(git status --porcelain)" || { echo DIRTY_WORKTREE_STOP; git status --short; exit 1; }; git checkout main && git pull && git checkout -b ops/role-boundary-012 && mkdir -p docs/superpowers/plans docs/superpowers/specs/ops-app-role-boundary && cp /home/olares/code/ops-app-role-boundary/2026-07-01-ops-app-role-boundary-design-v3.md docs/superpowers/specs/ && cp /home/olares/code/ops-app-role-boundary/OPS_APP_ROLE_BOUNDARY_AUDIT_2026-07-01.md /home/olares/code/ops-app-role-boundary/DECISIONS_RATIFIED_2026-07-01.md /home/olares/code/ops-app-role-boundary/IRP_COMBINED_2026-07-01.md /home/olares/code/ops-app-role-boundary/IRP_OPUS_2026-07-01.md /home/olares/code/ops-app-role-boundary/IRP_REGATE_V2_2026-07-01.md docs/superpowers/specs/ops-app-role-boundary/ && cp /home/olares/code/ops-app-role-boundary/2026-07-01-ops-app-role-boundary-plan.md docs/superpowers/plans/2026-07-01-ops-app-role-boundary.md'
```
MED-2: the `test -z "$(git status --porcelain)" || { ...; exit 1; }` HARD-STOPS on a dirty worktree (single-writer rule) instead of proceeding into `git checkout main`. Expect a clean tree (`git checkout` + branch create + copies succeed); on `DIRTY_WORKTREE_STOP`, resolve before retrying.

- [ ] **Step 2: Write the failing test.** Create `infra/database/migrations/ops/test_012_ops_app_role_boundary.py`:

```python
# test_012_ops_app_role_boundary.py -- self-contained migration test (mirrors test_011's shape).
# Applies the FULL ladder 001..012 on ops_test, then proves the 012 posture: role flags,
# non-membership, PUBLIC hygiene, DEFINER/owner conversion, the column-scoped grant matrix,
# the boundary-denial proofs, H2, the FOR-UPDATE regressions, and reversibility.
#
# Denial proofs run via SET ROLE from the admin session: object-privilege checks use
# current_user, and superuser bypass is off after SET ROLE to a non-super role.
# NOTE: the SET ROLE *membership* denial itself cannot be proven from an admin session
# (SET ROLE permission is checked against session_user, which stays postgres); the
# real-login SET ROLE denial lives in packages/ops-intake/tests (writer/api DSNs).
# Here, non-membership is proven via pg_has_role.
import os, pathlib, uuid
import psycopg, pytest
from psycopg import errors
from psycopg.conninfo import conninfo_to_dict

HERE = pathlib.Path(__file__).resolve().parent

DSN = os.environ.get("OPS_DEV_ADMIN_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    "password={} sslmode=disable".format(
        os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
    )
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "012 migration tests run on ops_test ONLY"

CHAIN = [
    "001_identity_skeleton.sql",
    "002_quote_model.sql",
    "003_intake_unique_keys.sql",
    "004_person_anchor.sql",
    "005_recognition_ledger.sql",
    "006_progress_billing.sql",
    "007_intake_envelope.sql",
    "008_core_equipment_models.sql",
    "009_recognition_bridge.sql",
    "010_native_envelope_intake.sql",
    "011_scope_quote_line_description.sql",
    "012_ops_app_role_boundary.sql",
]
DOWN012 = HERE / "012_ops_app_role_boundary_down.sql"
UP012 = HERE / "012_ops_app_role_boundary.sql"
DOWN011 = HERE / "011_scope_quote_line_description_down.sql"
DOWN010 = HERE / "010_native_envelope_intake_down.sql"
DOWN009 = HERE / "009_recognition_bridge_down.sql"
DOWN008 = HERE / "008_core_equipment_models_down.sql"
DOWN001 = HERE / "001_identity_skeleton_down.sql"


def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))


def _admin(autocommit=True):
    return psycopg.connect(DSN, autocommit=autocommit)


def _ops_schema_exists(conn) -> bool:
    return conn.execute(
        "select 1 from pg_catalog.pg_namespace where nspname='ops'"
    ).fetchone() is not None


def _clean_slate():
    """Drop all ops + core schemas so migrations apply cleanly on any ops_test state.
    012_down is guarded (to_regprocedure / pg_roles checks) so it is safe to run even
    when 012 was never applied."""
    with _admin() as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # 010 down data-loss guard
            _exec(DOWN012)
            _exec(DOWN011)
            _exec(DOWN010)
            _exec(DOWN009)
        _exec(DOWN008)
    _exec(DOWN001)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with _admin() as c:
        row = c.execute("select current_database()").fetchone()
        assert row[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _clean_slate()
    for f in CHAIN:
        _exec(HERE / f)
    yield
    _clean_slate()


# ---------- Task 1: roles ----------

def test_012_roles_exist_with_hardened_flags():
    with _admin() as c:
        for role, canlogin in (
            ("ops_intake_writer", True),
            ("ops_api", True),
            ("ops_fn_owner", False),
        ):
            row = c.execute(
                "select rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls,"
                " rolreplication from pg_roles where rolname=%s",
                (role,),
            ).fetchone()
            assert row is not None, role + " missing"
            assert row[0] is canlogin, role + " login flag wrong"
            assert row[1:] == (False, False, False, False, False), role + " has a privileged flag"


def test_012_no_login_role_is_member_of_fn_owner():
    with _admin() as c:
        for role in ("ops_intake_writer", "ops_api"):
            assert c.execute(
                "select pg_has_role(%s, 'ops_fn_owner', 'member')", (role,)
            ).fetchone()[0] is False, role + " can reach ops_fn_owner"
        # No non-superuser login role at all may be a member (superusers pass every
        # membership check by definition, so they are excluded from the sweep).
        bad = c.execute(
            "select rolname from pg_roles"
            " where rolcanlogin and not rolsuper"
            "   and pg_has_role(rolname, 'ops_fn_owner', 'member')"
        ).fetchall()
        assert bad == [], "login role(s) are members of ops_fn_owner: " + repr(bad)
```

- [ ] **Step 3: Run to verify it fails correctly**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; export OPS_DEV_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd infra/database/migrations/ops && uv run --with "psycopg[binary]" --with pytest pytest test_012_ops_app_role_boundary.py -v'
```
(This is the canonical fully-expanded `<ENV>` form. Every later pytest command in this plan MUST run the same preamble - the `PATH` export (uv) and the `OPS_DEV_ADMIN_DSN` export are BOTH required; a bare `. ./infra/.env` without them fails with `uv: command not found` or a KeyError on the hard-required admin DSN.)
Expected: FAIL/ERROR - `FileNotFoundError` for EITHER 012 file (the DOWN file first when a leftover ops schema exists, because `_clean_slate` runs `012_ops_app_role_boundary_down.sql` before the chain reaches the up file; on a clean ops_test it is the up file the CHAIN references). NOT a pass.

- [ ] **Step 4: Write the migration section [1] and the down's role teardown.** Create `infra/database/migrations/ops/012_ops_app_role_boundary.sql`:

```sql
-- 012_ops_app_role_boundary.sql
-- The ops_app role boundary: D1=B two-role split (ops_intake_writer / ops_api) + dedicated
-- NOLOGIN SECURITY DEFINER owner (ops_fn_owner) + PUBLIC hygiene + column-scoped grant
-- matrix + H2 completion-guard tightening + in-migration posture asserts.
-- Spec: docs/superpowers/specs/2026-07-01-ops-app-role-boundary-design-v3.md
-- Roles are CLUSTER-level and this ladder runs on ops_test AND ops_dev on the same
-- cluster: creation is guarded, flags are corrected unconditionally (M3).
-- Passwords for the two LOGIN roles are set OUT-OF-BAND by the operator - never here.

-- [1] Roles + membership hardening (M3, M4/V3-1) -------------------------------------

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'ops_intake_writer') then
    create role ops_intake_writer;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'ops_api') then
    create role ops_api;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'ops_fn_owner') then
    create role ops_fn_owner;
  end if;
end $$;

alter role ops_intake_writer with login  nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role ops_api           with login  nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role ops_fn_owner      with nologin nosuperuser nocreatedb nocreaterole nobypassrls noreplication;

-- NOLOGIN alone does not stop a MEMBER from SET ROLE ops_fn_owner: revoke membership
-- explicitly. (Membership cannot be granted to PUBLIC in PostgreSQL, so the spec's
-- "FROM PUBLIC" is vacuously satisfied; the assert below enforces it durably.)
revoke ops_fn_owner from ops_intake_writer;
revoke ops_fn_owner from ops_api;

-- [1a] posture asserts: flags + non-membership (migration FAILS on drift)
do $$
declare
  r record;
  bad text;
begin
  for r in
    select rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls, rolreplication
    from pg_roles where rolname in ('ops_intake_writer', 'ops_api', 'ops_fn_owner')
  loop
    if r.rolsuper or r.rolcreatedb or r.rolcreaterole or r.rolbypassrls or r.rolreplication then
      raise exception '012 posture: % holds a privileged flag', r.rolname;
    end if;
    if r.rolname = 'ops_fn_owner' and r.rolcanlogin then
      raise exception '012 posture: ops_fn_owner must be NOLOGIN';
    end if;
    if r.rolname in ('ops_intake_writer', 'ops_api') and not r.rolcanlogin then
      raise exception '012 posture: % must be LOGIN', r.rolname;
    end if;
  end loop;
  if (select count(*) from pg_roles where rolname in ('ops_intake_writer','ops_api','ops_fn_owner')) <> 3 then
    raise exception '012 posture: expected all three roles present';
  end if;
  if pg_has_role('ops_intake_writer', 'ops_fn_owner', 'member')
     or pg_has_role('ops_api', 'ops_fn_owner', 'member') then
    raise exception '012 posture: a login app role is a member of ops_fn_owner';
  end if;
  select rolname into bad from pg_roles
   where rolcanlogin and not rolsuper
     and pg_has_role(rolname, 'ops_fn_owner', 'member')
   limit 1;
  if bad is not null then
    raise exception '012 posture: login role % is a member of ops_fn_owner', bad;
  end if;
end $$;
```

Create `infra/database/migrations/ops/012_ops_app_role_boundary_down.sql` (grows in later tasks; role teardown lands now, in the spec's mandated position - LAST):

```sql
-- 012_ops_app_role_boundary_down.sql
-- Restores the pre-012 (insecure) posture: ladder symmetry, NOT a security recommendation.
-- Ordered per spec S7: [d1] fn owner -> postgres + SECURITY INVOKER (added in Task 3);
-- [d2] restore the pre-012 completion guard (added in Task 5); [d3] DROP OWNED BY the
-- three roles; [d4] guarded DROP ROLE; [d5] restore PUBLIC EXECUTE + CONNECT.
-- Every step is guarded so this file is safe to run even when 012 was never applied
-- (test _clean_slate runs it unconditionally).

-- [d3] revoke everything granted TO the roles in THIS database
do $$
begin
  if exists (select 1 from pg_roles where rolname = 'ops_intake_writer') then
    drop owned by ops_intake_writer;
  end if;
  if exists (select 1 from pg_roles where rolname = 'ops_api') then
    drop owned by ops_api;
  end if;
  if exists (select 1 from pg_roles where rolname = 'ops_fn_owner') then
    drop owned by ops_fn_owner;
  end if;
end $$;

-- [d4] guarded/drop-if-safe role drop (DEV-7, operator-ratified). PRIMARY guard: never
-- drop a login role whose SCRAM password was set out-of-band (pg_authid.rolpassword IS NOT
-- NULL). Dropping it and letting the up-side recreate it password-less would break every
-- scram login (Tasks 9/10/12). SECONDARY guard (DEV-4): DROP ROLE also fails with
-- dependent_objects_still_exist if the role owns grants in ANOTHER database of this cluster.
-- Either way [d3] DROP OWNED already revoked THIS DB's grants, so posture is restored
-- whether or not the role object survives. ops_fn_owner (NOLOGIN, no password) drops cleanly.
-- Reading pg_authid requires superuser; the down runs as the admin identity.
do $$
declare r text;
begin
  foreach r in array array['ops_intake_writer', 'ops_api', 'ops_fn_owner'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      if exists (select 1 from pg_authid where rolname = r and rolpassword is not null) then
        raise notice '012_down: role % has an out-of-band password set; left in place (DEV-7)', r;
        continue;
      end if;
      begin
        execute format('drop role %I', r);
      exception when dependent_objects_still_exist then
        raise notice '012_down: role % retains dependencies in another database; left in place', r;
      end;
    end if;
  end loop;
end $$;

-- [d5] restore PUBLIC posture (pre-012): EXECUTE on all ops/core (+work) functions, CONNECT.
-- CREATE on schema public is NOT re-granted (PG15+ default lacks it; DEV-5).
do $$
begin
  if to_regnamespace('ops') is not null then
    execute 'grant execute on all routines in schema ops to public';
  end if;
  if to_regnamespace('core') is not null then
    execute 'grant execute on all routines in schema core to public';
  end if;
  if to_regnamespace('work') is not null then
    execute 'grant execute on all routines in schema work to public';
  end if;
  execute format('grant connect on database %I to public', current_database());
end $$;
```

- [ ] **Step 5: Run the test to verify it passes**

Same command as Step 3. Expected: both tests PASS. (The whole prior ladder applies too - if an earlier migration fails, STOP: the tree was not clean.)

- [ ] **Step 6: ASCII audit + commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && grep -nP "[^\x00-\x7F]" infra/database/migrations/ops/012_ops_app_role_boundary.sql infra/database/migrations/ops/012_ops_app_role_boundary_down.sql infra/database/migrations/ops/test_012_ops_app_role_boundary.py; echo "ascii-exit=$?"'
```
Expected: no matches, `ascii-exit=1` (grep exit 1 = clean).

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add docs/superpowers infra/database/migrations/ops/012_ops_app_role_boundary.sql infra/database/migrations/ops/012_ops_app_role_boundary_down.sql infra/database/migrations/ops/test_012_ops_app_role_boundary.py && git commit -m "feat(ops): 012 role boundary - roles + membership hardening (spec v3 S7.1)

Lane docs (spec v3, audit, decisions, IRP records, plan) move into docs/.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"'
```

---

### Task 2: PUBLIC hygiene (D5, C3, H1)

**Files:**
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (append section [2])
- Modify: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (append tests)

**Interfaces:** Consumes the roles from Task 1. Produces: PUBLIC has no CONNECT on the database, no EXECUTE on any ops/core function, no CREATE on schema public; login roles hold CONNECT; work.* (when present) is zero-granted.

- [ ] **Step 1: Write the failing tests.** Append to test_012:

```python
# ---------- Task 2: PUBLIC hygiene ----------

def test_012_public_has_no_execute_on_ops_core_functions():
    with _admin() as c:
        n = c.execute(
            "select count(*) from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace"
            " where ns.nspname in ('ops','core')"
            "   and (p.proacl is null"
            "        or exists (select 1 from aclexplode(p.proacl) a"
            "                   where a.grantee = 0 and a.privilege_type = 'EXECUTE'))"
        ).fetchone()[0]
        assert n == 0, str(n) + " ops/core function(s) retain PUBLIC EXECUTE"


def test_012_public_connect_revoked_and_login_roles_connect():
    with _admin() as c:
        row = c.execute(
            "select datacl is null, exists (select 1 from aclexplode(coalesce(datacl,'{}'::aclitem[])) a"
            " where a.grantee = 0 and a.privilege_type = 'CONNECT')"
            " from pg_database where datname = current_database()"
        ).fetchone()
        assert row[0] is False, "datacl is NULL (default ACL includes PUBLIC CONNECT)"
        assert row[1] is False, "PUBLIC retains CONNECT"
        for role in ("ops_intake_writer", "ops_api"):
            assert c.execute(
                "select has_database_privilege(%s, current_database(), 'CONNECT')", (role,)
            ).fetchone()[0] is True, role + " lost CONNECT"
        assert c.execute(
            "select has_database_privilege('postgres', current_database(), 'CONNECT')"
        ).fetchone()[0] is True


def test_012_public_create_on_schema_public_revoked():
    with _admin() as c:
        row = c.execute(
            "select exists (select 1 from pg_namespace n,"
            " aclexplode(coalesce(n.nspacl,'{}'::aclitem[])) a"
            " where n.nspname='public' and a.grantee = 0 and a.privilege_type='CREATE')"
        ).fetchone()
        assert row[0] is False, "PUBLIC retains CREATE on schema public"
```

- [ ] **Step 2: Run to verify the new tests fail** (same pytest command as Task 1 Step 3, add `-k "public"`). Expected: the PUBLIC-EXECUTE test FAILS (proacl NULL on all ops fns today) and the CONNECT test FAILS (datacl NULL).

- [ ] **Step 3: Append section [2] to 012** (after section [1a]):

```sql
-- [2] PUBLIC hygiene (D5, C3, H1) ------------------------------------------------------
-- H1: PUBLIC EXECUTE on functions is a hard-wired creation default that ALTER DEFAULT
-- PRIVILEGES cannot displace for already-existing functions: the explicit REVOKE below is
-- the load-bearing statement, and it MUST precede the DEFINER conversion in section [3].
-- CI convention: any future migration creating a function must re-run this REVOKE or
-- grant explicitly; the [2a] assert loop closes drift at every ladder apply.
-- L3: ALL ROUTINES (not ALL FUNCTIONS) so the revoke also covers procedures - the [2a]
-- assert sweeps every prokind, so ALL FUNCTIONS would false-fail the day a procedure lands.

revoke execute on all routines in schema ops from public;
revoke execute on all routines in schema core from public;

-- C3: current_database() is invalid in REVOKE grammar and a bare name would break the
-- one-ladder-two-DBs invariant -> dynamic SQL.
do $$
begin
  execute format('revoke connect on database %I from public', current_database());
  execute format('grant connect on database %I to ops_intake_writer, ops_api', current_database());
end $$;

revoke create on schema public from public;

-- D6/C1: work.* zero grants, presence-gated (work exists on ops_dev, absent on ops_test).
do $$
begin
  if to_regnamespace('work') is not null then
    execute 'revoke execute on all routines in schema work from public';
    execute 'revoke all on all tables in schema work from ops_intake_writer, ops_api, ops_fn_owner';
    execute 'revoke usage on schema work from ops_intake_writer, ops_api, ops_fn_owner';
  end if;
end $$;

-- [2a] posture asserts
do $$
declare n int;
begin
  select count(*) into n
  from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
  where ns.nspname in ('ops','core')
    and (p.proacl is null
         or exists (select 1 from aclexplode(p.proacl) a
                    where a.grantee = 0 and a.privilege_type = 'EXECUTE'));
  if n > 0 then
    raise exception '012 posture: % ops/core function(s) retain PUBLIC EXECUTE', n;
  end if;
  if exists (select 1 from pg_database where datname = current_database() and datacl is null) then
    raise exception '012 posture: datacl is NULL (default ACL includes PUBLIC CONNECT)';
  end if;
  if exists (select 1 from pg_database d, aclexplode(d.datacl) a
             where d.datname = current_database()
               and a.grantee = 0 and a.privilege_type = 'CONNECT') then
    raise exception '012 posture: PUBLIC retains CONNECT on %', current_database();
  end if;
  if not has_database_privilege('postgres', current_database(), 'CONNECT') then
    raise exception '012 posture: admin lost CONNECT';
  end if;
  if to_regnamespace('work') is not null then
    if exists (
      select 1
      from pg_class c join pg_namespace ns on ns.oid = c.relnamespace,
           lateral (values ('ops_intake_writer'), ('ops_api')) roles(r)
      where ns.nspname = 'work' and c.relkind in ('r','v','m','p')
        and (has_table_privilege(roles.r, c.oid, 'SELECT')
          or has_table_privilege(roles.r, c.oid, 'INSERT')
          or has_table_privilege(roles.r, c.oid, 'UPDATE')
          or has_table_privilege(roles.r, c.oid, 'DELETE'))
    ) then
      raise exception '012 posture: a login role holds a work.* privilege';
    end if;
  end if;
end $$;
```

- [ ] **Step 4: Run the full test_012 file - verify all tests pass.**
- [ ] **Step 5: ASCII audit (same grep as Task 1 Step 6) + commit**

```bash
git add infra/database/migrations/ops/012_ops_app_role_boundary.sql infra/database/migrations/ops/test_012_ops_app_role_boundary.py
git commit -m "feat(ops): 012 PUBLIC hygiene - EXECUTE/CONNECT/CREATE revokes, work zero-grant (S7.2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: SECURITY DEFINER conversion + dedicated owner + owner object grants

**Files:**
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (append section [3])
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary_down.sql` (prepend section [d1])
- Modify: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (append tests)

**Interfaces:** Consumes roles (Task 1) + PUBLIC revokes (Task 2). Produces: the 9 fns SECURITY DEFINER, `search_path=ops, pg_temp`, owned by ops_fn_owner; ops_fn_owner holding exactly the S5 owner grant set. The signature array `SIGS` defined here is reused by the down and by test_012.

- [ ] **Step 1: Write the failing tests.** Append to test_012:

```python
# ---------- Task 3: DEFINER conversion + owner ----------

SIGS = [
    "ops.attest_apparatus_complete(uuid,uuid,text)",
    "ops.revoke_completion_attestation(uuid,uuid,text)",
    "ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)",
    "ops.reverse_recognition(uuid,uuid,text)",
    "ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)",
    "ops.issue_billing_application(uuid,uuid,text)",
    "ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)",
    "ops.discard_draft_billing_application(uuid,uuid)",
    "ops.void_billing_application(uuid,uuid,text)",
]


def test_012_nine_fns_definer_owned_searchpath():
    with _admin() as c:
        for sig in SIGS:
            row = c.execute(
                "select p.prosecdef, p.proowner::regrole::text, p.proconfig"
                " from pg_proc p where p.oid = to_regprocedure(%s)",
                (sig,),
            ).fetchone()
            assert row is not None, sig + " missing"
            assert row[0] is True, sig + " is not SECURITY DEFINER"
            assert row[1] == "ops_fn_owner", sig + " owner is " + row[1]
            assert row[2] is not None and any(
                x.startswith("search_path=") and "ops" in x and "pg_temp" in x for x in row[2]
            ), sig + " search_path not pinned to ops, pg_temp"


def test_012_owner_grants_cover_fn_read_and_lock_surface():
    with _admin() as c:
        # SELECT surface (RV-1: the owner needs SELECT on every table its fn bodies read/join)
        for t in ("apparatus", "scopes", "completion_attestation", "revenue_recognition_event",
                  "scope_quote", "projects", "persons",
                  "billing_application", "billing_application_line", "billing_application_draft"):
            assert c.execute(
                "select has_table_privilege('ops_fn_owner', %s, 'SELECT')", ("ops." + t,)
            ).fetchone()[0] is True, "ops_fn_owner missing SELECT on ops." + t
        # write/lock surface
        for t, priv in (
            ("apparatus", "UPDATE"),
            ("completion_attestation", "INSERT"), ("completion_attestation", "UPDATE"),
            ("revenue_recognition_event", "INSERT"), ("revenue_recognition_event", "UPDATE"),
            ("projects", "UPDATE"),
            ("billing_application", "INSERT"), ("billing_application", "UPDATE"), ("billing_application", "DELETE"),
            ("billing_application_line", "INSERT"), ("billing_application_line", "UPDATE"), ("billing_application_line", "DELETE"),
            ("billing_application_draft", "INSERT"), ("billing_application_draft", "UPDATE"), ("billing_application_draft", "DELETE"),
        ):
            assert c.execute(
                "select has_table_privilege('ops_fn_owner', %s, %s)", ("ops." + t, priv)
            ).fetchone()[0] is True, "ops_fn_owner missing " + priv + " on ops." + t
        assert c.execute(
            "select has_schema_privilege('ops_fn_owner', 'ops', 'USAGE')"
        ).fetchone()[0] is True
```

- [ ] **Step 2: Run to verify the new tests fail** (`-k "definer or owner_grants"`). Expected: prosecdef False / owner postgres.

- [ ] **Step 3: Append section [3] to 012:**

```sql
-- [3] SECURITY DEFINER conversion + dedicated owner (D3, M4) + owner grants (S5) --------
-- Exact signatures grounded from pg_proc. The loop FAILS LOUD if any signature drifted.

do $$
declare
  sig text;
  sigs text[] := array[
    'ops.attest_apparatus_complete(uuid,uuid,text)',
    'ops.revoke_completion_attestation(uuid,uuid,text)',
    'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
    'ops.reverse_recognition(uuid,uuid,text)',
    'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
    'ops.issue_billing_application(uuid,uuid,text)',
    'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
    'ops.discard_draft_billing_application(uuid,uuid)',
    'ops.void_billing_application(uuid,uuid,text)'
  ];
begin
  foreach sig in array sigs loop
    if to_regprocedure(sig) is null then
      raise exception '012: expected function % is missing - signature drift', sig;
    end if;
    execute format('alter function %s security definer set search_path = ops, pg_temp', sig);
    execute format('alter function %s owner to ops_fn_owner', sig);
  end loop;
end $$;

-- Owner object grants: ONLY what the 9 fn bodies need (S5; read-surface verified against
-- live pg_get_functiondef 2026-07-01 - no core.* reads, so no core USAGE for the owner).
grant usage on schema ops to ops_fn_owner;

-- RV-1: SELECT on every table the fn bodies read/join. scopes is REQUIRED (attest,
-- approve_and_recognize, and the revrec insert-integrity trigger all join ops.scopes).
grant select on ops.apparatus, ops.scopes, ops.completion_attestation,
  ops.revenue_recognition_event, ops.scope_quote, ops.projects, ops.persons
  to ops_fn_owner;

-- Write/lock surface. Table-level UPDATE is acceptable HERE ONLY: NOLOGIN + fn-gated +
-- non-membered; the append-only/integrity triggers still bar real ledger mutation.
grant update on ops.apparatus to ops_fn_owner;                       -- status writes + recognition FOR UPDATE
grant insert, update on ops.completion_attestation to ops_fn_owner;
grant insert, update on ops.revenue_recognition_event to ops_fn_owner;  -- UPDATE solely for reverse_recognition's FOR UPDATE
grant update on ops.projects to ops_fn_owner;                        -- solely for billing project FOR UPDATE locks
grant select, insert, update, delete on ops.billing_application,
  ops.billing_application_line, ops.billing_application_draft to ops_fn_owner;

-- [3a] posture asserts
do $$
begin
  if exists (
    select 1 from unnest(array[
      'ops.attest_apparatus_complete(uuid,uuid,text)',
      'ops.revoke_completion_attestation(uuid,uuid,text)',
      'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
      'ops.reverse_recognition(uuid,uuid,text)',
      'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.issue_billing_application(uuid,uuid,text)',
      'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.discard_draft_billing_application(uuid,uuid)',
      'ops.void_billing_application(uuid,uuid,text)'
    ]) s(sig)
    join pg_proc p on p.oid = to_regprocedure(s.sig)
    where not p.prosecdef or p.proowner <> 'ops_fn_owner'::regrole
  ) then
    raise exception '012 posture: a mutation fn is not DEFINER-owned by ops_fn_owner';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.scopes', 'SELECT') then
    raise exception '012 posture: ops_fn_owner missing SELECT on ops.scopes (RV-1)';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.revenue_recognition_event', 'UPDATE')
     or not has_table_privilege('ops_fn_owner', 'ops.projects', 'UPDATE') then
    raise exception '012 posture: ops_fn_owner missing a FOR UPDATE lock grant';
  end if;
  if not has_table_privilege('ops_fn_owner', 'ops.billing_application', 'SELECT') then
    raise exception '012 posture: ops_fn_owner missing billing SELECT (RV-2)';
  end if;
end $$;
```

- [ ] **Step 4: Prepend section [d1] to 012_down** (BEFORE [d3] - the file's first statement block, per spec order: fn owner reversal FIRST):

```sql
-- [d1] revert the 9 fns: owner -> postgres, SECURITY INVOKER, unpin search_path.
-- Guarded per-signature so a partially-applied ladder is safe.
do $$
declare
  sig text;
  sigs text[] := array[
    'ops.attest_apparatus_complete(uuid,uuid,text)',
    'ops.revoke_completion_attestation(uuid,uuid,text)',
    'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
    'ops.reverse_recognition(uuid,uuid,text)',
    'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
    'ops.issue_billing_application(uuid,uuid,text)',
    'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
    'ops.discard_draft_billing_application(uuid,uuid)',
    'ops.void_billing_application(uuid,uuid,text)'
  ];
begin
  foreach sig in array sigs loop
    if to_regprocedure(sig) is not null then
      execute format('alter function %s owner to postgres', sig);
      execute format('alter function %s security invoker', sig);
      execute format('alter function %s reset search_path', sig);
    end if;
  end loop;
end $$;
```

- [ ] **Step 5: Run the full test_012 file - all tests pass.**
- [ ] **Step 6: ASCII audit + commit** (`feat(ops): 012 DEFINER conversion + dedicated NOLOGIN owner + owner grants (S6, S7.3)` with the trailer).

---

### Task 4: Login-role grant matrix + EXECUTE + boundary-denial proofs (SET ROLE tier) + FOR-UPDATE regressions

**Files:**
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (append sections [4] and [5])
- Modify: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (append tests)

**Interfaces:** Consumes Tasks 1-3. Produces the FINAL login-role privilege surface. The seed helper `_seed_min(c)` defined here (project -> scope -> scope_quote -> apparatus, admin DML) is reused by Task 5.

- [ ] **Step 1: Write the failing tests.** Append to test_012:

```python
# ---------- Task 4: grant matrix + denial proofs ----------

PROJECTS_UPDATE_COLS = [
    "project_name", "status", "quote_revision", "contract_value", "description",
    "source_client_name", "source_site_name", "source_site_address", "source_site_city",
    "source_site_state", "source_site_zip", "source", "provenance_status", "updated_at",
]

APPARATUS_INSERT_COLS = [  # the 11 load.py columns, EXCLUDING status (D2)
    "scope_id", "task_id", "apparatus_designation", "apparatus_type", "equipment_model_ref",
    "drawing_reference", "quoted_hours", "quote_line_id", "source", "legacy_source_id",
    "provenance_status",
]

OPS_VIEWS = [
    "v_apparatus_quote", "v_apparatus_recognition", "v_billing_application_sov",
    "v_completion_recognition_rollup", "v_completion_recognition_worklist", "v_draft_preview",
    "v_project_billing", "v_project_recognition", "v_recognition_review_queue",
    "v_scope_recognition", "v_unbilled_recognition",
]


def _seed_min(c, project_number=None):
    """Admin setup DML: minimal project -> scope -> scope_quote -> apparatus('In Progress').
    Mirrors the eligible fixture in test_ops_recognition_routes.py."""
    pn = project_number or ("T012-" + uuid.uuid4().hex[:8])
    with c.cursor() as cur:
        cur.execute(
            "insert into ops.projects (project_number,project_name,status,provenance_status)"
            " values (%s,'P','Active','approved') returning id", (pn,))
        pid = cur.fetchone()[0]
        cur.execute(
            "insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
            " values (%s,'S','In Progress','approved','ops-intake') returning id", (pid,))
        sid = cur.fetchone()[0]
        cur.execute(
            "insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
            "total_quoted_hours,is_frozen,frozen_at) values (%s,1500,1,1,10,true,now())", (sid,))
        cur.execute(
            "insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
            "quoted_hours,quoted_revenue,source) values (%s,'A','In Progress','approved',10,1500,'ops-intake')"
            " returning id", (sid,))
        aid = cur.fetchone()[0]
    return pid, sid, aid


def _denied(sql, role, params=None, pre_sql=None):
    """Run sql AS role (SET ROLE from the admin session) inside a rolled-back txn;
    assert InsufficientPrivilege. Object-privilege checks use current_user, and
    superuser bypass is OFF after SET ROLE to a non-super role."""
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role " + role)
            if pre_sql:
                cur.execute(pre_sql)
            with pytest.raises(errors.InsufficientPrivilege):
                cur.execute(sql, params)
        c.rollback()


def test_012_writer_positive_matrix():
    with _admin() as c:
        for col in PROJECTS_UPDATE_COLS:
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.projects',%s,'UPDATE')", (col,)
            ).fetchone()[0] is True, "writer missing projects UPDATE(" + col + ")"
        for col in APPARATUS_INSERT_COLS:
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.apparatus',%s,'INSERT')", (col,)
            ).fetchone()[0] is True, "writer missing apparatus INSERT(" + col + ")"
        for col in ("quoted_revenue", "provenance_status", "updated_at"):
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.apparatus',%s,'UPDATE')", (col,)
            ).fetchone()[0] is True, "writer missing apparatus UPDATE(" + col + ")"
        for t, p in (("intake_runs", "INSERT"), ("intake_runs", "UPDATE"), ("intake_runs", "SELECT"),
                     ("intake_source_files", "INSERT"), ("intake_validation_findings", "INSERT"),
                     ("scopes", "INSERT"), ("scopes", "DELETE"), ("scope_quote", "INSERT"),
                     ("scope_quote_line", "INSERT"), ("tasks", "INSERT"), ("tasks", "UPDATE"),
                     ("revenue_recognition_event", "SELECT"), ("billing_application", "SELECT")):
            assert c.execute(
                "select has_table_privilege('ops_intake_writer', %s, %s)", ("ops." + t, p)
            ).fetchone()[0] is True, "writer missing " + p + " on ops." + t
        for col in ("total_quoted_hours", "is_frozen", "frozen_at"):
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.scope_quote',%s,'UPDATE')", (col,)
            ).fetchone()[0] is True
        for v in OPS_VIEWS:
            assert c.execute(
                "select has_table_privilege('ops_intake_writer', %s, 'SELECT')", ("ops." + v,)
            ).fetchone()[0] is True, "writer missing SELECT on ops." + v
        for t in ("core.v_equipment_models_resolved", "core.equipment_models"):
            assert c.execute(
                "select has_table_privilege('ops_intake_writer', %s, 'SELECT')", (t,)
            ).fetchone()[0] is True


def test_012_negative_matrix_the_boundary():
    with _admin() as c:
        # D2: no status privilege anywhere on a login role
        for role in ("ops_intake_writer", "ops_api"):
            for priv in ("INSERT", "UPDATE"):
                assert c.execute(
                    "select has_column_privilege(%s,'ops.apparatus','status',%s)", (role, priv)
                ).fetchone()[0] is False, role + " holds apparatus.status " + priv
        # writer: no source/scope_id UPDATE on apparatus, no DELETE on apparatus
        for col in ("source", "scope_id"):
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.apparatus',%s,'UPDATE')", (col,)
            ).fetchone()[0] is False
        # forge-closure: api has NO table DML; writer has NO ledger/attestation/billing DML
        for t in ("apparatus", "scopes", "projects", "intake_runs"):
            for p in ("INSERT", "UPDATE", "DELETE"):
                assert c.execute(
                    "select has_table_privilege('ops_api', %s, %s)", ("ops." + t, p)
                ).fetchone()[0] is False, "ops_api holds " + p + " on ops." + t
        for role in ("ops_intake_writer", "ops_api"):
            for t in ("revenue_recognition_event", "completion_attestation",
                      "billing_application", "billing_application_line", "billing_application_draft"):
                for p in ("INSERT", "UPDATE", "DELETE"):
                    assert c.execute(
                        "select has_table_privilege(%s, %s, %s)", (role, "ops." + t, p)
                    ).fetchone()[0] is False, role + " holds " + p + " on ops." + t
            for t in ("projects", "apparatus", "tasks", "scope_quote", "scope_quote_line"):
                assert c.execute(
                    "select has_table_privilege(%s, %s, 'DELETE')", (role, "ops." + t)
                ).fetchone()[0] is False, role + " holds DELETE on ops." + t
        # writer: no EXECUTE on any of the 9; api: EXECUTE on exactly the 4 recognition fns
        for sig in SIGS:
            assert c.execute(
                "select has_function_privilege('ops_intake_writer', to_regprocedure(%s), 'EXECUTE')", (sig,)
            ).fetchone()[0] is False, "writer can EXECUTE " + sig
        for sig in SIGS[:4]:
            assert c.execute(
                "select has_function_privilege('ops_api', to_regprocedure(%s), 'EXECUTE')", (sig,)
            ).fetchone()[0] is True, "api missing EXECUTE on " + sig
        for sig in SIGS[4:]:
            assert c.execute(
                "select has_function_privilege('ops_api', to_regprocedure(%s), 'EXECUTE')", (sig,)
            ).fetchone()[0] is False, "api can EXECUTE deferred billing fn " + sig


def test_012_denial_a_forged_complete_insert():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    # M6: every column here EXCEPT status is in the writer's 11-column INSERT grant, so
    # `status` is the SOLE unauthorized column - the denial proves the D2 boundary itself,
    # not an incidental grant gap (quoted_revenue was masking it: it is UPDATE-only).
    forged = ("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,source)"
              " values (%s,'F','Complete','approved','ops-intake')")
    _denied(forged, "ops_intake_writer", params=(sid,))
    # MANDATORY (D2): STILL denied after SET ops.completion_ctx='1' (the column-privilege
    # check fires BEFORE the completion guard, so the GUC cannot help).
    _denied(forged, "ops_intake_writer", params=(sid,), pre_sql="set local ops.completion_ctx='1'")


def test_012_denial_b_writer_status_update():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    _denied("update ops.apparatus set status='Complete' where id=%s", "ops_intake_writer", params=(aid,))


def test_012_denial_c_writer_cannot_execute_recognition():
    x = str(uuid.uuid4())
    _denied("select ops.attest_apparatus_complete(%s::uuid,%s::uuid,'x')", "ops_intake_writer", params=(x, x))
    _denied(
        "select ops.approve_and_recognize(%s::uuid,%s::uuid,"
        "'not_applicable'::ops.obligation_clearance,null,'not_applicable'::ops.obligation_clearance,null)",
        "ops_intake_writer", params=(x, x))


def test_012_denial_d_api_cannot_fabricate():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    _denied("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
            " values (%s,'F','In Progress','approved','ops-intake')", "ops_api", params=(pid,))
    _denied("insert into ops.apparatus (scope_id,apparatus_designation) values (%s,'F')",
            "ops_api", params=(sid,))


def test_012_denial_f_ledger_inserts():
    x = str(uuid.uuid4())
    for role in ("ops_intake_writer", "ops_api"):
        _denied("insert into ops.revenue_recognition_event (apparatus_id) values (%s::uuid)",
                role, params=(x,))
        _denied("insert into ops.completion_attestation (apparatus_id) values (%s::uuid)",
                role, params=(x,))
        _denied("insert into ops.billing_application (project_id) values (%s::uuid)",
                role, params=(x,), pre_sql="set local ops.billing_ctx='1'")


def test_012_denial_g_delete_projects():
    _denied("delete from ops.projects", "ops_intake_writer")
    _denied("delete from ops.projects", "ops_api")


def test_012_for_update_probe_regression():
    """Task 0 probe as a permanent regression: column-scoped UPDATE satisfies the
    approve.py:237 apparatus lock and the approve.py:233 projects lock as the writer."""
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_intake_writer")
            cur.execute(
                "select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                " where s.project_id = %s for update of a", (pid,))
            assert cur.fetchone() is not None
            cur.execute("select id from ops.projects where id = %s for update", (pid,))
            assert cur.fetchone() is not None
        c.rollback()


def test_012_for_update_two_session_concurrency():
    """Two-session interleave: writer A holds the apparatus row lock; writer B's NOWAIT
    lock attempt fails loud (proves the lock is really taken under column-scoped grants)."""
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    a = psycopg.connect(DSN, autocommit=False)
    b = psycopg.connect(DSN, autocommit=False)
    try:
        with a.cursor() as ca:
            ca.execute("set local role ops_intake_writer")
            ca.execute(
                "select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                " where s.project_id = %s for update of a", (pid,))
            assert ca.fetchone() is not None
            with b.cursor() as cb:
                cb.execute("set local role ops_intake_writer")
                with pytest.raises(errors.LockNotAvailable):
                    cb.execute(
                        "select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                        " where s.project_id = %s for update of a nowait", (pid,))
            b.rollback()
        a.rollback()
    finally:
        a.close()
        b.close()
```

NOTE on denial (f): the ledger/attestation/billing INSERT statements name only one column - the privilege check fires BEFORE NOT NULL/FK validation, so InsufficientPrivilege is raised first. If a different error arrives, the boundary is broken - investigate, do not loosen the test.
NOTE on denial (g) for work.*: ops_test has no work schema (presence-gated) - the work-write denial is covered by the [2a] in-migration assert on ops_dev; no test here.

- [ ] **Step 2: Run to verify the new tests fail** (`-k "matrix or denial or for_update"`). Expected failure shape: `test_012_writer_positive_matrix` and both FOR-UPDATE regression tests FAIL (no grants exist yet - even USAGE on schema ops is absent, so the probes raise InsufficientPrivilege on the schema). The denial tests may pass trivially at this point (with zero grants, everything is denied); that is fine - the RED gate for this task is the positive matrix + probe regressions failing first, and the denial tests earn their keep by staying green after the grants land.

- [ ] **Step 3: Append sections [4] and [5] to 012:**

```sql
-- [4] USAGE + EXECUTE (D3) --------------------------------------------------------------

grant usage on schema ops to ops_intake_writer;
grant usage on schema core to ops_intake_writer;
grant usage on schema ops to ops_api;

grant execute on function
  ops.attest_apparatus_complete(uuid,uuid,text),
  ops.revoke_completion_attestation(uuid,uuid,text),
  ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text),
  ops.reverse_recognition(uuid,uuid,text)
  to ops_api;
-- Billing EXECUTE deferred (GATE-12): the 5 billing fns get NO EXECUTE grant here.

-- [5] Login-role grant matrix (S5; FINAL per Task 0 PASS) --------------------------------

-- ops_intake_writer: intake surface
grant insert, update, select on ops.intake_runs to ops_intake_writer;
grant insert, select on ops.intake_source_files to ops_intake_writer;
grant insert, select on ops.intake_validation_findings to ops_intake_writer;

-- projects: column-scoped INSERT (load.py upsert_project) + column-scoped UPDATE
-- (upsert DO-UPDATE cols + approve.py _freeze provenance stamp). NOT retainage_pct /
-- lifecycle / is_active; NO DELETE.
grant insert (project_number, project_name, status, quote_revision, contract_value,
  description, source_client_name, source_site_name, source_site_address, source_site_city,
  source_site_state, source_site_zip, source, legacy_source_id, provenance_status),
  update (project_name, status, quote_revision, contract_value, description,
  source_client_name, source_site_name, source_site_address, source_site_city,
  source_site_state, source_site_zip, source, provenance_status, updated_at),
  select on ops.projects to ops_intake_writer;

-- scopes: DELETE = sanctioned full-replacement; RI cascade runs as table owner.
grant insert, delete, select on ops.scopes to ops_intake_writer;
grant insert, select, update (total_quoted_hours, is_frozen, frozen_at)
  on ops.scope_quote to ops_intake_writer;
grant insert, select on ops.scope_quote_line to ops_intake_writer;
grant insert, update, select on ops.tasks to ops_intake_writer;

-- apparatus (D2): INSERT on the 11 load.py columns EXCLUDING status; UPDATE on exactly
-- the approve.py _freeze columns. NO status, NO source/scope_id UPDATE, NO DELETE.
grant insert (scope_id, task_id, apparatus_designation, apparatus_type, equipment_model_ref,
  drawing_reference, quoted_hours, quote_line_id, source, legacy_source_id, provenance_status),
  select,
  update (quoted_revenue, provenance_status, updated_at)
  on ops.apparatus to ops_intake_writer;

-- read-only conflict checks
grant select on ops.revenue_recognition_event to ops_intake_writer;
grant select on ops.billing_application to ops_intake_writer;

-- catalog resolve
grant select on core.v_equipment_models_resolved to ops_intake_writer;
grant select on core.equipment_models to ops_intake_writer;

-- the 11 ops views (postgres-owned, non-security_invoker - asserted in [5a])
grant select on ops.v_apparatus_quote, ops.v_apparatus_recognition,
  ops.v_billing_application_sov, ops.v_completion_recognition_rollup,
  ops.v_completion_recognition_worklist, ops.v_draft_preview, ops.v_project_billing,
  ops.v_project_recognition, ops.v_recognition_review_queue, ops.v_scope_recognition,
  ops.v_unbilled_recognition to ops_intake_writer;

-- ops_api: recognition read surface only
grant select on ops.v_completion_recognition_worklist, ops.v_completion_recognition_rollup
  to ops_api;

-- [5a] posture asserts: the boundary, positively and negatively
do $$
declare
  col text;
  r text;
  t text;
  p text;
  n int;
begin
  -- positive: writer intake INSERT + the pinned projects UPDATE columns (V3-9)
  if not has_table_privilege('ops_intake_writer', 'ops.intake_runs', 'INSERT') then
    raise exception '012 posture: writer missing INSERT on intake_runs';
  end if;
  if not has_column_privilege('ops_intake_writer', 'ops.apparatus', 'quoted_revenue', 'UPDATE') then
    raise exception '012 posture: writer missing apparatus UPDATE(quoted_revenue)';
  end if;
  foreach col in array array['project_name','status','quote_revision','contract_value',
    'description','source_client_name','source_site_name','source_site_address',
    'source_site_city','source_site_state','source_site_zip','source','provenance_status',
    'updated_at'] loop
    if not has_column_privilege('ops_intake_writer', 'ops.projects', col, 'UPDATE') then
      raise exception '012 posture: writer missing projects UPDATE(%)', col;
    end if;
  end loop;
  -- negative: D2 - status leaves every login role (H3: has_column_privilege for column scope)
  foreach r in array array['ops_intake_writer', 'ops_api'] loop
    if has_column_privilege(r, 'ops.apparatus', 'status', 'INSERT')
       or has_column_privilege(r, 'ops.apparatus', 'status', 'UPDATE') then
      raise exception '012 posture: % holds apparatus.status privilege', r;
    end if;
    foreach t in array array['ops.revenue_recognition_event', 'ops.completion_attestation',
      'ops.billing_application', 'ops.billing_application_line', 'ops.billing_application_draft'] loop
      foreach p in array array['INSERT', 'UPDATE', 'DELETE'] loop
        if has_table_privilege(r, t, p) then
          raise exception '012 posture: % holds % on %', r, p, t;
        end if;
      end loop;
    end loop;
    if has_table_privilege(r, 'ops.projects', 'DELETE')
       or has_table_privilege(r, 'ops.apparatus', 'DELETE')
       or has_table_privilege(r, 'ops.tasks', 'DELETE')
       or has_table_privilege(r, 'ops.scope_quote', 'DELETE')
       or has_table_privilege(r, 'ops.scope_quote_line', 'DELETE') then
      raise exception '012 posture: % holds a forbidden DELETE', r;
    end if;
  end loop;
  if has_table_privilege('ops_api', 'ops.apparatus', 'INSERT')
     or has_table_privilege('ops_api', 'ops.scopes', 'INSERT') then
    raise exception '012 posture: ops_api can fabricate (INSERT on apparatus/scopes)';
  end if;
  -- writer must NOT execute any of the 9; api must execute EXACTLY the 4 recognition fns
  if exists (
    select 1 from unnest(array[
      'ops.attest_apparatus_complete(uuid,uuid,text)',
      'ops.revoke_completion_attestation(uuid,uuid,text)',
      'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
      'ops.reverse_recognition(uuid,uuid,text)',
      'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.issue_billing_application(uuid,uuid,text)',
      'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.discard_draft_billing_application(uuid,uuid)',
      'ops.void_billing_application(uuid,uuid,text)'
    ]) s(sig)
    where has_function_privilege('ops_intake_writer', to_regprocedure(s.sig), 'EXECUTE')
  ) then
    raise exception '012 posture: ops_intake_writer can EXECUTE a mutation fn';
  end if;
  if exists (
    select 1 from unnest(array[
      'ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.issue_billing_application(uuid,uuid,text)',
      'ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)',
      'ops.discard_draft_billing_application(uuid,uuid)',
      'ops.void_billing_application(uuid,uuid,text)'
    ]) s(sig)
    where has_function_privilege('ops_api', to_regprocedure(s.sig), 'EXECUTE')
  ) then
    raise exception '012 posture: ops_api can EXECUTE a deferred billing fn';
  end if;
  -- M2 (S7.7 positive): ops_api MUST hold EXECUTE on the 4 recognition fns. This is the
  -- ONLY guard on ops_dev/prod applies (pytest does not run there); a dropped GRANT EXECUTE
  -- fails LOUD here instead of silently breaking the recognition API.
  if exists (
    select 1 from unnest(array[
      'ops.attest_apparatus_complete(uuid,uuid,text)',
      'ops.revoke_completion_attestation(uuid,uuid,text)',
      'ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)',
      'ops.reverse_recognition(uuid,uuid,text)'
    ]) s(sig)
    where not has_function_privilege('ops_api', to_regprocedure(s.sig), 'EXECUTE')
  ) then
    raise exception '012 posture: ops_api is MISSING EXECUTE on a recognition fn';
  end if;
  -- R2: the 11 ops views are postgres-owned and NOT security_invoker
  select count(*) into n
  from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
  where ns.nspname = 'ops' and c.relkind = 'v';
  if n <> 11 then
    raise exception '012 posture: expected 11 ops views, found % (view drift - re-ground R2)', n;
  end if;
  if exists (
    select 1
    from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
    where ns.nspname = 'ops' and c.relkind = 'v'
      and (c.relowner <> 'postgres'::regrole
        or exists (select 1 from pg_options_to_table(c.reloptions) o
                   where o.option_name = 'security_invoker'
                     and lower(o.option_value) in ('true', 'on', '1')))
  ) then
    raise exception '012 posture: an ops view is not postgres-owned/non-invoker (R2)';
  end if;
end $$;
```

- [ ] **Step 4: Run the full test_012 file - all tests pass** (positive matrix, negative matrix, denials a/b/c/d/f/g, both FOR-UPDATE regressions).
- [ ] **Step 5: ASCII audit + commit** (`feat(ops): 012 login-role grant matrix + EXECUTE + denial proofs + FOR UPDATE regressions (S5, S7.4-5)` with the trailer).

---

### Task 5: H2 completion-guard tightening

**Files:**
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (append section [6])
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary_down.sql` (insert section [d2] AFTER [d1], BEFORE [d3])
- Modify: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (append tests)

**Interfaces:** Consumes `_seed_min` (Task 4). Produces the tightened guard: provenance change on a status='Complete' row raises REGARDLESS of ops.completion_ctx.

- [ ] **Step 1: Write the failing tests.** Append to test_012:

```python
# ---------- Task 5: H2 guard ----------

def _force_complete(aid):
    """Admin setup: flip an apparatus to Complete via the sanctioned ctx (setup DML tier).
    Uses its OWN autocommit=False connection so `set local` is inside a real transaction
    (on an autocommit connection SET LOCAL is inert); commit persists status='Complete'."""
    with _admin(autocommit=False) as c, c.cursor() as cur:
        cur.execute("set local ops.completion_ctx='1'")
        cur.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
        c.commit()


def test_012_h2_provenance_frozen_on_complete_regardless_of_guc():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    _force_complete(aid)
    upd = "update ops.apparatus set provenance_status='draft', updated_at=now() where id=%s"
    # proof (e): denied by the H2 guard even though the writer HOLDS the column privilege,
    # and even with the ctx GUC set. RaiseException (the guard), not InsufficientPrivilege.
    for pre in (None, "set local ops.completion_ctx='1'"):
        with _admin(autocommit=False) as c:
            with c.cursor() as cur:
                cur.execute("set local role ops_intake_writer")
                if pre:
                    cur.execute(pre)
                with pytest.raises(errors.RaiseException) as ei:
                    cur.execute(upd, (aid,))
                assert "provenance_status may not change while status" in str(ei.value)
            c.rollback()


def test_012_h2_breaks_no_sanctioned_path():
    """Writer provenance UPDATE on a NON-Complete row still works (the approve path),
    and attest/revoke (status-only writes) still work through the DEFINER fns."""
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
        with c.cursor() as cur:
            cur.execute("insert into ops.persons (display_name) values ('PM') returning person_id")
            who = cur.fetchone()[0]
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_intake_writer")
            cur.execute(
                "update ops.apparatus set provenance_status='approved', updated_at=now() where id=%s",
                (aid,))
        c.commit()
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_api")
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'ok')", (aid, who))
            att = cur.fetchone()[0]
            cur.execute("select ops.revoke_completion_attestation(%s,%s,'undo')", (att, who))
        c.commit()
```

- [ ] **Step 2: Run to verify failure** (`-k "h2"`). Expected: `test_012_h2_provenance_frozen...` FAILS - the writer's provenance UPDATE on the Complete row currently raises NOTHING when the ctx GUC is set (the old guard only fires on governed-complete transitions), or fails only in the no-GUC leg with the OLD guard message `governed-complete may change only via attest/revoke` (old_g flips because provenance leaves 'approved'). Either way the asserted H2 message is absent -> FAIL.

- [ ] **Step 3: Append section [6] to 012** (the grounded 009:53-69 body + the H2 clause):

```sql
-- [6] H2: completion-guard tightening (required) -----------------------------------------
-- Replaces the 009 guard. NEW: provenance_status may not change while status='Complete',
-- REGARDLESS of ops.completion_ctx - this makes "the ctx GUC is inert to login roles" true
-- by construction (D4). Grounded: no DEFINER fn legitimately changes provenance while
-- status='Complete' (approve stamps provenance at status='Not Started'; attest/revoke
-- change status, not provenance); recognized-then-reapprove is blocked earlier by the
-- _conflict_kind frozen gate. The trigger itself (009:70-71) is untouched.
create or replace function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $$
declare
  new_g boolean := (new.status='Complete' and new.provenance_status='approved');
  old_g boolean;
begin
  if tg_op = 'INSERT' then
    if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
    end if;
  else  -- UPDATE
    -- H2 (012): ctx-independent.
    if old.status = 'Complete' and new.provenance_status is distinct from old.provenance_status then
      raise exception 'apparatus %: provenance_status may not change while status=Complete', new.id;
    end if;
    old_g := (old.status='Complete' and old.provenance_status='approved');
    if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
    end if;
  end if;
  return new;
end; $$;
```

- [ ] **Step 4: Insert section [d2] into 012_down** (between [d1] and [d3]) - the pre-012 guard body restored VERBATIM from 009:53-69, wrapped in a schema-presence guard (the down must be safe when ops is absent - test `_clean_slate` runs it unconditionally):

```sql
-- [d2] restore the pre-012 completion guard (verbatim 009 body), guarded on schema presence
do $$
begin
  if to_regnamespace('ops') is not null and to_regclass('ops.apparatus') is not null then
    execute $guard$
create or replace function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $fn$
declare
  new_g boolean := (new.status='Complete' and new.provenance_status='approved');
  old_g boolean;
begin
  if tg_op = 'INSERT' then
    if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
    end if;
  else  -- UPDATE
    old_g := (old.status='Complete' and old.provenance_status='approved');
    if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
    end if;
  end if;
  return new;
end; $fn$;
$guard$;
  end if;
end $$;
```

- [ ] **Step 5: Run the full test_012 file - all pass** (including `test_012_h2_breaks_no_sanctioned_path` proving attest/revoke still work through the fns).
- [ ] **Step 6: ASCII audit + commit** (`feat(ops): 012 H2 completion-guard tightening - provenance frozen on Complete, ctx-independent (S6 H2)` with the trailer).

---

### Task 6: Down-migration completion + reversibility round-trip + MANIFEST row

**Files:**
- Modify: `infra/database/migrations/ops/012_ops_app_role_boundary_down.sql` (already complete after Tasks 1/3/5 - verify order [d1][d2][d3][d4][d5])
- Modify: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (append reversibility test)
- Modify: `infra/database/migrations/ops/MANIFEST.md` (012 row)

**Interfaces:** Consumes the complete up+down pair. Produces the proven up->down->up ladder and the MANIFEST entry.

- [ ] **Step 1: Verify the down file section order** reads exactly [d1] fn owner/INVOKER reversal, [d2] guard restore, [d3] DROP OWNED, [d4] guarded/drop-if-safe DROP ROLE (DEV-7), [d5] PUBLIC restore. Reorder if any task appended out of sequence.

- [ ] **Step 2: Write the failing (or immediately-passing) round-trip test.** Append to test_012:

```python
# ---------- Task 6: reversibility ----------

def test_012_reversible_round_trip():
    """down -> posture reverted; up -> posture restored. Leaves 012 APPLIED (chain teardown
    expects to run 012_down first via _clean_slate).

    DEV-7: the contract asserted here is POSTURE-RESTORED (grants revoked in this DB), NOT
    role-absence. Whether the login role OBJECT survives depends on whether a password was
    set out-of-band (rolpassword IS NOT NULL -> [d4] leaves it). During a test_012 run no
    password is set, so the role is dropped; after the Task-8 operator checkpoint it survives.
    Either way [d3] DROP OWNED revoked this DB's grants, which is what we assert. NEVER assert
    the role object is gone."""
    _exec(DOWN012)
    with _admin() as c:
        # fns reverted to INVOKER + postgres-owned
        row = c.execute(
            "select p.prosecdef, p.proowner::regrole::text from pg_proc p"
            " where p.oid = to_regprocedure('ops.attest_apparatus_complete(uuid,uuid,text)')"
        ).fetchone()
        assert row == (False, "postgres"), "down did not revert DEFINER/owner"
        # PUBLIC EXECUTE restored on ops fns (pre-012 posture)
        n = c.execute(
            "select count(*) from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace"
            " where ns.nspname = 'ops'"
            "   and not (p.proacl is null"
            "        or exists (select 1 from aclexplode(p.proacl) a"
            "                   where a.grantee = 0 and a.privilege_type = 'EXECUTE'))"
        ).fetchone()[0]
        assert n == 0, "down did not restore PUBLIC EXECUTE"
        # DEV-7 posture contract: if a role object survives (password-bearing, or cross-DB
        # dependency), its grants in THIS db must be gone (DROP OWNED). If it was dropped,
        # there is nothing to check. Guard has_*_privilege on existence (it errors on a
        # missing role). ops_api EXECUTE on the recognition fns must also be gone.
        for role in ("ops_intake_writer", "ops_api"):
            if c.execute("select 1 from pg_roles where rolname=%s", (role,)).fetchone():
                assert c.execute(
                    "select bool_or(has_table_privilege(%s, c.oid, 'SELECT') or"
                    " has_table_privilege(%s, c.oid, 'INSERT') or has_table_privilege(%s, c.oid, 'UPDATE'))"
                    " from pg_class c join pg_namespace ns on ns.oid=c.relnamespace"
                    " where ns.nspname='ops' and c.relkind in ('r','p')", (role, role, role)
                ).fetchone()[0] in (False, None), "down left " + role + " grants behind"
        if c.execute("select 1 from pg_roles where rolname='ops_api'").fetchone():
            assert c.execute(
                "select has_function_privilege('ops_api',"
                " to_regprocedure('ops.attest_apparatus_complete(uuid,uuid,text)'), 'EXECUTE')"
            ).fetchone()[0] is False, "down left ops_api EXECUTE behind"
    _exec(UP012)
    with _admin() as c:
        assert c.execute(
            "select p.prosecdef from pg_proc p"
            " where p.oid = to_regprocedure('ops.attest_apparatus_complete(uuid,uuid,text)')"
        ).fetchone()[0] is True, "re-up did not restore DEFINER"
```

- [ ] **Step 3: Run the full test_012 file** - the round-trip test must pass, and every OTHER test must still pass (proves 012 is idempotent enough to re-apply after its own down).

- [ ] **Step 4: Add the MANIFEST row.** In `infra/database/migrations/ops/MANIFEST.md`, append to the migration table (match the existing row format exactly - read the file first):

```
| 012 | ops_app role boundary | 012_ops_app_role_boundary.sql | 012_ops_app_role_boundary_down.sql | test_012_ops_app_role_boundary.py | D1=B two-role split (ops_intake_writer / ops_api) + NOLOGIN ops_fn_owner owning the 9 SECURITY DEFINER mutation fns; PUBLIC hygiene; column-scoped grant matrix (D2: status excluded); H2 guard; in-migration posture asserts. Passwords out-of-band. Spec: docs/superpowers/specs/2026-07-01-ops-app-role-boundary-design-v3.md |
```
(If MANIFEST.md uses prose entries instead of a table, mirror the 011 entry's exact shape.)

- [ ] **Step 5: ASCII audit + commit** (`feat(ops): 012 down-migration round-trip + MANIFEST row (S7 down, AC3)` with the trailer).

---

### Task 7: load.py D2 edit - drop status from insert_apparatus

**Files:**
- Modify: `packages/ops-intake/src/ops_intake/load.py:167-186`
- Test: `infra/database/migrations/ops/test_012_ops_app_role_boundary.py` (append one test)

**Interfaces:** Consumes the writer grant matrix (Task 4). Produces an insert_apparatus that succeeds AS ops_intake_writer (the NOT NULL DEFAULT 'Not Started' supplies status).

- [ ] **Step 1: Write the failing test.** Append to test_012:

```python
# ---------- Task 7: load.py D2 ----------

def test_012_insert_apparatus_succeeds_as_writer():
    """The live intake INSERT path must work under the column-scoped matrix (AC5 shape:
    the writer creates apparatus through load.py's statement, status supplied by DEFAULT)."""
    import sys
    sys.path.insert(0, str(HERE.parents[3] / "packages/ops-intake/src"))
    from ops_intake.load import insert_apparatus
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
        with c.cursor() as cur:
            cur.execute(
                "insert into ops.tasks (scope_id, task_name) values (%s,'T') returning id", (sid,))
            tid = cur.fetchone()[0]
            cur.execute(
                "insert into ops.scope_quote_line (scope_quote_id, line_no)"
                " select id, 1 from ops.scope_quote where scope_id=%s returning id", (sid,))
            qlid = cur.fetchone()[0]
            cur.execute("select id from core.equipment_models limit 1")
            em = cur.fetchone()
    emid = em[0] if em else None
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_intake_writer")
            insert_apparatus(
                cur, sid, tid, qlid,
                legacy_source_id="T012:A-1", designation="A-1", apparatus_type="XFMR",
                drawing=None, quoted_hours=1, equipment_model_ref=emid,
            )
            cur.execute(
                "select status from ops.apparatus where legacy_source_id='T012:A-1'")
            assert cur.fetchone()[0] == "Not Started", "DEFAULT did not supply status"
        c.rollback()
```

IMPLEMENTATION NOTE: the `ops.tasks` / `ops.scope_quote_line` seed columns above are the plan author's best grounding from load.py call-sites; if the actual NOT NULL columns differ (run `\d ops.tasks` / `\d ops.scope_quote_line` on ops_test), adjust the SEED ONLY - the assertion (insert_apparatus as writer succeeds; status = 'Not Started') is the fixed contract. If `core.equipment_models` is empty on ops_test and `equipment_model_ref` is NOT NULL on ops.apparatus, seed one minimal row as admin first (mirror a row shape from 008_equipment_models.seed.json).

- [ ] **Step 2: Run it - verify it fails correctly.** Expected: `psycopg.errors.InsufficientPrivilege: permission denied for table apparatus` raised from `insert_apparatus` - the CURRENT statement names `status` (a column the writer does not hold INSERT on).

- [ ] **Step 3: Edit load.py.** In `insert_apparatus` (load.py:167-186), drop `status` from the column list and `'Not Started'` from VALUES:

```python
    cur.execute(
        """
        insert into ops.apparatus (scope_id, task_id, apparatus_designation, apparatus_type,
            equipment_model_ref, drawing_reference, quoted_hours, quote_line_id,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft')
        """,
        (
            scope_id,
            task_id,
            designation,
            apparatus_type,
            equipment_model_ref,
            drawing,
            quoted_hours,
            quote_line_id,
            _SOURCE,
            legacy_source_id,
        ),
    )
```
Also update the function docstring's last line to note: `status is NOT named - the ops.apparatus NOT NULL DEFAULT 'Not Started' supplies it (D2: status is function-owned; the writer holds no status privilege).`

- [ ] **Step 4: Run the test - verify it passes.**
- [ ] **Step 5: Run the package's load tests as a regression sweep** (they still run under the OLD conftest/superuser DSN at this point - that is fine; the statement itself is role-agnostic):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd packages/ops-intake && uv run pytest tests/test_load.py tests/test_load_approve.py -v'
```
Expected: PASS (the INSERT omitting status produces the same row via the DEFAULT). NOTE: this is a PRE-cutover command - the conftest is still the OLD one (reads `OPS_DEV_DSN` directly; its localhost fallback targets `dbname=ops_dev` and would trip the `_require_ops_test` guard), so `OPS_DEV_DSN` is exported to an ops_test DSN here. After Task 9 the conftest hard-requires `OPS_DEV_ADMIN_DSN` and this export is retired.

- [ ] **Step 6: ASCII audit + commit** (`feat(ops): load.py insert_apparatus omits status - DEFAULT supplies it (D2, S3)` with the trailer).

**Task 7b (EXISTS ONLY IF Task 0 FAILED - otherwise skip):** bounded approve.py fallback per spec S0: remove/narrow the apparatus row-lock at approve.py:235-239 (and the projects lock at :233 if Probe B failed), relying on the advisory lock + NO ACTION FK backstop. Requires operator confirmation BEFORE implementation (Task 0 Step 4). Re-prove with two tests in packages/ops-intake/tests: (a) two concurrent approve_runs of the same project_number do not interleave (second blocks on the advisory lock); (b) concurrent approve + recognize aborts (FK NO ACTION), never corrupts. Test code authored at that point against the operator-confirmed lock strategy.

---

### Task 8: Router + mount-gate cutover (ATOMIC - one commit, per V3-4)

**Files:**
- Modify: `apps/control-plane-api/services/ops/intake_router.py:52-53`
- Modify: `apps/control-plane-api/services/ops/recognition_router.py:23-24`
- Modify: `apps/control-plane-api/main.py:109-111`
- Create: `apps/control-plane-api/tests/test_ops_route_mount_gate.py` (NO-DB module - both gate tests)
- Modify: `apps/control-plane-api/tests/test_ops_intake_routes.py` (DELETE its old host-gate test), `apps/control-plane-api/tests/test_ops_recognition_routes.py` (DELETE its host-gate subprocess test) - both move to the no-DB module.

**Interfaces:** Produces: `intake_router._dsn()` -> `OPS_INTAKE_WRITER_DSN`; `recognition_router._dsn()` -> `OPS_API_DSN` (which `_read_view()` at :99 inherits - single change point); `_ops_intake_enabled()` -> BOTH DSNs required. Tasks 9/10 rely on these env var names exactly.

**HIGH-1 (why a new module):** both route-test modules carry a SESSION-AUTOUSE `apply_migrations` fixture that reads `os.environ["OPS_DEV_DSN"]` (test_ops_intake_routes.py:75, test_ops_recognition_routes.py:17). It runs at collection BEFORE any selected test, so running just the gate tests in-place errors with `KeyError: OPS_DEV_DSN` before the assertion. The pure mount/host-gate tests therefore live in a dedicated NO-DB module (no autouse DB fixture); they are the S8 "host-gating guard tests re-authored in the same atomic change as the router cutover".

**API test contract (HIGH-2, applies to every API command in Tasks 8/10/12):** this repo is NOT a uv workspace (root pyproject has no workspace members); control-plane-api deps live in `requirements.txt`/`requirements-dev.txt`. Bare `uv run pytest` fails collecting psycopg. AND importing `main` requires `DATABASE_URL` (config.py:31). So every control-plane-api pytest command is:
`<ENV> && export DATABASE_URL=postgresql://localhost/ops_test && cd apps/control-plane-api && uv run --with-requirements requirements-dev.txt pytest <targets> -v`
(`DATABASE_URL` is a placeholder - the control-plane's own config; ops behavior routes through the role DSNs. `requirements-dev.txt` provides pytest + app deps; if pytest is absent from it, add `--with pytest`.)

- [ ] **Step 1: Write the failing gate module.** Create `apps/control-plane-api/tests/test_ops_route_mount_gate.py`:

```python
# test_ops_route_mount_gate.py -- NO-DB module for the ops-route mount/host gating tests.
# Deliberately carries NO apply_migrations autouse fixture, so it runs at Task 8 (before the
# Task-10 route-harness cutover). It only imports main/_ops_intake_enabled and spawns a
# subprocess; config.py requires DATABASE_URL at import, so set a placeholder first.
import os, pathlib, subprocess, sys
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/ops_test")


def test_ops_intake_enabled_requires_both_role_dsns(monkeypatch):
    from main import _ops_intake_enabled
    monkeypatch.delenv("OPS_INTAKE_WRITER_DSN", raising=False)
    monkeypatch.delenv("OPS_API_DSN", raising=False)
    monkeypatch.delenv("OPS_DEV_DSN", raising=False)
    assert _ops_intake_enabled() is False
    monkeypatch.setenv("OPS_INTAKE_WRITER_DSN", "x")
    assert _ops_intake_enabled() is False, "writer DSN alone must not mount"
    monkeypatch.setenv("OPS_API_DSN", "y")
    assert _ops_intake_enabled() is True
    monkeypatch.delenv("OPS_INTAKE_WRITER_DSN")
    assert _ops_intake_enabled() is False, "api DSN alone must not mount"
    monkeypatch.setenv("OPS_DEV_DSN", "z")
    assert _ops_intake_enabled() is False, "OPS_DEV_DSN must be inert"


def test_recognition_router_host_gated_subprocess():
    """With the role DSNs unset, the recognition routes are NOT mounted (404)."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("OPS_INTAKE_WRITER_DSN", "OPS_API_DSN", "OPS_DEV_DSN")}
    env["DATABASE_URL"] = "postgresql://localhost/ops_test"
    code = ("import os;"
            "[os.environ.pop(k, None) for k in ('OPS_INTAKE_WRITER_DSN','OPS_API_DSN','OPS_DEV_DSN')];"
            "from fastapi.testclient import TestClient; from main import app;"
            "c=TestClient(app);"
            "import sys; sys.exit(0 if c.post('/api/v1/ops/recognition/completion/attest',json={}).status_code==404 else 1)")
    r = subprocess.run([sys.executable, "-c", code],
                       cwd=str(pathlib.Path(__file__).resolve().parents[1]), env=env)
    assert r.returncode == 0, "recognition routes must be absent when the role DSNs are unset"
```
In the SAME commit, DELETE the old host-gate tests from the route files: the intake `monkeypatch`-OPS_DEV_DSN gate test (~test_ops_intake_routes.py:184-190) and the recognition subprocess test (test_ops_recognition_routes.py:64-73). Their coverage now lives in the no-DB module (S8 atomicity satisfied).

- [ ] **Step 2: Run it - verify it fails** (API contract above):
`<ENV> && export DATABASE_URL=postgresql://localhost/ops_test && cd apps/control-plane-api && uv run --with-requirements requirements-dev.txt pytest tests/test_ops_route_mount_gate.py::test_ops_intake_enabled_requires_both_role_dsns -v`
Expected (empirically confirmed 2026-07-01 with a throwaway copy of this module): FAIL on an ASSERTION - the pre-cutover gate is `bool(os.environ.get("OPS_DEV_DSN"))`, so with only the role DSNs set `_ops_intake_enabled()` returns False and the `is True` assert fails first (and with OPS_DEV_DSN set it returns True, failing the inert assert). Crucially NOT a collection error / `KeyError: OPS_DEV_DSN` / SyntaxError - the no-DB module (no autouse DB fixture; the api `tests/conftest.py` has none) runs standalone in <1s.

- [ ] **Step 3: Make the three edits (one atomic change):**

`apps/control-plane-api/services/ops/intake_router.py:52-53`:
```python
def _dsn() -> str:
    return os.environ["OPS_INTAKE_WRITER_DSN"]
```

`apps/control-plane-api/services/ops/recognition_router.py:23-24`:
```python
def _dsn() -> str:
    return os.environ["OPS_API_DSN"]
```

`apps/control-plane-api/main.py:109-111`:
```python
def _ops_intake_enabled() -> bool:
    # ops intake is host-only (mesh PG17); mount only when BOTH role DSNs are present.
    # OPS_DEV_DSN is retired as an app identity (012 role boundary) and must stay inert here.
    return bool(os.environ.get("OPS_INTAKE_WRITER_DSN")) and bool(os.environ.get("OPS_API_DSN"))
```
Also update the two module docstrings/comments in the routers that name OPS_DEV_DSN (intake_router.py:19-21 module docstring; any comment near recognition_router.py:23) to name the new vars.

- [ ] **Step 4: Run the no-DB gate module - verify BOTH tests pass:**
`<ENV> && export DATABASE_URL=postgresql://localhost/ops_test && cd apps/control-plane-api && uv run --with-requirements requirements-dev.txt pytest tests/test_ops_route_mount_gate.py -v`
Expected: 2 passed. NOTE: the REST of the two route-test files will FAIL/SKIP now (their autouse fixtures still read OPS_DEV_DSN + app process lacks the role DSNs) - EXPECTED, repaired in Task 10; do not run the full route files as this task's gate.
- [ ] **Step 5: ASCII audit + commit** (`feat(ops): three-DSN cutover - routers + both-DSN mount gate + no-DB gate module, OPS_DEV_DSN inert (S8, V3-3/V3-4, M5, HIGH-1/2)` with the trailer).

---

### OPERATOR CHECKPOINT (blocking, before Task 9)

The two LOGIN roles now exist on the dev cluster after any test_012 run. Out-of-band (never in a model-visible terminal, never in a file the agent reads back):

1. `ALTER ROLE ops_intake_writer PASSWORD '...'` and `ALTER ROLE ops_api PASSWORD '...'` on the dev cluster (psql as postgres via `docker exec apex-dev-pg psql -U postgres`).
2. Add to host `infra/.env`: `OPS_INTAKE_WRITER_DSN` and `OPS_API_DSN`. **All DSNs in this plan target `dbname=ops_test`** (the test tier). Both role DSNs use `host=127.0.0.1 port=5432 dbname=ops_test sslmode=disable` with `user=ops_intake_writer` / `user=ops_api` and the passwords just set. **OPS_DEV_ADMIN_DSN is NOT added to .env** - the Task P `<ENV>` preamble already exports it (built from `DEV_PG_PASSWORD`, user=postgres, dbname=ops_test); keep that convention. `OPS_DEV_DSN` (the pre-012 ops_dev app DSN, if present) is untouched here - Task 11 retires its last readers.

Agent-side verification (NAMES only, never values):
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && grep -cE "^(OPS_INTAKE_WRITER_DSN|OPS_API_DSN)=" infra/.env'
```
Expected: `2`. Then a login smoke (no value printed; admin DSN comes from the `<ENV>` preamble):
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; uv run --with "psycopg[binary]" python - <<PYEOF
import os, psycopg
for k in ("OPS_INTAKE_WRITER_DSN", "OPS_API_DSN"):
    with psycopg.connect(os.environ[k], connect_timeout=5) as c:
        u, s = c.execute("select current_user, (select rolsuper from pg_roles where rolname=current_user)").fetchone()
        print(k, "->", u, "super=", s)
PYEOF'
```
Expected: `OPS_INTAKE_WRITER_DSN -> ops_intake_writer super= False` and `OPS_API_DSN -> ops_api super= False`. If either raises OperationalError, the password/DSN is wrong or the role has no password - resolve before Task 9.

---

### Task 9: Package harness three-identity cutover + real-login SET ROLE denials

**Files:**
- Modify: `packages/ops-intake/tests/conftest.py` (full rewrite of the DSN layer)
- Modify: `packages/ops-intake/tests/test_recognition_wrappers.py` (DSN routing + new denial tests)
- Modify (M4 - whole-suite blast radius): any of the ~10 files in `packages/ops-intake/tests/` whose SETUP DML is denied to the writer once `clean_ops`/`dsn` return the writer DSN. Enumerated in Step 1b; each seed moves to `admin_dsn`, behavior stays on writer/api.

**Interfaces:** Consumes the three env DSNs (checkpoint). Produces fixtures `admin_dsn` / `writer_dsn` / `api_dsn`; `dsn` and `clean_ops` return the WRITER DSN (behavior default - AC5); `apply_migrations` runs the 001..012 chain as admin.

**M4 - blast radius warning:** flipping `dsn`/`clean_ops` to the writer DSN changes the identity for EVERY test that used them for SETUP, not just behavior. Grounded: `ops.persons` INSERTs, explicit-`status` apparatus INSERTs, and forced-Complete blocks appear across all 10 files in `packages/ops-intake/tests/`. Each becomes InsufficientPrivilege as the writer. Step 1b enumerates them up front so the rewire is planned, not discovered one-failure-at-a-time under the Constraint-10 STOP rule.

- [ ] **Step 1: Rewrite the conftest DSN layer.** Replace conftest.py lines 19-50 and the `apply_migrations` DSN usage (keep `_OPS_TRUNCATE`, `_MIGRATIONS_DIR`, `mini_workbook`, `real_workbook` unchanged):

```python
def _require_ops_test(dsn):
    from psycopg.conninfo import conninfo_to_dict
    db = conninfo_to_dict(dsn).get("dbname")
    assert db == "ops_test", (
        "Safety guard: DSN must target dbname=ops_test, got " + repr(db)
    )


def _admin_dsn():
    # Hard-require (C2/D7): the OPS_DEV_DSN fallback is deleted - no fallback, no superuser
    # behavior tier. Admin is for the ladder, TRUNCATE, and setup DML ONLY.
    d = os.environ["OPS_DEV_ADMIN_DSN"]
    _require_ops_test(d)
    return d


def _writer_dsn():
    d = os.environ["OPS_INTAKE_WRITER_DSN"]
    _require_ops_test(d)
    return d


def _api_dsn():
    d = os.environ["OPS_API_DSN"]
    _require_ops_test(d)
    return d


@pytest.fixture
def admin_dsn():
    return _admin_dsn()


@pytest.fixture
def writer_dsn():
    return _writer_dsn()


@pytest.fixture
def api_dsn():
    return _api_dsn()


@pytest.fixture
def dsn():
    # Behavior default: the intake/approve pipeline runs AS THE WRITER (AC5 - the
    # column-scoped matrix is exercised by the positive pipeline, not admin-seeded).
    return _writer_dsn()


@pytest.fixture
def clean_ops():
    # TRUNCATE is an admin-tier privilege; the returned DSN (what tests run behavior
    # against) is the WRITER.
    import psycopg
    with psycopg.connect(_admin_dsn(), autocommit=True) as c:
        c.execute(_OPS_TRUNCATE)
    return _writer_dsn()
```
In `apply_migrations`, replace `d = _dsn()` / `_require_ops_test(d)` with `d = _admin_dsn()`, extend `up_migrations` with `"012_ops_app_role_boundary.sql"`, and prepend `_run_sql(c, mig_dir / "012_ops_app_role_boundary_down.sql")` as the FIRST down in BOTH the pre-up reset and the teardown (before the 011 down). Delete the old module-level `_dsn()` (lines 27-35) entirely.

- [ ] **Step 1b (M4): enumerate the writer-denied setup DML across the whole package suite BEFORE rewiring.**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform/packages/ops-intake/tests && grep -rnE "insert into ops\.(persons|apparatus|scopes|projects)|completion_ctx|status=.Complete.|set local" .'
```
For each hit, classify: (i) SETUP DML (seeding a fixture/precondition - persons, forced-Complete, explicit-status apparatus, project/scope seeds) -> must run on `admin_dsn`; (ii) BEHAVIOR under test (a load.py/approve.py/rec.* call) -> stays on `writer_dsn`/`api_dsn`. Add a per-file rewire line to this task's checklist for every file that appears (expected: all ~10). Where a file has its OWN local `_person`/`_eligible` helpers (e.g. test_recognition_wrappers.py, test_load_approve.py), give those helpers an explicit dsn arg and pass `admin_dsn`; where a file seeds inline via `clean_ops`, open a separate `admin_dsn` connection for the seed and keep `clean_ops`/`dsn` (writer) for the behavior. Prefer a SHARED admin seed helper in conftest (`@pytest.fixture def seed_min` returning ids, admin-connected) to avoid per-file drift. Do NOT move a behavior call to admin to make it pass (Constraint 10).

- [ ] **Step 2: Re-route test_recognition_wrappers.py.** The seed helpers `_person` / `_eligible` and the forced-Complete setup are ADMIN DML; every `rec.*` behavior call runs as the API role:
  - Change every test signature from `(clean_ops)` to `(clean_ops, admin_dsn, api_dsn)`.
  - In each test body: seeds `_person(admin_dsn)` / `_eligible(admin_dsn)`; behavior `rec.attest_complete(api_dsn, ...)`, `rec.recognize(api_dsn, ...)`, `rec.reverse(api_dsn, ...)`, `rec.revoke(api_dsn, ...)`.
  - In `test_recognize_without_attestation_raises_state_error`, the forced-Complete block (`set local ops.completion_ctx='1'; update ops.apparatus set status='Complete'`) connects via `admin_dsn` (it is setup DML - the sanctioned superuser tier); the `rec.recognize` call uses `api_dsn`.
  - `test_intake_apparatus_insert_still_succeeds_under_completion_guard`: its direct INSERTs name `status` -> route them through `admin_dsn` (they are guard-behavior probes, not writer-path probes; the writer-path equivalent lives in test_012).

- [ ] **Step 3: Add the real-login denial tests** (proof (h) SET ROLE + package-tier forge-closure). Append to test_recognition_wrappers.py:

```python
def test_login_roles_cannot_set_role_fn_owner(writer_dsn, api_dsn):
    """Proof (h): a REAL login session (session_user = the role) cannot SET ROLE
    ops_fn_owner. (test_012 can only assert pg_has_role - SET ROLE permission is
    checked against session_user, which stays postgres there.)"""
    for d in (writer_dsn, api_dsn):
        with psycopg.connect(d) as c, c.cursor() as cur:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("set role ops_fn_owner")


def test_writer_cannot_recognize_forge_closure(clean_ops, admin_dsn, writer_dsn):
    """Forge-closure at the package tier: the writer identity cannot attest, even via
    the wrappers. The wrapper may translate the error - the contract is: the call FAILS
    and no attestation row exists."""
    who = _person(admin_dsn)
    aid = _eligible(admin_dsn)
    with pytest.raises(Exception):
        rec.attest_complete(writer_dsn, aid, who, "forged")
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        n = c.execute(
            "select count(*) from ops.completion_attestation where apparatus_id=%s", (aid,)
        ).fetchone()[0]
        assert n == 0, "a forged attestation row landed"
```

- [ ] **Step 4: Run the wrappers file** (`uv run pytest tests/test_recognition_wrappers.py -v`). Expected: PASS. Then run the FULL package suite (`uv run pytest tests/ -v`). Triage rule for failures (Global Constraint 10): setup-DML denied as writer -> move that seed to `admin_dsn`; a LIVE load.py/approve.py write denied as writer -> STOP, that is a grant-matrix finding for the operator. NEVER fix a failure by widening a grant or reverting a behavior connection to admin.
- [ ] **Step 5: ASCII audit + commit** (`feat(ops): package harness three-identity cutover - behavior as writer/api, admin fixtures, SET ROLE denials (S9, C2, AC5)` with the trailer).

---

### Task 10: API route-test cutover + route-boundary non-superuser proof

**Files:**
- Modify: `apps/control-plane-api/tests/test_ops_intake_routes.py`
- Modify: `apps/control-plane-api/tests/test_ops_recognition_routes.py`

**Interfaces:** Consumes the router env names (Task 8). Produces: both files' admin fixtures on OPS_DEV_ADMIN_DSN; ladders extended to 012; the TestClient app process running with ONLY the two role DSNs; the non-superuser app-process proof.

- [ ] **Step 1: test_ops_intake_routes.py edits:**
  - Local `_dsn()` (:63-64) becomes `_admin_dsn()` returning `os.environ["OPS_DEV_ADMIN_DSN"]`; every fixture/seed caller (`apply_migrations`, `clean_ops_between_tests`, `person_id`, the inline `psycopg.connect` seed at :417-430) switches to it.
  - **M3 - sweep EVERY textual `OPS_DEV_DSN` in this file, not just `_dsn()`:** `grep -n OPS_DEV_DSN` the file first (grounded hits at ~:13 DATABASE_URL note, ~:23 docstring, ~:155). The old monkeypatch host-gate test (~:184-190) was already DELETED in Task 8 (moved to test_ops_route_mount_gate.py) - confirm it is gone. Rename/delete each remaining hit so Task 11's acceptance grep returns zero for this file. The `DATABASE_URL` placeholder line stays (it is not OPS_DEV_DSN).
  - `up_migrations` (:98-109) extends with `"011_scope_quote_line_description.sql", "012_ops_app_role_boundary.sql"` (it currently stops at 010 - DEV-6); the teardown/reset gains the corresponding downs FIRST (`012_..._down.sql`, `011_..._down.sql` before the existing ones), with the `delete from ops.intake_runs` data-loss-guard step before 010's down (mirror the package conftest's reset block exactly).
  - The `client` fixture asserts the app-process env BEFORE constructing TestClient:
```python
@pytest.fixture(scope="session")
def client(apply_migrations):
    assert os.environ.get("OPS_INTAKE_WRITER_DSN") and os.environ.get("OPS_API_DSN"), (
        "route tests require the two role DSNs (operator checkpoint)"
    )
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
```

- [ ] **Step 2: Add the route-boundary false-green test** (V3-3c) to test_ops_intake_routes.py:

```python
def test_app_process_role_dsns_are_not_superuser():
    """The decisive false-green guard: the DSNs the TestClient app process actually uses
    (the routers' own _dsn()) must resolve to non-superuser roles. Fails loud if a
    builder points API behavior at the admin/postgres identity."""
    import psycopg
    from services.ops.intake_router import _dsn as intake_dsn
    from services.ops.recognition_router import _dsn as recognition_dsn
    for d, want in ((intake_dsn(), "ops_intake_writer"), (recognition_dsn(), "ops_api")):
        with psycopg.connect(d) as c:
            user, is_super = c.execute(
                "select current_user, (select rolsuper from pg_roles where rolname=current_user)"
            ).fetchone()
            assert user == want, "app-process DSN resolves to " + user + ", expected " + want
            assert is_super is False, "app-process DSN is a superuser"
```

- [ ] **Step 3: test_ops_recognition_routes.py edits:**
  - `_dsn()` (:11) becomes `_admin_dsn()` on `OPS_DEV_ADMIN_DSN`; `person_id`, `eligible`, and `apply_migrations` use it.
  - `_CHAIN` (:13-15) extends to the full 001..012 list (currently stops at 009 - DEV-6); reset/teardown mirrors the package conftest block (incl. `delete from ops.intake_runs` + the 012/011/010 downs).
  - The host-gating subprocess test (:64-73) was DELETED in Task 8 (moved to test_ops_route_mount_gate.py) - confirm it is gone; do NOT re-add it here.
  - **M3 - sweep EVERY remaining textual `OPS_DEV_DSN` in this file** (grounded hit at ~:65 and any comment/docstring) to the new names or delete, so Task 11's acceptance grep returns zero for this file.
  - `client` fixture: same both-DSN assert as Step 1.

- [ ] **Step 4: Run both route files** (API contract - `requirements-dev.txt` + DATABASE_URL, per Task 8):
`<ENV> && export DATABASE_URL=postgresql://localhost/ops_test && cd apps/control-plane-api && uv run --with-requirements requirements-dev.txt pytest tests/test_ops_intake_routes.py tests/test_ops_recognition_routes.py -v`
Expected: PASS - POST/GET route behavior now flows writer/api through the app process (started with the role DSNs from `.env`); fixtures flow admin (OPS_DEV_ADMIN_DSN); `test_app_process_role_dsns_are_not_superuser` proves the app process is non-superuser. Same triage rule as Task 9 Step 4.
- [ ] **Step 5: ASCII audit + commit** (`feat(ops): route-test three-identity cutover + non-superuser app-process proof (S9, V3-3)` with the trailer).

---

### Task 11: Infra ladder test cutover + smoke script + runbook + acceptance grep

**Files:**
- Modify: `infra/database/migrations/ops/test_001_identity_skeleton.py`, `test_002_quote_model.py`, `test_004_person_anchor.py`, `test_005_recognition_ledger.py`, `test_006_progress_billing.py`, `test_007_intake_envelope.py`, `test_008_core_equipment_models.py`, `test_009_recognition_bridge.py`, `test_010_native_envelope_intake.py`, `test_011_scope_quote_line_description.py`
- Modify: `apps/operations-web/scripts/smoke-estimator-native.mjs`
- Modify: `infra/database/migrations/ops/MANIFEST.md` (invocation line)

**Interfaces:** Produces zero OPS_DEV_DSN readers in the S8 acceptance-grep scope.

- [ ] **Step 1: Enumerate the OPS_DEV_DSN readers** (grounded expectation: one `os.environ.get("OPS_DEV_DSN")` fallback block per test file, same shape as test_011:11-16):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && grep -rn "OPS_DEV_DSN" infra/database/migrations/ops/ apps/operations-web/scripts/smoke-estimator-native.mjs'
```

- [ ] **Step 2: NORMALIZE each infra test file's DSN block (HIGH-3 - NOT a bare rename).** A mechanical `OPS_DEV_DSN`->`OPS_DEV_ADMIN_DSN` rename passes the acceptance grep but leaves UNSAFE DDL fallback: grounded, test_001 (:22) and test_002 (:23) default their fallback to `dbname=ops_dev` with NO guard, and test_006 (:6) defaults to ops_test but has NO DSN guard. Every `test_001..011` file must end up with (a) env read `os.environ.get("OPS_DEV_ADMIN_DSN")`, (b) any localhost fallback defaulting to `dbname=ops_test` (never ops_dev), and (c) a real guard - `assert conninfo_to_dict(DSN).get("dbname") == "ops_test"` at module level, matching test_011:11-17. Files that already have the guard+ops_test default (test_011, and test_010's shape) need only the env rename; test_001/002 need the default flipped to ops_test AND the guard added; test_006 needs the guard added. The point: admin-only DDL must be IMPOSSIBLE to run against ops_dev by env accident.

- [ ] **Step 3: smoke-estimator-native.mjs:** `grep -n OPS_DEV_DSN` first - there are MULTIPLE mentions: the actual variable read is at ~:314 (`const dsn = process.env.OPS_DEV_DSN`), plus a comment + two error strings at ~:309/:318/:323. Rename the `process.env.OPS_DEV_DSN` read to `process.env.OPS_DEV_ADMIN_DSN`, and update every comment/string that names OPS_DEV_DSN so the acceptance grep returns zero for this file. The HTTP intake/approve leg is untouched - it is writer-scoped because the API process starts with OPS_INTAKE_WRITER_DSN (the script cannot select the server's identity). Add that as a one-line comment at the change site.

- [ ] **Step 4: Runbook edit:** MANIFEST.md:21's documented CLI invocation `ops-intake load <xlsm> --dsn "<ops_dev dsn>" --approve` -> `--dsn "<ops_intake_writer dsn>"` with a note: materialization runs as the writer; migrations/TRUNCATE stay on the admin DSN.

- [ ] **Step 5: Acceptance grep (S8 - the gate; `rg` is not on the ssh PATH, use grep):**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && grep -rnI --exclude-dir=__pycache__ "OPS_DEV_DSN" infra/database/migrations/ops/ apps/control-plane-api/services/ops/intake_router.py apps/control-plane-api/services/ops/recognition_router.py apps/control-plane-api/main.py apps/control-plane-api/tests/test_ops_intake_routes.py apps/control-plane-api/tests/test_ops_recognition_routes.py apps/operations-web/scripts/smoke-estimator-native.mjs; echo "grep-exit=$?"'
```
Expected: NO matches, `grep-exit=1`. M3: `-I` skips binary matches and `--exclude-dir=__pycache__` skips compiled `.pyc` (either would otherwise leave `grep-exit=0` after all source is clean, masking the gate). `OPS_DEV_ADMIN_DSN` contains the substring `OPS_DEV_` but the search term is the full `OPS_DEV_DSN`, so the longer name does NOT match - verify zero hits. Separately:

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && grep -nI "OPS_DEV_DSN" packages/ops-intake/tests/conftest.py; echo "grep-exit=$?"'
```
Expected: `grep-exit=1` (the fallback is gone - done in Task 9).

Informational sweep (NOT the gate - report, do not silently change): `grep -rln "OPS_DEV_DSN" apps/ packages/ infra/ | grep -v node_modules`. Any hit OUTSIDE the S8 scope goes into the wrap-up for the operator (S8: "Keep OPS_DEV_DSN only if a separate read-only legacy path explicitly documents it").

- [ ] **Step 6: Run the touched infra tests** (spot: test_009, test_011 - the two biggest) + ASCII audit + commit (`feat(ops): infra ladder tests + smoke + runbook to OPS_DEV_ADMIN_DSN; acceptance grep clean (S8, RV-3)` with the trailer).

---

### Task 12: Full integration - positive pipeline as-role, full suites green, housekeeping

**Files:**
- Modify: `docs/spec/recognition-bridge` S5.11 status (locate via `grep -rn "S5.11" docs/`), lane docs.

**Interfaces:** Consumes everything. Produces the plan's DONE state (AC1, AC3-AC11 satisfied ON ops_test; AC2's ops_dev-apply leg + proof (g)'s work.* leg execute at the operator-gated ops_dev apply, OUT of this plan; AC12 = prod untouched holds by construction).

- [ ] **Step 1: Full migration-ladder suite** (full `<ENV>` preamble - PATH + admin DSN):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; export OPS_DEV_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd infra/database/migrations/ops && uv run --with "psycopg[binary]" --with pytest pytest test_001_identity_skeleton.py test_002_quote_model.py test_004_person_anchor.py test_005_recognition_ledger.py test_006_progress_billing.py test_007_intake_envelope.py test_008_core_equipment_models.py test_009_recognition_bridge.py test_010_native_envelope_intake.py test_011_scope_quote_line_description.py test_012_ops_app_role_boundary.py -v'
```
Expected: ALL PASS, exit 0 (unmasked - this command's exit code IS the gate).

- [ ] **Step 2: Full package suite as-role** (role DSNs come from `.env` via the checkpoint):

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; export OPS_DEV_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd packages/ops-intake && uv run pytest tests/ -v'
```
Expected: ALL PASS. This includes the positive pipeline (AC8): intake -> approve_run AS THE WRITER (apparatus created through load.py under the column-scoped matrix), recognition wrappers AS ops_api, and the recognized-then-reapprove edge in whichever existing test exercises `_conflict_kind` (verify it ran: `-k "reapprove or conflict"` lists at least one passed test; if none exists, add one: approve -> attest -> recognize (api) -> re-approve same project (writer) -> assert outcome `revision_blocked`).

- [ ] **Step 3: Ops route suites:**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . ./infra/.env; set +a; export PATH=$HOME/.local/bin:$PATH; export OPS_DEV_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; export DATABASE_URL=postgresql://localhost/ops_test; cd apps/control-plane-api && uv run --with-requirements requirements-dev.txt pytest tests/test_ops_route_mount_gate.py tests/test_ops_intake_routes.py tests/test_ops_recognition_routes.py -v'
```
Expected: ALL PASS, including `test_app_process_role_dsns_are_not_superuser` and both no-DB gate tests (`test_ops_route_mount_gate.py`). (API contract: `--with-requirements requirements-dev.txt` + `DATABASE_URL` - this repo is not a uv workspace and `main` requires DATABASE_URL at import.)

- [ ] **Step 4: Boundary-denial roll-call.** Verify every spec S9 proof has a green test: (a) `test_012_denial_a_forged_complete_insert`; (b) `test_012_denial_b_writer_status_update`; (c) `test_012_denial_c_writer_cannot_execute_recognition` + `test_writer_cannot_recognize_forge_closure`; (d) `test_012_denial_d_api_cannot_fabricate`; (e) `test_012_h2_provenance_frozen_on_complete_regardless_of_guc`; (f) `test_012_denial_f_ledger_inserts`; (g) `test_012_denial_g_delete_projects` (+ work.* via [2a] assert on ops_dev apply); (h) `test_login_roles_cannot_set_role_fn_owner` + `test_012_no_login_role_is_member_of_fn_owner`. List each with its file:line in the completion report.

- [ ] **Step 5: Housekeeping (part of done):** update the recognition-bridge spec S5.11 status line (012 built + tested on ops_test; ops_dev apply pending operator gate); confirm the MANIFEST 012 row (Task 6) and the plan/spec/IRP records under docs/ are committed.

- [ ] **Step 6: Final ASCII sweep over every file this plan touched + commit** (`feat(ops): 012 lane integration green on ops_test - full suites as-role, denial roll-call, housekeeping (AC1,AC3-11 on ops_test)` with the trailer).

- [ ] **Step 7: STOP.** Do NOT merge, do NOT apply 012 to ops_dev, do NOT touch prod. Next per the ratified flow: opus + Codex IRP on the built branch -> operator-gated ops_dev apply -> soak -> D8 prod re-grounding (separate packet).

---

## Self-Review (performed at authoring; refreshed after the adversarial re-gate)

1. **Spec coverage:** S0 -> Task 0 (+ probe regressions Task 4); S2/D1..D8+M4 -> Tasks 1-5; S3 (D2 mechanism) -> Tasks 4+7; S4 (role arch) -> Task 1; S5 (grant matrix incl RV-1/RV-2 owner grants) -> Tasks 3-4; S6 (DEFINER + ordering + H2) -> Tasks 3+5; S7 (012 structure, asserts, down order) -> Tasks 1-6; S8 (cutover map incl RV-3 infra tests, acceptance grep, runbook, housekeeping) -> Tasks 8-11 + 12.5; S9 (test plan: three-identity, route-boundary false-green, denials a-h, positive pipeline, concurrency) -> Tasks 4,5,9,10,12; S10 (out of scope) -> Task 12 Step 7 stop; S11 AC1-12 -> mapped in Task 12; S12 risks R1-R6 -> R1=Task 0, R2=[5a] view assert, R3=DEV-4/DEV-5 noted, R4/R5 operator-tier, R6=[3] comment.
2. **Placeholder scan:** no TBDs. Bounded discovery points are contracted, not placeholders: Task 7 Step 1 seed columns (assertion fixed, seed adjustable), Task 9 Step 1b + Task 11 Step 1 grep enumerations (mechanical rename), Task 7b (conditional on Task 0 FAIL + operator confirm). Task P Step 1 is an operator-gated environment reconcile, explicitly flagged.
3. **Type consistency:** `SIGS[:4]` = the 4 recognition fns everywhere; env var names identical across Tasks P/8/9/10/11 (`OPS_INTAKE_WRITER_DSN`, `OPS_API_DSN`, `OPS_DEV_ADMIN_DSN`); `_seed_min`/`_denied`/`_admin`/`_force_complete` defined in Tasks 1/4/5 and consumed downstream; the projects UPDATE column list is byte-identical in [5], [5a], and PROJECTS_UPDATE_COLS.
4. **Deviations from spec, all operator-visible:** DEV-1..DEV-8. DEV-7 (guarded DROP ROLE) is operator-RATIFIED 2026-07-01; DEV-8 (roles-before-PUBLIC-revoke ordering) is cosmetic with the S6 invariant preserved. Global Constraint 7 (the top-line down-order contract) is updated to match the DEV-7 body.
5. **Adversarial re-gate fixes folded (3-lens NOT_READY -> resolved):** H2 environment gap -> Task P preflight (operator-gated port reconcile + Infisical `.env.agent` note + host-TCP hard gate) + `<ENV>` preamble (PATH + admin DSN from DEV_PG_PASSWORD); H1 -> DEV-7 password-guarded DROP ROLE + Task 6 grants-revoked assertion; M1 checkpoint DSN wording; M2 positive ops_api EXECUTE assert in [5a]; M3 route-file/smoke textual sweep + `-I --exclude-dir=__pycache__` grep; M4 Task 9 Step 1b whole-suite enumeration; M5 recognition host-gate folded into Task 8; M6 forged-INSERT status-only; L1->DEV-8; L2 AC wording ops_test-scoped; L3 ALL ROUTINES; L4 probe ON_ERROR_ROLLBACK; L5 RED prediction; plus `_force_complete` transactional-connection fix. Second fast re-gate on the deltas found + fixed: escaped-quote heredoc (Task P probe), unqualified `oid` (Task 6 query) - both empirically re-verified live.
6. **Operator live-grounded review fixes folded (2026-07-01, 3 HIGH + 2 MED):** HIGH-1 the route-test autouse `apply_migrations` fixtures KeyError before the gate assertion -> pure mount/host-gate tests MOVED to a new NO-DB module `test_ops_route_mount_gate.py` (Task 8); HIGH-2 repo is not a uv workspace + `main` needs DATABASE_URL -> API commands use `uv run --with-requirements requirements-dev.txt` + `DATABASE_URL` (header contract + Tasks 8/10/12); HIGH-3 early-ladder infra tests default to ops_dev / lack a guard -> Task 11 Step 2 NORMALIZES every test_001..011 DSN block (ops_test default + conninfo guard), not a bare rename; MED-1 Task P compose targets SERVICE `dev-pg` (not container name) from repo root; MED-2 Task 1 hard-stops on a dirty worktree (`test -z "$(git status --porcelain)"`).
