# PM/Ops Emergency Containment — Phase 0 Design Packet

> **Design-only.** No production access, SQL, deploy, secret change, connectivity repair,
> schema promotion, A1–A3, OBS action, push, or PR was performed to produce this packet.
> Each action is **independently gated** by its own operator GO and **independently applied**
> (never one combined production transaction). Permanent identity is **P1** — separately gated,
> **not** a prerequisite for P0.

**Revision — rev4 (2026-07-14).** Folds the final verification round: Codex HIGH — the `ON FUNCTIONS` default-priv revoke names only `anon`/`authenticated`, but Postgres grants `EXECUTE` on new functions to **PUBLIC** via a built-in default that `ALTER DEFAULT PRIVILEGES` cannot reliably strip (repo precedent `ops-app-role-boundary/IRP_OPUS_2026-07-01.md`), so a future public SECURITY DEFINER function would be born callable by `anon`/`authenticated` via the PUBLIC grant. The 3 **known** write RPCs are fully closed (014 statement 2); the **future-function-PUBLIC** vector is not one-shot-closable in emergency P0 (a blanket `REVOKE … ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC` is too broad and would break legitimate callers) → reframed honestly and disclosed as a **standing-posture residual (§11.6)**, with a best-effort `PUBLIC` token added to the ADP function revokes. Plus doc nits: control-plane `conftest.py` needs an explicit `import os`; the composable-diff list adds mutation-seam `main.py` (P0-B + P0-D); the P0-B tests cross-reference the `PM_MUTATIONS_ENABLED` flag. rev1→rev3 history below.

**Revision — rev3 (2026-07-14).** Folds two focused cross-engine review rounds (3 adversarial Claude lenses + Codex gpt-5.5, read-only, grounded against live prod). rev2 fixed the rev1 CRITICAL SECURITY DEFINER RPC bypass + imports/MAINTAIN/asserts. **rev3 fixes what the rev2 re-review found against the live catalog:** (a) CRITICAL — the `supabase_admin` `ALTER DEFAULT PRIVILEGES` was bundled in the postgres-run transaction and would abort the *entire* migration (managed `postgres` is not a member of `supabase_admin`), so P0-C is **split by authority** (014 postgres-run primary + 015 supabase_admin-run secondary); (b) CRITICAL — P0-D's default-deny middleware would 503 the *existing* test suite in both apps, so P0-D now includes a **conftest `PM_MUTATIONS_ENABLED=true` default**; (c) HIGH — default-privilege prevention now also covers **functions** (`ON FUNCTIONS`), closing the born-EXECUTE-exposed RPC-bypass class; (d) P0-E drops the wrong-DB **learning** check and §11 discloses that control-plane readiness is truthfully `not_ready` in prod because **both `pm.idempotency_keys` and `work.*` are absent**.

**GATE_SHA (re-derived, not assumed):** `270ca6e16a9cd3cfdd0d64b67e4b6e247f24139f` (`origin/main`, clean).
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

**Reject condition (self-enforced):** no combined production transaction; P1 not a prerequisite; no cross-action dependency. Files touched by two actions are given as **composable diffs** (not full-file replacements): mutation-seam `health.py` (P0-B + P0-E), mutation-seam `main.py` (P0-B + P0-D), and control-plane `main.py` (P0-D + P0-E). P0-D is order-independent (its method gate covers `POST /reset` regardless of P0-B). **Within P0-C, `014` (the urgent primary containment) does NOT depend on `015`'s `supabase_admin` authority.**

---

## 2. P0-A — Read-only evidence preservation

**Objective.** Capture approved pre-change evidence. No mutation/deploy/secret/connectivity change. Stop with hashes, paths, results, drift.

**Deliverable.** `apps/mutation-seam/scripts/pm_ops_p0/preserve_evidence.py` (read-only; house style of `scripts/smoke_deployed_mutation_seam.py`) + the SQL below → custody `/home/olares/custody/pm-ops-p0/<UTC>/` (0700 dir, 0400 files) + SHA-256 manifest.

**Evidence set (each hashed + path-recorded):** (1) deployed OpenAPI both hosts + version/SHA; (2) `/reset` route + security state; (3) effective privileges + RLS on the 4 tables **for every grantee in the ACL**; (4) **every `SECURITY DEFINER` function in `public` referencing the 4 tables**, with args/owner/EXECUTE grants; (5) counts (no row bodies); (6) `pg_default_acl` for schema `public` **for both `objtype='r'` (tables) and `'f'` (functions)**, per grantor; (7) active backend classification (inferred; record source); (8) Render `POST /reset` access logs (operator-captured); (9) rollback inputs (exact per-grantee ACL + per-grantor default ACL, so both rollbacks are generated from the snapshot).

**Read-only SQL snapshot (P0-A):**
```sql
-- pm-ops-p0-A : ACL + RLS + counts + default-priv (tables+functions) + SECURITY DEFINER RPC baseline. READ-ONLY.
-- (a) exact per-grantee table ACL
select c.relname, c.relrowsecurity as rls_enabled,
       (select count(*) from pg_policy p where p.polrelid=c.oid) as policies,
       coalesce(array_to_string(c.relacl, E'\n'), '(default/no explicit acl)') as relacl
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relname in ('projects','scopes','tasks','apparatus') order by c.relname;
-- (b) effective privilege for EVERY grantee present in the ACL (dynamic; records apex_tcc_runtime etc.)
select c.relname, pg_get_userbyid(a.grantee) as grantee, a.privilege_type,
       has_table_privilege(a.grantee, c.oid, a.privilege_type) as effective
from pg_class c join pg_namespace n on n.oid=c.relnamespace cross join lateral aclexplode(c.relacl) a
where n.nspname='public' and c.relname in ('projects','scopes','tasks','apparatus')
order by c.relname, grantee, a.privilege_type;
-- (c) counts only
select 'projects' rel, count(*) n from public.projects
union all select 'scopes', count(*) from public.scopes
union all select 'tasks', count(*) from public.tasks
union all select 'apparatus', count(*) from public.apparatus;
-- (d) default privileges in schema public — BOTH objtypes r (tables) and f (functions), per grantor
select pg_get_userbyid(d.defaclrole) as grantor, d.defaclobjtype as objtype, array_to_string(d.defaclacl, E'\n') as default_acl
from pg_default_acl d join pg_namespace n on n.oid=d.defaclnamespace
where n.nspname='public' and d.defaclobjtype in ('r','f') order by grantor, objtype;
-- (e) SECURITY DEFINER functions in public referencing any of the 4 tables (the RPC write-path surface)
select p.proname, pg_get_function_identity_arguments(p.oid) as args, pg_get_userbyid(p.proowner) as owner,
       has_function_privilege('anon',p.oid,'EXECUTE') as anon_exec, has_function_privilege('authenticated',p.oid,'EXECUTE') as auth_exec,
       (pg_get_functiondef(p.oid) ~* '\y(insert|update|delete|truncate)\y') as body_writes
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.prosecdef and pg_get_functiondef(p.oid) ~* '\y(projects|scopes|tasks|apparatus)\y' order by p.proname;
```

**Baseline observed this session (re-captured authoritatively at GO):** 4 tables `rls_enabled=false`/`policies=0`; `anon`+`authenticated`+`apex_tcc_runtime` hold writes (anon/auth = full `arwdDxtm` incl. MAINTAIN; PUBLIC no direct table grant); default ACLs from grantors **`postgres`** and **`supabase_admin`** grant `anon`/`authenticated` full privileges on future public **tables AND `EXECUTE` on future functions**; query (e) returns exactly the 3 apparatus functions (owner postgres, PUBLIC+anon+authenticated EXECUTE, body_writes true).

**Stop condition.** Stop with hashes/paths/results + drift (drift → re-review before P0-C).

---

## 3. P0-B — `/reset` removal + fail-closed guard + test-only enablement

*(Unchanged from rev2; verified clean by re-review.)*

**Objective.** `/reset` absent in prod OpenAPI (POST → 404); the internal reset refuses production/Postgres execution; survives only as an explicit non-production, memory-backed, opt-in capability.

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

**Change 3 — `apps/mutation-seam/app/db/supabase_store.py` `reset()`** (defense-in-depth; `import os` already present):
```python
def reset(self):
    if os.getenv("APP_ENV", "production") == "production" or os.getenv("SEAM_TEST_RESET_ENABLED") != "true":
        raise RuntimeError("SupabaseStore.reset() refused: disabled in production; requires SEAM_TEST_RESET_ENABLED=true.")
    # ... existing truncate-in-FK-safe-order + reseed body unchanged ...
```

**Preconditions.** P0-A captured; prod confirms `APP_ENV=production`, `SEAM_STORE_BACKEND=postgres`, no `SEAM_TEST_RESET_ENABLED`. **Rollback.** Revert the P0-B commit.
**OpenAPI acceptance (GET-only):** `paths` excludes `/reset`; `POST /reset` → 404.
**Negative tests (pytest, subprocess isolation — the mount is decided once at import; mirror `test_ops_route_mount_gate.py::test_recognition_router_host_gated_subprocess`; each subprocess env must carry `PM_MUTATIONS_ENABLED=true` per §5 so the `/reset` POST is not masked as 503 once P0-D is live):** `test_reset_absent_in_production` (prod env → absent + 404); `test_reset_mounted_only_in_memory_harness` (test+memory+opt-in → present + 200); `test_supabase_reset_guard_raises_in_production` (in-process, raises before DB call); import-smoke subprocess (`from app.main import app` under prod env exits 0).
**Sequencing.** Deploy P0-B **before** any mutation-seam connectivity repair.

---

## 4. P0-C — Atomic revocation of Data-API write privileges (split by authority)

**Objective.** `PUBLIC`/`anon`/`authenticated` hold **no effective write** on the 4 tables **and no EXECUTE** on the 3 apparatus RPCs; new public **tables and functions** are not born write/EXECUTE-exposed; `SELECT` preserved. No schema relocation, no RLS redesign.

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

-- 3) postgres-grantor default-priv prevention — TABLES and FUNCTIONS (functions close the born-EXECUTE-exposed RPC class)
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON TABLES FROM anon, authenticated;
-- Revokes the NAMED-role (anon/authenticated) function default (live pg_default_acl objtype 'f' has those rows).
-- PUBLIC is best-effort: Postgres grants EXECUTE on NEW functions to PUBLIC via a built-in default ADP cannot
-- reliably strip (repo precedent ops-app-role-boundary/IRP_OPUS_2026-07-01.md). Known RPCs are closed by stmt 2;
-- the future-function-PUBLIC EXECUTE vector is a §11.6 standing-posture residual, NOT one-shot-closable here.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;

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
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;  -- PUBLIC best-effort (see 014 note + §11.6)
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
**Acceptance.** 014: table write false + RPC EXECUTE false for anon+authenticated (asserted); SELECT preserved (asserted); postgres-grantor default-priv closed for tables+functions (asserted); applies cleanly as postgres. 015: supabase_admin-grantor default-priv closed (asserted) OR recorded as residual if no authority path. Rollbacks captured (snapshot-derived). No schema relocation/RLS redesign. Advisors re-run on the 4 objects + the 3 functions.
**Post-change verification (read-only).** Re-run P0-A (a),(b),(d),(e); advisors; optional single read-only REST `GET .../rest/v1/projects?select=id&limit=1` still 200. Do not issue a write/RPC to "prove" closure.

---

## 5. P0-D — Temporary closure of unauthenticated PM mutation ingress

**Objective.** Temporarily block unauthenticated PM mutation verbs across both apps' PM route families, reversibly, without permanent identity (P1). Default (flag unset) = **fail-closed**.

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

**control-plane — `apps/control-plane-api/main.py`** (add `JSONResponse` to `from fastapi.responses import FileResponse` → `FileResponse, JSONResponse`; scope to PM prefixes; **composable diff — P0-E also edits this file**):
```python
_PM_MUTATION_PREFIXES = ("/api/v1/work", "/api/v1/ops/intake", "/api/v1/ops/recognition", "/api/v1/learning")
_PM_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
@app.middleware("http")
async def _pm_mutation_gate(request, call_next):
    if (request.method in _PM_MUTATING_METHODS and request.url.path.startswith(_PM_MUTATION_PREFIXES)
            and os.getenv("PM_MUTATIONS_ENABLED") != "true"):
        return JSONResponse(status_code=503, content={"detail": "PM mutations temporarily disabled (containment P0-D)."})
    return await call_next(request)
# ... registered ABOVE the CORS add_middleware call ...
```

**Test-suite deliverable (REQUIRED — the default-deny gate would otherwise 503 the entire existing suite in both apps).** Add, at the very top of each conftest **before** the app is imported:
- `apps/mutation-seam/tests/conftest.py`: `os.environ.setdefault("PM_MUTATIONS_ENABLED", "true")` (before `from app.main import app`).
- `apps/control-plane-api/tests/conftest.py`: **add `import os`** (this file does not currently import it), then `os.environ.setdefault("PM_MUTATIONS_ENABLED", "true")` (pytest loads this conftest before any test module's `from main import app`, so a top-of-file setdefault correctly precedes all app imports).
This also restores `test_ops_route_mount_gate.py::test_recognition_router_host_gated_subprocess` (which asserts 404 on an unmounted route — the gate would otherwise mask it as 503); its subprocess env must inherit/set `PM_MUTATIONS_ENABLED=true`. Without this deliverable, merging P0-D turns CI red across both apps.

**Preconditions.** None — order-independent. **Rollback.** `PM_MUTATIONS_ENABLED=true` or revert.
**Interaction note.** With P0-D live, the P0-B test-only `/reset` (a POST) is also gated by the mutation-seam blanket gate → the reset harness additionally needs `PM_MUTATIONS_ENABLED=true` (fails closed; documented).
**Negative tests + verification.** The new P0-D negative tests explicitly control the flag (unset → assert 503; `=true` → passthrough), so they do not depend on the conftest default. Deployed: `POST` (empty body) to one route per PM family → 503; GETs unchanged; verify the 503 carries `Access-Control-Allow-Origin` via a cross-origin `fetch()`.
**Out of scope.** No JWT/session/capability/actor derivation — that is **P1**.

---

## 6. P0-E — Contract-aware readiness

**Objective.** Readiness fails (**503**) when any **mounted** production domain's required schema, serving role, work table, durable-idempotency backend, or `pm.idempotency_keys` is unavailable. Liveness (`/health`, `/health/live`) stays static so Render's `healthCheckPath: /health` does not cycle the process.

**control-plane — replace `/health/ready`** (`apps/control-plane-api/main.py:~404`; **add `Response`**: `from fastapi import Depends, FastAPI, HTTPException, Request, Response`; **composable diff — P0-D also edits this file's imports/top**). Current behavior: 200-always, probes only `vw_trip_unit_cascade`.
```python
@app.get("/health/ready")
def health_ready(response: Response):
    """Contract-aware readiness: verify each MOUNTED domain's required contract; 503 when any is unavailable."""
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
    _sql("database", "SELECT 1")
    # work.* routes mounted unconditionally -> require representative work tables (not just the schema)
    _sql("work_tables", "SELECT to_regclass('work.projects') IS NOT NULL AND to_regclass('work.tasks') IS NOT NULL "
                        "AND to_regclass('work.work_packages') IS NOT NULL")
    # PM idempotency durability: singleton bound durable AND the backing table exists
    checks["pm_idempotency_backend"] = {"ok": idempotency_cache.backend_kind() == "durable"}
    ok = ok and checks["pm_idempotency_backend"]["ok"]
    _sql("pm_idempotency_keys", "SELECT to_regclass('pm.idempotency_keys') IS NOT NULL")
    # ops intake/recognition mounted only when both role DSNs set -> ops.persons lives in this same DB
    if _ops_intake_enabled():
        _sql("ops_persons", "SELECT to_regclass('ops.persons') IS NOT NULL")
    # NOTE: learning lives in a SEPARATE database (LEARNING_DEV_DSN); config.engine cannot validate it,
    # so no learning check here — a correct learning readiness probe needs its own DSN-bound connection (deferred).
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

**Behavior-change note.** control-plane `/health/ready` currently returns **200-always**; P0-E makes it **503 on not-ready**. Liveness paths unchanged (remain the Render health-check), so a 503 readiness does **not** cycle the service. **Consequence (see §11):** with `pm.idempotency_keys` **and** `work.*` both absent in prod today, P0-E control-plane readiness will correctly report **not_ready** — a truthful signal that the control-plane PM/work backend is not fully provisioned in prod (consistent with High-1's empty `work` schema and High-2's 500s). If any external monitor treats `/health/ready` non-200 as hard-down, repoint it to `/health` before P0-E.

**Preconditions.** None. **Rollback.** Revert. **Verification (GET-only).** `/health` → 200 both apps; `/health/ready` → 200 when contracts present, 503 with a per-check body otherwise. **Import-smoke test** (both apps): subprocess `from <module> import app` under prod env exits 0.

---

## 7. P1 — Permanent identity (separately gated; NOT a P0 prerequisite)

Out of scope; scoped for boundary clarity. A separate P1 packet designs: Supabase SSR/JWT in operations-web (real session, no browser-minted token); server-side JWT verification in both APIs (or one BFF); server-derived `actor`/`project`/capability from governed app-metadata / DB membership (never body actor UUIDs, never the `field_tech` default); the authorization matrix with horizontal/vertical privilege-escalation negative tests; and internal identity checks inside the 3 apparatus RPC bodies. P0-D + P0-C's RPC EXECUTE revocation bridge the gap until P1.

---

## 8. Docs delta (fold the four audit corrections)

Proposed edits to `notes/platform-status/2026-07-14-pm-ops-web-platform-audit.md` (proposed patch; applied when the operator chooses):
1. **High-2 tracer** — returns **500 with a valid `task_id`** (e.g. `?task_id=sched-task-001&max_depth=10`); missing `task_id` correctly returns 422. Degraded-backend conclusion unchanged.
2. **High-3 advisor counts** — keep the PM-target-scoped figures; **add**: "Project-wide totals (supplementary, not the PM subset): 31 `rls_disabled_in_public`, 31 `security_definer_view`, 20 `rls_enabled_no_policy`, 8 `rls_policy_always_true`, 67 `function_search_path_mutable`. PM-target figures are a deliberate subset; enumerate the PM target object list before recounting."
3. **High-4** — reframe as **readiness blindness** and record both durability failure modes: (a) startup-time durable-backend registration failure → **silent, persistent** in-memory fallback (`main.py:122-142`), real but fires only on a startup exception since binding is lazy; (b) after a successful lazy bind, request-time DB loss (or the **missing `pm.idempotency_keys` table**) → **500s on idempotent PM POSTs**; (c) `/health/ready` checks connectivity + a TCC view, not `pm.idempotency_keys`, `backend_kind()`, or mounted `work.*` — so neither is observable. *(Refines the ratified H4 wording, which stated "not a silent in-memory fallback" — the silent-fallback code path is real; operator to confirm final wording.)*
4. **High-3 anon exposure** — the audit describes "broad privileges" generically; **add**: exposure is **INSERT/UPDATE/DELETE capability via the Data API** plus the 3 SECURITY DEFINER apparatus RPCs, **inferred** from reachability + effective grants + absent RLS + PostgREST verb/RPC mapping; **no destructive REST request was executed**; do not characterize it as "TRUNCATE through REST" (additive clarification — that phrase is not in the note).

---

## 9. Acceptance (self-check)

| Action | Required outcome | Met by |
|---|---|---|
| P0-A | Read-only preservation: OpenAPI+SHA, /reset state, effective privileges+RLS (all grantees), SECURITY DEFINER RPCs, counts, default-priv (tables+functions, per grantor), backend classification, access logs, rollback inputs | §2 SQL (a)-(e) |
| P0-B | /reset absent in prod; internal reset refuses prod/Postgres | §3 conditional reset_router + reset() guard |
| P0-C | PUBLIC/anon/authenticated: no effective write on 4 tables **and** no EXECUTE on 3 RPCs; default-priv prevention (tables+functions, both grantors); SELECT preserved; **primary (014) does not depend on supabase_admin authority** | §4 split 014 (postgres) + 015 (supabase_admin) |
| P0-D | Unauth PM mutation verbs blocked (both apps, incl. learning); fail-closed; CORS-clean 503; **existing CI stays green** | §5 middleware + conftest deliverable |
| P0-E | Readiness 503 when any mounted schema/role/work-table/idempotency-backend/`pm.idempotency_keys` unavailable | §6 contract-aware /health/ready (both apps) + `backend_kind()` |
| P1 | Permanent SSR/JWT identity, capability authz, server-derived actors | §7 (separate GO) |

**Not one transaction; P1 not a prerequisite; no cross-action dependency:** each action = own file/commit/migration/GO; dual-touch files given as composable diffs; P0-D order-independent; P0-C 014 independent of 015. ✔

---

## 10. What this packet does NOT do

No production access, SQL, deploy, secret change, DB-connectivity repair, schema promotion/relocation, RLS-policy redesign, A1–A3 apply, OBS action, push, or PR. It stops at the design, the exact proposed code/SQL above, and the two-round review evidence (recorded at commit). Each action awaits its own separate GO; after design review, P0-B and P0-C each receive separate production GOs; connectivity repair only after P0-B is green.

---

## 11. Pre-existing issues surfaced (beyond P0 scope — flagged for operator)

The review rounds surfaced production defects predating this packet, **not** fixed by P0 (each its own decision):
1. **`pm.idempotency_keys` does not exist in prod** (no `pm` schema), yet control-plane binds the durable idempotency backend against it → durable PM idempotency is broken in prod (idempotent PM POSTs would 500 at request time; moot behind P0-D). Creating the table is a schema change (separate GO).
2. **`work.*` tables do not exist in prod** (the `work` schema exists but is empty), yet the `/api/v1/work/*` router is mounted unconditionally → those routes 500 against prod. This is a **second, independent** reason P0-E control-plane readiness reports `not_ready` (greening readiness needs both `work.*` and `pm.idempotency_keys` provisioned). Consistent with the audit's High-1 (`work` = 0 tables) and High-2 (500s).
3. **The 3 SECURITY DEFINER apparatus RPCs** were an unauthenticated write path to `public.apparatus` predating this packet; P0-C revokes the EXECUTE grants but the functions still lack internal identity checks — real fix is P1 (server-derived actor) or gating inside the bodies.
4. **`apex_tcc_runtime`** holds `arwd` on the 4 tables (intentionally out of P0-C scope; not Data-API-reachable) — recorded so "no effective write" is scoped accurately.
5. **`supabase_admin` default-privilege authority**: closing the `supabase_admin`-grantor default privileges (015) requires a `supabase_admin` session that managed `postgres` lacks. 014 closes all EXISTING exposures and the realistic postgres-created future-object vector; if no `supabase_admin` path exists on managed Supabase, the residual (platform-created future objects under the supabase_admin grantor being born exposed) is operator-accepted until such a path is available.
6. **Future-function-PUBLIC EXECUTE (standing-posture residual)**: Postgres grants `EXECUTE` on newly-created functions to `PUBLIC` via a built-in default that `ALTER DEFAULT PRIVILEGES` cannot reliably strip (repo precedent `ops-app-role-boundary/IRP_OPUS_2026-07-01.md`). The **3 known** apparatus write RPCs are explicitly closed (014 stmt 2), and the named-role (anon/authenticated) function defaults are revoked — but a *future* public `SECURITY DEFINER` function touching the PM tables would be born callable by anon/authenticated via the PUBLIC grant. A blanket `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC` is **too broad** for emergency P0 (it would break legitimate callers across the mixed `public` schema). Robust closure of this class is a **standing posture control** — per-function `REVOKE EXECUTE … FROM PUBLIC` on creation + a CI assert scanning `has_function_privilege('public', f, 'EXECUTE')` for new public SECURITY-DEFINER functions that reference PM tables — scoped as a follow-on (P1 or a dedicated posture packet), not one-shot-closable here. **Operator decision:** accept as a disclosed residual, or fold the CI posture assert into a follow-on.
