# PM/Ops Emergency Containment — Phase 0 Design Packet

> **Design-only.** No production access, SQL, deploy, secret change, connectivity repair,
> schema promotion, A1–A3, OBS action, push, or PR was performed to produce this packet.
> Each action is **independently gated** by its own operator GO and **independently applied**
> (never one combined production transaction). Permanent identity is **P1** — separately gated,
> **not** a prerequisite for P0.

**Revision — rev5 (2026-07-14).** Folds the operator-ratified rev5 code-review — all seven findings ratified; dispositions in §12 and the committed review record (`2026-07-14-pm-ops-p0-containment-review-record.md`). Changes: **(1)** `SupabaseStore.reset()` now **unconditionally** refuses in every environment — reset/reseed is a test-only capability that exists solely on `MemoryStore` (`app/db/memory_store_original.py:61`), reachable only when `SEAM_STORE_BACKEND=memory`. **(2)** P0-E readiness probes the **actual `ops_api`/`ops_intake_writer` serving identities** via `OPS_API_DSN`/`OPS_INTAKE_WRITER_DSN` (psycopg, mirroring the routers) — asserting `current_user`, a **per-role least-privilege contract** (`ops.v_completion_recognition_worklist` for `ops_api`, `ops.intake_runs` for the writer — **not** `ops.persons`, which is `ops_fn_owner`-only), and absence of a forbidden privilege — instead of checking `ops.persons` through the wrong (`config.engine`) connection. **(3)** P0-A is a single **guarded `REPEATABLE READ, READ ONLY`** transaction with a project-fingerprint + read-only guard, **effective-role closure** (fixed-principal × all privileges, plus the `pg_auth_members` membership closure — not ACL-literal enumeration), and **fail-closed-leaning** SECURITY DEFINER discovery (name-reference + dynamic-SQL flags as the reliable primary; `pg_depend` supplementary and inert for PL/pgSQL; unknowns treated in-scope; residual indirect-write gap disclosed in §2). **(4)** P0-C's immediate claim is narrowed to **existing-exposure containment**; the ineffective rev4 "best-effort PUBLIC" ADP-function token is **removed** — forward-function PUBLIC EXECUTE posture is a separately measured finish line (§11.6) that does **not** gate urgent `014`. **(5)** §1 replaces the "no cross-action dependency" claim with an explicit **dependency DAG + phase-aware `/reset` acceptance** (OpenAPI-absence is the invariant; runtime POST is 404 pre-P0-D, 503 post-P0-D). **(6)** P0-D drops the separately-governed **learning** family and uses **exact route-family boundary matching** (`path == p or path.startswith(p + "/")`) so `/api/v1/work` no longer over-matches `/api/v1/workflow`. **(7)** the **review record is committed alongside** this design; the IRP-precedent path is corrected to `docs/superpowers/specs/ops-app-role-boundary/IRP_OPUS_2026-07-01.md`; the audit-note path is qualified to the `apex-learning-lane` repo. rev1→rev4 history below.

**Revision — rev4 (2026-07-14).** Folds the final verification round: Codex HIGH — the `ON FUNCTIONS` default-priv revoke names only `anon`/`authenticated`, but Postgres grants `EXECUTE` on new functions to **PUBLIC** via a built-in default that `ALTER DEFAULT PRIVILEGES` cannot reliably strip (repo precedent `docs/superpowers/specs/ops-app-role-boundary/IRP_OPUS_2026-07-01.md`), so a future public SECURITY DEFINER function would be born callable by `anon`/`authenticated` via the PUBLIC grant. The 3 **known** write RPCs are fully closed (014 statement 2); the **future-function-PUBLIC** vector is not one-shot-closable in emergency P0 (a blanket `REVOKE … ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC` is too broad and would break legitimate callers) → reframed honestly and disclosed as a **standing-posture residual (§11.6)**, with a best-effort `PUBLIC` token added to the ADP function revokes. Plus doc nits: control-plane `conftest.py` needs an explicit `import os`; the composable-diff list adds mutation-seam `main.py` (P0-B + P0-D); the P0-B tests cross-reference the `PM_MUTATIONS_ENABLED` flag. rev1→rev3 history below.

**Revision — rev3 (2026-07-14).** Folds two focused cross-engine review rounds (3 adversarial Claude lenses + Codex gpt-5.5, read-only, grounded against live prod). rev2 fixed the rev1 CRITICAL SECURITY DEFINER RPC bypass + imports/MAINTAIN/asserts. **rev3 fixes what the rev2 re-review found against the live catalog:** (a) CRITICAL — the `supabase_admin` `ALTER DEFAULT PRIVILEGES` was bundled in the postgres-run transaction and would abort the *entire* migration (managed `postgres` is not a member of `supabase_admin`), so P0-C is **split by authority** (014 postgres-run primary + 015 supabase_admin-run secondary); (b) CRITICAL — P0-D's default-deny middleware would 503 the *existing* test suite in both apps, so P0-D now includes a **conftest `PM_MUTATIONS_ENABLED=true` default**; (c) HIGH — default-privilege prevention now also covers **functions** (`ON FUNCTIONS`), closing the born-EXECUTE-exposed RPC-bypass class; (d) P0-E drops the wrong-DB **learning** check and §11 discloses that control-plane readiness is truthfully `not_ready` in prod because **both `pm.idempotency_keys` and `work.*` are absent**.

**GATE_SHA (re-derived, not assumed):** `270ca6e16a9cd3cfdd0d64b67e4b6e247f24139f` (`origin/main`, clean; re-derived at rev5 2026-07-14 — unchanged).
**Branch / worktree:** `pm-ops/p0-containment-design` @ `/home/olares/code/apex/apex-pm-ops-p0` (isolated).
**Target production project:** Supabase `fxoyniqnrlkxfligbxmg` (PostgreSQL **17.6**; `postgres` is **not** superuser, `supabase_admin` is); deploy host = **Render**.

---

## 0. Why (grounded threat summary)

Two exposures are LIVE, unauthenticated, internet-reachable, unremediated (all verified read-only at GATE_SHA + live prod + Codex convergence):

- **C1 — unauth destructive `POST /reset`.** `health.py:21` mounts `POST /reset` with no auth; `memory_store.py:14` resolves `store` to `SupabaseStore` unless `SEAM_STORE_BACKEND=memory`; `render.yaml:22` sets `SEAM_STORE_BACKEND=postgres`; `supabase_store.py:560` `reset()` non-transactionally `DELETE`s 19 `seam.*` tables → partial destruction possible. Live OpenAPI advertises `/reset` with `security: NONE`. The current DB outage is accidental/reversible — **not a control**; it re-arms on connectivity repair. **Contain before repairing connectivity.**
- **C1b/High-3 — `public.{projects,scopes,tasks,apparatus}` write surface.** RLS off, 0 policies; on PG17 `anon`+`authenticated` each hold **8** privileges `arwdDxtm` (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, **MAINTAIN**). Data API live; `public` exposed; an active publishable key maps to role `anon`. **Additionally**, three `SECURITY DEFINER` functions owned by `postgres` — `approve_apparatus_completion`, `reject_apparatus_submission`, `submit_apparatus_for_review` — carry `EXECUTE` to `PUBLIC`/`anon`/`authenticated` and each `UPDATE public.apparatus` from caller-supplied UUIDs with no identity check → an **unauthenticated write path via PostgREST RPC that a table-ACL revoke does not close.** Write capability is **inferred** (reachability + effective grants + absent RLS + PostgREST verb/RPC semantics); **no mutating REST/RPC request was executed** ("INSERT/UPDATE/DELETE exposure", not "TRUNCATE through REST").

Supporting: C2 prototype auth (unsigned base64 tokens; missing-auth default `field_tech` actor; browser-minted token; unauthenticated `work`/ops routers; `HTTPBearer` declared-but-unenforced); H4 = readiness blindness **plus** a real (lazy-bound, rarely-firing) silent in-memory idempotency fallback over `pm.idempotency_keys`, **which does not exist in prod** (§11); tracer = **500 with a valid `task_id`** (422 only on missing `task_id`). Recorded, out of P0-C scope: a fourth role `apex_tcc_runtime` holds `arwd` on the 4 tables — a dedicated app-service role, **not** Data-API-reachable; the `012` precedent leaves it untouched, so P0-C's "no effective write" is scoped to the Data-API-reachable principals (`PUBLIC`/`anon`/`authenticated`).

---

## 1. Independence & gating matrix

| Action | Surface | Independent GO | Independently applied | Reversible via |
|---|---|---|---|---|
| **P0-A** | read-only evidence | `GO PM-OPS-P0-A READ-ONLY EVIDENCE` | n/a (read-only) | n/a |
| **P0-B** | mutation-seam app/deploy | `GO PM-OPS-P0-B RESET CONTAINMENT` | code deploy | revert commit / env |
| **P0-C** | Supabase prod grants + fn EXECUTE | `GO PM-OPS-P0-C PUBLIC WRITE REVOCATION` | **014 as postgres (atomic, primary); 015 as supabase_admin (separate, secondary)** | paired `.rollback.sql` per file |
| **P0-D** | both apps ingress + test conftest | `GO PM-OPS-P0-D MUTATION INGRESS CLOSURE` | code deploy + env | flip `PM_MUTATIONS_ENABLED=true` |
| **P0-E** | both apps readiness | `GO PM-OPS-P0-E READINESS` | code deploy | revert commit |
| **P1** | operations-web + APIs identity | separate P1 GO (later) | separate packet | n/a |

**Dependency DAG (replaces the earlier "no cross-action dependency" claim).** Every action is independently **gated** (its own operator GO) and independently **applied** (never one combined production transaction), but the actions are **not** all mutually order-independent:

- **P0-A → P0-B, P0-C.** Both consume P0-A's snapshot: P0-C's rollbacks are generated from the captured per-grantee/per-grantor ACL, and P0-B relies on the captured `/reset` state. Run P0-A first.
- **P0-B → (external) mutation-seam connectivity repair.** P0-B must be applied **before** connectivity is restored, or `/reset` re-arms.
- **P0-C:** `014` (postgres, urgent primary) is independent of `015` (supabase_admin, secondary).
- **P0-D, P0-E:** each independently applicable. **P0-D interacts with P0-B's acceptance** (below) but requires no ordering.
- **P1** is never a prerequisite for any P0 action.

**Phase-aware `/reset` acceptance (P0-B × P0-D).** The **durable invariant** is that `/reset` is **absent from the deployed OpenAPI `paths`** (verified via `GET /openapi.json`) — true whenever P0-B is applied, regardless of P0-D. The **runtime POST status is phase-dependent**: **404** when P0-B is applied and P0-D is not (route unmounted); **503** once P0-D is also live (the default-deny mutation gate preempts routing). Acceptance asserts OpenAPI-absence unconditionally and selects 404-or-503 by which actions are live — it never asserts a bare 404 in a phase where P0-D is active.

Files touched by two actions are given as **composable diffs** (not full-file replacements): mutation-seam `health.py` (P0-B + P0-E), mutation-seam `main.py` (P0-B + P0-D), and control-plane `main.py` (P0-D + P0-E). **Within P0-C, `014` (the urgent primary containment) does NOT depend on `015`'s `supabase_admin` authority.** No combined production transaction; P1 not a prerequisite.

---

## 2. P0-A — Read-only evidence preservation

**Objective.** Capture approved pre-change evidence. No mutation/deploy/secret/connectivity change. Runs as a **single guarded `REPEATABLE READ, READ ONLY` transaction** (project-fingerprint + read-only guard; fails closed on the wrong cluster); enumeration uses **effective-role closure** (fixed principals x all privileges + the anon/authenticated membership closure) and **fail-closed-leaning** SECURITY DEFINER discovery (name-reference + dynamic-SQL as the reliable primary, `pg_depend` supplementary; residual indirect-write / non-public-schema gap disclosed in the query (e) note). Stop with hashes, paths, results, drift.

**Deliverable.** `apps/mutation-seam/scripts/pm_ops_p0/preserve_evidence.py` (read-only; house style of `scripts/smoke_deployed_mutation_seam.py`) + the SQL below → custody `/home/olares/custody/pm-ops-p0/<UTC>/` (0700 dir, 0400 files) + SHA-256 manifest.

**Evidence set (each hashed + path-recorded):** (1) deployed OpenAPI both hosts + version/SHA; (2) `/reset` route + security state; (3) **effective privileges for the fixed Data-API principal set (`anon`/`authenticated`/`public`/`apex_tcc_runtime`) across all table privileges, plus the `anon`/`authenticated` membership closure** and per-table RLS; (4) **every `SECURITY DEFINER` function in `public` that depends on (via `pg_depend`), references by name, OR uses dynamic SQL touching the 4 tables — fail-closed `in_scope` flag**, with args/owner/EXECUTE grants (incl. PUBLIC); (5) counts (no row bodies); (6) `pg_default_acl` for schema `public` **for both `objtype='r'` (tables) and `'f'` (functions)**, per grantor; (7) active backend classification (inferred; record source); (8) Render `POST /reset` access logs (operator-captured); (9) rollback inputs (exact per-grantee ACL + per-grantor default ACL, so both rollbacks are generated from the snapshot).

**Read-only SQL snapshot (P0-A):**
```sql
-- pm-ops-p0-A : ACL + RLS + counts + default-priv (tables+functions) + effective-role closure
-- + FAIL-CLOSED SECURITY DEFINER discovery. Single guarded READ-ONLY transaction.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY;

-- (guard) fail closed on the wrong cluster/DB or a writable session: assert read-only + target fingerprint.
DO $$
BEGIN
  IF NOT (SELECT setting::bool FROM pg_settings WHERE name = 'transaction_read_only') THEN
    RAISE EXCEPTION 'P0-A refused: transaction is not READ ONLY';
  END IF;
  IF to_regclass('public.projects') IS NULL OR to_regclass('public.scopes') IS NULL
     OR to_regclass('public.tasks') IS NULL OR to_regclass('public.apparatus') IS NULL
     OR to_regproc('public.approve_apparatus_completion') IS NULL THEN
    RAISE EXCEPTION 'P0-A refused: target fingerprint absent (wrong database/project?) — expected the 4 PM tables + apparatus RPCs';
  END IF;
END $$;

-- (a) exact per-grantee table ACL (rollback-input source; literal ACL entries preserved)
select c.relname, c.relrowsecurity as rls_enabled,
       (select count(*) from pg_policy p where p.polrelid=c.oid) as policies,
       coalesce(array_to_string(c.relacl, E'\n'), '(default/no explicit acl)') as relacl
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relname in ('projects','scopes','tasks','apparatus') order by c.relname;

-- (b) EFFECTIVE privilege for the FIXED Data-API principal set across ALL table privileges,
--     driven by principals x privileges (NOT by ACL entries) so membership-inherited access is captured.
select c.relname, pr.role as principal, pv.priv as privilege_type,
       has_table_privilege(pr.role, c.oid, pv.priv) as effective
from pg_class c join pg_namespace n on n.oid=c.relnamespace
cross join (values ('anon'),('authenticated'),('public'),('apex_tcc_runtime')) as pr(role)
cross join (values ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER'),('MAINTAIN')) as pv(priv)
where n.nspname='public' and c.relname in ('projects','scopes','tasks','apparatus')
order by c.relname, principal, privilege_type;

-- (b2) role-membership closure of anon/authenticated (which roles inherit them) — completes effective-access evidence
with recursive closure(target, member) as (
    select rolname, rolname from pg_roles where rolname in ('anon','authenticated')
  union
    select c.target, r.rolname
    from closure c
    join pg_roles gr on gr.rolname = c.member
    join pg_auth_members m on m.roleid = gr.oid
    join pg_roles r on r.oid = m.member
)
select target as target_role, array_agg(distinct member order by member) as members_inheriting
from closure group by target order by target;

-- (c) counts only
select 'projects' rel, count(*) n from public.projects
union all select 'scopes', count(*) from public.scopes
union all select 'tasks', count(*) from public.tasks
union all select 'apparatus', count(*) from public.apparatus;

-- (d) default privileges in schema public — BOTH objtypes r (tables) and f (functions), per grantor
select pg_get_userbyid(d.defaclrole) as grantor, d.defaclobjtype as objtype, array_to_string(d.defaclacl, E'\n') as default_acl
from pg_default_acl d join pg_namespace n on n.oid=d.defaclnamespace
where n.nspname='public' and d.defaclobjtype in ('r','f') order by grantor, objtype;

-- (e) SECURITY DEFINER discovery. RELIABLE primary signals: name_refs_targets (regex on the function
--     definition) and has_dynamic_sql (EXECUTE present -> unresolvable target -> fail CLOSED).
--     depends_on_targets (pg_depend) is a SUPPLEMENTARY signal that is INERT for PL/pgSQL bodies (Postgres
--     records no dependency edge from a plpgsql body to referenced tables), so it does NOT fire for the 3
--     plpgsql apparatus RPCs -- they are caught by name_refs_targets. in_scope_failclosed = OR of the three.
--     Residual coverage gap (disclosed): a SECURITY DEFINER function writing a target only INDIRECTLY (via a
--     helper, with no name token and no EXECUTE), or a secdef writer in ANOTHER Data-API-exposed schema
--     (outside this public filter), is not flagged. P0-A output is operator-reviewed EVIDENCE, not an
--     automated gate -- treat any unexpected secdef function as in-scope pending review.
with tgt as (
  select oid from pg_class
  where relnamespace = 'public'::regnamespace and relname in ('projects','scopes','tasks','apparatus')
),
dep_fns as (
  select distinct d.objid as fnoid
  from pg_depend d join tgt on d.refobjid = tgt.oid
  where d.classid = 'pg_proc'::regclass and d.refclassid = 'pg_class'::regclass  -- guard same-numbered OIDs
)
select p.proname, pg_get_function_identity_arguments(p.oid) as args, pg_get_userbyid(p.proowner) as owner,
       has_function_privilege('public',p.oid,'EXECUTE') as public_exec,
       has_function_privilege('anon',p.oid,'EXECUTE') as anon_exec,
       has_function_privilege('authenticated',p.oid,'EXECUTE') as auth_exec,
       (p.oid in (select fnoid from dep_fns)) as depends_on_targets,
       (pg_get_functiondef(p.oid) ~* '\y(projects|scopes|tasks|apparatus)\y') as name_refs_targets,
       (pg_get_functiondef(p.oid) ~* '\yexecute\y') as has_dynamic_sql,
       ( p.oid in (select fnoid from dep_fns)
         or pg_get_functiondef(p.oid) ~* '\y(projects|scopes|tasks|apparatus)\y'
         or pg_get_functiondef(p.oid) ~* '\yexecute\y' ) as in_scope_failclosed
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.prosecdef
order by in_scope_failclosed desc, p.proname;
COMMIT;
```

**Baseline observed this session (re-captured authoritatively at GO):** 4 tables `rls_enabled=false`/`policies=0`; `anon`+`authenticated`+`apex_tcc_runtime` hold writes (anon/auth = full `arwdDxtm` incl. MAINTAIN; PUBLIC no direct table grant); default ACLs from grantors **`postgres`** and **`supabase_admin`** grant `anon`/`authenticated` full privileges on future public **tables AND `EXECUTE` on future functions**; query (e) is expected to flag exactly the 3 apparatus functions `in_scope_failclosed=true` (owner postgres, `public_exec`/`anon_exec`/`auth_exec` true), **caught via `name_refs_targets=true`** — with `depends_on_targets=false` **expected** (the RPCs are PL/pgSQL, whose bodies `pg_depend` does not track) and `has_dynamic_sql=false` for all in-scope rows. Any `in_scope_failclosed=true` row with `has_dynamic_sql=true` (an unresolvable dynamic-SQL SECURITY DEFINER function), or any secdef function beyond the known 3, is a NEW finding requiring re-review before P0-C.

**Stop condition.** Stop with hashes/paths/results + drift (drift → re-review before P0-C).

---

## 3. P0-B — `/reset` removal + fail-closed guard + test-only enablement

*(Unchanged from rev2; verified clean by re-review.)*

**Objective.** `/reset` absent in prod OpenAPI (per §1 phase-aware acceptance); `SupabaseStore.reset()` **unconditionally refuses in every environment**; reset/reseed survives only as an explicit non-production, memory-backed (`MemoryStore`), opt-in capability.

**Change 1 — `apps/mutation-seam/app/routers/health.py`** (composable additions, NOT a full-file replacement — P0-E also edits this file): add `import os`, keep `health_check`, delete the current unconditional `@router.post("/reset")` (lines 21-29), add:
```python
def test_reset_enabled() -> bool:
    """Mounted ONLY when ALL hold: not production, in-memory store backend, explicit opt-in. Default = disabled."""
    return (os.getenv("APP_ENV", "production") != "production"
            and os.getenv("SEAM_STORE_BACKEND") == "memory"
            and os.getenv("SEAM_TEST_RESET_ENABLED") == "true")

reset_router = APIRouter(tags=["health"])  # registered by main.py ONLY when test_reset_enabled()

@reset_router.post("/reset")
async def reset_store():
    """TEST-ONLY. Never mounted in production."""
    store.reset()
    return {"status": "reset", "message": "Store reset to seed data"}
```

**Change 2 — `apps/mutation-seam/app/main.py`** (mirror the `_ops_intake_enabled()` gating precedent):
```python
app.include_router(health.router)
if health.test_reset_enabled():          # TEST-ONLY: never true in production
    app.include_router(health.reset_router)
```

**Change 3 — `apps/mutation-seam/app/db/supabase_store.py` `reset()`** (`supabase_store.py:560`; **unconditional refusal** — the destructive Postgres reset path is removed entirely, in every environment):
```python
def reset(self):
    # Destructive reset/reseed is a TEST-ONLY capability and exists ONLY on MemoryStore
    # (app/db/memory_store_original.py:61). SupabaseStore targets PostgreSQL and must NEVER
    # destructively reset, in ANY environment -> refuse unconditionally.
    raise RuntimeError(
        "SupabaseStore.reset() is permanently disabled: destructive reset/reseed is available only via "
        "MemoryStore (SEAM_STORE_BACKEND=memory). SupabaseStore never resets Postgres."
    )
    # (the prior truncate-in-FK-safe-order + reseed body is DELETED — unreachable and intentionally removed)
```
The test-only `/reset` route (Changes 1-2) is mounted **only** when `SEAM_STORE_BACKEND=memory`, so `store` is a `MemoryStore` instance and `store.reset()` binds to `MemoryStore.reset()` — the memory path is unaffected. This change removes only the *Postgres* destruction path.

**Preconditions.** P0-A captured; prod confirms `APP_ENV=production`, `SEAM_STORE_BACKEND=postgres`, no `SEAM_TEST_RESET_ENABLED`. **Rollback.** Revert the P0-B commit.
**OpenAPI acceptance (GET-only):** durable invariant — deployed OpenAPI `paths` excludes `/reset`. Runtime `POST /reset` → **404** (P0-B applied, P0-D not) or **503** (P0-D also live), per the §1 phase-aware acceptance.
**Negative tests (pytest, subprocess isolation — the mount is decided once at import; mirror `test_ops_route_mount_gate.py::test_recognition_router_host_gated_subprocess`; each subprocess env must carry `PM_MUTATIONS_ENABLED=true` per §5 so the `/reset` POST is not masked as 503 once P0-D is live):** `test_reset_absent_in_production` (prod env → absent + 404); `test_reset_mounted_only_in_memory_harness` (test+memory+opt-in → present + 200); `test_supabase_reset_always_raises` (in-process; `SupabaseStore.reset()` raises in EVERY env — including non-production with `SEAM_TEST_RESET_ENABLED=true` — before any DB call); import-smoke subprocess (`from app.main import app` under prod env exits 0).
**Sequencing.** Deploy P0-B **before** any mutation-seam connectivity repair.
**Dev-tooling impact (disclosed — rev5 review).** The dev-only persisted-mode validation harness (`run_persisted_validation.py` → `validate.py`, which POSTs `/reset` against the *persisted* backend to reseed between scenarios) breaks under P0-B: in persisted mode `test_reset_enabled()` is false, so `reset_router` is unmounted and `POST /reset` → 404 (the harness aborts, or silently runs against a non-reset DB). This is an **intended** consequence of removing the Postgres `/reset` path — the harness must be updated to reseed via a direct DB helper (or a no-reset flow). **No production impact (dev tooling only).**

---

## 4. P0-C — Atomic revocation of Data-API write privileges (split by authority)

**Objective (immediate containment claim).** `PUBLIC`/`anon`/`authenticated` hold **no effective write** on the 4 tables **and no EXECUTE** on the 3 apparatus RPCs — the two live exposures; and the postgres-grantor **named-role** default privileges no longer birth write/EXECUTE-exposed tables/functions; `SELECT` preserved. No schema relocation, no RLS redesign. **Forward-function PUBLIC EXECUTE posture is explicitly NOT claimed here** — it is a separately measured finish line (§11.6) that does **not** gate urgent `014`.

**Why split.** The forward migration must run as **`postgres`** (owner/grantor of the 4 tables + 3 functions — the urgent revokes). But `ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin …` requires **`supabase_admin`** authority, which managed `postgres` does **not** hold (live-verified: `postgres` is not a member of `supabase_admin`; not superuser). Bundling both in one transaction means the `supabase_admin` statement errors and **rolls back the urgent revokes**. So:
- **`014` (postgres-run, atomic — PRIMARY, closes the two live exposures):** table write REVOKE + RPC EXECUTE REVOKE + `postgres`-grantor default-priv (tables **and** functions) + assertions. Live-confirmed to apply cleanly as `postgres` (owner of all objects; no `WITH GRANT OPTION`, so no CASCADE).
- **`015` (supabase_admin-run, separate — SECONDARY, defense-in-depth):** `supabase_admin`-grantor default-priv (tables + functions) + assertion. Requires a `supabase_admin` session. **014 does not depend on 015.** In practice new public objects in this project are created by `postgres` migrations (covered by 014's postgres-grantor default-priv); 015 covers platform-created objects and is best-effort where a `supabase_admin` path exists.

**Convention.** Mirrors `apps/control-plane-api/supabase/migrations/20260710_000012_harden_mcp_public_exposure_core.sql`. Home: `apps/control-plane-api/supabase/migrations/`. Apply via **raw `psql -v ON_ERROR_STOP=1 -f`, one file per invocation** (embedded `BEGIN/COMMIT` owns the txn). Prove both on a throwaway Supabase branch first.

**Forward — `20260714_000014_contain_public_pm_write_surface.sql` (run as postgres):**
```sql
-- 20260714_000014 — PM/Ops P0-C PRIMARY: close anon/authenticated Data-API WRITE surface on the 4 public PM tables
-- AND the 3 SECURITY DEFINER apparatus RPCs; prevent postgres-grantor born-exposed future tables+functions.
-- SELECT preserved. apex_tcc_runtime untouched. APPLY as postgres, raw psql -v ON_ERROR_STOP=1 -f. Idempotent.
BEGIN;
DO $$ BEGIN IF current_user <> 'postgres' THEN RAISE EXCEPTION 'run 014 as postgres (owner/grantor of the 4 tables + 3 functions)'; END IF; END $$;

-- 1) table write REVOKE (incl. PG17 MAINTAIN); SELECT preserved
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON
    public.projects, public.scopes, public.tasks, public.apparatus FROM PUBLIC, anon, authenticated;

-- 2) close the SECURITY DEFINER RPC write path (runs as owner postgres, so table-REVOKE alone does not stop it)
REVOKE EXECUTE ON FUNCTION
    public.approve_apparatus_completion(uuid, uuid, numeric, public.apparatus_assessment, text),
    public.reject_apparatus_submission(uuid, uuid, text),
    public.submit_apparatus_for_review(uuid, uuid, numeric, public.apparatus_assessment, numeric, text, text)
FROM PUBLIC, anon, authenticated;

-- 3) postgres-grantor NAMED-ROLE default-priv prevention — TABLES and FUNCTIONS.
--    Revokes the anon/authenticated default that live pg_default_acl (objtypes 'r' and 'f') actually carries.
--    Scope note: the built-in PUBLIC EXECUTE on NEW functions is a Postgres platform default that ADP cannot
--    reliably strip, so it is deliberately NOT addressed here (no ineffective best-effort token). The 3 KNOWN
--    write RPCs are fully closed by stmt 2; forward-function PUBLIC posture is a separately measured finish
--    line (§11.6, docs/superpowers/specs/ops-app-role-boundary/IRP_OPUS_2026-07-01.md) that does NOT block 014.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated;

-- 4a) assert: no effective write on the 4 tables for anon/authenticated (all 7 revoked verbs)
DO $$
DECLARE obj text; priv text; bad text[] := '{}';
BEGIN
  FOREACH obj IN ARRAY ARRAY['public.projects','public.scopes','public.tasks','public.apparatus'] LOOP
    FOREACH priv IN ARRAY ARRAY['INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'] LOOP
      IF has_table_privilege('anon', obj, priv)          THEN bad := bad || ('anon:'||obj||':'||priv); END IF;
      IF has_table_privilege('authenticated', obj, priv) THEN bad := bad || ('authenticated:'||obj||':'||priv); END IF;
    END LOOP;
  END LOOP;
  IF array_length(bad,1) IS NOT NULL THEN RAISE EXCEPTION 'P0-C(014) FAILED (tables): write retained: %', bad; END IF;
END $$;

-- 4b) assert: no EXECUTE on the 3 RPCs for anon/authenticated (has_function_privilege sees PUBLIC too)
DO $$
DECLARE fn text; g text; bad text[] := '{}';
BEGIN
  FOREACH fn IN ARRAY ARRAY[
    'public.approve_apparatus_completion(uuid, uuid, numeric, public.apparatus_assessment, text)',
    'public.reject_apparatus_submission(uuid, uuid, text)',
    'public.submit_apparatus_for_review(uuid, uuid, numeric, public.apparatus_assessment, numeric, text, text)'] LOOP
    FOREACH g IN ARRAY ARRAY['anon','authenticated'] LOOP
      IF has_function_privilege(g, fn, 'EXECUTE') THEN bad := bad || (g||':'||fn); END IF;
    END LOOP;
  END LOOP;
  IF array_length(bad,1) IS NOT NULL THEN RAISE EXCEPTION 'P0-C(014) FAILED (rpc): EXECUTE retained: %', bad; END IF;
END $$;

-- 4c) assert (guard over-revocation): SELECT preserved for BOTH anon and authenticated
DO $$
DECLARE obj text; g text;
BEGIN
  FOREACH obj IN ARRAY ARRAY['public.projects','public.scopes','public.tasks','public.apparatus'] LOOP
    FOREACH g IN ARRAY ARRAY['anon','authenticated'] LOOP
      IF NOT has_table_privilege(g, obj, 'SELECT') THEN RAISE EXCEPTION 'P0-C(014) FAILED: % SELECT revoked on %', g, obj; END IF;
    END LOOP;
  END LOOP;
END $$;

-- 5) assert: postgres-grantor NAMED-role (anon/authenticated) default privileges no longer expose future TABLES/FUNCTIONS.
--    (Does NOT assert the PUBLIC-inherited future-function EXECUTE built-in — a Postgres platform limitation tracked as §11.6.)
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(d.defaclobjtype||'/'||pg_get_userbyid(a.grantee)||':'||a.privilege_type, '; ') INTO bad
  FROM pg_default_acl d JOIN pg_namespace n ON n.oid=d.defaclnamespace CROSS JOIN LATERAL aclexplode(d.defaclacl) a
  WHERE n.nspname='public' AND d.defaclrole = 'postgres'::regrole AND d.defaclobjtype IN ('r','f')
    AND pg_get_userbyid(a.grantee) IN ('anon','authenticated')
    AND ( (d.defaclobjtype='r' AND a.privilege_type IN ('INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'))
       OR (d.defaclobjtype='f' AND a.privilege_type='EXECUTE') );
  IF bad IS NOT NULL THEN RAISE EXCEPTION 'P0-C(014) FAILED: postgres default privileges still expose future objects: %', bad; END IF;
END $$;
COMMIT;
```

**Forward — `20260714_000015_contain_public_pm_default_priv_supabase_admin.sql` (run as supabase_admin, SEPARATE invocation):**
```sql
-- 20260714_000015 — PM/Ops P0-C SECONDARY (defense-in-depth): close the supabase_admin-grantor default privileges
-- so future public tables/functions are not born exposed to anon/authenticated. REQUIRES supabase_admin authority
-- (managed postgres CANNOT run this). PRIMARY containment (014) does NOT depend on this file.
BEGIN;
DO $$ BEGIN IF current_user <> 'supabase_admin' THEN RAISE EXCEPTION 'run 015 as supabase_admin (grantor of these default privileges)'; END IF; END $$;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public
    REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated;  -- named roles only; PUBLIC posture = §11.6 finish line
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(d.defaclobjtype||'/'||pg_get_userbyid(a.grantee)||':'||a.privilege_type, '; ') INTO bad
  FROM pg_default_acl d JOIN pg_namespace n ON n.oid=d.defaclnamespace CROSS JOIN LATERAL aclexplode(d.defaclacl) a
  WHERE n.nspname='public' AND d.defaclrole = 'supabase_admin'::regrole AND d.defaclobjtype IN ('r','f')
    AND pg_get_userbyid(a.grantee) IN ('anon','authenticated')
    AND ( (d.defaclobjtype='r' AND a.privilege_type IN ('INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'))
       OR (d.defaclobjtype='f' AND a.privilege_type='EXECUTE') );
  IF bad IS NOT NULL THEN RAISE EXCEPTION 'P0-C(015) FAILED: supabase_admin default privileges still expose future objects: %', bad; END IF;
END $$;
COMMIT;
```
*(If no `supabase_admin` session is available on managed Supabase, 015 cannot run; record that as an operator-accepted residual — 014 fully closes all EXISTING exposures and the realistic postgres-created future-object vector; the residual is only platform-created future objects under the supabase_admin grantor.)*

**Rollbacks (operator-gated).** `014.rollback.sql` (run as postgres) restores EXACTLY the table write verbs (incl. MAINTAIN) + the 3 RPC EXECUTEs + the postgres-grantor default privileges, **generated from the P0-A per-grantee/per-grantor snapshot** (not a blanket static grant), to anon/authenticated only (PUBLIC had no direct table grant; it did hold direct RPC EXECUTE → restore that). `015.rollback.sql` (run as supabase_admin) restores the supabase_admin-grantor default privileges. Each guards its `current_user`; fail-closed for objects born after apply.

**Preconditions.** P0-A ACL + default-ACL (tables+functions) + SECURITY DEFINER snapshots captured; rollbacks generated; both migrations proven on a Supabase branch.
**Acceptance.** 014: table write false + RPC EXECUTE false for anon+authenticated (asserted); SELECT preserved (asserted); postgres-grantor **named-role** default-priv closed for tables+functions (asserted; PUBLIC future-function EXECUTE explicitly out of the 014 claim per §11.6); applies cleanly as postgres. 015: supabase_admin-grantor default-priv closed (asserted) OR recorded as residual if no authority path. Rollbacks captured (snapshot-derived). No schema relocation/RLS redesign. Advisors re-run on the 4 objects + the 3 functions.
**Post-change verification (read-only).** Re-run P0-A (a),(b),(d),(e); advisors; optional single read-only REST `GET .../rest/v1/projects?select=id&limit=1` still 200. Do not issue a write/RPC to "prove" closure.

---

## 5. P0-D — Temporary closure of unauthenticated PM mutation ingress

**Objective.** Temporarily block unauthenticated PM mutation verbs across both apps' PM route families, reversibly, without permanent identity (P1). Default (flag unset) = **fail-closed**. The separately-governed **learning** family (`/api/v1/learning`) is **excluded** — its ingress posture is decided under the learning lane, not P0-D.

**Mechanism.** A minimal ASGI middleware gated on `PM_MUTATIONS_ENABLED` (default disabled). **Register the gate BEFORE `app.add_middleware(CORSMiddleware, …)` in source order** (Starlette adds inner-first: last-added = outermost → CORS wraps the 503, so it carries CORS headers). Place the `@app.middleware("http")` block immediately after `app = FastAPI(...)`, above the CORS `add_middleware` call.

**mutation-seam — `apps/mutation-seam/app/main.py`** (add `import os` + `from fastapi.responses import JSONResponse`; whole app is PM):
```python
_PM_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
@app.middleware("http")
async def _pm_mutation_gate(request, call_next):
    if request.method in _PM_MUTATING_METHODS and os.getenv("PM_MUTATIONS_ENABLED") != "true":
        return JSONResponse(status_code=503, content={"detail": "PM mutations temporarily disabled (containment P0-D)."})
    return await call_next(request)
# ... app.add_middleware(CORSMiddleware, ...) BELOW this block ...
```

**control-plane — `apps/control-plane-api/main.py`** (add `JSONResponse` to `from fastapi.responses import FileResponse` → `FileResponse, JSONResponse`; scope to PM route families with **exact boundary matching**; **learning is separately governed and excluded**; **composable diff — P0-E also edits this file**):
```python
_PM_MUTATION_PREFIXES = ("/api/v1/work", "/api/v1/ops/intake", "/api/v1/ops/recognition")
_PM_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

def _is_pm_mutation_path(path: str) -> bool:
    # exact route-family boundary: matches "/api/v1/work" and "/api/v1/work/..", NOT "/api/v1/workflow".
    # learning (/api/v1/learning) is separately governed and intentionally NOT included here.
    return any(path == p or path.startswith(p + "/") for p in _PM_MUTATION_PREFIXES)

@app.middleware("http")
async def _pm_mutation_gate(request, call_next):
    if (request.method in _PM_MUTATING_METHODS and _is_pm_mutation_path(request.url.path)
            and os.getenv("PM_MUTATIONS_ENABLED") != "true"):
        return JSONResponse(status_code=503, content={"detail": "PM mutations temporarily disabled (containment P0-D)."})
    return await call_next(request)
# ... registered ABOVE the CORS add_middleware call (control-plane main.py:78) ...
```

**Test-suite deliverable (REQUIRED — the default-deny gate would otherwise 503 the entire existing suite in both apps).** Add, at the very top of each conftest **before** the app is imported:
- `apps/mutation-seam/tests/conftest.py`: `os.environ.setdefault("PM_MUTATIONS_ENABLED", "true")` (before `from app.main import app`).
- `apps/control-plane-api/tests/conftest.py`: **add `import os`** (this file does not currently import it), then `os.environ.setdefault("PM_MUTATIONS_ENABLED", "true")` (pytest loads this conftest before any test module's `from main import app`, so a top-of-file setdefault correctly precedes all app imports).
This also restores `test_ops_route_mount_gate.py::test_recognition_router_host_gated_subprocess` (which asserts 404 on an unmounted route — the gate would otherwise mask it as 503); its subprocess env must inherit/set `PM_MUTATIONS_ENABLED=true`. Without this deliverable, merging P0-D turns CI red across both apps.

**Preconditions.** None — order-independent. **Rollback.** `PM_MUTATIONS_ENABLED=true` or revert.
**Interaction note.** With P0-D live, the P0-B test-only `/reset` (a POST) is also gated by the mutation-seam blanket gate → the reset harness additionally needs `PM_MUTATIONS_ENABLED=true` (fails closed; documented).
**Negative tests + verification.** The new P0-D negative tests explicitly control the flag (unset → assert 503; `=true` → passthrough), so they do not depend on the conftest default. Plus a pure-unit `test_pm_gate_path_boundary` on `_is_pm_mutation_path`: `/api/v1/work` and `/api/v1/work/tasks` → True; `/api/v1/workflow` and `/api/v1/learning/x` → False (exact route-family boundary — no over-match, learning excluded). Deployed: `POST` (empty body) to one route per gated PM family → 503; a `POST` to a learning route is **not** gated by P0-D; GETs unchanged; verify the 503 carries `Access-Control-Allow-Origin` via a cross-origin `fetch()`.
**Out of scope.** No JWT/session/capability/actor derivation — that is **P1**.

---

## 6. P0-E — Contract-aware readiness

**Objective.** Readiness fails (**503**) when any **mounted** production domain's required schema, **serving-role identity/contract/permissions** (probed via the actual `OPS_API_DSN`/`OPS_INTAKE_WRITER_DSN`), work table, durable-idempotency backend, or `pm.idempotency_keys` is unavailable. Liveness (`/health`, `/health/live`) stays static so Render's `healthCheckPath: /health` does not cycle the process.

**control-plane — replace `/health/ready`** (`apps/control-plane-api/main.py:~404`; **add `Response`**: `from fastapi import Depends, FastAPI, HTTPException, Request, Response`; **composable diff — P0-D also edits this file's imports/top**). Current behavior: 200-always, probes only `vw_trip_unit_cascade`.
```python
@app.get("/health/ready")
def health_ready(response: Response):
    """Contract-aware readiness: verify each MOUNTED domain's required contract AND, for ops, the ACTUAL
    serving-role DSN identity/contract/permissions; 503 when any is unavailable."""
    import os
    import psycopg
    from config import engine
    from services.work.idempotency import idempotency_cache
    checks: dict[str, dict] = {}; ok = True
    def _sql(name: str, sql: str) -> None:
        nonlocal ok
        try:
            with engine.connect() as conn: row = conn.execute(text(sql)).fetchone()
            passed = bool(row and row[0]); checks[name] = {"ok": passed}; ok = ok and passed
        except Exception as exc:
            checks[name] = {"ok": False, "error": str(exc)}; ok = False
    # control-plane's OWN DB (config.engine): connectivity, work tables, PM idempotency durability
    _sql("database", "SELECT 1")
    _sql("work_tables", "SELECT to_regclass('work.projects') IS NOT NULL AND to_regclass('work.tasks') IS NOT NULL "
                        "AND to_regclass('work.work_packages') IS NOT NULL")
    checks["pm_idempotency_backend"] = {"ok": idempotency_cache.backend_kind() == "durable"}
    ok = ok and checks["pm_idempotency_backend"]["ok"]
    _sql("pm_idempotency_keys", "SELECT to_regclass('pm.idempotency_keys') IS NOT NULL")
    # ops: probe the ACTUAL serving-role DSNs (psycopg, as the routers do) -> identity + contract + forbidden priv.
    def _probe_role(name: str, dsn_env: str, expected_role: str, must_read: str) -> None:
        nonlocal ok
        dsn = os.getenv(dsn_env)
        if not dsn:
            checks[name] = {"ok": False, "error": f"{dsn_env} unset"}; ok = False; return
        try:
            with psycopg.connect(dsn, connect_timeout=5) as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT current_user, "
                    "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user), "
                    "has_schema_privilege(current_user, 'ops', 'USAGE'), "
                    "has_table_privilege(current_user, %s, 'SELECT'), "
                    "has_table_privilege(current_user, 'public.apparatus', 'UPDATE')",
                    (must_read,))
                who, is_super, ops_usage, can_read, writes_public = cur.fetchone()
            passed = (who == expected_role and not is_super and ops_usage and can_read and not writes_public)
            checks[name] = {"ok": passed, "current_user": who, "superuser": is_super,
                            "ops_usage": ops_usage, "contract_read": can_read, "forbidden_public_write": writes_public}
            ok = ok and passed
        except Exception as exc:
            checks[name] = {"ok": False, "error": str(exc)}; ok = False
    # mounted only when both role DSNs are set (mirrors _ops_intake_enabled()). Per-role LEAST-PRIVILEGE
    # contract (grounded vs the 012 ops role boundary + live ops_dev): ops_api reads the recognition worklist
    # VIEW; ops_intake_writer reads its intake_runs table. NEITHER login role may SELECT ops.persons (that
    # grant is ops_fn_owner-only), so probing ops.persons would FALSE-503 a healthy, correctly-provisioned
    # service AND tempt a boundary breach to "green" it. Use each role's actual granted object.
    if _ops_intake_enabled():
        _probe_role("ops_api_dsn", "OPS_API_DSN", "ops_api", "ops.v_completion_recognition_worklist")
        _probe_role("ops_intake_writer_dsn", "OPS_INTAKE_WRITER_DSN", "ops_intake_writer", "ops.intake_runs")
    # learning lives in a SEPARATE database (its own host-only DSN); a correct learning readiness probe needs
    # its own DSN-bound connection and is deferred with the learning lane (not checked here).
    response.status_code = 200 if ok else 503
    return {"status": "ready" if ok else "not_ready", "checks": checks}
```

**mutation-seam — add `/health/ready`** to `apps/mutation-seam/app/routers/health.py` (**add `Response`**: `from fastapi import APIRouter, Response`; composes with §3 additions — an addition, not a full-file replace):
```python
@router.get("/health/ready")
async def health_ready(response: Response):
    checks: dict[str, dict] = {}; ok = True
    try:
        from app.db.supabase_store import _conn_get
        conn = _conn_get()
        with conn.cursor() as cur:
            for tbl in ("seam.projects", "seam.tasks", "seam.apparatus"):
                cur.execute("SELECT to_regclass(%s) IS NOT NULL", (tbl,))
                present = bool(cur.fetchone()[0]); checks[tbl] = {"ok": present}; ok = ok and present
    except Exception as exc:
        checks["database"] = {"ok": False, "error": str(exc)}; ok = False
    response.status_code = 200 if ok else 503
    return {"status": "ready" if ok else "not_ready", "checks": checks}
```

**Behavior-change note.** control-plane `/health/ready` currently returns **200-always**; P0-E makes it **503 on not-ready**. Liveness paths unchanged (remain the Render health-check), so a 503 readiness does **not** cycle the service. The ops probes additionally verify each mounted serving role authenticates as its expected identity (`ops_api` / `ops_intake_writer`), holds its **least-privilege** read contract (`ops` schema `USAGE` + `SELECT` on `ops.v_completion_recognition_worklist` for `ops_api`, `ops.intake_runs` for `ops_intake_writer` — **not** `ops.persons`, which is `ops_fn_owner`-only; a `ops.persons` check would false-503 a healthy service), and lacks a forbidden privilege (not superuser; no `UPDATE` on `public.apparatus`) — so a misconfigured DSN or an over-granted serving role also (correctly) reports not_ready. (Each readiness call opens two short-lived psycopg connections at `connect_timeout=5`; on a degraded DB the two connects can sum to ~10s — repoint any tight-timeout external monitor to `/health`.) **Consequence (see §11):** with `pm.idempotency_keys` **and** `work.*` both absent in prod today, P0-E control-plane readiness will correctly report **not_ready** — a truthful signal that the control-plane PM/work backend is not fully provisioned in prod (consistent with High-1's empty `work` schema and High-2's 500s). If any external monitor treats `/health/ready` non-200 as hard-down, repoint it to `/health` before P0-E.

**Preconditions.** None. **Rollback.** Revert. **Verification (GET-only).** `/health` → 200 both apps; `/health/ready` → 200 when contracts present, 503 with a per-check body otherwise. **Import-smoke test** (both apps): subprocess `from <module> import app` under prod env exits 0.

---

## 7. P1 — Permanent identity (separately gated; NOT a P0 prerequisite)

Out of scope; scoped for boundary clarity. A separate P1 packet designs: Supabase SSR/JWT in operations-web (real session, no browser-minted token); server-side JWT verification in both APIs (or one BFF); server-derived `actor`/`project`/capability from governed app-metadata / DB membership (never body actor UUIDs, never the `field_tech` default); the authorization matrix with horizontal/vertical privilege-escalation negative tests; and internal identity checks inside the 3 apparatus RPC bodies. P0-D + P0-C's RPC EXECUTE revocation bridge the gap until P1.

---

## 8. Docs delta (fold the four audit corrections)

Proposed edits to the PM/Ops audit note **in the `apex-learning-lane` repo** — `/home/olares/code/apex/apex-learning-lane/notes/platform-status/2026-07-14-pm-ops-web-platform-audit.md` (a SEPARATE repo from this worktree; applied there under its own governance, **not** committed with this packet):
1. **High-2 tracer** — returns **500 with a valid `task_id`** (e.g. `?task_id=sched-task-001&max_depth=10`); missing `task_id` correctly returns 422. Degraded-backend conclusion unchanged.
2. **High-3 advisor counts** — keep the PM-target-scoped figures; **add**: "Project-wide totals (supplementary, not the PM subset): 31 `rls_disabled_in_public`, 31 `security_definer_view`, 20 `rls_enabled_no_policy`, 8 `rls_policy_always_true`, 67 `function_search_path_mutable`. PM-target figures are a deliberate subset; enumerate the PM target object list before recounting."
3. **High-4** — reframe as **readiness blindness** and record both durability failure modes: (a) startup-time durable-backend registration failure → **silent, persistent** in-memory fallback (`main.py:122-142`), real but fires only on a startup exception since binding is lazy; (b) after a successful lazy bind, request-time DB loss (or the **missing `pm.idempotency_keys` table**) → **500s on idempotent PM POSTs**; (c) `/health/ready` checks connectivity + a TCC view, not `pm.idempotency_keys`, `backend_kind()`, or mounted `work.*` — so neither is observable. *(Refines the ratified H4 wording, which stated "not a silent in-memory fallback" — the silent-fallback code path is real; operator to confirm final wording.)*
4. **High-3 anon exposure** — the audit describes "broad privileges" generically; **add**: exposure is **INSERT/UPDATE/DELETE capability via the Data API** plus the 3 SECURITY DEFINER apparatus RPCs, **inferred** from reachability + effective grants + absent RLS + PostgREST verb/RPC mapping; **no destructive REST request was executed**; do not characterize it as "TRUNCATE through REST" (additive clarification — that phrase is not in the note).

---

## 9. Acceptance (self-check)

| Action | Required outcome | Met by |
|---|---|---|
| P0-A | Read-only preservation: OpenAPI+SHA, /reset state, effective privileges+RLS (all grantees), SECURITY DEFINER RPCs, counts, default-priv (tables+functions, per grantor), backend classification, access logs, rollback inputs | §2 SQL (a)-(e) |
| P0-B | /reset absent in prod OpenAPI (phase-aware runtime status per §1); `SupabaseStore.reset()` **unconditionally** refuses in every environment | §3 conditional reset_router + unconditional `reset()` raise |
| P0-C | PUBLIC/anon/authenticated: no effective write on 4 tables **and** no EXECUTE on 3 RPCs; default-priv prevention (tables+functions, both grantors); SELECT preserved; **primary (014) does not depend on supabase_admin authority** | §4 split 014 (postgres) + 015 (supabase_admin) |
| P0-D | Unauth PM mutation verbs blocked (both apps; **exact route-family boundary**, learning excluded); fail-closed; CORS-clean 503; **existing CI stays green** | §5 middleware + `_is_pm_mutation_path` + conftest deliverable |
| P0-E | Readiness 503 when any mounted schema / **serving-role identity+contract+forbidden-priv** / work-table / idempotency-backend / `pm.idempotency_keys` unavailable | §6 contract-aware /health/ready (both apps) + per-DSN `_probe_role` + `backend_kind()` |
| P1 | Permanent SSR/JWT identity, capability authz, server-derived actors | §7 (separate GO) |

**Not one combined transaction; P1 not a prerequisite; ordering per the §1 dependency DAG** (P0-A → P0-B/P0-C; P0-B before mutation-seam connectivity repair; P0-C `014` independent of `015`; P0-D has no ordering prerequisite but interacts with P0-B's acceptance via the phase-aware `/reset` rule): each action = own file/commit/migration/GO; dual-touch files given as composable diffs. ✔

---

## 10. What this packet does NOT do

No production access, SQL, deploy, secret change, DB-connectivity repair, schema promotion/relocation, RLS-policy redesign, A1–A3 apply, OBS action, push, or PR. It stops at the design, the exact proposed code/SQL above, and the **cross-engine review record committed alongside** (`docs/superpowers/specs/2026-07-14-pm-ops-p0-containment-review-record.md`). Each action awaits its own separate GO; after design review, P0-B and P0-C each receive separate production GOs; connectivity repair only after P0-B is green.

---

## 11. Pre-existing issues surfaced (beyond P0 scope — flagged for operator)

The review rounds surfaced production defects predating this packet, **not** fixed by P0 (each its own decision):
1. **`pm.idempotency_keys` does not exist in prod** (no `pm` schema), yet control-plane binds the durable idempotency backend against it → durable PM idempotency is broken in prod (idempotent PM POSTs would 500 at request time; moot behind P0-D). Creating the table is a schema change (separate GO).
2. **`work.*` tables do not exist in prod** (the `work` schema exists but is empty), yet the `/api/v1/work/*` router is mounted unconditionally → those routes 500 against prod. This is a **second, independent** reason P0-E control-plane readiness reports `not_ready` (greening readiness needs both `work.*` and `pm.idempotency_keys` provisioned). Consistent with the audit's High-1 (`work` = 0 tables) and High-2 (500s).
3. **The 3 SECURITY DEFINER apparatus RPCs** were an unauthenticated write path to `public.apparatus` predating this packet; P0-C revokes the EXECUTE grants but the functions still lack internal identity checks — real fix is P1 (server-derived actor) or gating inside the bodies.
4. **`apex_tcc_runtime`** holds `arwd` on the 4 tables (intentionally out of P0-C scope; not Data-API-reachable) — recorded so "no effective write" is scoped accurately.
5. **`supabase_admin` default-privilege authority**: closing the `supabase_admin`-grantor default privileges (015) requires a `supabase_admin` session that managed `postgres` lacks. 014 closes all EXISTING exposures and the realistic postgres-created future-object vector; if no `supabase_admin` path exists on managed Supabase, the residual (platform-created future objects under the supabase_admin grantor being born exposed) is operator-accepted until such a path is available.
6. **Future-function-PUBLIC EXECUTE (separately measured finish line — rev5 ruling 4)**: Postgres grants `EXECUTE` on newly-created functions to `PUBLIC` via a built-in default that `ALTER DEFAULT PRIVILEGES` cannot reliably strip (repo precedent `docs/superpowers/specs/ops-app-role-boundary/IRP_OPUS_2026-07-01.md`). The **3 known** apparatus write RPCs are explicitly closed (014 stmt 2), and the named-role (anon/authenticated) function defaults are revoked — but a *future* public `SECURITY DEFINER` function touching the PM tables would be born callable via the PUBLIC grant. A blanket `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC` is **too broad** for emergency P0 (it would break legitimate callers across the mixed `public` schema). Per **rev5 ruling 4**, this vector is **not** claimed closed by 014 and does **not** delay it; robust closure is a **separately measured finish line** — per-function `REVOKE EXECUTE … FROM PUBLIC` at creation + a CI assert scanning `has_function_privilege('public', f, 'EXECUTE')` for new public SECURITY-DEFINER functions that reference PM tables (a dedicated posture packet, or folded into P1). Its completion is tracked independently of the P0 close-out.
7. **Control-plane mutation routes not in P0-D scope (operator decision surfaced by rev5 review).** `control_plane_router` (mounted at `/api/v1/control-plane`, `main.py:87`) exposes ~8 `POST` workflow mutations (e.g. `/review-decisions`, `/task-packets/{id}/status`, `/closeout-notes`) **not** covered by P0-D's PM-family prefixes (`/api/v1/work`, `/api/v1/ops/intake`, `/api/v1/ops/recognition`). This is scope-consistent with ruling-6's P0-D scope (and the ops narrowing misses nothing — `ops_router` is GET-only), but these are unauthenticated PM-adjacent mutations. **Operator decision:** confirm the current P0-D scope, or add `/api/v1/control-plane` to `_PM_MUTATION_PREFIXES` (same exact-boundary matcher) if those routes are in the unauth exposure and should be contained.

---

## 12. Finding dispositions (rev5 — operator-ratified)

All seven rev5-review findings were ratified by the operator; each is folded here. Full cross-engine detail (Claude adversarial lenses + Codex) is in the committed review record `docs/superpowers/specs/2026-07-14-pm-ops-p0-containment-review-record.md`.

| # | Sev | Finding | Ruling / fold | Where |
|---|---|---|---|---|
| 1 | High | `SupabaseStore.reset()` still executable outside production | Unconditional refuse; reset/reseed only on `MemoryStore` | §3 Change 3; test `test_supabase_reset_always_raises` |
| 2 | High | Readiness probes `config.engine`, not the real ops role DSNs | Probe `OPS_API_DSN`/`OPS_INTAKE_WRITER_DSN` identity+contract+forbidden-priv | §6 `_probe_role` |
| 3 | High | P0-A not an authoritative snapshot (no RO txn / ACL-only / regex discovery) | Guarded `REPEATABLE READ, READ ONLY` txn + effective-role closure + fail-closed `pg_depend`/dynamic-SQL discovery | §2 SQL guard,(b),(b2),(e) |
| 4 | High | Future-function hardening internally contradictory | Narrow 014 to existing-exposure containment; remove best-effort PUBLIC token; forward-function PUBLIC = separate finish line, does not delay 014 | §4 obj + 014 stmt 3 + 015 + §11.6 |
| 5 | Med | Actions "independent" but actually ordered; post-P0-D `/reset` 503 not 404 | Explicit dependency DAG + phase-aware `/reset` acceptance (OpenAPI-absence invariant) | §1 DAG; §3 OpenAPI acceptance |
| 6 | Med | P0-D reaches into learning + unsafe prefix `startswith` | Drop learning; exact route-family boundary `_is_pm_mutation_path` | §5 middleware + `test_pm_gate_path_boundary` |
| 7 | Med | Review evidence not committed; paths misstated | Commit review record; IRP path → `docs/superpowers/specs/ops-app-role-boundary/IRP_OPUS_2026-07-01.md`; audit note → `apex-learning-lane` repo | §8, §10, §11.6, review record |

**Preserved (unchanged) strengths per the review:** the 3-RPC `EXECUTE` revocation, the `014`/`015` authority split, snapshot-derived rollbacks, `SELECT` preservation, and P1 kept separate.

**Focused cross-engine re-review (rev5).** A focused adversarial pass (Codex `gpt-5.5` + 5 Claude lenses, read-only vs `6f4b68d4`) over these seven changes surfaced six additional refinements — all folded into this rev5: **HIGH** — P0-E readiness contract corrected (`ops.persons` → per-role `ops.v_completion_recognition_worklist` / `ops.intake_runs`; verified against live grants, since neither login role may SELECT `ops.persons`); **MEDIUM** — P0-A `pg_depend` is inert for PL/pgSQL (baseline corrected, `refclassid` guard added, name-match confirmed as the reliable primary); **LOW** — dev persisted-validation harness break disclosed (§3); **LOW/scope** — control-plane P0-D coverage surfaced (§11.7); **NOTE** — §9 P0-B row wording. Codex's one HIGH-flagged item (`has_table_privilege('public', …)` aborts) was **refuted** by direct catalog verification. Full detail + verdict in the review record §3.
