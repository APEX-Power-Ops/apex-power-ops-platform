param(
  [ValidateSet('up', 'down', 'status', 'verify')]
  [string]$Action = 'status',
  [string]$PacketId = '2026-05-06-olares-dev-residency-037'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\shell\common.ps1')

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile

$stateDir = Join-Path $repoRoot '.tmp/ai-workflow'
$logDir = Join-Path $stateDir 'logs'
$stateFile = Join-Path $stateDir 'minimal-mcp-trio.json'
$ledgerPath = Join-Path $repoRoot '.apex-data/apex-jobs-ledger.json'

New-Item -ItemType Directory -Force -Path $stateDir, $logDir | Out-Null

function Get-DbConnectionString {
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
  $verifyArgs = @(
    'tools/ai/verify_minimal_mcp_trio.py',
    '--packet-id', $PacketId,
    '--output', (Join-Path $stateDir 'verify-minimal-mcp-trio.json')
  )
  & 'c:/APEX Platform/.venv/Scripts/python.exe' @verifyArgs
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

switch ($Action) {
  'up' {
    $endpoints = [pscustomobject]@{
      fs = "http://127.0.0.1:$($env:APEX_DEV_MCP_FS_PORT)/mcp"
      db = "http://127.0.0.1:$($env:APEX_DEV_MCP_DB_PORT)/mcp"
      jobs = "http://127.0.0.1:$($env:APEX_DEV_MCP_JOBS_PORT)/mcp"
    }

    $existing = Read-State
    if ($null -ne $existing) {
      $running = @($existing.processes | Where-Object { Get-ProcessStatus $_.pid })
      if ($running.Count -eq $existing.processes.Count) {
        $existing | ConvertTo-Json -Depth 6
        break
      }
    }

    if ((Test-HealthyEndpoint "http://127.0.0.1:$($env:APEX_DEV_MCP_FS_PORT)/health") -and
        (Test-HealthyEndpoint "http://127.0.0.1:$($env:APEX_DEV_MCP_DB_PORT)/health") -and
        (Test-HealthyEndpoint "http://127.0.0.1:$($env:APEX_DEV_MCP_JOBS_PORT)/health")) {
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
        'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_FS_PORT
        'APEX_MCP_WORKSPACE_ROOT' = $repoRoot
        'APEX_MCP_DATA_ROOT' = (Join-Path $repoRoot '.apex-data')
      }
      Start-ManagedProcess -Name 'apex-db' -ArgumentList @('services/mcp/apex-db/build/http.js') -Environment @{
        'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_DB_PORT
        'APEX_DB_CONNECTION_STRING' = $dbConnectionString
      }
      Start-ManagedProcess -Name 'apex-jobs' -ArgumentList @('services/mcp/apex-jobs/build/http.js') -Environment @{
        'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_JOBS_PORT
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
      Write-Output '{"status":"not-running"}'
      break
    }

    $status = [pscustomobject]@{
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