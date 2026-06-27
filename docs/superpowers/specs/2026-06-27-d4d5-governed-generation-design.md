# D4/D5 Governed Generation (Phase 2 / D-C) -- Design

**Date:** 2026-06-27
**Lane:** `lvbreaker/tcc-79-d4d5-governed-generation` (off main `6e288120`)
**Status:** spec for operator ratification (build-only slice; NO prod apply)

## Goal
Replace the Path-B direct-Access dry-run generator with a generator that reads the breaker style
D4/D5 source from the GOVERNED `access_raw` (`tcc_fidelity_governed`) and emits provenance-stamped,
fail-closed `029`/`030` DATA SQL. The transform logic is unchanged; only the SOURCE, the provenance,
and the guards are new. This is D-C: generate-from-governed, not direct Access.

## Why (the corrected premise, now satisfied)
Phase 1 materialized a durable, checksum-validated `access_raw` in `tcc_fidelity_governed`
(run_id `c15adaef-20260608T210440`; ICCB/MCCB/PCB checksum_reconciliation matches=True; key_quality
ID-unique 608/10335/3279). The prod population SQL must derive from THAT governed mirror (with the
provenance travelling in the SQL header), not from a re-read of `D:\TCC_NEW.accdb`.

## Source swap (the only logic change)
- FROM: `access_raw."BreakerICCBStyles"` / `"BreakerMCCBStyles"` / `"BreakerPCBStyles"` in
  `tcc_fidelity_governed` (psycopg).
- The transform is COPIED VERBATIM from the proven, Codex-converged dry-run generator
  (`infra/database/sandbox/breaker/d4d5-population-dryrun/dry_run_direct_access_population_generator.py`):
  D4 6-col map (`tmt_tcc_number/tmt_notes/tmt_trip_plug/tmt_breaker_type/tmt_thermal_magnetic/tmt_thermal`
  <- `TMT_TCCNumber/TMT_Notes/TMT_TripPlug/TMT_BreakerType/TMT_ThermalMagnetic/TMT_Thermal`, ICCB/MCCB
  only); D5 5-block prefix map (`inst_override`=InstOvr*, `ninst_override`=NInstOvr*, `brk_times`=BrkTimes*,
  `r_int`=r_int_*, `r_iec`=r_iec_*) keyed by verbatim Access column name; `source_id` = Access `ID`;
  chunked `UPDATE ... FROM (VALUES ...)` (D4) and `INSERT ... ON CONFLICT (breaker_class,source_id) DO
  UPDATE` (D5). Verified against the queued DDL: 029 (6 cols x brk_iccb/brk_mccb) + 030
  (`brk_style_native_overrides`, PK `(breaker_class, source_id)`).
- NOTE (type fidelity): values now arrive as PG types from `access_raw`, not pyodbc. The block JSONB
  serializer already coerces Decimal/bytes/datetime. The `InstOvrAmps > 0` real-override metric must
  numeric-coerce defensively (access_raw may store it as text under the type map). This is a REPORT
  metric only (policy (a)), so it never drops a row -- but the count must stay honest.

## Artifacts (separate per migration -- maps to the separate-go apply chain)
- `029_d4_data.sql`  -- the D4 UPDATEs (brk_iccb_styles + brk_mccb_styles).
- `030_d5_data.sql`  -- the D5 INSERTs (brk_style_native_overrides).
- `generation_report.json` -- per-class counts / D4 non-null per col / D5 block-present / real_override
  / rating_only / samples + the full provenance block.

## Provenance header (embedded in EACH emitted SQL)
`run_id`, `snapshot_id`, Access `source_sha256`, `frozen_copy_path`, `driver`, and -- for each table
that artifact carries -- `row_count`, `checksum`, and `matches`. Plus `generated_at`, `generator_version`,
and the governed source DB name. The header is a SQL comment block; the integrity it asserts is enforced
by the gates below at generation time and by the in-tx invariants at apply time.

## Fail-closed gates (pre-emit; the generator REFUSES and exits nonzero)
1. **Wrong source DB:** the read connection `current_database()` must equal `tcc_fidelity_governed`
   (fence the read before any query). Refuse otherwise.
2. **run_id missing/ambiguous:** accept an explicit `--run-id`; if omitted, default to the sole row in
   `access_meta.extraction_run`. Refuse if the requested run_id is absent OR (when none requested) there
   is not exactly one run.
3. **Style reconciliation not True:** for EACH of ICCB/MCCB/PCB, `checksum_reconciliation.matches` must
   be True for this run_id. Refuse otherwise.
4. **Key quality not unique:** for EACH style parent, `key_quality.is_unique` must be True (candidate
   `['ID']`). Refuse otherwise.
5. **Required columns absent:** assert the source columns exist in `access_raw` before reading -- the 6
   D4 Access cols (ICCB/MCCB), the D5 prefix cols (InstOvr*/NInstOvr*/BrkTimes*/r_int_*/r_iec_*), `ID`,
   and `InstOvrAmps`. Refuse if any required column is missing.

## Policy (a) preserved (operator-ratified)
Carry the raw override/timing/rating blocks VERBATIM. `InstOvrAmps > 0` is a REPORT metric only, never
a filter. Rating-only styles (no real override, ratings present) are retained. One row per style with
>= 1 non-null D5 block (~14222 total).

## Guard strategy -- DECISION D1 (lean: A)
The emitted DATA SQL is the PROD-bound artifact (the SAME file is dry-run on a clone, then applied to
prod governed `tcc` on the gate -- exactly the 027/028 model).
- **A (lean):** DROP the dry-run-only `current_database() LIKE '%dryrun%'` name lock. Guard the prod
  artifact with 027/028-style IN-TX invariants instead: assert the 029/030 DDL is present (target
  columns/table exist) before writing; assert the source row counts in the header match the live
  pre-write state expectations (608/10335/3279); keep the ON CONFLICT upsert for idempotency. The
  dry-run validates this exact SQL on a fresh clone (DDL applied first); prod apply via `apply_migration`
  preflight on the gate. Rationale: a `%dryrun%` lock would block the prod apply, and 027/028 already
  proved the invariant-guard + gated-preflight model.
- **B:** Emit two variants (a `%dryrun%`-locked dry-run SQL + an unlocked prod SQL). More artifacts,
  divergent text to keep in sync; rejected unless you prefer a hard name-lock on the dry-run copy.

## Dry-run (after build, before any apply decision)
Fresh dated clone off `tcc_breaker_baseline_20260625` (e.g. `tcc_breaker_d4d5_gen_<date>`), NOT the
79audit clone. Apply 029 DDL + 030 DDL, then the generated 029/030 data SQL. Verify: counts
608/10335/3279 (D5 total 14222), real_override 241/129/317, rating_only retained (13533), idempotent
double-apply stable, and the provenance header matches the governed run.

## Review
Codex `apex-jobs review-run` + opus whole-slice, before any prod apply decision. Convergence-bounded.

## Out of scope
- Prod apply of 029/030 (separate operator gos, in order: 029 DDL -> governed 029 data -> 030 DDL ->
  governed 030 data).
- `031` view-transition (authored AFTER population; carries the 028 frame_counts perf-fix).
- F-79-03 row-level frame anti-join (separate, parked Access-evidence track).

## Decisions for ratification
- **D1 -- guard strategy:** A (invariant + count-assert guards on the prod artifact; no `%dryrun%`
  name lock; dry-run validates on the clone). Lean A.
- **D2 -- run_id selection:** default to the sole `extraction_run` row, accept explicit `--run-id`,
  refuse if absent/ambiguous. (Confirmation -- implied by the contract.)
- **D3 -- artifact split:** separate `029_d4_data.sql` + `030_d5_data.sql`. (Confirmation -- implied by
  the separate-go chain.)
