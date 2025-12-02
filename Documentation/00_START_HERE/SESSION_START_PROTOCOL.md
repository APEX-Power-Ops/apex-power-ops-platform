# Session Start Protocol
> Quick checklist for both Claude instances

## VS Code Claude (Copilot) - Start Here

### 1. Read Core Docs (2 minutes)
- WORKSPACE_SYSTEM.md - Environment, credentials, tables
- COORDINATED_TASK_LIST.md - Current tasks, priorities

### 2. Check Desktop Claude Updates
- Working/DESKTOP_CLAUDE_FINDINGS.md - Any MCP results or issues

### 3. Verify Environment
- Dataverse URL: org284447bd.crm.dynamics.com (NOT org99cd6c6e)
- Solution: RESA_Power_Build_V2

---

## Desktop Claude - Start Here

### 1. Read WORKSPACE_SYSTEM.md
Get correct credentials from the environment section.

### 2. Test MCP Connectivity
Query: cr950_locations
Expected: 4 records

### 3. If 401 Error
- Credential expired - user needs to refresh in Azure Portal
- Document in Working/DESKTOP_CLAUDE_FINDINGS.md

### 4. Write Findings
Always update Working/DESKTOP_CLAUDE_FINDINGS.md with:
- Query results
- Errors encountered
- Recommendations

---

## Troubleshooting

### 401 Unauthorized from MCP
1. Azure AD client secret expired
2. User must: Azure Portal -> App registrations -> Create new secret
3. Update: .env AND claude_desktop_config.json

### Table not found
1. Check EntitySetName (plural form with es suffix)
2. Reference: PROJECT_CONTEXT.json -> tables array

### Wrong data returned
1. Verify using correct org: org284447bd
2. Old docs may reference wrong org org99cd6c6e
