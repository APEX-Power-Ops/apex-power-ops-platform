# APEX PM Lane 379 - Field Authorization Placeholder Route Surfacing And Hosted Smoke Readiness Packet

Date: 2026-05-19

Status: Implemented locally and validated as route surfacing plus hosted-smoke readiness only.

Decision label:

`PM_FIELD_AUTHORIZATION_PLACEHOLDER_ROUTE_SURFACING_AND_HOSTED_SMOKE_READINESS`

## Purpose

PM Lane 379 opens the next explicit field-authority placeholder branch after the source-writeback placeholder publication work.

This lane gives operators a dedicated read-only PM route for field authorization and assignment planning and adds the route to the generic operations-web hosted HTML smoke path so future promoted-host validation will catch regressions.

This lane does not publish the route. It only creates the local route, the bounded local navigation surfaces, and the hosted-smoke readiness check.

## Selected Outcome

Selected outcome:

`PM_FIELD_AUTHORIZATION_PLACEHOLDER_ROUTE_LOCAL_AND_HOSTED_SMOKE_READY`

Meaning:

1. `apps/operations-web` now exposes `/pm-review/field-authorization-placeholder`,
2. the route keeps field authorization and assignment as a no-live planning branch only,
3. the governed PM shell and project overview route map now expose the branch directly,
4. the promoted-host smoke runner will fail if a future hosted deployment omits the route or its marker text,
5. hosted publication is not claimed in this tranche.

## Scope

This lane adds:

1. one read-only field-authority placeholder route,
2. PM shell and project-overview links to that route,
3. one route-scoped Playwright smoke,
4. one hosted-route smoke marker for `/pm-review/field-authorization-placeholder`,
5. no backend seam,
6. no mutation route,
7. no field authorization or assignment authority widening,
8. no schedule or status write widening,
9. no durable field record widening,
10. no production tracking widening,
11. no hosted promotion.

## Route Proof

The new local route is:

1. `/pm-review/field-authorization-placeholder`

Its public marker text for later hosted validation is:

1. `Field authorization and assignment stay blocked as a placeholder branch.`

The route explicitly separates:

1. intake and field-prep planning,
2. field authorization and assignment planning,
3. later schedule and status controls,
4. later durable field record and production tracking authority.

## Validation

Focused local validation passed:

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-field-authorization-placeholder.smoke.spec.ts
1 passed
```

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit
```

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url http://127.0.0.1:3030 --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=18 base_url=http://127.0.0.1:3030/
SMOKE_OK /pm-review/field-authorization-placeholder status=200 marker="Field authorization and assignment stay blocked as a placeholder branch."
```

## Publication Boundary

Hosted publication is not yet current in this lane. No truthful public claim is made here for the new field-authorization placeholder route until a new deployment exists and is verified.

## Next Truth

The next truthful step after Lane 379 is a separate hosted-publication tranche for the field-authorization placeholder route after a new deployable operations-web build exists. That later tranche must prove:

1. the deployed route returns HTML publicly,
2. `smoke-hosted-routes.mjs` passes against `https://operations.apexpowerops.com` with the field-authorization placeholder marker included,
3. the public route renders the blocked field-authorization placeholder heading and guardrail posture.