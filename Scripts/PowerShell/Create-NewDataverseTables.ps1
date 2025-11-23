# Create New Dataverse Tables - Excel Template Generator
# Created: November 22, 2025
# Purpose: Generate Excel files with table structures for new Dataverse entities

<#
.SYNOPSIS
    Generates Excel files with formatted tables for new Dataverse entities
.DESCRIPTION
    Creates 6 Excel files with proper table structures:
    - Clients
    - Sites  
    - Employees
    - Quotes
    - Resource Assignments
    - Equipment
#>

# Requires ImportExcel module
if (-not (Get-Module -ListAvailable -Name ImportExcel)) {
    Write-Host "📦 Installing ImportExcel module..." -ForegroundColor Cyan
    Install-Module -Name ImportExcel -Force -Scope CurrentUser
}

Import-Module ImportExcel

$outputPath = "C:\RESA_Power_Build\CSV_Templates\New_Tables"
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

Write-Host "`n🏗️  RESA Power - New Table Generator" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# ============================================
# 1. CLIENTS TABLE
# ============================================
Write-Host "`n📋 Creating Clients table..." -ForegroundColor Yellow

$clientsData = @(
    [PSCustomObject]@{
        cr950_name = "Sample Client Inc"
        cr950_clientnumber = "CLI-001"
        cr950_type = "Commercial"
        cr950_industry = "Utility"
        cr950_primarycontactname = "John Smith"
        cr950_primarycontactemail = "john.smith@sampleclient.com"
        cr950_primarycontactphone = "(555) 123-4567"
        cr950_billingcontactname = "Jane Doe"
        cr950_billingcontactemail = "billing@sampleclient.com"
        cr950_billingcontactphone = "(555) 123-4568"
        cr950_streetaddress = "123 Main Street"
        cr950_city = "Phoenix"
        cr950_state = "AZ"
        cr950_zipcode = "85001"
        cr950_country = "USA"
        cr950_taxid = "12-3456789"
        cr950_paymentterms = "Net 30"
        cr950_creditlimit = 100000
        cr950_insurancerequired = "Yes"
        cr950_insuranceexpirydate = (Get-Date).AddYears(1).ToString("yyyy-MM-dd")
        cr950_website = "www.sampleclient.com"
        cr950_notes = "Preferred client - priority service"
        cr950_status = "Active"
        cr950_accountmanager = "TBD"
        cr950_establisheddate = (Get-Date).AddYears(-5).ToString("yyyy-MM-dd")
    }
)

$clientsPath = "$outputPath\01_Clients_Template.xlsx"
$clientsData | Export-Excel -Path $clientsPath -WorksheetName "Clients" -TableName "ClientsTable" -TableStyle Medium2 -AutoSize -FreezeTopRow
Write-Host "   ✅ Created: $clientsPath" -ForegroundColor Green

# ============================================
# 2. SITES TABLE
# ============================================
Write-Host "`n📋 Creating Sites table..." -ForegroundColor Yellow

$sitesData = @(
    [PSCustomObject]@{
        cr950_name = "Main Substation - Phoenix"
        cr950_sitenumber = "SITE-001"
        cr950_client = "Sample Client Inc"
        cr950_type = "Substation"
        cr950_streetaddress = "456 Power Line Road"
        cr950_city = "Phoenix"
        cr950_state = "AZ"
        cr950_zipcode = "85002"
        cr950_country = "USA"
        cr950_latitude = "33.4484"
        cr950_longitude = "-112.0740"
        cr950_onsitecontactname = "Mike Johnson"
        cr950_onsitecontactphone = "(555) 234-5678"
        cr950_onsitecontactemail = "mike.j@sampleclient.com"
        cr950_accessrequirements = "Badge required, escort needed for first visit"
        cr950_safetyprotocol = "PPE required: hard hat, safety glasses, steel toes"
        cr950_parkinginfo = "Visitor parking on east side"
        cr950_securityclearance = "Standard"
        cr950_operatinghours = "24/7 - Schedule 24hrs in advance"
        cr950_emergencycontact = "(555) 999-9999"
        cr950_utilityprovider = "Sample Electric Co"
        cr950_voltage = "230kV"
        cr950_notes = "High security site - bring photo ID"
        cr950_status = "Active"
        cr950_lastvisited = (Get-Date).AddDays(-30).ToString("yyyy-MM-dd")
    }
)

$sitesPath = "$outputPath\02_Sites_Template.xlsx"
$sitesData | Export-Excel -Path $sitesPath -WorksheetName "Sites" -TableName "SitesTable" -TableStyle Medium2 -AutoSize -FreezeTopRow
Write-Host "   ✅ Created: $sitesPath" -ForegroundColor Green

# ============================================
# 3. EMPLOYEES TABLE
# ============================================
Write-Host "`n📋 Creating Employees table..." -ForegroundColor Yellow

$employeesData = @(
    [PSCustomObject]@{
        cr950_name = "Robert Martinez"
        cr950_employeenumber = "EMP-001"
        cr950_title = "Senior Field Technician"
        cr950_department = "Field Operations"
        cr950_email = "robert.martinez@resapower.com"
        cr950_phone = "(555) 345-6789"
        cr950_mobile = "(555) 345-6790"
        cr950_hiredate = (Get-Date).AddYears(-3).ToString("yyyy-MM-dd")
        cr950_employmenttype = "Full-Time"
        cr950_status = "Active"
        cr950_skillset = "NETA L3, Relay Testing, Switchgear"
        cr950_certifications = "NETA Level 3, OSHA 30, Arc Flash"
        cr950_certificationexpiry = (Get-Date).AddYears(2).ToString("yyyy-MM-dd")
        cr950_hourlylaborrate = 85.00
        cr950_overtimerate = 127.50
        cr950_billingrate = 165.00
        cr950_travelrate = 95.00
        cr950_availability = "Available"
        cr950_homeoffice = "Phoenix, AZ"
        cr950_willingtotravel = "Yes"
        cr950_maxdaysaway = 14
        cr950_emergencycontact = "Maria Martinez - (555) 999-1111"
        cr950_notes = "Preferred for complex relay work"
        cr950_supervisor = "TBD"
    }
)

$employeesPath = "$outputPath\03_Employees_Template.xlsx"
$employeesData | Export-Excel -Path $employeesPath -WorksheetName "Employees" -TableName "EmployeesTable" -TableStyle Medium2 -AutoSize -FreezeTopRow
Write-Host "   ✅ Created: $employeesPath" -ForegroundColor Green

# ============================================
# 4. QUOTES TABLE
# ============================================
Write-Host "`n📋 Creating Quotes table..." -ForegroundColor Yellow

$quotesData = @(
    [PSCustomObject]@{
        cr950_name = "Phoenix Substation Maintenance - 2025"
        cr950_quotenumber = "QTE-2025-001"
        cr950_client = "Sample Client Inc"
        cr950_site = "Main Substation - Phoenix"
        cr950_quotedate = (Get-Date).ToString("yyyy-MM-dd")
        cr950_validuntil = (Get-Date).AddDays(30).ToString("yyyy-MM-dd")
        cr950_requestedby = "John Smith"
        cr950_preparedby = "Sales Team"
        cr950_status = "Draft"
        cr950_type = "Maintenance"
        cr950_scopesummary = "Annual NETA testing and maintenance services"
        cr950_laborhours = 240
        cr950_laborrate = 165.00
        cr950_laboramount = 39600.00
        cr950_materialsamount = 2500.00
        cr950_travelamount = 1200.00
        cr950_equipmentamount = 500.00
        cr950_subtotal = 43800.00
        cr950_discount = 0.00
        cr950_tax = 0.00
        cr950_totalamount = 43800.00
        cr950_paymentterms = "50% upfront, 50% upon completion"
        cr950_projectduration = "2 weeks"
        cr950_proposedstartdate = (Get-Date).AddDays(45).ToString("yyyy-MM-dd")
        cr950_notes = "Includes all NETA testing per standards"
        cr950_wonlost = ""
        cr950_wondate = ""
        cr950_convertedproject = ""
        cr950_lossreason = ""
    }
)

$quotesPath = "$outputPath\04_Quotes_Template.xlsx"
$quotesData | Export-Excel -Path $quotesPath -WorksheetName "Quotes" -TableName "QuotesTable" -TableStyle Medium2 -AutoSize -FreezeTopRow
Write-Host "   ✅ Created: $quotesPath" -ForegroundColor Green

# ============================================
# 5. RESOURCE ASSIGNMENTS TABLE
# ============================================
Write-Host "`n📋 Creating Resource Assignments table..." -ForegroundColor Yellow

$assignmentsData = @(
    [PSCustomObject]@{
        cr950_name = "Robert Martinez - Phoenix Sub Project"
        cr950_assignmentnumber = "ASN-001"
        cr950_project = "Sample Project"
        cr950_employee = "Robert Martinez"
        cr950_role = "Lead Technician"
        cr950_startdate = (Get-Date).AddDays(10).ToString("yyyy-MM-dd")
        cr950_enddate = (Get-Date).AddDays(24).ToString("yyyy-MM-dd")
        cr950_estimatedhours = 120
        cr950_actualhours = 0
        cr950_remaininghours = 120
        cr950_percentcomplete = 0
        cr950_billingrate = 165.00
        cr950_laborrate = 85.00
        cr950_status = "Scheduled"
        cr950_assignmenttype = "Field Work"
        cr950_shifttype = "Day Shift"
        cr950_requirestravel = "Yes"
        cr950_accommodationsneeded = "Hotel"
        cr950_rentalcarneeded = "Yes"
        cr950_notes = "Primary relay technician"
        cr950_supervisor = "TBD"
        cr950_confirmationdate = ""
    }
)

$assignmentsPath = "$outputPath\05_Resource_Assignments_Template.xlsx"
$assignmentsData | Export-Excel -Path $assignmentsPath -WorksheetName "ResourceAssignments" -TableName "AssignmentsTable" -TableStyle Medium2 -AutoSize -FreezeTopRow
Write-Host "   ✅ Created: $assignmentsPath" -ForegroundColor Green

# ============================================
# 6. EQUIPMENT TABLE
# ============================================
Write-Host "`n📋 Creating Equipment table..." -ForegroundColor Yellow

$equipmentData = @(
    [PSCustomObject]@{
        cr950_name = "Omicron CMC 356"
        cr950_equipmentnumber = "EQP-001"
        cr950_type = "Relay Test Set"
        cr950_category = "Test Equipment"
        cr950_manufacturer = "Omicron"
        cr950_model = "CMC 356"
        cr950_serialnumber = "ABC123456"
        cr950_purchasedate = (Get-Date).AddYears(-2).ToString("yyyy-MM-dd")
        cr950_purchaseprice = 45000.00
        cr950_status = "Available"
        cr950_condition = "Excellent"
        cr950_location = "Phoenix Office"
        cr950_assignedto = ""
        cr950_currentproject = ""
        cr950_calibrationrequired = "Yes"
        cr950_lastcalibrationdate = (Get-Date).AddMonths(-6).ToString("yyyy-MM-dd")
        cr950_nextcalibrationdate = (Get-Date).AddMonths(6).ToString("yyyy-MM-dd")
        cr950_calibrationprovider = "Omicron Calibration Services"
        cr950_insurancevalue = 40000.00
        cr950_insurancepolicy = "TOOL-INS-2025"
        cr950_maintenanceschedule = "Annual"
        cr950_lastmaintenance = (Get-Date).AddMonths(-3).ToString("yyyy-MM-dd")
        cr950_nextmaintenance = (Get-Date).AddMonths(9).ToString("yyyy-MM-dd")
        cr950_rentalrate = 500.00
        cr950_notes = "Primary relay test set - excellent condition"
    }
)

$equipmentPath = "$outputPath\06_Equipment_Template.xlsx"
$equipmentData | Export-Excel -Path $equipmentPath -WorksheetName "Equipment" -TableName "EquipmentTable" -TableStyle Medium2 -AutoSize -FreezeTopRow
Write-Host "   ✅ Created: $equipmentPath" -ForegroundColor Green

# ============================================
# SUMMARY & DOCUMENTATION
# ============================================
Write-Host "`n" -NoNewline
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ All 6 Excel templates created!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

Write-Host "`n📁 Files created in:" -ForegroundColor Cyan
Write-Host "   $outputPath" -ForegroundColor White

Write-Host "`n📋 Templates:" -ForegroundColor Cyan
Write-Host "   1. Clients (25 columns)" -ForegroundColor White
Write-Host "   2. Sites (26 columns)" -ForegroundColor White
Write-Host "   3. Employees (25 columns)" -ForegroundColor White
Write-Host "   4. Quotes (31 columns)" -ForegroundColor White
Write-Host "   5. Resource Assignments (22 columns)" -ForegroundColor White
Write-Host "   6. Equipment (25 columns)" -ForegroundColor White

Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open each Excel file and review/modify columns" -ForegroundColor Yellow
Write-Host "   2. Add sample data rows as needed" -ForegroundColor Yellow
Write-Host "   3. Use Power Query to import to Dataverse" -ForegroundColor Yellow
Write-Host "   4. Or use PowerShell script to create tables via API" -ForegroundColor Yellow

Write-Host "`n💡 Features:" -ForegroundColor Cyan
Write-Host "   • Each file has Excel Table formatting" -ForegroundColor White
Write-Host "   • Column headers match Dataverse naming (cr950_ prefix)" -ForegroundColor White
Write-Host "   • Sample data row included in each" -ForegroundColor White
Write-Host "   • Auto-sized columns for readability" -ForegroundColor White
Write-Host "   • Frozen header rows" -ForegroundColor White

Write-Host "`n🔗 Relationships to Configure:" -ForegroundColor Cyan
Write-Host "   • Sites → Clients (lookup)" -ForegroundColor White
Write-Host "   • Quotes → Clients (lookup)" -ForegroundColor White
Write-Host "   • Quotes → Sites (lookup)" -ForegroundColor White
Write-Host "   • Resource Assignments → Projects (lookup)" -ForegroundColor White
Write-Host "   • Resource Assignments → Employees (lookup)" -ForegroundColor White
Write-Host "   • Equipment → Employees (assignedto lookup)" -ForegroundColor White
Write-Host "   • Equipment → Projects (currentproject lookup)" -ForegroundColor White

Write-Host "`n"
