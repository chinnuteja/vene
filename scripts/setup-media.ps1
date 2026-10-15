param()
. "$PSScriptRoot/common.ps1"
$pin=Get-Content -Raw -LiteralPath (Join-Path $ProjectRoot 'infra/livekit-binary.json') | ConvertFrom-Json
$downloadPath=Join-Path $ProjectRoot ".local/downloads/livekit-$($pin.version).zip"
$toolPath=Join-Path $ProjectRoot '.local/tools/livekit'
New-Item -ItemType Directory -Force -Path (Split-Path $downloadPath),$toolPath | Out-Null
if (-not (Test-Path -LiteralPath $downloadPath)) { Invoke-WebRequest -Uri $pin.source -OutFile $downloadPath }
if ((Get-FileHash -LiteralPath $downloadPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256) { throw 'LiveKit archive checksum does not match the pinned official release.' }
if (-not (Test-Path -LiteralPath (Join-Path $toolPath 'livekit-server.exe'))) { Expand-Archive -LiteralPath $downloadPath -DestinationPath $toolPath -Force }
Invoke-Checked (Join-Path $toolPath 'livekit-server.exe') @('--version')
$runtime=Read-Runtime
if (-not $runtime.livekit_key) { $runtime | Add-Member -NotePropertyName livekit_key -NotePropertyValue ('vene_'+[Guid]::NewGuid().ToString('N')) -Force }
if (-not $runtime.livekit_secret) { $secret=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant(); $runtime | Add-Member -NotePropertyName livekit_secret -NotePropertyValue $secret -Force }
if (-not $runtime.livekit_port) { $runtime | Add-Member -NotePropertyName livekit_port -NotePropertyValue 7880 -Force }
if (-not $runtime.livekit_tcp_port) { $runtime | Add-Member -NotePropertyName livekit_tcp_port -NotePropertyValue 7881 -Force }
if (-not $runtime.livekit_udp_port) { $runtime | Add-Member -NotePropertyName livekit_udp_port -NotePropertyValue 7882 -Force }
if (-not $runtime.livekit_turn_port) { $runtime | Add-Member -NotePropertyName livekit_turn_port -NotePropertyValue 3478 -Force }
$runtime | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $ProjectRoot '.local/runtime.json') -Encoding utf8NoBOM
Write-Output 'Pinned local LiveKit installed. Credentials saved only in ignored runtime state.'
