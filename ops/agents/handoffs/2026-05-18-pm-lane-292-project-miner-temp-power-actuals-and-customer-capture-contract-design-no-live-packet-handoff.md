# PM Lane 292 - Project Miner Temp Power Actuals And Customer Capture Contract Design No-Live Packet Handoff

## Summary

PM Lane 292 converts the accepted Lane 291 actuals/customer defaults into a no-live contract-design surface.

The lane defines explicit contract fields, validators, review checklist items, and future payload templates for actuals capture and customer preview while keeping persistence, delivery, finance outputs, source writeback, and all live/runtime behavior blocked.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_READY_NO_LIVE`

## Actuals Capture Contract Highlights

- fixed identity: `project_id`, `candidate_id`, `source_fingerprint`
- required task ownership: `task_id`
- apparatus-specific capture requires `apparatus_id`; otherwise `task_day_fallback_reason`
- `recorder_role` limited to `PM` or `FIELD_LEAD`
- `actual_labor_hours_preview` is nonnegative and review-only
- nonzero actuals require `evidence_bundle`
- replacement flow is append-only through `VOID_AND_REPLACEMENT`, `supersedes_capture_id`, and `replacement_reason`
- PM review fields are required before any later billable or payroll relevance

## Customer Preview Contract Highlights

- fixed preview identity through `customer_preview_id`
- required named recipient and recipient role
- approver role limited to `PM`
- `delivery_channel` limited to `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`
- `preview_artifact_refs` remain preview-only
- `durable_delivery_event` is fixed to `false`
- `future_delivery_proof_requirements` can describe later proof only

## Boundary

No product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation is admitted by this lane.

## Next Lane

`PM Lane 293 - Project Miner Temp Power Actuals And Customer Capture Review Surface Design No-Live Packet`

Next blocker:

`STOPPED_AWAITING_PM_LANE_293_ACTUALS_CUSTOMER_CAPTURE_REVIEW_SURFACE_DESIGN_NO_LIVE`

## Validation Before Closeout

Run before publication:

```powershell
Get-Content ops/agents/packets/draft/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-292-PROJECT-MINER-TEMP-POWER-ACTUALS-AND-CUSTOMER-CAPTURE-CONTRACT-DESIGN-NO-LIVE-PACKET-2026-05-18.md,ops/agents/packets/draft/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet.json,ops/agents/handoffs/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet-handoff.md,ops/agents/handoffs/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet-closeout.md -Pattern "PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_NO_LIVE_NO_OUTPUT_WRITE|ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_READY_NO_LIVE|task_id|recorder_role|actual_labor_hours_preview|customer_preview_id|delivery_channel|durable_delivery_event|Customer billing delivery|External finance sync"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-292-PROJECT-MINER-TEMP-POWER-ACTUALS-AND-CUSTOMER-CAPTURE-CONTRACT-DESIGN-NO-LIVE-PACKET-2026-05-18.md ops/agents/packets/draft/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet.json ops/agents/handoffs/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet-handoff.md ops/agents/handoffs/2026-05-18-pm-lane-292-project-miner-temp-power-actuals-and-customer-capture-contract-design-no-live-packet-closeout.md
```