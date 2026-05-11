# APEX Parent-Root Workflow And Ignore Retirement Packet

Date: 2026-05-07
Status: Recorded workflow-and-ignore retirement baseline with residual mirror tracking
Scope: controlled retirement of the parent-root `.github/workflows/` mirror and parent-root `.gitignore` active-boundary role after `apex-power-ops-platform/` becomes the standalone canonical git root

Closeout interpretation note:

This retirement event is already complete. This packet now preserves the executed workflow and ignore retirement method plus the residual mirror truth, not a live retirement event that still needs to be run.

Current routing:

1. use `PROJECT_STATUS.md` for the latest completed residue slice and current sequencing,
2. use `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for governing repo-foundation decisions,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover closeout queue,
4. use this packet when the executed workflow retirement, ignore retirement, or residual mirror boundary needs to be audited as historical provenance.

## Purpose

This packet preserves how the last parent-root publication surfaces were demoted after the git boundary moved.

It exists to prevent two failure modes after standalone cutover:

1. leaving `C:/APEX Platform/.github/workflows/` or `C:/APEX Platform/.gitignore` as hidden publication dependencies,
2. deleting those parent-root surfaces without first proving that the repo-owned workflow and ignore surfaces fully replace them.

## Current Assessment

The standalone git-boundary event is now complete.

Current closeout truth:

1. GitHub Actions publication for the canonical repo now comes from `apex-power-ops-platform/.github/workflows/` under `jasonlswenson-sys/apex-power-ops`.
2. `apex-power-ops-platform/.gitignore` is now the active ignore contract for the canonical repo.
3. `C:/APEX Platform/.github/workflows/deployed-control-plane-smoke.yml` remains only as historical mirror residue in the older umbrella repo.
4. `C:/APEX Platform/.gitignore` remains only as a workstation-umbrella ignore surface and must not be treated as the Apex Ops publication contract.

## Current Surfaces

Current parent-root residual surfaces:

1. `C:/APEX Platform/.github/workflows/deployed-control-plane-smoke.yml`
2. `C:/APEX Platform/.gitignore`

Current repo-owned canonical surfaces:

1. `apex-power-ops-platform/.github/workflows/calc-engine-ci.yml`
2. `apex-power-ops-platform/.github/workflows/control-plane-api-ci.yml`
3. `apex-power-ops-platform/.github/workflows/deployed-control-plane-smoke.yml`
4. `apex-power-ops-platform/.github/workflows/deployed-mutation-seam-smoke.yml`
5. `apex-power-ops-platform/.github/workflows/forms-engine-ci.yml`
6. `apex-power-ops-platform/.github/workflows/operations-web-browser-smoke.yml`
7. `apex-power-ops-platform/.github/workflows/operations-web-hosted-smoke.yml`
8. `apex-power-ops-platform/.github/workflows/pm-idempotency-metrics-export.yml`
9. `apex-power-ops-platform/.github/workflows/pm-idempotency-sweep.yml`
10. `apex-power-ops-platform/.gitignore`

## Retirement Objective

Retirement is complete only when all of the following are true:

1. GitHub Actions publication is sourced from `apex-power-ops-platform/.github/workflows/` under the standalone repo boundary.
2. `apex-power-ops-platform/.gitignore` is the only active ignore contract for the canonical repo.
3. `C:/APEX Platform/.github/workflows/` no longer participates in default publication.
4. `C:/APEX Platform/.gitignore` is no longer the active ignore surface for Apex Ops publication.
5. Any parent-root remnants that survive do so only as explicit archive or compatibility residue.

The current assessment above satisfies this objective for the canonical repo boundary.

The retained sequences below are now historical execution provenance plus residual mirror reference, not a live retirement checklist.

## Historical Preconditions

Before the retirement event was marked complete, all of the following had to be true:

1. the standalone git-boundary event defined in `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-EXECUTION-PACKET-2026-05-07.md` has completed successfully,
2. `git rev-parse --show-toplevel` from `C:/APEX Platform/apex-power-ops-platform` resolves to the standalone repo root,
3. the canonical remote for that standalone repo is proven against `jasonlswenson-sys/apex-power-ops`,
4. Olares parity has been reattached against `/home/olares/code/apex/apex-power-ops-platform`,
5. the closing cutover evidence confirms parent-root-only lanes were not silently absorbed into the standalone repo.

These preconditions are now satisfied by the recorded cutover evidence and operator-surface updates.

## Historical Evidence Captured Before Retirement

The retirement closeout was required to capture all of the following before mutating the parent-root workflow or ignore surfaces:

1. list of files under `C:/APEX Platform/.github/workflows/`,
2. list of files under `C:/APEX Platform/apex-power-ops-platform/.github/workflows/`,
3. top section of `C:/APEX Platform/.gitignore`,
4. top section of `C:/APEX Platform/apex-power-ops-platform/.gitignore`,
5. standalone repo-root `git status --short`,
6. standalone repo-root `git remote -v`,
7. Olares host workflow-path proof under `/home/olares/code/apex/apex-power-ops-platform/.github/workflows`.

## Historical Workflow Retirement Sequence

### Phase 1: Confirm Canonical Workflow Set

1. Verify the repo-owned workflow directory contains the full intended active workflow set.
2. Confirm the parent-root workflow directory is only transitional publication residue.
3. Compare any same-named workflow files, especially `deployed-control-plane-smoke.yml`, and verify the repo-owned copy is the authoritative one.

### Phase 2: Prove Standalone Workflow Publication

1. Confirm the standalone repo boundary exposes `apex-power-ops-platform/.github/workflows/` as the publishable GitHub Actions path.
2. Capture repository evidence showing the standalone repo root, branch, and remote before retiring the parent-root mirror.
3. If any workflow file still differs materially between parent-root and repo-owned locations, reconcile that file before retirement.

### Phase 3: Retire The Parent-Root Workflow Mirror

1. Remove the parent-root workflow mirror from the default publication contract.
2. Preserve a governed record of which parent-root workflow files were retired or archived.
3. Update any remaining docs that still imply `C:/APEX Platform/.github/workflows/` is publishable.

Execution result:

1. The default publication contract now points only at the standalone canonical repo.
2. The parent-root workflow file remains as explicit mirror residue in the historical umbrella repo.
3. Operator docs now describe the repo-owned workflow lane as canonical.

## Historical Ignore-Contract Retirement Sequence

### Phase 1: Compare Ignore Responsibilities

1. Review root-only ignore rules in `C:/APEX Platform/.gitignore`.
2. Identify which ignore rules are still required for `apex-power-ops-platform/` after standalone cutover.
3. Re-home any still-required canonical repo rules into `apex-power-ops-platform/.gitignore` before retirement.

### Phase 2: Remove Parent-Root Active Role

1. Retire the parent-root note that says `C:/APEX Platform/.gitignore` is the active ignore surface for Apex Ops publication.
2. Confirm the repo-owned `.gitignore` fully covers the canonical repo boundary.
3. Preserve any non-platform workstation umbrella ignore rules outside the canonical repo if they still serve the umbrella root.

Execution result:

1. The parent-root note is now rewritten to describe umbrella-only scope.
2. The repo-owned `.gitignore` remains the only active ignore contract for canonical repo operations.
3. Umbrella ignore rules remain available at the parent root without participating in repo publication.

## Historical No-Go Conditions

During the live retirement event, execution had to stop if any of the following remained true:

1. the standalone repo boundary is not yet proven,
2. any active workflow file still exists only at the parent root,
3. the repo-owned `.gitignore` is missing ignore rules required for normal canonical repo operation,
4. Olares host parity still depends on the parent-root workflow or ignore surfaces,
5. retirement would blur workstation-umbrella ignore rules with canonical repo ignore rules.

## Historical Closing Evidence Requirements

The retirement closeout was required to record:

1. pre-retirement and post-retirement workflow file listings,
2. explicit confirmation that the repo-owned workflow lane is the only publishable GitHub Actions surface,
3. pre-retirement and post-retirement ignore-contract proof,
4. confirmation that `apex-power-ops-platform/.gitignore` is the only active ignore contract for the canonical repo,
5. list of docs updated to remove the parent-root publication-surface assumption.

## Success Standard

This packet is now materially complete: the parent-root workflow mirror and parent-root ignore active role are demoted from default publication, and the standalone canonical repo plus its Olares mirror remain the active operating surfaces.