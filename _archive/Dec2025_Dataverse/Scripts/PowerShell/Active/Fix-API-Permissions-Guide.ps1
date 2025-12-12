# ═══════════════════════════════════════════════════════════
# Azure App Registration - Permission Fix Guide
# Issue: 401 Unauthorized when accessing Dataverse Metadata API
# ═══════════════════════════════════════════════════════════

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║  ⚠️  DATAVERSE API PERMISSION ISSUE DETECTED            ║" -ForegroundColor Red
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Red

Write-Host "`n📋 PROBLEM:" -ForegroundColor Yellow
Write-Host "   Your app registration can access Dataverse data (records)" -ForegroundColor White
Write-Host "   but CANNOT access Dataverse metadata (table definitions)." -ForegroundColor White
Write-Host "`n   This requires additional API permissions in Azure AD." -ForegroundColor White

Write-Host "`n🔧 SOLUTION - Add API Permissions:" -ForegroundColor Cyan
Write-Host "`n   Step 1: Open Azure Portal" -ForegroundColor Green
Write-Host "   → https://portal.azure.com" -ForegroundColor Gray
Write-Host "   → Navigate to: Azure Active Directory > App registrations" -ForegroundColor Gray

Write-Host "`n   Step 2: Find Your App Registration" -ForegroundColor Green
Write-Host "   → Search for: RESA-Dev-MCP-Access" -ForegroundColor Gray
Write-Host "   → Application (client) ID: 9df3350f-b3b4-47c4-97b5-499a8b02acc7" -ForegroundColor Gray

Write-Host "`n   Step 3: Add API Permissions" -ForegroundColor Green
Write-Host "   → Click 'API permissions' in left menu" -ForegroundColor Gray
Write-Host "   → Click '+ Add a permission'" -ForegroundColor Gray
Write-Host "   → Select 'Dynamics CRM' (or 'Common Data Service')" -ForegroundColor Gray
Write-Host "   → Choose 'Application permissions' (not Delegated)" -ForegroundColor Gray
Write-Host "   → Check: ☑ user_impersonation" -ForegroundColor Gray
Write-Host "   → Click 'Add permissions'" -ForegroundColor Gray

Write-Host "`n   Step 4: Grant Admin Consent" -ForegroundColor Green
Write-Host "   → Click '✓ Grant admin consent for [Your Org]'" -ForegroundColor Gray
Write-Host "   → Confirm: Yes" -ForegroundColor Gray
Write-Host "   → Wait for green checkmarks to appear" -ForegroundColor Gray

Write-Host "`n   Step 5: Assign Security Role in Dataverse" -ForegroundColor Green
Write-Host "   → Open Power Platform Admin Center" -ForegroundColor Gray
Write-Host "   → https://admin.powerplatform.microsoft.com" -ForegroundColor Gray
Write-Host "   → Environments > org99cd6c6e > Settings > Users + permissions > Application users" -ForegroundColor Gray
Write-Host "   → Find 'RESA-Dev-MCP-Access' application user" -ForegroundColor Gray
Write-Host "   → Edit > Assign 'System Administrator' role" -ForegroundColor Gray
Write-Host "   → Save" -ForegroundColor Gray

Write-Host "`n   Step 6: Test Connection" -ForegroundColor Green
Write-Host "   → Run: .\Create-RollupFields-Complete.ps1" -ForegroundColor Gray
Write-Host "   → Should now succeed without 401 errors" -ForegroundColor Gray

Write-Host "`n📚 Alternative: Use PAC CLI (Requires Interactive Login)" -ForegroundColor Cyan
Write-Host "   If you can't modify app permissions, use PAC CLI instead:" -ForegroundColor White
Write-Host "   → pac auth create --url https://org99cd6c6e.crm.dynamics.com" -ForegroundColor Gray
Write-Host "   → This uses YOUR user credentials (interactive browser login)" -ForegroundColor Gray
Write-Host "   → Requires you have System Administrator role" -ForegroundColor Gray

Write-Host "`n🔍 Current App Details:" -ForegroundColor Cyan
Write-Host "   Tenant ID: 270d5723-4b30-4f3b-b9cb-6527be741b42 (JSwensonLLC)" -ForegroundColor Gray
Write-Host "   Client ID: 9df3350f-b3b4-47c4-97b5-499a8b02acc7 (RESA-Dev-MCP-Access)" -ForegroundColor Gray
Write-Host "   Environment: https://org99cd6c6e.crm.dynamics.com" -ForegroundColor Gray

Write-Host "`n⏱️  IMPORTANT:" -ForegroundColor Yellow
Write-Host "   After granting permissions, wait 5-10 minutes for changes" -ForegroundColor White
Write-Host "   to propagate through Azure AD and Dataverse systems." -ForegroundColor White

Write-Host "`n✨ Once permissions are granted, re-run your rollup script!" -ForegroundColor Green
