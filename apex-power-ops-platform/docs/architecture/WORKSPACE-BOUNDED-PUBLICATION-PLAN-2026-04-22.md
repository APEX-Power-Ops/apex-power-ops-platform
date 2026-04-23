# Workspace Bounded Publication Plan

Date: 2026-04-22
Status: Active follow-on plan
Scope: deliberate introduction of the still-untracked portion of `C:/APEX Platform/apex-power-ops-platform`

## Purpose

The workflow and repo drift audit closed the stale bootstrap assumptions.

The remaining problem is different: most of `apex-power-ops-platform/` is still untracked at the parent git root, so publication now needs an explicit lane-by-lane introduction plan rather than another governance cleanup pass.

This document provides that bounded plan.

## Verified Inventory Baseline

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the `pm-schema-004` draft publication:

- total untracked paths under `apex-power-ops-platform/`: 3897
- `apps`: 2
- `archive`: 2516
- `knowledge`: 974
- `ops`: 405

Interpretation:

1. the dominant untracked mass is not active runtime code; it is `archive/`, `knowledge/`, and parts of `ops/`
2. the remaining `apps` residue is generated local output and should stay excluded from publication packets
3. the next publication tranche should keep decomposing `ops/` into bounded packets rather than widening into the full lane

## Publication Classes

### Class A: Published scaffold tranche

These were the best candidates for the first deliberate follow-on publication packet because they define active platform shape, build boundaries, or execution lanes:

- `.github/`
- `.gitignore`
- `AGENTS.md`
- `apps/`
- `infra/`
- `package.json`
- `packages/`
- `pnpm-lock.yaml`
- `pnpm-workspace.yaml`
- `pyproject.toml`
- `tests/`

Rule:

- introduce these with explicit path staging only, not with whole-subtree staging

Rationale:

- these lanes carry the active runtime, package, CI, and operator-contract surface that should define the live platform lane before archival or lineage-heavy material is added

Publication result:

- this scaffold tranche was published on 2026-04-22 as commit `ebb75aa` on parent-root `clean-main`

### Class B: Selective authority-doc introduction

These paths should be introduced, but selectively rather than as a full-lane sweep:

- the authoritative current-state docs under `docs/`
- active operator runbooks that support the introduced code and runtime lanes
- only the current authority subset under `ops/` that is needed to operate or understand the live tracked slice

Rule:

- prefer explicit file lists or bounded doc packets instead of broad `docs/` or `ops/` staging

Rationale:

- `docs/` is manageable in size, but `ops/` contains a large historical handoff backlog that should not be silently promoted with active operating guidance

### Class C: Defer as historical or lineage-heavy material

These lanes should remain untracked until a dedicated archive or knowledge publication decision is made:

- `archive/`
- `knowledge/`
- historical bulk under `ops/agents/handoffs/`
- any lineage-heavy documentation packets that are not required to operate the active tracked slice

Rule:

- do not mix these lanes into the next active runtime or governance tranche

Rationale:

- they dominate the current untracked count and would drown the review surface without improving immediate runtime or operator clarity

### Class D: Keep out of topology decisions

These are not publication tranches; they are discipline rules:

- continue excluding generated or workstation-local residue through ignore rules
- only widen the parent-root `.gitignore` when root-level operator noise appears again
- do not treat parked worktrees as evidence that a lane is already introduced in the live root

## Recommended Execution Order

1. introduce the root manifests and active platform lane scaffolds from Class A
2. introduce active runtime and package lanes from Class A in bounded packets
3. introduce the current authority docs and minimal active ops guidance from Class B
4. leave Class C untouched until there is an explicit archive or knowledge publication decision

Current concrete artifact for the completed scaffold step:

- `ops/agents/handoffs/2026-04-22-parent-root-class-a-scaffold-publication-handoff.md`

Current next-step interpretation:

- the scaffold, package-source, active app-lane runtime/support/test steps, shared package-source steps, the residual scaffold/doc step, the `infra` database step, the `docs` step, the `ops/knowledge-control-plane/registry` step, the `ops/agents/legacy-governance` step, the `ops/knowledge-resource-operations` step, the forms-import draft pair, the closed `001af` draft, the `apex-unification-001` draft pair, the `knowledge-import-001` draft pair, the `pm-schema-009` draft family, the `pm-schema-010` draft trio, the `pm-schema-011` dependency-activation family, the `pm-schema-012` identity and joined-read family, the `pm-schema-013` work-package write family, the `pm-schema-014` task-write pair, the `pm-schema-015` assignment-write pair, the `pm-schema-016` dependency-write singleton, the `pm-schema-017` execution-issue-write singleton, the `pm-schema-018` progress-snapshot-write singleton, the `pm-schema-019` write-surface consolidation singleton, the `pm-schema-019f` durable DB-backed idempotency store singleton, the `pm-schema-019g` idempotency sweep and ops metrics singleton, the `pm-schema-019h` sweep schedule wiring singleton, the `pm-schema-019i` idempotency by-route ops breakdown singleton, the `pm-schema-019j` ops metrics export schedule scrape singleton, the `pm-schema-019k` ops metrics threshold evaluation singleton, the `pm-schema-ui-002g` comparative schedule analytics read surface and host validation singleton, the `pm-schema-ui-002g` host-variance shell wiring and browser validation singleton, the `pm-schema-ui-002e-host` drivers shell wiring and browser validation singleton, the `pm-schema-ui-002f-host` tracer shell wiring and browser validation singleton, the `pm-schema-ui-001` field apparatus workflow prototype design singleton, the `pm-schema-ui-002` gantt layer comparison decision singleton, the `pm-schema-ui-003` PM approval queue prototype design singleton, the `pm-schema-ui-004` lead operations surface prototype design singleton, the `pm-schema-ui-005` cross-surface integration spec singleton, the `pm-schema-ui-006` mutation seam API spec and implementation scaffold singleton, the `pm-schema-ui-001a` field apparatus workflow and seam co-implementation singleton, the `pm-schema-ui-001b` lead operations surface and extended seam wiring singleton, the `pm-schema-ui-001c` PM approval queue and cross-surface review flow implementation singleton, the `pm-schema-ui-001d` cross-surface integration test surface and validation harness singleton, the `pm-schema-ui-001e` Supabase read model and mutation store migration singleton, the `pm-schema-ui-002a` P6 schedule context import and read bridge implementation singleton, the `pm-schema-ui-002b` read-only Gantt prototype implementation singleton, the `pm-schema-ui-002c` baseline overlay and read-model hardening singleton, the `pm-schema-ui-002d` baseline overlay re-issue and read-bridge extension singleton, the `pm-schema-ui-002e` schedule drivers read surface and host validation singleton, the `pm-schema-ui-002f` schedule tracer read surface and host validation singleton, the `pm-schema-001` entity field candidate matrix singleton, the `pm-schema-002` lifecycle and state model singleton, the `pm-schema-003` P6 integration boundary spec singleton, the `pm-schema-004` apparatus execution bridge spec singleton, the `pm-schema-020a` baseline field authority promotion singleton, the `pm-schema-020b` XER baseline mapping authorization singleton, the `pm-schema-020c` persisted schedule baseline DDL and loader lane singleton, the `pm-schema-020d` P6 baseline XER parser and loader wiring singleton, the `pm-schema-020e` internal baseline capture planning singleton, the `pm-schema-020f` real XER host parser verification and golden fixture admission singleton, the `pm-schema-020e.1` loader working-copy restoration and integrity gate singleton, the `pm-schema-020g-a` parser-surface reconciliation and baseline shim singleton, the `pm-schema-020g-b` governed baseline companion JSON path singleton, the `pm-schema-020e.2` parser-test reauthoring singleton, and the `pm-schema-020h` concrete sanitized golden fixture admission singleton are complete; the next bounded follow-on is `pm-schema-005` because it is the adjacent review-gate and SQL-readiness checklist packet in the residual foundational PM family, it stages cleanly as a single-file singleton, and the cross-family alternatives still widen immediately into physical archive or knowledge movement

Current concrete artifact for that next step:

- `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-005-draft-publication-handoff.md`

## Guardrails

1. do not use `git add -- apex-power-ops-platform/` for the next tranche
2. keep staging explicit to the intended packet paths
3. review each staged diff before commit from `C:/APEX Platform`
4. do not bundle `archive/` or `knowledge/` with active code-bearing publication
5. treat `ops/agents/handoffs/` as mixed content; introduce only the live authority subset unless a historical tranche is explicitly intended
6. prefer the smallest coherent `ops/` sublane rather than broad `ops/` publication when a cleaner packet exists

## Completion Standard

This plan is satisfied for the next cycle when:

1. the published scaffold tranche introduced active platform shape without broad subtree staging
2. the tracked lane continues to expand through explicit packets rather than accidental archive or knowledge bulk introduction
3. the remaining untracked majority is reduced intentionally, not just documented