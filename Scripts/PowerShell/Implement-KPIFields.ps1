# Master KPI Fields Implementation Script
# Created: November 22, 2025
# Purpose: Execute complete KPI implementation (Date Tracking + Financial Rollups)
# References: KPI_FIELDS_IMPLEMENTATION_PRIORITY.md

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("All", "DateTracking", "FinancialSummary", "Status")]
    [string]$Phase = "Status"
)

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      RESA Power - KPI Fields Master Implementation      ║" -ForegroundColor Cyan
Write-Host "║                                                          ║" -ForegroundColor Cyan
Write-Host "║  Phase 1: Date Tracking (Operations)                    ║" -ForegroundColor Cyan
Write-Host "║  Phase 2: Revenue Rollups (Finance - Separated)         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# FUNCTIONS
# ============================================================================

function Show-Status {
    Write-Host "`n📊 KPI FIELDS IMPLEMENTATION STATUS" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    Write-Host "Phase 1: Date Tracking Fields" -ForegroundColor Yellow
    Write-Host "  ├─ Base Fields (Apparatus): 3 fields" -ForegroundColor White
    Write-Host "  │  ├─ Anticipated Start (DateTime)" -ForegroundColor Gray
    Write-Host "  │  ├─ Actual Start (DateTime)" -ForegroundColor Gray
    Write-Host "  │  └─ Date Completed (DateTime)" -ForegroundColor Gray
    Write-Host "  ├─ Rollup Fields (Tasks): 6 fields - MANUAL CONFIG REQUIRED" -ForegroundColor White
    Write-Host "  ├─ Rollup Fields (Scopes): 6 fields - MANUAL CONFIG REQUIRED" -ForegroundColor White
    Write-Host "  └─ Rollup Fields (Projects): 6 fields - MANUAL CONFIG REQUIRED" -ForegroundColor White
    Write-Host "  Total: 21 fields | Time: 3 hours`n" -ForegroundColor Cyan
    
    Write-Host "Phase 2: Financial Summary Tables" -ForegroundColor Yellow
    Write-Host "  ├─ Scope Financial Summary: NEW TABLE" -ForegroundColor White
    Write-Host "  │  ├─ Scope Lookup (1:1 relationship)" -ForegroundColor Gray
    Write-Host "  │  └─ 7 revenue rollup fields - MANUAL CONFIG REQUIRED" -ForegroundColor Gray
    Write-Host "  └─ Project Financial Summary: NEW TABLE" -ForegroundColor White
    Write-Host "     ├─ Project Lookup (1:1 relationship)" -ForegroundColor Gray
    Write-Host "     └─ 7 revenue rollup fields - MANUAL CONFIG REQUIRED" -ForegroundColor Gray
    Write-Host "  Total: 2 tables + 14 rollup fields | Time: 2 hours`n" -ForegroundColor Cyan
    
    Write-Host "Architecture Decision:" -ForegroundColor Yellow
    Write-Host "  ✅ Operational data (dates) stays on operational tables" -ForegroundColor Green
    Write-Host "  ✅ Financial data (revenue) separated into dedicated tables" -ForegroundColor Green
    Write-Host "  ✅ Security roles enforce separation of concerns" -ForegroundColor Green
    Write-Host "  ✅ Finance and Operations work independently`n" -ForegroundColor Green
    
    Write-Host "Total Implementation:" -ForegroundColor Yellow
    Write-Host "  - New Tables: 2" -ForegroundColor White
    Write-Host "  - Base Fields: 3" -ForegroundColor White
    Write-Host "  - Rollup Fields: 32 (18 date + 14 revenue)" -ForegroundColor White
    Write-Host "  - Time Estimate: 5-6 hours" -ForegroundColor White
    Write-Host "  - Target Version: v1.5.0.0 (date tracking) → v1.5.1.0 (revenue)`n" -ForegroundColor White
    
    Write-Host "📖 Documentation:" -ForegroundColor Cyan
    Write-Host "  - KPI_FIELDS_IMPLEMENTATION_PRIORITY.md (master spec)" -ForegroundColor Gray
    Write-Host "  - DATE_TRACKING_IMPLEMENTATION.md (date tracking details)" -ForegroundColor Gray
    Write-Host "  - REVENUE_RECOGNITION_FLOW_SPEC.md (existing revenue flow)`n" -ForegroundColor Gray
}

function Show-Menu {
    Write-Host "`n🎯 EXECUTION OPTIONS:" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    Write-Host "1. Date Tracking Fields" -ForegroundColor Yellow
    Write-Host "   Run: .\Implement-KPIFields.ps1 -Phase DateTracking" -ForegroundColor White
    Write-Host "   Creates: 3 base date fields on Apparatus" -ForegroundColor Gray
    Write-Host "   Manual: Add 18 rollup fields via UI (Tasks, Scopes, Projects)" -ForegroundColor Gray
    Write-Host "   Time: 3 hours total`n" -ForegroundColor Gray
    
    Write-Host "2. Financial Summary Tables" -ForegroundColor Yellow
    Write-Host "   Run: .\Implement-KPIFields.ps1 -Phase FinancialSummary" -ForegroundColor White
    Write-Host "   Creates: 2 new tables with lookup fields" -ForegroundColor Gray
    Write-Host "   Manual: Add 14 rollup fields via UI (both tables)" -ForegroundColor Gray
    Write-Host "   Time: 2 hours total`n" -ForegroundColor Gray
    
    Write-Host "3. Complete Implementation" -ForegroundColor Yellow
    Write-Host "   Run: .\Implement-KPIFields.ps1 -Phase All" -ForegroundColor White
    Write-Host "   Executes both Phase 1 and Phase 2" -ForegroundColor Gray
    Write-Host "   Time: 5-6 hours total`n" -ForegroundColor Gray
    
    Write-Host "4. Show Status (Default)" -ForegroundColor Yellow
    Write-Host "   Run: .\Implement-KPIFields.ps1 -Phase Status" -ForegroundColor White
    Write-Host "   OR: .\Implement-KPIFields.ps1 (no parameters)" -ForegroundColor White
    Write-Host "   Displays this information`n" -ForegroundColor Gray
}

# ============================================================================
# PHASE EXECUTION
# ============================================================================

function Execute-DateTracking {
    Write-Host "`n▶️  Executing Phase 1: Date Tracking Fields`n" -ForegroundColor Cyan
    
    $dateTrackingScript = "$PSScriptRoot\Add-DateTrackingFields.ps1"
    
    if (Test-Path $dateTrackingScript) {
        & $dateTrackingScript
    }
    else {
        Write-Host "❌ Script not found: $dateTrackingScript" -ForegroundColor Red
        Write-Host "   Expected location: Scripts\PowerShell\Add-DateTrackingFields.ps1" -ForegroundColor Yellow
    }
}

function Execute-FinancialSummary {
    Write-Host "`n▶️  Executing Phase 2: Financial Summary Tables`n" -ForegroundColor Cyan
    
    $financialScript = "$PSScriptRoot\Create-FinancialSummaryTables.ps1"
    
    if (Test-Path $financialScript) {
        & $financialScript
    }
    else {
        Write-Host "❌ Script not found: $financialScript" -ForegroundColor Red
        Write-Host "   Expected location: Scripts\PowerShell\Create-FinancialSummaryTables.ps1" -ForegroundColor Yellow
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

switch ($Phase) {
    "Status" {
        Show-Status
        Show-Menu
    }
    
    "DateTracking" {
        Show-Status
        Write-Host "`n⚠️  IMPORTANT: This will create 3 base date fields on Apparatus table" -ForegroundColor Yellow
        Write-Host "   You will need to manually add 18 rollup fields via UI afterward`n" -ForegroundColor Yellow
        
        $confirm = Read-Host "Continue? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Execute-DateTracking
        }
        else {
            Write-Host "`n❌ Cancelled by user`n" -ForegroundColor Yellow
        }
    }
    
    "FinancialSummary" {
        Show-Status
        Write-Host "`n⚠️  IMPORTANT: This will create 2 new tables (Scope/Project Financial Summary)" -ForegroundColor Yellow
        Write-Host "   You will need to manually add 14 rollup fields via UI afterward`n" -ForegroundColor Yellow
        
        $confirm = Read-Host "Continue? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Execute-FinancialSummary
        }
        else {
            Write-Host "`n❌ Cancelled by user`n" -ForegroundColor Yellow
        }
    }
    
    "All" {
        Show-Status
        Write-Host "`n⚠️  IMPORTANT: This will execute BOTH phases:" -ForegroundColor Yellow
        Write-Host "   Phase 1: 3 date fields on Apparatus" -ForegroundColor Yellow
        Write-Host "   Phase 2: 2 new financial summary tables`n" -ForegroundColor Yellow
        Write-Host "   Total manual config after: 32 rollup fields`n" -ForegroundColor Yellow
        
        $confirm = Read-Host "Continue with full implementation? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Execute-DateTracking
            Write-Host "`n⏸️  Pausing 10 seconds before Phase 2...`n" -ForegroundColor Cyan
            Start-Sleep -Seconds 10
            Execute-FinancialSummary
            
            Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
            Write-Host "║           BOTH PHASES EXECUTION COMPLETE                 ║" -ForegroundColor Green
            Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
            
            Write-Host "`n✅ Created:" -ForegroundColor Cyan
            Write-Host "   - 3 base date fields (Apparatus)" -ForegroundColor White
            Write-Host "   - 2 financial summary tables (with lookup fields)" -ForegroundColor White
            
            Write-Host "`n⏳ Manual Configuration Required:" -ForegroundColor Yellow
            Write-Host "   - 18 date rollup fields (Tasks, Scopes, Projects)" -ForegroundColor White
            Write-Host "   - 14 revenue rollup fields (Scope/Project Financial Summary)" -ForegroundColor White
            Write-Host "   - 6 KPI views for date tracking" -ForegroundColor White
            Write-Host "   - 2 finance dashboard views" -ForegroundColor White
            Write-Host "   - Security role configuration" -ForegroundColor White
            Write-Host "   - Power Automate flows (auto-create financial records)" -ForegroundColor White
            
            Write-Host "`n📖 See KPI_FIELDS_IMPLEMENTATION_PRIORITY.md for complete specs`n" -ForegroundColor Cyan
        }
        else {
            Write-Host "`n❌ Cancelled by user`n" -ForegroundColor Yellow
        }
    }
}

Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
