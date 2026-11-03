$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try {
    if ($env:LG_PYTHON) {
        & $env:LG_PYTHON 'python/launcher.py' @args
    } elseif (Test-Path -LiteralPath '.venv/Scripts/python.exe') {
        & '.venv/Scripts/python.exe' 'python/launcher.py' @args
    } elseif (Test-Path -LiteralPath '.venv/bin/python') {
        & '.venv/bin/python' 'python/launcher.py' @args
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 'python/launcher.py' @args
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        & python3 'python/launcher.py' @args
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python 'python/launcher.py' @args
    } else {
        throw 'Python 3.12+ is required. Install Python or set LG_PYTHON.'
    }
    exit $LASTEXITCODE
} catch {
    Write-Error $_
    exit 1
}
