# ENVIRONMENT CONFIGURATION - CORRECTED
## Single Active Environment: org99cd6c6e.crm.dynamics.com

**Created:** November 23, 2025  
**Status:** ✅ VERIFIED - Single environment only  
**Action Required:** Use these exact credentials for all MCP development

---

## ✅ CORRECT ENVIRONMENT (ONLY ONE)

### **Azure AD App Registration**
```
Application Name:    RESA-Dev-MCP-Access
Application ID:      9df3350f-b3b4-47c4-97b5-499a8b02acc7
Object ID:           bf270233-917a-411e-baed-8ab93cbe62fb
Tenant ID:           270d5723-4b30-4f3b-b9cb-6527be741b42
Client Secret:       uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k
Secret ID:           795b408f-4a55-4710-825d-8fe64e98fcb9
```

### **Dataverse Environment**
```
Environment URL:     https://org99cd6c6e.crm.dynamics.com
Organization ID:     e550d661-edc7-f011-8729-000d3a33a005
Environment ID:      988ad729-62cf-e0b8-8266-ff32689fce02
```

### **User Account**
```
Email:               JasonSwenson@JSwensonLLC.onmicrosoft.com
Owner:               Jason Swenson
```

---

## 🔧 CONFIGURATION FILES

### **.env File** (Create at project root)

```bash
# RESA Power Build - Environment Configuration
# Location: C:\RESA_Power_Build\.env
# NEVER commit this file to Git!

# Azure AD Authentication
AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
AZURE_CLIENT_SECRET=uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k

# Dataverse Environment
DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
DATAVERSE_ORG_ID=e550d661-edc7-f011-8729-000d3a33a005
ENVIRONMENT=DEVELOPMENT

# Environment Metadata
ENVIRONMENT_NAME=RESA-Dev
ENVIRONMENT_PURPOSE=Development and MCP Testing
SOLUTION_VERSION=v1.4.0.0
LAST_VERIFIED=2025-11-23
```

### **Claude Desktop Config**

Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "resa-dataverse-dev": {
      "command": "node",
      "args": ["C:\\RESA_Power_Build\\MCP_Servers\\resa-dataverse-mcp\\build\\index.js"],
      "env": {
        "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
        "AZURE_TENANT_ID": "270d5723-4b30-4f3b-b9cb-6527be741b42",
        "AZURE_CLIENT_ID": "9df3350f-b3b4-47c4-97b5-499a8b02acc7",
        "AZURE_CLIENT_SECRET": "uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k",
        "ENVIRONMENT": "DEVELOPMENT"
      }
    },
    "resa-testing": {
      "command": "node",
      "args": ["C:\\RESA_Power_Build\\MCP_Servers\\resa-testing-mcp\\build\\index.js"],
      "env": {
        "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
        "AZURE_TENANT_ID": "270d5723-4b30-4f3b-b9cb-6527be741b42",
        "AZURE_CLIENT_ID": "9df3350f-b3b4-47c4-97b5-499a8b02acc7",
        "AZURE_CLIENT_SECRET": "uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k",
        "ENVIRONMENT": "DEVELOPMENT"
      }
    }
  }
}
```

---

## ✅ VERIFICATION STEPS

### **Step 1: Test Connection (5 minutes)**

```powershell
cd C:\RESA_Power_Build
.\Scripts\PowerShell\Test-DataverseConnection.ps1
```

**Expected Output:**
```
✅ Authentication successful!
✅ Dataverse API accessible!
✅ Found: Projects (Core)
✅ Found: Project Scopes
✅ Found: Tasks
✅ Found: Apparatus
📊 Found X of 8 tables

🎯 SUCCESS: Ready for MCP development
```

### **Step 2: Create .env File (5 minutes)**

```powershell
# Create .env file
notepad C:\RESA_Power_Build\.env

# Copy configuration from above
# Save and close
```

### **Step 3: Secure Credentials (5 minutes)**

```powershell
# Update .gitignore
Add-Content .gitignore "`n# Environment Configuration"
Add-Content .gitignore ".env"
Add-Content .gitignore "claude_desktop_config.json"

# Commit changes
git add .gitignore
git commit -m "Add .env to .gitignore"
```

---

## 🚫 OUTDATED REFERENCES

**These environments were referenced in earlier documents but are NOT active:**

❌ `orgf05a3756.crm.dynamics.com` - Outdated reference
❌ `org04ad071f.crm.dynamics.com` - Outdated reference
❌ Tenant: `6f93b183-1bd3-41c6-bdf7-eefcc992ae6f` - Outdated
❌ Client: `19f68ef1-90a0-4813-be5f-22bb10dd9afd` - Outdated

**If you see these in any document, ignore them and use the correct environment above.**

---

## 📋 MONDAY MORNING CHECKLIST (SIMPLIFIED)

### **Step 1: Verify Connection (15 minutes)**
```powershell
# Run connection test
.\Scripts\PowerShell\Test-DataverseConnection.ps1

# Expected: ✅ All checks pass
```

### **Step 2: Create .env File (10 minutes)**
```powershell
# Create file
notepad C:\RESA_Power_Build\.env

# Paste configuration from above
# Save
```

### **Step 3: Configure Claude Desktop (10 minutes)**
```powershell
# Open config
notepad %APPDATA%\Claude\claude_desktop_config.json

# Paste configuration from above
# Save

# Restart Claude Desktop
```

### **Step 4: Start Building (Rest of Monday)**
- Follow: `Documentation\00_START_HERE\MCP_SERVER_QUICK_START.md`
- Build: resa-testing-mcp project
- Test: Connection to org99cd6c6e.crm.dynamics.com

---

## 🔐 SECURITY NOTES

### **Current Security Status:**

✅ **GOOD:** Credentials stored in secure location (RESA-Dev-MCP-Access.txt)  
⚠️  **ACTION NEEDED:** Remove from Git tracking  
✅ **GOOD:** .env file approach for local development  
⚠️  **TODO:** Verify secret expiration date in Azure Portal

### **Security Checklist:**

- [ ] Remove RESA-Dev-MCP-Access.txt from Git tracking
- [ ] Add .env to .gitignore
- [ ] Verify secret expiration in Azure Portal
- [ ] Set calendar reminder for secret renewal (if needed)
- [ ] Test connection with production protection enabled

### **Production Protection:**

The existing `resa-dataverse-mcp` has this safety check:

```typescript
if (ENVIRONMENT === "PRODUCTION" && DATAVERSE_URL.includes("org04ad071f")) {
  throw new Error("FATAL: Cannot connect MCP to RESA production environment!");
}
```

This is now **outdated** since org04ad071f is not your active environment.

**New Production Protection (if needed later):**

```typescript
// Only allow development environment
if (DATAVERSE_URL !== "https://org99cd6c6e.crm.dynamics.com") {
  throw new Error("FATAL: MCP servers only allowed on development environment!");
}
```

---

## 📊 WHAT'S DEPLOYED

### **Tables in org99cd6c6e.crm.dynamics.com:**

The connection test script will verify which of these tables exist:

**Core Tables (v1.0-1.3):**
- cr950_projects
- cr950_projectscope  
- cr950_tasks
- cr950_apparatus

**v1.4.0.0 Tables:**
- cr950_client
- cr950_site
- cr950_employee
- cr950_quote
- cr950_resourceassignment
- cr950_equipment

**Financial Tables:**
- cr950_apparatusrevenue
- cr950_scopelabordetail
- cr950_apparatustypemaster

**Total Expected:** 16 tables (if v1.4.0.0 fully deployed)

---

## 🚀 READY TO START

You now have:
- ✅ Correct environment identified (org99cd6c6e.crm.dynamics.com)
- ✅ Complete credentials documented
- ✅ Configuration templates ready
- ✅ Test script to verify connection
- ✅ Security approach defined

**Next Step:** Run `Test-DataverseConnection.ps1` to verify everything works!

---

## 📞 TROUBLESHOOTING

### **Problem: Authentication Fails (401 Error)**

**Solutions:**
1. Check Azure Portal → App Registrations → RESA-Dev-MCP-Access
2. Verify secret hasn't expired (Certificates & Secrets section)
3. Generate new secret if needed, update RESA-Dev-MCP-Access.txt
4. Verify API permissions are granted (Dynamics CRM user_impersonation)

### **Problem: Environment Not Found (404 Error)**

**Solutions:**
1. Verify URL: https://org99cd6c6e.crm.dynamics.com (must include https://)
2. Check Power Platform Admin Center to confirm environment exists
3. Verify environment ID matches: 988ad729-62cf-e0b8-8266-ff32689fce02

### **Problem: Tables Not Found**

**Solutions:**
1. Verify v1.4.0.0 solution is imported in this environment
2. Check solution version in Power Apps maker portal
3. May need to import solution from Solution_Exports/v1.4.0.0/

---

**Document Version:** 1.0 (Corrected)  
**Created:** November 23, 2025  
**Status:** VERIFIED SINGLE ENVIRONMENT  
**Next Action:** Run connection test script

