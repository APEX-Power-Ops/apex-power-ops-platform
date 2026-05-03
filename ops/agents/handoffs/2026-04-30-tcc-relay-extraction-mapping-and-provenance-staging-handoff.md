# TCC Relay Extraction, Mapping, And Provenance Staging Handoff

Date: 2026-04-30
Status: Historical post-004 boundary; superseded by the Packet 005 runtime-scoping handoff
Authority: `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

Supersession note:

- Packet 005 is now on disk at `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`.
- Use `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-runtime-adoption-scoping-handoff.md`
    for the current post-005 continuation boundary.

---

## Objective

Carry the relay lane forward after Packet 004's extraction and provenance
ruling without opening migrations, data loads, or runtime code.

This handoff exists so the repo lane can open Packet 005 cleanly and keep the
staging boundary intact.

---

## Mandatory Read Set

Read these surfaces before any follow-on relay authoring:

1. `Platform-Authority/TCC-RELAY-SOURCE-INVENTORY-AND-AUTHORITY-CLASSIFICATION-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-SHARED-INFRA-LANDING-AND-CANONICAL-SCHEMA-DESIGN-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
4. `source-domains/tcc_v5_backend/TCC_SCHEMA_GAP_ANALYSIS.md`
5. `D:\apex-power-ops-platform\spec\relay-family-scoping\01-csv-inventory.md`
6. `D:\apex-power-ops-platform\spec\relay-family-scoping\REVIEW_NOTES.md`

---

## Packet 004 Rulings You Must Treat As Canonical

### Admitted source set

Only the Packet 003-admitted relay catalog and curve surfaces are in scope for
later staging and load execution.

### Mapping posture

1. root catalog and device surfaces map 1:1 by preserved source ids,
2. typed family parent tables map 1:1 by preserved source ids,
3. typed constant tables map 1:1 by preserved source rows,
4. TCP rows normalize into ordered points keyed by `(tcp_parent_id, time_dial,
   current_index)`.

### Provenance posture

Later execution must preserve snapshot id, source table, and source row identity
or composite key for every governed row.

### Validation posture

No later implementation packet may open without snapshot, relationship,
target-shape, and policy gates tied back to Packet 004.

---

## What Remains Explicitly Blocked

1. relay DDL,
2. data backfill,
3. calc-engine implementation,
4. API or UI work,
5. deferred platform-only enrichment tables.

---

## What Packet 005 Must Do

Packet 005 is now the next truthful repo-native move.

It must decide:

1. which runtime surfaces may consume the governed relay substrate,
2. whether calc-engine, API, and UI work should open and in what order,
3. which runtime validations and rollback rules would be required.

It must not reopen Packet 003 or Packet 004 decisions unless it returns a
governance exception request.

---

## Expected Outcome From This Handoff

If followed correctly, the next relay move in the repo lane will be a clean
Packet 005 scoping artifact that can later sequence runtime work without
bypassing the staging and provenance rules already fixed on disk.