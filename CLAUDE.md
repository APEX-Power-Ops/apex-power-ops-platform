# RESA Power Project - Claude Instructions

## START HERE
**Primary Reference**: `WORKSPACE_SYSTEM.md` - Single source of truth
**Task List**: `COORDINATED_TASK_LIST.md` - Shared between VS Code & Desktop Claude

## Quick Start
1. Read `WORKSPACE_SYSTEM.md` for environment and credentials
2. Read `COORDINATED_TASK_LIST.md` for current tasks
3. Check `Working/DESKTOP_CLAUDE_FINDINGS.md` for Desktop Claude updates

## Project Overview
- **What**: Dataverse/Power Platform project management system for electrical testing
- **Who**: RESA Power LLC (multi-location company)
- **Environment**: `org284447bd.crm.dynamics.com` (CORRECT)
- **Solution**: `RESA_Power_Build_V2` v1.0.0.1

**WRONG - DO NOT USE**: `org99cd6c6e.crm.dynamics.com` (old/incorrect)

## Connection References (Power Platform)
| Name | Type |
|------|------|
| `cr950_sharedsharepointonline_a9dba` | SharePoint |
| `new_sharedcommondataserviceforapps_f7a26` | Dataverse |

## Correct Table Names (EntitySetName for API queries)
| LogicalName | EntitySetName | Display |
|-------------|---------------|---------|
| cr950_client | cr950_clients | Client |
| cr950_site | cr950_sites | Site |
| cr950_location | cr950_locations | Location |
| cr950_projects | cr950_projectses | Projects |
| cr950_projectscope | cr950_projectscopes | Scope |
| cr950_apparatus | cr950_apparatuses | Apparatus |
| cr950_estimator | cr950_estimators | Estimator |

## Reusable Templates
Location: `Scripts/PowerShell/Templates/`

## MCP Server
- Location: `MCP_Servers/resa-dataverse-mcp/`
- Credentials: `.env` file (Azure AD client credentials)

## Key Directories
- Scripts/PowerShell/Templates/ - Reusable PowerShell templates
- Working/ - Power Automate code view samples
- MCP_Servers/resa-dataverse-mcp/ - Dataverse MCP server
- Solution_Exports/v2.0.0/ - Current solution version

## Session Protocol
### On Start
- Read `WORKSPACE_SYSTEM.md` 
- Read `COORDINATED_TASK_LIST.md`
- Check `Working/DESKTOP_CLAUDE_FINDINGS.md`

### On End
- Update `PROJECT_CONTEXT.json`
- Commit and push to Git
