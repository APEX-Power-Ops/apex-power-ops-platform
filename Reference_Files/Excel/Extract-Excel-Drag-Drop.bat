@echo off
REM ========================================
REM Excel Structure Extractor
REM ========================================
REM Drag and drop any .xlsx or .xlsm file onto this .bat file
REM It will extract all structure, formulas, data, and VBA code
REM Output goes to a folder next to the Excel file
REM ========================================

if "%~1"=="" (
    echo.
    echo  ==========================================
    echo   Excel Structure Extractor
    echo  ==========================================
    echo.
    echo   Usage: Drag and drop an Excel file onto this .bat file
    echo.
    echo   Supported: .xlsx, .xlsm, .xls
    echo.
    echo   Output: Creates a folder with extracted content including:
    echo     - Summary of workbook structure
    echo     - All formulas by sheet
    echo     - Named ranges
    echo     - Data as CSV files
    echo     - VBA code (if present)
    echo.
    pause
    exit /b
)

echo.
echo Processing: %~nx1
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0Extract-ExcelStructure.ps1" "%~1"
