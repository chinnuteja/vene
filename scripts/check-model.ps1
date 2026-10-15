. "$PSScriptRoot/common.ps1"
$runtime=Read-Runtime
Set-DatabaseEnvironment $runtime -Test
Invoke-Checked (Join-Path $ProjectRoot '.venv/Scripts/python.exe') @('scripts/model-check.py')
