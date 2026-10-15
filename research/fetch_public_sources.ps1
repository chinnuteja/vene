$ErrorActionPreference = 'Stop'
$researchRoot = Join-Path $PSScriptRoot 'sources'
New-Item -ItemType Directory -Force -Path $researchRoot | Out-Null
$researchSources = @(
    @('prologue-intake.ts', 'mayu99/prologue-health/d94a9f812c0dad7ba8b7cb0ab1eb3a9568e20253/lib/intake.ts'),
    @('prologue-clinical.ts', 'mayu99/prologue-health/d94a9f812c0dad7ba8b7cb0ab1eb3a9568e20253/lib/clinical.ts'),
    @('veteran-conversation.py', 'uzlnee/Veteran/496ffe703fda01a041a5b84250a70d22a17d8139/conversation_logic.py'),
    @('pills-talk.html', 'Andy-cool-blue/yaoshua-pills-talk/a7c7d6a39131c707a04d4a4e2112a4ed3f47433a/app/index.html'),
    @('careroute-safety.cs', 'monoqlo78/mimamoritai-careroute-ai/03e83aa0097761a5562ffcb81d32c272640f7582/src/MimamoriTai.Core/Application/DeviceSafetyPolicy.cs'),
    @('careroute-risk.cs', 'monoqlo78/mimamoritai-careroute-ai/03e83aa0097761a5562ffcb81d32c272640f7582/src/MimamoriTai.Core/Application/RiskAssessmentService.cs'),
    @('ufonia-README.md', 'Ufonia/wer-is-unaware/9844cb0ecb2592f338f47f6745a433aed699aa82/README.md'),
    @('ufonia-LICENSE', 'Ufonia/wer-is-unaware/9844cb0ecb2592f338f47f6745a433aed699aa82/LICENSE'),
    @('ufonia-signatures.py', 'Ufonia/wer-is-unaware/9844cb0ecb2592f338f47f6745a433aed699aa82/llm_judge/signatures.py'),
    @('hike-README.md', 'ThetaOne-AI/HiKE/436f6aaa7390ab94c78a928baba47ec668a5621c/README.md'),
    @('hike-LICENSE', 'ThetaOne-AI/HiKE/436f6aaa7390ab94c78a928baba47ec668a5621c/LICENSE'),
    @('hike-metric.py', 'ThetaOne-AI/HiKE/436f6aaa7390ab94c78a928baba47ec668a5621c/src/metrics/mer.py'),
    @('agentdam-README.md', 'facebookresearch/ai-agent-privacy/5d4068a404b624ed24ebbe5fb49ba5f644557912/README.md'),
    @('agentdam-LICENSE', 'facebookresearch/ai-agent-privacy/5d4068a404b624ed24ebbe5fb49ba5f644557912/LICENSE')
)
$researchManifest = @()
foreach ($researchSource in $researchSources) {
    $researchUrl = 'https://raw.githubusercontent.com/' + $researchSource[1]
    $researchPath = Join-Path $researchRoot $researchSource[0]
    Invoke-WebRequest -Uri $researchUrl -OutFile $researchPath
    $researchManifest += [pscustomobject]@{file=$researchSource[0]; url=$researchUrl; sha256=(Get-FileHash -LiteralPath $researchPath -Algorithm SHA256).Hash}
}
$researchManifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $researchRoot 'manifest.json') -Encoding utf8
$researchManifest | Select-Object file,sha256 | Format-Table -AutoSize
