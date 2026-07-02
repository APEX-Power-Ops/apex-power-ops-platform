# ops_app Role-Boundary - Ratified Decisions (2026-07-01)

> SUPERSEDED IN PART (2026-07-02): D1 was ratified A (single ops_app) in this record but was FLIPPED to B (two-role split: ops_intake_writer / ops_api + NOLOGIN ops_fn_owner) during the Deep IRP - see 2026-07-01-ops-app-role-boundary-design-v3.md section 2 / D1. The BUILD follows v3 (D1=B). This record remains authoritative for D2-D8; for D1, v3 governs.

Operator ratification of the 8 decisions from the current-surface audit
(`OPS_APP_ROLE_BOUNDARY_AUDIT_2026-07-01.md`). This is the AUTHORITATIVE decision
record the spec must implement. No code, no writes, no prod touch yet - next step is spec.

## Verdict (agreed; operator source-confirmed)
No real role boundary exists today. Confirmed from source: no 012 migration (ops stops at
011); no ops_app role DDL; no REVOKE EXECUTE/CONNECT FROM PUBLIC; no ALTER DEFAULT PRIVILEGES;
no REVOKE CREATE ON SCHEMA public; all ops functions are SECURITY INVOKER (no SECURITY DEFINER);
approve_run does direct Python DML into ops.projects / scopes / scope_quote / tasks /
scope_quote_line / apparatus. The original "just REVOKE apparatus INSERT/UPDATE" gate is NOT
implementable as written because approve_run is the sanctioned intake writer.

## Ratified decisions

**D1 - Role architecture: RATIFIED** = single `ops_app` role for this packet. (Two-role split
deferred to a later refinement; in-DB materializer rejected as a product refactor, out of scope.)

**D2 - Apparatus boundary: RATIFIED + TIGHTENED** = column-scoped grants, and the
forged-Complete-INSERT residual is CLOSED IN 012 (NOT a fast-follow). Specifically:
  - grant `ops_app` only the column-scoped INSERT that approve_run actually needs;
  - EXCLUDE `status` from ops_app INSERT privilege - let it default to 'Not Started', OR change
    the intake writer to omit `status`;
  - `status` mutation stays FUNCTION-OWNED only (attest / revoke via SECURITY DEFINER);
  - revoke status / source / scope_id UPDATE for ops_app;
  - MANDATORY acceptance test: a direct `INSERT ... status='Complete', provenance_status='approved'`
    as ops_app FAILS, even after `SET ops.completion_ctx='1'`.
  Rationale (operator): if ops_app holds table-level INSERT on ops.apparatus, ctx-set + direct
  insert still forges governed-complete rows - the exact class this lane exists to close. Do not
  knowingly leave the hole. AMEND the original GATE-1 text accordingly.

**D3 - SECURITY DEFINER conversion: RATIFIED** = convert all 9 live mutation functions to
SECURITY DEFINER with `search_path = ops, pg_temp`. The DESIGN INCLUDES reverse_recognition + the
5 billing functions (even though billing EXECUTE stays deferred - no Chip-4 route yet). GRANT
EXECUTE to ops_app only on the 4 live recognition functions.

**D4 - GUC authority: RATIFIED** = ops.completion_ctx / ops.billing_ctx stay INTERNAL to the
DEFINER functions only, as admin-session defense-in-depth. ops_app holds no DML on the guarded
tables, so its own SET is inert.

**D5 - PUBLIC hygiene: RATIFIED** = belongs IN 012, not a follow-up. REVOKE CONNECT FROM PUBLIC
(ops_dev / ops_test), REVOKE EXECUTE FROM PUBLIC on ops/core functions, ALTER DEFAULT PRIVILEGES
(ops + core + work), REVOKE CREATE ON SCHEMA public FROM PUBLIC. These are correctness
preconditions of the DEFINER conversion, not optional cleanup.

**D6 - work.* disposition: RATIFIED** = zero grants now (fail-closed). Dropping work.* from
ops_dev is a separate reversible chip (one-DB-per-workstream), not a rider on this packet.

**D7 - Tests-as-ops_app: RATIFIED** = the full behavior suite runs AS ops_app in CI;
admin/superuser DSN only for the DDL ladder + fixture setup (TRUNCATE). Plus the explicit
boundary-denial proofs, including the D2 forged-Complete-INSERT test.

**D8 - Sequencing: RATIFIED** = dev-first. 012 on ops_test + ops_dev + full OPS_DEV_DSN cutover +
soak. THEN a prod-grounding catalog audit of Supabase fxoyniqnrlkxfligbxmg (postgres
non-superuser, pooler in path, managed roles, platform DDL limits) BEFORE authoring any prod
variant. The prod variant is its own gated step.

## Packet shape (ONE hardening packet, no product behavior expansion)
migration 012 = idempotent ops_app role (CREATE ROLE is cluster-level, password out-of-band)
+ PUBLIC hygiene revokes (D5)
+ 9-function SECURITY DEFINER conversion with pinned search_path (D3)
+ column-scoped grant matrix (D1/D2) that CLOSES the forged-Complete-INSERT residual (D2 tighten)
+ zero work.* grants (D6)
+ in-migration posture asserts;
then OPS_DEV_DSN cutover across ALL consumers (control-plane-api routers, ops-intake package, CLI,
tests, operations-web smoke script);
then boundary-proof tests-as-ops_app (D7). Prod parked behind D8 re-grounding.

## Spec-phase must-resolve nuances (flagged; not new decisions)
- The exact `ops.apparatus.status` column default (confirm 'Not Started') and the precise load.py
  change to omit status at INSERT so column-scoped-INSERT-without-status succeeds while approve_run's
  legitimate path is preserved.
- approve_run's own provenance_status write vs the column-grant matrix - confirm it never sets
  status='Complete' (only attest does).
- FOR UPDATE privilege ripple (approve_run locks intake_runs / projects / apparatus) + the INVOKER
  trigger maintain_scope_quote_hours charging the CALLER UPDATE(total_quoted_hours) on scope_quote.

## Sequencing
NEXT = brainstorm -> spec -> writing-plans -> Workflow-SDD -> opus + Codex IRP -> operator-gated
dev apply (ops_test then ops_dev). NO build, NO apply, NO prod touch until the spec passes review.
