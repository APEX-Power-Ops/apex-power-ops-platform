param(
    [ValidateSet('open-web', 'close-web', 'open-rdp', 'close-rdp', 'status')]
    [string]$Action = 'open-web',

    [int]$LocalWebPort = 8007,

    [int]$LocalRdpPort = 3391,

    [string]$HostAlias = 'olares@100.64.0.1'
)

$knownHostsFile = Join-Path $env:TEMP 'olares_mesh_known_hosts'
$localUrl = "http://127.0.0.1:$LocalWebPort"
$rdpTarget = "127.0.0.1:$LocalRdpPort"

function Get-StateFile([string]$Kind) {
    switch ($Kind) {
        'web' { return Join-Path $env:TEMP 'apex-personal-windows-web-tunnel.json' }
        'rdp' { return Join-Path $env:TEMP 'apex-personal-windows-rdp-tunnel.json' }
        default { throw "Unsupported tunnel kind: $Kind" }
    }
}

function Get-State([string]$Kind) {
    $stateFile = Get-StateFile $Kind
    if (-not (Test-Path $stateFile)) { return $null }
    try { return Get-Content $stateFile -Raw | ConvertFrom-Json }
    catch {
        Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
        return $null
    }
}

function Save-State([string]$Kind, [int]$ProcessId, [int]$Port, [string]$Endpoint) {
    $stateFile = Get-StateFile $Kind
    [pscustomobject]@{
        Kind = $Kind
        ProcessId = $ProcessId
        LocalPort = $Port
        Endpoint = $Endpoint
        CreatedAt = (Get-Date).ToString('o')
    } | ConvertTo-Json | Set-Content -Path $stateFile
}

function Clear-State([string]$Kind) {
    $stateFile = Get-StateFile $Kind
    if (Test-Path $stateFile) {
        Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
    }
}

function Test-LocalUrl([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 5
        return $response.StatusCode -eq 200
    }
    catch { return $false }
}

function Test-TcpPort([string]$HostName, [int]$Port) {
    $client = $null
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(5000, $false)) {
            $client.Close()
            return $false
        }
        $client.EndConnect($async)
        $client.Close()
        return $true
    }
    catch {
        if ($null -ne $client) {
            $client.Close()
        }
        return $false
    }
}

function Get-RunningTunnel([string]$Kind) {
    $state = Get-State $Kind
    if ($null -eq $state) { return $null }
    $process = Get-Process -Id $state.ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Clear-State $Kind
        return $null
    }
    $endpoint = [string]$state.Endpoint
    if ([string]::IsNullOrWhiteSpace($endpoint)) {
        if ($Kind -eq 'web') {
            $endpoint = "http://127.0.0.1:$($state.LocalPort)"
        }
        else {
            $endpoint = "127.0.0.1:$($state.LocalPort)"
        }
    }

    return [pscustomobject]@{
        Kind = [string]$state.Kind
        Process = $process
        Port = [int]$state.LocalPort
        Endpoint = $endpoint
    }
}

function Start-SshTunnel([string]$LocalSpec) {
    return Start-Process -FilePath 'ssh' -ArgumentList @(
        '-o', 'BatchMode=yes',
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'ServerAliveInterval=30',
        '-o', 'ServerAliveCountMax=3',
        '-o', 'TCPKeepAlive=yes',
        '-o', 'StrictHostKeyChecking=accept-new',
        '-o', "UserKnownHostsFile=$knownHostsFile",
        '-N',
        '-L', $LocalSpec,
        $HostAlias
    ) -PassThru
}

function Open-WebTunnel {
    $runningTunnel = Get-RunningTunnel 'web'
    if ($null -ne $runningTunnel -and (Test-LocalUrl $runningTunnel.Endpoint)) {
        Start-Process $runningTunnel.Endpoint | Out-Null
        Write-Host "Windows Lab web viewer is already available at $($runningTunnel.Endpoint)"
        exit 0
    }

    if ($null -ne $runningTunnel) {
        Stop-Process -Id $runningTunnel.Process.Id -Force -ErrorAction SilentlyContinue
        Clear-State 'web'
    }

    $process = Start-SshTunnel ("{0}:127.0.0.1:8006" -f $LocalWebPort)

    Save-State -Kind 'web' -ProcessId $process.Id -Port $LocalWebPort -Endpoint $localUrl

    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 1000
        if (Test-LocalUrl $localUrl) { $ready = $true; break }
        if ($process.HasExited) { break }
    }

    if (-not $ready) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        Clear-State 'web'
        Write-Error "The Windows Lab web viewer tunnel did not become ready on $localUrl"
        exit 1
    }

    Start-Process $localUrl | Out-Null
    Write-Host "Windows Lab web viewer is ready at $localUrl"
    exit 0
}

function Open-RdpTunnel {
    $runningTunnel = Get-RunningTunnel 'rdp'
    if ($null -ne $runningTunnel -and (Test-TcpPort -HostName '127.0.0.1' -Port $LocalRdpPort)) {
        Start-Process 'mstsc.exe' -ArgumentList "/v:$($runningTunnel.Endpoint)" | Out-Null
        Write-Host "Windows Lab RDP tunnel is already available at $($runningTunnel.Endpoint)"
        exit 0
    }

    if ($null -ne $runningTunnel) {
        Stop-Process -Id $runningTunnel.Process.Id -Force -ErrorAction SilentlyContinue
        Clear-State 'rdp'
    }

    $process = Start-SshTunnel ("{0}:127.0.0.1:3390" -f $LocalRdpPort)

    Save-State -Kind 'rdp' -ProcessId $process.Id -Port $LocalRdpPort -Endpoint $rdpTarget

    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 1000
        if (Test-TcpPort -HostName '127.0.0.1' -Port $LocalRdpPort) { $ready = $true; break }
        if ($process.HasExited) { break }
    }

    if (-not $ready) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        Clear-State 'rdp'
        Write-Error "The Windows Lab RDP tunnel did not become ready on $rdpTarget"
        exit 1
    }

    Start-Process 'mstsc.exe' -ArgumentList "/v:$rdpTarget" | Out-Null
    Write-Host "Windows Lab RDP tunnel is ready at $rdpTarget"
    exit 0
}

function Close-Tunnel([string]$Kind, [string]$Label) {
    $runningTunnel = Get-RunningTunnel $Kind
    if ($null -eq $runningTunnel) {
        Write-Host "No Windows Lab $Label tunnel is currently recorded as running."
        exit 0
    }
    Stop-Process -Id $runningTunnel.Process.Id -Force -ErrorAction SilentlyContinue
    Clear-State $Kind
    Write-Host "Windows Lab $Label tunnel stopped."
    exit 0
}

switch ($Action) {
    'open-web' { Open-WebTunnel }
    'close-web' { Close-Tunnel -Kind 'web' -Label 'web' }
    'open-rdp' { Open-RdpTunnel }
    'close-rdp' { Close-Tunnel -Kind 'rdp' -Label 'RDP' }
    'status' {
        $webTunnel = Get-RunningTunnel 'web'
        if ($null -eq $webTunnel) {
            Write-Host 'Windows Lab web tunnel: not running.'
        }
        else {
            $httpState = if (Test-LocalUrl $webTunnel.Endpoint) { 'HTTP ready' } else { 'not responding yet' }
            Write-Host 'Windows Lab web tunnel: running'
            Write-Host "Local URL: $($webTunnel.Endpoint)"
            Write-Host "Tunnel process id: $($webTunnel.Process.Id)"
            Write-Host "Local probe: $httpState"
        }

        Write-Host ''

        $rdpTunnel = Get-RunningTunnel 'rdp'
        if ($null -eq $rdpTunnel) {
            Write-Host 'Windows Lab RDP tunnel: not running.'
        }
        else {
            $rdpState = if (Test-TcpPort -HostName '127.0.0.1' -Port $rdpTunnel.Port) { 'TCP ready' } else { 'not responding yet' }
            Write-Host 'Windows Lab RDP tunnel: running'
            Write-Host "Local target: $($rdpTunnel.Endpoint)"
            Write-Host "Tunnel process id: $($rdpTunnel.Process.Id)"
            Write-Host "Local probe: $rdpState"
        }
        exit 0
    }
}
