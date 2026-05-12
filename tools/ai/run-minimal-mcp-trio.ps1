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

Assert-ApexPacketId $PacketId

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile
$repoPython = Get-ApexRepoPython
$fsPort = if ($env:APEX_DEV_MCP_FS_PORT) { $env:APEX_DEV_MCP_FS_PORT } else { '8810' }
$dbPort = if ($env:APEX_DEV_MCP_DB_PORT) { $env:APEX_DEV_MCP_DB_PORT } else { '8811' }
$jobsPort = if ($env:APEX_DEV_MCP_JOBS_PORT) { $env:APEX_DEV_MCP_JOBS_PORT } else { '8812' }
$managedReadyAttempts = if ($env:APEX_MINIMAL_MCP_READY_ATTEMPTS) { [int]$env:APEX_MINIMAL_MCP_READY_ATTEMPTS } else { 50 }
$managedReadyIntervalSeconds = if ($env:APEX_MINIMAL_MCP_READY_INTERVAL_SECONDS) { [double]$env:APEX_MINIMAL_MCP_READY_INTERVAL_SECONDS } else { 0.2 }

$stateDir = Join-Path $repoRoot '.tmp/ai-workflow'
$logDir = Join-Path $stateDir 'logs'
$stateFile = Join-Path $stateDir 'minimal-mcp-trio.json'
$ledgerPath = Join-Path $repoRoot '.apex-data/apex-jobs-ledger.json'
$mcpContractActualDir = Join-Path $repoRoot 'tests/canary/mcp-contract/actual'
$fsEndpoint = "http://127.0.0.1:$fsPort/mcp"
$dbEndpoint = "http://127.0.0.1:$dbPort/mcp"
$jobsEndpoint = "http://127.0.0.1:$jobsPort/mcp"

New-Item -ItemType Directory -Force -Path $stateDir, $logDir, $mcpContractActualDir | Out-Null

$managedEntrypoints = @(
  'services/mcp/apex-fs/build/http.js',
  'services/mcp/apex-db/build/http.js',
  'services/mcp/apex-jobs/build/http.js'
)

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
  $existing = Read-State
  $stateEndpoints = $null
  if ($null -ne $existing) {
    $endpointsProperty = $existing.PSObject.Properties['endpoints']
    if ($null -ne $endpointsProperty) {
      $stateEndpoints = $endpointsProperty.Value
    }
  }

  if (-not $packetIdWasProvided) {
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

  if (
    $null -ne $stateEndpoints -and
    -not [string]::IsNullOrWhiteSpace($stateEndpoints.fs) -and
    -not [string]::IsNullOrWhiteSpace($stateEndpoints.db) -and
    -not [string]::IsNullOrWhiteSpace($stateEndpoints.jobs)
  ) {
    $verifyArgs += @(
      '--fs-url', [string]$stateEndpoints.fs,
      '--db-url', [string]$stateEndpoints.db,
      '--jobs-url', [string]$stateEndpoints.jobs
    )
  }

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

function Get-MissingManagedEntrypoints {
  return @(
    foreach ($entrypoint in $managedEntrypoints) {
      $fullPath = Join-Path $repoRoot $entrypoint
      if (-not (Test-Path $fullPath -PathType Leaf)) {
        $entrypoint
      }
    }
  )
}

function Get-ManagedReadinessState($processes, $endpoints) {
  $fsProcess = $processes | Where-Object { $_.name -eq 'apex-fs' } | Select-Object -First 1
  $dbProcess = $processes | Where-Object { $_.name -eq 'apex-db' } | Select-Object -First 1
  $jobsProcess = $processes | Where-Object { $_.name -eq 'apex-jobs' } | Select-Object -First 1

  $fsProcessRunning = $null -ne $fsProcess -and (Get-ProcessStatus $fsProcess.pid)
  $dbProcessRunning = $null -ne $dbProcess -and (Get-ProcessStatus $dbProcess.pid)
  $jobsProcessRunning = $null -ne $jobsProcess -and (Get-ProcessStatus $jobsProcess.pid)

  $fsReady = $fsProcessRunning -and (Test-McpEndpoint $endpoints.fs)
  $dbReady = $dbProcessRunning -and (Test-McpEndpoint $endpoints.db)
  $jobsReady = $jobsProcessRunning -and (Test-McpEndpoint $endpoints.jobs)

  return [pscustomobject]@{
    fs_process_running = [bool]$fsProcessRunning
    db_process_running = [bool]$dbProcessRunning
    jobs_process_running = [bool]$jobsProcessRunning
    fs_ready = [bool]$fsReady
    db_ready = [bool]$dbReady
    jobs_ready = [bool]$jobsReady
    all_ready = [bool]$fsReady -and [bool]$dbReady -and [bool]$jobsReady
  }
}

function Wait-ManagedEndpointsReady($processes, $endpoints) {
  $lastState = $null

  for ($attempt = 1; $attempt -le $managedReadyAttempts; $attempt++) {
    $lastState = Get-ManagedReadinessState -processes $processes -endpoints $endpoints
    if ($lastState.all_ready) {
      return $lastState
    }

    if (-not $lastState.fs_process_running -or -not $lastState.db_process_running -or -not $lastState.jobs_process_running) {
      return $lastState
    }

    if ($attempt -lt $managedReadyAttempts) {
      Start-Sleep -Seconds $managedReadyIntervalSeconds
    }
  }

  return $lastState
}

function Stop-ManagedProcesses($processes) {
  foreach ($process in $processes) {
    if (Get-ProcessStatus $process.pid) {
      Stop-Process -Id $process.pid -Force -ErrorAction SilentlyContinue
    }
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
    if ($null -ne $existing -and $existing.mode -ne 'adopted') {
      $running = @($existing.processes | Where-Object { Get-ProcessStatus $_.pid })
      if ($running.Count -eq $existing.processes.Count) {
        Write-Output '{"status":"already-running"}'
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
      Write-Output '{"status":"adopted"}'
      break
    }

    $missingEntrypoints = @(Get-MissingManagedEntrypoints)
    if ($missingEntrypoints.Count -gt 0) {
      [pscustomobject]@{
        status = 'start-refused'
        reason = 'missing-service-entrypoints'
        missing_entrypoints = $missingEntrypoints
      } | ConvertTo-Json -Depth 6 -Compress
      exit 1
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

    $readyState = Wait-ManagedEndpointsReady -processes $processes -endpoints $endpoints
    if (-not $readyState.all_ready) {
      Stop-ManagedProcesses -processes $processes
      [pscustomobject]@{
        status = 'start-refused'
        reason = 'services-not-ready'
        fs_running = $readyState.fs_process_running
        db_running = $readyState.db_process_running
        jobs_running = $readyState.jobs_process_running
        fs_ready = $readyState.fs_ready
        db_ready = $readyState.db_ready
        jobs_ready = $readyState.jobs_ready
      } | ConvertTo-Json -Depth 6 -Compress
      exit 1
    }

    $state = [pscustomobject]@{
      started_at = (Get-Date).ToString('o')
      packet_id = $PacketId
      mode = 'managed'
      processes = $processes
      endpoints = $endpoints
      ledger_path = $ledgerPath
    }

    Write-State $state
    Write-Output '{"status":"started"}'
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

    if ($existing.mode -eq 'adopted') {
      $fsRunning = Test-McpEndpoint $existing.endpoints.fs
      $dbRunning = Test-McpEndpoint $existing.endpoints.db
      $jobsRunning = Test-McpEndpoint $existing.endpoints.jobs
    }
    else {
      $managedStatus = Get-ManagedReadinessState -processes $existing.processes -endpoints $existing.endpoints
      $fsRunning = $managedStatus.fs_ready
      $dbRunning = $managedStatus.db_ready
      $jobsRunning = $managedStatus.jobs_ready
    }
    $allRunning = [bool]$fsRunning -and [bool]$dbRunning -and [bool]$jobsRunning
    $statusValue = if ($allRunning) {
      if ($existing.mode -eq 'adopted') { 'adopted-running' } else { 'managed-running' }
    }
    else {
      'not-running'
    }

    $status = [pscustomobject]@{
      status = $statusValue
      started_at = $existing.started_at
      packet_id = $existing.packet_id
      mode = $existing.mode
      fs_running = [bool]$fsRunning
      db_running = [bool]$dbRunning
      jobs_running = [bool]$jobsRunning
      ledger_path = $existing.ledger_path
      fs_endpoint = $existing.endpoints.fs
      db_endpoint = $existing.endpoints.db
      jobs_endpoint = $existing.endpoints.jobs
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
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
  }
}