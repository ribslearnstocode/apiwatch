$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath (Join-Path $projectRoot 'backend')
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run the README installation steps first.' }
& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --workers 1
