# PM Lane 307 - Project Miner Temp Power Actuals Capture Review Hosted Route Redeploy Gate Packet Handoff

## Summary

PM Lane 307 executed the first hosted Temp Power actuals-route smoke against both live mutation-seam hosts and closed the blocker precisely.

Both `https://mutation-seam.apexpowerops.com` and `https://apex-platform-mutation-seam.onrender.com` still serve a build that does not expose the Temp Power actuals-capture review routes.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_HOSTED_ROUTE_REDEPLOY_GATE_PACKET`

Selected outcome:

`HOSTED_ACTUALS_ROUTE_ABSENT_REDEPLOY_REQUIRED`

## Evidence

- `/health` passed on both hosts
- root passed on both hosts
- approval queue passed on both hosts
- schedule reads passed on both hosts
- `openapi.json` passed on both hosts
- OpenAPI omitted `/api/v1/mutations/temp-power-actuals-capture-reviews` on both hosts
- OpenAPI omitted `/api/v1/reads/temp-power-actuals-capture-review-status` on both hosts
- `GET /api/v1/reads/temp-power-actuals-capture-review-status` returned framework `404 Not Found` on both hosts

## Classification

This is not custom-domain drift.

Because the custom domain and the Render hostname fail identically, the truthful classification is service-wide hosted deploy lag. The existing hosted service must be redeployed before any hosted actuals-route proof can continue.

## Repo-Owned Follow-Through Added

- workflow input `include_temp_power_actuals_review` on `.github/workflows/deployed-mutation-seam-smoke.yml`
- VS Code task `Mutation-seam hosted actuals-review smoke`
- deployment-validation note in `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`

## Next Safe Step

1. redeploy the existing hosted mutation-seam service from current `clean-main`
2. rerun hosted smoke with `--include-temp-power-actuals-review`
3. only if hosted smoke turns green, decide whether hosted first-write proof is separately admitted