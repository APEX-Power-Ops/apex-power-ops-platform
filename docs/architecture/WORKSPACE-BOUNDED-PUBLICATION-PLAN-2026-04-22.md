# Workspace Bounded Publication Plan

Date: 2026-04-22
Status: Active follow-on plan
Scope: deliberate introduction of the still-untracked portion of `C:/APEX Platform/apex-power-ops-platform`

## Purpose

The workflow and repo drift audit closed the stale bootstrap assumptions.

The remaining problem is different: most of `apex-power-ops-platform/` is still untracked at the parent git root, so publication now needs an explicit lane-by-lane introduction plan rather than another governance cleanup pass.

This document provides that bounded plan.

## Verified Inventory Baseline

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22:

- total untracked paths under `apex-power-ops-platform/`: 4483
- `.github`: 10
- `.gitignore`: 1
- `AGENTS.md`: 1
- `apps`: 307
- `archive`: 2516
- `docs`: 62
- `infra`: 46
- `knowledge`: 974
- `ops`: 508
- `package.json`: 1
- `packages`: 53
- `pnpm-lock.yaml`: 1
- `pnpm-workspace.yaml`: 1
- `pyproject.toml`: 1
- `tests`: 1

Interpretation:

1. the dominant untracked mass is not active runtime code; it is `archive/`, `knowledge/`, and parts of `ops/`
2. the code-bearing and operator-bearing lanes are much smaller and can be introduced deliberately without bundling the historical residue
3. the next publication tranche after the published Class A scaffold should separate recursive active-code admission from archival accumulation

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

- the scaffold and package-source steps are complete; the next bounded follow-on is recursive publication for the smallest app lane and its minimum supporting runtime surfaces

Current concrete artifact for that next step:

- `ops/agents/handoffs/2026-04-22-parent-root-operations-web-runtime-publication-handoff.md`

## Guardrails

1. do not use `git add -- apex-power-ops-platform/` for the next tranche
2. keep staging explicit to the intended packet paths
3. review each staged diff before commit from `C:/APEX Platform`
4. do not bundle `archive/` or `knowledge/` with active code-bearing publication
5. treat `ops/agents/handoffs/` as mixed content; introduce only the live authority subset unless a historical tranche is explicitly intended

## Completion Standard

This plan is satisfied for the next cycle when:

1. the published scaffold tranche introduced active platform shape without broad subtree staging
2. the tracked lane continues to expand through explicit packets rather than accidental archive or knowledge bulk introduction
3. the remaining untracked majority is reduced intentionally, not just documented