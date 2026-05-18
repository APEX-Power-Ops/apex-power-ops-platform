# PM Lane 307 Closeout - Project Miner Temp Power Actuals Capture Review Hosted Route Redeploy Gate Packet

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_HOSTED_ROUTE_REDEPLOY_GATE_PACKET`

Selected outcome:

`HOSTED_ACTUALS_ROUTE_ABSENT_REDEPLOY_REQUIRED`

## Summary

PM Lane 307 is complete.

Hosted smoke for the admitted Temp Power actuals route was executed against both existing live mutation-seam hosts. Both hosts passed the legacy seam checks but failed the new Temp Power actuals route checks in the same way: OpenAPI did not expose either actuals route, and the actuals readback returned framework `404 Not Found`. The blocker is therefore a service redeploy, not custom-domain drift.

## Final Validation Before Closeout

Result: PASS.

Completed checks:

1. hosted smoke against `https://mutation-seam.apexpowerops.com`
2. hosted smoke against `https://apex-platform-mutation-seam.onrender.com`
3. diagnostics check on `.github/workflows/deployed-mutation-seam-smoke.yml` and `.vscode/tasks.json`
4. `.vscode/tasks.json` parse
5. `git diff --check`

## Next Stop

`HOSTED_MUTATION_SEAM_REDEPLOY_REQUIRED_BEFORE_ANY_ACTUALS_ROUTE_HOSTED_PROOF`