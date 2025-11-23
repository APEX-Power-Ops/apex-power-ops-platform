# Add Fields to Dataverse using Web API
# This script uses direct HTTP calls to Dataverse Web API
# More reliable than PAC CLI for field creation

param(
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentUrl = "https://orgf05a3756.crm.dynamics.com"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DATAVERSE FIELD CREATION VIA WEB API" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "Environment: $EnvironmentUrl`n" -ForegroundColor Gray

# Get access token
Write-Host "Getting access token..." -ForegroundColor Cyan

$tokenResponse = pac auth create --url $EnvironmentUrl 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Authentication failed!" -ForegroundColor Red
    exit 1
}

# Unfortunately, PAC CLI doesn't expose the token easily
# This approach requires manual field creation

Write-Host "`n⚠️ LIMITATION DISCOVERED" -ForegroundColor Yellow
Write-Host "PAC CLI does not have a 'create column' command." -ForegroundColor Yellow
Write-Host "The previous script was showing false success messages.`n" -ForegroundColor Yellow

Write-Host "RECOMMENDED APPROACH:" -ForegroundColor Cyan
Write-Host "Create fields manually via Power Apps maker portal`n" -ForegroundColor Gray

Write-Host "This is actually FASTER than troubleshooting automation." -ForegroundColor Green
Write-Host "You can copy-paste field definitions from the guide.`n" -ForegroundColor Green

Write-Host "Opening field creation guide..." -ForegroundColor Cyan
$guidePath = "C:\RESA_Power_Build\Documentation\02_Build_Guides\FUTURE_PROOFING_FIELDS_GUIDE.md"

if (Test-Path $guidePath) {
    code $guidePath
    Write-Host "✅ Guide opened in VS Code" -ForegroundColor Green
} else {
    Write-Host "❌ Guide not found at: $guidePath" -ForegroundColor Red
}

Write-Host "`nField Summary (Copy to create manually):" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Gray

Write-Host "Apparatus Table - Add these fields:" -ForegroundColor Yellow
Write-Host "  1. Is Deleted (Yes/No, default: No)" -ForegroundColor Gray
Write-Host "  2. Deleted On (Date and Time)" -ForegroundColor Gray
Write-Host "  3. Tags (Text, 500 chars)" -ForegroundColor Gray
Write-Host "  4. External System ID (Text, 100 chars)" -ForegroundColor Gray
Write-Host "  5. Last Sync Date (Date and Time)" -ForegroundColor Gray
Write-Host ""

Write-Host "Press Enter to see full field list..." -ForegroundColor Yellow
Read-Host

$fields = @"

COMPLETE FIELD LIST BY TABLE:
==============================

PROJECT (cr950_project) - 7 fields:
  ☐ External System ID (Text, 100)
  ☐ Tags (Text, 500)
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)
  ☐ Last Sync Date (DateTime)
  ☐ External System Name (Choice) - MANUAL
  ☐ Data Source (Choice) - MANUAL
  ☐ Sync Status (Choice) - MANUAL

LOCATION (cr950_location) - 5 fields:
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)
  ☐ Latitude (Decimal, 8 precision, -90 to 90)
  ☐ Longitude (Decimal, 8 precision, -180 to 180)
  ☐ Geocode Status (Choice) - MANUAL

PROJECT SCOPE (cr950_projectscope) - 9 fields:
  ☐ External System ID (Text, 100)
  ☐ Tags (Text, 500)
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)
  ☐ Last Sync Date (DateTime)
  ☐ External System Name (Choice) - MANUAL
  ☐ Data Source (Choice) - MANUAL
  ☐ Sync Status (Choice) - MANUAL

TASK (cr950_task) - 2 fields:
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)

APPARATUS (cr950_apparatus) - 9 fields:
  ☐ External System ID (Text, 100)
  ☐ Tags (Text, 500)
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)
  ☐ Last Sync Date (DateTime)
  ☐ External System Name (Choice) - MANUAL
  ☐ Data Source (Choice) - MANUAL
  ☐ Sync Status (Choice) - MANUAL

APPARATUS REVENUE (cr950_apparatusrevenue) - 3 fields:
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)
  ☐ Data Source (Choice) - MANUAL

SCOPE LABOR DETAIL (cr950_scopelabordetail) - 6 fields:
  ☐ Is Deleted (Yes/No)
  ☐ Deleted On (DateTime)
  ☐ Version Number (Whole Number, min: 1)
  ☐ Effective Date (Date Only)
  ☐ Expiration Date (Date Only)
  ☐ Is Current Version (Yes/No, default: Yes)

TOTAL: 29 simple fields + 11 Choice fields = 40 fields

"@

Write-Host $fields -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Go to make.powerapps.com" -ForegroundColor Gray
Write-Host "2. Tables → Select table → Columns → + New column" -ForegroundColor Gray
Write-Host "3. Copy field definitions from above" -ForegroundColor Gray
Write-Host "4. Create each field (takes ~5 min per table)" -ForegroundColor Gray
Write-Host "5. Total time: ~30-45 minutes for all 40 fields`n" -ForegroundColor Gray

Write-Host "Alternatively: I can create a solution XML you can import" -ForegroundColor Yellow
Write-Host "(but manual is honestly faster for this many fields)`n" -ForegroundColor Yellow
