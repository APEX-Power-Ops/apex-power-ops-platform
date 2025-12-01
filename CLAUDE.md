# RESA Power Project - Claude Instructions

## Quick Start
1. Read `PROJECT_CONTEXT.json` for current state and next tasks
2. Check `Scripts/PowerShell/Templates/` for reusable scripts
3. Use MCP tools when available (Dataverse, GitHub, Filesystem)

## Project Overview
- **What**: Dataverse/Power Platform project management system for electrical testing
- **Who**: RESA Power LLC (multi-location company)
- **Environment**: org99cd6c6e.crm.dynamics.com (RESA-Dev)
- **Solution Version**: v1.5.1.0

## Reusable Templates - ALWAYS CHECK FIRST
Location: `Scripts/PowerShell/Templates/`

```powershell
# Discover table names
. "C:\RESA_Power_Build\Scripts\PowerShell\Templates\Dataverse-TableDiscovery.ps1"
Connect-DataverseAPI
Get-AllCustomTables

# Field operations  
. "C:\RESA_Power_Build\Scripts\PowerShell\Templates\Dataverse-FieldOperations.ps1"
Connect-DataverseAPI
Get-DataverseFields -TableName "cr950_projects" -CustomOnly
```

## Correct Table Names (EntitySetName for API queries)
| LogicalName | EntitySetName | Display |
|-------------|---------------|---------|
| cr950_client | cr950_clients | Client |
| cr950_site | cr950_sites | Site |
| cr950_projects | cr950_projectses | Projects |
| cr950_projectscope | cr950_projectscopes | Scope |
| cr950_apparatus | cr950_apparatuses | Apparatus |
| cr950_estimator | cr950_estimators | Estimator |

Full list: `MCP_Servers/resa-dataverse-mcp/TABLE_NAMES_REFERENCE.md`

## MCP Server
- Location: `MCP_Servers/resa-dataverse-mcp/`
- Credentials: `.env` file (Azure AD client credentials)
- Build: `npm run build` in that directory
- Test: `node test-connection.js`

## Key Directories
```
Scripts/PowerShell/Templates/   <- Reusable PowerShell templates
Working/                        <- Power Automate code view JSON samples
Documentation/06_Implementation_Guides/  <- Flow specs and build guides
MCP_Servers/resa-dataverse-mcp/ <- Dataverse MCP server
Reference_Files/Excel/          <- VBA modules, test JSON files
```

## Session Protocol
### On Start
- Read `PROJECT_CONTEXT.json` 
- Check `criticalFacts` array
- Review Templates folder for existing solutions

### On End
- Update `PROJECT_CONTEXT.json` with progress
- Commit changes to Git
- Create session summary if significant work

## Current Architecture (Nov 29, 2025)
```
Excel Estimator → VBA Macro (DataverseExport.bas) → JSON file
JSON file → Power Automate trigger → Dataverse records
```
Office Scripts approach is DEPRECATED - use VBA JSON export.
