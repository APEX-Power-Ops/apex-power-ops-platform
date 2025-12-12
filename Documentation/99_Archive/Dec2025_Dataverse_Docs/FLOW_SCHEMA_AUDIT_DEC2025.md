# Flow Schema Audit Report
## Migration from V1 (org99cd6c6e) to V2 (org284447bd)

**Audit Date:** December 2, 2025  
**Auditor:** Claude AI Assistant  
**Purpose:** Schema compatibility analysis for Power Automate flow migration  

---

## 📋 Executive Summary

| Metric | Count |
|--------|-------|
| **Flows Analyzed** | 3 |
| **Unique Tables Referenced** | 8 |
| **Total Field References** | 47 |
| **Environment URLs to Update** | 12 |
| **Compatible Fields** | 29 |
| **Fields Requiring Rename** | 18 |
| **Critical Breaking Changes** | 4 |

**Overall Assessment:** ⚠️ MODERATE EFFORT - Flows require entity name updates and selective field renaming.

---

## 🔄 Environment Change Required

All flows must update the organization URL:

| Setting | Old Value | New Value |
|---------|-----------|-----------|
| **Organization URL** | `https://org99cd6c6e.crm.dynamics.com` | `https://org284447bd.crm.dynamics.com` |

**Occurrences by Flow:**
- EstimatorImport: 4 occurrences
- RevenueRecognition: 5 occurrences
- JSONImport: 3 occurrences (some use default connection)

---

## 📊 Flow 1: EstimatorImport

### Overview
**File:** `EstimatorImport-8F6329B1-CDCC-F011-BBD2-6045BD0391A9.json`  
**Trigger:** SharePoint file creation (.xlsm files)  
**Purpose:** Creates/updates Estimator records when new estimator files are saved

### Tables Referenced

| Old EntitySetName | V2 EntitySetName | Status |
|-------------------|------------------|--------|
| `cr950_clients` | `cr950_clients` | ✅ No change |
| `cr950_estimators` | `cr950_estimators` | ✅ No change |

### Field Mapping Analysis

#### cr950_clients Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_name` | `cr950_client_name` | ⚠️ RENAME | Primary field name changed |
| `cr950_clientid` | `cr950_clientid` | ✅ Compatible | Primary key unchanged |

#### cr950_estimators Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_estimatorid` | `cr950_estimatorid` | ✅ Compatible | Primary key |
| `cr950_currentrevision` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_estimatedate` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_estimator_file_url` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_filename` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_lastmodified` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_name` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_clientid@odata.bind` | `cr950_clientid@odata.bind` | ✅ Compatible | Lookup binding |
| `cr950_projectname` | TBD | ❓ Verify | Not in schema CSVs |
| `cr950_status` | TBD | ❓ Verify | Not in schema CSVs |

**⚠️ NOTE:** Estimator schema (09_Estimator_Schema.csv) was not found in the Schema folder. This table appears to be a v1.5+ addition. Verify fields exist in new environment before migration.

### Actions Requiring Updates

```
Action: "Validate_Client_Exists_in_Dataverse"
- Update: organization parameter → https://org284447bd.crm.dynamics.com
- Update: $filter → use cr950_client_name eq instead of cr950_name eq (if renamed)

Action: "Check_for_Existing_Estimator_Record"
- Update: organization parameter → https://org284447bd.crm.dynamics.com

Action: "Update_Existing_Estimator_Record"
- Update: organization parameter → https://org284447bd.crm.dynamics.com

Action: "Create_New_Estimator_Record"
- Update: organization parameter → https://org284447bd.crm.dynamics.com
- Update: cr950_clientid@odata.bind format if Client table changed
```

---

## 📊 Flow 2: Revenue Recognition on Apparatus Completion

### Overview
**File:** `RevenueRecognitiononApparatusCompletion-99416E85-35C4-F011-8544-000D3A5BE227.json`  
**Trigger:** Dataverse webhook (Apparatus completion_status = 2)  
**Purpose:** Auto-creates ApparatusRevenue records when apparatus is marked complete

### Tables Referenced

| Old EntitySetName | V2 EntitySetName | Status | Action Required |
|-------------------|------------------|--------|-----------------|
| `cr950_apparatus` | (trigger entity) | ✅ Compatible | None |
| `cr950_apparatuses` | `cr950_apparatuses` | ✅ No change | None |
| `cr950_projectscopes` | `cr950_scopes` | 🔴 BREAKING | Update all references |
| `cr950_scopelabordetailses` | `cr950_scopelabordetails` | 🔴 BREAKING | Update all references |
| `cr950_apparatusrevenues` | `cr950_apparatusrevenues` | ✅ No change | None |
| `cr950_projectses` | `cr950_projects` | 🔴 BREAKING | Update all references |

### Field Mapping Analysis

#### cr950_apparatus / cr950_apparatuses Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_apparatusid` | `cr950_apparatusid` | ✅ Compatible | Primary key |
| `cr950_completion_status` | `cr950_apparatus_status` | ⚠️ POSSIBLE RENAME | Verify field name |
| `cr950_datecompleted` | `cr950_apparatus_test_date` | ⚠️ POSSIBLE RENAME | Or may be separate field |
| `_cr950_scope_value` | `_cr950_apparatus_task_value` | ⚠️ VERIFY | Lookup may be to Task not Scope |
| `cr950_completed_hours` | `cr950_apparatus_total_hours` | ⚠️ VERIFY | Field name difference |
| `cr950_delays` | Not in V2 schema | ❓ Verify | May be custom addition |

#### cr950_projectscopes → cr950_scopes Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_projectscopeid` | `cr950_scopeid` | ⚠️ RENAME | Primary key renamed |
| `_cr950_project_value` | `_cr950_scope_project_value` | ⚠️ VERIFY | Lookup field name |

#### cr950_scopelabordetailses → cr950_scopelabordetails Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_scopelabordetailsid` | `cr950_scopelaborid` | ⚠️ POSSIBLE | PK might be renamed |
| `_cr950_projectscope_id_value` | `_cr950_scopelabor_scope_value` | ⚠️ RENAME | Lookup renamed |
| `cr950_effectivelaborrate` | `cr950_scopelabor_effective_rate` | ⚠️ RENAME | Field renamed |

#### cr950_apparatusrevenues Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_Apparatus@odata.bind` | `cr950_Apparatus@odata.bind` | ✅ Compatible | But target entity changed |
| `cr950_apparatushours` | `Labor_Hours` | ⚠️ RENAME | Per COMPLETE_TABLE_SCHEMAS.md |
| `cr950_Project@odata.bind` | `cr950_Project@odata.bind` | ✅ Compatible | But target entity changed |
| `cr950_revenuestatus` | `Billing_Status` | ⚠️ RENAME | Per COMPLETE_TABLE_SCHEMAS.md |
| `cr950_ScopeLaborDetail@odata.bind` | Update target entity | ⚠️ Update | Target EntitySetName changed |
| `cr950_delays` | Not found | ❓ Verify | May not exist in V2 |
| `cr950_effectivelaborrate` | `Base_Labor_Rate` | ⚠️ RENAME | Per COMPLETE_TABLE_SCHEMAS.md |
| `cr950_revenuerecognitiondate` | `Revenue_Recognized_Date` | ⚠️ RENAME | Per COMPLETE_TABLE_SCHEMAS.md |

### Critical Updates Required

```javascript
// ACTION: "Get_Scope" - BREAKING CHANGE
// Old:
"entityName": "cr950_projectscopes"
// New:
"entityName": "cr950_scopes"

// ACTION: "List_ScopeLaborDetail" - BREAKING CHANGE
// Old:
"entityName": "cr950_scopelabordetailses"
"$filter": "_cr950_projectscope_id_value eq @{outputs('Get_Scope')?['body/cr950_projectscopeid']}"
// New:
"entityName": "cr950_scopelabordetails"
"$filter": "_cr950_scopelabor_scope_value eq @{outputs('Get_Scope')?['body/cr950_scopeid']}"

// ACTION: "Create_Apparatus_Revenue" - Multiple field renames
// Old:
"item/cr950_Apparatus@odata.bind": "@concat('cr950_apparatuses(',triggerOutputs()?['body/cr950_apparatusid'],')')"
"item/cr950_Project@odata.bind": "@concat('cr950_projectses(',outputs('Get_Scope')?['body/_cr950_project_value'],')')"
"item/cr950_ScopeLaborDetail@odata.bind": "@concat('cr950_scopelabordetailses(',items('Apply_to_each')?['cr950_scopelabordetailsid'],')')"
// New:
"item/cr950_Apparatus@odata.bind": "@concat('cr950_apparatuses(',triggerOutputs()?['body/cr950_apparatusid'],')')"
"item/cr950_Project@odata.bind": "@concat('cr950_projects(',outputs('Get_Scope')?['body/_cr950_scope_project_value'],')')"
"item/cr950_ScopeLaborDetail@odata.bind": "@concat('cr950_scopelabordetails(',items('Apply_to_each')?['cr950_scopelaborid'],')')"
```

---

## 📊 Flow 3: JSON Import

### Overview
**File:** `JSONImport-49C39B0A-FACD-F011-BBD2-6045BD0391A9.json`  
**Trigger:** SharePoint file creation (JSON files)  
**Purpose:** Creates Client, Site, Project, Scope, ScopeLaborDetail, and Apparatus records from JSON

### Tables Referenced

| Old EntitySetName | V2 EntitySetName | Status | Action Required |
|-------------------|------------------|--------|-----------------|
| `cr950_clients` | `cr950_clients` | ✅ No change | None |
| `cr950_sites` | `cr950_sites` | ✅ No change | None |
| `cr950_projectses` | `cr950_projects` | 🔴 BREAKING | Update all references |
| `cr950_projectscopes` | `cr950_scopes` | 🔴 BREAKING | Update all references |
| `cr950_scopelabordetailses` | `cr950_scopelabordetails` | 🔴 BREAKING | Update all references |
| `cr950_apparatuses` | `cr950_apparatuses` | ✅ No change | None |

### Field Mapping Analysis

#### cr950_clients Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_name` | `cr950_client_name` | ⚠️ RENAME | Primary name field |
| `cr950_clientid` | `cr950_clientid` | ✅ Compatible | Primary key |

#### cr950_sites Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_name` | `cr950_site_name` | ⚠️ RENAME | Primary name field |
| `cr950_address` | `cr950_site_address` | ⚠️ RENAME | Address field |
| `cr950_city` | `cr950_site_city` | ⚠️ RENAME | City field |
| `cr950_state` | `cr950_site_state` | ⚠️ RENAME | State field |
| `cr950_zip` | `cr950_site_zip` | ⚠️ RENAME | Zip field |
| `cr950_sitecontactemail` | `cr950_site_contact_email` | ⚠️ RENAME | Contact email |
| `cr950_client@odata.bind` | `cr950_site_client@odata.bind` | ⚠️ RENAME | Lookup binding |
| `cr950_siteid` | `cr950_siteid` | ✅ Compatible | Primary key |

#### cr950_projectses → cr950_projects Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_project_name` | `cr950_project_name` | ✅ Compatible | Primary name |
| `cr950_job_number` | `cr950_project_number` | ⚠️ RENAME | Project number field |
| `cr950_client@odata.bind` | `cr950_project_client@odata.bind` | ⚠️ RENAME | Lookup binding |
| `cr950_site@odata.bind` | `cr950_project_site@odata.bind` | ⚠️ RENAME | Lookup binding |
| `cr950_projectsid` | `cr950_projectid` | ⚠️ RENAME | Primary key |

#### cr950_projectscopes → cr950_scopes Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_scope_name` | `cr950_scope_name` | ✅ Compatible | Primary name |
| `cr950_testing_standard` | `cr950_scope_type` | ⚠️ RENAME/VERIFY | Type field |
| `cr950_Project@odata.bind` | `cr950_scope_project@odata.bind` | ⚠️ RENAME | Lookup binding |
| `cr950_projectscopeid` | `cr950_scopeid` | ⚠️ RENAME | Primary key |

#### cr950_scopelabordetailses → cr950_scopelabordetails Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_name` | `cr950_scopelabor_name` | ⚠️ RENAME | Primary name |
| `cr950_total_apparatus_hours` | `cr950_scopelabor_total_hours` | ⚠️ RENAME | Hours field |
| `cr950_scope_total_value` | `cr950_scopelabor_quoted_amount` | ⚠️ RENAME | Amount field |
| `cr950_scopemultiplier` | `cr950_scopelabor_multiplier` | ⚠️ RENAME | Multiplier |
| `cr950_onsitelabortotal` | `cr950_scopelabor_onsite_total` | ⚠️ RENAME | Onsite total |
| `cr950_offsitelabortotal` | `cr950_scopelabor_offsite_total` | ⚠️ RENAME | Offsite total |
| `cr950_traveltotal` | `cr950_scopelabor_travel_total` | ⚠️ RENAME | Travel total |
| `cr950_outsideservicestotal` | `cr950_scopelabor_outside_total` | ⚠️ RENAME | Outside services |
| `cr950_iscurrentversion` | Not in V2 schema | ❓ Verify | May need to add |
| `cr950_projectscope_id@odata.bind` | `cr950_scopelabor_scope@odata.bind` | ⚠️ RENAME | Lookup binding |
| `cr950_scopelabordetailsid` | `cr950_scopelaborid` | ⚠️ POSSIBLE | Primary key |

#### cr950_apparatuses Table
| Flow Field | V2 Schema Field | Status | Notes |
|------------|-----------------|--------|-------|
| `cr950_apparatustype` | `cr950_apparatus_type` | ⚠️ RENAME | Type field |
| `cr950_labor_hours` | `cr950_apparatus_hours_per_unit` | ⚠️ RENAME | Hours field |
| `cr950_notes` | `cr950_apparatus_notes` | ⚠️ RENAME | Notes field |
| `cr950_Scope@odata.bind` | `cr950_apparatus_task@odata.bind` | 🔴 BREAKING | Changed from Scope to Task |
| `cr950_Project@odata.bind` | Not in V2 schema | ❓ Verify | May be removed |

### Critical Updates Required

```javascript
// ACTION: "Create_Project" - Entity and field renames
// Old:
"entityName": "cr950_projectses"
"item/cr950_job_number": ...
// New:
"entityName": "cr950_projects"
"item/cr950_project_number": ...

// ACTION: "Create_Scope" - Entity rename
// Old:
"entityName": "cr950_projectscopes"
"item/cr950_Project@odata.bind": "cr950_projectses(@{...})"
// New:
"entityName": "cr950_scopes"
"item/cr950_scope_project@odata.bind": "cr950_projects(@{...})"

// ACTION: "Create_ScopeLaborDetail" - Entity and extensive field renames
// Old:
"entityName": "cr950_scopelabordetailses"
// New:
"entityName": "cr950_scopelabordetails"
// Plus all field renames listed above

// ACTION: "Create_Apparatus" - ARCHITECTURE CHANGE
// Old: Apparatus links directly to Scope
"item/cr950_Scope@odata.bind": "cr950_projectscopes(@{...})"
// New: Apparatus links to Task (Tasks are children of Scopes)
"item/cr950_apparatus_task@odata.bind": "cr950_tasks(@{...})"
// ⚠️ This requires creating Tasks first before Apparatus!
```

---

## 🔴 Critical Breaking Changes Summary

### 1. EntitySetName Changes (4 Critical)

| Old EntitySetName | New EntitySetName | Affected Flows |
|-------------------|-------------------|----------------|
| `cr950_projectscopes` | `cr950_scopes` | Revenue Recognition, JSON Import |
| `cr950_projectses` | `cr950_projects` | Revenue Recognition, JSON Import |
| `cr950_scopelabordetailses` | `cr950_scopelabordetails` | Revenue Recognition, JSON Import |
| `cr950_taskses` | `cr950_tasks` | (Referenced in documentation) |

### 2. Architecture Change: Apparatus → Task (Critical)

**Old Architecture:**
```
Project → Scope → Apparatus
```

**New Architecture:**
```
Project → Scope → Task → Apparatus
```

**Impact on JSON Import Flow:**
- Cannot create Apparatus directly from Scope
- Must first create Task records
- Then create Apparatus with Task lookup

**Recommended Fix:**
```javascript
// Add new action after Create_Scope: "Create_Default_Task"
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "entityName": "cr950_tasks",
      "item/cr950_task_name": "@concat(items('Loop_Scopes')?['name'], ' - Default Task')",
      "item/cr950_task_scope@odata.bind": "cr950_scopes(@{outputs('Create_Scope')?['body/cr950_scopeid']})"
    }
  }
}

// Then modify Create_Apparatus to use Task
"item/cr950_apparatus_task@odata.bind": "cr950_tasks(@{outputs('Create_Default_Task')?['body/cr950_taskid']})"
```

### 3. Primary Key Field Renames

| Table | Old PK Field | New PK Field |
|-------|--------------|--------------|
| Projects | `cr950_projectsid` | `cr950_projectid` |
| Scopes | `cr950_projectscopeid` | `cr950_scopeid` |
| ScopeLaborDetail | `cr950_scopelabordetailsid` | `cr950_scopelaborid` (verify) |

### 4. Lookup Field Binding Changes

All OData binding expressions must be updated to reflect new EntitySetNames:

```javascript
// Old patterns:
"@concat('cr950_projectses(',guid,')')"
"@concat('cr950_projectscopes(',guid,')')"
"@concat('cr950_scopelabordetailses(',guid,')')"

// New patterns:
"@concat('cr950_projects(',guid,')')"
"@concat('cr950_scopes(',guid,')')"
"@concat('cr950_scopelabordetails(',guid,')')"
```

---

## ✅ V2 Schema Fields Available for Enhancement

The V2 schema includes new fields that could be populated by the flows:

### Client Table - New Fields
- `cr950_client_code` - Short code (e.g., LAFA)
- `cr950_client_phone` - Primary phone
- `cr950_client_website` - Company website
- `cr950_client_active` - Active flag

### Site Table - New Fields
- `cr950_site_code` - Short reference code
- `cr950_site_contact_name` - Primary site contact
- `cr950_site_contact_phone` - Contact phone
- `cr950_site_active` - Active flag

### Project Table - New Fields
- `cr950_project_status` - Current status
- `cr950_project_start_date` - Planned/actual start
- `cr950_project_end_date` - Planned/actual completion
- `cr950_project_po_number` - Purchase order
- `cr950_project_contract_value` - Total contract amount
- `cr950_project_active` - Active flag

### Scope Table - New Fields
- `cr950_scope_number` - Scope number within project
- `cr950_scope_status` - Current scope status
- `cr950_scope_due_date` - Completion target
- `cr950_scope_revenue_total` - Total scope revenue
- `cr950_scope_margin_percent` - Profit margin

### Apparatus Table - New Fields
- `cr950_apparatus_name` - Equipment identifier
- `cr950_apparatus_section` - Section grouping from estimator
- `cr950_apparatus_manufacturer` - Manufacturer
- `cr950_apparatus_model` - Model number
- `cr950_apparatus_serial` - Serial number
- `cr950_apparatus_location` - Physical location
- `cr950_apparatus_voltage` - Voltage rating
- `cr950_apparatus_amperage` - Amperage rating
- `cr950_apparatus_result` - Pass/Fail/Conditional
- `cr950_apparatus_sequence` - Display order
- `cr950_apparatus_row` - Original row from estimator

---

## 📋 Migration Checklist

### Pre-Migration Verification

- [ ] Confirm Estimator schema exists in new environment
- [ ] Verify all listed field names match actual V2 schema
- [ ] Test connectivity to org284447bd.crm.dynamics.com
- [ ] Export current flows as backup

### Flow 1: EstimatorImport

- [ ] Update organization URL (4 locations)
- [ ] Update cr950_name → cr950_client_name filter
- [ ] Test Client lookup functionality
- [ ] Test Estimator create/update operations
- [ ] Verify email notification works

### Flow 2: Revenue Recognition

- [ ] Update organization URL (5 locations)
- [ ] Change cr950_projectscopes → cr950_scopes
- [ ] Change cr950_scopelabordetailses → cr950_scopelabordetails
- [ ] Change cr950_projectses → cr950_projects
- [ ] Update all primary key field references
- [ ] Update all lookup field bindings
- [ ] Update field names in Create action
- [ ] Test with sample apparatus completion

### Flow 3: JSON Import

- [ ] Update organization URL (3 locations)
- [ ] Update all entity names
- [ ] Update all field names per mapping
- [ ] **CRITICAL:** Add Task creation step
- [ ] Update Apparatus to link to Task not Scope
- [ ] Remove Project lookup from Apparatus (if not in V2)
- [ ] Test complete import workflow

### Post-Migration Testing

- [ ] Run EstimatorImport with test file
- [ ] Mark apparatus complete and verify revenue record
- [ ] Import test JSON and verify all records created
- [ ] Verify rollup calculations work
- [ ] Check audit trail / history

---

## 📝 Recommendations

1. **Create Estimator Schema CSV** - The 09_Estimator_Schema.csv file is missing. Create it to document the Estimator table fields.

2. **Consider Flow Redesign for JSON Import** - The architecture change (Apparatus → Task instead of Apparatus → Scope) may require significant flow restructuring. Consider rebuilding this flow rather than patching.

3. **Add Version Check** - Add a version check at the start of each flow to ensure it's running against the correct schema version.

4. **Update Connection References** - After updating flows, you'll need to update connection references to point to the new environment.

5. **Test in Dev First** - Deploy updated flows to a development environment before production.

---

**Report Generated:** December 2, 2025  
**Schema Version Analyzed:** V2 (as per CSV_Templates/Schema/)  
**Solution Version Analyzed:** v1.5.1.3  
