# Olares Dev Residency 030 - Bounded Public Mutation-Seam Host And Ingress Scaffolding Execution Handoff

Date: 2026-05-06
Status: Complete
Packet: `2026-05-05-olares-dev-residency-030`

## Outcome

The repo now contains the missing public mutation-seam scaffold and the matching same-origin ingress contract in `apps/operations-web`.

This packet does **not** claim that the public seam host is already deployed. It only lands the repo-owned contract required for that next step.

## Landed Changes

1. `apps/operations-web/next.config.ts` now rewrites `/api/v1/reads/:path*`, `/api/v1/schedule/:path*`, and `/api/v1/mutations/:path*` to the server-side target `MUTATION_SEAM_BASE_URL`.
2. `apps/mutation-seam/render.yaml` now defines the first bounded Render host shape for `https://mutation-seam.apexpowerops.com`.
3. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py` plus `.github/workflows/deployed-mutation-seam-smoke.yml` now define the deployed seam smoke path.
4. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`, `apps/mutation-seam/DEPLOYMENT.md`, `apps/mutation-seam/README.md`, and `apps/operations-web/DEPLOYMENT_VALIDATION.md` now describe the public-host plus ingress contract explicitly.

## Validation

1. `corepack pnpm --filter @apex/operations-web build` -> PASS
2. `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py` -> PASS
3. editor error sweep on the touched config/workflow/script files -> no errors found

## Remaining Boundary

1. the Render service for `mutation-seam.apexpowerops.com` is not yet deployed from this packet
2. the Vercel host has not yet been rebuilt with `MUTATION_SEAM_BASE_URL=https://mutation-seam.apexpowerops.com`
3. public PM live-data proof remains pending until both of those hosted changes exist

## Next Recommended Packet

`Olares Dev Residency 031 - Bounded Public Mutation-Seam Hosted Deployment And Public PM Live-Data Proof`

Scope:

1. deploy the public mutation-seam host
2. run the deployed mutation-seam smoke
3. rebuild/promote `operations-web` with `MUTATION_SEAM_BASE_URL` pointed at the public seam host
4. rerun public PM live-data checks against `https://operations.apexpowerops.com`