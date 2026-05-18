# PM Lane 315 - Customer Preview Review First Write Publication And Hosted Promotion Gate

## Summary

PM Lane 315 is in progress with local implementation and publication complete.

The admitted Temp Power customer-preview review first-write slice was implemented, locally proven, and published to `clean-main` as `666f649d7cf477af3c657bcf4194975ad6dbf359`. Immediate bounded hosted smoke against both the custom domain and the Render hostname still shows the pre-publication hosted route surface, so the current blocker is hosted promotion lag rather than a local code-path defect.

## Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_FIRST_WRITE_PUBLICATION_AND_HOSTED_PROMOTION_GATE`

Selected outcome:

`CUSTOMER_PREVIEW_REVIEW_PUBLISHED_HOSTED_PROMOTION_PENDING`

## Publication Evidence

1. commit pushed to `origin/clean-main`: `666f649d7cf477af3c657bcf4194975ad6dbf359`
2. commit title: `Add temp power customer preview review slice`
3. focused pytest for `apps/mutation-seam/tests/test_temp_power_customer_preview_review_persistence.py` passed with `6 passed`
4. local proof runner `apps/mutation-seam/scripts/run_temp_power_customer_preview_review_local_proof.py` passed with accepted write, idempotent replay, delivery-blocked readback, unchanged downstream counts, and blocked boundary fields preserved

## Immediate Hosted Truth

Custom domain hosted smoke immediately after publication:

```text
health status=200 detail=ok
root status=200 detail=ok
reads_approval_queue status=200 detail=ok
schedule_projects status=200 detail=ok
schedule_drivers status=200 detail=ok
schedule_tracer status=200 detail=ok
schedule_variance status=200 detail=ok
openapi_temp_power_actuals_review status=200 detail=ok
temp_power_actuals_capture_review_status status=200 detail=ok
openapi_temp_power_customer_preview_review status=200 detail=ok
temp_power_customer_preview_status status=404 detail=Not Found
RESULT FAIL
FAILURE openapi missing /api/v1/mutations/temp-power-customer-preview-reviews
FAILURE openapi missing /api/v1/reads/temp-power-customer-preview-status
FAILURE temp_power_customer_preview_status returned framework 404 Not Found
```

Render hostname hosted smoke immediately after publication:

```text
health status=200 detail=ok
root status=200 detail=ok
reads_approval_queue status=200 detail=ok
schedule_projects status=200 detail=ok
schedule_drivers status=200 detail=ok
schedule_tracer status=200 detail=ok
schedule_variance status=200 detail=ok
openapi_temp_power_actuals_review status=200 detail=ok
temp_power_actuals_capture_review_status status=200 detail=ok
openapi_temp_power_customer_preview_review status=200 detail=ok
temp_power_customer_preview_status status=404 detail=Not Found
RESULT FAIL
FAILURE openapi missing /api/v1/mutations/temp-power-customer-preview-reviews
FAILURE openapi missing /api/v1/reads/temp-power-customer-preview-status
FAILURE temp_power_customer_preview_status returned framework 404 Not Found
```

## Blocker Classification

1. local code path is green: focused tests and first-write proof both pass
2. both hosted seam URLs fail in the same way
3. actuals hosted routes remain healthy on both hosts
4. therefore the remaining blocker is deploy promotion lag for the newly published customer-preview review slice, not a custom-domain-only issue and not a newly exposed local implementation defect

## Boundary Status

1. admitted and locally proven in this lane: customer-preview review first-write persistence and readback
2. still not admitted: hosted customer-preview POST execution
3. still not admitted: customer delivery completion or durable delivery proof
4. still not admitted: finance, payroll, billing, invoice, accounting, or source-system writeback outputs

## Next Action

Rerun the same bounded hosted smoke on both seam URLs after Render promotion catches up. Close the lane only after both hosts expose the new OpenAPI paths and the customer-preview status readback returns `200`.