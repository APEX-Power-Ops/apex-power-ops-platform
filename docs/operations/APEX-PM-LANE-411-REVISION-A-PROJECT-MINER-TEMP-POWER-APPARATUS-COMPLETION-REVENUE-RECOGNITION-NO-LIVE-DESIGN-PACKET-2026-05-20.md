# APEX PM Lane 411 Revision A - Project Miner Temp Power Apparatus Completion Revenue Recognition No-Live Design Packet

Date: 2026-05-20

Status: Documentation-only Revision A layered on top of the historical PM Lane 411 closeout to codify the recognition firewall, role-based table separation, and quote-data relocation into a dedicated financial table

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_REVISION_A`

## Purpose

PM Lane 411 Revision A corrects the structural separation between apparatus identity/status data and apparatus financial data.

The historical Lane 411 packet remains valid as a no-live recognition design and as the source of the multi-scope normalization fix. This revision layers on top of that record and changes the table topology so frozen quote data is held outside `seam.apparatus`.

## Selected Outcome

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE_REVISION_A`

Meaning:

1. Recognition remains bid-anchored and completion-triggered.
2. Frozen quote data moves out of `seam.apparatus` and into `seam.apparatus_financials`.
3. Role-based separation is enforced at the table boundary, not by hiding columns on the apparatus identity table.
4. Operational hours tracking is explicitly reserved to a later lane and is not part of the recognition path.

## Governing Principle

This revision codifies three design firewalls:

1. Recognition firewall: apparatus revenue recognition reads frozen-at-import quote data only.
2. Role-based table separation: field roles may read `seam.apparatus` without seeing financial data because financial data is stored on separate PM-and-Finance-only tables.
3. Vocabulary firewall: revenue is `quoted_revenue` when frozen and `recognized_amount` when earned. There is no valid legacy actual revenue concept in this design.

## Revised Financial Topology

`seam.apparatus` remains an identity, status, location, equipment, and dates table only.

Revision A removes these financial columns from the apparatus identity table:

```text
quoted_hours
quoted_revenue
contract_snapshot_id
```

Frozen quote data is now stored in a separate table.

## `seam.apparatus_financials`

Recommended shape:

```text
id UUID PRIMARY KEY
apparatus_id UUID NOT NULL REFERENCES seam.apparatus(id)
contract_snapshot_id UUID NOT NULL REFERENCES seam.project_contract_snapshots(id)
quoted_hours NUMERIC(14,2) NOT NULL CHECK (quoted_hours >= 0)
quoted_revenue NUMERIC(14,2) NOT NULL CHECK (quoted_revenue >= 0)
recognition_rate_per_hour_snapshot NUMERIC(14,6) NOT NULL CHECK (recognition_rate_per_hour_snapshot >= 0)
mutation_authority TEXT NOT NULL DEFAULT 'not_admitted'
revenue_recognition_authority TEXT NOT NULL DEFAULT 'not_admitted'
billing_export_authority TEXT NOT NULL DEFAULT 'not_admitted'
invoice_authority TEXT NOT NULL DEFAULT 'not_admitted'
accounting_authority TEXT NOT NULL DEFAULT 'not_admitted'
external_finance_sync_authority TEXT NOT NULL DEFAULT 'not_admitted'
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
created_by TEXT NOT NULL
audit_event_id TEXT NOT NULL
mutation_id TEXT NOT NULL
CHECK (
  ABS(quoted_revenue - (quoted_hours * recognition_rate_per_hour_snapshot)) < 0.01
)
```

Required constraints and enforcement:

1. unique `(apparatus_id, contract_snapshot_id)`
2. unique `mutation_id`
3. unique `audit_event_id`
4. trigger-enforced equality between `recognition_rate_per_hour_snapshot` and the referenced `seam.project_contract_snapshots.recognition_rate_per_hour` at insert time
5. insert-only trigger; reject update and delete
6. RLS enabled

Denormalization rationale:

`recognition_rate_per_hour_snapshot` is copied onto `seam.apparatus_financials` so the rate used to compute this apparatus's `quoted_revenue` is self-evident on the same row. That preserves audit clarity while the internal-consistency CHECK and insert-time trigger keep it aligned with the referenced snapshot.

## Recognition Model After Revision A

Project-level recognition rate remains frozen on `seam.project_contract_snapshots`:

```text
recognition_rate_per_hour = contract_value / total_quoted_hours
```

Per-apparatus frozen quote data is persisted on `seam.apparatus_financials`:

```text
quoted_revenue = quoted_hours * recognition_rate_per_hour_snapshot
```

Recognition event on PM disposition of apparatus status to `Complete` remains:

```text
recognized_amount = apparatus_financials.quoted_revenue
recognition_percent = 100
```

The multi-scope normalization rule from the historical Lane 411 correction remains unchanged.

## RLS And Role Separation

The security boundary is the table boundary.

Required grants:

1. `seam.apparatus_financials`: SELECT granted to PM role and Finance role only. INSERT granted to PM role only through the future governed mutation route. No SELECT or INSERT grants to Field Tech, Field Lead, `anon`, or `authenticated`.
2. `seam.project_contract_snapshots`: SELECT granted to PM role and Finance role only. No SELECT grants to Field Tech or Field Lead.
3. `seam.scope_labor_details`: SELECT granted to PM role and Finance role only. No SELECT grants to Field Tech or Field Lead.
4. `seam.apparatus_revenue_events`: SELECT granted to PM role and Finance role only. INSERT granted to PM role only through the future Lane 280 extension. No SELECT or INSERT grants to Field Tech or Field Lead.
5. `seam.apparatus`: keeps existing Field Tech and Field Lead read grants because it now contains no financial data.

This means a Field Tech or Field Lead may `SELECT * FROM seam.apparatus` and still see no financial information by table structure.

## Import-Side Dependency

Revision A depends on the PM Lane 412 Revision A sibling import-contract-support packet for the import-side write that creates:

1. one original `seam.project_contract_snapshots` row,
2. required `seam.scope_labor_details` rows,
3. one `seam.apparatus_financials` row per apparatus per snapshot.

Recognition continues to rely on frozen import-time quote data, but that data now enters through `apparatus_financials` rather than apparatus-table columns.

## Revised `seam.v_scope_financials`

`total_quoted_revenue` must now come from `seam.apparatus_financials` joined back to apparatus for scope membership:

```sql
scope_quoted AS (
  SELECT a.scope_id, af.contract_snapshot_id, SUM(af.quoted_revenue) AS total_quoted_revenue
  FROM seam.apparatus_financials af
  JOIN seam.apparatus a ON a.id = af.apparatus_id
  GROUP BY a.scope_id, af.contract_snapshot_id
)
```

The prior multi-scope correction remains required:

```text
scope_pool_share = scope_pool_amount / NULLIF(total_scope_pool_amount, 0)
```

Pool-recognized revenue is still normalized inside each scope, not against full project contract value.

## Revised Lane 280 Status-Mutation Extension Contract

The future Lane 280 extension remains same-transaction and insert-only, but its preconditions now reference `seam.apparatus_financials` instead of fields on `seam.apparatus`.

Required preconditions:

1. PM-only actor
2. apparatus belongs to the admitted imported project and scope
3. apparatus has an associated `seam.apparatus_financials` row for the referenced `contract_snapshot_id`
4. snapshot belongs to the same project
5. `recognition_percent = 100` for V1
6. no unreversed recognized event exists unless exact same-payload replay

Payload/readback notes:

1. `expected_quoted_revenue` is read from `seam.apparatus_financials.quoted_revenue`
2. `recognized_amount` is derived from `seam.apparatus_financials.quoted_revenue`
3. `event_id` remains part of readback for reversal workflows

## Recognition Firewall Against Operational Hours

Operational hours tracking is RESERVED to a separate later lane and is explicitly NOT part of this design surface.

The recognition firewall means apparatus revenue recognition reads only frozen-at-import quote data. Operational tables for actual hours, delay hours, delay categories, and change-order justification context have no data path into the recognition engine. Any future packet that proposes earning revenue based on operational actuals must be rejected at intake because recognition is bid-anchored only.

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

## Validation Before Closeout

Required validation for this revision packet:

1. `seam.apparatus` no longer carries `quoted_hours`, `quoted_revenue`, or `contract_snapshot_id` in the revision design.
2. `seam.apparatus_financials` includes the UNIQUE `(apparatus_id, contract_snapshot_id)` rule and the internal-consistency CHECK on `recognition_rate_per_hour_snapshot`.
3. Field Tech and Field Lead are explicitly listed as having no access to financial tables.
4. `seam.v_scope_financials` sources `total_quoted_revenue` from `seam.apparatus_financials`.
5. Lane 280 references `seam.apparatus_financials.quoted_revenue` for expected quote and recognition source.
6. the legacy underscore revenue token does not appear anywhere in this revision packet.
7. the operational-hours-reserved boundary is explicit.
