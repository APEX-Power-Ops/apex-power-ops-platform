# Apex Power Ops Platform

This directory is the active platform monorepo root and the canonical Apex Ops git boundary.

Current status:
- active implementation and publication surface for Apex Ops consolidation
- standalone repo root at `C:/APEX Platform/apex-power-ops-platform`
- canonical remote/branch flow now tracks `https://github.com/jasonlswenson-sys/apex-power-ops.git` on `clean-main`
- current operational target for platform consolidation, repo-boundary hardening, and Olares-hosted runtime work
- current stakeholder-facing status board now lives in `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`

Authority:
- strategic authority entry now starts at `C:/APEX Platform/apex-power-ops-platform/docs/authority/README.md`
- repo-structure authority now also lives in `C:/APEX Platform/apex-power-ops-platform/docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
- this root is the canonical implementation and git entrypoint for active Apex Ops work
- visual orientation for the current Vercel, Render, Supabase, Olares, Project Miner, and AI orchestration split lives at `C:/APEX Platform/apex-power-ops-platform/docs/operations/APEX-OPS-VISUAL-SYSTEM-MAP-2026-05-15.md`

## Olares One Transition

The Olares One workstation is now the intended primary host for the active APEX Platform development, services, and staging workflow.

Current repo authority for that transition lives in:

1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `C:/APEX Platform/apex-power-ops-platform/plan/Olares_MVP_Execution_Roadmap.md`
3. `C:/APEX Platform/apex-power-ops-platform/plan/infrastructure-olares-full-implementation-roadmap-1.md`
4. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-POST-CLOSURE-EXECUTION-CHECKLIST-2026-04-25.md`
5. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-PRIVATE-STACK-BLUEPRINT-2026-05-01.md`
6. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`
7. `C:/APEX Platform/apex-power-ops-platform/docs/authority/OLARES-BUILD-GUIDE.md`
8. `C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-CHECKLIST.md`

Execution bootstrap for fresh implementation sessions:

1. `C:/APEX Platform/apex-power-ops-platform/docs/operations/OLARES-VSCODE-BUILD-SESSION-PROMPT.md`
2. `C:/APEX Platform/apex-power-ops-platform/APEX Power Ops Platform.code-workspace`

Interpretation rules:

1. `apex-power-ops-platform/` is the live implementation workspace and canonical repo root for active Apex Ops work
2. `C:/APEX Platform` is now workstation-umbrella and historical lineage residue, not the default publication boundary for this repo
3. the first governed Olares workstation lane and the first installed-app proof lane for `forms-engine` and `p6-ingest` are already closed
4. the bounded `personal-notes` private lane is operationally closed in host-only scope and remains outside the governed installed-app set
5. newly-authored Olares work should add the dev/services/staging infrastructure layer to this existing workspace rather than replacing the current app/package/infra structure
6. do not treat future Olares work as open-ended bring-up; changes beyond the current closed baseline require a new explicit packet, especially for public routing, shared auth, or new installed apps

## Operator Quick Start

This standalone repo root should now be treated as the primary local operator surface for platform work.

Read `PROJECT_STATUS.md` first when you need the current post-cutover platform summary, Olares workspace posture, the signed-off laptop-to-Olares migration baseline, or any drift-triggered follow-on without reconstructing it from packet history.

Preferred Olares-hosted startup path:
1. attach through VS Code Remote-SSH or `ssh olares-mesh`
2. open `/home/olares/code/apex/apex-power-ops-platform/APEX Power Ops Platform.code-workspace` when using VS Code, or open the repo folder directly if a workspace file is not available
3. run bounded git preparation and focused validation directly from `/home/olares/code/apex/apex-power-ops-platform`

Host terminal example:

```bash
cd /home/olares/code/apex/apex-power-ops-platform
```

Recommended local startup path:
1. Open `C:/APEX Platform/apex-power-ops-platform/APEX Power Ops Platform.code-workspace` as the default VS Code entry artifact
2. Create or refresh the root virtual environment at `.venv/`
3. Activate that environment from the platform root
4. Run platform tasks from this root, not from sibling legacy repositories

Windows example:

```
cd C:\APEX Platform\apex-power-ops-platform
.venv\Scripts\Activate.ps1
```

If you need to override the interpreter used by workspace tasks, set `APEX_PLATFORM_PYTHON` to the desired Python executable path. Otherwise the workspace tasks now prefer `.venv\Scripts\python.exe` automatically.

## Git Boundary

Platform implementation work should be performed from `C:/APEX Platform/apex-power-ops-platform`, and this directory is now the standalone git root.

Current git posture:
1. run status, diff, stage, branch, and publication from this repo root or the matching Olares host repo root
2. default to explicit file paths or a bounded repo-relative pathspec when preparing staged changes
3. reserve whole-repo staging for intentionally broad change sets only
4. treat `C:/APEX Platform` and other sibling roots as separate historical or umbrella lanes unless an explicit cross-repo operation is intended

Preferred Olares-hosted git flow:

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git status --short
git add -- .vscode/tasks.json README.md docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- .
```

Windows client repo-root git flow:

```powershell
$repoRoot = 'C:/APEX Platform/apex-power-ops-platform'
Set-Location $repoRoot
git status --short
git add -- .vscode/tasks.json README.md docs/OPERATOR-BOOTSTRAP-RUNBOOK.md
git diff --cached -- .
```

Whole-repo staging is not the normal packet flow. Reserve `git add -- .` or the `Stage entire platform repo (broad change)` task for explicit broad publication events; prefer explicit file paths or bounded repo-relative pathspecs when the slice is narrower.

VS Code task usage for bounded packet staging:

```powershell
$env:APEX_PLATFORM_GIT_PATHSPEC='.vscode/tasks.json;README.md;docs/OPERATOR-BOOTSTRAP-RUNBOOK.md'
```

Then run `Stage named platform paths` and review `Platform repo staged diff` before any commit.

Those task helpers now resolve the repo root directly from the workspace location.

`apex-power-ops-platform/.gitignore` is now the active ignore contract for canonical repo operations. The parent-root `.gitignore` remains umbrella residue only.

For historical context on the completed first parent-root introduction packet, use `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`.

Current packet constraint:
1. this bootstrap subtree does not yet bundle the full active platform lane set under `apex-power-ops-platform/`
2. the remaining historical draft-packet helper tail in `.vscode/tasks.json` is preserved for provenance and packet review, but it is not the default operator path
3. lane names below this section refer to the current repo-local implementation surface unless explicitly marked as historical provenance or optional reconciliation residue

Git safety rules:
1. do not use `git add .` from `C:/APEX Platform/apex-power-ops-platform` unless a broad repo change is explicitly intended
2. default to staging explicit repo-relative file paths or a bounded packet pathspec rather than the whole repo
3. review the staged diff before any future commit so unrelated changes remain excluded
4. treat parent-root residue and sibling worktrees as separate lanes unless a deliberate cross-lane maintenance step is required

Current operator entrypoints:
- the bootstrap-packet helper tasks remain available for historical packet review and narrow bounded staging, but routine publication work now uses normal repo-root `git diff` and `git add -- <paths>` against tracked `HEAD`
- `Olares host platform git status` in `.vscode/tasks.json`
- `Olares host platform staged diff` in `.vscode/tasks.json`
- `Run platform API local` in `.vscode/tasks.json`
- `Restart platform API local` in `.vscode/tasks.json`
- `Platform repo git status` in `.vscode/tasks.json`
- `Stage named platform paths` in `.vscode/tasks.json`
- `Stage entire platform repo (broad change)` in `.vscode/tasks.json`
- `Preview parent-root bootstrap packet` in `.vscode/tasks.json`
- `Stage parent-root bootstrap packet` in `.vscode/tasks.json`
- `Parent-root bootstrap packet staged diff` in `.vscode/tasks.json`
- `Platform repo staged diff` in `.vscode/tasks.json`
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
- `apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py`
- `docs/architecture/OLARES-HOST-NATIVE-OPERATOR-PUBLICATION-WORKFLOW-2026-05-06.md`

Primary local contract and authority surfaces:
- `docs/authority/README.md`
- `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
- `plan/infrastructure-olares-full-implementation-roadmap-1.md`
- `apps/control-plane-api/docs/contracts/CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json`
- `apps/control-plane-api/README.md`
- `apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` for future hosted rerun validation if the deployed seam regresses

Current external frontier:
1. the workstation-local control-plane lane is green
2. the hosted apparatus-route deployment lane on `https://control.apexpowerops.com` is now closed for packet `001af`
3. use `apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` for the bootstrap-local hosted rerun path; earlier hosted execution handoffs are not bundled inside this packet
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

This root is the canonical operating surface for active Apex Ops consolidation work.
