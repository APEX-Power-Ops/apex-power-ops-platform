# Olares Dev Residency 010 Bounded Operations-Web Backend Seam And Hosted Route Validation Execution Handoff

Date: 2026-05-05
Status: Complete
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-010-bounded-operations-web-backend-seam-and-hosted-route-validation-execution.json`
Scope: bounded host-side execution of the public control-plane seam smoke and `operations-web` hosted-route smoke using already admitted host-local toolchains only

## Authority

This handoff depends on Packet 009, the published Packet 008 client-only
posture result, the `operations-web` scripts and deployment validation runbook,
and the roadmap.

## Execution Boundary

Packet 010 may execute only:

1. the public control-plane seam smoke against `https://control.apexpowerops.com`
2. the `operations-web` hosted-route smoke against `https://operations.apexpowerops.com`
3. host cleanliness checks around those commands

Packet 010 must not open Playwright browser runtime provisioning, host-local VS
Code desktop installation, package or lockfile mutation, runtime or service
mutation, public ingress widening, broader product delivery reopening by
implication, Gitea or canonical-hosting transition, remote rewrite, rollback,
force, reset, clean, or old-clone mutation.

## Exact Intended Commands

From `/home/olares/code/apex/apex-power-ops-platform` on Olares:

1. `/home/olares/apex-data/toolchains/calc-engine-venv/bin/python apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route`
2. `node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com`

## Verdict

Packet 010 confirms:

`bounded_host_side_validation_passed`

## Execution Result

From `/home/olares/code/apex/apex-power-ops-platform` on Olares:

1. `/home/olares/apex-data/toolchains/calc-engine-venv/bin/python apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route` ended in `RESULT PASS`
2. `node apps/operations-web/scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com` ended in `SMOKE_SUMMARY failed=0 passed=8 base_url=https://operations.apexpowerops.com/`

`/home/olares/code/apex` was clean before and after the slice at published
commit `08839ae08506a55cc0b1d64f19a3e2a984377f28`.

`/home/olares/src/apex-power-ops-platform` remained observe-only with status
count 30.

## Next Candidate

The next packet is:

`Olares Dev Residency 011 - Post-010 Operations Visibility Lane Reopening Decision`