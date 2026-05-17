# APEX PM Lane 224 - Project Miner Source Confirmation Question Packet No-Live

Date: 2026-05-17

Status: Local no-live source confirmation question packet

Decision label:

`PROJECT_MINER_SOURCE_CONFIRMATION_QUESTION_PACKET_NO_LIVE_NO_CONTENT_READ_NO_WRITE`

## Purpose

PM Lane 224 turns the Lane 223 source-authority hold into a compact Jason-facing question packet. The goal is to get the minimum useful source-role confirmation needed to keep Project Miner Temp Power planning moving without asking Jason to review technical packet structure.

This lane does not ask AI to infer source truth. It asks Jason to place each visible source item into one safe role bucket before any later source-content review, fingerprinting, approval, import, field, customer, production, or finance packet is admitted.

## Current Result

Current result:

`PROJECT_MINER_SOURCE_CONFIRMATION_QUESTION_PACKET_NO_LIVE_NO_CONTENT_READ_NO_WRITE`

Meaning:

1. The source-role blocker is now expressed as a short answer form.
2. The answer form is ready for Jason to complete in plain language.
3. No workbook or PDF content was opened.
4. No source role was inferred from filenames or metadata.
5. No Desktop Codex source classification prompt was dispatched.
6. No approval, import, field, customer, production, or finance authority was opened.

## Quick Answer Form

Jason can unblock the source-role branch by answering with this form:

```text
Current source candidates:
-

Reference only:
-

Resource context:
-

Unknown or stale:
-

Stop authority required:
-

Allowed for later bounded content review:
-

Must remain metadata-only:
-

Separate source package expected? yes/no/unknown:
-

Recommended next packet:
-

Notes:
-
```

Minimum useful answer:

1. name the current Temp Power estimator workbook,
2. name the current Temp Power drawing or drawing set,
3. identify the project data-entry workbook as current, reference-only, or stale,
4. mark the equipment and technician files as resource context, unknown/stale, or stop-authority-required,
5. identify anything that should not be opened later.

## Role Bucket Meanings

Use these buckets:

### `CURRENT_SOURCE_CANDIDATE`

The file belongs to the current Project Miner Temp Power source package. This permits a later bounded packet to ask for content review or fingerprint admission, but it does not approve import or field execution.

### `REFERENCE_ONLY`

The file helps explain a prior workflow, tracker pattern, example, or related context. It must not become current project source truth by implication.

### `RESOURCE_CONTEXT`

The file may help equipment, technician, material, or capability review later. It must not assign resources, direct field work, or create production state.

### `UNKNOWN_OR_STALE`

The file role, freshness, project fit, or source relationship is unclear. It should stay parked until clarified.

### `STOP_AUTHORITY_REQUIRED`

The file or question requires a separately admitted authority packet before it can be used.

## Source Questions

| Source item | Question for Jason | Allowed answer bucket |
| --- | --- | --- |
| `Estimator R3 - Project Miner Temp Power Testing.xlsm` | Is this the current Temp Power estimator source, a test workbook, or a scratch copy? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm` | Is this part of the current Project Miner work, a related/older estimator, or reference only? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `Miner Temp SLD-AP-BCARRASCO.pdf` | Is this the current Temp Power drawing source, related reference, or unknown/stale for active review? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `15_ELECTRICAL_COMBINED.pdf` | Is this part of the current Temp Power source package, reference only, or unknown/stale for active review? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `Building B IFC.pdf` | Is this current for the Project Miner Temp Power scope, related context, or not part of the current review? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `RESA Power - Project Data Entry MASTER.xlsm` | Is this still the intended workbook for turning estimator output into PM review rows? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `Garney- Central Mesa Reuse Tracker #677562.xlsm` | Is this reference-only process logic, a reusable tracker pattern, or active current project context? | `REFERENCE_ONLY`, `CURRENT_SOURCE_CANDIDATE`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `EQUIPMENT INVENTORY - 2026.xlsx` | Should this be treated as resource context for planning, unknown/stale, or stop-authority-required until a later resource packet? | `RESOURCE_CONTEXT`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `Phx Tech Testing Capability Matrix 032726.xlsx` | Should this be resource context only, unknown/stale, or stop-authority-required until a later resource-capability packet? | `RESOURCE_CONTEXT`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `DataverseExport.bas` | Is this still the intended export path for estimator-to-intake JSON, or historical reference only? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |
| `DataverseMappingVerification.bas` | Is this still the intended mapping verification path, or historical reference only? | `CURRENT_SOURCE_CANDIDATE`, `REFERENCE_ONLY`, `UNKNOWN_OR_STALE`, `STOP_AUTHORITY_REQUIRED` |

## What This Unblocks

A completed answer can unblock only the next no-live source branch:

1. source-role return intake,
2. later bounded content-review admission planning,
3. later resource-context review planning,
4. later import/approval prep planning.

It does not unblock:

1. source-content review,
2. durable source fingerprinting,
3. live approval POST,
4. approval-row creation,
5. project import,
6. task or workpackage creation,
7. assignments, schedule/status, field direction, durable field records, production tracking, customer reporting, or finance outputs.

## Return Intake Rule

When Jason returns this answer, classify it with the Lane 222 and Lane 223 rules. If the answer only names source-role buckets, the next packet should be:

`PM Lane 225 - Project Miner Source Confirmation Return Intake And Classification No-Live Packet`

If the answer asks to open source content, calculate fingerprints, import data, write approvals, direct field work, create customer commitments, or produce finance output, stop and prepare a separate authority-admission packet.

## Desktop Codex Sidecar Disposition

Desktop Codex remains parked for Project Miner source classification. The missing item is Jason source confirmation, not external AI analysis.

After Jason returns the source roles, Desktop Codex may become useful for a later bounded no-live scout only if a new PM packet explicitly admits a clear read scope and preserves no-write boundaries.

## Hard Stop Conditions

Any future executor must stop if:

1. work requires hosted proof, browser live route access, Supabase, Render, Vercel, Olares, credentials, or secrets,
2. work requires workbook content inspection, macro execution, workbook writeback, source PDF content review, or durable fingerprinting without a separately admitted packet,
3. work requires live approval POST, approval-row creation, project import, assignment, schedule/status, field, production, customer, or finance write,
4. source-role questions are treated as source-role confirmation,
5. returned source-role confirmation is treated as approval/import authority,
6. likely or provisional source roles are treated as confirmed without Jason confirmation,
7. local source metadata is treated as candidate fingerprint, source fingerprint, shape fingerprint, or current business-state truth,
8. a sidecar attempts to stage, commit, push, publish, or create PM business state,
9. any secret would be exposed in terminal output, markdown, packet JSON, screenshots, logs, or handoffs,
10. any AI agent attempts autonomous business-state mutation without a separately admitted packet.

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label and quick answer form references are present in all touched Lane 224 files.
3. All Lane 221 source items are present in the question packet.
4. Lane 221 bucket names are present.
5. Forbidden live/write paths remain explicitly blocked.
6. Corrupted-token scan passes.
7. Null-byte check passes.
8. `git diff --check` passes or reports only known line-ending warnings.
9. Staged diff includes only Lane 224 scoped docs, packet, handoff, closeout, and PM status/orchestration surfaces.

## Next Safe Packet

Next safe packet:

`PM Lane 225 - Project Miner Source Confirmation Return Intake And Classification No-Live Packet`

That packet should intake Jason's returned bucket assignments and classify the next no-live branch. It must not read workbook or PDF content, compute fingerprints, run macros, dispatch Desktop Codex source classification, access hosted services, admit approval/import, or create PM business state.

## No-Live Boundary

PM Lane 224 adds no product code, UI control, route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route access, live approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook content read, workbook macro/writeback, source PDF content read, durable source fingerprint, confirmed source-of-truth decision, Desktop Codex source classification dispatch, or autonomous AI business-state mutation.
