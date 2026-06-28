# D4/D5 Governed Generation (Phase 2 / D-C) -- Design (Rev 2)

**Date:** 2026-06-27
**Lane:** `lvbreaker/tcc-79-d4d5-governed-generation` (off main `6e288120`)
**Status:** Rev 2 (operator review folded: materialized_owner gate, exact per-class manifests,
temp-stage row-level apply, governed-vs-direct parity regression, explicit no-apply stop line).
Build-only slice; NO prod apply.

## Goal
Replace the Path-B direct-Access dry-run generator with a generator that reads the breaker style
D4/D5 source from the GOVERNED `access_raw` (`tcc_fidelity_governed`) and emits provenance-stamped,
fail-closed `029`/`030` DATA SQL. The transform logic is unchanged; only the SOURCE, the provenance,
and the guards are new. This is D-C: generate-from-governed, not direct Access.

## Why (the corrected premise, now satisfied)
Phase 1 materialized a durable, checksum-validated `access_raw` in `tcc_fidelity_governed`
(run_id `c15adaef-20260608T210440`; ICCB/MCCB/PCB checksum_reconciliation matches=True; key_quality
ID-unique 608/10335/3279). The prod population SQL must derive from THAT governed mirror, with the
provenance travelling in the SQL header, not from a re-read of `D:\TCC_NEW.accdb`.

## Source swap (the only logic change)
- FROM: `access_raw."BreakerICCBStyles"` / `"BreakerMCCBStyles"` / `"BreakerPCBStyles"` in
  `tcc_fidelity_governed` (psycopg). DETERMINISM (Rev 2.1): every class read uses `ORDER BY "ID"` so the
  generated SQL chunk order AND the report samples are byte-stable across runs (a provenance + diff
  requirement; Postgres does not guarantee row order without it).
- The transform is COPIED VERBATIM from the proven, Codex-converged dry-run generator
  (`infra/database/sandbox/breaker/d4d5-population-dryrun/dry_run_direct_access_population_generator.py`):
  D4 6-col map (ICCB/MCCB only); D5 5-block map (`inst_override`=InstOvr*, `ninst_override`=NInstOvr*,
  `brk_times`=BrkTimes*, `r_int`=r_int_*, `r_iec`=r_iec_*) keyed by verbatim Access column name;
  `source_id` = Access `ID`; chunked writes. Verified against the queued DDL: 029 (6 cols x
  brk_iccb/brk_mccb) + 030 (`brk_style_native_overrides`, PK `(breaker_class, source_id)`).
- Type fidelity: values arrive as PG types from `access_raw`, not pyodbc. `InstOvrAmps` is
  `double precision` in access_raw, so the `> 0` real-override metric is numerically clean. Other
  block values keep whatever PG type the harness type-map assigned; the JSONB serializer coerces
  Decimal/bytes/datetime. A governed-vs-direct parity regression (below) proves no representation drift.

## Artifacts (separate per migration -- maps to the separate-go apply chain)
- `029_d4_data.sql`  -- D4 staged UPDATEs (brk_iccb_styles + brk_mccb_styles).
- `030_d5_data.sql`  -- D5 staged INSERTs (brk_style_native_overrides).
- `generation_report.json` -- per-class counts / D4 non-null per col / D5 block-present / real_override
  / rating_only / samples + the full provenance block.

## Provenance header (embedded in EACH emitted SQL)
`run_id`, `snapshot_id`, governed source DB name, Access `source_sha256`, `frozen_copy_path`,
`driver`, and -- for each table that artifact carries -- `row_count`, `checksum`, `matches`. Plus
`generated_at`, `generator_version`. SQL comment block; integrity enforced by the gates (generation
time) and the in-tx invariants (apply time).

## Pre-emit fail-closed gates (the generator REFUSES + exits nonzero)
1. **Wrong source DB:** read connection `current_database()` must equal `tcc_fidelity_governed`
   (fence before any query).
2. **run_id missing/ambiguous:** accept explicit `--run-id`; if omitted, default to the sole row in
   `access_meta.extraction_run`. Refuse if the requested run_id is absent OR (none requested) there is
   not exactly one run.
3. **materialized_owner mismatch (NEW -- Rev 2):** for EACH of the 3 style tables,
   `access_meta.materialized_owner` (layer=`access_raw`, table_name) must equal the SELECTED run_id.
   This is the load-bearing gate: the harness keeps historical evidence by run_id while `access_raw` is
   latest-materialized, so an older `--run-id` could otherwise pass historical checksum/key-quality
   rows while we read NEWER table contents. Refuse on any mismatch (the mixed-evidence class
   `materialized_owner` exists to close).
4. **Style reconciliation not True:** for EACH of ICCB/MCCB/PCB, `checksum_reconciliation.matches`
   must be True for the selected run_id. Refuse otherwise.
5. **Key quality not unique:** for EACH style parent, `key_quality.is_unique` must be True (candidate
   `['ID']`). Refuse otherwise.
6. **Required columns absent (EXACT manifest -- Rev 2):** assert every column in the per-class manifest
   (Appendix A) is present in `access_raw` -- an explicit enumerated list, NOT a prefix wildcard, so a
   single vanished `InstOvr*`/`r_int_*` field is caught while sibling fields remain. PCB's extra
   `r_int_ninst_*` (3) and `r_iec_ninst_*` (11) are represented intentionally. Refuse on any missing
   column. (The manifest is pinned from the governed `access_raw` schema and committed as a constant.)

## Policy (a) preserved (operator-ratified)
Carry the raw override/timing/rating blocks VERBATIM. `InstOvrAmps > 0` is a REPORT metric only, never
a filter. Rating-only styles retained. One row per style with >= 1 non-null D5 block (~14222 total).

## Apply pattern -- D1 = A (ratified), with row-level guards (Rev 2)
The emitted DATA SQL is the SINGLE prod-bound artifact (same file dry-run on a clone, then applied to
prod governed `tcc` on the gate -- the 027/028 model). NO `%dryrun%` name lock; NO divergent variants.
Counts alone are insufficient for data SQL (IDs/classes can diverge while counts match), so each
artifact uses a TEMP-STAGE + ROW-LEVEL-COVERAGE pattern, all inside one `BEGIN; ... COMMIT;` with
`ON_ERROR_STOP` and an in-tx DO-guard so a RAISE aborts every following write even under `psql -f`:

**029 (D4):** stage `(source_id, tmt_*)` rows into a TEMP table, then assert before writing:
- stage row count == the header D4 count for that class;
- no duplicate `source_id` in stage;
- DDL present: the 6 `tmt_*` target columns exist on `tcc.brk_<class>_styles` (029 DDL applied);
- coverage: EVERY stage `source_id` joins EXACTLY ONE `tcc.brk_<class>_styles` row (anti-join empty;
  `source_id` is UNIQUE per mig 007).
Then `UPDATE ... FROM stage`; assert rows-updated == stage count.

**030 (D5):** stage `(breaker_class, source_id, inst_override, ninst_override, brk_times, r_int, r_iec)`
into a TEMP table, then assert:
- stage row count == the header D5 count (per-class and total);
- no duplicate `(breaker_class, source_id)` in stage;
- DDL present: `tcc.brk_style_native_overrides` exists with the PK `(breaker_class, source_id)`;
- coverage: EVERY stage `(breaker_class, source_id)` joins the corresponding `tcc.brk_<class>_styles`
  by `source_id` (anti-join empty) -- the side table is not a declared FK, so the SQL asserts coverage.
Then `INSERT ... SELECT FROM stage ON CONFLICT (breaker_class, source_id) DO UPDATE` (idempotent);
assert inserted+updated == stage count. EXTRA-ROW GUARD (Rev 2.1): a post-write assertion that, for EACH
class, the count of `brk_style_native_overrides` rows with that breaker_class equals the staged keyset for
that class -- equivalently, NO target `(breaker_class, source_id)` exists outside the stage (anti-join
target-minus-stage = 0). ON CONFLICT only makes the staged rows stable; this guard fails closed if a
polluted prior apply left extra rows the stage does not cover.

The dry-run validates this exact SQL on a fresh clone (029/030 DDL applied first); prod apply via
`apply_migration` preflight on the gate.

## Dry-run (after build, before any apply decision)
Fresh dated clone off `tcc_breaker_baseline_20260625` (e.g. `tcc_breaker_d4d5_gen_<date>`), NOT the
79audit clone. Apply 029 DDL + 030 DDL, then the generated 029/030 data SQL. Verify: counts
608/10335/3279 (D5 total 14222), and the explicit partition (verified live 2026-06-27 via read_class):
real_override 241/129/317 (687) + rating_only 367/10204/2962 (13533) + neither 0/2/0 (2) = 14222, where
rating_only = no real override AND r_int/r_iec present, and neither = no real override and no rating
(MCCB has the only 2 neither styles). All rating_only AND neither rows are RETAINED (policy (a)); the
InstOvrAmps>0 metric drops nothing. All row-level assertions pass, idempotent double-apply stable,
provenance header matches the governed run.

## Testing (TDD) -- includes the governed-vs-direct parity regression (Rev 2)
- Gate unit tests: each of the 6 pre-emit gates refuses on its own violation (wrong DB, absent/ambiguous
  run_id, materialized_owner mismatch, a forced matches=False, a forced non-unique key, a dropped
  manifest column) and passes on the clean governed state.
- **Parity regression:** generate from governed access_raw AND from the frozen direct-Access read for
  the same frozen sha; assert IDENTICAL per-class counts (D4 update / D5 insert / real_override /
  rating_only) and identical representative JSON block shape (key set + value representation, incl.
  Decimal/text/numeric and the InstOvrAmps coercion). Proves the source swap introduced no drift.
- Row-level apply assertions exercised against a disposable test DB (TDD on `tcc_fidelity_test` for the
  generator; the full clone dry-run is the live acceptance).

## STOP LINE (explicit -- Rev 2)
029/030 are STILL NOT applied to prod by this slice. The deliverable is the generator + the two
generated SQL artifacts + the clone dry-run evidence + the Codex/opus review record. Prod apply waits
for SEPARATE operator gos, in order: 029 DDL -> governed 029 data -> 030 DDL -> governed 030 data.

## Out of scope
- Prod apply of 029/030 (separate gos, above).
- `031` view-transition (authored AFTER population; carries the 028 frame_counts perf-fix).
- F-79-03 row-level frame anti-join (separate, parked Access-evidence track).

## Decisions
- **D1 -- apply pattern: RATIFIED A** -- single prod-bound artifact, no `%dryrun%` lock, guarded by
  the temp-stage row-level invariants above (not counts alone); dry-run validates on the clone.
- **D2 -- run_id selection:** default to the sole `extraction_run` row, accept explicit `--run-id`,
  refuse if absent/ambiguous. Confirmed.
- **D3 -- artifact split:** separate `029_d4_data.sql` + `030_d5_data.sql`. Confirmed.

## Appendix A -- exact per-class required-column manifest (pinned from governed `access_raw` 2026-06-27)
Common to ALL three classes: `ID` (integer), `InstOvrAmps` (double precision).
D5 blocks (verbatim Access names):
- `InstOvr*` (16, all classes): InstOvrAmps, InstOvrMinTolerance, InstOvrMaxTolerance, InstOvrClrDelayTime,
  InstOvrClrRadius, InstOvrOpnDelayTime, InstOvrOpnRadius, InstOvrNoteText, InstOvrClrCurve, InstOvrClrChar,
  InstOvrCurveCalcClr, InstOvrClrEnteredAt, InstOvrOpenCurve, InstOvrOpenChar, InstOvrCurveCalcOpen,
  InstOvrOpenEnteredAt.
- `NInstOvr*` (15, all classes): NInstOvrAmps, NInstOvrMinTolerance, NInstOvrMaxTolerance,
  NInstOvrClrDelayTime, NInstOvrClrRadius, NInstOvrOpnDelayTime, NInstOvrOpnRadius, NInstOvrClrCurve,
  NInstOvrClrChar, NInstOvrCurveCalcClr, NInstOvrClrEnteredAt, NInstOvrOpenCurve, NInstOvrOpenChar,
  NInstOvrCurveCalcOpen, NInstOvrOpenEnteredAt.
- `BrkTimes*` (4, all classes): BrkTimesMechOpening50, BrkTimesMechOpening60, BrkTimesSTDelayBand50,
  BrkTimesSTDelayBand60.
- `r_int_*`: ICCB/MCCB (6): r_int_inst_240/480/600, r_int_series_240/480/600. PCB (9): the 6 +
  r_int_ninst_240/480/600.
- `r_iec_*`: ICCB/MCCB (11): r_iec_inst_220/230/240/380/400/415/440/500/550/690/1000. PCB (22): the 11 +
  r_iec_ninst_220/230/240/380/400/415/440/500/550/690/1000.
D4 (ICCB/MCCB ONLY; PCB has none): TMT_TCCNumber, TMT_Notes, TMT_TripPlug, TMT_BreakerType,
TMT_ThermalMagnetic, TMT_Thermal.
Per-class D5 block-col totals: ICCB/MCCB = 52; PCB = 66. (Non-carried cols excluded by design:
BreakerID, Style, Ordinal, r_cont_current, c_testing_std, TMT_Use_SST, TMT_SST_Mfr, TMT_SST_Type,
TMT_SST_Style.)
