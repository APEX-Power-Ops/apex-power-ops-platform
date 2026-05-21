# PM Lane 412 Revision A - Lane 278 Sibling Import Contract Support No-Live Design Packet Closeout

## Outcome

PM Lane 412 Revision A is complete.

It layers the role-based separation refactor on top of the historical Lane 412 design and changes the future import-support packet to persist quote data into `seam.apparatus_financials`.

Final outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE_REVISION_A`

## Governing Facts

1. Recognition firewall: apparatus revenue recognition reads frozen-at-import quote data from `seam.apparatus_financials` only. Operational tables for actual hours, delay hours, delay categories, and change-order justification context are not in the recognition data path.
2. Role-based table separation: financial tables `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, and `seam.apparatus_revenue_events` are PM-and-Finance-role-only at the RLS grant level. Field Tech and Field Lead roles have no SELECT on these tables.
3. Vocabulary firewall: the legacy actual revenue term is not a valid concept in this design. Revenue is frozen as `quoted_revenue` and earned as `recognized_amount`; hours efficiency hits margin, not revenue.
4. The future sibling import-support route writes one insert-only `seam.apparatus_financials` row per apparatus per snapshot instead of populating financial columns on `seam.apparatus`.
5. `apparatus.contract_snapshot_id` nullability and update-then-freeze concerns are resolved structurally because the foreign key and quote data now live on `seam.apparatus_financials` under insert-only discipline.
6. Readback coverage and missing-count semantics now derive from `seam.apparatus_financials`, not apparatus-table quote columns.

## Boundary

Still blocked:

1. live route implementation
2. live schema creation or migration
3. live import-support writes
4. live revenue-event writes
5. apparatus status mutation
6. billing, payroll, invoice, accounting, customer-billing, and external-finance output
7. source workbook/PDF writeback and workbook macros
8. live operational-hours tracking implementation

## Next Truth

The next truthful follow-on remains a later live-admission packet for the sibling import-contract-support route and its readback proof. This revision itself remains documentation-only.