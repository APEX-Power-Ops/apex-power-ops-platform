# PM Lane Project Miner Intake Workflow

Date: 2026-05-15
Status: Active operator workflow
Scope: Project Miner planning-folder intake into the PM lane

## Purpose

This runbook explains how a real project starts in the PM lane using the current APEX Ops deployment model:

`Vercel UI -> Render mutation seam/API -> Supabase DB`

The Vercel URL is the user-facing PM application. Render is the governed API boundary between the UI and Supabase. Supabase is the data store and must not be treated as the user-facing workflow surface.

Companion operating plan:

`docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`

Companion visual map:

`docs/operations/APEX-OPS-VISUAL-SYSTEM-MAP-2026-05-15.md`

Start with the visual map when the platform split, PM workflow, or AI orchestration lanes are easier to understand as diagrams than as prose.

Companion acceleration lane:

`docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`

Use the acceleration lane when deciding whether a PM workflow step is actually helping. The PM lane should reduce Jason's coordination burden, not add another process he has to manually carry.

Use that plan for the Temp Power delivery target, Olares One orchestration posture, dual-lane execution rules, and capability-gap escalation duty.

## Current Source Packet

Default local planning root:

`C:/Users/jjswe/Desktop/Project Miner PM Planning`

Current files observed in that root:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
2. `Miner Temp SLD-AP-BCARRASCO.pdf`
3. `EQUIPMENT INVENTORY - 2026.xlsx`
4. `Phx Tech Testing Capability Matrix 032726.xlsx`
5. `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`
6. `15_ELECTRICAL_COMBINED.pdf`
7. `Building B IFC.pdf`
8. `RESA Power - Project Data Entry MASTER.xlsm`
9. `Garney- Central Mesa Reuse Tracker #677562.xlsm`

The current seeded PM lane starts from the smaller Miner Temp Power estimator and SLD package. The larger Building A/B estimator and IFC drawing sets are treated as next-project source evidence until a dedicated packet promotes them into the runtime seed.

## Day-To-Day Startup Flow

1. Collect source files into one planning folder.
2. Run the read-only preview command.
3. Review project name, location, drawing package, estimator sheet, line-item count, apparatus candidate count, crew count, equipment inventory rows, and capability rows.
4. Open `https://operations.apexpowerops.com/pm-review/workfront` for the user-facing PM workfront.
5. PM reviews readiness, blockers, unassigned rows, submitted snapshots, drillthrough links, and review signals.
6. Lead and field users work through `/lead-ops` and `/field-tech`.
7. Render mutation seam owns any governed API behavior or state transition.
8. Supabase persists project state after an admitted packet opens the relevant live-data write path.

## Preview Command

From `C:/APEX Platform/apex-power-ops-platform`:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

JSON output for downstream inspection:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --format json
```

To preview a specific estimator/PDF pair from the same planning folder:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --estimator-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm" `
  --sld-pdf "C:/Users/jjswe/Desktop/Project Miner PM Planning/Building B IFC.pdf"
```

To include explicit project data-entry or reference tracker workbooks:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_planning_sources.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --data-entry-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/RESA Power - Project Data Entry MASTER.xlsm" `
  --reference-tracker-workbook "C:/Users/jjswe/Desktop/Project Miner PM Planning/Garney- Central Mesa Reuse Tracker #677562.xlsm"
```

The command is read-only. It does not write to Supabase, mutate schedules, assign work, change statuses, or run Excel macros.

## Import Candidate Preview

PM Lane 032 adds a review-ready import candidate preview for Project Miner Temp Power.

Run it from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

JSON output for PM review or downstream UI work:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/preview_pm_import_candidate.py" `
  --planning-root "C:/Users/jjswe/Desktop/Project Miner PM Planning" `
  --format json
```

The same read-only candidate is exposed from the mutation seam at:

`GET /api/v1/reads/project-import-candidate`

The PM-facing review route is:

`https://operations.apexpowerops.com/pm-review/import-candidate`

Local or preview environments expose the same route at:

`/pm-review/import-candidate`

Current Temp Power local preview result:

1. 7 proposed workpackages,
2. 15 proposed tasks,
3. 186 apparatus candidates,
4. 15 crew,
5. 343 equipment inventory rows,
6. 50 capability rows,
7. 2 review signals: one missing-designation information item and one project-data-entry formula-warning item.

This import candidate is a review artifact only. It does not write Supabase rows, assign work, change status, mutate schedules, run Excel macros, or approve a project import.

PM Lane 034 hardens the same review route without admitting persistence:

1. source stat fingerprints show the source path, file size, modified time, availability, and aggregate candidate freshness key,
2. warning filters let PM review all, blocker, warning, info, or specific warning-code subsets without fetching or mutating data,
3. JSON export downloads the current read-only candidate plus the local PM draft notes for offline review or sidecar handoff,
4. PM questions draft is retained only in the local browser and is not approval, import, Supabase state, or a server-side note.

## Import Admission Plan

PM Lane 035 adds a read-only import-admission plan before any import mutation exists.

The read seam is:

`GET /api/v1/reads/project-import-admission-plan`

The PM-facing plan route is:

`/pm-review/import-admission-plan`

Hosted PM intake UI route:

`https://operations.apexpowerops.com/pm-review/import-admission-plan`

This route explains the future import gate:

1. approval record contract,
2. deterministic idempotency key strategy,
3. preview-to-import diff checks,
4. no-go checks,
5. target row counts,
6. future import sequence,
7. actions that remain disallowed.

This is not an approval screen and not an import screen. It does not persist approval, write Supabase rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## Import Approval Contract

PM Lane 038 adds a read-only approval-persistence contract before any approval record can be stored.

The read seam is:

`GET /api/v1/reads/project-import-approval-contract`

This contract explains the future approval packet in machine-checkable form:

1. candidate id, version, source fingerprint, shape fingerprint, and idempotency key that must match,
2. permitted PM decisions,
3. required approval fields,
4. warning codes the PM must accept exactly,
5. human-acceptance no-go checks that may be acknowledged,
6. non-overridable no-go checks that still block import,
7. decision payload template,
8. validation matrix,
9. future mutation contract placeholder.

The backend also includes a pure local validator for this approval payload. The validator rejects stale fingerprints, changed warning-code sets, unsupported decisions, missing PM actor/timestamp fields, empty review notes, and attempts to override non-overridable checks.

This is still not approval persistence and not import. It does not write Supabase rows, store PM notes, import project rows, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## Hosted Intake Parity Status

PM Lane 036 promoted the operations-web PM intake routes to Vercel production:

1. `https://operations.apexpowerops.com/pm-review/import-candidate`
2. `https://operations.apexpowerops.com/pm-review/import-admission-plan`

Hosted route smoke passed with both markers present.

The matching Render mutation-seam routes are not yet hosted-current:

1. `https://mutation-seam.apexpowerops.com/health` returns `200`,
2. hosted OpenAPI does not list `/api/v1/reads/project-import-candidate`,
3. hosted OpenAPI does not list `/api/v1/reads/project-import-admission-plan`,
4. both PM intake read routes currently return `404`.

This means the user-facing pages are visible, but hosted live intake data remains blocked until a Render-authenticated mutation-seam redeploy and log inspection closes the backend parity gap.

PM Lane 037 refreshes the Render-authenticated executor packet for this exact blocker and adds backend-only smoke coverage:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" `
  "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" `
  --base-url "https://mutation-seam.apexpowerops.com" `
  --include-pm-intake
```

That smoke should remain red until Render serves the current mutation-seam code. It checks the existing health, approval, and schedule reads plus the PM intake OpenAPI paths and read-only payload shape.

After PM Lane 038, the same flag also checks:

1. OpenAPI registration of `/api/v1/reads/project-import-approval-contract`,
2. `GET /api/v1/reads/project-import-approval-contract`,
3. approval-contract payload fields including `mutation_authority` and `persistence_authority`.

## Environment Overrides

Set this when using a different planning folder:

```powershell
$env:APEX_PROJECT_MINER_PLANNING_ROOT = "C:/Users/jjswe/Desktop/Project Miner PM Planning"
```

Specific file overrides still take precedence:

```powershell
$env:APEX_PROJECT_ESTIMATOR_WORKBOOK = "C:/path/to/Estimator.xlsm"
$env:APEX_PROJECT_SLD_PDF = "C:/path/to/SLD.pdf"
$env:APEX_FIELD_SEED_EQUIPMENT_WORKBOOK = "C:/path/to/EQUIPMENT INVENTORY - 2026.xlsx"
$env:APEX_FIELD_SEED_CAPABILITY_WORKBOOK = "C:/path/to/Phx Tech Testing Capability Matrix 032726.xlsx"
$env:APEX_PROJECT_DATA_ENTRY_WORKBOOK = "C:/path/to/RESA Power - Project Data Entry MASTER.xlsm"
$env:APEX_REFERENCE_TRACKER_WORKBOOK = "C:/path/to/Garney- Central Mesa Reuse Tracker #677562.xlsm"
```

## Excel MCP Tooling Posture

`sbroenne/mcp-server-excel` is useful as a workstation-side operator accelerator because it controls real Microsoft Excel through COM. It is a good fit for:

1. visually inspecting `.xlsm` estimator tabs,
2. verifying formulas and calculated quantities,
3. exporting screenshots for human review,
4. reviewing PivotTables, charts, Power Query, VBA, and formatting,
5. helping an agent map workbook rows into clean PM intake records.

It is not part of the production runtime:

1. no Render dependency,
2. no Vercel dependency,
3. no Supabase direct-write authority,
4. no server-side batch processing requirement,
5. no macro execution unless explicitly approved by a packet and a human operator.

The repo-owned baseline remains `openpyxl` and `pypdf` inside `apps/mutation-seam` for deterministic read-only intake preview. Excel MCP may be installed separately in VS Code or another MCP client when live Excel interaction is useful.

The built-in Codex spreadsheet tooling is appropriate for producing human-review workbooks, dashboards, or import QA summaries after a packet requests that artifact. It is not required for the live PM lane runtime and should not replace the deterministic seed readers without a bounded packet.

## Estimator VBA Lineage

Earlier estimator-intake work produced two VBA modules under:

1. `C:/APEX Platform/Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas`
2. `C:/APEX Platform/Reference_Files/Excel/Estimator VBA Modules/DataverseMappingVerification.bas`

Those modules are Dataverse-era artifacts and should not be treated as the current production import path. Their value is the workbook mapping they preserve:

1. metadata originally came from a `Dataverse_Import` sheet,
2. scope totals came from `Equipment Reference`,
3. active scope sheets were listed in `Equipment Reference!L:M`,
4. scope-level fields used `C4`, `J3`, `M4`, `P3`, and `P4`,
5. apparatus line rows used `C` for quantity, `E` for equipment type, `I` for hours per unit, and `J` for total hours,
6. each quantity greater than one expanded into one apparatus candidate per unit.

Current Project Miner workbooks no longer include `Dataverse_Import`, but they do still include `Equipment Reference`. The PM lane reader therefore supports two read-only estimator shapes:

1. flat quote shape: `Updated` or `Quote Tab`,
2. scope-sheet shape: active sheets listed in `Equipment Reference!L:M`.

The VBA files remain static reference evidence only. Do not run their macros as part of PM lane intake.

## Project Data-Entry Workbook Lineage

After the Dataverse JSON export, the old process used workbook tooling to turn streamlined estimator apparatus rows into a task-by-task and apparatus-by-apparatus project plan. The two reference files in the current planning folder are:

1. `C:/Users/jjswe/Desktop/Project Miner PM Planning/RESA Power - Project Data Entry MASTER.xlsm`
2. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Garney- Central Mesa Reuse Tracker #677562.xlsm`

The master workbook is the blank or reusable shaping surface. The Garney tracker is a populated example of the downstream project plan.

Important sheet roles:

1. `Project_Form` stores client, project, job number, start date, site, contact, project lead, and workscope names.
2. `Task_Entry` is the transitional import/input table with `Scope`, `NETA_Standard`, `Task_ID`, `Task`, `Apparatus`, `Designation`, `Drawing`, and `Apparatus_Hourrs`.
3. `All_Tasks` is the expanded task/apparatus plan with due date, notes, assessment, datasheet, completion, delays, hours, status, availability, priority, and apparatus category.
4. `All_Tasks_Billing` and `PowerBI_Data` are downstream reporting/export surfaces.

The PM lane preview now reads those workbooks as historical workflow evidence and reports project form metadata, workscope names, `Task_Entry` counts, `All_Tasks` counts, status counts, availability counts, apparatus-category counts, and formula-error counts. It does not write back to the workbooks.

The new PM lane should recreate this workflow as a governed review/import candidate:

1. estimator source rows become normalized apparatus candidates,
2. PM/Ops groups or accepts them into task rows,
3. the system preserves source workbook, sheet, and row traceability,
4. a human approves the import candidate,
5. only then may a later admitted packet write project, workpackage, task, and apparatus rows into Supabase.

## Current Delivery Target

Project Miner Temp Power is the first live PM lane pilot.

The near-term target is not a generic PM system demo. The target is a field-usable workflow before the late-May or early-June 2026 Temp Power start window.

Current priority order:

1. Render-authenticated mutation-seam parity for the new PM intake read endpoints through PM Lane 037,
2. PM Lane 038 approval-contract review and storage decision while keeping persistence unadmitted,
3. approval-persistence mutation only after hosted reads are current and explicit packet admission exists,
4. narrow idempotent import mutation only after human approval and explicit packet admission,
5. PM, Lead, and Field pilot on a bounded Temp Power slice.

Olares One should support this by reducing relay friction, preserving host validation, and keeping packet/handoff evidence durable. It is not currently assumed to provide autonomous AI-to-AI queue ownership.

## Workflow Levels

Level 0 - Source Intake:
Validate the planning folder exists and the preview command resolves the expected estimator, PDF, equipment inventory, capability matrix, project data-entry workbook, and reference tracker.

Level 1 - Scope Extraction:
Read estimator line items into project, workpackage, task, and apparatus candidates. Preserve drawing references, designations, source sheet names, scope sheet names, and source row references where available.

Level 2 - Task Plan Shaping:
Transform estimator apparatus candidates into task-by-task and apparatus-by-apparatus import candidates, mirroring the old `Task_Entry` to `All_Tasks` workflow without writing production state.

Level 2A - Import Candidate Review Hardening:
Review source freshness, warning filters, exported candidate JSON, and local PM questions before any import mutation is admitted.

Level 2B - Import Admission Planning:
Review the approval contract, idempotency key, diff checks, target rows, and no-go checks that a later import packet must satisfy.

Level 2C - Approval Contract Design:
Define and validate the PM approval packet shape, candidate fingerprints, warning acceptance, human-acceptance no-go acknowledgements, actor/timestamp fields, and reviewer notes before any approval persistence exists.

Level 2D - Approval Persistence:
Persist only the PM approval decision, candidate fingerprints, warning acceptance, no-go acknowledgement notes, and reviewer notes for the import candidate after a later packet admits a narrow storage path. This is not an import mutation and must not write project, workpackage, task, or apparatus rows.

Level 3 - Resource Context:
Read equipment inventory and technician capability rows so PM can understand whether the project can be staffed with available people and equipment.

Level 4 - PM Workfront:
Surface readiness, blockers, unassigned rows, PM review rows, submitted snapshots, review signals, and drillthrough links in the Vercel UI.

Level 5 - Lead/Field Execution:
Lead assigns work and field updates apparatus/checklist/issue progress through governed mutation-seam endpoints only after the relevant write path is admitted.

Level 6 - PM Review And Closeout:
PM reviews escalations, submitted snapshots, task/workpackage review, disposition history, schedule drillthroughs, and variance context before approving or returning work.

## Guardrails

1. Do not write directly from Excel to Supabase.
2. Do not treat spreadsheet rows as production state until an admitted packet opens a live-data import or write path.
3. Do not run workbook macros during read-only intake preview.
4. Do not write back to estimator, data-entry, or tracker workbooks during read-only preview.
5. Do not let Vercel become a second backend authority.
6. Do not let AI auto-assign apparatus, change statuses, mutate schedules, or write PM business state until a later packet explicitly admits that authority.
