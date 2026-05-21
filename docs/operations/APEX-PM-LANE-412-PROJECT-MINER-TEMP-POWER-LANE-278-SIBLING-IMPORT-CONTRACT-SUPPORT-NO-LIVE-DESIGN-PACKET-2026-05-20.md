# APEX PM Lane 412 - Project Miner Temp Power Lane 278 Sibling Import Contract Support No-Live Design Packet

Date: 2026-05-20

Status: Documentation-only no-live design packet for the import-side contract-support extractor required by PM Lane 411, without reopening historical PM Lane 278 or coupling import normalization to the later status-mutation branch

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_278_SIBLING_IMPORT_CONTRACT_SUPPORT_NO_LIVE_DESIGN`

## Purpose

PM Lane 412 isolates the import-side contract-support work that PM Lane 411 depends on.

PM Lane 278 is already executed and accepted closed as the bounded core import mutation for project, workpackage, task, and apparatus rows. That historical packet should stay stable. The snapshot, pool-allocation, and apparatus-quoted-revenue support logic needed for later apparatus-completion revenue recognition should therefore live in a separate sibling lane instead of being retroactively folded into Lane 278 or mixed into the later Lane 280 status-mutation branch.

This lane is design-only. It does not admit any live route, schema migration, hosted call, or import-support write. It defines the future import-side packet that would populate contract-support data after Lane 278 core import and before any later revenue-recognition or status-triggered write is considered.

## Source Classification

This lane stays under the same PM Lane 352 family classification used by PM Lane 411:

`OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED`

Reason:

The extractor would create additional persistent support rows and apparatus quote fields beyond the already-admitted Lane 278 core import surface. That is a separate write admission question even though it remains upstream of later finance-side or status-side behavior.

## Selected Outcome

Selected outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE`

Meaning:

1. Historical PM Lane 278 remains a closed core-import proof and is not retroactively widened.
2. The chosen follow-on is a separate sibling packet that persists contract-support data after the approved Temp Power project import already exists.
3. PM Lane 280 and later revenue-recognition work may depend on this support packet, but they do not own it.
4. The lane remains design-only: no live import-support write, no schema creation, no revenue-event insertion, and no status mutation is admitted here.

## Branching Decision

Rejected design paths:

1. Retroactively amend PM Lane 278 in place.
   - Rejected because PM Lane 278 is already executed, validated, and accepted closed with a narrower admitted write boundary.
2. Fold import-side normalization into the later Lane 280 status-mutation extension.
   - Rejected because scope-pool allocation, project snapshoting, and apparatus quoted revenue are prerequisites for status-triggered recognition, not side effects that should first appear during `Complete` disposition.

Selected design path:

1. Create one later sibling packet that runs after Lane 278 core import proof and before any Lane 280 or Lane 411 live implementation packet.

## Future Sibling Route Contract

Recommended future route:

`POST /api/v1/mutations/project-import-contract-support`

Entity and action:

```text
entity_type = pm_import_contract_support
action_type = persist_import_contract_support
```

Required preconditions:

1. PM actor
2. online source
3. mutation class `C`
4. PM Lane 278 import-status readback returns `classification=imported`
5. `current_candidate_match=true`
6. `counts_match=true`
7. imported project id is `pm-import-project-miner-temp-power`
8. no-go checks pass for contract value, hours, scope allocation, and apparatus revenue reconciliation
9. same-payload replay returns `idempotent_hit`
10. mismatched replay is rejected

## Admitted Future Writes

If a later live packet admits this route, it may write only:

1. one `seam.project_contract_snapshots` row with `snapshot_kind = 'original'`
2. the required `seam.scope_labor_details` rows for the four estimator pools after scope allocation
3. imported `seam.apparatus.quoted_hours`
4. imported `seam.apparatus.quoted_revenue`
5. imported `seam.apparatus.contract_snapshot_id`
6. one audit event
7. one idempotency cache entry

This future packet does not admit:

1. `seam.apparatus_revenue_events`
2. apparatus status mutation
3. billing, payroll, invoice, accounting, or customer billing delivery
4. change-order execution
5. source workbook writeback or macros

## Required Source Extractor Contract

The sibling packet must extract and normalize these source values:

1. `Onsite Labor Total (adjusted)` -> `labor_category = 'Onsite Labor'`
2. `Offsite Labor Total (adjusted)` -> `labor_category = 'Offsite Labor'`
3. `Travel Total` -> `labor_category = 'Travel'`
4. `Outside Services Total` -> `labor_category = 'Outside Services'`
5. per-apparatus `Hrs/Line` -> `apparatus.quoted_hours`
6. `Total Sheet $$$ Adjusted` -> project `contract_value`
7. contract sign date when extractable, otherwise import-support execution date

Derived values:

```text
total_quoted_hours = SUM(apparatus.quoted_hours)
recognition_rate_per_hour = contract_value / total_quoted_hours
apparatus.quoted_revenue = apparatus.quoted_hours * recognition_rate_per_hour
```

## Multi-Scope Allocation Rule

This lane adopts the same named normalization assumption used by PM Lane 411:

```text
scope_pool_amount = project_pool_amount * (scope_hours / project_hours)
```

That rule is mandatory for the sibling import-contract-support packet unless a later lane explicitly replaces it. The packet must not silently change allocation behavior on a project-by-project basis.

Required import-support no-go checks:

1. `contract_value > 0`
2. `total_quoted_hours > 0`
3. every imported apparatus row has `quoted_hours >= 0`
4. the sum of all scope-level pool amounts equals project snapshot `contract_value`
5. the sum of all apparatus-level `quoted_revenue` values reconciles to project snapshot `contract_value` within documented rounding tolerance
6. multi-scope fixtures must prove allocation with at least one non-single-scope project so single-scope Miner data cannot mask normalization defects

## Readback Contract

Recommended future readback route:

`GET /api/v1/reads/project-import-contract-support-status`

Recommended status classifications:

1. `missing`
2. `ready`
3. `stale_candidate`
4. `counts_mismatch`
5. `unavailable`

Recommended readback fields:

1. `project_id`
2. `candidate_id`
3. `classification`
4. `current_candidate_match`
5. `counts_match`
6. `contract_snapshot_count`
7. `scope_labor_detail_count`
8. `apparatus_quote_coverage_count`
9. `apparatus_missing_quote_count`
10. `snapshot_kind`
11. `source_fingerprint`
12. `scope_allocation_rule`
13. `contract_value_reconciles`
14. `total_quoted_hours_reconciles`
15. `apparatus_quoted_revenue_reconciles`
16. `revenue_recognition_authority`
17. `billing_export_authority`
18. `invoice_authority`
19. `accounting_authority`
20. `external_finance_sync_authority`

The later Lane 280 or Lane 411 live implementation packet should require this readback to be `classification=ready` before any status-triggered revenue behavior is allowed.

## Guardrails

This lane does not admit:

1. product code
2. backend route implementation
3. hosted smoke or hosted route call
4. schema migration
5. direct SQL
6. revenue event insertion
7. apparatus status mutation
8. customer reporting, billing, payroll, invoice, accounting, or external finance sync
9. source workbook/PDF edit or writeback
10. workbook macro execution
11. Render, Vercel, Olares, auth, ingress, DNS, or secret changes
12. autonomous AI business-state mutation

## Validation Before Closeout

Required validation for this documentation-only lane:

1. Packet JSON parses.
2. Decision label is present across the new PM Lane 412 doc, packet, handoff, closeout, and status supplement.
3. Selected outcome is present.
4. The branching decision explicitly rejects retroactive Lane 278 widening and Lane 280 coupling.
5. The selected future route and readback route are explicit.
6. The `scope_hours / project_hours` multi-scope allocation rule is explicit.
7. The multi-scope fixture requirement is explicit.
8. The boundary that no revenue event or status mutation is admitted is explicit.
9. `git diff --check` passes.
