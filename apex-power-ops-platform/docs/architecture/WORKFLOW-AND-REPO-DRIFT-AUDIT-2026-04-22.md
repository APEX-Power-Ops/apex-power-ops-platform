# Workflow And Repo Drift Audit

Date: 2026-04-22
Status: Closed drift audit
Scope: `C:/APEX Platform/apex-power-ops-platform` publication-boundary and operator-workflow truth

## Purpose

This audit closes the stale workflow and repo-drift assumptions that accumulated while the platform subtree moved from an untracked bootstrap packet to a tracked lane on parent-root `clean-main`.

It exists to answer one operational question clearly:

- what is the current git publication posture for `C:/APEX Platform/apex-power-ops-platform`?

## Current Verified State

Verified from the parent git root at `C:/APEX Platform`:

1. current branch is `clean-main`
2. current `HEAD` matches `origin/clean-main`
3. current `HEAD` is `0d8edb2`
4. the first bounded platform bootstrap slice is tracked on parent-root `clean-main`
5. the next bounded Class A scaffold tranche is also now published on parent-root `clean-main`
6. the bounded package source tranche for `packages/forms-engine` and `packages/calc-engine` is also now published on parent-root `clean-main`
7. the bounded `apps/operations-web` runtime tranche is also now published on parent-root `clean-main`
8. the bounded `apps/mutation-seam` runtime tranche is also now published on parent-root `clean-main`
9. the bounded `apps/control-plane-api` runtime-core tranche is also now published on parent-root `clean-main`
10. the bounded `apps/control-plane-api` support tranche is also now published on parent-root `clean-main`
11. the bounded `apps/control-plane-api` tests tranche is also now published on parent-root `clean-main`
12. the bounded residual scaffold/doc tranche is also now published on parent-root `clean-main`
13. the bounded `infra/database` tranche is also now published on parent-root `clean-main`
14. the bounded `docs/` tranche is also now published on parent-root `clean-main`
15. the bounded `ops/knowledge-control-plane/registry` tranche is also now published on parent-root `clean-main`
16. the bounded `ops/agents/legacy-governance` tranche is also now published on parent-root `clean-main`
17. the bounded `ops/knowledge-resource-operations` tranche is also now published on parent-root `clean-main`
18. the bounded forms-import draft tranche is also now published on parent-root `clean-main`
19. the bounded `001af` draft tranche is also now published on parent-root `clean-main`
20. the bounded `apex-unification-001` draft tranche is also now published on parent-root `clean-main`
21. the bounded `knowledge-import-001` draft tranche is also now published on parent-root `clean-main`
22. the bounded `pm-schema-009` draft tranche is also now published on parent-root `clean-main`
23. the bounded `pm-schema-010` draft tranche is also now published on parent-root `clean-main`
24. the bounded `pm-schema-011` draft tranche is also now published on parent-root `clean-main`
25. the bounded `pm-schema-012` draft tranche is also now published on parent-root `clean-main`
26. the bounded `pm-schema-013` draft tranche is also now published on parent-root `clean-main`
27. the bounded `pm-schema-014` draft tranche is also now published on parent-root `clean-main`
28. the bounded `pm-schema-015` draft tranche is also now published on parent-root `clean-main`
29. the bounded `pm-schema-016` draft tranche is also now published on parent-root `clean-main`
30. the bounded `pm-schema-017` draft tranche is also now published on parent-root `clean-main`
31. the bounded `pm-schema-018` draft tranche is also now published on parent-root `clean-main`
32. the bounded `pm-schema-019` draft tranche is also now published on parent-root `clean-main`
33. the bounded `pm-schema-019f` draft tranche is also now published on parent-root `clean-main`
34. the bounded `pm-schema-019g` draft tranche is also now published on parent-root `clean-main`
35. the bounded `pm-schema-019h` draft tranche is also now published on parent-root `clean-main`
36. the bounded `pm-schema-019i` draft tranche is also now published on parent-root `clean-main`
37. the bounded `pm-schema-019j` draft tranche is also now published on parent-root `clean-main`
38. the bounded `pm-schema-019k` draft tranche is also now published on parent-root `clean-main`
39. the bounded `pm-schema-ui-002g` draft tranche is also now published on parent-root `clean-main`
40. the bounded `pm-schema-ui-002g` host-variance draft tranche is also now published on parent-root `clean-main`
41. the bounded `pm-schema-ui-002e` host draft tranche is also now published on parent-root `clean-main`
42. the bounded `pm-schema-ui-002f` host draft tranche is also now published on parent-root `clean-main`
43. the bounded `pm-schema-ui-001` draft tranche is also now published on parent-root `clean-main`
44. the bounded `pm-schema-ui-002` draft tranche is also now published on parent-root `clean-main`
45. the bounded `pm-schema-ui-003` draft tranche is also now published on parent-root `clean-main`
46. the bounded `pm-schema-ui-004` draft tranche is also now published on parent-root `clean-main`
47. normal `git status`, `git diff`, and bounded `git add -- <paths>` now work against tracked `HEAD` for those already-introduced `apex-power-ops-platform/` paths
48. much of the broader subtree still remains untracked and therefore still requires deliberate introduction rather than assuming routine diff coverage
49. the parent root remains the actual git boundary even though day-to-day implementation work is platform-first inside the subtree

## Drift That Was Present

The live docs had drifted into two stale assumptions:

1. the platform subtree still appeared as `?? apex-power-ops-platform/` from the parent root
2. the first parent-root publication was still pending and future publication therefore needed bootstrap-only staging rules

Those assumptions were no longer true after the merged review-fix lane landed on `clean-main`.

## Surfaces Corrected In This Audit Cycle

The following live authority surfaces were updated so they now reflect the tracked clean-main reality:

1. `README.md`
2. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
3. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
4. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
5. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
6. `docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md`
7. `ops/agents/handoffs/README.md`
8. `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`
9. `ops/agents/handoffs/2026-04-22-parent-root-clean-main-reconciliation-handoff.md`

## Current Operator Rules

Use this posture going forward:

1. work from `C:/APEX Platform/apex-power-ops-platform` for implementation, but treat `C:/APEX Platform` as the authoritative git root
2. use routine `git diff` and bounded `git add -- <paths>` against tracked `HEAD` for already-introduced paths
3. keep whole-subtree staging reserved for explicit broad publication or cutover work
4. treat the 2026-04-22 bootstrap, Class A scaffold, package source, operations-web runtime, mutation-seam runtime, control-plane core, control-plane support, control-plane tests, residual scaffold, infra database, docs, ops knowledge-control-plane registry, ops legacy-governance, ops knowledge-resource-operations, forms-import draft, `001af` draft, `apex-unification-001` draft, `knowledge-import-001` draft, `pm-schema-009` draft, `pm-schema-010` draft, `pm-schema-011` draft, `pm-schema-012` draft, `pm-schema-013` draft, `pm-schema-014` draft, `pm-schema-015` draft, `pm-schema-016` draft, `pm-schema-017` draft, `pm-schema-018` draft, `pm-schema-019` draft, `pm-schema-019f` draft, `pm-schema-019g` draft, `pm-schema-019h` draft, `pm-schema-019i` draft, `pm-schema-019j` draft, `pm-schema-019k` draft, `pm-schema-ui-002g` draft, `pm-schema-ui-002g-host` draft, `pm-schema-ui-002e-host` draft, `pm-schema-ui-002f-host` draft, `pm-schema-ui-001` draft, `pm-schema-ui-002` draft, `pm-schema-ui-003` draft, `pm-schema-ui-004` draft, and reconciliation handoffs as historical records, not as active blockers or active workflow instructions
5. keep `C:/APEX Platform/apex-power-ops-platform-deploy-worktree` as a separate optional publication lane
6. keep `C:/APEX Platform/apex-power-ops-platform-clean-main-reconcile` as the historical clean review-fix worktree, not as the live authority surface
7. treat broader subtree publication beyond the already-tracked slice as explicit incremental introduction work

## Important Historical References

These remain useful, but only as historical context:

1. `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md`
2. `ops/agents/handoffs/2026-04-22-parent-root-class-a-scaffold-publication-handoff.md`
3. `ops/agents/handoffs/2026-04-22-parent-root-package-source-publication-handoff.md`
4. `ops/agents/handoffs/2026-04-22-parent-root-operations-web-runtime-publication-handoff.md`
5. `ops/agents/handoffs/2026-04-22-parent-root-mutation-seam-runtime-publication-handoff.md`
6. `ops/agents/handoffs/2026-04-22-parent-root-control-plane-core-publication-handoff.md`
7. `ops/agents/handoffs/2026-04-22-parent-root-control-plane-support-publication-handoff.md`
8. `ops/agents/handoffs/2026-04-22-parent-root-control-plane-tests-publication-handoff.md`
9. `ops/agents/handoffs/2026-04-22-parent-root-residual-scaffold-publication-handoff.md`
10. `ops/agents/handoffs/2026-04-22-parent-root-infra-database-publication-handoff.md`
11. `ops/agents/handoffs/2026-04-22-parent-root-docs-publication-handoff.md`
12. `ops/agents/handoffs/2026-04-22-parent-root-ops-knowledge-control-plane-registry-publication-handoff.md`
13. `ops/agents/handoffs/2026-04-22-parent-root-ops-legacy-governance-publication-handoff.md`
14. `ops/agents/handoffs/2026-04-22-parent-root-ops-knowledge-resource-operations-publication-handoff.md`
15. `ops/agents/handoffs/2026-04-22-parent-root-forms-import-draft-publication-handoff.md`
16. `ops/agents/handoffs/2026-04-22-parent-root-001af-draft-publication-handoff.md`
17. `ops/agents/handoffs/2026-04-22-parent-root-apex-unification-001-draft-publication-handoff.md`
18. `ops/agents/handoffs/2026-04-22-parent-root-knowledge-import-001-draft-publication-handoff.md`
19. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-009-draft-publication-handoff.md`
20. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-010-draft-publication-handoff.md`
21. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-011-draft-publication-handoff.md`
22. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-012-draft-publication-handoff.md`
23. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-013-draft-publication-handoff.md`
24. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-014-draft-publication-handoff.md`
25. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-015-draft-publication-handoff.md`
26. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-016-draft-publication-handoff.md`
27. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-017-draft-publication-handoff.md`
28. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-018-draft-publication-handoff.md`
29. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019-draft-publication-handoff.md`
30. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019f-draft-publication-handoff.md`
31. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019g-draft-publication-handoff.md`
32. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019h-draft-publication-handoff.md`
33. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019i-draft-publication-handoff.md`
34. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019j-draft-publication-handoff.md`
35. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-019k-draft-publication-handoff.md`
36. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-002g-draft-publication-handoff.md`
37. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-002g-host-variance-draft-publication-handoff.md`
38. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-002e-host-draft-publication-handoff.md`
39. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-002f-host-draft-publication-handoff.md`
40. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-001-draft-publication-handoff.md`
41. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-002-draft-publication-handoff.md`
42. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-003-draft-publication-handoff.md`
43. `ops/agents/handoffs/2026-04-22-parent-root-pm-schema-ui-004-draft-publication-handoff.md`
44. `ops/agents/handoffs/2026-04-22-parent-root-clean-main-reconciliation-handoff.md`
45. `C:/APEX-safety-snapshots/live-root-pre-merge-divergence-2026-04-22/RECOVERY-NOTES.md`
46. `C:/APEX-safety-snapshots/live-root-pre-merge-divergence-2026-04-22/INTEGRITY-REPORT.md`

## Residual Constraints

The repo is cleaner, but these constraints still matter:

1. parent-root git operations can still accidentally widen if unrelated root-level changes are present, so bounded staging remains the default
2. the parent-root `.gitignore` is intentionally narrower than the subtree `.gitignore`; expand it only for real parent-root operator problems, not by default
3. historical parked worktrees can still contain stale copies of docs; do not treat those parked copies as live authority
4. broader subtree introduction still needs an explicit classification baseline so active runtime lanes do not get bundled with archive or knowledge bulk; use `docs/architecture/WORKSPACE-BOUNDED-PUBLICATION-PLAN-2026-04-22.md` for that follow-on work

## Audit Outcome

The workflow drift is closed.

The platform subtree is no longer in a wholly untracked first-introduction bootstrap state. Its first bounded publication slice, its Class A scaffold tranche, its package source tranche, its `operations-web` runtime tranche, its `mutation-seam` runtime tranche, the full bounded `control-plane-api` lane (runtime core, support, and tests), the residual scaffold/doc tranche, the `infra/database` tranche, the `docs/` tranche, the `ops/knowledge-control-plane/registry` tranche, the `ops/agents/legacy-governance` tranche, the `ops/knowledge-resource-operations` tranche, the bounded forms-import draft tranche, the bounded `001af` draft tranche, the bounded `apex-unification-001` draft tranche, the bounded `knowledge-import-001` draft tranche, the bounded `pm-schema-009` draft tranche, the bounded `pm-schema-010` draft tranche, the bounded `pm-schema-011` draft tranche, the bounded `pm-schema-012` draft tranche, the bounded `pm-schema-013` draft tranche, the bounded `pm-schema-014` draft tranche, the bounded `pm-schema-015` draft tranche, the bounded `pm-schema-016` draft tranche, the bounded `pm-schema-017` draft tranche, the bounded `pm-schema-018` draft tranche, the bounded `pm-schema-019` draft tranche, the bounded `pm-schema-019f` draft tranche, the bounded `pm-schema-019g` draft tranche, the bounded `pm-schema-019h` draft tranche, the bounded `pm-schema-019i` draft tranche, the bounded `pm-schema-019j` draft tranche, the bounded `pm-schema-019k` draft tranche, the bounded `pm-schema-ui-002g` draft tranche, the bounded `pm-schema-ui-002g-host` draft tranche, the bounded `pm-schema-ui-002e-host` draft tranche, the bounded `pm-schema-ui-002f-host` draft tranche, the bounded `pm-schema-ui-001` draft tranche, the bounded `pm-schema-ui-002` draft tranche, the bounded `pm-schema-ui-003` draft tranche, and the bounded `pm-schema-ui-004` draft tranche are now published on `clean-main`, and future parent-root publication should distinguish between routine bounded staging for already-introduced paths and deliberate incremental introduction for the still-untracked majority of the subtree.
