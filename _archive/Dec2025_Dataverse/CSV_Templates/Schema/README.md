# Dataverse Schema Definitions

**Purpose**: Source of truth for table schema. Used by PowerShell scripts to create/recreate tables.

**Convention**: `cr950_{tablename}_{fieldpurpose}`

## Files

| Order | File | Table LogicalName | EntitySetName |
|-------|------|-------------------|---------------|
| 1 | 01_Client_Schema.csv | cr950_client | cr950_clients |
| 2 | 02_Site_Schema.csv | cr950_site | cr950_sites |
| 3 | 03_Project_Schema.csv | cr950_project | cr950_projects |
| 4 | 04_Scope_Schema.csv | cr950_scope | cr950_scopes |
| 5 | 05_Task_Schema.csv | cr950_task | cr950_tasks |
| 6 | 06_Apparatus_Schema.csv | cr950_apparatus | cr950_apparatuses |
| 7 | 07_ScopeLaborDetail_Schema.csv | cr950_scopelabordetail | cr950_scopelabordetails |

## CSV Column Reference

| Column | Description | Example |
|--------|-------------|---------|
| FieldLogicalName | API name (lowercase, underscores) | cr950_client_name |
| DisplayName | UI label | Client Name |
| Type | String, Integer, Decimal, Currency, DateTime, Boolean, Memo, Lookup | String |
| MaxLength | For String/Memo types | 200 |
| Required | true/false | true |
| Description | Help text | The official client company name |
| LookupTarget | For Lookup types - target table | cr950_client |

## Build Order

Tables must be created in order (1-7) because of lookup dependencies:
- Sites lookup to Clients
- Projects lookup to Sites (and optionally Clients)
- Scopes lookup to Projects
- Tasks lookup to Scopes
- Apparatus lookup to Tasks
- ScopeLaborDetail lookup to Scopes

## Usage

```powershell
# Create all tables from schema
.\Create-Tables-From-Schema.ps1 -SchemaFolder "C:\RESA_Power_Build\CSV_Templates\Schema"

# Create single table
.\Create-Tables-From-Schema.ps1 -SchemaFile "01_Client_Schema.csv"
```

## Migration Strategy

1. Export existing data via web app (JSON format)
2. Delete existing tables (Dev environment only!)
3. Run creation script
4. Re-import data via web app

---
*Created: 2024-11-30*
*Last Updated: 2024-11-30*
