# Olares Publication Boundary Retirement Dependency Inventory

Date: 2026-05-06
Status: Updated closeout inventory after canonical cutover and residue normalization
Scope: concrete record of which former publication-boundary dependencies are now closed and which residual hygiene items still remain after the canonical repo moved to `apex-power-ops-platform/`

Closeout interpretation note:

This inventory remains the active closeout queue for post-cutover boundary residue. It should be read together with the recent packet trail in `PROJECT_STATUS.md`, not as a pre-cutover dependency-discovery note.

## Purpose

This document records the publication-boundary dependencies that were formerly tied to `C:/APEX Platform` and the current closeout state after canonical branch promotion.

It exists so residual cleanup does not silently revive the old Windows parent-root publication contract.

## Current Boundary

The governing direction is now explicit: all Apex Ops work should converge on Olares-resident governance, execution, validation, toolchains, and operator context.

GitHub remains canonical.

`C:/APEX Platform/apex-power-ops-platform` is now the canonical publication boundary for active Apex Ops repo operations.

`C:/APEX Platform` is now workstation-umbrella and historical-lineage residue, not the default publication boundary.

`/home/olares/code/apex/apex-power-ops-platform` remains the authoritative host implementation surface.

`/home/olares/code/apex` remains the containing host umbrella, not the default git root for this repo.

## Dependency Classes

### 1. Root publication control no longer lives on the parent Windows boundary

Active publication and closeout work now run from the standalone repo root on both workstation and Olares host surfaces.

Evidence:

1. `C:/APEX Platform/apex-power-ops-platform/.git` now materializes the standalone repo boundary,
2. canonical `clean-main` now points at subtree-root commit `dd781695006f159f204ab20eaa20adf5e296772c`,
3. default operator git examples now start from the repo root rather than the parent-root umbrella.

### 2. Operator publication workflow is now documented from repo-root paths

The primary README, runbook, and active task helpers now describe the standalone repo-root contract directly.

Evidence:

1. `README.md` now states that `C:/APEX Platform/apex-power-ops-platform` is the standalone git root,
2. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` now stages and diffs repo-relative paths from repo root,
3. `.vscode/tasks.json` now resolves the workspace folder as repo root and uses repo-relative staging helpers.

### 2A. GitHub Actions publication no longer depends on the parent-root workflow lane

The canonical repo boundary now owns the publishable GitHub Actions lane directly. The parent-root workflow file survives only as historical mirror residue in the older umbrella repo.

Evidence:

1. `apex-power-ops-platform/.github/workflows/` now contains the active lane workflow set for calc-engine, control-plane, operations-web, mutation-seam, and PM idempotency automation,
2. canonical repo publication now targets `jasonlswenson-sys/apex-power-ops` rather than the parent-root umbrella repo,
3. the duplicated `deployed-control-plane-smoke.yml` files are aligned, which means the remaining parent-root file is mirror residue rather than an active dependency.

### 3. Strategic and status authority still has parent-root mirrors, but they are no longer publication dependencies

Even with Olares as the active implementation surface, some high-authority project surfaces still have aligned copies at the parent root.

Examples:

1. `PROJECT_STATUS.md`,
2. root `README.md`,
3. `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`,
4. `Platform-Authority/` strategic authority surfaces.

This is now a mirror-governance issue rather than a publication-boundary blocker.

### 4. Adjacent lane READMEs are mostly normalized; remaining drift is in older packet and planning surfaces

The highest-traffic README and runbook surfaces are now materially aligned to the standalone repo boundary and the Olares host implementation root.

The remaining documentation risk is narrower: older plan, packet, and historical workflow surfaces can still read like current instructions if their pre-cutover parent-root context is not stated explicitly.

Examples that require explicit historical interpretation rather than README command normalization:

1. roadmap and packet logs that preserve pre-cutover publication wording,
2. older workspace-boundary plans measured from the former parent-root topology,
3. mirror-governance notes that still mention parent-root publication steps as historical evidence.

These surfaces are now secondary documentation closeout, not blockers for the canonical repo boundary.

## Highest-Leverage Remaining Targets

The already-closed residue slices now include:

1. repo-owned current-truth authority normalization,
2. parent-root mirror routing normalization,
3. parent-root `.claude` entrypoint hardening,
4. early workspace planning demotion.

The next highest-leverage closeout targets are now:

1. older packet-history and legacy planning surfaces that still preserve pre-cutover operator wording without equivalent current-routing context,
2. any remaining mirror or inventory surfaces whose top-of-file status still presents cutover work as an active launch plan instead of closeout state,
3. continued host-parity validation against `/home/olares/code/apex/apex-power-ops-platform`, especially when Control-Hub must substitute for direct mesh SSH.

## Recommended Order

1. keep the operator contract repo-root first,
2. treat parent-root workflow and ignore files as historical or umbrella-only surfaces,
3. verify focused runtime and git-helper checks from the standalone repo root,
4. continue lane-by-lane doc hygiene without reopening the publication boundary question.

## Explicit Non-Goals

This inventory does not authorize:

1. GitHub replacement,
2. Gitea canonical transition,
3. remote rewrite,
4. runtime or service mutation,
5. package or lockfile mutation,
6. old-clone mutation,
7. silent publication-boundary retirement by assertion.

## Current Recommendation

The publication-boundary cutover itself is now materially complete.

The remaining truthful work is closeout: preserve the historical packet record, keep marking pre-cutover operator wording as historical when needed, prevent stale docs from reviving parent-root assumptions, and keep Olares-hosted validation aligned to the standalone canonical repo root.