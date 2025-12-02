# RESA Power Project - Copilot Instructions

## Project Context
This is a Dataverse/Power Platform project for RESA Power electrical testing company.
- **Environment**: org284447bd.crm.dynamics.com (CORRECT)
- **Solution**: RESA_Power_Build_V2 v1.0.0.1
- **Repository**: RESA-Power-Project-Management on GitHub

**WRONG - DO NOT USE**: org99cd6c6e.crm.dynamics.com (old/incorrect)

## Critical Files to Read First
1. `WORKSPACE_SYSTEM.md` - Single source of truth
2. `COORDINATED_TASK_LIST.md` - Current tasks  
3. `PROJECT_CONTEXT.json` - Machine-readable state

## Connection References
| Name | Type |
|------|------|
| cr950_sharedsharepointonline_a9dba | SharePoint |
| new_sharedcommondataserviceforapps_f7a26 | Dataverse |

## Key Table Names (EntitySetName for API)
`
cr950_clients          - Clients
cr950_sites            - Sites
cr950_locations        - Locations  
cr950_projectses       - Projects
cr950_projectscopes    - Scopes
cr950_apparatuses      - Apparatus
cr950_estimators       - Estimators
`

## MCP Server Configuration
- **Location**: MCP_Servers/resa-dataverse-mcp/
- **Credentials**: .env file (uses Azure AD app registration)

## Session Protocol
- **On Start**: Read WORKSPACE_SYSTEM.md, COORDINATED_TASK_LIST.md
- **On End**: Update PROJECT_CONTEXT.json, commit to Git
