# ESTIMATOR TO DATAVERSE IMPORT PIPELINE

## Standard Operating Procedure (SOP)

**Version:** 1.0  
**Created:** November 27, 2025  
**Status:** Production Ready (with known gap - see Section 6)  
**Tested On:** Central Mesa Reuse Plant (Job #677562)

---

## Overview

This document defines the complete process for importing Excel Estimator data into Dataverse. The pipeline converts quoted project data into operational tracking records.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Excel          │     │  JSON           │     │  Dataverse      │
│  Estimator      │────▶│  Export         │────▶│  Tables         │
│  (.xlsm)        │     │  (.json)        │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     VBA Module              Node.js              API (REST)
```

**What gets created:**
- 1 Client record
- 1 Site record  
- 1 Project record
- N Scope records (typically 1-6)
- N ScopeLaborDetail records (1 per scope) ⚠️ *See Section 6*
- N Apparatus records (typically 50-500)

---

## Prerequisites

### 1. Excel Workbook Setup

The Estimator workbook must have:

- [ ] **Dataverse_Import sheet** with metadata fields:
  - Job # (required)
  - Project Name (required)
  - Client Name (required)
  - Site Name, Address, City, State, Zip
  - Contact Email

- [ ] **Active scope sheets** (Scope1, Scope2, etc.) with:
  - J3: Total Hours
  - M4: Multiplier
  - P3: Grand Total (quoted amount)
  - C4: Job Type (ATS or MTS)
  - P14: Onsite Labor Total
  - P19: Offsite Labor Total
  - P26: Travel Total
  - P33: Outside Services Total
  - Rows 6-488: Apparatus items

### 2. VBA Module Installed

**File:** `DataverseExport.bas`  
**Location:** `C:\RESA_Power_Build\Reference_Files\Excel\Estimator VBA Modules\`

To install:
1. Open Estimator workbook
2. Alt+F11 (VBA Editor)
3. File → Import File → Select `DataverseExport.bas`
4. Close VBA Editor

### 3. Node.js Environment

**Location:** `C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\`

Required files:
- `import-estimator.js` (v2 with ScopeLaborDetail)
- `.env` file with credentials
- `package.json` with dependencies

**.env contents:**
```
DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
AZURE_CLIENT_SECRET=[your-secret]
```

---

## Step 1: Export from Excel

### 1.1 Open Estimator Workbook

Open the completed Estimator (.xlsm) file with all scopes finalized.

### 1.2 Run VBA Export

1. Press `Alt+F8` (Macros dialog)
2. Select `ExportToDataverse`
3. Click **Run**

### 1.3 Verify Output

The export creates a JSON file:
- **Location:** Same folder as workbook (or Desktop if cloud-saved)
- **Filename:** `{JobNumber}_DATAVERSE_IMPORT_{timestamp}.json`
- **Example:** `677562_DATAVERSE_IMPORT_20251127_114935.json`

### 1.4 Validate JSON Structure

Open the JSON file and verify it contains metadata, client, site, project, scopes with financials, and apparatus arrays.

---

## Step 2: Import to Dataverse

### 2.1 Copy JSON to Import Location

```powershell
Copy-Item "C:\Users\[you]\Desktop\677562_DATAVERSE_IMPORT_*.json" `
          "C:\RESA_Power_Build\Reference_Files\Excel\"
```

### 2.2 Run Import Script

```powershell
cd C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp
node import-estimator.js "path\to\json\file.json"
```

---

## Step 3: Validate Import

### 3.1 Verify Relationships

- [ ] All Scopes reference correct Project
- [ ] All Apparatus reference correct Scope and Project
- [ ] All ScopeLaborDetails reference correct Scope
- [ ] Rollup fields calculate correctly after trigger

---

## Step 4: Post-Import Tasks

### 4.1 Tasks Layer (PM Activity)

The import creates Scopes and Apparatus but **not Tasks**. 

PM should create Tasks to organize work:
1. Open Project in model-driven app
2. Navigate to Scopes
3. Create Tasks within each Scope
4. Reassign Apparatus to appropriate Tasks

### 4.2 Enable Revenue Flow

Before marking apparatus complete:
1. Verify ScopeLaborDetail has Effective Labor Rate
2. Turn ON "Revenue Recognition on Apparatus Completion" flow
3. Test with one apparatus

---

## Section 5: Field Mapping Reference

### Client Table (cr950_client)
| JSON Field | Dataverse Field | Type |
|------------|-----------------|------|
| client.name | cr950_name | String |

### Site Table (cr950_site)
| JSON Field | Dataverse Field | Type |
|------------|-----------------|------|
| site.name | cr950_name | String |
| site.address | cr950_address | String |
| (lookup) | cr950_client | Lookup → Client |

### Project Table (cr950_projects)
| JSON Field | Dataverse Field | Type |
|------------|-----------------|------|
| project.name | cr950_project_name | String |
| project.projectNumber | cr950_job_number | String |
| (lookup) | cr950_client | Lookup → Client |
| (lookup) | cr950_site | Lookup → Site |

### Scope Table (cr950_projectscope)
| JSON Field | Dataverse Field | Type |
|------------|-----------------|------|
| scope.name | cr950_scope_name | String |
| scope.scopeType | cr950_testing_standard | Choice |
| (lookup) | cr950_Project | Lookup → Project |

### ScopeLaborDetail Table (cr950_scopelabordetails)
| JSON Field | Dataverse Field | Type |
|------------|-----------------|------|
| scope.totalHours | cr950_total_apparatus_hours | Decimal |
| scope.quotedAmount | cr950_scope_total_value | Money |
| scope.financials.* | cr950_onsite/offsite/travel/outside | Money |
| (lookup) | cr950_projectscope_id | Lookup → Scope |

### Apparatus Table (cr950_apparatus)
| JSON Field | Dataverse Field | Type |
|------------|-----------------|------|
| apparatus.equipmentType | cr950_apparatus_designation | String |
| apparatus.hoursPerUnit | cr950_labor_hours | Decimal |
| (lookup) | cr950_Scope | Lookup → Scope |
| (lookup) | cr950_Project | Lookup → Project |

---

## Section 6: Known Gaps & Issues

### ⚠️ Gap 1: Import Script v1 Missing ScopeLaborDetail

**Issue:** The original `import-estimator.js` does not create ScopeLaborDetail records.

**Impact:** Revenue recognition flow fails with "No labor rates defined."

**Solution:** Use `import-estimator-v2.js` which includes ScopeLaborDetail creation.

### Gap 2: Effective Labor Rate Calculation

Dataverse may recalculate based on its formula. Verify formula matches business logic.

### Gap 3: Duplicate Prevention

Running import twice creates duplicate records. Add lookup-before-create logic.

---

## Section 7: Troubleshooting

### Error: "401 Unauthorized"
- Verify `.env` credentials
- Check Azure App Registration is active

### Error: "400 Bad Request - Field not found"
- Verify field logical names in Dataverse

### Apparatus Count Mismatch
Quantity field in Excel creates multiple records (correct behavior).

---

## Section 8: File Locations

| Component | Location |
|-----------|----------|
| VBA Module | `Reference_Files\Excel\Estimator VBA Modules\DataverseExport.bas` |
| Import Script | `MCP_Servers\resa-dataverse-mcp\import-estimator.js` |
| This SOP | `Documentation\06_Implementation_Guides\IMPORT_PIPELINE_SOP.md` |

---

**Document Owner:** Jason Swenson  
**Last Validated:** November 27, 2025
