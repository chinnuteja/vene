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

