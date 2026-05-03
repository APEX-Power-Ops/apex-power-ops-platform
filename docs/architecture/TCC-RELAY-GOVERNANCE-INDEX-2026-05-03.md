# TCC Relay Governance Index

Date: 2026-05-03
Status: Active repo-local governance index
Scope: Provide one repo-local index for the governing relay packet stack, current lane state, and non-reopen rules without replacing the root authority packets

## Purpose

The TCC relay lane is governed by a packet stack, not by one monolithic spec.

This file exists to make the controlling surfaces easy to find from inside the repo.

This file is an index and routing surface only.

If any summary here conflicts with a root `Platform-Authority` packet, the root `Platform-Authority` packet wins.

## Authority Boundary

The relay governance boundary is:

1. root `Platform-Authority/` packets are the governing authority,
2. repo-local handoffs under `ops/agents/handoffs/` are the execution-routing and closure surfaces,
3. repo-local runtime and validation files under `apps/`, `packages/`, and `infra/` are implementation evidence,
4. reviewed D: worktree relay-family notes are evidence input only and are not implementation authority until restated in governed C: artifacts.

The key source-authority rule is fixed by:

1. `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`

That packet establishes:

1. the C: repo plus `Platform-Authority` files remain the governing surfaces,
2. the D: relay-family packet is reviewed evidence input,
3. reusable conclusions from D: must be restated in governed C: artifacts before they influence platform implementation.

## Master Governing Packets

Use these as the master relay governance stack.

### 1. Source and authority split

`Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`

Use this first when you need to know:

1. what counts as governing authority,
2. what counts as reviewed evidence only,
3. which source system governs lineage versus runtime characterization.

### 2. Runtime-order governance

`Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`

Use this when you need the approved runtime-consumer order.

The fixed order is:

1. shared calc package first,
2. read-only control-plane API second,
3. browser and coordination consumers third.

### 3. Execution-ladder governance

`Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`

Use this when you need the governing implementation ladder.

This packet fixes:

1. the five-tranche execution order,
2. tranche merge gates,
3. validation surfaces,
4. rollback posture,
5. the rule that the ladder must not be collapsed into one release unit.

### 4. Post-ladder governance

`Platform-Authority/TCC-RELAY-POST-LADDER-FOLLOW-ON-PLANNING-PACKET-2026-04-30.md`

Use this as the current top-level relay governance surface after the five-tranche ladder closed PASS.

This packet fixes:

1. the four-phase post-ladder order,
2. the post-ladder gates,
3. the non-reopen rules,
4. the rule that there is no default Tranche 6.

## Governing Execution History

The relay ladder closed through five tranches.

Use these packet families for the landed implementation history:

1. `Platform-Authority/TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-TRANCHE-3-SHARED-CALC-SUBSTRATE-ENABLEMENT-EXECUTION-PACKET-2026-04-30.md`
4. `Platform-Authority/TCC-RELAY-TRANCHE-4-READ-ONLY-CONTROL-PLANE-API-ADOPTION-EXECUTION-PACKET-2026-04-30.md`
5. `Platform-Authority/TCC-RELAY-TRANCHE-5-BROWSER-AND-COORDINATION-ADOPTION-EXECUTION-PACKET-2026-04-30.md`

The repo-local closure record for the ladder is:

1. `ops/agents/handoffs/2026-04-30-tcc-relay-tranche-5-browser-and-coordination-adoption-execution-completion-handoff.md`

## Current Lane State

The current relay lane state is:

1. the five-tranche implementation ladder is closed PASS,
2. Phase 1 hosted proof is closed PASS,
3. the first bounded Phase 2 compare slice is closed PASS in repo and on promoted host,
4. the next truthful relay move is Phase 3 write-workflow design authoring in design space only,
5. deferred enrichment remains a later separately governed phase.

Current post-ladder authority and execution surfaces:

1. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-SCOPING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`
4. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-3-WRITE-WORKFLOW-DESIGN-SCOPING-PACKET-2026-04-30.md`
5. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-3-WRITE-WORKFLOW-DESIGN-EXECUTION-PACKET-2026-05-03.md`
6. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`
7. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
8. `docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
9. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-handoff.md`
10. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
11. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md`
12. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-handoff.md`

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

Use `Platform-Authority/TCC-RELAY-POST-LADDER-FOLLOW-ON-PLANNING-PACKET-2026-04-30.md` as the controlling source for those rules.

## How To Use This Index

If you need to answer a relay governance question, use this order:

1. start with this index,
2. open the root `Platform-Authority` packet named in the relevant section,
3. open the matching repo-local handoff for the live execution or closure state,
4. only then inspect code, runtime proof, or evidence surfaces.

If you need to execute current relay work, use this order:

1. open `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`,
2. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md` to see the final Phase 2 proof floor,
3. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md` only as the closed hosted-recovery record,
4. open `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-3-WRITE-WORKFLOW-DESIGN-SCOPING-PACKET-2026-04-30.md`,
5. open `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-3-WRITE-WORKFLOW-DESIGN-EXECUTION-PACKET-2026-05-03.md`,
6. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-3-write-workflow-design-authoring-handoff.md`,
7. keep work in authority and handoff design surfaces only unless a later packet explicitly opens implementation.

## Bottom Line

The TCC relay lane has governance and guidelines, but they are packetized.

The current master governance surface is the root `Platform-Authority` relay packet stack, with `Packet 007` acting as the top-level post-ladder authority, Phase 2 acting as the closed read-only browser proof floor, and the Phase 3 design execution packet acting as the current active guide.