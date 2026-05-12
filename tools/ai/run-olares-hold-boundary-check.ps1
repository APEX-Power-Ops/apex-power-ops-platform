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

Assert-ApexPacketId $PacketId

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile
$repoPython = Get-ApexRepoPython

$stateDir = Join-Path $repoRoot '.tmp/ai-workflow'
$logDir = Join-Path $stateDir 'logs'
$mcpContractActualDir = Join-Path $repoRoot 'tests/canary/mcp-contract/actual'
$deferredOpsActualDir = Join-Path $repoRoot 'tests/canary/deferred-ops-view-counts/actual'
$minimalStateFile = Join-Path $stateDir 'minimal-mcp-trio.json'
$liveDbPort = if ($env:APEX_HOLD_BOUNDARY_DB_PORT) { $env:APEX_HOLD_BOUNDARY_DB_PORT } else { '8721' }
$liveDbUrl = "http://127.0.0.1:$liveDbPort/mcp"
$liveDbRoot = Join-Path $repoRoot 'services/mcp/apex-db'
$liveDbLog = Join-Path $logDir 'live-hold-boundary-db.log'
$liveDbProcess = $null
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
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

function Test-HealthyEndpoint([string]$Url) {
  try {
    Invoke-WebRequest -Uri $Url -UseBasicParsing | Out-Null
    return $true
  }
  catch {
    return $false
  }
}

function Test-RepoPythonModule([string]$ModuleName) {
  & $repoPython '-c' "import $ModuleName" | Out-Null
  return $LASTEXITCODE -eq 0
}

function Start-LiveHoldBoundaryDb {
  $command = @(
    "`$env:APEX_MCP_HTTP_PORT = '$liveDbPort'",
    "`$env:APEX_DB_CONNECTION_STRING = '$($env:SEAM_DATABASE_URL)'",
    "Set-Location '$liveDbRoot'",
    "& 'node' 'build/http.js' *>> '$liveDbLog'"
  )

  return Start-Process pwsh -ArgumentList '-NoProfile', '-Command', ($command -join '; ') -PassThru
}

& (Join-Path $PSScriptRoot 'run-minimal-mcp-trio.ps1') -Action verify -PacketId $PacketId | Out-Null

$holdArgs = @(
  (Join-Path $PSScriptRoot 'check_deferred_ops_view_counts.py'),
  '--packet-id', $PacketId,
  '--output', $holdOutput
)

if (-not $DsnEnv -and (Test-Path $minimalStateFile)) {
  $minimalState = Get-Content $minimalStateFile -Raw | ConvertFrom-Json
  $endpointsProperty = $minimalState.PSObject.Properties['endpoints']
  if ($null -ne $endpointsProperty) {
    $dbEndpoint = [string]$endpointsProperty.Value.db
    if (-not [string]::IsNullOrWhiteSpace($dbEndpoint)) {
      $holdArgs += @('--db-url', $dbEndpoint)
    }
  }
}

if ($DsnEnv) {
  if (Test-RepoPythonModule 'sqlalchemy') {
    $holdArgs += @('--db-connection-string-env', 'SEAM_DATABASE_URL')
  }
  elseif (Test-Path (Join-Path $liveDbRoot 'build/http.js')) {
    $liveDbProcess = Start-LiveHoldBoundaryDb

    for ($attempt = 1; $attempt -le 30; $attempt++) {
      if (Test-HealthyEndpoint "http://127.0.0.1:$liveDbPort/health") {
        break
      }

      if ($attempt -eq 30) {
        throw "Timed out waiting for live hold-boundary apex-db on port $liveDbPort."
      }

      Start-Sleep -Milliseconds 500
    }

    $holdArgs += @('--db-url', $liveDbUrl)
  }
}

try {
  $holdHelperLines = & $repoPython @holdArgs
  $holdExitCode = $LASTEXITCODE
  if ($null -eq $holdHelperLines) {
    $holdHelperOutput = ''
  }
  elseif ($holdHelperLines -is [System.Array]) {
    $holdHelperOutput = ($holdHelperLines -join [Environment]::NewLine)
  }
  else {
    $holdHelperOutput = [string]$holdHelperLines
  }
}
finally {
  if ($null -ne $liveDbProcess -and -not $liveDbProcess.HasExited) {
    Stop-Process -Id $liveDbProcess.Id -Force
  }
}

if ($holdExitCode -ne 0 -and (Test-Path $holdOutput -PathType Leaf)) {
  exit $holdExitCode
}

if ($holdExitCode -ne 0 -and [string]::IsNullOrWhiteSpace($holdHelperOutput)) {
  exit $holdExitCode
}

$minimal = Get-Content $minimalOutput -Raw | ConvertFrom-Json
if (Test-Path $holdOutput -PathType Leaf) {
  $hold = Get-Content $holdOutput -Raw | ConvertFrom-Json
}
else {
  $hold = $holdHelperOutput | ConvertFrom-Json
}

$holdDecision = if ($hold.result -eq 'FAIL') {
  if ($hold.error) {
    $hold.error
  }
  elseif ($hold.output_error) {
    $hold.output_error
  }
  else {
    $hold.decision
  }
}
else {
  if ($hold.decision) {
    $hold.decision
  }
  elseif ($hold.error) {
    $hold.error
  }
  else {
    $hold.output_error
  }
}

$summary = [ordered]@{
  packet_id = $PacketId
  minimal_mcp = $minimal.result
  deferred_ops = $hold.result
  deferred_ops_decision = $holdDecision
  outputs = [ordered]@{
    minimal_mcp = $minimalOutput
    deferred_ops = $holdOutput
  }
}

$summary | ConvertTo-Json -Depth 6

if ($holdExitCode -ne 0) {
  exit $holdExitCode
}