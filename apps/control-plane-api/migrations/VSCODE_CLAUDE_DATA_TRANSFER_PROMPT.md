# Data Transfer Task — VS Code Claude Prompt

Copy and paste everything below the line into VS Code Claude (Claude Code / Copilot):

---

## Task: Run TCC v5 Data Transfer to Supabase

Execute the data migration script that transfers ~2.5M rows from the local PostgreSQL database to Supabase, with column renaming and a breaker_class backfill.

### What This Does

Transfers 31 tables of circuit breaker TCC (Time-Current Curve) data from:
- **Source**: `SOURCE_DATABASE_URL` or `DATABASE_URL_LOCAL`
- **Target**: `DATABASE_URL`

The target Supabase schema is already deployed (33 empty tables with `tcc_` prefixed names, RLS enabled). This script fills them with data from the local DB, renaming columns in the process.

### File Location

The active platform copy of the script is at:
```
C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\migrations\002_data_transfer.py
```

### Prerequisites

1. **Local PostgreSQL must be running** on `localhost:5432` with the `tcc_v5` database accessible
2. **psycopg2** must be installed: `pip install psycopg2-binary`
3. `.env` must provide the required source and target database URLs

### Steps to Execute

**Step 1: Dry run first (no writes)**
```bash
cd C:\APEX Platform\apex-power-ops-platform
python migrations/002_data_transfer.py --dry-run --verbose
```

Review the output. It should list all 31 tables with their source row counts and the column mappings that will be applied. Verify:
- All 31 tables are found in the source database
- Row counts look reasonable (biggest: `breaker_tmt_frame_curves` ~1.1M rows)
- No connection errors to either database

**Step 2: Execute the actual transfer**
```bash
python migrations/002_data_transfer.py
```

This will:
1. Connect to both local PG and Supabase
2. Build a breaker_class lookup (maps each TMT style_id to 'iccb', 'mccb', or 'pcb')
3. Transfer each table in FK dependency order
4. Use INSERT for small tables (<10K rows) and COPY protocol with 50K-row batches for large tables
5. Reset all SERIAL sequences to match transferred data
6. Print a summary with row counts and timing

**Expected output** should show something like:
```
✓ tcc_manufacturers: 450 rows (0.3s)
✓ tcc_trip_types: ~100 rows (0.2s)
...
✓ tcc_tmt_curves: 1,143,458 rows (COPY, ~3-5 min)
...
✓ tcc_etu_sensor_params: 136,384 rows (COPY, ~30s)
...
Total: ~2.5M rows in 31 tables
```

**Step 3: Verify row counts**

After the transfer completes, run this SQL against Supabase to verify (you can use the Supabase MCP or the SQL editor in the Supabase dashboard):

```sql
SELECT 'tcc_manufacturers' as tbl, count(*) FROM tcc_manufacturers
UNION ALL SELECT 'tcc_trip_types', count(*) FROM tcc_trip_types
UNION ALL SELECT 'tcc_trip_styles', count(*) FROM tcc_trip_styles
UNION ALL SELECT 'tcc_tmt_curves', count(*) FROM tcc_tmt_curves
UNION ALL SELECT 'tcc_etu_sensors', count(*) FROM tcc_etu_sensors
UNION ALL SELECT 'tcc_etu_ltpu_pickups', count(*) FROM tcc_etu_ltpu_pickups
UNION ALL SELECT 'tcc_etu_sensor_params', count(*) FROM tcc_etu_sensor_params
ORDER BY tbl;
```

### Troubleshooting

**Connection refused to localhost:5432**: PostgreSQL service isn't running. Start it:
```bash
net start postgresql-x64-16
```
(or whatever your PG version is — check Windows Services)

**Connection refused to Supabase**: Check that IPv4 add-on is enabled in Supabase dashboard (Settings → Add-ons → IPv4). It was enabled as of this migration.

**UNIQUE constraint violation**: The target tables already have data from a prior run. Truncate first:
```sql
-- Run on Supabase to clear all TCC tables (respects FK order)
TRUNCATE tcc_test_results, tcc_test_plans,
  tcc_etu_sensor_maint, tcc_etu_stpu_overrides, tcc_etu_ltd_params,
  tcc_etu_sensor_params, tcc_etu_inst_curves, tcc_etu_gfd_equations,
  tcc_etu_std_equations, tcc_etu_gfd_bands, tcc_etu_std_bands,
  tcc_etu_ltd_bands, tcc_etu_gfpu_pickups, tcc_etu_inst_pickups,
  tcc_etu_stpu_pickups, tcc_etu_ltpu_multipliers, tcc_etu_ltpu_pickups,
  tcc_etu_sensors, tcc_etu_plugs, tcc_tmt_thermal_adj, tcc_tmt_settings,
  tcc_tmt_curves, tcc_tmt_amps, tcc_tmt_frames, tcc_brk_pcb_styles,
  tcc_brk_pcb, tcc_brk_mccb_styles, tcc_brk_mccb, tcc_brk_iccb_styles,
  tcc_brk_iccb, tcc_trip_styles, tcc_trip_types, tcc_manufacturers
  CASCADE;
```

**Timeout on large table**: The `tcc_tmt_curves` table (1.1M rows) may take 3-5 minutes over the network. This is normal. The script uses 50K-row COPY batches to manage memory.

### Key Files for Reference

- **Active migration SQL** (already applied to Supabase): `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\migrations\001_tcc_schema.sql`
- **Column mapping reference**: `C:\APEX Platform\source-domains\tcc_v5_backend\FULL_MIGRATION_COLUMN_MAP.md`
- **Active transfer script**: `C:\APEX Platform\apex-power-ops-platform\apps\control-plane-api\migrations\002_data_transfer.py`
- **Source-lane lineage copy**: `C:\APEX Platform\source-domains\tcc_v5_backend\migrations\002_data_transfer.py`
- **Local env template**: `C:\APEX Platform\source-domains\tcc_v5_backend\.env.example` (the real `.env` remains local and untracked)

### Context

This is part of a migration from local PostgreSQL to Supabase for a NETA electrical testing platform. The schema was renamed from inconsistent legacy naming (SQLite origins) to a clean `tcc_` prefixed convention with `tcc_brk_` for breakers, `tcc_tmt_` for thermal-magnetic trip tables, and `tcc_etu_` for electronic trip unit tables. The Supabase schema (33 tables with RLS, indexes, and comments) was applied via two Supabase migrations. This script fills those tables with the actual data.
