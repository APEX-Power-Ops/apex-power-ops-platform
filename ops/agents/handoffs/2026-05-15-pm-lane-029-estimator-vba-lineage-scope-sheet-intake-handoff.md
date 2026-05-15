# PM Lane 029 Handoff - Estimator VBA Lineage Scope-Sheet Intake

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-029`
Scope: Read-only estimator VBA lineage and scope-sheet intake support

## Summary

PM Lane 029 brings the old estimator-intake work back into the active PM lane as static mapping evidence. The historical VBA modules were reviewed, but their macros were not run.

Reference files:

1. `C:/APEX Platform/Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas`
2. `C:/APEX Platform/Reference_Files/Excel/Estimator VBA Modules/DataverseMappingVerification.bas`

The modules are Dataverse-era export/verification tools. Their durable value is the estimator workbook mapping: `Equipment Reference`, active scope sheets, scope metadata cells, apparatus row columns, and quantity expansion.

PM Lane 029 uses that mapping to support the larger Project Miner Building A/B estimator as a read-only intake preview source while preserving the PM Lane 028 flat `Updated`/`Quote Tab` path.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane does not claim hosted PM live-data proof and does not write Supabase.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_seed_sources.py`
2. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py`
3. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py`
4. `C:/APEX Platform/apex-power-ops-platform/docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
5. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
6. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-029-estimator-vba-lineage-scope-sheet-intake.json`
7. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-029-estimator-vba-lineage-scope-sheet-intake-handoff.md`

The implementation adds:

1. flat estimator source format metadata for `Updated`/`Quote Tab`.
2. scope-sheet source format metadata for `Equipment Reference` driven estimators.
3. active scope discovery from `Equipment Reference!L:M` with nonzero totals.
4. scope metadata capture from `C4`, `J3`, `M4`, and `P3`.
5. apparatus row extraction from columns `C`, `E`, `I`, and `J`.
6. source row and scope sheet context on extracted line items.
7. quantity expansion into one apparatus candidate per unit.
8. preview CLI overrides for estimator workbook, SLD PDF, equipment workbook, and capability workbook.
9. runbook lineage notes for the historical VBA modules.

## Observed Source Shapes

Current planning folder inspection showed:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm` has `Equipment Reference`, `Quote Tab`, and `Updated`, but no `Dataverse_Import`.
2. `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm` has `Equipment Reference` and named active scope sheets, but no `Dataverse_Import`, `Updated`, or `Quote Tab`.

The current reader now supports both shapes:

1. flat quote shape: `Updated` or `Quote Tab`.
2. scope-sheet shape: active sheets listed in `Equipment Reference!L:M`.

## Building A/B Preview Result

Preview against:

1. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`
2. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Building B IFC.pdf`

Resolved:

1. source format: `scope_sheets`
2. active scope sheets: `9`
3. line items: `122`
4. apparatus candidates: `5,400`
5. topology labels: `1`
6. crew rows: `15`
7. equipment inventory rows: `343`
8. standard tech list rows: `22`
9. capability rows: `50`

Active scope sheets:

1. `A1) Medium-Voltage - Core`
2. `A2) Medium-Voltage - Mech`
3. `A3) Medium-Voltage - Production`
4. `A4) Medium-Voltage - Spine`
5. `B1) Medium-Voltage - Mech`
6. `B2) Medium-Voltage - Production`
7. `B3) Medium-Voltage -Spine`
8. `Mod Chiller Plant - Bldg. A`
9. `Mod Chiller Plant - Bldg. B`

## Validation

Passed:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_workbook_seed_reads.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_lane_seed.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" `
  -q

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_seed_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py"

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --line-limit 2

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --estimator-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm" `
  --sld-pdf "C:/Users/jjswe/Desktop/Project Miner PM Planning/Building B IFC.pdf" `
  --line-limit 3

git diff --check
```

Result:

```text
Focused mutation-seam tests: 12 passed
py_compile: passed
Default Miner Temp preview: passed
Building A/B scope-sheet preview: passed
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
5. No Render deployment action.
6. No Vercel promotion.
7. No service admission.
8. No auth or ingress widening.
9. No package dependency addition.
10. No Excel MCP production runtime dependency.
11. No workbook macro execution.
12. No Dataverse import path reopening.
13. No assignment mutation.
14. No schedule mutation.
15. No status mutation.
16. No Operations Visibility reopening.
17. No AI helper mutation.
18. No AI service admission widening.
19. No autonomous AI business-state mutation.

## Next Bounded Move

The next PM lane should produce a reviewed import candidate artifact for the two New Mexico data-center projects from the preview output.

That artifact should remain read-only and should include dedupe keys, project/workpackage/task/apparatus candidate grouping, source workbook/sheet/row traceability, and a human approval checkpoint before any live Supabase write path is admitted.
