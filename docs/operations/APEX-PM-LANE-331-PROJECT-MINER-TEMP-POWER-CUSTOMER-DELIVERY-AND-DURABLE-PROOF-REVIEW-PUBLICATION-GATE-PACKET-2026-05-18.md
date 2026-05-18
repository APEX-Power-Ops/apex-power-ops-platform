# APEX PM Lane 331 - Project Miner Temp Power Customer Delivery And Durable Proof Review Publication Gate Packet

Date: 2026-05-18

Status: Current truthful blocker after hosted smoke classification

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_PUBLICATION_GATE_PACKET`

## Purpose

PM Lane 331 closes the ambiguity left after local implementation and hosted-smoke readiness.

The goal of this lane is not to commit or push code. The goal is to prove whether the public mutation-seam hosts already serve the delivery/proof review routes and, if not, classify the next blocker precisely enough that the follow-up is publish-only rather than vague hosted troubleshooting.

## Selected Outcome

Selected outcome:

`CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_PUBLICATION_GATE_READY`

## Hosted Proof Performed

The repo-owned hosted smoke was run with the new bounded flag against both existing live hosts:

1. `https://mutation-seam.apexpowerops.com`
2. `https://apex-platform-mutation-seam.onrender.com`

Executed command shape:

1. `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url <host> --include-temp-power-customer-delivery-proof-review`

## Recorded Result

Both hosts returned the same outcome:

1. `/health` returned `200`
2. root returned `200`
3. approval queue returned `200`
4. all existing schedule reads returned `200`
5. `openapi.json` returned `200`
6. OpenAPI did not contain `/api/v1/mutations/temp-power-customer-delivery-proof-reviews`
7. OpenAPI did not contain `/api/v1/reads/temp-power-customer-delivery-proof-status`
8. `GET /api/v1/reads/temp-power-customer-delivery-proof-status` returned framework `404 Not Found`

This proves the blocker is not custom-domain drift. Both the custom domain and the Render hostname are still serving a build that predates the delivery/proof route registration.

## Publication-Gap Proof

The delivery/proof review slice is still only local worktree state.

Tracked files required for the slice remain modified locally, and the canonical route/persistence/migration/test files remain untracked locally. Hosted promotion cannot include files that are not yet published to `clean-main`.

## Required Next Action

The next truthful action is to publish only the separately admitted delivery/proof review slice to `clean-main`, then rerun the bounded hosted smoke on both public hosts.

Stop conditions:

1. do not claim hosted proof before the new routes appear in OpenAPI and the readback route stops returning framework `404`
2. do not widen into hosted delivery/proof write execution
3. do not widen finance behavior, source writeback, or customer billing delivery authority
4. do not create a new service, change DNS, widen ingress, or change secrets as part of this lane

## Validation Performed

1. hosted smoke against `https://mutation-seam.apexpowerops.com`
2. hosted smoke against `https://apex-platform-mutation-seam.onrender.com`
3. local publication-state inspection with `git status --short` on the delivery/proof slice
4. scoped `git diff --check`

## Next Safe Step

Publish-only follow-up lane:

1. publish the admitted delivery/proof slice to `clean-main`
2. rerun hosted smoke with `--include-temp-power-customer-delivery-proof-review`
3. only if hosted smoke turns green, decide whether hosted first-write proof is separately admitted