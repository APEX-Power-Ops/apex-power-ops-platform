# TCC Relay Shared-Infra Landing And Canonical Schema Design Handoff

Date: 2026-04-30
Status: Historical post-003 boundary; superseded by the Packet 004 staging handoff
Authority: `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- Packet 004 is now on disk at `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`.
- Use `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-extraction-mapping-and-provenance-staging-handoff.md`
   for the current post-004 continuation boundary.

---

## Objective

Carry the relay lane forward after Packet 003's design ruling without jumping
into DDL, import execution, or runtime code.

This handoff exists so the repo lane can use the newly governed design decisions
and open Packet 004 cleanly.

---

## Mandatory Read Set

Read these surfaces before any follow-on relay authoring:

1. `Platform-Authority/TCC-RELAY-STDLIB-INVESTIGATION-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
4. `source-domains/tcc_v5_backend/TCC_SCHEMA_GAP_ANALYSIS.md`
5. `D:\apex-power-ops-platform\spec\relay-family-scoping\REVIEW_NOTES.md`
6. `D:\apex-power-ops-platform\spec\relay-family-scoping\11-meq-decode.md`

---

## Packet 003 Rulings You Must Treat As Canonical

### Shared-infra landing

Relay shared-infra design belongs later under `apex-power-ops-platform/infra/database/`.
It does not belong in source-lane migrations or runtime lanes.

### Canonical design decisions

Packet 003 adopted:

1. `P1` for `tcc_relay_ranges`
2. `C2` typed per-family curve tables
3. `T2` tall normalized TCP points
4. `D-D` hybrid device-function storage with the reviewer refinements
5. `E2` migrations-only evolution posture

### First governed schema boundary

The first governed relay schema is the source-faithful catalog and curve
substrate only. It includes:

1. relay catalog roots and device/section tables
2. polymorphic ranges and discrete values
3. typed family parent tables
4. typed constant tables
5. normalized TCP points
6. the limited derived metadata layer on devices and line sections needed for
   queryability and later calc dispatch

It excludes the platform-only enrichment tables for now.

---

## What Is Explicitly Deferred

Do not silently reopen the following in Packet 004:

1. `tcc_relay_interlocks`
2. `tcc_relay_diff_characteristics`
3. `tcc_relay_impedance_circles`
4. frequency / voltage / directional setpoint tables
5. MEQ dedup or UI-only normalization overlays

Those are deferred design surfaces, not forgotten ones.

---

## What Packet 004 Must Do

Packet 004 is now the next truthful repo-native move.

It must produce:

1. extraction mechanics by source artifact
2. source-to-target mapping by admitted table family
3. replay and snapshot rules
4. validation gates for any later DDL or load execution

It must preserve Packet 003's fidelity rules:

1. source IDs preserved where available
2. source constants and TCP points preserved verbatim
3. source curve names preserved as metadata only
4. no import-time substitution of analytical forms for vendor-tabulated curves

---

## Hard Limits

1. No relay DDL.
2. No data backfill.
3. No calc-engine implementation.
4. No API or UI work.
5. No reclassification of deferred platform-only enrichments as first-boundary
   schema without a new governed packet.

---

## Expected Outcome From This Handoff

If followed correctly, the next relay move in the repo lane will be a clean
Packet 004 authority artifact that is able to drive later implementation
without re-litigating the base landing and canonical schema decisions.

If a follow-on step needs migrations or runtime code before Packet 004 closes,
stop and return a blocker note rather than widening the lane implicitly.