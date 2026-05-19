# APEX PM Lane 386 - Production Tracking Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Executed, hosted, and production-verified.

Decision label:

`PM_PRODUCTION_TRACKING_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 386 closes the hosted-publication tranche for the production-tracking placeholder route created in Lane 385.

This lane proves the production-tracking placeholder route is no longer only local truth. It is now publicly available on the production operations-web hosts and covered by the hosted-route smoke suite.

## Selected Outcome

Selected outcome:

`PM_PRODUCTION_TRACKING_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

Meaning:

1. clean-main commit `d7dafda2` is deployed,
2. `/pm-review/production-tracking-placeholder` is publicly reachable on the production aliases,
3. the public route renders the expected placeholder marker text,
4. the hosted smoke suite passes with the new route included.

## Deployment Proof

Preview deployment created from the clean-main commit:

1. deployment id: `dpl_4pKyGLkhmwKf7QSHnEBEXBvWtMN6`
2. preview URL: `https://apex-operations-yre8jrqmg-jasonlswenson-sys-projects.vercel.app`
3. status before promotion: `Ready`

Production deployment created by promotion:

1. deployment id: `dpl_De7b4xHYwbGnisPFMBMXUXWaxENh`
2. production URL: `https://apex-operations-5sufvd3df-jasonlswenson-sys-projects.vercel.app`
3. aliases attached:
   - `https://apex-operations-web.vercel.app`
   - `https://operations.apexpowerops.com`

## Public Route Proof

Direct HTTP verification passed on both public aliases for:

1. `/pm-review/production-tracking-placeholder`

Verified marker text:

1. `Production tracking stays blocked as a placeholder progress branch.`

Verification result:

```text
Url           : https://apex-operations-web.vercel.app/pm-review/production-tracking-placeholder
StatusCode    : 200
MarkerPresent : True

Url           : https://operations.apexpowerops.com/pm-review/production-tracking-placeholder
StatusCode    : 200
MarkerPresent : True
```

## Hosted Smoke Proof

Production hosted-route smoke passed:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=21 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/production-tracking-placeholder status=200 marker="Production tracking stays blocked as a placeholder progress branch."
```

## Boundary

This lane widens hosted availability only for the existing read-only production-tracking placeholder planning slice.

It does not admit:

1. production tracking writes,
2. customer reporting,
3. financial handoff,
4. backend seam mutation,
5. workbook macro execution,
6. autonomous AI business-state mutation.