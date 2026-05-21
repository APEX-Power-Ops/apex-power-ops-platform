# APEX PM Lane 501 Project Onboarding Design Reframing No-Write Design Packet

Date: 2026-05-21

Status: Executed and accepted closed

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_501_PROJECT_ONBOARDING_DESIGN_REFRAMING_NO_WRITE`

## Purpose

This packet reframes Temp Power onboarding as a design-only lane.

It does not write any `seam.*` or `public.*` row. It re-runs the existing Lane 029 extractor, inspects the current production import state read-only, and freezes a reviewable intermediate ingest contract plus reconciliation strategy for Lane 502.

## Phase 0 Discovery

### 1. Migration 016 clean state

Finding:

1. `seam.apparatus.scope_id` exists as nullable `TEXT`.
2. `apparatus_scope_id_fkey` targets `seam.scopes(id)`.
3. `apparatus_scope_id_idx` exists.
4. `pm` and `operations` retain `SELECT`, `INSERT`, and `UPDATE` on `seam.projects`, `seam.tasks`, and `seam.apparatus`.
5. `anon` and `authenticated` do not retain those privileges.

Artifact:

1. [data_jsonb_samples_20260521T103643Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/discovery/data_jsonb_samples_20260521T103643Z.json)

### 2. Production row count sanity

Finding:

1. `seam.projects = 1`
2. `seam.tasks = 15`
3. `seam.apparatus = 184`
4. `seam.scopes = 0`
5. Counts exactly match the migration 016 closeout state.

### 3. `seam.projects.data` sampling

Finding:

1. The single project row remains `pm-import-project-miner-temp-power`.
2. `data` carries the canonical project shape: project identity, source bundle metadata, import payload identity, freshness metadata, and warning-review lineage.
3. `import_summary.workpackage_count = 7` and `apparatus_candidate_count = 184` are already embedded on the project row.

### 4. `seam.tasks.data` sampling

Finding:

1. Sampled task rows carry source-trace lineage, designation, apparatus-type, planned-hours, and import identity.
2. No sampled task `data` row contains `scope_id`, `scope_sheet`, `scope_name`, or `scope_reference`.
3. The relational `workpackage_id` column is present and is the only current scope-adjacent structural linkage on tasks.

Conclusion:

Tasks do not carry implicit scope linkage today. Lane 501 leaves tasks out of scope.

### 5. `seam.apparatus.data` sampling

Finding:

1. Sampled apparatus rows carry `name`, `task_id`, `source_row`, `source_line_id`, `source_designation`, `source_apparatus_type`, `source_drawing_ref`, and `source_candidate_apparatus_id`.
2. All sampled `scope_id` values remain `NULL`.
3. The strongest natural match key is already embedded: `source_candidate_apparatus_id`.

### 6. Extractor re-run against the R3 workbook

Finding:

1. The workbook still resolves as `flat_quote`, not `scope_sheets`.
2. Active scope-sheet list is empty.
3. Extractor line-item count and expanded apparatus candidate count remain consistent with the imported surface.
4. Scope-specific metadata such as `scope_type`, `scope_total_hours`, `scope_multiplier`, and `scope_quoted_amount` are absent because the workbook is not currently in the scope-sheet shape.

Artifact:

1. [extractor_output_r3_temp_power_20260521T103643Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/discovery/extractor_output_r3_temp_power_20260521T103643Z.json)

### 7. Lane 029 extractor compatibility re-verification

Finding:

1. `apps/mutation-seam/tests/test_project_seed_sources.py`
2. `apps/mutation-seam/tests/test_workbook_seed_reads.py`
3. `apps/mutation-seam/tests/test_pm_lane_seed.py`

All ten tests passed during this packet.

### 8. Match-key candidate enumeration

Finding:

1. `source_candidate_apparatus_id` is collision-free and deterministic for the current sample.
2. `source_line_id + name` is also collision-free for the current sample and is the first fallback.
3. `source_row + source_designation + source_apparatus_type + name` remains deterministic and is the second fallback.
4. `source_row + source_designation + source_apparatus_type` is intentionally rejected as a confident key because repeated quantities collide.

### 9. Identifier scheme verification

Finding:

1. Project id pattern: `pm-import-project-miner-temp-power`
2. Task id pattern: `pm-import-project-miner-temp-power-task-0001`
3. Apparatus id pattern: `pm-import-project-miner-temp-power-app-0001`
4. Workpackage id pattern: `pm-import-project-miner-temp-power-wp-001`
5. Proposed scope id pattern: `pm-import-project-miner-temp-power-scope-001`

### 10. No-write verification

Finding:

1. Every SQL statement issued during Phase 0 was logged.
2. The log contains only `SELECT` statements.
3. No `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `CREATE`, `GRANT`, or `REVOKE` appears.

Artifact:

1. [no_write_sql_log_20260521T103643Z.txt](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/discovery/no_write_sql_log_20260521T103643Z.txt)

## Source Contract

The canonical intermediate contract is frozen at:

1. [intermediate_ingest_contract_v1.schema.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/contract/intermediate_ingest_contract_v1.schema.json)

Key design decisions:

1. The contract is purpose-built for `seam.*` ingestion and does not reuse the old Dataverse shape.
2. `scope_id` values are precomputed and embedded; Lane 502 must not invent them at runtime.
3. Scope objects are derived from existing workpackage section rollups because the workbook currently has no scope-sheet metadata.
4. Apparatus entries preserve reconciliation status, match keys, and source traceability.

## Reconciliation Strategy

The frozen reconciliation strategy is documented at:

1. [reconciliation_strategy.md](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/strategy/reconciliation_strategy.md)

Current sample result:

1. `matched = 184`
2. `unmatched_existing = 0`
3. `unmatched_extractor = 0`
4. `conflicting = 0`

## Sample Artifacts

1. [miner_temp_power_testing_intermediate_20260521T103643Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_intermediate_20260521T103643Z.json)
2. [miner_temp_power_testing_reconciliation_20260521T103643Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_reconciliation_20260521T103643Z.json)
3. [miner_temp_power_testing_reconciliation_20260521T103643Z.md](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_reconciliation_20260521T103643Z.md)

Frozen reconciliation report content hash:

`1b87397b17ffecd27679073d9645012d5663533ad344e15110c91258993d6130`

## Lane 502 Admission Criteria

Lane 502 may only be drafted against this packet if all of the following stay true:

1. The Lane 501 no-write artifacts remain the current review surface.
2. The reconciliation report body still hashes to `1b87397b17ffecd27679073d9645012d5663533ad344e15110c91258993d6130`.
3. No conflict is introduced in a later rerun.
4. Lane 502 honors the requirements frozen in [APEX-PM-LANE-501-LANE-502-IMPLEMENTATION-REQUIREMENTS-2026-05-21.md](c:/APEX%20Platform/apex-power-ops-platform/docs/operations/APEX-PM-LANE-501-LANE-502-IMPLEMENTATION-REQUIREMENTS-2026-05-21.md).

## Validation Results

1. Phase 0 documented all ten required findings.
2. The read-only generator completed successfully.
3. The SQL log contains zero mutation statements.
4. Production row counts remained unchanged at `1 / 15 / 184 / 0`.
5. The sample reconciliation includes all four outcome categories with explicit counts.

## Boundaries Preserved

This packet does not admit:

1. any `INSERT`, `UPDATE`, or `DELETE` against any seam table
2. any write to `public.*`
3. any write to financial tables
4. any reconciliation of `seam.tasks`
5. any normalization of `data` jsonb contents
6. any route, persistence, or auth module change
7. any mutation to prior-lane packet surfaces
8. any modification to `apps/mutation-seam/app/project_seed_sources.py`
9. any modification to `apps/mutation-seam/scripts/preview_pm_planning_sources.py`
10. any Lane 502 implementation or admission

## Final Verdict

Lane 501 is closed as a successful no-write design packet.

The frozen design conclusion is specific: because the current workbook remains `flat_quote`, the truthful onboarding contract must derive proposed scopes from the existing seven section-backed workpackages while matching apparatus rows by preserved source candidate identity. That leaves Lane 502 with a bounded implementation surface: insert scopes from the frozen contract, update `seam.apparatus.scope_id` for matched rows only, and enforce the reconciliation report hash at admission time.