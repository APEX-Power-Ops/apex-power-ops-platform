# Historical Workspace Implementation Roadmap

Date: 2026-04-21
Status: Historical pre-cutover roadmap snapshot
Scope: `C:/APEX Platform/apex-power-ops-platform`

Historical roadmap note:

This document preserves an earlier workspace-normalization roadmap from before standalone repo cutover and later repo-foundation realignment. It is not the current execution roadmap for repo-structure or Olares-first work.

Current routing:

1. use `../../PROJECT_STATUS.md` for the current execution frontier and residue-retirement ledger,
2. use `APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` plus `APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` for the current repo-structure and lane-routing contract,
3. use `../../plan/infrastructure-olares-full-implementation-roadmap-1.md` and `../authority/README.md` for the current maintained execution and authority stack,
4. use this document only when the earlier workspace-normalization sequencing needs to be reconstructed historically.

## Purpose

This roadmap defined the implementation sequence required to turn the then-current bootstrap repo into a more fully realized platform workspace using the audit, status, and checklist surfaces bundled in that packet family.

It was intentionally execution-focused. The goal was not to keep auditing the workspace; the goal was to finish normalizing it.

Its original execution companion was `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`.

## Implementation Priorities

### Priority 1: Governance completion

Outcome:
- the workspace stops depending on implicit ownership and memory-based approval

Required deliverables:

1. add `.github/CODEOWNERS`
2. add a repo-level ownership and workflow map
3. define approval lanes for apps, packages, infra, docs, ops, and knowledge
4. add `knowledge/README.md` to define the boundary between `knowledge/` and `docs/knowledge/`

Exit criteria:

1. every major path has an owner or steward group
2. review routing can be inferred from repo files, not chat history
3. operators can distinguish asset lanes from documentation lanes locally

### Priority 2: Workspace hygiene completion

Outcome:
- active workspace artifacts are clean enough to serve as authority surfaces

Required deliverables:

1. remove malformed residue in `apps/mutation-seam` if confirmed non-authoritative
2. normalize encoding in `ops/knowledge-control-plane/registry/GUIDE-REGISTRY.md`
3. review nearby ops registry files for the same inherited corruption pattern
4. keep ignore coverage current for generated residue

Exit criteria:

1. no malformed path-like artifacts remain in active lanes
2. no known corrupted registry files remain in active ops knowledge surfaces

### Priority 3: Transitional app rationalization

Outcome:
- the repo stops carrying ambiguous deployable lanes

Decision status:
1. `apps/field-surface` is retained as a seed lane and future rename pressure to `field-app` is deferred until field-runtime work exists
2. `apps/integration-surface` is a merge-target and both its Python validation harness and browser dashboard slice have already been re-homed into active lanes; the empty `public/` shell has been removed so the lane is now marker-only retirement residue
3. `apps/lead-surface` is classified as a merge-target into `apps/operations-web`; the lead-facing prototype now has an active-lane copy under `/lead-ops/index.html`, and the original lane is down to retirement residue
4. `apps/pm-surface` is classified as a merge-target into `apps/operations-web`; the approval shell plus the schedule, drivers, tracer, and variance review slices now have active-lane copies, and the duplicate browser artifacts have been removed so the lane is down to retirement residue

Required decisions:

1. convert the ratified lane calls into bounded re-home work
2. preserve `apps/field-surface` as a seed lane until field-runtime work exists
3. keep `apps/integration-surface` as marker-only retirement residue now that its active browser and validation slices have been re-homed and the empty `public/` shell has been removed
4. fold lead and PM browser concerns into `apps/operations-web` unless a hard deployment boundary is later proven

Execution companion:

1. use `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md` as the bounded follow-through surface for marker-only retirement lanes, deferred placeholders, and seed-lane preservation

Preferred implementation stance:

1. keep `field-surface` as a seed lane until field-runtime work exists
2. merge lead and PM UI concerns into `operations-web` unless a hard deployment boundary is proven
3. merge integration-only behavior into `control-plane-api` or `mutation-seam` unless it truly requires a standalone runtime

Exit criteria:

1. every app lane is either active, intentionally reserved, or archived
2. no app lane remains in indefinite transitional ambiguity

### Priority 4: Placeholder lane activation

Outcome:
- approved empty lanes become real or explicitly deferred

Decision status:
1. `apps/forms-studio` is explicitly deferred in this cycle because `packages/forms-engine` already carries the bounded reusable import and no governed browser app shell has been started yet
2. `packages/api-contracts` is explicitly deferred in this cycle because second-surface shared contract reuse is not yet proven in the active runtime lanes
3. `packages/forms-engine` now has bounded smoke, focused pytest, and package CI validation paths over the promoted MOP, PSS, and AHA artifact set while the forms browser app shell remains intentionally deferred

Required deliverables:

1. document the defer trigger for `apps/forms-studio`: start when a real forms browser app shell and bounded `neta-forms` UI slices are ready for promotion
2. document the defer trigger for `packages/api-contracts`: start when stable contracts are reused by more than one active surface
3. keep placeholder markers current until either trigger is met

Exit criteria:

1. placeholder lanes are either implemented or deliberately deferred with stated triggers
2. no placeholder is mistaken for abandoned work

### Priority 5: Runtime contract normalization

Outcome:
- active apps can be operated from the platform root with clear validation and deployment rules

Status note:
1. a unified runtime, validation, and env contract map now exists under `docs/architecture/ACTIVE-APP-RUNTIME-VALIDATION-MAP-2026-04-21.md`
2. workspace tasks are now aligned for `apps/control-plane-api`, `apps/operations-web`, and `apps/mutation-seam`, including the control-plane local readiness/bootstrap lane, the public control-plane apparatus-route gate, and the defaulted operations-web promoted-host smoke task
3. `apps/operations-web` now has a bounded deployment-proof runbook, a dedicated hosted route smoke script, local Playwright browser smoke, frontend smoke workflows, and a promoted-host browser-plus-seam smoke wrapper for deployed targets

Required deliverables:

1. add a deployment and validation map for each active app
2. document environment contracts for active runtimes
3. align workspace tasks with the declared operator entrypoints
4. ensure every active app has a clear test or smoke path

Target surfaces:

1. `apps/control-plane-api`
2. `apps/operations-web`
3. `apps/mutation-seam`
4. any newly promoted app lanes

Exit criteria:

1. each active app has a documented run path
2. each active app has a documented validation path
3. each active app has a documented env contract boundary

### Priority 6: Source-domain re-home completion

Outcome:
- sibling repos are reduced to lineage lanes instead of default work roots

Required deliverables:

1. continue bounded extraction from `tcc_v5_backend` into `apps/control-plane-api` and `packages/calc-engine`
2. continue bounded extraction from `neta-forms` into `packages/forms-engine` and keep `apps/forms-studio` deferred until a real browser app-shell packet starts
3. re-home approved knowledge assets into `knowledge/`
4. keep lineage mapping in docs or archive rather than flattening source repos into active lanes

Exit criteria:

1. active implementation no longer depends on sibling repos as day-to-day entrypoints
2. imported slices have named platform homes and lineage traceability

### Priority 7: Authority cutover readiness

Outcome:
- the repo is ready to stop behaving like a bootstrap and start behaving like the canonical platform root

Required deliverables:

1. reduce bridge-only dependence in `docs/authority`
2. promote the live workspace plan, status, and roadmap as normal operating documents
3. confirm that repo-local docs are sufficient for daily operator decisions
4. keep future parent-root publication bounded and routine for already-introduced paths now that the first bootstrap publication tranche has already landed on `clean-main`, while treating wider subtree introduction as explicit incremental publication work

Exit criteria:

1. the repo can serve as the canonical operator root
2. the remaining strategic authority gap is explicit, limited, and manageable

## Recommended Sequence

Implement in this order:

1. governance completion
2. hygiene cleanup
3. transitional lane decisions
4. placeholder activation decisions
5. runtime contract normalization
6. bounded source-domain re-home completion
7. authority cutover readiness

This order is deliberate. Ownership and hygiene come first because they reduce decision friction for every later phase.

## Near-Term Execution Plan

### Phase A: Finish governance baseline

Tasks:

1. author CODEOWNERS
2. author repo workflow and approval map
3. author `knowledge/README.md`

Result:
- the repo becomes self-routing and easier to govern

### Phase B: Remove known ambiguity

Tasks:

1. clean malformed mutation-seam residue
2. fix encoding-corrupted registry files
3. make keep, merge, or archive calls on transitional app lanes

Result:
- the active tree stops carrying obvious structural noise

### Phase C: Activate real implementation boundaries

Tasks:

1. record explicit defer decisions for `forms-studio` and `api-contracts`
3. publish active app deployment and validation map
4. execute the bounded merge targets already ratified for the transitional app lanes

Result:
- the repo becomes operationally legible to new operators

### Phase D: Complete platform-first posture

Tasks:

1. continue bounded slice migration from source domains
2. reduce residual sibling-repo dependency
3. prepare authority cutover package
4. if parent-root publication becomes necessary before cutover, use routine bounded staging against tracked `HEAD` for already-introduced paths, keep `ops/agents/handoffs/2026-04-22-parent-root-bootstrap-publication-handoff.md` only as historical context, and treat wider subtree introduction as a distinct follow-on tranche

Result:
- the workspace behaves like the platform root by default

## Definition Of Done

The roadmap is complete when:

1. ownership is explicit
2. hygiene defects in active governance lanes are closed
3. transitional lanes are resolved
4. placeholder lanes are implemented or deliberately deferred
5. every active app has documented runtime, validation, and env paths
6. source-domain extractions land into stable platform homes
7. the repo no longer feels like a bootstrap-only structure

## Companion Documents

- `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
- `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`