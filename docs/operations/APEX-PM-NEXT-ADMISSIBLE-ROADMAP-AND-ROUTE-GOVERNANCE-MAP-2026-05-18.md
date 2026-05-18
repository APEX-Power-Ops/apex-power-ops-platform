# APEX PM Next Admissible Roadmap And Route Governance Map

Date: 2026-05-18
Status: Active reference for post-Lane-355 PM continuation
Scope: What can move forward now inside the current PM governance boundary

## Purpose

This note records the practical post-Lane-355 PM operating posture in one place:

1. the exact next admissible roadmap,
2. the current feature classification by governance status, and
3. the live PM UI route map as observed in the hosted operations-web shell.

This note does not widen authority. It creates no product code, route, mutation, persistence, import, assignment, schedule/status write, durable field record, production tracking row, customer billing delivery, finance output, source writeback, workbook macro, or autonomous AI business-state mutation.

## Current Governing Posture

As of 2026-05-18 after PM Lanes 349 through 355:

1. actuals capture review, customer-preview review, customer-delivery durable-proof review, and customer-facing delivery execution are the current admitted Temp Power branch,
2. there is no remaining blocker inside the admitted customer-facing delivery execution slice,
3. the remaining blocked boundary is downstream only: finance output, customer billing delivery, and source workbook or PDF writeback,
4. no new downstream admission phrase is applicable yet,
5. generic continuation authority does not widen the blocked downstream boundary.

## Next Admissible Roadmap

### Immediate Roadmap

The following work can move forward now without opening finance or source write authority:

1. continue using the PM read surfaces as the operational PM shell: workfront, drivers, schedule review, tracer, variance, and intake reads,
2. continue using the admitted customer-facing delivery execution route for one bounded delivery-event request plus readback proof,
3. continue extending read-only PM review capability, browser proof, smoke coverage, route resilience, and operator guidance around the already admitted surfaces,
4. continue no-live planning and design work for later branches without opening any write path.

### Exact Next Packets

The next useful packets, in order, are:

1. PM Lane 356: finance-placeholder no-live design packet.
Reason: finance is explicitly a placeholder, so the right next step is to define the placeholder boundary, output taxonomy, and no-go conditions without opening any live output write.

2. PM Lane 357: hosted PM route verification and shell-hardening packet for promoted secondary review routes.
Reason: the hosted browser pass showed the secondary PM routes can still land on the shared loading shell before settling, and the drivers-linked review pages emitted a 404 resource error during inspection. This is a safe read-only hardening target that improves operability without widening business-state authority.

3. PM Lane 358: PM route governance map and operator routing packet.
Reason: the platform now has enough promoted PM routes that operators need one canonical route-to-authority map showing which surfaces are read-only, which are design-only, which are admitted, and which remain blocked.

4. Later separate packet only when explicitly requested: source-writeback authority packet.
Reason: workbook or PDF writeback remains a separate authority boundary and should not be mixed into finance placeholder work.

5. Later separate packet only when explicitly requested: customer billing delivery packet.
Reason: customer billing delivery remains blocked even though customer-facing delivery execution is admitted.

## Feature Classification

### Already Admissible Now

| Feature or surface | Current status | How it can move forward now |
| --- | --- | --- |
| PM workfront read model | Admissible now | Use live queue for PM triage, readiness review, blockers, owner gaps, and drillthrough navigation. |
| PM drivers route | Admissible now | Use live critical-path read view and continue read-only improvements, proof, and stability work. |
| PM schedule, tracer, variance reads | Admissible now as read surfaces | Continue promoted-route proof, route stability work, and read-only drillthrough flow improvements. |
| Project Miner intake workbench | Admissible now as read-only workbench | Use for candidate, admission-plan, approval-readiness, field-prep, and handoff review without approving or importing. |
| Import candidate review | Admissible now as read-only review | Continue exception review, source traceability review, warning triage, and local note drafting. |
| Import admission plan | Admissible now as read-only design | Continue future gate design, idempotency planning, no-go planning, and diff-check design. |
| Import approval readiness | Admissible now as read-only design | Continue contract/storage planning and proof preparation only. |
| Customer-facing delivery execution | Admitted bounded write slice | Use only for the single admitted delivery-event persistence plus readback proof path already defined by current guardrails. |

### No-Live Design Only

| Feature or surface | Current status | Allowed next work |
| --- | --- | --- |
| Finance placeholder | No-live design only | Define export shapes, labels, consumers, proof gates, and explicit no-go conditions without opening a live write. |
| Approval persistence design | No-live design only | Refine approval contract, storage-plan shape, validation matrix, and exact future mutation contract. |
| Import write design | No-live design only | Refine target rows, idempotency keys, preview-to-import diff checks, rollback assumptions, and no-go checks. |
| Field execution drafts in intake outputs | No-live design only | Continue draft artifacts and operator prompts without assigning, scheduling, authorizing, or writing field state. |
| Customer reporting drafts | No-live design only | Continue artifact drafting only; no delivery, commitment, or persisted customer reporting. |

### Needs New Admission

| Feature or surface | Why separate admission is required |
| --- | --- |
| Billing export writes | Downstream finance-state mutation |
| Payroll export writes | Downstream finance-state mutation |
| Invoice or accounting records | Downstream finance-state mutation |
| External finance sync | Downstream external-system mutation |
| Customer billing delivery | Separate downstream customer-delivery branch beyond current admitted delivery-event proof slice |
| Source workbook or PDF writeback | Separate source-of-truth mutation branch |
| Workbook macros | Separate source-system execution branch |
| Project import writes | Separate approval and import authority branch |
| Approval-row persistence | Separate exact admission phrase and proof gate branch |
| Assignment, schedule, status, field authorization, durable field record, production tracking | Separate downstream operational mutation branches |

## Live PM UI Route Map

The following route map combines source review with hosted browser inspection on 2026-05-18.

| Route | Hosted observation | Governance status | Current use |
| --- | --- | --- | --- |
| `/pm-review/workfront` | Live. Observed with 184 ready rows, 0 blocked, 0 unassigned during route walkthrough. | Read-only admissible now | Primary PM queue and drillthrough entrypoint. |
| `/pm-review` | Live. Observed critical-path driver edge data in hosted UI. | Read-only admissible now | PM critical-path driver review. |
| `/pm-review/customer-delivery-execution` | Live. Readback returned `customer_delivery_event_recorded_current_match` with current-match lineage and blocked downstream authorities. | Admitted bounded write slice | One customer-delivery event request plus readback proof only. |
| `/pm-review/import-intake` | Live. Hosted reads green; future route not admitted; export and output actions present but disabled. | Read-only admissible now | Consolidated intake and planning workbench. |
| `/pm-review/import-candidate` | Live. Read seam is live; mutation authority remains `not_admitted`; current hosted data was still waiting on candidate payload during inspection. | Read-only admissible now | Exception-first candidate review only. |
| `/pm-review/import-admission-plan` | Live. Plan seam is live; mutation authority remains `not_admitted`. | No-live design only | Future import gate design only. |
| `/pm-review/import-approval-readiness` | Live. Contract and storage seams are live; persistence authority remains `not_admitted`. | No-live design only | Future approval persistence planning only. |
| `/pm-review/schedule` | Promoted route exists in code and hosted shell opened, but this inspection pass landed on the shared loading shell before settling. | Read-only admissible now, hosted verification should be hardened | Schedule review route; safe target for read-only hosted proof hardening. |
| `/pm-review/tracer` | Promoted route exists in code and hosted shell opened, but this inspection pass landed on the shared loading shell before settling. | Read-only admissible now, hosted verification should be hardened | Upstream constraint tracing route. |
| `/pm-review/variance` | Promoted route exists in code and hosted shell opened, but this inspection pass landed on the shared loading shell before settling. | Read-only admissible now, hosted verification should be hardened | Schedule variance review route. |
| `/pm-review/approval` | Promoted route exists in code, includes mutation-surface contract language, and hosted shell opened, but current broader governance does not admit approval persistence or import. | Present as prototype or design surface; not currently open authority | Do not treat as live approval authority until a separate admitted approval packet opens it. |

## Operational Interpretation

The platform can keep moving forward now in three ways:

1. use the current admitted and read-only PM routes operationally,
2. improve and verify those routes without widening mutation authority,
3. author no-live design packets for later finance, source, approval, or import branches.

The platform should not move forward by silently converting design surfaces into live write authority. The governance framework is working when it allows read, review, planning, and bounded admitted execution to advance while keeping downstream write branches explicit and separate.

## Recommended Decision

If the goal is to keep the PM platform moving without opening finance yet, the recommended sequence is:

1. treat finance as placeholder-only and author PM Lane 356 as a no-live finance placeholder packet,
2. harden hosted verification for schedule, tracer, variance, and approval route shells as PM Lane 357,
3. publish a canonical PM route-to-authority operator map as PM Lane 358,
4. leave customer billing delivery and source writeback blocked until they are explicitly selected as separate later branches.