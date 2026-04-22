# Legacy Utility Boundary

These files remain in `migrations/` because they still provide diagnostic or recovery value, but they are no longer the canonical forward schema lane.

## Retained Legacy Utilities By Role

### A. Schema inspection and parity checks

1. `_check_cols.py`
2. `_check_target_cols.py`
3. `_verify_cols.py`
4. `_verify_counts.py`

Use these only to compare source, target, or live-state shape and counts while historical migration questions still exist.

### B. Recovery or replay utilities tied to older transfer workflows

1. `002_data_transfer.py`
2. `003_retransfer_thermal_adj.py`
3. `full_access_import.py`
4. `full_access_emt_import.py`

Use these only for controlled replay, recovery, or source-backed repair when the forward migration lane cannot express the task by itself.

### C. Focused diagnostics

1. `_debug_thermal.py`

Use this only for bounded investigation of thermal-adjustment transfer behavior or other source-validation questions.

### D. Local staging-only loader

1. `tcc_staging_load.py`

Use this only to load Access CSV exports into a local Docker PostgreSQL staging environment for bounded source-shape inspection or staging rehearsal. It is not part of the canonical Supabase forward migration lane and it is not current replay authority for the live runtime path.

## Archive-Readiness Assessment As Of 2026-03-24

Retain for now because they still have distinct bounded value:

1. `_check_cols.py`, `_check_target_cols.py`, `_verify_cols.py`, and `_verify_counts.py` remain useful for source-target parity checks while historical migration questions still exist.
2. `_debug_thermal.py` remains the only focused diagnostic for thermal-adjustment transfer behavior.
3. `002_data_transfer.py` remains the env-contract-aligned local PostgreSQL to Supabase replay utility referenced by the tracked implementation record.
4. `003_retransfer_thermal_adj.py` remains the only targeted replay utility for the thermal-adjustment correction.
5. `full_access_import.py` remains the documented Access CSV replay path for the expanded ETU import surface.
6. `full_access_emt_import.py` remains the distinct Access CSV replay path for EMT because EMT was not present in the available lowercase PostgreSQL source snapshot.
7. `tcc_staging_load.py` remains retained for staging-only value because it is still part of the bounded local source-shape and EMT staging evidence chain; it is not archive-ready from the current governed record.

Archived candidate now moved out of the active legacy set:

1. `002_transfer_data.py` has been moved to `_archive/002_transfer_data.py` because it appears functionally superseded by `002_data_transfer.py` for the current env-driven replay path and is not referenced by the current tracked execution record.

Rules:

1. use these files only for inspection, historical replay, controlled recovery, or source validation
2. do not introduce new schema changes through these files
3. do not treat dashboard-only edits or these scripts as the forward migration authority
4. place new schema changes in `../supabase/migrations/`
5. archive these utilities once their remaining diagnostic or replay value is exhausted and a governed record still captures the needed evidence
6. do not restore archived transfer utilities to the active legacy set unless a specific historical reconstruction requires them

Related governance surfaces:

1. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\README.md`
2. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\supabase\migrations\README.md`
3. `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\supabase\migrations\20260322_000001_live_baseline_marker.sql`