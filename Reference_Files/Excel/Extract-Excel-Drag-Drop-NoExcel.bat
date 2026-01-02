@echo off
REM ========================================
REM Excel Structure Extractor (No Excel Required)
REM ========================================
REM Drag and drop any .xlsx or .xlsm file onto this .bat file
REM Uses ImportExcel PowerShell module instead of Excel COM
REM Output goes to a folder next to the Excel file
REM ========================================

if "%~1"=="" (
    echo.
    echo  ==========================================
    echo   Excel Structure Extractor (No Excel)
    echo  ==========================================
    echo.
    echo   Usage: Drag and drop an Excel file onto this .bat file
    echo.
    echo   Supported: .xlsx, .xlsm
    echo.
    echo   Requirements: ImportExcel PowerShell module
    echo   Install: Install-Module ImportExcel -Scope CurrentUser
    echo.
    echo   Output: Creates a folder with extracted content including:
    echo     - Summary of workbook structure
    echo     - All formulas by sheet
    echo     - Named ranges
    echo     - Data as CSV files
    echo.
    pause
    exit /b
)

REM Check if PowerShell script exists
if not exist "%~dp0Extract-ExcelStructure-NoExcel.ps1" (
    echo.
    echo ERROR: Extract-ExcelStructure-NoExcel.ps1 not found in the same directory
    echo.
    pause
    exit /b 1
)

REM Validate file extension
set "ext=%~x1"
if /i not "%ext%"==".xlsx" if /i not "%ext%"==".xlsm" (
    echo.
    echo ERROR: File must be .xlsx or .xlsm
    echo        Received: %~nx1
    echo.
    pause
    exit /b 1
)

echo.
echo Processing: %~nx1
echo.

REM Execute PowerShell script and capture exit code
powershell -ExecutionPolicy Bypass -File "%~dp0Extract-ExcelStructure-NoExcel.ps1" "%~1"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PowerShell script failed with exit code %errorlevel%
    echo.
    pause
    exit /b %errorlevel%
)
