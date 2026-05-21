# PM Lane 411 Revision A - Apparatus Completion Revenue Recognition No-Live Design Packet Closeout

## Outcome

PM Lane 411 Revision A is complete.

It layers the role-based separation refactor on top of the historical Lane 411 design and relocates frozen quote data to `seam.apparatus_financials`.

Final outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE_REVISION_A`

## Governing Facts

1. Recognition firewall: apparatus revenue recognition reads frozen-at-import quote data from `seam.apparatus_financials` only. Operational tables for actual hours, delay hours, delay categories, and change-order justification context are not in the recognition data path.
2. Role-based table separation: financial tables `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, and `seam.apparatus_revenue_events` are PM-and-Finance-role-only at the RLS grant level. Field Tech and Field Lead roles have no SELECT on these tables.
3. Vocabulary firewall: the legacy actual revenue term is not a valid concept in this design. Revenue is frozen as `quoted_revenue` and earned as `recognized_amount`; hours efficiency hits margin, not revenue.
4. `seam.apparatus` no longer carries financial columns; quote data now lives in `seam.apparatus_financials` with insert-only discipline and an internal-consistency CHECK on the denormalized `recognition_rate_per_hour_snapshot`.
5. `seam.v_scope_financials` now sources `total_quoted_revenue` from `seam.apparatus_financials`, while the prior multi-scope denominator fix remains intact.
6. Operational hours tracking is reserved to a separate later lane and is explicitly not part of this recognition design surface.

## Boundary

Still blocked:

1. live revenue-event writes
2. live schema creation or migration
3. public schema writes
4. billing, payroll, invoice, accounting, customer-billing, and external-finance output
5. source workbook/PDF writeback and workbook macros
6. change-order admission
7. live operational-hours tracking implementation

## Next Truth

The next truthful follow-on remains a later packet that tightens Lane 280's design surfaces to require Lane 412 readiness readback before any status-triggered recognition behavior is considered. This revision itself remains documentation-only.