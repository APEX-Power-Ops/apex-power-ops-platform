# TCC Relay Governance Index

Date: 2026-05-03
Status: Active repo-local governance index
Scope: Provide one repo-local index for the governing relay packet stack, current lane state, and non-reopen rules without replacing the root authority packets

## Purpose

The TCC relay lane is governed by a packet stack, not by one monolithic spec.

This file exists to make the controlling surfaces easy to find from inside the repo.

This file is an index and routing surface only.

Closeout interpretation note:

The earlier `Platform-Authority/TCC-RELAY-*` packet names quoted in older relay records are preserved source labels from the pre-cutover governance chain, not current repo-local paths.

If any summary here conflicts with a more specific repo-local relay handoff or relay memo named below, the more specific repo-local surface wins.

## Authority Boundary

The relay governance boundary is:

1. repo-local relay handoffs under `ops/agents/handoffs/` are the governing continuity, execution-routing, and closure surfaces preserved in the canonical repo,
2. repo-local relay memos under `docs/architecture/` are the current planning, decision, and non-reopen surfaces for the relay lane,
3. repo-local runtime and validation files under `apps/`, `packages/`, and `infra/` are implementation evidence,
4. reviewed D: worktree relay-family notes are evidence input only and are not implementation authority until restated in governed repo artifacts.

The surviving repo-local source-authority split is fixed by:

1. `ops/agents/handoffs/2026-04-30-tcc-relay-governed-repo-lane-continuity-handoff.md`

That handoff preserves the controlling rule that:

1. the relay lane must be governed from repo-owned artifacts,
2. the D: relay-family packet is reviewed evidence input,
3. reusable conclusions from D: must be restated in governed repo artifacts before they influence platform implementation.

## Master Governing Records

Use these as the accessible relay governance stack inside the canonical repo.

### 1. Source and authority split

`ops/agents/handoffs/2026-04-30-tcc-relay-governed-repo-lane-continuity-handoff.md`

Use this first when you need to know:

1. what counts as governing authority,
2. what counts as reviewed evidence only,
3. which source system governs lineage versus runtime characterization.

### 2. Runtime-order governance

`ops/agents/handoffs/2026-04-30-tcc-relay-runtime-adoption-scoping-handoff.md`

Use this when you need the approved runtime-consumer order.

The fixed order is:

1. shared calc package first,
2. read-only control-plane API second,
3. browser and coordination consumers third.

### 3. Execution-ladder governance

`ops/agents/handoffs/2026-04-30-tcc-relay-execution-tranche-planning-handoff.md`

Use this when you need the governing implementation ladder.

This packet fixes:

1. the five-tranche execution order,
2. tranche merge gates,
3. validation surfaces,
4. rollback posture,
5. the rule that the ladder must not be collapsed into one release unit.

### 4. Post-ladder governance

`TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md`

Use this as the current top-level relay governance surface after the five-tranche ladder closed PASS and the Phase 3 write-design lane closed as design-only.

Use it with:

1. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`,
2. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`,
3. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-completion-handoff.md`

when you need the post-ladder order, gates, non-reopen rules, and the rule that there is no default Tranche 6.

## Governing Execution History

The relay ladder closed through five tranches.

Use these repo-local completion records for the landed implementation history:

1. `ops/agents/handoffs/2026-04-30-tcc-relay-tranche-1-shared-infra-schema-execution-completion-handoff.md`
2. `ops/agents/handoffs/2026-04-30-tcc-relay-tranche-2-staged-population-and-provenance-replay-execution-completion-handoff.md`
3. `ops/agents/handoffs/2026-04-30-tcc-relay-tranche-3-shared-calc-substrate-enablement-execution-completion-handoff.md`
4. `ops/agents/handoffs/2026-04-30-tcc-relay-tranche-4-read-only-control-plane-api-adoption-execution-completion-handoff.md`
5. `ops/agents/handoffs/2026-04-30-tcc-relay-tranche-5-browser-and-coordination-adoption-execution-completion-handoff.md`

## Current Lane State

The current relay lane state is:

1. the five-tranche implementation ladder is closed PASS,
2. Phase 1 hosted proof is closed PASS,
3. the first bounded Phase 2 compare slice is closed PASS in repo and on promoted host,
4. Phase 3 write-workflow design authoring is now closed PASS in repo as a design-only lane,
5. no relay write workflow opens now,
6. deferred enrichment remains a later separately governed phase and requires candidate-specific operator-need evidence plus a separately authored implementation scoping packet before any later write lane can reopen.

Current post-ladder authority and execution surfaces:

1. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`
2. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
3. `TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
4. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
5. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md`
6. `TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md`
7. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-completion-handoff.md`

Current feature-intake surface for relay compare expansion:

1. use `docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md` when evaluating exploratory relay-compare concepts against the bounded Phase 2 lane.

## Non-Reopen Rules

The following protections remain active across the landed ladder and post-ladder work:

1. no default Tranche 6,
2. no silent reopening of the five-tranche ladder,
3. no writes unless a later authority packet explicitly opens them,
4. no browser-direct database access,
5. no browser-side relay evaluator substitution,
6. no recommendation, ranking, or optimizer behavior that hides source identity,
7. curve identity remains source-faithful as storage family plus constants-or-points,
8. unsupported-family posture must remain explicit rather than hidden.

Use `TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md` plus the adjacent Phase 2 and Phase 3 completion handoffs as the controlling repo-local source for those rules.

## How To Use This Index

If you need to answer a relay governance question, use this order:

1. start with this index,
2. open the repo-local handoff or relay memo named in the relevant section,
3. open the matching repo-local completion handoff for the live execution or closure state,
4. only then inspect code, runtime proof, or evidence surfaces.

If you need to execute current relay work, use this order:

1. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md` to see the final Phase 2 proof floor,
2. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md` only as the closed hosted-recovery record,
3. open `TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md` when evaluating bounded compare expansion ideas,
4. open `TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md`,
5. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-completion-handoff.md`,
6. do not author or execute any new relay implementation packet unless candidate-specific operator-need evidence exists and a separate repo-owned scoping surface explicitly reopens the lane.

## Bottom Line

The TCC relay lane has governance and guidelines, but they are packetized.

The current master governance surface is the repo-local relay memo and handoff stack, with the continuity and tranche-completion handoffs preserving the governing relay path, Phase 2 acting as the closed read-only browser proof floor, and the closed Phase 3 decision memo plus completion handoff acting as the current repo-local relay closure record.