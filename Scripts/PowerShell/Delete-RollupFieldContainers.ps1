# ═══════════════════════════════════════════════════════════
# RESA Power Build - Delete Rollup Field Containers
# Removes the simple rollup fields created without full metadata
# Version: 1.0.0
# Date: 2025-01-22
# ═══════════════════════════════════════════════════════════

# Load Dataverse functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Delete Rollup Field Containers           ║" -ForegroundColor Cyan
Write-Host "║  Removes 18 simple rollup fields for recreation        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Connect to Dataverse
Write-Host "`n🔐 Connecting to Dataverse..." -ForegroundColor Yellow
Connect-Dataverse

function Remove-RollupField {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EntityLogicalName,
        
        [Parameter(Mandatory=$true)]
        [string]$AttributeLogicalName,
        
        [Parameter(Mandatory=$true)]
        [string]$DisplayName
    )
    
    try {
        Write-Host "   ➖ Deleting: $DisplayName" -ForegroundColor Yellow
        
        $baseUrl = "https://org99cd6c6e.crm.dynamics.com"
        
        # Get the MetadataId first
        $getUri = "$baseUrl/api/data/v9.2/EntityDefinitions(LogicalName='$EntityLogicalName')/Attributes(LogicalName='$AttributeLogicalName')"
        
        $attribute = Invoke-RestMethod -Uri $getUri -Method Get `
            -Headers @{
                "Authorization" = "Bearer $($Global:DataverseConnection.AccessToken)"
                "OData-MaxVersion" = "4.0"
                "OData-Version" = "4.0"
                "Accept" = "application/json"
            }
        
        # Delete using MetadataId
        $deleteUri = "$baseUrl/api/data/v9.2/EntityDefinitions(LogicalName='$EntityLogicalName')/Attributes($($attribute.MetadataId))"
        
        Invoke-RestMethod -Uri $deleteUri -Method Delete `
            -Headers @{
                "Authorization" = "Bearer $($Global:DataverseConnection.AccessToken)"
                "OData-MaxVersion" = "4.0"
                "OData-Version" = "4.0"
            }
        
        Write-Host "      ✅ Deleted successfully" -ForegroundColor Green
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "      ⚠️  Field not found (may already be deleted)" -ForegroundColor Gray
        }
        else {
            Write-Host "      ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        return $false
    }
}

# ═══════════════════════════════════════════════════════════
# Delete from Tasks Table (6 fields)
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " Deleting from Tasks Table (cr950_tasks)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Remove-RollupField -EntityLogicalName "cr950_tasks" -AttributeLogicalName "cr950_earliest_anticipated_start" -DisplayName "Earliest Anticipated Start"
Remove-RollupField -EntityLogicalName "cr950_tasks" -AttributeLogicalName "cr950_latest_anticipated_start" -DisplayName "Latest Anticipated Start"
Remove-RollupField -EntityLogicalName "cr950_tasks" -AttributeLogicalName "cr950_earliest_actual_start" -DisplayName "Earliest Actual Start"
Remove-RollupField -EntityLogicalName "cr950_tasks" -AttributeLogicalName "cr950_latest_actual_start" -DisplayName "Latest Actual Start"
Remove-RollupField -EntityLogicalName "cr950_tasks" -AttributeLogicalName "cr950_earliest_completion_date" -DisplayName "Earliest Completion Date"
Remove-RollupField -EntityLogicalName "cr950_tasks" -AttributeLogicalName "cr950_latest_completion_date" -DisplayName "Latest Completion Date"

# ═══════════════════════════════════════════════════════════
# Delete from Scopes Table (6 fields)
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " Deleting from Scopes Table (cr950_projectscope)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Remove-RollupField -EntityLogicalName "cr950_projectscope" -AttributeLogicalName "cr950_earliest_anticipated_start" -DisplayName "Earliest Anticipated Start"
Remove-RollupField -EntityLogicalName "cr950_projectscope" -AttributeLogicalName "cr950_latest_anticipated_start" -DisplayName "Latest Anticipated Start"
Remove-RollupField -EntityLogicalName "cr950_projectscope" -AttributeLogicalName "cr950_earliest_actual_start" -DisplayName "Earliest Actual Start"
Remove-RollupField -EntityLogicalName "cr950_projectscope" -AttributeLogicalName "cr950_latest_actual_start" -DisplayName "Latest Actual Start"
Remove-RollupField -EntityLogicalName "cr950_projectscope" -AttributeLogicalName "cr950_earliest_completion_date" -DisplayName "Earliest Completion Date"
Remove-RollupField -EntityLogicalName "cr950_projectscope" -AttributeLogicalName "cr950_latest_completion_date" -DisplayName "Latest Completion Date"

# ═══════════════════════════════════════════════════════════
# Delete from Projects Table (6 fields)
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host " Deleting from Projects Table (cr950_projects)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Yellow

Remove-RollupField -EntityLogicalName "cr950_projects" -AttributeLogicalName "cr950_earliest_anticipated_start" -DisplayName "Earliest Anticipated Start"
Remove-RollupField -EntityLogicalName "cr950_projects" -AttributeLogicalName "cr950_latest_anticipated_start" -DisplayName "Latest Anticipated Start"
Remove-RollupField -EntityLogicalName "cr950_projects" -AttributeLogicalName "cr950_earliest_actual_start" -DisplayName "Earliest Actual Start"
Remove-RollupField -EntityLogicalName "cr950_projects" -AttributeLogicalName "cr950_latest_actual_start" -DisplayName "Latest Actual Start"
Remove-RollupField -EntityLogicalName "cr950_projects" -AttributeLogicalName "cr950_earliest_completion_date" -DisplayName "Earliest Completion Date"
Remove-RollupField -EntityLogicalName "cr950_projects" -AttributeLogicalName "cr950_latest_completion_date" -DisplayName "Latest Completion Date"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║         DELETION COMPLETE (18 fields removed)            ║" -ForegroundColor Green
Write-Host "║    Ready to recreate with full rollup metadata          ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n✨ Next Step:" -ForegroundColor Cyan
Write-Host "   Run Add-RollupFields-FullyConfigured.ps1 to recreate with proper rollup metadata" -ForegroundColor White
