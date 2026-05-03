# TCC Relay Tranche 1 Shared-Infra Schema Execution — Completion Handoff

Date: 2026-04-30
Status: Closed PASS — Tranche 1 schema substrate only

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-1-shared-infra-schema-execution-handoff.md`
Authority packet: `Platform-Authority/TCC-RELAY-TRANCHE-1-SHARED-INFRA-SCHEMA-EXECUTION-PACKET-2026-04-30.md`
Upstream tranche planner: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`

---

## §1. Outcome

Relay Tranche 1 lands **closed PASS** in the governed shared-infra database
lane.

The relay schema substrate is now implemented under:

1. `infra/database/migrations/work/010_tcc_relay_tables.sql`
2. `infra/database/migrations/work/011_tcc_relay_indexes.sql`
3. `infra/database/migrations/work/MANIFEST.md`

Scope remained bounded exactly as authorized:

1. schema substrate only,
2. no data loads,
3. no calc-engine work,
4. no API work,
5. no browser work,
6. no deferred enrichment tables.

---

## §2. Required outputs delivered

| # | Required output | Path / artifact |
|---|---|---|
| 1 | Relay substrate table migration | `infra/database/migrations/work/010_tcc_relay_tables.sql` |
| 2 | Relay substrate index migration | `infra/database/migrations/work/011_tcc_relay_indexes.sql` |
| 3 | Work-lane manifest update | `infra/database/migrations/work/MANIFEST.md` |
| 4 | Executable staging validation | Local `apex_pm_stage` apply + verification queries in §4 |
| 5 | Completion handoff | this file |
| 6 | Exact downstream statement preserving Tranche 2 as a separate later move | §7 below |

---

## §3. Files changed

| # | Surface | Action |
|---|---|---|
| 1 | `infra/database/migrations/work/010_tcc_relay_tables.sql` | Added |
| 2 | `infra/database/migrations/work/011_tcc_relay_indexes.sql` | Added |
| 3 | `infra/database/migrations/work/MANIFEST.md` | Edited |
| 4 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-1-shared-infra-schema-execution-handoff.md` | Edited — status / supersession only |
| 5 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-execution-tranche-planning-handoff.md` | Edited earlier to historical during continuity advance |

**Untouched (intentional):**

1. all load and replay surfaces,
2. `packages/calc-engine/`,
3. `apps/control-plane-api/`,
4. `apps/operations-web/`,
5. all deferred enrichment tables,
6. all source-domain lineage migration lanes.

---

## §4. Verification

### Database execution target

Local staging database:

1. `apex_pm_stage`
2. user: `apex_pm_stage_user`

### Prerequisite note

The database initially exposed no tables, but the `work` schema and base
provenance enum set were already present. `pgcrypto` was not installed, so it
was added before the relay migration apply so `gen_random_uuid()` defaults could
resolve.

### Relay tranche apply result

The bounded relay substrate migrations were applied with `psql.exe` from the
local PostgreSQL 18 installation.

### Verification results

1. relay tables present in `work` schema: **21**
2. relay indexes named `idx_tcc_relay*`: **24**
3. relay-local enums present: **2**
4. deferred enrichment tables present: **0**
5. total rows across all new relay tables immediately after apply: **0**

Interpretation:

1. the schema substrate exists,
2. the tranche stayed schema-only,
3. deferred enrichments remained excluded,
4. no load or replay logic landed implicitly.

---

## §5. Acceptance criteria

1. ✅ Tranche 1 landed in the shared-infra `work` migration lane only.
2. ✅ Only the Packet 003-admitted relay substrate tables were introduced.
3. ✅ Relay-local enums and indexes exist for the substrate.
4. ✅ No data was loaded into the relay tables.
5. ✅ Deferred enrichment tables remain absent.
6. ✅ No runtime consumer lane was touched.

---

## §6. Hard limits honored

1. ✅ No staged population.
2. ✅ No calc-engine implementation.
3. ✅ No API implementation.
4. ✅ No browser or coordination implementation.
5. ✅ No app-local control-plane migration usage.
6. ✅ No source-domain lineage migration usage.
7. ✅ No deferred relay enrichment tables.
8. ✅ No all-at-once multi-tranche relay launch.

---

## §7. Downstream statement — Tranche 2 remains separate

This packet closes **Tranche 1 only**.

The next truthful move is a separately authored **Tranche 2 staged population
and provenance replay execution packet**.

That next move must remain limited to:

1. immutable snapshot use,
2. governed load and replay behavior,
3. provenance preservation,
4. orphan rejection,
5. no calc-engine, API, or browser work yet.

---

## §8. Bottom line

The relay lane is now past planning and past schema authorization. The first
implementation tranche is physically present in the governed shared-infra
database lane and has been applied successfully to the staging database without
opening any runtime consumer or data-loading surface.

The next lane is no longer Tranche 1. It is the separately governed Tranche 2
staged population and provenance replay slice.