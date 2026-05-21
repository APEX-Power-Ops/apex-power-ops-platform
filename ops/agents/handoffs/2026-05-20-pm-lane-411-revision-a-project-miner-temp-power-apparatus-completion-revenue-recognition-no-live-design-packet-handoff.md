# PM Lane 411 Revision A - Apparatus Completion Revenue Recognition No-Live Design Packet Handoff

## Summary

PM Lane 411 Revision A layers on top of the historical Lane 411 design and moves frozen quote data out of `seam.apparatus` into `seam.apparatus_financials`.

The revision preserves the earlier multi-scope normalization correction while codifying the recognition firewall, table-level role separation, and the removal of the legacy actual revenue term from the design vocabulary.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_REVISION_A`

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE_REVISION_A`

## Design Highlights

- `seam.apparatus` is now identity/status/location only and no longer carries `quoted_hours`, `quoted_revenue`, or `contract_snapshot_id`.
- `seam.apparatus_financials` is the new frozen quote-data table with insert-only discipline, `(apparatus_id, contract_snapshot_id)` uniqueness, and an internal-consistency CHECK on `recognition_rate_per_hour_snapshot`.
- Financial tables are PM-and-Finance-only by RLS grant: Field Tech and Field Lead have no SELECT on `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, or `seam.apparatus_revenue_events`.
- `seam.v_scope_financials` now sources `total_quoted_revenue` from `seam.apparatus_financials` joined to `seam.apparatus`.
- The future Lane 280 extension now reads `expected_quoted_revenue` and `recognized_amount` from `seam.apparatus_financials.quoted_revenue`.
- Operational hours tracking is explicitly reserved to a later lane and is outside the recognition path.

## Boundary

No live revenue-event write, schema migration, public schema write, billing/payroll/invoice/accounting/customer-billing/external-finance output, source workbook writeback, workbook macro, change-order admission, or live operational-hours implementation is admitted by this revision.

## Validation Before Closeout

```powershell
Get-Content ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-411-REVISION-A-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md,ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md -Pattern "apparatus_financials|recognition_rate_per_hour_snapshot|Field Tech|Field Lead|operational hours tracking|quoted_revenue"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-REVISION-A-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md docs/operations/APEX-PM-LANE-412-REVISION-A-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-REVISION-A-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md docs/operations/APEX-PM-LANE-412-REVISION-A-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md
```