param(
    [ValidateSet('install', 'uninstall', 'status', 'run-now')]
    [string]$Action = 'status',

    [string]$TaskName = 'APEX-Olares-Personal-Notes-Backup',

    [string]$StartTime = '02:15',

    [string]$LogRoot = "$HOME\OlaresPersonalBackups\logs",

    [string]$BackupScriptPath = ''
)

$scriptPath = $MyInvocation.MyCommand.Path
$resolvedBackupScript = if ($BackupScriptPath) {
    (Resolve-Path -Path $BackupScriptPath -ErrorAction Stop).Path
}
else {
    Join-Path (Split-Path -Parent $scriptPath) 'run-personal-stack-remote.ps1'
}

function Get-TaskCommand {
    $escapedScriptPath = $scriptPath.Replace('"', '""')
    return "-NoProfile -ExecutionPolicy Bypass -File `"$escapedScriptPath`" -Action run-now"
}

function Get-TaskRunCommand {
    return "pwsh.exe $(Get-TaskCommand)"
}

function Get-LegacyTaskName {
    return $TaskName
}

function Get-DailyTaskName {
    return "$TaskName-Daily"
}

function Get-LogonTaskName {
    return "$TaskName-Logon"
}

function Get-ManagedTaskDefinitions {
    return @(
        [pscustomobject]@{
            Name = Get-DailyTaskName
            TriggerLabel = 'Daily'
            Required = $true
            CreateArguments = @('/Create', '/TN', (Get-DailyTaskName), '/SC', 'DAILY', '/ST', $StartTime, '/TR', (Get-TaskRunCommand), '/F')
        },
        [pscustomobject]@{
            Name = Get-LogonTaskName
            TriggerLabel = 'AtLogOn'
            Required = $false
            CreateArguments = @('/Create', '/TN', (Get-LogonTaskName), '/SC', 'ONLOGON', '/TR', (Get-TaskRunCommand), '/F')
        }
    )
}

function Get-ManagedTaskNames {
    return (Get-ManagedTaskDefinitions | ForEach-Object { $_.Name })
}

function Invoke-Schtasks {
    param(
        [string[]]$Arguments,
        [switch]$AllowNotFound
    )

    $output = & schtasks.exe @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()

    if ($exitCode -ne 0) {
        if ($AllowNotFound -and $text -match 'cannot find the file specified') {
            return [pscustomobject]@{
                ExitCode = $exitCode
                Text = $text
                NotFound = $true
            }
        }

        throw "schtasks.exe $($Arguments -join ' ') failed with exit code $exitCode. $text"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Text = $text
        NotFound = $false
    }
}

function Get-TaskQueryMap {
    param(
        [string]$QueriedTaskName = $TaskName
    )

    $query = Invoke-Schtasks -Arguments @('/Query', '/TN', $QueriedTaskName, '/V', '/FO', 'LIST') -AllowNotFound
    if ($query.NotFound) {
        return $null
    }

    $map = [ordered]@{}
    foreach ($line in ($query.Text -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $parts = $line.Split(':', 2)
        if ($parts.Count -ne 2) {
            continue
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (-not $map.Contains($key)) {
            $map[$key] = $value
        }
    }

    return $map
}

function Get-TaskSafe {
    param(
        [string]$QueriedTaskName = $TaskName
    )

    $queryMap = Get-TaskQueryMap -QueriedTaskName $QueriedTaskName
    if ($null -eq $queryMap) {
        return $null
    }

    $task = $null
    $taskInfo = $null
    try {
        $task = Get-ScheduledTask -TaskName $QueriedTaskName -ErrorAction Stop
        $taskInfo = Get-ScheduledTaskInfo -TaskName $QueriedTaskName -ErrorAction Stop
    }
    catch {
    }

    return [pscustomobject]@{
        Task = $task
        TaskInfo = $taskInfo
        QueryMap = $queryMap
    }
}

function Get-InstalledTaskRecords {
    $records = @()
    foreach ($definition in Get-ManagedTaskDefinitions) {
        $record = Get-TaskSafe -QueriedTaskName $definition.Name
        if ($null -eq $record) {
            continue
        }

        $record | Add-Member -NotePropertyName InstalledName -NotePropertyValue $definition.Name
        $record | Add-Member -NotePropertyName TriggerLabel -NotePropertyValue $definition.TriggerLabel
        $records += $record
    }

    if ($records.Count -gt 0) {
        return $records
    }

    $legacyName = Get-LegacyTaskName
    $legacyRecord = Get-TaskSafe -QueriedTaskName $legacyName
    if ($null -eq $legacyRecord) {
        return @()
    }

    $legacyRecord | Add-Member -NotePropertyName InstalledName -NotePropertyValue $legacyName
    $legacyRecord | Add-Member -NotePropertyName TriggerLabel -NotePropertyValue 'Legacy'
    return @($legacyRecord)
}

function Install-Task {
    $optionalFailures = @()
    $legacyName = Get-LegacyTaskName
    if ($legacyName -notin (Get-ManagedTaskNames)) {
        [void](Invoke-Schtasks -Arguments @('/Delete', '/TN', $legacyName, '/F') -AllowNotFound)
    }

    foreach ($definition in Get-ManagedTaskDefinitions) {
        try {
            Invoke-Schtasks -Arguments $definition.CreateArguments | Out-Null
        }
        catch {
            if ($definition.Required) {
                throw
            }

            $optionalFailures += [pscustomobject]@{
                Name = $definition.Name
                TriggerLabel = $definition.TriggerLabel
                Error = $_.Exception.Message
            }
        }
    }

    $requiredNames = @(Get-ManagedTaskDefinitions | Where-Object { $_.Required } | ForEach-Object { $_.Name })
    $installedNames = @(Get-InstalledTaskRecords | ForEach-Object { $_.InstalledName })
    $missingNames = @($requiredNames | Where-Object { $_ -notin $installedNames })
    if ($missingNames.Count -gt 0) {
        throw "Scheduled task installation did not persist: $($missingNames -join ', ')"
    }

    return $optionalFailures
}

function Uninstall-Task {
    $taskNames = @()
    $taskNames += Get-ManagedTaskNames

    $legacyName = Get-LegacyTaskName
    if ($legacyName -notin $taskNames) {
        $taskNames += $legacyName
    }

    $removedAny = $false
    foreach ($taskNameToDelete in $taskNames) {
        $result = Invoke-Schtasks -Arguments @('/Delete', '/TN', $taskNameToDelete, '/F') -AllowNotFound
        if (-not $result.NotFound) {
            $removedAny = $true
        }
    }

    $remainingNames = @($taskNames | Where-Object { $null -ne (Get-TaskSafe -QueriedTaskName $_) })
    if ($remainingNames.Count -gt 0) {
        throw "Scheduled task still exists after delete: $($remainingNames -join ', ')"
    }

    return $removedAny
}

function Write-TaskStatus {
    $definitions = @(Get-ManagedTaskDefinitions)
    $taskRecords = @(Get-InstalledTaskRecords)
    if ($taskRecords.Count -eq 0) {
        Write-Host 'Personal Notes backup schedule: not installed.'
        return
    }

    Write-Host 'Personal Notes backup schedule: installed'
    Write-Host "Base task name: $TaskName"
    Write-Host "Task command: $(Get-TaskRunCommand)"
    foreach ($taskRecord in $taskRecords) {
        $task = $taskRecord.Task
        $taskInfo = $taskRecord.TaskInfo
        $queryMap = $taskRecord.QueryMap
        Write-Host "Trigger [$($taskRecord.TriggerLabel)]: $($taskRecord.InstalledName)"
        Write-Host "State [$($taskRecord.TriggerLabel)]: $(if ($null -ne $task) { $task.State } else { $queryMap['Status'] })"
        Write-Host "Last run time [$($taskRecord.TriggerLabel)]: $(if ($null -ne $taskInfo) { $taskInfo.LastRunTime } else { $queryMap['Last Run Time'] })"
        Write-Host "Last task result [$($taskRecord.TriggerLabel)]: $(if ($null -ne $taskInfo) { $taskInfo.LastTaskResult } else { $queryMap['Last Result'] })"
        Write-Host "Next run time [$($taskRecord.TriggerLabel)]: $(if ($null -ne $taskInfo) { $taskInfo.NextRunTime } else { $queryMap['Next Run Time'] })"
    }

    $installedNames = @($taskRecords | ForEach-Object { $_.InstalledName })
    foreach ($definition in $definitions | Where-Object { $_.Name -notin $installedNames }) {
        Write-Host "Trigger [$($definition.TriggerLabel)]: not installed"
        if (-not $definition.Required) {
            Write-Host "Trigger [$($definition.TriggerLabel)] note: optional trigger unavailable on this machine or skipped during install."
        }
    }

    Write-Host "Log root: $LogRoot"
}

switch ($Action) {
    'install' {
        if (-not (Test-Path $resolvedBackupScript)) {
            throw "Backup script not found: $resolvedBackupScript"
        }

        New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null

        $optionalFailures = @(Install-Task)

        Write-Host "Installed Personal Notes backup schedule base name: $TaskName"
        Write-Host "Daily task: $(Get-DailyTaskName) at $StartTime"
        Write-Host "Logon task: $(Get-LogonTaskName)"
        Write-Host "Log root: $LogRoot"
        foreach ($optionalFailure in $optionalFailures) {
            Write-Warning "Optional trigger [$($optionalFailure.TriggerLabel)] was not installed: $($optionalFailure.Error)"
        }
        exit 0
    }

    'uninstall' {
        $taskRecord = Get-TaskSafe
        if ($null -eq $taskRecord) {
            Write-Host 'Personal Notes backup schedule is not installed.'
            exit 0
        }

        [void](Uninstall-Task)
        Write-Host "Removed Personal Notes backup schedule: $TaskName"
        exit 0
    }

    'status' {
        Write-TaskStatus
        exit 0
    }

    'run-now' {
        if (-not (Test-Path $resolvedBackupScript)) {
            throw "Backup script not found: $resolvedBackupScript"
        }

        New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
        $timestamp = Get-Date -Format 'yyyyMMddTHHmmssZ'
        $logFile = Join-Path $LogRoot "personal-notes-backup-$timestamp.log"

        $output = & pwsh -NoProfile -ExecutionPolicy Bypass -File $resolvedBackupScript -Action backup-fetch-sync 2>&1
        $text = ($output | Out-String).TrimEnd()
        $header = @(
            "Timestamp: $((Get-Date).ToString('o'))"
            "Task name: $TaskName"
            "Backup script: $resolvedBackupScript"
            ''
        ) -join [Environment]::NewLine

        Set-Content -Path $logFile -Value ($header + $text) -Encoding utf8

        if ($LASTEXITCODE -ne 0) {
            if ($text) {
                Write-Error $text
            }
            else {
                Write-Error "Backup run failed. See log: $logFile"
            }
            exit $LASTEXITCODE
        }

        if ($text) {
            Write-Output $text
        }
        Write-Host "Log file: $logFile"
        exit 0
    }
}