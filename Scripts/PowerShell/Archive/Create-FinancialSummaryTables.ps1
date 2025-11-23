# Create Financial Summary Tables for RESA Power Build
# Created: November 22, 2025
# Purpose: Create Scope Financial Summary and Project Financial Summary tables
#          to maintain separation between operational and financial data

# Import reusable functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Financial Summary Tables Creator         ║" -ForegroundColor Cyan
Write-Host "║  Creates: Scope Financial Summary + Project Financial  ║" -ForegroundColor Cyan
Write-Host "║           Summary (Separation of Concerns)             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Connect to Dataverse
Connect-Dataverse

if (-not $script:DataverseToken) {
    Write-Host "❌ Failed to connect. Please check environment variables." -ForegroundColor Red
    exit 1
}

# Base URL for Web API
$baseUrl = "$($script:DataverseConfig.DataverseUrl)/api/data/v9.2"

# ============================================================================
# FUNCTION: Create Table via Web API
# ============================================================================
function New-DataverseTable {
    param(
        [string]$LogicalName,
        [string]$DisplayName,
        [string]$PluralName,
        [string]$Description,
        [string]$PrimaryFieldLogicalName,
        [string]$PrimaryFieldDisplayName
    )
    
    Write-Host "`n📋 Creating table: $DisplayName ($LogicalName)" -ForegroundColor Cyan
    
    $tableDefinition = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.EntityMetadata"
        "Attributes" = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
                "AttributeType" = "String"
                "AttributeTypeName" = @{
                    "Value" = "StringType"
                }
                "Description" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(
                        @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                            "Label" = "Primary field for $DisplayName"
                            "LanguageCode" = 1033
                        }
                    )
                }
                "DisplayName" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(
                        @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                            "Label" = $PrimaryFieldDisplayName
                            "LanguageCode" = 1033
                        }
                    )
                }
                "RequiredLevel" = @{
                    "Value" = "None"
                    "CanBeChanged" = $true
                }
                "SchemaName" = $PrimaryFieldLogicalName
                "MaxLength" = 100
                "IsPrimaryName" = $true
            }
        )
        "PrimaryNameAttribute" = $PrimaryFieldLogicalName
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $Description
                    "LanguageCode" = 1033
                }
            )
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $DisplayName
                    "LanguageCode" = 1033
                }
            )
        }
        "DisplayCollectionName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $PluralName
                    "LanguageCode" = 1033
                }
            )
        }
        "OwnershipType" = "UserOwned"
        "SchemaName" = $LogicalName
        "HasActivities" = $false
        "HasNotes" = $true
    }
    
    $body = $tableDefinition | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/EntityDefinitions" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $body
        
        Write-Host "   ✅ Table created successfully!" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "   ❌ Failed to create table: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Error: $($errorDetail.error.message)" -ForegroundColor Red
        }
        return $null
    }
}

# ============================================================================
# FUNCTION: Add Field to Table
# ============================================================================
function Add-DataverseField {
    param(
        [string]$TableLogicalName,
        [string]$FieldLogicalName,
        [string]$FieldDisplayName,
        [string]$FieldType,  # Lookup, Money, Decimal, Integer, DateTime
        [string]$Description,
        [hashtable]$AdditionalProperties = @{}
    )
    
    Write-Host "   ➕ Adding field: $FieldDisplayName" -ForegroundColor Gray
    
    # Base field definition
    $fieldDef = @{
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $Description
                    "LanguageCode" = 1033
                }
            )
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $FieldDisplayName
                    "LanguageCode" = 1033
                }
            )
        }
        "RequiredLevel" = @{
            "Value" = "None"
            "CanBeChanged" = $true
        }
        "SchemaName" = $FieldLogicalName
    }
    
    # Add type-specific properties
    switch ($FieldType) {
        "Lookup" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
            $fieldDef["AttributeType"] = "Lookup"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "LookupType" }
            if ($AdditionalProperties.ContainsKey("Targets")) {
                $fieldDef["Targets"] = $AdditionalProperties["Targets"]
            }
        }
        "Money" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.MoneyAttributeMetadata"
            $fieldDef["AttributeType"] = "Money"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "MoneyType" }
            $fieldDef["PrecisionSource"] = 2
            $fieldDef["Precision"] = 2
            $fieldDef["MinValue"] = 0
            $fieldDef["MaxValue"] = 1000000000
        }
        "Decimal" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
            $fieldDef["AttributeType"] = "Decimal"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "DecimalType" }
            $fieldDef["Precision"] = 2
            $fieldDef["MinValue"] = 0
            $fieldDef["MaxValue"] = 100000
        }
        "Integer" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
            $fieldDef["AttributeType"] = "Integer"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "IntegerType" }
            $fieldDef["MinValue"] = 0
            $fieldDef["MaxValue"] = 2147483647
        }
        "DateTime" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $fieldDef["AttributeType"] = "DateTime"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "DateTimeType" }
            $fieldDef["Format"] = "DateOnly"
            $fieldDef["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
        }
    }
    
    $body = $fieldDef | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $body
        
        Write-Host "      ✅ Field added" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ============================================================================
# CREATE SCOPE FINANCIAL SUMMARY TABLE
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " STEP 1: Creating Scope Financial Summary Table" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

$scopeFinancialTable = New-DataverseTable `
    -LogicalName "cr950_scopefinancialsummary" `
    -DisplayName "Scope Financial Summary" `
    -PluralName "Scope Financial Summaries" `
    -Description "Financial metrics aggregated at Scope level (separation from operations)" `
    -PrimaryFieldLogicalName "cr950_name" `
    -PrimaryFieldDisplayName "Name"

if ($scopeFinancialTable) {
    Start-Sleep -Seconds 5  # Wait for table creation to complete
    
    # Add Scope Lookup Field
    Add-DataverseField `
        -TableLogicalName "cr950_scopefinancialsummary" `
        -FieldLogicalName "cr950_scopeid" `
        -FieldDisplayName "Scope" `
        -FieldType "Lookup" `
        -Description "Link to the operational scope record (1:1 relationship)" `
        -AdditionalProperties @{ Targets = @("cr950_projectscope") }
    
    Start-Sleep -Seconds 2
    
    # Add Revenue Rollup Fields
    Write-Host "`n   📊 Adding revenue rollup fields..." -ForegroundColor Cyan
    Write-Host "   ⚠️  NOTE: Rollup fields must be configured in the UI after table creation" -ForegroundColor Yellow
    Write-Host "   Fields to add manually:" -ForegroundColor Gray
    Write-Host "   - Total Revenue Recognized (Money, Rollup from Apparatus Revenue)" -ForegroundColor Gray
    Write-Host "   - Total Revenue Pending (Money, Rollup from Apparatus Revenue)" -ForegroundColor Gray
    Write-Host "   - Total Billable Hours (Decimal, Rollup from Apparatus Revenue)" -ForegroundColor Gray
    Write-Host "   - Total Delay Hours (Decimal, Rollup from Apparatus Revenue)" -ForegroundColor Gray
    Write-Host "   - Revenue Record Count (Integer, Rollup from Apparatus Revenue)" -ForegroundColor Gray
    Write-Host "   - Average Revenue Per Apparatus (Money, Rollup from Apparatus Revenue)" -ForegroundColor Gray
    Write-Host "   - Latest Revenue Date (DateTime, Rollup from Apparatus Revenue)" -ForegroundColor Gray
}

# ============================================================================
# CREATE PROJECT FINANCIAL SUMMARY TABLE
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " STEP 2: Creating Project Financial Summary Table" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

$projectFinancialTable = New-DataverseTable `
    -LogicalName "cr950_projectfinancialsummary" `
    -DisplayName "Project Financial Summary" `
    -PluralName "Project Financial Summaries" `
    -Description "Financial metrics aggregated at Project level (separation from operations)" `
    -PrimaryFieldLogicalName "cr950_name" `
    -PrimaryFieldDisplayName "Name"

if ($projectFinancialTable) {
    Start-Sleep -Seconds 5
    
    # Add Project Lookup Field
    Add-DataverseField `
        -TableLogicalName "cr950_projectfinancialsummary" `
        -FieldLogicalName "cr950_projectid" `
        -FieldDisplayName "Project" `
        -FieldType "Lookup" `
        -Description "Link to the operational project record (1:1 relationship)" `
        -AdditionalProperties @{ Targets = @("cr950_projects") }
    
    Start-Sleep -Seconds 2
    
    # Add Revenue Rollup Fields
    Write-Host "`n   📊 Adding revenue rollup fields..." -ForegroundColor Cyan
    Write-Host "   ⚠️  NOTE: Rollup fields must be configured in the UI after table creation" -ForegroundColor Yellow
    Write-Host "   Fields to add manually:" -ForegroundColor Gray
    Write-Host "   - Total Revenue Recognized (Money, Rollup from Scope Financial Summary)" -ForegroundColor Gray
    Write-Host "   - Total Revenue Pending (Money, Rollup from Scope Financial Summary)" -ForegroundColor Gray
    Write-Host "   - Total Billable Hours (Decimal, Rollup from Scope Financial Summary)" -ForegroundColor Gray
    Write-Host "   - Total Delay Hours (Decimal, Rollup from Scope Financial Summary)" -ForegroundColor Gray
    Write-Host "   - Total Revenue Record Count (Integer, Rollup from Scope Financial Summary)" -ForegroundColor Gray
    Write-Host "   - Average Revenue Per Scope (Money, Rollup from Scope Financial Summary)" -ForegroundColor Gray
    Write-Host "   - Latest Revenue Date (DateTime, Rollup from Scope Financial Summary)" -ForegroundColor Gray
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  CREATION COMPLETE                       ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n✅ Tables Created:" -ForegroundColor Cyan
Write-Host "   1. Scope Financial Summary (cr950_scopefinancialsummary)" -ForegroundColor White
Write-Host "   2. Project Financial Summary (cr950_projectfinancialsummary)" -ForegroundColor White

Write-Host "`n⚠️  NEXT STEPS (Manual Configuration Required):" -ForegroundColor Yellow
Write-Host "`n   📋 STEP 1: Configure Rollup Fields in Dataverse UI" -ForegroundColor Yellow
Write-Host "      Navigate to each table and add the 7 rollup fields listed above" -ForegroundColor Gray
Write-Host "      (Rollup fields cannot be created via Web API - must use UI)" -ForegroundColor Gray

Write-Host "`n   🔐 STEP 2: Configure Security Roles" -ForegroundColor Yellow
Write-Host "      - Finance Role: Full CRUD on Financial Summary tables" -ForegroundColor Gray
Write-Host "      - Operations Role: NO access to Financial Summary tables" -ForegroundColor Gray
Write-Host "      - PM Role: Read-only on Financial Summary tables" -ForegroundColor Gray

Write-Host "`n   🔄 STEP 3: Create Power Automate Flows" -ForegroundColor Yellow
Write-Host "      - Auto-create Scope Financial Summary when Scope created" -ForegroundColor Gray
Write-Host "      - Auto-create Project Financial Summary when Project created" -ForegroundColor Gray

Write-Host "`n   📊 STEP 4: Create Finance Dashboard Views" -ForegroundColor Yellow
Write-Host "      - Scope Revenue Summary (Finance team)" -ForegroundColor Gray
Write-Host "      - Project Revenue Summary (Executive dashboard)" -ForegroundColor Gray

Write-Host "`n   📦 STEP 5: Add to Solution" -ForegroundColor Yellow
Write-Host "      Import both tables into your solution for version control" -ForegroundColor Gray

Write-Host "`n   ✅ STEP 6: Test Rollups" -ForegroundColor Yellow
Write-Host "      Create test apparatus → mark complete → verify rollups calculate" -ForegroundColor Gray

Write-Host "`n═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Export table info for reference
$exportData = @{
    CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    ScopeFinancialSummary = @{
        LogicalName = "cr950_scopefinancialsummary"
        DisplayName = "Scope Financial Summary"
        Fields = @(
            @{ Name = "Scope Lookup"; Type = "Lookup"; Target = "cr950_projectscope" }
            @{ Name = "Total Revenue Recognized"; Type = "Money (Rollup)"; Source = "Apparatus Revenue" }
            @{ Name = "Total Revenue Pending"; Type = "Money (Rollup)"; Source = "Apparatus Revenue" }
            @{ Name = "Total Billable Hours"; Type = "Decimal (Rollup)"; Source = "Apparatus Revenue" }
            @{ Name = "Total Delay Hours"; Type = "Decimal (Rollup)"; Source = "Apparatus Revenue" }
            @{ Name = "Revenue Record Count"; Type = "Integer (Rollup)"; Source = "Apparatus Revenue" }
            @{ Name = "Average Revenue Per Apparatus"; Type = "Money (Rollup)"; Source = "Apparatus Revenue" }
            @{ Name = "Latest Revenue Date"; Type = "DateTime (Rollup)"; Source = "Apparatus Revenue" }
        )
    }
    ProjectFinancialSummary = @{
        LogicalName = "cr950_projectfinancialsummary"
        DisplayName = "Project Financial Summary"
        Fields = @(
            @{ Name = "Project Lookup"; Type = "Lookup"; Target = "cr950_projects" }
            @{ Name = "Total Revenue Recognized"; Type = "Money (Rollup)"; Source = "Scope Financial Summary" }
            @{ Name = "Total Revenue Pending"; Type = "Money (Rollup)"; Source = "Scope Financial Summary" }
            @{ Name = "Total Billable Hours"; Type = "Decimal (Rollup)"; Source = "Scope Financial Summary" }
            @{ Name = "Total Delay Hours"; Type = "Decimal (Rollup)"; Source = "Scope Financial Summary" }
            @{ Name = "Total Revenue Record Count"; Type = "Integer (Rollup)"; Source = "Scope Financial Summary" }
            @{ Name = "Average Revenue Per Scope"; Type = "Money (Rollup)"; Source = "Scope Financial Summary" }
            @{ Name = "Latest Revenue Date"; Type = "DateTime (Rollup)"; Source = "Scope Financial Summary" }
        )
    }
}

$exportPath = "$PSScriptRoot\..\..\Logs\FinancialSummaryTables_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$exportData | ConvertTo-Json -Depth 10 | Out-File $exportPath
Write-Host "📄 Table definitions exported to: $exportPath" -ForegroundColor Cyan

Write-Host "`n✨ Script complete! Review KPI_FIELDS_IMPLEMENTATION_PRIORITY.md for detailed specs.`n" -ForegroundColor Green
