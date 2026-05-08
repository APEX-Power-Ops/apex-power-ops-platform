# APEX Authority Relocation Plan

Date: 2026-05-07
Status: Executed relocation bridge with residual mirror-demotion tracking
Scope: relocate surviving parent-root authority into the canonical `apex-power-ops-platform/` repo boundary without importing unrelated residue

Closeout interpretation note:

This plan records the relocation bridge that governed cutover and the first authority re-home phases. It now functions as a closeout map for remaining mirror-demotion and provenance residue rather than as a pre-cutover migration launch surface.

Current routing:

1. use `PROJECT_STATUS.md` for the current ordered residue queue,
2. use `docs/authority/README.md` for the current authority chain,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining closeout queue on boundary residue.

## Purpose

This plan defines which parent-root authority documents still matter, where they belong inside the canonical repo, and what should happen to each one during cutover.

It is the missing bridge between:

1. the repo-foundation decision,
2. the parent-root classification matrix,
3. the canonical repo cutover checklist.

## Relocation Rule

No parent-root document should remain active authority by accident.

Each surviving parent-root authority surface must end in one of five states:

1. moved into the canonical repo,
2. mirrored into the canonical repo with the parent copy demoted,
3. summarized and superseded by a repo-owned authority doc,
4. archived as historical input,
5. retired after verification.

## Highest-Priority Relocation Set

These were the first authority dependencies that had to be resolved before actual repo-boundary cutover and now serve as recorded closeout state.

| Current source | Current role | Target inside canonical repo | Planned action |
| --- | --- | --- | --- |
| `Platform-Authority/PLATFORM-UNIFICATION-MASTER-AUTHORITY-2026-04-12.md` | master strategic unification authority | `docs/authority/PLATFORM-UNIFICATION-MASTER-AUTHORITY-2026-04-12.md` | repo-owned authority copy now established; keep parent copy aligned until broader strategic-authority relocation closes |
| `Platform-Authority/README.md` | parent-root authority index | `docs/authority/README.md` | repo-owned authority entrypoint now established; keep parent copy as historical aligned mirror while underlying strategic documents are relocated or superseded |
| `Platform-Authority/UNIFIED-PLATFORM-BLUEPRINT-2026-04-12.md` | strategic platform blueprint | `docs/authority/UNIFIED-PLATFORM-BLUEPRINT-2026-04-12.md` | repo-owned authority copy now established; keep parent copy aligned until broader strategic-authority relocation closes |
| `Platform-Authority/MONOREPO-TARGET-TOPOLOGY-2026-04-12.md` | target topology source | superseded by `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` | keep parent copy as historical design input; do not treat it as active topology authority |
| `Platform-Authority/PLATFORM-DATA-AND-SCHEMA-STRATEGY-2026-04-12.md` | platform data authority | `docs/authority/PLATFORM-DATA-AND-SCHEMA-STRATEGY-2026-04-12.md` | repo-owned authority copy now established; schema review/design remain gated on explicit technical authority review and approval |
| `Platform-Authority/MULTI-AGENT-OPERATING-MODEL-2026-04-12.md` | multi-agent governance | `docs/authority/MULTI-AGENT-OPERATING-MODEL-2026-04-12.md` | repo-owned authority copy now established; keep parent copy aligned until broader strategic-authority relocation closes |
| `Platform-Authority/MIGRATION-ROADMAP-2026-04-12.md` | strategic migration roadmap | superseded by `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` and `plan/infrastructure-olares-full-implementation-roadmap-1.md` | keep parent copy as historical planning input; do not treat it as active migration authority |
| `Infrastructure/Olares_Workspace_Authority_Framework.md` | highest Olares workspace authority | `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md` | repo-owned authority copy now established; keep parent copy aligned until broader relocation closes |
| `Infrastructure/Olares_MVP_Execution_Roadmap.md` | Olares roadmap authority | `plan/Olares_MVP_Execution_Roadmap.md` | repo-owned context copy now established; keep parent copy aligned until broader relocation closes |
| `Infrastructure/Olares_Build_Guide.md` | operator/build guidance | `docs/authority/OLARES-BUILD-GUIDE.md` | repo-owned guidance copy now established; keep parent copy aligned until broader relocation closes |
| `Infrastructure/Olares_Architecture.svg` | Olares visual workspace architecture reference | `docs/authority/Olares_Architecture.svg` | repo-owned visual copy now established; keep parent copy aligned until broader relocation closes |
| `Infrastructure/Olares_Checklist.md` | operator checklist | `docs/operations/OLARES-CHECKLIST.md` | repo-owned operational copy now established |
| `Infrastructure/VSCode_Build_Prompt.md` | execution bootstrap prompt | `docs/operations/OLARES-VSCODE-BUILD-SESSION-PROMPT.md` | repo-owned non-authority execution bootstrap copy now established |
| `PROJECT_STATUS.md` | active parent-root status authority | repo root `PROJECT_STATUS.md` | repo-root copy now established and parent-root mirror now explicitly marked aligned historical copy until relocation closes |
| `PROJECT_OVERVIEW.md` | active parent-root overview authority | repo root `PROJECT_OVERVIEW.md` | repo-root copy now established and parent-root mirror now explicitly marked aligned historical copy until relocation closes |

## Secondary Relocation Set

These were secondary relocation dependencies and now serve as the remaining closeout checklist after the highest-priority chain landed.

| Current source | Current role | Target disposition |
| --- | --- | --- |
| `README.md` at parent root | umbrella guidance | workstation-umbrella routing now established; keep as non-authority guide until repo cutover retires or minimizes it |
| `WORKSPACE_DESIGN.md` | historical conceptual design | keep historical only |
| `WORKSPACE_PROTOCOL.md` | historical conceptual protocol | keep historical only |
| `SUPABASE_REPORT_WORKFLOW.md` | operational workflow note | verified as historical-only; repo-owned lineage copy already retained at `docs/architecture/apex-lineage/automation-reporting/SUPABASE_REPORT_WORKFLOW.md` |
| `.claude/MASTER.md`, `.claude/STATE.md`, `.claude/SESSION_LOG.md`, `.claude/BACKLOG.md` | historical parent-root coordination residue | historical-only notes now established; route operators to repo-owned authority, status, roadmap, and packet surfaces instead |
| `.claude/DECISION_LOG.md` | historical decision log with formerly active AI/orchestration decisions | surviving current decisions now extracted into `docs/architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md`; keep parent copy for provenance |

## Explicit Non-Goals

This relocation plan does not authorize:

1. wholesale import of `Documentation/`, `Supabase/`, `spec/`, or `Reference_Files/`,
2. promotion of archive-heavy material into active repo authority,
3. cutover of sibling source-domain repos into the canonical repo,
4. keeping parent-root authority files live indefinitely just because they already exist.

## Relocation Strategy By Class

### Class A: Move directly

Use for documents that are still clearly active, bounded, and structurally compatible with the canonical repo.

Candidates:

1. Olares authority framework,
2. Olares build guide,
3. Olares checklist,
4. surviving authority README surfaces.

### Class B: Mirror, then demote parent copy

Use for documents still referenced in active flows where immediate removal would break traceability.

Candidates:

1. `PROJECT_STATUS.md`,
2. `PROJECT_OVERVIEW.md`,
3. strategic blueprint documents still needed for continuity.

### Class C: Summarize and supersede

Use where the repo already has a newer authority surface and the parent-root document should remain provenance only.

Candidates:

1. target topology,
2. migration roadmap,
3. older workspace-concept docs.

### Class D: Archive or retire

Use where the document is not needed for daily operation after cutover.

Candidates:

1. obsolete workspace guidance,
2. legacy resume surfaces,
3. stale coordination files,
4. old root readme authority once the repo owns onboarding.

## Residual Repo-Owned Refactor Targets

The following repo-owned files should eventually stop pointing outside the canonical repo for active authority:

1. `docs/authority/README.md`,
2. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`,
3. `docs/architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md`,
4. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`.

## Recorded Execution Order

1. keep `docs/authority/README.md` as the repo-owned entrypoint and demote `Platform-Authority/README.md` to aligned mirror status while the underlying strategic documents are relocated or superseded,
2. relocate the Olares framework and operator docs from `Infrastructure/`,
3. keep repo-root `PROJECT_STATUS.md` and `PROJECT_OVERVIEW.md` aligned until the parent-root mirrors can be retired,
4. update repo-owned runbooks and authority docs so they no longer depend on parent-root paths,
5. demote or archive the parent-root copies only after the repo-owned replacements are verified.

## Exit Condition

This relocation lane is complete only when:

1. the canonical repo contains the full active authority chain,
2. parent-root copies are historical, mirrored, or retired by rule,
3. repo-owned docs no longer treat parent-root authority as a normal dependency,
4. cutover can proceed without hidden documentation dependencies outside the canonical repo.