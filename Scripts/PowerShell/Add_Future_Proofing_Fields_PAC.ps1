# Add Future-Proofing Fields to Dataverse using Power Platform CLI
# RESA Power Build - Schema Enhancement v1.3.0.4
# Uses 'pac' CLI to add fields programmatically

# Prerequisites: Install Power Platform CLI
# Install: winget install Microsoft.PowerPlatformCLI

param(
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentUrl = "https://org0f5a3756.crm.dynamics.com"
)

# Check if pac CLI is installed
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DATAVERSE SCHEMA ENHANCEMENT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$pacInstalled = Get-Command pac -ErrorAction SilentlyContinue
if (-not $pacInstalled) {
    Write-Host "❌ Power Platform CLI (pac) not found!" -ForegroundColor Red
    Write-Host "`nInstall with: winget install Microsoft.PowerPlatformCLI" -ForegroundColor Yellow
    Write-Host "Or download from: https://aka.ms/PowerPlatformCLI`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Power Platform CLI found" -ForegroundColor Green
Write-Host "Environment: $EnvironmentUrl`n" -ForegroundColor Gray

# Authenticate to environment
Write-Host "Authenticating to Dataverse..." -ForegroundColor Cyan
pac auth create --url $EnvironmentUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Authentication failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Authentication successful`n" -ForegroundColor Green

# Field definitions organized by task
$tasks = @{
    "External System ID Fields" = @(
        @{
            Table = "cr950_project"
            DisplayName = "Project"
            Fields = @(
                @{
                    SchemaName = "cr950_external_system_id"
                    DisplayName = "External System ID"
                    Type = "string"
                    MaxLength = 100
                    Description = "Unique identifier from external system (QuickBooks, legacy system, etc.)"
                },
                @{
                    SchemaName = "cr950_external_system_name"
                    DisplayName = "External System Name"
                    Type = "picklist"
                    Description = "Name of the external system this record syncs with"
                    Options = @(
                        @{ Value = 1; Label = "QuickBooks" },
                        @{ Value = 2; Label = "Legacy System" },
                        @{ Value = 3; Label = "Excel Import" },
                        @{ Value = 4; Label = "Other" }
                    )
                }
            )
        },
        @{
            Table = "cr950_projectscope"
            DisplayName = "Project Scope"
            Fields = @(
                @{
                    SchemaName = "cr950_external_system_id"
                    DisplayName = "External System ID"
                    Type = "string"
                    MaxLength = 100
                    Description = "Unique identifier from external system"
                },
                @{
                    SchemaName = "cr950_external_system_name"
                    DisplayName = "External System Name"
                    Type = "picklist"
                    Description = "Name of the external system"
                    Options = @(
                        @{ Value = 1; Label = "QuickBooks" },
                        @{ Value = 2; Label = "Legacy System" },
                        @{ Value = 3; Label = "Excel Import" },
                        @{ Value = 4; Label = "Other" }
                    )
                }
            )
        },
        @{
            Table = "cr950_apparatus"
            DisplayName = "Apparatus"
            Fields = @(
                @{
                    SchemaName = "cr950_external_system_id"
                    DisplayName = "External System ID"
                    Type = "string"
                    MaxLength = 100
                    Description = "Unique identifier from external system"
                },
                @{
                    SchemaName = "cr950_external_system_name"
                    DisplayName = "External System Name"
                    Type = "picklist"
                    Description = "Name of the external system"
                    Options = @(
                        @{ Value = 1; Label = "QuickBooks" },
                        @{ Value = 2; Label = "Legacy System" },
                        @{ Value = 3; Label = "Excel Import" },
                        @{ Value = 4; Label = "Other" }
                    )
                }
            )
        }
    )
    
    "Soft Delete Fields" = @(
        @{
            Table = "cr950_project"
            DisplayName = "Project"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted (prevents permanent data loss)"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        },
        @{
            Table = "cr950_location"
            DisplayName = "Location"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        },
        @{
            Table = "cr950_projectscope"
            DisplayName = "Project Scope"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        },
        @{
            Table = "cr950_task"
            DisplayName = "Task"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        },
        @{
            Table = "cr950_apparatus"
            DisplayName = "Apparatus"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        },
        @{
            Table = "cr950_apparatusrevenue"
            DisplayName = "Apparatus Revenue"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        },
        @{
            Table = "cr950_scopelabordetail"
            DisplayName = "Scope Labor Detail"
            Fields = @(
                @{
                    SchemaName = "cr950_is_deleted"
                    DisplayName = "Is Deleted"
                    Type = "boolean"
                    Description = "Indicates if record is soft-deleted"
                    DefaultValue = $false
                },
                @{
                    SchemaName = "cr950_deleted_on"
                    DisplayName = "Deleted On"
                    Type = "datetime"
                    Description = "Date and time when record was soft-deleted"
                }
            )
        }
    )
    
    "Geographic Fields" = @(
        @{
            Table = "cr950_location"
            DisplayName = "Location"
            Fields = @(
                @{
                    SchemaName = "cr950_latitude"
                    DisplayName = "Latitude"
                    Type = "decimal"
                    Precision = 8
                    Description = "Geographic latitude for map integration"
                    MinValue = -90
                    MaxValue = 90
                },
                @{
                    SchemaName = "cr950_longitude"
                    DisplayName = "Longitude"
                    Type = "decimal"
                    Precision = 8
                    Description = "Geographic longitude for map integration"
                    MinValue = -180
                    MaxValue = 180
                },
                @{
                    SchemaName = "cr950_geocode_status"
                    DisplayName = "Geocode Status"
                    Type = "picklist"
                    Description = "Status of geocoding operation"
                    Options = @(
                        @{ Value = 1; Label = "Not Geocoded" },
                        @{ Value = 2; Label = "Geocoded" },
                        @{ Value = 3; Label = "Failed" },
                        @{ Value = 4; Label = "Manual Entry" }
                    )
                }
            )
        }
    )
    
    "Tagging Fields" = @(
        @{
            Table = "cr950_project"
            DisplayName = "Project"
            Fields = @(
                @{
                    SchemaName = "cr950_tags"
                    DisplayName = "Tags"
                    Type = "string"
                    MaxLength = 500
                    Description = "Comma-separated tags for flexible categorization"
                }
            )
        },
        @{
            Table = "cr950_projectscope"
            DisplayName = "Project Scope"
            Fields = @(
                @{
                    SchemaName = "cr950_tags"
                    DisplayName = "Tags"
                    Type = "string"
                    MaxLength = 500
                    Description = "Comma-separated tags for categorization"
                }
            )
        },
        @{
            Table = "cr950_apparatus"
            DisplayName = "Apparatus"
            Fields = @(
                @{
                    SchemaName = "cr950_tags"
                    DisplayName = "Tags"
                    Type = "string"
                    MaxLength = 500
                    Description = "Comma-separated tags for categorization"
                }
            )
        }
    )
    
    "Data Source Tracking" = @(
        @{
            Table = "cr950_project"
            DisplayName = "Project"
            Fields = @(
                @{
                    SchemaName = "cr950_data_source"
                    DisplayName = "Data Source"
                    Type = "picklist"
                    Description = "How this record was created"
                    Options = @(
                        @{ Value = 1; Label = "Manual Entry" },
                        @{ Value = 2; Label = "Excel Import" },
                        @{ Value = 3; Label = "API Integration" },
                        @{ Value = 4; Label = "Power Automate Flow" },
                        @{ Value = 5; Label = "Mobile App" },
                        @{ Value = 6; Label = "Bulk Import" }
                    )
                },
                @{
                    SchemaName = "cr950_sync_status"
                    DisplayName = "Sync Status"
                    Type = "picklist"
                    Description = "External system sync status"
                    Options = @(
                        @{ Value = 1; Label = "Not Synced" },
                        @{ Value = 2; Label = "Pending" },
                        @{ Value = 3; Label = "Synced" },
                        @{ Value = 4; Label = "Error" },
                        @{ Value = 5; Label = "Conflict" }
                    )
                },
                @{
                    SchemaName = "cr950_last_sync_date"
                    DisplayName = "Last Sync Date"
                    Type = "datetime"
                    Description = "Last successful sync with external system"
                }
            )
        },
        @{
            Table = "cr950_projectscope"
            DisplayName = "Project Scope"
            Fields = @(
                @{
                    SchemaName = "cr950_data_source"
                    DisplayName = "Data Source"
                    Type = "picklist"
                    Description = "How this record was created"
                    Options = @(
                        @{ Value = 1; Label = "Manual Entry" },
                        @{ Value = 2; Label = "Excel Import" },
                        @{ Value = 3; Label = "API Integration" },
                        @{ Value = 4; Label = "Power Automate Flow" },
                        @{ Value = 5; Label = "Mobile App" },
                        @{ Value = 6; Label = "Bulk Import" }
                    )
                },
                @{
                    SchemaName = "cr950_sync_status"
                    DisplayName = "Sync Status"
                    Type = "picklist"
                    Description = "External system sync status"
                    Options = @(
                        @{ Value = 1; Label = "Not Synced" },
                        @{ Value = 2; Label = "Pending" },
                        @{ Value = 3; Label = "Synced" },
                        @{ Value = 4; Label = "Error" },
                        @{ Value = 5; Label = "Conflict" }
                    )
                },
                @{
                    SchemaName = "cr950_last_sync_date"
                    DisplayName = "Last Sync Date"
                    Type = "datetime"
                    Description = "Last successful sync with external system"
                }
            )
        },
        @{
            Table = "cr950_apparatus"
            DisplayName = "Apparatus"
            Fields = @(
                @{
                    SchemaName = "cr950_data_source"
                    DisplayName = "Data Source"
                    Type = "picklist"
                    Description = "How this record was created"
                    Options = @(
                        @{ Value = 1; Label = "Manual Entry" },
                        @{ Value = 2; Label = "Excel Import" },
                        @{ Value = 3; Label = "API Integration" },
                        @{ Value = 4; Label = "Power Automate Flow" },
                        @{ Value = 5; Label = "Mobile App" },
                        @{ Value = 6; Label = "Bulk Import" }
                    )
                },
                @{
                    SchemaName = "cr950_sync_status"
                    DisplayName = "Sync Status"
                    Type = "picklist"
                    Description = "External system sync status"
                    Options = @(
                        @{ Value = 1; Label = "Not Synced" },
                        @{ Value = 2; Label = "Pending" },
                        @{ Value = 3; Label = "Synced" },
                        @{ Value = 4; Label = "Error" },
                        @{ Value = 5; Label = "Conflict" }
                    )
                },
                @{
                    SchemaName = "cr950_last_sync_date"
                    DisplayName = "Last Sync Date"
                    Type = "datetime"
                    Description = "Last successful sync with external system"
                }
            )
        },
        @{
            Table = "cr950_apparatusrevenue"
            DisplayName = "Apparatus Revenue"
            Fields = @(
                @{
                    SchemaName = "cr950_data_source"
                    DisplayName = "Data Source"
                    Type = "picklist"
                    Description = "How this record was created"
                    Options = @(
                        @{ Value = 1; Label = "Manual Entry" },
                        @{ Value = 2; Label = "Excel Import" },
                        @{ Value = 3; Label = "API Integration" },
                        @{ Value = 4; Label = "Power Automate Flow" },
                        @{ Value = 5; Label = "Mobile App" },
                        @{ Value = 6; Label = "Bulk Import" }
                    )
                }
            )
        }
    )
    
    "Versioning Fields" = @(
        @{
            Table = "cr950_scopelabordetail"
            DisplayName = "Scope Labor Detail"
            Fields = @(
                @{
                    SchemaName = "cr950_version_number"
                    DisplayName = "Version Number"
                    Type = "integer"
                    Description = "Version number for rate changes (1, 2, 3...)"
                    MinValue = 1
                },
                @{
                    SchemaName = "cr950_effective_date"
                    DisplayName = "Effective Date"
                    Type = "datetime"
                    DateOnly = $true
                    Description = "Date when this version becomes active"
                },
                @{
                    SchemaName = "cr950_expiration_date"
                    DisplayName = "Expiration Date"
                    Type = "datetime"
                    DateOnly = $true
                    Description = "Date when this version expires (optional)"
                },
                @{
                    SchemaName = "cr950_is_current_version"
                    DisplayName = "Is Current Version"
                    Type = "boolean"
                    Description = "Indicates if this is the currently active version"
                    DefaultValue = $true
                }
            )
        }
    )
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FIELD ADDITION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$totalFields = 0
foreach ($taskName in $tasks.Keys) {
    Write-Host "📁 $taskName" -ForegroundColor Yellow
    foreach ($tableDef in $tasks[$taskName]) {
        $fieldCount = $tableDef.Fields.Count
        $totalFields += $fieldCount
        Write-Host "   ├─ $($tableDef.DisplayName): $fieldCount fields" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "Total fields to add: $totalFields`n" -ForegroundColor Green

# Confirm before proceeding
$confirmation = Read-Host "Proceed with adding fields? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "`n❌ Operation cancelled by user`n" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CREATING FIELDS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$successCount = 0
$errorCount = 0
$errors = @()

foreach ($taskName in $tasks.Keys) {
    Write-Host "`n📦 $taskName" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Gray
    
    foreach ($tableDef in $tasks[$taskName]) {
        Write-Host "`n  Table: $($tableDef.DisplayName) ($($tableDef.Table))" -ForegroundColor Yellow
        
        foreach ($field in $tableDef.Fields) {
            Write-Host "    → Adding: $($field.DisplayName) ($($field.SchemaName))..." -ForegroundColor Gray -NoNewline
            
            try {
                # Build command based on field type
                switch ($field.Type) {
                    "string" {
                        $cmd = "pac data create column --table-name $($tableDef.Table) --column-name $($field.SchemaName) --display-name `"$($field.DisplayName)`" --data-type SingleLineOfText --max-length $($field.MaxLength) --description `"$($field.Description)`" --searchable true"
                    }
                    "boolean" {
                        $defaultVal = if ($field.DefaultValue) { "true" } else { "false" }
                        $cmd = "pac data create column --table-name $($tableDef.Table) --column-name $($field.SchemaName) --display-name `"$($field.DisplayName)`" --data-type Boolean --default-value $defaultVal --description `"$($field.Description)`""
                    }
                    "datetime" {
                        $format = if ($field.DateOnly) { "DateOnly" } else { "DateAndTime" }
                        $cmd = "pac data create column --table-name $($tableDef.Table) --column-name $($field.SchemaName) --display-name `"$($field.DisplayName)`" --data-type DateTime --format $format --description `"$($field.Description)`""
                    }
                    "integer" {
                        $cmd = "pac data create column --table-name $($tableDef.Table) --column-name $($field.SchemaName) --display-name `"$($field.DisplayName)`" --data-type WholeNumber --min-value $($field.MinValue) --description `"$($field.Description)`""
                    }
                    "decimal" {
                        $cmd = "pac data create column --table-name $($tableDef.Table) --column-name $($field.SchemaName) --display-name `"$($field.DisplayName)`" --data-type DecimalNumber --precision $($field.Precision) --min-value $($field.MinValue) --max-value $($field.MaxValue) --description `"$($field.Description)`""
                    }
                    "picklist" {
                        # Note: pac CLI requires creating choice (option set) first, then column
                        # For simplicity, we'll output instructions for manual creation
                        Write-Host " ⚠️ MANUAL REQUIRED" -ForegroundColor Yellow
                        Write-Host "      (Choice fields need manual creation via portal)" -ForegroundColor DarkYellow
                        $errors += @{
                            Table = $tableDef.DisplayName
                            Field = $field.DisplayName
                            Reason = "Choice field - requires manual creation"
                            Options = $field.Options
                        }
                        continue
                    }
                }
                
                # Execute command (for non-picklist fields)
                if ($field.Type -ne "picklist") {
                    Invoke-Expression $cmd | Out-Null
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host " ✅" -ForegroundColor Green
                        $successCount++
                    } else {
                        Write-Host " ❌" -ForegroundColor Red
                        $errorCount++
                        $errors += @{
                            Table = $tableDef.DisplayName
                            Field = $field.DisplayName
                            Reason = "CLI error (code: $LASTEXITCODE)"
                        }
                    }
                }
                
            } catch {
                Write-Host " ❌" -ForegroundColor Red
                $errorCount++
                $errors += @{
                    Table = $tableDef.DisplayName
                    Field = $field.DisplayName
                    Reason = $_.Exception.Message
                }
            }
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESULTS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✅ Successfully created: $successCount fields" -ForegroundColor Green
Write-Host "❌ Errors: $errorCount fields" -ForegroundColor Red

if ($errors.Count -gt 0) {
    Write-Host "`n⚠️ MANUAL ACTION REQUIRED:`n" -ForegroundColor Yellow
    
    # Group errors by type
    $choiceFields = $errors | Where-Object { $_.Reason -like "*Choice field*" }
    $otherErrors = $errors | Where-Object { $_.Reason -notlike "*Choice field*" }
    
    if ($choiceFields.Count -gt 0) {
        Write-Host "📋 Choice Fields (Create via Power Apps Portal):`n" -ForegroundColor Yellow
        foreach ($error in $choiceFields) {
            Write-Host "  Table: $($error.Table)" -ForegroundColor Gray
            Write-Host "  Field: $($error.Field)" -ForegroundColor Gray
            if ($error.Options) {
                Write-Host "  Options:" -ForegroundColor Gray
                foreach ($opt in $error.Options) {
                    Write-Host "    $($opt.Value) = $($opt.Label)" -ForegroundColor DarkGray
                }
            }
            Write-Host ""
        }
    }
    
    if ($otherErrors.Count -gt 0) {
        Write-Host "❌ Actual Errors:`n" -ForegroundColor Red
        foreach ($error in $otherErrors) {
            Write-Host "  Table: $($error.Table)" -ForegroundColor Gray
            Write-Host "  Field: $($error.Field)" -ForegroundColor Gray
            Write-Host "  Reason: $($error.Reason)" -ForegroundColor DarkRed
            Write-Host ""
        }
    }
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Manually create Choice fields via Power Apps maker portal" -ForegroundColor Gray
Write-Host "2. Verify all fields were created correctly" -ForegroundColor Gray
Write-Host "3. Update forms to show new fields" -ForegroundColor Gray
Write-Host "4. Export solution v1.3.0.4`n" -ForegroundColor Gray
