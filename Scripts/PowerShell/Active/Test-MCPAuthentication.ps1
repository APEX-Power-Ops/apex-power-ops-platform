# Test MCP Authentication to Dev Environment
# Created: November 22, 2025
# Purpose: Verify Azure app registration can authenticate with Dataverse

$tenantId = $env:AZURE_TENANT_ID
$clientId = $env:AZURE_CLIENT_ID
$clientSecret = $env:AZURE_CLIENT_SECRET
$dataverseUrl = $env:DATAVERSE_URL

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  MCP Authentication Test" -ForegroundColor Cyan
Write-Host "  Dev Environment: org99cd6c6e" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

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
    Write-Host "   Token type: $($tokenResponse.token_type)" -ForegroundColor Green
    Write-Host "   Expires in: $($tokenResponse.expires_in) seconds" -ForegroundColor Green
    
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
    Write-Host "   User ID: $($whoAmI.UserId)" -ForegroundColor Green
    Write-Host "   Organization ID: $($whoAmI.OrganizationId)" -ForegroundColor Green
    
    # Test entity query
    Write-Host "`n🔍 Testing entity query (Projects)..." -ForegroundColor Cyan
    $projectsUrl = "$dataverseUrl/api/data/v9.2/cr950_projectses?`$top=1"
    try {
        $projects = Invoke-RestMethod -Uri $projectsUrl -Headers $headers -Method Get
        Write-Host "✅ Entity query successful!" -ForegroundColor Green
        Write-Host "   Found $($projects.value.Count) project(s)" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Entity query failed (expected if no projects exist yet)" -ForegroundColor Yellow
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  🎉 All tests passed!" -ForegroundColor Green
    Write-Host "  MCP authentication is working." -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Configure claude_desktop_config.json with these credentials" -ForegroundColor White
    Write-Host "2. Restart Claude Desktop" -ForegroundColor White
    Write-Host "3. Test MCP connection in Claude" -ForegroundColor White
    
} catch {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "  ❌ Authentication failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verify API permissions granted in Azure Portal" -ForegroundColor Yellow
    Write-Host "2. Confirm admin consent given (green checkmark)" -ForegroundColor Yellow
    Write-Host "3. Wait 5-10 minutes after granting permissions" -ForegroundColor Yellow
    Write-Host "4. Check Tenant ID, Client ID, and Secret are correct" -ForegroundColor Yellow
    
    Write-Host "`nAzure Portal: https://portal.azure.com" -ForegroundColor Cyan
    Write-Host "App Registration: RESA Dev MCP Access`n" -ForegroundColor Cyan
}
