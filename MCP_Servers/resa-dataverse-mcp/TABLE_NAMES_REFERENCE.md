# Dataverse Table Name Reference

| Logical Name (Metadata) | EntitySet Name (API Queries) | Display Name |
|-------------------------|------------------------------|--------------|
| `cr950_apparatus` | `cr950_apparatuses` | Apparatus |
| `cr950_apparatusrevenue` | `cr950_apparatusrevenues` | Apparatus Revenue |
| `cr950_apparatussubmission` | `cr950_apparatussubmissions` | Apparatus Submission |
| `cr950_apparatustestchecklist` | `cr950_apparatustestchecklists` | Apparatus Test Checklist |
| `cr950_apparatustypemaster` | `cr950_apparatustypemasters` | Apparatus Type Master |
| `cr950_businessunit` | `cr950_businessunits` | Business Unit |
| `cr950_client` | `cr950_clients` | Client |
| `cr950_employee` | `cr950_employees` | Employee |
| `cr950_equipment` | `cr950_equipments` | Equipment |
| `cr950_estimator` | `cr950_estimators` | Estimator |
| `cr950_netatesttemplate` | `cr950_netatesttemplates` | NETA Test Template |
| `cr950_projectdocument` | `cr950_projectdocuments` | Project Document |
| `cr950_projectfinancialsummary` | `cr950_projectfinancialsummaries` | Project Financial Summary |
| `cr950_projects` | `cr950_projectses` | Projects |
| `cr950_projectscope` | `cr950_projectscopes` | Project Scope |
| `cr950_quote` | `cr950_quotes` | Quote |
| `cr950_resourceassignment` | `cr950_resourceassignments` | Resource Assignment |
| `cr950_scopefinancialsummary` | `cr950_scopefinancialsummaries` | Scope Financial Summary |
| `cr950_scopelabordetails` | `cr950_scopelabordetailses` | Scope Labor Detail |
| `cr950_site` | `cr950_sites` | Site |
| `cr950_tasks` | `cr950_taskses` | Tasks |

**Usage Notes:**
- Use **LogicalName** in metadata API calls (EntityDefinitions)
- Use **EntitySetName** in record queries (/api/data/v9.2/{EntitySetName})
- Power Automate 'List rows' action uses EntitySetName
