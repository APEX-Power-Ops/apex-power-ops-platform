# RESA Power System State & Data Model Review
> **Date**: November 30, 2025  
> **Version**: Post-Import Pipeline Implementation  
> **Purpose**: Objective review of current architecture before further development

---

## 📊 Current System Overview

### What We've Built

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **VBA Export Module** | `DataverseExport.bas` | Export Excel estimator → JSON | ✅ Working v1.1 |
| **Next.js Web App** | `resa-web-app/` | Task configuration UI + Dataverse import | ✅ Working |
| **MCP Server** | `resa-dataverse-mcp/` | Copilot ↔ Dataverse integration | ✅ Working |
| **PowerShell Templates** | `Scripts/PowerShell/Templates/` | Schema discovery & operations | ✅ Working |
| **Node Import Script** | `import-estimator.js` | Direct JSON → Dataverse (legacy) | ✅ Working |

### Import Pipeline Flow
```
Excel Estimator → VBA Export → JSON (Clipboard) → Web App → Configure Tasks → Dataverse API
                                      ↓
                              (OR) JSON File → Node Script → Dataverse API
```

---

## 🗃️ Complete Dataverse Table Inventory

### 21 Custom Tables Currently

| # | Table Name | Purpose | Used By Import? | Status |
|---|------------|---------|-----------------|--------|
| 1 | **cr950_clients** | Customer organizations | ✅ Yes | Core |
| 2 | **cr950_sites** | Physical work locations | ✅ Yes | Core |
| 3 | **cr950_projectses** | Project header records | ✅ Yes | Core |
| 4 | **cr950_projectscopes** | Scope of work divisions | ✅ Yes | Core |
| 5 | **cr950_taskses** | Work breakdown within scopes | ✅ Yes | Core |
| 6 | **cr950_apparatuses** | Individual equipment items | ✅ Yes | Core |
| 7 | **cr950_scopelabordetailses** | Financial rollups per scope | ✅ Node script | Financial |
| 8 | **cr950_apparatusrevenues** | Revenue per apparatus | ❌ No | Financial |
| 9 | **cr950_projectfinancialsummaries** | Project-level financials | ❌ No | Financial |
| 10 | **cr950_scopefinancialsummaries** | Scope-level financials | ❌ No | Financial |
| 11 | **cr950_estimators** | Estimator file tracking | ⚠️ Partial | Tracking |
| 12 | **cr950_apparatustypemasters** | Master list of equipment types | ❌ No | Reference |
| 13 | **cr950_employees** | Employee/resource list | ❌ No | Resources |
| 14 | **cr950_resourceassignments** | Who's assigned to what | ❌ No | Resources |
| 15 | **cr950_equipments** | Company-owned test equipment | ❌ No | Assets |
| 16 | **cr950_quotes** | Quote documents | ❌ No | Sales |
| 17 | **cr950_businessunits** | Organizational structure | ❌ No | Org |
| 18 | **cr950_netatesttemplates** | NETA test form templates | ❌ No | Testing |
| 19 | **cr950_apparatustestchecklists** | Per-apparatus test checklists | ❌ No | Testing |
| 20 | **cr950_apparatussubmissions** | Completed test submissions | ❌ No | Testing |
| 21 | **cr950_projectdocuments** | Document attachments | ❌ No | Documents |

---

## 🔍 Table-by-Table Field Analysis

### 1. Clients (`cr950_clients`) ✅ GOOD
**Purpose**: Customer organizations  
**Fields**: 25 custom fields

| Field | Type | Needed? | Notes |
|-------|------|---------|-------|
| cr950_name | String | ✅ | Primary name |
| cr950_clientnumber | String | ✅ | For internal tracking |
| cr950_clienttype | Choice | ⚠️ | Not used yet |
| cr950_accountstatus | Choice | ⚠️ | Not used yet |
| cr950_primarycontact* | Various | ✅ | Contact info |
| cr950_billingcontact* | Various | ✅ | Billing contact |
| cr950_billingaddress | String | ✅ | Billing |
| cr950_mailing* | Various | ⚠️ | Redundant with Site? |
| cr950_creditlimit | Currency | ⚠️ | AR system feature |
| cr950_paymentterms | String | ⚠️ | AR system feature |
| cr950_taxid | String | ⚠️ | Tax compliance |
| cr950_insurance* | Various | ⚠️ | Subcontractor tracking? |

**Assessment**: Good core structure. Some AR/accounting fields that may not be needed.

---

### 2. Sites (`cr950_sites`) ✅ GOOD
**Purpose**: Physical work locations  
**Fields**: 24 custom fields

| Field | Type | Needed? | Notes |
|-------|------|---------|-------|
| cr950_name | String | ✅ | Site name |
| cr950_sitenumber | String | ⚠️ | Not widely used |
| cr950_address/city/state/zip | String | ✅ | Location |
| cr950_county | String | ⚠️ | Rarely used |
| cr950_latitude/longitude | Decimal | ⚠️ | For mapping - nice to have |
| cr950_client (Lookup) | Lookup | ✅ | Links to Client |
| cr950_sitecontact* | Various | ✅ | Site contact |
| cr950_sitetype | Choice | ⚠️ | Not standardized |
| cr950_status | Choice | ⚠️ | Not used |
| cr950_accessrequirements | Text | ✅ | Field ops need |
| cr950_parkinginstructions | Text | ⚠️ | Nice to have |
| cr950_safetyprotocols | Text | ✅ | Safety critical |
| cr950_utility* | Various | ⚠️ | Rarely used |

**Assessment**: Good. Could trim a few fields, but solid structure.

---

### 3. Projects (`cr950_projectses`) ⚠️ REVIEW NEEDED
**Purpose**: Project header/master record  
**Fields**: 72 custom fields (!)

**Core Fields (Keep)**:
- cr950_project_name, cr950_job_number, cr950_project_manager
- cr950_description, cr950_start_date, cr950_target_completion_date
- cr950_contract_number, cr950_contract_value, cr950_contract_url
- cr950_sharepoint_folder_url

**Lookup Fields (Keep)**:
- cr950_client, cr950_site, cr950_location (duplicate of site?)

**Rollup/Calculated Fields (20+ fields)**:
- cr950_total_apparatus_count + _date + _state
- cr950_completed_apparatus_count + _date + _state
- cr950_total_apparatus_hours + _date + _state
- cr950_total_actual_hours + _date + _state
- cr950_total_completed_hours + _date + _state
- cr950_total_remaining_hours + _date + _state
- cr950_total_delays + _date + _state
- cr950_percent_complete
- cr950_earliest/latest + actualstart/anticipatedstart/completiondate (12 fields!)

**Sync/Integration Fields**:
- cr950_externalsystemid, cr950_externalsystemname
- cr950_datasource, cr950_syncstatus, cr950_lastsyncdate
- cr950_isdeleted, cr950_deletedon

**Observations**:
1. **Too many rollup fields** - 20+ calculated fields with date/state variants
2. **Duplicate lookups** - cr950_location and cr950_site seem redundant
3. **Over-engineered tracking** - 12 fields for date tracking (earliest/latest × 3 stages)
4. **Good sync infrastructure** - External system tracking is forward-thinking

---

### 4. Scopes (`cr950_projectscopes`) ⚠️ SIMILAR ISSUES
**Purpose**: Divisions of work within a project  
**Fields**: 62 custom fields

**Core Fields**:
- cr950_scope_name, cr950_scope_number, cr950_description
- cr950_testing_standard (ATS/MTS choice)
- cr950_sld_reference, cr950_tags

**Lookups**:
- cr950_project, cr950_site

**Rollup Fields**: Same pattern as Projects - 20+ calculated fields

**Assessment**: Same issue - over-engineered rollups. Core fields are good.

---

### 5. Tasks (`cr950_taskses`) ⚠️ NEEDS SIMPLIFICATION
**Purpose**: Work breakdown structure  
**Fields**: 57 custom fields

**Core Fields**:
- cr950_task_name, cr950_task_number, cr950_description

**Lookups**:
- cr950_project, cr950_scope

**Oddity**: 
- cr950_apparatus_type (String) - Why is this here? Tasks contain multiple apparatus types.

**Rollup Fields**: Same 20+ rollup pattern

---

### 6. Apparatus (`cr950_apparatuses`) ✅ MOSTLY GOOD
**Purpose**: Individual equipment items to test  
**Fields**: 47 custom fields

**Core Fields (Essential)**:
- cr950_apparatus_designation (name/identifier)
- cr950_apparatus_number (sequence)
- cr950_apparatustype (string - equipment type name)
- cr950_labor_hours (estimated hours)
- cr950_manufacturer, cr950_serial_number, cr950_voltage_class

**Tracking Fields**:
- cr950_actual_hours, cr950_completed_hours, cr950_remaining_hours
- cr950_completion_status, cr950_checklist_status
- cr950_anticipatedstart, cr950_actualstart, cr950_datecompleted
- cr950_delays

**Lookups**:
- cr950_apparatus_type → cr950_apparatustypemaster (unused lookup!)
- cr950_task, cr950_scope, cr950_project
- cr950_assigned_employee

**Submission Tracking**:
- cr950_datasheet_completed, cr950_submitted_date, cr950_approval_date

**Observations**:
1. Has BOTH `cr950_apparatustype` (string) AND `cr950_apparatus_type` (lookup)
2. Lookup to ApparatusTypeMaster not being used
3. Otherwise well-structured

---

### 7. ScopeLaborDetails (`cr950_scopelabordetailses`) ⚠️ REDUNDANT?
**Purpose**: Financial breakdown per scope  
**Fields**: 40 custom fields

**Core Fields**:
- cr950_total_apparatus_hours, cr950_scopemultiplier, cr950_scope_total_value
- cr950_onsitelaborrate/total, cr950_offsitelaborrate/total
- cr950_travelrate/total, cr950_outsideservicesrate/total
- cr950_effectivelaborrate

**Versioning**:
- cr950_versionnumber, cr950_iscurrentversion, cr950_effectivedate, cr950_expirationdate

**Observations**:
1. Designed for quote versioning - good concept
2. Currently being created during import
3. Could this data live directly on Scope table instead?

---

## 🔗 Relationship Analysis

### Current Hierarchy
```
Client (1)
  └── Site (N)
        └── Project (N)
              └── Scope (N)
                    ├── Task (N)
                    │     └── Apparatus (N)
                    ├── Apparatus (N) - can be unassigned to task
                    └── ScopeLaborDetail (N) - financial versions
```

### Issues Found

1. **Project → Site vs Project → Client**
   - Project links to both Site AND Client
   - But Site already links to Client
   - Redundant relationship?

2. **Apparatus → Task vs Apparatus → Scope**
   - Apparatus links to both Scope AND Task
   - Task links to Scope
   - Could simplify: Apparatus → Task → Scope

3. **Location vs Site on Projects**
   - cr950_location AND cr950_site fields exist
   - Likely redundant

---

## 🚨 Key Issues Identified

### 1. Rollup Field Explosion
**Problem**: Every table has 20+ calculated/rollup fields with _date and _state suffixes.
- Total: ~80 rollup fields across 4 tables
- Each has 3 variants: value, date, state

**Why It Happened**: Dataverse rollup fields require date/state fields for async calculation.

**Recommendation**: 
- These are working correctly for aggregation
- Consider: Do we need ALL of these, or just key metrics?
- Key metrics to keep: total_apparatus_count, total_hours, percent_complete
- Could potentially remove: earliest/latest tracking (12 fields × 4 tables = 48 fields)

### 2. Duplicate Fields
| Field 1 | Field 2 | Table | Issue |
|---------|---------|-------|-------|
| cr950_apparatustype (string) | cr950_apparatus_type (lookup) | Apparatus | Using string, lookup unused |
| cr950_site | cr950_location | Projects | Same purpose |
| cr950_client_name | cr950_clientname | Projects | Redundant text fields |

### 3. Unused Tables
These tables exist but aren't integrated into the import workflow:
- `cr950_apparatustypemasters` - Master list (could standardize apparatus types)
- `cr950_quotes` - Quote tracking
- `cr950_employees` / `cr950_resourceassignments` - Resource management
- `cr950_netatesttemplates` / `cr950_apparatustestchecklists` - Test forms
- `cr950_equipments` - Company equipment inventory

### 4. Naming Inconsistencies
| Table | Field | Issue |
|-------|-------|-------|
| Projects | cr950_projectses | Awkward pluralization |
| Tasks | cr950_taskses | Awkward pluralization |
| ScopeLaborDetails | cr950_scopelabordetailses | Triple awkward |

*Note: EntitySetName pluralization is auto-generated by Dataverse, can't be changed without recreating table.*

---

## ✅ What's Working Well

1. **Core Entity Model**: Client → Site → Project → Scope → Task → Apparatus makes business sense
2. **Import Pipeline**: Excel → Web App → Dataverse flow is functional
3. **Field Naming Convention**: cr950_ prefix is consistent
4. **Sync Infrastructure**: External system ID/status fields ready for D365 integration
5. **Financial Model**: ScopeLaborDetail captures quote economics correctly

---

## 📋 Recommendations

### Immediate (Before More Development)

1. **Decide on ApparatusTypeMaster Usage**
   - Option A: Use the lookup field, standardize equipment types
   - Option B: Remove lookup, keep using string field (current approach)
   - Recommendation: **Option B** - String is simpler, standardization not critical now

2. **Clean Up Project Table**
   - Remove cr950_location if cr950_site is used
   - Consolidate cr950_client_name / cr950_clientname

3. **Simplify Date Tracking (Optional)**
   - If earliest/latest date tracking not used, consider removal (saves 48 fields)
   - This is lower priority - they don't hurt anything

### Medium-Term

4. **Decide on ScopeLaborDetail Future**
   - Keep separate table for quote versioning? 
   - Or move financials to Scope table?
   - Current approach works fine

5. **Integrate Unused Tables Gradually**
   - ApparatusTypeMaster - for standardized reporting
   - Employees - for resource tracking
   - TestChecklists - for field data capture

### Not Recommended

- ❌ Recreating tables to fix EntitySetName pluralization
- ❌ Major restructuring of working relationships
- ❌ Removing rollup fields that are calculating correctly

---

## 🖥️ Next.js Web App Details

### Location
`C:\Users\jjswe\Projects\resa-web-app`

### Tech Stack
- **Framework**: Next.js 16.0.5 (Turbopack)
- **Auth**: MSAL for Azure AD
- **UI**: Tailwind CSS + shadcn/ui components
- **State**: React useState/useEffect (no external state management)

### Key Routes
| Route | Purpose | Status |
|-------|---------|--------|
| `/` | Dashboard (placeholder) | ✅ Working |
| `/import` | JSON paste/upload | ✅ Working |
| `/import/configure` | Task configuration + Dataverse submit | ✅ Working |
| `/projects` | Project list | 🔲 Not built |

### Environment Variables
```env
NEXT_PUBLIC_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
NEXT_PUBLIC_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
NEXT_PUBLIC_DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
```

### Core Files
```
src/
├── app/
│   ├── page.tsx                 # Dashboard
│   └── import/
│       ├── page.tsx             # JSON input
│       └── configure/
│           └── page.tsx         # Task config + Dataverse API calls
├── components/
│   ├── auth-provider.tsx        # MSAL auth context
│   └── ui/                      # shadcn components
├── lib/
│   └── dataverse.ts             # Dataverse API client
└── types/
    └── import.ts                # TypeScript interfaces
```

### Dataverse Field Mapping (configure/page.tsx)
```typescript
// Sites
cr950_name, cr950_address, cr950_city, cr950_state, cr950_zip

// Projects  
cr950_project_name, cr950_job_number, cr950_project_manager

// Scopes
cr950_scope_name, cr950_scope_number, "cr950_Project@odata.bind"

// Tasks
cr950_task_name, cr950_task_number, "cr950_Scope@odata.bind"

// Apparatus
cr950_apparatus_designation, cr950_apparatustype, cr950_labor_hours, 
cr950_apparatus_number, "cr950_Scope@odata.bind", "cr950_Task@odata.bind"
```

---

## 📁 VBA Module Details

### Location
`Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas`

### Version
1.1 (November 30, 2025)

### Functions
| Function | Purpose |
|----------|---------|
| `ExportToDataverse()` | Main entry - clipboard + optional file save |
| `ExportToClipboardOnly()` | Quick clipboard export |
| `QuickValidate()` | Preview export without generating |

### JSON Structure Output
```json
{
  "metadata": { "version": "1.1", "exportDate": "..." },
  "client": { "name": "..." },
  "site": { "name": "...", "address": "...", "city": "...", "state": "...", "zipCode": "..." },
  "project": { "name": "...", "projectNumber": "...", "projectLead": "..." },
  "scopes": [
    {
      "name": "Scope1",
      "scopeType": "NETA ATS",
      "totalHours": 100,
      "multiplier": 1.5,
      "quotedAmount": 25000,
      "financials": { ... },
      "apparatus": [
        { "section": "...", "equipmentType": "...", "quantity": 1, "hoursPerUnit": 2.5 }
      ]
    }
  ],
  "summary": { "totalScopes": 4, "grandTotal": 97000 }
}
```

---

## 📊 Summary Metrics

| Metric | Count |
|--------|-------|
| Custom Tables | 21 |
| Total Custom Fields | ~650 |
| Rollup Fields | ~80 |
| Lookup Relationships | 26 |
| Tables in Active Use | 7 |
| Tables Unused | 14 |

---

## 🎯 Next Steps

1. **Document this review** ✅ (this file)
2. **Update PROJECT_CONTEXT.json** with latest state
3. **Decide on recommendations** - which changes to implement
4. **Continue development** with clear understanding of data model
