# ops_app Spec v2 - Combined Cross-Engine Re-Gate Record (2026-07-01)

Engines: opus 3-lens (forge-closure / migration-owner / harness-cutover, adversarially verified) + Codex
gpt-5.5 xhigh (host). Both READ-ONLY, both grounded against live source + catalog. Raw: codex-v2-review.out,
wd4o01pq3 output.

## Headline verdict
The two-role D1=B design is SOUND and the FORGE PATH IS CLOSED BY CONSTRUCTION - BOTH engines confirmed this
independently. What remains is a bounded set of spec-completeness fixes at the OWNER-grant and
CUTOVER/HARNESS layers. opus rated NOT_READY (not because the design is broken but because one gap is a
false-green that would let API-boundary behavior silently run as superuser); Codex rated it sound-if-fixed.
Reconciled: fold the residuals into v3, then a fast targeted confirm. NO finding invalidates the design.
NO NOT_READY on the boundary itself.

## Convergence (both engines, grounded)
- FORGE CLOSED. writer holds NO EXECUTE on any recognition fn + NO ledger/attestation DML; the 4 recognition
  fns are SECURITY DEFINER owned by NOLOGIN ops_fn_owner, EXECUTE-granted only to ops_api; approve_and_recognize
  derives scope_id/project_id/quoted_revenue from the apparatus ROW (005:118), not caller args - so ops_api
  cannot fabricate through the fn. Neither login role alone can fabricate AND recognize; cross-compromise of
  both is required (the intended raise). ops_fn_owner owns no forge path.
- H2 is CORRECT and breaks no sanctioned path (both checked the fn bodies): attest writes only status (009:114),
  revoke only status (009:151), approve sets provenance at status='Not Started'; none mutates provenance while
  status='Complete'. The recognized-then-reapprove path is blocked earlier by _conflict_kind's frozen gate.
- Migration 012 mechanics now right: work presence-gate via to_regnamespace('work') (work present ops_dev /
  absent ops_test - correct both ways); dynamic REVOKE CONNECT via format %I; explicit REVOKE EXECUTE (ADP is a
  no-op for functions); has_column_privilege vs has_table_privilege split; all 9 exact signatures verified
  byte-for-byte against pg_proc; DOWN teardown ordering (ALTER FUNCTION OWNER TO postgres BEFORE DROP OWNED
  BEFORE DROP ROLE) is load-bearing and correct.
- Both flagged the cutover/route layer as the weak point.

## Cross-engine delta (each caught what the other missed)
- Codex ALONE:
  - [HIGH-C1] ops_fn_owner reachable via SET ROLE. NOLOGIN does NOT stop a login role that is a MEMBER from
    `SET ROLE ops_fn_owner`. By default they are not members, but defense-in-depth demands it be explicit.
    (design v2:105/:191.) The one path that could undo the whole split - opus's forge lens asserted the owner
    "unreachable" and MISSED the membership vector.
  - [HIGH-C2] ops_fn_owner missing FOR UPDATE lock privileges. reverse_recognition locks
    revenue_recognition_event FOR UPDATE (005:133); billing fns lock projects (006:537) + revrec rows (006:609).
    v2 grants the owner only INSERT+SELECT on the ledger and SELECT on projects -> the owner's own fns would hit
    permission-denied on the lock. opus's migration-owner lens verified the WRITER's grants but not the OWNER's
    lock needs. REAL and Codex-unique.
- opus ALONE:
  - [HIGH-O1] API route-test false-green (the decisive NOT_READY). The behavior-under-test in
    test_ops_intake_routes.py / test_ops_recognition_routes.py runs INSIDE the FastAPI app process (TestClient),
    whose DSN is os.environ['OPS_DEV_DSN'] via intake_router._dsn()/recognition_router._dsn() + the main.py:111
    mount gate. v2's Section 9 three-identity split enumerates ONLY the package conftest; the route-test files
    carry their OWN duplicate admin fixtures + inline psycopg.connect seeds. A builder can keep those alive with
    OPS_DEV_DSN=postgres and run ALL API-boundary intake/approve/recognition behavior AS SUPERUSER while the
    suite goes green - the exact false-green Section 9 forbids. Codex raised the mount-gate at MEDIUM but opus
    traced it to the app-process-DSN + route-test-fixture layer and correctly escalated to HIGH.
  - [MED-O2] ops_intake_writer projects UPDATE column set under-specified as prose ("the load.py upsert cols");
    load.py upsert_project DO-UPDATE writes project_name, status, quote_revision, contract_value, description,
    source_client_name/site_*, source, updated_at (+ _freeze writes provenance_status). Pin the LITERAL set so a
    reapprove hitting DO-UPDATE does not get a runtime column permission-denied. NOTE: projects.status is
    project-level and IS grantable - do not conflate with apparatus.status (D2 bars that).
  - [MED-O4] operations-web smoke-estimator-native.mjs:314 hard-reads OPS_DEV_DSN for its psql verification
    read; env retirement contradicts it. Point it at OPS_DEV_ADMIN_DSN; the HTTP intake/approve leg is
    writer-scoped only because the API process starts with OPS_INTAKE_WRITER_DSN (script cannot select it).

## Reconciled residual findings for spec v3 (all mechanical / spec-completeness)

HIGH
- V3-1 [Codex-C1] REVOKE ops_fn_owner FROM ops_intake_writer, ops_api, PUBLIC; posture-assert no login role is
  a member (pg_has_role(...,'ops_fn_owner','member')=false). Add to migration 012 + Section 7 asserts.
- V3-2 [Codex-C2] Give ops_fn_owner the least-privilege UPDATE grants its own fns need for FOR UPDATE:
  revenue_recognition_event (reverse_recognition 005:133), projects (billing 006:537). Column-scope where
  feasible; assert. (Owner UPDATE is safe: NOLOGIN + fn-gated + the append-only insert-integrity trigger still
  bars real mutation.)
- V3-3 [opus-O1] Route-test cutover, explicit: (a) intake_router._dsn()->OPS_INTAKE_WRITER_DSN,
  recognition_router._dsn() (mutations AND _read_view)->OPS_API_DSN; (b) enumerate the route-test files' OWN
  admin fixtures + inline seeds -> OPS_DEV_ADMIN_DSN, distinct from the package copies; (c) add a boundary route
  test asserting the app process is NOT a superuser (fails loud if it is).

MEDIUM
- V3-4 [both] main.py mount gate _ops_intake_enabled() -> gate on presence of BOTH new DSNs (or an explicit
  OPS_ROUTES_ENABLED flag); re-author the host-gating guard tests; decide OPS_DEV_DSN's fate explicitly. Land in
  the SAME atomic change as V3-3 so the edits do not order-skew and 404 the suite mid-cutover.
- V3-5 [opus-O2] Pin the literal ops_intake_writer projects UPDATE column set (list above).
- V3-6 [opus-O4] smoke psql read -> OPS_DEV_ADMIN_DSN; state the HTTP leg's writer scoping.

LOW
- V3-7 [opus] Section 8 cutover = enumerated verifiable task set + acceptance grep: neither router references
  OPS_DEV_DSN post-cutover (a half-applied cutover fails the gate instead of silently reopening single-role).
- V3-8 [opus] Section 9 supersedes test_ops_intake_routes.py + test_ops_recognition_routes.py BY NAME; delete
  the OPS_DEV_DSN 'or (...)' fallback in the two route-test _dsn() copies (Section 7's single-conftest wording
  may not reach them).
- V3-9 [opus] Positive assert: has_column_privilege(writer,'ops.projects','status','UPDATE')=true + the rest of
  the pinned projects UPDATE cols (fails at apply, not first live reapprove).
- V3-10 [Codex] Down-migration: make the ordered list unambiguous (ALTER FUNCTION OWNER TO postgres FIRST, then
  DROP OWNED, then DROP ROLE) - currently reads correctly but starts with the DROP OWNED phrasing.
- V3-11 [opus] H2 wording is SAFE as-is; if expanded, cite the _conflict_kind frozen-gate as the durable reason.

INFO (no build action)
- H1 posture-assert loop scoped ops-only while REVOKE targets ops+core - safe (core has 0 functions); optionally
  widen the loop to ('ops','core').
- DOWN round-trip materializes an explicit PUBLIC CONNECT ACE (vs the implicit default) - cosmetic.

## Disposition
- Design VERDICT: sound; forge path closed by construction (both engines). No design change in v3.
- v3 = fold V3-1..V3-11 (all mechanical: 3 HIGH owner-grant/membership + route-test false-green, 3 MED, 5
  LOW/INFO). This is a bounded editing pass, not a redesign.
- Then a FAST targeted confirm on the changed sections (owner grants + membership; route-test/mount-gate
  cutover; projects column list) - not a third full IRP.
- Then operator review of v3 -> writing-plans.
