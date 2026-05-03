param(
    [ValidateSet('setup', 'config', 'up', 'down', 'status', 'credentials', 'tunnel-web', 'tunnel-rdp')]
    [string]$Action = 'status',

    [string]$HostAlias = 'olares@100.64.0.1',

    [string]$LabRoot = '$HOME/code/personal/compose/windows-lab',

    [string]$EnvFile = '$HOME/code/personal/.env.windows-lab',

    [int]$LocalWebPort = 8007,

    [int]$LocalRdpPort = 3391
)

$composeContent = @'
services:
  personal-windows-lab:
    image: dockurr/windows
    container_name: personal-windows-lab
    environment:
      VERSION: ${WINDOWS_VERSION:-10l}
      DISK_SIZE: ${WINDOWS_DISK_SIZE:-128G}
      RAM_SIZE: ${WINDOWS_RAM_SIZE:-4G}
      CPU_CORES: ${WINDOWS_CPU_CORES:-2}
      USERNAME: ${WINDOWS_USERNAME:-Personal}
      PASSWORD: ${WINDOWS_PASSWORD}
      LANGUAGE: ${WINDOWS_LANGUAGE:-English}
      REGION: ${WINDOWS_REGION:-en-US}
      KEYBOARD: ${WINDOWS_KEYBOARD:-en-US}
    devices:
      - /dev/kvm
      - /dev/net/tun
    cap_add:
      - NET_ADMIN
    ports:
      - "127.0.0.1:${WINDOWS_WEB_PORT:-8006}:8006"
      - "127.0.0.1:${WINDOWS_RDP_PORT:-3390}:3389/tcp"
      - "127.0.0.1:${WINDOWS_RDP_PORT:-3390}:3389/udp"
    volumes:
      - personal_windows_storage:/storage
      - ${WINDOWS_SHARED_ROOT:-/home/olares/Personal/Downloads}:/shared
    restart: unless-stopped
    stop_grace_period: 2m

volumes:
  personal_windows_storage:
    name: personal_windows_storage
'@

$setupScript = @'
set -euo pipefail

LAB_ROOT="__LAB_ROOT__"
ENV_FILE="__ENV_FILE__"
mkdir -p "$LAB_ROOT"
mkdir -p "$HOME/Personal/Downloads"
mkdir -p "$HOME/Personal/Notes"
mkdir -p "$HOME/Personal/Scratch"
mkdir -p "$HOME/code/personal"

if [ ! -f "$LAB_ROOT/compose.yml" ]; then
  cat > "$LAB_ROOT/compose.yml" <<'EOF'
__COMPOSE_CONTENT__
EOF
fi

if [ ! -f "$ENV_FILE" ]; then
  password="$(python3 - <<'PY'
import secrets
import string

alphabet = string.ascii_letters + string.digits
print(''.join(secrets.choice(alphabet) for _ in range(20)))
PY
)"
  cat > "$ENV_FILE" <<EOF
WINDOWS_VERSION=10l
WINDOWS_DISK_SIZE=128G
WINDOWS_RAM_SIZE=4G
WINDOWS_CPU_CORES=2
WINDOWS_WEB_PORT=8006
WINDOWS_RDP_PORT=3390
WINDOWS_LANGUAGE=English
WINDOWS_REGION=en-US
WINDOWS_KEYBOARD=en-US
WINDOWS_USERNAME=Personal
WINDOWS_PASSWORD=$password
WINDOWS_SHARED_ROOT=$HOME/Personal/Downloads
EOF
  chmod 600 "$ENV_FILE"
fi

echo "Prepared Windows Lab:"
echo "  compose root: $LAB_ROOT"
echo "  env file: $ENV_FILE"
echo "  shared folder: $HOME/Personal/Downloads"
echo "  docker volume: personal_windows_storage"
'@
$setupScript = $setupScript.Replace('__LAB_ROOT__', $LabRoot).Replace('__ENV_FILE__', $EnvFile).Replace('__COMPOSE_CONTENT__', $composeContent.Trim())

$configScript = @'
set -euo pipefail
cd "__LAB_ROOT__"
docker compose --env-file "__ENV_FILE__" config
'@
$configScript = $configScript.Replace('__LAB_ROOT__', $LabRoot).Replace('__ENV_FILE__', $EnvFile)

$upScript = @'
set -euo pipefail
cd "__LAB_ROOT__"
docker compose --env-file "__ENV_FILE__" up -d
'@
$upScript = $upScript.Replace('__LAB_ROOT__', $LabRoot).Replace('__ENV_FILE__', $EnvFile)

$downScript = @'
set -euo pipefail
cd "__LAB_ROOT__"
docker compose --env-file "__ENV_FILE__" down
'@
$downScript = $downScript.Replace('__LAB_ROOT__', $LabRoot).Replace('__ENV_FILE__', $EnvFile)

$statusScript = @'
set -euo pipefail
cd "__LAB_ROOT__"
set -a
. "__ENV_FILE__"
set +a

echo "== compose ps =="
docker compose --env-file "__ENV_FILE__" ps || true
echo

echo "== endpoints =="
echo "web viewer: http://127.0.0.1:${WINDOWS_WEB_PORT}"
echo "rdp: 127.0.0.1:${WINDOWS_RDP_PORT}"
echo

echo "== recent logs =="
docker logs --tail 20 personal-windows-lab 2>/dev/null || true
'@
$statusScript = $statusScript.Replace('__LAB_ROOT__', $LabRoot).Replace('__ENV_FILE__', $EnvFile)

$credentialsScript = @'
set -euo pipefail
set -a
. "__ENV_FILE__"
set +a

echo "Windows Lab credentials:"
echo "  Username: ${WINDOWS_USERNAME}"
echo "  Password: ${WINDOWS_PASSWORD}"
echo "  Web viewer URL on host: http://127.0.0.1:${WINDOWS_WEB_PORT}"
echo "  RDP port on host: 127.0.0.1:${WINDOWS_RDP_PORT}"
'@
$credentialsScript = $credentialsScript.Replace('__ENV_FILE__', $EnvFile)

function Invoke-RemoteScript {
    param([string]$ScriptBody)

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
    'setup' { Invoke-RemoteScript $setupScript }
    'config' { Invoke-RemoteScript $configScript }
    'up' { Invoke-RemoteScript $upScript }
    'down' { Invoke-RemoteScript $downScript }
    'status' { Invoke-RemoteScript $statusScript }
    'credentials' { Invoke-RemoteScript $credentialsScript }
    'tunnel-web' {
        & ssh `
            '-o' 'BatchMode=yes' `
            '-o' 'ExitOnForwardFailure=yes' `
            '-o' 'ServerAliveInterval=30' `
            '-o' 'ServerAliveCountMax=3' `
            '-o' 'TCPKeepAlive=yes' `
            '-N' `
            '-L' ("{0}:127.0.0.1:8006" -f $LocalWebPort) `
            $HostAlias
        exit $LASTEXITCODE
    }
    'tunnel-rdp' {
        & ssh `
            '-o' 'BatchMode=yes' `
            '-o' 'ExitOnForwardFailure=yes' `
            '-o' 'ServerAliveInterval=30' `
            '-o' 'ServerAliveCountMax=3' `
            '-o' 'TCPKeepAlive=yes' `
            '-N' `
            '-L' ("{0}:127.0.0.1:3390" -f $LocalRdpPort) `
            $HostAlias
        exit $LASTEXITCODE
    }
}
