# TCC Relay Tranche 2 Staged Population And Provenance Replay Execution — Completion Handoff

Date: 2026-04-30
Status: Closed PASS — Tranche 2 staged population and provenance replay

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-2-staged-population-and-provenance-replay-execution-handoff.md`
Authority packet: `Platform-Authority/TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md`
Upstream tranche planner: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`

---

## §1. Outcome

Relay Tranche 2 lands **closed PASS** in the governed shared-infra lane.

The relay snapshot, staged population, and provenance replay are now
implemented under:

1. `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/`
2. `infra/database/migrations/work/012_tcc_relay_staged_population.sql`
3. `infra/database/migrations/work/MANIFEST.md`

This tranche also closed the source-backed substrate gaps discovered during live
execution:

1. `RelayRanges.RangeKey 101` replays to `td_section`,
2. relay numeric source-faithful columns widened to `numeric(20,6)`,
3. `tcc_relay_curves_tcp.horizontal_amps_code` now preserves blank source values as null,
4. TCP point uniqueness is keyed by `source_ordinal` so real duplicate
   `time_dial` rows are preserved.

---

## §2. Required outputs delivered

| # | Required output | Path / artifact |
|---|---|---|
| 1 | Immutable relay snapshot root | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/` |
| 2 | Snapshot manifest | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/manifest/00_snapshot_manifest.md` |
| 3 | Validation checklist | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/manifest/01_validation_checklist.md` |
| 4 | Governed replay file | `infra/database/migrations/work/012_tcc_relay_staged_population.sql` |
| 5 | Stable replay proof | two successful executions of `012_tcc_relay_staged_population.sql` against `apex_pm_stage` |
| 6 | Completion handoff | this file |

---

## §3. Files changed

| # | Surface | Action |
|---|---|---|
| 1 | `infra/database/migrations/work/010_tcc_relay_tables.sql` | Edited — source-backed substrate corrections |
| 2 | `infra/database/migrations/work/012_tcc_relay_staged_population.sql` | Added |
| 3 | `infra/database/migrations/work/MANIFEST.md` | Edited |
| 4 | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/` | Added 22 admitted CSV files |
| 5 | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/LINEAGE-NOTE.md` | Added |
| 6 | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/manifest/00_snapshot_manifest.md` | Added |
| 7 | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/manifest/01_validation_checklist.md` | Added |
| 8 | `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-2-staged-population-and-provenance-replay-execution-handoff.md` | Edited — status / supersession only |

**Untouched (intentional):**

1. `packages/calc-engine/relay/`
2. `apps/control-plane-api/`
3. `apps/operations-web/`
4. deferred relay enrichment tables
5. browser and coordination surfaces

---

## §4. Verification

### Database execution target

Local staging database:

1. `apex_pm_stage`
2. user: `apex_pm_stage_user`

### Replay result

`012_tcc_relay_staged_population.sql` executed successfully twice against the
same immutable snapshot with stable counts.

### Key validation facts

1. raw snapshot admitted source files: **22**
2. rejected orphan `RelayDevices` rows: **342**
3. loaded relay roots: **1442**
4. loaded relay devices: **6850**
5. loaded relay line sections: **23387**
6. loaded relay td sections: **6635**
7. loaded relay ranges: **34213**
8. loaded relay discrete values: **38679**
9. loaded TCP parent rows: **16183**
10. loaded TCP normalized points: **1570700**
11. deferred enrichment tables present: **0**

### Fidelity proof

1. source-side `RangeKey` classification remains 100% resolved.
2. loaded `RelayRanges` counts match the admissible loaded-parent expectation exactly.
3. loaded TCP points equal the expected point count for admitted TCP parents exactly.
4. the lower loaded counts relative to raw source totals are explained by governed upstream exclusions, not by replay drift.

---

## §5. Acceptance criteria

1. ✅ One immutable relay snapshot id was fixed and preserved repo-natively.
2. ✅ Replay populated provenance-bearing rows into the existing relay substrate.
3. ✅ Orphan `RelayDevices` rejection was proven explicitly.
4. ✅ Replay from clean state was demonstrated by rerunning the same file successfully.
5. ✅ Deferred enrichment tables remain absent.
6. ✅ No runtime consumer lane was opened.

---

## §6. Hard limits honored

1. ✅ No calc-engine implementation.
2. ✅ No API implementation.
3. ✅ No browser or coordination implementation.
4. ✅ No deferred relay enrichment tables.
5. ✅ No live unversioned source reads during replay.
6. ✅ No all-at-once multi-tranche relay launch.

---

## §7. Downstream statement — Tranche 3 remains separate

This packet closes **Tranche 2 only**.

The next truthful move is a separately authored **Tranche 3 shared calc
substrate enablement execution packet**.

That next move must remain limited to:

1. `packages/calc-engine/relay/`,
2. family dispatch by canonical relay family code,
3. source-faithful curve identity,
4. no API or browser consumer yet.

---

## §8. Bottom line

The relay lane is now past schema-only existence and past data-free planning.
One immutable admitted snapshot is preserved in repo-native source-lineage, and
the governed replay path now loads that snapshot into the shared-infra relay
substrate with explicit orphan rejection, preserved provenance, stable reruns,
and continued runtime closure.

The next lane is no longer Tranche 2. It is the separately governed Tranche 3
shared calc substrate slice.