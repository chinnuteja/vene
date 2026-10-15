param([switch]$SkipSpeechMeasurement)
. "$PSScriptRoot/common.ps1"
Invoke-Checked (Join-Path $ProjectRoot '.venv/Scripts/python.exe') @('scripts/live-config-check.py')
if (-not (Test-Path -LiteralPath 'apps/web/.next-check/BUILD_ID')) { throw 'Run scripts/check.ps1 -All to build the local verification app first.' }
Invoke-Checked $NodeExe @('scripts/generate-live-audio.mjs')
& "$PSScriptRoot/check-model.ps1"
$env:NEXT_DIST_DIR='.next-check';$env:BRING_VENE_PHASE='8';$env:BRING_VENE_E2E_GREP='live providers complete';$env:BRING_VENE_LIVE_PROVIDER_GATE='true'
try { Invoke-Checked $NodeExe @('scripts/browser-check.mjs') }
finally { Remove-Item Env:BRING_VENE_LIVE_PROVIDER_GATE -ErrorAction SilentlyContinue;Remove-Item Env:BRING_VENE_E2E_GREP -ErrorAction SilentlyContinue }
& "$PSScriptRoot/check-speech.ps1" -LiveTts
if (-not $SkipSpeechMeasurement) { & "$PSScriptRoot/check-speech.ps1" -LiveTts -Measure }
Write-Output 'Configured model, real STT/TTS conversation and sandbox end-to-end gates completed. Review the actual outputs in docs/qa; physical microphone and human acceptance remain separate.'
