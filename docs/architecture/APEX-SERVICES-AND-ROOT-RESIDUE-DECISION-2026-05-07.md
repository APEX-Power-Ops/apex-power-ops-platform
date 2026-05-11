# APEX Services And Root Residue Decision

Date: 2026-05-07
Status: Recorded services-lane disposition baseline with residual maintenance guidance
Scope: recorded disposition of parent-root `services/` and the canonical meaning of repo-root `services/` after standalone cutover

Closeout interpretation note:

This services-lane decision is already executed through the completed standalone cutover. It now serves as recorded repo-foundation baseline for the canonical `services/` contract and remaining residue-handling rules, not as a live unresolved cutover decision.

Current routing:

1. use `PROJECT_STATUS.md` for the latest completed residue slice and current sequencing,
2. use `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for governing repo-foundation decisions,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover closeout queue,
4. use this decision note when the recorded `services/` boundary or parent-root residue handling needs to be audited as historical provenance.

## Decision

`apex-power-ops-platform/services/` is the only canonical top-level services lane.

`C:/APEX Platform/services/` is not a second valid application namespace and must not remain a live parallel source root.

## Why This Decision Was Needed

The current parent root exposes `services/` as ambiguous residue.

That ambiguity is unacceptable because:

1. the active repo already has a real `services/mcp/` lane,
2. live repo infrastructure points at repo-owned service entrypoints,
3. parent-root `services/` currently has no verified active references,
4. leaving both roots in play would preserve an unbounded second runtime namespace during cutover.

## Verified Current State

The bounded local check for this decision found:

1. `C:/APEX Platform/apex-power-ops-platform/services/mcp/` contains the active MCP service lane with `apex-db`, `apex-forms`, `apex-fs`, `apex-jobs`, and `apex-p6`.
2. `infra/compose.dev.yml` runs the repo-owned service entrypoints from `services/mcp/*/build/http.js`.
3. `C:/APEX Platform/services/mcp/` contains only `apex-p6`.
4. no active repo-owned documentation or infrastructure reference was found that requires the parent-root `services/` path.

## Canonical Contract Going Forward

Use the canonical repo root `services/` lane only for standalone service surfaces that are neither app-local business logic nor reusable packages.

That means:

1. MCP HTTP bridges and similar host/runtime sidecars belong in repo-root `services/`.
2. app-owned service code belongs under the owning app, such as `apps/control-plane-api/services/`.
3. reusable libraries and substrate code belong under `packages/`.
4. source-domain lineage code outside the repo remains source input, not canonical runtime.

## Parent-Root Disposition

`C:/APEX Platform/services/` is classified as transitional residue.

Its disposition is now:

1. do not add new work there,
2. do not treat it as valid steady-state topology,
3. the bounded `services/mcp/apex-p6` verification is complete and found no unique source material outside the canonical repo,
4. treat any future surviving parent-root `services/` residue as explicit reconcile-or-retire work rather than as a parallel live lane.

## Verified `apex-p6` Reconciliation State

The bounded reconciliation check on 2026-05-07 found:

1. `C:/APEX Platform/services/mcp/apex-p6` contained only a stray `package-lock.json` file and no unique source material.
2. the stray parent-root residue was retired after verification because it did not represent a viable canonical source lane.
3. `C:/APEX Platform/apex-power-ops-platform/services/mcp/apex-p6` is still the live runtime lane referenced by dev infrastructure through `infra/compose.dev.yml` via `services/mcp/apex-p6/build/http.js`.
4. the repo-owned `apex-p6` lane now contains a tracked `package.json`, `tsconfig.json`, `README.md`, and `src/` bridge sources that re-establish an explicit source-of-truth contract for the service name.
5. the restored repo-owned bridge package built successfully through `corepack pnpm --filter apex-p6 build` after the workspace contract was updated to include `services/mcp/*`.

Implication:

1. the parent-root `apex-p6` path was stale residue and is no longer needed,
2. the repo-owned `apex-p6` path is the only canonical source and runtime lane for this service name,
3. `apex-p6` is now source-owned again as a thin MCP bridge over `packages/p6-ingest` rather than an undocumented build-only residue lane.

## Cutover Rule

Repo-boundary cutover must preserve `apex-power-ops-platform/services/` as the canonical service lane and must not absorb parent-root `services/` wholesale.

If any surviving material exists only under `C:/APEX Platform/services/`, it must be reconciled file-by-file into the canonical repo or archived explicitly.

## Anti-Patterns Now Rejected

1. treating parent-root `services/` and repo-root `services/` as co-equal,
2. using root `services/` as a catch-all place for app-local logic,
3. bulk-merging sibling or parent-root source trees into canonical `services/` without bounded ownership,
4. leaving a hidden host dependency in the parent-root `services/` lane after cutover.

## Recorded Follow-Through And Standing Maintenance Rule

1. this decision is now recorded in repo-foundation status surfaces,
2. the parent-root classification matrix retains the `services/` disposition as reconcile-then-retire,
3. the `apex-p6` residue retirement and repo-owned source-of-truth recovery are now explicitly recorded as the bounded reconciliation outcome,
4. keep future service-lane cutover evidence explicit about whether each `services/mcp/*` lane is source-owned, generated at runtime, or still awaiting bounded scaffold recovery.