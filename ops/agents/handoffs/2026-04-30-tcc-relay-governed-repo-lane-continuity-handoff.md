# TCC Relay Governed Repo-Lane Continuity Handoff

Date: 2026-04-30
Status: Ready for documentation-level continuity only
Authority: `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`
Upstream opener: `Platform-Authority/TCC-RELAY-STDLIB-INVESTIGATION-PACKET-2026-04-30.md`
External evidence packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- Packet 003 is now on disk at `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`.
- Use `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-shared-infra-landing-and-canonical-schema-design-handoff.md`
   for the current post-003 continuation boundary.

---

## Objective

Carry the isolated relay-family scoping work into the governed APEX repo lane
without treating the D: worktree as if it were already implementation authority.

This handoff authorizes the continuity move only at the packet and handoff
level. It does not authorize relay DDL, runtime code, backfills, or public
scope claims.

---

## Mandatory Read Set

Open these files before authoring any follow-on relay packet or touching any
repo implementation lane:

1. `Platform-Authority/TCC-RELAY-STDLIB-INVESTIGATION-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`
3. `source-domains/tcc_v5_backend/TCC_SCHEMA_GAP_ANALYSIS.md`
4. `source-domains/tcc_v5_backend/ACCESS_TO_SUPABASE_GAP_ANALYSIS.md`
5. `D:\apex-power-ops-platform\spec\relay-family-scoping\00-README.md`
6. `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`
7. `D:\apex-power-ops-platform\spec\relay-family-scoping\REVIEW_NOTES.md`
8. `D:\apex-power-ops-platform\spec\relay-family-scoping\11-meq-decode.md`

---

## Continuity Ruling

### What migrates now

The relay lane may now migrate into the repo for continuity in exactly two
forms:

1. governed authority packets in `Platform-Authority/`
2. operator-facing bounded handoffs in `apex-power-ops-platform/ops/agents/handoffs/`

This means the repo can now carry the relay investigation forward honestly,
with citations back to the D: evidence packet, without copying any runtime or
schema proposal directly into implementation lanes.

### What does not migrate yet

Do not move this work yet into:

1. `apex-power-ops-platform/infra/database/`
2. `packages/calc-engine/`
3. `apps/control-plane-api/`
4. any UI lane
5. any import or staging execution lane

Those surfaces remain blocked until the later relay packets explicitly open
them.

---

## When The Repo Lane May Advance

Use the following staged rule:

### Stage A - Immediate and allowed now

Author and maintain repo-native governance artifacts only.

Exit condition:

1. Packet 002 exists on disk
2. this handoff exists on disk
3. the D: packet is treated as evidence input rather than authority output

### Stage B - Next truthful move

Author Packet 003 in `Platform-Authority/` to decide the governed shared-infra
landing shape and canonical relay schema boundary.

Exit condition:

1. the canonical target-home is explicit
2. the first governed `tcc_relay_*` boundary is explicit
3. platform-only enrichments are either admitted or deferred explicitly

### Stage C - After Packet 003 closes

Author Packet 004 to define extraction, provenance, replayability, and staging.

Exit condition:

1. source-to-target mapping rules are explicit
2. validation gates exist for later execution
3. no ambiguity remains about what data can be loaded and how it is traced

### Stage D - Only after Packets 003 through 005 close cleanly

Open execution planning for actual repo implementation.

Only then may later packets authorize bounded work in:

1. `apex-power-ops-platform/infra/database/`
2. `packages/calc-engine/`
3. `apps/control-plane-api/`
4. adjacent UI surfaces

---

## How The Migration Happens

Use this exact migration method:

1. cite the D: relay-family packet as reviewed evidence only
2. restate the accepted findings in repo-native packets before relying on them
3. keep source authority, runtime-characterization authority, and target schema
   authority separate in every follow-on document
4. treat any D: schema proposal as candidate design input until a governed C:
   packet explicitly adopts or rejects each slice
5. keep implementation out of scope until the relevant packet opens that lane

Negative rule:

- do not copy the D: markdown set wholesale into the repo and call that
  continuity

Continuity means governed restatement, not silent relocation.

---

## First Repo-Native Follow-On Deliverables

The next truthful repo-native deliverables are:

1. Packet 003 under `Platform-Authority/`
2. if Packet 003 opens a bounded schema-design slice cleanly, a paired handoff
   in `ops/agents/handoffs/` describing that design-only step

Do not skip directly from this handoff to migrations, API endpoints, or calc
evaluators.

---

## Specific Questions Packet 003 Must Resolve

Packet 003 should take the following inputs as live calls rather than silently
assuming them:

1. whether `tcc_relay_ranges` stays polymorphic or is split by parent type
2. whether the three platform-only relay enrichments land in the first governed
   schema or are deferred
3. whether the first governed schema mirrors source families verbatim or starts
   with a smaller runtime-oriented subset
4. how provenance columns and source keys are preserved from day one

---

## Hard Limits

1. No relay DDL.
2. No runtime code.
3. No data backfill.
4. No claim that relays are already part of active APEX platform scope.
5. No silent promotion of external documents into implementation authority.

---

## Expected Outcome From This Handoff

If followed correctly, the relay lane will have:

1. a governed continuity bridge from D: into the APEX repo
2. a truthful next packet boundary for Packet 003
3. a clean rule for when repo implementation lanes may open

If any follow-on step needs schema or runtime edits before Packet 003 through
005 close, treat that as a blocker and return a governance exception request
rather than widening the lane implicitly.