# Handoff Register

This directory is the operator-facing packet archive for bounded execution, blocker packets, and delegable next-step records.

## Current Hosted Route Promotion Status

As of 2026-04-22, the hosted control-plane route-promotion blocker on `https://control.apexpowerops.com` is closed for the packet `001af` scope.

Packet `2026-04-21-apex-unification-001af` is now the completed execution record for that hosted frontier.

Use these files first:

1. `../../../../apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md`
2. `2026-04-22-parent-root-ops-knowledge-resource-operations-publication-handoff.md` for the current next bounded parent-root publication tranche
3. `2026-04-22-parent-root-ops-legacy-governance-publication-handoff.md` when historical context on the published ops legacy-governance tranche is needed
4. `2026-04-22-parent-root-ops-knowledge-control-plane-registry-publication-handoff.md` when historical context on the published ops knowledge-control-plane registry tranche is needed
5. `2026-04-22-parent-root-docs-publication-handoff.md` when historical context on the published docs tranche is needed
6. `2026-04-22-parent-root-infra-database-publication-handoff.md` when historical context on the published infra-database tranche is needed
7. `2026-04-22-parent-root-residual-scaffold-publication-handoff.md` when historical context on the published residual scaffold/doc tranche is needed
8. `2026-04-22-parent-root-control-plane-tests-publication-handoff.md` when historical context on the published control-plane tests tranche is needed
9. `2026-04-22-parent-root-control-plane-support-publication-handoff.md` when historical context on the published control-plane support tranche is needed
10. `2026-04-22-parent-root-control-plane-core-publication-handoff.md` when historical context on the published control-plane runtime-core tranche is needed
11. `2026-04-22-parent-root-mutation-seam-runtime-publication-handoff.md` when historical context on the published mutation-seam runtime tranche is needed
12. `2026-04-22-parent-root-operations-web-runtime-publication-handoff.md` when historical context on the published operations-web runtime tranche is needed
13. `2026-04-22-parent-root-package-source-publication-handoff.md` when historical context on the published package source tranche is needed
14. `2026-04-22-parent-root-class-a-scaffold-publication-handoff.md` when historical context on the published Class A scaffold tranche is needed
15. `2026-04-22-parent-root-bootstrap-publication-handoff.md` only when historical context on the completed first parent-root publication tranche is needed

Historical hosted execution handoffs are not bundled inside this bootstrap packet.

Historical blocker state for the now-closed lane before closure:

1. the public host is otherwise healthy
2. the deployed OpenAPI document still omits `/api/v1/neta/apparatus/{apparatus_id}/resources`
3. the hosted probe still returns framework `404 Not Found` for that route

Hosted proof captured for closure:

1. the public OpenAPI document now advertises `/api/v1/neta/apparatus/{apparatus_id}/resources`
2. the public apparatus probe now returns handler-owned responses instead of framework `404 Not Found`
3. GitHub Actions run `24781243756` succeeded for the deployed control-plane smoke workflow
4. the repo-owned smoke script returned `RESULT PASS` against `https://control.apexpowerops.com`

## Operator Use

Use the promotion checklist when you need the smallest repo-owned rerun path after a future regression or deploy change:

1. rerun the public route gate manually
2. rerun the hosted smoke workflow if a later deploy changes the serving slice
3. use the repository-dispatch path only if future deploy automation requires it again

Current workspace constraint:

1. the dispatch dry-run path is available from this repo workspace
2. the live dispatch token is still not required for the now-closed packet `001af` outcome because hosted cutover was completed directly

## Current Closure Result

The packet `001af` closure conditions are now satisfied for hosted route promotion:

1. `Control-plane public apparatus-route gate` passes against `https://control.apexpowerops.com`
2. the public hosted route is present in deployed OpenAPI and returns handler-owned responses

Any later promoted-host browser proof is now a separate follow-on activity, not an open blocker for this route-promotion execution packet.

## Optional Follow-Through

These are maintenance items only. They do not reopen packet `001af`:

1. broader documentation refresh outside the closure packet and checklist surfaces
2. separate deploy-worktree reconciliation or publication if that tranche is being promoted next; a deploy-worktree handoff is not bundled inside this bootstrap packet yet
3. future parent-root publication for `C:/APEX Platform/apex-power-ops-platform` as routine bounded staging against tracked `HEAD`; use `2026-04-22-parent-root-ops-knowledge-resource-operations-publication-handoff.md` for the current active tranche and review the ops legacy-governance, ops knowledge-control-plane registry, docs, infra-database, residual scaffold, control-plane tests, control-plane support, control-plane core, mutation-seam, operations-web, package, Class A, and bootstrap handoffs only as historical closure records
