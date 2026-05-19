# APEX PM Lane 391 - Downstream Placeholder Coherence Refresh And Hosted Smoke Readiness Packet

Date: 2026-05-19

Status: Implemented locally and validated as route-coherence refresh plus hosted-smoke readiness only.

Decision label:

`PM_DOWNSTREAM_PLACEHOLDER_COHERENCE_REFRESH_AND_HOSTED_SMOKE_READINESS`

## Purpose

PM Lane 391 refreshes the already published downstream placeholder routes after the dedicated financial-handoff placeholder branch was introduced.

The goal is to make the downstream cluster truthful and internally consistent: finance output should no longer present financial handoff as part of finance taxonomy, and the finance, customer-billing, and source-writeback routes should all expose the separate financial-handoff branch directly.

This lane does not add a new route. It only refreshes existing read-only downstream placeholder content and validates that the hosted smoke set remains ready.

## Selected Outcome

Selected outcome:

`PM_DOWNSTREAM_PLACEHOLDER_ROUTES_LOCALLY_COHERENT_AND_HOSTED_SMOKE_READY`

Meaning:

1. finance placeholder copy now treats customer reporting and financial handoff as separate upstream branches,
2. finance placeholder taxonomy no longer lists `FINANCE_HANDOFF_DRAFT` as a finance output class,
3. finance, customer-billing, and source-writeback placeholder routes now link directly to `/pm-review/financial-handoff-placeholder`,
4. the existing promoted-host smoke runner stays green after the coherence refresh,
5. hosted publication is not claimed in this tranche.

## Scope

This lane changes:

1. `apps/operations-web/app/pm-review/finance-placeholder/page.tsx`
2. `apps/operations-web/app/pm-review/customer-billing-placeholder/page.tsx`
3. `apps/operations-web/app/pm-review/source-writeback-placeholder/page.tsx`
4. the three focused route-smoke specs covering those pages

This lane does not change:

1. route count,
2. hosted-route smoke list,
3. backend mutation surfaces,
4. finance authority,
5. customer billing authority,
6. source writeback authority.

## Validation

Focused local validation passed:

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-finance-placeholder.smoke.spec.ts tests/browser-shell.pm-customer-billing-placeholder.smoke.spec.ts tests/browser-shell.pm-source-writeback-placeholder.smoke.spec.ts
3 passed
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

Hosted publication is not yet current in this lane. No truthful public claim is made here for the refreshed downstream coherence until a new deployment exists and the public routes are re-verified.

## Next Truth

The next truthful step after Lane 391 is a separate hosted-publication tranche proving that production now serves the refreshed downstream placeholder coherence, including direct financial-handoff links on the finance, customer-billing, and source-writeback routes.