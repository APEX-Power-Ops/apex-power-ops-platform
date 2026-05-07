# Operator Bootstrap Runbook

This runbook defines the intended local operator workflow for the Apex Power Ops platform bootstrap.

## Operating Assumption

Use `/home/olares/code/apex/apex-power-ops-platform` as the preferred operator working root when attached to the Olares host.

Use `C:/APEX Platform/apex-power-ops-platform` as the client-side working view when the operator is attached from the Windows field laptop or another Windows client.

Do not assume sibling legacy repositories are the default execution surface.

## Git Scope

Use the platform root as the primary implementation surface, but remember that the current git boundary remains transitional and spans the parent-root mirror.

Required operator behavior:
- do not assume `C:/APEX Platform/apex-power-ops-platform` is already an independent git repo
- when checking git status or diffs, interpret results in the context of the parent repo boundary
- when staging work for future commits, explicitly scope paths to `apex-power-ops-platform/` or narrower so unrelated parent-repo changes are not mixed in
- treat tracked changes elsewhere under `C:/APEX Platform` as separate lanes unless a cross-lane operation is explicitly intended
- prefer originating bounded staging and staged-diff review from `/home/olares/code/apex` unless a client-only fallback is required

Preferred Olares-hosted parent-root git flow:

```bash
cd /home/olares/code/apex
git status --short -- apex-power-ops-platform/
git add -- apex-power-ops-platform/.vscode/tasks.json apex-power-ops-platform/README.md apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- apex-power-ops-platform/
```

Client-triggered host fallback:

```powershell
ssh olares-mesh 'cd /home/olares/code/apex && git status --short -- apex-power-ops-platform/'
ssh olares-mesh 'cd /home/olares/code/apex && git diff --cached -- apex-power-ops-platform/'
```

Windows client fallback parent-root git flow:

```powershell
Set-Location 'C:/APEX Platform'
git status --short -- apex-power-ops-platform/
git add -- apex-power-ops-platform/.vscode/tasks.json apex-power-ops-platform/README.md apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- apex-power-ops-platform/
```

Whole-subtree staging is not the default operator move even though `apex-power-ops-platform/` is now a tracked subtree inside the parent repo. Reserve `git add -- apex-power-ops-platform/` for explicit cutover or intentionally broad publication work only.

The current publication boundary is still transitional. Use the host-native flow for bounded staging, staged-diff review, and focused validation preparation, then close the slice through the normal publication and host-parity gate.

Bounded packet staging example for the `Stage named platform paths` task:

```powershell
$env:APEX_PLATFORM_GIT_PATHSPEC='apex-power-ops-platform/.vscode/tasks.json;apex-power-ops-platform/README.md;apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md'
```

After setting the pathspec, run `Stage named platform paths` and then `Platform subtree staged diff` before any commit.

The parent-root `.gitignore` now carries a scoped exception for `apex-power-ops-platform/.vscode/tasks.json`, so the workspace task surface can be included in bounded parent-root staging without `git add -f`.

For historical context on the completed first parent-root introduction packet, use `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`.

Current packet constraint:
- this bootstrap subtree does not yet contain every active platform lane under `apex-power-ops-platform/`; parent-root active lanes that already exist today are referenced below with `../...` paths from the subtree root

Git safety rules:
- do not use `git add .` from `C:/APEX Platform` unless an explicit cross-lane operation is intended
- a bounded slice of the platform subtree is now tracked on parent-root `clean-main`, so normal `git diff` against `HEAD` is available for already-introduced paths; still keep staging bounded when unrelated parent-root changes are present and treat broader subtree publication as deliberate introduction work
- default to staging explicit platform file paths or a bounded packet pathspec rather than the whole subtree
- review the staged diff before any commit so unrelated parent-repo changes remain outside the publication set

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
$repoRoot = 'C:/APEX Platform'
Set-Location $platformRoot
python -m venv .venv
& "$platformRoot/.venv/Scripts/python.exe" -m pip install --upgrade pip setuptools wheel
Set-Location "$repoRoot/apps/control-plane-api"
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
Get-ChildItem 'C:/APEX Platform/apex-power-ops-platform' -Recurse -File | Select-Object -ExpandProperty FullName
```

```powershell
Get-ChildItem 'C:/APEX Platform/apex-power-ops-platform' -Recurse -File |
	Select-String -Pattern 'pattern1|pattern2'
```

## Primary Operator Entry Points

VS Code tasks:
- the bootstrap-packet helper tasks remain available for historical packet review and narrow bounded staging, but routine publication work can now use normal parent-root `git diff` and `git add -- <paths>` against tracked `HEAD`
- `Olares host bootstrap status`
- `Olares host platform git status`
- `Olares host platform staged diff`
- `Run platform API local`
- `Restart platform API local`
- `Platform subtree git status`
- `Stage named platform paths`
- `Stage entire platform subtree (cutover only)`
- `Preview parent-root bootstrap packet`
- `Stage parent-root bootstrap packet`
- `Parent-root bootstrap packet staged diff`
- `Platform subtree staged diff`
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
- `../apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py`
- `../apps/control-plane-api/scripts/check_local_host_readiness.py`
- `../apps/control-plane-api/scripts/bootstrap_local_env.py`
- `../apps/control-plane-api/scripts/smoke_deployed_control_plane.py`
- `../apps/control-plane-api/scripts/check_schema_drift.py`

## Olares Durable-Host Entry Surface

Use the bounded host bootstrap surface when the operator needs one current-status view of the durable Olares development posture instead of separate MCP, hold-boundary, and git checks.

Use `docs/architecture/OLARES-HOST-NATIVE-OPERATOR-PUBLICATION-WORKFLOW-2026-05-06.md` when the operator needs the preferred Olares-hosted git-preparation flow rather than the older Windows-default packet guidance.

Primary task:

- `Olares host bootstrap status`

Direct host command:

```powershell
ssh olares-mesh 'cd /home/olares/code/apex && bash apex-power-ops-platform/tools/ai/run-olares-host-bootstrap-status.sh'
```

That surface reports:

1. current parent-root host commit and status count,
2. old-clone observe-only state,
3. materialized host toolchain presence,
4. minimal MCP trio readiness,
5. current hold-boundary result from the host posture.

## Local Contract Sources

Use these local files first:
- `C:/APEX Platform/Platform-Authority/`
- `../apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json`
- `../apps/control-plane-api/README.md`
- `../apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` when a future hosted regression needs a compact rerun checklist rather than repo-local runtime repair

Use `C:/APEX Platform/Platform-Authority/` for strategic authority above the bootstrap root.

## Validation Baseline

Current expected local validation slices:

```powershell
Set-Location 'C:/APEX Platform/apps/control-plane-api'
$env:DATABASE_URL='postgresql://placeholder:placeholder@localhost:5432/placeholder'
& 'C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe' -m pytest tests/test_control_plane.py tests/test_control_plane_worker.py tests/test_control_plane_sync.py tests/test_dispatch_dedicated_mcp_surface_check.py tests/test_dispatch_deployed_control_plane_smoke.py tests/test_github_mcp_transport.py -q
```

```powershell
Set-Location 'C:/APEX Platform/apex-power-ops-platform'
.venv/Scripts/python.exe ../apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py --task-id demo-task --target-path Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md --content 'draft content' --dry-run
```

## Governance Intent

The bootstrap root should operate as the current platform control surface even before final repository cutover.

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
