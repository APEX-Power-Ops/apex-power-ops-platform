param(
    [ValidateSet('install', 'uninstall', 'status', 'run-now')]
    [string]$Action = 'status',

    [string]$HostAlias = 'olares@100.64.0.1',

    [ValidateSet('backup', 'restore-drill')]
    [string]$ScheduleProfile = 'backup',

    [string]$UnitBaseName = '',

    [string]$OnCalendar = '',

    [string]$RemoteHostScriptPath = '',

    [string]$Description = '',

    [string]$RandomizedDelaySec = '20m',

    [string]$AccuracySec = '5m',

    [string]$StartLimitIntervalSec = '6h',

    [int]$StartLimitBurst = 2,

    [string]$LogDirectory = '$HOME/apex-logs/personal',

    [string]$LogRotateSize = '5M',

    [int]$LogRotateCount = 8,

    [string]$HostScriptSourcePath = ''
)

$knownHostsFile = Join-Path $env:TEMP 'olares_mesh_known_hosts'
$scriptPath = $MyInvocation.MyCommand.Path
$resolvedHostScript = if ($HostScriptSourcePath) {
    (Resolve-Path -Path $HostScriptSourcePath -ErrorAction Stop).Path
}
else {
    Join-Path (Split-Path -Parent $scriptPath) 'run-personal-notes-offsite-backup-host.sh'
}

function Invoke-RemoteScriptCapture {
    param(
        [string]$ScriptBody
    )

    $normalizedRemoteAction = $ScriptBody -replace "`r`n", "`n"
    $tempScript = [System.IO.Path]::GetTempFileName()
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($tempScript, $normalizedRemoteAction, $utf8NoBom)

    try {
        $process = Start-Process -FilePath 'ssh' -ArgumentList @(
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', "UserKnownHostsFile=$knownHostsFile",
            $HostAlias,
            'bash -s'
        ) -NoNewWindow -Wait -PassThru -RedirectStandardInput $tempScript -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile

        $stdout = if (Test-Path $stdoutFile) { [System.IO.File]::ReadAllText($stdoutFile) } else { '' }
        $stderr = if (Test-Path $stderrFile) { [System.IO.File]::ReadAllText($stderrFile) } else { '' }

        if ($process.ExitCode -ne 0) {
            $detail = ($stderr.Trim(), $stdout.Trim() | Where-Object { $_ }) -join [Environment]::NewLine
            if (-not $detail) {
                $detail = "Remote script failed with exit code $($process.ExitCode)."
            }
            throw $detail
        }

        return [pscustomobject]@{
            StdOut = $stdout
            StdErr = $stderr
        }
    }
    finally {
        foreach ($path in @($tempScript, $stdoutFile, $stderrFile)) {
            if (Test-Path $path) {
                Remove-Item $path -Force
            }
        }
    }
}

function Invoke-RemoteScript {
    param(
        [string]$ScriptBody
    )

    $result = Invoke-RemoteScriptCapture $ScriptBody
    if ($result.StdOut) {
        $text = $result.StdOut.TrimEnd()
        if ($text) {
            Write-Output $text
        }
    }
}

function Expand-RemoteTemplate {
    param(
        [string]$Template,
        [hashtable]$Replacements
    )

    $expanded = $Template
    foreach ($entry in $Replacements.GetEnumerator()) {
        $expanded = $expanded.Replace($entry.Key, $entry.Value)
    }

    return $expanded
}

function Resolve-RemoteHomePath {
    param(
        [string]$Path
    )

    $resolved = $Path.Replace('${HOME}', '/home/olares').Replace('$HOME', '/home/olares')
    if ($resolved -eq '~') {
        return '/home/olares'
    }

    if ($resolved.StartsWith('~/')) {
        return "/home/olares/$($resolved.Substring(2))"
    }

    return $resolved
}

function Get-ScheduleProfileDefaults {
    param(
        [string]$Profile,
        [string]$ScriptDirectory
    )

    switch ($Profile) {
        'backup' {
            return @{
                UnitBaseName = 'apex-personal-notes-offsite-backup'
                OnCalendar = '*-*-* 03:30:00'
                RemoteHostScriptPath = '/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh'
                HostScriptSourcePath = (Join-Path $ScriptDirectory 'run-personal-notes-offsite-backup-host.sh')
                Description = 'APEX Personal Notes Host-Owned Offsite Backup'
            }
        }
        'restore-drill' {
            return @{
                UnitBaseName = 'apex-personal-notes-offsite-restore-drill'
                OnCalendar = 'Sun *-*-* 05:00:00'
                RemoteHostScriptPath = '/home/olares/code/personal/run-personal-notes-offsite-restore-drill-host.sh'
                HostScriptSourcePath = (Join-Path $ScriptDirectory 'run-personal-notes-offsite-restore-drill-host.sh')
                Description = 'APEX Personal Notes Host-Owned Offsite Restore Drill'
            }
        }
    }
}

$profileDefaults = Get-ScheduleProfileDefaults -Profile $ScheduleProfile -ScriptDirectory (Split-Path -Parent $scriptPath)

if (-not $UnitBaseName) {
    $UnitBaseName = $profileDefaults.UnitBaseName
}

if (-not $OnCalendar) {
    $OnCalendar = $profileDefaults.OnCalendar
}

if (-not $RemoteHostScriptPath) {
    $RemoteHostScriptPath = $profileDefaults.RemoteHostScriptPath
}

if (-not $Description) {
    $Description = $profileDefaults.Description
}

if (-not $HostScriptSourcePath) {
    $resolvedHostScript = $profileDefaults.HostScriptSourcePath
}

if (-not (Test-Path $resolvedHostScript)) {
    throw "Host script not found: $resolvedHostScript"
}

$hostScriptContent = [System.IO.File]::ReadAllText($resolvedHostScript).Replace("`r`n", "`n")
$resolvedRemoteHostScriptPath = Resolve-RemoteHomePath $RemoteHostScriptPath
$resolvedLogDirectory = Resolve-RemoteHomePath $LogDirectory
$serviceName = "$UnitBaseName.service"
$timerName = "$UnitBaseName.timer"
$logrotateName = $UnitBaseName
$resolvedLogFile = "$resolvedLogDirectory/$UnitBaseName.log"

$serviceUnit = @"
[Unit]
Description=$Description
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=$StartLimitIntervalSec
StartLimitBurst=$StartLimitBurst

[Service]
Type=oneshot
User=olares
Group=olares
ExecStart=$resolvedRemoteHostScriptPath
WorkingDirectory=/home/olares
NoNewPrivileges=yes
Nice=10
UMask=0077
StandardOutput=append:$resolvedLogFile
StandardError=append:$resolvedLogFile
"@

$timerUnit = @"
[Unit]
Description=$Description Timer

[Timer]
OnCalendar=$OnCalendar
Persistent=true
RandomizedDelaySec=$RandomizedDelaySec
AccuracySec=$AccuracySec
Unit=$serviceName

[Install]
WantedBy=timers.target
"@

$logrotateConfig = @"
$resolvedLogFile {
    weekly
    rotate $LogRotateCount
    size $LogRotateSize
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su olares olares
}
"@

$replacements = @{
    '__REMOTE_HOST_SCRIPT_PATH__' = $resolvedRemoteHostScriptPath
    '__DESCRIPTION__' = $Description
    '__HOST_SCRIPT_CONTENT__' = $hostScriptContent
    '__SERVICE_NAME__' = $serviceName
    '__TIMER_NAME__' = $timerName
    '__LOGROTATE_NAME__' = $logrotateName
    '__RESOLVED_LOG_DIRECTORY__' = $resolvedLogDirectory
    '__RESOLVED_LOG_FILE__' = $resolvedLogFile
    '__SERVICE_UNIT__' = $serviceUnit.Replace("`r`n", "`n")
    '__TIMER_UNIT__' = $timerUnit.Replace("`r`n", "`n")
    '__LOGROTATE_CONFIG__' = $logrotateConfig.Replace("`r`n", "`n")
}

$installScript = Expand-RemoteTemplate -Template @'
set -euo pipefail

mkdir -p "$(dirname "__REMOTE_HOST_SCRIPT_PATH__")"
cat > "__REMOTE_HOST_SCRIPT_PATH__" <<'__APEX_HOST_SCRIPT__'
__HOST_SCRIPT_CONTENT__
__APEX_HOST_SCRIPT__
chmod 700 "__REMOTE_HOST_SCRIPT_PATH__"

sudo install -d -o olares -g olares -m 700 "__RESOLVED_LOG_DIRECTORY__"
sudo touch "__RESOLVED_LOG_FILE__"
sudo chown olares:olares "__RESOLVED_LOG_FILE__"

sudo tee "/etc/systemd/system/__SERVICE_NAME__" >/dev/null <<'__APEX_SERVICE_UNIT__'
__SERVICE_UNIT__
__APEX_SERVICE_UNIT__

sudo tee "/etc/systemd/system/__TIMER_NAME__" >/dev/null <<'__APEX_TIMER_UNIT__'
__TIMER_UNIT__
__APEX_TIMER_UNIT__

sudo tee "/etc/logrotate.d/__LOGROTATE_NAME__" >/dev/null <<'__APEX_LOGROTATE__'
__LOGROTATE_CONFIG__
__APEX_LOGROTATE__

sudo systemctl daemon-reload
sudo systemctl enable --now "__TIMER_NAME__"

echo "Installed service: __SERVICE_NAME__"
echo "Installed timer: __TIMER_NAME__"
echo "Log file: __RESOLVED_LOG_FILE__"
sudo systemctl list-timers "__TIMER_NAME__" --all --no-pager
'@ -Replacements $replacements

$statusScript = Expand-RemoteTemplate -Template @'
set -euo pipefail

if ! sudo test -f "/etc/systemd/system/__SERVICE_NAME__"; then
    echo "__DESCRIPTION__ schedule: not installed"
  exit 0
fi

echo "__DESCRIPTION__ schedule: installed"
echo "Host runner: __REMOTE_HOST_SCRIPT_PATH__"
echo "Service: __SERVICE_NAME__"
echo "Timer: __TIMER_NAME__"
echo "Log file: __RESOLVED_LOG_FILE__"
echo
sudo systemctl is-enabled "__TIMER_NAME__" || true
sudo systemctl is-active "__TIMER_NAME__" || true
echo
sudo systemctl list-timers "__TIMER_NAME__" --all --no-pager
echo
sudo systemctl status "__SERVICE_NAME__" "__TIMER_NAME__" --no-pager --lines=12 || true
echo
if sudo test -f "__RESOLVED_LOG_FILE__"; then
    sudo tail -n 20 "__RESOLVED_LOG_FILE__" || true
fi
'@ -Replacements $replacements

$runNowScript = Expand-RemoteTemplate -Template @'
set -euo pipefail

sudo systemctl start "__SERVICE_NAME__"
sudo systemctl show "__SERVICE_NAME__" \
    -p Result \
    -p ExecMainStatus \
    -p ActiveState \
    -p SubState \
    --no-pager
echo
sudo systemctl status "__SERVICE_NAME__" --no-pager --lines=20 || true
echo
if sudo test -f "__RESOLVED_LOG_FILE__"; then
    echo "== recent file log =="
    sudo tail -n 20 "__RESOLVED_LOG_FILE__" || true
    echo
fi
sudo journalctl -u "__SERVICE_NAME__" -n 40 --no-pager
'@ -Replacements $replacements

$uninstallScript = Expand-RemoteTemplate -Template @'
set -euo pipefail

if sudo test -f "/etc/systemd/system/__TIMER_NAME__"; then
  sudo systemctl disable --now "__TIMER_NAME__" || true
fi

if sudo test -f "/etc/systemd/system/__SERVICE_NAME__"; then
  sudo rm -f "/etc/systemd/system/__SERVICE_NAME__"
fi

if sudo test -f "/etc/systemd/system/__TIMER_NAME__"; then
  sudo rm -f "/etc/systemd/system/__TIMER_NAME__"
fi

if sudo test -f "/etc/logrotate.d/__LOGROTATE_NAME__"; then
    sudo rm -f "/etc/logrotate.d/__LOGROTATE_NAME__"
fi

sudo systemctl daemon-reload
rm -f "__REMOTE_HOST_SCRIPT_PATH__"
echo "Removed service: __SERVICE_NAME__"
echo "Removed timer: __TIMER_NAME__"
'@ -Replacements $replacements

switch ($Action) {
    'install' {
        Invoke-RemoteScript $installScript
        exit 0
    }
    'status' {
        Invoke-RemoteScript $statusScript
        exit 0
    }
    'run-now' {
        Invoke-RemoteScript $runNowScript
        exit 0
    }
    'uninstall' {
        Invoke-RemoteScript $uninstallScript
        exit 0
    }
}