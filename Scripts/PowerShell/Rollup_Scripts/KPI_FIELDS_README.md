# KPI Fields API Scripts

Created: November 22, 2025  
Purpose: PowerShell scripts for implementing KPI fields (Date Tracking + Financial Rollups)

---

## 📋 Overview

These scripts implement the KPI fields architecture described in `KPI_FIELDS_IMPLEMENTATION_PRIORITY.md`:

**Phase 1: Date Tracking** (Operational fields)
- 3 base date fields on Apparatus table
- 18 rollup fields on Tasks, Scopes, Projects (manual config)

**Phase 2: Financial Summary Tables** (Separated financial data)
- 2 new tables: Scope Financial Summary + Project Financial Summary
- 14 revenue rollup fields (manual config)
- Maintains separation between operations and finance

---

## 🚀 Quick Start

### Prerequisites

1. **Environment Variables Set:**
   ```powershell
   $env:DATAVERSE_URL      # e.g., https://org90c66be2.crm.dynamics.com
   $env:AZURE_TENANT_ID    # Your tenant ID
   $env:AZURE_CLIENT_ID    # Your app registration client ID
   $env:AZURE_CLIENT_SECRET # Your app registration secret
   ```

2. **Verify Connection:**
   ```powershell
   . .\Scripts\PowerShell\Dataverse-Functions.ps1
   Connect-Dataverse
   Get-DataverseConnection
   ```

---

## 📂 Scripts

### 1. **Implement-KPIFields.ps1** (Master Script)

**Usage:**
```powershell
# Show status and menu (default)
.\Scripts\PowerShell\Implement-KPIFields.ps1

# Execute Phase 1 only (Date Tracking)
.\Scripts\PowerShell\Implement-KPIFields.ps1 -Phase DateTracking

# Execute Phase 2 only (Financial Summary Tables)
.\Scripts\PowerShell\Implement-KPIFields.ps1 -Phase FinancialSummary

# Execute both phases
.\Scripts\PowerShell\Implement-KPIFields.ps1 -Phase All
```

**What it does:**
- Displays implementation status and menu
- Orchestrates phase execution
- Provides confirmation prompts
- Shows next steps after completion

---

### 2. **Add-DateTrackingFields.ps1** (Phase 1)

**Usage:**
```powershell
.\Scripts\PowerShell\Add-DateTrackingFields.ps1
```

**What it creates via API:**
- `cr950_anticipated_start` (DateTime) on Apparatus
- `cr950_actual_start` (DateTime) on Apparatus
- `cr950_date_completed` (DateTime) on Apparatus

**Manual steps after:**
1. Add 6 rollup fields to Tasks table (from Apparatus)
2. Add 6 rollup fields to Scopes table (from Apparatus)
3. Add 6 rollup fields to Projects table (from Scopes)

See: `DATE_TRACKING_IMPLEMENTATION.md` for exact field specs

**Time:** 15 minutes API + 2 hours manual config

---

### 3. **Create-FinancialSummaryTables.ps1** (Phase 2)

**Usage:**
```powershell
.\Scripts\PowerShell\Create-FinancialSummaryTables.ps1
```

**What it creates via API:**

**Scope Financial Summary Table:**
- Table: `cr950_scopefinancialsummary`
- Lookup field: `cr950_scopeid` → Scope (1:1)

**Project Financial Summary Table:**
- Table: `cr950_projectfinancialsummary`
- Lookup field: `cr950_projectid` → Project (1:1)

**Manual steps after:**
1. Add 7 rollup fields to Scope Financial Summary (from Apparatus Revenue)
2. Add 7 rollup fields to Project Financial Summary (from Scope Financial Summary)
3. Configure security roles (Finance, Operations, PM)
4. Create Power Automate flows (auto-create financial records)
5. Create finance dashboard views

See: `KPI_FIELDS_IMPLEMENTATION_PRIORITY.md` Section "Phase 2" for exact specs

**Time:** 10 minutes API + 1.5 hours manual config

---

## 🎯 Recommended Workflow

### Week 1: Date Tracking (Phase 1)

**Day 1:**
```powershell
# 1. Run date tracking script
.\Scripts\PowerShell\Add-DateTrackingFields.ps1

# 2. Verify fields created
# Navigate to Apparatus table in Dataverse UI
# Confirm 3 date fields exist
```

**Day 2-3:**
```
Manual UI Configuration:
1. Tasks table → Add 6 date rollup fields
2. Scopes table → Add 6 date rollup fields  
3. Projects table → Add 6 date rollup fields
4. Create 6 KPI views (Upcoming Work, Overdue, etc.)
5. Update forms to show date fields
6. Test with sample data
7. Export as v1.5.0.0
```

### Week 2: Financial Rollups (Phase 2)

**Day 1:**
```powershell
# 1. Run financial summary script
.\Scripts\PowerShell\Create-FinancialSummaryTables.ps1

# 2. Verify tables created
# Navigate to Tables in Dataverse UI
# Confirm 2 new financial summary tables exist
```

**Day 2-3:**
```
Manual UI Configuration:
1. Scope Financial Summary → Add 7 revenue rollup fields
2. Project Financial Summary → Add 7 revenue rollup fields
3. Configure security roles (Finance, Operations, PM)
4. Create Power Automate flows (auto-create records)
5. Create finance dashboard views
6. Test rollups with completed apparatus
7. Export as v1.5.1.0
```

---

## 🧪 Testing

### Test Date Tracking:

```powershell
# Connect to Dataverse
. .\Scripts\PowerShell\Dataverse-Functions.ps1
Connect-Dataverse

# Create test apparatus with anticipated start
$apparatus = @{
    "cr950_name" = "Test Apparatus - Date Tracking"
    "cr950_anticipated_start" = (Get-Date).AddDays(7).ToString("yyyy-MM-ddTHH:mm:ssZ")
}
New-DataverseRecord -EntityName "cr950_apparatus" -Data $apparatus

# Verify rollups calculate at Task/Scope/Project levels
# Wait 5 minutes, then check via UI
```

### Test Financial Rollups:

```powershell
# 1. Create apparatus
# 2. Mark complete (triggers revenue flow via existing Power Automate)
# 3. Wait 5 minutes for rollups
# 4. Check Scope Financial Summary record shows revenue
# 5. Check Project Financial Summary record aggregates from scopes
```

---

## 📊 Architecture Benefits

### Separation of Concerns:

**Operational Tables** (Projects, Scopes, Tasks, Apparatus):
- Date tracking fields for schedule visibility
- NO financial data
- Operations team has full access
- Focus: Work execution and scheduling

**Financial Tables** (Scope/Project Financial Summary):
- Revenue rollup fields
- NO operational fields
- Finance team has full access
- Focus: Revenue recognition and billing

### Security Model:

| Role | Operational Tables | Financial Tables |
|------|-------------------|------------------|
| **Operations** | Full CRUD | No Access |
| **Finance** | Read Only | Full CRUD |
| **PM** | Full CRUD | Read Only |
| **Executive** | Read Only | Read Only |

### Performance Benefits:

- ✅ Finance reports query small financial tables
- ✅ Operations reports query operational tables
- ✅ Rollups calculate faster (fewer records per table)
- ✅ Independent scaling for each domain

---

## 🗂️ Output Files

Each script creates a log file in `Logs/`:

**Date Tracking:**
```
Logs/DateTrackingFields_YYYYMMDD_HHMMSS.json
```

**Financial Summary:**
```
Logs/FinancialSummaryTables_YYYYMMDD_HHMMSS.json
```

Contains:
- Creation timestamp
- Field definitions
- Table metadata
- Manual steps remaining

---

## ⚠️ Important Notes

### Rollup Fields Cannot Be Created via API

**Limitation:** Dataverse Web API does not support creating rollup fields programmatically.

**Workaround:** Scripts create base fields and tables, then provide exact specifications for manual UI configuration.

**Documentation:** All rollup field specs documented in:
- `DATE_TRACKING_IMPLEMENTATION.md` (date rollups)
- `KPI_FIELDS_IMPLEMENTATION_PRIORITY.md` (revenue rollups)

### Existing Fields

**Date Completed:** May already exist on Apparatus table (used by revenue recognition flow). Script checks for existence and skips if found.

### Power Automate Dependencies

**Existing Flow:** "Revenue Recognition Flow" already creates Apparatus Revenue records when apparatus completes.

**New Flows Needed:**
1. Auto-create Scope Financial Summary when Scope created
2. Auto-create Project Financial Summary when Project created

See: `KPI_FIELDS_IMPLEMENTATION_PRIORITY.md` Phase 2, Step 4

---

## 📖 Related Documentation

- **KPI_FIELDS_IMPLEMENTATION_PRIORITY.md** - Master specification
- **DATE_TRACKING_IMPLEMENTATION.md** - Date tracking detailed specs
- **REVENUE_RECOGNITION_FLOW_SPEC.md** - Existing revenue flow
- **V1_4_0_0_ROADMAP_AND_PRIORITIES.md** - Overall roadmap
- **PROJECT_STATUS_TRACKER.md** - Current system state

---

## 🆘 Troubleshooting

### Connection Failed

```powershell
# Check environment variables
$env:DATAVERSE_URL
$env:AZURE_TENANT_ID
$env:AZURE_CLIENT_ID
$env:AZURE_CLIENT_SECRET

# Test connection manually
. .\Scripts\PowerShell\Dataverse-Functions.ps1
Connect-Dataverse
Get-DataverseConnection
```

### Field Already Exists

Script will skip and show warning. This is normal for `cr950_date_completed` which may exist from earlier implementation.

### Rollup Not Calculating

1. Wait 5-10 minutes (rollups are async)
2. Check related records exist
3. Verify filter conditions correct
4. Manually trigger recalculation in UI

### Security Access Denied

Ensure Azure App Registration has:
- `System Administrator` security role
- API permissions: `Dynamics CRM` → `user_impersonation`

---

## ✅ Success Criteria

### Phase 1 Complete:
- ✅ 3 date fields on Apparatus visible in UI
- ✅ 18 rollup fields added manually
- ✅ KPI views functional
- ✅ Forms updated
- ✅ Sample data tests pass
- ✅ Exported as v1.5.0.0

### Phase 2 Complete:
- ✅ 2 financial summary tables exist
- ✅ 14 rollup fields added manually
- ✅ Security roles configured
- ✅ Power Automate flows created
- ✅ Finance dashboards functional
- ✅ Rollup tests pass
- ✅ Exported as v1.5.1.0

---

**Total Time:** 5-6 hours (30 min API + 4.5-5.5 hours manual config)  
**Business Value:** $50,000-80,000 annual time savings + improved decision-making
