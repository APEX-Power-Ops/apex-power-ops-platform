# Add Future-Proofing Fields to Dataverse Tables
# RESA Power Build - Schema Enhancement
# Run this script to add fields for future integrations, auditing, and extensibility

# Configuration
$environmentUrl = "https://org04ad071f.crm.dynamics.com"

# Install required module if not present
if (-not (Get-Module -ListAvailable -Name Microsoft.PowerApps.Administration.PowerShell)) {
    Write-Host "Installing Microsoft.PowerApps.Administration.PowerShell module..." -ForegroundColor Yellow
    Install-Module -Name Microsoft.PowerApps.Administration.PowerShell -Force -AllowClobber
}

# Import module
Import-Module Microsoft.PowerApps.Administration.PowerShell

# Connect to Dataverse
Write-Host "`nConnecting to Dataverse environment..." -ForegroundColor Cyan
Write-Host "Environment: $environmentUrl" -ForegroundColor Gray
Add-PowerAppsAccount

# Field definitions organized by task
$fieldDefinitions = @{
    "External System Fields" = @(
        @{
            Table = "cr950_project"
            Fields = @(
                @{ LogicalName = "cr950_external_system_id"; DisplayName = "External System ID"; Type = "String"; MaxLength = 100; Description = "Unique identifier from external system (QuickBooks, legacy system, etc.)" }
                @{ LogicalName = "cr950_external_system_name"; DisplayName = "External System Name"; Type = "Picklist"; Description = "Name of the external system this record syncs with"; 
                   Options = @(
                       @{ Value = 1; Label = "QuickBooks" }
                       @{ Value = 2; Label = "Legacy System" }
                       @{ Value = 3; Label = "Excel Import" }
                       @{ Value = 4; Label = "Other" }
                   )
                }
            )
        }
        @{
            Table = "cr950_projectscope"
            Fields = @(
                @{ LogicalName = "cr950_external_system_id"; DisplayName = "External System ID"; Type = "String"; MaxLength = 100; Description = "Unique identifier from external system" }
                @{ LogicalName = "cr950_external_system_name"; DisplayName = "External System Name"; Type = "Picklist"; Description = "Name of the external system"; 
                   Options = @(
                       @{ Value = 1; Label = "QuickBooks" }
                       @{ Value = 2; Label = "Legacy System" }
                       @{ Value = 3; Label = "Excel Import" }
                       @{ Value = 4; Label = "Other" }
                   )
                }
            )
        }
        @{
            Table = "cr950_apparatus"
            Fields = @(
                @{ LogicalName = "cr950_external_system_id"; DisplayName = "External System ID"; Type = "String"; MaxLength = 100; Description = "Unique identifier from external system" }
                @{ LogicalName = "cr950_external_system_name"; DisplayName = "External System Name"; Type = "Picklist"; Description = "Name of the external system"; 
                   Options = @(
                       @{ Value = 1; Label = "QuickBooks" }
                       @{ Value = 2; Label = "Legacy System" }
                       @{ Value = 3; Label = "Excel Import" }
                       @{ Value = 4; Label = "Other" }
                   )
                }
            )
        }
    )
    
    "Soft Delete Fields" = @(
        @{
            Table = "cr950_project"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted (prevents permanent data loss)"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
        @{
            Table = "cr950_location"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
        @{
            Table = "cr950_projectscope"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
        @{
            Table = "cr950_task"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
        @{
            Table = "cr950_apparatus"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
        @{
            Table = "cr950_apparatusrevenue"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
        @{
            Table = "cr950_scopelabordetail"
            Fields = @(
                @{ LogicalName = "cr950_is_deleted"; DisplayName = "Is Deleted"; Type = "Boolean"; Description = "Indicates if record is soft-deleted"; DefaultValue = $false }
                @{ LogicalName = "cr950_deleted_on"; DisplayName = "Deleted On"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Date and time when record was soft-deleted" }
            )
        }
    )
    
    "Geographic Fields" = @(
        @{
            Table = "cr950_location"
            Fields = @(
                @{ LogicalName = "cr950_latitude"; DisplayName = "Latitude"; Type = "Decimal"; Precision = 8; Description = "Geographic latitude for map integration" }
                @{ LogicalName = "cr950_longitude"; DisplayName = "Longitude"; Type = "Decimal"; Precision = 8; Description = "Geographic longitude for map integration" }
                @{ LogicalName = "cr950_geocode_status"; DisplayName = "Geocode Status"; Type = "Picklist"; Description = "Status of geocoding operation"; 
                   Options = @(
                       @{ Value = 1; Label = "Not Geocoded" }
                       @{ Value = 2; Label = "Geocoded" }
                       @{ Value = 3; Label = "Failed" }
                       @{ Value = 4; Label = "Manual Entry" }
                   )
                }
            )
        }
    )
    
    "Tagging Fields" = @(
        @{
            Table = "cr950_project"
            Fields = @(
                @{ LogicalName = "cr950_tags"; DisplayName = "Tags"; Type = "String"; MaxLength = 500; Description = "Comma-separated tags for flexible categorization (e.g., high-voltage,urgent,public-sector)" }
            )
        }
        @{
            Table = "cr950_projectscope"
            Fields = @(
                @{ LogicalName = "cr950_tags"; DisplayName = "Tags"; Type = "String"; MaxLength = 500; Description = "Comma-separated tags for categorization" }
            )
        }
        @{
            Table = "cr950_apparatus"
            Fields = @(
                @{ LogicalName = "cr950_tags"; DisplayName = "Tags"; Type = "String"; MaxLength = 500; Description = "Comma-separated tags for categorization" }
            )
        }
    )
    
    "Data Source Tracking" = @(
        @{
            Table = "cr950_project"
            Fields = @(
                @{ LogicalName = "cr950_data_source"; DisplayName = "Data Source"; Type = "Picklist"; Description = "How this record was created"; 
                   Options = @(
                       @{ Value = 1; Label = "Manual Entry" }
                       @{ Value = 2; Label = "Excel Import" }
                       @{ Value = 3; Label = "API Integration" }
                       @{ Value = 4; Label = "Power Automate Flow" }
                       @{ Value = 5; Label = "Mobile App" }
                       @{ Value = 6; Label = "Bulk Import" }
                   )
                }
                @{ LogicalName = "cr950_sync_status"; DisplayName = "Sync Status"; Type = "Picklist"; Description = "External system sync status"; 
                   Options = @(
                       @{ Value = 1; Label = "Not Synced" }
                       @{ Value = 2; Label = "Pending" }
                       @{ Value = 3; Label = "Synced" }
                       @{ Value = 4; Label = "Error" }
                       @{ Value = 5; Label = "Conflict" }
                   )
                }
                @{ LogicalName = "cr950_last_sync_date"; DisplayName = "Last Sync Date"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Last successful sync with external system" }
            )
        }
        @{
            Table = "cr950_projectscope"
            Fields = @(
                @{ LogicalName = "cr950_data_source"; DisplayName = "Data Source"; Type = "Picklist"; Description = "How this record was created"; 
                   Options = @(
                       @{ Value = 1; Label = "Manual Entry" }
                       @{ Value = 2; Label = "Excel Import" }
                       @{ Value = 3; Label = "API Integration" }
                       @{ Value = 4; Label = "Power Automate Flow" }
                       @{ Value = 5; Label = "Mobile App" }
                       @{ Value = 6; Label = "Bulk Import" }
                   )
                }
                @{ LogicalName = "cr950_sync_status"; DisplayName = "Sync Status"; Type = "Picklist"; Description = "External system sync status"; 
                   Options = @(
                       @{ Value = 1; Label = "Not Synced" }
                       @{ Value = 2; Label = "Pending" }
                       @{ Value = 3; Label = "Synced" }
                       @{ Value = 4; Label = "Error" }
                       @{ Value = 5; Label = "Conflict" }
                   )
                }
                @{ LogicalName = "cr950_last_sync_date"; DisplayName = "Last Sync Date"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Last successful sync with external system" }
            )
        }
        @{
            Table = "cr950_apparatus"
            Fields = @(
                @{ LogicalName = "cr950_data_source"; DisplayName = "Data Source"; Type = "Picklist"; Description = "How this record was created"; 
                   Options = @(
                       @{ Value = 1; Label = "Manual Entry" }
                       @{ Value = 2; Label = "Excel Import" }
                       @{ Value = 3; Label = "API Integration" }
                       @{ Value = 4; Label = "Power Automate Flow" }
                       @{ Value = 5; Label = "Mobile App" }
                       @{ Value = 6; Label = "Bulk Import" }
                   )
                }
                @{ LogicalName = "cr950_sync_status"; DisplayName = "Sync Status"; Type = "Picklist"; Description = "External system sync status"; 
                   Options = @(
                       @{ Value = 1; Label = "Not Synced" }
                       @{ Value = 2; Label = "Pending" }
                       @{ Value = 3; Label = "Synced" }
                       @{ Value = 4; Label = "Error" }
                       @{ Value = 5; Label = "Conflict" }
                   )
                }
                @{ LogicalName = "cr950_last_sync_date"; DisplayName = "Last Sync Date"; Type = "DateTime"; DateTimeBehavior = "UserLocal"; Description = "Last successful sync with external system" }
            )
        }
        @{
            Table = "cr950_apparatusrevenue"
            Fields = @(
                @{ LogicalName = "cr950_data_source"; DisplayName = "Data Source"; Type = "Picklist"; Description = "How this record was created"; 
                   Options = @(
                       @{ Value = 1; Label = "Manual Entry" }
                       @{ Value = 2; Label = "Excel Import" }
                       @{ Value = 3; Label = "API Integration" }
                       @{ Value = 4; Label = "Power Automate Flow" }
                       @{ Value = 5; Label = "Mobile App" }
                       @{ Value = 6; Label = "Bulk Import" }
                   )
                }
            )
        }
    )
    
    "Versioning Fields (ScopeLaborDetail)" = @(
        @{
            Table = "cr950_scopelabordetail"
            Fields = @(
                @{ LogicalName = "cr950_version_number"; DisplayName = "Version Number"; Type = "Integer"; Description = "Version number for rate changes (1, 2, 3...)" }
                @{ LogicalName = "cr950_effective_date"; DisplayName = "Effective Date"; Type = "DateOnly"; Description = "Date when this version becomes active" }
                @{ LogicalName = "cr950_expiration_date"; DisplayName = "Expiration Date"; Type = "DateOnly"; Description = "Date when this version expires (optional)" }
                @{ LogicalName = "cr950_is_current_version"; DisplayName = "Is Current Version"; Type = "Boolean"; Description = "Indicates if this is the currently active version"; DefaultValue = $true }
            )
        }
    )
}

# Summary of changes
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SCHEMA ENHANCEMENT PLAN" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$totalFields = 0
foreach ($category in $fieldDefinitions.Keys) {
    Write-Host "📁 $category" -ForegroundColor Yellow
    foreach ($tableDef in $fieldDefinitions[$category]) {
        $fieldCount = $tableDef.Fields.Count
        $totalFields += $fieldCount
        Write-Host "   ├─ $($tableDef.Table): $fieldCount fields" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "Total fields to add: $totalFields" -ForegroundColor Green
Write-Host "`nNOTE: This is a DRY RUN script template." -ForegroundColor Yellow
Write-Host "To actually create fields, you need to:" -ForegroundColor Yellow
Write-Host "1. Use Power Platform CLI (pac)" -ForegroundColor Gray
Write-Host "2. Use Dataverse Web API" -ForegroundColor Gray
Write-Host "3. Manually add via Power Apps maker portal" -ForegroundColor Gray
Write-Host "`nRecommendation: Add fields manually via Power Apps portal for now." -ForegroundColor Cyan
Write-Host "This script serves as your reference guide." -ForegroundColor Cyan

# Export field definitions to JSON for reference
$jsonPath = Join-Path $PSScriptRoot "field_definitions.json"
$fieldDefinitions | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8
Write-Host "`n✅ Field definitions exported to: $jsonPath" -ForegroundColor Green
Write-Host "Use this as reference when adding fields manually.`n" -ForegroundColor Gray
