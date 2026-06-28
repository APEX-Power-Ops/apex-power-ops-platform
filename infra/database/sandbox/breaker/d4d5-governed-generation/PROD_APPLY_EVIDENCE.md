# D4/D5 Prod Apply Evidence -- governed Supabase `fxoyniqnrlkxfligbxmg`

Operator-gated prod apply of the D4/D5 carry (lane merged to main via PR #45, `ab054dcd`). Each step its
own explicit go; DDL never bundled with data. Apply-evidence standard per step: (1) pre-apply artifact
SHA, (2) post-apply counts/partition, (3) post-apply md5 of source-sensitive text vs the governed source
(esp. the 4 genuine `\r\r\n` MCCB rows 93192/93212/93252/93282), (4) this transcript committed.

DDL via authorized MCP `apply_migration`; DATA host-side `psql -f` over the prod session DSN (the data
files are 1.28MB/15.7MB, too large for an MCP SQL-as-argument call). Source-of-truth md5 (governed
`access_raw."BreakerMCCBStyles"."TMT_Notes"`): 93192=e70bad27170b52c4f558107e5d7e2942,
93212=2a40772d0f24e2590426ee131e869e72, 93252=87565a38caba18039d7ea304624f620f,
93282=9fea28c883bf58c4344172d33f9a8036.

---

## Step 1 -- 029 DDL (`tcc_029_d4_tmt_helper_recarry`) -- APPLIED 2026-06-28
- **Mechanism:** MCP `apply_migration` (the file's outer BEGIN/COMMIT omitted; the migration runner wraps
  the transaction; the fail-closed shape guard still aborts within it). Returned `{"success":true}`.
- **Pre-state (read-only):** brk_iccb/mccb_styles each had 4 pre-existing `tmt_sst_*` SST-bridge cols
  (tmt_sst_mfr/style/type, tmt_use_sst) and 0/6 of the new D4 cols -- DISJOINT names, no collision.
- **Post-state (verified):** both tables now carry all 6 D4 cols with correct types --
  tmt_tcc_number:text, tmt_notes:text, tmt_trip_plug:smallint, tmt_breaker_type:smallint,
  tmt_thermal_magnetic:smallint, tmt_thermal:smallint. Counts unchanged: iccb 608 / mccb 10335.

## Step 2 -- 029 data (`029_d4_data.sql`) -- APPLIED 2026-06-28
- **Pre-apply SHA:** host file sha256 = `27334c756b792704d791771fcc766e46bcc5f711de386332eab2e832a760afd1`
  == validated == origin/main blob (byte-faithful transfer confirmed before apply).
- **Mechanism:** host-side `psql "$SUPABASE_PROD_DSN" -v ON_ERROR_STOP=1 -f 029_d4_data.sql` (session
  connection verified beforehand: right prod DB [iccb 608 / mccb 10335], temp-table-in-transaction smoke
  test INSERT 0 3 -> 3 -> ROLLBACK). `PSQL_EXIT=0`.
- **Transcript (key lines):** `SET; SET; BEGIN; CREATE TABLE (stage_029_iccb); <INSERT batches>; DO
  (guard); UPDATE 608 (ICCB full-coverage recarry); DO (guard); CREATE TABLE (stage_029_mccb); <INSERT
  batches>; DO (guard); UPDATE 10335 (MCCB full-coverage); DO (guard); COMMIT`. All in-tx guards passed.
- **Post-apply verification:** iccb D4 non-null = 608; mccb D4 non-null = 10236 (99 all-NULL
  source-faithful); counts unchanged 608 / 10335.
- **Non-self-referential source cross-check (PASS):** prod `tcc.brk_mccb_styles.tmt_notes` md5 for the 4
  genuine-`\r\r\n` rows == governed source md5 EXACTLY -- 93192 e70bad27, 93212 2a40772d, 93252 87565a38,
  93282 9fea28c8. The CR-doubling class is confirmed absent from prod.

---

## Step 3 -- 030 DDL (`tcc_030_d5_native_overrides_sidetable`) -- APPLIED 2026-06-28
- **Mechanism:** MCP `apply_migration` (outer BEGIN/COMMIT omitted; runner wraps; fail-closed shape guard
  aborts within it). Returned `{"success":true}`. Side table was absent pre-apply -> fresh CREATE.
- **Post-state (verified):** `tcc.brk_style_native_overrides` exists with 8 cols
  (breaker_class:text, source_id:integer, inst_override/ninst_override/brk_times/r_int/r_iec/ovr_curves:jsonb),
  PK exactly (breaker_class, source_id), 2 named CHECK constraints, 0 rows.

## Step 4 -- 030 data (`030_d5_data.sql`) -- APPLIED 2026-06-28
- **Pre-apply SHA:** host file sha256 = `e384648c17336f25a4ded90ca98cef309f71a72863acbf11b7dcbab2c6c5e365`
  == validated == origin/main blob.
- **Mechanism:** host-side `psql "$SUPABASE_PROD_DSN" -v ON_ERROR_STOP=1 -f 030_d5_data.sql`. `PSQL_EXIT=0`.
- **Transcript (key lines):** `SET; SET; BEGIN; CREATE TABLE (stage_030_d5); <INSERT batches>; DO (guard);
  INSERT 0 14222 (into tcc.brk_style_native_overrides); DO; DO; DO (value-parity + full-domain extra-row +
  PK-exact guards); COMMIT`. All in-tx guards passed.
- **Post-apply verification (all PASS):** D5 per-class 608 / 10335 / 3279 = 14222; partition real 687 /
  rating_only 13533 / neither 2; orphans 0; ovr_curves non-null 0; value-parity ICCB sid 11
  InstOvrAmps=46000.0 with a 16-key inst_override block.

---

## Pending (operator-gated)
- Step 5 -- author + apply 031 (view-transition; per the VOCABULARY_MAP plan: drop the D4-absent flag,
  change the D5 flag to `d5_inst_override_carried_reference_only`, guarded to RAISE if not yet populated;
  carries the 028 `frame_counts` Cartesian-product perf-fix into the next view re-creation). 031 must be
  AUTHORED first (does not exist yet) -> design -> validate -> cross-engine -> separate gated apply.

## Summary
029 + 030 (DDL + data) fully applied + verified on governed prod `fxoyniqnrlkxfligbxmg`. D4 helper cols
populated (608 ICCB / 10236 MCCB non-null, source cross-check md5 4/4 == governed source); D5 side table
populated (14222 rows, partition 687/13533/2, 0 orphans, value-parity). NOT wired to serving (the serving
cut-line stays 028-defined per Decision 1). 031 view-transition is the remaining gated step.
