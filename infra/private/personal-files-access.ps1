param(
    [ValidateSet('open', 'rotate-open', 'status')]
    [string]$Action = 'open',

    [string]$FilesUrl = 'https://files.jlswen2121.olares.com/Files/External/olares/',

    [string]$VaultTarget = 'APEX-Olares-Personal-Files-SMB'
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridgeScript = Join-Path $scriptRoot 'run-personal-files-samba-bridge-remote.ps1'

function Invoke-BridgeAction {
    param(
        [string]$BridgeAction
    )

    $output = & pwsh -NoProfile -File $bridgeScript -Action $BridgeAction 2>&1
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

    $requiredKeys = @('username', 'password', 'files_url', 'share')
    $missing = $requiredKeys | Where-Object { -not $map.ContainsKey($_) }
    if ($missing.Count -gt 0) {
        throw "Missing bridge credential fields: $($missing -join ', ')"
    }

    return $map
}

function Test-VaultTarget {
    $null = & cmdkey.exe "/list:$VaultTarget" 2>$null
    return $LASTEXITCODE -eq 0
}

function Write-ReconnectSummary {
    param(
        [hashtable]$CredentialMap,
        [bool]$VaultPresent
    )

    Write-Host 'Personal Files reconnect details'
    Write-Host "Files page: $FilesUrl"
    Write-Host "Share URL: $($CredentialMap['files_url'])"
    Write-Host "Username: $($CredentialMap['username'])"
    Write-Host "Password: $($CredentialMap['password'])"
    Write-Host "Share: $($CredentialMap['share'])"
    Write-Host "Vault target: $VaultTarget"
    Write-Host "Vault present: $(if ($VaultPresent) { 'yes' } else { 'no' })"
}

function Copy-ReconnectSummary {
    param(
        [hashtable]$CredentialMap,
        [bool]$VaultPresent
    )

    $summary = @(
        'Personal Files reconnect details'
        "Files page: $FilesUrl"
        "Share URL: $($CredentialMap['files_url'])"
        "Username: $($CredentialMap['username'])"
        "Password: $($CredentialMap['password'])"
        "Share: $($CredentialMap['share'])"
        "Vault target: $VaultTarget"
        "Vault present: $(if ($VaultPresent) { 'yes' } else { 'no' })"
    ) -join [Environment]::NewLine

    Set-Clipboard -Value $summary
}

switch ($Action) {
    'status' {
        $credentialMap = Get-CredentialMap
        $vaultPresent = Test-VaultTarget
        Write-ReconnectSummary -CredentialMap $credentialMap -VaultPresent $vaultPresent
        exit 0
    }

    'open' {
        $credentialMap = Get-CredentialMap
        $vaultPresent = Test-VaultTarget
        Copy-ReconnectSummary -CredentialMap $credentialMap -VaultPresent $vaultPresent
        Start-Process $FilesUrl | Out-Null
        Write-ReconnectSummary -CredentialMap $credentialMap -VaultPresent $vaultPresent
        Write-Host 'Reconnect details were copied to the clipboard.'
        exit 0
    }

    'rotate-open' {
        Invoke-BridgeAction -BridgeAction 'rotate-vault' | Out-Null
        $credentialMap = Get-CredentialMap
        $vaultPresent = Test-VaultTarget
        Copy-ReconnectSummary -CredentialMap $credentialMap -VaultPresent $vaultPresent
        Start-Process $FilesUrl | Out-Null
        Write-ReconnectSummary -CredentialMap $credentialMap -VaultPresent $vaultPresent
        Write-Host 'The bridge password was rotated, stored in Windows Credential Manager, and reconnect details were copied to the clipboard.'
        exit 0
    }
}