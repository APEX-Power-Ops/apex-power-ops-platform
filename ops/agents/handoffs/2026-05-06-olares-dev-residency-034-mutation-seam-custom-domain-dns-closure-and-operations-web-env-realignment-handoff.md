# Olares Dev Residency 034 - Mutation-Seam Custom-Domain DNS Closure And Operations-Web Env Realignment Handoff

Date: 2026-05-06
Status: Complete
Packet: `2026-05-06-olares-dev-residency-034`

## Outcome

The hosted mutation-seam custom-domain lane is now closed end-to-end.

`https://mutation-seam.apexpowerops.com` is live over HTTPS and passes the repo-owned deployed seam smoke, `operations.apexpowerops.com` is cut over to production deployment `dpl_8kQsnU68Jjej285HbWpEEdRVHDZv`, and the public same-origin PM routes plus the governed promoted-host proof rerun green against the intended custom-domain seam target.

## Execution Result

1. Completed the GoDaddy DNS write for `mutation-seam.apexpowerops.com` by saving the CNAME `mutation-seam -> apex-platform-mutation-seam.onrender.com` through the OTP verification flow.
2. Confirmed public DNS resolution through `8.8.8.8` and `1.1.1.1`, then later through the default resolver as propagation completed.
3. Proved the custom-domain seam host was live by loading `https://mutation-seam.apexpowerops.com/health` successfully in the browser and rerunning `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py` to `RESULT PASS`.
4. Realigned `MUTATION_SEAM_BASE_URL` on the real Vercel project `apex-operations-web` back to `https://mutation-seam.apexpowerops.com` across Production, Preview, and Development using the isolated link at `C:/APEX Platform/tmp/vercel-apex-operations-web-link`.
5. Created fresh preview-derived deployment `https://apex-operations-4f2acc4np-jasonlswenson-sys-projects.vercel.app` and promoted it to production deployment `dpl_8kQsnU68Jjej285HbWpEEdRVHDZv` at `https://apex-operations-pp62b0s3o-jasonlswenson-sys-projects.vercel.app`, aliased to `https://operations.apexpowerops.com`.
6. Revalidated the public same-origin PM routes and reran the governed promoted-host proof to `PROMOTED_HOST_SUMMARY failed=0` after the final cutover.

## Validation

1. GoDaddy DNS UI -> PASS (`Your DNS record has been updated successfully` after saving CNAME `mutation-seam -> apex-platform-mutation-seam.onrender.com`)
2. Public DNS checks -> PASS (`Resolve-DnsName mutation-seam.apexpowerops.com -Server 8.8.8.8` and `-Server 1.1.1.1` both resolved the expected CNAME chain; the default resolver later matched)
3. Browser probe of `https://mutation-seam.apexpowerops.com/health` -> PASS (`{"status":"healthy","version":"0.1.0","seam":"mutation-seam"}`)
4. `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com` -> PASS (`RESULT PASS`)
5. `vercel env pull` from `C:/APEX Platform/tmp/vercel-apex-operations-web-link` -> PASS (`MUTATION_SEAM_BASE_URL="https://mutation-seam.apexpowerops.com"` on Production, Preview, and Development)
6. `npx -y vercel inspect operations.apexpowerops.com --scope jasonlswenson-sys-projects` -> PASS (public alias now resolves to deployment `dpl_8kQsnU68Jjej285HbWpEEdRVHDZv`)
7. Direct public probes against `https://operations.apexpowerops.com/api/v1/reads/approval-queue`, `/api/v1/schedule/projects`, `/api/v1/schedule/drivers`, `/api/v1/schedule/tracer?task_id=probe-task`, and `/api/v1/schedule/variance` -> PASS (`200 application/json` for all five routes)
8. `npx pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:promoted-host --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks` -> PASS (`PROMOTED_HOST_SUMMARY failed=0`)

## Notes

1. The Render settings page briefly continued to show stale `Waiting for DNS` and `Waiting for Verification` labels during propagation, but the live HTTPS endpoint and repo-owned smoke proved the real runtime state before production cutover.
2. The final Vercel production promotion took longer to settle than the earlier hosted closure packet; the new deployment remained `Initializing` for a few minutes before becoming `Ready` and acquiring the public aliases.

## Next Packet Candidate

None. The hosted mutation-seam custom-domain lane is closed. Reopen only for a new bounded infrastructure objective or a production regression.