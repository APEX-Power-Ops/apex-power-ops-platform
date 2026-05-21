# PM Lane 411 - Project Miner Temp Power Apparatus Completion Revenue Recognition No-Live Design Packet Handoff

## Summary

PM Lane 411 converts the current apparatus-completion revenue-recognition proposal into a bounded no-live design surface.

The request is correctly classified under PM Lane 352's return label `OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED` because it describes future output writes triggered by apparatus completion. This lane stops before live admission and authors the governing design first.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_NO_OUTPUT_WRITE`

Selected outcome:

`APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE`

## Design Highlights

- Recognition is fixed to one project-level frozen hours-weighted rate: `contract_value / total_quoted_hours`.
- Estimator pools remain separate imported metadata for cost analysis only: `Onsite Labor`, `Offsite Labor`, `Travel`, and `Outside Services`.
- `seam.project_contract_snapshots` carries versioned contract snapshots, but `snapshot_kind` is recommended as constrained text instead of a literal enum so future `change_order_N` values do not require enum migrations.
- The stored snapshot fields now require an internal consistency check so `recognition_rate_per_hour` must reconcile to `contract_value / total_quoted_hours` within tolerance.
- Revenue-recognition authority defaults should remain `not_admitted` on both snapshots and events; any admitted authority must be set explicitly by the inserting route.
- `seam.apparatus` gains frozen `quoted_hours`, `quoted_revenue`, and `contract_snapshot_id`.
- `seam.apparatus_revenue_events` is insert-only with `apparatus_revenue_zero_baseline`, `apparatus_revenue_recognized`, and `apparatus_revenue_reversed` rows plus idempotency and audit linkage.
- `seam.v_scope_financials` derives scope recognition and then re-splits recognized revenue back across static pool weights at query time, using `total_scope_pool_amount` as the denominator so multi-scope projects reconcile correctly.
- PM Lane 412 is the selected sibling import-contract-support packet. It must extract pool totals, apparatus hours, and original snapshot values before any later recognition write can exist.
- Lane 280's apparatus status mutation route can be extended later so PM disposition to `Complete` and revenue-event insertion happen in one transaction with same-payload replay returning `idempotent_hit`, and readback should include `event_id` for later reversal workflows.
- Reversal rows must inherit `contract_snapshot_id` from the original recognized row, and V1 disallows double reversal.
- The later implementation packet must include an explicit multi-scope fixture; Miner Temp Power alone will not expose the normalization bug because it is single-scope.

## Boundary

No product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, public schema write, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, live revenue event, billing export, payroll export, invoice, accounting post, customer billing delivery, external finance sync, source workbook/PDF writeback, workbook macro, change-order admission, or autonomous AI business-state mutation is admitted by this lane.

## Next Truth

The next truthful follow-on is a separate later admission packet if PM wants any schema creation, import-contract implementation, baseline seeding, apparatus-status mutation extension, or live apparatus revenue recognition write. This lane itself remains design-only.

## Validation Before Closeout

Run before publication:

```powershell
Get-Content ops/agents/packets/draft/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-411-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md,ops/agents/packets/draft/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md -Pattern "PROJECT_MINER_TEMP_POWER_APPARATUS_COMPLETION_REVENUE_RECOGNITION_NO_LIVE_DESIGN_NO_OUTPUT_WRITE|APPARATUS_COMPLETION_REVENUE_RECOGNITION_DESIGN_READY_NO_LIVE|OUTPUT_WRITE_REQUEST_SEPARATE_ADMISSION_REQUIRED|snapshot_kind|change_order_|apparatus_revenue_zero_baseline|apparatus_revenue_reversed|idempotent_hit"
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-411-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md,ops/agents/packets/draft/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json,ops/agents/handoffs/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md,ops/agents/handoffs/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md -Pattern "total_scope_pool_amount|not_admitted|event_id|contract_snapshot_id must equal|Cost data pending"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-411-PROJECT-MINER-TEMP-POWER-APPARATUS-COMPLETION-REVENUE-RECOGNITION-NO-LIVE-DESIGN-PACKET-2026-05-20.md ops/agents/packets/draft/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet.json ops/agents/handoffs/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-handoff.md ops/agents/handoffs/2026-05-20-pm-lane-411-project-miner-temp-power-apparatus-completion-revenue-recognition-no-live-design-packet-closeout.md
```