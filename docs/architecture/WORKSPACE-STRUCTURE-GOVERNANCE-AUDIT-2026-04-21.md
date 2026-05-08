# Historical Workspace Structure And Governance Audit

Date: 2026-04-21
Status: Historical pre-cutover cleanup and organization audit snapshot
Scope: Active platform repo only (`C:/APEX Platform/apex-power-ops-platform`)

Historical audit note:

This document preserves an early workspace cleanup baseline from before standalone repo cutover and later authority re-home work. It is not the current authority order for repo-shape or publication-boundary decisions.

Current routing:

1. use `docs/authority/README.md` for the current authority chain,
2. use `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for current repo-shape and cutover authority,
3. use `PROJECT_STATUS.md` and `plan/infrastructure-olares-full-implementation-roadmap-1.md` for current execution posture and sequencing.

## Purpose

This document preserves the earlier cleanup and organization baseline for the platform repo.

It does three things:

1. records the governed top-level workspace shape that now exists
2. separates already-closed governance and hygiene gaps from still-open normalization work
3. defines the remaining folder-structure cleanup rules so new work lands in the right lane without reopening broad workspace discovery

This document is intentionally platform-first in its original planning context:

1. implementation work belongs in this repo when a target lane already exists here
2. `C:/APEX Platform/Platform-Authority` remains historical strategic lineage for this older audit context
3. sibling source-domain repos remain lineage and extraction inputs, not equal primary workspaces

## Live Planning Stack

Use these documents together:

1. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md` -> current cleanup and structure baseline
2. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md` -> current operational status snapshot
3. `docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md` -> sequencing surface

Use this audit as historical design input and provenance. Use the current repo-owned authority, status, and roadmap surfaces for active execution sequencing.

## Authority Order

Use this order when structure, migration boundaries, or repo-shape decisions are involved:

1. `C:/APEX Platform/Platform-Authority/`
2. `C:/APEX Platform/Platform-Authority/` documents that have not yet been re-homed into this bootstrap subtree
3. `README.md`
4. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
5. source-domain docs only when a slice has not yet been re-homed

## Current Top-Level Classification

### Governed structural roots

- `.github/`
- `.vscode/`
- `apps/`
- `archive/`
- `docs/`
- `infra/`
- `knowledge/`
- `ops/`
- `packages/`
- `tests/`

These roots are part of the governed platform workspace shape.

### Local or generated roots

- `.venv/`
- `node_modules/`
- `.pytest_cache/`
- `pytest-cache-files-vra1va2u/`

These roots are workstation or generated residue, not governed topology. They must remain ignored or bounded and must not be treated as structure authority.

## Lane Classification

### Active implementation lanes

- `apps/control-plane-api`
- `apps/mutation-seam`
- `apps/operations-web`
- `packages/calc-engine`
- `packages/forms-engine`
- `packages/p6-ingest`
- `docs/authority`
- `docs/architecture`
- `infra/database`
- `ops/agents`
- `ops/knowledge-control-plane`
- `ops/knowledge-resource-operations`
- `knowledge/`

### Seed lane

- `apps/field-surface`

This remains a valid bounded seed lane. It should stay in place until field-runtime work proves either a deployable surface or a rename necessity.

### Merge-target retirement residue

- `apps/integration-surface`
- `apps/lead-surface`
- `apps/pm-surface`

These lanes no longer represent substantive active feature homes.

Current state:

1. `apps/integration-surface` is marker-only residue after the Python harness moved into `apps/mutation-seam` and the browser dashboard moved into `apps/operations-web`
2. `apps/lead-surface` is marker-only residue after the lead-facing browser prototype was re-homed into `apps/operations-web`
3. `apps/pm-surface` is marker-only residue after the PM approval and review slices were re-homed into `apps/operations-web`

Cleanup rule:

- treat these lanes as governed retirement markers, not as places for new implementation work, unless a new hard deployment boundary is explicitly proven

### Deferred placeholder lanes

- `apps/forms-studio`
- `packages/api-contracts`

These lanes are intentionally reserved but still deferred.

Cleanup rule:

- keep them documented and empty or bounded until real implementation packets justify activation

### Archive lane

- `archive/legacy-repos`

This lane must stay explicitly separated from active implementation work.

## Confirmed Current Findings

### 1. In-repo authority is still a bridge, not the final strategic authority

The strategic authority layer still sits above this bootstrap subtree in `C:/APEX Platform/Platform-Authority`.

Implication:

- do not let any future in-repo authority bridge drift into an unplanned replacement for the strategic authority stack
- any future promotion or rename must be explicit

### 2. Ownership governance is now present and should no longer be tracked as a gap

The repo now contains:

- `.github/CODEOWNERS`
- `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`

Implication:

- path ownership is explicit
- review routing is now governed at the repo level
- future structure audits must treat ownership governance as closed unless those files regress or stop matching the live lane model

### 3. Platform-local ignore coverage for generated residue is present and parent-root ignore remains intentionally narrower

The platform subtree `.gitignore` already covers the major generated or workstation residue patterns observed inside `C:/APEX Platform/apex-power-ops-platform`, including:

- `node_modules/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `pytest-cache-files-*/`
- `*.egg-info/`
- `.next/`
- `*.tsbuildinfo`
- `dist/`
- `build/`
- `.env` and `.env.*`

The parent-root `.gitignore` remains intentionally narrower and still focuses on secrets, IDE residue, and the scoped `.vscode/tasks.json` exception required for bounded platform task-surface publication.

Implication:

- cleanup work should focus on classification and lane use
- expand parent-root ignore only when root-level generated residue becomes a recurring operator problem rather than assuming the subtree policy should be copied upward wholesale

### 4. Placeholder and silent lanes now have explicit local markers

The previously ambiguous placeholder and transitional lanes now carry local README guidance.

Implication:

- these folders should be treated as intentional topology, not accidental emptiness
- future cleanup work should preserve marker clarity while avoiding new implementation drift into deferred or retirement lanes

Additional current fact:

- the lane markers now carry explicit local retirement, activation, or graduation gates so operators do not need to infer those thresholds from the architecture docs alone

### 5. Merge-target app lanes are now marker-only retirement residue

Direct directory inspection confirms that:

- `apps/integration-surface/` currently contains only `README.md`
- `apps/lead-surface/` currently contains only `README.md`
- `apps/pm-surface/` currently contains only `README.md`

Implication:

- the structural cleanup question is no longer where their substantive code lives
- the remaining decision is whether and when to keep or retire those markers after the broader lane model is stable enough

### 6. The repo now has the governance surfaces this audit previously said were missing

Current status surfaces already establish:

- explicit ownership governance
- explicit knowledge-boundary guidance
- explicit deployment and validation mapping

Implication:

- future workspace cleanup should focus on remaining normalization backlog, not on re-proposing already-completed control surfaces

### 7. Control-plane migration authority remains correctly split

The control-plane app still maintains the correct visible distinction between:

- `apps/control-plane-api/supabase/migrations/` -> canonical forward migration lane
- `apps/control-plane-api/migrations/` -> legacy utilities, diagnostics, and replay support

Implication:

- new schema changes must continue to land only in the Supabase migration lane
- legacy utilities must remain non-authoritative

### 8. Git authority remains at the parent APEX root even though platform work is now platform-first

Current operator work should happen from `C:/APEX Platform/apex-power-ops-platform`, but the current git root still sits at `C:/APEX Platform`.

Observed current fact:

- parent-root `clean-main` now tracks a bounded platform bootstrap slice on current `HEAD`
- `git diff -- apex-power-ops-platform/` and `git ls-files -- apex-power-ops-platform/` now operate against those already-introduced paths
- the broader subtree still contains substantial untracked platform material that has not yet been deliberately introduced to the parent repo index

Implication:

- git status, diff, stage, and commit operations must still respect the parent repo boundary
- normal diff-based packet publication against tracked `HEAD` state is now available for already-introduced platform paths
- broader subtree publication still requires explicit bounded introduction decisions rather than assuming the entire subtree is already under routine diff coverage
- staging should still default to explicit paths or bounded packet pathspecs when unrelated parent-root changes are present
- unrelated tracked changes elsewhere under `C:/APEX Platform` should be treated as separate lanes, not as default companions to platform work

## Remaining Cleanup And Organization Backlog

### 1. Keep generated roots out of workspace authority conversations

The workspace root still contains local and generated directories alongside governed roots.

Required posture:

1. do not document `.venv/`, `node_modules/`, or pytest caches as part of target topology
2. do not create workflow or structure guidance that depends on those directories being present
3. continue to prefer repo tasks and repo-local contracts over workstation-specific residue

### 2. Preserve the merge-target marker lanes until retirement is explicitly approved

`apps/integration-surface`, `apps/lead-surface`, and `apps/pm-surface` are now down to marker-only residue.

Required posture:

1. do not put new code back into those lanes casually
2. keep the markers while they still help operators understand re-home history and topology intent
3. retire or archive the markers only when the platform lane map is stable enough that the historical distinction no longer adds operational value

### 3. Keep placeholder lanes deferred until they have a real owning packet

`apps/forms-studio` and `packages/api-contracts` are still approved targets, but they are not yet active implementation lanes.

Required posture:

1. no speculative scaffolding
2. no source-domain bulk import just to make the folders look busy
3. activate only when a bounded implementation packet establishes their first real slice

### 4. Continue bounded source-domain re-home into existing platform lanes

The unresolved workspace problem is no longer broad top-level folder confusion. It is lane-by-lane re-home completion.

Required posture:

1. keep promoting source-domain slices into `apps/`, `packages/`, `infra/`, `ops/`, `knowledge/`, `docs/`, or `archive/`
2. do not reopen sibling source repos as default working roots
3. prefer extending active platform lanes over minting new top-level structure

### 5. Keep the deploy-worktree lane separate from active repo normalization

`C:/APEX Platform/apex-power-ops-platform-deploy-worktree` remains a separate optional reconciliation or publication lane.

Required posture:

1. do not treat that folder as part of this repo's governed structure baseline
2. do not use its residue as evidence that hosted packet `001af` has reopened
3. treat any later deploy-worktree handoff as a separate follow-on artifact rather than assuming it is already bundled in this bootstrap packet

## Workspace Standards Enforced By This Audit

### Structure standards

1. Every seed, placeholder, or retirement lane must carry a local `README.md` that explains its status and intended use.
2. New implementation work must prefer existing platform-root lanes over introducing new structural roots.
3. Source-domain repos must not be copied wholesale into the platform repo.
4. Archive and lineage material must stay explicitly separated from active runtime lanes.
5. Generated workstation roots must stay out of target-topology documentation.

### Governance standards

1. `.github/CODEOWNERS` and `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md` are now part of the workspace governance baseline.
2. Future audits must distinguish closed governance controls from open normalization work.
3. Transitional and retirement lanes must be called out explicitly rather than silently normalized away.

### Migration standards

1. Forward schema changes for the control-plane app belong only in `apps/control-plane-api/supabase/migrations/`.
2. `apps/control-plane-api/migrations/` remains a legacy utility lane, not a forward migration authority.
3. Migration acceptance still requires drift-aware validation before and after execution.

## Recommended Next Actions

### Priority 1

1. Continue bounded source-domain re-home into the existing active platform lanes.
2. Keep `apps/integration-surface`, `apps/lead-surface`, and `apps/pm-surface` as marker-only retirement residue until explicit retirement is approved.
3. Extend `apps/operations-web` proof from current local and hosted smoke into broader seam-aware promoted-host automation as the governed runtime broadens.

### Priority 2

1. Preserve `apps/field-surface` as a seed lane until field-runtime work proves a harder boundary.
2. Keep `apps/forms-studio` and `packages/api-contracts` explicitly deferred until their first real implementation packets land.
3. Keep current ownership and approval surfaces aligned with the real lane map as future re-home work lands.
4. if publication becomes necessary before cutover, use routine bounded parent-root staging for already-tracked paths, keep the first bootstrap publication handoff only as historical context, and treat wider subtree introduction as an explicit follow-on tranche.

### Priority 3

1. Reassess whether the merge-target marker lanes still add operational value after more re-home work closes.
2. Continue treating local deploy-worktree publication work as a separate bounded lane rather than workspace-shape evidence.

## Audit Outcome

The repo now has a governed and mostly credible top-level workspace shape.

The remaining workspace-cleanup problem is no longer missing ownership governance or missing deployment-map documentation. Those controls are now present.

The remaining work is narrower:

1. keep generated residue out of structural authority
2. keep deferred and retirement lanes clearly classified
3. continue bounded source-domain re-home into the active platform lanes without reopening broad topology drift
