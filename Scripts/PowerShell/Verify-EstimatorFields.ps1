# Verify-EstimatorFields.ps1
# Quick verification of Estimator table fields

$DocumentedCurrentNames = @(
    "cr950_estimatorid", "cr950_name", "cr950_clientid", "cr950_projectid",
    "cr950_projectname", "cr950_filename", "cr950_estimator_file_url",
    "cr950_estimatedate", "cr950_lastmodified", "cr950_currentrevision",
    "cr950_convertedtoproject", "cr950_status", "cr950_notes"
)

$DocumentedNewNames = @(
    "cr950_scopejson", "cr950_extractedat", "cr950_scopecount",
    "cr950_totalapparatus", "cr950_totalhours", "cr950_totalamount",
    "cr950_converteddate", "cr950_extractionstatus"
)

$DataverseNames = @(
    "cr950_clientid", "cr950_convertedtoproject", "cr950_currentrevision",
    "cr950_estimatedate", "cr950_estimator_file_url", "cr950_estimatorid",
    "cr950_filename", "cr950_lastmodified", "cr950_name", "cr950_notes",
    "cr950_projectid", "cr950_projectname", "cr950_status"
)

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "ESTIMATOR TABLE FIELD VERIFICATION" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`nVERIFIED (in Dataverse + Doc):" -ForegroundColor Green
$verified = $DocumentedCurrentNames | Where-Object { $_ -in $DataverseNames }
$verified | ForEach-Object { Write-Host "  [OK] $_" -ForegroundColor Green }
Write-Host "  Total: $($verified.Count)" -ForegroundColor Green

Write-Host "`nTO ADD (v1.6.0):" -ForegroundColor Yellow
$DocumentedNewNames | ForEach-Object { Write-Host "  [ADD] $_" -ForegroundColor Yellow }
Write-Host "  Total: $($DocumentedNewNames.Count)" -ForegroundColor Yellow

Write-Host "`nMISSING:" -ForegroundColor Red
$missing = $DocumentedCurrentNames | Where-Object { $_ -notin $DataverseNames }
if ($missing.Count -eq 0) { Write-Host "  None" -ForegroundColor Green }
else { $missing | ForEach-Object { Write-Host "  [X] $_" -ForegroundColor Red } }

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "SUMMARY: $($verified.Count) verified, $($DocumentedNewNames.Count) to add, $($missing.Count) missing" -ForegroundColor Cyan
