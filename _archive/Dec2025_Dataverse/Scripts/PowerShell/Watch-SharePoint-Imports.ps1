<#
.SYNOPSIS
    RESA Power - Watch SharePoint folder and import JSON files to Dataverse
    
.DESCRIPTION
    This script monitors a local folder (synced from SharePoint) for new JSON files
    and automatically imports them to Dataverse using the Node.js import script.
    
.NOTES
    Author: RESA Power Build System
    Version: 1.0
    
    Prerequisites:
    1. Node.js installed
    2. SharePoint folder synced locally
    3. MCP Server credentials configured in .env file
#>

param(
    [string]$WatchFolder = "C:\Users\$env:USERNAME\RESA Power\Estimating - Estimators\Dataverse_Exports",
    [string]$ScriptFolder = "C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp",
    [string]$ProcessedFolder = "C:\Users\$env:USERNAME\RESA Power\Estimating - Estimators\Dataverse_Exports\Processed",
    [switch]$WatchMode,
    [string]$SingleFile
)

$ErrorActionPreference = "Stop"

# Banner
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   RESA POWER - DATAVERSE IMPORT WATCHER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to import a single JSON file
function Import-EstimatorJSON {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "ERROR: File not found: $FilePath" -ForegroundColor Red
        return $false
    }
    
    $fileName = Split-Path $FilePath -Leaf
    Write-Host ""
    Write-Host "Processing: $fileName" -ForegroundColor Yellow
    Write-Host "   Path: $FilePath"
    
    # Run the Node.js import script
    Push-Location $ScriptFolder
    try {
        $result = & node import-estimator.js $FilePath 2>&1
        $exitCode = $LASTEXITCODE
        
        # Display output
        $result | ForEach-Object { Write-Host $_ }
        
        if ($exitCode -eq 0) {
            Write-Host ""
            Write-Host "   SUCCESS: Import completed" -ForegroundColor Green
            
            # Move to processed folder
            if (Test-Path $ProcessedFolder) {
                $newPath = Join-Path $ProcessedFolder $fileName
                Move-Item $FilePath $newPath -Force
                Write-Host "   Moved to: $ProcessedFolder" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host ""
            Write-Host "   FAILED: Import failed with exit code $exitCode" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        Pop-Location
    }
}

# Single file mode
if ($SingleFile) {
    Write-Host "Single File Mode" -ForegroundColor Cyan
    Import-EstimatorJSON -FilePath $SingleFile
    exit
}

# Ensure processed folder exists
if (-not (Test-Path $ProcessedFolder)) {
    New-Item -ItemType Directory -Path $ProcessedFolder -Force | Out-Null
    Write-Host "Created processed folder: $ProcessedFolder" -ForegroundColor Gray
}

# Check for existing files
Write-Host "Checking for pending JSON files in: $WatchFolder" -ForegroundColor Cyan
Write-Host ""

$pendingFiles = Get-ChildItem -Path $WatchFolder -Filter "*.json" -File -ErrorAction SilentlyContinue

if ($pendingFiles.Count -gt 0) {
    Write-Host "Found $($pendingFiles.Count) pending file(s)" -ForegroundColor Yellow
    
    foreach ($file in $pendingFiles) {
        Import-EstimatorJSON -FilePath $file.FullName
    }
}
else {
    Write-Host "No pending JSON files found" -ForegroundColor Gray
}

# Watch mode - continuously monitor for new files
if ($WatchMode) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   WATCH MODE ACTIVE - Monitoring for new files..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $WatchFolder
    $watcher.Filter = "*.json"
    $watcher.EnableRaisingEvents = $true
    
    $action = {
        $path = $Event.SourceEventArgs.FullPath
        $name = $Event.SourceEventArgs.Name
        
        Write-Host ""
        Write-Host "New file detected: $name" -ForegroundColor Yellow
        
        # Wait a moment for file to finish writing
        Start-Sleep -Seconds 2
        
        Import-EstimatorJSON -FilePath $path
    }
    
    Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action | Out-Null
    
    # Keep script running
    try {
        while ($true) {
            Start-Sleep -Seconds 1
        }
    }
    finally {
        $watcher.Dispose()
    }
}
else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "   BATCH PROCESSING COMPLETE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To enable continuous monitoring, run with -WatchMode flag:" -ForegroundColor Gray
    Write-Host "   .\Watch-SharePoint-Imports.ps1 -WatchMode" -ForegroundColor White
    Write-Host ""
}
