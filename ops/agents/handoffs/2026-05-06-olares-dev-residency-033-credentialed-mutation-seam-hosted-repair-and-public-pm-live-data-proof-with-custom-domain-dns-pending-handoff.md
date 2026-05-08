# Historical Olares Dev Residency 033 - Credentialed Mutation-Seam Hosted Repair And Public PM Live-Data Proof With Custom-Domain DNS Pending Handoff

Date: 2026-05-06
Status: Complete
Packet: `2026-05-06-olares-dev-residency-033`

Historical note: this handoff records one earlier Dev Residency transition record from before the canonical repo boundary moved to `C:/APEX Platform/apex-power-ops-platform` on 2026-05-07. It remains packet-history provenance, not live mutation-seam or AI-boundary transition guidance for current repo operations.

Current routing:

1. use `PROJECT_STATUS.md` for the current residue-retirement lane and latest completed packets,
2. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover boundary closeout queue,
3. use this handoff only when historical provenance is needed for the earlier Dev Residency 033 transition record preserved here.

## Outcome

The hosted PM lane is now functionally closed.

`mutation-seam` is live and passing its repo-owned smoke at `https://apex-platform-mutation-seam.onrender.com`, `operations.apexpowerops.com` is cut over to a production deployment that targets that live seam host, the public same-origin PM routes return `200`, and the governed promoted-host proof closes green.

## Execution Result

1. Attached `mutation-seam.apexpowerops.com` to the Render service and captured the required CNAME target `mutation-seam -> apex-platform-mutation-seam.onrender.com`.
2. Confirmed the Render default hostname was healthy, then used Render logs to identify the real hosted runtime blocker: the Supabase database backing the service did not yet contain the `schedule` schema relation `schedule.projects`.
3. Connected directly to the hosted Supabase database, created the minimal `seam` tables expected by the persisted mutation-seam store, and used `apps/mutation-seam/run_schedule_bootstrap.py` to apply the repo-owned `schedule` migrations and load the schedule fixture data.
4. Re-ran `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py` against `https://apex-platform-mutation-seam.onrender.com` and closed the seam host green.
5. Updated `MUTATION_SEAM_BASE_URL` on the real Vercel project `apex-operations-web` to `https://apex-platform-mutation-seam.onrender.com` so production could use the live seam host while custom-domain DNS remained unresolved.
6. Promoted the newest ready preview-derived deployment to production, producing deployment `dpl_CdxiFmzZ9q9ASirexMg5GeqTZ3Qn` at `https://apex-operations-518s8r5i8-jasonlswenson-sys-projects.vercel.app`, aliased to `https://operations.apexpowerops.com`.
7. Verified the public same-origin PM routes return `200 application/json` and reran the governed promoted-host proof to `PROMOTED_HOST_SUMMARY failed=0`.

## Validation

1. Render custom-domain settings -> PASS (`mutation-seam.apexpowerops.com` attached; verification target is `mutation-seam -> apex-platform-mutation-seam.onrender.com`; Render still shows `Waiting for DNS`)
2. `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://apex-platform-mutation-seam.onrender.com` -> PASS (`RESULT PASS`)
3. Direct hosted Supabase query -> PASS (`schedule.projects=1`, `schedule.tasks=4`, `schedule.relationships=3` after bootstrap)
4. Direct public probes against `https://operations.apexpowerops.com/api/v1/reads/approval-queue`, `/api/v1/schedule/projects`, `/api/v1/schedule/drivers`, `/api/v1/schedule/tracer?task_id=probe-task`, and `/api/v1/schedule/variance` -> PASS (`200 application/json` for all five routes)
5. `npx pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:promoted-host --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks` -> PASS (`PROMOTED_HOST_SUMMARY failed=0`)

## Residual Boundary

1. `https://mutation-seam.apexpowerops.com` still does not resolve publicly because the GoDaddy CNAME has not been added yet.
2. `apex-operations-web` production is intentionally pointed at the live Render hostname, not yet back at the intended custom-domain seam host.
3. The rerunnable `run_schedule_bootstrap.py` path is not fully idempotent on repeated fixture loads yet; the first hosted load succeeded and the live seam proof is green, but a subsequent rerun tripped an aborted-transaction path during the loader replay.

## Next Recommended Packet

`Olares Dev Residency 034 - Mutation-Seam Custom-Domain DNS Closure And Operations-Web Env Realignment`

Scope:

1. add the GoDaddy CNAME `mutation-seam -> apex-platform-mutation-seam.onrender.com`
2. wait for Render to verify `mutation-seam.apexpowerops.com`
3. restage `MUTATION_SEAM_BASE_URL=https://mutation-seam.apexpowerops.com` on `apex-operations-web`
4. perform one final server-side production cutover
5. rerun the public PM ingress probes and promoted-host proof with the custom-domain seam target