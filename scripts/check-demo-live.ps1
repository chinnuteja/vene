. "$PSScriptRoot/common.ps1"
# Same isolated test DB as browser-check. Never run alongside other DB-mutating gates.
$runtime=Read-Runtime
Start-ProjectDatabase $runtime
Invoke-Checked $NodeExe @('scripts/generate-live-audio.mjs','--demo')
$env:NEXT_DIST_DIR='.next-check'
$env:BRING_VENE_PHASE='12'
$env:BRING_VENE_LIVE_PROVIDER_GATE='true'
$env:BRING_VENE_E2E_GREP='single-screen demo follows actual'
try{Invoke-Checked $NodeExe @('scripts/browser-check.mjs')}
finally{Remove-Item Env:BRING_VENE_LIVE_PROVIDER_GATE -ErrorAction SilentlyContinue;Remove-Item Env:BRING_VENE_E2E_GREP -ErrorAction SilentlyContinue}
