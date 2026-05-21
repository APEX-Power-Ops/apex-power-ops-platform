# APEX PM Lane 412 Revision A - Project Miner Temp Power Lane 278 Sibling Import Contract Support No-Live Design Packet

Date: 2026-05-20

Status: Documentation-only Revision A layered on top of the historical PM Lane 412 closeout to move frozen quote data into `seam.apparatus_financials` and align import-support persistence with the recognition firewall

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_278_SIBLING_IMPORT_CONTRACT_SUPPORT_NO_LIVE_DESIGN_REVISION_A`

## Purpose

PM Lane 412 Revision A updates the sibling import-contract-support design so the import-side write persists quote data into `seam.apparatus_financials`, not onto `seam.apparatus`.

The historical Lane 412 packet remains valid as the separation of the import-support branch from both historical Lane 278 and later Lane 280. This revision layers on top of that record and changes the structural destination of quote data.

## Selected Outcome

Selected outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE_REVISION_A`

Meaning:

1. Historical Lane 278 remains a bounded core-import proof.
2. The sibling import-support packet remains the chosen prerequisite for later recognition work.
3. The future import-support write is pure insert-only into `seam.apparatus_financials`, not apparatus-table column population.
4. The packet keeps the recognition firewall and role-based table separation intact.

## Future Admitted Route

Recommended future route remains:

`POST /api/v1/mutations/project-import-contract-support`

Entity and action:

```text
entity_type = pm_import_contract_support
action_type = persist_import_contract_support
```

## Allowed Future Writes After Revision A

If a later live packet admits the route, it may write only:

1. one original `seam.project_contract_snapshots` row,
2. the required `seam.scope_labor_details` rows,
3. one insert-only `seam.apparatus_financials` row per apparatus per snapshot,
4. one audit event,
5. one idempotency cache entry.

This future packet does not write financial columns onto `seam.apparatus`.

## Extractor Mapping

Required source extracts remain:

1. `Onsite Labor Total (adjusted)`
2. `Offsite Labor Total (adjusted)`
3. `Travel Total`
4. `Outside Services Total`
5. per-apparatus `Hrs/Line`
6. `Total Sheet $$$ Adjusted`
7. contract sign date when extractable

Revised mapping:

```text
Per-apparatus Hrs/Line -> apparatus_financials.quoted_hours
Per-apparatus quoted_revenue (derived) -> apparatus_financials.quoted_revenue = quoted_hours * snapshot.recognition_rate_per_hour
Snapshot rate captured for audit (denormalized) -> apparatus_financials.recognition_rate_per_hour_snapshot = snapshot.recognition_rate_per_hour
```

Derived values:

```text
total_quoted_hours = SUM(apparatus_financials.quoted_hours)
recognition_rate_per_hour = contract_value / total_quoted_hours
quoted_revenue = quoted_hours * recognition_rate_per_hour_snapshot
```

## `seam.apparatus_financials` Write Discipline

The sibling route uses pure insert-only persistence.

Required table rules:

1. one row per `(apparatus_id, contract_snapshot_id)`
2. no updates
3. no deletes
4. internal-consistency CHECK:

```text
ABS(quoted_revenue - (quoted_hours * recognition_rate_per_hour_snapshot)) < 0.01
```

5. trigger-enforced equality between `recognition_rate_per_hour_snapshot` and the referenced snapshot rate

This structurally resolves the prior update-then-freeze concern: the pattern is now the same insert-only discipline used elsewhere in the PM seam family.

## Multi-Scope Allocation Rule

Revision A keeps the same governing allocation assumption:

```text
scope_pool_amount = project_pool_amount * (scope_hours / project_hours)
```

The multi-scope fixture requirement remains mandatory so single-scope Miner data cannot hide normalization defects.

## Revised Readback Contract

Recommended future readback route remains:

`GET /api/v1/reads/project-import-contract-support-status`

Classifications stay:

1. `missing`
2. `ready`
3. `stale_candidate`
4. `counts_mismatch`
5. `unavailable`

Revised field semantics:

1. `apparatus_quote_coverage_count`: count of distinct `apparatus_id` values in `seam.apparatus_financials` for the project's snapshot
2. `apparatus_missing_quote_count`: count of imported `seam.apparatus` rows for the project that do not have a matching `seam.apparatus_financials` row for the snapshot

The readback may aggregate these counts for PM consumption, but it must not expose row-level financials to field roles.

## RLS And Role Separation

Required grants remain table-level:

1. `seam.apparatus_financials`: PM role and Finance role only for SELECT; PM role only for INSERT through the future route; no grants to Field Tech or Field Lead
2. `seam.project_contract_snapshots`: PM role and Finance role only for SELECT; no grants to Field Tech or Field Lead
3. `seam.scope_labor_details`: PM role and Finance role only for SELECT; no grants to Field Tech or Field Lead
4. `seam.apparatus_revenue_events`: PM role and Finance role only for SELECT; PM role only for INSERT through future governed routes; no grants to Field Tech or Field Lead

Field roles may still read `seam.apparatus` because the financial data is structurally elsewhere.

## Structural Eliminations

This revision eliminates two earlier design concerns structurally:

1. `apparatus.contract_snapshot_id` nullability disappears because the foreign key lives on `seam.apparatus_financials` and is NOT NULL.
2. The import-support write no longer implies update-then-freeze behavior on apparatus because the future write is pure INSERT into `seam.apparatus_financials`.

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

1. `allowed_future_writes` is pure insert-only into `seam.apparatus_financials` rather than apparatus-table column population.
2. extractor mapping references `apparatus_financials.quoted_hours`, `apparatus_financials.quoted_revenue`, and `apparatus_financials.recognition_rate_per_hour_snapshot`.
3. readback coverage semantics reference `seam.apparatus_financials`.
4. Field Tech and Field Lead are explicitly denied access to financial tables.
5. the structural elimination of nullable `apparatus.contract_snapshot_id` and update-then-freeze concern is explicit.
