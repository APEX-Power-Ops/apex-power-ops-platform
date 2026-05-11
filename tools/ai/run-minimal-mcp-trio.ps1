param(
  [ValidateSet('up', 'down', 'status', 'verify')]
  [string]$Action = 'status',
  [string]$PacketId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\shell\common.ps1')

$packetIdWasProvided = $PSBoundParameters.ContainsKey('PacketId') -and -not [string]::IsNullOrWhiteSpace($PacketId)

if (-not $packetIdWasProvided) {
  $PacketId = Get-ApexDefaultPacketId 'minimal-mcp-trio'
}

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile
$repoPython = Get-ApexRepoPython
$fsPort = if ($env:APEX_DEV_MCP_FS_PORT) { $env:APEX_DEV_MCP_FS_PORT } else { '8810' }
$dbPort = if ($env:APEX_DEV_MCP_DB_PORT) { $env:APEX_DEV_MCP_DB_PORT } else { '8811' }
$jobsPort = if ($env:APEX_DEV_MCP_JOBS_PORT) { $env:APEX_DEV_MCP_JOBS_PORT } else { '8812' }

$stateDir = Join-Path $repoRoot '.tmp/ai-workflow'
$logDir = Join-Path $stateDir 'logs'
$stateFile = Join-Path $stateDir 'minimal-mcp-trio.json'
$ledgerPath = Join-Path $repoRoot '.apex-data/apex-jobs-ledger.json'
$mcpContractActualDir = Join-Path $repoRoot 'tests/canary/mcp-contract/actual'
$fsEndpoint = "http://127.0.0.1:$fsPort/mcp"
$dbEndpoint = "http://127.0.0.1:$dbPort/mcp"
$jobsEndpoint = "http://127.0.0.1:$jobsPort/mcp"

New-Item -ItemType Directory -Force -Path $stateDir, $logDir, $mcpContractActualDir | Out-Null

function Get-DbConnectionString {
  if ($env:SEAM_DATABASE_URL) {
    return $env:SEAM_DATABASE_URL
  }

  if ($env:APEX_DB_CONNECTION_STRING) {
    return $env:APEX_DB_CONNECTION_STRING
  }

  if ($env:DATABASE_URL) {
    return $env:DATABASE_URL
  }

  if ($env:APEX_DEV_POSTGRES_USER -and $env:APEX_DEV_POSTGRES_PASSWORD -and $env:APEX_DEV_POSTGRES_DB -and $env:APEX_DEV_POSTGRES_PORT) {
    return "postgresql://$($env:APEX_DEV_POSTGRES_USER):$($env:APEX_DEV_POSTGRES_PASSWORD)@127.0.0.1:$($env:APEX_DEV_POSTGRES_PORT)/$($env:APEX_DEV_POSTGRES_DB)"
  }

  return $null
}

function Read-State {
  if (-not (Test-Path $stateFile)) {
    return $null
  }

  return Get-Content $stateFile -Raw | ConvertFrom-Json
}

function Write-State($state) {
  $state | ConvertTo-Json -Depth 6 | Set-Content -Path $stateFile -Encoding UTF8
}

function Get-ProcessStatus([int]$Id) {
  $process = Get-Process -Id $Id -ErrorAction SilentlyContinue
  return $null -ne $process
}

function Start-ManagedProcess {
  param(
    [string]$Name,
    [string[]]$ArgumentList,
    [hashtable]$Environment
  )

  $commands = @()
  foreach ($key in $Environment.Keys) {
    $value = [string]$Environment[$key]
    $commands += "`$env:$key = '$value'"
  }

  $commands += "Set-Location '$repoRoot'"
  $quotedArgs = @($ArgumentList | ForEach-Object { "'$_'" }) -join ' '
  $commands += "& 'node' $quotedArgs *>> '$((Join-Path $logDir ($Name + '.log')))'"

  $process = Start-Process pwsh -ArgumentList '-NoProfile', '-Command', ($commands -join '; ') -PassThru
  return [pscustomobject]@{
    name = $Name
    pid = $process.Id
    log = (Join-Path $logDir ($Name + '.log'))
  }
}

function Invoke-Verify {
  if (-not $packetIdWasProvided) {
    $existing = Read-State
    if ($null -ne $existing -and -not [string]::IsNullOrWhiteSpace($existing.packet_id)) {
      $PacketId = $existing.packet_id
    }
  }

  $verifyOutput = Join-Path $mcpContractActualDir "verify-minimal-mcp-trio-$PacketId.json"
  $verifyArgs = @(
    'tools/ai/verify_minimal_mcp_trio.py',
    '--packet-id', $PacketId,
    '--output', $verifyOutput
  )
  & $repoPython @verifyArgs
}

function Test-McpEndpoint([string]$Url) {
  try {
    $payload = @{
      jsonrpc = '2.0'
      id = 0
      method = 'initialize'
      params = @{
        protocolVersion = '2025-03-26'
        capabilities = @{}
        clientInfo = @{
          name = 'minimal-mcp-trio'
          version = '0.1.0'
        }
      }
    } | ConvertTo-Json -Depth 5 -Compress

    Invoke-WebRequest -Uri $Url -Method Post -ContentType 'application/json' -Body $payload -UseBasicParsing | Out-Null
    return $true
  }
  catch {
    return $false
  }
}

switch ($Action) {
  'up' {
    $endpoints = [pscustomobject]@{
      fs = $fsEndpoint
      db = $dbEndpoint
      jobs = $jobsEndpoint
    }

    $existing = Read-State
    if ($null -ne $existing) {
      $running = @($existing.processes | Where-Object { Get-ProcessStatus $_.pid })
      if ($running.Count -eq $existing.processes.Count) {
        $existing | ConvertTo-Json -Depth 6
        break
      }
    }

    if ((Test-McpEndpoint $fsEndpoint) -and
      (Test-McpEndpoint $dbEndpoint) -and
      (Test-McpEndpoint $jobsEndpoint)) {
      $ownershipArgs = @(
        'tools/ai/check_apex_fs_ownership.py',
        '--fs-url', $fsEndpoint,
        '--expected-workspace-root', $repoRoot,
        '--expected-readme-path', (Join-Path $repoRoot 'README.md')
      )
      $ownershipProbe = (& $repoPython @ownershipArgs) | Out-String
      if ($LASTEXITCODE -ne 0) {
        $ownershipProbe.Trim()
        exit 1
      }

      $adoptedState = [pscustomobject]@{
        started_at = (Get-Date).ToString('o')
        packet_id = $PacketId
        mode = 'adopted'
        processes = @()
        endpoints = $endpoints
        ledger_path = $ledgerPath
      }
      Write-State $adoptedState
      $adoptedState | ConvertTo-Json -Depth 6
      break
    }

    $dbConnectionString = Get-DbConnectionString
    $processes = @(
      Start-ManagedProcess -Name 'apex-fs' -ArgumentList @('services/mcp/apex-fs/build/http.js') -Environment @{
        'APEX_MCP_HTTP_PORT' = $fsPort
        'APEX_MCP_WORKSPACE_ROOT' = $repoRoot
        'APEX_MCP_DATA_ROOT' = (Join-Path $repoRoot '.apex-data')
      }
      Start-ManagedProcess -Name 'apex-db' -ArgumentList @('services/mcp/apex-db/build/http.js') -Environment @{
        'APEX_MCP_HTTP_PORT' = $dbPort
        'APEX_DB_CONNECTION_STRING' = $dbConnectionString
      }
      Start-ManagedProcess -Name 'apex-jobs' -ArgumentList @('services/mcp/apex-jobs/build/http.js') -Environment @{
        'APEX_MCP_HTTP_PORT' = $jobsPort
        'APEX_JOBS_LEDGER_PATH' = $ledgerPath
      }
    )

    $state = [pscustomobject]@{
      started_at = (Get-Date).ToString('o')
      packet_id = $PacketId
      mode = 'managed'
      processes = $processes
      endpoints = $endpoints
      ledger_path = $ledgerPath
    }

    Write-State $state
    $state | ConvertTo-Json -Depth 6
  }
  'down' {
    $existing = Read-State
    if ($null -eq $existing) {
      Write-Output '{"status":"not-running"}'
      break
    }

    foreach ($process in $existing.processes) {
      if (Get-ProcessStatus $process.pid) {
        Stop-Process -Id $process.pid -Force
      }
    }

    Remove-Item $stateFile -Force -ErrorAction SilentlyContinue
    Write-Output '{"status":"stopped"}'
  }
  'status' {
    $existing = Read-State
    if ($null -eq $existing) {
        if ((Test-McpEndpoint $fsEndpoint) -and
          (Test-McpEndpoint $dbEndpoint) -and
          (Test-McpEndpoint $jobsEndpoint)) {
        $unmanaged = [ordered]@{
          status = 'unmanaged-running'
          mode = 'unmanaged'
          fs_running = $true
          db_running = $true
          jobs_running = $true
          ledger_path = $ledgerPath
          fs_endpoint = $fsEndpoint
          db_endpoint = $dbEndpoint
          jobs_endpoint = $jobsEndpoint
        }

        $unmanaged | ConvertTo-Json -Depth 6
        break
      }

      Write-Output '{"status":"not-running"}'
      break
    }

    $statusValue = if ($existing.mode -eq 'adopted') { 'adopted-running' } else { 'managed-running' }

    $status = [pscustomobject]@{
      status = $statusValue
      started_at = $existing.started_at
      packet_id = $existing.packet_id
      mode = $existing.mode
      ledger_path = $existing.ledger_path
      endpoints = $existing.endpoints
      processes = @(
        foreach ($process in $existing.processes) {
          [pscustomobject]@{
            name = $process.name
            pid = $process.pid
            running = (Get-ProcessStatus $process.pid)
            log = $process.log
          }
        }
      )
    }

    $status | ConvertTo-Json -Depth 6
  }
  'verify' {
    Invoke-Verify
  }
}