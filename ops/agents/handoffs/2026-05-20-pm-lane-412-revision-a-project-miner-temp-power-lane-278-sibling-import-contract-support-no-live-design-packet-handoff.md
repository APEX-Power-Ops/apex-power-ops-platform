# PM Lane 412 Revision A - Lane 278 Sibling Import Contract Support No-Live Design Packet Handoff

## Summary

PM Lane 412 Revision A layers on top of the historical Lane 412 design and changes the future import-support packet so frozen quote data is inserted into `seam.apparatus_financials` instead of being written onto `seam.apparatus`.

The revision keeps the sibling-lane split from historical Lane 278 and preserves the recognition firewall and role-based table separation.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_278_SIBLING_IMPORT_CONTRACT_SUPPORT_NO_LIVE_DESIGN_REVISION_A`

Selected outcome:

`IMPORT_CONTRACT_SUPPORT_DESIGN_READY_NO_LIVE_REVISION_A`

## Design Highlights

- `allowed_future_writes` is now pure insert-only support persistence: original project snapshot, scope labor details, and one `seam.apparatus_financials` row per apparatus per snapshot.
- Extractor mapping now lands `Hrs/Line`, derived `quoted_revenue`, and denormalized `recognition_rate_per_hour_snapshot` on `seam.apparatus_financials`.
- Readback coverage semantics now measure distinct apparatus coverage from `seam.apparatus_financials`, not quote columns on `seam.apparatus`.
- PM role may later INSERT into `seam.apparatus_financials`; Field Tech and Field Lead have no SELECT or INSERT on the table.
- The earlier nullable `apparatus.contract_snapshot_id` concern and update-then-freeze concern are both resolved structurally by this refactor.

## Boundary

No live route implementation, schema migration, import-support write, revenue-event write, apparatus status mutation, billing/payroll/invoice/accounting/customer-billing/external-finance output, source workbook writeback, workbook macro, or live operational-hours implementation is admitted by this revision.

## Validation Before Closeout

```powershell
Get-Content ops/agents/packets/draft/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-412-REVISION-A-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md,ops/agents/packets/draft/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md -Pattern "apparatus_financials|Field Tech|Field Lead|recognition_rate_per_hour_snapshot|structural"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-REVISION-A-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md docs/operations/APEX-PM-LANE-412-REVISION-A-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-REVISION-A-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-revision-a-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md docs/operations/APEX-PM-LANE-412-REVISION-A-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-412-revision-a-project-miner-temp-power-lane-278-sibling-import-contract-support-no-live-design-packet-closeout.md
```