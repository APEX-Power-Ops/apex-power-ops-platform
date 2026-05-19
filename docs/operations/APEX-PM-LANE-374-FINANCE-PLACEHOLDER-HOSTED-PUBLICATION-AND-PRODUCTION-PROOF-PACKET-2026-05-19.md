# APEX PM Lane 374 - Finance Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Hosted publication complete and production proof recorded for the admitted read-only finance-placeholder planning route.

Decision label:

`PM_FINANCE_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 374 closes the next truthful blocker after PM Lane 373 by proving the finance-placeholder route is now publicly published on operations-web production and covered by the same promoted-host smoke path that was added locally in the readiness tranche.

This lane records current hosted truth only. It does not widen finance authority beyond the already admitted read-only placeholder planning surface.

## Selected Outcome

Selected outcome:

`PM_FINANCE_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

## Hosted Publication Proof

The current production publication path for the finance-placeholder route is:

1. clean-main commit `47c2d712` created ready preview deployment `FWiFm21S4k4RACQRJ9RayJ4W5Bfr`,
2. that preview was available at `https://apex-operations-web-git-clean-main-jasonlswenson-sys-projects.vercel.app`,
3. the ready preview was promoted to production deployment `H7SMQhyYRuxmBZegBKH74ym8zska`,
4. the production deployment now serves both `https://apex-operations-web.vercel.app` and `https://operations.apexpowerops.com`.

Hosted publication is no longer the controlling blocker for the finance-placeholder route.

## Public Route Proof

Public route verification now succeeds on both production aliases:

1. `https://apex-operations-web.vercel.app/pm-review/finance-placeholder`
2. `https://operations.apexpowerops.com/pm-review/finance-placeholder`

Both public fetches returned the route marker:

1. `Finance is open only as a placeholder design branch.`

That public body confirms the route is not a dead link, not a 404, and not a stale pre-Lane-372 bundle.

## Hosted Smoke Proof

The production hosted-route smoke now passes end to end on the custom production domain:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=15 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/finance-placeholder status=200 marker="Finance is open only as a placeholder design branch."
```

This proves the promoted-host smoke control surface now matches the real production deployment for the finance-placeholder route.

## Boundary

This lane records hosted publication and production proof only.

It does not admit or claim:

1. finance writes, exports, invoice generation, billing, payroll, accounting, or external finance sync,
2. customer billing delivery,
3. source workbook or PDF writeback,
4. workbook macro execution,
5. any new backend seam or mutation route,
6. autonomous AI business-state mutation.

## Notes

Immediately after the promote action, the custom production domain still returned `404` while the new production deployment was building and assigning domains. After production deployment `H7SMQhyYRuxmBZegBKH74ym8zska` reached `Ready`, both the default Vercel alias and the custom domain returned the expected finance-placeholder content.

## Next Truth

The hosted-publication blocker for the finance-placeholder route is closed.

Any next PM move should target a different explicitly admitted branch rather than another finance-placeholder publication proof tranche.