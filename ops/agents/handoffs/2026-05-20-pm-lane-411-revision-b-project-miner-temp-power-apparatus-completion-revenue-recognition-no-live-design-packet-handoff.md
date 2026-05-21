# PM Lane 411 Revision B - Apparatus Completion Revenue Recognition No-Live Design Packet Handoff

## Summary

PM Lane 411 Revision B layers on top of the historical Lane 411 design and Lane 411 Revision A to tighten the future Lane 280 status-mutation extension gate.

The revision does not modify any Revision A financial or security surface. It adds only the missing reverse statement that Lane 280 live admission is blocked until Lane 412 import-contract-support readback is `ready`.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_REVISION_B`

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE_REVISION_B`

## Design Highlights

- The Lane 280 precondition list now includes a Lane 412 readback requirement: `GET /api/v1/reads/project-import-contract-support-status` must show `classification = ready`, `current_candidate_match = true`, and `counts_match = true`.
- A dedicated admission-time gate section now makes the timing explicit: the Lane 412 readback gate is evaluated once when live admission is granted, not on every recognition mutation call.
- The Lane 280 readback contract now includes `lane_412_readback_classification_at_admission_time` for audit traceability.
- The boundary list now explicitly states that Lane 280 live admission is undiscussable until the Lane 412 readback gate passes.
- Revision A surfaces remain inherited and unchanged: recognition firewall, `seam.apparatus_financials`, role-based table separation, RLS grants, multi-scope math, and operational-hours reservation all stay intact.

## Boundary

No live revenue-event write, schema migration, public schema write, billing/payroll/invoice/accounting/customer-billing/external-finance output, source workbook writeback, workbook macro, change-order admission, live operational-hours implementation, or autonomous AI business-state mutation is admitted by this revision. Live admission of Lane 280 remains separately blocked until Lane 412 readback is `ready`.

## Validation Before Closeout

```powershell
Get-Content ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-411-REVISION-B-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md,ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md -Pattern "classification = ready|lane_412_readback_classification_at_admission_time|admission-time gate|bidirectional"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-REVISION-B-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-revision-b-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md
```