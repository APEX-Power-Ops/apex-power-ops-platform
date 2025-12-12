# Dataverse Integration Quick Reference
**Created:** November 22, 2025  
**Environment:** org99cd6c6e.crm.dynamics.com (Dev)

## Two Ways to Access Dataverse

### 1. PowerShell Functions (VS Code)
**Best for:** Scripting, automation, batch operations, VS Code workflows

### 2. MCP Server (Claude Desktop)
**Best for:** Interactive queries, conversational data exploration, Claude-assisted development

---

## PowerShell Functions (VS Code)

### Setup
```powershell
# Load the functions
Import-Module C:\RESA_Power_Build\Scripts\PowerShell\Dataverse-Functions.ps1

# Connect to Dataverse
Connect-Dataverse
```

### Query Records
```powershell
# Get all projects
Get-DataverseRecords -EntityName "cr950_projectses"

# Get specific fields
Get-DataverseRecords -EntityName "cr950_apparatus" -Select "cr950_name,cr950_serialnumber" -Top 10

# Filter results
Get-DataverseRecords -EntityName "cr950_apparatus" -Filter "cr950_status eq 100000001"

# Combine options
Get-DataverseRecords -EntityName "cr950_projectses" `
    -Select "cr950_name,cr950_projectnumber" `
    -Filter "statecode eq 0" `
    -Top 20 `
    -OrderBy "createdon desc"
```

### Create Records
```powershell
# Create a project
$projectData = @{
    "cr950_name" = "New Test Project"
    "cr950_projectnumber" = "PRJ-2025-001"
    "cr950_description" = "Created via PowerShell"
}
$projectId = New-DataverseRecord -EntityName "cr950_projectses" -Data $projectData

# Create apparatus
$apparatusData = @{
    "cr950_name" = "Test Breaker"
    "cr950_serialnumber" = "SN-12345"
    "cr950_status" = 100000000  # Active
}
$apparatusId = New-DataverseRecord -EntityName "cr950_apparatus" -Data $apparatusData
```

### Update Records
```powershell
# Update apparatus status
$updates = @{
    "cr950_status" = 100000001  # Completed
    "cr950_completeddate" = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
}
Update-DataverseRecord -EntityName "cr950_apparatus" -RecordId $apparatusId -Data $updates

# Update project
$projectUpdates = @{
    "cr950_description" = "Updated via PowerShell"
}
Update-DataverseRecord -EntityName "cr950_projectses" -RecordId $projectId -Data $projectUpdates
```

### Delete Records
```powershell
# Delete a record
Remove-DataverseRecord -EntityName "cr950_apparatus" -RecordId $apparatusId

# Delete with confirmation
if (Read-Host "Delete project? (Y/N)") -eq "Y" {
    Remove-DataverseRecord -EntityName "cr950_projectses" -RecordId $projectId
}
```

### Advanced Queries (FetchXML)
```powershell
$fetchXml = @"
<fetch top="50">
  <entity name="cr950_apparatus">
    <attribute name="cr950_name" />
    <attribute name="cr950_status" />
    <attribute name="cr950_netahours" />
    <filter>
      <condition attribute="cr950_status" operator="eq" value="100000001" />
    </filter>
    <order attribute="createdon" descending="true" />
  </entity>
</fetch>
"@

$results = Invoke-DataverseFetchXml -FetchXml $fetchXml
```

### Check Connection
```powershell
Get-DataverseConnection
```

---

## MCP Server (Claude Desktop)

### Configuration
Already configured in: `C:\Users\jjswe\AppData\Roaming\Claude\claude_desktop_config.json`

### Setup Steps
1. Download and install **Claude Desktop** from anthropic.com
2. Restart Claude Desktop
3. Look for the 🔌 icon indicating MCP servers are loaded
4. Start a new chat

### Usage in Claude Desktop
Simply ask Claude to interact with your Dataverse:

**Examples:**
- "Show me all projects in Dataverse"
- "Create a new project called 'Phoenix Substation' with project number PRJ-2025-100"
- "Find all apparatus with status completed"
- "Update apparatus with ID xxx to status completed"
- "What tables exist in my Dataverse environment?"

### Available MCP Tools
- `query_dataverse` - Query records with filters
- `create_record` - Create new records
- `update_record` - Update existing records
- `delete_record` - Delete records

---

## Table Names Reference

### RESA Power Project Management Tables
| Display Name | Logical Name | Description |
|---|---|---|
| Projects | cr950_projectses | Main project records |
| Project Scope | cr950_projectscopes | Scope items within projects |
| Tasks | cr950_taskses | Task records |
| Apparatus | cr950_apparatuses | Equipment/apparatus records |
| Apparatus Revenue | cr950_apparatusrevenues | Revenue tracking |
| Scope Labor Details | cr950_scopelabordetails | Labor configuration |
| NETA Standards | cr950_netastandards | NETA testing standards |
| Business Unit | businessunit | Organization units |

### Common Field Prefixes
- `cr950_` - Custom fields for RESA solution
- `statecode` - Record state (0=Active, 1=Inactive)
- `statuscode` - Status reason code
- `createdon` - Creation date
- `modifiedon` - Last modified date

---

## Status Code Values

### Apparatus Status (cr950_status)
- `100000000` - Active
- `100000001` - Completed
- `100000002` - On Hold
- `100000003` - Cancelled

### Project State (statecode)
- `0` - Active
- `1` - Inactive

---

## Tips & Best Practices

### PowerShell
- Always run `Connect-Dataverse` before any operations
- Use `-Select` to limit fields and improve performance
- Use `-Top` to limit result sets during testing
- Store record IDs in variables for updates/deletes
- Use `-WhatIf` pattern for destructive operations

### Claude Desktop MCP
- Be specific about which fields you want
- Ask Claude to format results as tables for readability
- Use natural language - Claude will translate to proper queries
- Claude remembers context within a conversation
- Can ask Claude to generate PowerShell scripts from successful queries

### Both
- **NEVER connect to RESA production** (org04ad071f) - Fatal error protection built in
- Test in dev environment (org99cd6c6e) first
- Export data before bulk updates
- Keep credentials secure (already in environment variables)

---

## Troubleshooting

### PowerShell: "Not connected"
```powershell
Connect-Dataverse
Get-DataverseConnection
```

### PowerShell: Authentication fails
- Check if secret expired (expires 11/22/2027)
- Verify app registration has Dataverse permissions
- Confirm application user exists in environment

### Claude Desktop: MCP not loading
1. Check `claude_desktop_config.json` syntax (valid JSON)
2. Verify path to `build/index.js` exists
3. Check Claude Desktop logs in `%APPDATA%\Claude\logs\`
4. Restart Claude Desktop completely

### Both: 403 Forbidden
- Verify application user exists in environment
- Check security role assignment (needs System Administrator for testing)
- Wait 5-10 minutes after permission changes

---

## Next Steps

1. ✅ Import solution v1.3.0.5 to dev environment (if not done)
2. ✅ Test PowerShell functions with sample data
3. ✅ Test MCP server in Claude Desktop
4. Create test projects and apparatus
5. Build automation scripts for common tasks
6. Document custom workflows

---

**Environment Details:**
- Dev URL: https://org99cd6c6e.crm.dynamics.com
- Tenant ID: 270d5723-4b30-4f3b-b9cb-6527be741b42
- App Registration: RESA Dev MCP Access
- Client Secret Expires: November 22, 2027

**Last Updated:** November 22, 2025
