# Create Financial Tables for Revenue Recognition
# Created: December 2, 2025
# Purpose: Create ApparatusRevenue, ScopeFinancialSummary, ProjectFinancialSummary
# Environment: org7bdbc942.crm.dynamics.com (Developer)
# Pattern: Financial/Operations Separation

param(
    [switch]$WhatIf,
    [switch]$Force
)

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Financial Tables Creator                  ║" -ForegroundColor Cyan
Write-Host "║  Creates: ApparatusRevenue + ScopeFinancialSummary      ║" -ForegroundColor Cyan
Write-Host "║           + ProjectFinancialSummary                     ║" -ForegroundColor Cyan
Write-Host "║  Environment: org7bdbc942 (Developer)                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($WhatIf) {
    Write-Host "🔍 WHATIF MODE - No changes will be made`n" -ForegroundColor Yellow
}

# ============================================================================
# CONFIGURATION
# ============================================================================

$Config = @{
    TenantId = $env:AZURE_TENANT_ID
    ClientId = $env:AZURE_CLIENT_ID
    ClientSecret = $env:AZURE_CLIENT_SECRET
    DataverseUrl = "https://org7bdbc942.crm.dynamics.com"  # Developer environment
    ApiVersion = "v9.2"
    PublisherPrefix = "cr950"
}

# Validate environment variables
$missingVars = @()
if (-not $Config.TenantId) { $missingVars += "AZURE_TENANT_ID" }
if (-not $Config.ClientId) { $missingVars += "AZURE_CLIENT_ID" }
if (-not $Config.ClientSecret) { $missingVars += "AZURE_CLIENT_SECRET" }

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    $missingVars | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    Write-Host "`nSet these in your PowerShell session or .env file." -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# AUTHENTICATION
# ============================================================================

Write-Host "🔐 Authenticating to Dataverse..." -ForegroundColor Cyan

$tokenUrl = "https://login.microsoftonline.com/$($Config.TenantId)/oauth2/v2.0/token"
$tokenBody = @{
    client_id     = $Config.ClientId
    scope         = "$($Config.DataverseUrl)/.default"
    client_secret = $Config.ClientSecret
    grant_type    = "client_credentials"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
    $accessToken = $tokenResponse.access_token
    $headers = @{
        Authorization = "Bearer $accessToken"
        "OData-MaxVersion" = "4.0"
        "OData-Version" = "4.0"
        Accept = "application/json"
        "Content-Type" = "application/json; charset=utf-8"
    }
    Write-Host "✅ Authenticated to $($Config.DataverseUrl)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$baseUrl = "$($Config.DataverseUrl)/api/data/$($Config.ApiVersion)"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function New-DataverseTable {
    param(
        [string]$SchemaName,
        [string]$DisplayName,
        [string]$PluralName,
        [string]$Description
    )
    
    Write-Host "`n📋 Creating table: $DisplayName" -ForegroundColor Cyan
    Write-Host "   Schema: $SchemaName" -ForegroundColor Gray
    
    if ($WhatIf) {
        Write-Host "   [WHATIF] Would create table" -ForegroundColor Yellow
        return @{ success = $true; whatif = $true }
    }
    
    $tableDefinition = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.EntityMetadata"
        "Attributes" = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
                "AttributeType" = "String"
                "AttributeTypeName" = @{ "Value" = "StringType" }
                "Description" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(@{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        "Label" = "Primary name field"
                        "LanguageCode" = 1033
                    })
                }
                "DisplayName" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(@{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        "Label" = "Name"
                        "LanguageCode" = 1033
                    })
                }
                "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
                "SchemaName" = "$($Config.PublisherPrefix)_name"
                "MaxLength" = 200
                "IsPrimaryName" = $true
            }
        )
        "PrimaryNameAttribute" = "$($Config.PublisherPrefix)_name"
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                "Label" = $Description
                "LanguageCode" = 1033
            })
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                "Label" = $DisplayName
                "LanguageCode" = 1033
            })
        }
        "DisplayCollectionName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                "Label" = $PluralName
                "LanguageCode" = 1033
            })
        }
        "OwnershipType" = "UserOwned"
        "SchemaName" = $SchemaName
        "HasActivities" = $false
        "HasNotes" = $true
    }
    
    $body = $tableDefinition | ConvertTo-Json -Depth 15
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/EntityDefinitions" -Method Post -Headers $headers -Body $body
        Write-Host "   ✅ Table created!" -ForegroundColor Green
        return @{ success = $true; response = $response }
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($_.ErrorDetails.Message) {
            try {
                $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
                $errorMsg = $errorDetail.error.message
            } catch {}
        }
        Write-Host "   ❌ Failed: $errorMsg" -ForegroundColor Red
        return @{ success = $false; error = $errorMsg }
    }
}

function Add-DataverseField {
    param(
        [string]$TableSchemaName,
        [string]$FieldSchemaName,
        [string]$DisplayName,
        [string]$FieldType,
        [string]$Description,
        [hashtable]$Options = @{}
    )
    
    Write-Host "   ➕ $DisplayName ($FieldType)" -ForegroundColor Gray
    
    if ($WhatIf) {
        Write-Host "      [WHATIF] Would add field" -ForegroundColor Yellow
        return @{ success = $true; whatif = $true }
    }
    
    $fieldDef = @{
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                "Label" = $Description
                "LanguageCode" = 1033
            })
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(@{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                "Label" = $DisplayName
                "LanguageCode" = 1033
            })
        }
        "RequiredLevel" = @{
            "Value" = if ($Options.Required) { "ApplicationRequired" } else { "None" }
            "CanBeChanged" = $true
        }
        "SchemaName" = $FieldSchemaName
    }
    
    switch ($FieldType) {
        "Lookup" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
            $fieldDef["AttributeType"] = "Lookup"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "LookupType" }
            if ($Options.Targets) {
                $fieldDef["Targets"] = $Options.Targets
            }
        }
        "Money" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.MoneyAttributeMetadata"
            $fieldDef["AttributeType"] = "Money"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "MoneyType" }
            $fieldDef["PrecisionSource"] = 2
            $fieldDef["Precision"] = 2
            $fieldDef["MinValue"] = -1000000000
            $fieldDef["MaxValue"] = 1000000000
        }
        "Decimal" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
            $fieldDef["AttributeType"] = "Decimal"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "DecimalType" }
            $fieldDef["Precision"] = if ($Options.Precision) { $Options.Precision } else { 2 }
            $fieldDef["MinValue"] = -100000
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
            $fieldDef["Format"] = if ($Options.Format) { $Options.Format } else { "DateAndTime" }
            $fieldDef["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
        }
        "Choice" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
            $fieldDef["AttributeType"] = "Picklist"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "PicklistType" }
            if ($Options.OptionSet) {
                $fieldDef["OptionSet"] = $Options.OptionSet
            }
        }
    }
    
    $tableLogicalName = $TableSchemaName.ToLower()
    $body = $fieldDef | ConvertTo-Json -Depth 15
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$tableLogicalName')/Attributes" `
            -Method Post -Headers $headers -Body $body
        Write-Host "      ✅ Added" -ForegroundColor Green
        return @{ success = $true }
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($_.ErrorDetails.Message) {
            try {
                $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
                $errorMsg = $errorDetail.error.message
            } catch {}
        }
        Write-Host "      ❌ Failed: $errorMsg" -ForegroundColor Red
        return @{ success = $false; error = $errorMsg }
    }
}

# ============================================================================
# TABLE 1: APPARATUS REVENUE
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " TABLE 1: Apparatus Revenue (Detail Level)" -ForegroundColor Yellow
Write-Host " Purpose: Individual revenue per apparatus (financial separation)" -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

$result1 = New-DataverseTable `
    -SchemaName "cr950_apparatusrevenue" `
    -DisplayName "Apparatus Revenue" `
    -PluralName "Apparatus Revenue Records" `
    -Description "Financial metrics for individual apparatus (separation from operations)"

if ($result1.success -and -not $result1.whatif) {
    Start-Sleep -Seconds 5  # Wait for table creation
    
    Write-Host "`n   Adding fields to Apparatus Revenue..." -ForegroundColor Cyan
    
    # Apparatus Lookup (required)
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_apparatus_id" `
        -DisplayName "Apparatus" `
        -FieldType "Lookup" `
        -Description "Parent apparatus record" `
        -Options @{ Targets = @("cr950_apparatus"); Required = $true }
    Start-Sleep -Seconds 1
    
    # ScopeLaborDetail Lookup (required - for rate)
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_scopelabordetail_id" `
        -DisplayName "Scope Labor Detail" `
        -FieldType "Lookup" `
        -Description "Source of effective labor rate" `
        -Options @{ Targets = @("cr950_scopelabordetail"); Required = $true }
    Start-Sleep -Seconds 1
    
    # Planned Hours
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_plannedhours" `
        -DisplayName "Planned Hours" `
        -FieldType "Decimal" `
        -Description "Initial labor hour estimate from apparatus"
    Start-Sleep -Seconds 1
    
    # Delay Hours
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_delayhours" `
        -DisplayName "Delay Hours" `
        -FieldType "Decimal" `
        -Description "Additional hours due to delays or scope changes"
    Start-Sleep -Seconds 1
    
    # Actual Hours (will be calculated: planned + delay)
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_actualhours" `
        -DisplayName "Actual Hours" `
        -FieldType "Decimal" `
        -Description "Total actual hours (Planned + Delay) - calculated by flow"
    Start-Sleep -Seconds 1
    
    # Labor Rate Applied
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_laborrateapplied" `
        -DisplayName "Labor Rate Applied" `
        -FieldType "Money" `
        -Description "Effective labor rate at time of revenue recognition"
    Start-Sleep -Seconds 1
    
    # Revenue Amount (calculated: hours × rate)
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_revenueamount" `
        -DisplayName "Revenue Amount" `
        -FieldType "Money" `
        -Description "Calculated revenue (Actual Hours × Labor Rate) - calculated by flow"
    Start-Sleep -Seconds 1
    
    # Revenue Status (Choice)
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_revenuestatus" `
        -DisplayName "Revenue Status" `
        -FieldType "Choice" `
        -Description "Status: Planned (1), In Progress (2), Recognized (3)" `
        -Options @{
            OptionSet = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.OptionSetMetadata"
                "IsGlobal" = $false
                "OptionSetType" = "Picklist"
                "Options" = @(
                    @{
                        "Value" = 1
                        "Label" = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            "LocalizedLabels" = @(@{
                                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                "Label" = "Planned"
                                "LanguageCode" = 1033
                            })
                        }
                    }
                    @{
                        "Value" = 2
                        "Label" = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            "LocalizedLabels" = @(@{
                                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                "Label" = "In Progress"
                                "LanguageCode" = 1033
                            })
                        }
                    }
                    @{
                        "Value" = 3
                        "Label" = @{
                            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                            "LocalizedLabels" = @(@{
                                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                                "Label" = "Recognized"
                                "LanguageCode" = 1033
                            })
                        }
                    }
                )
            }
        }
    Start-Sleep -Seconds 1
    
    # Recognition Date
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_recognitiondate" `
        -DisplayName "Recognition Date" `
        -FieldType "DateTime" `
        -Description "Date when revenue was recognized"
    Start-Sleep -Seconds 1
    
    # ScopeFinancialSummary Lookup (for rollups)
    Add-DataverseField -TableSchemaName "cr950_apparatusrevenue" `
        -FieldSchemaName "cr950_scopefinancialsummary_id" `
        -DisplayName "Scope Financial Summary" `
        -FieldType "Lookup" `
        -Description "Parent financial summary for rollups" `
        -Options @{ Targets = @("cr950_scopefinancialsummary") }
}

# ============================================================================
# TABLE 2: SCOPE FINANCIAL SUMMARY
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " TABLE 2: Scope Financial Summary (Rollup Level)" -ForegroundColor Yellow
Write-Host " Purpose: Aggregate apparatus revenues by scope" -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

$result2 = New-DataverseTable `
    -SchemaName "cr950_scopefinancialsummary" `
    -DisplayName "Scope Financial Summary" `
    -PluralName "Scope Financial Summaries" `
    -Description "Financial metrics aggregated at Scope level (separation from operations)"

if ($result2.success -and -not $result2.whatif) {
    Start-Sleep -Seconds 5
    
    Write-Host "`n   Adding fields to Scope Financial Summary..." -ForegroundColor Cyan
    
    # Scope Lookup (1:1 relationship)
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_scope_id" `
        -DisplayName "Scope" `
        -FieldType "Lookup" `
        -Description "Link to operational scope record (1:1)" `
        -Options @{ Targets = @("cr950_scope"); Required = $true }
    Start-Sleep -Seconds 1
    
    # ScopeLaborDetail Lookup
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_scopelabordetail_id" `
        -DisplayName "Scope Labor Detail" `
        -FieldType "Lookup" `
        -Description "Link to labor rate configuration" `
        -Options @{ Targets = @("cr950_scopelabordetail") }
    Start-Sleep -Seconds 1
    
    # ProjectFinancialSummary Lookup (for project rollups)
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_projectfinancialsummary_id" `
        -DisplayName "Project Financial Summary" `
        -FieldType "Lookup" `
        -Description "Parent project financial summary for rollups" `
        -Options @{ Targets = @("cr950_projectfinancialsummary") }
    Start-Sleep -Seconds 1
    
    # --- Rollup Fields (configured manually, created as regular fields for now) ---
    Write-Host "`n   Creating rollup placeholder fields..." -ForegroundColor Cyan
    Write-Host "   ⚠️  NOTE: Rollup formulas must be configured in Power Apps UI" -ForegroundColor Yellow
    
    # Total Planned Hours
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_totalplannedhours" `
        -DisplayName "Total Planned Hours" `
        -FieldType "Decimal" `
        -Description "Sum of planned hours from ApparatusRevenue (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Actual Hours
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_totalactualhours" `
        -DisplayName "Total Actual Hours" `
        -FieldType "Decimal" `
        -Description "Sum of actual hours from ApparatusRevenue (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Revenue Recognized
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_totalrevenuerecognized" `
        -DisplayName "Total Revenue Recognized" `
        -FieldType "Money" `
        -Description "Sum of revenue where status=Recognized (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Revenue Pending
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_totalrevenuepending" `
        -DisplayName "Total Revenue Pending" `
        -FieldType "Money" `
        -Description "Sum of revenue where status!=Recognized (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Apparatus Revenue Count
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_apparatusrevenuecount" `
        -DisplayName "Apparatus Revenue Count" `
        -FieldType "Integer" `
        -Description "Count of ApparatusRevenue records (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Estimated Revenue (from ScopeLaborDetail)
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_estimatedrevenue" `
        -DisplayName "Estimated Revenue" `
        -FieldType "Money" `
        -Description "Original estimated revenue from ScopeLaborDetail"
    Start-Sleep -Seconds 1
    
    # Revenue Variance
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_revenuevariance" `
        -DisplayName "Revenue Variance" `
        -FieldType "Money" `
        -Description "Recognized - Estimated (calculated by flow)"
    Start-Sleep -Seconds 1
    
    # Latest Revenue Date
    Add-DataverseField -TableSchemaName "cr950_scopefinancialsummary" `
        -FieldSchemaName "cr950_latestrevenue_date" `
        -DisplayName "Latest Revenue Date" `
        -FieldType "DateTime" `
        -Description "Most recent revenue recognition date (configure as rollup)"
}

# ============================================================================
# TABLE 3: PROJECT FINANCIAL SUMMARY
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " TABLE 3: Project Financial Summary (Executive Level)" -ForegroundColor Yellow
Write-Host " Purpose: Aggregate scope financials by project" -ForegroundColor Gray
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

$result3 = New-DataverseTable `
    -SchemaName "cr950_projectfinancialsummary" `
    -DisplayName "Project Financial Summary" `
    -PluralName "Project Financial Summaries" `
    -Description "Financial metrics aggregated at Project level (separation from operations)"

if ($result3.success -and -not $result3.whatif) {
    Start-Sleep -Seconds 5
    
    Write-Host "`n   Adding fields to Project Financial Summary..." -ForegroundColor Cyan
    
    # Project Lookup (1:1 relationship)
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_project_id" `
        -DisplayName "Project" `
        -FieldType "Lookup" `
        -Description "Link to operational project record (1:1)" `
        -Options @{ Targets = @("cr950_project"); Required = $true }
    Start-Sleep -Seconds 1
    
    # --- Rollup Fields ---
    Write-Host "`n   Creating rollup placeholder fields..." -ForegroundColor Cyan
    Write-Host "   ⚠️  NOTE: Rollup formulas must be configured in Power Apps UI" -ForegroundColor Yellow
    
    # Scope Count
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_scopecount" `
        -DisplayName "Scope Count" `
        -FieldType "Integer" `
        -Description "Count of ScopeFinancialSummary records (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Project Hours
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_totalprojecthours" `
        -DisplayName "Total Project Hours" `
        -FieldType "Decimal" `
        -Description "Sum of actual hours across all scopes (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Revenue Recognized
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_totalrevenuerecognized" `
        -DisplayName "Total Revenue Recognized" `
        -FieldType "Money" `
        -Description "Sum of recognized revenue across scopes (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Revenue Pending
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_totalrevenuepending" `
        -DisplayName "Total Revenue Pending" `
        -FieldType "Money" `
        -Description "Sum of pending revenue across scopes (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Estimated Revenue
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_totalestimatedrevenue" `
        -DisplayName "Total Estimated Revenue" `
        -FieldType "Money" `
        -Description "Sum of estimated revenue across scopes (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Total Variance
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_totalvariance" `
        -DisplayName "Total Variance" `
        -FieldType "Money" `
        -Description "Recognized - Estimated across all scopes (calculated by flow)"
    Start-Sleep -Seconds 1
    
    # Apparatus Revenue Count
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_apparatusrevenuecount" `
        -DisplayName "Apparatus Revenue Count" `
        -FieldType "Integer" `
        -Description "Total apparatus revenue records (configure as rollup)"
    Start-Sleep -Seconds 1
    
    # Latest Revenue Date
    Add-DataverseField -TableSchemaName "cr950_projectfinancialsummary" `
        -FieldSchemaName "cr950_latestrevenue_date" `
        -DisplayName "Latest Revenue Date" `
        -FieldType "DateTime" `
        -Description "Most recent revenue recognition across scopes (configure as rollup)"
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  CREATION COMPLETE                                      ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Tables Created:                                        ║" -ForegroundColor Green
Write-Host "║  ├─ cr950_apparatusrevenue (10 fields)                  ║" -ForegroundColor White
Write-Host "║  ├─ cr950_scopefinancialsummary (11 fields)             ║" -ForegroundColor White
Write-Host "║  └─ cr950_projectfinancialsummary (9 fields)            ║" -ForegroundColor White
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  MANUAL STEPS REQUIRED:                                 ║" -ForegroundColor Yellow
Write-Host "║  1. Configure rollup fields in Power Apps UI            ║" -ForegroundColor White
Write-Host "║  2. Add tables to solution (RESA_Power_Build_V2)        ║" -ForegroundColor White
Write-Host "║  3. Create forms and views                              ║" -ForegroundColor White
Write-Host "║  4. Build Power Automate flows                          ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open Power Apps → Tables → Verify tables created" -ForegroundColor Gray
Write-Host "   2. Configure rollup fields (see build spec)" -ForegroundColor Gray
Write-Host "   3. Build ScopeLaborDetail Rate Calculation flow" -ForegroundColor Gray
Write-Host "   4. Build Revenue Recognition flow (on Apparatus complete)" -ForegroundColor Gray
Write-Host "   5. Build Auto-create Financial Summary flow" -ForegroundColor Gray
Write-Host "`n"
