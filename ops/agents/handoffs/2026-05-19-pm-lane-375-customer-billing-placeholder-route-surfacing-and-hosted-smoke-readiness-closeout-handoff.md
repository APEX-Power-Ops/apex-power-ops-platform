# PM Lane 375 - Customer Billing Placeholder Route Surfacing And Hosted Smoke Readiness Closeout Handoff

## Outcome

Executed PM Lane 375 as a bounded local route-surfacing and hosted-smoke-readiness slice for the customer-billing placeholder branch.

Selected outcome: `PM_CUSTOMER_BILLING_PLACEHOLDER_ROUTE_LOCAL_AND_HOSTED_SMOKE_READY`

The PM shell now has a dedicated read-only `/pm-review/customer-billing-placeholder` route that surfaces the blocked customer billing delivery branch without widening downstream authority, and the generic operations-web hosted HTML smoke path now includes that route.

## Scope

- Added `/pm-review/customer-billing-placeholder` as a read-only route in `apps/operations-web`.
- Updated the governed PM shell to link to the new route from `/pm-review`.
- Updated `/pm-review/project-overview` step 06 to open the customer-billing placeholder branch directly.
- Added a finance-placeholder cross-link to the new downstream branch.
- Added route-scoped Playwright smoke coverage.
- Updated `apps/operations-web/scripts/smoke-hosted-routes.mjs` to include `/pm-review/customer-billing-placeholder`.

## Validation

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-customer-billing-placeholder.smoke.spec.ts
1 passed
```

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit
```

```text
corepack pnpm --dir apps/operations-web smoke:hosted -- --base-url http://127.0.0.1:3030 --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=16 base_url=http://127.0.0.1:3030/
SMOKE_OK /pm-review/customer-billing-placeholder status=200 marker="Customer billing delivery stays blocked as a placeholder downstream branch."
```

## Boundary

- No hosted publication claimed.
- No backend seam.
- No mutation route.
- No finance write authority widening.
- No customer-billing-delivery authority widening.
- No source writeback widening.
- No workbook macro execution.

## Current Blocker

Hosted publication is not yet current. The new customer-billing placeholder route cannot be truthfully marked hosted until a new operations-web deployment exists and is verified on production.

## Next Bounded Move

The next bounded move is a hosted-publication tranche after a new deployable build exists for `apex-operations-web`, followed by public-route and hosted-smoke verification for `/pm-review/customer-billing-placeholder`.