Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$repoRoot = Get-ApexRepoRoot
$lane = Join-Path $repoRoot 'apps/mutation-seam'

if (-not (Test-Path $lane)) {
  throw 'apps/mutation-seam is not present under the repo root for this bootstrap packet.'
}

$python = Get-ApexRepoPython
Set-Location $lane
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
