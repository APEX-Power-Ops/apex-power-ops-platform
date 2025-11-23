# Dataverse PowerShell Functions
# Created: November 22, 2025
# Purpose: Reusable functions for interacting with Dataverse from VS Code/PowerShell

<#
.SYNOPSIS
    Initialize Dataverse connection and get authentication token
.EXAMPLE
    Connect-Dataverse
#>
function Connect-Dataverse {
    $script:DataverseConfig = @{
        TenantId = $env:AZURE_TENANT_ID
        ClientId = $env:AZURE_CLIENT_ID
        ClientSecret = $env:AZURE_CLIENT_SECRET
        DataverseUrl = $env:DATAVERSE_URL
        ApiVersion = "v9.2"
    }
    
    Write-Host "🔐 Connecting to Dataverse..." -ForegroundColor Cyan
    
    $tokenUrl = "https://login.microsoftonline.com/$($script:DataverseConfig.TenantId)/oauth2/v2.0/token"
    $body = @{
        client_id     = $script:DataverseConfig.ClientId
        scope         = "$($script:DataverseConfig.DataverseUrl)/.default"
        client_secret = $script:DataverseConfig.ClientSecret
        grant_type    = "client_credentials"
    }
    
    try {
        $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
        $script:DataverseToken = $tokenResponse.access_token
        $script:DataverseHeaders = @{
            Authorization = "Bearer $($script:DataverseToken)"
            "OData-MaxVersion" = "4.0"
            "OData-Version" = "4.0"
            Accept = "application/json"
            "Content-Type" = "application/json; charset=utf-8"
        }
        
        Write-Host "✅ Connected to Dataverse!" -ForegroundColor Green
        Write-Host "   Environment: org99cd6c6e (Dev)" -ForegroundColor Gray
        return $script:DataverseToken
    }
    catch {
        Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

<#
.SYNOPSIS
    Get records from a Dataverse table
.PARAMETER EntityName
    The logical name of the table (e.g., 'cr950_projectses', 'cr950_apparatus')
.PARAMETER Select
    Comma-separated list of fields to retrieve
.PARAMETER Filter
    OData filter expression
.PARAMETER Top
    Maximum number of records to return
.EXAMPLE
    Get-DataverseRecords -EntityName "cr950_projectses" -Top 10
.EXAMPLE
    Get-DataverseRecords -EntityName "cr950_apparatus" -Filter "cr950_status eq 100000001" -Select "cr950_name,cr950_serialnumber"
#>
function Get-DataverseRecords {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EntityName,
        
        [string]$Select,
        [string]$Filter,
        [int]$Top = 50,
        [string]$OrderBy
    )
    
    if (-not $script:DataverseToken) {
        Write-Host "⚠️  Not connected. Run Connect-Dataverse first." -ForegroundColor Yellow
        return
    }
    
    $url = "$($script:DataverseConfig.DataverseUrl)/api/data/$($script:DataverseConfig.ApiVersion)/$EntityName"
    
    $queryParams = @()
    if ($Select) { $queryParams += "`$select=$Select" }
    if ($Filter) { $queryParams += "`$filter=$Filter" }
    if ($Top) { $queryParams += "`$top=$Top" }
    if ($OrderBy) { $queryParams += "`$orderby=$OrderBy" }
    
    if ($queryParams.Count -gt 0) {
        $url += "?" + ($queryParams -join "&")
    }
    
    try {
        Write-Host "🔍 Querying $EntityName..." -ForegroundColor Cyan
        $response = Invoke-RestMethod -Uri $url -Headers $script:DataverseHeaders -Method Get
        Write-Host "✅ Found $($response.value.Count) record(s)" -ForegroundColor Green
        return $response.value
    }
    catch {
        Write-Host "❌ Query failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

<#
.SYNOPSIS
    Create a new record in Dataverse
.PARAMETER EntityName
    The logical name of the table
.PARAMETER Data
    Hashtable of field names and values
.EXAMPLE
    $project = @{
        "cr950_name" = "Test Project"
        "cr950_projectnumber" = "PRJ-001"
    }
    New-DataverseRecord -EntityName "cr950_projectses" -Data $project
#>
function New-DataverseRecord {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EntityName,
        
        [Parameter(Mandatory=$true)]
        [hashtable]$Data
    )
    
    if (-not $script:DataverseToken) {
        Write-Host "⚠️  Not connected. Run Connect-Dataverse first." -ForegroundColor Yellow
        return
    }
    
    $url = "$($script:DataverseConfig.DataverseUrl)/api/data/$($script:DataverseConfig.ApiVersion)/$EntityName"
    $body = $Data | ConvertTo-Json -Depth 10
    
    try {
        Write-Host "➕ Creating record in $EntityName..." -ForegroundColor Cyan
        $response = Invoke-RestMethod -Uri $url -Headers $script:DataverseHeaders -Method Post -Body $body
        Write-Host "✅ Record created successfully!" -ForegroundColor Green
        
        # Extract ID from response headers
        if ($response.PSObject.Properties['@odata.id']) {
            $recordId = $response.'@odata.id' -replace '.*/([^/]+)$', '$1'
            Write-Host "   ID: $recordId" -ForegroundColor Gray
            return $recordId
        }
        return $response
    }
    catch {
        Write-Host "❌ Create failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        return $null
    }
}

<#
.SYNOPSIS
    Update an existing record in Dataverse
.PARAMETER EntityName
    The logical name of the table
.PARAMETER RecordId
    The GUID of the record to update
.PARAMETER Data
    Hashtable of field names and values to update
.EXAMPLE
    $updates = @{
        "cr950_status" = 100000001
        "cr950_completeddate" = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    Update-DataverseRecord -EntityName "cr950_apparatus" -RecordId "12345678-1234-1234-1234-123456789012" -Data $updates
#>
function Update-DataverseRecord {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EntityName,
        
        [Parameter(Mandatory=$true)]
        [string]$RecordId,
        
        [Parameter(Mandatory=$true)]
        [hashtable]$Data
    )
    
    if (-not $script:DataverseToken) {
        Write-Host "⚠️  Not connected. Run Connect-Dataverse first." -ForegroundColor Yellow
        return
    }
    
    $url = "$($script:DataverseConfig.DataverseUrl)/api/data/$($script:DataverseConfig.ApiVersion)/$EntityName($RecordId)"
    $body = $Data | ConvertTo-Json -Depth 10
    
    try {
        Write-Host "✏️  Updating record in $EntityName..." -ForegroundColor Cyan
        Invoke-RestMethod -Uri $url -Headers $script:DataverseHeaders -Method Patch -Body $body
        Write-Host "✅ Record updated successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Update failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        return $false
    }
}

<#
.SYNOPSIS
    Delete a record from Dataverse
.PARAMETER EntityName
    The logical name of the table
.PARAMETER RecordId
    The GUID of the record to delete
.EXAMPLE
    Remove-DataverseRecord -EntityName "cr950_apparatus" -RecordId "12345678-1234-1234-1234-123456789012"
#>
function Remove-DataverseRecord {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EntityName,
        
        [Parameter(Mandatory=$true)]
        [string]$RecordId
    )
    
    if (-not $script:DataverseToken) {
        Write-Host "⚠️  Not connected. Run Connect-Dataverse first." -ForegroundColor Yellow
        return
    }
    
    $url = "$($script:DataverseConfig.DataverseUrl)/api/data/$($script:DataverseConfig.ApiVersion)/$EntityName($RecordId)"
    
    try {
        Write-Host "🗑️  Deleting record from $EntityName..." -ForegroundColor Cyan
        Invoke-RestMethod -Uri $url -Headers $script:DataverseHeaders -Method Delete
        Write-Host "✅ Record deleted successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Delete failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

<#
.SYNOPSIS
    Execute a FetchXML query against Dataverse
.PARAMETER FetchXml
    The FetchXML query string
.EXAMPLE
    $fetchXml = @"
    <fetch top="10">
      <entity name="cr950_apparatus">
        <attribute name="cr950_name" />
        <attribute name="cr950_status" />
        <filter>
          <condition attribute="cr950_status" operator="eq" value="100000001" />
        </filter>
      </entity>
    </fetch>
"@
    Invoke-DataverseFetchXml -FetchXml $fetchXml
#>
function Invoke-DataverseFetchXml {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FetchXml
    )
    
    if (-not $script:DataverseToken) {
        Write-Host "⚠️  Not connected. Run Connect-Dataverse first." -ForegroundColor Yellow
        return
    }
    
    # URL encode the FetchXML
    $encodedFetchXml = [System.Uri]::EscapeDataString($FetchXml)
    $url = "$($script:DataverseConfig.DataverseUrl)/api/data/$($script:DataverseConfig.ApiVersion)/cr950_projectses?fetchXml=$encodedFetchXml"
    
    try {
        Write-Host "🔍 Executing FetchXML query..." -ForegroundColor Cyan
        $response = Invoke-RestMethod -Uri $url -Headers $script:DataverseHeaders -Method Get
        Write-Host "✅ Found $($response.value.Count) record(s)" -ForegroundColor Green
        return $response.value
    }
    catch {
        Write-Host "❌ FetchXML query failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Helper function to display connection info
function Get-DataverseConnection {
    if ($script:DataverseToken) {
        Write-Host "`n✅ Connected to Dataverse" -ForegroundColor Green
        Write-Host "   Environment: $($script:DataverseConfig.DataverseUrl)" -ForegroundColor Gray
        Write-Host "   API Version: $($script:DataverseConfig.ApiVersion)" -ForegroundColor Gray
    }
    else {
        Write-Host "`n⚠️  Not connected to Dataverse" -ForegroundColor Yellow
        Write-Host "   Run: Connect-Dataverse" -ForegroundColor Gray
    }
}

# Export functions
Export-ModuleMember -Function Connect-Dataverse, Get-DataverseRecords, New-DataverseRecord, Update-DataverseRecord, Remove-DataverseRecord, Invoke-DataverseFetchXml, Get-DataverseConnection

Write-Host "`n📦 Dataverse Functions Loaded" -ForegroundColor Cyan
Write-Host "   Run 'Connect-Dataverse' to start" -ForegroundColor Gray
Write-Host "   Available functions:" -ForegroundColor Gray
Write-Host "   - Connect-Dataverse" -ForegroundColor White
Write-Host "   - Get-DataverseRecords" -ForegroundColor White
Write-Host "   - New-DataverseRecord" -ForegroundColor White
Write-Host "   - Update-DataverseRecord" -ForegroundColor White
Write-Host "   - Remove-DataverseRecord" -ForegroundColor White
Write-Host "   - Invoke-DataverseFetchXml" -ForegroundColor White
Write-Host "   - Get-DataverseConnection`n" -ForegroundColor White
