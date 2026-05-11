# TCC Relay Phase 2 Operations Web Promoted-Host Redeploy Blocker Handoff

Date: 2026-05-03
Status: Resolved recovery record
Scope: record the concrete hosted deployment blocker, the recovery actions that cleared it, and the final promoted-host validation outcome

Current routing: `docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`
Historical source-label note: the `Platform-Authority/TCC-RELAY-*` packet names preserved below are lineage labels from the original relay packet chain and are not current repo-local paths.

## Authority

This blocker handoff is governed by:

1. `docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`
2. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
3. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
4. `apps/operations-web/DEPLOYMENT_VALIDATION.md`

## Objective

Record how the completed production recovery for `https://operations.apexpowerops.com` was achieved after the first Phase 2 compare slice landed and why the blocker is now closed.

## Confirmed State

1. the first bounded Phase 2 compare slice is closed PASS in repo,
2. the promoted host `https://operations.apexpowerops.com` now serves the recovered compare-slice bundle,
3. the promoted-host rerun completed successfully with `PROMOTED_HOST_SUMMARY failed=0` against the production alias.

## Verified Deployment Facts

Read and write verification completed from this workstation:

1. `npx vercel whoami` returned `Logged in as jasonlswenson-sys` with active team `jasonlswenson-sys-projects`.
2. `git rev-parse --show-toplevel` confirmed the actual git root for this checkout is `C:/APEX Platform`, not `C:/APEX Platform/apex-power-ops-platform`.
3. `npx vercel project inspect apex-operations-web --scope jasonlswenson-sys-projects` confirmed the live project setting `Root Directory: apex-power-ops-platform/apps/operations-web`.
4. the app-local link file `apps/operations-web/.vercel/project.json` matches that same project and rootDirectory.
5. `npx vercel inspect operations.apexpowerops.com --scope jasonlswenson-sys-projects` now confirms the production alias points at deployment `dpl_2emJi8u3ZuMMKb42hDrWjo9Kxg5R` with status `Ready`.

## Verified Git Identity Facts

Git inspection and follow-through completed from this workstation:

1. global git config is now `Jason Swenson <jasonlswenson@gmail.com>`,
2. repo-local git config is now `Jason Swenson <jasonlswenson@gmail.com>`,
3. a corrected-author publish commit was created and pushed as `e07a3df7206c3f213f45c3fb6ecef037cef557a8` with author and committer both `Jason Swenson <jasonlswenson@gmail.com>`,
4. the next Git-linked Vercel deployment for branch `clean-main` used that corrected commit metadata successfully.

Conclusion: the git-author blocker is no longer the active deployment blocker.

## Root Cause And Recovery

The hosted redeploy failure resolved through this sequence:

1. Vercel project `apex-operations-web` is linked to GitHub repo `jasonlswenson-sys/apex-power-ops`,
2. a Git-linked deployment from commit `e07a3df` failed before build with Vercel error `NOW_SANDBOX_WORKER_ROOTDIR_NOT_EXIST` because the project setting had been reduced to `apps/operations-web` even though the real git root is the parent workspace root,
3. the Vercel project rootDirectory was corrected back to `apex-power-ops-platform/apps/operations-web`, which cleared the pre-build root resolution failure,
4. that exposed a second hosted packaging failure, `Cannot find module 'next/dist/compiled/next-server/server.runtime.prod.js'` from `/vercel/path0/apps/operations-web/noop.js`,
5. `apps/operations-web/next.config.ts` was then corrected in commit `2b572b35fa7bf3a3d98675616cc4ac4e54cfdf1b` so both `outputFileTracingRoot` and `turbopack.root` resolve from the true repo root `C:/APEX Platform`,
6. `corepack pnpm --filter @apex/operations-web build` passed locally after that change and `.next/required-server-files.json` reported `outputFileTracingRoot` anchored at `C:\APEX Platform`,
7. the next Git-linked preview deployment became `Ready`, and `npx vercel promote` was used to cut that ready deployment to production despite the still-stale `productionBranch=main` setting.

## Commands Attempted

### 1. Initial forced redeploy with app `--cwd`

Command:

```powershell
Set-Location "c:/APEX Platform"
npx vercel deploy "c:/APEX Platform" --cwd "c:/APEX Platform/apex-power-ops-platform/apps/operations-web" --yes --force --archive=tgz --scope jasonlswenson-sys-projects --prod --logs
```

Observed result:

1. Vercel targeted project `jasonlswenson-sys-projects/apex-operations-web`,
2. Vercel immediately failed with `Error: The specified Root Directory "apex-power-ops-platform/apps/operations-web" does not exist. Please update your Project Settings.`

### 2. Parent-root retry with explicit project IDs

Command:

```powershell
$env:VERCEL_ORG_ID="team_n57jODEAw5zSqRgdWW2etYxa"
$env:VERCEL_PROJECT_ID="prj_bI3w3TUEwhPvkwhsEmGsQVnzowke"
Set-Location "c:/APEX Platform"
npx vercel deploy "c:/APEX Platform" --yes --force --archive=tgz --scope jasonlswenson-sys-projects --prod --logs
```

Observed result:

1. Vercel again targeted project `apex-operations-web`,
2. Vercel again failed with the same rootDirectory error.

### 3. Final syntax-only retry from the exact parent root using `.`

Command:

```powershell
$env:VERCEL_ORG_ID="team_n57jODEAw5zSqRgdWW2etYxa"
$env:VERCEL_PROJECT_ID="prj_bI3w3TUEwhPvkwhsEmGsQVnzowke"
Set-Location "c:/APEX Platform"
npx vercel deploy . --yes --force --archive=tgz --scope jasonlswenson-sys-projects --prod --logs
```

Observed result:

1. identical failure: `The specified Root Directory "apex-power-ops-platform/apps/operations-web" does not exist.`

### 4. Repo-side trace-root correction

Command:

```powershell
corepack pnpm --filter @apex/operations-web build
```

Observed result:

1. local production build succeeded after `apps/operations-web/next.config.ts` was updated to trace from `C:/APEX Platform`,
2. the fix was committed and pushed as `2b572b3` with message `fix(operations-web): align Vercel trace root`.

### 5. Preview success and production promote

Commands:

```powershell
npx vercel inspect https://apex-operations-rb5td2vuy-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects
npx vercel promote https://apex-operations-rb5td2vuy-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects --yes
npx vercel inspect operations.apexpowerops.com --scope jasonlswenson-sys-projects
```

Observed result:

1. the Git-linked preview deployment became `Ready`,
2. the promoted production deployment became `dpl_2emJi8u3ZuMMKb42hDrWjo9Kxg5R`,
3. the production alias `https://operations.apexpowerops.com` moved to that new ready deployment.

### 6. Final promoted-host proof

Command:

```powershell
node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks
```

Observed result:

1. the control-plane seam check passed,
2. hosted route smoke passed with `failed=0`,
3. browser smoke passed with `3 passed`,
4. the final summary ended with `PROMOTED_HOST_SUMMARY failed=0`.

## Secondary Finding: Oversized Archive Shape

Before the `.vercelignore` fix at the parent workspace root, the parent-root production deploy path began uploading the full workstation workspace and reached `803.7MB / 2.4GB` before it was terminated.

To make any later parent-root deploy attempt operationally sane, a new parent-root `.vercelignore` was added at `C:/APEX Platform/.vercelignore` so future deploys do not archive unrelated workspace lanes and local build residue.

That improvement was supportive, not sufficient on its own. The actual recovery required both the rootDirectory correction and the repo-root trace fix in `apps/operations-web/next.config.ts`.

## Outcome Classification

This blocker is closed.

Specifically:

1. repo code is ready,
2. local and repo-scoped validations passed,
3. Vercel auth is present,
4. production alias ownership is confirmed,
5. the git-author blocker was cleared by commit `e07a3df`,
6. the rootDirectory failure was cleared by restoring `apex-power-ops-platform/apps/operations-web`,
7. the Next runtime packaging failure was cleared by commit `2b572b3`,
8. production now serves the recovered compare slice from deployment `dpl_2emJi8u3ZuMMKb42hDrWjo9Kxg5R`,
9. promoted-host smoke passed end to end.

## Residual Hygiene Item

The Vercel project still reports `productionBranch=main` while the active branch is `clean-main`.

That is no longer a blocker because the ready clean-main deployment was manually promoted to production, but it should still be corrected before assuming future Git-linked pushes will auto-promote on the intended branch.

## Final Truthful State

1. the deployment-operations blocker that sat between the repo-closed compare slice and public promoted-host proof is resolved,
2. the canonical deployment proof now lives in `apps/operations-web/DEPLOYMENT_VALIDATION.md`,
3. this document should be treated as a closed recovery record, not as an active blocker handoff.