<#
.SYNOPSIS
    Excel Workbook Extractor (No Excel Required)
    Uses ImportExcel module instead of Excel COM objects

.DESCRIPTION
    Extracts from Excel workbooks without requiring Excel installation:
    - All sheet names and data
    - Column headers
    - All formulas with cell locations
    - Named ranges
    - Tables (if accessible)
    - Data export to CSV

.OUTPUTS
    Creates a folder with the workbook name containing:
    - _Summary.txt - Overview of workbook structure
    - _Formulas.txt - All formulas organized by sheet
    - _NamedRanges.txt - Named range definitions
    - SheetName_Data.csv - Data from each sheet
    - SheetName_Structure.txt - Detailed structure per sheet
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ExcelFilePath
)

# Configuration
$ErrorActionPreference = 'Stop'

# Constants
$MAX_CSV_ROWS = 10000
$MAX_SAMPLE_ROWS = 30
$MAX_SAMPLE_COLS = 20

# Check for ImportExcel module
# Add user module path if not present
$userModulePath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PowerShell\Modules'
if ($env:PSModulePath -notlike "*$userModulePath*") {
    $env:PSModulePath = "$userModulePath;$env:PSModulePath"
}

try {
    Import-Module ImportExcel -ErrorAction Stop
} catch {
    Write-Host ""
    Write-Host "ERROR: ImportExcel module not found" -ForegroundColor Red
    Write-Host "Install it with: Install-Module ImportExcel -Scope CurrentUser" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Validate file exists
if (-not (Test-Path $ExcelFilePath)) {
    Write-Error "File not found: $ExcelFilePath"
    Read-Host "Press Enter to exit"
    exit 1
}

$file = Get-Item $ExcelFilePath
$fileName = $file.BaseName
$outputFolder = Join-Path $file.DirectoryName "$($fileName)_Extracted"

# Create output folder
if (Test-Path $outputFolder) {
    Remove-Item $outputFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $outputFolder | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Excel Structure Extractor (No Excel)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "File: $($file.Name)" -ForegroundColor Yellow
Write-Host "Output: $outputFolder" -ForegroundColor Yellow
Write-Host ""

try {
    # Get Excel package
    Write-Host "Opening workbook..." -ForegroundColor Gray
    $pkg = Open-ExcelPackage -Path $file.FullName
    
    # ============================================
    # SUMMARY FILE
    # ============================================
    $summaryFile = Join-Path $outputFolder "_Summary.txt"
    $summary = @()
    $summary += "=" * 80
    $summary += "EXCEL WORKBOOK ANALYSIS"
    $summary += "=" * 80
    $summary += "File: $($file.Name)"
    $summary += "Size: $([math]::Round($file.Length/1KB, 2)) KB"
    $summary += "Modified: $($file.LastWriteTime)"
    $summary += "Sheets: $($pkg.Workbook.Worksheets.Count)"
    $summary += ""
    
    # ============================================
    # NAMED RANGES
    # ============================================
    Write-Host "Extracting named ranges..." -ForegroundColor Gray
    $namedRangesFile = Join-Path $outputFolder "_NamedRanges.txt"
    $namedRanges = @()
    $namedRanges += "=" * 80
    $namedRanges += "NAMED RANGES"
    $namedRanges += "=" * 80
    
    foreach ($name in $pkg.Workbook.Names) {
        try {
            $namedRanges += ""
            $namedRanges += "Name: $($name.Name)"
            $namedRanges += "Formula: $($name.Formula)"
            if ($name.LocalSheet) {
                $namedRanges += "Scope: Sheet - $($name.LocalSheet.Name)"
            } else {
                $namedRanges += "Scope: Workbook"
            }
        } catch {
            $namedRanges += "  (Could not read)"
        }
    }
    $namedRanges | Out-File $namedRangesFile -Encoding UTF8
    
    # ============================================
    # FORMULAS FILE
    # ============================================
    $formulasFile = Join-Path $outputFolder "_Formulas.txt"
    $formulas = @()
    $formulas += "=" * 80
    $formulas += "ALL FORMULAS BY SHEET"
    $formulas += "=" * 80
    
    # ============================================
    # PROCESS EACH SHEET
    # ============================================
    $sheetIndex = 0
    foreach ($ws in $pkg.Workbook.Worksheets) {
        $sheetIndex++
        $sheetName = $ws.Name
        $safeSheetName = $sheetName -replace '[\\/:*?"<>|]', '_'
        
        Write-Host "Processing sheet $sheetIndex/$($pkg.Workbook.Worksheets.Count): $sheetName" -ForegroundColor White
        
        $dimension = $ws.Dimension
        if ($null -eq $dimension) {
            $summary += "Sheet: $sheetName (Empty)"
            continue
        }
        
        $rowCount = $dimension.Rows
        $colCount = $dimension.Columns
        
        $summary += ""
        $summary += "-" * 40
        $summary += "Sheet: $sheetName"
        $summary += "-" * 40
        $summary += "  Used Range: $($dimension.Address)"
        $summary += "  Rows: $rowCount, Columns: $colCount"
        
        # ============================================
        # STRUCTURE FILE FOR THIS SHEET
        # ============================================
        $structureFile = Join-Path $outputFolder "$($safeSheetName)_Structure.txt"
        $structure = @()
        $structure += "=" * 80
        $structure += "SHEET: $sheetName"
        $structure += "=" * 80
        $structure += "Used Range: $($dimension.Address)"
        $structure += "Rows: $rowCount, Columns: $colCount"
        $structure += ""
        
        # ============================================
        # COLUMN HEADERS (First row)
        # ============================================
        $structure += "-" * 40
        $structure += "COLUMN HEADERS (Row 1)"
        $structure += "-" * 40
        
        for ($col = 1; $col -le [Math]::Min($colCount, 50); $col++) {
            $cell = $ws.Cells[1, $col]
            $value = $cell.Value
            $formula = ""
            if ($cell.Formula) {
                $formula = " [FORMULA: $($cell.Formula)]"
            }
            $structure += "  $($cell.Address) : $value$formula"
        }
        $structure += ""
        
        # ============================================
        # TABLES
        # ============================================
        if ($ws.Tables.Count -gt 0) {
            $structure += "-" * 40
            $structure += "TABLES"
            $structure += "-" * 40
            foreach ($table in $ws.Tables) {
                $structure += "  Table: $($table.Name)"
                $structure += "    Range: $($table.Address)"
                $structure += "    Columns: $($table.Columns.Count)"
            }
            $structure += ""
        }
        
        # ============================================
        # FORMULAS ON THIS SHEET
        # ============================================
        $formulas += ""
        $formulas += "=" * 60
        $formulas += "SHEET: $sheetName"
        $formulas += "=" * 60
        
        $structure += "-" * 40
        $structure += "FORMULAS"
        $structure += "-" * 40
        
        $formulaCount = 0
        $formulaDict = @{}
        
        # Scan for formulas
        foreach ($cell in $ws.Cells) {
            if ($cell.Formula) {
                $formulaCount++
                $addr = $cell.Address
                $formula = $cell.Formula
                
                # Group similar formulas
                $formulaPattern = $formula -replace '\d+', '#'
                if (-not $formulaDict.ContainsKey($formulaPattern)) {
                    $formulaDict[$formulaPattern] = @{
                        Example = "$addr : $formula"
                        Count = 1
                        Cells = @($addr)
                    }
                } else {
                    $formulaDict[$formulaPattern].Count++
                    if ($formulaDict[$formulaPattern].Cells.Count -lt 5) {
                        $formulaDict[$formulaPattern].Cells += $addr
                    }
                }
            }
        }
        
        $structure += "  Total formulas: $formulaCount"
        $structure += ""
        
        # Output unique formula patterns
        if ($formulaDict.Count -gt 0) {
            $structure += "  UNIQUE FORMULA PATTERNS:"
            foreach ($pattern in $formulaDict.Keys | Sort-Object) {
                $info = $formulaDict[$pattern]
                $structure += ""
                $structure += "  Pattern (used $($info.Count)x):"
                $structure += "    Example: $($info.Example)"
                $structure += "    Cells: $($info.Cells -join ', ')$(if ($info.Count -gt 5) { '...' })"
                
                $formulas += ""
                $formulas += "Pattern (used $($info.Count)x):"
                $formulas += "  Example: $($info.Example)"
                $formulas += "  Cells: $($info.Cells -join ', ')$(if ($info.Count -gt 5) { '...' })"
            }
        } else {
            $structure += "  (No formulas found)"
        }
        $structure += ""
        
        # ============================================
        # SAMPLE DATA
        # ============================================
        $structure += "-" * 40
        $structure += "SAMPLE DATA (First $MAX_SAMPLE_ROWS rows)"
        $structure += "-" * 40
        
        $sampleRows = [Math]::Min($rowCount, $MAX_SAMPLE_ROWS)
        for ($row = 1; $row -le $sampleRows; $row++) {
            $rowData = @()
            for ($col = 1; $col -le [Math]::Min($colCount, $MAX_SAMPLE_COLS); $col++) {
                $val = $ws.Cells[$row, $col].Value
                if ($null -eq $val) { $val = "" }
                $val = "$val".Trim()
                if ($val.Length -gt 40) { $val = $val.Substring(0, 37) + "..." }
                $rowData += $val
            }
            $structure += "Row $row : $($rowData -join ' | ')"
        }
        
        $structure | Out-File $structureFile -Encoding UTF8
        
        # ============================================
        # CSV EXPORT
        # ============================================
        $csvFile = Join-Path $outputFolder "$($safeSheetName)_Data.csv"
        Write-Host "  Exporting to CSV..." -ForegroundColor Gray
        
        try {
            # Try reading with headers first, fall back to no headers
            $data = $null
            try {
                $data = Import-Excel -Path $file.FullName -WorksheetName $sheetName -ErrorAction Stop
            } catch {
                # If header detection fails, try without headers
                try {
                    $data = Import-Excel -Path $file.FullName -WorksheetName $sheetName -NoHeader -ErrorAction Stop
                } catch {
                    throw
                }
            }
            
            if ($data.Count -gt $MAX_CSV_ROWS) {
                $data = $data | Select-Object -First $MAX_CSV_ROWS
                Write-Host "  Note: CSV limited to first $MAX_CSV_ROWS rows (sheet has $($data.Count))" -ForegroundColor Yellow
                $summary += "  CSV Export: First $MAX_CSV_ROWS of $($data.Count) rows"
            }
            
            if ($data) {
                $data | Export-Csv -Path $csvFile -NoTypeInformation -Encoding UTF8
            } else {
                Write-Host "  No data to export" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  CSV export failed: $_" -ForegroundColor Red
            $summary += "  CSV Export: FAILED - $($_.Exception.Message)"
        }
        
        $summary += "  Formulas: $formulaCount"
        $summary += "  Tables: $($ws.Tables.Count)"
    }
    
    # Write summary and formulas files
    $summary | Out-File $summaryFile -Encoding UTF8
    $formulas | Out-File $formulasFile -Encoding UTF8
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "EXTRACTION COMPLETE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Output folder: $outputFolder" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Files created:" -ForegroundColor White
    Get-ChildItem $outputFolder | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: Failed to process workbook" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} finally {
    # Cleanup
    if ($pkg) {
        Close-ExcelPackage $pkg -NoSave
    }
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Cyan
Read-Host
exit 0
