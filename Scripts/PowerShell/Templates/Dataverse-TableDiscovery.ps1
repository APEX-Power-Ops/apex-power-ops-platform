# Dataverse Table Discovery Template
# Created: November 30, 2025
# Purpose: Discover actual Dataverse table names, EntitySetNames, and validate schema
#
# BACKGROUND:
# Dataverse table names can be confusing:
#   - LogicalName: cr950_project (singular, used in metadata)
#   - EntitySetName: cr950_projectses (plural, used in API queries)
#   - Sometimes "apparatus" → "cr950_apparatuses"
#
# This template helps discover the correct names to use in Power Automate and API calls.
#
# USAGE:
#   1. Dot-source this file: . "C:\RESA_Power_Build\Scripts\PowerShell\Templates\Dataverse-TableDiscovery.ps1"
#   2. Call Connect-DataverseAPI to authenticate
#   3. Use Get-AllCustomTables to list all tables with correct API names
#   4. Use Test-TableQuery to verify a table name works
#
# ENVIRONMENT VARIABLES REQUIRED (loaded from .env file):
#   - AZURE_TENANT_ID
#   - AZURE_CLIENT_ID  
#   - AZURE_CLIENT_SECRET
#   - DATAVERSE_URL

# ============================================================================
# CONFIGURATION
# ============================================================================

$script:EnvFilePath = "C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\.env"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Load-EnvironmentVariables {
    if (-not $env:AZURE_TENANT_ID -or -not $env:AZURE_CLIENT_ID) {
        if (Test-Path $script:EnvFilePath) {
            Write-Host "📂 Loading environment variables from .env file..." -ForegroundColor Gray
            Get-Content $script:EnvFilePath | ForEach-Object {
                if ($_ -match '^([^=]+)=(.*)$') {
                    $name = $Matches[1].Trim()
                    $value = $Matches[2].Trim()
                    Set-Item -Path "env:$name" -Value $value
                }
            }
            Write-Host "   ✅ Loaded from: $($script:EnvFilePath)" -ForegroundColor Gray
        }
        else {
            Write-Host "❌ .env file not found at: $($script:EnvFilePath)" -ForegroundColor Red
            return $false
        }
    }
    return $true
}

# ============================================================================
# CONNECTION FUNCTION
# ============================================================================

function Connect-DataverseAPI {
    if (-not (Load-EnvironmentVariables)) { return $false }
    
    $script:Config = @{
        TenantId     = $env:AZURE_TENANT_ID
        ClientId     = $env:AZURE_CLIENT_ID
        ClientSecret = $env:AZURE_CLIENT_SECRET
        DataverseUrl = $env:DATAVERSE_URL
    }
    
    Write-Host "`n🔐 Connecting to Dataverse API..." -ForegroundColor Cyan
    
    $tokenUrl = "https://login.microsoftonline.com/$($script:Config.TenantId)/oauth2/v2.0/token"
    $body = @{
        client_id     = $script:Config.ClientId
        scope         = "$($script:Config.DataverseUrl)/.default"
        client_secret = $script:Config.ClientSecret
        grant_type    = "client_credentials"
    }
    
    try {
        $response = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
        $script:AuthToken = $response.access_token
        $script:Headers = @{
            Authorization       = "Bearer $($script:AuthToken)"
            "OData-MaxVersion"  = "4.0"
            "OData-Version"     = "4.0"
            Accept              = "application/json"
            "Content-Type"      = "application/json; charset=utf-8"
        }
        
        Write-Host "✅ Connected to Dataverse!" -ForegroundColor Green
        Write-Host "   Environment: $($script:Config.DataverseUrl)" -ForegroundColor Gray
        return $true
    }
    catch {
        Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# TABLE DISCOVERY FUNCTIONS
# ============================================================================

function Get-AllCustomTables {
    <#
    .SYNOPSIS
        List all custom tables with their correct API names (EntitySetName)
    .DESCRIPTION
        Returns a table showing LogicalName (metadata) vs EntitySetName (API queries)
    .EXAMPLE
        Get-AllCustomTables
    .EXAMPLE
        Get-AllCustomTables | Where-Object { $_.LogicalName -like "*project*" }
    #>
    
    if (-not $script:AuthToken) {
        Write-Host "⚠️  Not connected. Run Connect-DataverseAPI first." -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "DATAVERSE TABLE DISCOVERY" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    
    # Get ALL entities, then filter client-side (OData startswith on LogicalName not supported)
    $url = "$($script:Config.DataverseUrl)/api/data/v9.2/EntityDefinitions?`$select=LogicalName,EntitySetName,DisplayName"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $script:Headers -Method Get
        
        $tables = $response.value | 
            Where-Object { $_.LogicalName -like "cr950_*" } |
            ForEach-Object {
                [PSCustomObject]@{
                    LogicalName   = $_.LogicalName
                    EntitySetName = $_.EntitySetName       # <-- Use this for API queries!
                    DisplayName   = $_.DisplayName.UserLocalizedLabel.Label
                }
            } | Sort-Object LogicalName
        
        Write-Host "`nCUSTOM TABLES (cr950_*):" -ForegroundColor Green
        Write-Host ("─" * 70) -ForegroundColor Gray
        Write-Host "  LogicalName (Metadata)".PadRight(30) + "EntitySetName (API Queries)" -ForegroundColor Yellow
        Write-Host ("─" * 70) -ForegroundColor Gray
        
        $tables | ForEach-Object {
            Write-Host "  $($_.LogicalName.PadRight(28)) → $($_.EntitySetName)" -ForegroundColor White
        }
        
        Write-Host ("─" * 70) -ForegroundColor Gray
        Write-Host "  Total: $($tables.Count) custom tables" -ForegroundColor Green
        Write-Host "`n  💡 Use EntitySetName for API queries and Power Automate 'List rows'" -ForegroundColor Cyan
        Write-Host ("=" * 70) + "`n" -ForegroundColor Cyan
        
        return $tables
    }
    catch {
        Write-Host "❌ Discovery failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Test-TableQuery {
    <#
    .SYNOPSIS
        Test if a table name works in API queries
    .PARAMETER TableName
        The table name to test (try EntitySetName from Get-AllCustomTables)
    .EXAMPLE
        Test-TableQuery -TableName "cr950_projectses"
    .EXAMPLE
        Test-TableQuery -TableName "cr950_apparatuses"
    #>
    param(
        [Parameter(Mandatory=$true)][string]$TableName
    )
    
    if (-not $script:AuthToken) {
        Write-Host "⚠️  Not connected. Run Connect-DataverseAPI first." -ForegroundColor Yellow
        return $false
    }
    
    $url = "$($script:Config.DataverseUrl)/api/data/v9.2/$TableName`?`$top=1"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $script:Headers -Method Get
        Write-Host "✅ $TableName - VALID (found $($response.value.Count) records)" -ForegroundColor Green
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "❌ $TableName - NOT FOUND (404)" -ForegroundColor Red
        }
        else {
            Write-Host "❌ $TableName - ERROR: $($_.Exception.Message)" -ForegroundColor Red
        }
        return $false
    }
}

function Get-TableNameMapping {
    <#
    .SYNOPSIS
        Generate a reference mapping for documentation
    .DESCRIPTION
        Creates a markdown table of LogicalName → EntitySetName for docs
    .EXAMPLE
        Get-TableNameMapping | Out-File "TABLE_NAMES.md"
    #>
    
    $tables = Get-AllCustomTables
    if (-not $tables) { return }
    
    $output = @()
    $output += "# Dataverse Table Name Reference"
    $output += ""
    $output += "| Logical Name (Metadata) | EntitySet Name (API Queries) | Display Name |"
    $output += "|-------------------------|------------------------------|--------------|"
    
    $tables | ForEach-Object {
        $output += "| ``$($_.LogicalName)`` | ``$($_.EntitySetName)`` | $($_.DisplayName) |"
    }
    
    $output += ""
    $output += "**Usage Notes:**"
    $output += "- Use **LogicalName** in metadata API calls (EntityDefinitions)"
    $output += "- Use **EntitySetName** in record queries (/api/data/v9.2/{EntitySetName})"
    $output += "- Power Automate 'List rows' action uses EntitySetName"
    
    return $output -join "`n"
}

function Get-TableFields {
    <#
    .SYNOPSIS
        Get all fields for a specific table
    .PARAMETER TableName
        The LogicalName of the table (e.g., 'cr950_project')
    .PARAMETER CustomOnly
        Only return custom fields (cr950_*)
    .EXAMPLE
        Get-TableFields -TableName "cr950_project" -CustomOnly
    #>
    param(
        [Parameter(Mandatory=$true)][string]$TableName,
        [switch]$CustomOnly
    )
    
    if (-not $script:AuthToken) {
        Write-Host "⚠️  Not connected. Run Connect-DataverseAPI first." -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "🔍 Getting fields for $TableName..." -ForegroundColor Cyan
    
    $url = "$($script:Config.DataverseUrl)/api/data/v9.2/EntityDefinitions(LogicalName='$TableName')/Attributes?`$select=LogicalName,AttributeType,DisplayName,SchemaName"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $script:Headers -Method Get
        $fields = $response.value
        
        if ($CustomOnly) {
            $fields = $fields | Where-Object { $_.LogicalName -like "cr950_*" }
        }
        
        $result = $fields | ForEach-Object {
            [PSCustomObject]@{
                LogicalName = $_.LogicalName
                SchemaName  = $_.SchemaName
                DisplayName = $_.DisplayName.UserLocalizedLabel.Label
                Type        = $_.AttributeType
            }
        } | Sort-Object LogicalName
        
        Write-Host "   Found $($result.Count) fields" -ForegroundColor Green
        return $result
    }
    catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Get-LookupFields {
    <#
    .SYNOPSIS
        Get all lookup (relationship) fields for a table
    .DESCRIPTION
        Useful for understanding table relationships and correct lookup syntax
    .PARAMETER TableName
        The LogicalName of the table
    .EXAMPLE
        Get-LookupFields -TableName "cr950_scope"
    #>
    param(
        [Parameter(Mandatory=$true)][string]$TableName
    )
    
    if (-not $script:AuthToken) {
        Write-Host "⚠️  Not connected. Run Connect-DataverseAPI first." -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "🔍 Getting lookup fields for $TableName..." -ForegroundColor Cyan
    
    $url = "$($script:Config.DataverseUrl)/api/data/v9.2/EntityDefinitions(LogicalName='$TableName')/Attributes/Microsoft.Dynamics.CRM.LookupAttributeMetadata?`$select=LogicalName,DisplayName,Targets"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $script:Headers -Method Get
        
        $result = $response.value | ForEach-Object {
            [PSCustomObject]@{
                LogicalName = $_.LogicalName
                DisplayName = $_.DisplayName.UserLocalizedLabel.Label
                TargetTable = ($_.Targets -join ", ")
            }
        } | Sort-Object LogicalName
        
        Write-Host "   Found $($result.Count) lookup fields" -ForegroundColor Green
        return $result
    }
    catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ============================================================================
# INITIALIZATION
# ============================================================================

Write-Host "`n📦 Dataverse Table Discovery Template Loaded" -ForegroundColor Cyan
Write-Host "   Run 'Connect-DataverseAPI' to start" -ForegroundColor Gray
Write-Host "   Functions:" -ForegroundColor White
Write-Host "     Get-AllCustomTables  - List tables with correct API names" -ForegroundColor Gray
Write-Host "     Test-TableQuery      - Verify a table name works" -ForegroundColor Gray
Write-Host "     Get-TableFields      - Get all fields for a table" -ForegroundColor Gray
Write-Host "     Get-LookupFields     - Get relationship/lookup fields" -ForegroundColor Gray
Write-Host "     Get-TableNameMapping - Generate markdown reference`n" -ForegroundColor Gray
