@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "REPO_ROOT=%%~fI"
set "PACKAGE_SRC=%REPO_ROOT%\packages\power-test-converters\src"

if defined PTM_DTAX_ROOT (
    set "REPO_ROOT=%PTM_DTAX_ROOT%"
    set "PACKAGE_SRC=%PTM_DTAX_ROOT%\packages\power-test-converters\src"
)

if not exist "%PACKAGE_SRC%\ptm_to_dtax.py" (
    echo ERROR: Could not find the PTM to DTAx converter package.
    echo Expected: "%PACKAGE_SRC%"
    echo If this batch file was copied outside the package folder, set PTM_DTAX_ROOT.
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Drag one or more .ptm files onto this batch file.
    echo.
    echo Output files are written beside each PTM as:
    echo   source-name-converted.dtax
    pause
    exit /b 2
)

if defined PTM_DTAX_PYTHON (
    set "PYTHON_EXE=%PTM_DTAX_PYTHON%"
) else (
    set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
    if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
)
set "PYTHONPATH=%PACKAGE_SRC%;%PYTHONPATH%"
set "FAILED=0"
set "TEMPLATE_PATH="
if defined DTAX_TEMPLATE (
    if exist "%DTAX_TEMPLATE%" set "TEMPLATE_PATH=%DTAX_TEMPLATE%"
)
if "%TEMPLATE_PATH%"=="" (
    if exist "%SCRIPT_DIR%doble-template.dtax" set "TEMPLATE_PATH=%SCRIPT_DIR%doble-template.dtax"
)
if "%TEMPLATE_PATH%"=="" (
    if exist "%USERPROFILE%\Desktop\Blank_X2.dtax" set "TEMPLATE_PATH=%USERPROFILE%\Desktop\Blank_X2.dtax"
)
if "%TEMPLATE_PATH%"=="" (
    echo WARNING: No Doble template was found.
    echo Doble software may reject the minimal generated dtax as incomplete.
    echo For import use, set DTAX_TEMPLATE or place doble-template.dtax beside this batch file.
) else (
    echo Using Doble template:
    echo   "%TEMPLATE_PATH%"
)

:convert_next
if "%~1"=="" goto done

if /I not "%~x1"==".ptm" (
    echo SKIP: "%~1" is not a .ptm file.
    set "FAILED=1"
    goto shift_next
)

if not exist "%~1" (
    echo ERROR: File not found: "%~1"
    set "FAILED=1"
    goto shift_next
)

set "OUTPUT_PATH=%~dpn1-converted.dtax"
echo.
echo Converting:
echo   "%~1"
echo To:
echo   "%OUTPUT_PATH%"

if "%TEMPLATE_PATH%"=="" (
    "%PYTHON_EXE%" "%PACKAGE_SRC%\ptm_to_dtax.py" "%~1" "%OUTPUT_PATH%" --overwrite
) else (
    "%PYTHON_EXE%" "%PACKAGE_SRC%\ptm_to_dtax.py" "%~1" "%OUTPUT_PATH%" --overwrite --template-dtax "%TEMPLATE_PATH%"
)
if errorlevel 1 (
    echo FAILED: "%~1"
    set "FAILED=1"
) else (
    echo WROTE: "%OUTPUT_PATH%"
)

:shift_next
shift
goto convert_next

:done
echo.
if "%FAILED%"=="0" (
    echo Done.
) else (
    echo Done with one or more skipped or failed files.
)
pause
exit /b %FAILED%
