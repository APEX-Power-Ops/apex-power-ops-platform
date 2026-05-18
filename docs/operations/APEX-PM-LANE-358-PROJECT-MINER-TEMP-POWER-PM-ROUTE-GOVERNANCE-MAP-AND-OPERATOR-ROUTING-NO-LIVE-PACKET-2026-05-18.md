# APEX PM Lane 358 - Project Miner Temp Power PM Route Governance Map And Operator Routing No-Live Packet

Date: 2026-05-18

Status: Documentation-only no-live PM route governance map and operator routing packet

Decision label:

`PROJECT_MINER_TEMP_POWER_PM_ROUTE_GOVERNANCE_MAP_AND_OPERATOR_ROUTING_NO_LIVE`

## Purpose

PM Lane 358 publishes one canonical PM route-to-authority map for the current hosted PM shell.

The route surface has grown enough that operators now need one explicit routing truth showing which PM routes are already usable now, which are read-only or design-only, which route is the admitted bounded write slice, and which surfaces must not be mistaken for live downstream authority.

This lane does not widen any route authority. It only maps and classifies the current PM surfaces so operators can route work correctly.

This lane is documentation-only. It creates no product code, UI control, backend seam, hosted mutation, approval row, import write, assignment, schedule/status write, customer billing delivery, finance output, source workbook/PDF writeback, workbook macro, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`PM_ROUTE_AUTHORITY_MAP_PUBLISHED_NO_LIVE`

Meaning:

1. the current hosted PM shell now has a canonical route-to-authority map,
2. operators can distinguish read-only review routes from design-only routes and from the single currently admitted bounded write slice,
3. the approval route remains explicitly non-authoritative,
4. downstream finance, customer-billing-delivery, and source-writeback branches remain separate.

## Route Classes

### Class A - Read-Only Admissible Now

These routes are usable now as read or review surfaces:

1. `/pm-review/workfront`
2. `/pm-review`
3. `/pm-review/import-intake`
4. `/pm-review/import-candidate`
5. `/pm-review/schedule`
6. `/pm-review/tracer`
7. `/pm-review/variance`

Operator meaning:

1. use these routes for PM review, queue triage, planning context, schedule analysis, tracing, and variance review,
2. do not interpret their presence as live write authority,
3. secondary promoted review routes still benefit from hosted shell-hardening proof per Lane 357.

### Class B - Design-Only Or Pre-Authority Planning Routes

These routes are present for planning or readiness only and remain no-live:

1. `/pm-review/import-admission-plan`
2. `/pm-review/import-approval-readiness`
3. `/pm-review/approval`

Operator meaning:

1. these routes are for future contract, storage, gate, and workflow review,
2. `/pm-review/approval` must not be treated as active approval authority,
3. no approval persistence or import write is admitted from these surfaces under current governance.

### Class C - Admitted Bounded Write Slice

The only currently admitted bounded write slice is:

1. `/pm-review/customer-delivery-execution`

Operator meaning:

1. this route is the current bounded customer-facing delivery-event execution surface,
2. it is limited to the admitted delivery-event request plus readback proof,
3. it does not widen into finance output, customer billing delivery, or source writeback.

## Route-To-Authority Map

| Route | Current class | Current authority |
| --- | --- | --- |
| `/pm-review/workfront` | Class A | Read-only PM queue and drillthrough surface |
| `/pm-review` | Class A | Read-only PM drivers review |
| `/pm-review/import-intake` | Class A | Read-only consolidated intake workbench |
| `/pm-review/import-candidate` | Class A | Read-only exception and source-traceability review |
| `/pm-review/schedule` | Class A | Read-only schedule review |
| `/pm-review/tracer` | Class A | Read-only upstream constraint tracing |
| `/pm-review/variance` | Class A | Read-only schedule variance review |
| `/pm-review/import-admission-plan` | Class B | Future import gate design only |
| `/pm-review/import-approval-readiness` | Class B | Future approval persistence planning only |
| `/pm-review/approval` | Class B | Prototype or design surface only; not current approval authority |
| `/pm-review/customer-delivery-execution` | Class C | Admitted bounded customer-delivery-event execution only |

## Operator Routing Rules

Use these rules when deciding where PM work should go now:

1. if the task is triage, visibility, schedule review, tracing, variance review, intake review, or candidate review, route it to a Class A surface,
2. if the task is future import-contract or approval-contract design, route it to a Class B surface,
3. if the task is the currently admitted customer-facing delivery-event persistence and readback proof, route it to Class C,
4. if the task implies approval persistence, project import, assignment, schedule/status write, field authorization, production tracking, finance output, customer billing delivery, or source writeback, stop and route to a later separate packet rather than a current PM route.

## Explicit Non-Route Authority

The following are still not opened merely because PM routes exist:

1. approval-row persistence,
2. project import writes,
3. assignment writes,
4. schedule/status writes,
5. field authorization,
6. durable field records,
7. production tracking,
8. finance output,
9. customer billing delivery,
10. source workbook/PDF writeback,
11. workbook macros.

## Companion Reference

Companion reference for the wider roadmap, feature classification, and hosted observations:

`docs/operations/APEX-PM-NEXT-ADMISSIBLE-ROADMAP-AND-ROUTE-GOVERNANCE-MAP-2026-05-18.md`

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 358 files.
3. Selected outcome is present.
4. All current PM routes in scope are classified.
5. Approval route non-authority posture is explicit.
6. The single admitted bounded write slice is explicit.
7. `git diff --check` passes.
8. Staged diff includes only Lane 358 scoped docs, handoff, and PM status surfaces.

## Next Truth

The next truthful PM move after Lane 358 is to use the route classes operationally and to continue separate no-live or admitted packets when a branch actually widens.

The next truthful PM move is not to infer new write authority from route presence alone.