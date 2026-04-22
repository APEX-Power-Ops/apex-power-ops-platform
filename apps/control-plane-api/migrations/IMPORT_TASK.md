# Task: Run Full Access DB → Supabase Import

## Status: Ready to execute

## What's Already Done
The Supabase schema migrations have been applied:
1. ✅ `tcc_etu_sensors` expanded from 24 → 94 columns (all 93 DatSensor + created_at)
2. ✅ `tcc_etu_sensor_maint` expanded from 11 → 69 columns (all 59 DatSensorMaint + originals)
3. ✅ `tcc_etu_settings` table created (DatSettings — 6 columns)
4. ✅ `tcc_etu_plugs` — sensor_id column added

## What This Script Does
Reads all 4 Access DB CSV exports and loads them into the expanded Supabase tables:

| Source Table | Target Table | Rows | Operation |
|---|---|---|---|
| DatSensor.csv | tcc_etu_sensors | 17,831 | UPSERT (updates 11,442 existing + inserts 6,389 missing) |
| DatSensorMaint.csv | tcc_etu_sensor_maint | 2,572 | UPDATE (fills new columns on existing rows) |
| DatSettings.csv | tcc_etu_settings | 3,514 | UPSERT (new table) |
| DatPlugs.csv | tcc_etu_plugs | 49,901 | TRUNCATE + INSERT (fixes FK to sensor_id) |

## Steps

### 1. Open VS Code Terminal
Navigate to the `tcc_v5_backend` folder.

### 2. Install dependency
```
pip install psycopg2-binary
```

### 3. Run the script
```
python migrations/full_access_import.py
```

### 4. Expected output
The script shows a progress bar for each table and runs verification checks at the end:
- Row counts should match Access DB exactly
- New columns (ltd_tol_hi, ltpu_func, etc.) should show populated values
- FK integrity checks should show zero orphans
- Sample sensor data should show real tolerance values (not flat ±10)

## Estimated Runtime
~2-5 minutes depending on network speed to Supabase pooler.

## Rollback
If something goes wrong, the script commits after each table so partial progress is preserved.
To fully rollback, the 4 Supabase migrations can be reverted (they only ADD columns, never remove).

## Files
- Script: `migrations/full_access_import.py`
- Column map: `FULL_MIGRATION_COLUMN_MAP.md`
- Gap analysis: `ACCESS_TO_SUPABASE_GAP_ANALYSIS.md`
- Strategy: `TCC-SUPABASE-MIGRATION-STRATEGY-DRAFT.md` (in NETA ETT folder)
