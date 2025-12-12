# Projects Table Documentation

**Generated:** 2025-11-24T00:50:45.096Z  
**Table Name:** cr950_projects  
**Display Name:** Projects  
**Primary Key:** cr950_projectsid  
**Created:** 11/22/2025  
**Last Modified:** 11/22/2025

---

## Description

Top-level project container for RESA Power electrical testing projects.

---

## Table Information

**Logical Name:** `cr950_projects`  
**Schema Name:** `cr950_Projects`  
**EntitySetName (for queries):** `cr950_projectses`  
**Primary Key:** `cr950_projectsid`  

---

## Relationships (29)

### Many-to-One (Lookups) - Parent Tables

| Display Name | Logical Name | Related Table | Related Field |
|--------------|--------------|---------------|---------------|
| Client Project | `cr950_client_project` | cr950_client | cr950_clientid |
| Site Project | `cr950_site_project` | cr950_site | cr950_siteid |
| Projects Location Businessunit | `cr950_projects_Location_cr950_businessunit` | cr950_businessunit | cr950_businessunitid |
| Lk Projects Createdby | `lk_cr950_projects_createdby` | systemuser | systemuserid |
| Lk Projects Createdonbehalfby | `lk_cr950_projects_createdonbehalfby` | systemuser | systemuserid |
| Lk Projects Modifiedby | `lk_cr950_projects_modifiedby` | systemuser | systemuserid |
| Lk Projects Modifiedonbehalfby | `lk_cr950_projects_modifiedonbehalfby` | systemuser | systemuserid |
| User Projects | `user_cr950_projects` | systemuser | systemuserid |
| Team Projects | `team_cr950_projects` | team | teamid |
| Owner Projects | `owner_cr950_projects` | owner | ownerid |
| Business Unit Projects | `business_unit_cr950_projects` | businessunit | businessunitid |
| TransactionCurrency Projects | `TransactionCurrency_cr950_Projects` | transactioncurrency | transactioncurrencyid |

**Key Parent Relationships:**
- **Client**: Links to the customer (cr950_client)
- **Site**: Links to the work location (cr950_site)  
- **Business Unit**: Links to RESA location (Phoenix, Las Vegas, Denver, San Diego)

### One-to-Many (Child Records) - Children Tables

**Business Data:**
| Display Name | Logical Name | Related Table | Related Field |
|--------------|--------------|---------------|---------------|
| Projectscope Project Projects | `cr950_projectscope_Project_cr950_projects` | cr950_projectscope | cr950_project |
| Tasks Project Projects | `cr950_tasks_Project_cr950_projects` | cr950_tasks | cr950_project |
| Apparatus Project Projects | `cr950_apparatus_Project_cr950_projects` | cr950_apparatus | cr950_project |
| Apparatusrevenue Project Projects | `cr950_apparatusrevenue_Project_cr950_projects` | cr950_apparatusrevenue | cr950_project |
| Equipment Projects Projects | `cr950_equipment_Projects_cr950_projects` | cr950_equipment | cr950_projects |
| Project Resourceassignment | `cr950_project_resourceassignment` | cr950_resourceassignment | cr950_project |
| Quote Projects Projects | `cr950_quote_Projects_cr950_projects` | cr950_quote | cr950_projects |
| Project Equipment Currentproject | `cr950_project_equipment_currentproject` | cr950_equipment | cr950_currentproject |

**Key Child Relationships:**
- **Project Scopes**: Work breakdown structure (1:N)
- **Tasks**: Task organization under scopes (1:N via scopes)
- **Apparatus**: Individual test items (1:N via tasks)
- **Apparatus Revenue**: Financial records (1:N)
- **Resource Assignments**: Team staffing (1:N)
- **Equipment**: Tools and instruments used (1:N)

**System Data:**
| Relationship | Purpose |
|--------------|---------|
| Projects SyncErrors | Error tracking |
| Projects DuplicateMatchingRecord | Duplicate detection |
| Projects DuplicateBaseRecord | Duplicate detection |
| Projects AsyncOperations | Background operations |
| Projects MailboxTrackingFolders | Email integration |
| Projects UserEntityInstanceDatas | User settings |
| Projects ProcessSession | Workflow tracking |
| Projects BulkDeleteFailures | Bulk operation tracking |
| Projects PrincipalObjectAttributeAccesses | Security tracking |

---

## Hierarchy Structure

```
Projects (Top Level)
├── Project Scopes (Work breakdown)
│   ├── Tasks (Task organization)
│   │   └── Apparatus (Individual items)
│   │       └── Apparatus Revenue (Financial records)
│   └── Scope Labor Detail (Budget & rates)
├── Resource Assignments (Staffing)
├── Equipment (Tools)
└── Quote (Source estimate)
```

---

## Usage Examples

### Query Records

```javascript
// Query all active Projects records
const projects = await query_dataverse(
  "cr950_projectses",  // Note: plural EntitySetName
  null,
  "statecode eq 0",
  10
);
```

### Query with Relationships

```javascript
// Query projects with client and site info
const projectsWithDetails = await query_dataverse(
  "cr950_projectses",
  null,
  "statecode eq 0",
  10
);
// Then fetch related records separately
```

### Create Record

```javascript
// Create new Project
const newProject = await create_record("cr950_projects", {
  cr950_name: "Hospital Upgrade 2025",
  cr950_projectnumber: "PHX-2025-001",
  "cr950_client@odata.bind": "/cr950_clients(client-guid)",
  "cr950_site@odata.bind": "/cr950_sites(site-guid)",
  "cr950_location@odata.bind": "/cr950_businessunits(location-guid)"
});
```

### Update Record

```javascript
// Update Project
await update_record("cr950_projects", projectId, {
  cr950_targetcompletion: "2025-12-31",
  cr950_projectstatus: 100000001  // In Progress
});
```

---

## Rollup Fields (Added in v1.5.0.0)

**Date Tracking Rollups (6 fields):**

| Field Name | Type | Source | Function |
|------------|------|--------|----------|
| `cr950_earliestanticipatedstart` | Rollup | Scopes | MIN(Anticipated Start) |
| `cr950_latestanticipatedstart` | Rollup | Scopes | MAX(Anticipated Start) |
| `cr950_earliestactualstart` | Rollup | Scopes | MIN(Actual Start) |
| `cr950_latestactualstart` | Rollup | Scopes | MAX(Actual Start) |
| `cr950_earliestcompletiondate` | Rollup | Scopes | MIN(Completion Date) |
| `cr950_latestcompletiondate` | Rollup | Scopes | MAX(Completion Date) |

**Purpose:** Provide project-level visibility into schedule across all scopes.

**Calculation:** Aggregates date values from all child Project Scope records.

---

## Notes

**Known Issue:** Field metadata shows 0 fields in automated documentation. This is likely a permissions issue with the metadata API. Fields exist and are functional in the actual Dataverse environment.

**For Complete Field List:** Reference the MASTER_BUILD_SPECIFICATION.md or Power Apps maker portal.

**Rollup Field Details:** See [SOLUTION_v1.5.0.0_AUDIT_REPORT.md](../03_Progress_Tracking/SOLUTION_v1.5.0.0_AUDIT_REPORT.md) for complete rollup field verification.

---

**Documentation Generator:** resa-docs-mcp v1.0.0  
**Environment:** org99cd6c6e.crm.dynamics.com  
**Status:** ✅ Table Verified Operational  
**Version:** v1.5.0.0 (includes 6 date tracking rollup fields)
