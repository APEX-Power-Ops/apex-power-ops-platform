# JSON Import Flow - Complete Build Specification

**Version:** 1.0  
**Date:** November 30, 2025  
**Status:** Ready for Implementation  
**Author:** Jason Swenson / Claude AI Assistant

---

## Overview

This document provides **copy-paste ready** Power Automate code view JSON for the JSON Import Flow. Each action is fully specified with the correct schema, expressions, and Dataverse field mappings.

### Flow Purpose
Import VBA-exported JSON files from Estimator workbooks into Dataverse, creating:
- Client (lookup or create)
- Site/Location (lookup or create)  
- Project (create or update)
- Scopes (create)
- Apparatus (create for each scope)

### Prerequisites
- SharePoint folder: `/Shared Documents/Dataverse_Imports/`
- Dataverse connection configured
- Office 365 Outlook connection (for notifications)

---

## Flow Metadata

```json
{
  "flowName": "JSON Estimator Import",
  "description": "Imports VBA-exported JSON files into Dataverse",
  "trigger": "SharePoint - When a file is created",
  "connections": [
    "shared_commondataserviceforapps",
    "shared_sharepointonline",
    "shared_office365"
  ]
}
```

---

## Action 1: Trigger - When a File is Created

**Type:** SharePoint Trigger (Polling)  
**Location:** Site: jswensonllc.sharepoint.com/sites/PhoenixProjects  
**Library ID:** bf92590a-261e-4ed4-8074-42dcf26db632  
**Folder:** /Shared Documents/Dataverse_Export  

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "dataset": "https://jswensonllc.sharepoint.com/sites/PhoenixProjects",
      "table": "bf92590a-261e-4ed4-8074-42dcf26db632",
      "folderPath": "/Shared Documents/Dataverse_Export"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
      "connection": "shared_sharepointonline",
      "operationId": "GetOnNewFileItems"
    }
  },
  "recurrence": {
    "interval": 1,
    "frequency": "Minute"
  },
  "splitOn": "@triggerOutputs()?['body/value']"
}
```

**Notes:**
- Polls every 1 minute for new files
- `splitOn` processes each file individually
- Filter to `.json` files can be added in trigger conditions if needed

---

## Action 2: Get File Content

**Purpose:** Read the JSON file content from SharePoint

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "dataset": "https://jswensonllc.sharepoint.com/sites/PhoenixProjects",
      "id": "@triggerOutputs()?['body/{Identifier}']"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
      "connection": "shared_sharepointonline",
      "operationId": "GetFileContent"
    }
  },
  "runAfter": {},
  "metadata": {
    "operationMetadataId": "get-file-content-001"
  }
}
```

---

## Action 3: Parse JSON

**Purpose:** Parse the file content into structured data

```json
{
  "type": "ParseJson",
  "inputs": {
    "content": "@body('Get_File_Content')",
    "schema": {
      "type": "object",
      "properties": {
        "metadata": {
          "type": "object",
          "properties": {
            "exportDate": { "type": "string" },
            "workbookName": { "type": "string" },
            "version": { "type": "string" }
          }
        },
        "client": {
          "type": "object",
          "properties": {
            "name": { "type": "string" }
          },
          "required": ["name"]
        },
        "site": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "address": { "type": "string" },
            "city": { "type": "string" },
            "state": { "type": "string" },
            "zipCode": { "type": "string" },
            "contactName": { "type": "string" },
            "contactPhone": { "type": "string" },
            "contactEmail": { "type": "string" }
          },
          "required": ["name"]
        },
        "project": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "projectNumber": { "type": "string" },
            "projectLead": { "type": "string" },
            "businessUnit": { "type": "string" },
            "startDate": { "type": "string" },
            "quoteDate": { "type": "string" },
            "quoteRevision": { "type": "string" }
          },
          "required": ["name"]
        },
        "scopes": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "scopeIndex": { "type": "integer" },
              "name": { "type": "string" },
              "scopeType": { "type": "string" },
              "totalHours": { "type": "number" },
              "multiplier": { "type": "number" },
              "quotedAmount": { "type": "number" },
              "financials": {
                "type": "object",
                "properties": {
                  "onsiteLaborTotal": { "type": "number" },
                  "offsiteLaborTotal": { "type": "number" },
                  "travelTotal": { "type": "number" },
                  "outsideServicesTotal": { "type": "number" }
                }
              },
              "apparatus": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "row": { "type": "integer" },
                    "section": { "type": "string" },
                    "quantity": { "type": "integer" },
                    "equipmentType": { "type": "string" },
                    "hoursPerUnit": { "type": "number" },
                    "totalHours": { "type": "number" }
                  },
                  "required": ["quantity", "equipmentType", "totalHours"]
                }
              }
            },
            "required": ["scopeIndex", "name", "totalHours", "quotedAmount"]
          }
        },
        "summary": {
          "type": "object",
          "properties": {
            "totalScopes": { "type": "integer" },
            "grandTotal": { "type": "number" }
          }
        }
      },
      "required": ["client", "project", "scopes"]
    }
  },
  "runAfter": {
    "Get_File_Content": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "parse-json-001"
  }
}
```

---

## Action 4: Lookup Client in Dataverse

**Purpose:** Check if client already exists

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org99cd6c6e.crm.dynamics.com",
      "entityName": "cr950_clients",
      "$filter": "cr950_name eq '@{body('Parse_JSON')?['client']?['name']}'"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "connection": "shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    }
  },
  "runAfter": {
    "Parse_JSON": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "lookup-client-001"
  }
}
```

---

## Action 5: Client Exists Check

**Purpose:** If client doesn't exist, create it; if exists, get ID

```json
{
  "type": "If",
  "expression": {
    "equals": [
      "@length(outputs('Lookup_Client')?['body/value'])",
      0
    ]
  },
  "actions": {
    "Create_Client": {
      "type": "OpenApiConnection",
      "inputs": {
        "parameters": {
          "organization": "https://org99cd6c6e.crm.dynamics.com",
          "entityName": "cr950_clients",
          "item/cr950_name": "@body('Parse_JSON')?['client']?['name']"
        },
        "host": {
          "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
          "connection": "shared_commondataserviceforapps",
          "operationId": "CreateRecordWithOrganization"
        }
      },
      "metadata": {
        "operationMetadataId": "create-client-001"
      }
    }
  },
  "else": {
    "actions": {}
  },
  "runAfter": {
    "Lookup_Client": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "client-exists-check-001"
  }
}
```

---

## Action 6: Get Client ID (Compose)

**Purpose:** Store client ID whether created or found

```json
{
  "type": "Compose",
  "inputs": "@if(equals(length(outputs('Lookup_Client')?['body/value']), 0), outputs('Create_Client')?['body/cr950_clientid'], first(outputs('Lookup_Client')?['body/value'])?['cr950_clientid'])",
  "runAfter": {
    "Client_Exists_Check": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "get-client-id-001"
  }
}
```

---

## Action 7: Lookup Site in Dataverse

**Purpose:** Check if site already exists (by name + client)

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org99cd6c6e.crm.dynamics.com",
      "entityName": "cr950_sites",
      "$filter": "cr950_name eq '@{body('Parse_JSON')?['site']?['name']}' and _cr950_clientid_value eq '@{outputs('Get_Client_ID')}'"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "connection": "shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    }
  },
  "runAfter": {
    "Get_Client_ID": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "lookup-site-001"
  }
}
```

**Note:** If `cr950_sites` doesn't have a client lookup field, use simpler filter:
```
"$filter": "cr950_name eq '@{body('Parse_JSON')?['site']?['name']}'"
```

---

## Action 8: Site Exists Check

**Purpose:** Create site if it doesn't exist

```json
{
  "type": "If",
  "expression": {
    "equals": [
      "@length(outputs('Lookup_Site')?['body/value'])",
      0
    ]
  },
  "actions": {
    "Create_Site": {
      "type": "OpenApiConnection",
      "inputs": {
        "parameters": {
          "organization": "https://org99cd6c6e.crm.dynamics.com",
          "entityName": "cr950_sites",
          "item/cr950_name": "@body('Parse_JSON')?['site']?['name']",
          "item/cr950_address": "@body('Parse_JSON')?['site']?['address']",
          "item/cr950_city": "@body('Parse_JSON')?['site']?['city']",
          "item/cr950_state": "@body('Parse_JSON')?['site']?['state']",
          "item/cr950_zipcode": "@body('Parse_JSON')?['site']?['zipCode']",
          "item/cr950_contactname": "@body('Parse_JSON')?['site']?['contactName']",
          "item/cr950_contactphone": "@body('Parse_JSON')?['site']?['contactPhone']",
          "item/cr950_contactemail": "@body('Parse_JSON')?['site']?['contactEmail']"
        },
        "host": {
          "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
          "connection": "shared_commondataserviceforapps",
          "operationId": "CreateRecordWithOrganization"
        }
      },
      "metadata": {
        "operationMetadataId": "create-site-001"
      }
    }
  },
  "else": {
    "actions": {}
  },
  "runAfter": {
    "Lookup_Site": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "site-exists-check-001"
  }
}
```

---

## Action 9: Get Site ID (Compose)

**Purpose:** Store site ID whether created or found

```json
{
  "type": "Compose",
  "inputs": "@if(equals(length(outputs('Lookup_Site')?['body/value']), 0), outputs('Create_Site')?['body/cr950_siteid'], first(outputs('Lookup_Site')?['body/value'])?['cr950_siteid'])",
  "runAfter": {
    "Site_Exists_Check": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "get-site-id-001"
  }
}
```

---

## Action 10: Lookup Existing Project

**Purpose:** Check if project exists by job number

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "organization": "https://org99cd6c6e.crm.dynamics.com",
      "entityName": "cr950_projectses",
      "$filter": "cr950_jobnumber eq '@{body('Parse_JSON')?['project']?['projectNumber']}'"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
      "connection": "shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    }
  },
  "runAfter": {
    "Get_Site_ID": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "lookup-project-001"
  }
}
```

---

## Action 11: Project Exists Check

**Purpose:** Create or update project

```json
{
  "type": "If",
  "expression": {
    "equals": [
      "@length(outputs('Lookup_Project')?['body/value'])",
      0
    ]
  },
  "actions": {
    "Create_Project": {
      "type": "OpenApiConnection",
      "inputs": {
        "parameters": {
          "organization": "https://org99cd6c6e.crm.dynamics.com",
          "entityName": "cr950_projectses",
          "item/cr950_name": "@body('Parse_JSON')?['project']?['name']",
          "item/cr950_jobnumber": "@body('Parse_JSON')?['project']?['projectNumber']",
          "item/cr950_projectlead": "@body('Parse_JSON')?['project']?['projectLead']",
          "item/cr950_quotedamount": "@body('Parse_JSON')?['summary']?['grandTotal']",
          "item/cr950_startdate": "@if(equals(body('Parse_JSON')?['project']?['startDate'], ''), null, body('Parse_JSON')?['project']?['startDate'])",
          "item/cr950_clientid@odata.bind": "/cr950_clients(@{outputs('Get_Client_ID')})",
          "item/cr950_siteid@odata.bind": "/cr950_sites(@{outputs('Get_Site_ID')})"
        },
        "host": {
          "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
          "connection": "shared_commondataserviceforapps",
          "operationId": "CreateRecordWithOrganization"
        }
      },
      "metadata": {
        "operationMetadataId": "create-project-001"
      }
    }
  },
  "else": {
    "actions": {
      "Update_Project": {
        "type": "OpenApiConnection",
        "inputs": {
          "parameters": {
            "organization": "https://org99cd6c6e.crm.dynamics.com",
            "entityName": "cr950_projectses",
            "recordId": "@first(outputs('Lookup_Project')?['body/value'])?['cr950_projectsid']",
            "item/cr950_name": "@body('Parse_JSON')?['project']?['name']",
            "item/cr950_projectlead": "@body('Parse_JSON')?['project']?['projectLead']",
            "item/cr950_quotedamount": "@body('Parse_JSON')?['summary']?['grandTotal']"
          },
          "host": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
            "connection": "shared_commondataserviceforapps",
            "operationId": "UpdateOnlyRecordWithOrganization"
          }
        },
        "metadata": {
          "operationMetadataId": "update-project-001"
        }
      }
    }
  },
  "runAfter": {
    "Lookup_Project": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "project-exists-check-001"
  }
}
```

---

## Action 12: Get Project ID (Compose)

**Purpose:** Store project ID whether created or updated

```json
{
  "type": "Compose",
  "inputs": "@if(equals(length(outputs('Lookup_Project')?['body/value']), 0), outputs('Create_Project')?['body/cr950_projectsid'], first(outputs('Lookup_Project')?['body/value'])?['cr950_projectsid'])",
  "runAfter": {
    "Project_Exists_Check": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "get-project-id-001"
  }
}
```

---

## Action 13: Initialize Scope Counter Variable

**Purpose:** Track scope creation for summary

```json
{
  "type": "InitializeVariable",
  "inputs": {
    "variables": [
      {
        "name": "ScopeCount",
        "type": "integer",
        "value": 0
      }
    ]
  },
  "runAfter": {
    "Get_Project_ID": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "init-scope-count-001"
  }
}
```

---

## Action 14: Initialize Apparatus Counter Variable

**Purpose:** Track total apparatus created

```json
{
  "type": "InitializeVariable",
  "inputs": {
    "variables": [
      {
        "name": "ApparatusCount",
        "type": "integer",
        "value": 0
      }
    ]
  },
  "runAfter": {
    "Initialize_Scope_Counter": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "init-apparatus-count-001"
  }
}
```

---

## Action 15: For Each Scope

**Purpose:** Loop through scopes array and create records

```json
{
  "type": "Foreach",
  "foreach": "@body('Parse_JSON')?['scopes']",
  "actions": {
    "Create_Scope": {
      "type": "OpenApiConnection",
      "inputs": {
        "parameters": {
          "organization": "https://org99cd6c6e.crm.dynamics.com",
          "entityName": "cr950_projectscopes",
          "item/cr950_name": "@items('For_Each_Scope')?['name']",
          "item/cr950_scopetype": "@items('For_Each_Scope')?['scopeType']",
          "item/cr950_scopeindex": "@items('For_Each_Scope')?['scopeIndex']",
          "item/cr950_totalhours": "@items('For_Each_Scope')?['totalHours']",
          "item/cr950_quotedamount": "@items('For_Each_Scope')?['quotedAmount']",
          "item/cr950_multiplier": "@items('For_Each_Scope')?['multiplier']",
          "item/cr950_onsitelabor": "@items('For_Each_Scope')?['financials']?['onsiteLaborTotal']",
          "item/cr950_offsitelabor": "@items('For_Each_Scope')?['financials']?['offsiteLaborTotal']",
          "item/cr950_travel": "@items('For_Each_Scope')?['financials']?['travelTotal']",
          "item/cr950_outsideservices": "@items('For_Each_Scope')?['financials']?['outsideServicesTotal']",
          "item/cr950_projectid@odata.bind": "/cr950_projectses(@{outputs('Get_Project_ID')})",
          "item/cr950_siteid@odata.bind": "/cr950_sites(@{outputs('Get_Site_ID')})"
        },
        "host": {
          "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
          "connection": "shared_commondataserviceforapps",
          "operationId": "CreateRecordWithOrganization"
        }
      },
      "metadata": {
        "operationMetadataId": "create-scope-001"
      }
    },
    "Increment_Scope_Count": {
      "type": "IncrementVariable",
      "inputs": {
        "name": "ScopeCount",
        "value": 1
      },
      "runAfter": {
        "Create_Scope": ["Succeeded"]
      },
      "metadata": {
        "operationMetadataId": "increment-scope-001"
      }
    },
    "For_Each_Apparatus": {
      "type": "Foreach",
      "foreach": "@items('For_Each_Scope')?['apparatus']",
      "actions": {
        "Create_Apparatus": {
          "type": "OpenApiConnection",
          "inputs": {
            "parameters": {
              "organization": "https://org99cd6c6e.crm.dynamics.com",
              "entityName": "cr950_apparatuses",
              "item/cr950_name": "@items('For_Each_Apparatus')?['equipmentType']",
              "item/cr950_apparatustype": "@items('For_Each_Apparatus')?['equipmentType']",
              "item/cr950_quantity": "@items('For_Each_Apparatus')?['quantity']",
              "item/cr950_hoursperunit": "@items('For_Each_Apparatus')?['hoursPerUnit']",
              "item/cr950_totalhours": "@items('For_Each_Apparatus')?['totalHours']",
              "item/cr950_section": "@items('For_Each_Apparatus')?['section']",
              "item/cr950_scopeid@odata.bind": "/cr950_projectscopes(@{outputs('Create_Scope')?['body/cr950_projectscopeid']})"
            },
            "host": {
              "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
              "connection": "shared_commondataserviceforapps",
              "operationId": "CreateRecordWithOrganization"
            }
          },
          "metadata": {
            "operationMetadataId": "create-apparatus-001"
          }
        },
        "Increment_Apparatus_Count": {
          "type": "IncrementVariable",
          "inputs": {
            "name": "ApparatusCount",
            "value": 1
          },
          "runAfter": {
            "Create_Apparatus": ["Succeeded"]
          },
          "metadata": {
            "operationMetadataId": "increment-apparatus-001"
          }
        }
      },
      "runAfter": {
        "Increment_Scope_Count": ["Succeeded"]
      },
      "runtimeConfiguration": {
        "concurrency": {
          "repetitions": 1
        }
      },
      "metadata": {
        "operationMetadataId": "foreach-apparatus-001"
      }
    }
  },
  "runAfter": {
    "Initialize_Apparatus_Counter": ["Succeeded"]
  },
  "runtimeConfiguration": {
    "concurrency": {
      "repetitions": 1
    }
  },
  "metadata": {
    "operationMetadataId": "foreach-scope-001"
  }
}
```

**IMPORTANT:** 
- Set `concurrency.repetitions: 1` on both loops to process sequentially
- This ensures Scope ID is available before Apparatus creation
- Prevents race conditions with variable increments

---

## Action 16: Move File to Processed Folder

**Purpose:** Move the JSON file after successful import

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "dataset": "https://jswensonllc.sharepoint.com/sites/PhoenixProjects",
      "sourceFileId": "@triggerOutputs()?['body/{Identifier}']",
      "destinationFolderPath": "/Shared Documents/Dataverse_Imports/Processed",
      "nameConflictBehavior": 1
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
      "connection": "shared_sharepointonline",
      "operationId": "MoveFile"
    }
  },
  "runAfter": {
    "For_Each_Scope": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "move-file-001"
  }
}
```

---

## Action 17: Send Success Notification

**Purpose:** Email summary of import

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "parameters": {
      "emailMessage/To": "jason.swenson@resapower.com",
      "emailMessage/Subject": "✅ Estimator Import Complete: @{body('Parse_JSON')?['project']?['name']}",
      "emailMessage/Body": "<h2>Import Summary</h2><p><strong>Project:</strong> @{body('Parse_JSON')?['project']?['name']}<br><strong>Job #:</strong> @{body('Parse_JSON')?['project']?['projectNumber']}<br><strong>Client:</strong> @{body('Parse_JSON')?['client']?['name']}<br><strong>Site:</strong> @{body('Parse_JSON')?['site']?['name']}<br><br><strong>Scopes Created:</strong> @{variables('ScopeCount')}<br><strong>Apparatus Created:</strong> @{variables('ApparatusCount')}<br><strong>Grand Total:</strong> $@{formatNumber(body('Parse_JSON')?['summary']?['grandTotal'], 'N2')}</p><p><strong>Source File:</strong> @{triggerOutputs()?['body/{FilenameWithExtension}']}<br><strong>Imported At:</strong> @{utcNow()}</p>",
      "emailMessage/Importance": "Normal"
    },
    "host": {
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_office365",
      "connection": "shared_office365",
      "operationId": "SendEmailV2"
    }
  },
  "runAfter": {
    "Move_File_to_Processed": ["Succeeded"]
  },
  "metadata": {
    "operationMetadataId": "send-notification-001"
  }
}
```

---

## Error Handling Scope

**Purpose:** Wrap main logic in try-catch for error handling

Add this as a parallel branch after trigger:

```json
{
  "type": "Scope",
  "actions": {
    "Send_Error_Notification": {
      "type": "OpenApiConnection",
      "inputs": {
        "parameters": {
          "emailMessage/To": "jason.swenson@resapower.com",
          "emailMessage/Subject": "❌ Estimator Import FAILED: @{triggerOutputs()?['body/{FilenameWithExtension}']}",
          "emailMessage/Body": "<h2>Import Failed</h2><p><strong>File:</strong> @{triggerOutputs()?['body/{FilenameWithExtension}']}<br><strong>Error:</strong> Check flow run history for details<br><strong>Time:</strong> @{utcNow()}</p>",
          "emailMessage/Importance": "High"
        },
        "host": {
          "apiId": "/providers/Microsoft.PowerApps/apis/shared_office365",
          "connection": "shared_office365",
          "operationId": "SendEmailV2"
        }
      }
    }
  },
  "runAfter": {
    "For_Each_Scope": ["Failed", "TimedOut"]
  }
}
```

---

## Field Mapping Quick Reference

### JSON → Dataverse Field Mappings

| JSON Path | Dataverse Table | Dataverse Field |
|-----------|-----------------|-----------------|
| `client.name` | cr950_clients | cr950_name |
| `site.name` | cr950_sites | cr950_name |
| `site.address` | cr950_sites | cr950_address |
| `site.city` | cr950_sites | cr950_city |
| `site.state` | cr950_sites | cr950_state |
| `site.zipCode` | cr950_sites | cr950_zipcode |
| `site.contactName` | cr950_sites | cr950_contactname |
| `site.contactPhone` | cr950_sites | cr950_contactphone |
| `site.contactEmail` | cr950_sites | cr950_contactemail |
| `project.name` | cr950_projectses | cr950_name |
| `project.projectNumber` | cr950_projectses | cr950_jobnumber |
| `project.projectLead` | cr950_projectses | cr950_projectlead |
| `project.startDate` | cr950_projectses | cr950_startdate |
| `summary.grandTotal` | cr950_projectses | cr950_quotedamount |
| `scopes[].name` | cr950_projectscopes | cr950_name |
| `scopes[].scopeType` | cr950_projectscopes | cr950_scopetype |
| `scopes[].scopeIndex` | cr950_projectscopes | cr950_scopeindex |
| `scopes[].totalHours` | cr950_projectscopes | cr950_totalhours |
| `scopes[].quotedAmount` | cr950_projectscopes | cr950_quotedamount |
| `scopes[].multiplier` | cr950_projectscopes | cr950_multiplier |
| `scopes[].financials.onsiteLaborTotal` | cr950_projectscopes | cr950_onsitelabor |
| `scopes[].financials.offsiteLaborTotal` | cr950_projectscopes | cr950_offsitelabor |
| `scopes[].financials.travelTotal` | cr950_projectscopes | cr950_travel |
| `scopes[].financials.outsideServicesTotal` | cr950_projectscopes | cr950_outsideservices |
| `apparatus[].equipmentType` | cr950_apparatus | cr950_apparatustype |
| `apparatus[].quantity` | cr950_apparatus | cr950_quantity |
| `apparatus[].hoursPerUnit` | cr950_apparatus | cr950_hoursperunit |
| `apparatus[].totalHours` | cr950_apparatus | cr950_totalhours |
| `apparatus[].section` | cr950_apparatus | cr950_section |

---

## Lookup Field Syntax

For Dataverse lookup fields, use the `@odata.bind` syntax:

```
"item/cr950_clientid@odata.bind": "/cr950_clients({GUID})"
"item/cr950_projectid@odata.bind": "/cr950_projectses({GUID})"
"item/cr950_scopeid@odata.bind": "/cr950_projectscopes({GUID})"
"item/cr950_siteid@odata.bind": "/cr950_sites({GUID})"
```

**Expression Example:**
```
"item/cr950_clientid@odata.bind": "/cr950_clients(@{outputs('Get_Client_ID')})"
```

---

## Verification Checklist

Before running the flow:

- [ ] SharePoint folder `/Dataverse_Imports/` exists
- [ ] SharePoint folder `/Dataverse_Imports/Processed/` exists
- [ ] Dataverse connection is authenticated
- [ ] Office 365 connection is authenticated
- [ ] All field names match actual Dataverse schema
- [ ] Test with a sample JSON file first

### Test JSON File
Use the existing test file:
`Reference_Files/Excel/_DATAVERSE_IMPORT_20251129_202330.json`

Copy to SharePoint `/Dataverse_Imports/` folder to trigger flow.

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-30 | Initial complete specification |
