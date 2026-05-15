# PM Lane 028 Handoff - Project Miner Planning-Folder Intake Tooling

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-028`
Scope: Read-only Project Miner PM planning-folder intake tooling

## Summary

PM Lane 028 makes `C:/Users/jjswe/Desktop/Project Miner PM Planning` the preferred default local source root for the Project Miner PM lane intake readers. The existing explicit file overrides still win, and the legacy Desktop file defaults remain as fallback paths.

This lane also adds a no-write preview command so operators and agents can inspect the current planning source bundle before any later packet admits a live-data import or production mutation path.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane does not claim hosted PM live-data proof and does not write Supabase.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_seed_sources.py`
2. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/seed_workbooks.py`
3. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py`
4. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py`
5. `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_workbook_seed_reads.py`
6. `C:/APEX Platform/apex-power-ops-platform/docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
7. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
8. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-028-project-miner-planning-folder-intake-tooling.json`
9. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-028-project-miner-planning-folder-intake-tooling-handoff.md`

The implementation adds:

1. `APEX_PROJECT_MINER_PLANNING_ROOT` as the common planning-folder override.
2. planning-folder defaults for the estimator workbook and SLD PDF.
3. planning-folder defaults for the equipment inventory and technician capability matrix.
4. fallback preservation for the previous Desktop file defaults.
5. `preview_pm_planning_sources.py` for text or JSON read-only source previews.
6. focused tests proving planning-root discovery without explicit file env vars.
7. an operator runbook for day-to-day PM lane intake and Vercel/Render/Supabase separation.

## Observed Current Planning Folder

Preview against `C:/Users/jjswe/Desktop/Project Miner PM Planning` resolved:

1. project: `Miner Temp Power`
2. location: `Santa Teresa, NM`
3. drawing package: `SLD: E01-00, E01-01, E01-02`
4. issue date: `Dated: 03/05/2026`
5. source sheet: `Updated`
6. line items: `15`
7. apparatus candidates: `186`
8. topology labels: `138`
9. topology counts: `MVTX=22`, `MVS=8`, `PWR SKID=38`, `SWBD=22`, `LVPP=16`, `LVTX=32`
10. crew rows: `15`
11. equipment inventory rows: `343`
12. standard tech list rows: `22`
13. capability rows: `50`

## Tooling Decision

`sbroenne/mcp-server-excel` is useful for Windows/Excel operator work because it can inspect real `.xlsm` files through Excel COM, including formulas, formatting, PivotTables, charts, VBA, and Power Query surfaces.

It is not admitted as production runtime for this lane. It should remain optional workstation tooling unless a future packet explicitly authorizes installation and a bounded use case.

The existing Codex spreadsheet tooling is appropriate for generating review workbooks, dashboards, or QA artifacts after a packet requests that output. It is not needed for the live PM lane runtime.

The repo-owned baseline for intake remains deterministic `openpyxl` and `pypdf` readers inside `apps/mutation-seam`.

## Validation

Passed:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --format json

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_seed_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_workbook_seed_reads.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_lane_seed.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" `
  -q

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/project_seed_sources.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/seed_workbooks.py" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py"

git diff --check
```

Result:

```text
Focused mutation-seam tests: 11 passed
py_compile: passed
Text preview: passed
JSON preview: passed
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
12. No assignment mutation.
13. No schedule mutation.
14. No status mutation.
15. No Operations Visibility reopening.
16. No AI helper mutation.
17. No AI service admission widening.
18. No autonomous AI business-state mutation.

## Next Bounded Move

The next PM product move should convert the preview into a reviewed import candidate artifact or operator-facing project intake checklist for the two New Mexico data-center projects.

That follow-on should still be read-only until a separate packet explicitly admits a live Supabase import/write path and defines owner approval, dedupe, idempotency, and rollback behavior.
