# RESA Power Project - Copilot Instructions

## Project Context
This is a Dataverse/Power Platform project for RESA Power electrical testing company.
- **Environment**: org99cd6c6e.crm.dynamics.com (RESA-Dev)
- **Solution**: RESAPowerProjectTracker v1.5.1.0
- **Repository**: RESA-Power-Project-Management on GitHub

## Critical Files to Read First
1. `PROJECT_CONTEXT.json` - Current state, next tasks, critical facts
2. `Documentation/00_START_HERE/SESSION_RESUME_CHECKLIST.md` - Session startup guide

## Reusable Templates (USE THESE!)
Location: `Scripts/PowerShell/Templates/`

| Template | Purpose |
|----------|---------|
| `Dataverse-TableDiscovery.ps1` | Discover correct table names, EntitySetNames |
| `Dataverse-FieldOperations.ps1` | Add/query Dataverse fields |
| `Dataverse-Functions.ps1` | Record CRUD operations (parent folder) |

### How to Use Templates
```powershell
# Load a template
. "C:\RESA_Power_Build\Scripts\PowerShell\Templates\Dataverse-TableDiscovery.ps1"
Connect-DataverseAPI
Get-AllCustomTables
```

## MCP Server Configuration
- **Location**: `MCP_Servers/resa-dataverse-mcp/`
- **Credentials**: `.env` file (uses Azure AD app registration)
- **Table Reference**: `TABLE_NAMES_REFERENCE.md`

## Key Table Names (EntitySetName for API)
```
cr950_clients          - Clients
cr950_sites            - Sites  
cr950_projectses       - Projects
cr950_projectscopes    - Scopes
cr950_apparatuses      - Apparatus
cr950_estimators       - Estimators
```

## Working Folder
`Working/` contains code view JSON from Power Automate flows - use as reference patterns.

## Session Protocol
- **On Start**: Read `PROJECT_CONTEXT.json`, check Templates folder
- **On End**: Update `PROJECT_CONTEXT.json`, commit to Git, create session summary if significant work
