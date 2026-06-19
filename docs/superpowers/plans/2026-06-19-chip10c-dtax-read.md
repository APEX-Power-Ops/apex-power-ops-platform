# Chip 10c — DTAX-read: implementation plan

**Goal:** `read_dtax(.dtax) -> PtmModel`, feeding the existing 10a ingest pipeline
(`map_ptm_transformer -> build_proposal -> review -> db.write_values`). Doble files import into
records datasheets, reusing the whole 10a downstream unchanged (spec-14 "PtmModel; generalize").

**Approach**
- `read_dtax` INVERTS the DataModel-R2 schema that `write_dtax` (power_test_converters/dtax.py) emits.
  Output is the SAME `PtmModel` that `read_ptm` produces -> the 10a mapping/proposal/commit reuse with zero change.
- New module `packages/power-test-converters/src/power_test_converters/dtax_read.py` (ADDITIVE — does NOT
  modify the settled dtax.py / model.py / ptm.py).
- Tests = round-trip: build a PtmModel (via read_ptm of a small self-contained sample), `write_dtax(model)`
  (no template — build_dtax_tree builds programmatically), `read_dtax` it back, assert reconstruction.
  No external .dtax fixture needed; the reader is defined relative to the proven writer.

**DataModel-R2 paths (from test_ptm_to_dtax.py = the writer output):**
- `two-winding-transformer-nameplate` @ serial-num/mfr/special-id/config/kV-0/kV-1/Va-0..3/phases/coolant/
  tanktype/BIL/weight/oil-volume + `winding-properties`(winding-material/temperature-rise) + HV/LVWindingDetails
  + `tapchanger-nameplates/tapchanger-nameplate`.
- `dta-sessions/dta-session/two-winding-transformer/`:
  - `test-admin-data/admin-data` @ test-name + bottom-sn (= instrument test_set_name) + top_sn (= serial_number)
  - `overall-test-set/overall-test` @ insulation/test-circuit/requested-test-kV/test-kV/mA/measured-cap/pfm  (overall power factor)
  - `m7-bushing-test/.../bushing-test-results` (bushing power factor)
  - `lvttratio-test` @ label + `ratio-test-fields` @ benchmark-ratio/ratio-1/deviation-1/hv-volt/lv-volt  (turns ratio)
  - `exciting-current-test` + `exciting-current-fields` + `exciting-current-connections`
  - `m7winding-resistance-test` + `winding-resistance-fields` (corr-factor/calculated/corrected) + `m7winding-resistance-connections`

**Phases (TDD; one domain per phase; each round-trips green):**
1. Nameplate -> PtmTransformer (+ windings / power_ratings with unit back-conversion kV/Va).
2. Overall power factor (overall-test rows -> PtmPowerFactorMeasurement) + instrument (admin-data bottom-sn/top_sn).
3. Turns ratio (lvttratio-test -> PtmTurnsRatioTest).
4. Winding resistance (m7winding-resistance -> PtmWindingResistanceTest).
5. Exciting current (exciting-current-test -> PtmExcitingCurrentTest).
6. Bushing power factor (m7-bushing-test -> PtmPowerFactorMeasurement).
7. Ingest wiring: records-import `ingest` gains a `.dtax` entry (`read_dtax -> map_ptm_transformer -> proposal`);
   e2e test imports a .dtax into a records_dev datasheet, mirroring 10a `test_ingest_end_to_end`.

**Acceptance:** each phase round-trip green; final e2e imports a .dtax into a records datasheet via the existing
pipeline with per-domain values matching. Multi-tap row expansion stays deferred (same as 10a).

**Branch:** `records/chip10c-dtax-read` (off main 8a75fed2).
**Run tests:** `uv run --with pytest --with-editable packages/records-import --with-editable packages/power-test-converters pytest <path> -q`
