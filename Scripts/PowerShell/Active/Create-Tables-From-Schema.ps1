# Create Core Tables from Schema CSVs
# Created: November 30, 2025
# Purpose: Read schema CSV files and create/recreate Dataverse tables
# Version: 1.0.0

param(
    [string]$SchemaFolder = "$PSScriptRoot\..\..\CSV_Templates\Schema",
    [string]$SchemaFile = "",
    [switch]$DeleteExisting = $false,
    [switch]$WhatIf = $false
)

# Import reusable functions
. "$PSScriptRoot\..\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Schema-Driven Table Creator (v1.0.0)          ║" -ForegroundColor Cyan
Write-Host "║  Creates tables from CSV schema definitions                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($WhatIf) {
    Write-Host "⚠️  WHAT-IF MODE - No changes will be made`n" -ForegroundColor Yellow
}

# ============================================================================
# TABLE DEFINITIONS (order matters for lookups!)
# ============================================================================
$tableDefinitions = @(
    @{ 
        Order = 1
        LogicalName = "cr950_client"
        DisplayName = "Client"
        PluralName = "Clients"
        Description = "Client/customer companies"
        PrimaryField = "cr950_client_name"
        PrimaryFieldDisplay = "Client Name"
        SchemaFile = "01_Client_Schema.csv"
    },
    @{ 
        Order = 2
        LogicalName = "cr950_site"
        DisplayName = "Site"
        PluralName = "Sites"
        Description = "Physical locations/facilities"
        PrimaryField = "cr950_site_name"
        PrimaryFieldDisplay = "Site Name"
        SchemaFile = "02_Site_Schema.csv"
    },
    @{ 
        Order = 3
        LogicalName = "cr950_project"
        DisplayName = "Project"
        PluralName = "Projects"
        Description = "Testing projects"
        PrimaryField = "cr950_project_name"
        PrimaryFieldDisplay = "Project Name"
        SchemaFile = "03_Project_Schema.csv"
    },
    @{ 
        Order = 4
        LogicalName = "cr950_scope"
        DisplayName = "Scope"
        PluralName = "Scopes"
        Description = "Project scopes of work"
        PrimaryField = "cr950_scope_name"
        PrimaryFieldDisplay = "Scope Name"
        SchemaFile = "04_Scope_Schema.csv"
    },
    @{ 
        Order = 5
        LogicalName = "cr950_task"
        DisplayName = "Task"
        PluralName = "Tasks"
        Description = "Individual test tasks"
        PrimaryField = "cr950_task_name"
        PrimaryFieldDisplay = "Task Name"
        SchemaFile = "05_Task_Schema.csv"
    },
    @{ 
        Order = 6
        LogicalName = "cr950_apparatus"
        DisplayName = "Apparatus"
        PluralName = "Apparatuses"
        Description = "Equipment being tested"
        PrimaryField = "cr950_apparatus_name"
        PrimaryFieldDisplay = "Apparatus Name"
        SchemaFile = "06_Apparatus_Schema.csv"
    },
    @{ 
        Order = 7
        LogicalName = "cr950_scopelabordetail"
        DisplayName = "Scope Labor Detail"
        PluralName = "Scope Labor Details"
        Description = "Labor breakdown for scopes"
        PrimaryField = "cr950_scopelabor_name"
        PrimaryFieldDisplay = "Labor Detail Name"
        SchemaFile = "07_ScopeLaborDetail_Schema.csv"
    }
)

# Connect to Dataverse
Connect-Dataverse

if (-not $script:DataverseToken) {
    Write-Host "❌ Failed to connect. Please check environment variables." -ForegroundColor Red
    exit 1
}

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
        [string]$PrimaryFieldDisplayName,
        [int]$PrimaryFieldMaxLength = 200
    )
    
    Write-Host "`n📋 Creating table: $DisplayName ($LogicalName)" -ForegroundColor Cyan
    
    if ($WhatIf) {
        Write-Host "   [WhatIf] Would create table" -ForegroundColor Yellow
        return $true
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
                    "LocalizedLabels" = @(
                        @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Primary field for $DisplayName"; "LanguageCode" = 1033 }
                    )
                }
                "DisplayName" = @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                    "LocalizedLabels" = @(
                        @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $PrimaryFieldDisplayName; "LanguageCode" = 1033 }
                    )
                }
                "RequiredLevel" = @{ "Value" = "ApplicationRequired"; "CanBeChanged" = $true }
                "SchemaName" = $PrimaryFieldLogicalName
                "MaxLength" = $PrimaryFieldMaxLength
                "IsPrimaryName" = $true
            }
        )
        "PrimaryNameAttribute" = $PrimaryFieldLogicalName
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $Description; "LanguageCode" = 1033 }
            )
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $DisplayName; "LanguageCode" = 1033 }
            )
        }
        "DisplayCollectionName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $PluralName; "LanguageCode" = 1033 }
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
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            Write-Host "   ⚠️ Table already exists" -ForegroundColor Yellow
            return $true
        }
        Write-Host "   ❌ Failed to create table: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($errorDetail) { Write-Host "   Error: $($errorDetail.error.message)" -ForegroundColor Red }
        }
        return $false
    }
}

# ============================================================================
# FUNCTION: Add Field from Schema Row
# ============================================================================
function Add-FieldFromSchema {
    param(
        [string]$TableLogicalName,
        [PSCustomObject]$SchemaRow
    )
    
    $fieldName = $SchemaRow.FieldLogicalName
    $displayName = $SchemaRow.DisplayName
    $fieldType = $SchemaRow.Type
    $maxLength = if ($SchemaRow.MaxLength) { [int]$SchemaRow.MaxLength } else { 100 }
    $description = $SchemaRow.Description
    
    Write-Host "   ➕ $displayName ($fieldType)" -ForegroundColor Gray
    
    if ($WhatIf) {
        Write-Host "      [WhatIf] Would add field" -ForegroundColor Yellow
        return $true
    }
    
    $fieldDefinition = @{
        "SchemaName" = $fieldName
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $description; "LanguageCode" = 1033 }
            )
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $displayName; "LanguageCode" = 1033 }
            )
        }
        "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
    }
    
    switch ($fieldType) {
        "String" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $fieldDefinition["MaxLength"] = $maxLength
            $fieldDefinition["FormatName"] = @{ "Value" = "Text" }
        }
        "Memo" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.MemoAttributeMetadata"
            $fieldDefinition["MaxLength"] = if ($maxLength -gt 100) { $maxLength } else { 2000 }
        }
        "Boolean" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
            $fieldDefinition["DefaultValue"] = $false
            $fieldDefinition["OptionSet"] = @{
                "TrueOption" = @{ "Value" = 1; "Label" = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; "LocalizedLabels" = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Yes"; "LanguageCode" = 1033 }) } }
                "FalseOption" = @{ "Value" = 0; "Label" = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; "LocalizedLabels" = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "No"; "LanguageCode" = 1033 }) } }
            }
        }
        "Integer" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
            $fieldDefinition["Format"] = "None"
            $fieldDefinition["MinValue"] = -2147483648
            $fieldDefinition["MaxValue"] = 2147483647
        }
        "Decimal" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
            $fieldDefinition["Precision"] = 2
            $fieldDefinition["MinValue"] = -100000000000
            $fieldDefinition["MaxValue"] = 100000000000
        }
        "Currency" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.MoneyAttributeMetadata"
            $fieldDefinition["Precision"] = 2
            $fieldDefinition["PrecisionSource"] = 2
        }
        "DateTime" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $fieldDefinition["Format"] = "DateAndTime"
            $fieldDefinition["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
        }
        "Lookup" {
            # Skip lookups - handled separately
            return $true
        }
        default {
            Write-Host "      ⚠️ Unknown type: $fieldType, treating as String" -ForegroundColor Yellow
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $fieldDefinition["MaxLength"] = 100
            $fieldDefinition["FormatName"] = @{ "Value" = "Text" }
        }
    }
    
    $body = $fieldDefinition | ConvertTo-Json -Depth 15
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $body
        
        Write-Host "      ✅ Added" -ForegroundColor Green
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            Write-Host "      ⚠️ Exists" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# FUNCTION: Add Lookup Relationship
# ============================================================================
function Add-LookupFromSchema {
    param(
        [string]$FromTable,
        [PSCustomObject]$SchemaRow
    )
    
    $fieldName = $SchemaRow.FieldLogicalName
    $displayName = $SchemaRow.DisplayName
    $targetTable = $SchemaRow.LookupTarget
    $relationshipName = "cr950_${FromTable}_${targetTable}"
    
    Write-Host "   🔗 $displayName ($FromTable → $targetTable)" -ForegroundColor Cyan
    
    if ($WhatIf) {
        Write-Host "      [WhatIf] Would create lookup" -ForegroundColor Yellow
        return $true
    }
    
    $relationshipDefinition = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
        "SchemaName" = $relationshipName
        "ReferencedEntity" = $targetTable
        "ReferencingEntity" = $FromTable
        "Lookup" = @{
            "SchemaName" = $fieldName
            "DisplayName" = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                "LocalizedLabels" = @(
                    @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $displayName; "LanguageCode" = 1033 }
                )
            }
            "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
        }
        "CascadeConfiguration" = @{
            "Assign" = "NoCascade"
            "Delete" = "RemoveLink"
            "Merge" = "NoCascade"
            "Reparent" = "NoCascade"
            "Share" = "NoCascade"
            "Unshare" = "NoCascade"
        }
    }
    
    $body = $relationshipDefinition | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/RelationshipDefinitions" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $body
        
        Write-Host "      ✅ Lookup created" -ForegroundColor Green
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            Write-Host "      ⚠️ Lookup exists" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# FUNCTION: Delete Table
# ============================================================================
function Remove-DataverseTable {
    param([string]$LogicalName)
    
    Write-Host "🗑️  Deleting table: $LogicalName" -ForegroundColor Red
    
    if ($WhatIf) {
        Write-Host "   [WhatIf] Would delete table" -ForegroundColor Yellow
        return $true
    }
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$LogicalName')" `
            -Method Delete `
            -Headers $script:DataverseHeaders
        
        Write-Host "   ✅ Deleted" -ForegroundColor Green
        Start-Sleep -Seconds 2  # Give Dataverse time to process
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "   ℹ️ Table doesn't exist" -ForegroundColor Gray
            return $true
        }
        Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Determine which tables to process
$tablesToProcess = @()
if ($SchemaFile) {
    # Single file mode
    $tablesToProcess = $tableDefinitions | Where-Object { $_.SchemaFile -eq $SchemaFile }
    if ($tablesToProcess.Count -eq 0) {
        Write-Host "❌ Schema file not found in definitions: $SchemaFile" -ForegroundColor Red
        exit 1
    }
} else {
    # Process all tables in order
    $tablesToProcess = $tableDefinitions | Sort-Object Order
}

Write-Host "`nTables to process: $($tablesToProcess.Count)" -ForegroundColor Cyan
$tablesToProcess | ForEach-Object { Write-Host "  $($_.Order). $($_.DisplayName) ($($_.LogicalName))" }

# Phase 1: Delete existing tables (if requested) - reverse order for lookups
if ($DeleteExisting) {
    Write-Host "`n" + "="*60 -ForegroundColor Red
    Write-Host "PHASE 1: DELETING EXISTING TABLES (REVERSE ORDER)" -ForegroundColor Red
    Write-Host "="*60 -ForegroundColor Red
    
    $reversed = $tablesToProcess | Sort-Object Order -Descending
    foreach ($table in $reversed) {
        Remove-DataverseTable -LogicalName $table.LogicalName
    }
}

# Phase 2: Create tables
Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "PHASE 2: CREATING TABLES" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green

foreach ($table in $tablesToProcess) {
    $created = New-DataverseTable `
        -LogicalName $table.LogicalName `
        -DisplayName $table.DisplayName `
        -PluralName $table.PluralName `
        -Description $table.Description `
        -PrimaryFieldLogicalName $table.PrimaryField `
        -PrimaryFieldDisplayName $table.PrimaryFieldDisplay
    
    if (-not $created) {
        Write-Host "⚠️ Stopping due to table creation failure" -ForegroundColor Red
        exit 1
    }
}

# Phase 3: Add fields from schema files
Write-Host "`n" + "="*60 -ForegroundColor Blue
Write-Host "PHASE 3: ADDING FIELDS FROM SCHEMA" -ForegroundColor Blue
Write-Host "="*60 -ForegroundColor Blue

$lookupFields = @()  # Collect lookups for Phase 4

foreach ($table in $tablesToProcess) {
    $schemaPath = Join-Path $SchemaFolder $table.SchemaFile
    
    if (-not (Test-Path $schemaPath)) {
        Write-Host "❌ Schema file not found: $schemaPath" -ForegroundColor Red
        continue
    }
    
    Write-Host "`n📄 Processing: $($table.DisplayName) from $($table.SchemaFile)" -ForegroundColor Magenta
    
    $schema = Import-Csv -Path $schemaPath
    
    foreach ($row in $schema) {
        # Skip the primary field (already created with table)
        if ($row.FieldLogicalName -eq $table.PrimaryField) {
            Write-Host "   ⏭️ Skipping primary field: $($row.DisplayName)" -ForegroundColor Gray
            continue
        }
        
        if ($row.Type -eq "Lookup") {
            # Save lookups for Phase 4
            $lookupFields += @{
                FromTable = $table.LogicalName
                SchemaRow = $row
            }
        } else {
            Add-FieldFromSchema -TableLogicalName $table.LogicalName -SchemaRow $row
        }
    }
}

# Phase 4: Create lookup relationships
Write-Host "`n" + "="*60 -ForegroundColor Yellow
Write-Host "PHASE 4: CREATING LOOKUP RELATIONSHIPS" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Yellow

foreach ($lookup in $lookupFields) {
    Add-LookupFromSchema -FromTable $lookup.FromTable -SchemaRow $lookup.SchemaRow
}

# Summary
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "COMPLETE!" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nCreated $($tablesToProcess.Count) tables with fields and lookups." -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Verify tables in Power Apps make.powerapps.com"
Write-Host "  2. Add tables to solution"
Write-Host "  3. Import test data via web app"
