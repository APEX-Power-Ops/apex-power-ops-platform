# RESA Power Estimator Import Flow Specification

**Version:** 3.0  
**Date:** November 29, 2025  
**Status:** Active - Simplified Architecture  
**Author:** Jason Swenson / Claude AI Assistant

**Related Documents:**
- [DATA_MODEL_REFERENCE.md](../01_Architecture/DATA_MODEL_REFERENCE.md) - Authoritative data model (Business Unit / Client / Site)
- [DataverseExport.bas](../../Reference_Files/Excel/Estimator%20VBA%20Modules/DataverseExport.bas) - VBA JSON export module

---

## Overview

This document specifies the Power Automate flows that automate the import of Estimator Excel workbooks into Dataverse.

### Architecture Decision (November 29, 2025)

**Previous approach (DEPRECATED):** Office Scripts + Power Automate inline parsing  
**Current approach:** VBA Macro exports JSON → Power Automate imports from JSON file

**Rationale:**
- VBA runs locally, no Office Scripts performance warnings
- JSON file provides clean handoff - decoupled from Excel complexity
- Simpler flow logic - just parse JSON, no Excel cell reading
- Works with SharePoint-synced files (no URL path issues)
- Macro already tested and working

### Key Principles
1. **VBA Does the Heavy Lifting**: Macro extracts all data, builds JSON
2. **JSON as Contract**: Structured file is the interface between Excel and Flow
3. **Flow Stays Simple**: Parse JSON, create Dataverse records
4. **User Control**: User clicks "Export" button, chooses save location

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SIMPLIFIED ESTIMATOR WORKFLOW                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  EXCEL WORKBOOK                    SHAREPOINT                           │
│  ──────────────                    ──────────                           │
│                                                                         │
│  1. User completes Estimator       4. JSON file syncs to SharePoint     │
│     workbook as normal                (via OneDrive sync)               │
│            ↓                                   ↓                        │
│  2. User fills Dataverse_Import    5. Power Automate triggers on        │
│     sheet with metadata               new JSON file                     │
│            ↓                                   ↓                        │
│  3. User clicks "Export to         6. Flow parses JSON, creates         │
│     Dataverse" macro button           Dataverse records                 │
│            ↓                                   ↓                        │
│     VBA creates JSON file          7. Client → Site → Project →         │
│     (Save As dialog)                  Scopes → Apparatus created        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  JSON OUTPUT STRUCTURE:                                                 │
│  {                                                                      │
│    "metadata": { exportDate, workbookName, version },                   │
│    "client": { name },                                                  │
│    "site": { name, address, city, state, zip, contact },               │
│    "project": { name, projectNumber, projectLead, startDate },         │
│    "scopes": [                                                          │
│      {                                                                  │
│        scopeIndex, name, scopeType, totalHours, quotedAmount,          │
│        financials: { onsite, offsite, travel, outsideServices },       │
│        apparatus: [ { quantity, equipmentType, hours } ]               │
│      }                                                                  │
│    ],                                                                   │
│    "summary": { totalScopes, grandTotal }                              │
│  }                                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## VBA Macro: DataverseExport.bas

### Location
`Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas`

### Entry Point
`ExportToDataverse` - Main macro, run from ribbon or button

### What It Does
1. Validates `Dataverse_Import` sheet exists with required fields
2. Extracts project metadata (client, site, project details)
3. Loops through Scope1-Scope20, extracts active scopes
4. For each scope, extracts apparatus rows with hours
5. Builds complete JSON structure
6. Shows Save As dialog (defaults to Documents folder)
7. Saves JSON file

### JSON Filename Pattern
```
{JobNumber}_DATAVERSE_IMPORT_YYYYMMDD_HHMMSS.json
```
Example: `677562_DATAVERSE_IMPORT_20251129_202330.json`

---

## Power Automate Flow: JSON Import

### Trigger Options

**Option A: SharePoint File Trigger (Recommended)**
- Trigger: "When a file is created (properties only)"
- Site: SharePoint site with synced folder
- Library: Documents
- Folder: `/Dataverse_Imports/` (dedicated folder for JSON files)

**Option B: Manual Trigger with File Selection**
- Trigger: "Manually trigger a flow"
- Input: File picker for JSON file
- User initiates import from Power Automate or Power Apps

### Flow Logic

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. TRIGGER: JSON file created in /Dataverse_Imports/           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. GET FILE CONTENT                                             │
│    Action: Get file content                                     │
│    File: @{triggerOutputs()?['body/Id']}                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. PARSE JSON                                                   │
│    Content: File content as string                              │
│    Schema: (see JSON Structure below)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LOOKUP/CREATE CLIENT                                         │
│    Query: cr950_clients where name = client.name                │
│    If not found: Create new client record                       │
│    Store: ClientId for lookups                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. LOOKUP/CREATE SITE                                           │
│    Query: cr950_locations where name = site.name                │
│    If not found: Create with address, city, state, zip          │
│    Store: SiteId for lookups                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. CREATE/UPDATE PROJECT                                        │
│    Query: Existing project by projectNumber?                    │
│    If exists: Update fields                                     │
│    If new: Create project with Client + Site lookups            │
│    Store: ProjectId                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. FOR EACH SCOPE                                               │
│    Apply to each: scopes[]                                      │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 7a. Create Scope record                                 │ │
│    │     - Link to Project                                   │ │
│    │     - Set financials (onsite, offsite, travel, etc.)   │ │
│    │     - Store: ScopeId                                    │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 7b. FOR EACH APPARATUS in scope                         │ │
│    │     - Create Apparatus record                           │ │
│    │     - Link to Scope                                     │ │
│    │     - Set quantity, type, hours                         │ │
│    └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. MOVE PROCESSED FILE                                          │
│    Move JSON to /Dataverse_Imports/Processed/                   │
│    Or delete after successful import                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. SEND NOTIFICATION (Optional)                                 │
│    Email or Teams message with import summary                   │
│    Include: Project name, scope count, total amount             │
└─────────────────────────────────────────────────────────────────┘
```

---

## JSON to Dataverse Field Mapping

### Client (cr950_clients)
| JSON Path | Dataverse Field |
|-----------|-----------------|
| `client.name` | `cr950_name` |

### Site/Location (cr950_locations)
| JSON Path | Dataverse Field |
|-----------|-----------------|
| `site.name` | `cr950_name` |
| `site.address` | `cr950_address` |
| `site.city` | `cr950_city` |
| `site.state` | `cr950_state` |
| `site.zipCode` | `cr950_zipcode` |
| `site.contactName` | `cr950_contactname` |
| `site.contactPhone` | `cr950_contactphone` |
| `site.contactEmail` | `cr950_contactemail` |

### Project (cr950_projectses)
| JSON Path | Dataverse Field |
|-----------|-----------------|
| `project.name` | `cr950_name` |
| `project.projectNumber` | `cr950_jobnumber` |
| `project.projectLead` | `cr950_projectlead` |
| `project.businessUnit` | `cr950_businessunit` |
| `project.startDate` | `cr950_startdate` |
| `project.quoteDate` | `cr950_quotedate` |
| `summary.grandTotal` | `cr950_quotedamount` |

### Scope (cr950_scopeses)
| JSON Path | Dataverse Field |
|-----------|-----------------|
| `scopes[].name` | `cr950_name` |
| `scopes[].scopeType` | `cr950_scopetype` |
| `scopes[].totalHours` | `cr950_totalhours` |
| `scopes[].quotedAmount` | `cr950_quotedamount` |
| `scopes[].multiplier` | `cr950_multiplier` |
| `scopes[].financials.onsiteLaborTotal` | `cr950_onsitelabor` |
| `scopes[].financials.offsiteLaborTotal` | `cr950_offsitelabor` |
| `scopes[].financials.travelTotal` | `cr950_travel` |
| `scopes[].financials.outsideServicesTotal` | `cr950_outsideservices` |

### Apparatus (cr950_apparatus)
| JSON Path | Dataverse Field |
|-----------|-----------------|
| `apparatus[].equipmentType` | `cr950_apparatustype` |
| `apparatus[].quantity` | `cr950_quantity` |
| `apparatus[].hoursPerUnit` | `cr950_hoursperunit` |
| `apparatus[].totalHours` | `cr950_totalhours` |
| `apparatus[].section` | `cr950_section` |

---

## Dataverse_Import Sheet Requirements

The VBA macro reads from a sheet named `Dataverse_Import` in the Estimator workbook.

### Required Fields (Column A = Label, Column B = Value)
| Label | Description | Required |
|-------|-------------|----------|
| Client: | Client company name | ✅ Yes |
| Project: | Project/Site name | ✅ Yes |
| Job #: | Job number | ✅ Yes |
| Site Address: | Street address | No |
| Site City: | City | No |
| Site State: | State abbreviation | No |
| Site Zip Code: | ZIP code | No |
| Site Contact: | Contact name | No |
| Site Contact Phone #: | Phone | No |
| Contact Email Address: | Email | No |
| Project Lead: | PM name | No |
| Business Unit: | Business unit | No |
| Project Start Date: | Start date | No |
| Quote Date: | Quote date | No |
| Quote Revision: | Revision number | No |

### Status Fields (Updated by Macro)
| Label | Description |
|-------|-------------|
| Import Status: | Set to "Exported - Ready for Import" after export |
| Last Import Date: | Timestamp of last export |

---

## Deprecated Approaches

> **Note:** The following approaches were explored but deprecated in favor of the VBA JSON export:

### Office Scripts Approach (DEPRECATED)
- **Issue:** Performance warnings with cell-by-cell reads
- **Issue:** Complex TypeScript for Excel structure navigation
- **Issue:** Debugging difficult in browser environment

### Direct Power Automate Excel Parsing (DEPRECATED)
- **Issue:** SharePoint URL paths incompatible with ChDir
- **Issue:** Excel Online connector slow for large workbooks
- **Issue:** Complex nested loops for apparatus extraction

---

## Future Enhancements

### Phase 2: Bidirectional Sync
- Update Excel workbook with Dataverse record IDs after import
- Enable "refresh from Dataverse" to pull updated actuals

### Phase 3: Web-Based Estimator
- Replace Excel entirely with web application
- AG Grid or similar for data entry
- Direct Dataverse API calls
- Auto-generate PDF proposals

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2025-11-29 | Simplified to VBA JSON export approach |
| 2.2 | 2025-11-29 | Office Scripts optimization attempts |
| 2.1 | 2025-11-28 | Added folder-based client/project detection |
| 2.0 | 2025-11-27 | Initial Office Scripts implementation |
| 1.0 | 2025-11-20 | Original specification |
