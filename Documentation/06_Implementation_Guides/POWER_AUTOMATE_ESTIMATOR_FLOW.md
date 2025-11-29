# Power Automate Flow: Estimator to Project Starter

## Overview
This flow automatically creates Dataverse project records when an Estimator Excel file is saved to SharePoint.

## Flow Definition

### Trigger
**When a file is created (properties only)**
- Site Address: `https://[tenant].sharepoint.com/sites/PhoenixProjects`
- Library Name: `Documents`
- Folder: `/Estimators/Pending`

### Actions

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. TRIGGER: When file created in /Estimators/Pending/          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. GET FILE CONTENT                                             │
│    Action: Get file content                                     │
│    Site: SharePoint site                                        │
│    File Identifier: @{triggerOutputs()?['body/Id']}            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RUN OFFICE SCRIPT                                            │
│    Action: Run script (Excel Online Business)                   │
│    Location: SharePoint site                                    │
│    Document Library: Documents                                  │
│    File: @{triggerOutputs()?['body/Path']}                     │
│    Script: ParseEstimator                                       │
│    Output: JSON with project, scopes, apparatus                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PARSE JSON                                                   │
│    Content: @{outputs('Run_script')?['body/result']}           │
│    Schema: (see below)                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. CREATE PROJECT RECORD                                        │
│    Action: Add a new row (Dataverse)                           │
│    Table: Projects (cr950_projectses)                          │
│    Fields:                                                      │
│      - cr950_name: @{body('Parse_JSON')?['project']['projectName']}
│      - cr950_projectnumber: @{body('Parse_JSON')?['project']['projectNumber']}
│      - cr950_clientname: @{body('Parse_JSON')?['project']['clientName']}
│      - cr950_location: @{body('Parse_JSON')?['project']['location']}
│      - cr950_estimator: @{body('Parse_JSON')?['project']['estimatorName']}
│      - cr950_status: 864340000 (Not Started)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. CREATE SHAREPOINT FOLDER STRUCTURE                           │
│    Action: Create new folder (SharePoint)                       │
│    Site: SharePoint site                                        │
│    Folders to create:                                           │
│      - /Projects/{ProjectNumber}/                               │
│      - /Projects/{ProjectNumber}/Estimator/                     │
│      - /Projects/{ProjectNumber}/Quotes/                        │
│      - /Projects/{ProjectNumber}/Field_Data/                    │
│      - /Projects/{ProjectNumber}/Reports/                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. COPY ESTIMATOR TO PROJECT FOLDER                             │
│    Action: Copy file (SharePoint)                               │
│    Source: /Estimators/Pending/{filename}                       │
│    Destination: /Projects/{ProjectNumber}/Estimator/{filename}  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. UPDATE PROJECT WITH URLS                                     │
│    Action: Update a row (Dataverse)                            │
│    Row ID: @{outputs('Create_Project')?['body/cr950_projectsid']}
│    Fields:                                                      │
│      - cr950_estimator_url: SharePoint file URL                │
│      - cr950_sharepoint_folder_url: Project folder URL         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. FOR EACH SCOPE                                               │
│    Apply to each: @{body('Parse_JSON')?['scopes']}             │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 9a. CREATE SCOPE RECORD                                 │ │
│    │     Table: Scopes (cr950_scopeses)                      │ │
│    │     Fields:                                             │ │
│    │       - cr950_name: @{items('For_each')?['scopeName']} │ │
│    │       - cr950_scopenumber: @{items('For_each')?['scopeNumber']}
│    │       - cr950_project: Project lookup                   │ │
│    │       - cr950_totalhours: @{items('For_each')?['totalHours']}
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 9b. FOR EACH APPARATUS                                  │ │
│    │     Apply to each: @{items('For_each')?['apparatus']}  │ │
│    │     ┌─────────────────────────────────────────────────┐ │ │
│    │     │ CREATE APPARATUS RECORD                         │ │ │
│    │     │ Table: Apparatus (cr950_apparatuses)            │ │ │
│    │     │ Fields:                                         │ │ │
│    │     │   - cr950_name: Type + Designation              │ │ │
│    │     │   - cr950_quantity: quantity                    │ │ │
│    │     │   - cr950_netacode: netaCode                    │ │ │
│    │     │   - cr950_apparatustype: apparatusType          │ │ │
│    │     │   - cr950_designation: designation              │ │ │
│    │     │   - cr950_drawingnumber: drawingNumber          │ │ │
│    │     │   - cr950_scope: Scope lookup                   │ │ │
│    │     └─────────────────────────────────────────────────┘ │ │
│    └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. MOVE ORIGINAL FILE TO PROCESSED                             │
│     Action: Move file (SharePoint)                              │
│     Source: /Estimators/Pending/{filename}                      │
│     Destination: /Estimators/Processed/{filename}               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. SEND NOTIFICATION                                           │
│     Action: Post adaptive card (Teams) or Send email           │
│     Content:                                                    │
│       - Project Name created                                    │
│       - X scopes, Y apparatus records                          │
│       - Link to project in Dataverse                           │
│       - Link to SharePoint folder                              │
└─────────────────────────────────────────────────────────────────┘
```

## JSON Schema for Parse JSON Action

```json
{
  "type": "object",
  "properties": {
    "project": {
      "type": "object",
      "properties": {
        "projectName": { "type": "string" },
        "projectNumber": { "type": "string" },
        "clientName": { "type": "string" },
        "clientContact": { "type": "string" },
        "location": { "type": "string" },
        "address": { "type": "string" },
        "estimatorName": { "type": "string" },
        "estimateDate": { "type": "string" },
        "poNumber": { "type": "string" },
        "totalHours": { "type": "number" },
        "totalAmount": { "type": "number" }
      }
    },
    "scopes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "scopeName": { "type": "string" },
          "scopeNumber": { "type": "integer" },
          "sheetName": { "type": "string" },
          "apparatus": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "quantity": { "type": "integer" },
                "netaCode": { "type": "string" },
                "apparatusType": { "type": "string" },
                "designation": { "type": "string" },
                "drawingNumber": { "type": "string" },
                "hours": { "type": "number" },
                "rate": { "type": "number" },
                "amount": { "type": "number" }
              }
            }
          },
          "totalHours": { "type": "number" },
          "totalAmount": { "type": "number" }
        }
      }
    },
    "extractedAt": { "type": "string" },
    "sourceFile": { "type": "string" }
  }
}
```

## Required Connections

1. **SharePoint** - For file operations
2. **Excel Online (Business)** - For running Office Scripts
3. **Microsoft Dataverse** - For creating records
4. **Microsoft Teams** (optional) - For notifications

## Environment Variables

Create these in Power Platform environment:

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `SharePointSiteUrl` | SharePoint site URL | `https://[tenant].sharepoint.com/sites/PhoenixProjects` |
| `DataverseEnvironment` | Dataverse environment URL | `https://org99cd6c6e.crm.dynamics.com` |
| `NotificationChannel` | Teams channel for notifications | `General` |

## Deployment Steps

1. **Import Office Script**
   - Open Excel Online
   - Go to Automate > New Script
   - Paste `ParseEstimator.ts` content
   - Save as "ParseEstimator"

2. **Create SharePoint Structure**
   - Create site: "Phoenix Projects"
   - Create document library folders:
     - `/Estimators/Pending/`
     - `/Estimators/Processed/`
     - `/Projects/`

3. **Create Power Automate Flow**
   - Go to make.powerautomate.com
   - Create new Automated cloud flow
   - Add trigger: SharePoint - When a file is created
   - Add actions per the diagram above

4. **Test**
   - Upload test Estimator to `/Estimators/Pending/`
   - Verify flow runs successfully
   - Check Dataverse for new records
   - Check SharePoint for folder structure

## Error Handling

Add Scope blocks around:
- Office Script execution (file might not be valid Excel)
- Dataverse operations (might fail on duplicate project numbers)
- SharePoint operations (folder might already exist)

Configure "Run after" settings to:
- Continue on folder exists errors
- Retry on transient failures
- Send notification on critical errors

## Monitoring

Enable:
- Flow run history
- Analytics dashboard
- Failed run notifications to admin
