# RESA Power - Database Setup Guide

## Quick Start (15 minutes to functional database)

### Step 1: Create Supabase Account & Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up with GitHub (recommended) or email
3. Click **"New Project"**
4. Configure:
   - **Name**: `resa-power-dev`
   - **Database Password**: Generate strong password (SAVE THIS!)
   - **Region**: Central US (closest to Texas)
   - **Pricing**: Free tier is fine for development
5. Click **"Create new project"**
6. Wait ~2 minutes for project to spin up

### Step 2: Run the Schema Scripts

1. In Supabase dashboard, click **"SQL Editor"** in left sidebar
2. Click **"New query"**
3. Copy entire contents of `01_supabase_schema.sql` and paste into editor
4. Click **"Run"** (or Ctrl+Enter)
5. Should see: `RESA Power schema created successfully!`
6. Click **"New query"** again
7. Copy entire contents of `03_pss_portal_tables.sql` and paste
8. Click **"Run"**
9. Should see: `PSS Portal tables created successfully!`

### Step 3: Load Test Data

1. Click **"New query"** again
2. Copy entire contents of `02_test_data.sql` and paste
3. Click **"Run"**
4. Verify with summary counts at bottom
5. Click **"New query"** again
6. Copy entire contents of `04_pss_portal_test_data.sql` and paste
7. Click **"Run"**
8. Verify PSS Portal data loaded

### Step 4: Verify in Table Editor

1. Click **"Table Editor"** in left sidebar
2. You should see all tables listed:

   **Core Operations:**
   - `apparatus`
   - `apparatus_revenue`
   - `apparatus_type_master`
   - `clients`
   - `employees`
   - `equipment`
   - `estimators`
   - `locations`
   - `neta_test_templates`
   - `project_financial_summary`
   - `projects`
   - `scope_financial_summary`
   - `scope_labor_details`
   - `scopes`
   - `sites`
   - `tasks`

   **PSS Portal:**
   - `pss_activity_log`
   - `pss_contacts`
   - `pss_document_templates`
   - `pss_documents`
   - `pss_engineers`
   - `pss_projects`
   - `pss_rfis`
   - `pss_users`

3. Click on `projects` to see LASNAP16 test data
4. Click on `pss_projects` to see PSS studies (Job 629266 - SWA Tech Ops, etc.)

---

## Connection Details

After setup, get these from **Settings → Database**:

```
Host: db.<project-ref>.supabase.co
Port: 5432
Database: postgres
User: postgres
Password: [your password from Step 1]
```

### API Connection (for apps)

From **Settings → API**:

```
Project URL: https://<project-ref>.supabase.co
Anon Key: eyJhbGciOi... (public, safe for client)
Service Key: eyJhbGciOi... (SECRET - server only!)
```

---

## Option A: NocoDB UI (Airtable-like interface)

For immediate spreadsheet-like access:

1. Go to [nocodb.com](https://www.nocodb.com/)
2. Sign up (free tier available)
3. Create workspace
4. Click **"Connect to a data source"**
5. Select **PostgreSQL**
6. Enter your Supabase connection details:
   ```
   Host: db.<project-ref>.supabase.co
   Port: 5432
   Database: postgres
   User: postgres
   Password: [your password]
   ```
7. NocoDB will import all tables and create forms/views automatically!

---

## Option B: Direct Supabase Dashboard

Supabase's built-in Table Editor works well for:
- Viewing/editing data
- Running SQL queries
- Testing API calls

---

## Testing the API

### Quick test with curl (PowerShell):

```powershell
# Replace with your actual values
$SUPABASE_URL = "https://YOUR-PROJECT-REF.supabase.co"
$SUPABASE_KEY = "YOUR-ANON-KEY"

# Get all projects
Invoke-RestMethod -Uri "$SUPABASE_URL/rest/v1/projects?select=*" `
    -Headers @{
        "apikey" = $SUPABASE_KEY
        "Authorization" = "Bearer $SUPABASE_KEY"
    }
```

### JavaScript/Node.js:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
    'https://YOUR-PROJECT-REF.supabase.co',
    'YOUR-ANON-KEY'
)

// Get all active projects
const { data, error } = await supabase
    .from('projects')
    .select('*, scopes(*)')
    .eq('is_active', true)
    .order('project_number')

console.log(data)
```

### Python:

```python
from supabase import create_client

supabase = create_client(
    "https://YOUR-PROJECT-REF.supabase.co",
    "YOUR-ANON-KEY"
)

# Get LASNAP16 project with scopes
response = supabase.table('projects') \
    .select('*, scopes(*)') \
    .eq('project_number', 'LASNAP16') \
    .execute()

print(response.data)
```

---

## Data Migration from Dataverse

If you need to migrate existing Dataverse data:

### Export from Dataverse:

```powershell
# Use existing MCP server or Power Automate to export
# Each entity to CSV format
```

### Import to Supabase:

1. **CSV Import** (Table Editor → Import CSV)
2. **SQL INSERT** (for bulk data)
3. **API** (for programmatic migration)

---

## Row Level Security (Optional but Recommended)

For production, enable RLS:

```sql
-- Enable RLS on all tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE scopes ENABLE ROW LEVEL SECURITY;
-- etc...

-- Example policy: Users can read all active records
CREATE POLICY "Read active records" ON projects
    FOR SELECT USING (is_active = true);
```

---

## Next Steps After Setup

1. ✅ **Verify data loads correctly**
2. 🔜 **Connect NocoDB or Retool for UI**
3. 🔜 **Set up Power Automate flows to sync with existing systems**
4. 🔜 **Build custom dashboards with Supabase Realtime**
5. 🔜 **Configure authentication for field users**

---

## Troubleshooting

### "Permission denied" error
- Make sure you're using the `postgres` user
- Check password is correct

### "Table already exists" error
- Drop tables first: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
- Re-run schema script

### "Foreign key violation" on test data
- Make sure you ran `01_supabase_schema.sql` first
- Tables must exist before inserting data

---

## Files in this folder

| File | Purpose |
|------|---------|
| `01_supabase_schema.sql` | Creates core operations tables (16 tables) |
| `02_test_data.sql` | Populates sample data (LASNAP16 project) |
| `03_pss_portal_tables.sql` | Creates PSS Portal tables (8 tables) |
| `04_pss_portal_test_data.sql` | Populates PSS sample data (5 studies) |
| `README.md` | This setup guide |

---

## Support

Questions? Check:
- [Supabase Docs](https://supabase.com/docs)
- [NocoDB Docs](https://docs.nocodb.com/)
- RESA project documentation in `/Documentation/` folder
