# APEX PM Lane 412 Revision B - Project Miner Temp Power Lane 278 Sibling Import Contract Support No-Live Design Packet

Date: 2026-05-20

Status: Documentation-only Revision B layered on top of the historical PM Lane 412 closeout and Lane 412 Revision A to add an explicit downstream-gate clause to the import-contract-support readback contract without changing any Revision A topology, security, or write-discipline surface

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_278_SIBLING_IMPORT_CONTRACT_SUPPORT_NO_LIVE_DESIGN_REVISION_B`

## Purpose

PM Lane 412 Revision B makes the downstream gate explicit on the Lane 412 side of the lane family.

Lane 412 Revision A already established the readback classifications and the role of the sibling import-support packet as the chosen prerequisite for later recognition work. Revision B adds the missing explicit clause that later Lane 280 status-mutation extension live admission is undiscussable until this readback returns `classification = ready` for the project in current production state.

This is a tightening revision only. It does not change the recognition firewall, role-based table separation, vocabulary firewall, `seam.apparatus_financials` topology, insert-only write discipline, extractor mapping, readback counts, structural eliminations, or any other Revision A design surface.

## Selected Outcome

Selected outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE_REVISION_B`

Meaning:

1. The historical Lane 412 packet remains intact as the original sibling import-contract-support design.
2. Lane 412 Revision A remains intact as the `seam.apparatus_financials` separation refactor.
3. Revision B adds only the explicit downstream-gate clause so the later Lane 280 admission dependency is stated directly in the Lane 412 readback contract.

## Inherited Revision A Baseline

All Revision A design facts remain unchanged:

1. The future sibling route remains pure insert-only into `seam.apparatus_financials` and companion PM financial tables.
2. Readback classifications remain `missing`, `ready`, `stale_candidate`, `counts_mismatch`, and `unavailable`.
3. Field Tech and Field Lead remain excluded from financial table access.
4. Operational hours remain outside this design surface.

## Revised Readback Contract

Recommended future readback route remains:

`GET /api/v1/reads/project-import-contract-support-status`

All Revision A classifications and readback semantics remain unchanged.

### Explicit Downstream Gate Clause

Any later Lane 280 status-mutation extension live admission is undiscussable until this readback returns `classification = ready` for the project in current production state.

This is a downstream live-admission gate on later write authority, not a runtime requirement to re-check the readback on every future recognition mutation. Once a later Lane 280 extension is admitted, runtime safety remains governed by that extension's own per-mutation preconditions, including the requirement that the apparatus has an associated `seam.apparatus_financials` row for the referenced `contract_snapshot_id`.

This downstream gate is the Lane 412 side of the bidirectional gate and pairs with Lane 411 Revision B's explicit Lane 280 admission-time prerequisite.

## Boundaries

This revision does not admit:

1. live route implementation
2. live schema creation or migration
3. live import-support writes
4. live revenue-event writes
5. apparatus status mutation
6. billing, invoice, payroll, accounting, customer-billing, or external-finance output
7. source workbook writeback or macros
8. live operational hours tracking implementation
9. autonomous AI business-state mutation

## Validation Before Closeout

Required validation for this revision packet:

1. the readback contract includes an explicit downstream-gate clause stating that later Lane 280 live admission is undiscussable until `classification = ready`
2. the downstream-gate clause is framed as a live-admission gate, not a per-mutation runtime check
3. the revision leaves all Lane 412 Revision A readback classifications and financial-topology surfaces unchanged
4. the revision pairs cleanly with Lane 411 Revision B's explicit admission-time gate language
5. the legacy underscore revenue token does not appear anywhere in this revision packet

## Correction Note - PM Lane 421 Schema Architecture Correction

1. The original Lane 412 design lineage, as materialized later by the Lane 420 schema floor, carried forward a Dataverse-era assumption that `seam.scope_labor_details.scope_id` and the downstream seam-side revenue scope pointer would target `public.scopes.id`.
2. PM Lane 421 live preflight and the 2026-05-21 schema architecture correction surfaced the operational truth: `public.*` is frozen at LASNAP sample data and is not the onboarding path for new projects such as Miner Temp Power.
3. Migration `015_seam_scopes_addition_and_fk_retarget.sql` preserves the Lane 412 import-contract-support intent while correcting the schema boundary by creating `seam.scopes` as the operational scope tier and retargeting `seam.scope_labor_details.scope_id` plus `seam.apparatus_revenue_events.scope_id` to `seam.scopes.id`.
4. `public.*` remains in the database as legacy reference only. No new project flow is expected to land in `public.*`, and any future cleanup or removal of that legacy surface remains a separate non-admitted packet.
