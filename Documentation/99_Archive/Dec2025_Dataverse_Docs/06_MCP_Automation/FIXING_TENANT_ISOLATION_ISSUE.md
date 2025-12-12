# FIXING DEVELOPER ENVIRONMENT - Isolate from Company Tenant

**Date:** November 21, 2025  
**Issue:** Developer subscription linked to company tenant instead of isolated  
**Solution:** Create new developer subscription with personal Microsoft account  

---

## 🚨 THE PROBLEM

```
Current Situation:
├── Signed up with: jason@resapower.com (work email)
├── Result: Linked to RESA's Microsoft 365 tenant
├── Admin portal shows: RESA company environment
├── NOT isolated from production
└── Risk: Changes could affect production systems

What We Need:
├── Completely separate Microsoft tenant
├── Zero connection to RESA
├── Your own admin access
├── Safe sandbox for development
└── New Dataverse environment (isolated)
```

---

## ✅ SOLUTION: CREATE TRULY ISOLATED ENVIRONMENT

### **Step 1: Sign Out of Work Account (1 minute)**

```
1. Go to: https://developer.microsoft.com/microsoft-365/dev-program

2. Click your profile icon (top right)

3. Click "Sign out"

4. Close browser (ensure fully signed out)

5. Open new incognito/private browser window
```

---

### **Step 2: Create Personal Microsoft Account (5 minutes)** 

**If you already have personal Microsoft account (Outlook, Hotmail, Xbox, etc.):**
- Skip to Step 3
- Use existing account

**If you need to create one:**

```
1. Go to: https://signup.live.com

2. Click "Get a new email address"

3. Choose one:
   Option A: yourname@outlook.com
   Option B: yourname@hotmail.com
   Option C: Use existing Gmail/Yahoo (click "Use your email instead")

4. Create password

5. Verify email/phone

6. Complete setup

Result: Personal Microsoft account (NOT connected to RESA)
```

**Recommended Format:**
```
Email: jason.swenson.dev@outlook.com
      (or)
      yourpreferred@outlook.com
      (or)
      use existing personal email

Purpose: Completely separate from RESA for development
```

---

### **Step 3: Join Developer Program with Personal Account (5 minutes)**

```
1. Go to: https://developer.microsoft.com/microsoft-365/dev-program

2. Click "Join now" (or "Sign in" if you see it)

3. Sign in with PERSONAL Microsoft account
   (NOT work email!)

4. Fill out profile:
   - Country/Region: United States
   - Company: Personal Development / Independent
   - Language: English
   - What are you interested in: Building solutions
   
5. Accept terms

6. Click "Setup E5 subscription"

7. Choose:
   - Admin username: jasondev (or your choice)
   - Domain: [username].onmicrosoft.com
   - Example: jasondev.onmicrosoft.com
   - Password: [create strong password - SAVE THIS!]
   
8. Add phone number (SMS verification)

9. Click "Continue"

10. Wait 2-3 minutes for provisioning
```

**What Gets Created:**
```
✅ NEW Microsoft 365 tenant (completely separate from RESA)
✅ NEW domain: jasondev.onmicrosoft.com
✅ NEW admin account: admin@jasondev.onmicrosoft.com
✅ NEW Dataverse environment
✅ 25 user licenses (for testing)
✅ Zero connection to RESA systems
```

---

### **Step 4: Access Your New Isolated Admin Portal (2 minutes)**

```
1. Go to: https://admin.microsoft.com

2. Sign in with NEW admin account:
   Email: admin@jasondev.onmicrosoft.com
   Password: [password you created in step 3]

3. You should see:
   ✅ YOUR tenant name (jasondev)
   ✅ YOUR domain (jasondev.onmicrosoft.com)
   ✅ Clean, empty tenant (no RESA data)
   ✅ 25 Microsoft 365 E5 licenses
   
4. This is YOUR isolated sandbox ⭐
```

**Verify it's isolated:**
```
Check:
□ Tenant name is NOT "RESA Power" or company name
□ Domain is NOT resapower.com
□ Users list is empty (or just admin user)
□ No company data visible
□ You have full admin access

If you see any RESA/company data:
❌ You're still in company tenant
➡️ Sign out and try again with personal account
```

---

### **Step 5: Get Your New Dataverse Environment URL (5 minutes)**

```
1. Go to: https://admin.powerplatform.microsoft.com

2. Sign in with admin@jasondev.onmicrosoft.com

3. Click "Environments" (left menu)

4. You should see a default environment

5. If NOT, create one:
   - Click "+ New"
   - Name: "Jason Dev Environment"
   - Type: Developer
   - Region: United States (default)
   - Create database: Yes
   - Language: English
   - Currency: USD
   - Click "Save"
   - Wait 5-10 minutes for provisioning

6. Click environment name

7. Copy "Environment URL"
   Example: https://org12345678.crm.dynamics.com
   
   SAVE THIS: _________________________________
   
   This is YOUR isolated Dataverse URL
```

---

### **Step 6: Update MCP Configuration (5 minutes)**

**Now configure MCP to use YOUR isolated environment (not RESA):**

**Location:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jason-dev-dataverse": {
      "command": "node",
      "args": [
        "C:\\RESA_Power_Build\\MCP_Servers\\safe-dataverse-mcp\\build\\index.js"
      ],
      "env": {
        "ENVIRONMENT": "PERSONAL_DEV",
        "DATAVERSE_URL": "https://YOUR-NEW-ORG.crm.dynamics.com",
        
        "AZURE_TENANT_ID": "your-new-tenant-id",
        "AZURE_CLIENT_ID": "your-new-client-id",
        "AZURE_CLIENT_SECRET": "your-new-client-secret",
        
        "MAX_REQUESTS_PER_MINUTE": "60",
        "MAX_CONCURRENT_REQUESTS": "5",
        "CIRCUIT_BREAKER_ENABLED": "true",
        "REQUEST_LOGGING": "true",
        "LOG_FILE": "C:\\RESA_Power_Build\\Logs\\mcp-dev-requests.log"
      }
    }
  }
}
```

**Get the new credentials:**

Follow authentication setup from previous guide:
1. Create app registration in YOUR new Azure portal
2. Get Tenant ID, Client ID, Client Secret
3. Grant Dynamics CRM permissions
4. Update MCP config above

---

### **Step 7: Verify Complete Isolation (5 minutes)**

**Critical checks:**

```powershell
# Test 1: Check which tenant you're in
# Go to: https://portal.azure.com
# Sign in with: admin@jasondev.onmicrosoft.com
# Top right should show: jasondev (NOT RESA)

# Test 2: Check Dataverse URL
# Your new URL: https://orgXXXXXX.crm.dynamics.com
# Should be DIFFERENT from RESA production
# RESA production: https://org04ad071f.crm.dynamics.com

# Test 3: Check admin portal
# https://admin.microsoft.com
# Should show YOUR tenant (jasondev)
# NOT show RESA company

# Test 4: Check for company data
# Dataverse should be EMPTY (no RESA data)
# Clean slate for development
```

---

## 🎯 WHAT YOU NOW HAVE

### **Two Completely Separate Environments:**

```
ENVIRONMENT 1: RESA PRODUCTION (Work Account)
├── Email: jason@resapower.com
├── Tenant: RESA Power
├── Domain: resapower.com
├── Dataverse: org04ad071f.crm.dynamics.com
├── Purpose: Production business systems
├── Access: Limited (standard user)
└── MCP Connection: ❌ NEVER connect MCP here

ENVIRONMENT 2: YOUR DEV SANDBOX (Personal Account)
├── Email: admin@jasondev.onmicrosoft.com
├── Tenant: jasondev
├── Domain: jasondev.onmicrosoft.com
├── Dataverse: orgXXXXXX.crm.dynamics.com (new)
├── Purpose: Safe development and testing
├── Access: Full admin (you own it)
└── MCP Connection: ✅ Connect MCP here
```

**Zero Connection Between Them:**
```
✅ Completely separate tenants
✅ Separate Dataverse instances
✅ Separate Azure AD
✅ Separate everything
✅ No data sharing
✅ No permission overlap
✅ No risk to production
```

---

## 🚀 DEVELOPMENT WORKFLOW

### **Safe Development Process:**

```
STEP 1: BUILD IN YOUR DEV ENVIRONMENT
├── Sign in: admin@jasondev.onmicrosoft.com
├── Connect: MCP to YOUR Dataverse
├── Build: Tables, apps, flows
├── Test: Aggressively, break things
├── Perfect: Iterate until working
└── Result: Tested, validated solution

STEP 2: EXPORT FROM YOUR DEV
├── Go to: https://make.powerapps.com (your tenant)
├── Solutions → Select solution
├── Export solution (managed)
├── Download .zip file
└── Save to: Box/GitHub for backup

STEP 3: IMPORT TO RESA PRODUCTION (When Ready)
├── Sign in: jason@resapower.com (work account)
├── Go to: RESA admin portal
├── Import solution .zip
├── Map connections
├── Test with pilot users
└── Monitor closely

STEP 4: ITERATE
├── Find issues in production
├── Go back to YOUR dev environment
├── Fix in isolated sandbox
├── Test thoroughly
├── Export and import again
```

---

## 📋 CREDENTIALS TO SAVE

### **Your New Dev Environment:**

```
Personal Microsoft Account:
Email: _________________________________
Password: _________________________________ 

Developer Tenant:
Admin Username: admin@____________.onmicrosoft.com
Admin Password: _________________________________
Tenant ID: _________________________________
Domain: _____________.onmicrosoft.com

Dataverse:
Environment URL: _________________________________
Environment Name: _________________________________

App Registration (for MCP):
Application (Client) ID: _________________________________
Client Secret: _________________________________
Secret Expiration: _____________ (24 months from creation)

Created: November 21, 2025
Purpose: Isolated development environment for RESA Power solution
```

**Store Securely:**
- Password manager (1Password, LastPass)
- Encrypted file
- Secure notes

---

## 🔐 SECURITY REMINDERS

```
✅ DO:
- Use personal account for dev environment
- Keep dev and production completely separate
- Test everything in dev first
- Export/import solutions manually
- Store credentials securely

❌ DON'T:
- Mix dev and production accounts
- Connect MCP to RESA production
- Share dev environment credentials
- Deploy untested solutions
- Store credentials in code/GitHub
```

---

## 🆘 TROUBLESHOOTING

### **Issue: Still seeing RESA admin portal**

```
Solution:
1. Sign out completely (all browser tabs)
2. Clear browser cookies for microsoft.com
3. Open incognito/private window
4. Go to admin.microsoft.com
5. Sign in with admin@jasondev.onmicrosoft.com
6. Should see YOUR tenant (not RESA)

If still seeing RESA:
- Wrong account signed in
- Check top right for which account is active
- Make sure using personal account, not work account
```

### **Issue: Can't create developer subscription with personal account**

```
Possible reasons:
1. Already have developer subscription with that account
   → Check https://developer.microsoft.com/microsoft-365/profile
   
2. Account too new (needs to age)
   → Wait 24 hours and try again
   
3. Region restrictions
   → Ensure country set to United States
   
4. Already at limit (rare)
   → Each Microsoft account can have 1 developer subscription
```

### **Issue: Don't have personal Microsoft account**

```
Create one (free):
1. Go to: https://signup.live.com
2. Get new email: yourname@outlook.com
3. Or use existing: Gmail, Yahoo, etc.
4. Verify and complete setup
5. Use for developer program
```

---

## ✅ VERIFICATION CHECKLIST

**You have true isolation when:**

```
□ Signed up with personal email (NOT work email)
□ New tenant created (yourname.onmicrosoft.com)
□ Admin portal shows YOUR tenant (not RESA)
□ No company data visible in environment
□ New Dataverse URL (different from RESA)
□ Full admin access to everything
□ Can create users, apps, environments freely
□ Zero connection to RESA systems
□ MCP configured to use YOUR Dataverse
□ Can test without any production risk
```

---

## 🎉 SUCCESS!

**When complete, you have:**

```
✅ Personal Microsoft 365 Developer subscription
✅ Completely isolated from RESA
✅ Your own Dataverse environment
✅ 25 user licenses for testing
✅ Full admin control
✅ Safe sandbox for MCP servers
✅ Zero risk to production
✅ Free for 90 days (renewable)

Cost: $0/month
Value: $1,925/month if purchased
Purpose: Safe development platform
Risk to RESA: Zero (completely isolated)
```

---

**Next Step:** Complete authentication setup (app registration) in YOUR new tenant, then configure MCP server to connect to YOUR isolated Dataverse.

**Remember:** You now manage TWO separate accounts:
1. **Work account** - RESA production (view only, no MCP)
2. **Personal account** - Your dev sandbox (full admin, MCP enabled)

Keep them separate. Build in dev. Import to production when ready. 🎯
