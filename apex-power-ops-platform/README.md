# Apex Power Ops Platform

This directory is the first physical bootstrap of the future platform monorepo.

Current status:
- bootstrap scaffold only
- not yet the canonical production repository
- created inside the current APEX Platform repo so topology, import boundaries, and operating rules can be ratified before cutover
- current operational target for platform consolidation and runtime hardening

Authority:
- strategic authority currently remains in `C:/APEX Platform/Platform-Authority/`
- this bootstrap should be treated as the implementation target derived from that authority layer

## Operator Quick Start

This bootstrap root should now be treated as the primary local operator surface for platform work.

Recommended local startup path:
1. Create or refresh the root virtual environment at `.venv/`
2. Activate that environment from the platform root
3. Run platform tasks from this root, not from sibling legacy repositories

Windows example:

```
cd C:\APEX Platform\apex-power-ops-platform
.venv\Scripts\Activate.ps1
```

If you need to override the interpreter used by workspace tasks, set `APEX_PLATFORM_PYTHON` to the desired Python executable path. Otherwise the workspace tasks now prefer `.venv\Scripts\python.exe` automatically.

## Git Boundary

Platform implementation work should be performed from `C:/APEX Platform/apex-power-ops-platform`, but the current git root still sits at `C:/APEX Platform`.

Current git posture:
1. do not assume `apex-power-ops-platform/` is yet an independent git repository
2. run status, diff, stage, and commit operations with the parent repo boundary in mind
3. when git work is necessary, explicitly scope staging to `apex-power-ops-platform/` or narrower file paths so unrelated parent-repo changes are not pulled in accidentally
4. treat parent-repo changes outside `apex-power-ops-platform/` as separate lanes unless an explicit cross-lane operation is intended

Recommended parent-root git flow:

```powershell
Set-Location 'C:/APEX Platform'
git status --short -- apex-power-ops-platform/
git add -- apex-power-ops-platform/.vscode/tasks.json apex-power-ops-platform/README.md apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- apex-power-ops-platform/
```

Whole-subtree staging is not the normal packet flow even though the platform lane is now tracked inside the parent repo. Reserve `git add -- apex-power-ops-platform/` for an explicit cutover or intentionally broad publication event; prefer explicit file paths or bounded pathspecs when unrelated parent-root changes are present.

VS Code task usage for bounded packet staging:

```powershell
$env:APEX_PLATFORM_GIT_PATHSPEC='apex-power-ops-platform/.vscode/tasks.json;apex-power-ops-platform/README.md;apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md'
```

Then run `Stage named platform paths` and review `Platform subtree staged diff` before any commit.

The parent-root `.gitignore` now carries a scoped exception for `apex-power-ops-platform/.vscode/tasks.json`, so the workspace task surface can be included in bounded parent-root staging without `git add -f`.

For historical context on the completed first parent-root introduction packet, use `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`.

Current packet constraint:
1. this bootstrap subtree does not yet bundle the full active platform lane set under `apex-power-ops-platform/`
2. paths below that start with `../` intentionally point at the current parent-root lanes that exist today under `C:/APEX Platform`
3. lane names without `../` are target topology or intended import scope, not a claim that the folder already exists inside this subtree

Git safety rules:
1. do not use `git add .` or repo-root-wide staging from `C:/APEX Platform` unless a cross-lane operation is explicitly intended
2. a bounded slice of `apex-power-ops-platform/` is now tracked on parent-root `clean-main`, so normal `git diff` and bounded publication against `HEAD` are available for already-introduced paths while broader subtree publication still requires deliberate introduction
3. default to staging explicit platform file paths or a bounded packet pathspec rather than the whole subtree
4. review the staged diff before any future commit so unrelated parent-repo changes remain excluded

Current operator entrypoints:
- the bootstrap-packet helper tasks remain available for historical packet review and narrow bounded staging, but routine publication work can now use normal parent-root `git diff` and `git add -- <paths>` against tracked `HEAD`
- `Run platform API local` in `.vscode/tasks.json`
- `Restart platform API local` in `.vscode/tasks.json`
- `Platform subtree git status` in `.vscode/tasks.json`
- `Stage named platform paths` in `.vscode/tasks.json`
- `Stage entire platform subtree (cutover only)` in `.vscode/tasks.json`
- `Preview parent-root bootstrap packet` in `.vscode/tasks.json`
- `Stage parent-root bootstrap packet` in `.vscode/tasks.json`
- `Parent-root bootstrap packet staged diff` in `.vscode/tasks.json`
- `Platform subtree staged diff` in `.vscode/tasks.json`
- `Platform API focused tests` in `.vscode/tasks.json`
- `Control-plane local host readiness` in `.vscode/tasks.json`
- `Control-plane local apparatus-route smoke` in `.vscode/tasks.json`
- `Bootstrap control-plane local env` in `.vscode/tasks.json`
- `Control-plane public apparatus-route gate` in `.vscode/tasks.json`
- `Control-plane public apparatus-route dispatch dry-run` in `.vscode/tasks.json`
- `Control-plane public apparatus-route dispatch` in `.vscode/tasks.json`
- `Calc engine offline tests` in `.vscode/tasks.json`
- `Operations web browser smoke` in `.vscode/tasks.json`
- `Operations web promoted-host smoke` in `.vscode/tasks.json`
- `../apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py`

Primary local contract and authority surfaces:
- `C:/APEX Platform/Platform-Authority/`
- `../apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json`
- `../apps/control-plane-api/README.md`
- `../apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` for future hosted rerun validation if the deployed seam regresses

Current external frontier:
1. the workstation-local control-plane lane is green
2. the hosted apparatus-route deployment lane on `https://control.apexpowerops.com` is now closed for packet `001af`
3. use `../apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` for the bootstrap-local hosted rerun path; earlier hosted execution handoffs are not bundled inside this packet
4. treat `C:/APEX Platform/apex-power-ops-platform-deploy-worktree` as a separate optional reconciliation or publication lane, not as evidence that hosted packet `001af` has reopened; a deploy-worktree handoff is not bundled inside this bootstrap packet yet

Initial scope in this bootstrap:
- `apps/control-plane-api`
- `apps/forms-studio`
- `apps/operations-web`
- `packages/api-contracts`
- `packages/calc-engine`
- `packages/forms-engine`
- `infra/database`
- `ops/agents`
- `knowledge/mappings`
- `docs/authority`
- `archive/legacy-repos`

Import policy:
1. import active slices first
2. keep archive material out of active paths
3. move data and schema work through explicit migration mappings
4. preserve old repo history as governed legacy snapshots rather than flattening everything into the new root

Recommended first imports:
1. `tcc_v5_backend` -> `apps/control-plane-api` and `packages/calc-engine`
2. `NETA-Forms` -> `apps/forms-studio` and `packages/forms-engine`
3. active APEX database and architecture assets -> `infra/database` and `docs/authority`
4. active NETA ETT knowledge assets -> `knowledge/`

This root is intentionally minimal until the bootstrap is ratified, but it is now the active operating surface for consolidation work.