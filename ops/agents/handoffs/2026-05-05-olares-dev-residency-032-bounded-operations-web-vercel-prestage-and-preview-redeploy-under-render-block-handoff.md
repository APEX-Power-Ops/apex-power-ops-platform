# Olares Dev Residency 032 - Bounded Operations-Web Vercel Prestage And Preview Redeploy Under Render Block Handoff

Date: 2026-05-06
Status: Complete
Packet: `2026-05-05-olares-dev-residency-032`

## Outcome

The operations-web Vercel side of the hosted lane is now materially prepared even though Render remains blocked.

The real browser-host project `apex-operations-web` now carries `MUTATION_SEAM_BASE_URL` across production, preview, and development, and a server-side preview redeploy succeeded against that project.

## Execution Result

1. Confirmed `https://operations.apexpowerops.com` is served by Vercel project `apex-operations-web` on deployment `dpl_3rR9YukiwRwnMcdbKN87Hh87rpVr`.
2. Created an isolated Vercel link at `C:/APEX Platform/tmp/vercel-apex-operations-web-link` targeting `apex-operations-web`.
3. Added `MUTATION_SEAM_BASE_URL=https://mutation-seam.apexpowerops.com` to production, preview, and development on `apex-operations-web`.
4. Removed the same variable back out of the unrelated `apex-power-ops-platform` Vercel project after discovering the first write landed on the wrong target.
5. Server-side redeployed the newest ready preview and produced `https://apex-operations-697hr5p9p-jasonlswenson-sys-projects.vercel.app`.
6. Probed that preview and confirmed preview protection still returns `401` for both the PM shell and same-origin API routes, so preview remains a prep surface rather than the public proof gate.
7. Revalidated that local CLI deploys from `C:/APEX Platform` still fail because Vercel uploads only `.vercelignore` and then reports the configured rootDirectory as missing.

## Validation

1. `npx -y vercel inspect operations.apexpowerops.com --scope jasonlswenson-sys-projects` -> PASS (`apex-operations-web`)
2. `npx -y vercel env ls --cwd C:/APEX Platform/tmp/vercel-apex-operations-web-link --scope jasonlswenson-sys-projects` -> PASS (`MUTATION_SEAM_BASE_URL` on Production, Preview, Development)
3. `npx -y vercel env ls` from `C:/APEX Platform/apex-power-ops-platform` -> PASS (`No Environment Variables found`)
4. `npx -y vercel redeploy https://apex-operations-fej01pnsg-jasonlswenson-sys-projects.vercel.app --target preview --scope jasonlswenson-sys-projects` -> PASS
5. preview probes against `/pm-review/index.html`, `/api/v1/reads/approval-queue`, and `/api/v1/schedule/projects` -> all `401` under preview protection
6. `npx -y vercel deploy --yes --scope jasonlswenson-sys-projects --debug` from `C:/APEX Platform` -> FAIL with local packaging/rootDirectory defect (`.vercelignore` only uploaded)

## Remaining Boundary

1. `https://mutation-seam.apexpowerops.com` still does not exist publicly and remains blocked on Render-authenticated access
2. the production alias `https://operations.apexpowerops.com` has not been re-promoted after the new seam env staging because the seam host is still absent
3. preview remains `401` protected, so it cannot serve as the public PM proof gate
4. public PM same-origin API routes on the production alias remain the prior `404` state until the Render host exists and production is redeployed

## Next Recommended Packet

`Olares Dev Residency 033 - Credentialed Public Mutation-Seam Deployment And Public PM Live-Data Proof`

Scope:

1. obtain or use a Render-authenticated surface
2. create or configure the public `mutation-seam` service
3. run `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com`
4. redeploy and, if valid, promote `apex-operations-web` using the already staged `MUTATION_SEAM_BASE_URL`
5. rerun public PM live-data proof against `https://operations.apexpowerops.com`