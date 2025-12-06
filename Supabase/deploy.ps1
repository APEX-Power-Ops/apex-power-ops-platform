# =============================================================================
# RESA Power Platform - Supabase Deployment Script
# =============================================================================
# Usage: .\deploy.ps1 -Password "your_db_password"
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "schema", "data", "test")]
    [string]$Mode = "all"
)

# Configuration
$ProjectRef = "fxoyniqnrlkxfligbxmg"
$DbHost = "db.$ProjectRef.supabase.co"
$DbPort = "5432"
$DbName = "postgres"
$DbUser = "postgres"

# Build connection string
$ConnectionString = "postgresql://${DbUser}:${Password}@${DbHost}:${DbPort}/${DbName}"

# Schema files in order
$SchemaFiles = @(
    "schema/00_enums.sql",
    "schema/01_tables.sql",
    "schema/02_relationships.sql",
    "schema/03_triggers.sql",
    "schema/04_views.sql",
    "schema/05_indexes.sql"
)

# Data files in order
$DataFiles = @(
    "data/10_seed_data.sql",
    "data/11_test_data.sql",
    "data/12_pss_test_data.sql"
)

# Colors for output
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Warn { param($msg) Write-Host "! $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }

# Check for psql
function Test-Psql {
    try {
        $null = Get-Command psql -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Execute SQL file
function Invoke-SqlFile {
    param([string]$FilePath)
    
    $FullPath = Join-Path $PSScriptRoot $FilePath
    if (-not (Test-Path $FullPath)) {
        Write-Fail "File not found: $FilePath"
        return $false
    }
    
    Write-Info "Executing: $FilePath"
    
    try {
        $env:PGPASSWORD = $Password
        $result = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $FullPath -v ON_ERROR_STOP=1 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Completed: $FilePath"
            return $true
        } else {
            Write-Fail "Failed: $FilePath"
            Write-Host $result -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Fail "Error executing: $FilePath - $_"
        return $false
    }
}

# Main execution
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        RESA Power Platform - Supabase Deployment             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Info "Project: $ProjectRef"
Write-Info "Mode: $Mode"
Write-Host ""

# Check prerequisites
if (-not (Test-Psql)) {
    Write-Fail "psql not found. Install PostgreSQL client tools."
    Write-Host ""
    Write-Host "Install options:"
    Write-Host "  - winget install PostgreSQL.PostgreSQL"
    Write-Host "  - Or download from https://www.postgresql.org/download/"
    exit 1
}

$success = $true
$startTime = Get-Date

# Deploy schema
if ($Mode -eq "all" -or $Mode -eq "schema") {
    Write-Host ""
    Write-Host "═══ DEPLOYING SCHEMA ═══" -ForegroundColor Yellow
    foreach ($file in $SchemaFiles) {
        if (-not (Invoke-SqlFile $file)) {
            $success = $false
            if ($Mode -ne "test") { break }
        }
    }
}

# Deploy data
if ($success -and ($Mode -eq "all" -or $Mode -eq "data")) {
    Write-Host ""
    Write-Host "═══ LOADING DATA ═══" -ForegroundColor Yellow
    foreach ($file in $DataFiles) {
        if (-not (Invoke-SqlFile $file)) {
            $success = $false
            if ($Mode -ne "test") { break }
        }
    }
}

# Summary
$elapsed = (Get-Date) - $startTime
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($success) {
    Write-Success "Deployment completed in $($elapsed.TotalSeconds.ToString('F1')) seconds"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Open Supabase Dashboard: https://supabase.com/dashboard/project/$ProjectRef"
    Write-Host "  2. Go to Table Editor to verify data"
    Write-Host "  3. Test API at: https://$ProjectRef.supabase.co/rest/v1/"
} else {
    Write-Fail "Deployment failed after $($elapsed.TotalSeconds.ToString('F1')) seconds"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Check error messages above"
    Write-Host "  - Verify password is correct"
    Write-Host "  - Try running failed SQL file manually in Supabase SQL Editor"
}

Write-Host ""
