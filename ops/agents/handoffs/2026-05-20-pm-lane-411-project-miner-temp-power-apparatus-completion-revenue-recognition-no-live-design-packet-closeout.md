# PM Lane 411 - Apparatus Completion Revenue Recognition No-Live Design Closeout

## Outcome

PM Lane 411 is complete.

It converts the current apparatus-completion revenue-recognition request into a separate no-live design packet without admitting any finance or revenue-recognition write.

Final outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE`

## Governing Facts

1. The request is classified under PM Lane 352's `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` path.
2. Recognition is fixed to one frozen project-level hours-weighted rate derived from adjusted contract value and total quoted hours.
3. Estimator pools remain imported separately for cost analysis only.
4. `v_scope_financials` must normalize pool-recognized revenue inside each scope by `total_scope_pool_amount`, not by full project `contract_value`, or multi-scope projects underreport recognized pool amounts.
5. `snapshot_kind` is kept as a named field but should be constrained text, not a literal enum, so future `change_order_N` values remain migration-free.
6. Stored snapshot financial fields must reconcile internally, and authority defaults should remain `not_admitted` until a later inserting route explicitly sets them.
7. Reversal rows must retain the original event `contract_snapshot_id`, and V1 disallows double reversal.
8. PM Lane 412 sibling import-contract-support work, Lane 280 status mutation extension, reversal events, zero-baseline seeding, and the explicit multi-scope fixture requirement are all defined as design only.

## Boundary

Still blocked:

1. live schema creation
2. live revenue-recognition writes
3. billing, payroll, invoice, accounting, customer billing delivery, and external finance sync
4. source workbook/PDF writeback and workbook macros
5. change-order admission and execution

## Next Truth

The next truthful follow-on is a separate later admission packet if PM wants to implement the snapshot tables, import amendment, apparatus-status mutation extension, baseline seeding, or live apparatus revenue-recognition write. This lane itself remains documentation-only.