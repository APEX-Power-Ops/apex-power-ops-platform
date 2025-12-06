# RESA Power - Supabase Migration Guide

## Quick Start (30 Minutes to Running Database)

### Step 1: Create Supabase Project (5 min)

1. Go to https://supabase.com
2. Sign in / Create account
3. Click "New Project"
4. Settings:
   - Name: `resa-power`
   - Database Password: (save this!)
   - Region: West US (closest to Phoenix)
5. Wait for project to provision (~2 min)

### Step 2: Deploy Schema (5 min)

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **New Query**
3. Open `001_schema.sql` from this folder
4. Copy entire contents
5. Paste into SQL Editor
6. Click **Run**
7. Should see "Success" (creates 22 tables, 5 views, 13 triggers)

### Step 3: Verify (2 min)

1. Go to **Table Editor** in Supabase
2. Confirm these tables exist:
   - Core: `clients`, `sites`, `projects`, `scopes`, `tasks`, `apparatus`
   - Revenue: `apparatus_revenue`, `scope_financial_summaries`, `project_financial_summaries`
   - PSS: `pss_studies`, `pss_documents`, `rfis`, `document_templates`
   - Lookup: `business_units`, `apparatus_type_master`, `employees`, `engineers`

### Step 4: Get Connection Info (2 min)

In Supabase Dashboard → **Settings** → **API**:

```
Project URL: https://xxxxx.supabase.co
Anon Key: eyJhbG...
Service Role Key: eyJhbG... (keep secret!)
```

In **Settings** → **Database** → **Connection string**:
```
postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

---

## Schema Summary

### Tables: 22

| Category | Tables |
|----------|--------|
| **Lookup (3)** | business_units, apparatus_type_master, locations |
| **Organization (4)** | clients, sites, employees, engineers, contacts |
| **Projects (4)** | projects, scopes, scope_labor_details, tasks |
| **Apparatus (2)** | apparatus, estimators |
| **Revenue (3)** | apparatus_revenue, scope_financial_summaries, project_financial_summaries |
| **PSS Portal (5)** | pss_studies, document_templates, pss_documents, rfis, activity_log |

### Key Features Included

✅ **Computed Columns** (that were missing from Dataverse V2):
- `scope_labor_details.effective_rate` - auto-calculated from totals/hours
- `apparatus_revenue.total_hours` - planned minus delays
- `apparatus_revenue.revenue_amount` - hours × rate
- `scope_financial_summaries.revenue_variance` - recognized vs estimated
- `project_financial_summaries.total_variance` - project-level variance

✅ **Triggers**:
- `updated_at` auto-update on all tables
- PSS status change logging
- **Revenue recognition on apparatus completion** (the main flow!)

✅ **Dashboard Views**:
- `v_project_dashboard` - Project overview with progress
- `v_scope_progress` - Scope-level metrics
- `v_pss_dashboard` - PSS Portal overview
- `v_outstanding_documents` - Document aging
- `v_revenue_recognition` - Revenue details

✅ **Seed Data**:
- 4 Business Units (Phoenix, Dallas, Houston, Denver)
- 17 Apparatus Types with standard hours
- 12 Document Templates for PSS studies

---

## Next Steps

### Migrate Existing Data

From Dataverse, you have:
- 1 Client (Garney)
- 1 Estimator

Export and insert:
```sql
INSERT INTO clients (name, code) VALUES ('Garney', 'GARNEY');
```

### Connect Web App

Replace `dataverse.ts` with Supabase client:

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

// Example query
const { data: projects } = await supabase
  .from('projects')
  .select(`
    *,
    clients(name),
    sites(name)
  `)
  .order('created_at', { ascending: false })
```

### Set Up Auth

```typescript
// Sign up
await supabase.auth.signUp({ email, password })

// Sign in
await supabase.auth.signInWithPassword({ email, password })

// Get current user
const { data: { user } } = await supabase.auth.getUser()
```

### Import PSS Tracker Data

The 18 projects from PSS_Tracker_NEW.xlsx need:
1. Create clients if not exist
2. Create projects with `project_type = 'PSS_STUDY'`
3. Create pss_studies linked to projects
4. Create pss_documents from document checklist

I can generate this import script next.

---

## File Reference

```
C:\RESA_Power_Build\Supabase\
├── 001_schema.sql       # Main schema (THIS FILE - run first)
├── QUICKSTART.md        # This guide
└── (more files coming)
    ├── 002_migrate_dataverse.sql  # Dataverse data import
    ├── 003_import_pss_tracker.sql # PSS Excel data import
    └── lib/supabase.ts            # TypeScript client
```

---

## Support

- Supabase Docs: https://supabase.com/docs
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Schema source: Dataverse V2 (v1.0.0.5) + V1.5.1.3 + PSS Portal

