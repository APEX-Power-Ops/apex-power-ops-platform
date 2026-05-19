# PM Lane 371 - Project Tracker All_Tasks Cache Lineage And UI Warning Alignment No-Live Packet

Date: 2026-05-19
Status: Local executed, no-live
Scope: Surface the Project Tracker `All_Tasks` cache-break explanation consistently in PM review UI and exports, and capture the workbook lineage mapping that explains the warning.

## Trigger

PM Lane 370 classified the Project Data Entry workbook issue more truthfully: `Task_Entry` source rows remain present, while every `All_Tasks` row carries the same cached `#REF!` failures across 15 workflow columns.

That backend classification was not yet visible in the PM route surfaces or repo-owned workbook-lineage documentation.

## Lane 371 Outcome

Selected outcome:

`PM_PROJECT_TRACKER_ALL_TASKS_CACHE_LINEAGE_AND_UI_WARNING_ALIGNMENT_LOCAL_CURRENT`

This lane keeps the workbook issue framed as a macro-built cache/build break instead of a generic source-workbook corruption signal.

## Workbook Lineage Map

Historical VBA evidence shows this workbook flow:

1. `Task_Entry` is the entered source sheet.
2. `BuildAll()` clones `Scope_Template`, writes parent and child rows, and injects workflow formulas into scope sheets.
3. `PopulateAllTasks_FromSheets(selectedSheets, appendMode)` flattens scope-sheet columns into `All_Tasks` columns A:U.
4. Downstream billing logic reads from `All_Tasks` into `All_Tasks_Billing`.

Exact failing `All_Tasks` columns in the current cache-break pattern:

- `Drawing`
- `Date Due`
- `Notes`
- `Assessment`
- `DATASHEET`
- `DATE COMPLETED`
- `NOTES2`
- `% COMPLETION`
- `TASK DELAYS`
- `Apparatus Hours`
- `Remaining Hours`
- `ACTUAL HOURS`
- `STATUS`
- `AVAILABILITY`
- `PRIORITY`

## Column Interpretation

| All_Tasks column | Workbook lineage | Why the failure points to cache/build break |
| --- | --- | --- |
| `Drawing` | `Task_Entry.G` -> scope child row `SC_COL_DRW` -> `All_Tasks.AT_COL_DRW` | This is copied through the macro path; if it fails uniformly while `Task_Entry` rows still exist, the build/cache surface is suspect rather than the source rows. |
| `Date Due` | scope workflow cell `SC_COL_DATE_DUE` -> `All_Tasks.AT_COL_DATE_DUE` | `BuildAll()` explicitly writes a due-date rollup formula into scope sheets before flattening. |
| `Notes` | `All_Tasks.AT_COL_NOTES` | `PopulateAllTasks.bas` currently writes this field as blank, so a workbook-wide `#REF!` here strongly suggests stale formula residue or workbook-version drift in the existing file, not missing source rows. |
| `Assessment` | scope workflow cell `SC_COL_ASSESSMENT` -> `All_Tasks.AT_COL_ASSESSMENT` | Flattened from scope-sheet workflow columns, not from direct PM route input. |
| `DATASHEET` | scope workflow cell `SC_COL_DATASHEET` -> `All_Tasks.AT_COL_DATASHEET` | Flattened from scope-sheet workflow columns. |
| `DATE COMPLETED` | scope workflow cell `SC_COL_DATE_COMP` -> `All_Tasks.AT_COL_DATE_COMP` | Carried from the macro-built scope sheet state. |
| `NOTES2` | scope workflow cell `SC_COL_NOTES` -> `All_Tasks.AT_COL_NOTES2` | Populated from the scope-sheet notes column, not from direct PM route entry. |
| `% COMPLETION` | scope workflow cell `SC_COL_PCT` -> `All_Tasks.AT_COL_PCT` | `BuildAll()` explicitly writes a child completion formula before flattening. |
| `TASK DELAYS` | scope workflow cell `SC_COL_DELAY` -> `All_Tasks.AT_COL_DELAY` | Flattened from scope-sheet workflow columns. |
| `Apparatus Hours` | `Task_Entry.H` -> scope child row `SC_COL_AHRS` -> `All_Tasks.AT_COL_AHRS` | Macro-carried numeric apparatus hours should still be recoverable from source rows when the cache breaks. |
| `Remaining Hours` | scope workflow cell `SC_COL_REMHRS` -> `All_Tasks.AT_COL_REMHRS` | Flattened from scope-sheet workflow columns. |
| `ACTUAL HOURS` | scope workflow cell `SC_COL_ACTHRS` -> `All_Tasks.AT_COL_ACTHRS` | Flattened from scope-sheet workflow columns. |
| `STATUS` | scope workflow cell `SC_COL_STATUS` -> `All_Tasks.AT_COL_STATUS` | `BuildAll()` explicitly writes the parent status formula and the scope sheet owns the workflow state that gets flattened. |
| `AVAILABILITY` | scope workflow cell `SC_COL_AVAIL` -> `All_Tasks.AT_COL_AVAIL` | Flattened from the scope-sheet workflow surface. |
| `PRIORITY` | scope workflow cell `SC_COL_PRIORITY` -> `All_Tasks.AT_COL_PRIORITY` | Flattened from the scope-sheet workflow surface. |

## Rebuild Sequence Indicated By The Lineage

The historical modules point to the workbook repair sequence, even though this lane does not execute it:

1. Treat `Task_Entry` as the source-of-truth capture surface.
2. Rebuild scope sheets from `Scope_Template` with `BuildAll()`.
3. Repopulate `All_Tasks` from the rebuilt scope sheets with `PopulateAllTasks_FromSheets(...)`.
4. Refresh any downstream billing sheet logic that assumes current `All_Tasks` values.

That sequence is materially narrower than re-triaging the PM candidate or treating the workbook warning as broad source corruption.

## UI And Export Alignment

Changed local PM review surfaces only:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
   - Adds support for `formula_error_pattern`, `formula_error_pattern_detail`, and `formula_error_vba_lineage_modules`.
   - Shows the cache-break explanation, workbook lineage modules, row/cell detail, and affected columns in Exception Review.
   - Threads the same detail into the intake exports so the warning survives outside the browser card.
2. `apps/operations-web/app/pm-review/import-candidate/page.tsx`
   - Shows the same cache-break explanation and workbook-lineage modules in Warning Review.
3. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
   - Updates the warning fixture and export assertions to the cache-break wording.
4. `apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts`
   - Updates the warning fixture to the cache-break wording and proves the new detail renders.

## Validation

Commands run:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts tests/browser-shell.pm-import-candidate.smoke.spec.ts
corepack pnpm --dir apps/operations-web typecheck
```

Validation result:

- Focused browser smokes: `2 passed`
- Operations-web typecheck: pass

## Guardrails

This lane does not:

1. execute workbook macros,
2. modify workbook files,
3. change mutation-seam hosted runtime,
4. promote operations-web hosted UI,
5. widen PM route authority,
6. create approval rows,
7. import project/work/task/apparatus rows,
8. assign leads, crews, or due dates,
9. change schedule or status,
10. create field, customer, finance, or production records,
11. call Supabase, Render, or Vercel mutations,
12. admit autonomous AI business-state mutation.

## Next Safe Move

If the deployed PM surfaces need the same wording, the next bounded move is a hosted publication lane for the already-local cache-break UI/export alignment and the hosted mutation-seam read surface that supplies the classified warning payload.
