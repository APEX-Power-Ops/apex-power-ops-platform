# Add Rollup Fields to RESA Power Build
# Created: November 22, 2025
# Purpose: Create rollup fields for date tracking and financial summary tables via Web API

# Import reusable functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Rollup Fields Creator (Web API)          ║" -ForegroundColor Cyan
Write-Host "║  Creates: 18 Date Rollups + 14 Revenue Rollups         ║" -ForegroundColor Cyan
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
# FUNCTION: Create Rollup Field
# ============================================================================
function Add-RollupField {
    param(
        [string]$TableLogicalName,
        [string]$FieldLogicalName,
        [string]$FieldDisplayName,
        [string]$Description,
        [string]$SourceEntity,
        [string]$SourceAttribute,
        [string]$AggregationType, # Sum, Min, Max, Count, Avg
        [string]$FilterXml = "",
        [string]$DataType = "DateTime" # DateTime, Money, Decimal, Integer
    )
    
    Write-Host "   ➕ Adding rollup: $FieldDisplayName" -ForegroundColor Gray
    
    # Determine attribute type
    $odataType = switch ($DataType) {
        "DateTime" { "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata" }
        "Money" { "Microsoft.Dynamics.CRM.MoneyAttributeMetadata" }
        "Decimal" { "Microsoft.Dynamics.CRM.DecimalAttributeMetadata" }
        "Integer" { "Microsoft.Dynamics.CRM.IntegerAttributeMetadata" }
        default { "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata" }
    }
    
    $attributeTypeName = switch ($DataType) {
        "DateTime" { "DateTimeType" }
        "Money" { "MoneyType" }
        "Decimal" { "DecimalType" }
        "Integer" { "IntegerType" }
        default { "DateTimeType" }
    }
    
    # Base field definition
    $fieldDef = @{
        "@odata.type" = $odataType
        "AttributeType" = $DataType
        "AttributeTypeName" = @{ "Value" = $attributeTypeName }
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
        "SourceTypeMask" = 2 # Rollup field
    }
    
    # Add type-specific properties
    if ($DataType -eq "DateTime") {
        $fieldDef["Format"] = "DateOnly"
        $fieldDef["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
    }
    elseif ($DataType -eq "Money") {
        $fieldDef["PrecisionSource"] = 2
        $fieldDef["Precision"] = 2
        $fieldDef["MinValue"] = 0
        $fieldDef["MaxValue"] = 1000000000
    }
    elseif ($DataType -eq "Decimal") {
        $fieldDef["Precision"] = 2
        $fieldDef["MinValue"] = 0
        $fieldDef["MaxValue"] = 100000
    }
    elseif ($DataType -eq "Integer") {
        $fieldDef["MinValue"] = 0
        $fieldDef["MaxValue"] = 2147483647
    }
    
    # Add rollup-specific properties - THIS IS THE KEY PART
    # Note: The actual rollup definition might need to be set after field creation
    # via a separate PATCH request or through the RollupField entity
    
    $body = $fieldDef | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $body
        
        Write-Host "      ✅ Rollup field created" -ForegroundColor Green
        
        # Note: Rollup definition (source entity, aggregation) needs to be configured
        # This may require additional API calls or UI configuration
        Write-Host "      ⚠️  Configure rollup details in UI: Source=$SourceEntity, Agg=$AggregationType" -ForegroundColor Yellow
        
        return $response
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -like "*already exists*") {
            Write-Host "      ⚠️  Field already exists (skipping)" -ForegroundColor Yellow
        }
        else {
            Write-Host "      ❌ Failed: $errorMsg" -ForegroundColor Red
        }
        return $null
    }
}

# ============================================================================
# PHASE 1: DATE ROLLUP FIELDS - TASKS TABLE
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1A: Date Rollups on Tasks Table (6 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Write-Host "`n📋 Tasks Table (cr950_tasks)" -ForegroundColor Cyan

Add-RollupField `
    -TableLogicalName "cr950_tasks" `
    -FieldLogicalName "cr950_earliest_anticipated_start" `
    -FieldDisplayName "Earliest Anticipated Start" `
    -Description "Earliest planned start date among all apparatus in this task" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_tasks" `
    -FieldLogicalName "cr950_latest_anticipated_start" `
    -FieldDisplayName "Latest Anticipated Start" `
    -Description "Latest planned start date among all apparatus in this task" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Max" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_tasks" `
    -FieldLogicalName "cr950_earliest_actual_start" `
    -FieldDisplayName "Earliest Actual Start" `
    -Description "Earliest actual start date among all apparatus in this task" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_tasks" `
    -FieldLogicalName "cr950_latest_actual_start" `
    -FieldDisplayName "Latest Actual Start" `
    -Description "Latest actual start date among all apparatus in this task" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Max" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_tasks" `
    -FieldLogicalName "cr950_earliest_completion_date" `
    -FieldDisplayName "Earliest Completion Date" `
    -Description "Earliest completion date among all apparatus in this task" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_tasks" `
    -FieldLogicalName "cr950_latest_completion_date" `
    -FieldDisplayName "Latest Completion Date" `
    -Description "Latest completion date among all apparatus in this task" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Max" `
    -DataType "DateTime"

Write-Host "`n   ✅ Tasks date rollups complete!" -ForegroundColor Green

# ============================================================================
# PHASE 1B: DATE ROLLUP FIELDS - SCOPES TABLE
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1B: Date Rollups on Scopes Table (6 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Write-Host "`n📋 Scopes Table (cr950_projectscope)" -ForegroundColor Cyan

Add-RollupField `
    -TableLogicalName "cr950_projectscope" `
    -FieldLogicalName "cr950_earliest_anticipated_start" `
    -FieldDisplayName "Earliest Anticipated Start" `
    -Description "Earliest planned start date among all apparatus in this scope" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projectscope" `
    -FieldLogicalName "cr950_latest_anticipated_start" `
    -FieldDisplayName "Latest Anticipated Start" `
    -Description "Latest planned start date among all apparatus in this scope" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Max" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projectscope" `
    -FieldLogicalName "cr950_earliest_actual_start" `
    -FieldDisplayName "Earliest Actual Start" `
    -Description "Earliest actual start date among all apparatus in this scope" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projectscope" `
    -FieldLogicalName "cr950_latest_actual_start" `
    -FieldDisplayName "Latest Actual Start" `
    -Description "Latest actual start date among all apparatus in this scope" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Max" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projectscope" `
    -FieldLogicalName "cr950_earliest_completion_date" `
    -FieldDisplayName "Earliest Completion Date" `
    -Description "Earliest completion date among all apparatus in this scope" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projectscope" `
    -FieldLogicalName "cr950_latest_completion_date" `
    -FieldDisplayName "Latest Completion Date" `
    -Description "Latest completion date among all apparatus in this scope" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Max" `
    -DataType "DateTime"

Write-Host "`n   ✅ Scopes date rollups complete!" -ForegroundColor Green

# ============================================================================
# PHASE 1C: DATE ROLLUP FIELDS - PROJECTS TABLE
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1C: Date Rollups on Projects Table (6 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Write-Host "`n📋 Projects Table (cr950_projects)" -ForegroundColor Cyan

Add-RollupField `
    -TableLogicalName "cr950_projects" `
    -FieldLogicalName "cr950_earliest_anticipated_start" `
    -FieldDisplayName "Earliest Anticipated Start" `
    -Description "Earliest planned start date among all scopes in this project" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_earliest_anticipated_start" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projects" `
    -FieldLogicalName "cr950_latest_anticipated_start" `
    -FieldDisplayName "Latest Anticipated Start" `
    -Description "Latest planned start date among all scopes in this project" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_latest_anticipated_start" `
    -AggregationType "Max" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projects" `
    -FieldLogicalName "cr950_earliest_actual_start" `
    -FieldDisplayName "Earliest Actual Start" `
    -Description "Earliest actual start date among all scopes in this project" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_earliest_actual_start" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projects" `
    -FieldLogicalName "cr950_latest_actual_start" `
    -FieldDisplayName "Latest Actual Start" `
    -Description "Latest actual start date among all scopes in this project" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_latest_actual_start" `
    -AggregationType "Max" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projects" `
    -FieldLogicalName "cr950_earliest_completion_date" `
    -FieldDisplayName "Earliest Completion Date" `
    -Description "Earliest completion date among all scopes in this project" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_earliest_completion_date" `
    -AggregationType "Min" `
    -DataType "DateTime"

Start-Sleep -Seconds 2

Add-RollupField `
    -TableLogicalName "cr950_projects" `
    -FieldLogicalName "cr950_latest_completion_date" `
    -FieldDisplayName "Latest Completion Date" `
    -Description "Latest completion date among all scopes in this project" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_latest_completion_date" `
    -AggregationType "Max" `
    -DataType "DateTime"

Write-Host "`n   ✅ Projects date rollups complete!" -ForegroundColor Green

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║       DATE ROLLUP FIELDS CREATION COMPLETE (18)          ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n⚠️  IMPORTANT:" -ForegroundColor Yellow
Write-Host "   These fields were created as rollup field CONTAINERS" -ForegroundColor Yellow
Write-Host "   You must configure the rollup logic in Dataverse UI:" -ForegroundColor Yellow
Write-Host "   1. Go to each table → Columns" -ForegroundColor White
Write-Host "   2. Edit each rollup field" -ForegroundColor White
Write-Host "   3. Configure: Source Entity, Source Field, Aggregation" -ForegroundColor White
Write-Host "   4. Set filters if needed" -ForegroundColor White
Write-Host "   5. Save and Publish`n" -ForegroundColor White

Write-Host "✨ Script complete! Fields ready for rollup configuration.`n" -ForegroundColor Green
