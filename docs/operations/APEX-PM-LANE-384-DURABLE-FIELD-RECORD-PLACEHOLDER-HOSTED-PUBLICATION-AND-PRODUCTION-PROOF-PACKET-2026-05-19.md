# APEX PM Lane 384 - Durable Field Record Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Executed, hosted, and production-verified.

Decision label:

`PM_DURABLE_FIELD_RECORD_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 384 closes the hosted-publication tranche for the durable-field-record placeholder route created in Lane 383.

This lane proves the durable-field-record placeholder route is no longer only local truth. It is now publicly available on the production operations-web hosts and covered by the hosted-route smoke suite.

## Selected Outcome

Selected outcome:

`PM_DURABLE_FIELD_RECORD_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

Meaning:

1. clean-main commit `ac569c58` is deployed,
2. `/pm-review/durable-field-record-placeholder` is publicly reachable on the production aliases,
3. the public route renders the expected placeholder marker text,
4. the hosted smoke suite passes with the new route included.

## Deployment Proof

Preview deployment created from the clean-main commit:

1. deployment id: `dpl_HkZWHUgX85ndJVac5w1orUSk9Nit`
2. preview URL: `https://apex-operations-e2a933iez-jasonlswenson-sys-projects.vercel.app`
3. status before promotion: `Ready`

Production deployment created by promotion:

1. deployment id: `dpl_8kSfWx8M9NHDYjfV84yWK2EbKBAT`
2. production URL: `https://apex-operations-m8sxbpep7-jasonlswenson-sys-projects.vercel.app`
3. aliases attached:
   - `https://apex-operations-web.vercel.app`
   - `https://operations.apexpowerops.com`

## Public Route Proof

Direct HTTP verification passed on both public aliases for:

1. `/pm-review/durable-field-record-placeholder`

Verified marker text:

1. `Durable field record stays blocked as a placeholder evidence branch.`

Verification result:

```text
Url           : https://apex-operations-web.vercel.app/pm-review/durable-field-record-placeholder
StatusCode    : 200
MarkerPresent : True

Url           : https://operations.apexpowerops.com/pm-review/durable-field-record-placeholder
StatusCode    : 200
MarkerPresent : True
```

## Hosted Smoke Proof

Production hosted-route smoke passed:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=20 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/durable-field-record-placeholder status=200 marker="Durable field record stays blocked as a placeholder evidence branch."
```

## Boundary

This lane widens hosted availability only for the existing read-only durable-field-record placeholder planning slice.

It does not admit:

1. durable field record writes,
2. evidence upload,
3. production tracking writes,
4. backend seam mutation,
5. workbook macro execution,
6. autonomous AI business-state mutation.