# TCC Relay Tranche 2 Staged Population And Provenance Replay Execution Handoff

Date: 2026-04-30
Status: Historical pre-execution boundary; superseded by the Tranche 2 completion handoff
Authority: `Platform-Authority/TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
Prior tranche closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-1-shared-infra-schema-execution-completion-handoff.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- Tranche 2 is now closed PASS via `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-2-staged-population-and-provenance-replay-execution-completion-handoff.md`.
- The next truthful move is a separately authored Tranche 3 shared calc substrate enablement execution packet.

---

## Objective

Carry the relay lane from schema-only existence into the smallest approved
data-bearing slice.

Only immutable snapshot capture, staged population, provenance replay, and
orphan rejection are in scope.

---

## Mandatory Read Set

Read these surfaces before touching the replay lane:

1. `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md`
4. `Platform-Authority/DATABASE-OWNERSHIP-SPLIT-2026-04-12.md`
5. `apex-power-ops-platform/infra/database/migrations/work/010_tcc_relay_tables.sql`
6. `apex-power-ops-platform/infra/database/migrations/work/MANIFEST.md`

---

## Canonical Scope Boundary

The next implementation move is limited to:

1. one immutable snapshot root under `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/`,
2. one governed replay file: `infra/database/migrations/work/012_tcc_relay_staged_population.sql`,
3. one manifest update in `infra/database/migrations/work/MANIFEST.md`.

And to the Packet 004-admitted relay source tables only.

---

## Explicitly Blocked In This Slice

Do not open:

1. new relay schema,
2. calc-engine work,
3. API work,
4. browser work,
5. deferred enrichment tables,
6. live unversioned source reads,
7. app-local or lineage-lane runtime migrations.

---

## Expected Outcome From This Handoff

If followed correctly, the next repo-native move will produce one immutable
relay snapshot, one replayable staged population path into the existing relay
substrate, explicit orphan rejection evidence, and a completion handoff proving
that runtime consumers still remain unopened.