param([switch]$Infrastructure)
. "$PSScriptRoot/common.ps1"
$pidPath = Join-Path $ProjectRoot '.local/processes.json'
if (Test-Path -LiteralPath $pidPath) {
    $owned = Get-Content -LiteralPath $pidPath -Raw | ConvertFrom-Json
    if ($owned.root -ne $ProjectRoot) { throw 'Process ownership does not match this checkout.' }
    $rootProcess = Get-Process -Id $owned.pid -ErrorAction SilentlyContinue
    if ($rootProcess) {
        $recordedStart = if ($owned.started_at -is [datetime]) { $owned.started_at.ToUniversalTime() } else { [datetimeoffset]::Parse($owned.started_at).UtcDateTime }
        $identity = Get-CimInstance Win32_Process -Filter "ProcessId=$($owned.pid)"
        if (-not $identity.CommandLine.Contains((Join-Path $ProjectRoot 'scripts/dev.mjs'))) { throw 'Process command does not match the owned launcher.' }
        if ([Math]::Abs(($rootProcess.StartTime.ToUniversalTime() - $recordedStart).TotalSeconds) -gt 3) {
            throw 'PID has been reused. Refusing to stop an unrelated process.'
        }
        $allProcesses = Get-CimInstance Win32_Process
        function Stop-OwnedTree([int]$ProcessId) {
            foreach ($child in $allProcesses | Where-Object ParentProcessId -eq $ProcessId) { Stop-OwnedTree $child.ProcessId }
            Stop-Process -Id $ProcessId -ErrorAction SilentlyContinue
        }
        Stop-OwnedTree $owned.pid
    }
    Remove-Item -LiteralPath $pidPath -ErrorAction SilentlyContinue
}
if ($Infrastructure) {
    $runtime = Read-Runtime
    if ($runtime.database_mode -eq 'native') {
        Invoke-Checked (Join-Path $ProjectRoot '.local/tools/postgres/pgsql/bin/pg_ctl.exe') @('stop','-D',(Join-Path $ProjectRoot '.local/pgdata'),'-m','fast','-w')
    } else {
        Invoke-Checked 'docker' @('compose','--env-file','.local/compose.env','-f','infra/compose.yaml','stop')
    }
}
Write-Output 'Owned application processes stopped.'

