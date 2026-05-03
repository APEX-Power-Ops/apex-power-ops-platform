param(
    [ValidateSet('setup', 'config', 'up', 'down', 'tunnel', 'backup', 'backup-fetch', 'backup-fetch-sync', 'sync-offsite', 'restore', 'restore-local', 'status')]
    [string]$Action = 'config',

    [string]$HostAlias = 'olares@100.64.0.1',

    [string]$ComposeFile = '/home/olares/src/apex-power-ops-platform/apex-power-ops-platform/infra/private/personal-stack.compose.yml',

    [string]$TemplateEnvFile = '/home/olares/src/apex-power-ops-platform/apex-power-ops-platform/infra/private/.env.personal.template',

    [string]$EnvFile = '$HOME/code/personal/.env.personal',

    [string]$NoteFile = '$HOME/code/personal/personal-stack-operator-note.md',

    [string]$BackupRoot = '$HOME/apex-backups/personal/memos',

    [string]$LocalBackupRoot = "$HOME\OlaresPersonalBackups\memos",

    [string]$OffsiteBackupRoot = "$HOME\OneDrive\OlaresPersonalBackups\memos",

    [string]$ArchiveFile = '',

    [string]$LocalArchiveFile = '',

    [int]$LocalPort = 5231,

    [string]$RemoteHost = '127.0.0.1',

    [int]$RemotePort = 5230,

    [switch]$ForceRestore,

    [switch]$SkipRestart,

    [switch]$WithDb
)

$dataRoot = '$HOME/apex-data/personal'
$secretsRoot = '$HOME/apex-secrets/personal'
$knownHostsFile = Join-Path $env:TEMP 'olares_mesh_known_hosts'
$script:RemoteHomeDirectory = $null

$noteContent = @'
# Personal Stack Operator Note

Date opened:

Host:

Purpose:

## Live Paths

- Env file: __ENV_FILE__
- Data root: __DATA_ROOT__
- Secrets root: __SECRETS_ROOT__

## Current Posture

- First live service: `personal-notes`
- Exposure: host-only through `127.0.0.1`
- Data classification: useful but recoverable
- Optional database profile: off by default

## Verification

- `config` run completed:
- `up` run completed:
- Persistence verified after restart:

## Follow-On Decisions

- Private mesh access needed:
- Optional database needed:
- Backup or restore path tested:
- Graduation packet needed:
'@
$noteContent = $noteContent.Replace('__ENV_FILE__', $EnvFile).Replace('__DATA_ROOT__', $dataRoot).Replace('__SECRETS_ROOT__', $secretsRoot)

$backupScript = @'
set -euo pipefail

export ENV_FILE="__ENV_FILE__"
export BACKUP_ROOT="__BACKUP_ROOT__"

mkdir -p "$BACKUP_ROOT"

env_source="$ENV_FILE"
if grep -q $'\r' "$ENV_FILE"; then
    env_source="$(mktemp)"
    tr -d '\r' < "$ENV_FILE" > "$env_source"
fi

set -a
. "$env_source"
set +a

if [ "$env_source" != "$ENV_FILE" ]; then
    rm -f "$env_source"
fi

DATA_ROOT="${PERSONAL_DATA_ROOT:-$HOME/apex-data/personal}"
SOURCE_DIR="$DATA_ROOT/memos"
DB_PATH="$SOURCE_DIR/memos_prod.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Missing database: $DB_PATH" >&2
    exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

mkdir -p "$workdir/memos"

export DB_PATH
export SNAPSHOT_DB="$workdir/memos/memos_prod.db"

python3 - <<'PY'
import os
import sqlite3

src = os.environ["DB_PATH"]
dst = os.environ["SNAPSHOT_DB"]

src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
dst_conn = sqlite3.connect(dst)
src_conn.backup(dst_conn)
dst_conn.close()
src_conn.close()
PY

shopt -s dotglob nullglob
for path in "$SOURCE_DIR"/*; do
    name="$(basename "$path")"
    case "$name" in
        memos_prod.db|memos_prod.db-shm|memos_prod.db-wal)
            continue
            ;;
    esac
    cp -a "$path" "$workdir/memos/"
done

manifest="$workdir/manifest.json"
cat > "$manifest" <<EOF
{
    "service": "personal-notes",
    "created_at_utc": "$timestamp",
    "env_file": "$ENV_FILE",
    "backup_root": "$BACKUP_ROOT",
    "source_dir": "$SOURCE_DIR",
    "db_snapshot": "memos/memos_prod.db"
}
EOF

archive="$BACKUP_ROOT/personal-notes-$timestamp.tgz"
tar -C "$workdir" -czf "$archive" manifest.json memos
echo "$archive"
'@
$backupScript = $backupScript.Replace('__ENV_FILE__', $EnvFile).Replace('__BACKUP_ROOT__', $BackupRoot)

$restoreScript = @'
set -euo pipefail

export ENV_FILE="__ENV_FILE__"
export BACKUP_ROOT="__BACKUP_ROOT__"
export COMPOSE_FILE="__COMPOSE_FILE__"
ARCHIVE_FILE="__ARCHIVE_FILE__"
FORCE_RESTORE="__FORCE_RESTORE__"
SKIP_RESTART="__SKIP_RESTART__"

if [ -z "$ARCHIVE_FILE" ]; then
    echo "ArchiveFile is required for restore." >&2
    exit 2
fi

if [ "$FORCE_RESTORE" != "1" ]; then
    echo "Restore requires explicit force confirmation." >&2
    exit 2
fi

if [ ! -f "$ARCHIVE_FILE" ]; then
    echo "Archive not found: $ARCHIVE_FILE" >&2
    exit 1
fi

mkdir -p "$BACKUP_ROOT"

env_source="$ENV_FILE"
if grep -q $'\r' "$ENV_FILE"; then
    env_source="$(mktemp)"
    tr -d '\r' < "$ENV_FILE" > "$env_source"
fi

set -a
. "$env_source"
set +a

if [ "$env_source" != "$ENV_FILE" ]; then
    rm -f "$env_source"
fi

DATA_ROOT="${PERSONAL_DATA_ROOT:-$HOME/apex-data/personal}"
SOURCE_DIR="$DATA_ROOT/memos"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

tar -C "$workdir" -xzf "$ARCHIVE_FILE"

if [ ! -f "$workdir/memos/memos_prod.db" ]; then
    echo "Archive does not contain memos/memos_prod.db" >&2
    exit 1
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" stop personal-notes

if [ -d "$SOURCE_DIR" ]; then
    pre_restore_archive="$BACKUP_ROOT/pre-restore-personal-notes-$timestamp.tgz"
    tar -C "$DATA_ROOT" -czf "$pre_restore_archive" memos
    echo "Pre-restore snapshot: $pre_restore_archive"
fi

rm -rf "$SOURCE_DIR"
mkdir -p "$SOURCE_DIR"
cp -a "$workdir/memos/." "$SOURCE_DIR/"

if [ "$SKIP_RESTART" = "1" ]; then
    echo "Restored to $SOURCE_DIR and left personal-notes stopped."
else
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d personal-notes
    echo "Restored to $SOURCE_DIR and restarted personal-notes."
fi
'@
$restoreScript = $restoreScript.Replace('__ENV_FILE__', $EnvFile).Replace('__BACKUP_ROOT__', $BackupRoot).Replace('__COMPOSE_FILE__', $ComposeFile).Replace('__ARCHIVE_FILE__', $ArchiveFile).Replace('__FORCE_RESTORE__', $(if ($ForceRestore) { '1' } else { '0' })).Replace('__SKIP_RESTART__', $(if ($SkipRestart) { '1' } else { '0' }))

$statusScript = @'
set -euo pipefail

export ENV_FILE="__ENV_FILE__"
export BACKUP_ROOT="__BACKUP_ROOT__"
export COMPOSE_FILE="__COMPOSE_FILE__"

env_source="$ENV_FILE"
if grep -q $'\r' "$ENV_FILE"; then
    env_source="$(mktemp)"
    tr -d '\r' < "$ENV_FILE" > "$env_source"
fi

set -a
. "$env_source"
set +a

if [ "$env_source" != "$ENV_FILE" ]; then
    rm -f "$env_source"
fi

DATA_ROOT="${PERSONAL_DATA_ROOT:-$HOME/apex-data/personal}"
SOURCE_DIR="$DATA_ROOT/memos"
DB_PATH="$SOURCE_DIR/memos_prod.db"

echo "== compose ps =="
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
echo

echo "== http health =="
curl -I -s http://127.0.0.1:${PERSONAL_NOTES_PORT:-5230} | head -n 5
echo

if [ -f "$DB_PATH" ]; then
    echo "== sqlite summary =="
    export DB_PATH
    python3 - <<'PY'
import os
import sqlite3

db_path = os.environ["DB_PATH"]
conn = sqlite3.connect(db_path)
cur = conn.cursor()
user_count = cur.execute("SELECT COUNT(*) FROM user").fetchone()[0]
memo_count = cur.execute("SELECT COUNT(*) FROM memo").fetchone()[0]
row = cur.execute("SELECT content FROM memo ORDER BY id LIMIT 1").fetchone()
headline = row[0].splitlines()[0] if row and row[0] else ""
print(f"user_count={user_count}")
print(f"memo_count={memo_count}")
print(f"first_memo_headline={headline}")
PY
    echo
fi

echo "== latest backups =="
if [ -d "$BACKUP_ROOT" ]; then
    find "$BACKUP_ROOT" -maxdepth 1 -type f | sort | tail -n 5
else
    echo "No backup directory: $BACKUP_ROOT"
fi
'@
$statusScript = $statusScript.Replace('__ENV_FILE__', $EnvFile).Replace('__BACKUP_ROOT__', $BackupRoot).Replace('__COMPOSE_FILE__', $ComposeFile)

$composeBase = "docker compose --env-file $EnvFile -f $ComposeFile"
if ($WithDb) {
    $composeBase += ' --profile db'
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

function Get-RemoteHomeDirectory {
    if ($script:RemoteHomeDirectory) {
        return $script:RemoteHomeDirectory
    }

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()

    try {
        $process = Start-Process -FilePath 'ssh' -ArgumentList @(
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', "UserKnownHostsFile=$knownHostsFile",
            $HostAlias,
            'printf %s "$HOME"'
        ) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile

        if ($process.ExitCode -ne 0) {
            $detail = @()
            foreach ($path in @($stderrFile, $stdoutFile)) {
                if (Test-Path $path) {
                    $text = [System.IO.File]::ReadAllText($path).Trim()
                    if ($text) {
                        $detail += $text
                    }
                }
            }

            if ($detail.Count -eq 0) {
                $detail = @("ssh failed with exit code $($process.ExitCode) while resolving remote home directory.")
            }

            throw ($detail -join [Environment]::NewLine)
        }

        $remoteHome = if (Test-Path $stdoutFile) { [System.IO.File]::ReadAllText($stdoutFile).Trim() } else { '' }
        if (-not $remoteHome) {
            throw 'Remote home directory resolution returned an empty value.'
        }

        $script:RemoteHomeDirectory = $remoteHome
        return $script:RemoteHomeDirectory
    }
    finally {
        foreach ($path in @($stdoutFile, $stderrFile)) {
            if (Test-Path $path) {
                Remove-Item $path -Force
            }
        }
    }
}

function Resolve-RemoteCopyPath {
    param(
        [string]$Path
    )

    $remoteHome = Get-RemoteHomeDirectory

    if ($Path -eq '$HOME') {
        return $remoteHome
    }

    if ($Path.StartsWith('$HOME/')) {
        return ($Path -replace '^\$HOME', $remoteHome)
    }

    if ($Path -eq '~') {
        return $remoteHome
    }

    if ($Path.StartsWith('~/')) {
        return "$remoteHome/$($Path.Substring(2))"
    }

    return $Path
}

function Copy-RemoteArchiveToLocal {
    param(
        [string]$RemoteArchivePath,
        [string]$LocalArchivePath
    )

    $resolvedRemoteArchivePath = Resolve-RemoteCopyPath $RemoteArchivePath
    $destinationDir = Split-Path -Parent $LocalArchivePath
    if (-not (Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()

    try {
        $process = Start-Process -FilePath 'scp' -ArgumentList @(
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', "UserKnownHostsFile=$knownHostsFile",
            ("{0}:{1}" -f $HostAlias, $resolvedRemoteArchivePath),
            $LocalArchivePath
        ) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile

        if ($process.ExitCode -ne 0) {
            $detail = @()
            foreach ($path in @($stderrFile, $stdoutFile)) {
                if (Test-Path $path) {
                    $text = [System.IO.File]::ReadAllText($path).Trim()
                    if ($text) {
                        $detail += $text
                    }
                }
            }

            if ($detail.Count -eq 0) {
                $detail = @("scp failed with exit code $($process.ExitCode).")
            }

            throw ($detail -join [Environment]::NewLine)
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

function Copy-LocalArchiveToRemote {
    param(
        [string]$LocalArchivePath,
        [string]$RemoteArchivePath
    )

    $resolvedRemoteArchivePath = Resolve-RemoteCopyPath $RemoteArchivePath
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()

    try {
        $process = Start-Process -FilePath 'scp' -ArgumentList @(
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', "UserKnownHostsFile=$knownHostsFile",
            $LocalArchivePath,
            ("{0}:{1}" -f $HostAlias, $resolvedRemoteArchivePath)
        ) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile

        if ($process.ExitCode -ne 0) {
            $detail = @()
            foreach ($path in @($stderrFile, $stdoutFile)) {
                if (Test-Path $path) {
                    $text = [System.IO.File]::ReadAllText($path).Trim()
                    if ($text) {
                        $detail += $text
                    }
                }
            }

            if ($detail.Count -eq 0) {
                $detail = @("scp failed with exit code $($process.ExitCode).")
            }

            throw ($detail -join [Environment]::NewLine)
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

function Sync-LocalBackupsToOffsite {
    param(
        [string]$SourceRoot,
        [string]$DestinationRoot
    )

    if (-not (Test-Path $SourceRoot)) {
        throw "Local backup root not found: $SourceRoot"
    }

    if (-not (Test-Path $DestinationRoot)) {
        New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
    }

    $copied = New-Object System.Collections.Generic.List[string]
    $skipped = New-Object System.Collections.Generic.List[string]

    foreach ($sourceFile in Get-ChildItem -Path $SourceRoot -File | Sort-Object Name) {
        $destinationFile = Join-Path $DestinationRoot $sourceFile.Name
        $shouldCopy = $true

        if (Test-Path $destinationFile) {
            $existing = Get-Item $destinationFile
            if ($existing.Length -eq $sourceFile.Length -and $existing.LastWriteTimeUtc -ge $sourceFile.LastWriteTimeUtc) {
                $shouldCopy = $false
            }
        }

        if ($shouldCopy) {
            Copy-Item -Path $sourceFile.FullName -Destination $destinationFile -Force
            (Get-Item $destinationFile).LastWriteTimeUtc = $sourceFile.LastWriteTimeUtc
            $copied.Add($destinationFile) | Out-Null
        }
        else {
            $skipped.Add($destinationFile) | Out-Null
        }
    }

    return [pscustomobject]@{
        SourceRoot = $SourceRoot
        DestinationRoot = $DestinationRoot
        Copied = $copied
        Skipped = $skipped
    }
}

function Write-OffsiteSyncSummary {
    param(
        [pscustomobject]$SyncResult
    )

    Write-Host "Offsite destination: $($SyncResult.DestinationRoot)"
    Write-Host "New or updated files copied: $($SyncResult.Copied.Count)"
    foreach ($path in $SyncResult.Copied) {
        Write-Host "  copied: $path"
    }

    Write-Host "Already-current files skipped: $($SyncResult.Skipped.Count)"
}

function Write-LocalBackupMirrorStatus {
    param(
        [string]$Label,
        [string]$Path
    )

    Write-Host "== $Label =="
    if (-not (Test-Path $Path)) {
        Write-Host "Missing path: $Path"
        Write-Host ''
        return
    }

    Write-Host "Path: $Path"
    $files = Get-ChildItem -Path $Path -File | Sort-Object LastWriteTimeUtc
    Write-Host "File count: $($files.Count)"
    foreach ($file in ($files | Select-Object -Last 5)) {
        Write-Host $file.FullName
    }
    Write-Host ''
}

$remoteAction = switch ($Action) {
    'setup' {
        @"
mkdir -p "`$(dirname "$EnvFile")"
mkdir -p "`$(dirname "$NoteFile")"
mkdir -p "$dataRoot/memos"
mkdir -p "$secretsRoot"
if [ ! -f "$EnvFile" ]; then
    tr -d '\r' < "$TemplateEnvFile" > "$EnvFile"
  chmod 600 "$EnvFile"
fi
if [ ! -f "$NoteFile" ]; then
  cat > "$NoteFile" <<EOF
$noteContent
EOF
  chmod 600 "$NoteFile"
fi
echo "Prepared personal stack host paths:"
echo "  env file: $EnvFile"
echo "  note file: $NoteFile"
echo "  data root: $dataRoot"
echo "  secrets root: $secretsRoot"
"@
    }
    'config' {
        "$composeBase config"
    }
    'up' {
        "$composeBase up -d"
    }
    'down' {
        "$composeBase down"
    }
    'tunnel' {
        $null
    }
    'backup' {
        $backupScript
    }
    'restore' {
        $restoreScript
    }
    'status' {
        $statusScript
    }
}

if ($Action -eq 'tunnel') {
    & ssh `
        '-o' 'BatchMode=yes' `
        '-o' 'ExitOnForwardFailure=yes' `
        '-o' 'ServerAliveInterval=30' `
        '-o' 'ServerAliveCountMax=3' `
        '-o' 'TCPKeepAlive=yes' `
        '-N' `
        '-L' ("{0}:{1}:{2}" -f $LocalPort, $RemoteHost, $RemotePort) `
        $HostAlias
    exit $LASTEXITCODE
}

if ($Action -eq 'backup-fetch') {
    $result = Invoke-RemoteScriptCapture $backupScript
    if ($result.StdOut) {
        $text = $result.StdOut.TrimEnd()
        if ($text) {
            Write-Output $text
        }
    }

    $remoteArchive = ($result.StdOut -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Last 1).Trim()
    if (-not $remoteArchive) {
        throw 'The backup action completed without returning an archive path.'
    }

    $localArchive = Join-Path $LocalBackupRoot (Split-Path -Path $remoteArchive -Leaf)
    Copy-RemoteArchiveToLocal -RemoteArchivePath $remoteArchive -LocalArchivePath $localArchive

    Write-Host "Downloaded archive to $localArchive"
    exit 0
}

if ($Action -eq 'backup-fetch-sync') {
    $argumentList = @(
        '-NoProfile',
        '-File', $PSCommandPath,
        '-Action', 'backup-fetch',
        '-HostAlias', $HostAlias,
        '-ComposeFile', $ComposeFile,
        '-TemplateEnvFile', $TemplateEnvFile,
        '-EnvFile', $EnvFile,
        '-NoteFile', $NoteFile,
        '-BackupRoot', $BackupRoot,
        '-LocalBackupRoot', $LocalBackupRoot,
        '-LocalPort', "$LocalPort",
        '-RemoteHost', $RemoteHost,
        '-RemotePort', "$RemotePort",
        '-OffsiteBackupRoot', $OffsiteBackupRoot
    )

    if ($ForceRestore) {
        $argumentList += '-ForceRestore'
    }

    if ($SkipRestart) {
        $argumentList += '-SkipRestart'
    }

    if ($WithDb) {
        $argumentList += '-WithDb'
    }

    $output = & pwsh @argumentList 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw (($output | Out-String).Trim())
    }

    if ($output) {
        ($output | Out-String).TrimEnd() | Write-Output
    }

    $syncResult = Sync-LocalBackupsToOffsite -SourceRoot $LocalBackupRoot -DestinationRoot $OffsiteBackupRoot
    Write-OffsiteSyncSummary -SyncResult $syncResult
    exit 0
}

if ($Action -eq 'sync-offsite') {
    $syncResult = Sync-LocalBackupsToOffsite -SourceRoot $LocalBackupRoot -DestinationRoot $OffsiteBackupRoot
    Write-OffsiteSyncSummary -SyncResult $syncResult
    exit 0
}

if ($Action -eq 'restore-local') {
    if (-not $LocalArchiveFile) {
        throw 'LocalArchiveFile is required for restore-local.'
    }

    $resolvedLocalArchive = (Resolve-Path -Path $LocalArchiveFile -ErrorAction Stop).Path
    $remoteImportRoot = "$BackupRoot/imported"
    $remoteArchive = "$remoteImportRoot/$([System.IO.Path]::GetFileName($resolvedLocalArchive))"

    Invoke-RemoteScript @"
set -euo pipefail
mkdir -p "$remoteImportRoot"
"@
    Copy-LocalArchiveToRemote -LocalArchivePath $resolvedLocalArchive -RemoteArchivePath $remoteArchive

    $argumentList = @(
        '-NoProfile',
        '-File', $PSCommandPath,
        '-Action', 'restore',
        '-HostAlias', $HostAlias,
        '-ComposeFile', $ComposeFile,
        '-TemplateEnvFile', $TemplateEnvFile,
        '-EnvFile', $EnvFile,
        '-NoteFile', $NoteFile,
        '-BackupRoot', $BackupRoot,
        '-ArchiveFile', $remoteArchive
    )

    if ($ForceRestore) {
        $argumentList += '-ForceRestore'
    }

    if ($SkipRestart) {
        $argumentList += '-SkipRestart'
    }

    if ($WithDb) {
        $argumentList += '-WithDb'
    }

    $output = & pwsh @argumentList 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw (($output | Out-String).Trim())
    }

    if ($output) {
        ($output | Out-String).TrimEnd() | Write-Output
    }

    Write-Host "Uploaded archive from $resolvedLocalArchive to $remoteArchive"
    exit 0
}

if ($Action -in @('setup', 'backup', 'restore', 'status')) {
    Invoke-RemoteScript $remoteAction
    if ($Action -eq 'status') {
        Write-Host ''
        Write-LocalBackupMirrorStatus -Label 'workstation backup copies' -Path $LocalBackupRoot
        Write-LocalBackupMirrorStatus -Label 'offsite backup mirror' -Path $OffsiteBackupRoot
    }
    exit $LASTEXITCODE
}

& ssh $HostAlias $remoteAction
exit $LASTEXITCODE
