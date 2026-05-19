# PM Lane 393 - Import Intake Output Selector Placeholder Route Coherence And Hosted Smoke Readiness Closeout Handoff

## Outcome

Executed PM Lane 393 as a bounded local coherence refresh for the read-only import-intake Output Selector.

Selected outcome: `PM_IMPORT_INTAKE_OUTPUT_SELECTOR_LOCALLY_COHERENT_WITH_PUBLISHED_PLACEHOLDER_ROUTES_AND_HOSTED_SMOKE_READY`

The six Admission Draft items in `/pm-review/import-intake` now point directly to the published placeholder routes instead of stale local `#field-prep` anchors.

## Scope

- Refreshed the Output Selector links for Field Authorization Assignment, Schedule Status Controls, Durable Field Record, Production Tracking, Customer Reporting, and Financial Handoff drafts.
- Preserved the existing read-only import-intake workbench behavior and zero-mutation boundary.
- Updated the focused import-intake smoke to assert the refreshed placeholder-route hrefs.

## Validation

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
1 passed
```

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit
```

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url http://127.0.0.1:3030 --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=23 base_url=http://127.0.0.1:3030/
```

## Boundary

- No new route.
- No route-count increase.
- No import-intake export change.
- No backend mutation surface change.
- No approval, import, assignment, schedule/status, field, production, customer, or finance authority widening.
- No hosted publication claimed.

## Next Bounded Move

The next bounded move is a hosted-publication tranche that proves production now serves the refreshed import-intake Output Selector links to the six already published placeholder routes.
