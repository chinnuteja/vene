param([ValidateSet('fixture','live')][string]$Mode = 'fixture', [switch]$Production, [switch]$ModelLive, [switch]$TtsLive, [switch]$LiveProviders)
. "$PSScriptRoot/common.ps1"
$runtime = Read-Runtime
Set-DatabaseEnvironment $runtime
$arguments = @((Join-Path $ProjectRoot 'scripts/dev.mjs'), '--mode', $Mode)
if ($Production) { $arguments += '--production' }
if ($ModelLive) { $arguments += '--model-live' }
if ($TtsLive) { $arguments += '--tts-live' }
if ($LiveProviders) { $arguments += '--live-providers' }
Invoke-Checked $NodeExe $arguments

