# Dataverse Table Name Reference

## Environment: org7bdbc942.crm.dynamics.com (Developer)
**Last Updated:** December 2, 2025

| Logical Name | EntitySet Name (API) | Display Name |
|--------------|---------------------|--------------|
| `cr950_apparatus` | `cr950_apparatuses` | Apparatus |
| `cr950_client` | `cr950_clients` | Client |
| `cr950_estimator` | `cr950_estimators` | Estimator |
| `cr950_location` | `cr950_locations` | Location |
| `cr950_project` | `cr950_projects` | Project |
| `cr950_scope` | `cr950_scopes` | Scope |
| `cr950_scopelabordetail` | `cr950_scopelabordetails` | Scope Labor Detail |
| `cr950_site` | `cr950_sites` | Site |
| `cr950_task` | `cr950_tasks` | Task |

## Key Fields by Table

### cr950_clients
- `cr950_clientid` - Primary key (GUID)
- `cr950_name` - Client name (text)

### cr950_sites
- `cr950_siteid` - Primary key (GUID)
- `cr950_name` - Site name
- `cr950_address`, `cr950_city`, `cr950_state`, `cr950_zip`
- `cr950_sitecontactemail`
- `_cr950_client_value` - Lookup to Client

### cr950_projects
- `cr950_projectid` - Primary key (GUID)
- `cr950_project_name` - Project name
- `cr950_job_number` - Job number
- `_cr950_client_value` - Lookup to Client
- `_cr950_site_value` - Lookup to Site

### cr950_scopes
- `cr950_scopeid` - Primary key (GUID)
- `cr950_scope_name` - Scope name
- `cr950_testing_standard` - Choice (ATS=957080000, MTS=957080001)
- `_cr950_project_value` - Lookup to Project

### cr950_scopelabordetails
- `cr950_scopelabordetailid` - Primary key (GUID)
- `cr950_name` - Display name
- `cr950_total_apparatus_hours` - Total hours
- `cr950_scope_total_value` - Total value ($)
- `cr950_scopemultiplier` - Multiplier
- `cr950_effectivelaborrate` - Effective rate
- `_cr950_scope_id_value` - Lookup to Scope

### cr950_apparatuses
- `cr950_apparatusid` - Primary key (GUID)
- `cr950_apparatus_designation` - Equipment type
- `cr950_labor_hours` - Hours per unit
- `cr950_notes` - Section/notes
- `_cr950_scope_value` - Lookup to Scope
- `_cr950_project_value` - Lookup to Project

### cr950_estimators
- `cr950_estimatorid` - Primary key (GUID)
- `cr950_name` - Display name
- `cr950_projectname` - Project name (text, not lookup)
- `cr950_filename` - Estimator filename
- `cr950_estimator_file_url` - SharePoint URL
- `cr950_currentrevision` - Revision number
- `cr950_estimatedate` - Date
- `cr950_status` - Choice
- `_cr950_clientid_value` - Lookup to Client

## Usage Notes

1. **Use EntitySet Name for API queries:**
   ```
   GET /api/data/v9.2/cr950_projects
   ```

2. **Lookup bindings use EntitySet Name:**
   ```json
   {
     "cr950_client@odata.bind": "/cr950_clients(guid-here)"
   }
   ```

3. **Filter on lookup values use _value suffix:**
   ```
   $filter=_cr950_client_value eq 'guid-here'
   ```

## Deprecated Table Names (OLD Environment)

These were used in org99cd6c6e/org284447bd - DO NOT USE:
- ~~cr950_projectses~~ → now `cr950_projects`
- ~~cr950_projectscopes~~ → now `cr950_scopes`  
- ~~cr950_scopelabordetailses~~ → now `cr950_scopelabordetails`
- ~~cr950_taskses~~ → now `cr950_tasks`
