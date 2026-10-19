$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BundledRoot = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies'
$NodeExe = Join-Path $BundledRoot 'node/bin/node.exe'
if (-not (Test-Path -LiteralPath $NodeExe)) { $NodeExe = (Get-Command node.exe).Source }
$PnpmExe = Join-Path $BundledRoot 'bin/fallback/pnpm.cmd'
if (-not (Test-Path -LiteralPath $PnpmExe)) { $PnpmExe = (Get-Command pnpm.cmd).Source }
$UvExe = Join-Path $env:USERPROFILE '.local/bin/uv.exe'
if (-not (Test-Path -LiteralPath $UvExe)) { $UvExe = (Get-Command uv.exe).Source }
$PythonExe = Join-Path $BundledRoot 'python/python.exe'
$env:PATH = (Split-Path $NodeExe) + ';' + $env:PATH
$env:NEXT_TELEMETRY_DISABLED = '1'
Set-Location -LiteralPath $ProjectRoot

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Executable" }
}
function Get-FreePort {
    param([int]$Preferred)
    for ($candidate = $Preferred; $candidate -lt $Preferred + 100; $candidate++) {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $candidate)
        try { $listener.Start(); return $candidate } catch { } finally { $listener.Stop() }
    }
    throw 'No local port available.'
}
function Read-Runtime {
    $path = Join-Path $ProjectRoot '.local/runtime.json'
    if (-not (Test-Path -LiteralPath $path)) { throw 'Run scripts/setup.ps1 first.' }
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
}
function Set-DatabaseEnvironment {
    param($Runtime, [switch]$Test)
    $env:DATABASE_URL = if ($Test) { $Runtime.test_database_url } else { $Runtime.database_url }
    $env:TEST_DATABASE_URL = $Runtime.test_database_url
}

function Start-ProjectDatabase {
    param($Runtime)
    if ($Runtime.database_mode -ne 'native') { return }
    $ctl = Join-Path $ProjectRoot '.local/tools/postgres/pgsql/bin/pg_ctl.exe'
    $data = Join-Path $ProjectRoot '.local/pgdata'
    if (-not (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) { throw 'Run scripts/setup.ps1 first. The saved cluster is missing.' }
    & $ctl status -D $data 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { return }
    # Wait for pg_ctl itself, never the long-lived postgres descendant tree.
    $log = Join-Path $ProjectRoot '.local/logs/postgres.log'
    $arguments = 'start -D "' + $data + '" -l "' + $log + '" -o "-h 127.0.0.1 -p ' + $Runtime.postgres_port + '" -w'
    $starter = Start-Process -FilePath $ctl -ArgumentList $arguments -WindowStyle Hidden -PassThru
    if (-not $starter.WaitForExit(30000)) { throw 'Project PostgreSQL startup timed out. Inspect .local/logs/postgres.log.' }
    if ($starter.ExitCode -ne 0) { throw 'Project PostgreSQL could not start. No data was reset.' }
}

