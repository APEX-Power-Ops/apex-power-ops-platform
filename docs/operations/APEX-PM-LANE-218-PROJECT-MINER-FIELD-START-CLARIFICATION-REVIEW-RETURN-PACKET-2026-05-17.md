# APEX PM Lane 218 - Project Miner Field-Start Clarification Review Return Packet

Date: 2026-05-17

Status: Local no-live clarification review return packet

Decision label:

`PROJECT_MINER_FIELD_START_CLARIFICATION_REVIEW_RETURN_NO_LIVE_NO_WRITE`

## Purpose

PM Lane 218 turns the Lane 217 direction decision into a practical no-live field-start clarification review return.

The approval first-row branch remains parked. This lane does not reopen approval or import authority. It packages the current Project Miner Temp Power review burden into source, customer/site, lead/resource, import-candidate, blocked-authority, and next-packet sections so Jason can bring back usable clarification without creating business state.

This lane is not live admission. It does not run hosted proof, open browser live routes, submit an approval POST, create an approval row, import a project, create notes, create tasks, assign owners or due dates, select leads, assign crews, issue field direction, create durable field records, or mutate downstream PM business state.

## Current Result

Current result:

`PROJECT_MINER_FIELD_START_CLARIFICATION_REVIEW_RETURN_NO_LIVE_NO_WRITE`

Meaning:

1. Project Miner clarification can be organized locally.
2. Local clarification is not business-state truth.
3. Source/customer/lead returns can be reviewed before any approval, import, field, production, customer, or finance write.
4. Anything requiring authority must move to a later bounded packet.

## Sidecar Review

A bounded sidecar review was used to test the dual-lane orchestration pattern without widening authority.

Sidecar recommendation:

`PROJECT_MINER_FIELD_START_CLARIFICATION_REVIEW_RETURN_NO_LIVE_NO_WRITE`

Adopted technical-authority decision:

1. Adopt the sidecar decision label as the formal repo label.
2. Keep Lane 218 no-code and use existing local field-start surfaces.
3. Do not add panels, controls, storage keys, routes, handlers, or exports.
4. Treat the next safe packet as a no-live closeout and next-packet selection, not a write or UI lane.

## Review Return Sections

The field-start clarification review return has these sections:

1. `Project Identity Snapshot`
2. `Source Evidence Review`
3. `Customer And Site Clarification`
4. `Lead And Resource Clarification`
5. `Import Candidate Context`
6. `Blocked Authority And No-Go List`
7. `Return Package For Codex Or Sidecar`
8. `Next Packet Decision Menu`

## Project Identity Snapshot

Use this section to keep the review anchored without treating local notes as production state.

Capture:

1. project name or working label,
2. customer,
3. site/location,
4. project phase,
5. Temp Power posture,
6. source files referenced,
7. identity questions still open.

Status label:

`UNVERIFIED_LOCAL_CONTEXT`

## Source Evidence Review

Use this section to identify what source evidence needs human review before approval or import can be considered.

Capture:

1. estimator export or workbook source,
2. drawing or tracker source,
3. source fingerprint needed later,
4. shape fingerprint needed later,
5. candidate identity question,
6. duplicate or risky source signals,
7. source rows that should not be treated as import-ready.

Boundary:

This section does not authorize source ingestion, direct workbook writeback, macro execution, database import, approval POST, or approval-row creation.

## Customer And Site Clarification

Use this section to capture what must be clarified with the customer/site contact before field-start execution can be considered.

Capture:

1. site access and escort path,
2. outage or shutdown windows,
3. safety and LOTO requirements,
4. work-hour constraints,
5. staging constraints,
6. customer promise stop-line,
7. customer questions that need a later bounded packet.

Boundary:

This section does not create customer commitments, customer reports, field instructions, action items, owners, due dates, or schedule/status writes.

## Lead And Resource Clarification

Use this section to capture what must be clarified with the field lead or internal resource path before field-start execution can be considered.

Capture:

1. field lead or lead-candidate context,
2. crew assumptions,
3. material readiness,
4. equipment readiness,
5. staging/resource constraints,
6. lead/resource authority stop-line,
7. lead/resource questions that need a later bounded packet.

Boundary:

This section does not select a lead, assign a crew, authorize field work, create schedule/status rows, create durable records, or create production tracking rows.

## Import Candidate Context

Use this section to summarize what the local review thinks the estimator/workbook output may propose.

Capture:

1. apparent project scope,
2. apparent work packages or task families,
3. apparent apparatus groups,
4. exception or duplicate signals,
5. risk signals,
6. missing source context,
7. why import remains blocked.

Boundary:

This section does not create import candidates, project rows, workpackages, tasks, apparatus rows, assignments, or approval records.

## Blocked Authority And No-Go List

Keep these blocked until a later explicit packet admits them:

1. hosted proof,
2. browser live route access,
3. live approval POST,
4. approval-row creation,
5. project import,
6. lead selection,
7. crew assignment,
8. schedule/status writes,
9. field authorization,
10. durable field records,
11. production tracking,
12. customer reporting,
13. completion evidence,
14. billing, payroll, invoice, accounting, or external finance output.

## Return Package For Codex Or Sidecar

When Jason brings clarification back, use this compact return shape:

```text
Project identity:

Source evidence reviewed:

Customer/site clarification:

Lead/resource clarification:

Import-candidate context:

Known no-go or blocked authority:

Requested next packet:
```

This return package is local review context only. It does not create notes, tasks, action items, owners, due dates, assignments, field instructions, approval records, import records, customer commitments, or finance outputs.

## Next Packet Decision Menu

After the clarification return, the next packet should be one of:

1. `HOLD_NO_LIVE`: keep review local.
2. `REFRESH_SOURCE_CONTEXT_NO_LIVE`: refresh source/candidate/fingerprint questions only.
3. `PREPARE_APPROVAL_ADMISSION_LATER`: prepare but do not execute approval admission.
4. `PREPARE_IMPORT_REVIEW_LATER`: prepare but do not execute import review.
5. `REQUEST_UI_SCAN_BURDEN_REVIEW`: only if Jason identifies a real scan-burden problem in the current local workbench.

## Dual-Lane Orchestration Posture

VS Code Codex remains PM lane technical authority and final repo integration authority.

Sidecars may:

1. review this return shape,
2. identify missing no-live clarification categories,
3. recommend whether a returned item belongs in source, customer/site, lead/resource, import-candidate, or future-packet buckets,
4. recommend the next safe bounded packet.

Sidecars may not:

1. access hosted services,
2. run macros,
3. read or print secrets,
4. stage, commit, push, or publish repo changes unless separately authorized,
5. treat clarification as business-state truth,
6. admit approval, import, assignment, field, customer, production, or finance authority.

## Hard Stop Conditions

Any future executor must stop if:

1. work requires hosted proof, browser live route access, Supabase, Render, Vercel, Olares, credentials, or secrets,
2. work requires live approval POST, approval-row creation, project import, task/workpackage/apparatus mutation, assignment, schedule/status write, field authorization, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance output,
3. the exact PM Lane 142 phrase is absent but an executor attempts to continue toward live approval,
4. local clarification is treated as current business-state truth,
5. a sidecar attempts to stage, commit, push, publish, or create PM business state,
6. any secret would be exposed in terminal output, markdown, packet JSON, screenshots, logs, or handoffs,
7. any AI agent attempts autonomous business-state mutation without a separately admitted packet.

## No-Live Boundary

PM Lane 218 adds no product code, UI control, route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route access, live approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook macro/writeback, secret exposure, or autonomous AI business-state mutation.

## Next Safe Packet

If no fresh live admission arrives, the next safe packet is:

`PM Lane 219 - Project Miner Field-Start Clarification Return Closeout And Next-Packet Selection`

PM Lane 219 should classify the returned clarification as hold, source refresh, later approval preparation, or later import review preparation without creating notes, tasks, owners, due dates, field instructions, approval records, import records, or downstream PM business state.
