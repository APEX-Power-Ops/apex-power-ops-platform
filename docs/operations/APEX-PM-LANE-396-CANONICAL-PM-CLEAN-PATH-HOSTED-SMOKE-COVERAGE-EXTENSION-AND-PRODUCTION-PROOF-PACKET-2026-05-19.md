# APEX PM Lane 396 - Canonical PM Clean Path Hosted Smoke Coverage Extension And Production Proof Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_CANONICAL_CLEAN_PATH_HOSTED_SMOKE_COVERAGE_EXTENSION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 396 closes the next hosted-proof gap after PM Lane 395. The canonical clean-path PM review routes already existed in the Next.js app and were returning production `200` responses, but the repo-owned hosted smoke only exercised the legacy static compare hosts for drivers, approval, schedule, tracer, and variance.

This lane extends the hosted smoke to include the canonical clean paths:

1. `/pm-review`
2. `/pm-review/approval`
3. `/pm-review/schedule`
4. `/pm-review/tracer`
5. `/pm-review/variance`

## Observed Production Contract

The canonical clean-path PM routes currently bail out to a shared client-side loading shell in raw HTML, so fetch-based hosted smoke can truthfully prove route presence but not route-specific hydrated body content.

Verified discriminating proof:

```text
CANONICAL_OK https://operations.apexpowerops.com/pm-review marker=Loading PM drivers route.
CANONICAL_OK https://operations.apexpowerops.com/pm-review/approval marker=Loading PM drivers route.
CANONICAL_OK https://operations.apexpowerops.com/pm-review/schedule marker=Loading PM drivers route.
CANONICAL_OK https://operations.apexpowerops.com/pm-review/tracer marker=Loading PM drivers route.
CANONICAL_OK https://operations.apexpowerops.com/pm-review/variance marker=Loading PM drivers route.
```

Non-route discrimination proof:

```text
STATUS=404
MISSING_LOADING_MARKER
```

for `https://operations.apexpowerops.com/pm-review/not-a-real-route`.

## Change Surface

Updated file:

1. `apps/operations-web/scripts/smoke-hosted-routes.mjs`

Added canonical route checks:

```text
{ path: '/pm-review', marker: 'Loading PM drivers route.' }
{ path: '/pm-review/approval', marker: 'Loading PM drivers route.' }
{ path: '/pm-review/schedule', marker: 'Loading PM drivers route.' }
{ path: '/pm-review/tracer', marker: 'Loading PM drivers route.' }
{ path: '/pm-review/variance', marker: 'Loading PM drivers route.' }
```

## Production Smoke Proof

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_OK /pm-review status=200 marker="Loading PM drivers route."
SMOKE_OK /pm-review/approval status=200 marker="Loading PM drivers route."
SMOKE_OK /pm-review/schedule status=200 marker="Loading PM drivers route."
SMOKE_OK /pm-review/tracer status=200 marker="Loading PM drivers route."
SMOKE_OK /pm-review/variance status=200 marker="Loading PM drivers route."
SMOKE_SUMMARY failed=0 passed=29 base_url=https://operations.apexpowerops.com/
```

## Boundary

This lane does not:

1. deploy a new operations-web build,
2. change any PM route implementation,
3. change Vercel routing,
4. change mutation-seam behavior,
5. widen approval, import, assignment, schedule/status, field, production, customer, or finance authority,
6. add backend mutation,
7. admit autonomous AI business-state mutation.

## Result

The canonical hosted smoke now covers both the Next.js clean-path PM review routes and the legacy static compare hosts, with production proof green at 29 routes.
