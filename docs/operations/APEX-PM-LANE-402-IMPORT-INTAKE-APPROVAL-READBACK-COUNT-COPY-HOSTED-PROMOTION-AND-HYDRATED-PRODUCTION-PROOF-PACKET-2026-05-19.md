# APEX PM Lane 402 - Import-Intake Approval-Readback Count Copy Hosted Promotion And Hydrated Production Proof Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_IMPORT_INTAKE_APPROVAL_READBACK_COUNT_COPY_HOSTED_PROMOTION_AND_HYDRATED_PRODUCTION_PROOF`

## Purpose

PM Lane 402 closes the next bounded tranche after local completion of PM Lane 401.

PM Lane 401 aligned the canonical `/pm-review/import-intake` copy with the live approval-readback count in source, but production was still serving the older import-intake deployment from commit `b767e19` rather than the ready preview built from commit `9326204`. The immediate remaining gap was hosted promotion and truthful live-browser proof for the latest canonical route state.

## Root Cause

The repo-local approval-readback copy alignment was complete, but hosted production had not yet been advanced to the latest ready `clean-main` deployment.

Observed hosted state before this lane:

```text
Production deployment: BQ1jSFN7CPZoBfswrPYiHc2EYXcC
Production source:     clean-main @ b767e19
Preview deployment:    3uZg3FVunXZUYXQsSDaHB8LDWG6w
Preview source:        clean-main @ 9326204
```

## Change Surface

Hosted surface updated:

1. Vercel deployment state for `apex-operations-web`

Repo governance files updated:

1. `PROJECT_STATUS.md`
2. `docs/operations/APEX-PM-LANE-402-IMPORT-INTAKE-APPROVAL-READBACK-COUNT-COPY-HOSTED-PROMOTION-AND-HYDRATED-PRODUCTION-PROOF-PACKET-2026-05-19.md`
3. `ops/agents/handoffs/2026-05-19-pm-lane-402-import-intake-approval-readback-count-copy-hosted-promotion-and-hydrated-production-proof-closeout-handoff.md`

Implemented hosted action:

1. Confirmed production was still on `b767e19`
2. Confirmed the latest ready `clean-main` preview was `3uZg3FVunXZUYXQsSDaHB8LDWG6w` from `9326204`
3. Promoted that ready preview to production in Vercel
4. Verified the resulting production deployment `CEwDX7a174tGYgny8S6ozaWZgV3g` reached `Ready`
5. Verified the hosted approval-status read seam through both mutation-seam and operations-web public paths
6. Verified the hydrated live `/pm-review/import-intake` page in a headless browser after network idle

## Hosted Validation

Focused hosted validation passed:

```text
Vercel production deployment before promotion
Production deployment BQ1jSFN7CPZoBfswrPYiHc2EYXcC
Source clean-main @ b767e19
Status Ready

Vercel ready preview deployment identified
Preview deployment 3uZg3FVunXZUYXQsSDaHB8LDWG6w
Source clean-main @ 9326204
Status Ready

Vercel production promotion
Created production deployment CEwDX7a174tGYgny8S6ozaWZgV3g
Source clean-main @ 9326204
Status Ready

Hosted approval-status read proof
https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-status
- classification: approved_for_import_packet
- current_candidate_match: true
- approval_record_count_for_candidate: 1

https://operations.apexpowerops.com/api/v1/reads/project-import-approval-status
- classification: approved_for_import_packet
- current_candidate_match: true
- approval_record_count_for_candidate: 1

Hydrated browser proof
https://operations.apexpowerops.com/pm-review/import-intake
- MATCH: current readback shows 1 approval record for this candidate
- MATCH: approved for import packet
- MATCH: APPROVAL RECORDS 1
- NO MATCH: zero approval records for this candidate
```

## Proof Boundary

Raw public HTML still exposes the client page's pre-hydration fallback state, which can include zero-branch copy before JavaScript settles.

This lane proves the stronger surface that matters for the live workbench:

1. the PM Lane 401 commit is the live production deployment,
2. the hosted approval-status read seam returns `approved_for_import_packet` with one matching approval record,
3. the hydrated live browser renders the nonzero branch for the current candidate.

## Boundary

This lane does not:

1. change product code,
2. change route behavior or payload schema,
3. add approval POST wiring or admit approval-row creation,
4. change approval, import, assignment, schedule/status, field, production, customer, or finance authority,
5. add backend mutation, schema migration, or data write,
6. widen services, auth, ingress, secrets, or autonomous AI business-state mutation.

## Result

The latest import-intake approval-readback copy commit is now the ready production deployment on Vercel, and the hydrated live `operations.apexpowerops.com/pm-review/import-intake` page truthfully renders the nonzero approval-readback branch for the current candidate. This closes the hosted publication and live-browser proof gap that remained after the local copy-alignment tranche.