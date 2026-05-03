# TCC Relay Tranche 1 Shared-Infra Schema Execution Handoff

Date: 2026-04-30
Status: Historical pre-execution boundary; superseded by the Tranche 1 completion handoff
Authority: `Platform-Authority/TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- Tranche 1 is now closed PASS via `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-1-shared-infra-schema-execution-completion-handoff.md`.
- The next truthful move is a separately authored Tranche 2 staged population and provenance replay execution packet.

---

## Objective

Carry the relay lane from planning into the smallest approved implementation
slice.

Only the shared-infra schema substrate is in scope.

---

## Mandatory Read Set

Read these surfaces before touching the migration lane:

1. `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md`
4. `Platform-Authority/DATABASE-OWNERSHIP-SPLIT-2026-04-12.md`
5. `apex-power-ops-platform/infra/database/migrations/work/MANIFEST.md`

---

## Canonical Scope Boundary

The next implementation move is limited to:

1. `infra/database/migrations/work/010_tcc_relay_tables.sql`
2. `infra/database/migrations/work/011_tcc_relay_indexes.sql`
3. `infra/database/migrations/work/MANIFEST.md`

And to the Packet 003-admitted relay substrate tables only.

---

## Explicitly Blocked In This Slice

Do not open:

1. staged population,
2. calc-engine work,
3. API work,
4. browser work,
5. deferred enrichment tables,
6. app-local or lineage-lane migrations.

---

## Expected Outcome From This Handoff

If followed correctly, the next repo-native move will create the relay schema
substrate with low blast radius, no runtime exposure, and a clean schema-local
rollback path.