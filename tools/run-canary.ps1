Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'shell/common.ps1')

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile
$repoPython = Get-ApexRepoPython

$processes = @()

function Test-HealthyEndpoint {
  param(
    [string]$Url
  )

  try {
    Invoke-WebRequest -Uri $Url -UseBasicParsing | Out-Null
    return $true
  }
  catch {
    return $false
  }
}

function Wait-ApexEndpoint {
  param(
    [string]$Name,
    [string]$Url,
    [int]$MaxAttempts = 30
  )

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    if (Test-HealthyEndpoint $Url) {
      return
    }

    Start-Sleep -Milliseconds 500
  }

  throw "Timed out waiting for $Name at $Url"
}

function Start-ApexBackgroundProcess {
  param(
    [string]$FilePath,
    [string[]]$ArgumentList,
    [hashtable]$Environment = @{}
  )

  $command = @()
  foreach ($key in $Environment.Keys) {
    $value = [string]$Environment[$key]
    $command += "`$env:$key = '$value'"
  }

  $command += "Set-Location '$repoRoot'"
  $quotedArgs = $ArgumentList | ForEach-Object { "'$_'" }
  $command += "& '$FilePath' $($quotedArgs -join ' ')"

  $process = Start-Process pwsh -ArgumentList '-NoProfile', '-Command', ($command -join '; ') -PassThru
  $script:processes += $process
}

try {
  $formsTemplates = Join-Path $repoRoot '.tmp/forms-engine/templates'
  $formsArtifacts = Join-Path $repoRoot '.tmp/forms-engine/artifacts'
  $p6Artifacts = Join-Path $repoRoot '.tmp/p6-ingest/artifacts'
  New-Item -ItemType Directory -Force -Path $formsTemplates, $formsArtifacts, $p6Artifacts | Out-Null

  $formsRuntimePort = if ($env:APEX_DEV_FORMS_ENGINE_PORT) { $env:APEX_DEV_FORMS_ENGINE_PORT } else { '8080' }
  $p6RuntimePort = if ($env:APEX_DEV_P6_INGEST_PORT) { $env:APEX_DEV_P6_INGEST_PORT } else { '8081' }
  $fsMcpPort = if ($env:APEX_DEV_MCP_FS_PORT) { $env:APEX_DEV_MCP_FS_PORT } else { '8810' }
  $dbMcpPort = if ($env:APEX_DEV_MCP_DB_PORT) { $env:APEX_DEV_MCP_DB_PORT } else { '8811' }
  $jobsMcpPort = if ($env:APEX_DEV_MCP_JOBS_PORT) { $env:APEX_DEV_MCP_JOBS_PORT } else { '8812' }
  $p6McpPort = if ($env:APEX_DEV_MCP_P6_PORT) { $env:APEX_DEV_MCP_P6_PORT } else { '8713' }
  $formsMcpPort = if ($env:APEX_DEV_MCP_FORMS_PORT) { $env:APEX_DEV_MCP_FORMS_PORT } else { '8714' }

  Start-ApexBackgroundProcess -FilePath $repoPython -ArgumentList @('-m', 'apex_forms_engine.runtime') -Environment @{
    'PYTHONPATH' = 'packages/forms-engine/src'
    'FORMS_ENGINE_TEMPLATES_PATH' = $formsTemplates
    'FORMS_ENGINE_ARTIFACTS_PATH' = $formsArtifacts
    'OIDC_ISSUER_URL' = $env:APEX_DEV_OIDC_ISSUER_URL
    'OIDC_CLIENT_ID' = $env:APEX_DEV_FORMS_ENGINE_OIDC_CLIENT_ID
  }

  Start-ApexBackgroundProcess -FilePath $repoPython -ArgumentList @('-m', 'apex_p6_ingest.runtime') -Environment @{
    'PYTHONPATH' = 'packages/p6-ingest/src'
    'P6_INGEST_ARTIFACTS_PATH' = $p6Artifacts
    'APEX_P6_FIXTURE_PATH' = (Join-Path $repoRoot 'apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer')
    'OIDC_ISSUER_URL' = $env:APEX_DEV_OIDC_ISSUER_URL
    'OIDC_CLIENT_ID' = $env:APEX_DEV_P6_INGEST_OIDC_CLIENT_ID
  }

  Start-ApexBackgroundProcess -FilePath 'node' -ArgumentList @('services/mcp/apex-fs/build/http.js') -Environment @{
    'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_FS_PORT
    'APEX_MCP_WORKSPACE_ROOT' = $repoRoot
    'APEX_MCP_DATA_ROOT' = (Join-Path $repoRoot '.apex-data')
  }

  Start-ApexBackgroundProcess -FilePath 'node' -ArgumentList @('services/mcp/apex-db/build/http.js') -Environment @{
    'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_DB_PORT
  }

  Start-ApexBackgroundProcess -FilePath 'node' -ArgumentList @('services/mcp/apex-jobs/build/http.js') -Environment @{
    'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_JOBS_PORT
    'APEX_JOBS_LEDGER_PATH' = (Join-Path $repoRoot '.apex-data/apex-jobs-ledger.json')
  }

  Start-ApexBackgroundProcess -FilePath 'node' -ArgumentList @('services/mcp/apex-forms/build/http.js') -Environment @{
    'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_FORMS_PORT
    'APEX_FORMS_RUNTIME_URL' = "http://127.0.0.1:$($env:APEX_DEV_FORMS_ENGINE_PORT)"
  }

  Start-ApexBackgroundProcess -FilePath 'node' -ArgumentList @('services/mcp/apex-p6/build/http.js') -Environment @{
    'APEX_MCP_HTTP_PORT' = $env:APEX_DEV_MCP_P6_PORT
    'APEX_P6_RUNTIME_URL' = "http://127.0.0.1:$($env:APEX_DEV_P6_INGEST_PORT)"
  }

  Wait-ApexEndpoint -Name 'forms runtime' -Url "http://127.0.0.1:$formsRuntimePort/health"
  Wait-ApexEndpoint -Name 'p6 runtime' -Url "http://127.0.0.1:$p6RuntimePort/health"
  Wait-ApexEndpoint -Name 'apex-fs MCP transport' -Url "http://127.0.0.1:$fsMcpPort/mcp"
  Wait-ApexEndpoint -Name 'apex-db MCP transport' -Url "http://127.0.0.1:$dbMcpPort/mcp"
  Wait-ApexEndpoint -Name 'apex-jobs MCP transport' -Url "http://127.0.0.1:$jobsMcpPort/mcp"
  Wait-ApexEndpoint -Name 'apex-p6 MCP transport' -Url "http://127.0.0.1:$p6McpPort/mcp"
  Wait-ApexEndpoint -Name 'apex-forms MCP transport' -Url "http://127.0.0.1:$formsMcpPort/mcp"

  & $repoPython 'tools/canary/run_canary.py'
}
finally {
  foreach ($process in $processes) {
    if ($null -ne $process -and -not $process.HasExited) {
      Stop-Process -Id $process.Id -Force
    }
  }
}
