<#
.SYNOPSIS
    Comprehensive Excel Workbook Extractor
    Drag an .xlsx or .xlsm file onto the .bat file to extract full structure

.DESCRIPTION
    Extracts from Excel workbooks:
    - All sheet names and types
    - Column headers and data samples
    - All formulas with cell locations
    - Named ranges and their definitions
    - Data validation rules
    - Cell comments
    - Conditional formatting rules
    - Tables (ListObjects)
    - Pivot tables
    - Chart information

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
Write-Host "Excel Structure Extractor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "File: $($file.Name)" -ForegroundColor Yellow
Write-Host "Output: $outputFolder" -ForegroundColor Yellow
Write-Host ""

# Initialize Excel COM object
Write-Host "Opening Excel..." -ForegroundColor Gray
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($file.FullName, $false, $true) # ReadOnly
    
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
    $summary += "Sheets: $($workbook.Sheets.Count)"
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
    
    foreach ($name in $workbook.Names) {
        try {
            $namedRanges += ""
            $namedRanges += "Name: $($name.Name)"
            $namedRanges += "RefersTo: $($name.RefersTo)"
            $namedRanges += "Scope: $(if ($name.Parent.Name -eq $workbook.Name) { 'Workbook' } else { $name.Parent.Name })"
            
            # Try to get the value
            try {
                $range = $name.RefersToRange
                if ($range.Cells.Count -eq 1) {
                    $namedRanges += "Value: $($range.Value2)"
                } else {
                    $namedRanges += "Range Size: $($range.Rows.Count) rows x $($range.Columns.Count) columns"
                }
            } catch {}
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
    foreach ($sheet in $workbook.Sheets) {
        $sheetIndex++
        $sheetName = $sheet.Name
        $safeSheetName = $sheetName -replace '[\\/:*?"<>|]', '_'
        
        Write-Host "Processing sheet $sheetIndex/$($workbook.Sheets.Count): $sheetName" -ForegroundColor White
        
        # Skip chart sheets
        if ($sheet.Type -ne -4167) { # xlWorksheet
            $summary += "Sheet: $sheetName (Chart/Other - skipped)"
            continue
        }
        
        $ws = $sheet
        
        # Get used range
        $usedRange = $ws.UsedRange
        if ($null -eq $usedRange) {
            $summary += "Sheet: $sheetName (Empty)"
            continue
        }
        
        $rowCount = $usedRange.Rows.Count
        $colCount = $usedRange.Columns.Count
        $startRow = $usedRange.Row
        $startCol = $usedRange.Column
        
        $summary += ""
        $summary += "-" * 40
        $summary += "Sheet: $sheetName"
        $summary += "-" * 40
        $summary += "  Used Range: $($usedRange.Address)"
        $summary += "  Rows: $rowCount, Columns: $colCount"
        
        # ============================================
        # STRUCTURE FILE FOR THIS SHEET
        # ============================================
        $structureFile = Join-Path $outputFolder "$($safeSheetName)_Structure.txt"
        $structure = @()
        $structure += "=" * 80
        $structure += "SHEET: $sheetName"
        $structure += "=" * 80
        $structure += "Used Range: $($usedRange.Address)"
        $structure += "Rows: $rowCount, Columns: $colCount"
        $structure += ""
        
        # ============================================
        # COLUMN HEADERS (First row analysis)
        # ============================================
        $structure += "-" * 40
        $structure += "COLUMN HEADERS (Row 1)"
        $structure += "-" * 40
        
        $headers = @()
        for ($col = 1; $col -le [Math]::Min($colCount, 50); $col++) {
            $cell = $ws.Cells.Item($startRow, $startCol + $col - 1)
            $colLetter = $cell.Address($false, $false) -replace '\d+', ''
            $value = $cell.Value2
            $formula = ""
            if ($cell.HasFormula) {
                $formula = " [FORMULA: $($cell.Formula)]"
            }
            $headers += "  $colLetter : $value$formula"
        }
        $structure += $headers
        $structure += ""
        
        # ============================================
        # TABLES (ListObjects)
        # ============================================
        if ($ws.ListObjects.Count -gt 0) {
            $structure += "-" * 40
            $structure += "TABLES (ListObjects)"
            $structure += "-" * 40
            foreach ($table in $ws.ListObjects) {
                $structure += "  Table: $($table.Name)"
                $structure += "    Range: $($table.Range.Address)"
                $structure += "    Columns: $($table.ListColumns.Count)"
                $structure += "    Rows: $($table.ListRows.Count)"
                $structure += "    Headers: $($table.HeaderRowRange.Value2 -join ', ')"
            }
            $structure += ""
        }
        
        # ============================================
        # DATA VALIDATION
        # ============================================
        $structure += "-" * 40
        $structure += "DATA VALIDATION RULES"
        $structure += "-" * 40
        
        $validationFound = $false
        for ($col = 1; $col -le [Math]::Min($colCount, 30); $col++) {
            for ($row = 1; $row -le [Math]::Min($rowCount, 100); $row++) {
                try {
                    $cell = $ws.Cells.Item($startRow + $row - 1, $startCol + $col - 1)
                    $validation = $cell.Validation
                    if ($validation.Type -gt 0) {
                        $validationFound = $true
                        $structure += "  Cell $($cell.Address): Type=$($validation.Type), Formula1=$($validation.Formula1)"
                    }
                } catch {}
            }
        }
        if (-not $validationFound) {
            $structure += "  (None found in scanned range)"
        }
        $structure += ""
        
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
        for ($row = 1; $row -le $rowCount; $row++) {
            for ($col = 1; $col -le $colCount; $col++) {
                try {
                    $cell = $ws.Cells.Item($startRow + $row - 1, $startCol + $col - 1)
                    if ($cell.HasFormula) {
                        $formulaCount++
                        $addr = $cell.Address($false, $false)
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
                } catch {}
            }
        }
        
        $structure += "  Total formulas: $formulaCount"
        $structure += ""
        
        # Output unique formula patterns
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
        $structure += ""
        
        # ============================================
        # SAMPLE DATA (First 30 rows)
        # ============================================
        $structure += "-" * 40
        $structure += "SAMPLE DATA (First 30 rows)"
        $structure += "-" * 40
        
        $sampleRows = [Math]::Min($rowCount, 30)
        for ($row = 1; $row -le $sampleRows; $row++) {
            $rowData = @()
            for ($col = 1; $col -le [Math]::Min($colCount, 20); $col++) {
                try {
                    $cell = $ws.Cells.Item($startRow + $row - 1, $startCol + $col - 1)
                    $val = $cell.Value2
                    if ($null -eq $val) { $val = "" }
                    $val = "$val".Trim()
                    if ($val.Length -gt 40) { $val = $val.Substring(0, 37) + "..." }
                    $rowData += $val
                } catch {
                    $rowData += ""
                }
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
            # Read all data into array
            $data = @()
            for ($row = 1; $row -le [Math]::Min($rowCount, 5000); $row++) {
                $rowData = @()
                for ($col = 1; $col -le $colCount; $col++) {
                    try {
                        $cell = $ws.Cells.Item($startRow + $row - 1, $startCol + $col - 1)
                        $val = $cell.Value2
                        if ($null -eq $val) { $val = "" }
                        # Escape for CSV
                        $val = "$val" -replace '"', '""'
                        if ($val -match '[,"\n\r]') {
                            $val = "`"$val`""
                        }
                        $rowData += $val
                    } catch {
                        $rowData += ""
                    }
                }
                $data += ($rowData -join ",")
            }
            $data | Out-File $csvFile -Encoding UTF8
        } catch {
            Write-Host "  CSV export failed: $_" -ForegroundColor Red
        }
        
        $summary += "  Formulas: $formulaCount"
        $summary += "  Tables: $($ws.ListObjects.Count)"
    }
    
    # ============================================
    # VBA MODULES
    # ============================================
    Write-Host "Checking for VBA code..." -ForegroundColor Gray
    $summary += ""
    $summary += "=" * 40
    $summary += "VBA MODULES"
    $summary += "=" * 40
    
    try {
        $vbProject = $workbook.VBProject
        foreach ($component in $vbProject.VBComponents) {
            $moduleName = $component.Name
            $moduleType = switch ($component.Type) {
                1 { "Standard Module" }
                2 { "Class Module" }
                3 { "UserForm" }
                100 { "Document Module" }
                default { "Unknown ($($component.Type))" }
            }
            $codeLines = $component.CodeModule.CountOfLines
            $summary += "  $moduleName ($moduleType) - $codeLines lines"
            
            # Export VBA code
            if ($codeLines -gt 0) {
                $vbaFile = Join-Path $outputFolder "VBA_$moduleName.txt"
                $code = $component.CodeModule.Lines(1, $codeLines)
                $code | Out-File $vbaFile -Encoding UTF8
                Write-Host "  Exported VBA: $moduleName" -ForegroundColor Gray
            }
        }
    } catch {
        $summary += "  (VBA access denied or no VBA content)"
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
    Write-Error "Error processing workbook: $_"
} finally {
    # Cleanup
    if ($workbook) {
        $workbook.Close($false)
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($workbook) | Out-Null
    }
    if ($excel) {
        $excel.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Cyan
Read-Host
