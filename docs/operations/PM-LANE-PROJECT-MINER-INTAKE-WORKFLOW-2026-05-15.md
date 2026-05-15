# PM Lane Project Miner Intake Workflow

Date: 2026-05-15
Status: Active operator workflow
Scope: Project Miner planning-folder intake into the PM lane

## Purpose

This runbook explains how a real project starts in the PM lane using the current APEX Ops deployment model:

`Vercel UI -> Render mutation seam/API -> Supabase DB`

The Vercel URL is the user-facing PM application. Render is the governed API boundary between the UI and Supabase. Supabase is the data store and must not be treated as the user-facing workflow surface.

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

The command is read-only. It does not write to Supabase, mutate schedules, assign work, change statuses, or run Excel macros.

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

## Workflow Levels

Level 0 - Source Intake:
Validate the planning folder exists and the preview command resolves the expected workbook, PDF, equipment inventory, and capability matrix.

Level 1 - Scope Extraction:
Read estimator line items into project, workpackage, task, and apparatus candidates. Preserve drawing references and designations.

Level 2 - Resource Context:
Read equipment inventory and technician capability rows so PM can understand whether the project can be staffed with available people and equipment.

Level 3 - PM Workfront:
Surface readiness, blockers, unassigned rows, PM review rows, submitted snapshots, review signals, and drillthrough links in the Vercel UI.

Level 4 - Lead/Field Execution:
Lead assigns work and field updates apparatus/checklist/issue progress through governed mutation-seam endpoints only after the relevant write path is admitted.

Level 5 - PM Review And Closeout:
PM reviews escalations, submitted snapshots, task/workpackage review, disposition history, schedule drillthroughs, and variance context before approving or returning work.

## Guardrails

1. Do not write directly from Excel to Supabase.
2. Do not treat spreadsheet rows as production state until an admitted packet opens a live-data import or write path.
3. Do not run workbook macros during read-only intake preview.
4. Do not let Vercel become a second backend authority.
5. Do not let AI auto-assign apparatus, change statuses, mutate schedules, or write PM business state until a later packet explicitly admits that authority.
