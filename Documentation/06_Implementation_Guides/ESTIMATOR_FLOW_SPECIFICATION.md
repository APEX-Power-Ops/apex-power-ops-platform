# RESA Power Estimator Import Flow Specification

**Version:** 2.1  
**Date:** November 28, 2025  
**Status:** In Development  
**Author:** Jason Swenson / Claude AI Assistant

**Related Documents:**
- [DATA_MODEL_REFERENCE.md](../01_Architecture/DATA_MODEL_REFERENCE.md) - Authoritative data model (Business Unit / Client / Site)

---

## Overview

This document specifies the Power Automate flows that automate the import of Estimator Excel workbooks into Dataverse. The system uses **SharePoint folder structure as data** - client and project names are derived from folder paths, with files synced locally via OneDrive for seamless user experience.

### Key Principles
1. **Folders = Data**: Client and Project names come from folder structure
2. **Local Sync**: Users save to synced local folders, SharePoint handles the rest
3. **Minimal Filename Requirements**: Only date and revision must follow convention
4. **Validated Clients**: Client folders must match Dataverse Clients table
5. **Web App for Views**: Dataverse + Web App provide filtered, organized access

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ESTIMATOR LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LOCAL (User's Machine)              CLOUD                              │
│  ──────────────────────              ─────                              │
│  C:\Users\{user}\                    SharePoint Phoenix Projects        │
│    └─ Phoenix Projects\                └─ /Documents/                   │
│        └─ Estimators\      ←SYNC→          └─ /Estimators/              │
│            └─ {Client}/                        └─ {Client}/             │
│                └─ {Project}/                       └─ {Project}/        │
│                    └─ file.xlsm ──────────────────────→ [FLOW TRIGGER]  │
│                                                              ↓          │
│                                                         Dataverse       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STAGE 1: Estimator Created/Updated                                     │
│  ───────────────────────────────────                                    │
│  User saves file to local synced folder                                 │
│  OneDrive syncs to SharePoint                                           │
│                     ↓                                                   │
│          [Flow 1: Estimator Import] (recursive trigger)                 │
│                     ↓                                                   │
│  • Validates Client folder against Dataverse Clients table              │
│  • Creates/Updates Estimator record in Dataverse                        │
│  • Stores: Client (lookup), Project Name, Date, Revision, File URL      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STAGE 2: Quote Created (CRM Integration - TBD)                         │
│  ──────────────────────────────────────────────                         │
│  Quote PDF saved to /Quotes/ folder                                     │
│  Flow creates Quote record, links to Estimator                          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STAGE 3: PO Received - Project Creation                                │
│  ───────────────────────────────────────                                │
│  Web App: User clicks "Convert to Project"                              │
│                     ↓                                                   │
│  Opens Estimator in Excel Online                                        │
│  User fills Dataverse_Import sheet (PO#, dates, PM)                     │
│  User clicks "Create Project" in Web App                                │
│                     ↓                                                   │
│                [Flow 2: Project Import] (HTTP trigger)                  │
│                     ↓                                                   │
│       Creates Project + Scopes + Apparatus in Dataverse                 │
│       Links to Estimator record                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## SharePoint Folder Structure

**Site:** Phoenix Projects  
**URL:** `https://jswensonllc.sharepoint.com/sites/PhoenixProjects`  
**Document Library:** Documents  
**Local Sync:** Users click "Sync" button to add to local file explorer

```
/Documents/
    /Estimators/                          ← Root for all estimators
        /{Client Name}/                   ← Must match Dataverse Client table
            /{Project Name}/              ← User-created, becomes Project Name
                {filename}_YYYYMMDD_Rev#.xlsm
    
    /Quotes/                              ← Quote PDFs (future CRM integration)
    
    /Projects/                            ← Post-award project files
        /{JobNumber} - {Project Name}/
            /Estimator/
            /Quote/
            /Deliverables/
            /Field Reports/
            /Photos/
```

### Client Folder Rules
- **Must exactly match** a client name in Dataverse `cr950_clients` table
- Flow validates on file save - rejects if client not found
- New clients must be added to Dataverse first (via Web App or Power Apps)

### Project Folder Rules
- User creates folder with descriptive project name
- This becomes the `Project Name` in Dataverse Estimator record
- No validation required - free text

---

## File Naming Convention

### Required Format (End of Filename)
```
{anything}_YYYYMMDD_Rev#.xlsm
```

### Examples (All Valid)
```
Mesa Reuse Estimate_20251128_Rev1.xlsm
Garney Mesa_20251128_Rev2.xlsm
my working file_20251115_Rev1.xlsm
LASNAP16 Final Quote_20251201_Rev3.xlsm
random name here_20251128_Rev1.xlsm
```

### What's Extracted from Filename
| Component | Pattern | Example |
|-----------|---------|---------|
| Date | `_YYYYMMDD_` | `_20251128_` → 2025-11-28 |
| Revision | `_Rev#` | `_Rev3` → Revision 3 |

### What's Extracted from Folder Path
| Component | Source | Example |
|-----------|--------|---------|
| Client | 2nd level folder | `/Estimators/Garney Construction/...` → Garney Construction |
| Project Name | 3rd level folder | `/Estimators/.../Mesa Reuse Project/` → Mesa Reuse Project |

### Regex Pattern for Filename Parsing
```regex
_(\d{8})_Rev(\d+)\.xlsm$
```
- Group 1: Date (YYYYMMDD) - e.g., "20251128"
- Group 2: Revision number - e.g., "3"

### Path Parsing Logic
```
Full Path: /Estimators/Garney Construction/Mesa Reuse Project/file_20251128_Rev2.xlsm

Split by "/":
  [0] = ""
  [1] = "Estimators"           ← Root (ignored)
  [2] = "Garney Construction"  ← Client Name (validated)
  [3] = "Mesa Reuse Project"   ← Project Name
  [4] = "file_20251128_Rev2.xlsm" ← Filename (parsed for date/rev)
```

---

## Flow 1: Estimator Import (Folder-Based)

### Purpose
Create or update Estimator records when files are saved to the SharePoint folder structure. Uses folder path to determine Client and Project Name, validates against Dataverse.

### Trigger
- **Type:** SharePoint - "When a file is created or modified (properties only)"
- **Site:** Phoenix Projects
- **Library:** Documents
- **Folder:** `/Estimators`
- **Include Nested Items:** Yes (recursive - watches all subfolders)

### Flow Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│  Trigger: File created/modified in /Estimators/**              │
│                          ↓                                      │
│  Condition: Is .xlsm file?                                     │
│      No → Exit                                                 │
│      Yes ↓                                                     │
│  Parse folder path → Extract Client Name, Project Name         │
│                          ↓                                      │
│  Query Dataverse: Does Client exist?                           │
│      No → Send error notification, Exit                        │
│      Yes ↓                                                     │
│  Parse filename → Extract Date, Revision                       │
│      Invalid format → Send warning, Exit                       │
│      Valid ↓                                                   │
│  Query: Existing Estimator for this Client+Project?            │
│      No → Create new Estimator record                          │
│      Yes → Update existing (new revision)                      │
│                          ↓                                      │
│  Success notification (optional)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Actions

#### Step 1: Get File Properties & Validate File Type
```
Action: Condition
Expression: endsWith(triggerOutputs()?['body/{FilenameWithExtension}'], '.xlsm')
If No: Terminate (ignore non-estimator files)
```

#### Step 2: Parse Folder Path
```
Action: Compose - ParsePath
Expression: split(triggerOutputs()?['body/{Path}'], '/')

Result example: ["", "Estimators", "Garney Construction", "Mesa Reuse Project", "file.xlsm"]
```

```
Action: Compose - ClientName
Expression: outputs('ParsePath')[2]
Result: "Garney Construction"
```

```
Action: Compose - ProjectName  
Expression: outputs('ParsePath')[3]
Result: "Mesa Reuse Project"
```

#### Step 3: Validate Client Exists in Dataverse
```
Action: Dataverse - List rows
Table: Clients (cr950_clients)
Filter: cr950_name eq '@{outputs('ClientName')}'
```

```
Action: Condition - Client Exists?
Expression: length(outputs('ListClients')?['body/value']) > 0
If No:
  → Send email notification: "Invalid client folder: {ClientName}"
  → Terminate flow
```

#### Step 4: Parse Filename for Date and Revision
```
Action: Compose - Filename
Expression: triggerOutputs()?['body/{FilenameWithExtension}']
```

```
Action: Compose - ExtractDateRevision
Expression: 
  Using regex pattern: _(\d{8})_Rev(\d+)\.xlsm$
  
  Alternative with string functions:
  - Find last "_Rev" position
  - Extract 8 digits before it for date
  - Extract digits after "Rev" for revision
```

```
Action: Compose - EstimateDate
Expression: concat(
  substring(outputs('DateString'), 0, 4), '-',
  substring(outputs('DateString'), 4, 2), '-', 
  substring(outputs('DateString'), 6, 2)
)
Result: "2025-11-28"
```

```
Action: Compose - RevisionNumber
Expression: int(outputs('RevString'))
Result: 2
```

#### Step 5: Build SharePoint File URL
```
Action: Compose - EstimatorFileUrl
Expression: concat(
  'https://jswensonllc.sharepoint.com/sites/PhoenixProjects/Shared%20Documents',
  replace(triggerOutputs()?['body/{Path}'], ' ', '%20')
)
```

#### Step 6: Check for Existing Estimator Record
```
Action: Dataverse - List rows
Table: Estimators (cr950_estimator)
Filter: 
  _cr950_clientid_value eq '@{first(outputs('ListClients')?['body/value'])?['cr950_clientid']}'
  and cr950_projectname eq '@{outputs('ProjectName')}'
```

#### Step 7: Condition - Estimator Exists?
```
Action: Condition
Expression: length(outputs('Check_for_Existing_Estimator_Record')?['body/value']) greater than 0

If Yes → Go to Step 7b (Update existing record)
If No → Go to Step 7a (Create new record)
```

#### Step 7a: Create New Estimator Record (If No existing record)
```
Action: Dataverse - Add a new row
Table: Estimators (cr950_estimator)
Fields:
  - cr950_name: @{outputs('ProjectName')} (display name)
  - cr950_clientid: @{first(outputs('ListClients')?['body/value'])?['cr950_clientid']} (lookup)
  - cr950_projectname: @{outputs('ProjectName')}
  - cr950_estimatedate: @{outputs('EstimateDate')}
  - cr950_currentrevision: @{outputs('RevisionNumber')}
  - cr950_estimator_file_url: @{outputs('EstimatorFileUrl')}
  - cr950_filename: @{outputs('Filename')}
  - cr950_status: 864340000 (Draft)
  - statecode: 0 (Active)
```

#### Step 7b: Update Existing Estimator Record (If exists)
```
Action: Dataverse - Update a row
Table: Estimators (cr950_estimator)
Row ID: @{first(outputs('Check_for_Existing_Estimator_Record')?['body/value'])?['cr950_estimatorid']}
Fields:
  - cr950_estimatedate: @{outputs('EstimateDate')}
  - cr950_currentrevision: @{outputs('RevisionNumber')}
  - cr950_estimator_file_url: @{outputs('EstimatorFileUrl')}
  - cr950_filename: @{outputs('Filename')}
  - cr950_lastmodified: @{utcNow()}
```

#### Step 8: Send Notification (Optional)
```
Action: Condition - Is new estimator?
If Yes:
  Action: Send email
  To: jason.swenson@resapower.com
  Subject: New Estimator Created: @{outputs('ClientName')} - @{outputs('ProjectName')}
  Body: 
    A new estimator has been imported.
    
    Client: @{outputs('ClientName')}
    Project: @{outputs('ProjectName')}
    Date: @{outputs('EstimateDate')}
    Revision: @{outputs('RevisionNumber')}
    
    View in Web App: [link]
```

### Error Handling

| Error | Action |
|-------|--------|
| File not .xlsm | Ignore silently |
| Client folder doesn't match Dataverse | Email notification, terminate |
| Filename doesn't match pattern | Email warning, terminate |
| Dataverse connection fails | Retry 3x, then alert |
| Duplicate detection conflict | Log warning, continue |

---

## Flow 2: Project Import (Full Import)

### Purpose
Create full Project structure with Scopes and Apparatus when user initiates conversion from Estimator to Project via Web App.

### Trigger
- **Type:** HTTP - "When an HTTP request is received"
- **Method:** POST
- **Request Body JSON Schema:**
```json
{
  "type": "object",
  "properties": {
    "estimatorId": { "type": "string" },
    "estimatorFileUrl": { "type": "string" }
  },
  "required": ["estimatorId", "estimatorFileUrl"]
}
```

### Actions

#### Step 1: Get Estimator Record
```
Action: Dataverse - Get a row by ID
Table: Estimators (cr950_estimators)
Row ID: @{triggerBody()?['estimatorId']}
Expand: cr950_client
```

#### Step 2: Get File Identifier from URL
```
Action: SharePoint - Get file metadata using path
Site: Phoenix Projects
File Path: [extracted from estimatorFileUrl]
```

#### Step 3: Run Office Script (ParseEstimator)
```
Action: Excel Online (Business) - Run script
Location: SharePoint Site
Document Library: Documents
File: @{outputs('GetFileMetadata')?['ItemId']}
Script: ParseEstimator
```

#### Step 4: Parse Script Output
```
Action: Parse JSON
Content: @{body('Run_script')?['result']}
Schema: [EstimatorOutput interface schema]
```

#### Step 5: Create Project Record
```
Action: Dataverse - Add a new row
Table: Projects (cr950_projectses)
Fields:
  - cr950_project_number: @{body('ParsedOutput')?['project']?['projectNumber']}
  - cr950_name: @{body('ParsedOutput')?['project']?['projectName']}
  - cr950_client: @{outputs('GetEstimator')?['body/_cr950_client_value']} (lookup)
  - cr950_address: @{body('ParsedOutput')?['project']?['address']}
  - cr950_estimator_file_url: @{triggerBody()?['estimatorFileUrl']}
  - cr950_estimator: @{triggerBody()?['estimatorId']} (lookup)
  - cr950_status: 864340001 (Awarded)
```

#### Step 6: Loop - Create Scopes
```
Action: Apply to each
Array: @{body('ParsedOutput')?['scopes']}

  Action: Dataverse - Add a new row
  Table: Project Scopes (cr950_projectscopes)
  Fields:
    - cr950_name: @{items('Apply_to_each')?['scopeName']}
    - cr950_scopenumber: @{items('Apply_to_each')?['scopeNumber']}
    - cr950_project_id: @{outputs('CreateProject')?['body/cr950_projectsesid']}
    - cr950_total_hours: @{items('Apply_to_each')?['totalHours']}
    - cr950_quotedamount: @{items('Apply_to_each')?['totalAmount']}
```

#### Step 7: Nested Loop - Create Apparatus
```
Action: Apply to each (nested)
Array: @{items('Apply_to_each_Scope')?['apparatus']}

  Action: Dataverse - Add a new row
  Table: Apparatus (cr950_apparatus)
  Fields:
    - cr950_name: @{items('Apply_to_each_Apparatus')?['apparatusType']}
    - cr950_quantity: @{items('Apply_to_each_Apparatus')?['quantity']}
    - cr950_hours: @{items('Apply_to_each_Apparatus')?['hours']}
    - cr950_scope_id: @{outputs('CreateScope')?['body/cr950_projectscopeid']}
    - cr950_project_id: @{outputs('CreateProject')?['body/cr950_projectsesid']}
```

#### Step 8: Update Estimator Status
```
Action: Dataverse - Update a row
Table: Estimators (cr950_estimators)
Row ID: @{triggerBody()?['estimatorId']}
Fields:
  - cr950_status: 864340002 (Converted)
  - cr950_convertedtoproject: true
  - cr950_project: @{outputs('CreateProject')?['body/cr950_projectsesid']}
```

#### Step 9: Create Project Folder Structure
```
Action: SharePoint - Create new folder
Site: Phoenix Projects
Folder Path: /Projects/@{body('ParsedOutput')?['project']?['projectNumber']} - @{body('ParsedOutput')?['project']?['projectName']}
```

```
Action: SharePoint - Create new folder (repeat for each)
Subfolders:
  - /Estimator
  - /Quote
  - /Deliverables
  - /Field Reports
  - /Photos
```

#### Step 10: Copy Estimator to Project Folder
```
Action: SharePoint - Copy file
Source: @{triggerBody()?['estimatorFileUrl']}
Destination: /Projects/{ProjectNumber} - {ProjectName}/Estimator/
```

#### Step 11: Return Response
```
Action: Response
Status Code: 200
Body: {
  "success": true,
  "projectId": "@{outputs('CreateProject')?['body/cr950_projectsesid']}",
  "projectNumber": "@{body('ParsedOutput')?['project']?['projectNumber']}",
  "scopeCount": @{length(body('ParsedOutput')?['scopes'])},
  "apparatusCount": [sum of all apparatus],
  "projectFolderUrl": "[SharePoint folder URL]"
}
```

### Error Handling
- Script execution failure → Return 500 with error message
- Dataverse failures → Rollback if possible, return 500
- Partial success → Return 207 with details of what succeeded

---

## Office Script: ParseEstimator

### Location
- **OneDrive:** `/Documents/Office Scripts/ParseEstimator.osts`
- **Local Copy:** `c:\RESA_Power_Build\Scripts\OfficeScripts\ParseEstimator.ts`

### Output Interface
```typescript
interface EstimatorOutput {
  project: {
    projectName: string;
    projectNumber: string;
    clientName: string;
    clientContact: string;
    location: string;
    address: string;
    estimatorName: string;
    estimateDate: string;
    poNumber: string;
    totalHours: number;
    totalAmount: number;
  };
  scopes: Array<{
    scopeName: string;
    scopeNumber: number;
    sheetName: string;
    apparatus: Array<{
      quantity: number;
      apparatusType: string;
      hours: number;
      amount: number;
    }>;
    totalHours: number;
    totalAmount: number;
  }>;
  extractedAt: string;
  sourceFile: string;
}
```

### Data Sources in Estimator Workbook
- **Dataverse_Import sheet:** Project metadata (A1:B25)
- **Scope sheets:** Named with NETA/ATS/PSS patterns
  - Cell J3: Total Hours
  - Cell P3: Quoted Amount
  - Rows 6-488: Apparatus data (C=Qty, E=Type, I=Hours, J=Total)

---

## Web App Integration

### Estimators Page Functionality

```typescript
// API call to trigger Flow 2
async function convertEstimatorToProject(estimatorId: string, fileUrl: string) {
  const response = await fetch(FLOW_2_HTTP_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      estimatorId: estimatorId,
      estimatorFileUrl: fileUrl
    })
  });
  
  if (response.ok) {
    const result = await response.json();
    // Navigate to new project or show success
    return result;
  }
}
```

### UI Flow
1. User views Estimators list in Web App (filtered by client, status, etc.)
2. Clicks "Convert to Project" on an estimator
3. Modal opens with:
   - Link to open Estimator in Excel Online
   - Instructions to fill Dataverse_Import sheet (PO#, dates, PM)
   - "Create Project" button
4. User fills data in Excel, saves
5. User clicks "Create Project"
6. Flow 2 runs, creates all records
7. User redirected to new Project view

---

## Dataverse Tables Involved

| Table | Schema Name | Role |
|-------|-------------|------|
| Clients | cr950_clients | Master client list (validated for folder names) |
| Estimators | cr950_estimators | Created by Flow 1 from SharePoint folder structure |
| Projects | cr950_projectses | Full project from Flow 2 |
| Project Scopes | cr950_projectscopes | Scopes from Flow 2 |
| Apparatus | cr950_apparatus | Equipment items from Flow 2 |
| Quote | cr950_quote | (Future) CRM integration for quote PDFs |

---

## Testing Checklist

### Flow 1: Estimator Import
- [ ] Sync SharePoint site to local machine
- [ ] Create client folder matching Dataverse client name
- [ ] Create project subfolder
- [ ] Save estimator file with `_YYYYMMDD_Rev#.xlsm` suffix
- [ ] Verify flow triggers within 5 minutes
- [ ] Check Estimator record created in Dataverse
- [ ] Verify Client lookup is correct
- [ ] Confirm file URL is accessible
- [ ] Save Rev2 file → Verify record updates (not duplicates)

### Flow 1: Error Handling
- [ ] Save to invalid client folder → Error notification sent
- [ ] Save file without date/rev suffix → Warning sent
- [ ] Save non-.xlsm file → Ignored silently

### Flow 2: Project Import
- [ ] Call HTTP endpoint with valid estimatorId
- [ ] Verify Office Script executes successfully
- [ ] Check Project record created with correct client
- [ ] Verify all Scopes created
- [ ] Verify all Apparatus created
- [ ] Confirm Estimator updated with project link
- [ ] Verify project folder created in /Projects/
- [ ] Confirm estimator copied to project folder

### End-to-End Test
- [ ] Save new estimator → Appears in Web App Estimators list
- [ ] Filter by client → Shows only that client's estimators
- [ ] Click "Convert to Project" → Excel Online opens
- [ ] Fill Dataverse_Import → Save
- [ ] Click "Create Project" → Project created
- [ ] Navigate to Project → All data visible
- [ ] Check /Projects/ folder → New project folder exists

---

## Maintenance Notes

### Common Issues
1. **Flow doesn't trigger:** Check folder path, ensure "Include Nested Items" is enabled
2. **Client validation fails:** Ensure folder name exactly matches Dataverse client name
3. **Filename parsing fails:** Verify `_YYYYMMDD_Rev#.xlsm` format
4. **Script fails:** Verify Dataverse_Import sheet exists, check column mappings
5. **Duplicate records:** Flow checks for existing Client+Project combination

### Monitoring
- Check Flow run history daily during initial rollout
- Set up alerts for flow failures
- Review Dataverse records for data quality
- Monitor for orphaned estimator records (no matching project)

### Client Management
- New clients must be added to Dataverse BEFORE creating folders
- Consider Web App or Power Apps form for adding clients
- Client names should be standardized (no abbreviations, consistent formatting)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-28 | Initial specification |
| 2.0 | 2025-11-28 | Complete redesign: Folder-based architecture, Client validation, simplified filename requirements |
| 2.1 | 2025-11-28 | Added link to DATA_MODEL_REFERENCE.md; clarified Business Unit / Client / Site terminology |

---

## Summary: The "Sell" Points

### For Users (Estimators)
- **Save locally** - just save to your synced folder, no extra steps
- **Familiar structure** - Client → Project folders make sense
- **Minimal filename rules** - just add `_YYYYMMDD_Rev#` at the end
- **Automatic tracking** - Dataverse record created on save
- **Find everything** - Web App shows all estimators with filters

### For Management
- **Enforced client names** - Must match Dataverse, no variations
- **Automatic revision tracking** - Every save is logged
- **Centralized visibility** - All estimators in one system
- **Clean project creation** - One click converts to full project
- **Audit trail** - Who saved what, when

### For IT/Admin
- **Single recursive flow** - One flow watches all subfolders
- **Validated data** - Client lookup enforces data quality
- **Simple parsing** - Folders = data, minimal filename complexity
- **Error notifications** - Invalid saves generate alerts
- **Scalable** - Works for 10 or 10,000 estimators

---

## Quick Reference

### Folder Path
```
/Estimators/{Client Name}/{Project Name}/
```

### Filename Pattern
```
{anything}_YYYYMMDD_Rev#.xlsm
```

### Valid Examples
```
/Estimators/Garney Construction/Mesa Reuse/estimate_20251128_Rev1.xlsm  ✅
/Estimators/City of Los Angeles/LASNAP16/final quote_20251115_Rev3.xlsm  ✅
/Estimators/Phoenix Water/Treatment Plant/my file_20251201_Rev2.xlsm  ✅
```

### Invalid Examples
```
/Estimators/Garney/Mesa Reuse/file.xlsm  ❌ (Client "Garney" not in Dataverse)
/Estimators/Garney Construction/file_20251128_Rev1.xlsm  ❌ (No project folder)
/Estimators/Garney Construction/Mesa Reuse/estimate.xlsm  ❌ (No date/rev suffix)
```
