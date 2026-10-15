. "$PSScriptRoot/common.ps1"
$env:PLAYWRIGHT_BROWSERS_PATH=Join-Path $ProjectRoot '.local/pw-extra'
try { Invoke-Checked $NodeExe @('node_modules/@playwright/test/cli.js','install','firefox','webkit') }
finally { Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue }
