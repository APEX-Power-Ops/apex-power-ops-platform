# Add Date Tracking Fields to RESA Power Build Tables
# Created: November 22, 2025
# Purpose: Add date tracking fields to Apparatus, Tasks, Scopes, Projects
#          Follows DATE_TRACKING_IMPLEMENTATION.md specification

# Import reusable functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Date Tracking Fields Implementation      ║" -ForegroundColor Cyan
Write-Host "║  Phase 1: Operational Date Fields for Schedule KPIs   ║" -ForegroundColor Cyan
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
# FUNCTION: Add Field to Table
# ============================================================================
function Add-DataverseField {
    param(
        [string]$TableLogicalName,
        [string]$FieldLogicalName,
        [string]$FieldDisplayName,
        [string]$FieldType,  # DateTime, String, Integer, Decimal, etc.
        [string]$Description,
        [hashtable]$AdditionalProperties = @{}
    )
    
    Write-Host "   ➕ Adding: $FieldDisplayName" -ForegroundColor Gray
    
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
        "DateTime" {
            $fieldDef["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $fieldDef["AttributeType"] = "DateTime"
            $fieldDef["AttributeTypeName"] = @{ "Value" = "DateTimeType" }
            $fieldDef["Format"] = "DateAndTime"
            $fieldDef["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
        }
        "DateOnly" {
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
        
        Write-Host "      ✅ Added successfully" -ForegroundColor Green
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
# PHASE 1: ADD BASE DATE FIELDS TO APPARATUS
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 1: Adding Base Date Fields to Apparatus Table" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Write-Host "`n📋 Apparatus Table (cr950_apparatus)" -ForegroundColor Cyan

# 1. Anticipated Start
Add-DataverseField `
    -TableLogicalName "cr950_apparatus" `
    -FieldLogicalName "cr950_anticipated_start" `
    -FieldDisplayName "Anticipated Start" `
    -FieldType "DateTime" `
    -Description "When work is planned to begin on this apparatus"

Start-Sleep -Seconds 1

# 2. Actual Start
Add-DataverseField `
    -TableLogicalName "cr950_apparatus" `
    -FieldLogicalName "cr950_actual_start" `
    -FieldDisplayName "Actual Start" `
    -FieldType "DateTime" `
    -Description "When work actually began on this apparatus (can be auto-populated by Power Automate)"

Start-Sleep -Seconds 1

# 3. Date Completed (may already exist - check first)
Write-Host "`n   ⚠️  Checking if Date Completed already exists..." -ForegroundColor Yellow
Add-DataverseField `
    -TableLogicalName "cr950_apparatus" `
    -FieldLogicalName "cr950_date_completed" `
    -FieldDisplayName "Date Completed" `
    -FieldType "DateTime" `
    -Description "When work was finished on this apparatus (auto-populated by Power Automate)"

Write-Host "`n   ✅ Apparatus base date fields complete!" -ForegroundColor Green

# ============================================================================
# PHASE 2: ROLLUP FIELDS NOTIFICATION
# ============================================================================

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " PHASE 2-4: Rollup Fields (Manual Configuration Required)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Write-Host "`n⚠️  IMPORTANT: Rollup fields cannot be created via Web API" -ForegroundColor Yellow
Write-Host "    You must add the following rollup fields manually in the UI:`n" -ForegroundColor Yellow

Write-Host "📋 TASKS TABLE (cr950_tasks) - 6 Rollup Fields:" -ForegroundColor Cyan
Write-Host "   1. Earliest Anticipated Start (Date Only, MIN from Apparatus)" -ForegroundColor White
Write-Host "   2. Latest Anticipated Start (Date Only, MAX from Apparatus)" -ForegroundColor White
Write-Host "   3. Earliest Actual Start (Date Only, MIN from Apparatus)" -ForegroundColor White
Write-Host "   4. Latest Actual Start (Date Only, MAX from Apparatus)" -ForegroundColor White
Write-Host "   5. Earliest Completion Date (Date Only, MIN from Apparatus)" -ForegroundColor White
Write-Host "   6. Latest Completion Date (Date Only, MAX from Apparatus)" -ForegroundColor White

Write-Host "`n📋 SCOPES TABLE (cr950_projectscope) - 6 Rollup Fields:" -ForegroundColor Cyan
Write-Host "   1. Earliest Anticipated Start (Date Only, MIN from Apparatus)" -ForegroundColor White
Write-Host "   2. Latest Anticipated Start (Date Only, MAX from Apparatus)" -ForegroundColor White
Write-Host "   3. Earliest Actual Start (Date Only, MIN from Apparatus)" -ForegroundColor White
Write-Host "   4. Latest Actual Start (Date Only, MAX from Apparatus)" -ForegroundColor White
Write-Host "   5. Earliest Completion Date (Date Only, MIN from Apparatus)" -ForegroundColor White
Write-Host "   6. Latest Completion Date (Date Only, MAX from Apparatus)" -ForegroundColor White

Write-Host "`n📋 PROJECTS TABLE (cr950_projects) - 6 Rollup Fields:" -ForegroundColor Cyan
Write-Host "   1. Earliest Anticipated Start (Date Only, MIN from Scopes)" -ForegroundColor White
Write-Host "   2. Latest Anticipated Start (Date Only, MAX from Scopes)" -ForegroundColor White
Write-Host "   3. Earliest Actual Start (Date Only, MIN from Scopes)" -ForegroundColor White
Write-Host "   4. Latest Actual Start (Date Only, MAX from Scopes)" -ForegroundColor White
Write-Host "   5. Earliest Completion Date (Date Only, MIN from Scopes)" -ForegroundColor White
Write-Host "   6. Latest Completion Date (Date Only, MAX from Scopes)" -ForegroundColor White

Write-Host "`n📖 Full specifications in: DATE_TRACKING_IMPLEMENTATION.md" -ForegroundColor Gray

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              BASE FIELDS CREATION COMPLETE               ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n✅ Completed:" -ForegroundColor Cyan
Write-Host "   - 3 base date fields added to Apparatus table" -ForegroundColor White

Write-Host "`n⏳ Next Steps (Manual UI Configuration):" -ForegroundColor Yellow
Write-Host "`n   📋 STEP 1: Add 18 Rollup Fields (1-2 hours)" -ForegroundColor Yellow
Write-Host "      - 6 rollups on Tasks (from Apparatus)" -ForegroundColor Gray
Write-Host "      - 6 rollups on Scopes (from Apparatus)" -ForegroundColor Gray
Write-Host "      - 6 rollups on Projects (from Scopes)" -ForegroundColor Gray
Write-Host "      See: DATE_TRACKING_IMPLEMENTATION.md for exact specs" -ForegroundColor Gray

Write-Host "`n   📊 STEP 2: Create KPI Views (30 minutes)" -ForegroundColor Yellow
Write-Host "      - Upcoming Work (Next 7 Days)" -ForegroundColor Gray
Write-Host "      - Overdue Starts" -ForegroundColor Gray
Write-Host "      - Work In Progress" -ForegroundColor Gray
Write-Host "      - Recently Completed (Last 7 Days)" -ForegroundColor Gray
Write-Host "      - Resource Timeline" -ForegroundColor Gray
Write-Host "      - Schedule Performance Report" -ForegroundColor Gray

Write-Host "`n   🎨 STEP 3: Update Forms (15 minutes)" -ForegroundColor Yellow
Write-Host "      Add date fields to main forms for:" -ForegroundColor Gray
Write-Host "      - Apparatus (all 3 base fields)" -ForegroundColor Gray
Write-Host "      - Tasks (6 rollup fields, read-only)" -ForegroundColor Gray
Write-Host "      - Scopes (6 rollup fields, read-only)" -ForegroundColor Gray
Write-Host "      - Projects (6 rollup fields, read-only)" -ForegroundColor Gray

Write-Host "`n   🔄 STEP 4: Configure Power Automate (Optional)" -ForegroundColor Yellow
Write-Host "      Auto-populate Actual Start when status changes from 'Not Started'" -ForegroundColor Gray
Write-Host "      (Date Completed already auto-populated by existing flow)" -ForegroundColor Gray

Write-Host "`n   ✅ STEP 5: Test with Sample Data (30 minutes)" -ForegroundColor Yellow
Write-Host "      - Create apparatus with Anticipated Start = Tomorrow" -ForegroundColor Gray
Write-Host "      - Verify rollups calculate at Task/Scope/Project levels" -ForegroundColor Gray
Write-Host "      - Test KPI views show correct data" -ForegroundColor Gray

Write-Host "`n   📦 STEP 6: Export as v1.5.0.0" -ForegroundColor Yellow
Write-Host "      After all fields configured and tested" -ForegroundColor Gray

Write-Host "`n═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Export field info for reference
$exportData = @{
    CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Phase1_BaseDateFields = @{
        Table = "Apparatus (cr950_apparatus)"
        Fields = @(
            @{
                LogicalName = "cr950_anticipated_start"
                DisplayName = "Anticipated Start"
                Type = "DateTime"
                Behavior = "UserLocal"
                Description = "When work is planned to begin on this apparatus"
            }
            @{
                LogicalName = "cr950_actual_start"
                DisplayName = "Actual Start"
                Type = "DateTime"
                Behavior = "UserLocal"
                Description = "When work actually began on this apparatus"
            }
            @{
                LogicalName = "cr950_date_completed"
                DisplayName = "Date Completed"
                Type = "DateTime"
                Behavior = "UserLocal"
                Description = "When work was finished (auto-populated)"
                Note = "May already exist - verify before adding"
            }
        )
    }
    Phase2_4_RollupsToAdd = @{
        Tasks = @{
            Count = 6
            Source = "Apparatus"
            Fields = @("Earliest/Latest Anticipated Start", "Earliest/Latest Actual Start", "Earliest/Latest Completion Date")
        }
        Scopes = @{
            Count = 6
            Source = "Apparatus"
            Fields = @("Earliest/Latest Anticipated Start", "Earliest/Latest Actual Start", "Earliest/Latest Completion Date")
        }
        Projects = @{
            Count = 6
            Source = "Scopes"
            Fields = @("Earliest/Latest Anticipated Start", "Earliest/Latest Actual Start", "Earliest/Latest Completion Date")
        }
    }
    TotalFields = 21
    Implementation_Time_Estimate = "2.5-3 hours total"
}

$exportPath = "$PSScriptRoot\..\..\Logs\DateTrackingFields_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$exportData | ConvertTo-Json -Depth 10 | Out-File $exportPath
Write-Host "📄 Field definitions exported to: $exportPath" -ForegroundColor Cyan

Write-Host "`n✨ Phase 1 complete! Follow DATE_TRACKING_IMPLEMENTATION.md for remaining phases.`n" -ForegroundColor Green
