param(
    [ValidateSet('setup', 'status', 'init', 'backup', 'snapshots', 'forget-prune', 'restore-drill')]
    [string]$Action = 'status',

    [string]$HostAlias = 'olares@100.64.0.1',

    [string]$EnvTemplateFile = (Join-Path $PSScriptRoot '.env.personal-offsite-backup.template'),

    [string]$RemoteEnvFile = '$HOME/code/personal/.env.personal-offsite-backup',

    [string]$BackupRoot = '$HOME/apex-backups/personal/memos',

    [string]$RestoreDrillRoot = '$HOME/apex-restore-drills/personal/memos',

    [string]$SnapshotScriptPath = (Join-Path $PSScriptRoot 'run-personal-stack-remote.ps1'),

    [int]$KeepDaily = 7,

    [int]$KeepWeekly = 4,

    [int]$KeepMonthly = 3,

    [int]$KeepYearly = 1,

    [switch]$SkipLocalSnapshot
)

$knownHostsFile = Join-Path $env:TEMP 'olares_mesh_known_hosts'

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

function Get-TemplateContent {
    if (-not (Test-Path $EnvTemplateFile)) {
        throw "EnvTemplateFile not found: $EnvTemplateFile"
    }

    return [System.IO.File]::ReadAllText($EnvTemplateFile).Replace("`r`n", "`n")
}

function Invoke-LocalSnapshot {
    if ($SkipLocalSnapshot) {
        Write-Host 'Skipping fresh host-local snapshot creation.'
        return
    }

    if (-not (Test-Path $SnapshotScriptPath)) {
        throw "SnapshotScriptPath not found: $SnapshotScriptPath"
    }

    $output = & pwsh -NoProfile -ExecutionPolicy Bypass -File $SnapshotScriptPath -Action backup -HostAlias $HostAlias -BackupRoot $BackupRoot 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw (($output | Out-String).Trim())
    }

    if ($output) {
        ($output | Out-String).TrimEnd() | Write-Output
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

$templateContent = Get-TemplateContent

$baseReplacements = @{
    '__ENV_FILE__' = $RemoteEnvFile
    '__BACKUP_ROOT__' = $BackupRoot
    '__RESTORE_DRILL_ROOT__' = $RestoreDrillRoot
    '__KEEP_DAILY__' = [string]$KeepDaily
    '__KEEP_WEEKLY__' = [string]$KeepWeekly
    '__KEEP_MONTHLY__' = [string]$KeepMonthly
    '__KEEP_YEARLY__' = [string]$KeepYearly
}

$remoteBootstrap = Expand-RemoteTemplate -Template @'
set -euo pipefail

value_is_placeholder() {
    case "${1:-}" in
        ''|*REPLACE_WITH*|*SET_FROM*|*SET_IF_REQUIRED*|*OPTIONAL_* )
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

ENV_FILE="__ENV_FILE__"
BACKUP_ROOT="__BACKUP_ROOT__"
RESTORE_DRILL_ROOT="__RESTORE_DRILL_ROOT__"
'@ -Replacements $baseReplacements

$setupScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

mkdir -p "$(dirname "$ENV_FILE")"
mkdir -p "$RESTORE_DRILL_ROOT"

if [ ! -f "$ENV_FILE" ]; then
cat > "$ENV_FILE" <<'EOF'
__TEMPLATE_CONTENT__
EOF
  chmod 600 "$ENV_FILE"
fi

chmod 700 "$RESTORE_DRILL_ROOT"

echo "Remote env file: $ENV_FILE"
echo "Restore drill root: $RESTORE_DRILL_ROOT"
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
        '__TEMPLATE_CONTENT__' = $templateContent
    } + $baseReplacements)

$statusScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

echo "== host-owned encrypted offsite readiness =="
echo "env file: $ENV_FILE"
echo "backup root: $BACKUP_ROOT"
echo "restore drill root: $RESTORE_DRILL_ROOT"

restic_path="$(command -v restic || true)"
if [ -z "$restic_path" ]; then
    echo "restic installed: no"
    exit 0
fi

echo "restic installed: yes ($restic_path)"

if [ ! -f "$ENV_FILE" ]; then
    echo "env file present: no"
    exit 0
fi

echo "env file present: yes"

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

repository_ready=no
password_ready=no
credentials_ready=n-a

if ! value_is_placeholder "${RESTIC_REPOSITORY:-}"; then
    repository_ready=yes
fi

if ! value_is_placeholder "${RESTIC_PASSWORD:-}"; then
    password_ready=yes
fi

case "${RESTIC_REPOSITORY:-}" in
    s3:*)
        credentials_ready=no
        if ! value_is_placeholder "${AWS_ACCESS_KEY_ID:-}" && ! value_is_placeholder "${AWS_SECRET_ACCESS_KEY:-}"; then
            credentials_ready=yes
        fi
        ;;
esac

echo "repository configured: $repository_ready"
echo "password configured: $password_ready"
echo "provider credentials ready: $credentials_ready"

if [ -d "$BACKUP_ROOT" ]; then
    echo "local archive root present: yes"
    echo "latest local archives:"
    find "$BACKUP_ROOT" -maxdepth 1 -type f -name 'personal-notes-*.tgz' | sort | tail -n 5
else
    echo "local archive root present: no"
fi

if [ "$repository_ready" = yes ] && [ "$password_ready" = yes ] && { [ "$credentials_ready" = yes ] || [ "$credentials_ready" = n-a ]; }; then
    workdir="$(mktemp -d)"
    trap 'rm -rf "$workdir"' EXIT
    if restic snapshots > "$workdir/snapshots.txt" 2> "$workdir/restic.err"; then
        echo "repository reachable: yes"
        echo "latest restic snapshots:"
        tail -n 10 "$workdir/snapshots.txt"
    else
        echo "repository reachable: no"
        echo "restic error:"
        cat "$workdir/restic.err"
    fi
fi
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
    } + $baseReplacements)

$initScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

if ! command -v restic >/dev/null 2>&1; then
    echo "restic is not installed on the host." >&2
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing env file: $ENV_FILE" >&2
    exit 1
fi

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

if value_is_placeholder "${RESTIC_REPOSITORY:-}" || value_is_placeholder "${RESTIC_PASSWORD:-}"; then
    echo "RESTIC_REPOSITORY and RESTIC_PASSWORD must be filled before init." >&2
    exit 1
fi

case "${RESTIC_REPOSITORY:-}" in
    s3:*)
        if value_is_placeholder "${AWS_ACCESS_KEY_ID:-}" || value_is_placeholder "${AWS_SECRET_ACCESS_KEY:-}"; then
            echo "S3 repository selected but AWS credentials are still placeholders." >&2
            exit 1
        fi
        ;;
esac

if restic cat config >/dev/null 2>&1; then
    echo "Restic repository already initialized."
else
    restic init
fi
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
    } + $baseReplacements)

$backupScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

if ! command -v restic >/dev/null 2>&1; then
    echo "restic is not installed on the host." >&2
    exit 1
fi

if [ ! -d "$BACKUP_ROOT" ]; then
    echo "Backup root not found: $BACKUP_ROOT" >&2
    exit 1
fi

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

if value_is_placeholder "${RESTIC_REPOSITORY:-}" || value_is_placeholder "${RESTIC_PASSWORD:-}"; then
    echo "RESTIC_REPOSITORY and RESTIC_PASSWORD must be filled before backup." >&2
    exit 1
fi

case "${RESTIC_REPOSITORY:-}" in
    s3:*)
        if value_is_placeholder "${AWS_ACCESS_KEY_ID:-}" || value_is_placeholder "${AWS_SECRET_ACCESS_KEY:-}"; then
            echo "S3 repository selected but AWS credentials are still placeholders." >&2
            exit 1
        fi
        ;;
esac

restic backup "$BACKUP_ROOT" --host "${RESTIC_HOST_LABEL:-$(hostname)}" --tag personal-notes --tag host-local-archives --tag private-lane
restic snapshots | tail -n 10
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
    } + $baseReplacements)

$snapshotsScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

if ! command -v restic >/dev/null 2>&1; then
    echo "restic is not installed on the host." >&2
    exit 1
fi

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

restic snapshots
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
    } + $baseReplacements)

$forgetPruneScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

if ! command -v restic >/dev/null 2>&1; then
    echo "restic is not installed on the host." >&2
    exit 1
fi

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

keep_daily="${RESTIC_KEEP_DAILY:-__KEEP_DAILY__}"
keep_weekly="${RESTIC_KEEP_WEEKLY:-__KEEP_WEEKLY__}"
keep_monthly="${RESTIC_KEEP_MONTHLY:-__KEEP_MONTHLY__}"
keep_yearly="${RESTIC_KEEP_YEARLY:-__KEEP_YEARLY__}"

restic forget --keep-daily "$keep_daily" --keep-weekly "$keep_weekly" --keep-monthly "$keep_monthly" --keep-yearly "$keep_yearly" --prune
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
    } + $baseReplacements)

$restoreDrillScript = Expand-RemoteTemplate -Template @'
__REMOTE_BOOTSTRAP__

if ! command -v restic >/dev/null 2>&1; then
    echo "restic is not installed on the host." >&2
    exit 1
fi

mkdir -p "$RESTORE_DRILL_ROOT"

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

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target_dir="$RESTORE_DRILL_ROOT/$timestamp"
extract_dir="$(mktemp -d)"
trap 'rm -rf "$extract_dir"' EXIT

restic restore latest --target "$target_dir"

restored_archive="$(find "$target_dir" -type f -name 'personal-notes-*.tgz' | sort | tail -n 1)"
if [ -z "$restored_archive" ]; then
    echo "Restore drill did not recover a personal-notes archive." >&2
    exit 1
fi

tar -C "$extract_dir" -xzf "$restored_archive"

if [ ! -f "$extract_dir/manifest.json" ] || [ ! -f "$extract_dir/memos/memos_prod.db" ]; then
    echo "Restore drill recovered an archive but failed integrity validation." >&2
    exit 1
fi

echo "Restore drill target: $target_dir"
echo "Validated archive: $restored_archive"
'@ -Replacements (@{
        '__REMOTE_BOOTSTRAP__' = $remoteBootstrap
    } + $baseReplacements)

switch ($Action) {
    'setup' {
        Invoke-RemoteScript $setupScript
        break
    }
    'status' {
        Invoke-RemoteScript $statusScript
        break
    }
    'init' {
        Invoke-RemoteScript $initScript
        break
    }
    'backup' {
        Invoke-LocalSnapshot
        Invoke-RemoteScript $backupScript
        break
    }
    'snapshots' {
        Invoke-RemoteScript $snapshotsScript
        break
    }
    'forget-prune' {
        Invoke-RemoteScript $forgetPruneScript
        break
    }
    'restore-drill' {
        Invoke-RemoteScript $restoreDrillScript
        break
    }
}

exit $LASTEXITCODE