# APEX PM Lane 393 - Import Intake Output Selector Placeholder Route Coherence And Hosted Smoke Readiness Packet

Date: 2026-05-19

Status: Implemented locally and validated as import-intake route-coherence refresh plus hosted-smoke readiness only.

Decision label:

`PM_IMPORT_INTAKE_OUTPUT_SELECTOR_PLACEHOLDER_ROUTE_COHERENCE_AND_HOSTED_SMOKE_READINESS`

## Purpose

PM Lane 393 refreshes the read-only Project Miner import-intake workbench so the Admission Draft items in the Output Selector now point to the already published placeholder review routes instead of stale local `#field-prep` anchors.

The goal is to make the import-intake workbench truthful and navigable against the current PM route map: Jason can move directly from the workbench to the published placeholder branches for field authorization, schedule and status, durable field record, production tracking, customer reporting, and financial handoff.

This lane does not add a new route, export, or mutation surface. It only refreshes existing read-only import-intake route links and validates that the hosted smoke set remains ready.

## Selected Outcome

Selected outcome:

`PM_IMPORT_INTAKE_OUTPUT_SELECTOR_LOCALLY_COHERENT_WITH_PUBLISHED_PLACEHOLDER_ROUTES_AND_HOSTED_SMOKE_READY`

Meaning:

1. the six Admission Draft items in the import-intake Output Selector now point to their published placeholder routes,
2. the import-intake workbench remains read-only and link-only for those selectors,
3. the focused import-intake smoke now proves the exact placeholder-route hrefs,
4. the existing promoted-host smoke runner stays green after the coherence refresh,
5. hosted publication is not claimed in this tranche.

## Scope

This lane changes:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

This lane does not change:

1. route count,
2. hosted-route smoke list,
3. import-intake export handlers,
4. backend mutation surfaces,
5. approval, import, assignment, schedule/status, field, production, customer, or finance authority.

## Validation

Focused local validation passed:

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

## Publication Boundary

Hosted publication is not yet current in this lane. No truthful public claim is made here for the refreshed import-intake placeholder-route links until a new deployment exists and the public import-intake page is re-verified.

## Next Truth

The next truthful step after Lane 393 is a separate hosted-publication tranche proving that production now serves the refreshed import-intake Output Selector links to the six published placeholder routes while the production hosted smoke remains green.
