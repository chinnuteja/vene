param([int]$Phase = 1, [switch]$All)
. "$PSScriptRoot/common.ps1"
if ($Phase -notin @(1,2,3,4,5,6,7,8,9,10)) { throw 'Only Phases 1-10 checks are implemented. Later phases cannot be declared passed.' }
$runtime = Read-Runtime
if ($All) { $Phase = 10; Write-Output 'All implemented checks: Phases 1-10. Live STT/model/TTS and physical acoustics remain separate gates.' }
Set-DatabaseEnvironment $runtime
$startedAt = Get-Date
Invoke-Checked $NodeExe @('--test','scripts/child-logs.test.mjs')
Invoke-Checked $UvExe @('run','--frozen','pytest')
Invoke-Checked $NodeExe @('scripts/contracts.mjs','--check')
Invoke-Checked $PnpmExe @('typecheck')
$env:NEXT_DIST_DIR = '.next-check'
Invoke-Checked $PnpmExe @('build')
$env:BRING_VENE_BASE_URL = "http://127.0.0.1:$($runtime.web_port)"
$env:BRING_VENE_PHASE = [string]$Phase
Remove-Item Env:BRING_VENE_E2E_GREP -ErrorAction SilentlyContinue
Invoke-Checked $NodeExe @('scripts/browser-check.mjs')
$report = [pscustomobject]@{ phase=$Phase; checked_at=(Get-Date).ToString('o'); duration_seconds=((Get-Date)-$startedAt).TotalSeconds; backend='passed'; contracts='passed'; typecheck='passed'; build='passed'; browser='passed'; mode='fixture' }
if ($Phase -ge 3) {
    $report | Add-Member -NotePropertyName real_media_transport -NotePropertyValue 'passed'
    $report | Add-Member -NotePropertyName live_stt -NotePropertyValue 'not_exercised_by_fixture_suite'
    $report | Add-Member -NotePropertyName physical_microphone -NotePropertyValue 'not_exercised'
}
if ($Phase -ge 4) { $report | Add-Member -NotePropertyName real_model -NotePropertyValue 'not_exercised_by_fixture_suite' }
if ($Phase -ge 5) { $report | Add-Member -NotePropertyName live_tts -NotePropertyValue 'not_exercised_by_fixture_suite' }
if ($Phase -ge 6) { $report | Add-Member -NotePropertyName sandbox_execution -NotePropertyValue 'passed_actual_local_http_office' }
if ($Phase -ge 7) { $report | Add-Member -NotePropertyName continuity -NotePropertyValue 'passed_signed_callbacks_pdf_family_acknowledgement_restart_and_private_next_visit' }
if ($Phase -ge 8) { $report | Add-Member -NotePropertyName packaging -NotePropertyValue 'three_cases_accessibility_and_platform_smoke; see_docs_qa_for_platform_limits'; $report | Add-Member -NotePropertyName founder_demo_readiness -NotePropertyValue 'pending_live_provider_outputs_timing_and_human_review' }
$report | ConvertTo-Json | Set-Content -LiteralPath ('.local/check-phase-{0:d2}.json' -f $Phase)
Write-Output "Phase $Phase automated checks passed. Visual browser review is recorded separately."
if ($Phase -ge 3) { Write-Output 'Live STT accuracy and physical microphone quality remain separate, unverified gates.' }
if ($Phase -ge 4) { Write-Output 'Real-model free-form extraction remains an open gate. These scenario checks do not establish model quality.' }
if ($Phase -eq 5) { Write-Output 'Offline speech is verified separately from live TTS quality; measurement evidence is recorded in docs/qa.' }

