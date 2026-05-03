param(
    [ValidateSet('up', 'down', 'config')]
    [string]$Action = 'config',

    [string]$EnvFile = "$HOME/code/personal/.env.personal",

    [switch]$WithDb
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$composeFile = Join-Path $scriptRoot 'personal-stack.compose.yml'

$composeArgs = @(
    'compose'
    '--env-file', $EnvFile
    '-f', $composeFile
)

if ($WithDb) {
    $composeArgs += @('--profile', 'db')
}

switch ($Action) {
    'up' {
        $composeArgs += @('up', '-d')
    }
    'down' {
        $composeArgs += 'down'
    }
    'config' {
        $composeArgs += 'config'
    }
}

Push-Location $repoRoot
try {
    & docker @composeArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
