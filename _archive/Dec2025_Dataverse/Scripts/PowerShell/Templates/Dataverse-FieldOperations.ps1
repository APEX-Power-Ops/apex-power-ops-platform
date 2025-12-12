# Dataverse Field Operations Template
# Created: November 23, 2025
# Purpose: Reusable functions for Dataverse schema/metadata operations (fields, tables)
# 
# This complements Dataverse-Functions.ps1 which handles record CRUD operations.
# Use this for:
#   - Adding fields to existing tables
#   - Querying table metadata/schema
#   - Comparing documented fields vs actual fields
#
# USAGE:
#   1. Dot-source this file: . "C:\RESA_Power_Build\Scripts\PowerShell\Templates\Dataverse-FieldOperations.ps1"
#   2. Call Connect-DataverseAPI to authenticate
#   3. Use Add-DataverseField, Get-DataverseFields, etc.
#
# ENVIRONMENT VARIABLES REQUIRED (in .env file or set manually):
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
# FIELD OPERATIONS
# ============================================================================

function Add-DataverseField {
    param(
        [Parameter(Mandatory=$true)][string]$TableName,
        [Parameter(Mandatory=$true)][string]$FieldName,
        [Parameter(Mandatory=$true)][string]$DisplayName,
        [Parameter(Mandatory=$true)]
        [ValidateSet("String", "Integer", "Decimal", "Currency", "DateTime", "Boolean", "Picklist", "Memo")]
        [string]$FieldType,
        [int]$MaxLength = 100,
        [int]$Precision = 2,
        [hashtable]$PicklistOptions,
        [bool]$Required = $false
    )
    
    if (-not $script:AuthToken) {
        Write-Host "⚠️  Not connected. Run Connect-DataverseAPI first." -ForegroundColor Yellow
        return $false
    }
    
    $fullFieldName = if ($FieldName -like "cr950_*") { $FieldName } else { "cr950_$FieldName" }
    Write-Host "➕ Adding field: $fullFieldName ($FieldType)..." -ForegroundColor Cyan
    
    $attributeDef = @{
        "@odata.type"   = ""
        SchemaName      = $fullFieldName
        DisplayName     = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; Label = $DisplayName; LanguageCode = 1033 }) }
        RequiredLevel   = @{ Value = if ($Required) { "ApplicationRequired" } else { "None" } }
    }
    
    switch ($FieldType) {
        "String" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $attributeDef["MaxLength"] = $MaxLength
            $attributeDef["FormatName"] = @{ Value = "Text" }
        }
        "Memo" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.MemoAttributeMetadata"
            $attributeDef["MaxLength"] = $MaxLength
            $attributeDef["Format"] = "Text"
        }
        "Integer" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
            $attributeDef["Format"] = "None"
            $attributeDef["MinValue"] = -2147483648
            $attributeDef["MaxValue"] = 2147483647
        }
        "Decimal" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
            $attributeDef["Precision"] = $Precision
            $attributeDef["MinValue"] = -100000000000
            $attributeDef["MaxValue"] = 100000000000
        }
        "Currency" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.MoneyAttributeMetadata"
            $attributeDef["Precision"] = $Precision
            $attributeDef["PrecisionSource"] = 2
        }
        "DateTime" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $attributeDef["Format"] = "DateAndTime"
            $attributeDef["DateTimeBehavior"] = @{ Value = "UserLocal" }
        }
        "Boolean" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
            $attributeDef["OptionSet"] = @{
                TrueOption  = @{ Value = 1; Label = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; Label = "Yes"; LanguageCode = 1033 }) } }
                FalseOption = @{ Value = 0; Label = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; Label = "No"; LanguageCode = 1033 }) } }
            }
        }
        "Picklist" {
            $attributeDef["@odata.type"] = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
            $options = @()
            foreach ($key in $PicklistOptions.Keys | Sort-Object) {
                $options += @{
                    Value = [int]$key
                    Label = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; LocalizedLabels = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; Label = $PicklistOptions[$key]; LanguageCode = 1033 }) }
                }
            }
            $attributeDef["OptionSet"] = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.OptionSetMetadata"
                IsGlobal      = $false
                OptionSetType = "Picklist"
                Options       = $options
            }
        }
    }
    
    $url = "$($script:Config.DataverseUrl)/api/data/v9.2/EntityDefinitions(LogicalName='$TableName')/Attributes"
    $body = $attributeDef | ConvertTo-Json -Depth 10
    
    try {
        Invoke-RestMethod -Uri $url -Headers $script:Headers -Method Post -Body $body
        Write-Host "   ✅ Field created: $fullFieldName" -ForegroundColor Green
        return $true
    }
    catch {
        $errorDetails = $_.ErrorDetails.Message
        if ($errorDetails -match "already exists|already in use|duplicate") {
            Write-Host "   ⚠️  Field already exists: $fullFieldName" -ForegroundColor Yellow
            return $true
        }
        else {
            Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
}

function Get-DataverseFields {
    param(
        [Parameter(Mandatory=$true)][string]$TableName,
        [switch]$CustomOnly
    )
    
    if (-not $script:AuthToken) {
        Write-Host "⚠️  Not connected. Run Connect-DataverseAPI first." -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "🔍 Querying fields for $TableName..." -ForegroundColor Cyan
    $url = "$($script:Config.DataverseUrl)/api/data/v9.2/EntityDefinitions(LogicalName='$TableName')/Attributes?`$select=LogicalName,AttributeType,DisplayName"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $script:Headers -Method Get
        $fields = $response.value
        
        if ($CustomOnly) {
            $fields = $fields | Where-Object { $_.LogicalName -like "cr950_*" }
        }
        
        $result = $fields | ForEach-Object {
            [PSCustomObject]@{
                LogicalName = $_.LogicalName
                DisplayName = $_.DisplayName.UserLocalizedLabel.Label
                Type        = $_.AttributeType
            }
        } | Sort-Object LogicalName
        
        Write-Host "   Found $($result.Count) fields" -ForegroundColor Green
        return $result
    }
    catch {
        Write-Host "❌ Query failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ============================================================================
# INITIALIZATION
# ============================================================================

Write-Host "`n📦 Dataverse Field Operations Template Loaded" -ForegroundColor Cyan
Write-Host "   Run 'Connect-DataverseAPI' to start" -ForegroundColor Gray
Write-Host "   Functions: Connect-DataverseAPI, Add-DataverseField, Get-DataverseFields`n" -ForegroundColor White