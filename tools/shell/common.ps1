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
    if ($name -and $null -ne $value) {
      [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
    }
  }
}

function Get-ApexRepoPython {
  if ($env:APEX_PLATFORM_PYTHON) {
    $configuredPython = $env:APEX_PLATFORM_PYTHON
    if ($configuredPython -match '[\\/]') {
      if (Test-Path $configuredPython) {
        return (Resolve-Path $configuredPython).Path
      }

      throw "Configured APEX_PLATFORM_PYTHON path not found: $configuredPython"
    }

    $command = Get-Command $configuredPython -ErrorAction SilentlyContinue
    if ($null -ne $command -and $command.Path) {
      return $command.Path
    }

    throw "Configured APEX_PLATFORM_PYTHON command not found: $configuredPython"
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

function Get-ApexDefaultPacketId {
  param(
    [string]$Label = 'operator'
  )

  if ($env:APEX_PACKET_ID) {
    return $env:APEX_PACKET_ID
  }

  $timestamp = [DateTime]::UtcNow.ToString('yyyy-MM-dd-HHmmss')
  return "adhoc-$Label-$timestamp"
}
