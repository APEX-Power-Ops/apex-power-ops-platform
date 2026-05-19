# APEX PM Lane 383 - Durable Field Record Placeholder Route Surfacing And Hosted Smoke Readiness Packet

Date: 2026-05-19

Status: Implemented locally and validated as route surfacing plus hosted-smoke readiness only.

Decision label:

`PM_DURABLE_FIELD_RECORD_PLACEHOLDER_ROUTE_SURFACING_AND_HOSTED_SMOKE_READINESS`

## Purpose

PM Lane 383 opens the next explicit field-evidence placeholder branch after the schedule-status placeholder publication work.

This lane gives operators a dedicated read-only PM route for durable field record planning and adds the route to the generic operations-web hosted HTML smoke path so future promoted-host validation will catch regressions.

This lane does not publish the route. It only creates the local route, the bounded local navigation surfaces, and the hosted-smoke readiness check.

## Selected Outcome

Selected outcome:

`PM_DURABLE_FIELD_RECORD_PLACEHOLDER_ROUTE_LOCAL_AND_HOSTED_SMOKE_READY`

Meaning:

1. `apps/operations-web` now exposes `/pm-review/durable-field-record-placeholder`,
2. the route keeps durable field record as a no-live planning branch only,
3. the governed PM shell and project overview route map now expose the branch directly,
4. the promoted-host smoke runner will fail if a future hosted deployment omits the route or its marker text,
5. hosted publication is not claimed in this tranche.

## Scope

This lane adds:

1. one read-only durable-field-record placeholder route,
2. PM shell and project-overview links to that route,
3. one schedule-status-placeholder cross-link to that route,
4. one route-scoped Playwright smoke,
5. one hosted-route smoke marker for `/pm-review/durable-field-record-placeholder`,
6. no backend seam,
7. no mutation route,
8. no durable field record authority widening,
9. no evidence upload or daily record commit,
10. no production tracking widening,
11. no hosted promotion.

## Route Proof

The new local route is:

1. `/pm-review/durable-field-record-placeholder`

Its public marker text for later hosted validation is:

1. `Durable field record stays blocked as a placeholder evidence branch.`

The route explicitly separates:

1. schedule and status planning,
2. durable field record planning,
3. later production tracking authority,
4. downstream reporting and finance authority.

## Validation

Focused local validation passed:

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-durable-field-record-placeholder.smoke.spec.ts
1 passed
```

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit
```

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url http://127.0.0.1:3030 --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=20 base_url=http://127.0.0.1:3030/
SMOKE_OK /pm-review/durable-field-record-placeholder status=200 marker="Durable field record stays blocked as a placeholder evidence branch."
```

## Publication Boundary

Hosted publication is not yet current in this lane. No truthful public claim is made here for the new durable-field-record placeholder route until a new deployment exists and is verified.

## Next Truth

The next truthful step after Lane 383 is a separate hosted-publication tranche for the durable-field-record placeholder route after a new deployable operations-web build exists. That later tranche must prove:

1. the deployed route returns HTML publicly,
2. `smoke-hosted-routes.mjs` passes against `https://operations.apexpowerops.com` with the durable-field-record placeholder marker included,
3. the public route renders the blocked durable-field-record placeholder heading and guardrail posture.