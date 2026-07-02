# ops_app Role-Boundary Spec - Combined Cross-Engine IRP Record (2026-07-01)

Engines: opus 5-lens panel (grounded, adversarially verified) + Codex gpt-5.5 xhigh (host, grounded against
live source). Both READ-ONLY. Verdict (both): READY_WITH_FIXES - the boundary design holds; the migration +
test-cutover wiring is broken as authored and must be fixed before build; one architectural residual is an
operator decision. Raw records: OPS_APP_IRP_OPUS.md, codex-spec-review.out.

## Convergence (both engines, grounded)
- The privilege BOUNDARY is sound. D2's status-column denial genuinely holds (governed-complete unforgeable
  at the privilege layer, before the completion guard fires). The 9-function SECURITY DEFINER set is COMPLETE
  (opus scanned pg_proc: the only standalone writers of ledger/attestation/apparatus.status are exactly those
  9). Grant coverage for every live DML statement is complete (conflict SELECTs, 4 FOR UPDATE sites,
  scopes-DELETE RI cascade, maintain_scope_quote_hours caller-charge). REVOKE-EXECUTE-before-DEFINER ordering
  is correct and load-bearing.
- Both independently caught the #1 build-breaker: the `work` schema.

## Cross-engine delta (what one caught and the other did not)
- Codex ALONE: (a) D4's "GUC is inert" rationale is FALSE - ops_app holds UPDATE(provenance_status) on
  apparatus, and with SET ops.completion_ctx='1' it can mutate provenance on an already-Complete row (opus's
  boundary lens asserted the guard blocks this - it MISSED that ops_app can set the ctx). (b) Single-role
  function-path forgery - the architectural residual (below).
- opus ALONE: the entire test-harness DSN-split problem (three CRITICALs) - the "tests-as-ops_app" plan is
  unrunnable / false-green as authored because a single OPS_DEV_DSN feeds both admin fixtures and the
  app-under-test; plus the ADP-is-a-no-op-for-functions finding (live-reproduced), the has_table_privilege
  column-grant assert bug, and the REVOKE CONNECT portability defect.
- Both refined the Task-0 fallback: it is mischaracterized as belt-and-suspenders (real; the apparatus
  row-lock is the ONLY cross-path serializer vs approve_and_recognize), but opus adjusted the severity down
  because the NO ACTION FKs make the race fail-CLOSED (abort, not corrupt).

## Confirmed findings, reconciled + ranked

### CRITICAL (build-breakers / false-green blockers - fix before build)
- C1 [both] `work` schema breaks the ladder. `work` is a SEPARATE migration family (targets apex_pm_stage)
  and does NOT exist in ops_test; the ops chain builds ops+core only. So 012's unconditional
  `REVOKE EXECUTE ... IN SCHEMA work`, `ALTER DEFAULT PRIVILEGES ... work`, and the work negative-assert loop
  ERROR on ops_test. Fix: presence-gate every work reference on `to_regnamespace('work') IS NOT NULL` (or
  `EXISTS (SELECT 1 FROM pg_namespace WHERE nspname='work')`); schema-absent = pass. ops_dev still covered.
- C2 [opus] Test-harness DSN split is unspecified -> AS-ops_app proof is unrunnable OR false-greens as
  superuser. All harnesses read ONE env var (OPS_DEV_DSN) for BOTH admin work (DDL ladder, autouse TRUNCATE,
  person + status-bearing apparatus setup INSERTs) AND the behavior-under-test. Fix: split at the FIXTURE
  level - behavior/boundary connections use the ops_app DSN; every admin fixture (ladder, clean_ops /
  clean_ops_between_tests TRUNCATE, _person/_eligible/forced-Complete setup) opens its own OPS_DEV_ADMIN_DSN
  connection. Enumerate each as a concrete conftest-edit task. (Subsumes: TRUNCATE priv ops_app lacks; DDL
  ladder cannot run as ops_app; recognition setup does status writes ops_app is denied; a third "setup-DML ->
  admin" bucket beyond ladder+TRUNCATE.)
- C3 [opus] `REVOKE CONNECT` is not authored-portable across the two DBs the one migration runs on:
  `current_database()` is invalid in REVOKE grammar and a bare name is a literal. Fix: dynamic SQL
  `EXECUTE format('revoke connect on database %I from public', current_database())`. Same one-ladder-two-DBs
  invariant as C1. (opus filed MEDIUM but flagged for elevation; grouping here because it hard-breaks apply.)

### HIGH
- H1 [opus, live-verified] `ALTER DEFAULT PRIVILEGES ... REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC` is a SILENT
  NO-OP - PUBLIC EXECUTE is a hard-wired world default ADP cannot displace. Audit gap G-A is NOT closed by
  ADP; future ops functions silently re-acquire PUBLIC EXECUTE, reopening the DEFINER-escalation class. Fix:
  keep the explicit `REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA ops FROM PUBLIC`; add a per-new-function REVOKE
  CI convention; add a posture assert that FAILS if any ops function retains PUBLIC EXECUTE post-migration.
- H2 [Codex; opus-missed] D4 rationale false / provenance-on-Complete. The completion guard fires only when
  the governed-complete predicate CHANGES and ctx != '1'; ops_app can `SET ops.completion_ctx='1'` (unpriv
  GUC) and then use its UPDATE(provenance_status) grant to change provenance on a Complete row. Fix: tighten
  the completion guard to REJECT any provenance_status change while status='Complete' REGARDLESS of ctx
  (legit provenance writes happen at approve time when status='Not Started', never on Complete rows) - a
  targeted guard addition that does not break approve_run. Restores D4's inertness claim as a real invariant.
- H3 [opus] Positive posture asserts using `has_table_privilege(...,'INSERT')` return FALSE under
  column-scoped grants (apparatus, scope_quote) -> the migration self-fails, or a builder relaxes to
  table-level INSERT and reopens D2. Fix: use `has_column_privilege(role,table,col,'INSERT')` per-column for
  column-scoped objects; reserve has_table_privilege for fully-granted relations.

### OPERATOR DECISION (the headline)
- D-FORGE [Codex] Single-role function-path forgery. D1=A gives ops_app BOTH materialization grants (INSERT
  apparatus/projects/scopes, UPDATE provenance) AND EXECUTE on attest+recognize; the functions validate
  CURRENT ROW STATE, not a non-forgeable authority record. So a COMPROMISED ops_app can manufacture a fake
  project->scope->apparatus, set provenance=approved, attest, and recognize fabricated revenue entirely
  through the sanctioned path. This is a real residual of the single-role choice.
  Context for the decision:
  - What 012 already achieves regardless: the app stops being SUPERUSER. A compromised ops_app CANNOT disable
    triggers, do direct ledger/attestation DML, set apparatus.status directly, escalate to superuser, or
    touch other schemas. Blast radius drops enormously; the forgery is multi-step, attributed in the ledger,
    and leaves a visible fake project.
  - Full closure = D1=B (split ops_intake_writer [materialize] vs ops_api [recognize]; neither alone can both
    fabricate AND recognize) OR an in-DB approved-intake authority ops_app cannot forge. D1=B costs two
    credentials + per-route DSN selection in the API.
  - LEAN: document D-FORGE as a bounded, known residual in 012 and commit D1=B as the DEFINED next hardening
    step (matches the ratified D1 "A now, B later"). BUT this is a forge path knowingly left open - which is
    the exact class your D2 tightening refused to defer - so it is genuinely YOUR call whether to pull D1=B
    into 012 now or accept-and-defer. If you want it closed now, the packet grows to a two-role design.

### MEDIUM
- M1 [both] Task-0 FAIL fallback rewrite: name the real cross-path counterparties (approve_and_recognize
  005:89, attest 009:138, reverse 005:139, revrec-insert trigger 005:173 - 5, not 2) and cite the NO ACTION
  FKs on revenue_recognition_event/completion_attestation.apparatus_id as the durable fail-closed barrier;
  the apparatus row-lock is spurious-abort avoidance, not the correctness barrier. Add a 2-session concurrency
  regression (the 1-session probe cannot exercise the interleave).
- M2 [Codex] ops.projects over-granted (table UPDATE includes retainage_pct + lifecycle). Column-scope
  projects INSERT/UPDATE to the load.py columns + provenance_status/updated_at.
- M3 [Codex] Role idempotency weak: if ops_app pre-exists with bad flags the guarded CREATE ROLE no-ops. Fix:
  unconditional `ALTER ROLE ops_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS` + assert
  pg_roles flags.
- M4 [Codex] Superuser-owned DEFINER functions = superuser blast radius on any future definer bug. Fix
  (defense-in-depth): own the 9 fns with a dedicated NOLOGIN owner holding only the required object
  privileges. (012 or a documented follow-up - operator lean welcome.)
- M5 [opus] Down migration DROP ROLE is blocked by residual granted privileges (not just ownership). Fix:
  REVOKE every up-grant in reverse OR `DROP OWNED BY ops_app` then `DROP ROLE`.
- M6 [opus] Env-var naming is internally contradictory (Section 7 rotate OPS_DEV_DSN vs Section 8/AC6
  OPS_APP_DSN). Standardize once: OPS_DEV_DSN = ops_app (behavior), OPS_DEV_ADMIN_DSN = fixtures, drop
  OPS_APP_DSN; propagate.

### LOW / INFO (cheap precision - fold silently in v2)
- persons SELECT is an over-grant (RI + DEFINER attest run as owner); drop it or correct the note.
- Pin the literal post-D2 apparatus INSERT column list + positive has_column_privilege asserts so a missed
  column fails the migration, not the live pipeline.
- Replace every `has_function_privilege('...(...)')` / `ALTER FUNCTION ...(...)` placeholder with exact
  argument-type signatures; enumerate BOTH issue_billing_application overloads.
- Delete the dead conftest fallback (do not retarget to a postgres-user default); hard-require explicit DSNs.
- AC5 must actually drive intake+approve AS ops_app (recognition tests use admin-seeded apparatus and never
  exercise the column-scoped INSERT/UPDATE matrix).
- Add a view-security in-migration assert (11 ops views stay postgres-owned, non-security_invoker).
- Down: re-GRANT EXECUTE on ALL functions (not just the 9) to restore the clean round-trip; presence-gate work.
- Add the recognized-then-reapprove boundary test (NO ACTION FK makes it hard-fail; exercise the path).

## Disposition
- Design VERDICT stands: READY_WITH_FIXES. No NOT_READY finding.
- Fold C1-C3, H1-H3, M1-M6, and all LOW/INFO into spec v2 (mechanical/wiring; leans are clear).
- BLOCK on operator rulings: (1) D-FORGE = accept-and-defer to D1=B, or pull D1=B into 012 now; (2) M4 owner
  role in 012 or follow-up; (3) small posture choices (persons SELECT drop; env scheme confirm).
- Then: revise spec -> quick re-gate (targeted, not a full second IRP) -> writing-plans.
