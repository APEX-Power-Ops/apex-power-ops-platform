param(
  [string]$PacketId = '2026-05-06-olares-dev-residency-056',
  [string]$DsnEnv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\shell\common.ps1')

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile

$stateDir = Join-Path $repoRoot '.tmp/ai-workflow'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

$minimalOutput = Join-Path $stateDir 'verify-minimal-mcp-trio.json'
$holdOutput = Join-Path $stateDir 'deferred-ops-view-counts.json'

if ($DsnEnv) {
  $dsnValue = [Environment]::GetEnvironmentVariable($DsnEnv, 'Process')
  if (-not $dsnValue) {
    throw "$DsnEnv is not set; cannot run the hold-boundary cadence check against a live DSN."
  }
  $env:SEAM_DATABASE_URL = $dsnValue
}

& (Join-Path $PSScriptRoot 'run-minimal-mcp-trio.ps1') -Action verify -PacketId $PacketId | Out-Null

$holdArgs = @(
  (Join-Path $PSScriptRoot 'check_deferred_ops_view_counts.py'),
  '--packet-id', $PacketId,
  '--output', $holdOutput
)

if ($DsnEnv) {
  $holdArgs += @('--db-connection-string-env', 'SEAM_DATABASE_URL')
}

& 'c:/APEX Platform/.venv/Scripts/python.exe' @holdArgs | Out-Null

$minimal = Get-Content $minimalOutput -Raw | ConvertFrom-Json
$hold = Get-Content $holdOutput -Raw | ConvertFrom-Json

$summary = [ordered]@{
  packet_id = $PacketId
  minimal_mcp = $minimal.result
  deferred_ops = $hold.result
  deferred_ops_decision = $hold.decision
  outputs = [ordered]@{
    minimal_mcp = $minimalOutput
    deferred_ops = $holdOutput
  }
}

$summary | ConvertTo-Json -Depth 6