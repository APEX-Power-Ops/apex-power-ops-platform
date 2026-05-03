param(
    [ValidateSet('open', 'close', 'status')]
    [string]$Action = 'open',

    [int]$LocalPort = 5231,

    [string]$HostAlias = 'olares@100.64.0.1',

    [string]$RemoteHost = '127.0.0.1',

    [int]$RemotePort = 5230
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateFile = Join-Path $env:TEMP 'apex-personal-notes-tunnel.json'
$knownHostsFile = Join-Path $env:TEMP 'olares_mesh_known_hosts'
$localUrl = "http://127.0.0.1:$LocalPort"

function Get-State {
    if (-not (Test-Path $stateFile)) {
        return $null
    }

    try {
        return Get-Content $stateFile -Raw | ConvertFrom-Json
    }
    catch {
        Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
        return $null
    }
}

function Save-State([int]$ProcessId, [int]$Port) {
    [pscustomobject]@{
        ProcessId = $ProcessId
        LocalPort = $Port
        LocalUrl = "http://127.0.0.1:$Port"
        CreatedAt = (Get-Date).ToString('o')
    } | ConvertTo-Json | Set-Content -Path $stateFile
}

function Clear-State {
    if (Test-Path $stateFile) {
        Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
    }
}

function Test-LocalUrl([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 5
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Get-RunningTunnel {
    $state = Get-State
    if ($null -eq $state) {
        return $null
    }

    $process = Get-Process -Id $state.ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Clear-State
        return $null
    }

    return [pscustomobject]@{
        Process = $process
        Port = [int]$state.LocalPort
        Url = [string]$state.LocalUrl
    }
}

switch ($Action) {
    'open' {
        $runningTunnel = Get-RunningTunnel
        if ($null -ne $runningTunnel -and (Test-LocalUrl $runningTunnel.Url)) {
            Start-Process $runningTunnel.Url | Out-Null
            Write-Host "Personal Notes is already available at $($runningTunnel.Url)"
            Write-Host "To stop it later, run: pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-access.ps1 -Action close"
            exit 0
        }

        if ($null -ne $runningTunnel) {
            Stop-Process -Id $runningTunnel.Process.Id -Force -ErrorAction SilentlyContinue
            Clear-State
        }

        $process = Start-Process -FilePath 'ssh' -ArgumentList @(
            '-o', 'BatchMode=yes',
            '-o', 'ExitOnForwardFailure=yes',
            '-o', 'ServerAliveInterval=30',
            '-o', 'ServerAliveCountMax=3',
            '-o', 'TCPKeepAlive=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', "UserKnownHostsFile=$knownHostsFile",
            '-N',
            '-L', ("{0}:{1}:{2}" -f $LocalPort, $RemoteHost, $RemotePort),
            $HostAlias
        ) -PassThru

        Save-State -ProcessId $process.Id -Port $LocalPort

        $ready = $false
        for ($attempt = 0; $attempt -lt 10; $attempt++) {
            Start-Sleep -Milliseconds 750
            if (Test-LocalUrl $localUrl) {
                $ready = $true
                break
            }

            if ($process.HasExited) {
                break
            }
        }

        if (-not $ready) {
            if (-not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
            Clear-State
            Write-Error "The Personal Notes tunnel did not become ready on $localUrl"
            exit 1
        }

        Start-Process $localUrl | Out-Null
        Write-Host "Personal Notes is ready at $localUrl"
        Write-Host "A local tunnel process was started for you."
        Write-Host "To stop it later, run: pwsh -NoProfile -File .\apex-power-ops-platform\infra\private\personal-notes-access.ps1 -Action close"
        exit 0
    }

    'close' {
        $runningTunnel = Get-RunningTunnel
        if ($null -eq $runningTunnel) {
            Write-Host 'No Personal Notes tunnel is currently recorded as running.'
            exit 0
        }

        Stop-Process -Id $runningTunnel.Process.Id -Force -ErrorAction SilentlyContinue
        Clear-State
        Write-Host 'Personal Notes tunnel stopped.'
        exit 0
    }

    'status' {
        $runningTunnel = Get-RunningTunnel
        if ($null -eq $runningTunnel) {
            Write-Host 'Personal Notes tunnel: not running.'
            exit 0
        }

        $httpState = if (Test-LocalUrl $runningTunnel.Url) { 'HTTP 200' } else { 'not responding' }
        Write-Host "Personal Notes tunnel: running"
        Write-Host "Local URL: $($runningTunnel.Url)"
        Write-Host "Tunnel process id: $($runningTunnel.Process.Id)"
        Write-Host "Local probe: $httpState"
        exit 0
    }
}