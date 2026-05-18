# PM Lane 304 - Project Miner Temp Power Actuals Capture Review First Write Mutation Seam Packet Handoff

## Summary

PM Lane 304 converts the admitted first-write branch into one bounded mutation-seam implementation for the actuals-capture review route only.

The lane adds the actuals mutation route, paired readback route, insert-only migration, focused tests, and in-memory-store reset support for the new review collection. It proves accepted write, idempotent replay, current-match readback, stale-source classification, replacement-chain classification, and unchanged downstream domain counts locally.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_FIRST_WRITE_MUTATION_SEAM_PACKET`

Selected outcome:

`ACTUALS_CAPTURE_REVIEW_FIRST_WRITE_IMPLEMENTED_AND_VALIDATED_LOCALLY`

## Implementation Highlights

- add `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
- add `GET /api/v1/reads/temp-power-actuals-capture-review-status`
- enforce PM-only role, Temp Power project scope, current project/candidate/source identity, and strict idempotency replay
- keep `customer_delivery_authority`, `finance_authority`, and `source_writeback_authority` at `not_admitted`
- keep `durable_delivery_event=false`
- add insert-only migration `008_pm_lane_304_actuals_capture_reviews.sql`
- add focused pytest coverage and clean in-memory reset behavior for the new review store

## Still Blocked

- `POST /api/v1/mutations/temp-power-customer-preview-reviews`
- any customer preview persistence
- any customer delivery event or delivery-proof recording
- any finance/export/accounting behavior
- any source workbook writeback or macro behavior
- any hosted promotion or hosted live-row proof

## Next Safe Step

No second route is admitted by this lane.

Separate later admission only:

`Project Miner Temp Power Customer Preview Review First Write Packet`

Next blocker:

`CUSTOMER_PREVIEW_ROUTE_STILL_NOT_ADMITTED_OR_IMPLEMENTED`

## Validation Before Closeout

Run before publication:

```powershell
Get-Content ops/agents/packets/draft/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet.json | ConvertFrom-Json
Select-String -Path PROJECT_STATUS.md,docs/operations/APEX-PM-LANE-304-PROJECT-MINER-TEMP-POWER-ACTUALS-CAPTURE-REVIEW-FIRST-WRITE-MUTATION-SEAM-PACKET-2026-05-18.md,ops/agents/packets/draft/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet.json,ops/agents/handoffs/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet-handoff.md,ops/agents/handoffs/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet-closeout.md -Pattern "PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_FIRST_WRITE_MUTATION_SEAM_PACKET|ACTUALS_CAPTURE_REVIEW_FIRST_WRITE_IMPLEMENTED_AND_VALIDATED_LOCALLY|temp-power-actuals-capture-reviews|temp-power-actuals-capture-review-status|008_pm_lane_304_actuals_capture_reviews.sql|customer-preview|customer delivery event|finance/export/accounting|source workbook writeback|CUSTOMER_PREVIEW_ROUTE_STILL_NOT_ADMITTED_OR_IMPLEMENTED"
git diff --check -- PROJECT_STATUS.md docs/operations/APEX-PM-LANE-304-PROJECT-MINER-TEMP-POWER-ACTUALS-CAPTURE-REVIEW-FIRST-WRITE-MUTATION-SEAM-PACKET-2026-05-18.md ops/agents/packets/draft/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet.json ops/agents/handoffs/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet-handoff.md ops/agents/handoffs/2026-05-18-pm-lane-304-project-miner-temp-power-actuals-capture-review-first-write-mutation-seam-packet-closeout.md
```