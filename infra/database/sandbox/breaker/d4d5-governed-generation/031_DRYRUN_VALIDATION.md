# 031 TMT Contract-View Transition -- Dry-Run Validation Evidence

> 2026-06-28. Branch `tcc/031-tmt-contract-view-transition` @ `56cc2d25` (off main `9a2ba40a`).
> Substrate: host clone `tcc_breaker_d4d5_031val_20260628` off `tcc_breaker_baseline_20260625`
> (apex-dev-pg, PG17), with the real committed chain `028 -> 029 DDL -> 029 data -> 030 DDL ->
> 030 data` applied. NOT applied to prod -- gated.

## Custody (data files == prod-applied bytes)

`git show origin/main:.../029_d4_data.sql | sha256sum` = `27334c756b792704d791771fcc766e46bcc5f711de386332eab2e832a760afd1` (recorded). PASS.
`git show origin/main:.../030_d5_data.sql | sha256sum` = `e384648c17336f25a4ded90ca98cef309f71a72863acbf11b7dcbab2c6c5e365` (recorded). PASS.

## Gate -- clone reproduces prod (before trusting any 031 result)

Clone 028 view, post-chain:
- `total=42069, serving=40125, hazards=1944, curveless=1923, orphans=0`
- `parity_hash_excl_hazards = 58cc15fe36e5dabf131e154e730c1833` == prod. PASS (no baseline drift).
- D4/D5 population: `iccb_d4=608, mccb_d4=10236, d5_rows=14222` == prod. PASS.

## Validation steps (all PASS)

1. **Guard negative (D4):** in a rolled-back tx, `UPDATE ... SET tmt_breaker_type=NULL` ->
   031 guard raised `ERROR: 031 precondition: D4 tmt helper columns are unpopulated`. Rollback held.
2. **Guard negative (D5):** in a rolled-back tx, `DELETE FROM tcc.brk_style_native_overrides` ->
   031 guard raised `ERROR: 031 precondition: tcc.brk_style_native_overrides is empty`. Rollback held.
   (Post-tests: clone intact at d5=14222, mccb_d4=10236.)
3. **Apply clean:** 031 applied; `NOTICE: 031 precondition OK: D4 populated rows=10844, D5 side rows=14222`;
   `CREATE VIEW`; `NOTICE: 031 TMT contract (LIVE): frames=42069, serving=40125, hazards=1944,
   curveless=1923, orphans=0, d5_carried=42069`; COMMIT (exit 0). Both DO-block invariants passed.
4. **Value-parity:** post-031 `parity_hash_excl_hazards = 58cc15fe...` -- IDENTICAL to 028. Aggregates
   unchanged. Proves the per-child aggregation rewrite is value-neutral vs `count(DISTINCT)`.
5. **Hazard transition (exact):** post-031 `projection_hazards` distribution ==

   | n | projection_hazards |
   |---|---|
   | 20073 | `{missing_setting_options,missing_thermal_adjustment_rows,d5_inst_override_carried_reference_only}` |
   | 14538 | `{missing_thermal_adjustment_rows,d5_inst_override_carried_reference_only}` |
   | 5502 | `{d5_inst_override_carried_reference_only}` |
   | 1923 | `{missing_curve_points,missing_thermal_adjustment_rows,d5_inst_override_carried_reference_only}` |
   | 21 | `{missing_amp_options,missing_setting_options,missing_thermal_adjustment_rows,d5_inst_override_carried_reference_only}` |
   | 12 | `{missing_setting_options,d5_inst_override_carried_reference_only}` |

   sum 42069; `d4_absent_survivors=0, d5_old_survivors=0, d5_carried=42069`. Matches the spec's predicted distribution exactly.
6. **Perf:** `EXPLAIN (ANALYZE)` of `count(*)` over the full view:
   - 031: **65.96 ms**, no Nested Loop, no >=6-digit intermediate.
   - 028 (after down): **275.21 ms**; visible Cartesian -- inner parallel hash right join `rows=1440228`
     actual, outer join estimate `rows=8849004`, before `COUNT(DISTINCT)`. ~4.2x faster; Cartesian removed.
7. **Idempotency:** re-applying 031 is a clean no-op (precondition OK, CREATE VIEW, post-NOTICE, exit 0).
8. **Down restores 028:** `031_down` -> `CREATE VIEW`/`COMMENT`; hash returns `58cc15fe...`; hazard
   distribution returns to 10 combos (6 carry the d4 flag); aggregates `42069/40125/1944/1923/0`.

## Disposition

Dry-run COMPLETE and fully green. NEXT: cross-engine IRP (Codex via apex-jobs review-run + adversarial
Claude lenses), then operator-gated prod apply (031 DDL via MCP apply_migration; its OWN explicit go).
Clone `tcc_breaker_d4d5_031val_20260628` is disposable (DROP hook-blocked -> manual).
