# RESA POWER BUILD - ENVIRONMENT QUICK REFERENCE
## ⚡ Single Active Environment Only

**Last Updated:** November 23, 2025

---

## 🎯 THE ONLY ENVIRONMENT YOU NEED

```
URL:         https://org99cd6c6e.crm.dynamics.com
Tenant:      270d5723-4b30-4f3b-b9cb-6527be741b42
Client:      9df3350f-b3b4-47c4-97b5-499a8b02acc7
Secret:      REDACTED-AZURE-AD-CLIENT-SECRET-2026-05-27-1
Org ID:      e550d661-edc7-f011-8729-000d3a33a005
App:         RESA-Dev-MCP-Access
```

---

## ⚡ MONDAY MORNING - 3 COMMANDS

```powershell
# 1. Test connection (15 minutes)
.\Scripts\PowerShell\Test-DataverseConnection.ps1

# 2. Create .env file (10 minutes)
@"
AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
AZURE_CLIENT_SECRET=REDACTED-AZURE-AD-CLIENT-SECRET-2026-05-27-1
DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
ENVIRONMENT=DEVELOPMENT
"@ | Out-File .env -Encoding UTF8

# 3. Start building
cd MCP_Servers
mkdir resa-testing-mcp
cd resa-testing-mcp
npm init -y
```

---

## 🚫 IGNORE THESE (OLD/OUTDATED)

❌ orgf05a3756.crm.dynamics.com  
❌ org04ad071f.crm.dynamics.com  
❌ 6f93b183-1bd3-41c6-bdf7-eefcc992ae6f  
❌ 19f68ef1-90a0-4813-be5f-22bb10dd9afd

**If you see these anywhere → IGNORE and use org99cd6c6e instead**

---

## 📱 QUICK CONTACT

- Azure Portal: https://portal.azure.com
- Power Platform: https://make.powerapps.com
- App Registration: RESA-Dev-MCP-Access
- Environment: RESA-Dev (org99cd6c6e)

---

## ✅ MONDAY CHECKLIST

- [ ] Run Test-DataverseConnection.ps1
- [ ] Create .env file
- [ ] Configure Claude Desktop
- [ ] Start resa-testing-mcp
- [ ] Test MCP connection

---

**Print this page and keep it handy!**
