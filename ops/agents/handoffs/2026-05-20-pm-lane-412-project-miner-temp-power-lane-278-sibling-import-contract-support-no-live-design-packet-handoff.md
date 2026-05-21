# PM Lane 412 - Lane 278 Sibling Import Contract Support No-Live Design Packet Handoff

## Summary

PM Lane 412 isolates the import-side contract-support extractor from both historical PM Lane 278 and the later Lane 280 status-mutation branch.

The lane keeps PM Lane 278 historically stable as the already executed core import proof, then defines a separate future sibling packet for project contract snapshots, scope labor details, and apparatus quote-field population.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_278_SIBLING_IMPORT_CONTRACT_SUPPORT_NO_LIVE_DESIGN`

Selected outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE`

## Branching Decision

- Retroactive Lane 278 widening is rejected because the historical live-admission packet is already executed and accepted closed with a narrower write scope.
- Folding import normalization into Lane 280 is rejected because snapshoting, scope-pool allocation, and apparatus quoted revenue are prerequisites for later status-triggered recognition.
- The selected path is a separate future sibling packet after Lane 278 core import and before any later Lane 280 or Lane 411 live implementation.

## Design Highlights

- The future admitted route is `POST /api/v1/mutations/project-import-contract-support` with entity/action `pm_import_contract_support` / `persist_import_contract_support`.
- The route is gated by existing Lane 278 import readback: `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- The route may write only one original `seam.project_contract_snapshots` row, the required `seam.scope_labor_details` rows, imported apparatus `quoted_hours`, imported apparatus `quoted_revenue`, imported apparatus `contract_snapshot_id`, one audit event, and one idempotency entry.
- Required extracts are the four adjusted estimator pools, per-apparatus `Hrs/Line`, `Total Sheet $$$ Adjusted`, and contract sign date when extractable.
- The governing multi-scope allocation rule is `scope_pool_amount = project_pool_amount * (scope_hours / project_hours)`.
- A future `GET /api/v1/reads/project-import-contract-support-status` readback should prove snapshot count, scope labor detail count, apparatus quote coverage, candidate match, counts match, and reconciliation booleans before any later status-triggered revenue packet is admitted.
- The explicit multi-scope fixture requirement is preserved so single-scope Miner data cannot mask normalization defects.

## Boundary

No product code, route implementation, hosted call, schema migration, direct SQL, revenue-event insertion, apparatus status mutation, billing/payroll/invoice/accounting/customer billing output, source workbook writeback, workbook macro execution, service/auth/ingress/secret change, or autonomous AI business-state mutation is admitted by this lane.

## Validation Before Closeout

Run before publication:

```powershell
Get-Content ops/agents/packets/draft/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-412-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md,ops/agents/packets/draft/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md -Pattern "PROJECT_MINER_TEMP_POWER_LANE_278_SIBLING_IMPORT_CONTRACT_SUPPORT_NO_LIVE_DESIGN|IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE|project-import-contract-support|project-import-contract-support-status|scope_hours / project_hours"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-412-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-412-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md
```