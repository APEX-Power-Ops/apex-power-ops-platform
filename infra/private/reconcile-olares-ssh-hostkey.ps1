param(
    [Parameter(Mandatory = $true)]
    [string]$ExpectedFingerprint,

    [string]$KnownHostsFile = 'C:/Users/jjswe/.ssh/known_hosts',

    [string[]]$Hosts = @('jlswen2121.olares.com'),

    [switch]$ValidateOnly
)

$tempDir = Join-Path $env:TEMP ("olares-hostkey-" + [guid]::NewGuid().ToString())
$null = New-Item -ItemType Directory -Path $tempDir -Force

try {
    $scanFile = Join-Path $tempDir 'scanned_known_hosts'
    $verifiedEntries = @()
    $normalizedExpectedFingerprint = $ExpectedFingerprint.Trim().TrimEnd('.')

    function Get-ScannedHostEntry {
        param(
            [string]$TargetHost,
            [string]$OutputFile
        )

        $keyscanOutput = & ssh-keyscan -T 10 -t ed25519 $TargetHost 2>$null
        if ($keyscanOutput) {
            Set-Content -Path $OutputFile -Value $keyscanOutput
            return $keyscanOutput
        }

        $captureFile = Join-Path $tempDir ("capture-" + ($TargetHost -replace '[^A-Za-z0-9._-]', '_') + '.known_hosts')
        if (Test-Path $captureFile) {
            Remove-Item $captureFile -Force
        }

        $sshArgs = @(
            '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=accept-new',
            '-o', "UserKnownHostsFile=$captureFile",
            $TargetHost,
            'exit'
        )

        & ssh @sshArgs 2>$null | Out-Null

        if (-not (Test-Path $captureFile)) {
            throw "Could not fetch an SSH host key for $TargetHost via ssh-keyscan or temporary ssh capture."
        }

        $capturedEntry = Get-Content -Path $captureFile
        if (-not $capturedEntry) {
            throw "Temporary ssh capture for $TargetHost did not record a host key."
        }

        Set-Content -Path $OutputFile -Value $capturedEntry
        return $capturedEntry
    }

    foreach ($targetHost in $Hosts) {
        $capturedEntries = Get-ScannedHostEntry -TargetHost $targetHost -OutputFile $scanFile
        $fingerprintLine = & ssh-keygen -lf $scanFile -E sha256
        if (-not $fingerprintLine) {
            throw "Could not derive a fingerprint for $targetHost."
        }

        $actualFingerprint = (($fingerprintLine -split '\s+')[1]).Trim().TrimEnd('.')
        if ($actualFingerprint -ne $normalizedExpectedFingerprint) {
            throw "Fingerprint mismatch for $targetHost. Expected $normalizedExpectedFingerprint but received $actualFingerprint."
        }

        $verifiedEntries += $capturedEntries
    }

    if ($ValidateOnly) {
        Write-Host "Validated fingerprint $normalizedExpectedFingerprint for hosts: $($Hosts -join ', ')"
        return
    }

    foreach ($targetHost in $Hosts) {
        & ssh-keygen -R $targetHost -f $KnownHostsFile | Out-Null
    }

    Add-Content -Path $KnownHostsFile -Value $verifiedEntries
    Write-Host "Updated $KnownHostsFile for hosts: $($Hosts -join ', ')"
    Write-Host "Accepted fingerprint: $normalizedExpectedFingerprint"
}
finally {
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
