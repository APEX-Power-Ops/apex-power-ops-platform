Set-StrictMode -Version Latest

function Get-ApexRepoRoot {
  $scriptRoot = Split-Path -Parent $PSScriptRoot
  return (Resolve-Path (Join-Path $scriptRoot '..')).Path
}

function Import-ApexEnvFile {
  param(
    [string]$EnvFile = (Join-Path (Get-ApexRepoRoot) '.env.dev')
  )

  if (-not (Test-Path $EnvFile)) {
    $EnvFile = Join-Path (Get-ApexRepoRoot) '.env.dev.template'
  }

  Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^(#|\s*$)') {
      return
    }

    $name, $value = $_ -split '=', 2
    if ($name -and $value -ne $null) {
      [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
    }
  }
}

function Get-ApexRepoPython {
  if ($env:APEX_PLATFORM_PYTHON) {
    return $env:APEX_PLATFORM_PYTHON
  }

  $repoRoot = Get-ApexRepoRoot
  $candidates = @(
    (Join-Path $repoRoot '.venv\Scripts\python.exe'),
    (Join-Path $repoRoot '.venv/bin/python')
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  throw "No repo-local Python interpreter found under $repoRoot/.venv."
}
