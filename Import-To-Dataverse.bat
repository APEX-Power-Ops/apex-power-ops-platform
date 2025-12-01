@echo off
REM ============================================================
REM RESA Power - Import Estimator JSON to Dataverse
REM ============================================================
REM 
REM USAGE: Drag and drop a JSON file onto this batch file, 
REM        OR run it and paste the file path when prompted.
REM
REM ============================================================

title RESA Power - Dataverse Import Tool

echo.
echo ============================================================
echo    RESA POWER - DATAVERSE IMPORT TOOL
echo ============================================================
echo.

REM Check if a file was provided as argument
if "%~1"=="" (
    echo No file was provided.
    echo.
    echo Please drag and drop a JSON file onto this batch file,
    echo or enter the full path to the JSON file below:
    echo.
    set /p JSONFILE="JSON File Path: "
) else (
    set JSONFILE=%~1
)

REM Check if file exists
if not exist "%JSONFILE%" (
    echo.
    echo ERROR: File not found: %JSONFILE%
    echo.
    pause
    exit /b 1
)

echo.
echo Importing: %JSONFILE%
echo.
echo Starting import process...
echo.

REM Change to the MCP server directory and run the import
cd /d "%~dp0"
cd MCP_Servers\resa-dataverse-mcp

REM Run Node.js import script
node import-estimator.js "%JSONFILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo    IMPORT COMPLETED SUCCESSFULLY!
    echo ============================================================
    echo.
) else (
    echo.
    echo ============================================================
    echo    IMPORT FAILED - See error above
    echo ============================================================
    echo.
)

pause
