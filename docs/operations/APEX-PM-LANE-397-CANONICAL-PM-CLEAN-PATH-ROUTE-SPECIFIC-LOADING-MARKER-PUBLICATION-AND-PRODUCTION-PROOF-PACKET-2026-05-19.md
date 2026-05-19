# APEX PM Lane 397 - Canonical PM Clean Path Route-Specific Loading Marker Publication And Production Proof Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_CANONICAL_CLEAN_PATH_ROUTE_SPECIFIC_LOADING_MARKER_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 397 closes the remaining truthful hosted-proof gap left after PM Lane 396.

PM Lane 396 extended the canonical PM clean-path hosted smoke to `/pm-review`, `/pm-review/approval`, `/pm-review/schedule`, `/pm-review/tracer`, and `/pm-review/variance`, but the fetch-based proof still depended on one shared raw-HTML loading marker: `Loading PM drivers route.` for all five paths.

This lane makes the four clean-path subroutes route-discriminating in server-returned raw HTML by adding segment-level loading shells for:

1. `/pm-review/approval`
2. `/pm-review/schedule`
3. `/pm-review/tracer`
4. `/pm-review/variance`

It then publishes that change to production and re-proves the canonical PM clean-path hosted smoke contract on both public aliases.

## Root Cause

The shared loading shell at `apps/operations-web/app/pm-review/loading.tsx` controlled the raw HTML returned for the PM review segment during fetch-based hosted smoke. Without segment-level `loading.tsx` files below the clean-path subroutes, approval, schedule, tracer, and variance all surfaced the same shared marker even though the routes themselves were distinct.

## Change Surface

Added files:

1. `apps/operations-web/app/pm-review/approval/loading.tsx`
2. `apps/operations-web/app/pm-review/schedule/loading.tsx`
3. `apps/operations-web/app/pm-review/tracer/loading.tsx`
4. `apps/operations-web/app/pm-review/variance/loading.tsx`

Updated file:

1. `apps/operations-web/scripts/smoke-hosted-routes.mjs`

Route markers after this lane:

```text
{ path: '/pm-review', marker: 'Loading PM drivers route.' }
{ path: '/pm-review/approval', marker: 'Loading PM approval route.' }
{ path: '/pm-review/schedule', marker: 'Loading PM schedule route.' }
{ path: '/pm-review/tracer', marker: 'Loading PM tracer route.' }
{ path: '/pm-review/variance', marker: 'Loading PM variance route.' }
```

## Local Validation

Focused repo validation passed before publication:

```text
get_errors: no errors in touched operations-web files
corepack pnpm --dir apps/operations-web typecheck
PASS
corepack pnpm --dir . --filter @apex/operations-web build
PASS
```

Code publication commit:

```text
4108f733a58fa5dfcd2f553361f8c253dca1f851
Add route-specific PM loading markers
```

## Hosted Publication

Verified ready preview for commit `4108f73`:

```text
Preview deployment slug: 3XLUA8YDmzeYkuhx6oYNUgv5EPoF
```

Promoted production deployment:

```text
Previous production slug: D7YGSfBoAhRBkTVqyj6jXU7E38Xf
New production slug: HHGsNVNUgfDBu8afiW4mfNi6aY9d
Production deployment id: dpl_HHGsNVNUgfDBu8afiW4mfNi6aY9d
Status: Ready
Environment: Production
```

The preview alias was authenticated and returned `401 Unauthorized` for direct public probing, so public proof for this lane is taken only from the production aliases.

## Public Alias Proof

Verified route-specific raw-HTML markers on both public aliases:

```text
PUBLIC_OK https://apex-operations-web.vercel.app/pm-review/approval marker=Loading PM approval route.
PUBLIC_OK https://apex-operations-web.vercel.app/pm-review/schedule marker=Loading PM schedule route.
PUBLIC_OK https://apex-operations-web.vercel.app/pm-review/tracer marker=Loading PM tracer route.
PUBLIC_OK https://apex-operations-web.vercel.app/pm-review/variance marker=Loading PM variance route.
PUBLIC_OK https://operations.apexpowerops.com/pm-review/approval marker=Loading PM approval route.
PUBLIC_OK https://operations.apexpowerops.com/pm-review/schedule marker=Loading PM schedule route.
PUBLIC_OK https://operations.apexpowerops.com/pm-review/tracer marker=Loading PM tracer route.
PUBLIC_OK https://operations.apexpowerops.com/pm-review/variance marker=Loading PM variance route.
```

The root PM clean path remains truthfully shared at:

```text
/pm-review -> Loading PM drivers route.
```

## Production Smoke Proof

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_OK /pm-review status=200 marker="Loading PM drivers route."
SMOKE_OK /pm-review/approval status=200 marker="Loading PM approval route."
SMOKE_OK /pm-review/schedule status=200 marker="Loading PM schedule route."
SMOKE_OK /pm-review/tracer status=200 marker="Loading PM tracer route."
SMOKE_OK /pm-review/variance status=200 marker="Loading PM variance route."
SMOKE_SUMMARY failed=0 passed=29 base_url=https://operations.apexpowerops.com/
```

## Boundary

This lane does not:

1. change PM business-state authority,
2. add or widen approval, import, assignment, schedule/status, field, production, customer, or finance mutation authority,
3. change mutation-seam behavior,
4. add backend mutation,
5. admit autonomous AI business-state mutation.

## Result

The canonical PM clean-path hosted smoke is now route-specific where raw HTML can truthfully discriminate it. Approval, schedule, tracer, and variance each return their own server-visible loading marker on both public aliases, and the full production hosted smoke remains green at 29 of 29 routes.
