<#
.SYNOPSIS
    Creates new Dataverse tables from Excel template definitions using Web API
.DESCRIPTION
    Reads Excel templates and creates corresponding tables in Dataverse with all fields defined.
    Uses the Dataverse Web API to create entity metadata programmatically.
.EXAMPLE
    .\Import-DataverseTables.ps1
#>

# Import required modules
Import-Module ImportExcel
. "$PSScriptRoot\Dataverse-Functions.ps1"

# Connect to Dataverse
Write-Host "🔐 Connecting to Dataverse..." -ForegroundColor Cyan
$token = Connect-Dataverse

# Helper function to create entity metadata
function New-DataverseTable {
    param(
        [string]$Token,
        [string]$DisplayName,
        [string]$LogicalName,
        [string]$PluralName,
        [string]$Description,
        [array]$Attributes
    )
    
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "application/json; charset=utf-8"
        "Accept" = "application/json"
        "OData-MaxVersion" = "4.0"
        "OData-Version" = "4.0"
    }
    
    $dataverseUrl = $env:DATAVERSE_URL
    
    # Create entity definition
    # First attribute is the primary name field
    $primaryAttribute = $Attributes[0]
    $primaryAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
    $primaryAttribute["IsPrimaryName"] = $true
    if (-not $primaryAttribute.ContainsKey("MaxLength")) {
        $primaryAttribute["MaxLength"] = 100
    }
    
    $entityDefinition = @{
        "@odata.type" = "Microsoft.Dynamics.CRM.EntityMetadata"
        "Attributes" = @($Attributes)
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $DisplayName
                    "LanguageCode" = 1033
                }
            )
        }
        "DisplayCollectionName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $PluralName
                    "LanguageCode" = 1033
                }
            )
        }
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
        "SchemaName" = $LogicalName
        "HasActivities" = $false
        "HasNotes" = $true
        "IsActivity" = $false
        "OwnershipType" = "UserOwned"
    }
    
    try {
        $response = Invoke-RestMethod -Uri "$dataverseUrl/api/data/v9.2/EntityDefinitions" `
            -Method Post `
            -Headers $headers `
            -Body ($entityDefinition | ConvertTo-Json -Depth 10)
        
        Write-Host "   ✅ Created table: $DisplayName" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "   ❌ Error creating $DisplayName : $_" -ForegroundColor Red
        Write-Host "   Response: $($_.Exception.Response)" -ForegroundColor Yellow
        return $false
    }
}

# Helper function to map Excel column types to Dataverse attribute types
function Get-AttributeDefinition {
    param(
        [string]$ColumnName,
        [string]$DisplayName,
        [string]$DataType = "String"
    )
    
    $schemaName = $ColumnName
    
    $baseAttribute = @{
        "SchemaName" = $schemaName
        "DisplayName" = @{
            "@odata.type" = "Microsoft.Dynamics.CRM.Label"
            "LocalizedLabels" = @(
                @{
                    "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                    "Label" = $DisplayName
                    "LanguageCode" = 1033
                }
            )
        }
        "RequiredLevel" = @{
            "Value" = "None"
            "CanBeChanged" = $true
        }
    }
    
    switch ($DataType) {
        "Money" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.MoneyAttributeMetadata"
            $baseAttribute["PrecisionSource"] = 2
            $baseAttribute["MinValue"] = 0.0
            $baseAttribute["MaxValue"] = 1000000000.0
        }
        "Integer" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
            $baseAttribute["Format"] = "None"
            $baseAttribute["MinValue"] = -2147483648
            $baseAttribute["MaxValue"] = 2147483647
        }
        "Decimal" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
            $baseAttribute["MinValue"] = 0.0
            $baseAttribute["MaxValue"] = 100000000000.0
            $baseAttribute["Precision"] = 2
        }
        "Boolean" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
            $baseAttribute["OptionSet"] = @{
                "@odata.type" = "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata"
                "TrueOption" = @{
                    "Value" = 1
                    "Label" = @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(@{
                            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                            "Label" = "Yes"
                            "LanguageCode" = 1033
                        })
                    }
                }
                "FalseOption" = @{
                    "Value" = 0
                    "Label" = @{
                        "@odata.type" = "Microsoft.Dynamics.CRM.Label"
                        "LocalizedLabels" = @(@{
                            "@odata.type" = "Microsoft.Dynamics.CRM.LocalizedLabel"
                            "Label" = "No"
                            "LanguageCode" = 1033
                        })
                    }
                }
            }
        }
        "DateTime" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
            $baseAttribute["Format"] = "DateOnly"
        }
        "Email" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $baseAttribute["FormatName"] = @{ "Value" = "Email" }
            $baseAttribute["MaxLength"] = 100
        }
        "Phone" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $baseAttribute["FormatName"] = @{ "Value" = "Phone" }
            $baseAttribute["MaxLength"] = 50
        }
        "Url" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $baseAttribute["FormatName"] = @{ "Value" = "Url" }
            $baseAttribute["MaxLength"] = 200
        }
        "Memo" {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.MemoAttributeMetadata"
            $baseAttribute["Format"] = "TextArea"
            $baseAttribute["MaxLength"] = 2000
        }
        default {
            $baseAttribute["@odata.type"] = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
            $baseAttribute["FormatName"] = @{ "Value" = "Text" }
            $baseAttribute["MaxLength"] = 100
        }
    }
    
    return $baseAttribute
}

Write-Host ""
Write-Host "🏗️  RESA Power - Table Import Utility" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Table 1: Clients
Write-Host "📋 Creating Clients table..." -ForegroundColor Yellow
$clientAttributes = @(
    (Get-AttributeDefinition "cr950_name" "Client Name" "String"),
    (Get-AttributeDefinition "cr950_clientnumber" "Client Number" "String"),
    (Get-AttributeDefinition "cr950_clienttype" "Client Type" "String"),
    (Get-AttributeDefinition "cr950_industry" "Industry" "String"),
    (Get-AttributeDefinition "cr950_accountstatus" "Account Status" "String"),
    (Get-AttributeDefinition "cr950_primarycontactname" "Primary Contact Name" "String"),
    (Get-AttributeDefinition "cr950_primarycontacttitle" "Primary Contact Title" "String"),
    (Get-AttributeDefinition "cr950_primarycontactemail" "Primary Contact Email" "Email"),
    (Get-AttributeDefinition "cr950_primarycontactphone" "Primary Contact Phone" "Phone"),
    (Get-AttributeDefinition "cr950_billingcontactname" "Billing Contact Name" "String"),
    (Get-AttributeDefinition "cr950_billingcontactemail" "Billing Contact Email" "Email"),
    (Get-AttributeDefinition "cr950_billingcontactphone" "Billing Contact Phone" "Phone"),
    (Get-AttributeDefinition "cr950_mailingaddress" "Mailing Address" "String"),
    (Get-AttributeDefinition "cr950_mailingcity" "Mailing City" "String"),
    (Get-AttributeDefinition "cr950_mailingstate" "Mailing State" "String"),
    (Get-AttributeDefinition "cr950_mailingzip" "Mailing ZIP" "String"),
    (Get-AttributeDefinition "cr950_billingaddress" "Billing Address" "String"),
    (Get-AttributeDefinition "cr950_taxid" "Tax ID" "String"),
    (Get-AttributeDefinition "cr950_paymentterms" "Payment Terms" "String"),
    (Get-AttributeDefinition "cr950_creditlimit" "Credit Limit" "Money"),
    (Get-AttributeDefinition "cr950_insurancecertificate" "Insurance Certificate" "String"),
    (Get-AttributeDefinition "cr950_insuranceexpiration" "Insurance Expiration" "DateTime"),
    (Get-AttributeDefinition "cr950_notes" "Notes" "Memo")
)

New-DataverseTable -Token $token -DisplayName "Client" -LogicalName "cr950_Client" `
    -PluralName "Clients" -Description "Customer and client management" -Attributes $clientAttributes

# Table 2: Sites
Write-Host "📋 Creating Sites table..." -ForegroundColor Yellow
$siteAttributes = @(
    (Get-AttributeDefinition "cr950_name" "Site Name" "String"),
    (Get-AttributeDefinition "cr950_sitenumber" "Site Number" "String"),
    (Get-AttributeDefinition "cr950_sitetype" "Site Type" "String"),
    (Get-AttributeDefinition "cr950_status" "Status" "String"),
    (Get-AttributeDefinition "cr950_address" "Address" "String"),
    (Get-AttributeDefinition "cr950_city" "City" "String"),
    (Get-AttributeDefinition "cr950_state" "State" "String"),
    (Get-AttributeDefinition "cr950_zip" "ZIP Code" "String"),
    (Get-AttributeDefinition "cr950_county" "County" "String"),
    (Get-AttributeDefinition "cr950_latitude" "Latitude" "Decimal"),
    (Get-AttributeDefinition "cr950_longitude" "Longitude" "Decimal"),
    (Get-AttributeDefinition "cr950_sitecaccess" "Site Contact" "String"),
    (Get-AttributeDefinition "cr950_sitecontactphone" "Site Contact Phone" "Phone"),
    (Get-AttributeDefinition "cr950_sitecontactemail" "Site Contact Email" "Email"),
    (Get-AttributeDefinition "cr950_accessrequirements" "Access Requirements" "Memo"),
    (Get-AttributeDefinition "cr950_safetyprotocols" "Safety Protocols" "Memo"),
    (Get-AttributeDefinition "cr950_parkinginstructions" "Parking Instructions" "String"),
    (Get-AttributeDefinition "cr950_specialequipment" "Special Equipment" "String"),
    (Get-AttributeDefinition "cr950_utilitycompany" "Utility Company" "String"),
    (Get-AttributeDefinition "cr950_utilityaccountnumber" "Utility Account Number" "String"),
    (Get-AttributeDefinition "cr950_notes" "Notes" "Memo")
)

New-DataverseTable -Token $token -DisplayName "Site" -LogicalName "cr950_Site" `
    -PluralName "Sites" -Description "Project site locations and details" -Attributes $siteAttributes

# Table 3: Employees
Write-Host "📋 Creating Employees table..." -ForegroundColor Yellow
$employeeAttributes = @(
    (Get-AttributeDefinition "cr950_name" "Full Name" "String"),
    (Get-AttributeDefinition "cr950_employeenumber" "Employee Number" "String"),
    (Get-AttributeDefinition "cr950_employeetype" "Employee Type" "String"),
    (Get-AttributeDefinition "cr950_status" "Status" "String"),
    (Get-AttributeDefinition "cr950_title" "Title" "String"),
    (Get-AttributeDefinition "cr950_department" "Department" "String"),
    (Get-AttributeDefinition "cr950_email" "Email" "Email"),
    (Get-AttributeDefinition "cr950_phone" "Phone" "Phone"),
    (Get-AttributeDefinition "cr950_hiredate" "Hire Date" "DateTime"),
    (Get-AttributeDefinition "cr950_skillset" "Skillset" "Memo"),
    (Get-AttributeDefinition "cr950_certifications" "Certifications" "Memo"),
    (Get-AttributeDefinition "cr950_licensenumber" "License Number" "String"),
    (Get-AttributeDefinition "cr950_licenseexpiration" "License Expiration" "DateTime"),
    (Get-AttributeDefinition "cr950_hourlyrate" "Hourly Rate" "Money"),
    (Get-AttributeDefinition "cr950_overtimerate" "Overtime Rate" "Money"),
    (Get-AttributeDefinition "cr950_emergencycontact" "Emergency Contact" "String"),
    (Get-AttributeDefinition "cr950_emergencyphone" "Emergency Phone" "Phone"),
    (Get-AttributeDefinition "cr950_availability" "Availability" "String"),
    (Get-AttributeDefinition "cr950_notes" "Notes" "Memo")
)

New-DataverseTable -Token $token -DisplayName "Employee" -LogicalName "cr950_Employee" `
    -PluralName "Employees" -Description "Employee and resource management" -Attributes $employeeAttributes

# Table 4: Quotes
Write-Host "📋 Creating Quotes table..." -ForegroundColor Yellow
$quoteAttributes = @(
    (Get-AttributeDefinition "cr950_name" "Quote Name" "String"),
    (Get-AttributeDefinition "cr950_quotenumber" "Quote Number" "String"),
    (Get-AttributeDefinition "cr950_quotetype" "Quote Type" "String"),
    (Get-AttributeDefinition "cr950_status" "Status" "String"),
    (Get-AttributeDefinition "cr950_quotedate" "Quote Date" "DateTime"),
    (Get-AttributeDefinition "cr950_expirationdate" "Expiration Date" "DateTime"),
    (Get-AttributeDefinition "cr950_requestedby" "Requested By" "String"),
    (Get-AttributeDefinition "cr950_requestedemail" "Requested Email" "Email"),
    (Get-AttributeDefinition "cr950_scopedescription" "Scope Description" "Memo"),
    (Get-AttributeDefinition "cr950_estimatedhours" "Estimated Hours" "Decimal"),
    (Get-AttributeDefinition "cr950_laborrate" "Labor Rate" "Money"),
    (Get-AttributeDefinition "cr950_laborcost" "Labor Cost" "Money"),
    (Get-AttributeDefinition "cr950_materialcost" "Material Cost" "Money"),
    (Get-AttributeDefinition "cr950_equipmentcost" "Equipment Cost" "Money"),
    (Get-AttributeDefinition "cr950_othercosts" "Other Costs" "Money"),
    (Get-AttributeDefinition "cr950_subtotal" "Subtotal" "Money"),
    (Get-AttributeDefinition "cr950_margin" "Margin %" "Decimal"),
    (Get-AttributeDefinition "cr950_totalquote" "Total Quote" "Money"),
    (Get-AttributeDefinition "cr950_preparedby" "Prepared By" "String"),
    (Get-AttributeDefinition "cr950_approvedby" "Approved By" "String"),
    (Get-AttributeDefinition "cr950_approvaldate" "Approval Date" "DateTime"),
    (Get-AttributeDefinition "cr950_convertedtoproject" "Converted to Project" "Boolean"),
    (Get-AttributeDefinition "cr950_conversiondate" "Conversion Date" "DateTime"),
    (Get-AttributeDefinition "cr950_lossreason" "Loss Reason" "String"),
    (Get-AttributeDefinition "cr950_notes" "Notes" "Memo")
)

New-DataverseTable -Token $token -DisplayName "Quote" -LogicalName "cr950_Quote" `
    -PluralName "Quotes" -Description "Quote and proposal management" -Attributes $quoteAttributes

# Table 5: Resource Assignments
Write-Host "📋 Creating Resource Assignments table..." -ForegroundColor Yellow
$assignmentAttributes = @(
    (Get-AttributeDefinition "cr950_name" "Assignment Name" "String"),
    (Get-AttributeDefinition "cr950_assignmentnumber" "Assignment Number" "String"),
    (Get-AttributeDefinition "cr950_assignmenttype" "Assignment Type" "String"),
    (Get-AttributeDefinition "cr950_status" "Status" "String"),
    (Get-AttributeDefinition "cr950_startdate" "Start Date" "DateTime"),
    (Get-AttributeDefinition "cr950_enddate" "End Date" "DateTime"),
    (Get-AttributeDefinition "cr950_allocatedhours" "Allocated Hours" "Decimal"),
    (Get-AttributeDefinition "cr950_actualhours" "Actual Hours" "Decimal"),
    (Get-AttributeDefinition "cr950_remaininghours" "Remaining Hours" "Decimal"),
    (Get-AttributeDefinition "cr950_role" "Role" "String"),
    (Get-AttributeDefinition "cr950_billable" "Billable" "Boolean"),
    (Get-AttributeDefinition "cr950_billingrate" "Billing Rate" "Money"),
    (Get-AttributeDefinition "cr950_notes" "Notes" "Memo")
)

New-DataverseTable -Token $token -DisplayName "Resource Assignment" -LogicalName "cr950_ResourceAssignment" `
    -PluralName "Resource Assignments" -Description "Project resource allocation and tracking" -Attributes $assignmentAttributes

# Table 6: Equipment
Write-Host "📋 Creating Equipment table..." -ForegroundColor Yellow
$equipmentAttributes = @(
    (Get-AttributeDefinition "cr950_name" "Equipment Name" "String"),
    (Get-AttributeDefinition "cr950_equipmentnumber" "Equipment Number" "String"),
    (Get-AttributeDefinition "cr950_equipmenttype" "Equipment Type" "String"),
    (Get-AttributeDefinition "cr950_category" "Category" "String"),
    (Get-AttributeDefinition "cr950_status" "Status" "String"),
    (Get-AttributeDefinition "cr950_manufacturer" "Manufacturer" "String"),
    (Get-AttributeDefinition "cr950_model" "Model" "String"),
    (Get-AttributeDefinition "cr950_serialnumber" "Serial Number" "String"),
    (Get-AttributeDefinition "cr950_purchasedate" "Purchase Date" "DateTime"),
    (Get-AttributeDefinition "cr950_purchasecost" "Purchase Cost" "Money"),
    (Get-AttributeDefinition "cr950_calibrationrequired" "Calibration Required" "Boolean"),
    (Get-AttributeDefinition "cr950_lastcalibrationdate" "Last Calibration Date" "DateTime"),
    (Get-AttributeDefinition "cr950_nextcalibrationdue" "Next Calibration Due" "DateTime"),
    (Get-AttributeDefinition "cr950_calibrationinterval" "Calibration Interval (Days)" "Integer"),
    (Get-AttributeDefinition "cr950_maintenanceschedule" "Maintenance Schedule" "String"),
    (Get-AttributeDefinition "cr950_lastmaintenancedate" "Last Maintenance Date" "DateTime"),
    (Get-AttributeDefinition "cr950_nextmaintenancedue" "Next Maintenance Due" "DateTime"),
    (Get-AttributeDefinition "cr950_location" "Current Location" "String"),
    (Get-AttributeDefinition "cr950_notes" "Notes" "Memo")
)

New-DataverseTable -Token $token -DisplayName "Equipment" -LogicalName "cr950_Equipment" `
    -PluralName "Equipment" -Description "Test equipment and tools tracking" -Attributes $equipmentAttributes

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Table creation process completed!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Verify tables in Power Apps maker portal" -ForegroundColor White
Write-Host "   2. Configure lookup relationships between tables" -ForegroundColor White
Write-Host "   3. Test table creation with sample records" -ForegroundColor White
Write-Host "   4. Update existing Projects to reference new Clients/Sites" -ForegroundColor White
Write-Host ""
