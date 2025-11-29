# Add Document URL Fields to Quote and Project Tables
# Created: November 28, 2025
# Purpose: Enable document linking (Estimators, Quotes, Contracts) for future SharePoint integration

# Import reusable functions
. "$PSScriptRoot\..\Dataverse-Functions.ps1"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RESA Power - Document URL Fields (v1.6.0.0)              ║" -ForegroundColor Cyan
Write-Host "║  Adds URL fields to Quote and Project tables for         ║" -ForegroundColor Cyan
Write-Host "║  future SharePoint/document management integration       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Connect to Dataverse
Connect-Dataverse

if (-not $script:DataverseToken) {
    Write-Host "❌ Failed to connect. Please check environment variables." -ForegroundColor Red
    exit 1
}

$baseUrl = "$($env:DATAVERSE_URL)/api/data/v9.2"

# Function to add a URL field
function Add-UrlField {
    param(
        [string]$TableLogicalName,
        [string]$FieldSchemaName,
        [string]$DisplayName,
        [string]$Description,
        [int]$MaxLength = 2000
    )
    
    Write-Host "   ➕ Adding field: $DisplayName ($FieldSchemaName)" -ForegroundColor White
    
    $fieldDef = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        SchemaName = $FieldSchemaName
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
                    Label = $Description
                    LanguageCode = 1033
                }
            )
        }
        RequiredLevel = @{
            Value = "None"
        }
        MaxLength = $MaxLength
        FormatName = @{
            Value = "Url"
        }
    }
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body ($fieldDef | ConvertTo-Json -Depth 10) `
            -ContentType "application/json; charset=utf-8"
        
        Write-Host "      ✅ Field added" -ForegroundColor Green
        return $true
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -like "*already exists*" -or $errorMsg -like "*duplicate*") {
            Write-Host "      ⚠️  Field already exists (skipping)" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Error: $errorMsg" -ForegroundColor Red
        return $false
    }
}

# Function to add a text field (for version, notes, etc.)
function Add-TextField {
    param(
        [string]$TableLogicalName,
        [string]$FieldSchemaName,
        [string]$DisplayName,
        [string]$Description,
        [int]$MaxLength = 100
    )
    
    Write-Host "   ➕ Adding field: $DisplayName ($FieldSchemaName)" -ForegroundColor White
    
    $fieldDef = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        SchemaName = $FieldSchemaName
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
                    Label = $Description
                    LanguageCode = 1033
                }
            )
        }
        RequiredLevel = @{
            Value = "None"
        }
        MaxLength = $MaxLength
        FormatName = @{
            Value = "Text"
        }
    }
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body ($fieldDef | ConvertTo-Json -Depth 10) `
            -ContentType "application/json; charset=utf-8"
        
        Write-Host "      ✅ Field added" -ForegroundColor Green
        return $true
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -like "*already exists*" -or $errorMsg -like "*duplicate*") {
            Write-Host "      ⚠️  Field already exists (skipping)" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Error: $errorMsg" -ForegroundColor Red
        return $false
    }
}

# Function to add an integer field
function Add-IntegerField {
    param(
        [string]$TableLogicalName,
        [string]$FieldSchemaName,
        [string]$DisplayName,
        [string]$Description
    )
    
    Write-Host "   ➕ Adding field: $DisplayName ($FieldSchemaName)" -ForegroundColor White
    
    $fieldDef = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
        SchemaName = $FieldSchemaName
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
                    Label = $Description
                    LanguageCode = 1033
                }
            )
        }
        RequiredLevel = @{
            Value = "None"
        }
        MinValue = 0
        MaxValue = 999
    }
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$baseUrl/EntityDefinitions(LogicalName='$TableLogicalName')/Attributes" `
            -Method Post `
            -Headers $script:DataverseHeaders `
            -Body ($fieldDef | ConvertTo-Json -Depth 10) `
            -ContentType "application/json; charset=utf-8"
        
        Write-Host "      ✅ Field added" -ForegroundColor Green
        return $true
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -like "*already exists*" -or $errorMsg -like "*duplicate*") {
            Write-Host "      ⚠️  Field already exists (skipping)" -ForegroundColor Yellow
            return $true
        }
        Write-Host "      ❌ Error: $errorMsg" -ForegroundColor Red
        return $false
    }
}

# ============================================================
# PHASE 1: Add Document Fields to QUOTE Table
# ============================================================
Write-Host "`n" + ("=" * 60) -ForegroundColor Magenta
Write-Host "PHASE 1: Adding Document Fields to QUOTE Table (cr950_quote)" -ForegroundColor Magenta
Write-Host ("=" * 60) + "`n" -ForegroundColor Magenta

# Estimator fields
Add-UrlField -TableLogicalName "cr950_quote" `
    -FieldSchemaName "cr950_estimator_url" `
    -DisplayName "Estimator URL" `
    -Description "Link to estimator workbook in SharePoint"

Add-IntegerField -TableLogicalName "cr950_quote" `
    -FieldSchemaName "cr950_estimator_version" `
    -DisplayName "Estimator Version" `
    -Description "Current version number of the estimator"

Add-TextField -TableLogicalName "cr950_quote" `
    -FieldSchemaName "cr950_estimator_filename" `
    -DisplayName "Estimator Filename" `
    -Description "Original filename of the estimator workbook" `
    -MaxLength 255

# Quote PDF fields
Add-UrlField -TableLogicalName "cr950_quote" `
    -FieldSchemaName "cr950_quote_pdf_url" `
    -DisplayName "Quote PDF URL" `
    -Description "Link to quote PDF in SharePoint or CRM"

Add-TextField -TableLogicalName "cr950_quote" `
    -FieldSchemaName "cr950_quote_source" `
    -DisplayName "Quote Source" `
    -Description "Source system: CRM, Manual, Import" `
    -MaxLength 50

# Signed quote/contract at quote level
Add-UrlField -TableLogicalName "cr950_quote" `
    -FieldSchemaName "cr950_signed_quote_url" `
    -DisplayName "Signed Quote URL" `
    -Description "Link to signed/accepted quote PDF"

# ============================================================
# PHASE 2: Add Document Fields to PROJECT Table
# ============================================================
Write-Host "`n" + ("=" * 60) -ForegroundColor Magenta
Write-Host "PHASE 2: Adding Document Fields to PROJECT Table (cr950_projectses)" -ForegroundColor Magenta
Write-Host ("=" * 60) + "`n" -ForegroundColor Magenta

# Contract document
Add-UrlField -TableLogicalName "cr950_projectses" `
    -FieldSchemaName "cr950_contract_url" `
    -DisplayName "Contract URL" `
    -Description "Link to signed contract in SharePoint"

Add-TextField -TableLogicalName "cr950_projectses" `
    -FieldSchemaName "cr950_contract_number" `
    -DisplayName "Contract Number" `
    -Description "Client contract or PO number" `
    -MaxLength 50

# Project folder link
Add-UrlField -TableLogicalName "cr950_projectses" `
    -FieldSchemaName "cr950_sharepoint_folder_url" `
    -DisplayName "SharePoint Folder URL" `
    -Description "Link to project folder in SharePoint"

# ============================================================
# PHASE 3: Create Project Documents Table
# ============================================================
Write-Host "`n" + ("=" * 60) -ForegroundColor Magenta
Write-Host "PHASE 3: Creating Project Documents Table" -ForegroundColor Magenta
Write-Host ("=" * 60) + "`n" -ForegroundColor Magenta

Write-Host "📋 Creating table: Project Documents (cr950_projectdocument)" -ForegroundColor Cyan

$tableDefinition = @{
    "@odata.type" = "Microsoft.Dynamics.CRM.EntityMetadata"
    SchemaName = "cr950_projectdocument"
    DisplayName = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        LocalizedLabels = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label = "Project Document"
                LanguageCode = 1033
            }
        )
    }
    DisplayCollectionName = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        LocalizedLabels = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label = "Project Documents"
                LanguageCode = 1033
            }
        )
    }
    Description = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        LocalizedLabels = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label = "Central repository for all project-related documents including estimators, quotes, contracts, and reports"
                LanguageCode = 1033
            }
        )
    }
    OwnershipType = "UserOwned"
    IsActivity = $false
    HasNotes = $true
    HasActivities = $false
    PrimaryNameAttribute = "cr950_name"
    Attributes = @(
        @{
            "@odata.type" = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            SchemaName = "cr950_name"
            DisplayName = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                LocalizedLabels = @(
                    @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                        Label = "Document Name"
                        LanguageCode = 1033
                    }
                )
            }
            RequiredLevel = @{ Value = "ApplicationRequired" }
            MaxLength = 200
            IsPrimaryName = $true
        }
    )
}

try {
    $response = Invoke-RestMethod `
        -Uri "$baseUrl/EntityDefinitions" `
        -Method Post `
        -Headers $script:DataverseHeaders `
        -Body ($tableDefinition | ConvertTo-Json -Depth 15) `
        -ContentType "application/json; charset=utf-8"
    
    Write-Host "   ✅ Table created successfully!" -ForegroundColor Green
    Start-Sleep -Seconds 3  # Wait for table to be available
}
catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -like "*already exists*" -or $errorMsg -like "*duplicate*") {
        Write-Host "   ⚠️  Table already exists (continuing with fields)" -ForegroundColor Yellow
    }
    else {
        Write-Host "   ❌ Error creating table: $errorMsg" -ForegroundColor Red
    }
}

# Add fields to Project Documents table
Write-Host "`n   Adding fields to Project Documents table..." -ForegroundColor Cyan

Add-UrlField -TableLogicalName "cr950_projectdocument" `
    -FieldSchemaName "cr950_document_url" `
    -DisplayName "Document URL" `
    -Description "Link to document in SharePoint or other storage"

Add-TextField -TableLogicalName "cr950_projectdocument" `
    -FieldSchemaName "cr950_document_type" `
    -DisplayName "Document Type" `
    -Description "Type: Estimator, Quote, Contract, Change Order, Test Report, Other" `
    -MaxLength 50

Add-IntegerField -TableLogicalName "cr950_projectdocument" `
    -FieldSchemaName "cr950_version" `
    -DisplayName "Version" `
    -Description "Document version number"

Add-TextField -TableLogicalName "cr950_projectdocument" `
    -FieldSchemaName "cr950_original_filename" `
    -DisplayName "Original Filename" `
    -Description "Original filename when uploaded" `
    -MaxLength 255

Add-TextField -TableLogicalName "cr950_projectdocument" `
    -FieldSchemaName "cr950_description" `
    -DisplayName "Description" `
    -Description "Notes or description of the document" `
    -MaxLength 500

# Create lookup to Project
Write-Host "   🔗 Creating lookup: Project (cr950_projectdocument → cr950_projectses)" -ForegroundColor White

$lookupDef = @{
    "@odata.type" = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
    SchemaName = "cr950_project"
    DisplayName = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        LocalizedLabels = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label = "Project"
                LanguageCode = 1033
            }
        )
    }
    RequiredLevel = @{ Value = "None" }
    Targets = @("cr950_projectses")
}

try {
    $response = Invoke-RestMethod `
        -Uri "$baseUrl/EntityDefinitions(LogicalName='cr950_projectdocument')/Attributes" `
        -Method Post `
        -Headers $script:DataverseHeaders `
        -Body ($lookupDef | ConvertTo-Json -Depth 10) `
        -ContentType "application/json; charset=utf-8"
    
    Write-Host "      ✅ Lookup created" -ForegroundColor Green
}
catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -like "*already exists*") {
        Write-Host "      ⚠️  Lookup already exists" -ForegroundColor Yellow
    }
    else {
        Write-Host "      ❌ Error: $errorMsg" -ForegroundColor Red
    }
}

# Create lookup to Quote
Write-Host "   🔗 Creating lookup: Quote (cr950_projectdocument → cr950_quote)" -ForegroundColor White

$quoteLookupDef = @{
    "@odata.type" = "Microsoft.Dynamics.CRM.LookupAttributeMetadata"
    SchemaName = "cr950_quote"
    DisplayName = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
        LocalizedLabels = @(
            @{
                "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                Label = "Quote"
                LanguageCode = 1033
            }
        )
    }
    RequiredLevel = @{ Value = "None" }
    Targets = @("cr950_quote")
}

try {
    $response = Invoke-RestMethod `
        -Uri "$baseUrl/EntityDefinitions(LogicalName='cr950_projectdocument')/Attributes" `
        -Method Post `
        -Headers $script:DataverseHeaders `
        -Body ($quoteLookupDef | ConvertTo-Json -Depth 10) `
        -ContentType "application/json; charset=utf-8"
    
    Write-Host "      ✅ Lookup created" -ForegroundColor Green
}
catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -like "*already exists*") {
        Write-Host "      ⚠️  Lookup already exists" -ForegroundColor Yellow
    }
    else {
        Write-Host "      ❌ Error: $errorMsg" -ForegroundColor Red
    }
}

# ============================================================
# SUMMARY
# ============================================================
Write-Host "`n" + ("=" * 60) -ForegroundColor Green
Write-Host "✅ DOCUMENT URL FIELDS CREATION COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

Write-Host "`nQuote Table (cr950_quote) - New Fields:" -ForegroundColor Cyan
Write-Host "  • Estimator URL" -ForegroundColor White
Write-Host "  • Estimator Version" -ForegroundColor White
Write-Host "  • Estimator Filename" -ForegroundColor White
Write-Host "  • Quote PDF URL" -ForegroundColor White
Write-Host "  • Quote Source" -ForegroundColor White
Write-Host "  • Signed Quote URL" -ForegroundColor White

Write-Host "`nProject Table (cr950_projectses) - New Fields:" -ForegroundColor Cyan
Write-Host "  • Contract URL" -ForegroundColor White
Write-Host "  • Contract Number" -ForegroundColor White
Write-Host "  • SharePoint Folder URL" -ForegroundColor White

Write-Host "`nNew Table Created: Project Documents (cr950_projectdocument)" -ForegroundColor Cyan
Write-Host "  • Document Name (primary)" -ForegroundColor White
Write-Host "  • Document URL" -ForegroundColor White
Write-Host "  • Document Type" -ForegroundColor White
Write-Host "  • Version" -ForegroundColor White
Write-Host "  • Original Filename" -ForegroundColor White
Write-Host "  • Description" -ForegroundColor White
Write-Host "  • Project (lookup)" -ForegroundColor White
Write-Host "  • Quote (lookup)" -ForegroundColor White

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Add new table to solution in Power Apps" -ForegroundColor White
Write-Host "  2. Create SharePoint document libraries (when ready)" -ForegroundColor White
Write-Host "  3. Update forms to show new URL fields" -ForegroundColor White
Write-Host "  4. Create Power Automate flow to auto-populate URLs" -ForegroundColor White
