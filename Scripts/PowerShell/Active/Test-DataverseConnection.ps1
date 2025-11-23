# Test-DataverseConnection.ps1
# RESA Power Build - Dataverse Connection Verification
# Tests the SINGLE active environment: org99cd6c6e.crm.dynamics.com

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESA Power Build" -ForegroundColor Cyan
Write-Host "  Dataverse Connection Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Testing RESA-Dev Environment..." -ForegroundColor Yellow
Write-Host "  URL: https://org99cd6c6e.crm.dynamics.com"
Write-Host "  Tenant: 270d5723-4b30-4f3b-b9cb-6527be741b42"
Write-Host "  App: RESA-Dev-MCP-Access`n"

# Environment credentials from RESA-Dev-MCP-Access.txt
$env = @{
    Name = "RESA-Dev Environment"
    TenantId = "270d5723-4b30-4f3b-b9cb-6527be741b42"
    ClientId = "9df3350f-b3b4-47c4-97b5-499a8b02acc7"
    ClientSecret = "uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k"
    DataverseUrl = "https://org99cd6c6e.crm.dynamics.com"
}

try {
    # Step 1: Authenticate
    Write-Host "[1/4] Testing Azure AD authentication..." -ForegroundColor Yellow
    
    $body = @{
        client_id = $env.ClientId
        scope = "$($env.DataverseUrl)/.default"
        client_secret = $env.ClientSecret
        grant_type = "client_credentials"
    }
    
    $tokenUrl = "https://login.microsoftonline.com/$($env.TenantId)/oauth2/v2.0/token"
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method POST -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
    
    if ($tokenResponse.access_token) {
        Write-Host "      ✅ Authentication successful!" -ForegroundColor Green
        Write-Host "      Token expires in: $($tokenResponse.expires_in / 60) minutes`n"
    }
    
    # Step 2: Test Dataverse access
    Write-Host "[2/4] Testing Dataverse API access..." -ForegroundColor Yellow
    
    $headers = @{
        Authorization = "Bearer $($tokenResponse.access_token)"
        "OData-MaxVersion" = "4.0"
        "OData-Version" = "4.0"
        Accept = "application/json"
    }
    
    $testUrl = "$($env.DataverseUrl)/api/data/v9.2/EntityDefinitions?`$top=1&`$select=LogicalName"
    $apiResponse = Invoke-RestMethod -Uri $testUrl -Headers $headers -ErrorAction Stop
    
    Write-Host "      ✅ Dataverse API accessible!" -ForegroundColor Green
    Write-Host "      Connected to: $($env.DataverseUrl)`n"
    
    # Step 3: Check for RESA Power solution
    Write-Host "[3/4] Checking for RESA Power solution tables..." -ForegroundColor Yellow
    
    $tables = @{
        "cr950_projects" = "Projects (Core)"
        "cr950_projectscope" = "Project Scopes"
        "cr950_tasks" = "Tasks"
        "cr950_apparatus" = "Apparatus"
        "cr950_client" = "Clients (v1.4.0.0)"
        "cr950_site" = "Sites (v1.4.0.0)"
        "cr950_employee" = "Employees (v1.4.0.0)"
        "cr950_quote" = "Quotes (v1.4.0.0)"
    }
    
    $foundTables = 0
    $totalTables = $tables.Count
    
    foreach ($table in $tables.Keys) {
        $checkUrl = "$($env.DataverseUrl)/api/data/v9.2/EntityDefinitions?`$filter=LogicalName eq '$table'&`$select=LogicalName"
        try {
            $checkResponse = Invoke-RestMethod -Uri $checkUrl -Headers $headers -ErrorAction Stop
            if ($checkResponse.value.Count -gt 0) {
                Write-Host "      ✅ Found: $($tables[$table])" -ForegroundColor Green
                $foundTables++
            } else {
                Write-Host "      ❌ Missing: $($tables[$table])" -ForegroundColor Red
            }
        } catch {
            Write-Host "      ❌ Missing: $($tables[$table])" -ForegroundColor Red
        }
    }
    
    Write-Host "`n      📊 Found $foundTables of $totalTables tables`n"
    
    # Step 4: Check record counts
    Write-Host "[4/4] Checking record counts..." -ForegroundColor Yellow
    
    if ($foundTables -gt 0) {
        try {
            $recordsUrl = "$($env.DataverseUrl)/api/data/v9.2/cr950_projectses?`$count=true&`$top=1&`$select=cr950_projectsid"
            $recordsResponse = Invoke-RestMethod -Uri $recordsUrl -Headers $headers -ErrorAction SilentlyContinue
            
            if ($recordsResponse.'@odata.count' -ne $null) {
                Write-Host "      📋 Projects: $($recordsResponse.'@odata.count') records" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "      ⚠️  Could not query record counts" -ForegroundColor Yellow
        }
    }
    
    # Summary
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  TEST RESULTS" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    if ($foundTables -eq $totalTables) {
        Write-Host "  🎯 SUCCESS: Complete v1.4.0.0 deployment detected!" -ForegroundColor Green -BackgroundColor DarkGreen
        Write-Host "  ✅ All tables present and accessible" -ForegroundColor Green
        Write-Host "  ✅ Ready for MCP development`n" -ForegroundColor Green
    } elseif ($foundTables -ge 4) {
        Write-Host "  ⚠️  PARTIAL: Core tables found ($foundTables/$totalTables)" -ForegroundColor Yellow
        Write-Host "  ⚠️  Some v1.4.0.0 tables missing" -ForegroundColor Yellow
        Write-Host "  💡 May need to import/update solution`n" -ForegroundColor Yellow
    } else {
        Write-Host "  ❌ WARNING: RESA Power solution not detected" -ForegroundColor Red
        Write-Host "  ❌ Only $foundTables of $totalTables tables found" -ForegroundColor Red
        Write-Host "  💡 Solution may need to be imported`n" -ForegroundColor Red
    }
    
    Write-Host "CONFIGURATION FOR MCP SERVERS:" -ForegroundColor Yellow
    Write-Host "================================" -ForegroundColor Yellow
    Write-Host "DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com"
    Write-Host "AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42"
    Write-Host "AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7"
    Write-Host "AZURE_CLIENT_SECRET=uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k"
    Write-Host "ENVIRONMENT=DEVELOPMENT`n"
    
    Write-Host "NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "1. Create .env file with these credentials"
    Write-Host "2. Update Claude Desktop config: %APPDATA%\Claude\claude_desktop_config.json"
    Write-Host "3. Start building resa-testing-mcp`n"
    
} catch {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "  TEST FAILED" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Red
    
    Write-Host "❌ Connection failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)`n" -ForegroundColor Red
    
    if ($_.Exception.Message -like "*401*") {
        Write-Host "POSSIBLE CAUSES:" -ForegroundColor Yellow
        Write-Host "  • Client secret has expired" -ForegroundColor Yellow
        Write-Host "  • Client secret is incorrect" -ForegroundColor Yellow
        Write-Host "  • App registration permissions not granted`n" -ForegroundColor Yellow
        
        Write-Host "SOLUTIONS:" -ForegroundColor Yellow
        Write-Host "  1. Login to Azure Portal: https://portal.azure.com" -ForegroundColor Yellow
        Write-Host "  2. Navigate to Azure Active Directory → App Registrations" -ForegroundColor Yellow
        Write-Host "  3. Find 'RESA-Dev-MCP-Access' (9df3350f-b3b4-47c4-97b5-499a8b02acc7)" -ForegroundColor Yellow
        Write-Host "  4. Check Certificates & Secrets → Generate new secret if expired" -ForegroundColor Yellow
        Write-Host "  5. Update RESA-Dev-MCP-Access.txt with new secret`n" -ForegroundColor Yellow
        
    } elseif ($_.Exception.Message -like "*404*") {
        Write-Host "POSSIBLE CAUSES:" -ForegroundColor Yellow
        Write-Host "  • Dataverse URL is incorrect" -ForegroundColor Yellow
        Write-Host "  • Environment has been deleted/moved`n" -ForegroundColor Yellow
        
    } else {
        Write-Host "TROUBLESHOOTING:" -ForegroundColor Yellow
        Write-Host "  1. Check internet connection" -ForegroundColor Yellow
        Write-Host "  2. Verify credentials in RESA-Dev-MCP-Access.txt" -ForegroundColor Yellow
        Write-Host "  3. Check Azure Portal for app registration status`n" -ForegroundColor Yellow
    }
}

Write-Host "========================================`n" -ForegroundColor Cyan
