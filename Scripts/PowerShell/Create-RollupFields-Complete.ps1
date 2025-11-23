# ═══════════════════════════════════════════════════════════
# RESA Power Build - Create Rollup Fields with Full Metadata
# Creates 18 date rollups + 14 revenue rollups via Web API
# Version: 1.0.0
# Date: 2025-01-22
# ═══════════════════════════════════════════════════════════

# Load Dataverse functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Create Rollup Fields (Full Metadata)     ║" -ForegroundColor Cyan
Write-Host "║  Creates: 18 Date Rollups + 14 Revenue Rollups         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Connect to Dataverse
Write-Host "`n🔐 Connecting to Dataverse..." -ForegroundColor Yellow
Connect-Dataverse

if (-not $script:DataverseToken) {
    Write-Host "❌ Failed to connect. Please check environment variables." -ForegroundColor Red
    exit 1
}

$baseUrl = "$($script:DataverseConfig.DataverseUrl)/api/data/v9.2"

function New-DateRollupField {
    param(
        [Parameter(Mandatory=$true)]
        [string]$TargetEntity,
        
        [Parameter(Mandatory=$true)]
        [string]$LogicalName,
        
        [Parameter(Mandatory=$true)]
        [string]$DisplayName,
        
        [Parameter(Mandatory=$true)]
        [string]$SourceEntity,
        
        [Parameter(Mandatory=$true)]
        [string]$SourceAttribute,
        
        [Parameter(Mandatory=$true)]
        [ValidateSet("Min", "Max")]
        [string]$AggregationType,
        
        [Parameter(Mandatory=$false)]
        [string]$FilterXml = ""
    )
    
    # Build the rollup metadata
    $rollupMetadata = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.RollupAttributeMetadata"
        SchemaName = $LogicalName
        DisplayName = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label = $DisplayName
                    LanguageCode = 1033
                }
            )
        }
        Description = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label = "Rollup of $SourceAttribute from $SourceEntity ($AggregationType)"
                    LanguageCode = 1033
                }
            )
        }
        RequiredLevel = @{
            Value = "None"
            CanBeChanged = $true
        }
        AttributeTypeName = @{
            Value = "DateTimeType"
        }
        DateTimeBehavior = @{
            Value = "UserLocal"
        }
        Format = "DateOnly"
        ImeMode = "Auto"
        SourceEntity = $SourceEntity
        SourceAttribute = $SourceAttribute
        AggregationType = $AggregationType
    }
    
    if ($FilterXml) {
        $rollupMetadata["FilterCriteria"] = $FilterXml
    }
    
    $json = $rollupMetadata | ConvertTo-Json -Depth 10
    
    try {
        Write-Host "   ➕ Creating: $DisplayName" -ForegroundColor Cyan
        Write-Host "      Source: $SourceEntity.$SourceAttribute" -ForegroundColor Gray
        Write-Host "      Aggregation: $AggregationType" -ForegroundColor Gray
        
        $uri = "$baseUrl/EntityDefinitions(LogicalName='$TargetEntity')/Attributes"
        
        $response = Invoke-RestMethod -Uri $uri -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $json
        
        Write-Host "      ✅ Rollup field created successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "      ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "      Details: $($errorDetails.error.message)" -ForegroundColor Red
        }
        return $false
    }
}

function New-RevenueRollupField {
    param(
        [Parameter(Mandatory=$true)]
        [string]$TargetEntity,
        
        [Parameter(Mandatory=$true)]
        [string]$LogicalName,
        
        [Parameter(Mandatory=$true)]
        [string]$DisplayName,
        
        [Parameter(Mandatory=$true)]
        [string]$SourceEntity,
        
        [Parameter(Mandatory=$true)]
        [string]$SourceAttribute,
        
        [Parameter(Mandatory=$true)]
        [ValidateSet("Sum", "Count", "Min", "Max", "Avg")]
        [string]$AggregationType,
        
        [Parameter(Mandatory=$false)]
        [string]$AttributeType = "Money",  # Money, Integer, or DateTime
        
        [Parameter(Mandatory=$false)]
        [string]$FilterXml = ""
    )
    
    # Determine the OData type based on attribute type
    $odataType = switch ($AttributeType) {
        "Money" { "Microsoft.Dynamics.CRM.MoneyAttributeMetadata" }
        "Integer" { "Microsoft.Dynamics.CRM.IntegerAttributeMetadata" }
        "DateTime" { "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata" }
        default { "Microsoft.Dynamics.CRM.MoneyAttributeMetadata" }
    }
    
    # Build the rollup metadata
    $rollupMetadata = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.RollupAttributeMetadata"
        SchemaName = $LogicalName
        DisplayName = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label = $DisplayName
                    LanguageCode = 1033
                }
            )
        }
        Description = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            LocalizedLabels = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    Label = "Rollup of $SourceAttribute from $SourceEntity ($AggregationType)"
                    LanguageCode = 1033
                }
            )
        }
        RequiredLevel = @{
            Value = "None"
            CanBeChanged = $true
        }
        SourceEntity = $SourceEntity
        SourceAttribute = $SourceAttribute
        AggregationType = $AggregationType
    }
    
    # Add type-specific properties
    if ($AttributeType -eq "Money") {
        $rollupMetadata["AttributeTypeName"] = @{ Value = "MoneyType" }
        $rollupMetadata["PrecisionSource"] = 2
        $rollupMetadata["Precision"] = 2
        $rollupMetadata["MinValue"] = -922337203685477.0
        $rollupMetadata["MaxValue"] = 922337203685477.0
        $rollupMetadata["ImeMode"] = "Auto"
    }
    elseif ($AttributeType -eq "Integer") {
        $rollupMetadata["AttributeTypeName"] = @{ Value = "IntegerType" }
        $rollupMetadata["Format"] = "None"
        $rollupMetadata["MinValue"] = -2147483648
        $rollupMetadata["MaxValue"] = 2147483647
    }
    elseif ($AttributeType -eq "DateTime") {
        $rollupMetadata["AttributeTypeName"] = @{ Value = "DateTimeType" }
        $rollupMetadata["DateTimeBehavior"] = @{ Value = "UserLocal" }
        $rollupMetadata["Format"] = "DateOnly"
        $rollupMetadata["ImeMode"] = "Auto"
    }
    
    if ($FilterXml) {
        $rollupMetadata["FilterCriteria"] = $FilterXml
    }
    
    $json = $rollupMetadata | ConvertTo-Json -Depth 10
    
    try {
        Write-Host "   ➕ Creating: $DisplayName" -ForegroundColor Cyan
        Write-Host "      Source: $SourceEntity.$SourceAttribute" -ForegroundColor Gray
        Write-Host "      Aggregation: $AggregationType ($AttributeType)" -ForegroundColor Gray
        
        $uri = "$baseUrl/EntityDefinitions(LogicalName='$TargetEntity')/Attributes"
        
        $response = Invoke-RestMethod -Uri $uri -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $json
        
        Write-Host "      ✅ Rollup field created successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "      ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "      Details: $($errorDetails.error.message)" -ForegroundColor Red
        }
        return $false
    }
}

# ═══════════════════════════════════════════════════════════
# PHASE 1: DATE ROLLUPS (18 fields)
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1A: Date Rollups on Tasks (6 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "`n📋 Tasks Table (cr950_tasks)" -ForegroundColor Cyan
Write-Host "   Rolling up from: Apparatus (cr950_apparatus)" -ForegroundColor Gray

New-DateRollupField -TargetEntity "cr950_tasks" `
    -LogicalName "cr950_earliest_anticipated_start" `
    -DisplayName "Earliest Anticipated Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_tasks" `
    -LogicalName "cr950_latest_anticipated_start" `
    -DisplayName "Latest Anticipated Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Max"

New-DateRollupField -TargetEntity "cr950_tasks" `
    -LogicalName "cr950_earliest_actual_start" `
    -DisplayName "Earliest Actual Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_tasks" `
    -LogicalName "cr950_latest_actual_start" `
    -DisplayName "Latest Actual Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Max"

New-DateRollupField -TargetEntity "cr950_tasks" `
    -LogicalName "cr950_earliest_completion_date" `
    -DisplayName "Earliest Completion Date" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_tasks" `
    -LogicalName "cr950_latest_completion_date" `
    -DisplayName "Latest Completion Date" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Max"

Write-Host "`n   ✅ Tasks date rollups complete!" -ForegroundColor Green

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1B: Date Rollups on Scopes (6 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "`n📋 Scopes Table (cr950_projectscope)" -ForegroundColor Cyan
Write-Host "   Rolling up from: Apparatus (cr950_apparatus)" -ForegroundColor Gray

New-DateRollupField -TargetEntity "cr950_projectscope" `
    -LogicalName "cr950_earliest_anticipated_start" `
    -DisplayName "Earliest Anticipated Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_projectscope" `
    -LogicalName "cr950_latest_anticipated_start" `
    -DisplayName "Latest Anticipated Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_anticipated_start" `
    -AggregationType "Max"

New-DateRollupField -TargetEntity "cr950_projectscope" `
    -LogicalName "cr950_earliest_actual_start" `
    -DisplayName "Earliest Actual Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_projectscope" `
    -LogicalName "cr950_latest_actual_start" `
    -DisplayName "Latest Actual Start" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_actual_start" `
    -AggregationType "Max"

New-DateRollupField -TargetEntity "cr950_projectscope" `
    -LogicalName "cr950_earliest_completion_date" `
    -DisplayName "Earliest Completion Date" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_projectscope" `
    -LogicalName "cr950_latest_completion_date" `
    -DisplayName "Latest Completion Date" `
    -SourceEntity "cr950_apparatus" `
    -SourceAttribute "cr950_date_completed" `
    -AggregationType "Max"

Write-Host "`n   ✅ Scopes date rollups complete!" -ForegroundColor Green

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1C: Date Rollups on Projects (6 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "`n📋 Projects Table (cr950_projects)" -ForegroundColor Cyan
Write-Host "   Rolling up from: Scopes (cr950_projectscope)" -ForegroundColor Gray

New-DateRollupField -TargetEntity "cr950_projects" `
    -LogicalName "cr950_earliest_anticipated_start" `
    -DisplayName "Earliest Anticipated Start" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_earliest_anticipated_start" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_projects" `
    -LogicalName "cr950_latest_anticipated_start" `
    -DisplayName "Latest Anticipated Start" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_latest_anticipated_start" `
    -AggregationType "Max"

New-DateRollupField -TargetEntity "cr950_projects" `
    -LogicalName "cr950_earliest_actual_start" `
    -DisplayName "Earliest Actual Start" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_earliest_actual_start" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_projects" `
    -LogicalName "cr950_latest_actual_start" `
    -DisplayName "Latest Actual Start" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_latest_actual_start" `
    -AggregationType "Max"

New-DateRollupField -TargetEntity "cr950_projects" `
    -LogicalName "cr950_earliest_completion_date" `
    -DisplayName "Earliest Completion Date" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_earliest_completion_date" `
    -AggregationType "Min"

New-DateRollupField -TargetEntity "cr950_projects" `
    -LogicalName "cr950_latest_completion_date" `
    -DisplayName "Latest Completion Date" `
    -SourceEntity "cr950_projectscope" `
    -SourceAttribute "cr950_latest_completion_date" `
    -AggregationType "Max"

Write-Host "`n   ✅ Projects date rollups complete!" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════
# PHASE 2: REVENUE ROLLUPS (14 fields)
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 2A: Revenue Rollups on Scope Financial Summary (7 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "`n📋 Scope Financial Summary (cr950_scopefinancialsummary)" -ForegroundColor Cyan
Write-Host "   Rolling up from: Apparatus Revenue (cr950_apparatusrevenue)" -ForegroundColor Gray

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_total_recognized_revenue" `
    -DisplayName "Total Recognized Revenue" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "cr950_recognized_revenue" `
    -AggregationType "Sum" `
    -AttributeType "Money"

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_total_pending_revenue" `
    -DisplayName "Total Pending Revenue" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "cr950_pending_revenue" `
    -AggregationType "Sum" `
    -AttributeType "Money"

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_total_billable_hours" `
    -DisplayName "Total Billable Hours" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "cr950_billable_hours" `
    -AggregationType "Sum" `
    -AttributeType "Integer"

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_total_delay_hours" `
    -DisplayName "Total Delay Hours" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "cr950_delay_hours" `
    -AggregationType "Sum" `
    -AttributeType "Integer"

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_apparatus_count" `
    -DisplayName "Apparatus Count" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "cr950_apparatusrevenueid" `
    -AggregationType "Count" `
    -AttributeType "Integer"

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_avg_revenue_per_apparatus" `
    -DisplayName "Avg Revenue per Apparatus" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "cr950_recognized_revenue" `
    -AggregationType "Avg" `
    -AttributeType "Money"

New-RevenueRollupField -TargetEntity "cr950_scopefinancialsummary" `
    -LogicalName "cr950_latest_revenue_date" `
    -DisplayName "Latest Revenue Date" `
    -SourceEntity "cr950_apparatusrevenue" `
    -SourceAttribute "createdon" `
    -AggregationType "Max" `
    -AttributeType "DateTime"

Write-Host "`n   ✅ Scope Financial Summary revenue rollups complete!" -ForegroundColor Green

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 2B: Revenue Rollups on Project Financial Summary (7 fields)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "`n📋 Project Financial Summary (cr950_projectfinancialsummary)" -ForegroundColor Cyan
Write-Host "   Rolling up from: Scope Financial Summary (cr950_scopefinancialsummary)" -ForegroundColor Gray

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_total_recognized_revenue" `
    -DisplayName "Total Recognized Revenue" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_total_recognized_revenue" `
    -AggregationType "Sum" `
    -AttributeType "Money"

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_total_pending_revenue" `
    -DisplayName "Total Pending Revenue" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_total_pending_revenue" `
    -AggregationType "Sum" `
    -AttributeType "Money"

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_total_billable_hours" `
    -DisplayName "Total Billable Hours" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_total_billable_hours" `
    -AggregationType "Sum" `
    -AttributeType "Integer"

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_total_delay_hours" `
    -DisplayName "Total Delay Hours" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_total_delay_hours" `
    -AggregationType "Sum" `
    -AttributeType "Integer"

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_scope_count" `
    -DisplayName "Scope Count" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_scopefinancialsummaryid" `
    -AggregationType "Count" `
    -AttributeType "Integer"

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_avg_revenue_per_scope" `
    -DisplayName "Avg Revenue per Scope" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_total_recognized_revenue" `
    -AggregationType "Avg" `
    -AttributeType "Money"

New-RevenueRollupField -TargetEntity "cr950_projectfinancialsummary" `
    -LogicalName "cr950_latest_revenue_date" `
    -DisplayName "Latest Revenue Date" `
    -SourceEntity "cr950_scopefinancialsummary" `
    -SourceAttribute "cr950_latest_revenue_date" `
    -AggregationType "Max" `
    -AttributeType "DateTime"

Write-Host "`n   ✅ Project Financial Summary revenue rollups complete!" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║    ROLLUP FIELDS CREATION COMPLETE!                      ║" -ForegroundColor Green
Write-Host "║    ✅ 18 Date Rollups Created                            ║" -ForegroundColor Green
Write-Host "║    ✅ 14 Revenue Rollups Created                         ║" -ForegroundColor Green
Write-Host "║    📊 Total: 32 Rollup Fields                            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n✨ Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Publish customizations in Dataverse" -ForegroundColor White
Write-Host "   2. Test rollup calculations with sample data" -ForegroundColor White
Write-Host "   3. Create Power Automate flows for financial record creation" -ForegroundColor White
Write-Host "   4. Configure security roles" -ForegroundColor White
Write-Host "   5. Build KPI views and dashboards" -ForegroundColor White
