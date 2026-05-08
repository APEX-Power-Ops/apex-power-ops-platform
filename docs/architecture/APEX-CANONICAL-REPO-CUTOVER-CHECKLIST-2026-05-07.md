# APEX Canonical Repo Cutover Checklist

Date: 2026-05-07
Status: Active closeout checklist after canonical cutover promotion
Scope: auditable checklist for converting `apex-power-ops-platform/` from target root into the canonical git root and retiring `C:/APEX Platform` as the durable publication boundary

## Purpose

This checklist is the execution gate for repo-boundary cutover.

It exists to prevent two failure modes:

1. treating cutover as a vague aspiration instead of a controlled engineering event,
2. flattening mixed parent-root residue into the permanent repo shell during the move.

## Success Condition

Cutover is complete only when all of the following are true:

1. `apex-power-ops-platform/` is the canonical git root,
2. GitHub points at that canonical root rather than the mixed parent root,
3. `/home/olares/code/apex` mirrors the canonical repo root directly,
4. parent-root authority files are either re-homed, archived, or explicitly retired,
5. the default operator and validation workflow no longer assumes parent-root git.

## Non-Negotiable Rules

1. GitHub remains canonical throughout cutover.
2. Olares remains the durable development anchor.
3. The cutover must not import workstation-local, secret, cache, or binary-heavy residue into the permanent repo shell.
4. The old observe-only clone at `/home/olares/src/apex-power-ops-platform` stays non-canonical.
5. No destructive cleanup happens until replacement authority and validation paths are already proven.

## Entry Criteria

Do not execute the actual cutover until these are satisfied:

1. The repo-foundation authority exists in `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`.
2. The parent-root classification matrix exists in `docs/architecture/APEX-PARENT-ROOT-CLASSIFICATION-MATRIX-2026-05-07.md`.
3. Live authority surfaces still outside the repo have a relocation plan.
4. The disposition of parent-root `services/` is decided in `docs/architecture/APEX-SERVICES-AND-ROOT-RESIDUE-DECISION-2026-05-07.md`.
5. The canonical repo root contains the documents and automation required for day-to-day operation.
6. The execution event is defined in `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-EXECUTION-PACKET-2026-05-07.md`.
7. The post-cutover workflow and ignore retirement event is defined in `docs/architecture/APEX-PARENT-ROOT-WORKFLOW-AND-IGNORE-RETIREMENT-PACKET-2026-05-07.md`.
8. The preflight evidence and remote-target reconciliation state are recorded in `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-PREFLIGHT-EVIDENCE-2026-05-07.md`.
9. The canonical target-repo mapping is defined in `docs/architecture/APEX-REMOTE-TARGET-RECONCILIATION-DECISION-2026-05-07.md`.

## Current Closeout Notes

The git-boundary cutover itself is now materially complete.

Current closeout state:

1. standalone git boundaries now exist at both `C:/APEX Platform/apex-power-ops-platform` and `/home/olares/code/apex/apex-power-ops-platform`,
2. canonical `clean-main` now points at subtree-root commit `dd781695006f159f204ab20eaa20adf5e296772c` in `jasonlswenson-sys/apex-power-ops`,
3. default operator tasks, runbooks, and git examples now point at the standalone repo root,
4. parent-root workflow and ignore surfaces are now demoted to mirror or umbrella residue rather than active publication dependencies,
5. Packet 099 now records focused post-cutover proof from the canonical repo boundary: `corepack pnpm check`, repo-local calc-engine pytest, `@apex/operations-web` production build, and fresh old-clone observation all ran without reopening parent-root helpers or mutating the historical clone,
6. the remaining work is residual lane-by-lane authority relocation, demotion, and retirement rather than git-boundary proof.

## Phase 1: Freeze The Parent Root

- [ ] Stop creating new live authority only at `C:/APEX Platform`.
- [ ] Treat parent-root staging as temporary migration debt, not normal steady-state workflow.
- [ ] Confirm all new repo-structure decisions are authored under `apex-power-ops-platform/docs/architecture/`.
- [ ] Confirm the active status surface records repo cutover as a live top-priority lane.

## Phase 2: Re-home Live Authority

- [ ] Reconcile `Platform-Authority/` and promote surviving active documents into repo-owned `docs/authority/` or `docs/architecture/`.
- [ ] Reconcile `Infrastructure/` and promote surviving active Olares governance and operator docs into repo-owned docs or infra lanes.
- [x] Decide whether active parent-root `PROJECT_STATUS.md` and `PROJECT_OVERVIEW.md` become repo-root files or repo-doc mirrors.
- [ ] Split current versus historical `.claude/` guidance so only the surviving active continuity surfaces remain in the canonical repo.
- [ ] Mark superseded parent-root authority documents as historical or retire them after verification.

## Phase 3: Reconcile Ambiguous Root Residue

- [x] Decide the final disposition of parent-root `services/`.
- [ ] Reconcile any still-active parent-root `apps/` or `packages/` residue lane-by-lane.
- [ ] Confirm `Documentation/`, `Supabase/`, `spec/`, and `Reference_Files/` will not be imported wholesale.
- [ ] Confirm `APEX_Schema_V2/` remains reviewed input, not active runtime authority.
- [ ] Confirm binary-heavy and workstation-local material remain outside the canonical repo boundary.

## Phase 4: Prepare The Canonical Repo Root

- [ ] Ensure the canonical repo root contains the full active authority chain.
- [x] Ensure the canonical repo root contains the default workspace entrypoint.
- [x] Ensure repo-root README and operator guidance no longer describe the repo as transitional bootstrap.
- [x] Ensure root tasks, validation commands, and runbooks no longer require parent-root git assumptions.
- [x] Ensure `.github/` workflows needed for active lanes are present under the canonical repo.
- [x] Retire or deliberately mirror the remaining parent-root publishable `.github/workflows` lane after git-boundary cutover makes repo-owned workflows executable by default.

### Phase 5: Execute Git-Boundary Cutover

- [x] Create the canonical standalone git boundary for `apex-power-ops-platform/`.
- [x] Preserve required lineage from the parent-root history in a governed way.
- [x] Update the canonical remote flow so normal status, diff, branch, and publication happen from the repo root.
- [x] Rebuild or reattach the Olares host mirror against the canonical repo boundary.
- [x] Verify that the parent root is now workstation umbrella only and no longer the publication boundary.

## Phase 6: Validate Post-Cutover Operation

- [x] Verify the canonical repo can run its bounded lint, test, build, and documentation workflow without parent-root helpers.
- [x] Verify Olares host parity against the canonical repo root.
- [x] Verify default operator onboarding now starts from the canonical repo root.
- [x] Verify parent-root only files no longer act as hidden dependencies.
- [x] Verify old-clone observe-only posture remains intact.

Phase 6 evidence recorded in Packet 099:

1. `corepack pnpm check` now passes from `C:/APEX Platform/apex-power-ops-platform` after repairing the canonical root `check` script to use corepack-backed nested invocation.
2. `c:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe -m pytest packages/calc-engine/tests/test_golden_fixtures.py` passes with `9 passed, 1 skipped`.
3. `corepack pnpm --filter @apex/operations-web build` passes and emits the promoted PM routes from the canonical repo boundary.
4. `/home/olares/src/apex-power-ops-platform` remains observe-only at `2836a2622309b4e146ca24f23b5bf87312c0c857` with status count `30`.

## Required Evidence To Record

When the actual cutover executes, the closing packet must record:

1. pre-cutover and post-cutover git roots,
2. canonical remote target and branch evidence,
3. Olares host mirror pre/post state,
4. old-clone preserved state,
5. list of authority files re-homed or retired,
6. validation commands run from the new canonical repo boundary,
7. explicit confirmation that excluded parent-root lanes were not silently absorbed.

## No-Go Conditions

Do not execute cutover if any of the following remain true:

1. active authority still depends on parent-root-only files with no relocation plan,
2. `services/` or other ambiguous top-level residues still lack disposition,
3. operator runbooks and tasks still require parent-root git as the default contract,
4. Olares parity for the new repo boundary has not been planned,
5. the cutover would require flattening archives, secrets, caches, or binary-heavy holdings into the canonical repo,
6. the preflight evidence still shows a remote-target mismatch and the cutover is not following the mapping defined in `docs/architecture/APEX-REMOTE-TARGET-RECONCILIATION-DECISION-2026-05-07.md`,
7. the cutover plan still assumes a direct attach to the current parent-root-shaped `clean-main` tree instead of a subtree-rooted history step.

## Immediate Next Outputs

This checklist assumes the next adjacent repo-structure artifacts are:

1. a live authority relocation plan for parent-root docs that still matter,
2. a `services/` reconciliation decision, now started in `docs/architecture/APEX-SERVICES-AND-ROOT-RESIDUE-DECISION-2026-05-07.md`,
3. a repo-first workspace entrypoint decision, now started in `docs/architecture/APEX-WORKSPACE-ENTRYPOINT-DECISION-2026-05-07.md`,
4. the recorded cutover execution packet at `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-EXECUTION-PACKET-2026-05-07.md`.
5. the recorded parent-root workflow and ignore retirement packet at `docs/architecture/APEX-PARENT-ROOT-WORKFLOW-AND-IGNORE-RETIREMENT-PACKET-2026-05-07.md`.