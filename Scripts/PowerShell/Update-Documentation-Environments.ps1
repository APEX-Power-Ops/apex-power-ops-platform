# Update Documentation - Fix Outdated Environment References
# Created: November 23, 2025
# Purpose: Batch update all documentation with correct environment (org99cd6c6e only)

Write-Host "`n=== Documentation Environment Update ===" -ForegroundColor Cyan
Write-Host "Updating all documentation to reflect single environment: org99cd6c6e`n"

$filesToUpdate = @(
    "Documentation\00_START_HERE\SESSION_RESUME_CHECKLIST.md",
    "Documentation\00_START_HERE\MY_DEV_ENVIRONMENT.md",
    "Documentation\00_START_HERE\PROJECT_GUIDELINES_AND_WORKFLOWS.md",
    "Documentation\00_START_HERE\MCP_SERVER_QUICK_START.md",
    "Documentation\00_START_HERE\ACCELERATED_DEVELOPMENT_ENVIRONMENT_BLUEPRINT.md",
    "Documentation\00_START_HERE\DATAVERSE_ACCESS_QUICK_REFERENCE.md",
    "Documentation\00_START_HERE\MEMORY_MCP_TESTING_GUIDE.md",
    "Documentation\01_Architecture\MASTER_INDEX_BUILD_SPECIFICATIONS.md"
)

$replacements = @{
    "orgf05a3756.crm.dynamics.com" = "org99cd6c6e.crm.dynamics.com"
    "org04ad071f.crm.dynamics.com" = "org99cd6c6e.crm.dynamics.com"
    "org90c66be2.crm.dynamics.com" = "org99cd6c6e.crm.dynamics.com"
    "6f93b183-1bd3-41c6-bdf7-eefcc992ae6f" = "270d5723-4b30-4f3b-b9cb-6527be741b42"
    "19f68ef1-90a0-4813-be5f-22bb10dd9afd" = "9df3350f-b3b4-47c4-97b5-499a8b02acc7"
    "RESAPowerPM" = "RESA-Dev"
}

$totalUpdates = 0

foreach ($file in $filesToUpdate) {
    $fullPath = Join-Path $PSScriptRoot "..\..\$file"
    
    if (Test-Path $fullPath) {
        Write-Host "Updating: $file" -ForegroundColor Yellow
        
        $content = Get-Content $fullPath -Raw
        $originalContent = $content
        
        foreach ($old in $replacements.Keys) {
            $new = $replacements[$old]
            $content = $content -replace [regex]::Escape($old), $new
        }
        
        if ($content -ne $originalContent) {
            Set-Content -Path $fullPath -Value $content -NoNewline
            $totalUpdates++
            Write-Host "  ✅ Updated" -ForegroundColor Green
        } else {
            Write-Host "  ⏭️  No changes needed" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠️  File not found: $file" -ForegroundColor Red
    }
}

Write-Host "`n=== Update Complete ===" -ForegroundColor Cyan
Write-Host "Files updated: $totalUpdates`n" -ForegroundColor Green
