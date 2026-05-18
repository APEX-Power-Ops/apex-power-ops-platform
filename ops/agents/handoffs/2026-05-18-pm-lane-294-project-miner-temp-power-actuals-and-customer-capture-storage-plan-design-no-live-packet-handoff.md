# PM Lane 294 - Project Miner Temp Power Actuals And Customer Capture Storage Plan Design No-Live Packet Handoff

## Summary

PM Lane 294 converts the actuals/customer contract and review-surface design into a future storage-plan decision only.

The lane recommends dedicated insert-only mutation-seam-owned storage, future mutation/readback routes, required columns and constraints, adapter/readback requirements, and rejected unsafe storage shortcuts. No schema, no route, no persistence, and no delivery behavior is admitted.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_STORAGE_PLAN_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_STORAGE_PLAN_DESIGN_READY_NO_LIVE`

## Recommended Storage Decision

- tables: `seam.pm_actuals_capture_reviews`, `seam.pm_customer_preview_reviews`
- entity types: `pm_actuals_capture_review`, `pm_customer_preview_review`
- future mutation routes: `/api/v1/mutations/temp-power-actuals-capture-reviews`, `/api/v1/mutations/temp-power-customer-preview-reviews`
- future readback routes: `/api/v1/reads/temp-power-actuals-capture-review-status`, `/api/v1/reads/temp-power-customer-preview-status`
- customer preview storage must preserve `durable_delivery_event=false`

## Rejected Unsafe Storage Options

- audit-log-only canonical storage
- reusing project/task/apparatus/delivery rows
- browser-local storage as canonical PM review state
- generic PgDict upsert without a dedicated adapter
- direct Supabase writes from Excel, UI, or ad hoc scripts
- any storage path implying customer delivery or finance export occurred

## Next Lane

`PM Lane 295 - Project Miner Temp Power Actuals And Customer Capture Readback Design No-Live Packet`

Next blocker:

`STOPPED_AWAITING_PM_LANE_295_ACTUALS_CUSTOMER_CAPTURE_READBACK_DESIGN_NO_LIVE`

## Validation Before Closeout

Run before publication:

```powershell
Get-Content ops/agents/packets/draft/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-294-PROJECT-MINER-TEMP-POWER-ACTUALS-AND-CUSTOMER-CAPTURE-STORAGE-PLAN-DESIGN-NO-LIVE-PACKET-2026-05-18.md,ops/agents/packets/draft/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet.json,ops/agents/handoffs/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet-handoff.md,ops/agents/handoffs/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet-closeout.md -Pattern "PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_STORAGE_PLAN_DESIGN_NO_LIVE_NO_OUTPUT_WRITE|ACTUALS_CUSTOMER_CAPTURE_STORAGE_PLAN_DESIGN_READY_NO_LIVE|seam.pm_actuals_capture_reviews|seam.pm_customer_preview_reviews|temp-power-actuals-capture-reviews|temp-power-customer-preview-reviews|durable_delivery_event|audit-log-only|Customer billing delivery|External finance sync"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-294-PROJECT-MINER-TEMP-POWER-ACTUALS-AND-CUSTOMER-CAPTURE-STORAGE-PLAN-DESIGN-NO-LIVE-PACKET-2026-05-18.md ops/agents/packets/draft/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet.json ops/agents/handoffs/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet-handoff.md ops/agents/handoffs/2026-05-18-pm-lane-294-project-miner-temp-power-actuals-and-customer-capture-storage-plan-design-no-live-packet-closeout.md
```