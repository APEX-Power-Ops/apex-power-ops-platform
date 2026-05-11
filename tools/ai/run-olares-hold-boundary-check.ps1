param(
  [string]$PacketId,
  [string]$DsnEnv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\shell\common.ps1')

if (-not $PSBoundParameters.ContainsKey('PacketId') -or [string]::IsNullOrWhiteSpace($PacketId)) {
  $PacketId = Get-ApexDefaultPacketId 'hold-boundary'
}

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile
$repoPython = Get-ApexRepoPython

$stateDir = Join-Path $repoRoot '.tmp/ai-workflow'
$mcpContractActualDir = Join-Path $repoRoot 'tests/canary/mcp-contract/actual'
$deferredOpsActualDir = Join-Path $repoRoot 'tests/canary/deferred-ops-view-counts/actual'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $mcpContractActualDir | Out-Null
New-Item -ItemType Directory -Force -Path $deferredOpsActualDir | Out-Null

$minimalOutput = Join-Path $mcpContractActualDir "verify-minimal-mcp-trio-$PacketId.json"
$holdOutput = Join-Path $deferredOpsActualDir "deferred-ops-view-counts-$PacketId.json"

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

& $repoPython @holdArgs | Out-Null

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