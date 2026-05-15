# PM Lane 030 Handoff - Project Data-Entry Tracker Lineage Preview

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-030`
Scope: Read-only project data-entry and tracker workbook lineage preview

## Summary

PM Lane 030 captures the historical post-estimator import layer. After estimator JSON export, PM or Operations used a project data-entry workbook to shape apparatus rows into a task-by-task and apparatus-by-apparatus plan.

Reference files:

1. `C:/Users/jjswe/Desktop/Project Miner PM Planning/RESA Power - Project Data Entry MASTER.xlsm`
2. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Garney- Central Mesa Reuse Tracker #677562.xlsm`

The implementation reads those workbooks as lineage evidence only. It does not run macros, write workbook cells, write Supabase, or reopen the old Dataverse import path.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane does not claim hosted PM live-data proof.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_tracker_sources.py`
2. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py`
3. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_tracker_sources.py`
4. `C:/APEX Platform/apex-power-ops-platform/docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
5. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
6. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-030-project-data-entry-tracker-lineage-preview.json`
7. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-030-project-data-entry-tracker-lineage-preview-handoff.md`

The implementation adds:

1. `project_tracker_sources.py` for read-only workbook parsing.
2. `Project_Form` metadata and workscope extraction.
3. `Task_Entry` parsing for scope, standard, task ID, task, apparatus, designation, drawing, and apparatus hours.
4. `All_Tasks` parsing for expanded task/apparatus plan context.
5. status, availability, apparatus-category, scope, and formula-error summaries.
6. active-row filtering so template formula residue is not counted as project work.
7. preview CLI overrides for data-entry and reference-tracker workbooks.
8. PM intake runbook documentation for the old `Task_Entry` to `All_Tasks` workflow.

## Workbook Roles

The workbook layer maps to the new PM lane as:

1. `Project_Form`: project metadata and work breakdown names.
2. `Task_Entry`: PM/Ops shaping surface for estimator apparatus rows.
3. `All_Tasks`: expanded task/apparatus plan with status, availability, completion, and hours.
4. `All_Tasks_Billing` and `PowerBI_Data`: downstream reporting/export surfaces.

The future APEX workflow should reproduce this as a governed import-candidate review rather than as direct Excel-to-database automation.

## Observed Current Planning Folder

Preview against the current planning folder resolved:

1. project data-entry master found: `true`
2. project data-entry `Task_Entry` rows: `14`
3. project data-entry active-looking `All_Tasks` rows: `234`
4. project data-entry formula-error rows: `234`
5. reference tracker found: `true`
6. reference tracker `Task_Entry` rows: `6`
7. reference tracker `All_Tasks` rows: `143`
8. reference tracker statuses: `COMPLETED=99`, `NOT STARTED=34`
9. reference tracker formula-error rows: `0`

## Validation

Passed:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_tracker_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_workbook_seed_reads.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_lane_seed.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" `
  -q

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_tracker_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py"

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --line-limit 2

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --format json `
  --line-limit 0

git diff --check
```

Result:

```text
Focused mutation-seam tests: 14 passed
py_compile: passed
Default planning preview with tracker summaries: passed
JSON planning-workbook preview: passed
```

## Publication And Host Parity

Publication and host parity are coordinator closeout duties for the commit containing this handoff:

1. push `clean-main`
2. fast-forward `/home/olares/code/apex/apex-power-ops-platform`
3. verify host head matches the published commit
4. verify host worktree status
5. verify `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`

## Guardrails Preserved

1. No SQL or schema migration.
2. No live database write.
3. No seed replay into Supabase.
4. No production import job.
5. No workbook writeback.
6. No workbook macro execution.
7. No Render deployment action.
8. No Vercel promotion.
9. No service admission.
10. No auth or ingress widening.
11. No package dependency addition.
12. No Excel MCP production runtime dependency.
13. No Dataverse import path reopening.
14. No assignment mutation.
15. No schedule mutation.
16. No status mutation.
17. No Operations Visibility reopening.
18. No AI helper mutation.
19. No AI service admission widening.
20. No autonomous AI business-state mutation.

## Next Bounded Move

The next PM lane should generate a read-only import-candidate artifact from estimator candidates plus project data-entry/tracker lineage.

That artifact should preserve source workbook/sheet/row traceability, proposed workpackage/task/apparatus grouping, dedupe keys, formula-error warnings, and a human approval checkpoint before any live Supabase write path is admitted.
