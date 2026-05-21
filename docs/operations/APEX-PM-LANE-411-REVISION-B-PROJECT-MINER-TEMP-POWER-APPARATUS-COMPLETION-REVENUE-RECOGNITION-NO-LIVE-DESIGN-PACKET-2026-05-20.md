# APEX PM Lane 411 Revision B - Project Miner Temp Power Apparatus Completion Revenue Recognition No-Live Design Packet

Date: 2026-05-20

Status: Documentation-only Revision B layered on top of the historical PM Lane 411 closeout and Lane 411 Revision A to tighten the Lane 280 status-mutation extension admission gate without changing any Revision A financial or security surfaces

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_REVISION_B`

## Purpose

PM Lane 411 Revision B makes the Lane 280 status-mutation extension contract explicitly bidirectional with the Lane 412 Revision B readback contract.

Lane 412 Revision B supplies the explicit downstream-gate clause that any later Lane 280 live implementation remains undiscussable until import-contract-support readback returns `classification = ready`. Lane 411 Revision B supplies the reverse statement on the Lane 411 side so the same admission gate is visible from both directions.

This is a tightening revision only. It does not change the recognition firewall, role-based table separation, vocabulary firewall, financial topology, RLS grant model, multi-scope math, snapshot consistency rules, or reversal discipline already locked by Revision A.

## Selected Outcome

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE_REVISION_B`

Meaning:

1. The historical Lane 411 packet remains intact as the original no-live recognition design.
2. Lane 411 Revision A remains intact as the recognition-firewall and `seam.apparatus_financials` separation refactor.
3. Revision B adds only the Lane 280 admission-gate tightening that cross-references Lane 412 readiness from the Lane 411 side.

## Inherited Revision A Baseline

All Revision A design facts remain unchanged:

1. Recognition stays bid-anchored and completion-triggered.
2. Frozen quote data remains stored on `seam.apparatus_financials`, not `seam.apparatus`.
3. Financial tables remain PM-and-Finance-role-only by table-level grants.
4. Operational hours tracking remains reserved to a later lane and outside the recognition path.

## Revised Lane 280 Status-Mutation Extension Contract

The future Lane 280 extension remains same-transaction and insert-only. Revision B adds the import-support readiness admission gate so the Lane 280 design explicitly names the Lane 412 prerequisite already carried by the Lane 412 readback contract.

Required preconditions:

1. PM-only actor
2. apparatus belongs to the admitted imported project and scope
3. apparatus has an associated `seam.apparatus_financials` row for the referenced `contract_snapshot_id`
4. snapshot belongs to the same project
5. `recognition_percent = 100` for V1
6. no unreversed recognized event exists unless exact same-payload replay
7. the project referenced by the apparatus must have a current `GET /api/v1/reads/project-import-contract-support-status` response with `classification = ready`, `current_candidate_match = true`, and `counts_match = true`; this precondition is evaluated at admission time, not at every mutation call

### Admission-Time Gate Language

Live admission of this status-mutation extension is undiscussable until the Lane 412 readback returns `classification = ready` for the project in current production state.

This is a one-time admission gate against the live readback surface, not a runtime check on every recognition event. Subsequent recognition events rely on the per-mutation precondition that the apparatus has an associated `seam.apparatus_financials` row for the referenced `contract_snapshot_id`, which Lane 412 establishes as a side effect of reaching the `ready` classification.

### Readback Contract Additions

Payload/readback notes:

1. `expected_quoted_revenue` is read from `seam.apparatus_financials.quoted_revenue`
2. `recognized_amount` is derived from `seam.apparatus_financials.quoted_revenue`
3. `event_id` remains part of readback for reversal workflows
4. `lane_412_readback_classification_at_admission_time`: the Lane 412 readback classification observed at the moment this extension's live admission was granted; recorded for audit traceability so every recognition event can be traced back to the import-support state that authorized the recognition mutation to exist

This field is set once at admission time and stamped on every event row created under this extension. It is not re-read per mutation call.

## Bidirectional Gate Note

Revision B makes the gate explicit in both directions:

1. Lane 412 Revision B readback now carries the downstream gate that later Lane 280 live admission is blocked until readback is `ready`.
2. Lane 411 Revision B now records the same gate inside the Lane 280 extension contract.

Either direction alone is insufficient documentation. Both directions must remain in place.

## Boundaries

This revision does not admit:

1. live revenue-event writes
2. live schema migration
3. public schema writes
4. billing, invoice, payroll, accounting, customer-billing, or external-finance output
5. source workbook writeback or macros
6. change-order admission
7. live operational hours tracking implementation
8. autonomous AI business-state mutation
9. live admission of the Lane 280 status-mutation extension unless the Lane 412 readback has passed the one-time `classification = ready` gate; this gate is bidirectional with the Lane 412 Revision B readback contract's downstream gate clause

## Validation Before Closeout

Required validation for this revision packet:

1. the Lane 280 precondition list includes the Lane 412 readback readiness requirement
2. a dedicated admission-time gate language section appears separately from the precondition list
3. the readback contract includes `lane_412_readback_classification_at_admission_time`
4. the boundary list includes the new Lane 412 readiness gate item
5. this revision does not restate or alter Revision A financial topology, role separation, multi-scope math, or snapshot consistency rules beyond inherited references
6. the legacy underscore revenue token does not appear anywhere in this revision packet
