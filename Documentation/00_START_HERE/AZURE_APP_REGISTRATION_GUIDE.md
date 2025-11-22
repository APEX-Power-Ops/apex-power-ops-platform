# Azure App Registration Setup Guide
## For MCP Server Authentication to Dev Environment

**Purpose:** Configure Azure AD app registration for MCP servers to authenticate with your isolated dev Dataverse environment  
**Environment:** org99cd6c6e.crm.dynamics.com (Jason Swenson's Environment)  
**Time Required:** 15 minutes  
**Last Updated:** November 22, 2025

---

## 🎯 What You're Creating

An Azure Active Directory application registration that allows your MCP servers to authenticate and access Dataverse APIs safely in your isolated development environment.

---

## 📋 Step-by-Step Instructions

### **Step 1: Open Azure Portal** (1 minute)

Open your browser and navigate to:
```
https://portal.azure.com
```

Sign in with: `jjswens21@msn.com` (your personal Microsoft account)

---

### **Step 2: Navigate to App Registrations** (1 minute)

1. In the search bar at the top, type: `App registrations`
2. Click on **"App registrations"** service
3. Click **"+ New registration"** button

---

### **Step 3: Register the Application** (3 minutes)

Fill in the registration form:

**Name:**
```
RESA-Dev-MCP-Access
```

**Supported account types:**
- Select: **"Accounts in this organizational directory only (Single tenant)"**

**Redirect URI:**
- Leave blank (not needed for service principal authentication)

Click **"Register"** button

---

### **Step 4: Save Application IDs** (2 minutes)

After registration completes, you'll see the Overview page.

**Copy these values immediately:**

```
Application (client) ID: [Copy from Azure Portal]
Directory (tenant) ID:   [Copy from Azure Portal]
```

💾 **Save these securely (password manager or local encrypted file)**

---

### **Step 5: Create Client Secret** (3 minutes)

1. In the left menu, click **"Certificates & secrets"**
2. Click **"+ New client secret"** button
3. Fill in:
   - **Description:** `MCP Server Authentication`
   - **Expires:** Select **"24 months"** (longest available)
4. Click **"Add"**

⚠️ **CRITICAL: Copy the secret VALUE immediately!**

```
Client Secret Value: [SECURELY STORED - NOT IN GIT]
Secret ID:           599a6fbd-92df-476e-bf5a-9033ce43f4c1
Description:         MCP Server Authentication
Expires:             11/22/2027
```

**⚠️ IMPORTANT: Actual secret stored securely locally, not committed to Git** ✅

**This value is shown ONLY ONCE!** If you miss it, you'll need to create a new secret.

---

### **Step 6: Grant API Permissions** (5 minutes)

1. In the left menu, click **"API permissions"**
2. Click **"+ Add a permission"**
3. Select **"Dynamics CRM"** (scroll down if needed)
4. Select **"Delegated permissions"**
5. Check the box for **"user_impersonation"**
6. Click **"Add permissions"**

**Grant Admin Consent:**
7. Click **"Grant admin consent for [your tenant]"** button
8. Click **"Yes"** to confirm
9. Wait for status to show green checkmark: ✅ "Granted for [tenant]"

---

## ✅ Verification Checklist

Before proceeding, confirm you have:

- [ ] Application (Client) ID saved
- [ ] Directory (Tenant) ID saved
- [ ] Client Secret VALUE saved (not the ID!)
- [ ] API permission "user_impersonation" granted
- [ ] Admin consent granted (green checkmark visible)

---

## 🔧 Configure MCP Server

Now update your MCP server configuration with these values.

### **Edit Claude Desktop Config**

Location: `%APPDATA%\Claude\claude_desktop_config.json`

Full path: `C:\Users\jjswe\AppData\Roaming\Claude\claude_desktop_config.json`

**Configuration Template:**

```json
{
  "mcpServers": {
    "resa-dataverse-dev": {
      "command": "node",
      "args": [
        "C:\\RESA_Power_Build\\MCP_Servers\\resa-dataverse-mcp\\build\\index.js"
      ],
      "env": {
        "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
        "AZURE_TENANT_ID": "YOUR_TENANT_ID_HERE",
        "AZURE_CLIENT_ID": "YOUR_APPLICATION_CLIENT_ID_HERE",
        "AZURE_CLIENT_SECRET": "YOUR_CLIENT_SECRET_VALUE_HERE",
        "ENVIRONMENT": "DEVELOPMENT",
        "MAX_REQUESTS_PER_MINUTE": "60",
        "MAX_CONCURRENT_REQUESTS": "5",
        "CIRCUIT_BREAKER_ENABLED": "true",
        "REQUEST_LOGGING": "true",
        "LOG_FILE_PATH": "C:\\RESA_Power_Build\\Logs\\mcp-requests.log"
      }
    }
  }
}
```

**Replace placeholders with your actual values from above:**

- `YOUR_TENANT_ID_HERE` → Your Directory (Tenant) ID
- `YOUR_APPLICATION_CLIENT_ID_HERE` → Your Application (Client) ID
- `YOUR_CLIENT_SECRET_VALUE_HERE` → Your Client Secret VALUE

---

## 🧪 Test Authentication

### **PowerShell Test Script**

Create: `c:\RESA_Power_Build\Scripts\PowerShell\Test-MCPAuthentication.ps1`

```powershell
# Test MCP Authentication to Dev Environment
$tenantId = "YOUR_TENANT_ID"
$clientId = "YOUR_CLIENT_ID"
$clientSecret = "YOUR_CLIENT_SECRET"
$dataverseUrl = "https://org99cd6c6e.crm.dynamics.com"

# Get OAuth token
$tokenUrl = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"
$body = @{
    client_id     = $clientId
    scope         = "$dataverseUrl/.default"
    client_secret = $clientSecret
    grant_type    = "client_credentials"
}

try {
    Write-Host "🔐 Requesting authentication token..." -ForegroundColor Cyan
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    
    Write-Host "✅ Authentication successful!" -ForegroundColor Green
    Write-Host "Token type: $($tokenResponse.token_type)" -ForegroundColor Green
    Write-Host "Expires in: $($tokenResponse.expires_in) seconds" -ForegroundColor Green
    
    # Test API call
    Write-Host "`n🔍 Testing Dataverse API access..." -ForegroundColor Cyan
    $headers = @{
        Authorization = "Bearer $($tokenResponse.access_token)"
        "OData-MaxVersion" = "4.0"
        "OData-Version" = "4.0"
        Accept = "application/json"
    }
    
    $whoAmIUrl = "$dataverseUrl/api/data/v9.2/WhoAmI"
    $whoAmI = Invoke-RestMethod -Uri $whoAmIUrl -Headers $headers -Method Get
    
    Write-Host "✅ API access confirmed!" -ForegroundColor Green
    Write-Host "User ID: $($whoAmI.UserId)" -ForegroundColor Green
    Write-Host "Organization ID: $($whoAmI.OrganizationId)" -ForegroundColor Green
    
    Write-Host "`n🎉 All tests passed! MCP authentication is working." -ForegroundColor Green
    
} catch {
    Write-Host "❌ Authentication failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verify Tenant ID, Client ID, and Client Secret are correct" -ForegroundColor Yellow
    Write-Host "2. Confirm API permissions granted and admin consent given" -ForegroundColor Yellow
    Write-Host "3. Wait 5-10 minutes after granting permissions for Azure to sync" -ForegroundColor Yellow
}
```

**Run the test:**
```powershell
cd c:\RESA_Power_Build\Scripts\PowerShell
.\Test-MCPAuthentication.ps1
```

**Expected output:**
```
🔐 Requesting authentication token...
✅ Authentication successful!
Token type: Bearer
Expires in: 3599 seconds

🔍 Testing Dataverse API access...
✅ API access confirmed!
User ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Organization ID: a5036521-cde7-4d7a-90a-08fd8a13ad05

🎉 All tests passed! MCP authentication is working.
```

---

## 🔒 Security Best Practices

### **Credential Storage**

**✅ DO:**
- Store in password manager (1Password, LastPass, Bitwarden)
- Use environment variables (not in code)
- Encrypt Claude Desktop config if possible
- Keep separate dev/prod credentials

**❌ DON'T:**
- Commit credentials to GitHub
- Share credentials in chat/email
- Store in plain text files
- Reuse production credentials

### **Secret Rotation**

```
Set calendar reminder: 22 months from now

Before secret expires:
1. Create new client secret (25 days before expiration)
2. Update MCP configuration with new secret
3. Test MCP still connects
4. Delete old secret after confirming new one works
```

---

## 🚨 Troubleshooting

### **Issue: Authentication fails**

**Check:**
1. Tenant ID, Client ID, Secret are exactly correct (no extra spaces)
2. API permissions granted (green checkmark visible)
3. Admin consent granted
4. Wait 5-10 minutes after granting permissions
5. Secret hasn't expired
6. Using Client Secret VALUE (not the ID)

### **Issue: Permission denied**

**Fix:**
1. Go back to API permissions
2. Verify "user_impersonation" is checked
3. Click "Grant admin consent" again
4. Wait 5 minutes
5. Try again

### **Issue: MCP won't connect**

**Check:**
1. MCP server built successfully (`npm run build`)
2. Claude Desktop config JSON is valid (no syntax errors)
3. Paths to MCP server files are correct
4. Restart Claude Desktop after config changes
5. Check MCP logs for specific errors

---

## 📞 Next Steps

After successful authentication:

1. ✅ Restart Claude Desktop to load new MCP configuration
2. ✅ Test MCP connection in Claude
3. ✅ Verify safeguards active (rate limiting, circuit breaker)
4. ✅ Start with READ-ONLY operations
5. ✅ Document success in MY_DEV_ENVIRONMENT.md

---

**App Registration Complete!** 🎉  
**Next:** Configure and test MCP servers with your isolated dev environment.

**Last Updated:** November 22, 2025  
**Status:** Ready for implementation
