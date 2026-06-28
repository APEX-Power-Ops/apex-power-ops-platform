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

## Step 5 -- 031 view-transition (`tcc_031_lvbreakertcc_tmt_contract_view_transition`) -- APPLIED 2026-06-28
- **Lane:** authored + dry-run validated + cross-engine IRP on branch `tcc/031-tmt-contract-view-transition`
  (final SQL `841ca3a8`, off main `9a2ba40a`). Dry-run 8/8 + guard re-validation green on a clone that
  first reproduced the prod 028 hash `58cc15fe`. IRP found + fixed a guard fail-open (D4 Important, Claude)
  and a D5 partial-coverage gap (Codex P2) -> terminal per-frame coverage guard; final Codex pass clean.
  See `031_DRYRUN_VALIDATION.md` + `031_IRP_REVIEW.md`.
- **Pre-apply preflight (live prod, read-only):** 031 absent from migration history; pre-031 state confirmed
  (d4_absent_old=30809, d5_old=42069, d5_carried_new=0); value-parity baseline hash 58cc15fe + aggregates
  42069/40125/1944/1923/0; 029/030 data present (iccb 608 / mccb 10236 / d5 14222); guard preconditions hold
  on prod (0 D4-uncarried frames, 0 D5-uncovered frames).
- **Mechanism:** MCP `apply_migration` (outer BEGIN/COMMIT stripped; runner wraps the tx; the leading
  per-frame guard runs first and the trailing partition/survivor guard aborts within the runner tx).
  Returned `{"success":true}` -- both DO-block guards passed.
- **Post-apply verification (all PASS):** value-parity hash `58cc15fe36e5dabf131e154e730c1833` IDENTICAL to
  pre-031 (perf-fix value-neutral); aggregates 42069/40125/1944/1923/0 unchanged; d4_absent_survivors=0,
  d5_old_survivors=0, d5_carried=42069; `projection_hazards` distribution = the exact 6 combos
  (20073 / 14538 / 5502 / 1923 / 21 / 12, sum 42069). No serving change (Decision 1); the side table and the
  diagnostic views remain not Data-API-reachable.

## Summary
029 + 030 + 031 (DDL + data + view-transition) fully applied + verified on governed prod
`fxoyniqnrlkxfligbxmg`. D4 helper cols populated (608 ICCB / 10236 MCCB non-null, source cross-check md5
4/4 == governed source); D5 side table populated (14222 rows, partition 687/13533/2, 0 orphans,
value-parity). 031 transitioned the 028 hazard surface (d4-absent dropped, d5 relabeled
`carried_reference_only`) and removed the `frame_counts` Cartesian -- value-parity hash 58cc15fe unchanged,
exact 6-combo distribution, 0 stale survivors. NOT wired to serving (the serving cut-line stays 028-defined
per Decision 1). The breaker D4/D5 carry lane (#79) is complete end-to-end on prod.
