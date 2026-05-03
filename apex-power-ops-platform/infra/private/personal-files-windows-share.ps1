param(
    [ValidateSet('map', 'remap', 'status', 'unmap')]
    [string]$Action = 'status',

    [ValidatePattern('^[A-Z]$')]
    [string]$DriveLetter = 'P',

    [string]$HostAlias = '',

    [string]$BridgeScriptPath = ''
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$resolvedBridgeScript = if ($BridgeScriptPath) {
    (Resolve-Path -Path $BridgeScriptPath -ErrorAction Stop).Path
}
else {
    Join-Path $scriptRoot 'run-personal-files-samba-bridge-remote.ps1'
}

function Invoke-BridgeAction {
    param(
        [string]$BridgeAction
    )

    $arguments = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $resolvedBridgeScript,
        '-Action', $BridgeAction
    )

    if ($HostAlias) {
        $arguments += @('-HostAlias', $HostAlias)
    }

    $output = & pwsh @arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw (($output | Out-String).Trim())
    }

    return ($output | Out-String)
}

function Get-CredentialMap {
    $output = Invoke-BridgeAction -BridgeAction 'credentials'
    $map = @{}

    foreach ($line in ($output -split "`r?`n")) {
        if ($line -match '^(?<key>[a-z_]+):\s*(?<value>.*)$') {
            $map[$matches['key']] = $matches['value']
        }
    }

    $requiredKeys = @('server', 'share', 'username', 'password')
    $missing = $requiredKeys | Where-Object { -not $map.ContainsKey($_) }
    if ($missing.Count -gt 0) {
        throw "Missing bridge credential fields: $($missing -join ', ')"
    }

    return $map
}

function Remove-ExistingMapping {
    param(
        [string]$LocalPath,
        [string]$RemotePath
    )

    try {
        Remove-SmbMapping -LocalPath $LocalPath -Force -UpdateProfile -ErrorAction SilentlyContinue | Out-Null
    }
    catch {
    }

    try {
        Remove-PSDrive -Name $LocalPath.TrimEnd(':') -Force -ErrorAction SilentlyContinue
    }
    catch {
    }

    & cmd.exe /c "net use $LocalPath /delete /y" *> $null
    & cmd.exe /c "net use $RemotePath /delete /y" *> $null
}

function Try-NewPsDriveMapping {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$UserName,
        [string]$Password
    )

    $securePassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
    $credential = [pscredential]::new($UserName, $securePassword)
    $driveName = $LocalPath.TrimEnd(':')

    New-PSDrive -Name $driveName -PSProvider FileSystem -Root $RemotePath -Persist -Credential $credential -ErrorAction Stop | Out-Null
}

function Try-NetUseMapping {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$UserName,
        [string]$Password
    )

    $arguments = @(
        '/c',
        'net',
        'use',
        $LocalPath,
        $RemotePath,
        $Password,
        "/user:$UserName",
        '/persistent:yes'
    )

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $process = Start-Process -FilePath 'cmd.exe' -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        $stdout = if (Test-Path $stdoutFile) { [System.IO.File]::ReadAllText($stdoutFile) } else { '' }
        $stderr = if (Test-Path $stderrFile) { [System.IO.File]::ReadAllText($stderrFile) } else { '' }

        if ($process.ExitCode -ne 0) {
            $detail = ($stderr.Trim(), $stdout.Trim() | Where-Object { $_ }) -join [Environment]::NewLine
            if (-not $detail) {
                $detail = 'net use returned a non-zero exit code.'
            }
            throw $detail
        }
    }
    finally {
        foreach ($path in @($stdoutFile, $stderrFile)) {
            if (Test-Path $path) {
                Remove-Item $path -Force
            }
        }
    }
}

function New-PersonalFilesMapping {
    param(
        [hashtable]$CredentialMap,
        [string]$LocalPath
    )

    $server = $CredentialMap['server']
    $share = $CredentialMap['share']
    $username = $CredentialMap['username']
    $password = $CredentialMap['password']
    $remotePath = "\\$server\$share"

    if ($CredentialMap.ContainsKey('windows_direct_supported') -and $CredentialMap['windows_direct_supported'] -ne 'yes') {
        $note = if ($CredentialMap.ContainsKey('windows_direct_note')) { $CredentialMap['windows_direct_note'] } else { '' }
        if (-not $note) {
            $note = 'Direct Windows SMB mapping to the Olares host bridge is not supported on this node.'
        }

        throw $note
    }

    if (-not (Get-Command New-SmbMapping -ErrorAction SilentlyContinue)) {
        throw 'New-SmbMapping is not available on this Windows client.'
    }

    $reachability = Test-NetConnection -ComputerName $server -Port 445 -WarningAction SilentlyContinue
    if (-not $reachability.TcpTestSucceeded) {
        throw "SMB port 445 is not reachable on $server."
    }

    Remove-ExistingMapping -LocalPath $LocalPath -RemotePath $remotePath

    $candidates = @(
        $username,
        "$server\$username",
        "OLARES\$username",
        "olares\$username",
        ".\$username",
        "WORKGROUP\$username"
    ) | Select-Object -Unique

    $lastErrorText = ''
    foreach ($candidate in $candidates) {
        try {
            New-SmbMapping -LocalPath $LocalPath -RemotePath $remotePath -UserName $candidate -Password $password -Persistent $true -ErrorAction Stop | Out-Null

            return [pscustomobject]@{
                LocalPath = $LocalPath
                RemotePath = $remotePath
                UserName = $candidate
            }
        }
        catch {
            $lastErrorText = $_.Exception.Message
        }

        try {
            Try-NewPsDriveMapping -LocalPath $LocalPath -RemotePath $remotePath -UserName $candidate -Password $password

            return [pscustomobject]@{
                LocalPath = $LocalPath
                RemotePath = $remotePath
                UserName = $candidate
            }
        }
        catch {
            $lastErrorText = $_.Exception.Message
        }

        try {
            Try-NetUseMapping -LocalPath $LocalPath -RemotePath $remotePath -UserName $candidate -Password $password

            return [pscustomobject]@{
                LocalPath = $LocalPath
                RemotePath = $remotePath
                UserName = $candidate
            }
        }
        catch {
            $lastErrorText = $_.Exception.Message
        }
    }

    throw "Failed to map $remotePath. Last error: $lastErrorText"
}

function Get-MappingStatus {
    param(
        [string]$LocalPath
    )

    $mapping = Get-SmbMapping | Where-Object { $_.LocalPath -eq $LocalPath } | Select-Object -First 1
    if (-not $mapping) {
        Write-Output "Personal Files Windows mapping: not mapped ($LocalPath)"
        return
    }

    Write-Output 'Personal Files Windows mapping: mapped'
    Write-Output "  local_path: $($mapping.LocalPath)"
    Write-Output "  remote_path: $($mapping.RemotePath)"
    Write-Output "  username: $($mapping.UserName)"
    Write-Output "  status: $($mapping.Status)"

    if (Test-Path "$LocalPath\") {
        Write-Output '  sample_entries:'
        Get-ChildItem "$LocalPath\" | Select-Object -First 10 Name, Mode | ForEach-Object {
            Write-Output "    $($_.Mode) $($_.Name)"
        }
    }
}

$localPath = "${DriveLetter}:"

switch ($Action) {
    'map' {
        Invoke-BridgeAction -BridgeAction 'setup' | Out-Null
        $credentialMap = Get-CredentialMap
        $result = New-PersonalFilesMapping -CredentialMap $credentialMap -LocalPath $localPath
        Write-Output "Mapped Personal Files share:"
        Write-Output "  local_path: $($result.LocalPath)"
        Write-Output "  remote_path: $($result.RemotePath)"
        Write-Output "  username: $($result.UserName)"
        if (Test-Path "$localPath\") {
            Get-ChildItem "$localPath\" | Select-Object -First 10 Name, Mode
        }
        exit 0
    }
    'remap' {
        $credentialMap = Get-CredentialMap
        $result = New-PersonalFilesMapping -CredentialMap $credentialMap -LocalPath $localPath
        Write-Output "Remapped Personal Files share:"
        Write-Output "  local_path: $($result.LocalPath)"
        Write-Output "  remote_path: $($result.RemotePath)"
        Write-Output "  username: $($result.UserName)"
        if (Test-Path "$localPath\") {
            Get-ChildItem "$localPath\" | Select-Object -First 10 Name, Mode
        }
        exit 0
    }
    'status' {
        Get-MappingStatus -LocalPath $localPath
        exit 0
    }
    'unmap' {
        $credentialMap = Get-CredentialMap
        Remove-ExistingMapping -LocalPath $localPath -RemotePath ("\\{0}\{1}" -f $credentialMap['server'], $credentialMap['share'])
        Write-Output "Removed Personal Files mapping from $localPath"
        exit 0
    }
}