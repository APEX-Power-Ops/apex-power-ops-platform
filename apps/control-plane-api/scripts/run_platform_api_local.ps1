param(
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

Write-Host "[NON-OPS] This Windows launcher runs control-plane-api WITHOUT Infisical-sourced OPS_*." -ForegroundColor Yellow
Write-Host "[NON-OPS] The ops intake/recognition routers will NOT mount unless OPS_* are already in this Windows environment." -ForegroundColor Yellow
Write-Host "[NON-OPS] For ops-router work use the host launcher apps/control-plane-api/scripts/run_platform_api_local.sh (Infisical-backed) under the dev-residency workspace." -ForegroundColor Yellow

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

& ".\.venv\Scripts\python.exe" -m uvicorn main:app --app-dir apps/control-plane-api --host 0.0.0.0 --port 8010