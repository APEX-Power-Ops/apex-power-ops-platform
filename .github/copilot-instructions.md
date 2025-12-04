# RESA Power Project - Copilot Instructions

## Project Context
This is a Dataverse/Power Platform project for RESA Power electrical testing company.
- **Environment**: org7bdbc942.crm.dynamics.com (Developer)
- **Solution**: RESA_Power_Build_V2 (v1.0.0.5)
- **Repository**: RESA-Power-Project-Management on GitHub

**WRONG - DO NOT USE**: 
- org99cd6c6e.crm.dynamics.com (jswensonllc default)
- org284447bd.crm.dynamics.com (old dev)

## ⚠️ CRITICAL: Schema Reference
**ALWAYS read `MASTER_SCHEMA.md` before any Dataverse development.**
This is the ONLY authoritative source for entity/field names.

## Critical Files to Read First
1. `MASTER_SCHEMA.md` - **AUTHORITATIVE** schema reference (EntitySets, fields, lookups)
2. `WORKSPACE_SYSTEM.md` - Single source of truth
3. `COORDINATED_TASK_LIST.md` - Current tasks  
4. `PROJECT_CONTEXT.json` - Machine-readable state

## Key Table Names (EntitySetName for API)
```
cr950_clients          - Clients
cr950_sites            - Sites
cr950_locations        - Locations  
cr950_projects         - Projects (NOT projectses!)
cr950_scopes           - Scopes (NOT projectscopes!)
cr950_tasks            - Tasks
cr950_apparatuses      - Apparatus
cr950_estimators       - Estimators
cr950_scopelabordetails - Scope Labor Details
```

## MCP Server Configuration
- **Location**: MCP_Servers/resa-dataverse-mcp/
- **Credentials**: .env file (uses Azure AD app registration)

## Session Protocol
- **On Start**: Read WORKSPACE_SYSTEM.md, COORDINATED_TASK_LIST.md
- **On End**: Update PROJECT_CONTEXT.json, commit to Git
