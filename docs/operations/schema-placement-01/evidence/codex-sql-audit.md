# Codex SQL Audit - Schema-Placement Packet 01

**Verdict**

BLOCK prod write-GO as written. I found no obvious PG16 syntax error in the three forward actions, but the SQL's in-transaction assertions and rollback are not strong enough for the claimed gate. The biggest issues are false-pass assertion logic for authenticated privileges and definer-view allowlisting, plus unresolved DB-only proof of the deployed control-plane database role. I did not execute SQL or connect to prod.

**Findings**

1. **high - Assertion can false-pass authenticated contract retirement**
   Area: correctness, assertion correctness, no unintended breakage.
   Action 2 revokes `ALL` and drops INSERT-capable authenticated policies, but its assert only checks `has_table_privilege('authenticated', obj, 'SELECT')` for the 8 objects ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:132) lines 132-145). It would not catch retained `INSERT`, `UPDATE`, or `DELETE` through PUBLIC, membership, drifted grants, or the guarded 7th table. This matters because 000008 intentionally granted authenticated insert paths for review decisions and local action queue ([000008](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000008_enable_control_plane_rls.sql:43) lines 43-49, [000008](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000008_enable_control_plane_rls.sql:66) lines 66-72).

2. **high - Definer-view allowlist assert does not enforce the allowlist**
   Area: assertion correctness, residual exposure/honesty.
   The Action 1 allowlist block only counts whether the two named views are still definer ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:73) lines 73-85). It does not fail on any additional `public` SECURITY DEFINER view, despite the spec requiring acceptance failure on any additional definer-view finding ([spec](/tmp/schema_placement_01_rescoped_spec.md:84) lines 84-87). `pg_options_to_table(c.reloptions)` on NULL reloptions is fine here, but the query's scope is too narrow.

3. **high - Runtime DB role safety remains DB-only and unproven from repo**
   Area: no unintended breakage, privilege sufficiency.
   The control-plane uses SQLAlchemy direct DB sessions, not Supabase `.from('mcp_*')` Data API calls: DB URL resolution and engine setup are in [config.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/config.py:31) lines 31-80, and routes depend on `get_db` ([config.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/config.py:86) lines 86-92). The code then runs schema-qualified SQL against `public.mcp_*`, e.g. task summaries ([router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:670) lines 670-690), writes decisions/status ([router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:788) lines 788-820), and worker queue/job writes ([worker.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/worker.py:793) lines 793-883). If the deployed DB role is `postgres` with bypassrls or a true `service_role`, A2 should not break it; if it is a non-bypass runtime role such as `apex_tcc_runtime`, RLS-on plus only `service_role_all` policies can block it. The spec itself requires actual deployed DSN role proof before write ([spec](/tmp/schema_placement_01_rescoped_spec.md:191) lines 191-194). Needs DB verification.

4. **medium - Forward-hardening for `mcp_external_action_audits` is order-dependent**
   Area: idempotency, residual exposure/honesty.
   A1/A2 guard the 7th table with `to_regclass` ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:37) lines 37-43, [draft SQL](/tmp/schema_placement_01_migration_draft.sql:109) lines 109-114), but if this exact SQL is applied while the table is absent and repo migration 000009 is applied later, this migration will not automatically re-run. 000009 creates the table and only adds a service policy, with no explicit anon/auth revoke ([000009](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260407_000009_add_external_mcp_action_audits.sql:15) lines 15-43). The draft note saying to re-apply later is operationally fragile ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:276) lines 276-277).

5. **medium - Rollback is not exact**
   Area: rollback fidelity.
   Action 2 rollback recreates the eight policies with semantics matching 000008, but it does not restore the original table comments after forward comments are changed ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:125) lines 125-130, rollback note [draft SQL](/tmp/schema_placement_01_migration_draft.sql:238) lines 238-260; originals in [000008](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000008_enable_control_plane_rls.sql:123) lines 123-139). Rollback also omits guarded restore grants for `mcp_external_action_audits` if present, even though forward actions revoke it conditionally.

6. **low - Action 3 is idempotent only after a successful first apply on the verified prod shape**
   Area: correctness/idempotency.
   The move is guarded ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:180) lines 180-188), but the assert requires both tables to exist in `archive` ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:201) lines 201-222). That is fine for the verified prod fact that both scratch tables exist, but it is not a no-op in an environment where either object was never present.

**What Is Correct**

- A1/A2 role targeting is mechanically narrow: A1 revokes only `PUBLIC, anon`; A2 revokes only `authenticated`; neither statement names `postgres`, `service_role`, or `apex_tcc_runtime` ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:26) lines 26-35, [draft SQL](/tmp/schema_placement_01_migration_draft.sql:98) lines 98-107).
- `to_regclass(...) IS NOT NULL` guards are the right pattern for the absent 7th table and scratch-table moves.
- `has_table_privilege` is the right effective-privilege function; the problem is incomplete privilege coverage, not the function choice.
- The two definer-view lints do not clear on pure revoke. That note is honest because the SQL leaves the views as SECURITY DEFINER ([draft SQL](/tmp/schema_placement_01_migration_draft.sql:70) lines 70-85; spec [spec](/tmp/schema_placement_01_rescoped_spec.md:139) lines 139-141).
- Action 3 being outside the control-plane table lane is directionally correct. Repo authority distinguishes app-local forward migrations from shared infra/archive-only database artifacts ([authority](/home/olares/code/apex/apex-power-ops-platform/docs/authority/PLATFORM-UNIFICATION-MASTER-AUTHORITY-2026-04-12.md:297) lines 297-300), though the exact target lane should be made concrete.

**Needs DB Verification**

- Actual deployed control-plane DB `current_user`, `rolbypassrls`, memberships, and effective privileges after A1/A2.
- `postgres` CREATE privilege on the database, archive schema absence/owner, object ownership, and lock/dependency posture for Action 3.
- Current full SECURITY DEFINER advisor inventory, not just the two mcp summary views.
- Full effective privileges for `anon` and `authenticated` across SELECT/INSERT/UPDATE/DELETE and relevant table privileges on all 6-or-7 tables plus 2 views.
- PostgREST exposed schemas/cache reload and REST status classification.
- RPC/function residual exposure. This SQL does not close RPC surfaces; it should be characterized, not claimed fixed.

**BLOCKING vs NON-BLOCKING for Prod Write-GO**

BLOCKING:
- Strengthen A2 privilege assertions to cover all retired privileges and the guarded 7th table.
- Replace the definer-view count check with a real allowlist query that fails on any additional public SECURITY DEFINER view finding.
- Obtain and record deployed runtime DB role proof before A2, because repo code cannot prove whether RLS remains usable.
- Resolve 000009 ordering or add a post-000009 hardener if claiming durable forward-hardening.
- Decide whether rollback must be exact; if yes, restore comments and guarded 7th-table grants.

NON-BLOCKING if explicitly accepted:
- Action 3's absent-object portability gap, for this exact prod target where both scratch tables are verified present.
- The SQL mechanics for `REVOKE`, `DROP POLICY IF EXISTS`, `COMMENT`, `ALTER DEFAULT PRIVILEGES`, and `ALTER TABLE ... SET SCHEMA`; I see no clear PG16 syntax blocker.
