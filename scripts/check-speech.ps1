param([switch]$Measure,[switch]$LiveTts)
. "$PSScriptRoot/common.ps1"
# Run after check.ps1 -Phase 5. This gate resets only bring_vene_test;
# do not run it concurrently with backend, browser or model checks.
if (-not (Test-Path -LiteralPath 'apps/web/.next-check/BUILD_ID')) { throw 'Run check.ps1 -Phase 5 to build the production verification frontend first.' }
$env:NEXT_DIST_DIR='.next-check'
$env:BRING_VENE_PHASE='5'
$env:BRING_VENE_E2E_GREP=if($Measure){'speech latency'}else{'coordinated speech'}
if($Measure){$env:BRING_VENE_SPEECH_MEASURE='true'}
else{Remove-Item Env:BRING_VENE_SPEECH_MEASURE -ErrorAction SilentlyContinue}
if($LiveTts){$env:BRING_VENE_TTS_LIVE_GATE='true'}
else{Remove-Item Env:BRING_VENE_TTS_LIVE_GATE -ErrorAction SilentlyContinue}
try{Invoke-Checked $NodeExe @('scripts/browser-check.mjs')}
finally{Remove-Item Env:BRING_VENE_SPEECH_MEASURE -ErrorAction SilentlyContinue;Remove-Item Env:BRING_VENE_E2E_GREP -ErrorAction SilentlyContinue;Remove-Item Env:BRING_VENE_TTS_LIVE_GATE -ErrorAction SilentlyContinue}
