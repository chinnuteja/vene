param([ValidateSet('fixture','live')][string]$Mode = 'fixture', [switch]$Production, [switch]$ModelLive, [switch]$TtsLive, [switch]$LiveProviders, [switch]$Guided)
. "$PSScriptRoot/common.ps1"
$runtime = Read-Runtime
if ($Guided -and ($LiveProviders -or $ModelLive -or $TtsLive -or $Mode -eq 'live')) { throw 'Guided fixture must be explicitly separate from live providers.' }
Start-ProjectDatabase $runtime
Set-DatabaseEnvironment $runtime
Invoke-Checked $UvExe @('run','--frozen','alembic','-c','services/backend/alembic.ini','upgrade','head')
$arguments = @((Join-Path $ProjectRoot 'scripts/dev.mjs'), '--mode', $Mode)
if ($Guided) { $arguments += '--guided' }
if ($Production) { $arguments += '--production' }
if ($ModelLive) { $arguments += '--model-live' }
if ($TtsLive) { $arguments += '--tts-live' }
if ($LiveProviders) { $arguments += '--live-providers' }
Invoke-Checked $NodeExe $arguments

