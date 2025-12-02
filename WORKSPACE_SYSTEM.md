# RESA Power Build - Workspace System
> **Single Source of Truth for All Claude Instances**
> Last Updated: 2025-12-02

## Quick Reference

| Item | Value |
|------|-------|
| **Dataverse URL** | `https://org284447bd.crm.dynamics.com` |
| **Solution** | `RESA_Power_Build_V2` v1.0.0.1 |
| **Repository** | `github.com/jasonlswenson-sys/RESA-Power-Project-Management` |
| **Branch** | `clean-main` |

> **WRONG VALUE - DO NOT USE**: `org99cd6c6e.crm.dynamics.com` (appears in old docs)

---

## Environment Credentials

### Azure AD App Registration
| Property | Value |
|----------|-------|
| Tenant ID | `270d5723-4b30-4f3b-b9cb-6527be741b42` |
| Client ID | `9df3350f-b3b4-47c4-97b5-499a8b02acc7` |
| Client Secret | Stored in `.env` files (see Credential Locations) |

### Connection References (Power Platform)
| Name | Type |
|------|------|
| `cr950_sharedsharepointonline_a9dba` | SharePoint |
| `new_sharedcommondataserviceforapps_f7a26` | Dataverse |

### Credential Locations
1. **MCP Server**: `C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\.env`
2. **Desktop Claude**: `%APPDATA%\Claude\claude_desktop_config.json`

---

## Dataverse Tables (9 Custom)

| Display Name | Logical Name | EntitySetName | Records |
|--------------|--------------|---------------|---------|
| Client | cr950_client | cr950_clients | TBD |
| Site | cr950_site | cr950_sites | TBD |
| Location | cr950_location | cr950_locations | 4 |
| Project | cr950_projects | cr950_projectses | TBD |
| Scope | cr950_projectscope | cr950_projectscopes | TBD |
| Task | cr950_tasks | cr950_taskses | TBD |
| Apparatus | cr950_apparatus | cr950_apparatuses | TBD |
| Scope Labor Detail | cr950_scopelabordetails | cr950_scopelabordetailses | TBD |
| Estimator | cr950_estimator | cr950_estimators | 0 |

---

## Folder Structure

C:\RESA_Power_Build\
- WORKSPACE_SYSTEM.md          # THIS FILE - Start here
- COORDINATED_TASK_LIST.md     # Active tasks for both Claude instances
- PROJECT_CONTEXT.json         # Machine-readable state
- CLAUDE.md                    # VS Code Claude instructions
- Documentation/00_START_HERE/SESSION_START_PROTOCOL.md
- MCP_Servers/resa-dataverse-mcp/.env
- Solution_Exports/v2.0.0/unpacked/Workflows/
- Working/DESKTOP_CLAUDE_FINDINGS.md

---

## Session Protocols

### VS Code Claude (Copilot)
1. Read `WORKSPACE_SYSTEM.md` (this file)
2. Read `COORDINATED_TASK_LIST.md` for active tasks
3. Check `Working/DESKTOP_CLAUDE_FINDINGS.md` for Desktop Claude updates

### Desktop Claude
1. Read `WORKSPACE_SYSTEM.md` for correct credentials
2. Test MCP: Query `cr950_locations` table
3. Write findings to `Working/DESKTOP_CLAUDE_FINDINGS.md`

---

## Known Issues

### Azure AD Secret Expiration
- **Symptom**: 401 Unauthorized errors from MCP
- **Fix**: User must refresh secret in Azure Portal -> App registrations -> Certificates & secrets
- **Update Locations**: Both `.env` and `claude_desktop_config.json`

### Old Org URL in Documentation
- Many older docs reference `org99cd6c6e.crm.dynamics.com`
- This is WRONG - always use `org284447bd.crm.dynamics.com`

---

## Current Status (2025-12-02)

COMPLETED:
- Solution RESA_Power_Build_V2 deployed
- Estimator Import Flow V2 deployed
- Location table has 4 records
- Workspace system documentation created

PENDING:
- User refresh of Azure AD client secret
- Desktop Claude connectivity verification
- Archive old Solution_V2/ and Solution_V3/ folders
