# PM Lane 412 - Lane 278 Sibling Import Contract Support No-Live Design Packet Closeout

## Outcome

PM Lane 412 is complete.

It converts the import-side contract-support prerequisite from an open-ended follow-on note into a separate no-live sibling packet, without reopening PM Lane 278 or coupling the extractor to Lane 280.

Final outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE`

## Governing Facts

1. PM Lane 278 remains historically closed as the bounded core import mutation lane.
2. The chosen path is a separate future sibling route, `POST /api/v1/mutations/project-import-contract-support`, rather than a retroactive Lane 278 widening.
3. The sibling packet owns only import-side contract-support persistence: one original project snapshot, scope labor details, and apparatus quote-field population.
4. The governing multi-scope allocation rule is `scope_hours / project_hours`, and the later implementation packet must prove it with an explicit multi-scope fixture.
5. Later status-triggered revenue behavior must depend on a separate import-side readback, `GET /api/v1/reads/project-import-contract-support-status`, rather than owning these derivations itself.

## Boundary

Still blocked:

1. live route implementation
2. live schema creation
3. live import-contract-support writes
4. live revenue-event writes
5. apparatus status mutation
6. billing, payroll, invoice, accounting, customer billing delivery, and external finance sync
7. source workbook/PDF writeback and workbook macros

## Next Truth

The next truthful follow-on is a separate later implementation packet if PM wants to admit the sibling import-contract-support route, its readback, the required schema surfaces, and the multi-scope fixture proof. This lane itself remains documentation-only.