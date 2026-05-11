# Historical Workspace Current Status

Date: 2026-04-21
Status: Historical pre-cutover status snapshot
Scope: `C:/APEX Platform/apex-power-ops-platform`

Historical status note:

This document preserves an early workspace-status snapshot from before standalone repo cutover and later repo-foundation normalization. It is not the current status authority.

Current routing:

1. use `PROJECT_STATUS.md` for the current status surface,
2. use `docs/authority/README.md` for the current authority chain,
3. use `plan/infrastructure-olares-full-implementation-roadmap-1.md` and `ops/agents/handoffs/` for current sequencing and packet history.

## Historical Executive Status

This snapshot records the workspace state before the later standalone repo cutover and authority relocation work closed several of the gaps described below.

What was already true in that snapshot:

1. the repo is the active implementation surface for platform consolidation work
2. the top-level lane model is present and mostly aligned to target topology
3. multiple active runtime and shared-package lanes already exist
4. the repo now has a documented workspace audit and local status markers for silent lanes
5. the workspace cleanup and organization baseline has been refreshed so the authority audit now tracks current facts instead of stale governance gaps
6. the workspace now has an execution checklist for lane normalization so merge-target and deferred-lane follow-through no longer depends on implied next steps
7. operator-facing docs at that time still reflected an earlier platform-first but parent-root-boundary model
8. the task surface at that time still relied on bounded parent-root git inspection and explicit-path staging

What was not yet true in that snapshot:

1. transitional app-lane decisions are now ratified, but their bounded merge execution is not yet complete
2. placeholder lanes are documented and explicitly deferred rather than implemented
3. the repo does not yet expose a final deployment and validation map for deferred, seed, or future lanes beyond the currently active runtimes
4. source-domain re-home is still only partially materialized in platform-local lanes
5. parent-root git authority still sat at `C:/APEX Platform` in this historical snapshot; that statement is now preserved only as pre-cutover provenance and not as current repo-boundary guidance

## Lane Status

### Active runtime and implementation lanes

| Lane | State | Status summary |
| --- | --- | --- |
| `apps/control-plane-api` | active | primary backend control-plane lane; large active drift and ongoing service expansion are present |
| `apps/operations-web` | active | primary browser operator surface; already substantial enough to treat as real runtime, and now carries multiple re-homed PM read-only review slices |
| `apps/mutation-seam` | active | valid bounded runtime lane; malformed residue cleanup is complete |
| `packages/calc-engine` | active | shared calculation core |
| `packages/forms-engine` | active | bounded forms-engine import is live in the platform repo and now has workspace-local smoke, focused pytest, and package CI validation paths over the promoted MOP, PSS, and AHA artifact set |
| `packages/p6-ingest` | active | shared P6/Primavera baseline ingest package; first host-installed proof closed 2026-04-25 under the Olares roadmap and live MCP `apex-p6` endpoint plus committed canary runtime evidence resolve through the governed cross-lane fixture in `apps/mutation-seam/app/schedule/fixtures/` |
| `infra/database` | active | active infrastructure lane |
| `ops/agents` | active | packet and handoff workflow lane |
| `ops/knowledge-control-plane` | active | active registry lane; known registry encoding corruption has been normalized |
| `ops/knowledge-resource-operations` | active | active ops knowledge lane |
| `knowledge/` | active | valid top-level knowledge lane with explicit local boundary guidance |

### Reserved, seed, and transitional lanes

| Lane | State | Status summary |
| --- | --- | --- |
| `apps/forms-studio` | deferred placeholder | approved destination lane; explicitly deferred until a real forms app-shell packet starts and bounded `neta-forms` UI slices are promoted |
| `packages/api-contracts` | deferred placeholder | approved destination lane; explicitly deferred until stable shared contracts are reused by more than one active surface |
| `apps/field-surface` | seed | retain as a bounded field-runtime seed lane; current prototype shell is real enough to keep, but it is not yet a governed deployable and the future `field-app` rename remains deferred |
| `apps/integration-surface` | merge-target | both the Python harness and the browser dashboard have now been re-homed into active lanes, the empty `public/` shell has been removed, and the lane is now marker-only retirement residue rather than an active feature home |
| `apps/lead-surface` | merge-target | the lead-facing browser prototype has been re-homed into `apps/operations-web` under `/lead-ops/index.html`; `apps/lead-surface` is now down to marker-only retirement residue unless a hard deployment boundary is later proven |
| `apps/pm-surface` | merge-target | duplicate PM browser artifacts have been removed from the lane; the approval shell, schedule, drivers, tracer, and variance slices now live in `apps/operations-web`, and `apps/pm-surface` is down to marker-only retirement residue unless a hard deployment boundary is later proven |

### Archive lane

| Lane | State | Status summary |
| --- | --- | --- |
| `archive/legacy-repos` | archive | correctly separated from active implementation paths |

## Governance Status

| Control | Current state | Status |
| --- | --- | --- |
| Authority order | documented in multiple places | partial |
| Workspace audit | documented | complete |
| Lane markers for empty or silent lanes | added | complete |
| Path ownership | `.github/CODEOWNERS` present | complete |
| Workflow and approval map | repo-level map present under `.github/` | complete |
| Migration boundary for control-plane app | documented and valid | complete |
| Knowledge vs docs boundary | `knowledge/README.md` now defines local boundary | complete |
| Deployment and validation map by app | unified map present under `docs/architecture/` | complete |

## Hygiene Status

Confirmed resolved in this audit cycle:

1. generated residue patterns now have root ignore coverage
2. placeholder and transitional lanes now explain themselves locally
3. placeholder, retirement, and seed lane markers now carry explicit local retirement, activation, or graduation gates
4. malformed mutation-seam residue has been removed from the active lane
5. `ops/knowledge-control-plane/registry/GUIDE-REGISTRY.md` has been normalized and nearby registry review found no adjacent corrupted files
6. active app runtime, validation, and env contract paths are now unified in one repo-local map
7. `apps/operations-web` now has a bounded deployment-proof runbook and validated production build path
8. operator docs now carry explicit git-scope guidance plus guarded narrow-path staging examples so future parent-root staging can stay isolated from unrelated changes

Confirmed still open:

1. broader hosted browser-proof and deployment-proof follow-through remains optional, but the governed backend seam on `https://control.apexpowerops.com` is no longer the active blocker because the public host now advertises and serves `/api/v1/neta/apparatus/{apparatus_id}/resources`
2. local deploy-worktree reconciliation and publication remain a separate optional lane: treat `C:/APEX Platform/apex-power-ops-platform-deploy-worktree` as divergent publication residue rather than as evidence that hosted packet `001af` has reopened; a dedicated deploy-worktree handoff is not bundled inside this bootstrap packet
3. the first parent-root publication is no longer an open bootstrap concern because the initial bounded tranche is now tracked on parent-root `clean-main`; keep `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md` as the historical record of that completed first-introduction tranche while treating broader subtree publication as a still-deliberate incremental follow-on

## Structural Assessment

### What is working

1. the repo already has the correct top-level shape for monorepo-style consolidation
2. active code is landing in bounded lanes rather than being spread randomly across the root
3. app-local versus legacy migration distinction in control-plane work is explicit and defensible
4. the repo can already act as the main local operating surface

### What is still unstable

1. merge-target execution has removed the substantive browser residue from `apps/integration-surface`, `apps/lead-surface`, and `apps/pm-surface`; those lanes are now marker-only retirement residue and the remaining work is deployment-proof hardening plus source-domain re-home
2. governance no longer depends on implied ownership, but still operates under a single-maintainer review model
3. source-domain import strategy is understood, but not yet fully materialized through lane-by-lane implementation plans
4. active app entrypoints are now documented and task-aligned, and `apps/operations-web` now has hosted route smoke, local browser smoke, and a promoted-host browser-plus-seam smoke path for the current governed shell contract; the latest public-host rerun shows health, readiness, OAuth discovery, MCP metadata, unauthenticated `401 Bearer` behavior, deployed OpenAPI advertisement, and handler-owned apparatus-route responses all green on `https://control.apexpowerops.com`
5. workstation-level host validation for `apps/control-plane-api` is now a repo-owned readiness-and-seam lane with bootstrap, readiness, restart, and local apparatus smoke tasks; on the current workstation the lane now closes as `host-ready`, and the default local host on `8010` passes bounded apparatus seam smoke after a deterministic restart while the hosted lane is separately closed with public proof
6. the hosted route-promotion step is now closed and proof-backed rather than implicit: use `../apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` for the bootstrap-local rerun path; earlier hosted execution handoffs are not bundled inside this packet
7. parent-root git operations are now safer and more explicit, and the initial platform bootstrap tranche is now intentionally tracked on `clean-main`; the remaining publication risk is a mix of unrelated parent-root drift plus the still-untracked majority of the subtree, not the already-closed first-introduction event itself

## Current Implementation Posture

In this historical snapshot, the workspace was treated as:

- operationally active
- structurally credible
- governance-defined
- not yet fully normalized

That meant new work should continue there, but major lane-shape, ownership, and merge-or-archive decisions should follow the then-live workspace plan instead of accumulating ad hoc.

## Immediate Status Conclusion

At the time of this snapshot, the workspace was ready for deliberate normalization, not another broad discovery pass.

Do not use `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md` as the current cleanup and folder-structure authority baseline for active repo work.

Treat `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md` as historical packet-family follow-through context rather than the active execution surface.

The next implementation work identified in this historical snapshot focused on:

1. continuing bounded source-domain re-home into the active platform lanes
2. source-domain re-home completion by lane
3. extending `apps/operations-web` browser proof from local Playwright smoke to promoted-host seam-aware automation
4. keeping merge-target lane markers current if any new hard deployment boundary is later proven
5. treating deploy-worktree reconciliation or publication as a distinct bounded follow-through lane rather than as remaining hosted route-promotion work
6. treating future publication of already-introduced platform paths as routine bounded staging against tracked `HEAD` state while handling still-untracked subtree material as explicit incremental introduction work