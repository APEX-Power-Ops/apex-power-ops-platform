# RESA Power Dataverse Master Schema Reference

> **AUTHORITY DOCUMENT** - All development MUST reference this schema.  
> **Last Verified**: December 3, 2025  
> **Environment**: org7bdbc942.crm.dynamics.com (Developer)  
> **Solution**: RESA_Power_Build_V2 (v1.0.0.5)

---

## ⚠️ CRITICAL RULES

1. **NEVER guess entity or field names** - Always use this document
2. **EntitySetName ≠ LogicalName** - API calls use EntitySetName (plural)
3. **Lookup bindings use EntitySetName** - e.g., `/cr950_clients(guid)`
4. **All lookups return `_fieldname_value`** - underscore prefix and suffix

---

## Quick Reference Table

| Table | LogicalName | EntitySetName | PrimaryKey | NameField |
|-------|-------------|---------------|------------|-----------|
| Client | cr950_client | **cr950_clients** | cr950_clientid | cr950_clientname |
| Site | cr950_site | **cr950_sites** | cr950_siteid | cr950_sitename |
| Location | cr950_location | **cr950_locations** | cr950_locationid | cr950_location_name |
| Project | cr950_project | **cr950_projects** | cr950_projectid | cr950_projectname |
| Scope | cr950_scope | **cr950_scopes** | cr950_scopeid | cr950_scopename |
| Task | cr950_task | **cr950_tasks** | cr950_taskid | cr950_taskname |
| Apparatus | cr950_apparatus | **cr950_apparatuses** | cr950_apparatusid | cr950_apparatusname |
| Estimator | cr950_estimator | **cr950_estimators** | cr950_estimatorid | cr950_estimator_name |
| Scope Labor Detail | cr950_scopelabordetail | **cr950_scopelabordetails** | cr950_scopelabordetailid | cr950_scopelaborname |
| Apparatus Revenue | cr950_apparatusrevenue | **cr950_apparatusrevenues** | cr950_apparatusrevenueid | cr950_name |
| Scope Financial Summary | cr950_scopefinancialsummary | **cr950_scopefinancialsummaries** | cr950_scopefinancialsummaryid | cr950_name |
| Project Financial Summary | cr950_projectfinancialsummary | **cr950_projectfinancialsummaries** | cr950_projectfinancialsummaryid | cr950_name |

---

## Lookup Binding Syntax

When creating/updating records with lookups, use this EXACT syntax:

```javascript
// Format: "SchemaName@odata.bind": "/EntitySetName(GUID)"

// Site → Client
"cr950_SiteClient@odata.bind": "/cr950_clients(${clientId})"

// Project → Site
"cr950_ProjectSite@odata.bind": "/cr950_sites(${siteId})"

// Project → Client  
"cr950_ProjectClient@odata.bind": "/cr950_clients(${clientId})"

// Scope → Project
"cr950_ScopeProject@odata.bind": "/cr950_projects(${projectId})"

// Scope → Site
"cr950_scope_siteid@odata.bind": "/cr950_sites(${siteId})"

// Scope → Client
"cr950_scope_clientid@odata.bind": "/cr950_clients(${clientId})"

// Task → Scope
"cr950_TaskScope@odata.bind": "/cr950_scopes(${scopeId})"

// Apparatus → Scope
"cr950_apparatus_scopeid@odata.bind": "/cr950_scopes(${scopeId})"

// Apparatus → Task
"cr950_apparatustask@odata.bind": "/cr950_tasks(${taskId})"

// Scope Labor Detail → Scope
"cr950_scopelaborscope@odata.bind": "/cr950_scopes(${scopeId})"
```

### Reading Lookup Values

When READING records, lookup values are returned with underscore format:
```javascript
// Returns: _cr950_scopeproject_value (GUID string)
// NOT: cr950_scopeproject or cr950_ScopeProject
```

---

## Entity Details

### 1. Client (cr950_client)

**EntitySetName**: `cr950_clients`  
**PrimaryKey**: `cr950_clientid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_clientname | string | Client name (primary) |
| Code | cr950_clientcode | string | Short code |
| Active | cr950_clientactive | boolean | Is active |
| Address | cr950_clientaddress | string | Street address |
| City | cr950_clientcity | string | City |
| State | cr950_clientstate | string | State |
| Zip | cr950_clientzip | string | Zip code |
| Country | cr950_clientcountry | string | Country |
| Phone | cr950_clientphone | string | Phone number |
| Email | cr950_clientemail | string | Email |
| Website | cr950_clientwebsite | string | Website URL |
| Notes | cr950_clientnotes | string | Notes |

---

### 2. Site (cr950_site)

**EntitySetName**: `cr950_sites`  
**PrimaryKey**: `cr950_siteid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_sitename | string | Site name (primary) |
| Client | cr950_siteclient | lookup | → cr950_client |
| Code | cr950_sitecode | string | Short code |
| Active | cr950_siteactive | boolean | Is active |
| Address | cr950_siteaddress | string | Street address |
| City | cr950_sitecity | string | City |
| State | cr950_sitestate | string | State |
| Zip | cr950_sitezip | string | Zip code |
| Country | cr950_sitecountry | string | Country |
| Contact Name | cr950_sitecontactname | string | Contact person |
| Contact Phone | cr950_sitecontactphone | string | Contact phone |
| Contact Email | cr950_sitecontactemail | string | Contact email |
| Notes | cr950_sitenotes | string | Notes |

**Lookup Binding**: `"cr950_SiteClient@odata.bind": "/cr950_clients(guid)"`

---

### 3. Location (cr950_location)

**EntitySetName**: `cr950_locations`  
**PrimaryKey**: `cr950_locationid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_location_name | string | Location name (primary) |
| Abbreviation | cr950_location_abbreviation | string | Short abbreviation |
| Code | cr950_location_code | string | Code |
| Active | cr950_location_active | boolean | Is active |
| Region | cr950_location_region | string | Region |
| Manager | cr950_location_manager | string | Manager name |
| Address | cr950_location_address | string | Address |
| Sort Order | cr950_location_sortorder | int | Display order |
| Notes | cr950_location_notes | string | Notes |

---

### 4. Project (cr950_project)

**EntitySetName**: `cr950_projects`  
**PrimaryKey**: `cr950_projectid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_projectname | string | Project name (primary) |
| Number | cr950_projectnumber | string | Project number |
| Site | cr950_projectsite | lookup | → cr950_site |
| Client | cr950_projectclient | lookup | → cr950_client |
| Location | cr950_project_locationid | lookup | → cr950_location |
| Active | cr950_projectactive | boolean | Is active |
| Status | cr950_projectstatus | optionset | Project status |
| Lead | cr950_project_lead | string | Project lead name |
| Business Unit | cr950_project_business_unit | string | Business unit |
| Start Date | cr950_projectstartdate | datetime | Start date |
| End Date | cr950_projectenddate | datetime | End date |
| PO Number | cr950_projectponumber | string | Purchase order |
| Contract Value | cr950_projectcontractvalue | currency | Contract value |
| Quote Date | cr950_project_quote_date | datetime | Quote date |
| Quote Revision | cr950_project_quote_revision | string | Quote revision |
| Description | cr950_projectdescription | string | Description |
| Notes | cr950_projectnotes | string | Notes |

**Lookup Bindings**:
```javascript
"cr950_ProjectSite@odata.bind": "/cr950_sites(guid)"
"cr950_ProjectClient@odata.bind": "/cr950_clients(guid)"
"cr950_project_locationid@odata.bind": "/cr950_locations(guid)"
```

---

### 5. Scope (cr950_scope)

**EntitySetName**: `cr950_scopes`  
**PrimaryKey**: `cr950_scopeid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_scopename | string | Scope name (primary) |
| Number | cr950_scopenumber | string | Scope number |
| Project | cr950_scopeproject | lookup | → cr950_project |
| Client | cr950_scope_clientid | lookup | → cr950_client |
| Site | cr950_scope_siteid | lookup | → cr950_site |
| Type | cr950_scopetype | string | Scope type (ATS, etc.) |
| Active | cr950_scopeactive | boolean | Is active |
| Status | cr950_scopestatus | optionset | Status |
| Due Date | cr950_scopeduedate | datetime | Due date |
| Labor Total | cr950_scopelabortotal | currency | Labor total |
| Material Total | cr950_scopematerialtotal | currency | Material total |
| Revenue Total | cr950_scoperevenuetotal | currency | Revenue total |
| Margin Percent | cr950_scopemarginpercent | decimal | Margin % |
| Description | cr950_scopedescription | string | Description |
| Notes | cr950_scopenotes | string | Notes |

**Lookup Bindings**:
```javascript
"cr950_ScopeProject@odata.bind": "/cr950_projects(guid)"
"cr950_scope_clientid@odata.bind": "/cr950_clients(guid)"
"cr950_scope_siteid@odata.bind": "/cr950_sites(guid)"
```

---

### 6. Task (cr950_task)

**EntitySetName**: `cr950_tasks`  
**PrimaryKey**: `cr950_taskid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_taskname | string | Task name (primary) |
| Number | cr950_tasknumber | string | Task number |
| Scope | cr950_taskscope | lookup | → cr950_scope |
| Client | cr950_task_clientid | lookup | → cr950_client |
| Site | cr950_task_siteid | lookup | → cr950_site |
| Project | cr950_task_projectid | lookup | → cr950_project |
| Type | cr950_tasktype | string | Task type |
| Active | cr950_taskactive | boolean | Is active |
| Status | cr950_taskstatus | optionset | Status |
| Sequence | cr950_tasksequence | int | Display order |
| Quantity | cr950_taskquantity | int | Quantity |
| Unit Price | cr950_taskunitprice | currency | Unit price |
| Labor Hours | cr950_tasklaborhours | decimal | Labor hours |
| Labor Rate | cr950_tasklaborrate | currency | Labor rate |
| Labor Total | cr950_tasklabortotal | currency | Labor total |
| Task Total | cr950_tasktotal | currency | Total amount |
| Assigned To | cr950_task_assigned_to | string | Assigned person |
| Notes | cr950_tasknotes | string | Notes |

**Lookup Bindings**:
```javascript
"cr950_TaskScope@odata.bind": "/cr950_scopes(guid)"
"cr950_task_clientid@odata.bind": "/cr950_clients(guid)"
"cr950_task_siteid@odata.bind": "/cr950_sites(guid)"
"cr950_task_projectid@odata.bind": "/cr950_projects(guid)"
```

---

### 7. Apparatus (cr950_apparatus)

**EntitySetName**: `cr950_apparatuses`  
**PrimaryKey**: `cr950_apparatusid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_apparatusname | string | Apparatus name (primary) |
| Scope | cr950_apparatus_scopeid | lookup | → cr950_scope |
| Task | cr950_apparatustask | lookup | → cr950_task |
| Client | cr950_apparatus_clientid | lookup | → cr950_client |
| Site | cr950_apparatus_siteid | lookup | → cr950_site |
| Project | cr950_apparatus_projectid | lookup | → cr950_project |
| Type | cr950_apparatustype | string | Equipment type |
| Active | cr950_apparatusactive | boolean | Is active |
| Status | cr950_apparatusstatus | optionset | Status |
| Manufacturer | cr950_apparatusmanufacturer | string | Manufacturer |
| Model | cr950_apparatusmodel | string | Model |
| Serial | cr950_apparatusserial | string | Serial number |
| Location | cr950_apparatuslocation | string | Location in facility |
| Section | cr950_apparatussection | string | Section |
| Row | cr950_apparatusrow | string | Row |
| Voltage | cr950_apparatusvoltage | string | Voltage |
| Amperage | cr950_apparatusamperage | string | Amperage |
| Quantity | cr950_apparatusquantity | int | Quantity |
| Hours Per Unit | cr950_apparatushoursperunit | decimal | Hours per unit |
| Total Hours | cr950_apparatustotalhours | decimal | Total hours |
| Revenue | cr950_apparatusrevenue | currency | Revenue amount |
| Sequence | cr950_apparatussequence | int | Display order |
| Result | cr950_apparatusresult | string | Test result |
| Test Date | cr950_apparatustestdate | datetime | Test date |
| Date Completed | cr950_datecompleted | datetime | Completion date |
| Completion Status | cr950_completion_status | optionset | Completion status |
| Delay Hours | cr950_delayhours | decimal | Delay hours |
| Assigned To | cr950_apparatus_assigned_to | string | Assigned person |
| Notes | cr950_apparatusnotes | string | Notes |

**Lookup Bindings**:
```javascript
"cr950_apparatus_scopeid@odata.bind": "/cr950_scopes(guid)"
"cr950_apparatustask@odata.bind": "/cr950_tasks(guid)"
"cr950_apparatus_clientid@odata.bind": "/cr950_clients(guid)"
"cr950_apparatus_siteid@odata.bind": "/cr950_sites(guid)"
"cr950_apparatus_projectid@odata.bind": "/cr950_projects(guid)"
```

---

### 8. Estimator (cr950_estimator)

**EntitySetName**: `cr950_estimators`  
**PrimaryKey**: `cr950_estimatorid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_estimator_name | string | Estimator name |
| Project Name | cr950_estimator_projectname | string | Project name |
| Client | cr950_estimator_clientid | lookup | → cr950_client |
| Project | cr950_estimator_projectid | lookup | → cr950_project |
| Location | cr950_estimator_locationid | lookup | → cr950_location |
| File Name | cr950_estimator_filename | string | Excel filename |
| File URL | cr950_estimator_fileurl | string | SharePoint URL |
| Estimate Date | cr950_estimator_estimatedate | datetime | Estimate date |
| Extracted At | cr950_estimator_extractedat | datetime | Extraction time |
| Last Modified | cr950_estimator_lastmodified | datetime | Last modified |
| Current Revision | cr950_estimator_currentrevision | int | Revision number |
| Scope Count | cr950_estimator_scopecount | int | Number of scopes |
| Total Amount | cr950_estimator_totalamount | currency | Total amount |
| Scope JSON | cr950_estimator_scopejson | string | JSON data |
| Converted | cr950_estimator_convertedtoproject | boolean | Converted flag |
| Converted Date | cr950_estimator_converteddate | datetime | Conversion date |
| Notes | cr950_estimator_notes | string | Notes |

**Lookup Bindings**:
```javascript
"cr950_estimator_clientid@odata.bind": "/cr950_clients(guid)"
"cr950_estimator_projectid@odata.bind": "/cr950_projects(guid)"
"cr950_estimator_locationid@odata.bind": "/cr950_locations(guid)"
```

---

### 9. Scope Labor Detail (cr950_scopelabordetail)

**EntitySetName**: `cr950_scopelabordetails`  
**PrimaryKey**: `cr950_scopelabordetailid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_scopelaborname | string | Labor detail name |
| Scope | cr950_scopelaborscope | lookup | → cr950_scope |
| Active | cr950_scopelaboractive | boolean | Is active |
| Source | cr950_scopelaborsource | string | Labor source |
| Total Hours | cr950_scopelabortotalhours | decimal | Total hours |
| Multiplier | cr950_scopelabormultiplier | decimal | Rate multiplier |
| Effective Rate | cr950_scopelaboreffectiverate | currency | Effective rate |
| Onsite Rate | cr950_scopelaboronsiterate | currency | Onsite rate |
| Onsite Total | cr950_scopelaboronsitetotal | currency | Onsite total |
| Offsite Rate | cr950_scopelaboroffsiterate | currency | Offsite rate |
| Offsite Total | cr950_scopelaboroffsitetotal | currency | Offsite total |
| Travel Rate | cr950_scopelabortravelrate | currency | Travel rate |
| Travel Total | cr950_scopelabortraveltotal | currency | Travel total |
| Outside Rate | cr950_scopelaboroutsiderate | currency | Outside rate |
| Outside Total | cr950_scopelaboroutsidetotal | currency | Outside total |
| Sum of Rates | cr950_scopelaborsumofrates | currency | Sum of rates |
| Quoted Amount | cr950_scopelaborquotedamount | currency | Quoted amount |
| Adjusted | cr950_scopelaboradjusted | currency | Adjusted amount |
| Not Adjusted | cr950_scopelabornotadjusted | currency | Unadjusted |
| Notes | cr950_scopelabornotes | string | Notes |

**Lookup Binding**:
```javascript
"cr950_scopelaborscope@odata.bind": "/cr950_scopes(guid)"
```

---

### 10. Apparatus Revenue (cr950_apparatusrevenue)

**EntitySetName**: `cr950_apparatusrevenues`  
**PrimaryKey**: `cr950_apparatusrevenueid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_name | string | Revenue record name |
| Planned Hours | cr950_plannedhours | decimal | Planned hours |
| Actual Hours | cr950_actualhours | decimal | Actual hours |
| Delay Hours | cr950_delayhours | decimal | Delay hours |
| Labor Rate | cr950_laborrateapplied | currency | Applied rate |
| Revenue Amount | cr950_revenueamount | currency | Revenue amount |
| Revenue Status | cr950_revenuestatus | optionset | Status |
| Recognition Date | cr950_recognitiondate | datetime | Recognition date |

---

### 11. Scope Financial Summary (cr950_scopefinancialsummary)

**EntitySetName**: `cr950_scopefinancialsummaries`  
**PrimaryKey**: `cr950_scopefinancialsummaryid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_name | string | Summary name |
| Apparatus Revenue Count | cr950_apparatusrevenuecount | int | Revenue count |
| Estimated Revenue | cr950_estimatedrevenue | currency | Estimated |
| Total Revenue Recognized | cr950_totalrevenuerecognized | currency | Recognized |
| Total Revenue Pending | cr950_totalrevenuepending | currency | Pending |
| Revenue Variance | cr950_revenuevariance | currency | Variance |
| Total Planned Hours | cr950_totalplannedhours | decimal | Planned hours |
| Total Actual Hours | cr950_totalactualhours | decimal | Actual hours |
| Latest Revenue Date | cr950_latestrevenue_date | datetime | Latest date |

---

### 12. Project Financial Summary (cr950_projectfinancialsummary)

**EntitySetName**: `cr950_projectfinancialsummaries`  
**PrimaryKey**: `cr950_projectfinancialsummaryid`

| Field | LogicalName | Type | Description |
|-------|-------------|------|-------------|
| Name | cr950_name | string | Summary name |
| Scope Count | cr950_scopecount | int | Scope count |
| Apparatus Revenue Count | cr950_apparatusrevenuecount | int | Revenue count |
| Total Estimated Revenue | cr950_totalestimatedrevenue | currency | Estimated |
| Total Revenue Recognized | cr950_totalrevenuerecognized | currency | Recognized |
| Total Revenue Pending | cr950_totalrevenuepending | currency | Pending |
| Total Variance | cr950_totalvariance | currency | Variance |
| Total Project Hours | cr950_totalprojecthours | decimal | Total hours |
| Latest Revenue Date | cr950_latestrevenue_date | datetime | Latest date |

---

## API Query Examples

### Get all projects with client/site expansion
```
cr950_projects?$expand=cr950_ProjectClient($select=cr950_clientname),cr950_ProjectSite($select=cr950_sitename)&$orderby=createdon desc
```

### Get scopes for a project
```
cr950_scopes?$filter=_cr950_scopeproject_value eq 'GUID'&$orderby=cr950_scopenumber
```

### Get apparatus for a scope
```
cr950_apparatuses?$filter=_cr950_apparatus_scopeid_value eq 'GUID'&$orderby=cr950_apparatussequence
```

### Get tasks for a scope
```
cr950_tasks?$filter=_cr950_taskscope_value eq 'GUID'&$orderby=cr950_tasksequence
```

---

## Validation Queries

Run these to verify schema accuracy:

```powershell
# Test each EntitySet
$entities = @('cr950_clients', 'cr950_sites', 'cr950_locations', 'cr950_projects', 
              'cr950_scopes', 'cr950_tasks', 'cr950_apparatuses', 'cr950_estimators',
              'cr950_scopelabordetails', 'cr950_apparatusrevenues', 
              'cr950_scopefinancialsummaries', 'cr950_projectfinancialsummaries')

foreach ($entity in $entities) {
    $response = Invoke-RestMethod -Uri "$env:DATAVERSE_URL/api/data/v9.2/$entity?`$top=1" -Headers @{Authorization = "Bearer $token"}
    Write-Host "$entity : OK" -ForegroundColor Green
}
```

---

## Common Mistakes to Avoid

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| `cr950_projectses` | `cr950_projects` |
| `cr950_projectsid` | `cr950_projectid` |
| `cr950_scopeproject` (in filter) | `_cr950_scopeproject_value` |
| `"cr950_scopeproject@odata.bind"` | `"cr950_ScopeProject@odata.bind"` |
| `/cr950_project(guid)` | `/cr950_projects(guid)` |

---

## Version History

| Date | Change | Verified By |
|------|--------|-------------|
| 2025-12-03 | Initial creation from solution v1.0.0.5 | Claude/Copilot |

