# PM Lane 383 - Durable Field Record Placeholder Route Surfacing And Hosted Smoke Readiness Closeout Handoff

## Outcome

Executed PM Lane 383 as a bounded local route-surfacing and hosted-smoke-readiness slice for the durable-field-record placeholder branch.

Selected outcome: `PM_DURABLE_FIELD_RECORD_PLACEHOLDER_ROUTE_LOCAL_AND_HOSTED_SMOKE_READY`

The PM shell now has a dedicated read-only `/pm-review/durable-field-record-placeholder` route that surfaces the blocked durable field record branch without widening field evidence authority, and the generic operations-web hosted HTML smoke path now includes that route.

## Scope

- Added `/pm-review/durable-field-record-placeholder` as a read-only route in `apps/operations-web`.
- Updated the governed PM shell to link to the new route from `/pm-review`.
- Updated `/pm-review/project-overview` step 04 to open the durable-field-record placeholder branch directly.
- Added a schedule-status-placeholder cross-link to the new branch.
- Added route-scoped Playwright smoke coverage.
- Updated `apps/operations-web/scripts/smoke-hosted-routes.mjs` to include `/pm-review/durable-field-record-placeholder`.

## Validation

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

## Boundary

- No hosted publication claimed.
- No backend seam.
- No mutation route.
- No durable field record authority widening.
- No evidence upload or daily record commit.
- No production tracking widening.
- No live field evidence control.

## Current Blocker

Hosted publication is not yet current. The new durable-field-record placeholder route cannot be truthfully marked hosted until a new operations-web deployment exists and is verified on production.

## Next Bounded Move

The next bounded move is a hosted-publication tranche after a new deployable build exists for `apex-operations-web`, followed by public-route and hosted-smoke verification for `/pm-review/durable-field-record-placeholder`.