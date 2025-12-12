# Create NETA Checklist Tables for RESA Power Build
# Created: November 28, 2025
# Purpose: Create NETA Test Template, Apparatus Test Checklist, and Apparatus Submission tables
#          Also adds new fields to existing Apparatus and ApparatusTypeMaster tables

# Import reusable functions (located in parent PowerShell folder)
. "$PSScriptRoot\..\Dataverse-Functions.ps1"

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - NETA Checklist Tables Creator (v1.6.0.0) ║" -ForegroundColor Cyan
Write-Host "║  Creates: NETA Test Template, Apparatus Test Checklist,║" -ForegroundColor Cyan
Write-Host "║           Apparatus Submission + adds fields to exist. ║" -ForegroundColor Cyan
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
        "Memo" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.MemoAttributeMetadata"
            $fieldDefinition["MaxLength"] = if ($AdditionalProperties.MaxLength) { $AdditionalProperties.MaxLength } else { 2000 }
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
            $fieldDefinition["MinValue"] = -2147483648
            $fieldDefinition["MaxValue"] = 2147483647
        }
        "DateTime" {
            $fieldDefinition["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $fieldDefinition["Format"] = "DateAndTime"
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
# CREATE TABLE 1: NETA Test Template
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Magenta
Write-Host "PHASE 1: Creating NETA Test Template Table" -ForegroundColor Magenta
Write-Host "="*60 -ForegroundColor Magenta

$table1Created = New-DataverseTable `
    -LogicalName "cr950_netatesttemplate" `
    -DisplayName "NETA Test Template" `
    -PluralName "NETA Test Templates" `
    -Description "Master templates for NETA test specifications" `
    -PrimaryFieldLogicalName "cr950_test_description" `
    -PrimaryFieldDisplayName "Test Description" `
    -PrimaryFieldMaxLength 500

if ($table1Created) {
    # Add fields
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_neta_section" -FieldDisplayName "NETA Section" `
        -FieldType "String" -Description "NETA section number (e.g., 7.6.3)" `
        -AdditionalProperties @{ MaxLength = 20 }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_equipment_type" -FieldDisplayName "Equipment Type" `
        -FieldType "String" -Description "Equipment type name" `
        -AdditionalProperties @{ MaxLength = 200 }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_test_type" -FieldDisplayName "Test Type" `
        -FieldType "Picklist" -Description "Visual/Mechanical or Electrical" `
        -AdditionalProperties @{ Options = @("Visual/Mechanical", "Electrical") }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_test_number" -FieldDisplayName "Test Number" `
        -FieldType "String" -Description "Test number (e.g., A.1, B.3)" `
        -AdditionalProperties @{ MaxLength = 10 }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_neta_standard" -FieldDisplayName "NETA Standard" `
        -FieldType "Picklist" -Description "ATS or MTS" `
        -AdditionalProperties @{ Options = @("ATS (Acceptance)", "MTS (Maintenance)") }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_is_optional" -FieldDisplayName "Is Optional" `
        -FieldType "Boolean" -Description "Whether test is optional per NETA" `
        -AdditionalProperties @{ DefaultValue = $false }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_requires_value" -FieldDisplayName "Requires Value" `
        -FieldType "Boolean" -Description "Whether test requires a recorded value" `
        -AdditionalProperties @{ DefaultValue = $false }
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_sort_order" -FieldDisplayName "Sort Order" `
        -FieldType "Integer" -Description "Display sequence"
    
    Add-DataverseField -TableLogicalName "cr950_netatesttemplate" `
        -FieldLogicalName "cr950_active" -FieldDisplayName "Active" `
        -FieldType "Boolean" -Description "Whether template is active" `
        -AdditionalProperties @{ DefaultValue = $true }
}

# ============================================================================
# CREATE TABLE 2: Apparatus Test Checklist
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Magenta
Write-Host "PHASE 2: Creating Apparatus Test Checklist Table" -ForegroundColor Magenta
Write-Host "="*60 -ForegroundColor Magenta

$table2Created = New-DataverseTable `
    -LogicalName "cr950_apparatustestchecklist" `
    -DisplayName "Apparatus Test Checklist" `
    -PluralName "Apparatus Test Checklists" `
    -Description "Individual test checklist items for each apparatus" `
    -PrimaryFieldLogicalName "cr950_name" `
    -PrimaryFieldDisplayName "Name" `
    -PrimaryFieldMaxLength 200

if ($table2Created) {
    Add-DataverseField -TableLogicalName "cr950_apparatustestchecklist" `
        -FieldLogicalName "cr950_status" -FieldDisplayName "Status" `
        -FieldType "Picklist" -Description "Checklist item status" `
        -AdditionalProperties @{ Options = @("Not Started", "Complete", "N/A", "Failed") }
    
    Add-DataverseField -TableLogicalName "cr950_apparatustestchecklist" `
        -FieldLogicalName "cr950_is_complete" -FieldDisplayName "Is Complete" `
        -FieldType "Boolean" -Description "Whether test is complete" `
        -AdditionalProperties @{ DefaultValue = $false }
    
    Add-DataverseField -TableLogicalName "cr950_apparatustestchecklist" `
        -FieldLogicalName "cr950_recorded_value" -FieldDisplayName "Recorded Value" `
        -FieldType "String" -Description "Measured value if applicable" `
        -AdditionalProperties @{ MaxLength = 100 }
    
    Add-DataverseField -TableLogicalName "cr950_apparatustestchecklist" `
        -FieldLogicalName "cr950_notes" -FieldDisplayName "Notes" `
        -FieldType "Memo" -Description "Technician notes" `
        -AdditionalProperties @{ MaxLength = 2000 }
    
    Add-DataverseField -TableLogicalName "cr950_apparatustestchecklist" `
        -FieldLogicalName "cr950_completed_date" -FieldDisplayName "Completed Date" `
        -FieldType "DateTime" -Description "When test was marked complete"
    
    # Create lookups
    Add-DataverseLookup -FromTable "cr950_apparatustestchecklist" -ToTable "cr950_apparatus" `
        -LookupFieldName "cr950_apparatus" -LookupDisplayName "Apparatus" `
        -RelationshipName "cr950_apparatus_testchecklist"
    
    Add-DataverseLookup -FromTable "cr950_apparatustestchecklist" -ToTable "cr950_netatesttemplate" `
        -LookupFieldName "cr950_test_template" -LookupDisplayName "Test Template" `
        -RelationshipName "cr950_testtemplate_checklist"
}

# ============================================================================
# CREATE TABLE 3: Apparatus Submission
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Magenta
Write-Host "PHASE 3: Creating Apparatus Submission Table" -ForegroundColor Magenta
Write-Host "="*60 -ForegroundColor Magenta

$table3Created = New-DataverseTable `
    -LogicalName "cr950_apparatussubmission" `
    -DisplayName "Apparatus Submission" `
    -PluralName "Apparatus Submissions" `
    -Description "Submission and approval workflow for apparatus completion" `
    -PrimaryFieldLogicalName "cr950_name" `
    -PrimaryFieldDisplayName "Name" `
    -PrimaryFieldMaxLength 200

if ($table3Created) {
    Add-DataverseField -TableLogicalName "cr950_apparatussubmission" `
        -FieldLogicalName "cr950_submitted_date" -FieldDisplayName "Submitted Date" `
        -FieldType "DateTime" -Description "When submitted for review"
    
    Add-DataverseField -TableLogicalName "cr950_apparatussubmission" `
        -FieldLogicalName "cr950_review_status" -FieldDisplayName "Review Status" `
        -FieldType "Picklist" -Description "Approval status" `
        -AdditionalProperties @{ Options = @("Pending", "Approved", "Rejected", "Returned for Revision") }
    
    Add-DataverseField -TableLogicalName "cr950_apparatussubmission" `
        -FieldLogicalName "cr950_reviewed_date" -FieldDisplayName "Reviewed Date" `
        -FieldType "DateTime" -Description "When reviewed"
    
    Add-DataverseField -TableLogicalName "cr950_apparatussubmission" `
        -FieldLogicalName "cr950_rejection_reason" -FieldDisplayName "Rejection Reason" `
        -FieldType "Memo" -Description "Reason if rejected" `
        -AdditionalProperties @{ MaxLength = 2000 }
    
    Add-DataverseField -TableLogicalName "cr950_apparatussubmission" `
        -FieldLogicalName "cr950_tests_complete" -FieldDisplayName "Tests Complete" `
        -FieldType "Integer" -Description "Number of tests complete at submission"
    
    Add-DataverseField -TableLogicalName "cr950_apparatussubmission" `
        -FieldLogicalName "cr950_tests_total" -FieldDisplayName "Tests Total" `
        -FieldType "Integer" -Description "Total number of tests"
    
    # Create lookup to Apparatus
    Add-DataverseLookup -FromTable "cr950_apparatussubmission" -ToTable "cr950_apparatus" `
        -LookupFieldName "cr950_apparatus" -LookupDisplayName "Apparatus" `
        -RelationshipName "cr950_apparatus_submission"
}

# ============================================================================
# ADD FIELDS TO EXISTING TABLES
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Magenta
Write-Host "PHASE 4: Adding Fields to Existing Tables" -ForegroundColor Magenta
Write-Host "="*60 -ForegroundColor Magenta

# Add to Apparatus table
Write-Host "`n📋 Adding fields to Apparatus table..." -ForegroundColor Cyan

Add-DataverseField -TableLogicalName "cr950_apparatus" `
    -FieldLogicalName "cr950_checklist_status" -FieldDisplayName "Checklist Status" `
    -FieldType "Picklist" -Description "Overall checklist completion status" `
    -AdditionalProperties @{ Options = @("Not Started", "In Progress", "Submitted", "Approved", "Rejected") }

Add-DataverseField -TableLogicalName "cr950_apparatus" `
    -FieldLogicalName "cr950_submitted_date" -FieldDisplayName "Submitted Date" `
    -FieldType "DateTime" -Description "When submitted for review"

Add-DataverseField -TableLogicalName "cr950_apparatus" `
    -FieldLogicalName "cr950_approval_date" -FieldDisplayName "Approval Date" `
    -FieldType "DateTime" -Description "When approved by job lead"

# Add to ApparatusTypeMaster table
Write-Host "`n📋 Adding fields to Apparatus Type Master table..." -ForegroundColor Cyan

Add-DataverseField -TableLogicalName "cr950_apparatustypemaster" `
    -FieldLogicalName "cr950_neta_ats_section" -FieldDisplayName "NETA ATS Section" `
    -FieldType "String" -Description "NETA ATS section reference" `
    -AdditionalProperties @{ MaxLength = 20 }

Add-DataverseField -TableLogicalName "cr950_apparatustypemaster" `
    -FieldLogicalName "cr950_neta_mts_section" -FieldDisplayName "NETA MTS Section" `
    -FieldType "String" -Description "NETA MTS section reference" `
    -AdditionalProperties @{ MaxLength = 20 }

Add-DataverseField -TableLogicalName "cr950_apparatustypemaster" `
    -FieldLogicalName "cr950_voltage_class" -FieldDisplayName "Voltage Class" `
    -FieldType "Picklist" -Description "Voltage classification" `
    -AdditionalProperties @{ Options = @("Low Voltage (< 1kV)", "Medium Voltage (1-38kV)", "High Voltage (> 38kV)") }

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "✅ NETA CHECKLIST TABLES CREATION COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host @"

Tables Created:
  ✅ NETA Test Template (cr950_netatesttemplate)
  ✅ Apparatus Test Checklist (cr950_apparatustestchecklist)
  ✅ Apparatus Submission (cr950_apparatussubmission)

Fields Added to Existing Tables:
  ✅ Apparatus: Checklist Status, Submitted Date, Approval Date
  ✅ Apparatus Type Master: NETA ATS Section, NETA MTS Section, Voltage Class

Next Steps:
  1. Run Import-NETATemplates.ps1 to load NETA test templates
  2. Verify tables in Power Apps maker portal
  3. Create Power Automate flows for checklist automation

"@ -ForegroundColor Cyan
