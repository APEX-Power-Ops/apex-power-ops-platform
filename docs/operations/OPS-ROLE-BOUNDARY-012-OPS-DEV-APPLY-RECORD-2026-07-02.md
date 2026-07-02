# ops_dev APPLY RECORD -- migration 012 ops_app role-boundary
Date: 2026-07-02. Operator GO received (with option A: synthetic positive-write smoke, cleaned up).
Applied from merged SHA 23ce8e53388032b92808c522697d02bd8e98cc46 (PR #55, origin/main HEAD).
Provenance re-verified immediately before apply: worktree 012 up+down files == origin/main (git diff empty);
only dirt = 3 foreign records-lane files (untouched).

## 1. Apply (13:47:55Z)
docker exec -i apex-dev-pg psql -U postgres -d ops_dev --single-transaction -v ON_ERROR_STOP=1 \
  -f - < infra/database/migrations/ops/012_ops_app_role_boundary.sql
Exit code 0 (single transaction committed; internal [2a]/[3a]/[5a] asserts all passed in-line).
Two expected WARNINGs only (defensive REVOKE of never-granted ops_fn_owner membership).

## 2. Post-apply DSN reconnect (all green)
ADMIN=postgres/ops_dev/super=True; ops_intake_writer/ops_dev/super=False; ops_api/ops_dev/super=False.
PUBLIC CONNECT revoked; explicit CONNECT carries both login roles (F-012-3 down-path also protected).

## 3. Standalone posture checks (read-only, all green)
- db CONNECT: writer=t api=t; PUBLIC CONNECT ACE on ops_dev: GONE.
- SECURITY DEFINER fns owned by ops_fn_owner: 9/9.
- ops_api EXECUTE = exactly the 4 recognition fns (attest_apparatus_complete, revoke_completion_attestation,
  approve_and_recognize, reverse_recognition). api DML grants in ops: 0 (forge closure).
- ops_intake_writer EXECUTE = exactly 1 fn: ops._intake_source_format_text (F-012-1).
- PUBLIC EXECUTE leaks in ops (incl. null-proacl defaults): 0.
- writer apparatus.status column: INSERT=f UPDATE=f (D2).
- ops_fn_owner SELECT on ops.tasks: t (F-012-2).
- schema USAGE writer/api: t/t; ops views: 11.

## 4. Denial smoke (SET ROLE, each in rolled-back txn; 7/7 denied)
a writer UPDATE apparatus.status; b writer EXECUTE attest; c writer EXECUTE approve_and_recognize;
d api INSERT projects; e api INSERT intake_runs; f api DELETE apparatus; g api UPDATE apparatus.status.
All 7 returned "permission denied"; all rolled back.

## 5. Positive-write smoke (option A) -- PASS (RB012-SMOKE-20260702T135610Z)
Real login connections (dbname-swapped role DSNs), package code paths:
- WRITER (ops_intake_writer): projects+scopes+scope_quote inserts; apparatus insert in the exact
  load.py 11-column shape (status NOT named -> default supplied "Not Started", D2 proven live);
  approve.py _freeze port (quoted_revenue=round(hours*GENERATED blended_rate,2)=1500.00,
  provenance approved, quote frozen); intake_runs insert exercising the F-012-1 index-predicate helper.
- API (ops_api): attest_complete OK (att 5fb70a23) -> approve_and_recognize OK (event dae5f361,
  +1500.00) -> reverse_recognition OK (reversal 19ac18f0, -1500.00) -> revoke_completion_attestation OK.
- v1 attempt deviation (recorded): first smoke draft INSERTed apparatus.quoted_revenue -- correctly
  DENIED (quoted_revenue is writer-UPDATE-only via _freeze, not writer-INSERT). NOT a matrix defect;
  the smoke was corrected to the real app path. v1 partial rows purged before v2.

## 6. Cleanup + residue (explicitly reported per operator instruction)
Deleted by admin: v1 partials (project/scope/scope_quote/person) + v2 inert intake_run (DELETE allowed;
trg_intake_run_immutable guards mutation, not deletion).
RESIDUE (7 rows, permanent BY DESIGN -- ops.revenue_recognition_event and ops.completion_attestation
are append-only (revrec_immutable / completion_attestation_immutable raise on DELETE, admin included)
and the 2 ledger events FK-pin their full ancestry; triggers were NOT bypassed):
- ops.projects 1: RB012-SMOKE-20260702T135610Z (Active/approved)
- ops.scopes 1 (RB012-S), ops.scope_quote 1 (frozen), ops.apparatus 1 (RB012-A, In Progress/approved, 1500.00)
- ops.persons 1 (RB012-SMOKE PM, c289d01f)
- ops.completion_attestation 1 (5fb70a23, revoked=t)
- ops.revenue_recognition_event 2 (dae5f361 +1500.00; 19ac18f0 reversal -1500.00) -- NET 0.00
All rows carry the RB012-SMOKE label; ledger is net-zero; no financial or operational effect.

## 7. Soak watch (open)
Watch for permission-denied errors, route mount issues, or DSN drift. NEVER run test_012 against
ops_dev (fixture rebuilds schemas). Prod (D8) = separate Supabase re-grounding packet; do NOT apply.

## 8. HTTP product-path smoke (mounted app process, 2026-07-02, post-apply)
Ephemeral uvicorn via the documented app-env contract (`cd apps/control-plane-api && uv run
--with-requirements requirements.txt uvicorn main:app`), with OPS_INTAKE_WRITER_DSN /
OPS_API_DSN dbname-swapped to ops_dev in-shell (never printed) + placeholder URL-form
DATABASE_URL. Ops routes MOUNTED (gate saw both role DSNs). Read-only roundtrips:
- GET /api/v1/ops/recognition/worklist -> 200 (ops_api role reading live ops_dev views)
- GET /api/v1/ops/recognition/rollup   -> 200 (ops_api)
- GET /api/v1/ops/intake/<zero-uuid>   -> 404 "run not found" (ops_intake_writer DB roundtrip)
No permission-denied in the app log; clean shutdown; residue-free (reads only). Proves the
mounted app process operates ops_dev through the role DSNs end-to-end over HTTP.

DEPLOYMENT NOTE (for the dev service wiring): apps/control-plane-api/.venv is STALE
(psycopg2-only, no workspace packages -- cannot run the ops routers); a deployed dev service
must use the requirements.txt environment (or equivalent) and set all three of
OPS_INTAKE_WRITER_DSN, OPS_API_DSN (ops_dev), and a DATABASE_URL-class var (URL form,
required at import by config.py) or the ops routes will not mount / the app will not start.
