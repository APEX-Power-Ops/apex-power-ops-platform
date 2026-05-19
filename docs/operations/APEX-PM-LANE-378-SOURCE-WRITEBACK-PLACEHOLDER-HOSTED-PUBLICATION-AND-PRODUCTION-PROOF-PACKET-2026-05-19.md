# APEX PM Lane 378 - Source Writeback Placeholder Hosted Publication And Production Proof Packet

Date: 2026-05-19

Status: Hosted publication complete and production proof recorded for the admitted read-only source-writeback placeholder planning route.

Decision label:

`PM_SOURCE_WRITEBACK_PLACEHOLDER_HOSTED_PUBLICATION_AND_PRODUCTION_PROOF`

## Purpose

PM Lane 378 closes the next truthful blocker after PM Lane 377 by proving the source-writeback placeholder route is now publicly published on operations-web production and covered by the same promoted-host smoke path that was added locally in the readiness tranche.

This lane records current hosted truth only. It does not widen source writeback authority beyond the already admitted read-only placeholder planning surface.

## Selected Outcome

Selected outcome:

`PM_SOURCE_WRITEBACK_PLACEHOLDER_HOSTED_CURRENT_ON_PRODUCTION`

## Hosted Publication Proof

The current production publication path for the source-writeback placeholder route is:

1. clean-main commit `89355931` created ready preview deployment `dpl_kQEVoXpbm9wwmof6QJ1RBYrTTzFP`,
2. that preview was available at `https://apex-operations-gcxobhbk9-jasonlswenson-sys-projects.vercel.app`,
3. the ready preview was promoted to production deployment `dpl_4cjwdojwDFHBZpMBWarksGWSSE6C`,
4. the production deployment now serves both `https://apex-operations-web.vercel.app` and `https://operations.apexpowerops.com`.

Hosted publication is no longer the controlling blocker for the source-writeback placeholder route.

## Public Route Proof

Direct HTTP verification now succeeds on both production aliases:

1. `https://operations.apexpowerops.com/pm-review/source-writeback-placeholder`
2. `https://apex-operations-web.vercel.app/pm-review/source-writeback-placeholder`

Both public checks returned:

1. HTTP `200`,
2. route marker present: `Source writeback stays blocked as a placeholder downstream branch.`

## Hosted Smoke Proof

The production hosted-route smoke now passes end to end on the custom production domain:

```text
node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 15000
SMOKE_SUMMARY failed=0 passed=17 base_url=https://operations.apexpowerops.com/
SMOKE_OK /pm-review/source-writeback-placeholder status=200 marker="Source writeback stays blocked as a placeholder downstream branch."
```

This proves the promoted-host smoke control surface now matches the real production deployment for the source-writeback placeholder route.

## Boundary

This lane records hosted publication and production proof only.

It does not admit or claim:

1. source workbook writeback, PDF overwrite, source correction commit, or source-system sync authority,
2. workbook macro execution,
3. finance writes, payroll, accounting persistence, or finance-output authority,
4. customer billing delivery or other customer-facing billing release authority,
5. any new backend seam or mutation route,
6. autonomous AI business-state mutation.

## Notes

The promoted production deployment initially appeared in Vercel as `Building` before the public aliases moved. Once production deployment `dpl_4cjwdojwDFHBZpMBWarksGWSSE6C` became `Ready` with the public aliases attached, direct HTTP checks on both public aliases returned `200` with the expected source-writeback placeholder marker and the production hosted smoke passed.

## Next Truth

The hosted-publication blocker for the source-writeback placeholder route is closed.

Any next PM move should target a different explicitly admitted branch rather than another source-writeback placeholder publication proof tranche.