# APEX Workspace Entrypoint Decision

Date: 2026-05-07
Status: Recorded workspace-entrypoint baseline
Scope: canonical VS Code entry artifact for the standalone `apex-power-ops-platform/` repo boundary

Closeout interpretation note:

This entrypoint decision is already executed through the completed standalone cutover. It now serves as recorded repo-foundation baseline for the canonical VS Code entry artifact, not as a live pending cutover choice.

Current routing:

1. use `PROJECT_STATUS.md` for the latest completed residue slice and current sequencing,
2. use `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for governing repo-foundation decisions,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover closeout queue,
4. use this decision note when the recorded workspace-entrypoint contract or parent-root compatibility posture needs to be audited as historical provenance.

## Decision

The default checked-in VS Code entry artifact for the canonical repo is:

`APEX Power Ops Platform.code-workspace`

located at the root of `apex-power-ops-platform/`.

## Why This Decision Was Needed

Before the compatibility rewrite, the parent-root workspace file at `C:/APEX Platform/APEX Platform.code-workspace` opened the mixed umbrella root rather than the intended canonical repo boundary.

That is now migration debt, not a design asset.

Without a repo-owned entrypoint:

1. operators keep entering through the transitional parent root,
2. the repo boundary remains conceptually blurry even when the implementation surface is already repo-first,
3. old root-level residue stays visible as if it were part of the durable daily workspace contract.

## Verified Current State

The bounded check for this decision found:

1. the only checked-in workspace artifact before this change was `C:/APEX Platform/APEX Platform.code-workspace`,
2. that file opens `.` at the parent-root umbrella,
3. the repo already contains a live `.vscode/tasks.json` surface under `apex-power-ops-platform/`,
4. the repo README and operator runbook now point users at the repo-owned workspace artifact as the default VS Code entrypoint.

## Canonical Contract

Going forward:

1. the repo-owned workspace file is the default VS Code entrypoint for platform work,
2. the workspace should open the canonical repo root only,
3. parent-root workspace artifacts are transitional compatibility surfaces until cutover retires them,
4. no new checked-in workspace artifact should normalize the mixed parent root as the steady-state entry contract.

## MVP Shape

The first canonical workspace entrypoint is intentionally minimal:

1. one folder: `.`,
2. rooted at `apex-power-ops-platform/`,
3. relying on repo-owned `.vscode/tasks.json` and repo-local docs,
4. avoiding parent-root path assumptions inside the workspace artifact itself.

## Optimal Shape

After full git-boundary cutover, the same repo-owned workspace artifact should remain the default entrypoint unless a later explicit multi-root decision is justified by real operator need.

Multi-root convenience is not the default.

## Parent-Root Disposition

`C:/APEX Platform/APEX Platform.code-workspace` is now classified as retire-after-verify residue.

It may remain temporarily for compatibility during cutover, but it should no longer be treated as the preferred entry artifact once the repo-owned workspace file exists.

Current compatibility posture:

1. the parent-root workspace file now opens `apex-power-ops-platform/` instead of the umbrella root,
2. that keeps accidental mixed-root entry from being normalized while the legacy filename still exists,
3. the repo-owned workspace file remains the preferred checked-in entry artifact.

## Recorded Follow-Through

1. the repo README and operator runbook now point at the repo-owned workspace artifact,
2. the repo-owned workspace file now serves as the default onboarding path,
3. any final retirement of the parent-root workspace artifact remains separate residue-closeout work after compatibility is no longer needed.