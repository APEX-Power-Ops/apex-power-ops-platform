# Codex Cross-Engine Audit - Schema-Placement Packet 01

**Verdict**

Do not approve as written. The packet over-scopes the relocate lane. `mcp_*` is a live control-plane backend surface, not a dead/internal no-consumer cluster. The `ai_*` cluster is function-wired and needs RPC/grant verification before relocation. The TCC `_pre_rebuild` set is not honestly "dead archive" while kept plan tables or rollback/down paths can still depend on it.

The safe relocate set appears to collapse to `_phase3_load_manifest`, likely `_009_rollback_snapshot` after retention confirmation, and possibly `ai_knowledge` only after live dependency/grant verification. The urgent security fix should be a faster revoke/view-hardening packet, separate from schema placement.

**Findings**

- **Critical - `mcp_*` must reclassify out of Packet 01 relocate scope. Areas 1, 2, 5, 6.**
  `control-plane-api` requires the public mcp relations by name: required relation lists include the two summary views and six tables in [router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:81), direct reads from `public.mcp_task_packets` at [router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:333), writes to `public.mcp_task_packets` and `public.mcp_review_decisions` at [router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:437), summary reads at [router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:690) and [router.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/router.py:1254), worker reads/writes at [worker.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/worker.py:493), [worker.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/worker.py:799), [worker.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/worker.py:883), sync writes at [sync.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/sync.py:135), and queue writes at [queue.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/services/control_plane/queue.py:61). A `SET SCHEMA agent` without code cutover breaks production.

- **High - dropping or relocating mcp summary views is wrong without code cutover. Areas 2, 3, 6.**
  The repo creates `public.mcp_task_packet_summary_v` over `public.mcp_task_packets` and `public.mcp_job_run_summary_v` over `public.mcp_local_action_queue`/`public.mcp_job_runs` in [20260328_000007_add_control_plane_tables.sql](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:163) and [20260328_000007_add_control_plane_tables.sql](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:175). Control-plane reads both. The right interim is revoke anon and convert/replace definer behavior as needed, not drop.

- **High - mcp security posture is a revoke/view-hardening problem, not placement-only. Areas 3, 5.**
  RLS exists, but current policies deliberately permit authenticated reads for several mcp tables: [20260328_000008_enable_control_plane_rls.sql](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000008_enable_control_plane_rls.sql:26), [20260328_000008_enable_control_plane_rls.sql](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000008_enable_control_plane_rls.sql:101), [20260328_000008_enable_control_plane_rls.sql](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000008_enable_control_plane_rls.sql:113). If anon exposure is urgent, revoke anon from public views/tables and fix SECURITY DEFINER leakage first. Moving later requires route SQL and drift-check changes.

- **High - `ai_*` is not proven safe because public task RPC functions are wired to it. Areas 1, 2, 3.**
  No direct app/ORM hits found for `ai_*` in `apps/`, `packages/`, or `services`, but repo SQL defines public functions over these tables: `claim_task` reads/updates `ai_tasks`, `ai_agent_state`, `ai_task_history` at [11_ai_orchestration_functions.sql](/home/olares/code/apex/apex-power-ops-platform/infra/database/source-lineage/apex-resa/automation-orchestration/schema/11_ai_orchestration_functions.sql:12); `create_task` inserts `ai_tasks` at [11_ai_orchestration_functions.sql](/home/olares/code/apex/apex-power-ops-platform/infra/database/source-lineage/apex-resa/automation-orchestration/schema/11_ai_orchestration_functions.sql:162); `get_my_tasks` reads `ai_tasks` at [11_ai_orchestration_functions.sql](/home/olares/code/apex/apex-power-ops-platform/infra/database/source-lineage/apex-resa/automation-orchestration/schema/11_ai_orchestration_functions.sql:270); `get_pending_handoffs` joins `ai_handoffs` and `ai_tasks` at [11_ai_orchestration_functions.sql](/home/olares/code/apex/apex-power-ops-platform/infra/database/source-lineage/apex-resa/automation-orchestration/schema/11_ai_orchestration_functions.sql:300). These functions use unqualified table names, so moving tables breaks RPC unless functions move or are rewritten/schema-qualified.

- **High - TCC `_pre_rebuild` is not honestly dead archive. Areas 1, 4, 6.**
  Current repo migration explicitly marks all 10 target `_pre_rebuild` tables as `must_keep` alongside `tcc_test_plans` and `tcc_test_results`: [004_phase4b_drop_backcompat.sql](/home/olares/code/apex/apex-power-ops-platform/infra/database/migrations/tcc/004_phase4b_drop_backcompat.sql:97). Current ORM maps `tcc_test_plans` to canonical `tcc.*` FKs in [models/user.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/models/user.py:43), but the grounding brief says prod still has inbound FKs from kept `tcc_test_plans` to pre-rebuild tables. That live topology must be verified before any archive move.

- **Medium - migrations/drift checks will recreate or fail against moved objects. Areas 2, 4.**
  `check_schema_drift.py` expects mcp tables in the default/public inspection set and checks their RLS by table name: [check_schema_drift.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/scripts/check_schema_drift.py:25), [check_schema_drift.py](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/scripts/check_schema_drift.py:73). The mcp bootstrap migration uses `CREATE TABLE IF NOT EXISTS public.mcp_*`; after a move, rerun creates fresh empty public tables/views instead of validating the moved ones: [20260328_000007_add_control_plane_tables.sql](/home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api/supabase/migrations/20260328_000007_add_control_plane_tables.sql:37).

- **Medium - atomicity claim is incomplete. Areas 4, 6.**
  One DB transaction per dependency component is right mechanically, and `SET SCHEMA` is metadata-only, but it still takes DDL locks and the component is not only "tables + views." For `mcp`, the real component includes application SQL and drift checks, which cannot be atomically changed by DB DDL alone. For TCC, the component includes kept inbound FK dependents and rollback/down migration assumptions.

**What The Spec/Brief Got Right**

The spec correctly identifies SECURITY DEFINER views as bypass/leak risk and correctly rejects per-object moves that leave public definer views behind. It is also right that `agent`/`archive` should not be exposed PostgREST profiles, and that moves should be reversible with captured pre-ACL/view definitions. The grounding brief's `mcp_*` live-consumer warning is confirmed by repo code.

**What Needs DB Verification**

- Actual prod grants on the 10 public `ai_*` functions and whether anon/authenticated can call them through PostgREST RPC.
- Whether live `content_registry.created_by_task -> ai_tasks` exists and whether any rows depend on it.
- Whether prod `tcc_test_plans` still has inbound FKs to the 8 `_pre_rebuild` ETU tables, despite current repo ORM pointing to `tcc.*`.
- Whether `_009_rollback_snapshot` is still referenced by any live rollback procedure; repo only shows a deferred retention-review note in [G2-RULES-GUIDE.md](/home/olares/code/apex/apex-power-ops-platform/reference/tcc/G2-RULES-GUIDE.md:95).
- `postgres` ability in Supabase prod to `CREATE SCHEMA`, `ALTER DEFAULT PRIVILEGES`, revoke all intended grants, and drop/alter views.

**Recommended Scope Change**

Split the packet:

1. Fast security packet: revoke anon from live-but-exposed public clusters and convert/replace public summary views so anon cannot read them while control-plane remains working.
2. Tiny placement packet: relocate `_phase3_load_manifest`, `_009_rollback_snapshot` after retention confirmation, and maybe `ai_knowledge` after live dependency proof.
3. Later choreographed placement packet: move `mcp_*` only with code cutover from `public.mcp_*` to the new schema.
4. Separate TCC topology packet: resolve `tcc_test_plans`/`tcc_test_results` and pre-rebuild FK disposition before calling those tables archive.
