# FREE Microsoft 365 Developer Environment - Complete Setup Guide

**Date:** November 21, 2025  
**Status:** ✅ Developer Program Account Created  
**Cost:** $0/month (completely free)  
**Next Step:** Configure authentication for MCP servers

---

## 🎉 CONGRATULATIONS!

You just got access to a **$1,925/month Microsoft 365 E5 environment for FREE**. This includes everything you need to build, test, and perfect your RESA Power solution without any risk to production systems.

---

## 📋 WHAT YOU HAVE NOW

```
Your Free Microsoft 365 Developer Subscription:
├── 25 User Licenses (Microsoft 365 E5)
├── Dataverse Environment (fully functional)
├── Power Apps (unlimited for dev/test)
├── Power Automate (unlimited for dev/test)
├── Power BI Pro
├── Azure Active Directory Premium P2
├── Microsoft Teams
├── SharePoint Online
├── OneDrive for Business
├── Exchange Online
├── Microsoft Graph API (full access)
└── Valid for 90 days (auto-renewable if actively used)

Retail Value: $1,925/month
Your Cost: $0/month
```

---

## 🚀 STEP-BY-STEP SETUP (30 minutes)

### **Step 1: Find Your Dataverse Environment (5 minutes)**

```
1. Go to: https://admin.powerplatform.microsoft.com

2. Sign in with your developer account

3. Click "Environments" in left nav

4. You should see an environment (might be named with your email prefix)

5. Click the environment name

6. Copy the "Environment URL"
   Example: https://orgXXXXXXXX.crm.dynamics.com
   
   THIS IS YOUR DEV DATAVERSE URL ⭐
   Write it down: _________________________________
```

**If you don't see an environment:**
```
1. Go to: https://make.powerapps.com
2. Click environment dropdown (top right)
3. Should see your developer environment
4. OR create one: Settings → Admin Center → Environments → New
   - Name: "RESA Dev"
   - Type: Developer
   - Region: United States (default)
   - Add Dataverse: Yes
```

---

### **Step 2: Create App Registration for MCP Authentication (10 minutes)**

```
1. Go to: https://portal.azure.com

2. Sign in with your developer account

3. Navigate to: Azure Active Directory

4. Click: App registrations (left menu)

5. Click: + New registration

6. Fill in:
   Name: RESA-MCP-Dev-Server
   Supported account types: Accounts in this organizational directory only
   Redirect URI: Leave blank (not needed for MCP)

7. Click: Register

8. SAVE THESE VALUES (you'll need them for MCP config):
   
   Application (client) ID: ________________________________
   
   Directory (tenant) ID: ________________________________
```

---

### **Step 3: Create Client Secret (5 minutes)**

```
1. In your app registration, click: Certificates & secrets (left menu)

2. Click: + New client secret

3. Description: MCP Server Authentication
   Expires: 24 months

4. Click: Add

5. ⚠️ IMMEDIATELY COPY THE SECRET VALUE (shows only once!)
   
   Client Secret Value: ________________________________
   
   ⚠️ You CANNOT retrieve this later! Save it now!
```

---

### **Step 4: Grant API Permissions (5 minutes)**

```
1. In your app registration, click: API permissions (left menu)

2. Click: + Add a permission

3. Click: Dynamics CRM

4. Click: Delegated permissions

5. Check: user_impersonation

6. Click: Add permissions

7. Click: Grant admin consent for [Your Directory]
   (Blue button at top)

8. Confirm: Yes

9. Verify all permissions show green checkmarks ✅
```

---

### **Step 5: Configure MCP Server (5 minutes)**

**Edit your Claude Desktop config:**

Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "resa-dataverse-dev": {
      "command": "node",
      "args": [
        "C:\\RESA_Power_Build\\MCP_Servers\\safe-dataverse-mcp\\build\\index.js"
      ],
      "env": {
        "ENVIRONMENT": "DEVELOPMENT",
        "DATAVERSE_URL": "https://YOUR-ORG-ID.crm.dynamics.com",
        "AZURE_TENANT_ID": "your-tenant-id-from-step-2",
        "AZURE_CLIENT_ID": "your-client-id-from-step-2",
        "AZURE_CLIENT_SECRET": "your-secret-from-step-3",
        
        "MAX_REQUESTS_PER_MINUTE": "60",
        "MAX_CONCURRENT_REQUESTS": "5",
        "CIRCUIT_BREAKER_ENABLED": "true",
        "REQUEST_LOGGING": "true",
        "LOG_FILE": "C:\\RESA_Power_Build\\Logs\\mcp-requests.log"
      }
    }
  }
}
```

**Replace these values:**
- `DATAVERSE_URL`: Your environment URL from Step 1
- `AZURE_TENANT_ID`: Tenant ID from Step 2
- `AZURE_CLIENT_ID`: Application ID from Step 2
- `AZURE_CLIENT_SECRET`: Secret value from Step 3

---

### **Step 6: Test Authentication (5 minutes)**

```powershell
# Option 1: Test with PowerShell
$tenantId = "your-tenant-id"
$clientId = "your-client-id"
$clientSecret = "your-client-secret"
$resource = "https://YOUR-ORG-ID.crm.dynamics.com"

$body = @{
    client_id     = $clientId
    client_secret = $clientSecret
    resource      = $resource
    grant_type    = "client_credentials"
}

$tokenResponse = Invoke-RestMethod -Method Post `
    -Uri "https://login.microsoftonline.com/$tenantId/oauth2/token" `
    -Body $body

if ($tokenResponse.access_token) {
    Write-Host "✅ Authentication successful!" -ForegroundColor Green
    Write-Host "Token expires in: $($tokenResponse.expires_in) seconds"
} else {
    Write-Host "❌ Authentication failed" -ForegroundColor Red
}
```

**OR**

```
# Option 2: Test with Claude Desktop

1. Restart Claude Desktop (to pick up new config)

2. In a chat, ask:
   "Test connection to Dataverse dev environment"

3. Should see MCP server connect and authenticate

4. If working, you'll see: ✅ Connected to Dataverse
```

---

## 🎯 VERIFY EVERYTHING WORKS

### **Checklist:**

```
□ Developer tenant created (https://developer.microsoft.com/microsoft-365/profile)
□ Dataverse environment exists (https://admin.powerplatform.microsoft.com)
□ Environment URL copied
□ App registration created (https://portal.azure.com)
□ Client ID saved
□ Tenant ID saved
□ Client secret created and saved
□ API permissions granted (user_impersonation)
□ Admin consent granted (green checkmarks)
□ MCP config updated with credentials
□ Claude Desktop restarted
□ Test connection successful
```

---

## 🛡️ SECURITY BEST PRACTICES

### **Keep These Safe:**

```
🔐 NEVER commit to GitHub:
- Client Secret
- Tenant ID
- Client ID
- Any credentials

✅ DO store securely:
- Password manager (1Password, LastPass)
- Encrypted file
- Secure notes app

❌ DON'T share:
- Client secret (regenerate if exposed)
- Give others admin access
- Connect to production
```

### **Credential Storage Template:**

```
Service: Microsoft 365 Developer - RESA MCP
Created: November 21, 2025

Tenant ID: [paste here]
Client ID: [paste here]
Client Secret: [paste here]
Environment URL: [paste here]

Notes:
- Client secret expires: [date 24 months from now]
- Used for: MCP Dataverse development server
- Renewal: Developer subscription renews if actively used
```

---

## 🚀 NOW YOU CAN BUILD!

### **Safe Development Workflow:**

```
1. BUILD IN DEV (Your Free Environment)
   ├── Connect MCP servers to dev environment
   ├── Create tables, fields, relationships
   ├── Build Power Apps
   ├── Create Power Automate flows
   ├── Test everything thoroughly
   ├── Break things, learn, iterate
   └── Zero risk to RESA production

2. VALIDATE IN DEV
   ├── Run all validation tools
   ├── Test with realistic data
   ├── Multi-user testing (25 test accounts!)
   ├── Integration testing
   ├── Performance testing
   └── Security testing

3. EXPORT SOLUTION
   ├── Power Platform → Solutions
   ├── Export as managed solution
   ├── Download .zip file
   ├── Upload to Box for safekeeping
   └── Version tag: v1.3.0.5-dev-tested

4. IMPORT TO PRODUCTION (Manual)
   ├── RESA production environment
   ├── Power Platform → Solutions
   ├── Import solution
   ├── Map connections
   ├── Publish customizations
   └── Test in production with pilot users

5. MONITOR & ITERATE
   ├── Watch for issues
   ├── Gather feedback
   ├── Make improvements in DEV
   ├── Test thoroughly
   └── Re-export and import
```

---

## 💡 WHAT YOU CAN TEST (All Free!)

### **Power Platform Features:**

```
✅ Dataverse
   - Create custom tables
   - Complex relationships
   - Calculated fields
   - Rollup fields
   - Business rules
   - Security roles

✅ Power Apps
   - Canvas apps
   - Model-driven apps
   - Mobile apps
   - Component libraries
   - Connectors

✅ Power Automate
   - Cloud flows
   - Desktop flows
   - Approval workflows
   - Scheduled flows
   - HTTP connectors

✅ Power BI
   - Connect to Dataverse
   - Build dashboards
   - Create reports
   - Embedded analytics
```

### **Microsoft Graph Integrations:**

```
✅ Outlook
   - Send emails from system
   - Read mailboxes
   - Calendar integration
   - Contact management

✅ Teams
   - Create channels
   - Post messages
   - Chat notifications
   - File sharing

✅ SharePoint
   - Document libraries
   - Lists
   - Sites
   - Permissions

✅ OneDrive
   - File storage
   - Upload/download
   - Sharing
   - Versioning

✅ Azure AD
   - User management
   - Groups
   - Authentication
   - SSO testing
```

---

## 📊 DEVELOPER SUBSCRIPTION RENEWAL

**Your subscription is FREE as long as you use it:**

```
Renewal Conditions:
✓ Active development (logging in, making changes)
✓ Using the environment regularly
✓ Building solutions

Microsoft Tracks:
- Login frequency
- API calls
- Resource usage
- Development activity

Renewal Process:
- Automatically renews every 90 days
- Email notification before expiration
- No action needed if actively used
- Can manually extend if needed
```

**If it does expire:**
```
No Problem!
1. Renew through developer portal
2. Request extension
3. Create new subscription
4. Your work is backed up (export solutions regularly)
```

---

## 🆘 TROUBLESHOOTING

### **Issue: Can't find Dataverse environment**

```
Solution 1:
- Go to https://make.powerapps.com
- Check environment dropdown (top right)
- May take 10-15 minutes to provision

Solution 2:
- Create manually:
  https://admin.powerplatform.microsoft.com
  → Environments → New
  → Type: Developer
  → Add Dataverse: Yes
```

### **Issue: Authentication fails**

```
Check:
□ Client secret copied correctly (no spaces)
□ Client ID is correct
□ Tenant ID is correct
□ API permissions granted
□ Admin consent given (green checkmarks)
□ Dataverse URL is correct (include https://)

Test token manually:
- Use PowerShell script above
- Should get access_token in response
```

### **Issue: Permission denied**

```
Fix:
1. Go to app registration
2. API permissions
3. Verify "user_impersonation" is there
4. Click "Grant admin consent"
5. Wait 5 minutes for propagation
6. Try again
```

### **Issue: MCP server won't start**

```
Check:
□ Node.js installed (node --version)
□ MCP server built (npm run build)
□ Config file valid JSON (no trailing commas)
□ Paths use double backslashes (C:\\path\\to\\file)
□ Claude Desktop restarted after config change
```

---

## 📋 QUICK REFERENCE

### **Important URLs:**

```
Developer Portal:
https://developer.microsoft.com/microsoft-365/profile

Power Platform Admin:
https://admin.powerplatform.microsoft.com

Azure Portal:
https://portal.azure.com

Power Apps Maker:
https://make.powerapps.com

Dataverse API Docs:
https://learn.microsoft.com/power-apps/developer/data-platform/webapi/overview
```

### **Your Credentials (Store Securely):**

```
Environment URL: _________________________________
Tenant ID: _________________________________
Client ID: _________________________________
Client Secret: _________________________________ (expires: ________)
Secret Expiration: [24 months from creation]
Created: November 21, 2025
```

---

## ✅ SUCCESS CRITERIA

**You're ready when:**

```
✅ Can authenticate to Dataverse via MCP
✅ Can query entities (even if empty)
✅ MCP server connects without errors
✅ Request logging works (see log file)
✅ Rate limiting enabled (config shows true)
✅ Circuit breaker enabled (config shows true)
✅ No connection to RESA production
✅ All safeguards active
```

---

## 🎯 NEXT STEPS

**Now that you have isolated dev environment:**

1. **Import Your Current Solution**
   - Export from RESA production (if you have access)
   - Import to your dev environment
   - Now you have safe copy to modify

2. **Build Your MCP Servers**
   - Dataverse MCP with all safeguards
   - Validation MCP
   - Testing MCP
   - Documentation MCP

3. **Test Aggressively**
   - Make API calls
   - Test rate limiting
   - Test circuit breaker
   - Test error handling
   - Break things and learn

4. **Develop New Features**
   - Add tables/fields
   - Build Power Apps
   - Create automations
   - Test thoroughly

5. **Export & Import to Production**
   - When ready and tested
   - Manual import only
   - Pilot users first
   - Monitor closely

---

## 💰 COST SUMMARY

```
Your Development Environment:
├── Microsoft 365 Developer Program: $0/month
├── Dataverse environment: $0/month
├── Power Apps/Automate: $0/month
├── 25 test user licenses: $0/month
├── Microsoft Graph API: $0/month
├── Azure AD Premium: $0/month
└── Total Monthly Cost: $0

Optional Paid Services (only if needed):
├── Azure Pay-As-You-Go: ~$50-100/month
│   (Only for production-grade load testing)
│   (99% of development doesn't need this)
└── Total Optional: $0-100/month

Recommendation: Start with $0/month free tier
             Add paid only if you hit limits (unlikely)
```

---

**🎉 Congratulations! You now have a complete, isolated, FREE development platform with zero risk to production!**

**Start building with confidence. Break things. Learn. Iterate. When it's perfect, import to production.**

---

**Document Version:** 1.0  
**Created:** November 21, 2025  
**Status:** Ready to use  
**Next:** Complete Step-by-Step Setup Above
