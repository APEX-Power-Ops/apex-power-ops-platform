# Create Estimators Table for RESA Power Build
# Created: November 28, 2025
# Purpose: Create Estimators table for Power Automate Estimator Import flow
#          Tracks Excel estimator workbooks imported from SharePoint folder structure

# Import reusable functions (located in parent PowerShell folder)
. "$PSScriptRoot\..\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Create Estimators Table                    ║" -ForegroundColor Cyan
Write-Host "║  For: Power Automate Estimator Import Flow               ║" -ForegroundColor Cyan
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
        [string]$PrimaryFieldDisplayName,
        [int]$PrimaryFieldMaxLength = 100
    )
    
    Write-Host "`n📋 Creating table: $DisplayName ($LogicalName)" -ForegroundColor Cyan
    
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
            Write-Host "   ⚠️ Table already exists, skipping..." -ForegroundColor Yellow
            return $true
        }
        Write-Host "   ❌ Failed to create table: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Error: $($errorDetail.error.message)" -ForegroundColor Red
        }
        return $false
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
        [string]$FieldType,
        [string]$Description = "",
        [hashtable]$AdditionalProperties = @{}
    )
    
    Write-Host "   ➕ Adding field: $FieldDisplayName ($FieldType)" -ForegroundColor Gray
    
    $fieldDefinition = @{
        "SchemaName" = $FieldLogicalName
        "Description" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $Description; "LanguageCode" = 1033 }
            )
        }
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $FieldDisplayName; "LanguageCode" = 1033 }
            )
        }
        "RequiredLevel" = @{ "Value" = "None"; "CanBeChanged" = $true }
    }
    
    switch ($FieldType) {
        "String" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $fieldDefinition["MaxLength"] = if ($AdditionalProperties.MaxLength) { $AdditionalProperties.MaxLength } else { 100 }
            $fieldDefinition["FormatName"] = @{ "Value" = "Text" }
        }
        "Url" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $fieldDefinition["MaxLength"] = if ($AdditionalProperties.MaxLength) { $AdditionalProperties.MaxLength } else { 2000 }
            $fieldDefinition["FormatName"] = @{ "Value" = "Url" }
        }
        "Memo" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.MemoAttributeMetadata"
            $fieldDefinition["MaxLength"] = if ($AdditionalProperties.MaxLength) { $AdditionalProperties.MaxLength } else { 4000 }
        }
        "Boolean" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
            $fieldDefinition["DefaultValue"] = if ($AdditionalProperties.ContainsKey("DefaultValue")) { $AdditionalProperties.DefaultValue } else { $false }
            $fieldDefinition["OptionSet"] = @{
                "TrueOption" = @{ "Value" = 1; "Label" = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; "LocalizedLabels" = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "Yes"; "LanguageCode" = 1033 }) } }
                "FalseOption" = @{ "Value" = 0; "Label" = @{ "@odata.type" = "Microsoft.Dynamics.CRM.Label"; "LocalizedLabels" = @(@{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = "No"; "LanguageCode" = 1033 }) } }
            }
        }
        "Integer" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
            $fieldDefinition["Format"] = "None"
            $fieldDefinition["MinValue"] = 0
            $fieldDefinition["MaxValue"] = 999999
        }
        "DateTime" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $fieldDefinition["Format"] = "DateAndTime"
            $fieldDefinition["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
        }
        "DateOnly" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $fieldDefinition["Format"] = "DateOnly"
            $fieldDefinition["DateTimeBehavior"] = @{ "Value" = "UserLocal" }
        }
        "Picklist" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
            $options = @()
            $value = 864340000
            foreach ($option in $AdditionalProperties.Options) {
                $options += @{
                    "Value" = $value
                    "Label" = @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(
                            @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $option; "LanguageCode" = 1033 }
                        )
                    }
                }
                $value++
            }
            $fieldDefinition["OptionSet"] = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.OptionSetMetadata"
                "IsGlobal" = $false
                "OptionSetType" = "Picklist"
                "Options" = $options
            }
        }
    }
    
    $body = $fieldDefinition | ConvertTo-Json -Depth 15
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body $body
        
        Write-Host "      ✅ Field added" -ForegroundColor Green
        return $true
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            Write-Host "      ⚠️ Field exists, skipping" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# FUNCTION: Create Lookup Relationship
# ============================================================================
function Add-DataverseLookup {
    param(
        [string]$FromTable,
        [string]$ToTable,
        [string]$LookupFieldName,
        [string]$LookupDisplayName,
        [string]$RelationshipName
    )
    
    Write-Host "   🔗 Creating lookup: $LookupDisplayName ($FromTable → $ToTable)" -ForegroundColor Gray
    
    $relationshipDefinition = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
        "SchemaName" = $RelationshipName
        "ReferencedEntity" = $ToTable
        "ReferencingEntity" = $FromTable
        "Lookup" = @{
            "SchemaName" = $LookupFieldName
            "DisplayName" = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                "LocalizedLabels" = @(
                    @{ "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"; "Label" = $LookupDisplayName; "LanguageCode" = 1033 }
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
            Write-Host "      ⚠️ Lookup exists, skipping" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# CREATE ESTIMATORS TABLE
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Magenta
Write-Host "PHASE 1: Creating Estimators Table" -ForegroundColor Magenta
Write-Host "="*60 -ForegroundColor Magenta

$tableCreated = New-DataverseTable `
    -LogicalName "cr950_estimator" `
    -DisplayName "Estimator" `
    -PluralName "Estimators" `
    -Description "Tracks Excel estimator workbooks imported from SharePoint folder structure" `
    -PrimaryFieldLogicalName "cr950_name" `
    -PrimaryFieldDisplayName "Name" `
    -PrimaryFieldMaxLength 200

if ($tableCreated) {
    # Add fields
    Write-Host "`n📋 Adding fields to Estimators table..." -ForegroundColor Cyan
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_projectname" -FieldDisplayName "Project Name" `
        -FieldType "String" -Description "Project name from folder path" `
        -AdditionalProperties @{ MaxLength = 200 }
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_estimatedate" -FieldDisplayName "Estimate Date" `
        -FieldType "DateOnly" -Description "Date extracted from filename (YYYYMMDD)"
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_currentrevision" -FieldDisplayName "Current Revision" `
        -FieldType "Integer" -Description "Revision number from filename"
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_estimator_file_url" -FieldDisplayName "Estimator File URL" `
        -FieldType "Url" -Description "SharePoint URL to the estimator file" `
        -AdditionalProperties @{ MaxLength = 2000 }
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_filename" -FieldDisplayName "Filename" `
        -FieldType "String" -Description "Original filename with extension" `
        -AdditionalProperties @{ MaxLength = 500 }
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_status" -FieldDisplayName "Status" `
        -FieldType "Picklist" -Description "Estimator status" `
        -AdditionalProperties @{ Options = @("Draft", "Quoted", "Awarded", "Converted", "Rejected", "On Hold") }
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_convertedtoproject" -FieldDisplayName "Converted to Project" `
        -FieldType "Boolean" -Description "Whether estimator has been converted to a project" `
        -AdditionalProperties @{ DefaultValue = $false }
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_lastmodified" -FieldDisplayName "Last Modified" `
        -FieldType "DateTime" -Description "Last update timestamp"
    
    Add-DataverseField -TableLogicalName "cr950_estimator" `
        -FieldLogicalName "cr950_notes" -FieldDisplayName "Notes" `
        -FieldType "Memo" -Description "Free text notes" `
        -AdditionalProperties @{ MaxLength = 4000 }
    
    # Create lookups
    Write-Host "`n📋 Creating lookup relationships..." -ForegroundColor Cyan
    
    Add-DataverseLookup -FromTable "cr950_estimator" -ToTable "cr950_clients" `
        -LookupFieldName "cr950_client" -LookupDisplayName "Client" `
        -RelationshipName "cr950_client_estimator"
    
    Add-DataverseLookup -FromTable "cr950_estimator" -ToTable "cr950_projectses" `
        -LookupFieldName "cr950_project" -LookupDisplayName "Project" `
        -RelationshipName "cr950_project_estimator"
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "✅ ESTIMATORS TABLE CREATION COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host @"

Table Created:
  ✅ Estimator (cr950_estimator)

Fields Added:
  ✅ Name (Primary) - Display name
  ✅ Project Name - From folder path
  ✅ Estimate Date - From filename
  ✅ Current Revision - From filename
  ✅ Estimator File URL - SharePoint link
  ✅ Filename - Original filename
  ✅ Status - Draft/Quoted/Awarded/Converted/Rejected/On Hold
  ✅ Converted to Project - Boolean flag
  ✅ Last Modified - Timestamp
  ✅ Notes - Free text

Lookups Created:
  ✅ Client → Clients table
  ✅ Project → Projects table (for after conversion)

Status Choice Values:
  864340000 = Draft
  864340001 = Quoted
  864340002 = Awarded
  864340003 = Converted
  864340004 = Rejected
  864340005 = On Hold

Next Steps:
  1. Verify table in Power Apps maker portal
  2. Build Power Automate flow using ESTIMATOR_FLOW_SPECIFICATION.md
  3. Test with sample .xlsm file in SharePoint

"@ -ForegroundColor Cyan
