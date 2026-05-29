param(
    [string]$PythonPath = ".venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$python = Join-Path $repoRoot $PythonPath

if (-not (Test-Path $python)) {
    throw "Python interpreter not found at $python"
}

function Test-ModuleInstalled {
    param(
        [string]$ModuleName
    )

    & $python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)" | Out-Null
    return $LASTEXITCODE -eq 0
}

Push-Location $repoRoot
try {
    if (-not (Test-ModuleInstalled -ModuleName "playwright")) {
        Write-Host "Installing Playwright into repo-local venv..."
        & $python -m pip install playwright
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install Playwright into repo-local venv"
        }
    }

    & $python -c "from playwright.sync_api import sync_playwright; pw = sync_playwright().start(); browser = pw.chromium.launch(headless=True); browser.close(); pw.stop()" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Provisioning Chromium browser binaries for Playwright..."
        & $python -m playwright install chromium
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install Playwright Chromium browser binaries"
        }
    }

    Write-Host "Playwright provisioned for repo-local venv."
}
finally {
    Pop-Location
}