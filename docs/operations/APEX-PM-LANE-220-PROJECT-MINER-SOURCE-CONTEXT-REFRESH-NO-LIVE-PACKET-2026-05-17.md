# APEX PM Lane 220 - Project Miner Source Context Refresh No-Live Packet

Date: 2026-05-17

Status: Local no-live source-context refresh packet

Decision label:

`PROJECT_MINER_SOURCE_CONTEXT_REFRESH_NO_LIVE_METADATA_ONLY_NO_WRITE`

## Purpose

PM Lane 220 refreshes the Project Miner source context that should inform the next PM intake decision without opening a live approval path, importing project rows, reading workbook contents, running macros, or treating local source files as business-state truth.

PM Lane 219 selected a source-context refresh as the next safe bounded move. This lane records the currently visible source package, the known estimator/export artifacts, the questions that still need human confirmation, and the next packet boundary.

## Current Result

Current result:

`PROJECT_MINER_SOURCE_CONTEXT_REFRESH_NO_LIVE_METADATA_ONLY_NO_WRITE`

Meaning:

1. The Project Miner planning folder is visible locally.
2. The known estimator export modules and PM planning workbooks exist at the expected local paths.
3. The source package has enough metadata-only context for a no-live source role confirmation packet.
4. No candidate fingerprint, source fingerprint, shape fingerprint, approval, import, task, assignment, field instruction, customer commitment, production record, or finance output was created.

## Metadata-Only Source Inventory

The following local directory was inspected by filename, size, and modified time only:

`C:\Users\jjswe\Desktop\Project Miner PM Planning`

| Source item | Size bytes | Last modified | Current lane interpretation |
| --- | ---: | --- | --- |
| `15_ELECTRICAL_COMBINED.pdf` | 315039039 | 2026-03-12 09:05:10 | Drawing/source reference candidate; content not opened. |
| `Building B IFC.pdf` | 530280550 | 2026-04-01 09:57:09 | Drawing/source reference candidate; content not opened. |
| `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm` | 1306791 | 2026-05-13 12:36:02 | Estimator workbook candidate; workbook not opened and macros not run. |
| `EQUIPMENT INVENTORY - 2026.xlsx` | 50762 | 2026-05-13 08:09:38 | Resource context candidate; workbook not opened. |
| `Estimator R3 - Project Miner Temp Power Testing.xlsm` | 914288 | 2026-05-15 05:42:08 | Temp Power estimator candidate; workbook not opened and macros not run. |
| `Garney- Central Mesa Reuse Tracker #677562.xlsm` | 4513105 | 2025-12-29 08:36:56 | Existing PM tracker/import-planning reference; workbook not opened and macros not run. |
| `Miner Temp SLD-AP-BCARRASCO.pdf` | 6223173 | 2026-04-16 20:14:30 | Temp Power drawing/source reference candidate; content not opened. |
| `Phx Tech Testing Capability Matrix 032726.xlsx` | 29557 | 2026-04-24 10:14:08 | Technician/resource context candidate; workbook not opened. |
| `RESA Power - Project Data Entry MASTER.xlsm` | 4202870 | 2026-05-15 13:31:14 | Project Data Entry planning workbook candidate; workbook not opened and macros not run. |

The following known workflow artifacts also exist:

1. `C:\APEX Platform\Reference_Files\Excel\Estimator VBA Modules\DataverseExport.bas`
2. `C:\APEX Platform\Reference_Files\Excel\Estimator VBA Modules\DataverseMappingVerification.bas`
3. `C:\Users\jjswe\Desktop\Project Miner PM Planning\Garney- Central Mesa Reuse Tracker #677562.xlsm`
4. `C:\Users\jjswe\Desktop\Project Miner PM Planning\RESA Power - Project Data Entry MASTER.xlsm`

Existence means only that the local files were present during this lane. It does not certify file contents, workbook formulas, macros, candidate identity, source freshness, or import readiness.

## Source Context Buckets

Use these buckets for the next review:

### `CURRENT_SOURCE_CANDIDATE`

Use only for files Jason confirms are part of the current Project Miner Temp Power source package.

### `REFERENCE_ONLY`

Use for files that help understand the workflow or prior planning process but are not the current source of truth.

### `RESOURCE_CONTEXT`

Use for inventory, technician, equipment, or capability context that may inform later planning but cannot assign resources or field work.

### `UNKNOWN_OR_STALE`

Use for files whose role, date, project fit, or source relationship is unclear.

### `STOP_AUTHORITY_REQUIRED`

Use for any file or question that requires live approval, project import, source-content certification, customer commitment, field instruction, assignment, schedule/status write, production tracking, or finance output.

## Human Confirmation Questions

These questions are the useful next PM review surface:

1. Which file is the current estimator source for the Temp Power work?
2. Is `Estimator R3 - Project Miner Temp Power Testing.xlsm` the current Temp Power estimator, a test workbook, or a scratch copy?
3. Is `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm` part of the current Project Miner work, or a related/older estimator reference?
4. Is `RESA Power - Project Data Entry MASTER.xlsm` still the intended apparatus/task planning workbook for turning estimator output into PM review rows?
5. Is `Garney- Central Mesa Reuse Tracker #677562.xlsm` an example/import-planning reference only, or does it still carry current process logic?
6. Which drawing files should be considered current for Temp Power scope review?
7. Are the two upcoming New Mexico data-center projects represented in this folder, or is a separate source package still expected?
8. Which source files may be safely opened later by an admitted review packet, and which should remain metadata-only?
9. Which source artifacts must be excluded from Git or only referenced as external local/Box sources?
10. What candidate identity should be used later, if and only if a separate no-write candidate review packet is admitted?

## Next Safe Packet

The next safe packet is:

`PM Lane 221 - Project Miner Source Artifact Role Confirmation No-Live Packet`

That packet should ask Jason or a bounded sidecar to classify the source items into the buckets above. It should not read workbook contents, run macros, compute durable fingerprints, open hosted routes, access Supabase/Render/Vercel/Olares, create approvals, import project rows, create notes/tasks/owners/due dates, issue field direction, create customer commitments, or mutate field/customer/finance state.

## Dual-Lane Orchestration Posture

VS Code Codex remains PM lane technical authority and final repo integration authority.

Sidecars may:

1. review repo-local PM lane surfaces,
2. inspect file metadata such as existence, filename, size, and modified time,
3. recommend source-role buckets,
4. identify missing confirmation questions,
5. flag authority-required items for stop/escalation.

Sidecars may not:

1. open workbook contents,
2. run macros,
3. read source PDF contents,
4. compute or publish durable source fingerprints unless separately admitted,
5. access hosted services,
6. stage, commit, push, or publish repo changes unless separately authorized,
7. treat local files as current PM business state,
8. admit approval, import, assignment, field, customer, production, or finance authority.

## Hard Stop Conditions

Any future executor must stop if:

1. work requires hosted proof, browser live route access, Supabase, Render, Vercel, Olares, credentials, or secrets,
2. work requires workbook content inspection, macro execution, workbook writeback, or source PDF content review outside a separately admitted packet,
3. work requires live approval POST, approval-row creation, project import, assignment, schedule/status, field, production, customer, or finance write,
4. the exact PM Lane 142 phrase is absent but an executor attempts to continue toward live approval,
5. local source metadata is treated as candidate fingerprint, source fingerprint, shape fingerprint, or current business-state truth,
6. a sidecar attempts to stage, commit, push, publish, or create PM business state,
7. any secret would be exposed in terminal output, markdown, packet JSON, screenshots, logs, or handoffs,
8. any AI agent attempts autonomous business-state mutation without a separately admitted packet.

## No-Live Boundary

PM Lane 220 adds no product code, UI control, route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route access, live approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook content read, workbook macro/writeback, source PDF content read, durable source fingerprint, secret exposure, or autonomous AI business-state mutation.
