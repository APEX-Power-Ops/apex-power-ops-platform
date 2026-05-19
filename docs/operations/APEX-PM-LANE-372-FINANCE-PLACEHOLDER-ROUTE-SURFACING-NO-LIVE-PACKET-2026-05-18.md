# APEX PM Lane 372 - Finance Placeholder Route Surfacing No-Live Packet

Date: 2026-05-18

Status: Implemented locally and validated as a read-only PM route surfacing the existing finance-placeholder design branch.

Decision label:

`PM_FINANCE_PLACEHOLDER_ROUTE_SURFACING_NO_LIVE`

## Purpose

PM Lane 372 turns the existing finance-placeholder documentation branch into a governed local PM route so operators can open one dedicated surface for downstream finance-placeholder posture instead of routing through a generic admission page.

This lane does not widen finance authority. It surfaces the existing placeholder taxonomy, guardrails, recommended next placeholder work, and the still-separate customer-billing-delivery and source-writeback boundaries.

## Selected Outcome

Selected outcome:

`PM_FINANCE_PLACEHOLDER_ROUTE_LOCAL_CURRENT`

Meaning:

1. `/pm-review/finance-placeholder` now exists inside `apps/operations-web` as a read-only downstream-planning surface,
2. `/pm-review/project-overview` step 06 now links directly to the finance-placeholder branch,
3. the PM shell navigation now exposes the finance-placeholder route alongside the other promoted PM surfaces,
4. the route remains local-only in this tranche and does not claim hosted publication,
5. billing export, payroll export, invoice/accounting persistence, customer billing delivery, source writeback, and workbook macro behavior remain blocked.

## Scope

Product changes in this lane:

1. add a dedicated read-only route at `/pm-review/finance-placeholder`,
2. surface the Lane 356 placeholder taxonomy inside the route,
3. surface explicit placeholder guardrails and non-finance boundary separation inside the route,
4. retarget PM overview stage 06 to the new finance-placeholder route,
5. add shell-level navigation access to the new route,
6. add one focused Playwright smoke for the new route.

## Guardrails Preserved

This lane adds:

1. no backend seam,
2. no mutation route,
3. no live finance write,
4. no customer billing delivery widening,
5. no source workbook or PDF writeback,
6. no workbook macro execution,
7. no hosted publication,
8. no autonomous AI business-state mutation.

## Validation

Focused validation passed:

```text
corepack pnpm exec playwright test tests/browser-shell.pm-finance-placeholder.smoke.spec.ts
1 passed
```

The smoke proves the route renders the placeholder taxonomy, guardrails, recommended next placeholder work, and non-finance boundary reminders while sending no mutation request.

## Next Truth

The next truthful move after Lane 372 is one of the following, depending on operator need:

1. keep the finance-placeholder branch local and continue placeholder-only design refinement,
2. open a separate hosted-publication lane if this route must be available on the public PM shell,
3. open a later separate admitted packet if real finance output, customer billing delivery, or source writeback is intentionally selected.