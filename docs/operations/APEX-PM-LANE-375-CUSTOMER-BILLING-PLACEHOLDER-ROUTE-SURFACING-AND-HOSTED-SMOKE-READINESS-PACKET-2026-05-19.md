# APEX PM Lane 375 - Customer Billing Placeholder Route Surfacing And Hosted Smoke Readiness Packet

Date: 2026-05-19

Status: Implemented locally and validated as route surfacing plus hosted-smoke readiness only.

Decision label:

`PM_CUSTOMER_BILLING_PLACEHOLDER_ROUTE_SURFACING_AND_HOSTED_SMOKE_READINESS`

## Purpose

PM Lane 375 opens the next explicit downstream placeholder branch after the finance-placeholder publication work.

This lane gives operators a dedicated read-only PM route for customer billing delivery planning and adds the route to the generic operations-web hosted HTML smoke path so future promoted-host validation will catch regressions.

This lane does not publish the route. It only creates the local route, the bounded local navigation surfaces, and the hosted-smoke readiness check.

## Selected Outcome

Selected outcome:

`PM_CUSTOMER_BILLING_PLACEHOLDER_ROUTE_LOCAL_AND_HOSTED_SMOKE_READY`

Meaning:

1. `apps/operations-web` now exposes `/pm-review/customer-billing-placeholder`,
2. the route keeps customer billing delivery as a no-live planning branch only,
3. the governed PM shell and project overview route map now expose the branch directly,
4. the promoted-host smoke runner will fail if a future hosted deployment omits the route or its marker text,
5. hosted publication is not claimed in this tranche.

## Scope

This lane adds:

1. one read-only downstream-planning route for customer billing delivery,
2. PM shell and project-overview links to that route,
3. a finance-placeholder cross-link to the new route,
4. one route-scoped Playwright smoke,
5. one hosted-route smoke marker for `/pm-review/customer-billing-placeholder`,
6. no backend seam,
7. no mutation route,
8. no customer billing delivery authority widening,
9. no finance write widening,
10. no source writeback widening,
11. no hosted promotion.

## Route Proof

The new local route is:

1. `/pm-review/customer-billing-placeholder`

Its public marker text for later hosted validation is:

1. `Customer billing delivery stays blocked as a placeholder downstream branch.`

The route explicitly separates:

1. customer-facing billing release planning,
2. internal finance handoff planning,
3. admitted customer-delivery execution proof,
4. still-blocked source writeback.

## Validation

Focused local validation passed:

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

## Publication Boundary

Hosted publication is not yet current in this lane. No truthful public claim is made here for the new customer-billing placeholder route until a new deployment exists and is verified.

## Next Truth

The next truthful step after Lane 375 is a separate hosted-publication tranche for the customer-billing placeholder route after a new deployable operations-web build exists. That later tranche must prove:

1. the deployed route returns HTML publicly,
2. `smoke-hosted-routes.mjs` passes against `https://operations.apexpowerops.com` with the customer-billing placeholder marker included,
3. the public route renders the blocked customer-billing placeholder heading and guardrail posture.