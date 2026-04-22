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
3. current `HEAD` is `211cbac`
4. the first bounded platform bootstrap slice is tracked on parent-root `clean-main`
5. the next bounded Class A scaffold tranche is also now published on parent-root `clean-main`
6. the bounded package source tranche for `packages/forms-engine` and `packages/calc-engine` is also now published on parent-root `clean-main`
7. the bounded `apps/operations-web` runtime tranche is also now published on parent-root `clean-main`
8. the bounded `apps/mutation-seam` runtime tranche is also now published on parent-root `clean-main`
9. the bounded `apps/control-plane-api` runtime-core tranche is also now published on parent-root `clean-main`
10. the bounded `apps/control-plane-api` support tranche is also now published on parent-root `clean-main`
11. the bounded `apps/control-plane-api` tests tranche is also now published on parent-root `clean-main`
12. normal `git status`, `git diff`, and bounded `git add -- <paths>` now work against tracked `HEAD` for those already-introduced `apex-power-ops-platform/` paths
13. much of the broader subtree still remains untracked and therefore still requires deliberate introduction rather than assuming routine diff coverage
14. the parent root remains the actual git boundary even though day-to-day implementation work is platform-first inside the subtree

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
4. treat the 2026-04-22 bootstrap, Class A scaffold, package source, operations-web runtime, mutation-seam runtime, control-plane core, control-plane support, control-plane tests, and reconciliation handoffs as historical records, not as active blockers or active workflow instructions
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
9. `ops/agents/handoffs/2026-04-22-parent-root-clean-main-reconciliation-handoff.md`
10. `C:/APEX-safety-snapshots/live-root-pre-merge-divergence-2026-04-22/RECOVERY-NOTES.md`
11. `C:/APEX-safety-snapshots/live-root-pre-merge-divergence-2026-04-22/INTEGRITY-REPORT.md`

## Residual Constraints

The repo is cleaner, but these constraints still matter:

1. parent-root git operations can still accidentally widen if unrelated root-level changes are present, so bounded staging remains the default
2. the parent-root `.gitignore` is intentionally narrower than the subtree `.gitignore`; expand it only for real parent-root operator problems, not by default
3. historical parked worktrees can still contain stale copies of docs; do not treat those parked copies as live authority
4. broader subtree introduction still needs an explicit classification baseline so active runtime lanes do not get bundled with archive or knowledge bulk; use `docs/architecture/WORKSPACE-BOUNDED-PUBLICATION-PLAN-2026-04-22.md` for that follow-on work

## Audit Outcome

The workflow drift is closed.

The platform subtree is no longer in a wholly untracked first-introduction bootstrap state. Its first bounded publication slice, its Class A scaffold tranche, its package source tranche, its `operations-web` runtime tranche, its `mutation-seam` runtime tranche, and the full bounded `control-plane-api` lane (runtime core, support, and tests) are now published on `clean-main`, and future parent-root publication should distinguish between routine bounded staging for already-introduced paths and deliberate incremental introduction for the still-untracked majority of the subtree.
