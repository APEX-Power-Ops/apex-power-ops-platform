# TCC Relay Execution Tranche Planning Handoff

Date: 2026-04-30
Status: Historical post-006 boundary; superseded by the Tranche 1 schema execution handoff
Authority: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- The Tranche 1 execution packet is now on disk at `Platform-Authority/TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md`.
- Use `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-1-shared-infra-schema-execution-handoff.md`
	for the current continuation boundary.

---

## Objective

Carry the relay lane forward after Packet 006 without reopening planning.

The next move is execution, but only in the smallest schema-first slice.

---

## Mandatory Read Set

Read these surfaces before any relay implementation authoring:

1. `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
4. `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
5. `D:\apex-power-ops-platform\spec\relay-family-scoping\09-dvleng-semantic-decode.md`
6. `D:\apex-power-ops-platform\spec\relay-family-scoping\11-meq-decode.md`

---

## Packet 006 Rulings You Must Treat As Canonical

### Tranche order

1. shared-infra schema substrate,
2. staged population and provenance replay,
3. shared calc substrate enablement,
4. read-only control-plane API adoption,
5. browser and coordination adoption.

### Current GO boundary

Only Tranche 1 is approved to open next, and only through a separately authored
execution packet.

### Current NO-GO boundary

Do not open:

1. multi-tranche implementation,
2. runtime-first relay implementation,
3. API-first or UI-first exposure,
4. deferred enrichment tables,
5. silent external-work merges.

---

## What The Next Execution Packet Must Cover

The next execution packet must stay limited to Tranche 1 and must target:

1. `apex-power-ops-platform/infra/database/`

Its allowed scope is:

1. Packet 003-admitted shared-infra relay tables only,
2. schema-local validation,
3. schema-local rollback.

Its prohibited scope is:

1. data loads,
2. calc-engine work,
3. API work,
4. browser work,
5. deferred enrichment tables.

---

## Expected Outcome From This Handoff

If followed correctly, the next repo-native move will be a narrow relay schema
execution packet with low blast radius and a clean rollback path, rather than a
combined schema-load-runtime launch.