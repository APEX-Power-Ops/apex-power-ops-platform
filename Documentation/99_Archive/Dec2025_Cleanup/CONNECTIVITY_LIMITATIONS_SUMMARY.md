# RESA Power Project - Connectivity Limitations Summary

**Generated:** December 2, 2025  
**Purpose:** Document blockers preventing full system audit  
**Action Required:** Resolve before proceeding with schema audit

---

## Executive Summary

The RESA Power Project Tracker system audit cannot proceed due to **expired Dataverse authentication credentials**. This affects both Claude.ai (web) and Desktop Claude's ability to query live Dataverse tables for schema verification.

---

## 🚫 Limitation #1: Dataverse Authentication Failure

### Symptom
```
AUTH: FAILED - The remote server returned an error: (401) Unauthorized.
```

### Root Cause
The Azure AD client secret for the `RESA-Dev-MCP-Access` app registration has likely expired.

### Affected Credentials
| Parameter | Value | Status |
|-----------|-------|--------|
| **Tenant ID** | `270d5723-4b30-4f3b-b9cb-6527be741b42` | ✅ Valid |
| **Client ID** | `9df3350f-b3b4-47c4-97b5-499a8b02acc7` | ✅ Valid |
| **Client Secret** | `uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k` | ❌ **EXPIRED** |
| **Dataverse URL** | `https://org99cd6c6e.crm.dynamics.com` | ✅ Valid |

### Impact
- ❌ Cannot query `cr950_locations` to verify 4 expected records
- ❌ Cannot enumerate actual fields on any Dataverse table
- ❌ Cannot validate VS Claude's schema implementation against intended design
- ❌ Cannot test rollup field calculations
- ❌ Cannot verify relationship integrity

---

## 🔧 Resolution Steps

### Step 1: Generate New Client Secret in Azure Portal

1. Navigate to: https://portal.azure.com
2. Go to: **Azure Active Directory** → **App Registrations**
3. Find: `RESA-Dev-MCP-Access` (Client ID: `9df3350f-b3b4-47c4-97b5-499a8b02acc7`)
4. Click: **Certificates & secrets** → **Client secrets**
5. Click: **+ New client secret**
6. Set expiration: **12 months** (or longer for stability)
7. Copy the new secret value immediately (it won't be shown again)

### Step 2: Update Credential Storage

Update the following locations with the new client secret:

| Location | File/Setting | Purpose |
|----------|--------------|---------|
| **Desktop Claude MCP Config** | `%APPDATA%\Claude\claude_desktop_config.json` | Desktop Claude Dataverse access |
| **Local Credentials File** | `C:\RESA_Power_Build\Credentials\RESA-Dev-MCP-Access.txt` | Reference storage |
| **PowerShell Test Script** | `C:\RESA_Power_Build\Scripts\PowerShell\Test-DataverseConnection.ps1` | Connection testing |
| **VS Claude MCP Server** | Environment variables for `resa-dataverse-mcp` | VS Claude Dataverse access |

### Step 3: Verify Connectivity

Run the PowerShell test script after updating:
```powershell
cd C:\RESA_Power_Build\Scripts\PowerShell
.\Test-DataverseConnection.ps1
```

Expected output:
```
✅ Authentication successful!
✅ Dataverse API accessible!
✅ Found: Projects (Core)
✅ Found: Project Scopes
...
```

---

## 📋 What I CAN Do Without Live Connectivity

While credentials are being refreshed, I can perform **offline analysis** using:

| Resource | Location | What It Provides |
|----------|----------|------------------|
| `customizations.xml` | `/mnt/project/customizations.xml` (816KB) | Full schema export from Dataverse solution |
| CSV Templates | `/mnt/project/00_Locations_Template.csv` through `06_*.csv` | Intended field design |
| Nov 27 Audit | `/mnt/project/DATAVERSE_SCHEMA_AUDIT_20251127.md` | Previous schema analysis (16 tables, 565+ fields) |
| Complete Table Schemas | `/mnt/project/COMPLETE_TABLE_SCHEMAS.md` | Documented field inventory |

**Offline audit can identify:**
- ✅ Schema design gaps between CSV templates and customizations.xml
- ✅ Naming convention violations
- ✅ Missing calculated/rollup field definitions
- ✅ Relationship configuration issues

**Offline audit CANNOT verify:**
- ❌ Actual record counts (e.g., 4 locations exist)
- ❌ Live rollup field calculations
- ❌ Data integrity between related tables
- ❌ Runtime behavior of Power Automate flows

---

## 🎯 Recommended Action Plan

### Immediate (Today)
1. **Generate new Azure AD client secret** (5 minutes)
2. **Update Desktop Claude config** with new secret (2 minutes)
3. **Update VS Claude MCP server config** with new secret (2 minutes)
4. **Run connectivity test** to confirm (2 minutes)

### After Credentials Restored
1. Resume full system audit with live Dataverse queries
2. Verify all 4 locations exist in `cr950_locations`
3. Enumerate actual fields on all 8+ tables
4. Compare live schema against CSV template specifications
5. Generate gap analysis with prioritized fixes

---

## 📞 Additional Context

### Why This Matters
- The schema audit is comparing **VS Claude's actual Dataverse implementation** against **intended design in CSV templates**
- Without live connectivity, we can only compare documentation against documentation
- Live queries are essential to catch implementation drift or errors

### MCP Server Status (Desktop Claude)
The `resa-dataverse-mcp` server configuration in Desktop Claude likely has the same expired secret. After updating Azure AD, update:

```json
// %APPDATA%\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "resa-dataverse": {
      "env": {
        "AZURE_CLIENT_SECRET": "<NEW_SECRET_HERE>"
      }
    }
  }
}
```

### Timeline Impact
- **Blocked:** Full schema audit against live Dataverse
- **Not Blocked:** Offline documentation analysis, architecture review
- **Estimated Delay:** 15-30 minutes once credentials are refreshed

---

## ✅ Confirmation Checklist

After resolving, confirm these work:

- [ ] PowerShell `Test-DataverseConnection.ps1` returns SUCCESS
- [ ] Desktop Claude can query Dataverse via MCP tools
- [ ] VS Claude can query Dataverse via its MCP server
- [ ] Query `cr950_locations` returns 4 records (Phoenix, Denver, San Diego, Las Vegas)

---

**Document Version:** 1.0  
**Created By:** Claude.ai (Web)  
**Status:** AWAITING CREDENTIAL REFRESH
