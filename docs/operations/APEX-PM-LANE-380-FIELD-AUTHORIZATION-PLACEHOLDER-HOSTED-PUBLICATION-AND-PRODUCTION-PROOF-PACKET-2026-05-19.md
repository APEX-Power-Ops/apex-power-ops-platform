# APEX PM Lane 380 - Field Authorization Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Executed, hosted, and production-verified.

Decision label:

`PM_FIELD_AUTHORIZATION_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 380 closes the hosted-publication tranche for the field-authorization placeholder route created in Lane 379.

This lane proves the field-authorization placeholder route is no longer only local truth. It is now publicly available on the production operations-web hosts and covered by the hosted-route smoke suite.

## Selected Outcome

Selected outcome:

`PM_FIELD_AUTHORIZATION_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

Meaning:

1. clean-main commit `fd3ff632` is deployed,
2. `/pm-review/field-authorization-placeholder` is publicly reachable on the production aliases,
3. the public route renders the expected placeholder marker text,
4. the hosted smoke suite passes with the new route included.

## Deployment Proof

Preview deployment created from the clean-main commit:

1. deployment id: `dpl_EggXDcGXgbGhJP78xARaX4kd5z5B`
2. preview URL: `https://apex-operations-12ltxs5zl-jasonlswenson-sys-projects.vercel.app`
3. status before promotion: `Ready`

Production deployment created by promotion:

1. deployment id: `dpl_4jnW9fvwZgPHgRq6GDZF6c1iK1MN`
2. production URL: `https://apex-operations-9vb1c4x17-jasonlswenson-sys-projects.vercel.app`
3. aliases attached:
   - `https://apex-operations-web.vercel.app`
   - `https://operations.apexpowerops.com`

## Public Route Proof

Direct HTTP verification passed on both public aliases for:

1. `/pm-review/field-authorization-placeholder`

Verified marker text:

1. `Field authorization and assignment stay blocked as a placeholder branch.`

Verification result:

```text
Url           : https://apex-operations-web.vercel.app/pm-review/field-authorization-placeholder
StatusCode    : 200
MarkerPresent : True

Url           : https://operations.apexpowerops.com/pm-review/field-authorization-placeholder
StatusCode    : 200
MarkerPresent : True
```

## Hosted Smoke Proof

Production hosted-route smoke passed:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=18 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/field-authorization-placeholder status=200 marker="Field authorization and assignment stay blocked as a placeholder branch."
```

## Boundary

This lane widens hosted availability only for the existing read-only field-authorization placeholder planning slice.

It does not admit:

1. field authorization,
2. lead or crew assignment,
3. schedule or status mutation,
4. durable field record writes,
5. production tracking writes,
6. backend seam mutation,
7. workbook macro execution,
8. autonomous AI business-state mutation.