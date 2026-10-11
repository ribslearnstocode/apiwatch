param([string]$PostgresBin = 'C:\Program Files\PostgreSQL\17\bin')
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$dataPath = Join-Path $projectRoot '.local-pg'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install backend requirements first; see README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $PostgresBin 'pg_ctl.exe'))) { throw 'Pass -PostgresBin with the path to your PostgreSQL bin directory.' }
$env:PATH = $PostgresBin + ';' + $env:PATH
# Use the installed PostgreSQL client library on Windows.
$env:PSYCOPG_IMPL = 'python'
if (-not (Test-Path -LiteralPath (Join-Path $dataPath 'PG_VERSION'))) {
    & (Join-Path $PostgresBin 'initdb.exe') -D $dataPath -U apiwatch --auth=trust --encoding=UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL initialization failed.' }
}
& (Join-Path $PostgresBin 'pg_ctl.exe') -D $dataPath status *> $null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $PostgresBin 'pg_ctl.exe') -D $dataPath -l (Join-Path $dataPath 'server.log') -o '-p 55433 -h 127.0.0.1' start
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL did not start. Check whether port 55433 is occupied.' }
}
$databaseExists = & (Join-Path $PostgresBin 'psql.exe') -h 127.0.0.1 -p 55433 -U apiwatch -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='apiwatch'"
if ($LASTEXITCODE -ne 0) { throw 'Could not connect to the local PostgreSQL cluster.' }
if ($databaseExists -ne '1') {
    & (Join-Path $PostgresBin 'createdb.exe') -h 127.0.0.1 -p 55433 -U apiwatch apiwatch
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the apiwatch database.' }
}
$env:DATABASE_URL = 'postgresql+psycopg://apiwatch@127.0.0.1:55433/apiwatch'
$env:SCHEDULER_ENABLED = 'true'
Set-Location -LiteralPath (Join-Path $projectRoot 'backend')
& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --workers 1
