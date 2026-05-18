# PM Lane 296 - Project Miner Temp Power Actuals And Customer Capture Route And Payload Design No-Live Packet Handoff

## Summary

PM Lane 296 converts the actuals/customer storage and readback design into exact future request contracts only.

The lane defines the future mutation routes, common envelope requirements, action types, required payload fields, replay behavior, success/failure expectations, readback proof, and the separate execution-gate requirement. No implementation, no request send, and no persistence behavior is admitted.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_ROUTE_AND_PAYLOAD_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_ROUTE_AND_PAYLOAD_DESIGN_READY_NO_LIVE`

## Route And Payload Highlights

- future routes: `POST /api/v1/mutations/temp-power-actuals-capture-reviews`, `POST /api/v1/mutations/temp-power-customer-preview-reviews`
- required `mutation_class: C`
- exact matching envelope/payload idempotency keys
- exact current project/candidate/source identity
- action types: `persist_temp_power_actuals_capture_review`, `persist_temp_power_customer_preview_review`
- customer preview must keep `durable_delivery_event=false` and `delivery_proof_recorded=false`
- successful future writes must be followed by matching status readback

## Separate Execution Gate

First execution of either future route must remain owned by a separate explicit execution-gate packet.

## Next Lane

`PM Lane 297 - Project Miner Temp Power Actuals And Customer Capture Execution Gate Design No-Live Packet`

Next blocker:

`STOPPED_AWAITING_PM_LANE_297_ACTUALS_CUSTOMER_CAPTURE_EXECUTION_GATE_DESIGN_NO_LIVE`

## Validation Before Closeout

Run before publication:

```powershell
Get-Content ops/agents/packets/draft/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-296-PROJECT-MINER-TEMP-POWER-ACTUALS-AND-CUSTOMER-CAPTURE-ROUTE-AND-PAYLOAD-DESIGN-NO-LIVE-PACKET-2026-05-18.md,ops/agents/packets/draft/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet.json,ops/agents/handoffs/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet-handoff.md,ops/agents/handoffs/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet-closeout.md -Pattern "PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_ROUTE_AND_PAYLOAD_DESIGN_NO_LIVE_NO_OUTPUT_WRITE|ACTUALS_CUSTOMER_CAPTURE_ROUTE_AND_PAYLOAD_DESIGN_READY_NO_LIVE|temp-power-actuals-capture-reviews|temp-power-customer-preview-reviews|persist_temp_power_actuals_capture_review|persist_temp_power_customer_preview_review|durable_delivery_event=false|delivery_proof_recorded=false|separate explicit execution-gate packet|Customer billing delivery|External finance sync"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-296-PROJECT-MINER-TEMP-POWER-ACTUALS-AND-CUSTOMER-CAPTURE-ROUTE-AND-PAYLOAD-DESIGN-NO-LIVE-PACKET-2026-05-18.md ops/agents/packets/draft/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet.json ops/agents/handoffs/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet-handoff.md ops/agents/handoffs/2026-05-18-pm-lane-296-project-miner-temp-power-actuals-and-customer-capture-route-and-payload-design-no-live-packet-closeout.md
```