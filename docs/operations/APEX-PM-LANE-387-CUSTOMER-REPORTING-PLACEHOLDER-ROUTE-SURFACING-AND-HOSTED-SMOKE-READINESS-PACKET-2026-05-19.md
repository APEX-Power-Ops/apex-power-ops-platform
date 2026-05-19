# APEX PM Lane 387 - Customer Reporting Placeholder Route Surfacing And Hosted Smoke Readiness Packet

Date: 2026-05-19

Status: Implemented locally and validated as route surfacing plus hosted-smoke readiness only.

Decision label:

`PM_CUSTOMER_REPORTING_PLACEHOLDER_ROUTE_SURFACING_AND_HOSTED_SMOKE_READINESS`

## Purpose

PM Lane 387 opens the next explicit downstream reporting placeholder branch after the production-tracking placeholder publication work.

This lane gives operators a dedicated read-only PM route for customer reporting planning and adds the route to the generic operations-web hosted HTML smoke path so future promoted-host validation will catch regressions.

This lane does not publish the route. It only creates the local route, the bounded local navigation surfaces, and the hosted-smoke readiness check.

## Selected Outcome

Selected outcome:

`PM_CUSTOMER_REPORTING_PLACEHOLDER_ROUTE_LOCAL_AND_HOSTED_SMOKE_READY`

Meaning:

1. `apps/operations-web` now exposes `/pm-review/customer-reporting-placeholder`,
2. the route keeps customer reporting as a no-live planning branch only,
3. the governed PM shell and project overview route map now expose the branch directly,
4. the promoted-host smoke runner will fail if a future hosted deployment omits the route or its marker text,
5. hosted publication is not claimed in this tranche.

## Scope

This lane adds:

1. one read-only customer-reporting placeholder route,
2. PM shell and project-overview links to that route,
3. one production-tracking-placeholder cross-link to that route,
4. one route-scoped Playwright smoke,
5. one hosted-route smoke marker for `/pm-review/customer-reporting-placeholder`,
6. no backend seam,
7. no mutation route,
8. no customer reporting authority widening,
9. no financial handoff widening,
10. no finance output widening,
11. no hosted promotion.

## Route Proof

The new local route is:

1. `/pm-review/customer-reporting-placeholder`

Its public marker text for later hosted validation is:

1. `Customer reporting stays blocked as a placeholder downstream branch.`

The route explicitly separates:

1. production tracking planning,
2. customer reporting planning,
3. later financial handoff authority,
4. later finance and customer billing authority.

## Validation

Focused local validation passed:

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-customer-reporting-placeholder.smoke.spec.ts
1 passed
```

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit
```

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url http://127.0.0.1:3030 --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=22 base_url=http://127.0.0.1:3030/
SMOKE_OK /pm-review/customer-reporting-placeholder status=200 marker="Customer reporting stays blocked as a placeholder downstream branch."
```

## Publication Boundary

Hosted publication is not yet current in this lane. No truthful public claim is made here for the new customer-reporting placeholder route until a new deployment exists and is verified.

## Next Truth

The next truthful step after Lane 387 is a separate hosted-publication tranche for the customer-reporting placeholder route after a new deployable operations-web build exists. That later tranche must prove:

1. the deployed route returns HTML publicly,
2. `smoke-hosted-routes.mjs` passes against `https://operations.apexpowerops.com` with the customer-reporting placeholder marker included,
3. the public route renders the blocked customer-reporting placeholder heading and guardrail posture.