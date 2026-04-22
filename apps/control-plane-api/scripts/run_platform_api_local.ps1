param(
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$appDir = Join-Path $repoRoot 'apps/control-plane-api'
$subtreePython = Join-Path $repoRoot 'apex-power-ops-platform/.venv/Scripts/python.exe'
$rootPython = Join-Path $repoRoot '.venv/Scripts/python.exe'

if ($env:APEX_PLATFORM_PYTHON) {
    $python = $env:APEX_PLATFORM_PYTHON
} elseif (Test-Path $subtreePython) {
    $python = $subtreePython
} elseif (Test-Path $rootPython) {
    $python = $rootPython
} else {
    $python = 'python'
}

if (-not (Test-Path $appDir)) {
    Write-Error "apps/control-plane-api is not present under the parent repo root."
    exit 1
}

$listener = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    if (-not $Restart) {
        Write-Error "Port 8010 is already in use. Use Restart platform API local to replace the existing control-plane host."
        exit 1
    }

    Stop-Process -Id $listener.OwningProcess -Force
    Wait-Process -Id $listener.OwningProcess -Timeout 5 -ErrorAction SilentlyContinue

    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        $listener = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $listener) {
            break
        }

        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)

    if ($listener) {
        Write-Error "Port 8010 is still in use after stopping the previous control-plane host."
        exit 1
    }
}

& $python -m uvicorn main:app --app-dir $appDir --host 0.0.0.0 --port 8010