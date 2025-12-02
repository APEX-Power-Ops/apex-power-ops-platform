# Estimator Import Flow Specification - V2 Schema

**Version:** 2.0.0  
**Date:** December 2, 2025  
**Status:** READY FOR IMPLEMENTATION  
**Target Environment:** org284447bd.crm.dynamics.com  
**Author:** Jason Swenson / Claude AI Assistant

---

## 📋 Overview

**Purpose:** Automatically create/update Estimator tracking records when Excel estimator files (.xlsm) are saved to SharePoint folder structure.

**Trigger:** SharePoint file creation in monitored library  
**Tables Used:** cr950_clients, cr950_estimators  
**Complexity:** 🟢 Low - Minimal schema changes required

---

## 🔄 V1 → V2 Migration Summary

| Change Type | V1 Value | V2 Value | Status |
|-------------|----------|----------|--------|
| Environment URL | org99cd6c6e.crm.dynamics.com | org284447bd.crm.dynamics.com | 🔴 UPDATE |
| Client name field | cr950_name | cr950_client_name | ⚠️ VERIFY |
| Estimator table | cr950_estimators | cr950_estimators | ✅ No change |
| Client table | cr950_clients | cr950_clients | ✅ No change |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    ESTIMATOR IMPORT FLOW - V2                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SHAREPOINT TRIGGER                                                      │
│  ─────────────────                                                       │
│  Site: jswensonllc.sharepoint.com/sites/PhoenixProjects                 │
│  Library: Shared Documents                                               │
│  Folder Structure: /Shared Documents/{Client Name}/{Project Name}/       │
│  File Pattern: *_Rev#.xlsm                                              │
│                                                                          │
│  FLOW SEQUENCE:                                                          │
│  ──────────────                                                          │
│                                                                          │
│  1. File Created (.xlsm only)                                           │
│        │                                                                 │
│        ▼                                                                 │
│  2. Extract Client Name (from folder path position [2])                 │
│     Extract Project Name (from folder path position [3])                │
│        │                                                                 │
│        ▼                                                                 │
│  3. Validate Client Exists in Dataverse (cr950_clients)                │
│        │                                                                 │
│        ├─── NO ──→ Send Error Email → Terminate                        │
│        │                                                                 │
│        ▼ YES                                                             │
│  4. Extract Date/Revision from Filename                                 │
│     Pattern: {name}_Rev{YYYYMMDD}.xlsm                                  │
│        │                                                                 │
│        ▼                                                                 │
│  5. Check for Existing Estimator Record                                 │
│     Filter: Client + Project Name match                                  │
│        │                                                                 │
│        ├─── EXISTS ──→ Update Existing Record                           │
│        │                                                                 │
│        ▼ NOT EXISTS                                                      │
│  6. Create New Estimator Record                                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 V2 Table Schemas

### cr950_clients (Clients Table)

| V2 Field | Display Name | Type | Notes |
|----------|--------------|------|-------|
| cr950_clientid | Client ID | GUID | Primary key |
| cr950_client_name | Client Name | String(200) | **PRIMARY FIELD** - used in lookup |
| cr950_client_code | Client Code | String(20) | Short code (e.g., LAFA) |
| cr950_client_active | Active | Boolean | Is client active |

### cr950_estimators (Estimators Table)

| V2 Field | Display Name | Type | Notes |
|----------|--------------|------|-------|
| cr950_estimatorid | Estimator ID | GUID | Primary key |
| cr950_name | Name | String(200) | Display name - typically project name |
| cr950_client | Client | Lookup | FK to cr950_clients |
| cr950_projectname | Project Name | String(200) | Project name from folder path |
| cr950_estimatedate | Estimate Date | Date | Date from filename |
| cr950_currentrevision | Current Revision | Integer | Revision from filename |
| cr950_estimator_file_url | Estimator File URL | URL | Full SharePoint URL |
| cr950_filename | Filename | String(500) | Original filename |
| cr950_status | Status | Choice | Draft/Quoted/Awarded/Converted/Rejected/On Hold |
| cr950_convertedtoproject | Converted to Project | Boolean | Default: No |
| cr950_project | Project | Lookup | FK to cr950_projects (after conversion) |
| cr950_lastmodified | Last Modified | DateTime | Last update timestamp |
| cr950_notes | Notes | Memo(4000) | Free text notes |

### Status Choice Values

| Value | Label |
|-------|-------|
| 864340000 | Draft |
| 864340001 | Quoted |
| 864340002 | Awarded |
| 864340003 | Converted |
| 864340004 | Rejected |
| 864340005 | On Hold |

---

## 🔧 Flow Actions - V2 Configuration

### Action 1: Trigger Configuration

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "dataset": "https://jswensonllc.sharepoint.com/sites/PhoenixProjects",
      "table": "bf92590a-261e-4ed4-8074-42dcf26db632",
      "view": "a00198a5-5ec1-4d1b-a428-dc43788f5fe1"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
      "operationId": "GetOnNewFileItems"
    }
  },
  "recurrence": {
    "interval": 5,
    "frequency": "Minute"
  }
}
```

### Action 2: Validate Client Exists - V2

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_clients",
      "$filter": "cr950_client_name eq '@{outputs('Client_Name')}'"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    }
  }
}
```

**⚠️ CHANGE FROM V1:** Filter field changed from `cr950_name` to `cr950_client_name`

### Action 3: Check for Existing Estimator - V2

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_estimators",
      "$filter": "_cr950_client_value eq '@{first(outputs('Validate_Client_Exists')?['body/value'])?['cr950_clientid']}' and cr950_projectname eq '@{outputs('Project_Name')}'"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    }
  }
}
```

### Action 4: Update Existing Estimator - V2

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_estimators",
      "recordId": "@first(outputs('Check_for_Existing_Estimator')?['body/value'])?['cr950_estimatorid']",
      "item/cr950_currentrevision": "@int(last(split(first(split(triggerOutputs()?['body/{FilenameWithExtension}'], '.xlsm')), '_Rev')))",
      "item/cr950_estimatedate": "@outputs('EstimateDate')",
      "item/cr950_estimator_file_url": "@concat('https://jswensonllc.sharepoint.com/sites/PhoenixProjects/', replace(triggerOutputs()?['body/{Path}'], ' ', '%20'))",
      "item/cr950_filename": "@outputs('Filename')",
      "item/cr950_lastmodified": "@utcNow()"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "operationId": "UpdateOnlyRecordWithOrganization"
    }
  }
}
```

### Action 5: Create New Estimator - V2

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_estimators",
      "item/cr950_name": "@{outputs('Project_Name')} (display name)",
      "item/cr950_client@odata.bind": "/cr950_clients(@{first(outputs('Validate_Client_Exists')?['body/value'])?['cr950_clientid']})",
      "item/cr950_currentrevision": "@int(last(split(first(split(triggerOutputs()?['body/{FilenameWithExtension}'], '.xlsm')), '_Rev')))",
      "item/cr950_estimatedate": "@outputs('EstimateDate')",
      "item/cr950_estimator_file_url": "@concat('https://jswensonllc.sharepoint.com/sites/PhoenixProjects/', replace(triggerOutputs()?['body/{Path}'], ' ', '%20'))",
      "item/cr950_filename": "@outputs('Filename')",
      "item/cr950_projectname": "@outputs('Project_Name')",
      "item/cr950_status": 864340000,
      "item/statuscode": 1
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "operationId": "CreateRecordWithOrganization"
    }
  }
}
```

---

## 🔀 V1 vs V2 Comparison

| Action | V1 Configuration | V2 Configuration |
|--------|------------------|------------------|
| Organization URL | org99cd6c6e.crm.dynamics.com | org284447bd.crm.dynamics.com |
| Client filter field | `cr950_name eq ...` | `cr950_client_name eq ...` |
| Client lookup binding | Same | Same |
| Estimator fields | Same | Same (table being created by VS Claude) |

---

## ✅ Implementation Checklist

### Pre-Implementation
- [ ] Confirm cr950_clients table exists in new environment
- [ ] Confirm cr950_client_name is the primary name field
- [ ] Confirm cr950_estimators table created by VS Claude
- [ ] Verify Estimator table schema matches spec above

### Flow Updates
- [ ] Update organization URL (4 locations)
- [ ] Update client filter to use cr950_client_name
- [ ] Test with existing SharePoint file structure
- [ ] Verify email notifications work

### Testing
- [ ] Save new .xlsm file to valid client folder
- [ ] Verify Estimator record created
- [ ] Save updated revision, verify record updated
- [ ] Save to invalid client folder, verify error email sent

---

## 📁 Related Files

| Item | Location |
|------|----------|
| V1 Flow JSON | `Solution_Exports/v1.5.1.3/Workflows/EstimatorImport-*.json` |
| Schema Audit | `Documentation/FLOW_SCHEMA_AUDIT_DEC2025.md` |
| Estimator Template | `CSV_Templates/New_Tables/07_Estimators_Template.csv` |
| Client Schema | `CSV_Templates/Schema/01_Client_Schema.csv` |

---

**Document Owner:** Jason Swenson  
**Created:** December 2, 2025  
**Status:** Ready for implementation after VS Claude completes table creation
