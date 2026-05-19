# APEX PM Lane 395 - PM Workfront Hosted Smoke Coverage Extension And Production Proof Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_WORKFRONT_HOSTED_SMOKE_COVERAGE_EXTENSION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 395 closes a hosted-proof gap in the repo-owned production smoke runner. The PM workfront route was already live on production, but `apps/operations-web/scripts/smoke-hosted-routes.mjs` did not exercise `/pm-review/workfront`.

This lane extends hosted smoke coverage to include the live PM workfront route and records production proof against the existing public alias without changing route behavior, deployment state, or mutation authority.

## Change Surface

Updated file:

1. `apps/operations-web/scripts/smoke-hosted-routes.mjs`

Added hosted route check:

```text
{ path: '/pm-review/workfront', marker: 'PM workfront now has a governed read model.' }
```

## Production Proof

Direct route proof:

```text
STATUS=200
MARKER_OK PM workfront now has a governed read model.
```

Hosted smoke proof:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_OK /pm-review/workfront status=200 marker="PM workfront now has a governed read model."
SMOKE_SUMMARY failed=0 passed=24 base_url=https://operations.apexpowerops.com/
```

## Boundary

This lane does not:

1. deploy a new operations-web build,
2. change Vercel routing,
3. change the PM workfront page,
4. change mutation-seam behavior,
5. widen approval, import, assignment, schedule/status, field, production, customer, or finance authority,
6. add backend mutation,
7. admit autonomous AI business-state mutation.

## Result

The canonical hosted smoke now truthfully covers the live PM workfront route, and production proof is recorded with the suite green at 24 routes.
