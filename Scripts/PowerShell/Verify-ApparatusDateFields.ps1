# Verify Apparatus Date Fields
# Created: November 23, 2025
# Purpose: Query Dataverse metadata to identify all date fields on cr950_apparatus table

# Import reusable functions
. "$PSScriptRoot\Dataverse-Functions.ps1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Apparatus Date Fields Verification   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Connect to Dataverse
Connect-Dataverse
if (-not $script:DataverseToken) {
    Write-Host "❌ Failed to connect to Dataverse" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "📊 Querying EntityDefinitions for cr950_apparatus..." -ForegroundColor Yellow
Write-Host ""

# Query entity metadata
$metadataUrl = "$($script:DataverseConfig.DataverseUrl)/api/data/v9.2/EntityDefinitions(LogicalName='cr950_apparatus')?`$select=LogicalName,SchemaName,DisplayName&`$expand=Attributes(`$select=LogicalName,SchemaName,DisplayName,AttributeType,RequiredLevel,Description;`$filter=AttributeType eq Microsoft.Dynamics.CRM.AttributeTypeCode'DateTime')"

try {
    $response = Invoke-RestMethod -Uri $metadataUrl -Method Get -Headers $script:DataverseHeaders
    
    Write-Host "✅ Successfully retrieved metadata" -ForegroundColor Green
    Write-Host ""
    Write-Host "📅 DATE/DATETIME FIELDS ON APPARATUS TABLE:" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    
    $dateFields = $response.Attributes | Where-Object { $_.AttributeType -eq 'DateTime' }
    
    if ($dateFields) {
        $results = @()
        
        foreach ($field in $dateFields) {
            $displayName = if ($field.DisplayName.LocalizedLabels.Count -gt 0) { 
                $field.DisplayName.LocalizedLabels[0].Label 
            } else { 
                "N/A" 
            }
            
            $description = if ($field.Description.LocalizedLabels.Count -gt 0) { 
                $field.Description.LocalizedLabels[0].Label 
            } else { 
                "" 
            }
            
            $requiredLevel = $field.RequiredLevel.Value
            
            $results += [PSCustomObject]@{
                LogicalName = $field.LogicalName
                SchemaName = $field.SchemaName
                DisplayName = $displayName
                RequiredLevel = $requiredLevel
                Description = $description
            }
        }
        
        # Sort by LogicalName to group similar fields
        $results = $results | Sort-Object LogicalName
        
        Write-Host "Total Date/DateTime Fields Found: $($results.Count)" -ForegroundColor White
        Write-Host ""
        
        # Display in table format
        $results | Format-Table -AutoSize -Wrap -Property `
            @{Label="Logical Name"; Expression={$_.LogicalName}; Width=30},
            @{Label="Schema Name"; Expression={$_.SchemaName}; Width=30},
            @{Label="Display Name"; Expression={$_.DisplayName}; Width=20},
            @{Label="Required"; Expression={$_.RequiredLevel}; Width=15}
        
        Write-Host ""
        Write-Host "🔍 DETAILED FIELD INFORMATION:" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host ""
        
        foreach ($field in $results) {
            Write-Host "Field: $($field.LogicalName)" -ForegroundColor Yellow
            Write-Host "  Schema Name: $($field.SchemaName)" -ForegroundColor Gray
            Write-Host "  Display Name: $($field.DisplayName)" -ForegroundColor Gray
            Write-Host "  Required Level: $($field.RequiredLevel)" -ForegroundColor Gray
            if ($field.Description) {
                Write-Host "  Description: $($field.Description)" -ForegroundColor Gray
            }
            Write-Host ""
        }
        
        # Check for duplicates
        Write-Host ""
        Write-Host "🚨 DUPLICATE ANALYSIS:" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host ""
        
        $duplicates = @()
        
        # Check for anticipated_start variants
        $anticipatedFields = $results | Where-Object { $_.LogicalName -like "*anticipated*start*" }
        if ($anticipatedFields.Count -gt 1) {
            Write-Host "⚠️  DUPLICATE: Anticipated Start fields found:" -ForegroundColor Yellow
            $anticipatedFields | ForEach-Object {
                Write-Host "     - $($_.LogicalName) ($($_.SchemaName))" -ForegroundColor Yellow
            }
            $duplicates += "anticipated_start"
        }
        
        # Check for actual_start variants
        $actualFields = $results | Where-Object { $_.LogicalName -like "*actual*start*" }
        if ($actualFields.Count -gt 1) {
            Write-Host "⚠️  DUPLICATE: Actual Start fields found:" -ForegroundColor Yellow
            $actualFields | ForEach-Object {
                Write-Host "     - $($_.LogicalName) ($($_.SchemaName))" -ForegroundColor Yellow
            }
            $duplicates += "actual_start"
        }
        
        # Check for date_completed variants
        $completedFields = $results | Where-Object { $_.LogicalName -like "*completed*" -or $_.LogicalName -like "*completion*" }
        if ($completedFields.Count -gt 1) {
            Write-Host "⚠️  DUPLICATE: Completion Date fields found:" -ForegroundColor Yellow
            $completedFields | ForEach-Object {
                Write-Host "     - $($_.LogicalName) ($($_.SchemaName))" -ForegroundColor Yellow
            }
            $duplicates += "date_completed"
        }
        
        if ($duplicates.Count -eq 0) {
            Write-Host "✅ No duplicate date fields found" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "❌ CRITICAL: $($duplicates.Count) duplicate field pattern(s) detected" -ForegroundColor Red
            Write-Host "   These must be resolved before creating rollup fields!" -ForegroundColor Red
        }
        
        # Export to JSON for documentation
        Write-Host ""
        Write-Host "💾 Saving results to JSON..." -ForegroundColor Cyan
        $exportPath = "$PSScriptRoot\..\..\Logs\Apparatus_DateFields_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        
        $exportData = @{
            QueryDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            TableName = "cr950_apparatus"
            TotalDateFields = $results.Count
            DuplicatesFound = $duplicates.Count
            Fields = $results
        }
        
        $exportData | ConvertTo-Json -Depth 10 | Out-File $exportPath -Encoding UTF8
        Write-Host "✅ Results saved to: $exportPath" -ForegroundColor Green
        
        # Recommendation
        Write-Host ""
        Write-Host "📋 RECOMMENDATIONS:" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host ""
        
        if ($duplicates.Count -gt 0) {
            Write-Host "1. ⚠️  IMMEDIATE: Identify which fields are in active use" -ForegroundColor Yellow
            Write-Host "2. ⚠️  Delete unused duplicate fields via Power Apps UI" -ForegroundColor Yellow
            Write-Host "3. ⚠️  Update MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md with correct field names" -ForegroundColor Yellow
            Write-Host "4. ✅  Proceed with rollup field implementation after cleanup" -ForegroundColor Green
        } else {
            Write-Host "1. ✅  No duplicates found - safe to proceed with rollup fields" -ForegroundColor Green
            Write-Host "2. ✅  Verify field names match MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md" -ForegroundColor Green
            Write-Host "3. ✅  Update documentation with confirmed field names" -ForegroundColor Green
        }
        
    } else {
        Write-Host "⚠️  No date/datetime fields found on cr950_apparatus table" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Error querying metadata: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host ""
        Write-Host "💡 Token may have expired. Try running Connect-Dataverse again." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           Verification Complete         " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
