# APEX PM Lane 376 - Customer Billing Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Hosted publication complete and production proof recorded for the admitted read-only customer-billing placeholder planning route.

Decision label:

`PM_CUSTOMER_BILLING_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 376 closes the next truthful blocker after PM Lane 375 by proving the customer-billing placeholder route is now publicly published on operations-web production and covered by the same promoted-host smoke path that was added locally in the readiness tranche.

This lane records current hosted truth only. It does not widen customer billing authority beyond the already admitted read-only placeholder planning surface.

## Selected Outcome

Selected outcome:

`PM_CUSTOMER_BILLING_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

## Hosted Publication Proof

The current production publication path for the customer-billing placeholder route is:

1. clean-main commit `6e3c35c4` created ready preview deployment `dpl_9MWnV8TeiPgXWqRUeQdWMSPgFWtQ`,
2. that preview was available at `https://apex-operations-qowhalov5-jasonlswenson-sys-projects.vercel.app`,
3. the ready preview was promoted to production deployment `dpl_5uCHB9KLyhhV4thQJ31BAuAKzT21`,
4. the production deployment now serves both `https://apex-operations-web.vercel.app` and `https://operations.apexpowerops.com`.

Hosted publication is no longer the controlling blocker for the customer-billing placeholder route.

## Public Route Proof

Direct HTTP verification now succeeds on both production aliases:

1. `https://operations.apexpowerops.com/pm-review/customer-billing-placeholder`
2. `https://apex-operations-web.vercel.app/pm-review/customer-billing-placeholder`

Both public checks returned:

1. HTTP `200`,
2. route marker present: `Customer billing delivery stays blocked as a placeholder downstream branch.`

## Hosted Smoke Proof

The production hosted-route smoke now passes end to end on the custom production domain:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=16 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/customer-billing-placeholder status=200 marker="Customer billing delivery stays blocked as a placeholder downstream branch."
```

This proves the promoted-host smoke control surface now matches the real production deployment for the customer-billing placeholder route.

## Boundary

This lane records hosted publication and production proof only.

It does not admit or claim:

1. customer billing release authority,
2. invoice dispatch, billing export release, customer-facing billing notification, or external finance sync,
3. finance writes, payroll, accounting persistence, or other finance-output authority,
4. source workbook or PDF writeback,
5. workbook macro execution,
6. any new backend seam or mutation route,
7. autonomous AI business-state mutation.

## Notes

Immediately after the promote action, the public fetch path still showed stale route behavior while alias propagation caught up. Once production deployment `dpl_5uCHB9KLyhhV4thQJ31BAuAKzT21` became the current alias target, direct HTTP checks on both public aliases returned `200` with the expected customer-billing placeholder marker and the production hosted smoke passed.

## Next Truth

The hosted-publication blocker for the customer-billing placeholder route is closed.

Any next PM move should target a different explicitly admitted branch rather than another customer-billing placeholder publication proof tranche.