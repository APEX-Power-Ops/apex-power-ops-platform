# TCC Relay Runtime Adoption Scoping Handoff

Date: 2026-04-30
Status: Historical post-005 boundary; superseded by the Packet 006 execution-tranche planning handoff
Authority: `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- Packet 006 is now on disk at `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`.
- Use `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-execution-tranche-planning-handoff.md`
	for the current post-006 continuation boundary.

---

## Objective

Carry the relay lane forward after Packet 005's runtime-scoping ruling without
opening schema implementation, loads, or runtime code.

This handoff exists so the repo lane can open Packet 006 cleanly.

---

## Mandatory Read Set

Read these surfaces before any follow-on relay authoring:

1. `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
4. `D:\apex-power-ops-platform\spec\relay-family-scoping\09-dvleng-semantic-decode.md`
5. `D:\apex-power-ops-platform\spec\relay-family-scoping\REVIEW_NOTES.md`
6. `D:\apex-power-ops-platform\spec\relay-family-scoping\11-meq-decode.md`

---

## Packet 005 Rulings You Must Treat As Canonical

### Runtime order

1. `packages/calc-engine/relay/` first
2. read-only `apps/control-plane-api/` second
3. browser and coordination surfaces third, defaulting to `apps/operations-web/`

### Runtime contract posture

1. curve identity by storage family plus constants-or-points,
2. no analytical substitution for vendor-tabulated curves,
3. provenance-carrying runtime contracts,
4. no implied support for deferred enrichments or missing catalog-gap surfaces.

### Rollback posture

Later execution tranches must layer from least externally visible to most
externally visible so rollback can disable UI first, API second, and leave the
shared package isolated.

---

## What Remains Explicitly Blocked

1. migrations,
2. data loads,
3. any runtime implementation,
4. deferred platform-only enrichments,
5. catalog-gap resolution workstreams,
6. optimizer or write-back workflows.

---

## What Packet 006 Must Do

Packet 006 is now the next truthful repo-native move.

It must decide the smallest execution tranches for:

1. shared-infra schema implementation,
2. staged population,
3. shared calc substrate enablement,
4. read-only API adoption,
5. browser and coordination adoption,
6. validation and rollback gates between each tranche.

It must not bypass any Packet 003, Packet 004, or Packet 005 ruling.

---

## Expected Outcome From This Handoff

If followed correctly, the next relay move in the repo lane will be a clean
Packet 006 planning artifact that sequences implementation tranches without
reopening the already-closed governance and design stages.