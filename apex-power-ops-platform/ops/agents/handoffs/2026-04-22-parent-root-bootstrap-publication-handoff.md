# Parent-Root Bootstrap Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Bounded first parent-root publication planning for `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The active implementation surface is now `C:/APEX Platform/apex-power-ops-platform`, but the actual git root still sits one level higher at `C:/APEX Platform`.

Current verified state:

1. parent-root status still reports the subtree as untracked: `?? apex-power-ops-platform/`
2. `git ls-files -- apex-power-ops-platform/` returns no tracked paths
3. normal diff-based packet publication against tracked `HEAD` state is therefore not yet available for platform paths
4. bounded first introduction of named platform files is still feasible from the parent root
5. the parent-root `.gitignore` now includes a scoped exception for `apex-power-ops-platform/.vscode/tasks.json`, so the task surface can be included in an initial bounded packet without `git add -f`

This means the next publication move is not a routine incremental commit. It is an explicit bootstrap packet that introduces the first tracked platform paths into the parent repository.

## 2. What Was Verified

The following facts were verified directly from the parent root at `C:/APEX Platform`:

1. `git status --short -- apex-power-ops-platform/` returns `?? apex-power-ops-platform/`
2. `git ls-files -- apex-power-ops-platform/` returns no tracked paths
3. a dry-run bounded add over named platform files shows Git can isolate the requested file paths without pulling broader unexpected paths into scope
4. the earlier dry-run also exposed that `.vscode/tasks.json` was blocked by parent-root ignore policy until a scoped exception was added
5. the scoped parent-root `.gitignore` exception is the smallest root-cause fix because it preserves the broader `.vscode/` ignore posture while allowing the platform task surface to be versioned deliberately

## 3. Recommended First Packet Shape

Treat the first parent-root publication as a governance-and-operator bootstrap packet, not as a broad code-surface cutover.

Recommended packet contents:

1. `C:/APEX Platform/.gitignore`
2. `C:/APEX Platform/apex-power-ops-platform/.vscode/tasks.json`
3. `C:/APEX Platform/apex-power-ops-platform/README.md`
4. `C:/APEX Platform/apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
5. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
6. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
7. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
8. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md`
9. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/README.md`
10. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`

Rationale:

1. it introduces the governed operator and planning truth surfaces first
2. it keeps the first tracked platform packet bounded to documentation, task automation, and publication protocol
3. it avoids turning the initial parent-root introduction into an uncontrolled broad subtree add

## 4. Recommended Parent-Root Staging Sequence

From `C:/APEX Platform`:

```powershell
git status --short -- apex-power-ops-platform/
$env:APEX_PLATFORM_GIT_PATHSPEC='apex-power-ops-platform/.vscode/tasks.json;apex-power-ops-platform/README.md;apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md;apex-power-ops-platform/docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md;apex-power-ops-platform/docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md;apex-power-ops-platform/docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md;apex-power-ops-platform/docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md;apex-power-ops-platform/ops/agents/handoffs/README.md;apex-power-ops-platform/ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md'
git add -- .gitignore
git add -- ($env:APEX_PLATFORM_GIT_PATHSPEC -split ';')
git diff --cached -- .gitignore apex-power-ops-platform/
```

If the VS Code task surface is preferred instead of direct `git add`, set the same `APEX_PLATFORM_GIT_PATHSPEC` value and run `Stage named platform paths`, then separately stage `C:/APEX Platform/.gitignore` from the parent root before reviewing the staged diff.

The root task surface now also exposes the packet directly:

1. `Preview parent-root bootstrap packet`
2. `Stage parent-root bootstrap packet`
3. `Parent-root bootstrap packet staged diff`

Use that task trio when the packet matches this handoff exactly. Fall back to the explicit `git add` sequence above only when the packet definition changes.

## 5. Validation Expectation For This Packet

Before any eventual commit, validate only the smallest relevant slice:

1. syntax or file-error validation on the touched markdown and JSON surfaces
2. `git add -n -- .gitignore` plus a dry-run add over the named packet paths if the packet definition changes
3. `git diff --cached -- .gitignore apex-power-ops-platform/` review before any commit

This packet does not require runtime deploy proof, browser smoke, or hosted route reruns because it is a publication-boundary bootstrap packet, not a runtime behavior packet.

## 6. Do Not Do

1. do not use `git add .` or repo-root-wide staging from `C:/APEX Platform`
2. do not use `git add -- apex-power-ops-platform/` for this first packet unless the decision has shifted from bounded bootstrap introduction to explicit broad cutover
3. do not assume `git diff` against `HEAD` will tell the full platform story before the first platform paths are intentionally tracked
4. do not include unrelated parent-repo changes outside the defined packet just because they are visible at the same git root
5. do not reopen hosted packet `001af` or the separate deploy-worktree lane because this bootstrap publication tranche exists

## 7. Exit Condition

This handoff closes when:

1. the first parent-root bootstrap packet is explicitly defined and dry-run validated
2. the staged set remains bounded to the named governance and operator surfaces
3. a future commit, if performed, introduces only the intended first tracked platform paths

## 8. Current Authority Order For This Lane

When this tranche is resumed, use authority in this order:

1. `README.md` and `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` for current operator git-boundary instructions
2. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md` and `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md` for current workspace-state and publication-boundary framing
3. this handoff for the bounded first parent-root bootstrap packet definition

This handoff does not authorize a broad cutover by itself. It defines the smallest governed parent-root publication path so future continuation does not confuse first introduction of tracked platform paths with routine incremental repo work.