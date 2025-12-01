# Add JSON Import Fields to Dataverse
# Created: November 30, 2025
# Purpose: Add missing fields needed for JSON Import flow from VBA Estimator exports
#
# Fields being added:
#   Apparatus table: quantity, hours_per_unit, section  
#   (row_number maps to existing apparatus_number)
#
# USAGE:
#   . "C:\RESA_Power_Build\Scripts\PowerShell\Active\Add-JSONImportFields.ps1"
#   Add-JSONImportFields

# Load the field operations template
. "C:\RESA_Power_Build\Scripts\PowerShell\Templates\Dataverse-FieldOperations.ps1"

function Add-JSONImportFields {
    <#
    .SYNOPSIS
        Adds missing fields to Dataverse tables for JSON Import flow
    .DESCRIPTION
        Adds:
        - cr950_quantity (Integer) - Number of identical apparatus items
        - cr950_hours_per_unit (Decimal) - Hours per individual unit
        - cr950_section (String) - SLD section reference from estimator
    #>
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "JSON IMPORT FIELD ADDITION" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Connect to Dataverse
    if (-not (Connect-DataverseAPI)) {
        Write-Host "❌ Failed to connect to Dataverse" -ForegroundColor Red
        return $false
    }
    
    Write-Host "`n📋 Adding fields to cr950_apparatus table..." -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    # Field 1: Quantity
    Add-DataverseField `
        -TableName "cr950_apparatus" `
        -FieldName "quantity" `
        -DisplayName "Quantity" `
        -FieldType "Integer" `
        -Required $false
    
    # Field 2: Hours Per Unit  
    Add-DataverseField `
        -TableName "cr950_apparatus" `
        -FieldName "hours_per_unit" `
        -DisplayName "Hours Per Unit" `
        -FieldType "Decimal" `
        -Precision 2 `
        -Required $false
    
    # Field 3: Section (SLD Reference)
    Add-DataverseField `
        -TableName "cr950_apparatus" `
        -FieldName "section" `
        -DisplayName "Section" `
        -FieldType "String" `
        -MaxLength 200 `
        -Required $false
    
    Write-Host "`n✅ Field addition complete!" -ForegroundColor Green
    Write-Host "`nReminder: After adding fields, you may need to:" -ForegroundColor Yellow
    Write-Host "   1. Add fields to forms in the model-driven app" -ForegroundColor Gray
    Write-Host "   2. Publish customizations in Power Apps" -ForegroundColor Gray
    Write-Host "   3. Export a new solution version" -ForegroundColor Gray
    
    return $true
}

function Show-ApparatusFields {
    <#
    .SYNOPSIS
        Shows current apparatus table fields
    #>
    
    if (-not (Connect-DataverseAPI)) { return }
    
    $fields = Get-DataverseFields -TableName "cr950_apparatus" -CustomOnly
    
    Write-Host "`n📋 APPARATUS TABLE FIELDS (cr950_apparatus)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    $fields | Format-Table LogicalName, DisplayName, Type -AutoSize
}

function Show-ScopeFields {
    <#
    .SYNOPSIS
        Shows current scope table fields  
    #>
    
    if (-not (Connect-DataverseAPI)) { return }
    
    $fields = Get-DataverseFields -TableName "cr950_projectscope" -CustomOnly
    
    Write-Host "`n📋 SCOPE TABLE FIELDS (cr950_projectscope)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    $fields | Format-Table LogicalName, DisplayName, Type -AutoSize
}

# ============================================================================
# INITIALIZATION
# ============================================================================

Write-Host "`n📦 JSON Import Field Script Loaded" -ForegroundColor Cyan
Write-Host "   Commands available:" -ForegroundColor Gray
Write-Host "   • Add-JSONImportFields  - Add missing apparatus fields" -ForegroundColor White
Write-Host "   • Show-ApparatusFields  - List current apparatus fields" -ForegroundColor White
Write-Host "   • Show-ScopeFields      - List current scope fields`n" -ForegroundColor White
