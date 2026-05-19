# APEX PM Lane 382 - Schedule Status Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Executed, hosted, and production-verified.

Decision label:

`PM_SCHEDULE_STATUS_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 382 closes the hosted-publication tranche for the schedule-status placeholder route created in Lane 381.

This lane proves the schedule-status placeholder route is no longer only local truth. It is now publicly available on the production operations-web hosts and covered by the hosted-route smoke suite.

## Selected Outcome

Selected outcome:

`PM_SCHEDULE_STATUS_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

Meaning:

1. clean-main commit `588646a4` is deployed,
2. `/pm-review/schedule-status-placeholder` is publicly reachable on the production aliases,
3. the public route renders the expected placeholder marker text,
4. the hosted smoke suite passes with the new route included.

## Deployment Proof

Preview deployment created from the clean-main commit:

1. deployment id: `dpl_2kzcTcLcB2DtZPGZqQkFT34kJkcy`
2. preview URL: `https://apex-operations-cjk32f50k-jasonlswenson-sys-projects.vercel.app`
3. status before promotion: `Ready`

Production deployment created by promotion:

1. deployment id: `dpl_GCGEjTq9xKEwwRamMQWQVWBsiQVh`
2. production URL: `https://apex-operations-42kfeckl2-jasonlswenson-sys-projects.vercel.app`
3. aliases attached:
   - `https://apex-operations-web.vercel.app`
   - `https://operations.apexpowerops.com`

## Public Route Proof

Direct HTTP verification passed on both public aliases for:

1. `/pm-review/schedule-status-placeholder`

Verified marker text:

1. `Schedule and status stay blocked as a placeholder control branch.`

Verification result:

```text
Url           : https://apex-operations-web.vercel.app/pm-review/schedule-status-placeholder
StatusCode    : 200
MarkerPresent : True

Url           : https://operations.apexpowerops.com/pm-review/schedule-status-placeholder
StatusCode    : 200
MarkerPresent : True
```

## Hosted Smoke Proof

Production hosted-route smoke passed:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=19 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/schedule-status-placeholder status=200 marker="Schedule and status stay blocked as a placeholder control branch."
```

## Boundary

This lane widens hosted availability only for the existing read-only schedule-status placeholder planning slice.

It does not admit:

1. schedule changes,
2. status mutation,
3. customer promises,
4. durable field record writes,
5. production tracking writes,
6. backend seam mutation,
7. workbook macro execution,
8. autonomous AI business-state mutation.