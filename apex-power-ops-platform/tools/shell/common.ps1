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
