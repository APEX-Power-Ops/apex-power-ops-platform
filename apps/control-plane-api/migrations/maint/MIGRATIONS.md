# MAINT Mode Migrations

SQL source files for the 8 MAINT-related Supabase migrations applied 2026-03-20/21.

## Supabase migration history (chronological)

| # | Migration name | Purpose |
|---|---|---|
| 1 | `backfill_maint_flat_columns_from_params_json` | Populated 59 flat maint columns from params_json (interim bridge) |
| 2 | `add_maint_columns_to_sensor_calc_context` | Added maint columns to vw_sensor_calc_context via LEFT JOIN |
| 3 | `replace_fn_calculate_test_currents_with_maint_mode` | Added p_maint_mode param, maint tolerance overrides |
| 4 | `replace_fn_evaluate_test_results_with_maint_mode` | Added p_maint_mode param, maint tolerance overrides |
| 5 | `restore_maint_available_add_maint_capable` | Restored maint_available=false, added maint_capable computed column |
| 6 | `fn_calculate_use_maint_capable` | Fixed calculate to use ctx.maint_capable instead of ctx.maint_available |
| 7 | `fn_evaluate_use_maint_capable` | Fixed evaluate to use ctx.maint_capable instead of ctx.maint_available |

## Source files (current consolidated state)

- `vw_sensor_calc_context.sql` — View definition with maint_available + maint_capable
- `fn_calculate_test_currents.sql` — Calculate function with full MAINT support
- `fn_evaluate_test_results.sql` — Evaluate function with full MAINT support

## Key semantic distinction

- **maint_available** — Runtime toggle from the original Access DB. Currently `false` for all rows.
- **maint_capable** — Derived from data presence: `COALESCE(maint_inst_calc, -1) != -1 OR COALESCE(maint_gfpu_calc, -1) != -1`. This is what the SQL functions use to gate MAINT behavior.

## maint_support_level

Both functions return a `maint_support_level` field:
- `'none'` — sensor has no maint config data
- `'partial_inst_gfpu'` — INST/GFPU maint data exists but LTPU/STPU reduction factors are missing
- `'full'` — all maint data including reduction factors is present
