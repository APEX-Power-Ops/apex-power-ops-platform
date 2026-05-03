param(
    [ValidateSet('setup', 'rotate', 'status', 'credentials', 'vault', 'rotate-vault')]
    [string]$Action = 'status',

    [string]$HostAlias = 'olares@100.64.0.1',

    [string]$ShareName = 'personal',

    [string]$SharePath = '$HOME/Personal',

    [string]$SmbUser = 'personalshare',

    [string]$EnvFilePath = '$HOME/apex-secrets/personal/samba-personal-files.env',

    [string]$IncludeFile = '/etc/samba/smb-personal.conf',

    [string]$VaultTarget = 'APEX-Olares-Personal-Files-SMB'
)

$setupScript = @'
set -euo pipefail

SHARE_NAME="__SHARE_NAME__"
SHARE_PATH="__SHARE_PATH__"
SMB_USER="__SMB_USER__"
CREDENTIAL_FILE="__CREDENTIAL_FILE__"
INCLUDE_FILE="__INCLUDE_FILE__"
SMB_CONF="/etc/samba/smb.conf"
ALLOWED_HOSTS="127.0.0.1 10.233.0.0/16 100.64.0.0/10 192.168.0.0/16"
FORCE_ROTATE="__FORCE_ROTATE__"

mkdir -p "$(dirname "$CREDENTIAL_FILE")"

HOST_IP="$(kubectl get nodes -o wide --no-headers 2>/dev/null | awk 'NR==1 { print $6 }')"
if [ -z "$HOST_IP" ]; then
    HOST_IP="$(hostname -I | awk '{print $1}')"
fi

if [ -f "$CREDENTIAL_FILE" ]; then
    EXISTING_PASSWORD_LINE="$(grep '^SMB_PASSWORD=' "$CREDENTIAL_FILE" 2>/dev/null | tail -n 1 || true)"
    if [ -n "$EXISTING_PASSWORD_LINE" ]; then
        SMB_PASSWORD="${EXISTING_PASSWORD_LINE#SMB_PASSWORD=}"
        SMB_PASSWORD="${SMB_PASSWORD#\'}"
        SMB_PASSWORD="${SMB_PASSWORD%\'}"
    fi
fi

if [ "$FORCE_ROTATE" = "1" ] || [ -z "${SMB_PASSWORD:-}" ]; then
    SMB_PASSWORD="$(python3 - <<'PY'
import secrets
import string

alphabet = string.ascii_letters + string.digits
print(''.join(secrets.choice(alphabet) for _ in range(24)))
PY
)"
fi

if ! command -v smbd >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    sudo apt-get update
    sudo apt-get install -y samba
fi

if ! id -u "$SMB_USER" >/dev/null 2>&1; then
    sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$SMB_USER"
fi

printf '%s:%s\n' "$SMB_USER" "$SMB_PASSWORD" | sudo chpasswd

sudo mkdir -p "$SHARE_PATH"
sudo chown -R olares:olares "$SHARE_PATH"

sudo tee "$INCLUDE_FILE" >/dev/null <<EOF
[${SHARE_NAME}]
    path = ${SHARE_PATH}
    browseable = yes
    read only = no
    guest ok = no
    valid users = ${SMB_USER}
    force user = olares
    create mask = 0640
    directory mask = 0750
    hosts allow = ${ALLOWED_HOSTS}
EOF

sudo python3 - <<'PY'
from pathlib import Path

smb_conf = Path('/etc/samba/smb.conf')
include_line = 'include = __INCLUDE_FILE__'
text = smb_conf.read_text()
lines = [line for line in text.splitlines() if line.strip() != include_line]

insert_at = None
for index, line in enumerate(lines):
    stripped = line.strip()
    if stripped.lower() == '[global]':
        insert_at = index + 1
        break

if insert_at is None:
    raise SystemExit('Missing [global] section in smb.conf')

while insert_at < len(lines) and lines[insert_at].strip() == '':
    insert_at += 1

lines.insert(insert_at, include_line)
smb_conf.write_text('\n'.join(lines) + '\n')
PY

printf '%s\n%s\n' "$SMB_PASSWORD" "$SMB_PASSWORD" | sudo smbpasswd -a -s "$SMB_USER" >/dev/null

sudo testparm -s >/dev/null
sudo systemctl enable --now smbd
sudo systemctl restart smbd

WINDOWS_DIRECT_SMB_SUPPORTED=yes
WINDOWS_DIRECT_SMB_NOTE=
if command -v kubectl >/dev/null 2>&1; then
    if kubectl -n os-framework get svc files-samba -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null | grep -qx '445'; then
        WINDOWS_DIRECT_SMB_SUPPORTED=no
        WINDOWS_DIRECT_SMB_NOTE='Olares files-samba already owns LAN TCP 445 on the node IP. Use Files -> External with SMB_FILES_URL, then use the built-in Olares Files endpoint or LarePass sync on Windows instead of direct host SMB mapping.'
    fi
fi

{
    printf 'SMB_SERVER=%q\n' "$HOST_IP"
    printf 'SMB_SHARE=%q\n' "$SHARE_NAME"
    printf 'SMB_USERNAME=%q\n' "$SMB_USER"
    printf 'SMB_PASSWORD=%q\n' "$SMB_PASSWORD"
    printf 'SMB_URL=%q\n' "smb://${HOST_IP}/${SHARE_NAME}"
    printf 'SMB_ALT_URL=%q\n' "//${HOST_IP}/${SHARE_NAME}"
    printf 'SMB_FILES_URL=%q\n' "//127.0.0.1/${SHARE_NAME}"
    printf 'SMB_WINDOWS_DIRECT_SUPPORTED=%q\n' "$WINDOWS_DIRECT_SMB_SUPPORTED"
    printf 'SMB_WINDOWS_DIRECT_NOTE=%q\n' "$WINDOWS_DIRECT_SMB_NOTE"
    printf 'SHARE_PATH=%q\n' "$SHARE_PATH"
} > "$CREDENTIAL_FILE"
chmod 600 "$CREDENTIAL_FILE"

echo "Prepared Personal Files Samba bridge:"
echo "  share path: $SHARE_PATH"
echo "  server: $HOST_IP"
echo "  share: $SHARE_NAME"
echo "  username: $SMB_USER"
echo "  credential file: $CREDENTIAL_FILE"
'@
$setupScriptTemplate = $setupScript.Replace('__SHARE_NAME__', $ShareName).Replace('__SHARE_PATH__', $SharePath).Replace('__SMB_USER__', $SmbUser).Replace('__CREDENTIAL_FILE__', $EnvFilePath).Replace('__INCLUDE_FILE__', $IncludeFile)

$statusScript = @'
set -euo pipefail

CREDENTIAL_FILE="__CREDENTIAL_FILE__"
INCLUDE_FILE="__INCLUDE_FILE__"

echo "== samba service =="
sudo systemctl is-active smbd || true
echo
echo "== listening on 445 =="
sudo ss -ltnp | grep ':445' || true
echo
echo "== share include =="
sudo test -f "$INCLUDE_FILE" && sudo cat "$INCLUDE_FILE" || echo "Missing include file: $INCLUDE_FILE"
echo
echo "== credentials =="
if [ -f "$CREDENTIAL_FILE" ]; then
    sed 's/^SMB_PASSWORD=.*/SMB_PASSWORD=********/' "$CREDENTIAL_FILE"
else
    echo "Missing credential file: $CREDENTIAL_FILE"
fi
'@
$statusScript = $statusScript.Replace('__CREDENTIAL_FILE__', $EnvFilePath).Replace('__INCLUDE_FILE__', $IncludeFile)

$credentialsScript = @'
set -euo pipefail

CREDENTIAL_FILE="__CREDENTIAL_FILE__"

if [ ! -f "$CREDENTIAL_FILE" ]; then
    echo "Missing credential file: $CREDENTIAL_FILE" >&2
    exit 1
fi

set -a
. "$CREDENTIAL_FILE"
set +a

echo "Personal Files bridge credentials"
echo "server: ${SMB_SERVER}"
echo "share: ${SMB_SHARE}"
echo "username: ${SMB_USERNAME}"
echo "password: ${SMB_PASSWORD}"
echo "smb_url: ${SMB_URL}"
echo "alt_url: ${SMB_ALT_URL}"
echo "files_url: ${SMB_FILES_URL:-//127.0.0.1/${SMB_SHARE}}"
echo "share_path: ${SHARE_PATH}"
if [ -n "${SMB_WINDOWS_DIRECT_SUPPORTED:-}" ]; then
    echo "windows_direct_supported: ${SMB_WINDOWS_DIRECT_SUPPORTED}"
fi
if [ -n "${SMB_WINDOWS_DIRECT_NOTE:-}" ]; then
    echo "windows_direct_note: ${SMB_WINDOWS_DIRECT_NOTE}"
fi
'@
$credentialsScript = $credentialsScript.Replace('__CREDENTIAL_FILE__', $EnvFilePath)

$credentialEnvScript = @'
set -euo pipefail

CREDENTIAL_FILE="__CREDENTIAL_FILE__"

if [ ! -f "$CREDENTIAL_FILE" ]; then
    echo "Missing credential file: $CREDENTIAL_FILE" >&2
    exit 1
fi

set -a
. "$CREDENTIAL_FILE"
set +a

printf 'SMB_SERVER=%s\n' "$SMB_SERVER"
printf 'SMB_SHARE=%s\n' "$SMB_SHARE"
printf 'SMB_USERNAME=%s\n' "$SMB_USERNAME"
printf 'SMB_PASSWORD=%s\n' "$SMB_PASSWORD"
printf 'SMB_URL=%s\n' "$SMB_URL"
printf 'SMB_ALT_URL=%s\n' "$SMB_ALT_URL"
printf 'SMB_FILES_URL=%s\n' "${SMB_FILES_URL:-//127.0.0.1/${SMB_SHARE}}"
printf 'SMB_WINDOWS_DIRECT_SUPPORTED=%s\n' "${SMB_WINDOWS_DIRECT_SUPPORTED:-yes}"
printf 'SMB_WINDOWS_DIRECT_NOTE=%s\n' "${SMB_WINDOWS_DIRECT_NOTE:-}"
printf 'SHARE_PATH=%s\n' "$SHARE_PATH"
'@
$credentialEnvScript = $credentialEnvScript.Replace('__CREDENTIAL_FILE__', $EnvFilePath)

function Invoke-RemoteScriptCapture {
    param(
        [string]$ScriptBody
    )

    $normalized = $ScriptBody -replace "`r`n", "`n"
    $tempScript = [System.IO.Path]::GetTempFileName()
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($tempScript, $normalized, $utf8NoBom)

    try {
        $process = Start-Process -FilePath 'ssh' -ArgumentList @($HostAlias, 'bash -s') -NoNewWindow -Wait -PassThru -RedirectStandardInput $tempScript -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        $stdout = if (Test-Path $stdoutFile) { [System.IO.File]::ReadAllText($stdoutFile) } else { '' }
        $stderr = if (Test-Path $stderrFile) { [System.IO.File]::ReadAllText($stderrFile) } else { '' }

        if ($process.ExitCode -ne 0) {
            $detail = ($stderr.Trim(), $stdout.Trim() | Where-Object { $_ }) -join [Environment]::NewLine
            if (-not $detail) {
                $detail = "Remote script failed with exit code $($process.ExitCode)."
            }
            throw $detail
        }

        [pscustomobject]@{
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

function Get-RemoteCredentialMap {
    $result = Invoke-RemoteScriptCapture $credentialEnvScript
    $map = @{}

    foreach ($line in ($result.StdOut -split "`r?`n")) {
        if ($line -match '^(?<key>[A-Z_]+)=(?<value>.*)$') {
            $map[$matches['key']] = $matches['value']
        }
    }

    $requiredKeys = @('SMB_USERNAME', 'SMB_PASSWORD', 'SMB_FILES_URL', 'SMB_SHARE')
    $missing = $requiredKeys | Where-Object { -not $map.ContainsKey($_) }
    if ($missing.Count -gt 0) {
        throw "Missing credential fields: $($missing -join ', ')"
    }

    return $map
}

function Sync-CredentialToVault {
    param(
        [hashtable]$CredentialMap
    )

    $null = & cmdkey.exe "/delete:$VaultTarget" 2>$null
    $null = & cmdkey.exe "/generic:$VaultTarget" "/user:$($CredentialMap['SMB_USERNAME'])" "/pass:$($CredentialMap['SMB_PASSWORD'])"

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to store credential in Windows Credential Manager target $VaultTarget."
    }

    $vaultCheck = & cmdkey.exe "/list:$VaultTarget"
    if ($LASTEXITCODE -ne 0) {
        throw "Credential Manager target $VaultTarget was not found after write."
    }

    Write-Output "Stored Personal Files bridge credential in Windows Credential Manager:"
    Write-Output "  target: $VaultTarget"
    Write-Output "  user: $($CredentialMap['SMB_USERNAME'])"
    Write-Output "  files_url: $($CredentialMap['SMB_FILES_URL'])"
}

switch ($Action) {
    'setup' {
        Invoke-RemoteScript ($setupScriptTemplate.Replace('__FORCE_ROTATE__', '0'))
    }
    'rotate' {
        Invoke-RemoteScript ($setupScriptTemplate.Replace('__FORCE_ROTATE__', '1'))
    }
    'status' {
        Invoke-RemoteScript $statusScript
    }
    'credentials' {
        Invoke-RemoteScript $credentialsScript
    }
    'vault' {
        $credentialMap = Get-RemoteCredentialMap
        Sync-CredentialToVault $credentialMap
    }
    'rotate-vault' {
        Invoke-RemoteScript ($setupScriptTemplate.Replace('__FORCE_ROTATE__', '1'))
        $credentialMap = Get-RemoteCredentialMap
        Sync-CredentialToVault $credentialMap
    }
}