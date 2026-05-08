# Operator Bootstrap Runbook

This runbook defines the intended local operator workflow for the Apex Power Ops platform bootstrap.

Current high-level status board:

- `PROJECT_STATUS.md` for the current post-cutover platform summary, Olares workspace posture, remaining implementation items, and laptop-to-Olares migration status

## Operating Assumption

Use `/home/olares/code/apex/apex-power-ops-platform` as the preferred operator working root when attached to the Olares host.

Use `C:/APEX Platform/apex-power-ops-platform` as the client-side working view when the operator is attached from the Windows field laptop or another Windows client.

Use `APEX Power Ops Platform.code-workspace` at the repo root as the default VS Code entry artifact.

Do not assume sibling legacy repositories are the default execution surface.

## Git Scope

Use the platform root as the primary implementation, staging, and publication surface.

Required operator behavior:
- treat `C:/APEX Platform/apex-power-ops-platform` and `/home/olares/code/apex/apex-power-ops-platform` as matching standalone repo roots
- run `git status`, `git diff`, `git add`, branching, and publication from those repo roots, not from the parent umbrella root
- when staging work for future commits, explicitly scope repo-relative paths when the slice is narrower than the whole repo
- treat tracked changes elsewhere under `C:/APEX Platform` as separate lanes unless a deliberate cross-repo maintenance step is intended
- prefer originating bounded staging and staged-diff review from `/home/olares/code/apex/apex-power-ops-platform` when attached to the host

Preferred Olares-hosted git flow:

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git status --short
git add -- .vscode/tasks.json README.md docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- .
```

Client-triggered host fallback:

```powershell
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git status --short'
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git diff --cached -- .'
```

Windows client repo-root git flow:

```powershell
$repoRoot = 'C:/APEX Platform/apex-power-ops-platform'
Set-Location $repoRoot
git status --short
git add -- .vscode/tasks.json README.md docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- .
```

Whole-repo staging is not the default operator move. Reserve `git add -- .` or the `Stage entire platform repo (broad change)` task for explicit broad publication work only.

The current publication boundary is the standalone repo. Use the host-native flow or the matching local repo-root flow for bounded staging, staged-diff review, and focused validation preparation.

Bounded packet staging example for the `Stage named platform paths` task:

```powershell
$env:APEX_PLATFORM_GIT_PATHSPEC='.vscode/tasks.json;README.md;docs/OPERATOR-BOOTSTRAP-RUNBOOK.md'
```

After setting the pathspec, run `Stage named platform paths` and then `Platform repo staged diff` before any commit.

Those task helpers now resolve the repo root directly from the workspace location.

`apex-power-ops-platform/.gitignore` is now the active ignore contract for canonical repo operations. The parent-root `.gitignore` remains umbrella residue only.

For historical context on the completed first parent-root introduction packet, use `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`.

Treat the historical parent-root task trios as provenance helpers only. They are not routine staging surfaces for current repo-root work.

Current packet constraint:
- this bootstrap subtree does not yet contain every active platform lane under the broader umbrella workspace; parent-root-only lanes remain separate provenance or reconciliation residue and are not part of the default repo contract

Git safety rules:
- do not use `git add .` from `C:/APEX Platform/apex-power-ops-platform` unless an explicit broad repo change is intended
- default to staging explicit repo-relative file paths or a bounded packet pathspec rather than the whole repo
- review the staged diff before any commit so unrelated changes remain outside the publication set
- treat parent-root residue, old worktrees, and sibling lanes as separate concerns unless a deliberate cross-lane maintenance step is intended

## Local Environment

Primary local Python environment:
- `C:/APEX Platform/apex-power-ops-platform/.venv`

Preferred local tooling for analysis and inventory work:
- `python`
- PowerShell 7+
- `rg` if available on `PATH`
- direct file reads from the workspace

Bootstrap commands on Windows:

```powershell
$platformRoot = 'C:/APEX Platform/apex-power-ops-platform'
Set-Location $platformRoot
python -m venv .venv
& "$platformRoot/.venv/Scripts/python.exe" -m pip install --upgrade pip setuptools wheel
Set-Location "$platformRoot/apps/control-plane-api"
& "$platformRoot/.venv/Scripts/python.exe" -m pip install -r requirements-dev.txt
```

If a different interpreter must be used for workspace tasks, set:

```powershell
$env:APEX_PLATFORM_PYTHON='C:/Path/To/python.exe'
```

## Tooling Constraints And Fallbacks

Current working assumptions:
- `rg` may be unavailable in some Windows shell sessions
- markdown-conversion tooling may hang and should not be treated as a required dependency for repo analysis

Required operator behavior:
- if `rg` is present, use it for fast file discovery and text search
- if `rg` is absent, fall back to PowerShell `Get-ChildItem` and `Select-String`
- prefer direct workspace file reads for markdown, docs, and schema review work
- do not block inventory or authority work on markdown-conversion tooling

Windows fallback examples:

```powershell
$platformRoot = 'C:/APEX Platform/apex-power-ops-platform'
Get-ChildItem $platformRoot -Recurse -File | Select-Object -ExpandProperty FullName
```

```powershell
$platformRoot = 'C:/APEX Platform/apex-power-ops-platform'
Get-ChildItem $platformRoot -Recurse -File |
	Select-String -Pattern 'pattern1|pattern2'
```

## Primary Operator Entry Points

Default VS Code entry artifact:
- `APEX Power Ops Platform.code-workspace`

Current status surface:
- `PROJECT_STATUS.md`

VS Code tasks:
- the parent-root bootstrap and scaffold helper tasks remain available only as explicitly historical packet-review surfaces, and routine publication work now uses normal repo-root `git diff` and `git add -- <paths>` against tracked `HEAD`
- `Olares host bootstrap status`
- `Olares host platform git status`
- `Olares host platform staged diff`
- `Run platform API local`
- `Restart platform API local`
- `Platform repo git status`
- `Stage named platform paths`
- `Stage entire platform repo (broad change)`
- `Preview historical parent-root bootstrap packet`
- `Stage historical parent-root bootstrap packet`
- `Historical parent-root bootstrap packet staged diff`
- `Preview historical parent-root Class A scaffold packet`
- `Stage historical parent-root Class A scaffold packet`
- `Historical parent-root Class A scaffold packet staged diff`
- `Platform repo staged diff`
- `Platform API focused tests`
- `Control-plane local host readiness`
- `Control-plane local apparatus-route smoke`
- `Bootstrap control-plane local env`
- `Control-plane public apparatus-route gate`
- `Control-plane public apparatus-route dispatch dry-run`
- `Control-plane public apparatus-route dispatch`
- `Calc engine offline tests`
- `Operations web browser smoke`
- `Operations web promoted-host smoke`

Direct script entry points:
- `apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py`
- `apps/control-plane-api/scripts/check_local_host_readiness.py`
- `apps/control-plane-api/scripts/bootstrap_local_env.py`
- `apps/control-plane-api/scripts/smoke_deployed_control_plane.py`
- `apps/control-plane-api/scripts/check_schema_drift.py`

## Olares Durable-Host Entry Surface

Use the bounded host bootstrap surface when the operator needs one current-status view of the durable Olares development posture instead of separate MCP, hold-boundary, and git checks.

Use `docs/architecture/OLARES-HOST-NATIVE-OPERATOR-PUBLICATION-WORKFLOW-2026-05-06.md` when the operator needs the preferred Olares-hosted git-preparation flow rather than the older Windows-default packet guidance.

Primary task:

- `Olares host bootstrap status`

Direct host command:

```powershell
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && bash tools/ai/run-olares-host-bootstrap-status.sh'
```

That surface reports:

1. current standalone host repo commit and status count,
2. old-clone observe-only state,
3. materialized host toolchain presence,
4. minimal MCP trio readiness,
5. current hold-boundary result from the host posture.

## Local Contract Sources

Use these local files first:
- `docs/authority/README.md`
- `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
- `apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json`
- `apps/control-plane-api/README.md`
- `apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` when a future hosted regression needs a compact rerun checklist rather than repo-local runtime repair

Use `C:/APEX Platform/Platform-Authority/` only as historical strategic provenance when a surviving decision has not yet been fully re-homed into the repo-owned authority chain.

## Validation Baseline

Current expected local validation slices:

```powershell
Set-Location 'C:/APEX Platform/apex-power-ops-platform/apps/control-plane-api'
$env:DATABASE_URL='postgresql://placeholder:placeholder@localhost:5432/placeholder'
& 'C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe' -m pytest tests/test_control_plane.py tests/test_control_plane_worker.py tests/test_control_plane_sync.py tests/test_dispatch_dedicated_mcp_surface_check.py tests/test_dispatch_deployed_control_plane_smoke.py tests/test_github_mcp_transport.py -q
```

```powershell
Set-Location 'C:/APEX Platform/apex-power-ops-platform'
.venv/Scripts/python.exe apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py --task-id demo-task --target-path Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md --content 'draft content' --dry-run
```

## Governance Intent

The bootstrap root now operates as the canonical platform control surface after repository cutover.

Current external frontier:

1. the workstation-local control-plane lane is green
2. the hosted apparatus-route deployment lane on `https://control.apexpowerops.com` is now closed for packet `001af`
3. use `../apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` as the compact rerun checklist if a future deploy regresses the hosted seam
4. treat `C:/APEX Platform/apex-power-ops-platform-deploy-worktree` as a separate optional reconciliation or publication lane, not as evidence that hosted packet `001af` has reopened; a deploy-worktree handoff is not bundled inside this bootstrap packet yet

That means:
- live operator docs should prefer platform-root paths
- local task automation should prefer platform-root tools and environments
- compatibility references to older repos are provenance, not default runtime instructions
- local analysis workflows should tolerate missing shell utilities and avoid dependence on unstable markdown-conversion paths
