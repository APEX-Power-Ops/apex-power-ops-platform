# PM Lane 032 Handoff - Temp Power Import Candidate Review

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-032`
Scope: Read-only Project Miner Temp Power import candidate review

## Summary

PM Lane 032 creates the first review-ready Project Miner Temp Power import candidate.

The candidate turns the existing read-only planning folder inputs into proposed workpackages, tasks, and apparatus candidates with source traceability, warning summaries, and human decision prompts. It is designed to reduce Jason's review burden: the PM can inspect exceptions and proposed grouping before any database write path is admitted.

This is not an import mutation. The candidate keeps `mutation_authority: not_admitted`.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_import_candidate.py`
2. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_seed_sources.py`
3. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/routers/reads.py`
4. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py`
5. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_import_candidate.py`
6. `C:/APEX Platform/apex-power-ops-platform/docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
7. `C:/APEX Platform/apex-power-ops-platform/docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
8. `C:/APEX Platform/apex-power-ops-platform/docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
9. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
10. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-032-sidecar-import-candidate-review-scout-handoff.md`
11. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-032-temp-power-import-candidate-review.json`
12. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-032-temp-power-import-candidate-review-handoff.md`

The implementation adds:

1. a read-only import-candidate builder,
2. source row traceability from flat estimator rows into line items and apparatus candidates,
3. `GET /api/v1/reads/project-import-candidate`,
4. `apps/mutation-seam/scripts/preview_pm_import_candidate.py`,
5. candidate grouping into workpackages, tasks, and apparatus candidates,
6. warning and human-decision summaries,
7. explicit no-mutation review guidance,
8. focused tests for grouping, traceability, warning surfacing, and endpoint posture.

## Sidecar Scout

The external Codex Desktop sidecar produced a handoff-only UI/workflow scout:

`C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-032-sidecar-import-candidate-review-scout-handoff.md`

The scout stayed inside guardrails: no product code edits, no staging, no commits, no macros, and no Supabase, Render, or Vercel access.

Accepted PM Lane 033 guidance from the scout:

1. make the review surface exception-first,
2. show candidate summary and required decisions before dense row tables,
3. keep clean rows collapsible,
4. show warning and duplicate context at the top,
5. preserve source traceability without forcing workbook inspection,
6. keep approval/import mutation out of the first UI tranche.

## Real Temp Power Preview

Command:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

Observed result:

1. candidate `pm-import-candidate-miner-temp-power`,
2. project `Miner Temp Power`,
3. location `Santa Teresa, NM`,
4. source format `flat_quote`,
5. 7 proposed workpackages,
6. 15 proposed tasks,
7. 186 apparatus candidates,
8. 15 crew,
9. 343 equipment inventory rows,
10. 50 capability rows,
11. 2 review signals.

Warnings:

1. `MISSING_DESIGNATIONS`: 1 estimator line item does not have an explicit designation.
2. `PROJECT_DATA_ENTRY_FORMULA_ERRORS`: 234 project-data-entry planning-workbook rows include formula errors across 3510 cells.

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
13. No durable AI queue admission.
14. No `ai_tasks` ownership admission.
15. No Dataverse import path reopening.
16. No assignment mutation.
17. No schedule mutation.
18. No status mutation.
19. No Operations Visibility reopening.
20. No autonomous AI business-state mutation.

## Validation

Passed:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_import_candidate.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_tracker_sources.py"

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_import_candidate.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py"

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-032-temp-power-import-candidate-review.json', encoding='utf-8')); print('packet-json-ok')"

git diff --check
```

Results:

```text
9 passed
py_compile passed
real Temp Power preview passed
packet-json-ok
git diff --check passed
```

## Capability Gaps

Known gaps carried forward:

1. Hosted Render mutation-seam parity is still needed before hosted PM proof or production import proof.
2. Excel MCP remains optional operator acceleration only; the runtime path remains deterministic Python readers.
3. The import mutation is still not admitted.
4. Workbook macro execution is still not admitted.

## Next Bounded Move

Recommended next product move:

`PM Lane 033 - Import Candidate PM UI Review`

Goal: surface this read-only candidate in the PM UI so Jason can review workpackages, tasks, apparatus counts, source traceability, warnings, and human-decision prompts without reading raw JSON.
