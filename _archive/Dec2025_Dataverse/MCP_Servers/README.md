# Dataverse Integration Setup

## ⚠️ Credentials Required

This repository does NOT contain credentials for security reasons. You must set up environment variables locally.

### Step 1: Set Environment Variables

**PowerShell (current session):**
```powershell
$env:AZURE_TENANT_ID = "your-tenant-id"
$env:AZURE_CLIENT_ID = "your-client-id"  
$env:AZURE_CLIENT_SECRET = "your-client-secret"
$env:DATAVERSE_URL = "https://your-org.crm.dynamics.com"
$env:ENVIRONMENT = "DEVELOPMENT"
```

**PowerShell (permanent - user profile):**
Add to `$PROFILE` (run `notepad $PROFILE`):
```powershell
# Dataverse Credentials
$env:AZURE_TENANT_ID = "your-tenant-id"
$env:AZURE_CLIENT_ID = "your-client-id"
$env:AZURE_CLIENT_SECRET = "your-client-secret"
$env:DATAVERSE_URL = "https://your-org.crm.dynamics.com"
$env:ENVIRONMENT = "DEVELOPMENT"
```

### Step 2: Use PowerShell Functions

```powershell
Import-Module .\Scripts\PowerShell\Dataverse-Functions.ps1
Connect-Dataverse
Get-DataverseRecords -EntityName "cr950_projectses"
```

### Step 3: Use MCP Server (Claude Desktop)

1. Edit `%APPDATA%\Claude\claude_desktop_config.json`
2. Update the `env` section with your values:
```json
{
  "mcpServers": {
    "resa-dataverse-dev": {
      "command": "node",
      "args": ["C:\\RESA_Power_Build\\MCP_Servers\\resa-dataverse-mcp\\build\\index.js"],
      "env": {
        "DATAVERSE_URL": "https://your-org.crm.dynamics.com",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret",
        "ENVIRONMENT": "DEVELOPMENT"
      }
    }
  }
}
```

3. Build the MCP server:
```powershell
cd MCP_Servers\resa-dataverse-mcp
npm install
npm run build
```

4. Restart Claude Desktop

## Getting Credentials

See `Documentation/00_START_HERE/AZURE_APP_REGISTRATION_GUIDE.md` for complete setup instructions.

## Security Notes

- **NEVER commit credentials to Git**
- `.env` files are gitignored
- `claude_desktop_config.json` is gitignored
- Azure Client Secret expires: 11/22/2027 (set reminder to renew)
