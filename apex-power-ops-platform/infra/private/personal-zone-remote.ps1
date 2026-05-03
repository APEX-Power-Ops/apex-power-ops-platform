param(
    [ValidateSet('setup', 'status')]
    [string]$Action = 'status',

    [string]$HostAlias = 'olares@100.64.0.1'
)

$readmeContent = @'
# Personal Zone

This folder is your safe non-APEX workspace on the Olares machine.

## What Belongs Here

- personal downloads
- personal notes
- personal Docker Compose experiments
- personal test files and scratch work

## What Does Not Belong Here

- APEX source code
- APEX secrets
- governed APEX runtime data

## Important Notes

- Olares Market apps are platform-managed by Olares itself. They are outside the APEX repo, but they are not installed into this folder.
- Docker on this host is Linux-only. Windows containers are not supported on this Ubuntu Olares machine.
- Large Docker images and container layers already live in Docker-managed host storage, not in this folder.

## Main Paths

- `~/Personal/Downloads`
- `~/Personal/Notes`
- `~/Personal/Scratch`
- `~/Personal/Compose` -> `~/code/personal/compose`
- `~/Personal/Data` -> `~/apex-data/personal`
- `~/Personal/Backups` -> `~/apex-backups/personal`

## Practical Use

1. Save personal downloads into `~/Personal/Downloads`.
2. Put personal compose files into `~/Personal/Compose`.
3. Use `~/Personal/Notes` for plain files you want to keep separate from APEX.
4. Use the workstation helper `infra/private/personal-notes-access.ps1 -Action open` when you want the existing Personal Notes app.
'@

$remoteSetup = @'
set -euo pipefail

PERSONAL_HOME="$HOME/Personal"
DOWNLOADS_DIR="$PERSONAL_HOME/Downloads"
NOTES_DIR="$PERSONAL_HOME/Notes"
SCRATCH_DIR="$PERSONAL_HOME/Scratch"
CODE_ROOT="$HOME/code/personal"
COMPOSE_DIR="$CODE_ROOT/compose"
BIN_DIR="$CODE_ROOT/bin"
DATA_DIR="$HOME/apex-data/personal"
BACKUPS_DIR="$HOME/apex-backups/personal"
README_FILE="$PERSONAL_HOME/README.md"

mkdir -p "$DOWNLOADS_DIR"
mkdir -p "$NOTES_DIR"
mkdir -p "$SCRATCH_DIR"
mkdir -p "$COMPOSE_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$BACKUPS_DIR"

ln -sfn "$COMPOSE_DIR" "$PERSONAL_HOME/Compose"
ln -sfn "$DATA_DIR" "$PERSONAL_HOME/Data"
ln -sfn "$BACKUPS_DIR" "$PERSONAL_HOME/Backups"

cat > "$README_FILE" <<'EOF'
__README_CONTENT__
EOF

echo "Prepared Personal zone:"
echo "  home folder: $PERSONAL_HOME"
echo "  downloads: $DOWNLOADS_DIR"
echo "  notes: $NOTES_DIR"
echo "  scratch: $SCRATCH_DIR"
echo "  compose: $COMPOSE_DIR"
echo "  data: $DATA_DIR"
echo "  backups: $BACKUPS_DIR"
echo
echo "Disk posture:"
df -h "$HOME" /var | sed '1d'
'@

$remoteStatus = @'
set -euo pipefail

PERSONAL_HOME="$HOME/Personal"
CODE_ROOT="$HOME/code/personal"
DATA_DIR="$HOME/apex-data/personal"
BACKUPS_DIR="$HOME/apex-backups/personal"

echo "== personal zone paths =="
ls -ld "$PERSONAL_HOME" "$PERSONAL_HOME/Downloads" "$PERSONAL_HOME/Notes" "$PERSONAL_HOME/Scratch" 2>/dev/null || true
ls -ld "$PERSONAL_HOME/Compose" "$PERSONAL_HOME/Data" "$PERSONAL_HOME/Backups" 2>/dev/null || true
echo
echo "== backing paths =="
ls -ld "$CODE_ROOT" "$CODE_ROOT/compose" "$DATA_DIR" "$BACKUPS_DIR" 2>/dev/null || true
echo
echo "== disk posture =="
df -h "$HOME" /var | sed '1d'
echo
echo "== docker posture =="
docker info --format '{{.OSType}} {{.OperatingSystem}}' 2>/dev/null || true
'@

function Invoke-RemoteScript {
    param(
        [string]$ScriptBody
    )

    $normalized = $ScriptBody -replace "`r`n", "`n"
    $tempScript = [System.IO.Path]::GetTempFileName()
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($tempScript, $normalized, $utf8NoBom)

    try {
        $process = Start-Process -FilePath 'ssh' -ArgumentList @($HostAlias, 'bash -s') -NoNewWindow -Wait -PassThru -RedirectStandardInput $tempScript
        exit $process.ExitCode
    }
    finally {
        if (Test-Path $tempScript) {
            Remove-Item $tempScript -Force
        }
    }
}

switch ($Action) {
    'setup' {
        Invoke-RemoteScript ($remoteSetup.Replace('__README_CONTENT__', $readmeContent.Trim()))
    }
    'status' {
        Invoke-RemoteScript $remoteStatus
    }
}