# RESA Power Platform - Quick Start Guide

Get up and running with the RESA Power Supabase database in 5 minutes.

## Prerequisites

- Supabase account (free tier works)
- PowerShell 5.1+ (Windows) OR psql client
- Database password from Supabase dashboard

## 🚀 Fastest: One-Command Deployment

```powershell
# From Supabase folder:
cd C:\RESA_Power_Build\Supabase
.\deploy.ps1 -Password "YOUR_DB_PASSWORD"
```

This deploys everything: schema (6 files) + data (3 files) in ~30 seconds.

**Options:**
```powershell
.\deploy.ps1 -Password "xxx" -Mode schema  # Schema only
.\deploy.ps1 -Password "xxx" -Mode data    # Data only (after schema)
.\deploy.ps1 -Password "xxx" -Mode all     # Everything (default)
```

---

## Manual Deployment Options

### Option A: Supabase Dashboard (No tools needed)

1. Open SQL Editor: https://supabase.com/dashboard/project/fxoyniqnrlkxfligbxmg/sql
2. Run each file in order:

```
00_enums.sql      → Creates ENUM types
01_tables.sql     → Creates 25 tables
02_relationships.sql → Adds foreign keys
03_triggers.sql   → Adds automation
04_views.sql      → Creates views
05_indexes.sql    → Adds performance indexes
```

### Option B: psql Command Line

```bash
# Set connection string
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.fxoyniqnrlkxfligbxmg.supabase.co:5432/postgres"

# Run all schema files
psql $DATABASE_URL -f schema/00_enums.sql
psql $DATABASE_URL -f schema/01_tables.sql
psql $DATABASE_URL -f schema/02_relationships.sql
psql $DATABASE_URL -f schema/03_triggers.sql
psql $DATABASE_URL -f schema/04_views.sql
psql $DATABASE_URL -f schema/05_indexes.sql
```

### Option C: Single Combined File

```bash
# Concatenate all schema files
cat schema/*.sql > combined_schema.sql

# Run combined file
psql $DATABASE_URL -f combined_schema.sql
```

## Step 3: Load Test Data

```bash
# Load reference data (locations, types)
psql $DATABASE_URL -f data/10_seed_data.sql

# Load LASNAP16 project test data
psql $DATABASE_URL -f data/11_test_data.sql

# Load PSS portal test data
psql $DATABASE_URL -f data/12_pss_test_data.sql
```

## Step 4: Verify Installation

Run these queries to confirm everything works:

```sql
-- Check tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check ENUM types
SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;

-- Check test project loaded
SELECT project_number, project_name, total_apparatus_count 
FROM projects WHERE project_number = 'LASNAP16';
-- Expected: total_apparatus_count = 47

-- Check PSS studies
SELECT study_number, study_name, status FROM pss_studies;
-- Expected: 5 studies

-- Test a view
SELECT * FROM v_projects_full;
```

## Step 5: Test Triggers

```sql
-- Add a test apparatus
INSERT INTO apparatus (scope_id, apparatus_designation, apparatus_name)
VALUES ('44444444-0000-0000-0000-000000000001', 'TEST-001', 'Test Apparatus');

-- Verify rollup updated
SELECT total_apparatus_count FROM scopes 
WHERE id = '44444444-0000-0000-0000-000000000001';
-- Should be 16 (was 15)

-- Clean up
DELETE FROM apparatus WHERE apparatus_designation = 'TEST-001';
```

## Common Issues

### "type already exists"
```sql
-- Drop and recreate ENUMs
DROP TYPE IF EXISTS project_status CASCADE;
-- Then re-run 00_enums.sql
```

### "relation already exists"
```sql
-- Drop all tables (DANGER: loses data)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
-- Then re-run all schema files
```

### "foreign key violation"
Make sure you load data files in order:
1. `10_seed_data.sql` (creates locations that employees reference)
2. `11_test_data.sql` (creates employees, clients, projects)
3. `12_pss_test_data.sql` (references employees and projects)

## Connection Strings

### For Applications

```
# Supabase connection string format
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Example with pooling (recommended for apps)
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### For Local Development

Add to `.env`:
```env
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=[your-anon-key]
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

## Next Steps

1. **Enable Row Level Security (RLS)** - Secure your tables
2. **Create API endpoints** - Use Supabase auto-generated REST API
3. **Build frontend** - Connect with Supabase JS client
4. **Set up realtime** - Subscribe to table changes

## File Sizes (Reference)

| File | Lines | Description |
|------|-------|-------------|
| 00_enums.sql | 253 | 18 ENUM types |
| 01_tables.sql | 523 | 25 tables |
| 02_relationships.sql | 257 | All FK constraints |
| 03_triggers.sql | 507 | 12 trigger functions |
| 04_views.sql | 504 | 15 views + 1 materialized |
| 05_indexes.sql | 232 | ~50 indexes |
| 10_seed_data.sql | ~100 | Reference data |
| 11_test_data.sql | ~400 | LASNAP16 project |
| 12_pss_test_data.sql | ~350 | PSS portal data |

**Total**: ~3,100 lines of SQL

## Support

- See `/spec/` folder for detailed documentation
- Check `README.md` for complete schema reference
- Review spec files for field-level documentation

---

*Quick Start Guide v1.0.0 | December 5, 2025*
