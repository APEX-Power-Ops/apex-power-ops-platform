# RESA Power Build - Workspace System
> **Single Source of Truth for All Claude Instances**
> Last Updated: 2025-12-02

## Quick Reference

| Item | Value |
|------|-------|
| **Dataverse URL** | `https://org7bdbc942.crm.dynamics.com` |
| **Solution** | `RESA_Power_Build_V2` v1.0.0.4 |
| **Repository** | `github.com/jasonlswenson-sys/RESA-Power-Project-Management` |
| **Branch** | `clean-main` |
| **Environment Type** | Developer |
| **Solution Export** | `Solution_Exports/v1.0.0.4/` |

> **WRONG URLs - DO NOT USE**: 
> - `org99cd6c6e.crm.dynamics.com` (jswensonllc default - NOT developer)
> - `org284447bd.crm.dynamics.com` (old dev environment)

---

## Environment Credentials

### Azure AD App Registration
| Property | Value |
|----------|-------|
| Tenant ID | `270d5723-4b30-4f3b-b9cb-6527be741b42` |
| Client ID | `9df3350f-b3b4-47c4-97b5-499a8b02acc7` |
| Secret ID | `d706e910-15be-4aa4-9108-f56a8c84fa64` |
| Client Secret | Stored in `.env` files (see Credential Locations) |

### Connection References (Power Platform)
| Name | Type |
|------|------|
| TBD after solution import | SharePoint |
| TBD after solution import | Dataverse |

### Credential Locations
1. **MCP Server**: `C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\.env`
2. **Desktop Claude**: `%APPDATA%\Claude\claude_desktop_config.json`

---

## Dataverse Tables (To be imported)

| Display Name | Logical Name | EntitySetName |
|--------------|--------------|---------------|
| Client | cr950_client | cr950_clients |
| Site | cr950_site | cr950_sites |
| Location | cr950_location | cr950_locations |
| Project | cr950_projects | cr950_projectses |
| Scope | cr950_projectscope | cr950_projectscopes |
| Task | cr950_tasks | cr950_taskses |
| Apparatus | cr950_apparatus | cr950_apparatuses |
| Scope Labor Detail | cr950_scopelabordetails | cr950_scopelabordetailses |
| Estimator | cr950_estimator | cr950_estimators |

---

## Folder Structure

C:\RESA_Power_Build\
- WORKSPACE_SYSTEM.md          # THIS FILE - Start here
- COORDINATED_TASK_LIST.md     # Active tasks for both Claude instances
- PROJECT_CONTEXT.json         # Machine-readable state
- CLAUDE.md                    # VS Code Claude instructions
- Documentation/00_START_HERE/SESSION_START_PROTOCOL.md
- MCP_Servers/resa-dataverse-mcp/.env
- Solution_Exports/
- Working/DESKTOP_CLAUDE_FINDINGS.md

---

## Session Protocols

### VS Code Claude (Copilot)
1. Read `WORKSPACE_SYSTEM.md` (this file)
2. Read `COORDINATED_TASK_LIST.md` for active tasks
3. Check `Working/DESKTOP_CLAUDE_FINDINGS.md` for Desktop Claude updates

### Desktop Claude
1. Read `WORKSPACE_SYSTEM.md` for correct credentials
2. Test MCP: Query `cr950_locations` table (after solution import)
3. Write findings to `Working/DESKTOP_CLAUDE_FINDINGS.md`

---

## Known Issues

### Azure AD Secret Rotation
- **Current Secret ID**: d706e910-15be-4aa4-9108-f56a8c84fa64
- **Created**: December 2, 2025
- **Expiration**: Check Azure Portal

### Environment History
- Dec 2, 2025: NEW `org7bdbc942` (Developer environment)
- Previous: `org284447bd` (old dev - deprecated)
- Previous: `org99cd6c6e` (jswensonllc default - NOT developer)

---

## Current Status (2025-12-02)

IN PROGRESS:
- New Developer environment created
- Solution export in progress
- Credentials updated

PENDING:
- Import solution to new environment
- Update Desktop Claude config
- Test MCP connectivity
