# JSON Import Flow Specification - V2 Schema

**Version:** 2.0.0  
**Date:** December 2, 2025  
**Status:** READY FOR IMPLEMENTATION  
**Target Environment:** org284447bd.crm.dynamics.com  
**Author:** Jason Swenson / Claude AI Assistant

---

## 📋 Overview

**Purpose:** Import complete project structures from JSON files exported by VBA macro. Creates Client → Site → Project → Scope → Task → Apparatus hierarchy with ScopeLaborDetail financial configuration.

**Trigger:** SharePoint file creation (JSON files in /Dataverse_Imports/)  
**Tables Used:** cr950_clients, cr950_sites, cr950_projects, cr950_scopes, cr950_tasks, cr950_scopelabordetails, cr950_apparatuses  
**Complexity:** 🔴 High - Multiple entity renames + architecture change

---

## 🔴 CRITICAL V1 → V2 Changes

### Entity Renames

| V1 EntitySetName | V2 EntitySetName | Impact |
|------------------|------------------|--------|
| cr950_projectses | cr950_projects | 🔴 BREAKING |
| cr950_projectscopes | cr950_scopes | 🔴 BREAKING |
| cr950_scopelabordetailses | cr950_scopelabordetails | 🔴 BREAKING |
| cr950_taskses | cr950_tasks | 🔴 BREAKING |
| cr950_clients | cr950_clients | ✅ No change |
| cr950_sites | cr950_sites | ✅ No change |
| cr950_apparatuses | cr950_apparatuses | ✅ No change |

### 🚨 ARCHITECTURE CHANGE - Apparatus Hierarchy

**V1 Architecture:**
```
Project → Scope → Apparatus (direct link)
```

**V2 Architecture:**
```
Project → Scope → Task → Apparatus
```

**Impact:** Flow MUST create Task records before creating Apparatus. Each Apparatus now links to a Task, not directly to a Scope.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    JSON IMPORT FLOW - V2 SCHEMA                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  TRIGGER: JSON file created in /Dataverse_Imports/                      │
│                                                                          │
│  JSON STRUCTURE:                                                         │
│  {                                                                       │
│    "client": { "name": "..." },                                         │
│    "site": { "name", "address", "city", "state", "zipCode" },          │
│    "project": { "name", "projectNumber" },                              │
│    "scopes": [{                                                         │
│      "name", "scopeType", "totalHours", "quotedAmount",                │
│      "financials": { onsite, offsite, travel, outside },               │
│      "apparatus": [{ "equipmentType", "quantity", "hoursPerUnit" }]    │
│    }]                                                                   │
│  }                                                                       │
│                                                                          │
│  FLOW SEQUENCE:                                                          │
│  ──────────────                                                          │
│                                                                          │
│  1. Get File Content → Parse JSON                                       │
│        │                                                                 │
│        ▼                                                                 │
│  2. CREATE CLIENT (cr950_clients)                                       │
│     - cr950_client_name = client.name                                   │
│        │                                                                 │
│        ▼                                                                 │
│  3. CREATE SITE (cr950_sites)                                           │
│     - cr950_site_name, address, city, state, zip                        │
│     - cr950_site_client@odata.bind → Client                             │
│        │                                                                 │
│        ▼                                                                 │
│  4. CREATE PROJECT (cr950_projects)                                     │
│     - cr950_project_name, cr950_project_number                          │
│     - cr950_project_client@odata.bind → Client                          │
│     - cr950_project_site@odata.bind → Site                              │
│        │                                                                 │
│        ▼                                                                 │
│  5. FOR EACH SCOPE in scopes[]:                                         │
│     ┌───────────────────────────────────────────────────────────────┐   │
│     │ 5a. CREATE SCOPE (cr950_scopes)                               │   │
│     │     - cr950_scope_name, cr950_scope_type                      │   │
│     │     - cr950_scope_project@odata.bind → Project                │   │
│     └───────────────────────────────────────────────────────────────┘   │
│     ┌───────────────────────────────────────────────────────────────┐   │
│     │ 5b. CREATE SCOPELABORDETAIL (cr950_scopelabordetails)         │   │
│     │     - cr950_scopelabor_name                                   │   │
│     │     - cr950_scopelabor_total_hours, quoted_amount             │   │
│     │     - Financial totals (onsite, offsite, travel, outside)     │   │
│     │     - cr950_scopelabor_scope@odata.bind → Scope               │   │
│     └───────────────────────────────────────────────────────────────┘   │
│     ┌───────────────────────────────────────────────────────────────┐   │
│     │ 5c. 🆕 CREATE DEFAULT TASK (cr950_tasks) ← V2 ADDITION        │   │
│     │     - cr950_task_name = "{Scope Name} - Default Task"         │   │
│     │     - cr950_task_scope@odata.bind → Scope                     │   │
│     └───────────────────────────────────────────────────────────────┘   │
│     ┌───────────────────────────────────────────────────────────────┐   │
│     │ 5d. FOR EACH APPARATUS in scope.apparatus[]:                  │   │
│     │     FOR i = 0 to quantity:                                    │   │
│     │       CREATE APPARATUS (cr950_apparatuses)                    │   │
│     │       - cr950_apparatus_type, hours_per_unit                  │   │
│     │       - cr950_apparatus_task@odata.bind → Task ← V2 CHANGE   │   │
│     │       (V1 used cr950_Scope@odata.bind)                        │   │
│     └───────────────────────────────────────────────────────────────┘   │
│        │                                                                 │
│        ▼                                                                 │
│  6. Move processed file to /Processed/ folder                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 V2 Field Mappings

### JSON → Client (cr950_clients)

| JSON Path | V2 Field | V1 Field | Notes |
|-----------|----------|----------|-------|
| `client.name` | `cr950_client_name` | cr950_name | **RENAMED** |

### JSON → Site (cr950_sites)

| JSON Path | V2 Field | V1 Field | Notes |
|-----------|----------|----------|-------|
| `site.name` | `cr950_site_name` | cr950_name | **RENAMED** |
| `site.address` | `cr950_site_address` | cr950_address | **RENAMED** |
| `site.city` | `cr950_site_city` | cr950_city | **RENAMED** |
| `site.state` | `cr950_site_state` | cr950_state | **RENAMED** |
| `site.zipCode` | `cr950_site_zip` | cr950_zip | **RENAMED** |
| `site.contactEmail` | `cr950_site_contact_email` | cr950_sitecontactemail | **RENAMED** |
| Client lookup | `cr950_site_client@odata.bind` | cr950_client@odata.bind | **RENAMED** |

### JSON → Project (cr950_projects)

| JSON Path | V2 Field | V1 Field | Notes |
|-----------|----------|----------|-------|
| `project.name` | `cr950_project_name` | cr950_project_name | ✅ Same |
| `project.projectNumber` | `cr950_project_number` | cr950_job_number | **RENAMED** |
| Client lookup | `cr950_project_client@odata.bind` | cr950_client@odata.bind | **RENAMED** |
| Site lookup | `cr950_project_site@odata.bind` | cr950_site@odata.bind | **RENAMED** |
| **Primary Key** | `cr950_projectid` | cr950_projectsid | **RENAMED** |

### JSON → Scope (cr950_scopes)

| JSON Path | V2 Field | V1 Field | Notes |
|-----------|----------|----------|-------|
| `scopes[].name` | `cr950_scope_name` | cr950_scope_name | ✅ Same |
| `scopes[].scopeType` | `cr950_scope_type` | cr950_testing_standard | **RENAMED** |
| Project lookup | `cr950_scope_project@odata.bind` | cr950_Project@odata.bind | **RENAMED** |
| **Primary Key** | `cr950_scopeid` | cr950_projectscopeid | **RENAMED** |

### JSON → ScopeLaborDetail (cr950_scopelabordetails)

| JSON Path | V2 Field | V1 Field | Notes |
|-----------|----------|----------|-------|
| Auto-generated | `cr950_scopelabor_name` | cr950_name | **RENAMED** |
| `scopes[].totalHours` | `cr950_scopelabor_total_hours` | cr950_total_apparatus_hours | **RENAMED** |
| `scopes[].quotedAmount` | `cr950_scopelabor_quoted_amount` | cr950_scope_total_value | **RENAMED** |
| `scopes[].multiplier` | `cr950_scopelabor_multiplier` | cr950_scopemultiplier | **RENAMED** |
| `financials.onsiteLaborTotal` | `cr950_scopelabor_onsite_total` | cr950_onsitelabortotal | **RENAMED** |
| `financials.offsiteLaborTotal` | `cr950_scopelabor_offsite_total` | cr950_offsitelabortotal | **RENAMED** |
| `financials.travelTotal` | `cr950_scopelabor_travel_total` | cr950_traveltotal | **RENAMED** |
| `financials.outsideServicesTotal` | `cr950_scopelabor_outside_total` | cr950_outsideservicestotal | **RENAMED** |
| Scope lookup | `cr950_scopelabor_scope@odata.bind` | cr950_projectscope_id@odata.bind | **RENAMED** |
| **Primary Key** | `cr950_scopelaborid` | cr950_scopelabordetailsid | **RENAMED** |

### JSON → Task (cr950_tasks) - 🆕 V2 ADDITION

| Source | V2 Field | Notes |
|--------|----------|-------|
| Generated | `cr950_task_name` | "{Scope Name} - Default Task" |
| Scope lookup | `cr950_task_scope@odata.bind` | Link to parent Scope |
| **Primary Key** | `cr950_taskid` | New in V2 |

### JSON → Apparatus (cr950_apparatuses)

| JSON Path | V2 Field | V1 Field | Notes |
|-----------|----------|----------|-------|
| `apparatus[].equipmentType` | `cr950_apparatus_type` | cr950_apparatustype | **RENAMED** |
| `apparatus[].hoursPerUnit` | `cr950_apparatus_hours_per_unit` | cr950_labor_hours | **RENAMED** |
| `apparatus[].section` | `cr950_apparatus_section` | cr950_notes | **RENAMED** |
| ~~Scope lookup~~ | ~~cr950_Scope@odata.bind~~ | - | 🔴 **REMOVED** |
| Task lookup | `cr950_apparatus_task@odata.bind` | - | 🆕 **V2 ADDITION** |
| ~~Project lookup~~ | ~~cr950_Project@odata.bind~~ | - | 🔴 **REMOVED** (denormalized) |

---

## 🔧 Flow Actions - V2 Configuration

### Action 1: Get File Content

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_sharepointonline",
      "operationId": "GetFileContent"
    },
    "parameters": {
      "dataset": "https://jswensonllc.sharepoint.com/sites/PhoenixProjects",
      "id": "@triggerOutputs()?['body/Id']"
    }
  }
}
```

### Action 2: Parse JSON

```json
{
  "type": "ParseJson",
  "inputs": {
    "content": "@{body('Get_file_content')}",
    "schema": {
      "type": "object",
      "properties": {
        "exportDate": { "type": "string" },
        "client": {
          "type": "object",
          "properties": { "name": { "type": "string" } }
        },
        "site": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "address": { "type": "string" },
            "city": { "type": "string" },
            "state": { "type": "string" },
            "zipCode": { "type": "string" },
            "contactEmail": { "type": "string" }
          }
        },
        "project": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "projectNumber": { "type": "string" }
          }
        },
        "scopes": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "scopeType": { "type": "string" },
              "totalHours": { "type": "number" },
              "quotedAmount": { "type": "number" },
              "multiplier": { "type": "number" },
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
                    "equipmentType": { "type": "string" },
                    "quantity": { "type": "integer" },
                    "hoursPerUnit": { "type": "number" },
                    "section": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Action 3: Create Client - V2

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "CreateRecord"
    },
    "parameters": {
      "entityName": "cr950_clients",
      "item/cr950_client_name": "@body('Parse_JSON')?['client']?['name']"
    }
  }
}
```

**⚠️ V1 → V2:** Field `cr950_name` → `cr950_client_name`

### Action 4: Create Site - V2

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "CreateRecord"
    },
    "parameters": {
      "entityName": "cr950_sites",
      "item/cr950_site_name": "@body('Parse_JSON')?['site']?['name']",
      "item/cr950_site_address": "@body('Parse_JSON')?['site']?['address']",
      "item/cr950_site_city": "@body('Parse_JSON')?['site']?['city']",
      "item/cr950_site_state": "@body('Parse_JSON')?['site']?['state']",
      "item/cr950_site_zip": "@body('Parse_JSON')?['site']?['zipCode']",
      "item/cr950_site_contact_email": "@body('Parse_JSON')?['site']?['contactEmail']",
      "item/cr950_site_client@odata.bind": "cr950_clients(@{outputs('Create_Client')?['body/cr950_clientid']})"
    }
  }
}
```

### Action 5: Create Project - V2 🔴 CHANGED

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "CreateRecord"
    },
    "parameters": {
      "entityName": "cr950_projects",
      "item/cr950_project_name": "@body('Parse_JSON')?['project']?['name']",
      "item/cr950_project_number": "@body('Parse_JSON')?['project']?['projectNumber']",
      "item/cr950_project_client@odata.bind": "cr950_clients(@{outputs('Create_Client')?['body/cr950_clientid']})",
      "item/cr950_project_site@odata.bind": "cr950_sites(@{outputs('Create_Site')?['body/cr950_siteid']})"
    }
  }
}
```

**⚠️ V1 → V2 CHANGES:**
- EntityName: `cr950_projectses` → `cr950_projects`
- Field: `cr950_job_number` → `cr950_project_number`
- Lookup bindings renamed

### Action 6: Loop Scopes with Task Creation - V2 🆕

```json
{
  "type": "Foreach",
  "foreach": "@body('Parse_JSON')?['scopes']",
  "actions": {
    "Create_Scope": {
      "type": "OpenApiConnection",
      "inputs": {
        "parameters": {
          "entityName": "cr950_scopes",
          "item/cr950_scope_name": "@items('Loop_Scopes')?['name']",
          "item/cr950_scope_type": "@items('Loop_Scopes')?['scopeType']",
          "item/cr950_scope_project@odata.bind": "cr950_projects(@{outputs('Create_Project')?['body/cr950_projectid']})"
        }
      }
    },
    "Create_ScopeLaborDetail": {
      "type": "OpenApiConnection",
      "runAfter": { "Create_Scope": ["Succeeded"] },
      "inputs": {
        "parameters": {
          "entityName": "cr950_scopelabordetails",
          "item/cr950_scopelabor_name": "@concat(items('Loop_Scopes')?['name'], ' - Labor Details')",
          "item/cr950_scopelabor_total_hours": "@items('Loop_Scopes')?['totalHours']",
          "item/cr950_scopelabor_quoted_amount": "@items('Loop_Scopes')?['quotedAmount']",
          "item/cr950_scopelabor_multiplier": "@coalesce(items('Loop_Scopes')?['multiplier'], 1.0)",
          "item/cr950_scopelabor_onsite_total": "@coalesce(items('Loop_Scopes')?['financials']?['onsiteLaborTotal'], 0)",
          "item/cr950_scopelabor_offsite_total": "@coalesce(items('Loop_Scopes')?['financials']?['offsiteLaborTotal'], 0)",
          "item/cr950_scopelabor_travel_total": "@coalesce(items('Loop_Scopes')?['financials']?['travelTotal'], 0)",
          "item/cr950_scopelabor_outside_total": "@coalesce(items('Loop_Scopes')?['financials']?['outsideServicesTotal'], 0)",
          "item/cr950_scopelabor_scope@odata.bind": "cr950_scopes(@{outputs('Create_Scope')?['body/cr950_scopeid']})"
        }
      }
    },
    "Create_Default_Task": {
      "type": "OpenApiConnection",
      "runAfter": { "Create_ScopeLaborDetail": ["Succeeded"] },
      "inputs": {
        "parameters": {
          "entityName": "cr950_tasks",
          "item/cr950_task_name": "@concat(items('Loop_Scopes')?['name'], ' - Default Task')",
          "item/cr950_task_scope@odata.bind": "cr950_scopes(@{outputs('Create_Scope')?['body/cr950_scopeid']})"
        }
      }
    },
    "Loop_Apparatus": {
      "type": "Foreach",
      "runAfter": { "Create_Default_Task": ["Succeeded"] },
      "foreach": "@items('Loop_Scopes')?['apparatus']",
      "actions": {
        "Create_Apparatus_Records": {
          "type": "Foreach",
          "foreach": "@range(0, items('Loop_Apparatus')?['quantity'])",
          "actions": {
            "Create_Apparatus": {
              "type": "OpenApiConnection",
              "inputs": {
                "parameters": {
                  "entityName": "cr950_apparatuses",
                  "item/cr950_apparatus_type": "@items('Loop_Apparatus')?['equipmentType']",
                  "item/cr950_apparatus_hours_per_unit": "@items('Loop_Apparatus')?['hoursPerUnit']",
                  "item/cr950_apparatus_section": "@items('Loop_Apparatus')?['section']",
                  "item/cr950_apparatus_task@odata.bind": "cr950_tasks(@{outputs('Create_Default_Task')?['body/cr950_taskid']})"
                }
              }
            }
          },
          "runtimeConfiguration": { "concurrency": { "repetitions": 1 } }
        }
      }
    }
  },
  "runtimeConfiguration": { "concurrency": { "repetitions": 1 } }
}
```

**🆕 V2 ADDITIONS:**
1. `Create_Default_Task` action - creates Task for each Scope
2. Apparatus now links to Task via `cr950_apparatus_task@odata.bind`

**🔴 V2 REMOVALS:**
1. `cr950_Scope@odata.bind` removed from Apparatus
2. `cr950_Project@odata.bind` removed from Apparatus (denormalized)

---

## 🔀 Complete V1 vs V2 Comparison

| Action | V1 | V2 |
|--------|----|----|
| Create Client | `cr950_name` | `cr950_client_name` |
| Create Site | Multiple `cr950_*` fields | `cr950_site_*` fields |
| Create Project entity | `cr950_projectses` | `cr950_projects` |
| Create Project fields | `cr950_job_number` | `cr950_project_number` |
| Create Scope entity | `cr950_projectscopes` | `cr950_scopes` |
| Create ScopeLaborDetail entity | `cr950_scopelabordetailses` | `cr950_scopelabordetails` |
| Create ScopeLaborDetail fields | `cr950_*total` | `cr950_scopelabor_*_total` |
| **Create Task** | ❌ Not present | ✅ **NEW ACTION** |
| Apparatus link | `cr950_Scope@odata.bind` | `cr950_apparatus_task@odata.bind` |
| Apparatus Project link | `cr950_Project@odata.bind` | ❌ **REMOVED** |

---

## ✅ Implementation Checklist

### Pre-Implementation
- [ ] Confirm all V2 tables exist in new environment
- [ ] Verify field names match V2 schema CSVs
- [ ] Test connection to org284447bd.crm.dynamics.com

### Flow Rebuild (Recommended: Rebuild vs Patch)
- [ ] Create new flow from scratch using V2 spec
- [ ] Configure SharePoint trigger
- [ ] Implement Parse JSON with correct schema
- [ ] Create Client with `cr950_client_name`
- [ ] Create Site with `cr950_site_*` fields
- [ ] Create Project with `cr950_projects` entity
- [ ] Create Scope loop with:
  - [ ] Create Scope (`cr950_scopes`)
  - [ ] Create ScopeLaborDetail (`cr950_scopelabordetails`)
  - [ ] 🆕 Create Default Task (`cr950_tasks`)
  - [ ] Create Apparatus with Task link

### Testing
- [ ] Create test JSON file with sample data
- [ ] Run flow and verify all records created
- [ ] Check Client → Site → Project hierarchy
- [ ] Check Scope → Task → Apparatus hierarchy
- [ ] Verify ScopeLaborDetail linked to Scope
- [ ] Confirm no orphaned records

---

## ❌ Common Migration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Resource not found" on Create Project | Wrong entity name | Use `cr950_projects` not `cr950_projectses` |
| "Resource not found" on Create Scope | Wrong entity name | Use `cr950_scopes` not `cr950_projectscopes` |
| Apparatus creation fails | Missing Task | Ensure Task created before Apparatus loop |
| Field not found | Old field names | Update all fields to V2 naming convention |
| Lookup binding fails | Wrong entity in binding | Update all OData bindings to V2 entity names |

---

## 📁 Related Files

| Item | Location |
|------|----------|
| V1 Flow JSON | `Solution_Exports/v1.5.1.3/Workflows/JSONImport-*.json` |
| Schema Audit | `Documentation/FLOW_SCHEMA_AUDIT_DEC2025.md` |
| V1 Estimator Flow Spec | `Documentation/06_Implementation_Guides/ESTIMATOR_FLOW_SPECIFICATION.md` |
| All V2 Schemas | `CSV_Templates/Schema/*.csv` |

---

## 💡 Recommendation: Rebuild vs Patch

Given the extensive changes required (entity renames, field renames, AND architecture change with Task insertion), **we recommend rebuilding this flow from scratch** rather than attempting to patch the V1 flow.

**Reasons:**
1. More changes than unchanged elements
2. Architecture change requires new action (Create Task)
3. Cleaner maintenance going forward
4. Easier to test and validate

**Estimated Effort:**
- Patch V1: 2-3 hours (high error risk)
- Rebuild V2: 1-2 hours (cleaner result)

---

**Document Owner:** Jason Swenson  
**Created:** December 2, 2025  
**Status:** Ready for implementation
