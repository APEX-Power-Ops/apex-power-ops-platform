# Workspace Lane Normalization Checklist

Date: 2026-04-22
Status: Active execution checklist
Scope: `C:/APEX Platform/apex-power-ops-platform`

## Purpose

This checklist converts the current workspace audit into bounded execution work.

Use it to:

1. normalize merge-target and deferred lanes without reopening broad workspace discovery
2. keep source-domain re-home aligned to the current platform lane model
3. preserve operator clarity while the repo is still in bootstrap-to-canonical transition

This document is intentionally narrower than the audit and more concrete than the roadmap.

## Authority Position

Use these documents together:

1. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md` -> structure and cleanup baseline
2. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md` -> active status snapshot
3. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md` -> execution checklist for lane cleanup and re-home follow-through
4. `docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md` -> sequencing surface

## Execution Rules

1. Do not reopen broad top-level topology debates while this checklist is active.
2. Do not place new implementation work in marker-only retirement lanes.
3. Do not activate deferred lanes without a bounded owning packet.
4. Do not treat generated roots as part of governed workspace shape.
5. Do not let deploy-worktree publication residue drive active repo structure decisions.

## Lane Classes In Scope

### Marker-only retirement residue

- `apps/integration-surface`
- `apps/lead-surface`
- `apps/pm-surface`

### Deferred placeholders

- `apps/forms-studio`
- `packages/api-contracts`

### Seed lane

- `apps/field-surface`

### Active destination lanes affected by re-home follow-through

- `apps/control-plane-api`
- `apps/mutation-seam`
- `apps/operations-web`
- `packages/calc-engine`
- `packages/forms-engine`
- `infra/database`
- `docs/authority`
- `knowledge/`
- `ops/`

## Checklist

### 1. Marker-only retirement lanes

#### `apps/integration-surface`

- [ ] confirm the lane still contains marker-only guidance and no new runtime assets
- [ ] keep the README explicit that Python harness work lives in `apps/mutation-seam`
- [ ] keep the README explicit that browser-facing residue lives in `apps/operations-web`
- [ ] reject any new implementation landing here unless a hard standalone runtime boundary is proven
- [ ] reassess marker retirement only after the surrounding active-lane proofs are stable

Exit condition:

- the lane remains explanation-only or is explicitly retired by a separate authority decision

#### `apps/lead-surface`

- [ ] confirm the lane remains marker-only with no revived prototype assets
- [ ] keep the marker tied to the re-home target under `apps/operations-web`
- [ ] reject any new lead-facing browser code here unless a separate deployment boundary is proven
- [ ] reassess marker retirement only after the lead-facing surface in `apps/operations-web` is operationally stable

Exit condition:

- the lane stays marker-only or is retired by explicit authority, but it does not drift back into use

#### `apps/pm-surface`

- [ ] confirm the lane remains marker-only after PM browser slice re-home
- [ ] keep the marker tied to the active PM review and approval surfaces now living in `apps/operations-web`
- [ ] reject new PM browser implementation work here unless a hard deployment boundary is proven
- [ ] reassess marker retirement only after the operations-web PM tranche is stable and fully documented

Exit condition:

- the lane stays marker-only or is retired explicitly, with no silent browser residue growth

### 2. Deferred placeholder lanes

#### `apps/forms-studio`

- [ ] keep the lane marker explicit that activation is deferred
- [ ] do not add speculative browser scaffolding
- [ ] activate only when a bounded forms browser app-shell packet is approved
- [ ] keep re-home pressure flowing into `packages/forms-engine` until that trigger is met

Exit condition:

- the lane remains clearly deferred or receives its first approved app-shell slice

#### `packages/api-contracts`

- [ ] keep the lane marker explicit that activation is deferred
- [ ] do not add speculative shared-contract scaffolding
- [ ] activate only when more than one active surface proves durable contract reuse
- [ ] prefer keeping current contracts near their owning active surfaces until reuse is real

Exit condition:

- the lane remains clearly deferred or receives its first approved shared-contract slice

### 3. Seed lane preservation

#### `apps/field-surface`

- [ ] keep the lane framed as a seed, not as an abandoned shell
- [ ] do not force a rename while field-runtime boundaries are still unproven
- [ ] allow bounded field-runtime work to land only if it strengthens the case for a real runtime surface
- [ ] reassess the lane name only when field-runtime deployment and operator flows are concrete

Exit condition:

- the lane remains a legitimate seed or graduates through a separate authority decision

### 4. Active destination lane discipline

#### `apps/operations-web`

- [ ] keep absorbing lead and PM browser concerns unless a hard deployment split is proven
- [ ] keep route, smoke, and promoted-host proof aligned with the re-homed surface set
- [ ] update local lane markers elsewhere whenever a re-home into this lane closes another residue path

#### `apps/mutation-seam`

- [ ] keep Python validation or mutation harness work here rather than rehydrating `apps/integration-surface`
- [ ] reject new integration-lane drift that belongs in this lane

#### `apps/control-plane-api`

- [ ] keep backend runtime expansion here rather than creating adjacent app lanes for narrow slices
- [ ] preserve the migration authority split between `supabase/migrations/` and legacy utilities

#### `packages/forms-engine`

- [ ] continue bounded NETA Forms re-home here until a real forms-studio app shell is justified

#### `packages/calc-engine`

- [ ] continue bounded calc extraction here instead of creating sidecar package sprawl

Exit condition:

- new implementation lands in active platform lanes instead of reviving transitional ones

### 5. Source-domain re-home control

- [ ] keep extracting from sibling source repos in bounded slices only
- [ ] route implementation slices into existing active platform lanes first
- [ ] route archive-heavy or lineage-heavy material into `archive/`, `docs/`, `knowledge/`, or `ops/` instead of runtime lanes
- [ ] preserve lineage traceability when re-homing source material

Exit condition:

- source-domain work reduces default dependency on sibling repos without creating new top-level drift

### 6. Generated-root discipline

- [ ] keep `.venv/`, `node_modules/`, `.pytest_cache/`, and pytest cache artifacts out of topology decisions
- [ ] avoid docs or tasks that assume workstation residue is present as a governed lane
- [ ] extend ignore coverage only when a genuinely new residue class appears

Exit condition:

- workstation residue remains bounded and non-authoritative

### 7. Git publication boundary

- [x] keep git status, diff, stage, and commit decisions aligned to the current parent repo root at `C:/APEX Platform`
- [x] do not assume `apex-power-ops-platform/` is already an independent git repository
- [x] acknowledge that the first bounded platform tranche is now tracked at the parent root, so normal diff-based packet publication against `HEAD` is available again for already-introduced paths
- [x] establish a bounded classification baseline for the still-untracked majority of the subtree in `docs/architecture/WORKSPACE-BOUNDED-PUBLICATION-PLAN-2026-04-22.md`
- [x] define the post-Class-A recursive package-source follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-package-source-publication-handoff.md`
- [x] define the post-package operations-web runtime follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-operations-web-runtime-publication-handoff.md`
- [x] define the post-operations-web mutation-seam runtime follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-mutation-seam-runtime-publication-handoff.md`
- [x] define the post-mutation-seam control-plane core follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-control-plane-core-publication-handoff.md`
- [x] define the post-control-plane-core support follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-control-plane-support-publication-handoff.md`
- [x] define the post-control-plane-support test follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-control-plane-tests-publication-handoff.md`
- [x] define the post-control-plane residual scaffold/doc follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-residual-scaffold-publication-handoff.md`
- [x] define the post-residual infra-database follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-infra-database-publication-handoff.md`
- [x] define the post-infra docs follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-docs-publication-handoff.md`
- [x] define the post-docs ops knowledge-control-plane registry follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-ops-knowledge-control-plane-registry-publication-handoff.md`
- [x] define the post-registry ops legacy-governance follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-ops-legacy-governance-publication-handoff.md`
- [x] define the post-legacy-governance ops knowledge-resource-operations follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-ops-knowledge-resource-operations-publication-handoff.md`
- [x] define the post-knowledge-resource-operations forms-import draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-forms-import-draft-publication-handoff.md`
- [x] define the post-forms-import `001af` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-001af-draft-publication-handoff.md`
- [x] define the post-`001af` apex-unification `001` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-apex-unification-001-draft-publication-handoff.md`
- [x] define the post-apex-unification `001` knowledge-import `001` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-knowledge-import-001-draft-publication-handoff.md`
- [x] define the post-knowledge-import `001` pm-schema `009` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-009-draft-publication-handoff.md`
- [x] define the post-pm-schema `009` pm-schema `010` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-010-draft-publication-handoff.md`
- [x] define the post-pm-schema `010` pm-schema `011` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-011-draft-publication-handoff.md`
- [x] define the post-pm-schema `011` pm-schema `012` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-012-draft-publication-handoff.md`
- [x] define the post-pm-schema `012` pm-schema `013` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-013-draft-publication-handoff.md`
- [x] define the post-pm-schema `013` pm-schema `014` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-014-draft-publication-handoff.md`
- [x] define the post-pm-schema `014` pm-schema `015` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-015-draft-publication-handoff.md`
- [x] define the post-pm-schema `015` pm-schema `016` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-016-draft-publication-handoff.md`
- [x] define the post-pm-schema `016` pm-schema `017` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-017-draft-publication-handoff.md`
- [x] define the post-pm-schema `017` pm-schema `018` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-018-draft-publication-handoff.md`
- [x] define the post-pm-schema `018` pm-schema `019` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019-draft-publication-handoff.md`
- [x] define the post-pm-schema `019` pm-schema `019f` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019f-draft-publication-handoff.md`
- [x] define the post-pm-schema `019f` pm-schema `019g` draft follow-on packet in `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019g-draft-publication-handoff.md`
- [ ] default future publication work to explicit platform file paths or bounded packet pathspecs rather than whole-subtree staging
- [ ] reserve `git add -- apex-power-ops-platform/` for explicit cutover or intentionally broad publication work only
- [ ] treat unrelated tracked changes elsewhere under `C:/APEX Platform` as separate lanes unless a cross-lane operation is explicitly intended

Exit condition:

- future git publication work can isolate already-introduced platform paths from unrelated parent-repo changes while still using normal diff-based review against tracked `HEAD`, and broader subtree introduction remains deliberate

### 8. Deploy-worktree separation

- [ ] keep `C:/APEX Platform/apex-power-ops-platform-deploy-worktree` treated as a separate publication or reconciliation lane
- [ ] do not use that lane as evidence that hosted packet `001af` has reopened
- [ ] treat any later deploy-worktree handoff as a separate follow-on artifact rather than assuming it is already bundled inside this bootstrap packet

Exit condition:

- active repo normalization stays decoupled from deploy-worktree residue

## Recommended Execution Order

1. verify marker-only lanes stay marker-only
2. keep deferred lanes deferred and explicit
3. preserve `apps/field-surface` as a seed lane
4. keep future git publication work scoped to the parent-root boundary without broad staging
5. continue active-lane re-home into `apps/operations-web`, `apps/mutation-seam`, `apps/control-plane-api`, and the active packages
6. continue bounded source-domain re-home
7. reassess marker retirement only after active-lane proofs stabilize

## Completion Standard

This checklist is complete for the current cycle when:

1. no marker-only lane has resumed ungoverned implementation use
2. no deferred lane has been activated speculatively
3. active re-home work continues to land in governed destination lanes
4. generated roots remain excluded from workspace-shape authority
5. future git publication work remains isolatable from unrelated parent-repo changes while using routine bounded staging against tracked `HEAD` for already-introduced paths and deliberate introduction for wider subtree material
6. deploy-worktree residue remains separated from active repo normalization