# Olares Publication Boundary Retirement Dependency Inventory

Date: 2026-05-06
Status: Active migration dependency inventory
Scope: concrete remaining dependencies that keep `C:/APEX Platform` as the transitional publication boundary while the program converges toward Olares-first execution

## Purpose

This document records the remaining split-residency dependencies that still tie publication and some operator workflows to `C:/APEX Platform`.

It exists so the next Olares packets can retire those dependencies deliberately instead of treating the current Windows parent-root boundary as a vague background fact.

## Current Boundary

The governing direction is now explicit: all Apex Ops work should converge on Olares-resident governance, execution, validation, toolchains, and operator context.

GitHub remains canonical.

`C:/APEX Platform` remains the current transitional publication boundary.

`/home/olares/code/apex` remains the authoritative host mirror and `/home/olares/code/apex/apex-power-ops-platform` remains the authoritative host implementation surface.

## Dependency Classes

### 1. Root publication control still lives on Windows

Active publication and closeout work is still initiated from the Windows parent-root git boundary.

Evidence:

1. the active authority still names `C:/APEX Platform` as the current publication boundary,
2. the PM cockpit still lists transitional parent-root git publication from `C:/APEX Platform`,
3. publication closeout proof still centers `git push origin clean-main` followed by host `git pull --ff-only`.

### 2. Operator publication workflow is still documented from Windows paths

The current operator bootstrap runbook still teaches parent-root git flow and staging from `C:/APEX Platform`.

Evidence:

1. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` still says the current git root sits at `C:/APEX Platform`,
2. the preferred publication flow begins with `Set-Location 'C:/APEX Platform'`,
3. bounded staging guidance is still expressed from the Windows parent-root posture.

### 3. Strategic and status authority still spans parent-root surfaces outside the platform subtree

Even with Olares as the active implementation surface, high-authority project surfaces still live at the parent root.

Examples:

1. `PROJECT_STATUS.md`,
2. root `README.md`,
3. `Infrastructure/Olares_Workspace_Authority_Framework.md`,
4. `Platform-Authority/` strategic authority surfaces.

This is not automatically wrong, but it means publication-boundary retirement is not only a git-flow issue; it is also an authority-surface placement issue.

### 4. Lane READMEs and command examples still normalize Windows-local execution

Several active READMEs still present Windows-root command examples and path assumptions.

Examples captured during this inventory:

1. `apex-power-ops-platform/README.md`,
2. `apps/operations-web/README.md`,
3. `apps/control-plane-api/README.md`,
4. package READMEs that still reference `C:/APEX Platform/apex-power-ops-platform`.

These surfaces can reintroduce split practice even when the host path is already proven.

## Highest-Leverage Retirement Targets

The next highest-leverage retirement targets are:

1. host-native operator publication workflow and staging guidance,
2. root authority and start-here routing surfaces that still normalize `C:/APEX Platform` as the live publication center,
3. active lane README command examples that still default to Windows-local execution.

## Recommended Order

1. author a bounded host-native publication workflow packet,
2. update the operator runbook and start-here surfaces so the default operational flow starts from Olares-hosted execution,
3. reconcile the highest-traffic lane READMEs to remove Windows-first command guidance,
4. only after those are stable, reassess whether the current parent-root publication boundary can be narrowed or retired without governance loss.

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

The next truthful Olares packet should target the host-native operator publication workflow.

That is the smallest concrete migration dependency with both governance value and day-to-day operator leverage.