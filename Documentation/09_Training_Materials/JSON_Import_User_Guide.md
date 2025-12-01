# RESA Power - JSON Import User Guide

## Overview
This guide explains how to import estimator data from Excel to Dataverse using the JSON export/import pipeline.

---

## Quick Start Options

### Option 1: Drag-and-Drop (Simplest)
1. Export JSON from Excel using the **"Export to JSON"** button
2. Drag the JSON file onto `Import-To-Dataverse.bat`
3. Watch the import complete!

### Option 2: Double-Click the Batch File
1. Double-click `Import-To-Dataverse.bat`
2. Paste the full path to your JSON file when prompted
3. Press Enter

### Option 3: SharePoint Folder Drop (Coming Soon)
1. Drop JSON file in SharePoint folder: `/Shared Documents/Estimators/Dataverse_Exports`
2. Power Automate will automatically import to Dataverse

---

## What Gets Created

When you import a JSON file, the following records are created in Dataverse:

| Entity | Description |
|--------|-------------|
| **Client** | Customer company |
| **Site** | Location with address |
| **Project** | Job with project number |
| **Scopes** | ATS/MTS testing scopes |
| **Scope Labor Details** | Financial data per scope |
| **Apparatus** | Individual equipment records (1 per quantity) |

---

## JSON File Format

The JSON file exported from Excel should look like:

```json
{
  "exportDate": "2024-12-01T10:30:00",
  "client": {
    "name": "ABC Company"
  },
  "site": {
    "name": "Main Campus",
    "address": "123 Main St",
    "city": "Denver",
    "state": "CO",
    "zipCode": "80202"
  },
  "project": {
    "name": "Annual Testing 2024",
    "projectNumber": "2024-0123"
  },
  "scopes": [
    {
      "name": "Switchgear Testing",
      "scopeType": "ATS",
      "totalHours": 40,
      "quotedAmount": 8000,
      "multiplier": 1.0,
      "financials": {
        "onsiteLaborTotal": 6000,
        "offsiteLaborTotal": 1000,
        "travelTotal": 500,
        "outsideServicesTotal": 500
      },
      "apparatus": [
        {
          "equipmentType": "15kV Metal-Clad Switchgear",
          "quantity": 2,
          "hoursPerUnit": 8,
          "section": "Main Distribution"
        }
      ]
    }
  ]
}
```

---

## Troubleshooting

### "Node.js not found"
Install Node.js from https://nodejs.org

### "File not found"
Make sure the full file path is correct, including the `.json` extension

### "Authentication failed"
Check that the `.env` file in `MCP_Servers/resa-dataverse-mcp/` has valid Azure AD credentials

### Import errors
Check the console output for specific error messages. Common issues:
- Duplicate project numbers
- Missing required fields
- Invalid data types

---

## File Locations

| File | Purpose |
|------|---------|
| `Import-To-Dataverse.bat` | Drag-and-drop import tool |
| `Scripts/PowerShell/Watch-SharePoint-Imports.ps1` | Auto-import watcher |
| `MCP_Servers/resa-dataverse-mcp/import-estimator.js` | Core import script |
| `Reference_Files/Excel/` | Sample JSON files |

---

## Support

For issues, check:
1. `Documentation/02_Build_Guides/IMPORT_PIPELINE_SOP.md`
2. `PROJECT_CONTEXT.json` for current status
3. Create an issue in GitHub repository
