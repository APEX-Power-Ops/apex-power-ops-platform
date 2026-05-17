# APEX PM Lane 219 - Project Miner Field-Start Clarification Return Closeout And Next-Packet Selection

Date: 2026-05-17

Status: Local no-live clarification classifier packet

Decision label:

`PROJECT_MINER_FIELD_START_CLARIFICATION_RETURN_CLOSEOUT_NEXT_PACKET_SELECTION_NO_LIVE_NO_WRITE`

## Purpose

PM Lane 219 closes the current field-start clarification return shape by adding a no-live classifier for whatever Jason brings back later.

PM Lane 218 created the return package. Lane 219 defines how to sort that return without creating notes, tasks, owners, due dates, approvals, imports, field instructions, customer commitments, or finance outputs.

This lane does not assume returned clarification already exists. It only defines the classification path that should be used after a clarification return is provided.

## Current Result

Current result:

`PROJECT_MINER_FIELD_START_CLARIFICATION_RETURN_CLOSEOUT_NEXT_PACKET_SELECTION_NO_LIVE_NO_WRITE`

Meaning:

1. The Lane 218 return package is ready for Jason or a bounded sidecar.
2. Returned clarification remains local review context only.
3. The next packet must be selected from an explicit classifier, not inferred by AI.
4. No approval, import, assignment, schedule/status, field, production, customer, or finance write is admitted.

## Sidecar Review

A bounded sidecar review was used to test the dual-lane orchestration pattern without widening authority.

Sidecar recommendation:

`PROJECT_MINER_FIELD_START_CLARIFICATION_RETURN_CLOSEOUT_NEXT_PACKET_SELECTION_NO_LIVE_NO_WRITE`

Adopted technical-authority decision:

1. Adopt the sidecar decision label as the formal repo label.
2. Use four primary classifier buckets: hold, source refresh, later approval prep, and later import prep.
3. Treat customer/site and lead/resource details as context flags unless Jason's return specifically justifies a later dedicated packet.
4. Keep UI scan-burden review gated behind a concrete Jason-identified scan-burden issue.

## What This Lane Closes Out

Lane 219 closes out these questions from Lane 218:

1. How should returned source/customer/lead clarification be classified?
2. Which returned items can remain local?
3. Which returned items require a later bounded packet?
4. Which returned items must stop because they require live authority?
5. Which next packet is safe when no returned clarification exists yet?

It does not close out the actual field-start clarification, because Jason has not yet provided a current returned clarification package.

## Clarification Classifier

Use exactly one primary classifier and any needed context flags.

### `HOLD_NO_LIVE`

Use when the return contains no new actionable clarification or Jason wants to keep review local.

Allowed next move:

`PM Lane 220 - Project Miner Source Context Refresh No-Live Packet`

### `REFRESH_SOURCE_CONTEXT_NO_LIVE`

Use when returned items are about source files, estimator exports, workbooks, drawings, tracker context, candidate identity, source fingerprint, shape fingerprint, duplicate signals, or risky source rows.

Allowed next move:

`PM Lane 220 - Project Miner Source Context Refresh No-Live Packet`

### `PREPARE_APPROVAL_ADMISSION_LATER`

Use only when Jason explicitly asks to prepare a later approval-admission packet while keeping live execution blocked.

Allowed next move:

`PM Lane 222 - Approval Admission Prep No-Execute Packet`

### `PREPARE_IMPORT_REVIEW_LATER`

Use only when Jason explicitly asks to prepare a later import review packet while keeping import execution blocked.

Allowed next move:

`PM Lane 223 - Import Review Prep No-Execute Packet`

### Context Flags

Use any of these context flags alongside the primary classifier:

1. `CUSTOMER_SITE_CONTEXT`: access, escorts, outages, shutdown windows, safety, LOTO, work windows, staging, site constraints, or customer/site questions.
2. `LEAD_RESOURCE_CONTEXT`: field lead context, crew assumptions, material readiness, equipment readiness, staging limits, resource constraints, or internal lead/resource questions.
3. `UI_SCAN_BURDEN_SIGNAL`: only if Jason identifies a concrete scan-burden issue in the current local workbench.
4. `STOP_AUTHORITY_REQUIRED`: any returned item asks for or implies live approval, project import, assignment, field direction, customer commitment, production tracking, billing, payroll, invoice, accounting, hosted proof, credentials, or any business-state mutation.

## Default Selection

If no returned clarification exists yet, the default selection is:

`HOLD_NO_LIVE`

The next safe packet is:

`PM Lane 220 - Project Miner Source Context Refresh No-Live Packet`

This is a no-live prompt packet only. It should help Jason gather source/candidate/fingerprint questions without opening approval, import, field, customer, production, or finance authority.

## Closeout Template

When a returned clarification package exists, classify it with this template:

```text
Returned clarification present:

Primary classifier:

Context flags:

Source context status:

Customer/site context status:

Lead/resource context status:

Authority required:

Recommended next packet:

Stop conditions triggered:
```

This template is local review context only. It does not create notes, tasks, owners, due dates, field instructions, approval records, import records, customer commitments, durable field records, production rows, or finance outputs.

## Dual-Lane Orchestration Posture

VS Code Codex remains PM lane technical authority and final repo integration authority.

Sidecars may:

1. classify returned text into the Lane 219 buckets,
2. identify missing no-live clarification categories,
3. recommend the next safe bounded packet,
4. flag authority-required items for stop/escalation.

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
2. work requires live approval POST, approval-row creation, project import, task/workpackage/apparatus mutation, assignment, schedule/status write, field authorization, field instruction, durable field record, production tracking, customer commitment, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance output,
3. the exact PM Lane 142 phrase is absent but an executor attempts to continue toward live approval,
4. local clarification is treated as current business-state truth,
5. a sidecar attempts to stage, commit, push, publish, or create PM business state,
6. any secret would be exposed in terminal output, markdown, packet JSON, screenshots, logs, or handoffs,
7. any AI agent attempts autonomous business-state mutation without a separately admitted packet.

## No-Live Boundary

PM Lane 219 adds no product code, UI control, route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route access, live approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook macro/writeback, secret exposure, or autonomous AI business-state mutation.

## Next Safe Packet

If no fresh live admission or returned clarification arrives, the next safe packet is:

`PM Lane 220 - Project Miner Source Context Refresh No-Live Packet`

PM Lane 220 should create a tight no-live packet for source/candidate/fingerprint questions and should not read secrets, run macros, access hosted services, import project rows, create approvals, create notes/tasks/owners/due dates, issue field instructions, or mutate field/customer/finance state.
