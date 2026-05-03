Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'shell/common.ps1')

$repoRoot = Get-ApexRepoRoot
Import-ApexEnvFile

$processes = @()

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

  Start-ApexBackgroundProcess -FilePath 'c:/APEX Platform/.venv/Scripts/python.exe' -ArgumentList @('-m', 'apex_forms_engine.runtime') -Environment @{
    'PYTHONPATH' = 'packages/forms-engine/src'
    'FORMS_ENGINE_TEMPLATES_PATH' = $formsTemplates
    'FORMS_ENGINE_ARTIFACTS_PATH' = $formsArtifacts
    'OIDC_ISSUER_URL' = $env:APEX_DEV_OIDC_ISSUER_URL
    'OIDC_CLIENT_ID' = $env:APEX_DEV_FORMS_ENGINE_OIDC_CLIENT_ID
  }

  Start-ApexBackgroundProcess -FilePath 'c:/APEX Platform/.venv/Scripts/python.exe' -ArgumentList @('-m', 'apex_p6_ingest.runtime') -Environment @{
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

  Start-Sleep -Seconds 3

  & 'c:/APEX Platform/.venv/Scripts/python.exe' 'tools/canary/run_canary.py'
}
finally {
  foreach ($process in $processes) {
    if ($null -ne $process -and -not $process.HasExited) {
      Stop-Process -Id $process.Id -Force
    }
  }
}
