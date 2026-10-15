param([int]$ProcessId)
. "$PSScriptRoot/common.ps1"
$record=Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot '.local/browser-media-process.json') | ConvertFrom-Json
if ($record.root -ne $ProjectRoot -or $record.pid -ne $ProcessId) { throw 'Test process ownership does not match this workspace.' }
$target=Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
$expectedExe=Join-Path $ProjectRoot '.local/tools/livekit/livekit-server.exe'
$expectedConfig=Join-Path $ProjectRoot '.local/browser-livekit.yaml'
if (-not $target -or $target.ParentProcessId -ne $record.parent_pid -or -not $target.CommandLine.Contains($expectedExe) -or -not $target.CommandLine.Contains($expectedConfig)) { throw 'Refusing to stop a process outside the owned browser test server.' }
$started=[datetimeoffset]::Parse([string]$record.started_at).UtcDateTime
if ([Math]::Abs(((Get-Process -Id $ProcessId).StartTime.ToUniversalTime()-$started).TotalSeconds) -gt 3) { throw 'Test PID has been reused.' }
Stop-Process -Id $ProcessId
Write-Output 'Owned browser-test media server stopped for the server-loss scenario.'
