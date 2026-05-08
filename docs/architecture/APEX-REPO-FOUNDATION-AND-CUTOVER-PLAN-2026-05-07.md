# APEX Repo Foundation And Cutover Plan

Date: 2026-05-07
Status: Executed cutover baseline with residual structure-governance tracking
Scope: canonical repository target, cutover rules, MVP structure, optimal structure, and execution sequence for retiring the parent-root transitional boundary

Closeout interpretation note:

The standalone repo-boundary cutover is now complete. This document remains the governing repo-foundation baseline for structure and residue-retirement questions, but it is no longer a pre-cutover launch plan.

Current routing:

1. use `PROJECT_STATUS.md` for current sequencing and the latest completed residue slices,
2. use `docs/architecture/APEX-CANONICAL-REPO-CUTOVER-CHECKLIST-2026-05-07.md` for the recorded cutover completion criteria and proof baseline,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the current closeout queue on remaining boundary residue.

## Purpose

This document preserves the repo-foundation decision that made repository structure the top-priority platform concern and records the structural rule that governed cutover.

It converts the earlier topology recommendation, bootstrap staging language, and Olares workspace migration posture into the structural rule that now governs post-cutover residue retirement:

The final durable repo must be `apex-power-ops-platform` itself, not the mixed parent root at `C:/APEX Platform`.

Use this document when the question is:

1. what the canonical repo boundary should be,
2. which folders belong inside the active repo versus outside it,
3. what MVP repo structure is required now,
4. what the optimal structure should become,
5. how to cut over from the current parent-root git boundary without dragging legacy clutter into the permanent shell.

## Governing Decision

Repo structure is now the highest-leverage active platform priority.

The current parent-root publication model solved short-term consolidation, but it is not acceptable as the permanent operating model because it mixes:

1. active implementation,
2. strategic authority,
3. historical archives,
4. workstation residue,
5. binary-heavy reference material,
6. unrelated publication drift.

The repo must be redesigned around the product and operating model, not around the accident of the current filesystem history.

## Canonical Target

### Final git root

The intended long-term git root is:

`apex-power-ops-platform/`

The parent folder `C:/APEX Platform` should remain a workstation umbrella, not the durable repo boundary.

### Parent umbrella after cutover

After cutover, `C:/APEX Platform` should contain only:

1. the canonical repo checkout,
2. source-domain extraction lanes that are intentionally external,
3. machine-local archives and reference holdings,
4. local-only tooling state that does not belong in the repo.

It must not remain the place where canonical project authority, commits, and publication boundaries are decided.

## MVP Repo Shape

The MVP repo shape should be the smallest structure that cleanly supports current delivery, Olares-hosted development, and future growth without another topology reset.

```text
apex-power-ops-platform/
├── apps/
├── packages/
├── infra/
├── ops/
├── knowledge/
├── docs/
├── tools/
├── tests/
├── archive/
├── .github/
├── .vscode/
├── package.json
├── pnpm-workspace.yaml
├── pyproject.toml
└── README.md
```

### MVP rules

1. Deployable runtimes belong in `apps/`.
2. Reusable code belongs in `packages/`.
3. Executable database and environment assets belong in `infra/`.
4. Agent packets, handoffs, runbooks, and operator workflow surfaces belong in `ops/`.
5. Curated knowledge assets, manifests, mappings, and standards belong in `knowledge/`.
6. Human authority and architectural documentation belong in `docs/`.
7. Repeatable repo-owned operator scripts belong in `tools/`.
8. Cross-app or repo-level validation belongs in `tests/`.
9. Historical material belongs in `archive/` and is non-authoritative by default.

## Optimal Repo Shape

The optimal repo shape extends the MVP without changing the root contract.

```text
apex-power-ops-platform/
├── apps/
│   ├── operations-web/
│   ├── control-plane-api/
│   ├── forms-studio/
│   ├── field-app/
│   └── knowledge-console/
├── packages/
│   ├── api-contracts/
│   ├── calc-engine/
│   ├── forms-engine/
│   ├── domain-model/
│   ├── ui-system/
│   ├── automation-sdk/
│   └── shared-config/
├── infra/
│   ├── database/
│   ├── deployment/
│   ├── environments/
│   ├── storage/
│   └── search/
├── ops/
│   ├── agents/
│   ├── runbooks/
│   ├── workflows/
│   └── monitoring/
├── knowledge/
│   ├── standards/
│   ├── extractions/
│   ├── question-bank/
│   ├── mappings/
│   └── manifests/
├── docs/
│   ├── authority/
│   ├── architecture/
│   ├── product/
│   ├── operations/
│   └── decisions/
├── tools/
├── tests/
├── archive/
│   ├── legacy-repos/
│   ├── historical-exports/
│   ├── superseded-docs/
│   └── deprecated-loaders/
└── assets/
    ├── branding/
    ├── templates/
    ├── diagrams/
    └── generated/
```

## Explicit Anti-Patterns To Retire

The following must not define the permanent repo model:

1. root-level `Documentation/`, `Supabase/`, `Platform-Authority/`, and `APEX_Schema_V2/` remaining outside the active repo while still carrying live authority,
2. the repo README describing the active implementation root as only a bootstrap scaffold,
3. parent-root git staging discipline being normal daily operating posture,
4. mixed active and historical artifacts sharing one authority layer,
5. top-level `services/` acting as an ambiguous second application namespace,
6. binary-heavy reference holdings and scratch outputs living near active code and docs,
7. old workspace entrypoints or stale coordination paths acting as accidental authority.

## Classification Rules

### Must live inside the canonical repo

1. active apps,
2. active packages,
3. active infra and migration code,
4. active authority docs,
5. active runbooks and operator workflows,
6. curated active knowledge assets,
7. repo-owned tests and tools.

### Must live outside the canonical repo

1. secrets,
2. runtime data,
3. local caches,
4. heavy reference libraries that are not required for daily engineering,
5. scratch exports,
6. obsolete session artifacts,
7. old repo snapshots except where intentionally archived in a governed lightweight form.

### Needs explicit lane-by-lane reconciliation

1. `services/` in the current repo root,
2. root-level authority outside `apex-power-ops-platform/`,
3. `Documentation/`, `Supabase/`, `spec/`, and `Reference_Files/` at the parent root,
4. `source-domains/` holdings that still feed active imports,
5. `.claude/` continuity surfaces that are partly current and partly historical residue.

## Cutover Rules

### MVP cutover objective

The first required cutover is not a broad content migration. It is a boundary cutover:

1. make `apex-power-ops-platform/` the canonical git root,
2. demote `C:/APEX Platform` to workstation umbrella status,
3. move live repo authority references inside the repo,
4. leave source-domain and archive holdings outside the canonical repo unless deliberately promoted.

### Cutover invariants

1. GitHub remains canonical.
2. Olares remains the durable development anchor.
3. `/home/olares/code/apex` should mirror the canonical repo boundary that survives cutover.
4. The old observe-only clone at `/home/olares/src/apex-power-ops-platform` remains non-canonical.
5. No cutover step is allowed to flatten archives, binaries, or machine-local residue into the permanent repo shell.

## Execution Sequence

### Phase 1: Freeze the authority boundary

1. stop adding new live authority to parent-root-only folders,
2. point active docs to this repo-first plan,
3. treat the parent-root publication boundary as temporary migration debt.

### Phase 2: Build the classification map

1. classify every top-level parent-root folder as one of:
   - promote into repo,
   - keep outside as source lane,
   - keep outside as workstation-local,
   - archive,
   - delete after verification,
2. identify every live authority document still outside the repo,
3. identify every ambiguous active lane still using placeholder or bootstrap language.

### Phase 3: Prepare the repo-root cutover

1. ensure the repo root contains the full authority chain needed for daily operation,
2. ensure root workspace entrypoints and tasks open from the canonical repo,
3. ensure validation, lint, test, and publication commands no longer assume parent-root git.

### Phase 4: Execute git-boundary cutover

1. create the canonical standalone repo boundary around `apex-power-ops-platform/`,
2. preserve parent-root history as workstation lineage or governed archive,
3. restore Olares host parity against the new canonical root,
4. retire the parent-root publication workflow.

### Phase 5: Post-cutover hardening

1. remove stale bootstrap language,
2. remove obsolete multi-root residue from the default workflow,
3. enforce path-scoped CI from the canonical repo root,
4. continue lane-by-lane source-domain re-home without reopening topology debates.

## Immediate Program Priority

The initial setup outputs below are now in place. The next active repo-structure work should focus on the remaining cutover-only blockers:

1. standalone git-boundary execution readiness so `apex-power-ops-platform/` can become the real git root,
2. root tasks, validation commands, and operator runbooks that still assume parent-root git,
3. retirement or deliberate mirroring of the remaining parent-root publishable surfaces such as `.github/workflows/` and `.gitignore`,
4. Olares host reattachment and parity proof against the standalone canonical repo root,
5. governed lineage preservation so cutover does not sever required parent-root history.

The foundational outputs already established are:

1. a full folder classification matrix for `C:/APEX Platform`, now started in `docs/architecture/APEX-PARENT-ROOT-CLASSIFICATION-MATRIX-2026-05-07.md`,
2. a canonical repo-boundary cutover checklist, now started in `docs/architecture/APEX-CANONICAL-REPO-CUTOVER-CHECKLIST-2026-05-07.md`,
3. a live authority relocation plan for parent-root docs that still matter, now started in `docs/architecture/APEX-AUTHORITY-RELOCATION-PLAN-2026-05-07.md`,
4. a `services/` and root-residue reconciliation decision so the target root contract is unambiguous, now started in `docs/architecture/APEX-SERVICES-AND-ROOT-RESIDUE-DECISION-2026-05-07.md`,
5. a repo-first workspace entrypoint decision, now started in `docs/architecture/APEX-WORKSPACE-ENTRYPOINT-DECISION-2026-05-07.md`.

## Success Standard

This repo-structure priority is complete only when:

1. `apex-power-ops-platform/` is the canonical git root,
2. Olares mirrors that root directly,
3. the parent `C:/APEX Platform` folder is no longer the publication boundary,
4. active authority no longer depends on root-level folders outside the canonical repo,
5. archive, source-lane, and workstation-local material are clearly separated from active engineering surfaces.